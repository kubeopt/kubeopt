"""
Azure Cloud Provider Adapters
==============================

Thin wrappers around existing Azure SDK integrations:
  - AzureSDKManager (authenticator.py)
  - AzureMetricCollector (metrics.py)
  - EnhancedAKSCostProcessor + VMPricingService (costs.py)
  - AzureSubscriptionManager (accounts.py)
  - execute_aks_command (executor.py)
"""

from infrastructure.cloud_providers.azure.authenticator import AzureAuthenticator
from infrastructure.cloud_providers.azure.executor import AzureKubernetesExecutor
from infrastructure.cloud_providers.azure.metrics import AzureMetricsAdapter
from infrastructure.cloud_providers.azure.costs import AzureCostAdapter
from infrastructure.cloud_providers.azure.accounts import AzureAccountAdapter

__all__ = [
    'AzureAuthenticator',
    'AzureKubernetesExecutor',
    'AzureMetricsAdapter',
    'AzureCostAdapter',
    'AzureAccountAdapter',
]
