"""GCP Infrastructure Inspector (Stub)"""

from typing import Optional
from infrastructure.cloud_providers.base import CloudInfrastructureInspector
from infrastructure.cloud_providers.types import ClusterIdentifier


class GCPInfrastructureInspector(CloudInfrastructureInspector):
    """Placeholder — all methods raise NotImplementedError until GKE implementation."""

    def get_cluster_details(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_node_pools(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_cluster_version(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_cluster_identity(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_cluster_region(self, cluster: ClusterIdentifier) -> str:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_node_resource_scope(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_log_analytics_resources(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_application_monitoring(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_observability_costs(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_consumption_usage(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_orphaned_disks(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_unused_public_ips(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_load_balancer_analysis(self, cluster: ClusterIdentifier) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_storage_tier_analysis(self, cluster: ClusterIdentifier, pvc_data: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")

    def get_network_waste_analysis(self, cluster: ClusterIdentifier, services_data: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError("GCP GKE inspector not yet implemented")
