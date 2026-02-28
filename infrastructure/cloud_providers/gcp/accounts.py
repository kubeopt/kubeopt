"""GCP Account Manager — Stub for Phase 7 (Resource Manager projects.list)."""

from typing import Optional, Dict, Any, List
from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import ClusterIdentifier


class GCPAccountManager(CloudAccountManager):
    def list_accounts(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("GCP project listing not yet implemented (Session 8)")

    def validate_cluster_access(self, cluster: ClusterIdentifier) -> bool:
        raise NotImplementedError("GCP cluster access validation not yet implemented (Session 8)")

    def discover_clusters(self, account_id: Optional[str] = None) -> List[ClusterIdentifier]:
        raise NotImplementedError("GCP GKE cluster discovery not yet implemented (Session 8)")

    def find_cluster_account(self, cluster_name: str, resource_group: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError("GCP cluster account detection not yet implemented (Session 8)")

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("GCP account info not yet implemented (Session 8)")

    def execute_with_account_context(self, account_id: str, func, *args, **kwargs):
        raise NotImplementedError("GCP account context execution not yet implemented (Session 8)")
