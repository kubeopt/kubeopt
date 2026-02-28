"""
Azure Kubernetes Command Executor
===================================

Delegates kubectl execution to AzureSDKManager.execute_aks_command()
which uses the Azure Run Command API (server-side execution).
"""

import logging
from typing import Optional

from infrastructure.cloud_providers.base import KubernetesCommandExecutor
from infrastructure.cloud_providers.types import ClusterIdentifier, CloudProvider

logger = logging.getLogger(__name__)


class AzureKubernetesExecutor(KubernetesCommandExecutor):
    """Execute kubectl commands via Azure Run Command API."""

    def __init__(self):
        from infrastructure.services.azure_sdk_manager import azure_sdk_manager
        self._manager = azure_sdk_manager

    def _validate_azure_cluster(self, cluster: ClusterIdentifier) -> None:
        """Ensure cluster has required Azure fields."""
        if not cluster.subscription_id:
            raise ValueError("Azure cluster requires subscription_id")
        if not cluster.resource_group:
            raise ValueError("Azure cluster requires resource_group")

    def execute_kubectl(
        self,
        cluster: ClusterIdentifier,
        command: str,
        timeout: int = 180,
    ) -> Optional[str]:
        self._validate_azure_cluster(cluster)
        return self._manager.execute_aks_command(
            subscription_id=cluster.subscription_id,
            resource_group=cluster.resource_group,
            cluster_name=cluster.cluster_name,
            kubectl_command=command,
        )

    def execute_managed_command(
        self,
        cluster: ClusterIdentifier,
        command: str,
        timeout: int = 180,
    ) -> Optional[str]:
        """
        Execute Azure-managed commands (az aks show, az aks nodepool list, etc.)
        via the Azure SDK directly rather than CLI.
        """
        self._validate_azure_cluster(cluster)

        # For 'az aks show' style commands, delegate to SDK
        if command.startswith('az aks show'):
            return self._execute_aks_show(cluster, command)
        elif command.startswith('az aks nodepool list'):
            return self._execute_nodepool_list(cluster)

        # Fall back to running via Run Command API
        return self._manager.execute_aks_command(
            subscription_id=cluster.subscription_id,
            resource_group=cluster.resource_group,
            cluster_name=cluster.cluster_name,
            kubectl_command=command,
        )

    def test_connectivity(self, cluster: ClusterIdentifier) -> bool:
        self._validate_azure_cluster(cluster)
        try:
            result = self._manager.execute_aks_command(
                subscription_id=cluster.subscription_id,
                resource_group=cluster.resource_group,
                cluster_name=cluster.cluster_name,
                kubectl_command="kubectl version --client=false --short 2>/dev/null || kubectl version",
            )
            return result is not None
        except Exception as e:
            logger.warning(f"Connectivity test failed for {cluster.cluster_name}: {e}")
            return False

    def _execute_aks_show(self, cluster: ClusterIdentifier, command: str) -> Optional[str]:
        """Handle 'az aks show' via SDK."""
        import json
        try:
            aks_client = self._manager.get_aks_client(cluster.subscription_id)
            if not aks_client:
                return None
            managed_cluster = aks_client.managed_clusters.get(
                cluster.resource_group, cluster.cluster_name
            )
            # Return serialized result
            return json.dumps(managed_cluster.as_dict(), default=str)
        except Exception as e:
            logger.error(f"az aks show via SDK failed: {e}")
            return None

    def _execute_nodepool_list(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Handle 'az aks nodepool list' via SDK."""
        import json
        try:
            aks_client = self._manager.get_aks_client(cluster.subscription_id)
            if not aks_client:
                return None
            pools = list(aks_client.agent_pools.list(
                cluster.resource_group, cluster.cluster_name
            ))
            return json.dumps([p.as_dict() for p in pools], default=str)
        except Exception as e:
            logger.error(f"az aks nodepool list via SDK failed: {e}")
            return None
