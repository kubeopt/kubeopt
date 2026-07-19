"""Tests for Task 3: RecommendationSchema serialization and chart_generator replacement."""

import pytest
from kubeopt.shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory
from kubeopt.presentation.api.v2.schemas.analysis import RecommendationSchema


# ---------------------------------------------------------------------------
# Unit: RecommendationSchema serializes correctly from a Recommendation model
# ---------------------------------------------------------------------------

def _make_rightsizing_rec() -> Recommendation:
    return Recommendation(
        id="test-abc-123",
        category=RecommendationCategory.RIGHTSIZING,
        title="Reduce CPU request for api-server",
        resource_ref="deployment/api-server",
        namespace="prod",
        monthly_savings=312.0,
        confidence=0.85,
        risk_level=RiskLevel.LOW,
        priority_score=265.2,
        evidence="p95 CPU 420m, current request 2000m (21% utilization)",
        command="kubectl set resources deployment/api-server --requests=cpu=600m -n prod",
        yaml_patch='resources:\n  requests:\n    cpu: "600m"',
        rollback="kubectl set resources deployment/api-server --requests=cpu=2000m -n prod",
        requires_ai=False,
    )


def test_recommendation_schema_serializes_from_model_dump():
    rec = _make_rightsizing_rec()
    schema = RecommendationSchema(**rec.model_dump())
    assert schema.id == "test-abc-123"
    assert schema.category == "rightsizing"
    assert schema.risk_level == "low"
    assert schema.command is not None
    assert "kubectl set resources" in schema.command
    assert schema.rollback is not None
    assert schema.requires_ai is False
    assert schema.monthly_savings == 312.0


def test_recommendation_schema_optional_fields_default_none():
    rec = Recommendation(
        id="test-idle-001",
        category=RecommendationCategory.IDLE_WORKLOAD,
        title="Review idle workload: legacy-batch",
        resource_ref="deployment/legacy-batch",
        namespace="staging",
        monthly_savings=96.0,
        confidence=0.60,
        risk_level=RiskLevel.MEDIUM,
        priority_score=34.56,
        evidence="No traffic for 14 days",
        requires_ai=False,
    )
    schema = RecommendationSchema(**rec.model_dump())
    assert schema.command is None
    assert schema.yaml_patch is None
    assert schema.rollback is None
    assert schema.risk_level == "medium"


# ---------------------------------------------------------------------------
# Unit: generate_execution_commands returns non-empty dict for rightsizing data
# ---------------------------------------------------------------------------

RIGHTSIZING_ANALYSIS = {
    "resource_utilization": {
        "workloads": [
            {
                "name": "api-server",
                "namespace": "prod",
                "kind": "Deployment",
                "cpu_requested_m": 2000,
                "cpu_p95_m": 420,
                "monthly_cost": 480.0,
            }
        ]
    },
    "hpa_recommendations": [],
    "insights": [],
    "node_recommendations": [],
}


def test_generate_execution_commands_returns_non_empty_for_rightsizing():
    from kubeopt.presentation.api.chart_generator import generate_execution_commands
    result = generate_execution_commands(RIGHTSIZING_ANALYSIS)
    assert isinstance(result, dict)
    assert len(result) > 0
    # Each value should be a kubectl command string
    for rec_id, command in result.items():
        assert isinstance(rec_id, str) and rec_id
        assert "kubectl" in command


def test_generate_execution_commands_returns_empty_for_empty_data():
    from kubeopt.presentation.api.chart_generator import generate_execution_commands
    result = generate_execution_commands({})
    assert result == {}


def test_generate_execution_commands_excludes_review_only_recs():
    """Idle workload recs have no command and must not appear in the dict."""
    from kubeopt.presentation.api.chart_generator import generate_execution_commands
    idle_data = {
        "resource_utilization": {"workloads": []},
        "hpa_recommendations": [],
        "node_recommendations": [],
        "insights": [
            {
                "type": "idle_workload",
                "workload": "legacy-batch",
                "namespace": "staging",
                "kind": "Deployment",
                "idle_days": 14,
                "estimated_savings": 96.0,
                "confidence": 0.60,
            }
        ],
    }
    result = generate_execution_commands(idle_data)
    # Idle workload recs have no command; dict must be empty
    assert result == {}
