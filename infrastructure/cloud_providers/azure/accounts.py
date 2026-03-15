"""
Azure Account Adapter
======================

Delegates to AzureSubscriptionManager for account/subscription management.
"""

import logging
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import ClusterIdentifier, CloudProvider

logger = logging.getLogger(__name__)


class AzureAccountAdapter(CloudAccountManager):
    """Wraps AzureSubscriptionManager for the CloudAccountManager interface."""

    def __init__(self):
        from infrastructure.services.subscription_manager import azure_subscription_manager
        self._manager = azure_subscription_manager

    def list_accounts(self) -> List[Dict[str, Any]]:
        try:
            subscriptions = self._manager.get_available_subscriptions()
            return [
                {
                    'id': sub.subscription_id,
                    'name': sub.subscription_name,
                    'provider': 'azure',
                    'tenant_id': sub.tenant_id,
                    'state': sub.state,
                    'is_default': sub.is_default,
                }
                for sub in subscriptions
            ]
        except Exception as e:
            logger.error(f"Failed to list Azure subscriptions: {e}")
            return []

    def validate_cluster_access(
        self,
        cluster: ClusterIdentifier,
    ) -> bool:
        if not cluster.subscription_id or not cluster.resource_group:
            logger.error("Azure cluster requires subscription_id and resource_group")
            return False

        try:
            result = self._manager.validate_cluster_access(
                subscription_id=cluster.subscription_id,
                resource_group=cluster.resource_group,
                cluster_name=cluster.cluster_name,
            )
            if isinstance(result, dict):
                return result.get('valid', result.get('accessible', False))
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to validate cluster access for {cluster.cluster_name}: {e}")
            return False

    def find_cluster_account(
        self,
        cluster_name: str,
        resource_group: Optional[str] = None,
    ) -> Optional[str]:
        try:
            return self._manager.find_cluster_subscription(resource_group or '', cluster_name)
        except Exception as e:
            logger.error(f"Failed to find account for cluster {cluster_name}: {e}")
            return None

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        try:
            info = self._manager.get_subscription_info(account_id)
            if not info:
                return None
            return {
                'id': info.subscription_id,
                'name': info.subscription_name,
                'provider': 'azure',
                'tenant_id': getattr(info, 'tenant_id', None),
                'state': getattr(info, 'state', None),
            }
        except Exception as e:
            logger.error(f"Failed to get account info for {account_id}: {e}")
            return None

    def execute_with_account_context(self, account_id: str, func, *args, **kwargs):
        return self._manager.execute_with_subscription_context(account_id, func, *args, **kwargs)

    def discover_clusters(
        self,
        account_id: Optional[str] = None,
    ) -> List[ClusterIdentifier]:
        clusters = []
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager

            # If a specific subscription is given, search only that one
            subscription_ids = [account_id] if account_id else []
            if not subscription_ids:
                subs = self._manager.get_available_subscriptions()
                subscription_ids = [s.subscription_id for s in subs]

            for sub_id in subscription_ids:
                try:
                    aks_client = azure_sdk_manager.get_aks_client(sub_id)
                    if not aks_client:
                        continue
                    for cluster in aks_client.managed_clusters.list():
                        # Extract resource group from the cluster's ID
                        rg = cluster.id.split('/')[4] if cluster.id else None
                        location = cluster.location or ''
                        clusters.append(ClusterIdentifier(
                            provider=CloudProvider.AZURE,
                            cluster_name=cluster.name,
                            region=location,
                            resource_group=rg,
                            subscription_id=sub_id,
                        ))
                except Exception as e:
                    logger.warning(f"Failed to discover clusters in subscription {sub_id[:8]}...: {e}")

        except Exception as e:
            logger.error(f"Failed to discover Azure clusters: {e}")

        return clusters
