"""
AWS Cloud Provider Adapters
=============================

Full EKS implementation via boto3: authenticator (STS), executor (kubectl + EKS SDK),
accounts (cluster discovery), metrics (CloudWatch + kubectl top), inspector (15 methods),
and costs (Cost Explorer + Pricing API).
"""

from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
from infrastructure.cloud_providers.aws.executor import AWSKubernetesExecutor
from infrastructure.cloud_providers.aws.metrics import AWSMetricsCollector
from infrastructure.cloud_providers.aws.costs import AWSCostManager
from infrastructure.cloud_providers.aws.accounts import AWSAccountManager
from infrastructure.cloud_providers.aws.inspector import AWSInfrastructureInspector

__all__ = [
    'AWSAuthenticator',
    'AWSKubernetesExecutor',
    'AWSMetricsCollector',
    'AWSCostManager',
    'AWSAccountManager',
    'AWSInfrastructureInspector',
]
