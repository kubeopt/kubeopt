"""Exercise base/head snapshots and the offline CLI against real Git commits."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from manifest_diff.command import build_preview
from manifest_diff.parser import ManifestError, parse_manifests
from manifest_diff.differ import diff_workloads
from manifest_diff.formatter import render_markdown


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = """apiVersion: apps/v1
kind: Deployment
metadata: {name: inference-api, namespace: staging}
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: inference
        resources:
          requests: {cpu: 500m, memory: 1Gi}
          limits: {cpu: '1', memory: 2Gi, nvidia.com/gpu: 1}
"""


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null",
         "-c", "user.name=KubeOpt Test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


@pytest.fixture
def history(tmp_path):
    git(tmp_path, "init")
    (tmp_path / "app.yaml").write_text(MANIFEST)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "base manifest")
    base = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "app.yaml").write_text(MANIFEST.replace("replicas: 2", "replicas: 3"))
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "increase replicas")
    return tmp_path, base, git(tmp_path, "rev-parse", "HEAD")


def test_commits_are_used_even_when_working_tree_is_dirty(history):
    repo, base, head = history
    (repo / "app.yaml").write_text("invalid YAML: [")
    report = build_preview(base, head, repo)
    assert report["base"] == base
    assert report["head"] == head
    assert len(report["changes"]) == 1
    change = report["changes"][0]
    assert change["requests_delta"] == {
        "cpu_millicores": "500", "memory_bytes": "1073741824", "nvidia_gpu": "1", "amd_gpu": "0",
    }
    assert change["limits_delta"]["cpu_millicores"] == "1000"
    assert report["pricing"]["billing_delta"] is None


def test_rename_does_not_create_a_resource_change(history):
    repo, _, base = history
    git(repo, "mv", "app.yaml", "moved.yml")
    git(repo, "commit", "-m", "move manifest")
    assert build_preview(base, "HEAD", repo)["changes"] == []


def test_deleted_workload_is_reported(history):
    repo, _, base = history
    git(repo, "rm", "app.yaml")
    git(repo, "commit", "-m", "remove workload")
    change = build_preview(base, "HEAD", repo)["changes"][0]
    assert change["status"] == "removed"
    assert change["requests_delta"]["nvidia_gpu"] == "-3"


def test_unmodified_templates_do_not_block_plain_manifest_diff(history):
    repo, _, _ = history
    (repo / "template.yaml").write_text("{{ invalid template }}")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "add template")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "app.yaml").write_text(MANIFEST.replace("replicas: 2", "replicas: 4"))
    git(repo, "add", ".")
    git(repo, "commit", "-m", "change plain manifest")
    assert len(build_preview(base, "HEAD", repo)["changes"]) == 1


def test_bad_ref_has_actionable_error(history):
    repo, _, head = history
    with pytest.raises(ManifestError, match="commit refs"):
        build_preview("--help", head, repo)


@pytest.mark.parametrize("price", ["-1", "NaN", "Infinity", "wrong"])
def test_invalid_prices_fail(history, price):
    repo, base, head = history
    with pytest.raises(ManifestError, match="finite non-negative"):
        build_preview(base, head, repo, price)


@pytest.mark.parametrize("price", ["0", "125.50"])
def test_node_price_never_invents_a_workload_estimate(history, price):
    repo, base, head = history
    report = build_preview(base, head, repo, price)
    assert report["pricing"]["monthly_allocation_delta"] is None
    assert report["pricing"]["billing_delta"] is None
    assert "Operator-provided node price" in report["markdown"]
    assert "Cost estimate unavailable" in report["markdown"]


def test_cli_json_is_parseable_and_markdown_is_separate(history):
    repo, base, head = history
    cmd = [sys.executable, str(ROOT / "cli.py"), "diff", "--repo", str(repo), "--base", base, "--head", head]
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    report = json.loads(completed.stdout)
    assert report["changes"][0]["name"] == "inference-api"
    assert "Pricing input" not in report["markdown"]
    markdown = subprocess.run(cmd + ["--format", "markdown"], check=True, capture_output=True, text=True)
    assert markdown.stdout.startswith("## KubeOpt resource preview")


def test_offline_command_does_not_load_credentials(history, monkeypatch, capsys):
    import cli

    def fail(*args, **kwargs):
        raise AssertionError("Offline diff must not load credentials")

    monkeypatch.setattr(cli, "_load_dotenv", fail)
    monkeypatch.setitem(sys.modules, "mcp_server.api_client", None)
    repo, base, head = history
    assert cli.main(["diff", "--repo", str(repo), "--base", base, "--head", head]) == 0
    assert json.loads(capsys.readouterr().out)["changes"]


def test_invalid_cli_input_does_not_print_a_partial_report(history):
    repo, _, head = history
    completed = subprocess.run(
        [sys.executable, str(ROOT / "cli.py"), "diff", "--repo", str(repo), "--base", "missing", "--head", head],
        capture_output=True, text=True,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert "ERROR:" in completed.stderr


def test_markdown_escapes_untrusted_labels():
    parsed = parse_manifests(MANIFEST.replace("inference-api", "<script>|bad"))
    rendered = render_markdown(diff_workloads([], parsed))
    assert "<script>" not in rendered
    assert "&lt;script&gt;&#124;bad" in rendered
