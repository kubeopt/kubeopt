"""AWS Metrics Collector — Stub for Phase 6 (CloudWatch)."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from infrastructure.cloud_providers.base import CloudMetricsCollector
from infrastructure.cloud_providers.types import ClusterIdentifier


class AWSMetricsCollector(CloudMetricsCollector):
    def get_node_metrics(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("AWS CloudWatch metrics not yet implemented (Phase 6)")

    def get_cluster_info(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("AWS EKS cluster info not yet implemented (Phase 6)")

    def get_metric_data(self, cluster: ClusterIdentifier, metric_name: str, start_time: datetime, end_time: datetime, interval: str = "PT1H") -> Optional[List[Dict[str, Any]]]:
        raise NotImplementedError("AWS CloudWatch metric data not yet implemented (Phase 6)")
