"""GCP Metrics Collector — kubectl top nodes + Cloud Monitoring API."""

import json
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudMetricsCollector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPMetricsCollector(CloudMetricsCollector):
    """Collects metrics from GKE clusters via kubectl and Cloud Monitoring."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPMetricsCollector._auth_instance is None or not GCPMetricsCollector._auth_instance.is_authenticated():
            GCPMetricsCollector._auth_instance = GCPAuthenticator()
        return GCPMetricsCollector._auth_instance

    def _get_executor(self):
        from infrastructure.cloud_providers.gcp.executor import GCPKubernetesExecutor
        return GCPKubernetesExecutor()

    def get_node_metrics(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        """Get node CPU/memory metrics via kubectl top nodes."""
        try:
            executor = self._get_executor()
            output = executor.execute_kubectl(cluster, "top nodes --no-headers")
            if not output:
                return None

            nodes = []
            for line in output.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5:
                    name = parts[0]
                    cpu_raw = parts[1]    # e.g. "250m" or "1"
                    cpu_pct = parts[2].replace('%', '')
                    mem_raw = parts[3]    # e.g. "1024Mi"
                    mem_pct = parts[4].replace('%', '')

                    nodes.append({
                        'name': name,
                        'cpu_usage': cpu_raw,
                        'cpu_percent': float(cpu_pct),
                        'memory_usage': mem_raw,
                        'memory_percent': float(mem_pct),
                    })

            return {'nodes': nodes}

        except Exception as e:
            logger.error(f"GKE node metrics error: {e}")
            return None

    def get_cluster_info(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        """Get cluster info via GKE Container API."""
        try:
            from google.cloud import container_v1

            auth = self._get_auth()
            client = container_v1.ClusterManagerClient(credentials=auth.credentials)
            project = cluster.project_id or auth.project_id
            location = cluster.zone or cluster.region
            name = f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

            result = client.get_cluster(name=name)

            return {
                'cluster_info': {
                    'cluster_name': result.name,
                    'kubernetes_version': result.current_master_version,
                    'status': result.status.name if result.status else 'UNKNOWN',
                    'region': result.location,
                    'endpoint': result.endpoint,
                    'node_pool_count': len(result.node_pools),
                    'network': result.network,
                    'subnetwork': result.subnetwork,
                    'self_link': result.self_link,
                }
            }

        except Exception as e:
            logger.error(f"GKE cluster info error: {e}")
            return None

    def get_metric_data(self, cluster: ClusterIdentifier, metric_name: str,
                        start_time: datetime, end_time: datetime,
                        interval: str = "PT1H") -> Optional[List[Dict[str, Any]]]:
        """Query Cloud Monitoring for time-series data."""
        try:
            from google.cloud import monitoring_v3
            from google.protobuf.timestamp_pb2 import Timestamp

            auth = self._get_auth()
            project = cluster.project_id or auth.project_id
            client = monitoring_v3.MetricServiceClient(credentials=auth.credentials)

            project_name = f"projects/{project}"
            period_seconds = self._parse_interval(interval)

            # Map common metric names to Cloud Monitoring metric types
            metric_type = self._resolve_metric_type(metric_name)

            interval_pb = monitoring_v3.TimeInterval()
            start_ts = Timestamp()
            start_ts.FromDatetime(start_time)
            end_ts = Timestamp()
            end_ts.FromDatetime(end_time)
            interval_pb.start_time = start_ts
            interval_pb.end_time = end_ts

            aggregation = monitoring_v3.Aggregation()
            aggregation.alignment_period = {"seconds": period_seconds}
            aggregation.per_series_aligner = monitoring_v3.Aggregation.Aligner.ALIGN_MEAN

            results = client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type = "{metric_type}" AND '
                              f'resource.labels.cluster_name = "{cluster.cluster_name}"',
                    "interval": interval_pb,
                    "aggregation": aggregation,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )

            data_points = []
            for ts in results:
                for point in ts.points:
                    data_points.append({
                        'timestamp': point.interval.end_time.isoformat(),
                        'value': point.value.double_value if point.value._pb.HasField('double_value') else point.value.int64_value,
                    })

            # Sort by timestamp
            data_points.sort(key=lambda x: x['timestamp'])
            return data_points

        except Exception as e:
            logger.error(f"GKE metric data error: {e}")
            return None

    @staticmethod
    def _parse_interval(interval: str) -> int:
        """Parse ISO 8601 duration to seconds. PT1H -> 3600, PT5M -> 300, PT1D -> 86400."""
        match = re.match(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', interval, re.IGNORECASE)
        if not match:
            return 3600  # default 1 hour

        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)
        return days * 86400 + hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _resolve_metric_type(metric_name: str) -> str:
        """Map common metric names to GCP Cloud Monitoring metric types."""
        metric_map = {
            'cpu': 'kubernetes.io/node/cpu/allocatable_utilization',
            'cpu_utilization': 'kubernetes.io/node/cpu/allocatable_utilization',
            'memory': 'kubernetes.io/node/memory/allocatable_utilization',
            'memory_utilization': 'kubernetes.io/node/memory/allocatable_utilization',
            'disk': 'kubernetes.io/node/ephemeral_storage/used_bytes',
            'network_in': 'kubernetes.io/node/network/received_bytes_count',
            'network_out': 'kubernetes.io/node/network/sent_bytes_count',
            'pod_count': 'kubernetes.io/node/pid_used',
        }
        return metric_map.get(metric_name.lower(), metric_name)
