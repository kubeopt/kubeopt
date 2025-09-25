#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Enhanced Cost Data Processing for AKS Cost Optimization - kubevista
==================================================================
Comprehensive cost processing with advanced allocation methods based on Azure best practices.
Includes all cost components: networking, system pods, idle resources, add-ons, etc.
"""

import json
# subprocess removed - using Azure SDK instead
import threading
import time
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from shared.config.config import logger
from shared.utils.utils import validate_cost_data


@dataclass
class CostAllocationConfig:
    """Configuration for cost allocation strategies"""
    system_pod_percentage: float = 0.10  # 10% for system pods
    idle_resource_threshold: float = 0.15  # 15% threshold for idle detection
    load_balancer_allocation_method: str = "proportional"  # proportional or equal
    cross_zone_data_transfer_factor: float = 0.02  # 2% of networking costs
    enable_advanced_allocation: bool = True


class EnhancedAKSCostProcessor:
    """Enhanced AKS Cost Processor with comprehensive cost allocation"""
    
    def __init__(self, config: CostAllocationConfig = None):
        self.config = config or CostAllocationConfig()
        self.cost_allocation_rules = self._initialize_allocation_rules()
    
    def _initialize_allocation_rules(self) -> Dict:
        """Initialize advanced cost allocation rules"""
        return {
            'system_components': {
                'kube-system': 0.4,  # 40% of system costs
                'kube-public': 0.1,
                'kube-node-lease': 0.1,
                'azure-system': 0.3,
                'monitoring': 0.1
            },
            'networking_distribution': {
                'load_balancer': 0.4,
                'public_ip': 0.2,
                'data_transfer': 0.25,
                'dns': 0.05,
                'other_networking': 0.1
            },
            'storage_types': {
                'premium_ssd': {'weight': 3.0, 'iops_factor': 2.0},
                'standard_ssd': {'weight': 2.0, 'iops_factor': 1.5},
                'standard_hdd': {'weight': 1.0, 'iops_factor': 1.0}
            }
        }

    def process_aks_cost_data_enhanced(self, cost_data_json: Dict) -> pd.DataFrame:
        """Enhanced cost data processing with comprehensive categorization"""
        cost_df_data = []
        
        logger.info(f"🔄 Processing enhanced AKS cost data, size: {len(str(cost_data_json))} bytes")
        
        if 'properties' in cost_data_json and 'rows' in cost_data_json['properties']:
            column_names = self._extract_column_names(cost_data_json)
            cost_rows = cost_data_json['properties'].get('rows', [])
            
            logger.info(f"📊 Found {len(cost_rows)} cost rows with columns: {column_names}")
            
            for row_idx, row in enumerate(cost_rows):
                try:
                    cost_entry = self._process_cost_row(row, column_names, row_idx)
                    if cost_entry and cost_entry['Cost'] > 0:
                        cost_df_data.append(cost_entry)
                except Exception as row_error:
                    logger.warning(f"⚠️ Error processing row {row_idx}: {row_error}")
                    continue
        
        # Create enhanced DataFrame
        cost_df = pd.DataFrame(cost_df_data)
        
        if cost_df.empty:
            logger.warning("⚠️ No valid cost data processed")
            return self._create_empty_cost_dataframe()
        
        # Apply enhanced categorization and allocation
        cost_df = self._apply_enhanced_categorization(cost_df)
        cost_df = self._calculate_advanced_allocations(cost_df)
        
        # Add comprehensive metadata
        cost_df.attrs.update({
            'is_sample_data': False,
            'data_source': 'Enhanced Azure Cost Management API',
            'total_cost': cost_df['Cost'].sum(),
            'categories': cost_df['Category'].unique().tolist(),
            'subcategories': cost_df['Subcategory'].unique().tolist(),
            'enhancement_level': 'comprehensive',
            'allocation_method': 'advanced_proportional',
            'timestamp': datetime.now().isoformat(),
            'system_cost_allocated': True,
            'idle_cost_calculated': True,
            'networking_detailed': True
        })
        
        self._log_enhanced_cost_details(cost_df)
        return cost_df

    def _generate_cost_optimization_insights(self, cost_df: pd.DataFrame, multiplier: float) -> Dict:
        """Generate actionable cost optimization insights for each service category"""
        insights = {}
        
        # Group by category and generate insights
        for category in cost_df['Category'].unique():
            category_data = cost_df[cost_df['Category'] == category]
            category_cost = float(category_data['Cost'].sum()) * multiplier
            
            if category_cost > 0:
                # Get optimization tips from metadata
                optimization_tips = []
                cost_drivers = []
                
                for _, row in category_data.iterrows():
                    metadata = row.get('CostMetadata', {})
                    if 'optimization_tip' in metadata:
                        tip = metadata['optimization_tip']
                        if tip not in optimization_tips:
                            optimization_tips.append(tip)
                    if 'cost_driver' in metadata:
                        driver = metadata['cost_driver']
                        if driver not in cost_drivers:
                            cost_drivers.append(driver)
                
                # Generate priority level based on cost
                if category_cost > 100:
                    priority = 'High'
                elif category_cost > 50:
                    priority = 'Medium'
                else:
                    priority = 'Low'
                
                insights[category] = {
                    'monthly_cost': category_cost,
                    'priority': priority,
                    'optimization_tips': optimization_tips,
                    'cost_drivers': cost_drivers,
                    'service_count': len(category_data),
                    'subcategories': category_data['Subcategory'].unique().tolist()
                }
        
        return insights

    def _extract_column_names(self, cost_data_json: Dict) -> List[str]:
        """Extract and validate column names"""
        columns = cost_data_json['properties'].get('columns', [])
        column_names = [col['name'] for col in columns if 'name' in col]
        
        # Validate required columns
        required_columns = ['PreTaxCost', 'ResourceType', 'ResourceGroupName', 'ServiceName']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            logger.warning(f"⚠️ Missing required columns: {missing_columns}")
        
        return column_names

    def _process_cost_row(self, row: List, column_names: List[str], row_idx: int) -> Optional[Dict]:
        """Process individual cost row with enhanced data extraction"""
        if len(row) < len(column_names):
            return None
        
        # Create column mapping
        row_data = dict(zip(column_names, row))
        
        # Extract enhanced cost information
        cost = float(row_data.get('PreTaxCost', 0)) if row_data.get('PreTaxCost') else 0
        resource_type = str(row_data.get('ResourceType', ''))
        resource_group = str(row_data.get('ResourceGroupName', ''))
        service_name = str(row_data.get('ServiceName', ''))
        resource_id = str(row_data.get('ResourceId', ''))
        meter_category = str(row_data.get('MeterCategory', ''))
        
        # Use 'Meter' instead of 'MeterName' as it's a valid dimension
        meter_name = str(row_data.get('Meter', ''))
        if not meter_name:
            # Fallback to MeterSubcategory if Meter is empty
            meter_name = str(row_data.get('MeterSubcategory', ''))
        
        location = str(row_data.get('ResourceLocation', ''))
        
        # Enhanced categorization
        category, subcategory, cost_metadata = self._categorize_resource_enhanced(
            resource_type, service_name, meter_category, meter_name, resource_id, location
        )
        
        return {
            'Cost': cost,
            'ResourceType': resource_type,
            'ResourceGroup': resource_group,
            'Service': service_name,
            'ResourceId': resource_id,
            'MeterCategory': meter_category,
            'MeterName': meter_name,  # Keep this field name for compatibility
            'Location': location,
            'Category': category,
            'Subcategory': subcategory,
            'CostMetadata': cost_metadata,
            'RowIndex': row_idx
        }

    def _categorize_resource_enhanced(self, resource_type: str, service_name: str, 
                                    meter_category: str, meter_name: str, 
                                    resource_id: str, location: str) -> Tuple[str, str, Dict]:
        """Enhanced resource categorization with comprehensive Azure service mapping"""
        
        resource_type_lower = resource_type.lower()
        service_name_lower = service_name.lower()
        meter_category_lower = meter_category.lower()
        meter_name_lower = meter_name.lower()
        
        category = "Uncategorized"
        subcategory = "Unknown Service"
        cost_metadata = {}
        
        # === AKS CONTROL PLANE (Enhanced) ===
        if "microsoft.containerservice/managedclusters" in resource_type_lower:
            category = "AKS Control Plane"
            if "standard" in meter_name_lower:
                subcategory = "Standard Tier ($0.10/hr)"
                cost_metadata = {"tier": "standard", "hourly_base": 0.10}
            elif "premium" in meter_name_lower:
                subcategory = "Premium Tier ($0.60/hr)"
                cost_metadata = {"tier": "premium", "hourly_base": 0.60}
            else:
                subcategory = "AKS Management"
                cost_metadata = {"tier": "free"}
        
        # === NODE POOLS (Enhanced with VM series detection) ===
        elif "microsoft.compute/virtualmachinescalesets" in resource_type_lower:
            category = "Node Pools"
            vm_series = self._detect_vm_series(service_name_lower, meter_name_lower)
            subcategory = f"{vm_series['series']} ({vm_series['description']})"
            cost_metadata = {
                "vm_series": vm_series['series'],
                "performance_tier": vm_series['tier'],
                "compute_optimized": vm_series['compute_optimized']
            }
        
        # === STORAGE (Enhanced with performance tiers) ===
        elif "microsoft.compute/disks" in resource_type_lower or "microsoft.storage" in resource_type_lower or "storage" in meter_category_lower:
            category = "Storage"
            storage_info = self._categorize_storage_enhanced(meter_name_lower, service_name_lower, resource_type_lower)
            subcategory = storage_info['type']
            cost_metadata = storage_info['metadata']
        
        # === NETWORKING (Comprehensive breakdown) ===
        elif "microsoft.network" in resource_type_lower or "networking" in meter_category_lower:
            category = "Networking"
            networking_info = self._categorize_networking_enhanced(
                resource_type_lower, meter_name_lower, meter_category_lower
            )
            subcategory = networking_info['type']
            cost_metadata = networking_info['metadata']
        
        # === APPLICATION SERVICES (New category) ===
        elif self._is_application_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "Application Services"
            app_service_info = self._categorize_application_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = app_service_info['type']
            cost_metadata = app_service_info['metadata']
        
        # === DATA SERVICES (New category) ===
        elif self._is_data_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "Data Services"
            data_service_info = self._categorize_data_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = data_service_info['type']
            cost_metadata = data_service_info['metadata']
        
        # === INTEGRATION SERVICES (New category) ===
        elif self._is_integration_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "Integration Services"
            integration_info = self._categorize_integration_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = integration_info['type']
            cost_metadata = integration_info['metadata']
        
        # === DEVOPS & CI/CD (New category) ===
        elif self._is_devops_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "DevOps & CI/CD"
            devops_info = self._categorize_devops_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = devops_info['type']
            cost_metadata = devops_info['metadata']
        
        # === BACKUP & RECOVERY (New category) ===
        elif self._is_backup_recovery_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "Backup & Recovery"
            backup_info = self._categorize_backup_recovery_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = backup_info['type']
            cost_metadata = backup_info['metadata']
        
        # === GOVERNANCE & COMPLIANCE (New category) ===
        elif self._is_governance_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "Governance & Compliance"
            governance_info = self._categorize_governance_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = governance_info['type']
            cost_metadata = governance_info['metadata']
        
        # === CONTAINER REGISTRY ===
        elif "microsoft.containerregistry" in resource_type_lower:
            category = "Container Registry"
            if "premium" in meter_name_lower:
                subcategory = "ACR Premium"
            elif "standard" in meter_name_lower:
                subcategory = "ACR Standard"
            else:
                subcategory = "ACR Basic"
            cost_metadata = {"registry_tier": subcategory.lower()}
        
        # === MONITORING & OBSERVABILITY ===
        elif any(service in resource_type_lower for service in 
                ["microsoft.operationalinsights", "microsoft.insights", "microsoft.monitor"]):
            category = "Monitoring"
            subcategory = self._categorize_monitoring_service(meter_name_lower, meter_category_lower)
            cost_metadata = {"observability_component": True}
        
        # === SECURITY & COMPLIANCE ===
        elif "microsoft.security" in resource_type_lower or "defender" in meter_name_lower:
            category = "Security"
            subcategory = "Azure Defender for Containers"
            cost_metadata = {"security_service": True}
        
        # === KEY VAULT ===
        elif "microsoft.keyvault" in resource_type_lower:
            category = "Key Vault"
            subcategory = "Key Management"
            cost_metadata = {"security_component": True}
        
        # === BANDWIDTH & DATA TRANSFER ===
        elif "bandwidth" in meter_category_lower or "data transfer" in meter_name_lower:
            category = "Data Transfer"
            subcategory = self._categorize_data_transfer(meter_name_lower, location)
            cost_metadata = {"transfer_type": subcategory.lower()}
        
        # === SUPPORT & MANAGEMENT (New category) ===
        elif self._is_support_management_service(resource_type_lower, service_name_lower, meter_name_lower):
            category = "Support & Management"
            support_info = self._categorize_support_management_service(resource_type_lower, service_name_lower, meter_name_lower)
            subcategory = support_info['type']
            cost_metadata = support_info['metadata']
        
        return category, subcategory, cost_metadata

    def _detect_vm_series(self, service_name: str, meter_name: str) -> Dict:
        """Detect VM series and characteristics"""
        vm_patterns = {
            'standard_d': {'series': 'D-Series', 'description': 'General Purpose', 'tier': 'standard', 'compute_optimized': False},
            'standard_e': {'series': 'E-Series', 'description': 'Memory Optimized', 'tier': 'standard', 'compute_optimized': False},
            'standard_f': {'series': 'F-Series', 'description': 'Compute Optimized', 'tier': 'standard', 'compute_optimized': True},
            'standard_b': {'series': 'B-Series', 'description': 'Burstable', 'tier': 'basic', 'compute_optimized': False},
            'standard_a': {'series': 'A-Series', 'description': 'Basic', 'tier': 'basic', 'compute_optimized': False},
            'standard_nc': {'series': 'NC-Series', 'description': 'GPU Compute', 'tier': 'premium', 'compute_optimized': True},
            'standard_nv': {'series': 'NV-Series', 'description': 'GPU Visualization', 'tier': 'premium', 'compute_optimized': True}
        }
        
        combined_text = f"{service_name} {meter_name}".lower()
        
        for pattern, info in vm_patterns.items():
            if pattern in combined_text:
                return info
        
        return {'series': 'Unknown', 'description': 'Unidentified VM Type', 'tier': 'unknown', 'compute_optimized': False}

    def _categorize_storage_enhanced(self, meter_name: str, service_name: str, resource_type: str = "") -> Dict:
        """Enhanced storage categorization with performance characteristics"""
        storage_types = {
            'premium_ssd': {
                'type': 'Premium SSD',
                'metadata': {'performance_tier': 'premium', 'iops_capability': 'high', 'use_case': 'production'}
            },
            'standardssd': {
                'type': 'Standard SSD',
                'metadata': {'performance_tier': 'standard', 'iops_capability': 'medium', 'use_case': 'general'}
            },
            'standard': {
                'type': 'Standard HDD',
                'metadata': {'performance_tier': 'basic', 'iops_capability': 'low', 'use_case': 'archive'}
            },
            'ultra': {
                'type': 'Ultra SSD',
                'metadata': {'performance_tier': 'ultra', 'iops_capability': 'extreme', 'use_case': 'high_performance'}
            }
        }
        
        combined_text = f"{meter_name} {service_name}".lower()
        
        # Check for Azure Files, Blob Storage, etc.
        if "files" in combined_text:
            return {
                'type': 'Azure Files',
                'metadata': {'performance_tier': 'standard', 'iops_capability': 'medium', 'use_case': 'file_shares'}
            }
        elif "blob" in combined_text:
            return {
                'type': 'Azure Blob Storage',
                'metadata': {'performance_tier': 'standard', 'iops_capability': 'high', 'use_case': 'object_storage'}
            }
        elif "microsoft.storage" in resource_type.lower():
            return {
                'type': 'Azure Storage Account',
                'metadata': {'performance_tier': 'standard', 'iops_capability': 'medium', 'use_case': 'general_storage'}
            }
        
        for pattern, info in storage_types.items():
            if pattern in combined_text:
                return info
        
        return {
            'type': 'Unknown Storage',
            'metadata': {'performance_tier': 'unknown', 'iops_capability': 'unknown', 'use_case': 'unknown'}
        }

    def _categorize_networking_enhanced(self, resource_type: str, meter_name: str, meter_category: str) -> Dict:
        """Enhanced networking categorization"""
        networking_types = {
            'loadbalancer': {
                'type': 'Load Balancer',
                'metadata': {'component': 'load_balancing', 'allocation_weight': 2.0}
            },
            'publicipaddress': {
                'type': 'Public IP Addresses',
                'metadata': {'component': 'public_connectivity', 'allocation_weight': 1.5}
            },
            'bandwidth': {
                'type': 'Bandwidth',
                'metadata': {'component': 'data_transfer', 'allocation_weight': 1.0}
            },
            'dns': {
                'type': 'DNS Services',
                'metadata': {'component': 'name_resolution', 'allocation_weight': 0.5}
            },
            'virtual network': {
                'type': 'Virtual Network',
                'metadata': {'component': 'network_infrastructure', 'allocation_weight': 1.0}
            },
            'network security group': {
                'type': 'Network Security Groups',
                'metadata': {'component': 'network_security', 'allocation_weight': 0.5}
            }
        }
        
        combined_text = f"{resource_type} {meter_name} {meter_category}".lower()
        
        for pattern, info in networking_types.items():
            if pattern in combined_text:
                return info
        
        return {
            'type': 'Other Networking',
            'metadata': {'component': 'networking_other', 'allocation_weight': 1.0}
        }

    def _categorize_monitoring_service(self, meter_name: str, meter_category: str) -> str:
        """Categorize monitoring and observability services"""
        if "log analytics" in meter_name or "logs" in meter_category:
            return "Log Analytics"
        elif "application insights" in meter_name:
            return "Application Insights"
        elif "metrics" in meter_name:
            return "Azure Metrics"
        elif "alerts" in meter_name:
            return "Alert Rules"
        else:
            return "Monitoring Services"

    def _categorize_data_transfer(self, meter_name: str, location: str) -> str:
        """Categorize data transfer types"""
        if "outbound" in meter_name:
            return "Outbound Data Transfer"
        elif "inbound" in meter_name:
            return "Inbound Data Transfer"
        elif "zone" in meter_name:
            return "Cross-Zone Data Transfer"
        elif "region" in meter_name:
            return "Cross-Region Data Transfer"
        else:
            return "Data Transfer"

    # === NEW ENHANCED CATEGORIZATION METHODS ===
    
    def _is_application_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is an application service"""
        app_service_indicators = [
            "microsoft.web", "microsoft.apimanagement", "microsoft.cdn",
            "microsoft.frontdoor", "microsoft.trafficmanager", "microsoft.signalr",
            "microsoft.logic", "microsoft.search", "microsoft.cognitiveservices",
            "application gateway", "app service", "function app", "api management"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in app_service_indicators)
    
    def _categorize_application_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize application services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "microsoft.web" in resource_type or "app service" in combined_text:
            return {
                'type': 'App Service',
                'metadata': {'optimization_tip': 'Consider scaling down unused app service plans', 'cost_driver': 'compute_hours'}
            }
        elif "microsoft.apimanagement" in resource_type or "api management" in combined_text:
            return {
                'type': 'API Management',
                'metadata': {'optimization_tip': 'Review API call volumes and tier selection', 'cost_driver': 'api_calls'}
            }
        elif "microsoft.cdn" in resource_type or "cdn" in combined_text:
            return {
                'type': 'Content Delivery Network',
                'metadata': {'optimization_tip': 'Monitor bandwidth usage and cache hit ratios', 'cost_driver': 'bandwidth'}
            }
        elif "microsoft.frontdoor" in resource_type or "front door" in combined_text:
            return {
                'type': 'Azure Front Door',
                'metadata': {'optimization_tip': 'Review routing rules and reduce backend calls', 'cost_driver': 'requests'}
            }
        elif "microsoft.trafficmanager" in resource_type or "traffic manager" in combined_text:
            return {
                'type': 'Traffic Manager',
                'metadata': {'optimization_tip': 'Optimize DNS queries and endpoint health checks', 'cost_driver': 'dns_queries'}
            }
        elif "microsoft.signalr" in resource_type or "signalr" in combined_text:
            return {
                'type': 'SignalR Service',
                'metadata': {'optimization_tip': 'Monitor concurrent connections and message counts', 'cost_driver': 'connections'}
            }
        elif "microsoft.logic" in resource_type or "logic app" in combined_text:
            return {
                'type': 'Logic Apps',
                'metadata': {'optimization_tip': 'Optimize workflow triggers and actions', 'cost_driver': 'executions'}
            }
        elif "microsoft.search" in resource_type or "search" in combined_text:
            return {
                'type': 'Azure Cognitive Search',
                'metadata': {'optimization_tip': 'Right-size search units and storage', 'cost_driver': 'search_units'}
            }
        elif "microsoft.cognitiveservices" in resource_type or "cognitive" in combined_text:
            return {
                'type': 'Cognitive Services',
                'metadata': {'optimization_tip': 'Monitor API usage and consider batch processing', 'cost_driver': 'api_calls'}
            }
        elif "application gateway" in combined_text or "appgw" in combined_text:
            return {
                'type': 'Application Gateway',
                'metadata': {'optimization_tip': 'Review capacity units and consider v2 SKU', 'cost_driver': 'capacity_units'}
            }
        else:
            return {
                'type': 'Other Application Service',
                'metadata': {'optimization_tip': 'Review service usage and scaling configuration', 'cost_driver': 'usage'}
            }
    
    def _is_data_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is a data service"""
        data_service_indicators = [
            "microsoft.sql", "microsoft.documentdb", "microsoft.dbforpostgresql",
            "microsoft.dbformysql", "microsoft.dbformariadb", "microsoft.cache",
            "microsoft.analysisservices", "microsoft.datafactory", "microsoft.databricks",
            "microsoft.hdinsight", "microsoft.streamanalytics", "microsoft.synapse",
            "microsoft.eventgrid", "microsoft.eventhub", "microsoft.servicebus",
            "sql", "cosmos", "redis", "postgresql", "mysql", "mariadb"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in data_service_indicators)
    
    def _categorize_data_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize data services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "microsoft.sql" in resource_type or "sql database" in combined_text:
            return {
                'type': 'Azure SQL Database',
                'metadata': {'optimization_tip': 'Consider elastic pools and reserved capacity', 'cost_driver': 'compute_storage'}
            }
        elif "microsoft.documentdb" in resource_type or "cosmos" in combined_text:
            return {
                'type': 'Azure Cosmos DB',
                'metadata': {'optimization_tip': 'Optimize RU/s provisioning and indexing', 'cost_driver': 'request_units'}
            }
        elif "microsoft.cache" in resource_type or "redis" in combined_text:
            return {
                'type': 'Azure Cache for Redis',
                'metadata': {'optimization_tip': 'Right-size cache tier and monitor hit ratios', 'cost_driver': 'cache_size'}
            }
        elif any(db in combined_text for db in ["postgresql", "mysql", "mariadb"]):
            return {
                'type': 'Azure Database for Open Source',
                'metadata': {'optimization_tip': 'Consider reserved instances and storage optimization', 'cost_driver': 'compute_storage'}
            }
        elif "microsoft.databricks" in resource_type or "databricks" in combined_text:
            return {
                'type': 'Azure Databricks',
                'metadata': {'optimization_tip': 'Optimize cluster sizing and auto-termination', 'cost_driver': 'compute_hours'}
            }
        elif "microsoft.hdinsight" in resource_type or "hdinsight" in combined_text:
            return {
                'type': 'Azure HDInsight',
                'metadata': {'optimization_tip': 'Use autoscaling and spot instances where possible', 'cost_driver': 'compute_hours'}
            }
        elif "microsoft.synapse" in resource_type or "synapse" in combined_text:
            return {
                'type': 'Azure Synapse Analytics',
                'metadata': {'optimization_tip': 'Pause unused SQL pools and optimize DWU', 'cost_driver': 'compute_storage'}
            }
        elif "microsoft.datafactory" in resource_type or "data factory" in combined_text:
            return {
                'type': 'Azure Data Factory',
                'metadata': {'optimization_tip': 'Optimize pipeline runs and data movement', 'cost_driver': 'pipeline_runs'}
            }
        else:
            return {
                'type': 'Other Data Service',
                'metadata': {'optimization_tip': 'Review data service usage patterns', 'cost_driver': 'usage'}
            }
    
    def _is_integration_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is an integration service"""
        integration_indicators = [
            "microsoft.eventgrid", "microsoft.eventhub", "microsoft.servicebus",
            "microsoft.relay", "microsoft.notificationhubs", "microsoft.devices",
            "event grid", "event hub", "service bus", "iot hub", "notification hubs"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in integration_indicators)
    
    def _categorize_integration_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize integration services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "microsoft.eventgrid" in resource_type or "event grid" in combined_text:
            return {
                'type': 'Event Grid',
                'metadata': {'optimization_tip': 'Monitor event volumes and dead letter queues', 'cost_driver': 'events'}
            }
        elif "microsoft.eventhub" in resource_type or "event hub" in combined_text:
            return {
                'type': 'Event Hubs',
                'metadata': {'optimization_tip': 'Optimize throughput units and retention', 'cost_driver': 'throughput_units'}
            }
        elif "microsoft.servicebus" in resource_type or "service bus" in combined_text:
            return {
                'type': 'Service Bus',
                'metadata': {'optimization_tip': 'Right-size messaging units and optimize partitioning', 'cost_driver': 'messaging_units'}
            }
        elif "microsoft.devices" in resource_type or "iot hub" in combined_text:
            return {
                'type': 'IoT Hub',
                'metadata': {'optimization_tip': 'Optimize device-to-cloud messages and pricing tier', 'cost_driver': 'messages'}
            }
        elif "microsoft.notificationhubs" in resource_type or "notification" in combined_text:
            return {
                'type': 'Notification Hubs',
                'metadata': {'optimization_tip': 'Monitor push notification volumes', 'cost_driver': 'notifications'}
            }
        else:
            return {
                'type': 'Other Integration Service',
                'metadata': {'optimization_tip': 'Review message/event volumes', 'cost_driver': 'usage'}
            }
    
    def _is_devops_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is a DevOps service"""
        devops_indicators = [
            "microsoft.visualstudio", "microsoft.devtestlab", "azure devops", 
            "github", "visual studio", "devtest", "build", "release", "artifacts"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in devops_indicators)
    
    def _categorize_devops_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize DevOps services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "azure devops" in combined_text or "visual studio" in combined_text:
            return {
                'type': 'Azure DevOps',
                'metadata': {'optimization_tip': 'Review build minutes and test plans usage', 'cost_driver': 'build_minutes'}
            }
        elif "github" in combined_text:
            return {
                'type': 'GitHub Actions',
                'metadata': {'optimization_tip': 'Optimize workflow efficiency and self-hosted runners', 'cost_driver': 'compute_minutes'}
            }
        elif "microsoft.devtestlab" in resource_type or "devtest" in combined_text:
            return {
                'type': 'DevTest Labs',
                'metadata': {'optimization_tip': 'Set auto-shutdown policies and optimize VM sizes', 'cost_driver': 'compute_hours'}
            }
        elif "artifacts" in combined_text:
            return {
                'type': 'Azure Artifacts',
                'metadata': {'optimization_tip': 'Monitor package storage and downloads', 'cost_driver': 'storage_bandwidth'}
            }
        else:
            return {
                'type': 'Other DevOps Service',
                'metadata': {'optimization_tip': 'Review development and testing resource usage', 'cost_driver': 'usage'}
            }
    
    def _is_backup_recovery_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is a backup/recovery service"""
        backup_indicators = [
            "microsoft.recoveryservices", "microsoft.backup", "microsoft.dataprotection",
            "backup", "recovery", "site recovery", "vault"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in backup_indicators)
    
    def _categorize_backup_recovery_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize backup and recovery services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "microsoft.recoveryservices" in resource_type or "recovery services" in combined_text:
            return {
                'type': 'Recovery Services Vault',
                'metadata': {'optimization_tip': 'Review backup retention policies and redundancy', 'cost_driver': 'backup_storage'}
            }
        elif "site recovery" in combined_text:
            return {
                'type': 'Azure Site Recovery',
                'metadata': {'optimization_tip': 'Optimize replication frequency and target regions', 'cost_driver': 'replicated_instances'}
            }
        elif "backup" in combined_text:
            return {
                'type': 'Azure Backup',
                'metadata': {'optimization_tip': 'Optimize backup schedules and retention', 'cost_driver': 'backup_storage'}
            }
        else:
            return {
                'type': 'Other Backup Service',
                'metadata': {'optimization_tip': 'Review backup and recovery configurations', 'cost_driver': 'storage'}
            }
    
    def _is_governance_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is a governance service"""
        governance_indicators = [
            "microsoft.policyinsights", "microsoft.advisor", "microsoft.authorization",
            "microsoft.blueprint", "microsoft.managementgroups", "microsoft.compliance",
            "policy", "governance", "compliance", "advisor", "blueprint"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in governance_indicators)
    
    def _categorize_governance_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize governance services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "microsoft.policyinsights" in resource_type or "policy" in combined_text:
            return {
                'type': 'Azure Policy',
                'metadata': {'optimization_tip': 'Review policy assignments and compliance scans', 'cost_driver': 'evaluations'}
            }
        elif "microsoft.advisor" in resource_type or "advisor" in combined_text:
            return {
                'type': 'Azure Advisor',
                'metadata': {'optimization_tip': 'Usually minimal cost - review recommendations', 'cost_driver': 'assessments'}
            }
        elif "microsoft.blueprint" in resource_type or "blueprint" in combined_text:
            return {
                'type': 'Azure Blueprints',
                'metadata': {'optimization_tip': 'Monitor blueprint deployments and assignments', 'cost_driver': 'assignments'}
            }
        elif "compliance" in combined_text:
            return {
                'type': 'Compliance Services',
                'metadata': {'optimization_tip': 'Review compliance scanning frequency', 'cost_driver': 'scans'}
            }
        else:
            return {
                'type': 'Other Governance Service',
                'metadata': {'optimization_tip': 'Review governance tool usage', 'cost_driver': 'usage'}
            }
    
    def _is_support_management_service(self, resource_type: str, service_name: str, meter_name: str) -> bool:
        """Check if this is a support/management service"""
        support_indicators = [
            "microsoft.support", "microsoft.costmanagement", "microsoft.billing",
            "microsoft.consumption", "microsoft.advisor", "microsoft.resourcehealth",
            "support", "cost management", "billing", "consumption", "resource health"
        ]
        
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        return any(indicator in combined_text for indicator in support_indicators)
    
    def _categorize_support_management_service(self, resource_type: str, service_name: str, meter_name: str) -> Dict:
        """Categorize support and management services"""
        combined_text = f"{resource_type} {service_name} {meter_name}".lower()
        
        if "microsoft.support" in resource_type or "support" in combined_text:
            return {
                'type': 'Azure Support Plan',
                'metadata': {'optimization_tip': 'Review support plan tier vs actual usage', 'cost_driver': 'monthly_fee'}
            }
        elif "microsoft.costmanagement" in resource_type or "cost management" in combined_text:
            return {
                'type': 'Cost Management',
                'metadata': {'optimization_tip': 'Usually free - review export and alert usage', 'cost_driver': 'exports'}
            }
        elif "microsoft.billing" in resource_type or "billing" in combined_text:
            return {
                'type': 'Billing Services',
                'metadata': {'optimization_tip': 'Review billing account and profile setup', 'cost_driver': 'transactions'}
            }
        elif "microsoft.consumption" in resource_type or "consumption" in combined_text:
            return {
                'type': 'Consumption APIs',
                'metadata': {'optimization_tip': 'Monitor API call volumes', 'cost_driver': 'api_calls'}
            }
        elif "resource health" in combined_text:
            return {
                'type': 'Resource Health',
                'metadata': {'optimization_tip': 'Usually free - review health monitoring', 'cost_driver': 'checks'}
            }
        else:
            return {
                'type': 'Other Support Service',
                'metadata': {'optimization_tip': 'Review support and management tool usage', 'cost_driver': 'usage'}
            }

    def _apply_enhanced_categorization(self, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Apply enhanced categorization and cost allocation logic"""
        if cost_df.empty:
            return cost_df
        
        # Add allocation weights based on categories
        cost_df['AllocationWeight'] = cost_df.apply(self._calculate_allocation_weight, axis=1)
        
        # Add system vs user cost classification
        cost_df['CostType'] = cost_df.apply(self._classify_cost_type, axis=1)
        
        # Calculate cost distribution scores
        cost_df['DistributionScore'] = cost_df.apply(self._calculate_distribution_score, axis=1)
        
        return cost_df

    def _calculate_allocation_weight(self, row: pd.Series) -> float:
        """Calculate allocation weight for cost distribution"""
        category = row['Category']
        subcategory = row['Subcategory']
        
        # Base weights by category
        category_weights = {
            'Node Pools': 3.0,  # Highest weight - directly attributable
            'Storage': 2.5,
            'Networking': 2.0,
            'AKS Control Plane': 1.0,  # Shared cost
            'Container Registry': 1.5,
            'Monitoring': 1.0,
            'Security': 1.0,
            'Data Transfer': 2.0,
            'Key Vault': 0.5,
            'Application Services': 2.0,  # New category
            'Data Services': 2.5,  # New category - often expensive
            'Integration Services': 1.5,  # New category
            'DevOps & CI/CD': 1.0,  # New category
            'Backup & Recovery': 1.0,  # New category
            'Governance & Compliance': 0.5,  # New category - usually low cost
            'Support & Management': 0.5,  # New category - usually low cost
            'Uncategorized': 0.5  # Lowest weight for unknown services
        }
        
        base_weight = category_weights.get(category, 1.0)
        
        # Adjust based on subcategory
        if 'Premium' in subcategory:
            base_weight *= 1.2
        elif 'Basic' in subcategory:
            base_weight *= 0.8
        
        return base_weight

    def _classify_cost_type(self, row: pd.Series) -> str:
        """Classify cost as system, user, or shared"""
        category = row['Category']
        
        system_categories = ['AKS Control Plane', 'Monitoring', 'Security', 'Governance & Compliance', 'Support & Management']
        user_categories = ['Node Pools', 'Storage', 'Application Services', 'Data Services']
        shared_categories = ['Networking', 'Container Registry', 'Integration Services', 'DevOps & CI/CD', 'Backup & Recovery', 'Key Vault', 'Data Transfer']
        
        if category in system_categories:
            return 'system'
        elif category in user_categories:
            return 'user'
        elif category in shared_categories:
            return 'shared'
        else:
            return 'uncategorized'

    def _calculate_distribution_score(self, row: pd.Series) -> float:
        """Calculate how easily this cost can be distributed to namespaces"""
        cost_type = row['CostType']
        allocation_weight = row['AllocationWeight']
        
        if cost_type == 'user':
            return allocation_weight * 1.0  # Full distribution
        elif cost_type == 'shared':
            return allocation_weight * 0.7  # Partial distribution
        else:  # system
            return allocation_weight * 0.3  # Minimal distribution

    def _calculate_advanced_allocations(self, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced cost allocations including system and idle costs"""
        if cost_df.empty:
            return cost_df
        
        # Calculate system cost allocation
        cost_df = self._allocate_system_costs(cost_df)
        
        # Calculate idle resource costs
        cost_df = self._calculate_idle_costs(cost_df)
        
        # Apply networking cost distribution
        cost_df = self._distribute_networking_costs(cost_df)
        
        # Calculate add-on service allocations
        cost_df = self._allocate_addon_services(cost_df)
        
        return cost_df

    def _allocate_system_costs(self, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Allocate system costs (control plane, monitoring, etc.) across workloads"""
        system_costs = cost_df[cost_df['CostType'] == 'system']['Cost'].sum()
        
        if system_costs > 0:
            # Distribute system costs proportionally
            user_costs = cost_df[cost_df['CostType'] == 'user']['Cost'].sum()
            
            if user_costs > 0:
                system_allocation_rate = system_costs / user_costs
                cost_df.loc[cost_df['CostType'] == 'user', 'SystemCostAllocation'] = \
                    cost_df.loc[cost_df['CostType'] == 'user', 'Cost'] * system_allocation_rate
            else:
                cost_df['SystemCostAllocation'] = 0
        else:
            cost_df['SystemCostAllocation'] = 0
        
        return cost_df

    def _calculate_idle_costs(self, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate idle resource costs based on utilization patterns"""
        # For node pools, estimate idle costs
        node_costs = cost_df[cost_df['Category'] == 'Node Pools']
        
        if not node_costs.empty:
            # Estimate idle percentage (this would be enhanced with actual utilization data)
            estimated_idle_percentage = self.config.idle_resource_threshold
            
            cost_df.loc[cost_df['Category'] == 'Node Pools', 'IdleCost'] = \
                cost_df.loc[cost_df['Category'] == 'Node Pools', 'Cost'] * estimated_idle_percentage
        
        cost_df['IdleCost'] = cost_df.get('IdleCost', 0)
        return cost_df

    def _distribute_networking_costs(self, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Distribute networking costs using advanced allocation methods"""
        networking_costs = cost_df[cost_df['Category'] == 'Networking']
        
        for idx, row in networking_costs.iterrows():
            metadata = row.get('CostMetadata', {})
            allocation_method = metadata.get('allocation_method', 'proportional')
            
            if allocation_method == 'proportional':
                # Proportional to node costs
                cost_df.loc[idx, 'AllocationMethod'] = 'proportional_to_nodes'
            elif allocation_method == 'equal':
                # Equal distribution
                cost_df.loc[idx, 'AllocationMethod'] = 'equal_distribution'
        
        return cost_df

    def _allocate_addon_services(self, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Allocate add-on service costs (monitoring, security, etc.)"""
        addon_categories = [
            'Monitoring', 'Security', 'Container Registry', 'Application Services',
            'Data Services', 'Integration Services', 'DevOps & CI/CD', 'Backup & Recovery',
            'Governance & Compliance', 'Support & Management'
        ]
        
        for category in addon_categories:
            addon_costs = cost_df[cost_df['Category'] == category]
            
            if not addon_costs.empty:
                # Distribute based on namespace activity (simplified)
                cost_df.loc[cost_df['Category'] == category, 'AddonAllocation'] = \
                    cost_df.loc[cost_df['Category'] == category, 'Cost'] * 0.8  # 80% allocatable
        
        cost_df['AddonAllocation'] = cost_df.get('AddonAllocation', 0)
        return cost_df

    def extract_enhanced_cost_components(self, cost_df: pd.DataFrame, days: int, 
                                       monthly_equivalent_cost: float) -> Dict:
        """Enhanced cost component extraction with advanced allocation"""
        multiplier = 30/days if days != 30 else 1
        
        # Basic components (enhanced)
        node_cost = float(cost_df[cost_df['Category'] == 'Node Pools']['Cost'].sum()) * multiplier
        storage_cost = float(cost_df[cost_df['Category'] == 'Storage']['Cost'].sum()) * multiplier
        control_plane_cost = float(cost_df[cost_df['Category'] == 'AKS Control Plane']['Cost'].sum()) * multiplier
        
        # Enhanced networking breakdown
        networking_df = cost_df[cost_df['Category'] == 'Networking']
        load_balancer_cost = float(networking_df[networking_df['Subcategory'].str.contains('Load Balancer', na=False)]['Cost'].sum()) * multiplier
        public_ip_cost = float(networking_df[networking_df['Subcategory'].str.contains('Public IP', na=False)]['Cost'].sum()) * multiplier
        data_transfer_cost = float(networking_df[networking_df['Subcategory'].str.contains('Transfer', na=False)]['Cost'].sum()) * multiplier
        other_networking_cost = float(networking_df[~networking_df['Subcategory'].str.contains('Load Balancer|Public IP|Transfer', na=False)]['Cost'].sum()) * multiplier
        
        # Enhanced add-on services
        registry_cost = float(cost_df[cost_df['Category'] == 'Container Registry']['Cost'].sum()) * multiplier
        monitoring_cost = float(cost_df[cost_df['Category'] == 'Monitoring']['Cost'].sum()) * multiplier
        security_cost = float(cost_df[cost_df['Category'] == 'Security']['Cost'].sum()) * multiplier
        keyvault_cost = float(cost_df[cost_df['Category'] == 'Key Vault']['Cost'].sum()) * multiplier
        
        # New service categories
        application_services_cost = float(cost_df[cost_df['Category'] == 'Application Services']['Cost'].sum()) * multiplier
        data_services_cost = float(cost_df[cost_df['Category'] == 'Data Services']['Cost'].sum()) * multiplier
        integration_services_cost = float(cost_df[cost_df['Category'] == 'Integration Services']['Cost'].sum()) * multiplier
        devops_cost = float(cost_df[cost_df['Category'] == 'DevOps & CI/CD']['Cost'].sum()) * multiplier
        backup_recovery_cost = float(cost_df[cost_df['Category'] == 'Backup & Recovery']['Cost'].sum()) * multiplier
        governance_cost = float(cost_df[cost_df['Category'] == 'Governance & Compliance']['Cost'].sum()) * multiplier
        support_management_cost = float(cost_df[cost_df['Category'] == 'Support & Management']['Cost'].sum()) * multiplier
        
        # System and idle costs
        system_cost = float(cost_df[cost_df['CostType'] == 'system']['Cost'].sum()) * multiplier
        idle_cost = float(cost_df['IdleCost'].sum()) * multiplier if 'IdleCost' in cost_df.columns else 0
        
        # Remaining uncategorized costs
        categorized_categories = [
            'Node Pools', 'Storage', 'Networking', 'AKS Control Plane', 
            'Container Registry', 'Monitoring', 'Security', 'Key Vault',
            'Application Services', 'Data Services', 'Integration Services',
            'DevOps & CI/CD', 'Backup & Recovery', 'Governance & Compliance',
            'Support & Management', 'Data Transfer'
        ]
        other_categories = cost_df[~cost_df['Category'].isin(categorized_categories)]
        other_cost = float(other_categories['Cost'].sum()) * multiplier
        
        # Total networking cost
        total_networking_cost = load_balancer_cost + public_ip_cost + data_transfer_cost + other_networking_cost
        
        # Validation and reconciliation
        component_sum = (node_cost + storage_cost + total_networking_cost + control_plane_cost + 
                        registry_cost + monitoring_cost + security_cost + keyvault_cost + 
                        application_services_cost + data_services_cost + integration_services_cost +
                        devops_cost + backup_recovery_cost + governance_cost + support_management_cost + other_cost)
        
        logger.info(f"💰 Enhanced cost breakdown:")
        logger.info(f"   - Node Pools: ${node_cost:.2f}")
        logger.info(f"   - Storage: ${storage_cost:.2f}")
        logger.info(f"   - Load Balancers: ${load_balancer_cost:.2f}")
        logger.info(f"   - Public IPs: ${public_ip_cost:.2f}")
        logger.info(f"   - Data Transfer: ${data_transfer_cost:.2f}")
        logger.info(f"   - Control Plane: ${control_plane_cost:.2f}")
        logger.info(f"   - Container Registry: ${registry_cost:.2f}")
        logger.info(f"   - Monitoring: ${monitoring_cost:.2f}")
        logger.info(f"   - Security: ${security_cost:.2f}")
        logger.info(f"   - Application Services: ${application_services_cost:.2f}")
        logger.info(f"   - Data Services: ${data_services_cost:.2f}")
        logger.info(f"   - Integration Services: ${integration_services_cost:.2f}")
        logger.info(f"   - DevOps & CI/CD: ${devops_cost:.2f}")
        logger.info(f"   - Backup & Recovery: ${backup_recovery_cost:.2f}")
        logger.info(f"   - Governance & Compliance: ${governance_cost:.2f}")
        logger.info(f"   - Support & Management: ${support_management_cost:.2f}")
        logger.info(f"   - System Overhead: ${system_cost:.2f}")
        logger.info(f"   - Idle Resources: ${idle_cost:.2f}")
        logger.info(f"   - Other/Uncategorized: ${other_cost:.2f}")
        
        # Reconcile with expected total
        if abs(component_sum - monthly_equivalent_cost) > 1.0:
            logger.warning(f"⚠️ Cost reconciliation needed: {component_sum:.2f} vs {monthly_equivalent_cost:.2f}")
            adjustment_factor = monthly_equivalent_cost / component_sum if component_sum > 0 else 1
            
            # Apply proportional adjustment
            node_cost *= adjustment_factor
            storage_cost *= adjustment_factor
            total_networking_cost *= adjustment_factor
            control_plane_cost *= adjustment_factor
            registry_cost *= adjustment_factor
            monitoring_cost *= adjustment_factor
            security_cost *= adjustment_factor
            keyvault_cost *= adjustment_factor
            application_services_cost *= adjustment_factor
            data_services_cost *= adjustment_factor
            integration_services_cost *= adjustment_factor
            devops_cost *= adjustment_factor
            backup_recovery_cost *= adjustment_factor
            governance_cost *= adjustment_factor
            support_management_cost *= adjustment_factor
            other_cost *= adjustment_factor
        
        return {
            'total_cost': monthly_equivalent_cost,
            'node_cost': node_cost,
            'storage_cost': storage_cost,
            'networking_cost': total_networking_cost,
            'control_plane_cost': control_plane_cost,
            'registry_cost': registry_cost,
            'other_cost': other_cost,
            
            # Enhanced networking breakdown
            'load_balancer_cost': load_balancer_cost,
            'public_ip_cost': public_ip_cost,
            'data_transfer_cost': data_transfer_cost,
            'other_networking_cost': other_networking_cost,
            
            # Traditional add-on services
            'monitoring_cost': monitoring_cost,
            'security_cost': security_cost,
            'keyvault_cost': keyvault_cost,
            
            # New service categories with optimization insights
            'application_services_cost': application_services_cost,
            'data_services_cost': data_services_cost,
            'integration_services_cost': integration_services_cost,
            'devops_cost': devops_cost,
            'backup_recovery_cost': backup_recovery_cost,
            'governance_cost': governance_cost,
            'support_management_cost': support_management_cost,
            
            # System costs
            'system_cost': system_cost,
            'idle_cost': idle_cost,
            
            # Optimization insights by category
            'cost_optimization_insights': self._generate_cost_optimization_insights(cost_df, multiplier),
            
            # Metadata
            'analysis_period_days': days,
            'enhancement_level': 'comprehensive_v2',
            'allocation_methods_applied': True,
            'system_costs_allocated': True,
            'idle_costs_calculated': True,
            'networking_detailed_breakdown': True,
            'service_categorization_enhanced': True,
            'optimization_insights_included': True
        }

    def _create_empty_cost_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with proper structure"""
        return pd.DataFrame(columns=[
            'Cost', 'ResourceType', 'ResourceGroup', 'Service', 'Category', 
            'Subcategory', 'CostMetadata', 'AllocationWeight', 'CostType', 
            'DistributionScore', 'SystemCostAllocation', 'IdleCost'
        ])

    def _log_enhanced_cost_details(self, cost_df: pd.DataFrame):
        """Log enhanced cost breakdown details"""
        logger.info("=== Enhanced Cost Breakdown ===")
        
        # Log by category with enhanced details
        for category in cost_df['Category'].unique():
            category_data = cost_df[cost_df['Category'] == category]
            category_cost = category_data['Cost'].sum()
            avg_allocation_weight = category_data['AllocationWeight'].mean()
            
            logger.info(f"  {category}: ${category_cost:.2f} (weight: {avg_allocation_weight:.1f})")
            
            # Log subcategories
            for subcategory in category_data['Subcategory'].unique():
                subcat_cost = category_data[category_data['Subcategory'] == subcategory]['Cost'].sum()
                logger.info(f"    └─ {subcategory}: ${subcat_cost:.2f}")
        
        # Log system vs user costs
        system_cost = cost_df[cost_df['CostType'] == 'system']['Cost'].sum()
        user_cost = cost_df[cost_df['CostType'] == 'user']['Cost'].sum()
        shared_cost = cost_df[cost_df['CostType'] == 'shared']['Cost'].sum()
        
        logger.info(f"=== Cost Type Distribution ===")
        logger.info(f"  System Costs: ${system_cost:.2f}")
        logger.info(f"  User Costs: ${user_cost:.2f}")
        logger.info(f"  Shared Costs: ${shared_cost:.2f}")
        logger.info(f"Total Enhanced Cost: ${cost_df['Cost'].sum():.2f}")


# Main API functions - No backward compatibility
def process_aks_cost_data(cost_data_json):
    """Process AKS cost data with comprehensive enhancement"""
    processor = EnhancedAKSCostProcessor()
    return processor.process_aks_cost_data_enhanced(cost_data_json)

def categorize_resource(resource_type, service_name):
    """Enhanced resource categorization with comprehensive Azure service mapping"""
    processor = EnhancedAKSCostProcessor()
    category, subcategory, metadata = processor._categorize_resource_enhanced(
        resource_type, service_name, "", "", "", ""
    )
    return category, subcategory, metadata

def extract_cost_components(cost_df, days, monthly_equivalent_cost):
    """Enhanced cost component extraction with comprehensive allocation"""
    processor = EnhancedAKSCostProcessor()
    return processor.extract_enhanced_cost_components(cost_df, days, monthly_equivalent_cost)

def _merge_cost_data(aks_cost_data: Dict, additional_cost_data: Dict, thread_id: int) -> Dict:
    """Merge AKS-specific and additional services cost data"""
    logger.info(f"🔄 Thread {thread_id}: Merging cost data from AKS and additional services queries")
    
    # Start with AKS cost data as base
    merged_data = aks_cost_data.copy()
    
    # Check if both datasets have valid structure
    if ('properties' not in aks_cost_data or 'rows' not in aks_cost_data['properties'] or
        'properties' not in additional_cost_data or 'rows' not in additional_cost_data['properties']):
        logger.warning(f"⚠️ Thread {thread_id}: Invalid cost data structure, returning AKS data only")
        return aks_cost_data
    
    # Get rows from both datasets
    aks_rows = aks_cost_data['properties'].get('rows', [])
    additional_rows = additional_cost_data['properties'].get('rows', [])
    
    # Merge the rows
    merged_rows = aks_rows + additional_rows
    merged_data['properties']['rows'] = merged_rows
    
    logger.info(f"✅ Thread {thread_id}: Merged {len(aks_rows)} AKS rows with {len(additional_rows)} additional service rows = {len(merged_rows)} total rows")
    
    return merged_data

def get_aks_specific_cost_data(resource_group, cluster_name, start_date, end_date, 
                              subscription_id, cluster_id=None):
    """
    Comprehensive AKS cost collection - captures ACTUAL cluster costs across entire subscription.
    
    Uses dual-query approach:
    1. Direct AKS resources (cluster, nodes, disks in resource groups)
    2. Supporting services (networking, monitoring, security, storage across subscription)
    
    No backward compatibility - this is the definitive cost collection method.
    """
    logger.info(f"💰 COMPREHENSIVE: Fetching actual cluster costs for {cluster_name} in subscription {subscription_id[:8]}")
    
    max_retries = 3
    base_delay = 2  # Reduced from 5 seconds for faster retries
    thread_id = threading.get_ident()
    
    for attempt in range(max_retries):
        try:
            # Format dates for Azure SDK (ISO 8601 format)
            start_date_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
            end_date_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
            
            logger.info(f"📅 Thread {thread_id}: Using date range: {start_date_str} to {end_date_str}")
            
            # Get the node resource group using Azure SDK
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            aks_client = azure_sdk_manager.get_aks_client(subscription_id)
            if not aks_client:
                raise Exception(f"Cannot get AKS client for subscription {subscription_id}")
            
            cluster_info = aks_client.managed_clusters.get(resource_group, cluster_name)
            node_resource_group = cluster_info.node_resource_group
            
            logger.info(f"🔧 Thread {thread_id}: Using node resource group: {node_resource_group}")
            
            # Comprehensive cost query to capture ALL cluster-related Azure costs
            # Query 1: Direct AKS resources (cluster, nodes, disks in resource groups)
            aks_cost_query = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date_str,
                    "to": end_date_str
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
                    ],
                    "filter": {
                        "dimensions": {
                            "name": "ResourceGroupName",
                            "operator": "In",
                            "values": [resource_group, node_resource_group]
                        }
                    }
                }
            }
            
            # Query 2: Comprehensive additional services across subscription that support the cluster
            additional_services_query = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date_str,
                    "to": end_date_str
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
                    ],
                    "filter": {
                        "or": [
                            # All networking costs (critical for actual cluster costs)
                            {
                                "dimensions": {
                                    "name": "MeterCategory",
                                    "operator": "In",
                                    "values": ["Networking", "Virtual Network", "Load Balancer", "Application Gateway", 
                                              "VPN Gateway", "ExpressRoute", "Bandwidth", "Data Transfer", "NAT Gateway",
                                              "Azure Firewall", "Network Watcher", "Front Door", "Content Delivery Network"]
                                }
                            },
                            # All storage costs not captured in main query
                            {
                                "dimensions": {
                                    "name": "MeterCategory",
                                    "operator": "In",
                                    "values": ["Storage", "Azure Files", "Blob Storage", "Disk Storage", "Archive Storage",
                                              "Premium Storage", "Standard Storage"]
                                }
                            },
                            # Monitoring and observability services
                            {
                                "dimensions": {
                                    "name": "ServiceName",
                                    "operator": "In",
                                    "values": ["Azure Monitor", "Log Analytics", "Application Insights", "Azure Metrics",
                                              "Microsoft.Insights", "Microsoft.OperationalInsights"]
                                }
                            },
                            # Security and compliance services
                            {
                                "dimensions": {
                                    "name": "ServiceName",
                                    "operator": "In",
                                    "values": ["Key Vault", "Security Center", "Microsoft Defender for Cloud",
                                              "Azure Security Center", "Microsoft.KeyVault", "Microsoft.Security"]
                                }
                            },
                            # Container services across subscription
                            {
                                "dimensions": {
                                    "name": "ServiceName",
                                    "operator": "In",
                                    "values": ["Container Registry", "Azure Container Registry", "Container Instances",
                                              "Microsoft.ContainerRegistry", "Microsoft.ContainerInstance"]
                                }
                            },
                            # Backup and disaster recovery
                            {
                                "dimensions": {
                                    "name": "ServiceName",
                                    "operator": "In",
                                    "values": ["Azure Backup", "Site Recovery", "Recovery Services",
                                              "Microsoft.RecoveryServices", "Microsoft.DataProtection"]
                                }
                            },
                            # Database and data services that might support applications
                            {
                                "dimensions": {
                                    "name": "ServiceName",
                                    "operator": "In",
                                    "values": ["Azure SQL Database", "Azure Database for PostgreSQL", "Azure Database for MySQL",
                                              "Azure Cosmos DB", "Redis Cache", "Microsoft.Sql", "Microsoft.DBforPostgreSQL",
                                              "Microsoft.DBforMySQL", "Microsoft.DocumentDB", "Microsoft.Cache"]
                                }
                            },
                            # Additional Azure services commonly used with AKS
                            {
                                "dimensions": {
                                    "name": "ServiceName",
                                    "operator": "In",
                                    "values": ["Azure DNS", "Azure Active Directory", "Azure Policy", "Azure Resource Manager",
                                              "Microsoft.Network", "Microsoft.Authorization", "Microsoft.PolicyInsights"]
                                }
                            }
                        ]
                    }
                }
            }
            
            # Execute comprehensive cost collection with both queries
            logger.info(f"🔄 Thread {thread_id}: Executing comprehensive cost collection with both AKS and additional services queries")
            
            # Thread-safe temp file naming
            aks_query_file = f'aks_cost_query_{subscription_id[:8]}_{thread_id}_{int(time.time())}.json'
            additional_query_file = f'additional_services_query_{subscription_id[:8]}_{thread_id}_{int(time.time())}.json'
            
            # Write both query files
            with open(aks_query_file, 'w', encoding='utf-8') as f:
                json.dump(aks_cost_query, f, indent=2)
            
            with open(additional_query_file, 'w', encoding='utf-8') as f:
                json.dump(additional_services_query, f, indent=2)
            
            try:
                # Use Azure SDK instead of CLI for cost queries
                from infrastructure.services.azure_sdk_manager import azure_sdk_manager
                
                cost_client = azure_sdk_manager.get_cost_client(subscription_id)
                if not cost_client:
                    raise Exception(f"Cannot get cost client for subscription {subscription_id}")
                
                # Execute AKS-specific query using SDK
                logger.info(f"💰 COMPREHENSIVE: Thread {thread_id}: Executing direct AKS resources query via SDK (attempt {attempt + 1}/{max_retries})")
                
                # Load query definition from JSON file
                with open(aks_query_file, 'r') as f:
                    aks_query_dict = json.load(f)
                
                # Convert to SDK query definition
                from azure.mgmt.costmanagement.models import QueryDefinition
                aks_query_definition = QueryDefinition.from_dict(aks_query_dict)
                
                # Execute query
                scope = f"/subscriptions/{subscription_id}"
                aks_query_result = cost_client.query.usage(scope=scope, parameters=aks_query_definition)
                
                # Convert result to expected format
                aks_cost_data = {
                    'properties': {
                        'rows': aks_query_result.rows,
                        'columns': [{'name': col.name, 'type': col.type} for col in aks_query_result.columns] if aks_query_result.columns else []
                    }
                }
                
                # Execute additional services query using SDK
                logger.info(f"🔧 COMPREHENSIVE: Thread {thread_id}: Executing subscription-wide supporting services query via SDK")
                
                # Load additional query definition
                with open(additional_query_file, 'r') as f:
                    additional_query_dict = json.load(f)
                
                additional_query_definition = QueryDefinition.from_dict(additional_query_dict)
                additional_query_result = cost_client.query.usage(scope=scope, parameters=additional_query_definition)
                
                # Convert result to expected format
                additional_cost_data = {
                    'properties': {
                        'rows': additional_query_result.rows,
                        'columns': [{'name': col.name, 'type': col.type} for col in additional_query_result.columns] if additional_query_result.columns else []
                    }
                }
                
                # Merge cost data from both queries to get ACTUAL cluster costs
                merged_cost_data = _merge_cost_data(aks_cost_data, additional_cost_data, thread_id)
                
                logger.info(f"✅ Thread {thread_id}: Successfully captured actual cluster costs using comprehensive dual-query method")
                
                # Process with enhanced processor
                processor = EnhancedAKSCostProcessor()
                cost_df = processor.process_aks_cost_data_enhanced(merged_cost_data)
                
                # Add comprehensive metadata
                cost_df.attrs.update({
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'subscription_id': subscription_id,
                    'cluster_name': cluster_name,
                    'thread_id': thread_id,
                    'data_source': 'Comprehensive Azure Cost Management SDK - Dual Query',
                    'collection_method': 'comprehensive_dual_query_sdk',
                    'backward_compatibility': False,
                    'captures_actual_costs': True,
                    'queries_executed': ['aks_resources', 'additional_services'],
                    'cost_completeness': 'comprehensive',
                    'enhancement_version': '2.0',
                    'kubevista_comprehensive': True,
                    'cli_free': True
                })
                
                return cost_df
            
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "too many requests" in error_str or "throttl" in error_str:
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        logger.warning(f"⚠️ Thread {thread_id}: Rate limited, retrying in {retry_delay}s")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"❌ Thread {thread_id}: Rate limit exceeded after {max_retries} attempts")
                        raise Exception("Comprehensive Cost API rate limit exceeded")
                else:
                    logger.error(f"❌ Thread {thread_id}: Comprehensive SDK API error: {e}")
                    raise
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Thread {thread_id}: Comprehensive cost collection attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(base_delay)
                    continue
                else:
                    logger.error(f"❌ Thread {thread_id}: All comprehensive cost collection attempts failed: {e}")
                    raise
            
            finally:
                # Clean up temp files
                try:
                    if os.path.exists(aks_query_file):
                        os.remove(aks_query_file)
                        logger.debug(f"🧹 Thread {thread_id}: Cleaned up {aks_query_file}")
                    if os.path.exists(additional_query_file):
                        os.remove(additional_query_file)
                        logger.debug(f"🧹 Thread {thread_id}: Cleaned up {additional_query_file}")
                except Exception as file_e:
                    logger.warning(f"⚠️ Thread {thread_id}: Failed to remove temp files: {file_e}")
        
        except Exception as outer_e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Thread {thread_id}: Comprehensive cost collection outer attempt {attempt + 1} failed: {outer_e}, retrying...")
                time.sleep(base_delay)
                continue
            else:
                logger.error(f"❌ Thread {thread_id}: All comprehensive cost collection retry attempts exhausted: {outer_e}")
                return None
    
    return None

def log_cost_details(cost_df):
    """Enhanced cost logging with better breakdown"""
    processor = EnhancedAKSCostProcessor()
    processor._log_enhanced_cost_details(cost_df)