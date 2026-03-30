"""
AWS Kubernetes Command Executor
=================================

Executes kubectl commands via local subprocess (user runs `aws eks update-kubeconfig` beforehand).
Executes EKS SDK commands (describe-cluster, list-nodegroups) via boto3.
"""

import json
import logging
import re
import shlex
import subprocess
from typing import Optional

from infrastructure.cloud_providers.base import KubernetesCommandExecutor
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class AWSKubernetesExecutor(KubernetesCommandExecutor):
    """Execute kubectl via subprocess, EKS queries via boto3."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        if AWSKubernetesExecutor._auth_instance is None or not AWSKubernetesExecutor._auth_instance.is_authenticated():
            AWSKubernetesExecutor._auth_instance = AWSAuthenticator()
        return AWSKubernetesExecutor._auth_instance

    def _get_eks_client(self, cluster: ClusterIdentifier):
        auth = self._get_auth()
        if not auth.session:
            raise RuntimeError("AWS authenticator not available")
        return auth.session.client('eks', region_name=cluster.region)

    def execute_kubectl(
        self,
        cluster: ClusterIdentifier,
        command: str,
        timeout: int = 180,
    ) -> Optional[str]:
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if stderr:
                    logger.warning(f"kubectl stderr for {cluster.cluster_name}: {stderr[:200]}")
                if not result.stdout.strip():
                    return None
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"kubectl timed out after {timeout}s for {cluster.cluster_name}")
            return None
        except Exception as e:
            logger.error(f"kubectl execution failed for {cluster.cluster_name}: {e}")
            return None

    def execute_managed_command(
        self,
        cluster: ClusterIdentifier,
        command: str,
        timeout: int = 180,
    ) -> Optional[str]:
        try:
            eks = self._get_eks_client(cluster)

            if 'describe-cluster' in command or 'eks show' in command:
                resp = eks.describe_cluster(name=cluster.cluster_name)
                return json.dumps(resp['cluster'], default=str)

            if 'list-nodegroups' in command:
                resp = eks.list_nodegroups(clusterName=cluster.cluster_name)
                return json.dumps(resp['nodegroups'], default=str)

            if 'describe-nodegroup' in command:
                # Parse nodegroup name from command if present
                parts = command.split()
                ng_name = None
                for i, p in enumerate(parts):
                    if p == '--nodegroup-name' and i + 1 < len(parts):
                        ng_name = parts[i + 1]
                        break
                if ng_name:
                    resp = eks.describe_nodegroup(
                        clusterName=cluster.cluster_name,
                        nodegroupName=ng_name,
                    )
                    return json.dumps(resp['nodegroup'], default=str)

            # Fallback: run as shell command
            return self.execute_kubectl(cluster, command, timeout)
        except Exception as e:
            logger.error(f"EKS managed command failed: {e}")
            return None

    def test_connectivity(self, cluster: ClusterIdentifier) -> bool:
        try:
            result = self.execute_kubectl(
                cluster,
                "kubectl version --client=false --short",
                timeout=30,
            )
            if result is None or 'Server Version' not in (result or ''):
                result = self.execute_kubectl(
                    cluster,
                    "kubectl version",
                    timeout=30,
                )
            return result is not None and 'Server Version' in (result or '')
        except Exception as e:
            logger.warning(f"Connectivity test failed for {cluster.cluster_name}: {e}")
            return False
