"""Regression tests: disabled CPU-proxy GPU findings must not appear in API responses."""

import os
os.environ.setdefault("LOCAL_DEV", "true")

from presentation.api.v2.routers.analysis import _filter_disabled_gpu_findings


_DISABLED_TITLES = [
    "Idle GPU pod -- inference-api",
    "Low CPU on GPU pod -- inference-api",
    "Low GPU node pool occupancy -- a100-pool",
]

_ALLOWED_TITLES = [
    "GPU workload without autoscaling -- inference-api",
    "GPU pod missing cpu/memory limits -- inference-api",
    "Right-size deployment/web-app",
    "Idle namespace -- staging",
]


def _rec(title: str) -> dict:
    return {
        "id": "abc123",
        "title": title,
        "category": "GPU_WORKLOAD",
        "resource_ref": "deployment/x",
        "namespace": "default",
        "monthly_savings": 500.0,
        "confidence": 0.85,
        "risk_level": "LOW",
        "priority_score": 425.0,
        "evidence": "...",
        "command": "kubectl delete pod x -n default",
        "rollback": None,
        "requires_ai": False,
    }


class TestDisabledGPUFindingFilter:
    def test_idle_gpu_pod_title_is_filtered(self):
        recs = [_rec("Idle GPU pod -- inference-api")]
        assert _filter_disabled_gpu_findings(recs) == []

    def test_low_cpu_gpu_pod_title_is_filtered(self):
        recs = [_rec("Low CPU on GPU pod -- inference-api")]
        assert _filter_disabled_gpu_findings(recs) == []

    def test_low_occupancy_title_is_filtered(self):
        recs = [_rec("Low GPU node pool occupancy -- a100-pool")]
        assert _filter_disabled_gpu_findings(recs) == []

    def test_allowed_gpu_titles_pass_through(self):
        for title in _ALLOWED_TITLES:
            recs = [_rec(title)]
            result = _filter_disabled_gpu_findings(recs)
            assert len(result) == 1, f"Expected {title!r} to pass through filter"

    def test_mixed_list_removes_only_disabled(self):
        mixed = [_rec(t) for t in _DISABLED_TITLES + _ALLOWED_TITLES]
        result = _filter_disabled_gpu_findings(mixed)
        result_titles = [r["title"] for r in result]
        for title in _DISABLED_TITLES:
            assert title not in result_titles, f"Disabled title should be removed: {title}"
        for title in _ALLOWED_TITLES:
            assert title in result_titles, f"Allowed title should remain: {title}"

    def test_filter_preserves_savings_for_allowed_findings(self):
        """Savings on allowed findings must not be zeroed by the filter."""
        recs = [_rec("GPU workload without autoscaling -- inference-api")]
        result = _filter_disabled_gpu_findings(recs)
        assert result[0]["monthly_savings"] == 500.0

    def test_empty_list_returns_empty(self):
        assert _filter_disabled_gpu_findings([]) == []

    def test_no_delete_pod_command_survives_from_disabled_rules(self):
        """The kubectl delete pod command from disabled rules must not reach the caller."""
        recs = [_rec("Idle GPU pod -- finetune-job-stale")]
        result = _filter_disabled_gpu_findings(recs)
        assert result == []
        # Verify the unfiltered rec did carry the command, confirming the filter is load-bearing
        assert recs[0]["command"] == "kubectl delete pod x -n default"
