import pytest
from kubeopt.assessment.command_generator import generate_recommendations
from kubeopt.shared.models.recommendation import RiskLevel, RecommendationCategory


RIGHTSIZING_DATA = {
    "node_recommendations": [],
    "hpa_recommendations": [],
    "insights": [],
    "resource_utilization": {
        "workloads": [
            {
                "name": "api-server",
                "namespace": "prod",
                "kind": "Deployment",
                "cpu_requested_m": 2000,
                "cpu_p95_m": 420,
                "memory_requested_mb": 1024,
                "memory_p95_mb": 310,
                "monthly_cost": 480.0,
            }
        ]
    },
    "workload_costs": [],
}

HPA_DATA = {
    "node_recommendations": [],
    "hpa_recommendations": [
        {
            "workload": "worker",
            "namespace": "default",
            "kind": "Deployment",
            "current_replicas": 5,
            "recommended_min": 2,
            "recommended_max": 10,
            "cpu_target_percent": 70,
            "estimated_savings": 200.0,
            "confidence": 0.80,
        }
    ],
    "insights": [],
    "resource_utilization": {"workloads": []},
    "workload_costs": [],
}

IDLE_DATA = {
    "node_recommendations": [],
    "hpa_recommendations": [],
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
    "resource_utilization": {"workloads": []},
    "workload_costs": [],
}

NODE_POOL_HIGH_CONFIDENCE = {
    "node_recommendations": [
        {
            "node_pool": "standard-d4s",
            "namespace": "default",
            "current_vm": "Standard_D4s_v3",
            "recommended_vm": "Standard_D2s_v3",
            "estimated_savings": 540.0,
            "confidence": 0.92,
            "cloud_provider": "azure",
        }
    ],
    "hpa_recommendations": [],
    "insights": [],
    "resource_utilization": {"workloads": []},
    "workload_costs": [],
}

NODE_POOL_LOW_CONFIDENCE = {
    "node_recommendations": [
        {
            "node_pool": "standard-d8s",
            "namespace": "default",
            "current_vm": "Standard_D8s_v3",
            "recommended_vm": "Standard_D4s_v3",
            "estimated_savings": 900.0,
            "confidence": 0.55,  # below 0.80 threshold
            "cloud_provider": "azure",
        }
    ],
    "hpa_recommendations": [],
    "insights": [],
    "resource_utilization": {"workloads": []},
    "workload_costs": [],
}


def test_rightsizing_generates_command_when_utilization_below_threshold():
    recs = generate_recommendations(RIGHTSIZING_DATA)
    rightsizing = [r for r in recs if r.category == "rightsizing"]
    assert len(rightsizing) == 1
    rec = rightsizing[0]
    assert rec.command is not None
    assert "kubectl set resources" in rec.command
    assert "api-server" in rec.command
    assert rec.requires_ai is False
    assert rec.risk_level == "low"
    assert rec.monthly_savings > 0


def test_rightsizing_command_contains_namespace():
    recs = generate_recommendations(RIGHTSIZING_DATA)
    rightsizing = [r for r in recs if r.category == "rightsizing"]
    assert "-n prod" in rightsizing[0].command


def test_rightsizing_includes_rollback():
    recs = generate_recommendations(RIGHTSIZING_DATA)
    rightsizing = [r for r in recs if r.category == "rightsizing"]
    assert rightsizing[0].rollback is not None
    assert "kubectl set resources" in rightsizing[0].rollback
    assert "--requests=cpu=" in rightsizing[0].rollback


def test_hpa_recommendation_generates_autoscale_command():
    recs = generate_recommendations(HPA_DATA)
    hpa = [r for r in recs if r.category == "hpa"]
    assert len(hpa) == 1
    assert "kubectl autoscale" in hpa[0].command
    assert "worker" in hpa[0].command
    assert hpa[0].rollback is not None


def test_idle_workload_is_review_only_no_command():
    recs = generate_recommendations(IDLE_DATA)
    idle = [r for r in recs if r.category == "idle_workload"]
    assert len(idle) == 1
    assert idle[0].command is None  # review only, never destructive
    assert idle[0].risk_level == "medium"
    assert idle[0].evidence is not None


def test_node_pool_high_confidence_generates_review_recommendation():
    recs = generate_recommendations(NODE_POOL_HIGH_CONFIDENCE)
    node = [r for r in recs if r.category == "node_pool"]
    assert len(node) == 1
    # node pool changes are review type even at high confidence
    assert node[0].command is None or "review" in node[0].title.lower()


def test_node_pool_low_confidence_excluded():
    recs = generate_recommendations(NODE_POOL_LOW_CONFIDENCE)
    node = [r for r in recs if r.category == "node_pool"]
    # below 0.80 confidence: not included
    assert len(node) == 0


def test_recommendations_sorted_by_priority_score_descending():
    combined = {
        **RIGHTSIZING_DATA,
        "hpa_recommendations": HPA_DATA["hpa_recommendations"],
    }
    recs = generate_recommendations(combined)
    scores = [r.priority_score for r in recs]
    assert scores == sorted(scores, reverse=True)


def test_empty_analysis_data_returns_empty_list():
    recs = generate_recommendations({})
    assert recs == []


def test_all_recommendations_have_ids():
    combined = {**RIGHTSIZING_DATA, "hpa_recommendations": HPA_DATA["hpa_recommendations"]}
    recs = generate_recommendations(combined)
    ids = [r.id for r in recs]
    assert all(ids)
    assert len(ids) == len(set(ids))  # all unique


def test_recommendation_ids_are_stable_across_calls():
    recs1 = generate_recommendations(RIGHTSIZING_DATA)
    recs2 = generate_recommendations(RIGHTSIZING_DATA)
    assert [r.id for r in recs1] == [r.id for r in recs2]
