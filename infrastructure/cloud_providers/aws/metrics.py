"""
AWS Metrics Collector — kubectl top + EKS describe + CloudWatch
=================================================================

Collects node/pod metrics via kubectl top (metrics-server),
cluster metadata via EKS describe-cluster, and time-series via CloudWatch.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudMetricsCollector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class AWSMetricsCollector(CloudMetricsCollector):
    """AWS metrics via kubectl top + EKS API + CloudWatch Container Insights."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        if AWSMetricsCollector._auth_instance is None or not AWSMetricsCollector._auth_instance.is_authenticated():
            AWSMetricsCollector._auth_instance = AWSAuthenticator()
        return AWSMetricsCollector._auth_instance

    def get_node_metrics(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        try:
            from infrastructure.cloud_providers.aws.executor import AWSKubernetesExecutor
            executor = AWSKubernetesExecutor()

            output = executor.execute_kubectl(
                cluster, "kubectl top nodes --no-headers", timeout=30
            )
            if not output:
                return None

            nodes = []
            for line in output.strip().split('\n'):
                parts = line.split()
                if len(parts) < 5:
                    continue
                name = parts[0]
                # Parse CPU: "250m" → millicores or "2" → cores
                cpu_str = parts[1]
                cpu_pct_str = parts[2].rstrip('%')
                mem_str = parts[3]
                mem_pct_str = parts[4].rstrip('%')

                try:
                    cpu_pct = float(cpu_pct_str)
                except ValueError:
                    cpu_pct = 0.0
                try:
                    mem_pct = float(mem_pct_str)
                except ValueError:
                    mem_pct = 0.0

                nodes.append({
                    'name': name,
                    'cpu_usage': cpu_str,
                    'cpu_percent': cpu_pct,
                    'memory_usage': mem_str,
                    'memory_percent': mem_pct,
                })

            return {'nodes': nodes}
        except Exception as e:
            logger.error(f"Failed to get node metrics for {cluster.cluster_name}: {e}")
            return None

    def get_cluster_info(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        try:
            auth = self._get_auth()
            eks = auth.session.client('eks', region_name=cluster.region)
            resp = eks.describe_cluster(name=cluster.cluster_name)
            c = resp['cluster']

            return {
                'cluster_info': {
                    'cluster_name': c['name'],
                    'kubernetes_version': c['version'],
                    'api_server_address': c.get('endpoint', ''),
                    'status': c.get('status', 'UNKNOWN'),
                    'region': cluster.region,
                    'arn': c.get('arn', ''),
                    'platform_version': c.get('platformVersion', ''),
                }
            }
        except Exception as e:
            logger.error(f"Failed to get EKS cluster info for {cluster.cluster_name}: {e}")
            return None

    def get_metric_data(
        self,
        cluster: ClusterIdentifier,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "PT1H",
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            auth = self._get_auth()
            cw = auth.session.client('cloudwatch', region_name=cluster.region)

            # Convert ISO 8601 duration to seconds (PT1H → 3600)
            period = self._parse_interval(interval)

            response = cw.get_metric_statistics(
                Namespace='ContainerInsights',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'ClusterName', 'Value': cluster.cluster_name},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=['Average'],
            )

            datapoints = []
            for dp in response.get('Datapoints', []):
                datapoints.append({
                    'timestamp': dp['Timestamp'].isoformat(),
                    'value': dp.get('Average', 0),
                })
            datapoints.sort(key=lambda d: d['timestamp'])
            return datapoints
        except Exception as e:
            logger.error(f"Failed to get CloudWatch metric {metric_name}: {e}")
            return None

    @staticmethod
    def _parse_interval(interval: str) -> int:
        """Parse ISO 8601 duration to seconds. PT1H→3600, PT5M→300, PT1D→86400."""
        interval = interval.upper()
        if not interval.startswith('PT'):
            return 3600
        rest = interval[2:]
        seconds = 0
        num = ''
        for ch in rest:
            if ch.isdigit():
                num += ch
            elif ch == 'H' and num:
                seconds += int(num) * 3600
                num = ''
            elif ch == 'M' and num:
                seconds += int(num) * 60
                num = ''
            elif ch == 'S' and num:
                seconds += int(num)
                num = ''
        return seconds if seconds > 0 else 3600
