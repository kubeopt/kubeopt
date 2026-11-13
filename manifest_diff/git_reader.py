"""Read changed manifests directly from two immutable Git snapshots."""

from pathlib import Path
import subprocess

from .parser import ManifestError, parse_manifests


def _git(repo, *args):
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        raise ManifestError(f"Git operation failed: {args[0]}; check repository and commit refs") from exc


def _commit(repo, ref):
    return _git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()


def _snapshot(repo, commit, changed_paths):
    workloads = []
    for record in _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit).split(b"\0"):
        if not record:
            continue
        header, path = record.split(b"\t", 1)
        if path not in changed_paths:
            continue
        mode, kind, blob = header.split()
        source = path.decode("utf-8", errors="replace")
        if kind != b"blob" or mode not in (b"100644", b"100755"):
            raise ManifestError(f"{source}: only regular manifest files are supported")
        size = int(_git(repo, "cat-file", "-s", blob.decode()))
        if size > 2 * 1024 * 1024:
            raise ManifestError(f"{source}: manifest exceeds 2 MiB")
        try:
            text = _git(repo, "cat-file", "blob", blob.decode()).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ManifestError(f"{source}: manifest must be UTF-8") from exc
        workloads.extend(parse_manifests(text, source=source))
    return workloads


def read_git_states(base, head, repo=Path(".")):
    base_commit, head_commit = _commit(repo, base), _commit(repo, head)
    paths = set(_git(
        repo, "diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", base_commit, head_commit,
        "--", "*.yaml", "*.yml",
    ).split(b"\0")) - {b""}
    return (base_commit, head_commit,
            _snapshot(repo, base_commit, paths), _snapshot(repo, head_commit, paths))
