"""Smoke tests: CLI demo mode, API recommendations on demo data, no-AI requirement.

https://app.clickup.com/t/86d3qg0c0

Test categories
---------------
- No marker: static assertions, no server required, always run in CI.
- @pytest.mark.integration: requires a running demo server (spun up by the
  demo_api fixture using .venv/bin/python3.12). These are skipped unless
  RUN_INTEGRATION_TESTS=1 is set in the environment.

  To run locally:
      RUN_INTEGRATION_TESTS=1 python3 -m pytest tests/test_smoke.py -v
"""

import os
import pathlib
import subprocess
import sys
import time

import pytest
import requests


DEMO_API_BASE = "http://localhost:15001"
NPM_CLI_PATH = "kubeopt-distribution/npm-cli/bin/kubeopt.js"

_run_integration = os.environ.get("RUN_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")
integration = pytest.mark.skipif(
    not _run_integration,
    reason="Set RUN_INTEGRATION_TESTS=1 to run demo-server smoke tests",
)

# Root of the KubeOpt monorepo (two levels above kubeopt/)
_REPO_ROOT = pathlib.Path(__file__).parents[2]
# Root of the kubeopt/ Python package tree (parent of tests/)
_KUBEOPT_ROOT = pathlib.Path(__file__).parents[1]


# ---------------------------------------------------------------------------
# CLI smoke assertions (no server needed)
# ---------------------------------------------------------------------------

def test_npm_cli_file_exists():
    """CLI entry point must exist for npx kubeopt to work."""
    cli = _REPO_ROOT / NPM_CLI_PATH
    assert cli.exists(), f"CLI not found at {cli}"


def test_npm_cli_demo_arg_is_present():
    """CLI must reference KUBEOPT_DEMO env var when demo subcommand is used."""
    cli = _REPO_ROOT / NPM_CLI_PATH
    content = cli.read_text()
    assert "KUBEOPT_DEMO" in content, "CLI does not reference KUBEOPT_DEMO env var"


# ---------------------------------------------------------------------------
# Demo API server fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def demo_api():
    """Start a demo API server on port 15001, yield, then stop."""
    env = {
        **os.environ,
        "KUBEOPT_DEMO": "true",
        "LOCAL_DEV": "true",
        "PORT": "15001",
    }
    # Use the venv Python that has all kubeopt dependencies installed
    venv_python = str(_KUBEOPT_ROOT / ".venv" / "bin" / "python3.12")
    proc = subprocess.Popen(
        [
            venv_python, "-m", "uvicorn", "fastapi_app:app",
            "--port", "15001",
            "--log-level", "warning",
        ],
        env=env,
        cwd=str(_KUBEOPT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server to be ready (up to 10 seconds)
    for _ in range(20):
        try:
            r = requests.get(f"{DEMO_API_BASE}/health", timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait(timeout=5)


def _get_demo_token():
    """Log in as the demo user and return a JWT."""
    r = requests.post(
        f"{DEMO_API_BASE}/api/auth/login",
        json={"username": "demo", "password": "demo"},
        timeout=5,
    )
    assert r.status_code == 200, f"Demo login failed: {r.status_code} {r.text}"
    return r.json()["token"]


# ---------------------------------------------------------------------------
# API smoke assertions (require demo server)
# ---------------------------------------------------------------------------

@integration
def test_demo_api_returns_clusters(demo_api):
    token = _get_demo_token()
    r = requests.get(
        f"{DEMO_API_BASE}/api/clusters",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    assert r.status_code == 200, f"GET /api/clusters returned {r.status_code}"
    body = r.json()
    clusters = body.get("clusters", body) if isinstance(body, dict) else body
    assert len(clusters) > 0, "Demo mode must return at least one cluster"


@integration
def test_demo_api_recommendations_non_empty(demo_api):
    token = _get_demo_token()
    clusters_r = requests.get(
        f"{DEMO_API_BASE}/api/clusters",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    body = clusters_r.json()
    clusters = body.get("clusters", body) if isinstance(body, dict) else body
    cluster_id = clusters[0]["cluster_id"]

    recs_r = requests.get(
        f"{DEMO_API_BASE}/api/clusters/{cluster_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert recs_r.status_code == 200, f"GET recommendations returned {recs_r.status_code}: {recs_r.text}"
    recs = recs_r.json()
    assert len(recs) > 0, "Demo cluster must return at least one recommendation"
    first = recs[0]
    assert "id" in first
    assert "monthly_savings" in first
    assert "priority_score" in first


@integration
def test_demo_recommendations_do_not_require_ai(demo_api):
    token = _get_demo_token()
    clusters_r = requests.get(
        f"{DEMO_API_BASE}/api/clusters",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    body = clusters_r.json()
    clusters = body.get("clusters", body) if isinstance(body, dict) else body
    cluster_id = clusters[0]["cluster_id"]

    recs_r = requests.get(
        f"{DEMO_API_BASE}/api/clusters/{cluster_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    recs = recs_r.json()
    non_ai = [rec for rec in recs if not rec.get("requires_ai", True)]
    assert len(non_ai) > 0, "At least one recommendation must not require AI"
