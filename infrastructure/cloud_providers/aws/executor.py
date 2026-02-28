"""AWS Kubernetes Executor — Stub for Phase 6 (SSM send-command / direct kubectl)."""

from typing import Optional
from infrastructure.cloud_providers.base import KubernetesCommandExecutor
from infrastructure.cloud_providers.types import ClusterIdentifier


class AWSKubernetesExecutor(KubernetesCommandExecutor):
    def execute_kubectl(self, cluster: ClusterIdentifier, command: str, timeout: int = 180) -> Optional[str]:
        raise NotImplementedError("AWS EKS kubectl execution not yet implemented (Phase 6)")

    def execute_managed_command(self, cluster: ClusterIdentifier, command: str, timeout: int = 180) -> Optional[str]:
        raise NotImplementedError("AWS EKS managed commands not yet implemented (Phase 6)")

    def test_connectivity(self, cluster: ClusterIdentifier) -> bool:
        raise NotImplementedError("AWS EKS connectivity test not yet implemented (Phase 6)")
