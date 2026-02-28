"""
GCP Cloud Provider Adapters (Stubs)
====================================

Placeholder implementations for GCP GKE support.
All methods raise NotImplementedError until Phase 7.
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
