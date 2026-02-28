"""
AWS Cloud Provider Adapters (Stubs)
====================================

Placeholder implementations for AWS EKS support.
All methods raise NotImplementedError until Phase 6.
"""

from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
from infrastructure.cloud_providers.aws.executor import AWSKubernetesExecutor
from infrastructure.cloud_providers.aws.metrics import AWSMetricsCollector
from infrastructure.cloud_providers.aws.costs import AWSCostManager
from infrastructure.cloud_providers.aws.accounts import AWSAccountManager

__all__ = [
    'AWSAuthenticator',
    'AWSKubernetesExecutor',
    'AWSMetricsCollector',
    'AWSCostManager',
    'AWSAccountManager',
]
