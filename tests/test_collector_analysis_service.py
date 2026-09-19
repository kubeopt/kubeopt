"""Tests for CollectorAnalysisService -- inventory observations without cloud credentials."""

import json
import os
import sys
import pytest
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("LOCAL_DEV", "true")

from shared.models.collector import CollectorReport, PVCSummary, NamespaceSummary
from shared.models.recommendation import RecommendationCategory

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> CollectorReport:
    return CollectorReport(**json.loads((FIXTURES / name).read_text()))


def _svc():
    from infrastructure.services.collector_analysis import CollectorAnalysisService
    return CollectorAnalysisService()


def _report_with_unbound_pvc() -> CollectorReport:
    r = _load("collector_report_small.json")
    pvc = PVCSummary(name="lost-claim", namespace="staging", capacity_gb=50.0, phase="Pending")
    return r.model_copy(update={"pvcs": list(r.pvcs) + [pvc]})


def _report_with_empty_namespace() -> CollectorReport:
    r = _load("collector_report_small.json")
    empty_ns = NamespaceSummary(name="stale-team", pod_count=0)
    return r.model_copy(update={"namespaces": list(r.namespaces) + [empty_ns]})


# ---------------------------------------------------------------------------
# Cloud isolation -- execution path must make no cloud calls
# ---------------------------------------------------------------------------

class TestCloudIsolation:
    def test_run_completes_without_importing_cloud_adapters(self):
        """
        Run the service on a real CollectorReport with no mocks and verify that
        no cloud adapter module is loaded as a side effect. The service must not
        import cloud packages even transitively.
        """
        r = _load("collector_report_small.json")
        modules_before = set(sys.modules.keys())

        _svc().run(r)

        modules_after = set(sys.modules.keys())
        new_imports = modules_after - modules_before
        forbidden_prefixes = (
            "infrastructure.adapters",
            "infrastructure.services.account_manager",
            "shared.kubernetes_data_cache",
            "assessment.background_processor",
        )
        violations = [
            m for m in new_imports
            if any(m.startswith(p) for p in forbidden_prefixes)
        ]
        assert not violations, (
            f"CollectorAnalysisService.run() caused cloud adapter imports: {violations}"
        )

    def test_run_produces_no_gpu_category_findings(self):
        """
        GPU findings are appended by the API layer, not by this service.
        run() must never return a GPU_WORKLOAD finding regardless of the report.
        """
        r = _load("collector_report_gpu_workloads.json")
        recs = _svc().run(r)
        gpu_recs = [rec for rec in recs if rec.category == RecommendationCategory.GPU_WORKLOAD]
        assert gpu_recs == [], (
            f"Service must not produce GPU findings; API layer handles them: "
            f"{[(r.title, r.command) for r in gpu_recs]}"
        )

    def test_run_accepts_report_with_no_cloud_cluster_object(self):
        """run() takes only a CollectorReport -- no cluster DB object or cloud ident needed."""
        r = _load("collector_report_small.json")
        recs = _svc().run(r)
        assert isinstance(recs, list)


# ---------------------------------------------------------------------------
# No destructive actions
# ---------------------------------------------------------------------------

class TestNoDestructiveActions:
    def test_no_findings_carry_kubectl_delete(self):
        """Regression: GPU fixture previously produced 'kubectl delete pod' via gpu_evaluator."""
        r = _load("collector_report_gpu_workloads.json")
        r = r.model_copy(update={
            "pvcs": list(r.pvcs) + [PVCSummary(name="lost-claim", namespace="staging",
                                               capacity_gb=50.0, phase="Pending")],
            "namespaces": list(r.namespaces) + [NamespaceSummary(name="stale-team", pod_count=0)],
        })
        for rec in _svc().run(r):
            assert rec.command is None or "delete" not in rec.command, (
                f"Finding {rec.title!r} must not emit a deletion command: {rec.command!r}"
            )

    def test_empty_namespace_is_informational_only(self):
        r = _report_with_empty_namespace()
        recs = _svc().run(r)
        ns_recs = [rec for rec in recs if "stale-team" in rec.resource_ref]
        assert len(ns_recs) == 1
        assert ns_recs[0].command is None
        assert ns_recs[0].rollback is None
        assert "may still contain" in ns_recs[0].evidence.lower() or "inspect" in ns_recs[0].evidence.lower()

    def test_unbound_pvc_is_informational_only(self):
        r = _report_with_unbound_pvc()
        recs = _svc().run(r)
        pvc_recs = [rec for rec in recs if "lost-claim" in rec.resource_ref]
        assert len(pvc_recs) == 1
        assert pvc_recs[0].command is None
        assert "verify" in pvc_recs[0].evidence.lower() or "may be" in pvc_recs[0].evidence.lower()

    def test_rightsizing_carries_no_kubectl_command(self):
        r = _load("collector_report_small.json")
        assert r.metrics_server_available
        recs = _svc().run(r)
        rs_recs = [rec for rec in recs if rec.category == RecommendationCategory.RIGHTSIZING]
        for rec in rs_recs:
            assert rec.command is None, (
                f"Right-sizing from single snapshot must not emit a command: {rec.command!r}"
            )

    def test_hpa_gap_carries_no_kubectl_command(self):
        r = _load("collector_report_small.json")
        recs = _svc().run(r)
        hpa_recs = [rec for rec in recs if rec.category == RecommendationCategory.HPA]
        for rec in hpa_recs:
            assert rec.command is None
            assert rec.yaml_patch is None


# ---------------------------------------------------------------------------
# No unsupported savings
# ---------------------------------------------------------------------------

class TestNoUnsupportedSavings:
    def test_all_findings_have_none_savings(self):
        """
        Every finding from CollectorAnalysisService must carry monthly_savings=None.
        No savings can be established from a single snapshot regardless of pricing.
        Includes PVC, namespace, rightsizing, and HPA findings explicitly.
        GPU findings must be absent entirely (delegated to API layer, not this service).
        """
        r = _report_with_unbound_pvc()
        r = r.model_copy(update={
            "namespaces": list(r.namespaces) + [NamespaceSummary(name="empty-ns", pod_count=0)]
        })
        recs = _svc().run(r, node_monthly_cost=None)
        assert recs, "Expected at least one finding from the combined fixture"
        for rec in recs:
            assert rec.category != RecommendationCategory.GPU_WORKLOAD, (
                f"GPU findings must not appear in service output: {rec.title!r}"
            )
            assert rec.monthly_savings is None, (
                f"{rec.title!r} (category={rec.category}) must have None savings, "
                f"got {rec.monthly_savings}"
            )

    def test_pvc_finding_has_none_savings_regardless_of_node_pricing(self):
        """
        Storage cost cannot be derived from node pricing. PVC findings carry
        None savings even when node_monthly_cost is provided.
        """
        r = _report_with_unbound_pvc()
        for rec in _svc().run(r, node_monthly_cost=500.0):
            if rec.category == RecommendationCategory.STORAGE:
                assert rec.monthly_savings is None, (
                    f"PVC savings must not be derived from node pricing: {rec.monthly_savings}"
                )

    def test_rightsizing_has_none_savings(self):
        """Single snapshot does not establish recoverable spend."""
        r = _load("collector_report_small.json")
        for rec in _svc().run(r):
            if rec.category == RecommendationCategory.RIGHTSIZING:
                assert rec.monthly_savings is None

    def test_hpa_finding_has_none_savings(self):
        """No traffic variance data -- savings cannot be attributed to adding an HPA."""
        r = _load("collector_report_small.json")
        for rec in _svc().run(r):
            if rec.category == RecommendationCategory.HPA:
                assert rec.monthly_savings is None


# ---------------------------------------------------------------------------
# Metrics-server absent
# ---------------------------------------------------------------------------

class TestMetricsServerAbsent:
    def test_no_rightsizing_when_metrics_unavailable(self):
        r = _load("collector_report_small.json")
        r = r.model_copy(update={"metrics_server_available": False})
        recs = _svc().run(r)
        assert not any(rec.category == RecommendationCategory.RIGHTSIZING for rec in recs), (
            "Right-sizing requires live CPU metrics; must be suppressed when metrics-server absent"
        )

    def test_hpa_and_namespace_findings_still_surface_without_metrics(self):
        """HPA gaps and empty namespaces do not need metrics-server data."""
        r = _load("collector_report_small.json")
        r = r.model_copy(update={
            "metrics_server_available": False,
            "namespaces": list(r.namespaces) + [NamespaceSummary(name="empty-ns", pod_count=0)],
        })
        recs = _svc().run(r)
        categories = {rec.category for rec in recs}
        assert RecommendationCategory.HPA in categories or RecommendationCategory.IDLE_WORKLOAD in categories


# ---------------------------------------------------------------------------
# Single-snapshot disclaimer in rightsizing evidence
# ---------------------------------------------------------------------------

class TestRightsizingEvidence:
    def test_rightsizing_evidence_notes_single_snapshot_limitation(self):
        r = _load("collector_report_small.json")
        recs = _svc().run(r)
        rs_recs = [rec for rec in recs if rec.category == RecommendationCategory.RIGHTSIZING]
        assert rs_recs, "Expected at least one rightsizing observation from small fixture"
        for rec in rs_recs:
            evidence_lower = rec.evidence.lower()
            assert "single" in evidence_lower or "snapshot" in evidence_lower or "historical" in evidence_lower, (
                f"Right-sizing evidence must note single-snapshot limitation: {rec.evidence!r}"
            )

    def test_rightsizing_title_is_observational_not_prescriptive(self):
        """Title must say what was observed, not instruct a change."""
        r = _load("collector_report_small.json")
        for rec in _svc().run(r):
            if rec.category == RecommendationCategory.RIGHTSIZING:
                assert "reduce" not in rec.title.lower(), (
                    f"Right-sizing title must not prescribe a change: {rec.title!r}"
                )


# ---------------------------------------------------------------------------
# HPA observation is non-prescriptive
# ---------------------------------------------------------------------------

class TestHPAObservation:
    def test_hpa_evidence_does_not_prescribe_scaling_policy(self):
        r = _load("collector_report_small.json")
        for rec in _svc().run(r):
            if rec.category == RecommendationCategory.HPA:
                evidence_lower = rec.evidence.lower()
                assert "review" in evidence_lower or "consider" in evidence_lower or "whether" in evidence_lower, (
                    f"HPA finding must not prescribe a scaling policy: {rec.evidence!r}"
                )


# ---------------------------------------------------------------------------
# Stale-report contract: service runs but caller owns freshness gate
# ---------------------------------------------------------------------------

class TestStaleReportContract:
    def test_service_runs_with_old_report_caller_owns_freshness(self):
        """
        CollectorAnalysisService does not check freshness -- that is the path
        selector's responsibility. This test documents the contract: the service
        accepts any report; freshness enforcement lives in background_processor.
        """
        r = _load("collector_report_small.json")
        old = r.model_copy(update={"collected_at": datetime.utcnow() - timedelta(hours=2)})
        recs = _svc().run(old)
        assert isinstance(recs, list)
