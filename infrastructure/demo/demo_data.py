"""
Seed data for demo mode (KUBEOPT_DEMO=true).

Three realistic clusters across AWS, GCP, and Azure with pre-computed analysis
results. No cloud credentials or network access required.
"""

import os


def is_demo_mode() -> bool:
    return os.getenv("KUBEOPT_DEMO", "").lower() in ("1", "true", "yes")


DEMO_CLUSTERS = [
    {
        "cluster_id": "demo-prod-eks-us-east-1",
        "cluster_name": "prod-eks-us-east-1",
        "cloud_provider": "aws",
        "region": "us-east-1",
        "subscription_id": "demo-aws-account",
        "resource_group": "prod-k8s",
        "node_count": 12,
        "status": "active",
        "last_analysis": "2026-06-19T08:00:00Z",
        "optimization_score": 0.61,
        "total_cost": 4800.0,
        "potential_savings": 1680.0,
    },
    {
        "cluster_id": "demo-staging-gke-eu-west1",
        "cluster_name": "staging-gke-eu-west1",
        "cloud_provider": "gcp",
        "region": "europe-west1",
        "subscription_id": "demo-gcp-project",
        "resource_group": "staging-k8s",
        "node_count": 6,
        "status": "active",
        "last_analysis": "2026-06-19T08:05:00Z",
        "optimization_score": 0.72,
        "total_cost": 1200.0,
        "potential_savings": 396.0,
    },
    {
        "cluster_id": "demo-dev-aks-westus2",
        "cluster_name": "dev-aks-westus2",
        "cloud_provider": "azure",
        "region": "westus2",
        "subscription_id": "demo-azure-sub",
        "resource_group": "dev-k8s-rg",
        "node_count": 4,
        "status": "active",
        "last_analysis": "2026-06-19T08:10:00Z",
        "optimization_score": 0.48,
        "total_cost": 960.0,
        "potential_savings": 480.0,
    },
]

_DEMO_CLUSTER_MAP = {c["cluster_id"]: c for c in DEMO_CLUSTERS}


def get_demo_cluster(cluster_id: str):
    return _DEMO_CLUSTER_MAP.get(cluster_id)


def get_demo_analysis_status(cluster_id: str) -> dict:
    return {
        "session_key": cluster_id,
        "status": "completed",
        "progress": 100.0,
        "current_phase": "Complete",
        "message": "Analysis complete (demo data)",
        "started_at": "2026-06-19T08:00:00Z",
        "completed_at": "2026-06-19T08:02:30Z",
        "error": None,
    }


_CHART_DATA = {
    "demo-prod-eks-us-east-1": {
        "total_cost": 4800.0,
        "cpu_gap": 38.2,
        "memory_gap": 29.5,
        "hpa_efficiency": 61.0,
        "namespace_count": 8,
        "workload_count": 34,
        "cost_breakdown": [
            {"name": "Compute", "value": 3360.0},
            {"name": "Storage", "value": 720.0},
            {"name": "Network", "value": 480.0},
            {"name": "Support", "value": 240.0},
        ],
        "cost_categories": [
            {"category": "Idle compute", "amount": 960.0},
            {"category": "Oversized requests", "amount": 480.0},
            {"category": "Unused storage", "amount": 240.0},
        ],
        "resource_utilization": [
            {"name": "CPU", "requested": 72.0, "used": 33.8, "limit": 100.0},
            {"name": "Memory", "requested": 68.0, "used": 38.5, "limit": 100.0},
        ],
        "savings_breakdown": {
            "right_sizing": 840.0,
            "idle_workload_removal": 480.0,
            "storage_cleanup": 240.0,
            "hpa_tuning": 120.0,
        },
        "namespace_costs": [
            {"namespace": "production", "cost": 2160.0},
            {"namespace": "monitoring", "cost": 960.0},
            {"namespace": "data-pipeline", "cost": 720.0},
            {"namespace": "kube-system", "cost": 480.0},
            {"namespace": "logging", "cost": 240.0},
            {"namespace": "staging", "cost": 240.0},
        ],
        "workload_costs": [
            {"workload": "api-server", "namespace": "production", "cost": 840.0, "savings_opportunity": 336.0},
            {"workload": "data-processor", "namespace": "data-pipeline", "cost": 720.0, "savings_opportunity": 288.0},
            {"workload": "prometheus", "namespace": "monitoring", "cost": 480.0, "savings_opportunity": 192.0},
            {"workload": "ml-worker", "namespace": "production", "cost": 456.0, "savings_opportunity": 0.0},
            {"workload": "redis-cache", "namespace": "production", "cost": 360.0, "savings_opportunity": 144.0},
            {"workload": "nginx-ingress", "namespace": "production", "cost": 240.0, "savings_opportunity": 96.0},
        ],
        "insights": [
            {"category": "Right-sizing", "message": "6 deployments request 3x more CPU than their 30-day peak. Reducing requests saves $840/mo."},
            {"category": "Idle workloads", "message": "data-processor ran at under 5% CPU utilization for 18 of the last 30 days."},
            {"category": "Resource limits", "message": "11 pods in kube-system and logging have no memory limits set, creating eviction risk."},
            {"category": "HPA", "message": "api-server HPA triggers at 80% CPU but average load is 34%. Lower the threshold to 55% to scale earlier."},
            {"category": "Storage", "message": "4 PersistentVolumeClaims totalling 400 GiB are unbound to any running pod."},
        ],
        "trend_data": [
            {"month": "Jan", "cost": 4200.0},
            {"month": "Feb", "cost": 4350.0},
            {"month": "Mar", "cost": 4500.0},
            {"month": "Apr", "cost": 4620.0},
            {"month": "May", "cost": 4750.0},
            {"month": "Jun", "cost": 4800.0},
        ],
        "node_recommendations": [
            {"current_node_type": "m5.2xlarge", "recommended_node_type": "m5.xlarge", "node_count": 4, "monthly_savings": 480.0, "confidence": 0.89},
            {"current_node_type": "m5.2xlarge", "recommended_node_type": "m5a.2xlarge", "node_count": 8, "monthly_savings": 192.0, "confidence": 0.81},
        ],
        "hpa_comparison": [],
    },
    "demo-staging-gke-eu-west1": {
        "total_cost": 1200.0,
        "cpu_gap": 41.0,
        "memory_gap": 22.0,
        "hpa_efficiency": 72.0,
        "namespace_count": 5,
        "workload_count": 18,
        "cost_breakdown": [
            {"name": "Compute", "value": 840.0},
            {"name": "Storage", "value": 216.0},
            {"name": "Network", "value": 144.0},
        ],
        "cost_categories": [
            {"category": "Oversized requests", "amount": 264.0},
            {"category": "Idle workloads", "amount": 132.0},
        ],
        "resource_utilization": [
            {"name": "CPU", "requested": 78.0, "used": 37.0, "limit": 100.0},
            {"name": "Memory", "requested": 65.0, "used": 43.0, "limit": 100.0},
        ],
        "savings_breakdown": {
            "right_sizing": 216.0,
            "idle_workload_removal": 132.0,
            "storage_cleanup": 48.0,
        },
        "namespace_costs": [
            {"namespace": "staging", "cost": 600.0},
            {"namespace": "monitoring", "cost": 360.0},
            {"namespace": "kube-system", "cost": 240.0},
        ],
        "workload_costs": [
            {"workload": "staging-api", "namespace": "staging", "cost": 360.0, "savings_opportunity": 144.0},
            {"workload": "prometheus", "namespace": "monitoring", "cost": 240.0, "savings_opportunity": 96.0},
            {"workload": "staging-worker", "namespace": "staging", "cost": 240.0, "savings_opportunity": 96.0},
        ],
        "insights": [
            {"category": "Right-sizing", "message": "staging-api requests 4 CPU cores but peaks at 1.2. Reduce to 1.5 cores to save $144/mo."},
            {"category": "Idle workloads", "message": "3 workloads in staging have not received traffic in 14+ days."},
            {"category": "Node pools", "message": "Consider using n2-standard-4 Spot instances for staging to reduce compute cost by 60%."},
        ],
        "trend_data": [
            {"month": "Jan", "cost": 980.0},
            {"month": "Feb", "cost": 1020.0},
            {"month": "Mar", "cost": 1080.0},
            {"month": "Apr", "cost": 1120.0},
            {"month": "May", "cost": 1180.0},
            {"month": "Jun", "cost": 1200.0},
        ],
        "node_recommendations": [
            {"current_node_type": "n1-standard-4", "recommended_node_type": "n2-standard-4-spot", "node_count": 6, "monthly_savings": 288.0, "confidence": 0.76},
        ],
        "hpa_comparison": [],
    },
    "demo-dev-aks-westus2": {
        "total_cost": 960.0,
        "cpu_gap": 55.0,
        "memory_gap": 47.0,
        "hpa_efficiency": 48.0,
        "namespace_count": 4,
        "workload_count": 22,
        "cost_breakdown": [
            {"name": "Compute", "value": 720.0},
            {"name": "Storage", "value": 144.0},
            {"name": "Network", "value": 96.0},
        ],
        "cost_categories": [
            {"category": "Idle compute", "amount": 288.0},
            {"category": "Oversized requests", "amount": 144.0},
            {"category": "Unused storage", "amount": 48.0},
        ],
        "resource_utilization": [
            {"name": "CPU", "requested": 82.0, "used": 27.0, "limit": 100.0},
            {"name": "Memory", "requested": 74.0, "used": 27.0, "limit": 100.0},
        ],
        "savings_breakdown": {
            "right_sizing": 240.0,
            "idle_workload_removal": 144.0,
            "spot_instances": 96.0,
        },
        "namespace_costs": [
            {"namespace": "dev", "cost": 600.0},
            {"namespace": "test", "cost": 240.0},
            {"namespace": "kube-system", "cost": 120.0},
        ],
        "workload_costs": [
            {"workload": "dev-api", "namespace": "dev", "cost": 360.0, "savings_opportunity": 216.0},
            {"workload": "dev-worker", "namespace": "dev", "cost": 240.0, "savings_opportunity": 144.0},
            {"workload": "test-runner", "namespace": "test", "cost": 144.0, "savings_opportunity": 72.0},
            {"workload": "dev-db", "namespace": "dev", "cost": 120.0, "savings_opportunity": 0.0},
        ],
        "insights": [
            {"category": "Resource limits", "message": "19 of 22 pods have no CPU or memory limits. This causes noisy-neighbor issues and unpredictable evictions."},
            {"category": "Idle workloads", "message": "dev cluster runs 24/7 but team hours are 09:00-18:00. A scale-to-zero schedule saves $288/mo."},
            {"category": "Right-sizing", "message": "dev-api requests 8 CPU but the dev environment has never used more than 2.1."},
            {"category": "Spot instances", "message": "Dev workloads tolerate interruption. Switching to Spot/Preemptible nodes cuts compute by 60%."},
        ],
        "trend_data": [
            {"month": "Jan", "cost": 820.0},
            {"month": "Feb", "cost": 840.0},
            {"month": "Mar", "cost": 880.0},
            {"month": "Apr", "cost": 910.0},
            {"month": "May", "cost": 940.0},
            {"month": "Jun", "cost": 960.0},
        ],
        "node_recommendations": [
            {"current_node_type": "Standard_D4s_v3", "recommended_node_type": "Standard_D2s_v3", "node_count": 4, "monthly_savings": 240.0, "confidence": 0.91},
        ],
        "hpa_comparison": [],
    },
}


def get_demo_chart_data(cluster_id: str) -> dict:
    return _CHART_DATA.get(cluster_id, {})
