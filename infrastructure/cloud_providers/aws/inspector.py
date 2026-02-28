"""
AWS Infrastructure Inspector — EKS Metadata, CloudWatch Logs, EC2 Waste
==========================================================================

15 methods: cluster metadata (6), observability (4), waste detection (5).
get_cluster_details() maps EKS nodegroups to the agent_pool_profiles schema
that analysis_engine.py expects.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from infrastructure.cloud_providers.base import CloudInfrastructureInspector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class AWSInfrastructureInspector(CloudInfrastructureInspector):
    """AWS EKS implementation of infrastructure inspection."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        if AWSInfrastructureInspector._auth_instance is None or not AWSInfrastructureInspector._auth_instance.is_authenticated():
            AWSInfrastructureInspector._auth_instance = AWSAuthenticator()
            if not AWSInfrastructureInspector._auth_instance.is_authenticated():
                raise RuntimeError("AWS authentication failed — set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return AWSInfrastructureInspector._auth_instance

    def _get_eks_client(self, cluster: ClusterIdentifier):
        auth = self._get_auth()
        return auth.session.client('eks', region_name=cluster.region)

    def _describe_cluster(self, cluster: ClusterIdentifier) -> dict:
        eks = self._get_eks_client(cluster)
        return eks.describe_cluster(name=cluster.cluster_name)['cluster']

    def _list_nodegroups(self, cluster: ClusterIdentifier) -> list:
        eks = self._get_eks_client(cluster)
        names = eks.list_nodegroups(clusterName=cluster.cluster_name).get('nodegroups', [])
        nodegroups = []
        for ng_name in names:
            try:
                resp = eks.describe_nodegroup(
                    clusterName=cluster.cluster_name,
                    nodegroupName=ng_name,
                )
                nodegroups.append(resp['nodegroup'])
            except Exception as e:
                logger.warning(f"Could not describe nodegroup {ng_name}: {e}")
        return nodegroups

    # --- Cluster metadata ---

    def get_cluster_details(self, cluster: ClusterIdentifier) -> Optional[str]:
        """
        Returns JSON compatible with analysis_engine.py expectations.
        Maps EKS nodegroups to agent_pool_profiles schema with:
        location, current_kubernetes_version, kubernetes_version, agent_pool_profiles[]
        """
        try:
            c = self._describe_cluster(cluster)
            nodegroups = self._list_nodegroups(cluster)

            agent_pool_profiles = []
            for ng in nodegroups:
                scaling = ng.get('scalingConfig', {})
                instance_types = ng.get('instanceTypes', [])
                instance_type = instance_types[0] if instance_types else 'unknown'
                capacity_type = ng.get('capacityType', 'ON_DEMAND')

                agent_pool_profiles.append({
                    'name': ng.get('nodegroupName', 'unknown'),
                    'vm_size': instance_type,
                    'count': scaling.get('desiredSize', 0),
                    'min_count': scaling.get('minSize', 0),
                    'max_count': scaling.get('maxSize', 0),
                    'enable_auto_scaling': scaling.get('minSize', 0) != scaling.get('maxSize', 0),
                    'os_type': ng.get('amiType', 'AL2_x86_64'),
                    'mode': 'System' if ng.get('labels', {}).get('role') == 'system' else 'User',
                    'scale_set_priority': 'Spot' if capacity_type == 'SPOT' else 'Regular',
                })

            result = {
                'location': cluster.region,
                'current_kubernetes_version': c.get('version'),
                'kubernetes_version': c.get('version'),
                'agent_pool_profiles': agent_pool_profiles,
                'name': c.get('name'),
                'arn': c.get('arn'),
                'status': c.get('status'),
                'endpoint': c.get('endpoint'),
                'platform_version': c.get('platformVersion'),
                'provider': 'aws',
            }

            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to get EKS cluster details for {cluster.cluster_name}: {e}")
            return None

    def get_node_pools(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            nodegroups = self._list_nodegroups(cluster)
            pools = []
            for ng in nodegroups:
                scaling = ng.get('scalingConfig', {})
                instance_types = ng.get('instanceTypes', [])
                pools.append({
                    'name': ng.get('nodegroupName'),
                    'instance_types': instance_types,
                    'desired_size': scaling.get('desiredSize', 0),
                    'min_size': scaling.get('minSize', 0),
                    'max_size': scaling.get('maxSize', 0),
                    'capacity_type': ng.get('capacityType', 'ON_DEMAND'),
                    'ami_type': ng.get('amiType'),
                    'status': ng.get('status'),
                    'labels': ng.get('labels', {}),
                    'taints': ng.get('taints', []),
                })
            return json.dumps(pools, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to get EKS node pools for {cluster.cluster_name}: {e}")
            return None

    def get_cluster_version(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            c = self._describe_cluster(cluster)
            return c.get('version')
        except Exception as e:
            logger.error(f"Failed to get EKS cluster version: {e}")
            return None

    def get_cluster_identity(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            c = self._describe_cluster(cluster)
            identity = c.get('identity', {})
            return json.dumps(identity, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to get EKS cluster identity: {e}")
            return None

    def get_cluster_region(self, cluster: ClusterIdentifier) -> str:
        return cluster.region

    def get_node_resource_scope(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Return Auto Scaling Group names used by EKS nodegroups."""
        try:
            nodegroups = self._list_nodegroups(cluster)
            asg_names = []
            for ng in nodegroups:
                resources = ng.get('resources', {})
                for asg in resources.get('autoScalingGroups', []):
                    asg_names.append(asg.get('name', ''))
            return json.dumps(asg_names) if asg_names else None
        except Exception as e:
            logger.warning(f"Could not get node resource scope: {e}")
            return None

    # --- Observability ---

    def get_log_analytics_resources(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            auth = self._get_auth()
            logs = auth.session.client('logs', region_name=cluster.region)
            prefix = f'/aws/eks/{cluster.cluster_name}/'
            log_groups = []
            paginator = logs.get_paginator('describe_log_groups')
            for page in paginator.paginate(logGroupNamePrefix=prefix):
                for lg in page.get('logGroups', []):
                    log_groups.append({
                        'name': lg.get('logGroupName'),
                        'retentionInDays': lg.get('retentionInDays'),
                        'storedBytes': lg.get('storedBytes', 0),
                        'arn': lg.get('arn'),
                    })
            return json.dumps(log_groups)
        except Exception as e:
            logger.error(f"Failed to get CloudWatch Log Groups: {e}")
            return "[]"

    def get_application_monitoring(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            c = self._describe_cluster(cluster)
            logging_config = c.get('logging', {})
            cluster_logging = logging_config.get('clusterLogging', [])

            monitoring = {
                'container_insights': False,
                'cluster_logging': [],
                'xray_enabled': False,
            }

            for log_config in cluster_logging:
                if log_config.get('enabled'):
                    monitoring['cluster_logging'].extend(log_config.get('types', []))

            # Check if Container Insights addon is enabled via CloudWatch
            try:
                auth = self._get_auth()
                cw = auth.session.client('cloudwatch', region_name=cluster.region)
                resp = cw.list_metrics(
                    Namespace='ContainerInsights',
                    Dimensions=[{'Name': 'ClusterName', 'Value': cluster.cluster_name}],
                    MetricName='node_cpu_utilization',
                )
                if resp.get('Metrics'):
                    monitoring['container_insights'] = True
            except Exception:
                pass

            return json.dumps(monitoring)
        except Exception as e:
            logger.error(f"Failed to get application monitoring: {e}")
            return "[]"

    def get_observability_costs(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        try:
            auth = self._get_auth()
            ce = auth.session.client('ce', region_name='us-east-1')
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            resp = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d'),
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'And': [
                        {
                            'Dimensions': {
                                'Key': 'SERVICE',
                                'Values': [
                                    'AmazonCloudWatch',
                                    'AWS X-Ray',
                                    'Amazon CloudWatch Logs',
                                ],
                            }
                        },
                    ]
                },
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
            )

            costs = []
            for result in resp.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    costs.append({
                        'service': group['Keys'][0],
                        'cost': float(group['Metrics']['UnblendedCost']['Amount']),
                        'currency': group['Metrics']['UnblendedCost'].get('Unit', 'USD'),
                        'period_start': result['TimePeriod']['Start'],
                        'period_end': result['TimePeriod']['End'],
                    })
            return json.dumps(costs)
        except Exception as e:
            logger.warning(f"Failed to get observability costs (Cost Explorer may not be enabled): {e}")
            return "[]"

    def get_consumption_usage(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        try:
            auth = self._get_auth()
            ce = auth.session.client('ce', region_name='us-east-1')
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            resp = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d'),
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
            )

            usage = []
            for result in resp.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0:
                        usage.append({
                            'cost': cost,
                            'category': group['Keys'][0],
                            'date': result['TimePeriod']['Start'],
                        })
            return json.dumps(usage)
        except Exception as e:
            logger.warning(f"Failed to get consumption usage: {e}")
            return "[]"

    # --- Waste detection ---

    def get_orphaned_disks(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            auth = self._get_auth()
            ec2 = auth.session.client('ec2', region_name=cluster.region)

            # Find unattached EBS volumes
            resp = ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )

            orphaned = []
            cluster_tag = f'kubernetes.io/cluster/{cluster.cluster_name}'
            for vol in resp.get('Volumes', []):
                tags = {t['Key']: t['Value'] for t in vol.get('Tags', [])}
                is_related = (
                    cluster_tag in tags
                    or any('kubernetes' in k.lower() or 'pvc' in k.lower() for k in tags)
                    or any(cluster.cluster_name.lower() in str(v).lower() for v in tags.values())
                )
                if is_related:
                    orphaned.append({
                        'name': vol['VolumeId'],
                        'size_gb': vol.get('Size', 0),
                        'sku': vol.get('VolumeType', 'unknown'),
                        'created_time': vol.get('CreateTime', '').isoformat() if hasattr(vol.get('CreateTime', ''), 'isoformat') else str(vol.get('CreateTime', '')),
                        'tags': tags,
                        'location': vol.get('AvailabilityZone', cluster.region),
                    })

            return json.dumps(orphaned)
        except Exception as e:
            logger.error(f"Failed to analyze orphaned EBS volumes: {e}")
            return "[]"

    def get_unused_public_ips(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            auth = self._get_auth()
            ec2 = auth.session.client('ec2', region_name=cluster.region)

            resp = ec2.describe_addresses()
            unused = []
            for addr in resp.get('Addresses', []):
                # Only unassociated Elastic IPs
                if addr.get('AssociationId'):
                    continue
                tags = {t['Key']: t['Value'] for t in addr.get('Tags', [])}
                cluster_tag = f'kubernetes.io/cluster/{cluster.cluster_name}'
                is_related = (
                    cluster_tag in tags
                    or any('kubernetes' in k.lower() for k in tags)
                    or any(cluster.cluster_name.lower() in str(v).lower() for v in tags.values())
                )
                if is_related:
                    unused.append({
                        'name': addr.get('AllocationId', ''),
                        'ip_address': addr.get('PublicIp', ''),
                        'allocation_method': 'Static',
                        'tags': tags,
                        'location': cluster.region,
                    })

            return json.dumps(unused)
        except Exception as e:
            logger.error(f"Failed to analyze unused Elastic IPs: {e}")
            return "[]"

    def get_load_balancer_analysis(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            auth = self._get_auth()
            elbv2 = auth.session.client('elbv2', region_name=cluster.region)

            lbs = elbv2.describe_load_balancers().get('LoadBalancers', [])
            cluster_tag = f'kubernetes.io/cluster/{cluster.cluster_name}'

            cluster_lbs = []
            for lb in lbs:
                # Check tags for cluster association
                try:
                    tag_resp = elbv2.describe_tags(ResourceArns=[lb['LoadBalancerArn']])
                    tags = {}
                    for desc in tag_resp.get('TagDescriptions', []):
                        tags = {t['Key']: t['Value'] for t in desc.get('Tags', [])}
                    if cluster_tag not in tags:
                        # Also check for elbv2.k8s.aws/cluster tag
                        if tags.get('elbv2.k8s.aws/cluster') != cluster.cluster_name:
                            continue
                except Exception:
                    continue

                # Get target groups for this LB
                try:
                    tg_resp = elbv2.describe_target_groups(
                        LoadBalancerArn=lb['LoadBalancerArn']
                    )
                    tg_count = len(tg_resp.get('TargetGroups', []))
                except Exception:
                    tg_count = 0

                cluster_lbs.append({
                    'name': lb.get('LoadBalancerName', ''),
                    'sku': lb.get('Type', 'application'),
                    'frontend_ip_count': len(lb.get('AvailabilityZones', [])),
                    'backend_pool_count': tg_count,
                    'dns_name': lb.get('DNSName', ''),
                    'state': lb.get('State', {}).get('Code', 'unknown'),
                })

            lb_analysis = {
                'total_load_balancers': len(cluster_lbs),
                'load_balancers': cluster_lbs,
            }
            return json.dumps([lb_analysis])
        except Exception as e:
            logger.error(f"Failed to analyze load balancers: {e}")
            return "[]"

    def get_storage_tier_analysis(
        self,
        cluster: ClusterIdentifier,
        pvc_data: Optional[str] = None,
    ) -> Optional[str]:
        try:
            if not pvc_data:
                return "[]"
            pvcs = json.loads(pvc_data)
            analysis = []
            for pvc in pvcs.get('items', []):
                storage_class = pvc.get('spec', {}).get('storage_class_name', 'unknown')
                # EKS: detect gp2 → gp3 migration opportunities
                if 'gp2' in storage_class.lower():
                    analysis.append({
                        'pvc_name': pvc.get('metadata', {}).get('name', 'unknown'),
                        'namespace': pvc.get('metadata', {}).get('namespace', 'unknown'),
                        'current_storage_class': storage_class,
                        'storage_tier': 'gp2',
                        'recommended_tier': 'gp3',
                        'reason': 'gp3 offers better price/performance than gp2 (20% cheaper, 4x IOPS)',
                        'confidence': 'High',
                    })
                elif 'io1' in storage_class.lower():
                    analysis.append({
                        'pvc_name': pvc.get('metadata', {}).get('name', 'unknown'),
                        'namespace': pvc.get('metadata', {}).get('namespace', 'unknown'),
                        'current_storage_class': storage_class,
                        'storage_tier': 'io1',
                        'recommended_tier': 'io2',
                        'reason': 'io2 provides higher durability at same price - verify IOPS needs',
                        'confidence': 'Medium',
                    })
            return json.dumps(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze storage tiers: {e}")
            return "[]"

    def get_network_waste_analysis(
        self,
        cluster: ClusterIdentifier,
        services_data: Optional[str] = None,
    ) -> Optional[str]:
        try:
            result = {
                'analysis_type': 'cluster_network_waste',
                'cluster_name': cluster.cluster_name,
                'timestamp': datetime.now().isoformat(),
                'recommendations': [],
            }
            if services_data:
                services = json.loads(services_data)
                items = services.get('items', [])
                total = len(items)
                lb_count = sum(
                    1 for s in items
                    if s.get('spec', {}).get('type') == 'LoadBalancer'
                )
                if lb_count > 1:
                    result['recommendations'].append({
                        'type': 'ingress_consolidation',
                        'current_lb_services': lb_count,
                        'total_services': total,
                        'recommendation': 'Consider using AWS Load Balancer Controller with Ingress to consolidate ALBs/NLBs',
                        'confidence': 'Medium',
                    })
                # NAT Gateway cost analysis
                result['recommendations'].append({
                    'type': 'nat_gateway_review',
                    'recommendation': 'Review NAT Gateway usage — consider VPC endpoints for S3/DynamoDB to reduce data transfer costs',
                    'confidence': 'Low',
                })
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to analyze network waste: {e}")
            return "[]"
