import pytest
from kubeopt.shared.models.recommendation import (
    Recommendation, RiskLevel, RecommendationCategory
)


def test_recommendation_requires_ai_defaults_false():
    rec = Recommendation(
        id="rec-001",
        category=RecommendationCategory.RIGHTSIZING,
        title="Reduce CPU request for api-server",
        resource_ref="deployment/api-server",
        namespace="prod",
        monthly_savings=312.0,
        confidence=0.87,
        risk_level=RiskLevel.LOW,
        priority_score=271.44,
        evidence="p95 CPU usage 420m, current request 2000m (21% utilization)",
        command="kubectl set resources deployment/api-server --requests=cpu=600m -n prod",
        yaml_patch='resources:\n  requests:\n    cpu: "600m"',
        rollback="kubectl set resources deployment/api-server --requests=cpu=2000m -n prod",
    )
    assert rec.requires_ai is False


def test_recommendation_review_type_has_no_command():
    rec = Recommendation(
        id="rec-002",
        category=RecommendationCategory.IDLE_WORKLOAD,
        title="Review idle workload: legacy-batch",
        resource_ref="deployment/legacy-batch",
        namespace="staging",
        monthly_savings=96.0,
        confidence=0.60,
        risk_level=RiskLevel.MEDIUM,
        priority_score=28.8,
        evidence="0 requests/day for 14 days, CPU < 5m",
        command=None,
        yaml_patch=None,
        rollback=None,
        requires_ai=False,
    )
    assert rec.command is None
    assert rec.risk_level == RiskLevel.MEDIUM


def test_priority_score_is_float():
    rec = Recommendation(
        id="rec-003",
        category=RecommendationCategory.HPA,
        title="Add HPA to worker deployment",
        resource_ref="deployment/worker",
        namespace="default",
        monthly_savings=200.0,
        confidence=0.75,
        risk_level=RiskLevel.LOW,
        priority_score=150.0,
        evidence="CPU spikes to 900m but base usage is 150m",
        command='kubectl autoscale deployment worker --cpu-percent=70 --min=2 --max=10 -n default',
        yaml_patch=None,
        rollback="kubectl delete hpa worker -n default",
    )
    assert isinstance(rec.priority_score, float)


def test_risk_level_enum_values():
    assert RiskLevel.LOW == "low"
    assert RiskLevel.MEDIUM == "medium"
    assert RiskLevel.HIGH == "high"


def test_category_enum_values():
    assert RecommendationCategory.RIGHTSIZING == "rightsizing"
    assert RecommendationCategory.IDLE_WORKLOAD == "idle_workload"
    assert RecommendationCategory.HPA == "hpa"
    assert RecommendationCategory.NODE_POOL == "node_pool"
    assert RecommendationCategory.STORAGE == "storage"
