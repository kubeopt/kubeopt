"""GCP Metrics Collector — Stub for Phase 7 (Cloud Monitoring)."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from infrastructure.cloud_providers.base import CloudMetricsCollector
from infrastructure.cloud_providers.types import ClusterIdentifier


class GCPMetricsCollector(CloudMetricsCollector):
    def get_node_metrics(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("GCP Cloud Monitoring metrics not yet implemented (Phase 7)")

    def get_cluster_info(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("GCP GKE cluster info not yet implemented (Phase 7)")

    def get_metric_data(self, cluster: ClusterIdentifier, metric_name: str, start_time: datetime, end_time: datetime, interval: str = "PT1H") -> Optional[List[Dict[str, Any]]]:
        raise NotImplementedError("GCP Cloud Monitoring metric data not yet implemented (Phase 7)")
