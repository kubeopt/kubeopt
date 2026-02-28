"""
Azure Infrastructure Inspector
================================

Extracts cloud resource queries from kubernetes_data_cache.py into the
CloudInfrastructureInspector interface. Each method delegates to azure_sdk_manager.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from infrastructure.cloud_providers.base import CloudInfrastructureInspector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class AzureInfrastructureInspector(CloudInfrastructureInspector):
    """Azure implementation — delegates to azure_sdk_manager."""

    def _get_aks_client(self, cluster: ClusterIdentifier):
        from infrastructure.services.azure_sdk_manager import azure_sdk_manager
        client = azure_sdk_manager.get_aks_client(cluster.subscription_id)
        if not client:
            raise RuntimeError(f"Cannot get AKS client for subscription {cluster.subscription_id}")
        return client

    def _get_managed_cluster(self, cluster: ClusterIdentifier):
        client = self._get_aks_client(cluster)
        return client.managed_clusters.get(cluster.resource_group, cluster.cluster_name)

    # --- Cluster metadata ---

    def get_cluster_details(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            mc = self._get_managed_cluster(cluster)
            return json.dumps(mc.as_dict(), indent=2)
        except Exception as e:
            logger.error(f"Failed to get cluster details for {cluster.cluster_name}: {e}")
            return None

    def get_node_pools(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            client = self._get_aks_client(cluster)
            pools = list(client.agent_pools.list(cluster.resource_group, cluster.cluster_name))
            return json.dumps([p.as_dict() for p in pools], indent=2)
        except Exception as e:
            logger.error(f"Failed to get node pools for {cluster.cluster_name}: {e}")
            return None

    def get_cluster_version(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            mc = self._get_managed_cluster(cluster)
            version = mc.current_kubernetes_version or mc.kubernetes_version
            return str(version) if version else None
        except Exception as e:
            logger.error(f"Failed to get cluster version for {cluster.cluster_name}: {e}")
            return None

    def get_cluster_identity(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            mc = self._get_managed_cluster(cluster)
            identity = mc.identity
            return json.dumps(identity.as_dict() if identity else {}, indent=2)
        except Exception as e:
            logger.error(f"Failed to get cluster identity for {cluster.cluster_name}: {e}")
            return None

    def get_cluster_region(self, cluster: ClusterIdentifier) -> str:
        try:
            mc = self._get_managed_cluster(cluster)
            return mc.location
        except Exception as e:
            raise ValueError(f"Could not determine cluster region for {cluster.cluster_name}: {e}")

    def get_node_resource_scope(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            mc = self._get_managed_cluster(cluster)
            return mc.node_resource_group
        except Exception as e:
            logger.warning(f"Could not get node resource group for {cluster.cluster_name}: {e}")
            return None

    # --- Observability ---

    def get_log_analytics_resources(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            client = azure_sdk_manager.get_log_analytics_client(cluster.subscription_id)
            if client is None:
                return "[]"
            workspaces = client.workspaces.list_by_resource_group(cluster.resource_group)
            result = [
                {
                    'id': ws.id, 'name': ws.name, 'location': ws.location,
                    'retentionInDays': ws.retention_in_days, 'tags': ws.tags,
                }
                for ws in workspaces
            ]
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to get Log Analytics workspaces: {e}")
            return None

    def get_application_monitoring(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            client = azure_sdk_manager.get_application_insights_client(cluster.subscription_id)
            if client is None:
                return "[]"
            components = client.components.list_by_resource_group(cluster.resource_group)
            result = [
                {
                    'id': c.id, 'name': c.name, 'location': c.location,
                    'appId': c.app_id, 'instrumentationKey': c.instrumentation_key, 'tags': c.tags,
                }
                for c in components
            ]
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to get Application Insights components: {e}")
            return None

    def get_observability_costs(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            cost_client = azure_sdk_manager.get_cost_management_client(cluster.subscription_id)
            scope = f"/subscriptions/{cluster.subscription_id}/resourceGroups/{cluster.resource_group}"
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            query_definition = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    "to": end_date.strftime("%Y-%m-%dT23:59:59Z"),
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                    "grouping": [{"type": "Dimension", "name": "MeterCategory"}],
                    "filter": {
                        "dimensions": {
                            "name": "MeterCategory",
                            "operator": "In",
                            "values": ["Log Analytics", "Application Insights", "Azure Monitor"],
                        }
                    },
                },
            }
            result = cost_client.query.usage(scope, query_definition)
            return json.dumps(result.as_dict())
        except Exception as e:
            logger.error(f"Failed to get observability costs: {e}")
            return None

    def get_consumption_usage(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            consumption_client = azure_sdk_manager.get_consumption_client(cluster.subscription_id)
            if consumption_client is None:
                return "[]"
            scopes = [
                f"/subscriptions/{cluster.subscription_id}/resourceGroups/{cluster.resource_group}",
                f"/subscriptions/{cluster.subscription_id}",
            ]
            usage_details = None
            for scope in scopes:
                try:
                    usage_details = consumption_client.usage_details.list(scope=scope)
                    break
                except Exception:
                    try:
                        usage_details = consumption_client.usage_details.list(scope=scope, top=100)
                        break
                    except Exception:
                        continue
            if usage_details is None:
                return "[]"
            result = [
                {
                    'cost': u.pretax_cost,
                    'meter': u.meter_name,
                    'category': u.meter_category,
                    'subcategory': u.meter_subcategory,
                    'date': u.date.isoformat() if u.date else None,
                }
                for u in usage_details
            ]
            return json.dumps(result)
        except Exception as e:
            logger.warning(f"Failed to get consumption usage: {e}")
            return "[]"

    # --- Waste detection ---

    def get_orphaned_disks(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            compute_client = azure_sdk_manager.get_compute_client(cluster.subscription_id)
            if not compute_client:
                return "[]"
            resource_groups = [cluster.resource_group]
            mc_rg = self.get_node_resource_scope(cluster)
            if mc_rg:
                resource_groups.append(mc_rg)
            orphaned = []
            for rg in resource_groups:
                try:
                    for disk in compute_client.disks.list_by_resource_group(rg):
                        if disk.managed_by is not None or disk.managed_by_extended is not None:
                            continue
                        is_related = rg.startswith('MC_')
                        if not is_related and disk.tags:
                            for k, v in disk.tags.items():
                                if any(m in k.lower() or m in str(v).lower()
                                       for m in ['kubernetes', 'k8s', cluster.cluster_name.lower(), 'pvc', 'persistent']):
                                    is_related = True
                                    break
                        if not is_related:
                            if any(p in disk.name.lower() for p in ['pvc-', 'kubernetes-', cluster.cluster_name.lower()]):
                                is_related = True
                        if is_related:
                            orphaned.append({
                                'name': disk.name, 'resource_group': rg,
                                'size_gb': disk.disk_size_gb,
                                'sku': disk.sku.name if disk.sku else 'Unknown',
                                'created_time': disk.time_created.isoformat() if disk.time_created else None,
                                'tags': disk.tags or {}, 'location': disk.location,
                            })
                except Exception as e:
                    logger.warning(f"Could not list disks in {rg}: {e}")
            return json.dumps(orphaned)
        except Exception as e:
            logger.error(f"Failed to analyze orphaned disks: {e}")
            return "[]"

    def get_unused_public_ips(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            network_client = azure_sdk_manager.get_network_client(cluster.subscription_id)
            if not network_client:
                return "[]"
            resource_groups = [cluster.resource_group]
            mc_rg = self.get_node_resource_scope(cluster)
            if mc_rg:
                resource_groups.append(mc_rg)
            unused = []
            for rg in resource_groups:
                try:
                    for pip in network_client.public_ip_addresses.list(rg):
                        if pip.ip_configuration:
                            continue
                        is_related = rg.startswith('MC_')
                        if not is_related and pip.tags:
                            for k, v in pip.tags.items():
                                if any(m in k.lower() or m in str(v).lower()
                                       for m in ['kubernetes', 'k8s', cluster.cluster_name.lower()]):
                                    is_related = True
                                    break
                        if not is_related:
                            if any(p in pip.name.lower() for p in ['kubernetes-', cluster.cluster_name.lower()]):
                                is_related = True
                        if is_related:
                            unused.append({
                                'name': pip.name, 'resource_group': rg,
                                'ip_address': pip.ip_address,
                                'sku': pip.sku.name if pip.sku else 'Basic',
                                'allocation_method': pip.public_ip_allocation_method,
                                'tags': pip.tags or {}, 'location': pip.location,
                            })
                except Exception as e:
                    logger.warning(f"Could not list public IPs in {rg}: {e}")
            return json.dumps(unused)
        except Exception as e:
            logger.error(f"Failed to analyze unused public IPs: {e}")
            return "[]"

    def get_load_balancer_analysis(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            network_client = azure_sdk_manager.get_network_client(cluster.subscription_id)
            if not network_client:
                return "[]"
            mc_rg = self.get_node_resource_scope(cluster)
            if not mc_rg:
                return "[]"
            lbs = list(network_client.load_balancers.list(mc_rg))
            lb_analysis = {
                'total_load_balancers': len(lbs),
                'load_balancers': [
                    {
                        'name': lb.name,
                        'sku': lb.sku.name if lb.sku else 'Basic',
                        'frontend_ip_count': len(lb.frontend_ip_configurations) if lb.frontend_ip_configurations else 0,
                        'backend_pool_count': len(lb.backend_address_pools) if lb.backend_address_pools else 0,
                        'tags': lb.tags or {}, 'location': lb.location,
                    }
                    for lb in lbs
                ],
            }
            return json.dumps([lb_analysis])
        except Exception as e:
            logger.error(f"Failed to analyze load balancers: {e}")
            return "[]"

    def get_storage_tier_analysis(self, cluster: ClusterIdentifier, pvc_data: Optional[str] = None) -> Optional[str]:
        try:
            if not pvc_data:
                return "[]"
            pvcs = json.loads(pvc_data)
            analysis = []
            for pvc in pvcs.get('items', []):
                storage_class = pvc.get('spec', {}).get('storage_class_name', 'unknown')
                if 'premium' in storage_class.lower():
                    analysis.append({
                        'pvc_name': pvc.get('metadata', {}).get('name', 'unknown'),
                        'namespace': pvc.get('metadata', {}).get('namespace', 'unknown'),
                        'current_storage_class': storage_class,
                        'storage_tier': 'Premium_LRS',
                        'recommended_tier': 'Standard_LRS',
                        'reason': 'Premium storage detected - verify if high IOPS needed',
                        'confidence': 'Medium',
                    })
            return json.dumps(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze storage tiers: {e}")
            return "[]"

    def get_network_waste_analysis(self, cluster: ClusterIdentifier, services_data: Optional[str] = None) -> Optional[str]:
        try:
            result = {
                'analysis_type': 'cluster_network_waste',
                'cluster_name': cluster.cluster_name,
                'timestamp': datetime.now().isoformat(),
                'recommendations': [],
            }
            if services_data:
                services = json.loads(services_data)
                total = len(services.get('items', []))
                lb_count = sum(1 for s in services.get('items', []) if s.get('spec', {}).get('type') == 'LoadBalancer')
                if lb_count > 0 and total > 0 and lb_count / total > 0.3:
                    result['recommendations'].append({
                        'type': 'ingress_consolidation',
                        'current_lb_services': lb_count,
                        'total_services': total,
                        'recommendation': 'Consider using Ingress controller to consolidate load balancers',
                        'confidence': 'Medium',
                    })
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to analyze network waste: {e}")
            return "[]"
