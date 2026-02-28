"""
AWS Account Manager — STS Identity + EKS Cluster Discovery
=============================================================

Uses STS for account identity, EKS API for cluster discovery,
and optionally Organizations API for multi-account setups.
"""

import logging
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import ClusterIdentifier, CloudProvider

logger = logging.getLogger(__name__)


class AWSAccountManager(CloudAccountManager):
    """AWS account and EKS cluster management via boto3."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        if AWSAccountManager._auth_instance is None or not AWSAccountManager._auth_instance.is_authenticated():
            AWSAccountManager._auth_instance = AWSAuthenticator()
            if not AWSAccountManager._auth_instance.is_authenticated():
                raise RuntimeError("AWS authentication failed — set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return AWSAccountManager._auth_instance

    def list_accounts(self) -> List[Dict[str, Any]]:
        try:
            auth = self._get_auth()
            session = auth.session
            account_id = auth.account_id
            region = auth.region

            accounts = [{
                'id': account_id,
                'name': f'AWS Account {account_id}',
                'provider': 'aws',
                'region': region,
            }]

            # Try Organizations API for multi-account (graceful fallback)
            try:
                org_client = session.client('organizations', region_name='us-east-1')
                paginator = org_client.get_paginator('list_accounts')
                org_accounts = []
                for page in paginator.paginate():
                    for acct in page['Accounts']:
                        if acct['Id'] != account_id:
                            org_accounts.append({
                                'id': acct['Id'],
                                'name': acct.get('Name', f'AWS Account {acct["Id"]}'),
                                'provider': 'aws',
                                'status': acct.get('Status', 'UNKNOWN'),
                            })
                accounts.extend(org_accounts)
            except Exception:
                pass  # Organizations not available or no permissions

            return accounts
        except Exception as e:
            logger.warning(f"Failed to list AWS accounts: {e}")
            return []

    def validate_cluster_access(self, cluster: ClusterIdentifier) -> bool:
        try:
            auth = self._get_auth()
            eks = auth.session.client('eks', region_name=cluster.region)
            eks.describe_cluster(name=cluster.cluster_name)
            return True
        except Exception as e:
            logger.warning(f"Cannot access EKS cluster {cluster.cluster_name}: {e}")
            return False

    # Regions to scan for EKS clusters during discovery
    _EKS_REGIONS = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2', 'ap-south-1',
        'ca-central-1', 'sa-east-1',
    ]

    def discover_clusters(self, account_id: Optional[str] = None) -> List[ClusterIdentifier]:
        try:
            auth = self._get_auth()
            session = auth.session
            current_account = auth.account_id

            # Scan multiple regions — one account can have clusters in different regions
            clusters = []
            for region in self._EKS_REGIONS:
                try:
                    eks = session.client('eks', region_name=region)
                    cluster_names = eks.list_clusters()['clusters']
                    for name in cluster_names:
                        try:
                            desc = eks.describe_cluster(name=name)['cluster']
                            clusters.append(ClusterIdentifier(
                                provider=CloudProvider.AWS,
                                cluster_name=name,
                                region=region,
                                account_id=current_account,
                                cluster_arn=desc.get('arn'),
                            ))
                        except Exception as e:
                            logger.warning(f"Could not describe cluster {name} in {region}: {e}")
                except Exception:
                    pass  # Region may not be enabled or no EKS access

            if not clusters:
                logger.info(f"No EKS clusters found across {len(self._EKS_REGIONS)} regions")
            else:
                regions_found = set(c.region for c in clusters)
                logger.info(f"Discovered {len(clusters)} EKS cluster(s) across regions: {', '.join(sorted(regions_found))}")

            return clusters
        except Exception as e:
            logger.warning(f"Failed to discover EKS clusters: {e}")
            return []

    def find_cluster_account(
        self,
        cluster_name: str,
        resource_group: Optional[str] = None,
    ) -> Optional[str]:
        try:
            auth = self._get_auth()
            # Try default region first, then scan others
            for region in [auth.region] + [r for r in self._EKS_REGIONS if r != auth.region]:
                try:
                    eks = auth.session.client('eks', region_name=region)
                    eks.describe_cluster(name=cluster_name)
                    return auth.account_id
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        try:
            auth = self._get_auth()
            current = auth.account_id

            info = {
                'id': account_id,
                'name': f'AWS Account {account_id}',
                'provider': 'aws',
            }

            if account_id == current:
                # Try to get account alias
                try:
                    iam = auth.session.client('iam')
                    aliases = iam.list_account_aliases().get('AccountAliases', [])
                    if aliases:
                        info['name'] = aliases[0]
                except Exception:
                    pass

            return info
        except Exception as e:
            logger.warning(f"Failed to get account info for {account_id}: {e}")
            return None

    def execute_with_account_context(
        self,
        account_id: str,
        func,
        *args,
        **kwargs,
    ) -> Any:
        # Single-account for now — just execute directly
        return func(*args, **kwargs)
