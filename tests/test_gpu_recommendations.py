"""Tests for GPU/AI workload cost recommendations -- Sprint 3."""

import json
import os
import pytest
from pathlib import Path

os.environ.setdefault("LOCAL_DEV", "true")

from shared.models.collector import CollectorReport
from shared.models.recommendation import RecommendationCategory

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> CollectorReport:
    return CollectorReport(**json.loads((FIXTURES / name).read_text()))


def _recs(report: CollectorReport):
    from assessment.gpu_evaluator import evaluate_gpu_workloads
    return evaluate_gpu_workloads(report)


# ---------------------------------------------------------------------------
# Fixture parsing
# ---------------------------------------------------------------------------

class TestGPUFixture:
    def test_gpu_fixture_parses(self):
        r = _load("collector_report_gpu_workloads.json")
        assert r.cluster_id == "gpu-cluster-001"
        assert len(r.pods) == 8

    def test_gpu_pods_have_gpu_fields(self):
        r = _load("collector_report_gpu_workloads.json")
        gpu_pods = [p for p in r.pods if p.gpu_request > 0]
        assert len(gpu_pods) == 6
        assert all(p.gpu_vendor is not None for p in gpu_pods)

    def test_non_gpu_pods_have_zero_gpu(self):
        r = _load("collector_report_gpu_workloads.json")
        cpu_pods = [p for p in r.pods if p.gpu_request == 0]
        assert len(cpu_pods) == 2
        assert all(p.gpu_vendor is None for p in cpu_pods)

    def test_existing_fixtures_still_parse(self):
        for name in ["collector_report_small.json", "collector_report_idle_namespace.json",
                     "collector_report_hpa_missing.json"]:
            r = _load(name)
            for pod in r.pods:
                assert pod.gpu_request == 0   # default


# ---------------------------------------------------------------------------
# GPU recommendation generation
# ---------------------------------------------------------------------------

class TestGPUEvaluator:
    def test_gpu_fixture_produces_recommendations(self):
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        assert len(recs) > 0

    def test_all_recommendations_are_gpu_category(self):
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        assert all(rec.category == RecommendationCategory.GPU_WORKLOAD for rec in recs)

    def test_non_gpu_cluster_produces_no_gpu_recommendations(self):
        r = _load("collector_report_small.json")
        recs = _recs(r)
        assert recs == []

    def test_idle_gpu_pod_detected(self):
        """finetune-job-stale: 4 GPUs requested, CPU used only 8m (trivial)."""
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        idle_recs = [rec for rec in recs if "idle" in rec.title.lower() or "stale" in rec.evidence.lower() or "finetune-job-stale" in rec.resource_ref]
        assert len(idle_recs) >= 1

    def test_gpu_without_hpa_detected(self):
        """inference-api is a Deployment with GPU pods and no HPA."""
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        hpa_recs = [rec for rec in recs if "hpa" in rec.title.lower() or "autoscal" in rec.title.lower()]
        assert len(hpa_recs) >= 1
        assert any("inference-api" in rec.resource_ref for rec in hpa_recs)

    def test_gpu_missing_limits_detected(self):
        """inference-api pods have gpu_limit=1 but cpu_limit=0 and memory_limit=0."""
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        limit_recs = [rec for rec in recs if "limit" in rec.title.lower()]
        assert len(limit_recs) >= 1

    def test_well_run_gpu_pod_not_flagged_as_idle(self):
        """well-run-gpu-trainer: CPU used 7200m of 8000m requested -- active, should not be flagged idle."""
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        idle_recs = [rec for rec in recs if "well-run-gpu-trainer" in rec.resource_ref]
        assert idle_recs == []

    def test_each_recommendation_has_required_fields(self):
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        for rec in recs:
            assert rec.id
            assert rec.title
            # namespace is empty string for cluster-scoped findings (node pools)
            assert rec.namespace is not None
            assert rec.resource_ref
            assert rec.evidence
            assert 0.0 <= rec.confidence <= 1.0
            assert rec.monthly_savings >= 0.0
            assert rec.priority_score >= 0.0

    def test_recommendations_are_deterministic(self):
        r = _load("collector_report_gpu_workloads.json")
        recs1 = _recs(r)
        recs2 = _recs(r)
        assert [rec.id for rec in recs1] == [rec.id for rec in recs2]

    def test_low_gpu_node_occupancy_detected(self):
        """gpu-node-a100-2: only 4000m CPU requested on a 24000m node with GPU pods -- under-filled."""
        r = _load("collector_report_gpu_workloads.json")
        recs = _recs(r)
        occupancy_recs = [rec for rec in recs if "occupanc" in rec.title.lower() or "node pool" in rec.title.lower() or "utiliz" in rec.title.lower()]
        assert len(occupancy_recs) >= 1
