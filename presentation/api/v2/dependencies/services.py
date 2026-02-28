"""
Service dependency functions for FastAPI Depends().

Each function reads from the global ServiceContainer — no inline imports in routers.
"""

from typing import Any, Dict

from presentation.api.v2.services import get_container


def get_cluster_manager():
    return get_container().cluster_manager


def get_auth_manager():
    return get_container().auth_manager


def get_api_security():
    return get_container().api_security


def get_settings_manager():
    return get_container().settings_manager


def get_license_validator_dep():
    return get_container().license_validator


def get_scheduler():
    return get_container().scheduler


def get_external_api_client():
    return get_container().external_api_client


def get_cpu_report_exporter():
    return get_container().cpu_report_exporter


def get_alerts_manager():
    return get_container().alerts_manager


def get_provider_registry():
    return get_container().provider_registry


def get_cloud_provider() -> str:
    return get_container().cloud_provider


def get_analysis_results() -> Dict[str, Any]:
    return get_container().analysis_results


def get_analysis_cache() -> Dict[str, Any]:
    return get_container().analysis_cache


def get_kubernetes_dashboard():
    """Fresh KubernetesDashboard per request (not cached)."""
    from presentation.api.kubernetes_dashboard import PodsDashboardAPI, WorkloadsDashboardAPI, ResourcesDashboardAPI

    class _Dashboard:
        def __init__(self):
            self.pods = PodsDashboardAPI()
            self.workloads = WorkloadsDashboardAPI()
            self.resources = ResourcesDashboardAPI()

        def get_pods_overview(self, cluster_id, subscription_id):
            return self.pods.get_pods_overview(cluster_id, subscription_id)

        def get_workloads_overview(self, cluster_id, subscription_id):
            return self.workloads.get_workloads_overview(cluster_id, subscription_id)

        def get_resources_overview(self, cluster_id, subscription_id):
            return self.resources.get_resources_overview(cluster_id, subscription_id)

        def get_unified_dashboard(self, cluster_id, subscription_id):
            return {
                "cluster_id": cluster_id,
                "pods": self.get_pods_overview(cluster_id, subscription_id),
                "workloads": self.get_workloads_overview(cluster_id, subscription_id),
                "resources": self.get_resources_overview(cluster_id, subscription_id),
            }

    return _Dashboard()


def get_account_manager():
    """Cloud-agnostic account manager from provider registry."""
    registry = get_container().provider_registry
    return registry.get_account_manager()
