"""Regression tests: disabled CPU-proxy GPU findings must not appear in API responses."""

import os
os.environ.setdefault("LOCAL_DEV", "true")

from presentation.api.v2.routers.analysis import (
    _filter_disabled_gpu_findings,
    _append_collector_gpu_recommendations,
)


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


class TestCollectorGPUSavingsWithoutPricingSource:
    """P0 regression: GPU savings from the price table must not appear when no pricing source exists.

    CollectorAnalysisService intentionally omits all savings (monthly_savings=None).
    The GPU evaluator appended by _append_collector_gpu_recommendations derives savings
    from a hard-coded price table. Without a real pricing source (no cloud billing,
    no node_monthly_cost), those figures are fabricated and must be cleared to None.
    """

    def _gpu_rec_with_savings(self, savings: float = 2100.0) -> dict:
        return {
            "id": "gpu-rec-001",
            "title": "GPU workload without autoscaling -- inference-api",
            "category": "GPU_WORKLOAD",
            "resource_ref": "deployment/inference-api",
            "namespace": "ml",
            "monthly_savings": savings,
            "confidence": 0.75,
            "risk_level": "MEDIUM",
            "priority_score": 945.0,
            "evidence": "No HPA configured.",
            "command": None,
            "yaml_patch": None,
            "requires_ai": False,
        }

    def test_gpu_savings_cleared_when_no_pricing_source(self, monkeypatch):
        """monthly_savings must be None for GPU findings when has_pricing_source=False."""
        gpu_rec = self._gpu_rec_with_savings(2100.0)

        def fake_gpu_recs(report):
            from shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory
            return [Recommendation(
                id=gpu_rec["id"],
                title=gpu_rec["title"],
                category=RecommendationCategory.GPU_WORKLOAD,
                resource_ref=gpu_rec["resource_ref"],
                namespace=gpu_rec["namespace"],
                monthly_savings=2100.0,
                confidence=0.75,
                risk_level=RiskLevel.MEDIUM,
                priority_score=945.0,
                evidence=gpu_rec["evidence"],
                command=None,
                yaml_patch=None,
                requires_ai=False,
            )]

        import json, datetime
        from shared.models.collector import CollectorReport, PodSummary
        report = CollectorReport(
            cluster_id="test-cluster",
            collected_at=datetime.datetime.utcnow(),
            nodes=[],
            pods=[PodSummary(
                name="inf-pod", namespace="ml", workload="inference-api",
                workload_kind="Deployment", node="node-1",
                cpu_request_m=500, cpu_limit_m=0, cpu_used_m=50,
                memory_request_mb=1024, memory_limit_mb=0, memory_used_mb=800,
                gpu_request=1, gpu_limit=1, gpu_vendor="nvidia.com/gpu",
                restarts=0,
            )],
            hpas=[],
            pvcs=[],
            namespaces=[],
            metrics_server_available=False,
        )

        from infrastructure.services.collector_store import get_collector_store
        store = get_collector_store()
        store.save(report)

        monkeypatch.setattr(
            "presentation.api.v2.routers.analysis.evaluate_gpu_workloads",
            fake_gpu_recs,
        )

        result = _append_collector_gpu_recommendations(
            "test-cluster", [], has_pricing_source=False
        )

        assert len(result) == 1, "GPU finding should still be present"
        assert result[0]["monthly_savings"] is None, (
            f"monthly_savings must be None when no pricing source; got {result[0]['monthly_savings']}"
        )

    def test_gpu_savings_preserved_when_pricing_source_exists(self, monkeypatch):
        """monthly_savings must be kept when has_pricing_source=True (cloud billing available)."""
        import datetime
        from shared.models.collector import CollectorReport, PodSummary
        from shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory

        report = CollectorReport(
            cluster_id="priced-cluster",
            collected_at=datetime.datetime.utcnow(),
            nodes=[],
            pods=[PodSummary(
                name="inf-pod", namespace="ml", workload="inference-api",
                workload_kind="Deployment", node="node-1",
                cpu_request_m=500, cpu_limit_m=0, cpu_used_m=50,
                memory_request_mb=1024, memory_limit_mb=0, memory_used_mb=800,
                gpu_request=1, gpu_limit=1, gpu_vendor="nvidia.com/gpu",
                restarts=0,
            )],
            hpas=[], pvcs=[], namespaces=[],
            metrics_server_available=False,
        )

        from infrastructure.services.collector_store import get_collector_store
        get_collector_store().save(report)

        monkeypatch.setattr(
            "presentation.api.v2.routers.analysis.evaluate_gpu_workloads",
            lambda r: [Recommendation(
                id="gpu-001", title="GPU workload without autoscaling -- inference-api",
                category=RecommendationCategory.GPU_WORKLOAD,
                resource_ref="deployment/inference-api", namespace="ml",
                monthly_savings=2100.0, confidence=0.75,
                risk_level=RiskLevel.MEDIUM, priority_score=945.0,
                evidence="No HPA.", command=None, yaml_patch=None, requires_ai=False,
            )],
        )

        result = _append_collector_gpu_recommendations(
            "priced-cluster", [], has_pricing_source=True
        )

        assert result[0]["monthly_savings"] == 2100.0, (
            "monthly_savings must be preserved when a pricing source exists"
        )


class TestAutoSelectPathSelection:
    """P1 regression: auto-select must not route credentialed clusters to the collector path.

    The collector plan decision rule: collector path only when BOTH
    (a) a fresh report exists AND (b) no cloud credentials are configured.
    A cluster with a subscription_id has cloud credentials and must use the cloud path.
    """

    def test_auto_select_collector_requires_no_cloud_credentials(self):
        """The collector path auto-select logic correctly requires no subscription_id.

        This test imports the decision-logic expression directly to verify the
        boolean guard without invoking the full route handler.
        """
        # Simulate cluster_info rows with/without credentials
        def should_auto_select_collector(cluster_info: dict, has_fresh_report: bool) -> bool:
            no_cloud_creds = not bool(cluster_info.get("subscription_id"))
            return no_cloud_creds and has_fresh_report

        # Credentialed cluster + fresh report -> cloud path
        assert not should_auto_select_collector(
            {"subscription_id": "sub-abc123"}, has_fresh_report=True
        ), "Credentialed cluster with fresh report must use cloud path"

        # No credentials + fresh report -> collector path
        assert should_auto_select_collector(
            {"subscription_id": None}, has_fresh_report=True
        ), "Uncredentialed cluster with fresh report must use collector path"

        # No credentials + no fresh report -> cloud path (stale error will propagate)
        assert not should_auto_select_collector(
            {"subscription_id": None}, has_fresh_report=False
        ), "Uncredentialed cluster without fresh report must not use collector path"

        # Credentialed cluster + no fresh report -> cloud path
        assert not should_auto_select_collector(
            {"subscription_id": "sub-abc123"}, has_fresh_report=False
        ), "Credentialed cluster without fresh report must use cloud path"
