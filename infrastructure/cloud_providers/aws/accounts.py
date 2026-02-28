"""AWS Account Manager — Stub for Phase 6 (STS + Organizations)."""

from typing import Optional, Dict, Any, List
from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import ClusterIdentifier


class AWSAccountManager(CloudAccountManager):
    def list_accounts(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("AWS account listing not yet implemented (Phase 6)")

    def validate_cluster_access(self, cluster: ClusterIdentifier) -> bool:
        raise NotImplementedError("AWS cluster access validation not yet implemented (Phase 6)")

    def discover_clusters(self, account_id: Optional[str] = None) -> List[ClusterIdentifier]:
        raise NotImplementedError("AWS EKS cluster discovery not yet implemented (Phase 6)")
