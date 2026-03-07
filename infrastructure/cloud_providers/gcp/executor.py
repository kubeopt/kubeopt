"""GCP Kubernetes Executor — subprocess kubectl + GKE Container API for managed commands."""

import json
import logging
import subprocess
from typing import Optional

from infrastructure.cloud_providers.base import KubernetesCommandExecutor
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPKubernetesExecutor(KubernetesCommandExecutor):
    """Executes kubectl commands against GKE clusters.

    Assumes user has run: gcloud container clusters get-credentials <cluster> --zone <zone> --project <project>
    Intercepts GKE-specific commands and routes them to the Container API.
    """

    _auth_instance = None  # Class-level singleton (same pattern as AWS)

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPKubernetesExecutor._auth_instance is None or not GCPKubernetesExecutor._auth_instance.is_authenticated():
            GCPKubernetesExecutor._auth_instance = GCPAuthenticator()
        return GCPKubernetesExecutor._auth_instance

    def _get_container_client(self):
        from google.cloud import container_v1
        auth = self._get_auth()
        return container_v1.ClusterManagerClient(credentials=auth.credentials)

    def _cluster_path(self, cluster: ClusterIdentifier) -> str:
        """GKE cluster resource path: projects/{project}/locations/{location}/clusters/{name}"""
        auth = self._get_auth()
        project = cluster.project_id or auth.project_id
        location = cluster.zone or cluster.region
        return f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

    def execute_kubectl(self, cluster: ClusterIdentifier, command: str, timeout: int = 180) -> Optional[str]:
        try:
            full_command = f"kubectl {command}"
            logger.debug(f"GKE kubectl: {full_command[:100]}...")

            result = subprocess.run(
                full_command, shell=True, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"GKE kubectl failed (rc={result.returncode}): {result.stderr[:200]}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"GKE kubectl timed out after {timeout}s: {command[:80]}")
            return None
        except Exception as e:
            logger.error(f"GKE kubectl error: {e}")
            return None

    def execute_managed_command(self, cluster: ClusterIdentifier, command: str, timeout: int = 180) -> Optional[str]:
        """Intercept GKE SDK commands, fall back to kubectl."""
        try:
            cmd_lower = command.lower().strip()

            # Intercept: describe-cluster
            if 'describe-cluster' in cmd_lower or 'get-cluster' in cmd_lower:
                client = self._get_container_client()
                result = client.get_cluster(name=self._cluster_path(cluster))
                return json.dumps({
                    'name': result.name,
                    'status': result.status.name if result.status else 'UNKNOWN',
                    'location': result.location,
                    'currentMasterVersion': result.current_master_version,
                    'currentNodeVersion': result.current_node_version,
                    'endpoint': result.endpoint,
                    'nodePoolCount': len(result.node_pools),
                }, indent=2)

            # Intercept: list-nodepools
            if 'list-nodepool' in cmd_lower or 'list-node-pool' in cmd_lower:
                client = self._get_container_client()
                result = client.list_node_pools(parent=self._cluster_path(cluster))
                pools = []
                for np in result.node_pools:
                    pools.append({
                        'name': np.name,
                        'machineType': np.config.machine_type if np.config else None,
                        'diskSizeGb': np.config.disk_size_gb if np.config else None,
                        'nodeCount': np.initial_node_count,
                        'status': np.status.name if np.status else 'UNKNOWN',
                        'autoscaling': {
                            'enabled': np.autoscaling.enabled if np.autoscaling else False,
                            'minNodeCount': np.autoscaling.min_node_count if np.autoscaling else 0,
                            'maxNodeCount': np.autoscaling.max_node_count if np.autoscaling else 0,
                        } if np.autoscaling else None,
                    })
                return json.dumps(pools, indent=2)

            # Intercept: describe-nodepool
            if 'describe-nodepool' in cmd_lower or 'describe-node-pool' in cmd_lower:
                # Extract nodepool name from command (last token)
                parts = command.strip().split()
                pool_name = parts[-1] if parts else None
                if pool_name:
                    client = self._get_container_client()
                    pool_path = f"{self._cluster_path(cluster)}/nodePools/{pool_name}"
                    result = client.get_node_pool(name=pool_path)
                    return json.dumps({
                        'name': result.name,
                        'machineType': result.config.machine_type if result.config else None,
                        'diskSizeGb': result.config.disk_size_gb if result.config else None,
                        'initialNodeCount': result.initial_node_count,
                        'status': result.status.name if result.status else 'UNKNOWN',
                        'version': result.version,
                        'autoscaling': {
                            'enabled': result.autoscaling.enabled if result.autoscaling else False,
                            'minNodeCount': result.autoscaling.min_node_count if result.autoscaling else 0,
                            'maxNodeCount': result.autoscaling.max_node_count if result.autoscaling else 0,
                        } if result.autoscaling else None,
                    }, indent=2)

            # Fallback to kubectl
            return self.execute_kubectl(cluster, command, timeout)

        except Exception as e:
            logger.error(f"GKE managed command failed: {e}")
            return None

    def test_connectivity(self, cluster: ClusterIdentifier) -> bool:
        """Test cluster connectivity via GKE API (describe_cluster)."""
        try:
            client = self._get_container_client()
            result = client.get_cluster(name=self._cluster_path(cluster))
            return result.status.name in ('RUNNING', 'RECONCILING', 'PROVISIONING')
        except Exception as e:
            logger.warning(f"GKE connectivity test failed: {e}")
            return False
