"""GCP Infrastructure Inspector — cluster metadata, observability, and waste detection via GCP APIs."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from infrastructure.cloud_providers.base import CloudInfrastructureInspector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPInfrastructureInspector(CloudInfrastructureInspector):
    """Inspects GKE cluster infrastructure for optimization analysis.

    Uses GKE Container API, Compute Engine API, Cloud Logging, Cloud Monitoring,
    and BigQuery for comprehensive cluster inspection.
    """

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPInfrastructureInspector._auth_instance is None or not GCPInfrastructureInspector._auth_instance.is_authenticated():
            GCPInfrastructureInspector._auth_instance = GCPAuthenticator()
        return GCPInfrastructureInspector._auth_instance

    def _get_container_client(self):
        from google.cloud import container_v1
        auth = self._get_auth()
        return container_v1.ClusterManagerClient(credentials=auth.credentials)

    def _cluster_path(self, cluster: ClusterIdentifier) -> str:
        auth = self._get_auth()
        project = cluster.project_id or auth.project_id
        location = cluster.zone or cluster.region
        return f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

    def _get_cluster(self, cluster: ClusterIdentifier):
        """Shared helper: fetch cluster object from GKE API."""
        client = self._get_container_client()
        return client.get_cluster(name=self._cluster_path(cluster))

    def _get_project(self, cluster: ClusterIdentifier) -> str:
        auth = self._get_auth()
        return cluster.project_id or auth.project_id

    # =========================================================================
    # Cluster Metadata (6 methods)
    # =========================================================================

    def get_cluster_details(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get cluster details with node pools normalized to agent_pool_profiles schema."""
        try:
            result = self._get_cluster(cluster)

            # Normalize GKE node pools to agent_pool_profiles (same schema as AKS/EKS)
            agent_pool_profiles = []
            for np in result.node_pools:
                config = np.config
                autoscaling = np.autoscaling

                is_spot = False
                if config and config.spot:
                    is_spot = True
                elif config and config.preemptible:
                    is_spot = True

                pool = {
                    'name': np.name,
                    'vm_size': config.machine_type if config else 'unknown',
                    'count': np.initial_node_count or 0,
                    'min_count': autoscaling.min_node_count if autoscaling and autoscaling.enabled else 0,
                    'max_count': autoscaling.max_node_count if autoscaling and autoscaling.enabled else 0,
                    'enable_auto_scaling': autoscaling.enabled if autoscaling else False,
                    'os_type': config.image_type if config else 'COS_CONTAINERD',
                    'mode': 'System' if np.name == 'default-pool' else 'User',
                    'scale_set_priority': 'Spot' if is_spot else 'Regular',
                    'disk_size_gb': config.disk_size_gb if config else 100,
                    'disk_type': config.disk_type if config else 'pd-standard',
                }
                agent_pool_profiles.append(pool)

            details = {
                'location': result.location,
                'current_kubernetes_version': result.current_master_version,
                'kubernetes_version': result.current_master_version,
                'agent_pool_profiles': agent_pool_profiles,
                'self_link': result.self_link,
                'status': result.status.name if result.status else 'UNKNOWN',
                'endpoint': result.endpoint,
                'network': result.network,
                'subnetwork': result.subnetwork,
                'cluster_ipv4_cidr': result.cluster_ipv4_cidr,
            }

            return json.dumps(details, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_cluster_details error: {e}")
            return None

    def get_node_pools(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get detailed node pool information."""
        try:
            client = self._get_container_client()
            response = client.list_node_pools(parent=self._cluster_path(cluster))

            pools = []
            for np in response.node_pools:
                config = np.config
                pool_info = {
                    'name': np.name,
                    'machine_type': config.machine_type if config else None,
                    'disk_size_gb': config.disk_size_gb if config else None,
                    'disk_type': config.disk_type if config else None,
                    'initial_node_count': np.initial_node_count,
                    'version': np.version,
                    'status': np.status.name if np.status else 'UNKNOWN',
                    'spot': config.spot if config else False,
                    'preemptible': config.preemptible if config else False,
                    'image_type': config.image_type if config else None,
                    'autoscaling': {
                        'enabled': np.autoscaling.enabled if np.autoscaling else False,
                        'min_node_count': np.autoscaling.min_node_count if np.autoscaling else 0,
                        'max_node_count': np.autoscaling.max_node_count if np.autoscaling else 0,
                    },
                    'labels': dict(config.labels) if config and config.labels else {},
                    'taints': [
                        {'key': t.key, 'value': t.value, 'effect': t.effect.name if t.effect else 'NO_SCHEDULE'}
                        for t in config.taints
                    ] if config and config.taints else [],
                }
                pools.append(pool_info)

            return json.dumps(pools, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_node_pools error: {e}")
            return None

    def get_cluster_version(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            result = self._get_cluster(cluster)
            return result.current_master_version
        except Exception as e:
            logger.error(f"GKE get_cluster_version error: {e}")
            return None

    def get_cluster_identity(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get cluster identity (workload identity, network config)."""
        try:
            result = self._get_cluster(cluster)

            identity = {
                'workload_identity_config': {
                    'workload_pool': result.workload_identity_config.workload_pool
                } if result.workload_identity_config else None,
                'network_policy': {
                    'enabled': result.network_policy.enabled,
                    'provider': result.network_policy.provider.name if result.network_policy.provider else None,
                } if result.network_policy else None,
                'legacy_abac': {
                    'enabled': result.legacy_abac.enabled
                } if result.legacy_abac else None,
                'master_auth': {
                    'username': bool(result.master_auth.username) if result.master_auth else False,
                    'client_certificate_config': bool(result.master_auth.client_certificate_config) if result.master_auth else False,
                } if result.master_auth else None,
            }

            return json.dumps(identity, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_cluster_identity error: {e}")
            return None

    def get_cluster_region(self, cluster: ClusterIdentifier) -> str:
        """Extract region from cluster location (e.g. 'us-central1-a' -> 'us-central1')."""
        try:
            result = self._get_cluster(cluster)
            location = result.location
            # Zonal cluster: us-central1-a -> us-central1
            # Regional cluster: us-central1 -> us-central1
            parts = location.split('-')
            if len(parts) >= 3 and parts[-1].isalpha() and len(parts[-1]) == 1:
                return '-'.join(parts[:-1])
            return location
        except Exception as e:
            logger.error(f"GKE get_cluster_region error: {e}")
            return cluster.region or ''

    def get_node_resource_scope(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get managed instance group names backing node pools."""
        try:
            result = self._get_cluster(cluster)
            instance_groups = []

            for np in result.node_pools:
                if np.instance_group_urls:
                    for url in np.instance_group_urls:
                        # URL format: https://www.googleapis.com/compute/v1/projects/.../zones/.../instanceGroupManagers/...
                        ig_name = url.split('/')[-1]
                        instance_groups.append({
                            'node_pool': np.name,
                            'instance_group': ig_name,
                            'url': url,
                        })

            return json.dumps(instance_groups, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_node_resource_scope error: {e}")
            return None

    # =========================================================================
    # Observability (4 methods)
    # =========================================================================

    def get_log_analytics_resources(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get Cloud Logging log sinks and log buckets related to the cluster."""
        try:
            from google.cloud import logging_v2

            auth = self._get_auth()
            project = self._get_project(cluster)
            client = logging_v2.Client(credentials=auth.credentials, project=project)

            # List log sinks
            sinks = []
            for sink in client.list_sinks():
                # Filter for kubernetes-related sinks
                if 'k8s' in (sink.filter_ or '').lower() or 'kubernetes' in sink.name.lower():
                    sinks.append({
                        'name': sink.name,
                        'destination': sink.destination,
                        'filter': sink.filter_,
                    })

            # Check for GKE-specific log entries (sample query)
            log_resources = {
                'sinks': sinks,
                'expected_log_names': [
                    f'projects/{project}/logs/events',
                    f'projects/{project}/logs/stdout',
                    f'projects/{project}/logs/stderr',
                ],
            }

            return json.dumps(log_resources, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_log_analytics_resources error: {e}")
            return None

    def get_application_monitoring(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Check GKE monitoring add-ons (Managed Prometheus, logging, monitoring)."""
        try:
            result = self._get_cluster(cluster)

            addons = result.addons_config
            monitoring_config = result.monitoring_config
            logging_config = result.logging_config

            info = {
                'monitoring_service': result.monitoring_service,
                'logging_service': result.logging_service,
                'addons': {
                    'http_load_balancing': not (addons.http_load_balancing.disabled) if addons and addons.http_load_balancing else None,
                    'horizontal_pod_autoscaling': not (addons.horizontal_pod_autoscaling.disabled) if addons and addons.horizontal_pod_autoscaling else None,
                    'network_policy_config': not (addons.network_policy_config.disabled) if addons and addons.network_policy_config else None,
                    'gce_persistent_disk_csi': not (addons.gce_persistent_disk_csi_driver_config.enabled is False) if addons and addons.gce_persistent_disk_csi_driver_config else None,
                },
                'managed_prometheus': {
                    'enabled': monitoring_config.managed_prometheus_config.enabled
                } if monitoring_config and monitoring_config.managed_prometheus_config else {'enabled': False},
                'logging_component_config': {
                    'components': [c.name for c in logging_config.component_config.enable_components]
                } if logging_config and logging_config.component_config else None,
            }

            return json.dumps(info, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_application_monitoring error: {e}")
            return None

    def get_observability_costs(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        """Get Cloud Logging + Cloud Monitoring costs from BigQuery billing export."""
        try:
            import os
            from google.cloud import bigquery

            auth = self._get_auth()
            project = self._get_project(cluster)
            dataset = os.getenv('GCP_BILLING_DATASET')
            billing_account_id = os.getenv('GCP_BILLING_ACCOUNT_ID', '').replace('-', '')

            if not dataset:
                return json.dumps([])

            client = bigquery.Client(credentials=auth.credentials, project=project)
            table = f"`{project}.{dataset}.gcp_billing_export_resource_v1_{billing_account_id}`"

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            query = f"""
                SELECT
                    service.description AS service,
                    SUM(cost) AS cost,
                    currency
                FROM {table}
                WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
                    AND project.id = @project_id
                    AND service.description IN (
                        'Cloud Logging', 'Cloud Monitoring', 'Cloud Trace',
                        'Stackdriver Logging', 'Stackdriver Monitoring'
                    )
                GROUP BY service.description, currency
                ORDER BY cost DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("project_id", "STRING", project),
                ]
            )

            results = client.query(query, job_config=job_config).result()
            costs = []
            for row in results:
                costs.append({
                    'service': row.service,
                    'cost': round(float(row.cost), 2),
                    'currency': row.currency,
                    'period_start': start_date.strftime('%Y-%m-%d'),
                    'period_end': end_date.strftime('%Y-%m-%d'),
                })

            return json.dumps(costs, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_observability_costs error: {e}")
            return None

    def get_consumption_usage(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        """Get daily cost breakdown from BigQuery billing export."""
        try:
            import os
            from google.cloud import bigquery

            auth = self._get_auth()
            project = self._get_project(cluster)
            dataset = os.getenv('GCP_BILLING_DATASET')
            billing_account_id = os.getenv('GCP_BILLING_ACCOUNT_ID', '').replace('-', '')

            if not dataset:
                return json.dumps([])

            client = bigquery.Client(credentials=auth.credentials, project=project)
            table = f"`{project}.{dataset}.gcp_billing_export_resource_v1_{billing_account_id}`"

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            query = f"""
                SELECT
                    DATE(usage_start_time) AS usage_date,
                    service.description AS service,
                    SUM(cost) AS daily_cost,
                    currency
                FROM {table}
                WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
                    AND project.id = @project_id
                    AND EXISTS (
                        SELECT 1 FROM UNNEST(labels) AS l
                        WHERE l.key = 'goog-k8s-cluster-name'
                        AND l.value = @cluster_name
                    )
                GROUP BY usage_date, service.description, currency
                ORDER BY usage_date DESC, daily_cost DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("project_id", "STRING", project),
                    bigquery.ScalarQueryParameter("cluster_name", "STRING", cluster.cluster_name),
                ]
            )

            results = client.query(query, job_config=job_config).result()
            usage = []
            for row in results:
                usage.append({
                    'date': row.usage_date.isoformat(),
                    'service': row.service,
                    'cost': round(float(row.daily_cost), 2),
                    'currency': row.currency,
                })

            return json.dumps(usage, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_consumption_usage error: {e}")
            return None

    # =========================================================================
    # Waste Detection (5 methods)
    # =========================================================================

    def get_orphaned_disks(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Find unattached persistent disks that may belong to this cluster."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = self._get_project(cluster)
            client = compute_v1.DisksClient(credentials=auth.credentials)

            # List disks across all zones in the cluster's region
            region = cluster.region or (cluster.zone.rsplit('-', 1)[0] if cluster.zone else '')
            agg_request = compute_v1.AggregatedListDisksRequest(project=project)

            orphaned = []
            for zone_name, scoped_list in client.aggregated_list(request=agg_request):
                if not scoped_list.disks:
                    continue
                # Filter to cluster's region
                if region and region not in zone_name:
                    continue

                for disk in scoped_list.disks:
                    # Orphaned = no users (not attached to any VM)
                    if disk.users:
                        continue

                    # Check if disk belongs to this cluster via labels
                    labels = dict(disk.labels) if disk.labels else {}
                    is_cluster_disk = (
                        labels.get('goog-k8s-cluster-name') == cluster.cluster_name
                        or 'kubernetes' in disk.name.lower()
                        or 'pvc' in disk.name.lower()
                    )

                    if is_cluster_disk:
                        orphaned.append({
                            'name': disk.name,
                            'size_gb': disk.size_gb,
                            'sku': disk.type_.split('/')[-1] if disk.type_ else 'pd-standard',
                            'created_time': disk.creation_timestamp,
                            'tags': labels,
                            'location': zone_name.split('/')[-1] if '/' in zone_name else zone_name,
                            'status': disk.status,
                        })

            return json.dumps(orphaned, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_orphaned_disks error: {e}")
            return None

    def get_unused_public_ips(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Find reserved but unassigned static IP addresses."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = self._get_project(cluster)
            region = cluster.region or (cluster.zone.rsplit('-', 1)[0] if cluster.zone else '')

            unused = []

            # Check regional addresses
            try:
                client = compute_v1.AddressesClient(credentials=auth.credentials)
                if region:
                    for addr in client.list(project=project, region=region):
                        if addr.status == 'RESERVED':  # Not in use
                            labels = dict(addr.labels) if addr.labels else {}
                            unused.append({
                                'name': addr.name,
                                'ip_address': addr.address,
                                'allocation_method': 'Static',
                                'tags': labels,
                                'location': region,
                                'address_type': addr.address_type,
                            })
            except Exception as e:
                logger.debug(f"Regional address listing failed: {e}")

            # Check global addresses
            try:
                global_client = compute_v1.GlobalAddressesClient(credentials=auth.credentials)
                for addr in global_client.list(project=project):
                    if addr.status == 'RESERVED':
                        labels = dict(addr.labels) if addr.labels else {}
                        unused.append({
                            'name': addr.name,
                            'ip_address': addr.address,
                            'allocation_method': 'Static',
                            'tags': labels,
                            'location': 'global',
                            'address_type': addr.address_type,
                        })
            except Exception as e:
                logger.debug(f"Global address listing failed: {e}")

            return json.dumps(unused, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_unused_public_ips error: {e}")
            return None

    def get_load_balancer_analysis(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Analyze GCP load balancers (forwarding rules + backend services)."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = self._get_project(cluster)
            region = cluster.region or (cluster.zone.rsplit('-', 1)[0] if cluster.zone else '')

            load_balancers = []

            # List forwarding rules (regional)
            try:
                fr_client = compute_v1.ForwardingRulesClient(credentials=auth.credentials)
                if region:
                    for rule in fr_client.list(project=project, region=region):
                        # Filter for k8s-related rules
                        desc = (rule.description or '').lower()
                        name = rule.name.lower()
                        if 'k8s' in name or 'kubernetes' in desc or cluster.cluster_name.lower() in name:
                            load_balancers.append({
                                'name': rule.name,
                                'sku': rule.load_balancing_scheme or 'EXTERNAL',
                                'frontend_ip_count': 1,
                                'backend_pool_count': 1 if rule.backend_service else 0,
                                'ip_address': getattr(rule, 'ip_address', None),
                                'target': rule.target,
                                'port_range': rule.port_range,
                            })
            except Exception as e:
                logger.debug(f"Forwarding rules listing failed: {e}")

            # List global forwarding rules
            try:
                gfr_client = compute_v1.GlobalForwardingRulesClient(credentials=auth.credentials)
                for rule in gfr_client.list(project=project):
                    name = rule.name.lower()
                    if 'k8s' in name or cluster.cluster_name.lower() in name:
                        load_balancers.append({
                            'name': rule.name,
                            'sku': rule.load_balancing_scheme or 'EXTERNAL',
                            'frontend_ip_count': 1,
                            'backend_pool_count': 1 if rule.backend_service else 0,
                            'ip_address': getattr(rule, 'ip_address', None),
                            'target': rule.target,
                            'port_range': rule.port_range,
                        })
            except Exception as e:
                logger.debug(f"Global forwarding rules listing failed: {e}")

            result = [{
                'total_load_balancers': len(load_balancers),
                'load_balancers': load_balancers,
            }]

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_load_balancer_analysis error: {e}")
            return None

    def get_storage_tier_analysis(self, cluster: ClusterIdentifier, pvc_data: Optional[str] = None) -> Optional[str]:
        """Analyze PVC storage classes and recommend upgrades."""
        try:
            recommendations = []

            if pvc_data:
                pvcs = json.loads(pvc_data) if isinstance(pvc_data, str) else pvc_data

                items = pvcs.get('items', []) if isinstance(pvcs, dict) else pvcs

                for pvc in items:
                    metadata = pvc.get('metadata', {})
                    spec = pvc.get('spec', {})
                    storage_class = spec.get('storageClassName', 'standard')
                    pvc_name = metadata.get('name', 'unknown')
                    namespace = metadata.get('namespace', 'default')

                    rec = {
                        'pvc_name': pvc_name,
                        'namespace': namespace,
                        'current_storage_class': storage_class,
                    }

                    # pd-standard -> pd-balanced (better IOPS, similar price)
                    if storage_class in ('standard', 'pd-standard', 'standard-rwo'):
                        rec['storage_tier'] = 'pd-standard'
                        rec['recommended_tier'] = 'pd-balanced'
                        rec['reason'] = 'pd-balanced offers 2x IOPS at ~20% higher cost, better price/performance'
                        rec['confidence'] = 'high'
                        recommendations.append(rec)

                    # pd-ssd -> pd-ssd (already optimal) or check for over-provisioning
                    elif storage_class in ('premium-rwo', 'pd-ssd'):
                        capacity = spec.get('resources', {}).get('requests', {}).get('storage', '')
                        if capacity and self._parse_storage_size(capacity) > 500:
                            rec['storage_tier'] = 'pd-ssd'
                            rec['recommended_tier'] = 'pd-balanced'
                            rec['reason'] = 'Large SSD volumes may be over-provisioned; pd-balanced is cheaper for >500Gi'
                            rec['confidence'] = 'medium'
                            recommendations.append(rec)

            return json.dumps(recommendations, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_storage_tier_analysis error: {e}")
            return None

    def get_network_waste_analysis(self, cluster: ClusterIdentifier, services_data: Optional[str] = None) -> Optional[str]:
        """Analyze network waste (multiple LBs, NAT Gateway opportunities)."""
        try:
            recommendations = []

            if services_data:
                services = json.loads(services_data) if isinstance(services_data, str) else services_data
                items = services.get('items', []) if isinstance(services, dict) else services

                lb_services = [
                    s for s in items
                    if s.get('spec', {}).get('type') == 'LoadBalancer'
                ]

                if len(lb_services) > 2:
                    recommendations.append({
                        'type': 'lb_consolidation',
                        'severity': 'medium',
                        'title': f'Consolidate {len(lb_services)} LoadBalancer services',
                        'description': (
                            f'Found {len(lb_services)} LoadBalancer-type services. '
                            f'Consider using GKE Ingress (GCE L7 LB) or Gateway API '
                            f'to consolidate into fewer load balancers. '
                            f'Each GCP LB costs ~$18/month + data processing.'
                        ),
                        'estimated_monthly_savings': round((len(lb_services) - 1) * 18, 2),
                    })

            # Always suggest Cloud NAT optimization
            recommendations.append({
                'type': 'nat_optimization',
                'severity': 'low',
                'title': 'Review Cloud NAT configuration',
                'description': (
                    'If using Cloud NAT for egress, consider Private Google Access '
                    'for GCP API calls and VPC Service Controls to reduce NAT data processing costs.'
                ),
                'estimated_monthly_savings': 0,
            })

            result = {
                'analysis_type': 'network_waste',
                'cluster_name': cluster.cluster_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'recommendations': recommendations,
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_network_waste_analysis error: {e}")
            return None

    @staticmethod
    def _parse_storage_size(size_str: str) -> int:
        """Parse Kubernetes storage size string to GB. '100Gi' -> 100, '500Mi' -> 0."""
        size_str = size_str.strip()
        if size_str.endswith('Gi'):
            return int(size_str[:-2])
        elif size_str.endswith('Ti'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('Mi'):
            return max(1, int(size_str[:-2]) // 1024)
        return 0
