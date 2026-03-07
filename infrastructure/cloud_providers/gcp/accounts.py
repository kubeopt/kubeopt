"""GCP Account Manager — Resource Manager projects + GKE cluster discovery."""

import logging
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import CloudProvider, ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPAccountManager(CloudAccountManager):
    """Manages GCP project access and GKE cluster discovery."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPAccountManager._auth_instance is None or not GCPAccountManager._auth_instance.is_authenticated():
            GCPAccountManager._auth_instance = GCPAuthenticator()
        return GCPAccountManager._auth_instance

    def list_accounts(self) -> List[Dict[str, Any]]:
        """List accessible GCP projects."""
        try:
            auth = self._get_auth()
            accounts = []

            # Always include the default project
            if auth.project_id:
                accounts.append({
                    'id': auth.project_id,
                    'name': auth.project_id,
                    'provider': 'gcp',
                    'is_default': True,
                })

            # Try to list additional projects via Resource Manager
            try:
                from google.cloud import resourcemanager_v3

                client = resourcemanager_v3.ProjectsClient(credentials=auth.credentials)
                request = resourcemanager_v3.SearchProjectsRequest()
                for project in client.search_projects(request=request):
                    if project.project_id != auth.project_id and project.state.name == 'ACTIVE':
                        accounts.append({
                            'id': project.project_id,
                            'name': project.display_name or project.project_id,
                            'provider': 'gcp',
                            'is_default': False,
                        })
            except Exception as e:
                logger.debug(f"Resource Manager project listing unavailable: {e}")

            return accounts

        except Exception as e:
            logger.error(f"GCP list_accounts error: {e}")
            return []

    def validate_cluster_access(self, cluster: ClusterIdentifier) -> bool:
        """Verify we can access this GKE cluster."""
        try:
            from google.cloud import container_v1

            auth = self._get_auth()
            client = container_v1.ClusterManagerClient(credentials=auth.credentials)
            project = cluster.project_id or auth.project_id
            location = cluster.zone or cluster.region

            if location:
                name = f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"
                result = client.get_cluster(name=name)
                return result.status.name in ('RUNNING', 'RECONCILING', 'PROVISIONING')

            # No location — use wildcard discovery to find the cluster
            parent = f"projects/{project}/locations/-"
            response = client.list_clusters(parent=parent)
            for c in response.clusters:
                if c.name == cluster.cluster_name:
                    logger.info(f"Found GKE cluster '{c.name}' in location '{c.location}' via discovery")
                    return c.status.name in ('RUNNING', 'RECONCILING', 'PROVISIONING')

            logger.warning(f"GKE cluster '{cluster.cluster_name}' not found in project '{project}'")
            return False

        except Exception as e:
            logger.warning(f"GKE cluster access validation failed: {e}")
            return False

    def discover_clusters(self, account_id: Optional[str] = None) -> List[ClusterIdentifier]:
        """Discover all GKE clusters in a project using locations/- wildcard."""
        try:
            from google.cloud import container_v1

            auth = self._get_auth()
            project = account_id or auth.project_id
            if not project:
                logger.warning("No project ID available for cluster discovery")
                return []

            client = container_v1.ClusterManagerClient(credentials=auth.credentials)

            # locations/- is the wildcard for ALL locations (zones + regions)
            parent = f"projects/{project}/locations/-"
            response = client.list_clusters(parent=parent)

            clusters = []
            for c in response.clusters:
                # Extract region from location (e.g. 'us-central1-a' -> 'us-central1')
                location = c.location
                region = '-'.join(location.split('-')[:2]) if location.count('-') >= 2 else location

                clusters.append(ClusterIdentifier(
                    provider=CloudProvider.GCP,
                    cluster_name=c.name,
                    region=region,
                    project_id=project,
                    zone=location,
                ))

            if clusters:
                locations = set(c.zone for c in clusters)
                logger.info(f"Discovered {len(clusters)} GKE cluster(s) in project '{project}' "
                            f"across {len(locations)} location(s)")
            else:
                logger.info(f"No GKE clusters found in project '{project}'")

            return clusters

        except Exception as e:
            logger.error(f"GKE cluster discovery error: {e}")
            return []

    def find_cluster_account(self, cluster_name: str, resource_group: Optional[str] = None) -> Optional[str]:
        """Find which project contains a GKE cluster by name."""
        try:
            accounts = self.list_accounts()
            for account in accounts:
                clusters = self.discover_clusters(account['id'])
                for c in clusters:
                    if c.cluster_name == cluster_name:
                        logger.info(f"Found GKE cluster '{cluster_name}' in project '{account['id']}'")
                        return account['id']

            logger.warning(f"GKE cluster '{cluster_name}' not found in any accessible project")
            return None

        except Exception as e:
            logger.error(f"GKE find_cluster_account error: {e}")
            return None

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get GCP project metadata."""
        try:
            from google.cloud import resourcemanager_v3

            auth = self._get_auth()
            client = resourcemanager_v3.ProjectsClient(credentials=auth.credentials)
            project = client.get_project(name=f"projects/{account_id}")

            return {
                'id': project.project_id,
                'name': project.display_name or project.project_id,
                'provider': 'gcp',
                'state': project.state.name if project.state else 'UNKNOWN',
            }

        except Exception as e:
            logger.warning(f"GCP project info unavailable for '{account_id}': {e}")
            return {
                'id': account_id,
                'name': account_id,
                'provider': 'gcp',
            }

    def execute_with_account_context(self, account_id: str, func, *args, **kwargs):
        """Execute function within project context (pass-through for GCP)."""
        return func(*args, **kwargs)
