#!/usr/bin/env python3
"""
Comprehensive Cost Collector - Enhanced Azure Cost Data Collection
================================================================

Developer: Srinivas Kondepudi  
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Extends existing cost collection to capture comprehensive Azure cost data
for enhanced savings analysis while maintaining backwards compatibility.
"""

import logging
import subprocess
import json
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ComprehensiveCostCollector:
    """
    Enhanced cost collector that extends existing cost data collection
    to capture comprehensive Azure cost information for better savings analysis
    """
    
    def __init__(self):
        self.cost_categories = self._initialize_cost_categories()
        
    def _initialize_cost_categories(self) -> Dict:
        """Initialize comprehensive cost categorization mapping"""
        return {
            'compute': {
                'keywords': ['Virtual Machines', 'Container', 'Kubernetes Service', 'Azure Kubernetes Service'],
                'meters': ['Compute Hours', 'vCore', 'Premium vCore', 'Standard vCore']
            },
            'storage': {
                'keywords': ['Storage', 'Managed Disks', 'Blob Storage', 'File Storage'],
                'meters': ['LRS', 'ZRS', 'GRS', 'Premium SSD', 'Standard SSD', 'Standard HDD']
            },
            'networking': {
                'keywords': ['Load Balancer', 'Public IP', 'Virtual Network', 'Bandwidth', 'VPN Gateway'],
                'meters': ['Data Transfer', 'Outbound Data Transfer', 'Load Balancer']
            },
            'monitoring': {
                'keywords': ['Monitor', 'Application Insights', 'Log Analytics'],
                'meters': ['Data Ingestion', 'Data Retention', 'Query']
            },
            'security': {
                'keywords': ['Key Vault', 'Security Center', 'Defender'],
                'meters': ['Operations', 'Advanced Operations', 'Secret Operations']
            },
            'backup': {
                'keywords': ['Backup', 'Site Recovery', 'Archive'],
                'meters': ['Protected Instance', 'Storage Consumed', 'Backup Storage']
            },
            'database': {
                'keywords': ['SQL Database', 'Cosmos DB', 'Database', 'Redis Cache'],
                'meters': ['DTU', 'vCore', 'RU', 'Cache Size']
            },
            'addons': {
                'keywords': ['Service Bus', 'Event Grid', 'API Management', 'Application Gateway'],
                'meters': ['Standard Operations', 'Premium Operations', 'Messages']
            }
        }
    
    def collect_comprehensive_cost_data(self, resource_group: str, cluster_name: str,
                                      subscription_id: str, days: int = 30) -> Dict:
        """
        Collect comprehensive cost data extending existing functionality
        
        This method enhances the existing cost collection with additional
        cost categories and metrics needed for comprehensive savings analysis.
        """
        
        logger.info(f"🔄 Collecting comprehensive cost data for {cluster_name} ({days} days)")
        
        try:
            # Get base cost data using existing method
            base_cost_data = self._get_base_aks_cost_data(resource_group, cluster_name, 
                                                        subscription_id, days)
            
            # Enhance with additional cost categories
            comprehensive_data = self._enhance_cost_data_with_additional_categories(
                base_cost_data, resource_group, cluster_name, subscription_id, days
            )
            
            # Add cost trend analysis
            comprehensive_data['cost_trends'] = self._analyze_cost_trends(
                resource_group, cluster_name, subscription_id
            )
            
            # Add resource utilization context
            comprehensive_data['resource_context'] = self._collect_resource_utilization_context(
                resource_group, cluster_name, subscription_id
            )
            
            # Calculate comprehensive cost breakdown
            comprehensive_data['enhanced_breakdown'] = self._calculate_enhanced_breakdown(
                comprehensive_data
            )
            
            logger.info(f"✅ Comprehensive cost data collected: ${comprehensive_data.get('total_cost', 0):.2f}")
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"❌ Comprehensive cost collection failed: {e}")
            # Fall back to basic cost collection to maintain tool functionality
            return self._get_fallback_cost_data(resource_group, cluster_name, subscription_id, days)
    
    def _get_base_aks_cost_data(self, resource_group: str, cluster_name: str,
                               subscription_id: str, days: int) -> Dict:
        """
        Get base AKS cost data using existing functionality
        (This would integrate with your existing get_aks_specific_cost_data function)
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # This mirrors your existing cost query structure
        cost_query = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "PreTaxCost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {"type": "Dimension", "name": "ResourceType"},
                    {"type": "Dimension", "name": "ResourceGroupName"},
                    {"type": "Dimension", "name": "ServiceName"},
                    {"type": "Dimension", "name": "ResourceId"},
                    {"type": "Dimension", "name": "MeterCategory"},
                    {"type": "Dimension", "name": "Meter"},
                    {"type": "Dimension", "name": "MeterSubcategory"},
                    {"type": "Dimension", "name": "ResourceLocation"}
                ]
            }
        }
        
        try:
            # Execute the cost query
            cost_data = self._execute_azure_cost_query(cost_query, subscription_id)
            
            # Process and categorize the results
            processed_data = self._process_base_cost_results(cost_data, resource_group, cluster_name)
            
            return processed_data
            
        except Exception as e:
            logger.warning(f"⚠️ Base cost data collection failed: {e}")
            return {'total_cost': 0, 'cost_breakdown': {}, 'daily_costs': []}
    
    def _enhance_cost_data_with_additional_categories(self, base_data: Dict,
                                                    resource_group: str, cluster_name: str,
                                                    subscription_id: str, days: int) -> Dict:
        """
        Enhance base cost data with additional categories for comprehensive analysis
        """
        
        enhanced_data = base_data.copy()
        
        # Add network cost analysis
        network_costs = self._collect_network_costs(resource_group, subscription_id, days)
        enhanced_data['network_costs'] = network_costs
        
        # Add monitoring and logging costs
        monitoring_costs = self._collect_monitoring_costs(resource_group, subscription_id, days)
        enhanced_data['monitoring_costs'] = monitoring_costs
        
        # Add backup and disaster recovery costs
        backup_costs = self._collect_backup_costs(resource_group, subscription_id, days)
        enhanced_data['backup_costs'] = backup_costs
        
        # Add security service costs
        security_costs = self._collect_security_costs(resource_group, subscription_id, days)
        enhanced_data['security_costs'] = security_costs
        
        # Add addon service costs
        addon_costs = self._collect_addon_costs(resource_group, subscription_id, days)
        enhanced_data['addon_costs'] = addon_costs
        
        # Calculate total enhanced cost
        additional_costs = sum([
            network_costs.get('total', 0),
            monitoring_costs.get('total', 0),
            backup_costs.get('total', 0),
            security_costs.get('total', 0),
            addon_costs.get('total', 0)
        ])
        
        enhanced_data['total_cost'] = enhanced_data.get('total_cost', 0) + additional_costs
        enhanced_data['additional_categories_cost'] = additional_costs
        
        logger.info(f"📊 Enhanced cost data: +${additional_costs:.2f} from additional categories")
        
        return enhanced_data
    
    def _collect_network_costs(self, resource_group: str, subscription_id: str, days: int) -> Dict:
        """Collect detailed network-related costs"""
        
        network_query = f"""
        az consumption usage list \\
            --subscription {subscription_id} \\
            --start-date {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} \\
            --end-date {datetime.now().strftime('%Y-%m-%d')} \\
            --query "[?contains(instanceName, '{resource_group}') && (contains(meterName, 'Load Balancer') || contains(meterName, 'Public IP') || contains(meterName, 'Data Transfer') || contains(meterName, 'Bandwidth'))].{{meterName:meterName, quantity:quantity, pretaxCost:pretaxCost}}" \\
            --output json
        """
        
        try:
            result = subprocess.run(network_query, shell=True, capture_output=True, text=True, check=True)
            network_data = json.loads(result.stdout)
            
            network_breakdown = {
                'load_balancer': 0,
                'public_ip': 0,
                'data_transfer': 0,
                'bandwidth': 0,
                'total': 0
            }
            
            for item in network_data:
                cost = float(item.get('pretaxCost', 0))
                meter_name = item.get('meterName', '').lower()
                
                if 'load balancer' in meter_name:
                    network_breakdown['load_balancer'] += cost
                elif 'public ip' in meter_name or 'ip address' in meter_name:
                    network_breakdown['public_ip'] += cost
                elif 'data transfer' in meter_name:
                    network_breakdown['data_transfer'] += cost
                elif 'bandwidth' in meter_name:
                    network_breakdown['bandwidth'] += cost
                
                network_breakdown['total'] += cost
            
            return network_breakdown
            
        except Exception as e:
            logger.warning(f"⚠️ Network cost collection failed: {e}")
            return {'total': 0, 'load_balancer': 0, 'public_ip': 0, 'data_transfer': 0, 'bandwidth': 0}
    
    def _collect_monitoring_costs(self, resource_group: str, subscription_id: str, days: int) -> Dict:
        """Collect monitoring and logging costs"""
        
        monitoring_query = f"""
        az consumption usage list \\
            --subscription {subscription_id} \\
            --start-date {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} \\
            --end-date {datetime.now().strftime('%Y-%m-%d')} \\
            --query "[?contains(instanceName, '{resource_group}') && (contains(meterName, 'Monitor') || contains(meterName, 'Log Analytics') || contains(meterName, 'Application Insights') || contains(meterName, 'Data Ingestion') || contains(meterName, 'Data Retention'))].{{meterName:meterName, quantity:quantity, pretaxCost:pretaxCost}}" \\
            --output json
        """
        
        try:
            result = subprocess.run(monitoring_query, shell=True, capture_output=True, text=True, check=True)
            monitoring_data = json.loads(result.stdout)
            
            monitoring_breakdown = {
                'log_analytics': 0,
                'application_insights': 0,
                'azure_monitor': 0,
                'data_ingestion': 0,
                'data_retention': 0,
                'total': 0
            }
            
            for item in monitoring_data:
                cost = float(item.get('pretaxCost', 0))
                meter_name = item.get('meterName', '').lower()
                
                if 'log analytics' in meter_name:
                    monitoring_breakdown['log_analytics'] += cost
                elif 'application insights' in meter_name:
                    monitoring_breakdown['application_insights'] += cost
                elif 'monitor' in meter_name:
                    monitoring_breakdown['azure_monitor'] += cost
                elif 'data ingestion' in meter_name:
                    monitoring_breakdown['data_ingestion'] += cost
                elif 'data retention' in meter_name:
                    monitoring_breakdown['data_retention'] += cost
                
                monitoring_breakdown['total'] += cost
            
            return monitoring_breakdown
            
        except Exception as e:
            logger.warning(f"⚠️ Monitoring cost collection failed: {e}")
            return {'total': 0, 'log_analytics': 0, 'application_insights': 0, 'azure_monitor': 0, 
                   'data_ingestion': 0, 'data_retention': 0}
    
    def _collect_backup_costs(self, resource_group: str, subscription_id: str, days: int) -> Dict:
        """Collect backup and disaster recovery costs"""
        
        backup_query = f"""
        az consumption usage list \\
            --subscription {subscription_id} \\
            --start-date {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} \\
            --end-date {datetime.now().strftime('%Y-%m-%d')} \\
            --query "[?contains(instanceName, '{resource_group}') && (contains(meterName, 'Backup') || contains(meterName, 'Site Recovery') || contains(meterName, 'Archive') || contains(serviceName, 'Backup'))].{{meterName:meterName, quantity:quantity, pretaxCost:pretaxCost}}" \\
            --output json
        """
        
        try:
            result = subprocess.run(backup_query, shell=True, capture_output=True, text=True, check=True)
            backup_data = json.loads(result.stdout)
            
            backup_breakdown = {
                'backup_storage': 0,
                'backup_operations': 0,
                'site_recovery': 0,
                'archive_storage': 0,
                'total': 0
            }
            
            for item in backup_data:
                cost = float(item.get('pretaxCost', 0))
                meter_name = item.get('meterName', '').lower()
                
                if 'backup' in meter_name and 'storage' in meter_name:
                    backup_breakdown['backup_storage'] += cost
                elif 'backup' in meter_name:
                    backup_breakdown['backup_operations'] += cost
                elif 'site recovery' in meter_name:
                    backup_breakdown['site_recovery'] += cost
                elif 'archive' in meter_name:
                    backup_breakdown['archive_storage'] += cost
                
                backup_breakdown['total'] += cost
            
            return backup_breakdown
            
        except Exception as e:
            logger.warning(f"⚠️ Backup cost collection failed: {e}")
            return {'total': 0, 'backup_storage': 0, 'backup_operations': 0, 'site_recovery': 0, 'archive_storage': 0}
    
    def _collect_security_costs(self, resource_group: str, subscription_id: str, days: int) -> Dict:
        """Collect security service costs"""
        
        security_query = f"""
        az consumption usage list \\
            --subscription {subscription_id} \\
            --start-date {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} \\
            --end-date {datetime.now().strftime('%Y-%m-%d')} \\
            --query "[?contains(instanceName, '{resource_group}') && (contains(meterName, 'Key Vault') || contains(meterName, 'Security Center') || contains(meterName, 'Defender') || contains(serviceName, 'Key Vault'))].{{meterName:meterName, quantity:quantity, pretaxCost:pretaxCost}}" \\
            --output json
        """
        
        try:
            result = subprocess.run(security_query, shell=True, capture_output=True, text=True, check=True)
            security_data = json.loads(result.stdout)
            
            security_breakdown = {
                'key_vault': 0,
                'security_center': 0,
                'defender': 0,
                'total': 0
            }
            
            for item in security_data:
                cost = float(item.get('pretaxCost', 0))
                meter_name = item.get('meterName', '').lower()
                
                if 'key vault' in meter_name:
                    security_breakdown['key_vault'] += cost
                elif 'security center' in meter_name:
                    security_breakdown['security_center'] += cost
                elif 'defender' in meter_name:
                    security_breakdown['defender'] += cost
                
                security_breakdown['total'] += cost
            
            return security_breakdown
            
        except Exception as e:
            logger.warning(f"⚠️ Security cost collection failed: {e}")
            return {'total': 0, 'key_vault': 0, 'security_center': 0, 'defender': 0}
    
    def _collect_addon_costs(self, resource_group: str, subscription_id: str, days: int) -> Dict:
        """Collect addon service costs"""
        
        addon_query = f"""
        az consumption usage list \\
            --subscription {subscription_id} \\
            --start-date {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} \\
            --end-date {datetime.now().strftime('%Y-%m-%d')} \\
            --query "[?contains(instanceName, '{resource_group}') && (contains(meterName, 'Service Bus') || contains(meterName, 'Event Grid') || contains(meterName, 'API Management') || contains(meterName, 'Application Gateway') || contains(meterName, 'Redis'))].{{meterName:meterName, quantity:quantity, pretaxCost:pretaxCost}}" \\
            --output json
        """
        
        try:
            result = subprocess.run(addon_query, shell=True, capture_output=True, text=True, check=True)
            addon_data = json.loads(result.stdout)
            
            addon_breakdown = {
                'service_bus': 0,
                'event_grid': 0,
                'api_management': 0,
                'application_gateway': 0,
                'redis_cache': 0,
                'total': 0
            }
            
            for item in addon_data:
                cost = float(item.get('pretaxCost', 0))
                meter_name = item.get('meterName', '').lower()
                
                if 'service bus' in meter_name:
                    addon_breakdown['service_bus'] += cost
                elif 'event grid' in meter_name:
                    addon_breakdown['event_grid'] += cost
                elif 'api management' in meter_name:
                    addon_breakdown['api_management'] += cost
                elif 'application gateway' in meter_name:
                    addon_breakdown['application_gateway'] += cost
                elif 'redis' in meter_name:
                    addon_breakdown['redis_cache'] += cost
                
                addon_breakdown['total'] += cost
            
            return addon_breakdown
            
        except Exception as e:
            logger.warning(f"⚠️ Addon cost collection failed: {e}")
            return {'total': 0, 'service_bus': 0, 'event_grid': 0, 'api_management': 0, 
                   'application_gateway': 0, 'redis_cache': 0}
    
    def _analyze_cost_trends(self, resource_group: str, cluster_name: str, 
                           subscription_id: str) -> Dict:
        """Analyze cost trends over time for better optimization insights"""
        
        try:
            # Get 90-day trend data
            trend_query = f"""
            az costmanagement query \\
                --subscription {subscription_id} \\
                --type 'ActualCost' \\
                --timeframe 'Custom' \\
                --time-period from={((datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))} to={datetime.now().strftime('%Y-%m-%d')} \\
                --dataset '{{"granularity": "Monthly", "aggregation": {{"totalCost": {{"name": "PreTaxCost", "function": "Sum"}}}}, "grouping": [{{"type": "Dimension", "name": "ResourceGroupName"}}], "filter": {{"dimensions": {{"name": "ResourceGroupName", "operator": "In", "values": ["{resource_group}"]}}}}}}' \\
                --output json
            """
            
            result = subprocess.run(trend_query, shell=True, capture_output=True, text=True, check=True)
            trend_data = json.loads(result.stdout)
            
            monthly_costs = []
            if 'properties' in trend_data and 'rows' in trend_data['properties']:
                for row in trend_data['properties']['rows']:
                    if len(row) >= 2:
                        cost = float(row[0]) if row[0] else 0
                        date = row[1] if len(row) > 1 else ''
                        monthly_costs.append({'date': date, 'cost': cost})
            
            # Calculate trend metrics
            if len(monthly_costs) >= 2:
                recent_cost = monthly_costs[-1]['cost']
                previous_cost = monthly_costs[-2]['cost']
                trend_pct = ((recent_cost - previous_cost) / previous_cost * 100) if previous_cost > 0 else 0
            else:
                trend_pct = 0
            
            return {
                'monthly_costs': monthly_costs,
                'trend_percentage': trend_pct,
                'trend_direction': 'increasing' if trend_pct > 5 else 'decreasing' if trend_pct < -5 else 'stable'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Cost trend analysis failed: {e}")
            return {'monthly_costs': [], 'trend_percentage': 0, 'trend_direction': 'unknown'}
    
    def _collect_resource_utilization_context(self, resource_group: str, 
                                            cluster_name: str, subscription_id: str) -> Dict:
        """Collect resource utilization context for better optimization recommendations"""
        
        context = {
            'node_utilization': {},
            'workload_patterns': {},
            'scaling_behavior': {},
            'resource_allocation': {}
        }
        
        try:
            # Get node utilization data
            node_query = f"az aks nodepool list --resource-group {resource_group} --cluster-name {cluster_name} --subscription {subscription_id}"
            result = subprocess.run(node_query, shell=True, capture_output=True, text=True, check=True)
            node_data = json.loads(result.stdout)
            
            context['node_utilization'] = {
                'total_nodes': sum(pool.get('count', 0) for pool in node_data),
                'node_pools': len(node_data),
                'autoscaling_enabled': any(pool.get('enableAutoScaling', False) for pool in node_data),
                'spot_nodes': sum(pool.get('count', 0) for pool in node_data if pool.get('scaleSetPriority') == 'Spot')
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Resource context collection failed: {e}")
        
        return context
    
    def _calculate_enhanced_breakdown(self, comprehensive_data: Dict) -> Dict:
        """Calculate enhanced cost breakdown for analysis"""
        
        base_cost = comprehensive_data.get('total_cost', 0) - comprehensive_data.get('additional_categories_cost', 0)
        
        breakdown = {
            'compute_costs': base_cost * 0.7,  # Estimate 70% is compute
            'storage_costs': base_cost * 0.15, # Estimate 15% is storage
            'network_costs': comprehensive_data.get('network_costs', {}).get('total', 0),
            'monitoring_costs': comprehensive_data.get('monitoring_costs', {}).get('total', 0),
            'security_costs': comprehensive_data.get('security_costs', {}).get('total', 0),
            'backup_costs': comprehensive_data.get('backup_costs', {}).get('total', 0),
            'addon_costs': comprehensive_data.get('addon_costs', {}).get('total', 0),
            'other_costs': base_cost * 0.15  # Remaining 15%
        }
        
        # Calculate percentages
        total = sum(breakdown.values())
        if total > 0:
            breakdown_pct = {f"{k}_percentage": (v/total)*100 for k, v in breakdown.items()}
            breakdown.update(breakdown_pct)
        
        return breakdown
    
    def _execute_azure_cost_query(self, query: Dict, subscription_id: str) -> Dict:
        """Execute Azure cost query using Azure CLI"""
        
        query_json = json.dumps(query).replace('"', '\\"')
        cmd = f'az costmanagement query --subscription {subscription_id} --type ActualCost --dataset \'{query_json}\' --output json'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    
    def _process_base_cost_results(self, cost_data: Dict, resource_group: str, cluster_name: str) -> Dict:
        """Process base cost query results"""
        
        processed_data = {
            'total_cost': 0,
            'cost_breakdown': {},
            'daily_costs': []
        }
        
        if 'properties' in cost_data and 'rows' in cost_data['properties']:
            for row in cost_data['properties']['rows']:
                if len(row) >= 2:
                    cost = float(row[0]) if row[0] else 0
                    service = row[1] if len(row) > 1 else 'Unknown'
                    
                    processed_data['total_cost'] += cost
                    processed_data['cost_breakdown'][service] = processed_data['cost_breakdown'].get(service, 0) + cost
        
        return processed_data
    
    def _get_fallback_cost_data(self, resource_group: str, cluster_name: str,
                               subscription_id: str, days: int) -> Dict:
        """Fallback cost data collection to ensure tool doesn't break"""
        
        logger.warning("⚠️ Using fallback cost data collection")
        
        return {
            'total_cost': 0,
            'cost_breakdown': {},
            'network_costs': {'total': 0},
            'monitoring_costs': {'total': 0},
            'security_costs': {'total': 0},
            'backup_costs': {'total': 0},
            'addon_costs': {'total': 0},
            'cost_trends': {'trend_percentage': 0, 'trend_direction': 'unknown'},
            'resource_context': {},
            'enhanced_breakdown': {}
        }


def integrate_comprehensive_cost_collection(resource_group: str, cluster_name: str,
                                          subscription_id: str, days: int = 30) -> Dict:
    """
    Integration function to enhance existing cost collection
    
    This can be called from your existing cost processor to add comprehensive
    cost data collection without breaking current functionality.
    """
    
    logger.info("🔄 Integrating comprehensive cost collection...")
    
    try:
        collector = ComprehensiveCostCollector()
        comprehensive_data = collector.collect_comprehensive_cost_data(
            resource_group, cluster_name, subscription_id, days
        )
        
        logger.info(f"✅ Comprehensive cost collection complete: ${comprehensive_data.get('total_cost', 0):.2f}")
        
        return comprehensive_data
        
    except Exception as e:
        logger.error(f"❌ Comprehensive cost collection failed: {e}")
        # Return minimal structure to prevent breaking existing code
        return {
            'total_cost': 0,
            'cost_breakdown': {},
            'enhanced_breakdown': {}
        }