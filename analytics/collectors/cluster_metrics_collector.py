"""
Cloud-agnostic cluster metrics collector.
Re-exports ClusterMetricsFetcher from the implementation module.
"""
from analytics.collectors.aks_realtime_metrics import ClusterMetricsFetcher, KubernetesParsingUtils

__all__ = ['ClusterMetricsFetcher', 'KubernetesParsingUtils']
