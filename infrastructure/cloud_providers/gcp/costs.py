"""GCP Cost Manager — Stub for Phase 7 (BigQuery billing / Cloud Billing API)."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from infrastructure.cloud_providers.base import CloudCostManager
from infrastructure.cloud_providers.types import ClusterIdentifier


class GCPCostManager(CloudCostManager):
    def get_cluster_costs(self, cluster: ClusterIdentifier, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("GCP Cloud Billing not yet implemented (Phase 7)")

    def get_vm_pricing(self, region: str, vm_sizes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("GCP Compute Engine pricing not yet implemented (Phase 7)")

    def estimate_savings(self, cluster: ClusterIdentifier, recommendations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("GCP savings estimation not yet implemented (Phase 7)")
