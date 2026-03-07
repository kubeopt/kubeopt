"""
GCP Cloud Provider Adapters (Full GKE Implementation)
======================================================

Full implementations for GCP GKE support using Google Cloud Python client libraries.
Uses google-auth (ADC), google-cloud-container (GKE API), google-cloud-compute (VMs/disks/IPs),
google-cloud-monitoring (metrics), google-cloud-bigquery (cost analysis), google-cloud-logging (logs),
and google-cloud-resource-manager (project discovery).
"""

from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
from infrastructure.cloud_providers.gcp.executor import GCPKubernetesExecutor
from infrastructure.cloud_providers.gcp.metrics import GCPMetricsCollector
from infrastructure.cloud_providers.gcp.costs import GCPCostManager
from infrastructure.cloud_providers.gcp.accounts import GCPAccountManager
from infrastructure.cloud_providers.gcp.inspector import GCPInfrastructureInspector

__all__ = [
    'GCPAuthenticator',
    'GCPKubernetesExecutor',
    'GCPMetricsCollector',
    'GCPCostManager',
    'GCPAccountManager',
    'GCPInfrastructureInspector',
]
