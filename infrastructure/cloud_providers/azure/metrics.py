"""
Azure Metrics Adapter
======================

Delegates to AzureMetricCollector for Azure Monitor metrics.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudMetricsCollector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class AzureMetricsAdapter(CloudMetricsCollector):
    """Wraps AzureMetricCollector for the CloudMetricsCollector interface."""

    def _get_collector(self, cluster: ClusterIdentifier):
        """Create an AzureMetricCollector for the given cluster."""
        from shared.azure_metric_collector import AzureMetricCollector
        return AzureMetricCollector(
            subscription_id=cluster.subscription_id,
            resource_group=cluster.resource_group,
            cluster_name=cluster.cluster_name,
        )

    def get_node_metrics(
        self,
        cluster: ClusterIdentifier,
    ) -> Optional[Dict[str, Any]]:
        try:
            collector = self._get_collector(cluster)
            return collector.get_node_metrics()
        except Exception as e:
            logger.error(f"Failed to get node metrics for {cluster.cluster_name}: {e}")
            return None

    def get_cluster_info(
        self,
        cluster: ClusterIdentifier,
    ) -> Optional[Dict[str, Any]]:
        try:
            collector = self._get_collector(cluster)
            return collector.get_cluster_info()
        except Exception as e:
            logger.error(f"Failed to get cluster info for {cluster.cluster_name}: {e}")
            return None

    def get_metric_data(
        self,
        cluster: ClusterIdentifier,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "PT1H",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Query Azure Monitor time-series data.

        This delegates to the Monitor Management client from AzureSDKManager.
        """
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            monitor_client = azure_sdk_manager.get_monitor_client(cluster.subscription_id)
            if not monitor_client:
                return None

            # Build the resource URI for the AKS cluster
            resource_uri = (
                f"/subscriptions/{cluster.subscription_id}"
                f"/resourceGroups/{cluster.resource_group}"
                f"/providers/Microsoft.ContainerService/managedClusters/{cluster.cluster_name}"
            )

            result = monitor_client.metrics.list(
                resource_uri=resource_uri,
                metricnames=metric_name,
                timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                interval=interval,
                aggregation="Average",
            )

            data_points = []
            for metric in result.value:
                for ts in metric.timeseries:
                    for dp in ts.data:
                        if dp.average is not None:
                            data_points.append({
                                'timestamp': dp.time_stamp,
                                'value': dp.average,
                            })
            return data_points

        except Exception as e:
            logger.error(f"Failed to get metric data for {cluster.cluster_name}: {e}")
            return None
