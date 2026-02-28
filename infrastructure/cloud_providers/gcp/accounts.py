"""GCP Account Manager — Stub for Phase 7 (Resource Manager projects.list)."""

from typing import Optional, Dict, Any, List
from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import ClusterIdentifier


class GCPAccountManager(CloudAccountManager):
    def list_accounts(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("GCP project listing not yet implemented (Phase 7)")

    def validate_cluster_access(self, cluster: ClusterIdentifier) -> bool:
        raise NotImplementedError("GCP cluster access validation not yet implemented (Phase 7)")

    def discover_clusters(self, account_id: Optional[str] = None) -> List[ClusterIdentifier]:
        raise NotImplementedError("GCP GKE cluster discovery not yet implemented (Phase 7)")
