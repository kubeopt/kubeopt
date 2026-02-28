"""
Cloud Provider Abstraction Layer
================================

Multi-cloud support for KubeOpt: Azure AKS, AWS EKS, GCP GKE.
Each provider implements the base ABCs defined in base.py.
"""

from infrastructure.cloud_providers.types import CloudProvider, ClusterIdentifier
from infrastructure.cloud_providers.registry import ProviderRegistry

__all__ = [
    'CloudProvider',
    'ClusterIdentifier',
    'ProviderRegistry',
]
