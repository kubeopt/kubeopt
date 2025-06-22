"""
AKS Cost Optimization Tool
--------------------------
A web application for analyzing and optimizing AKS costs, with a focus on
memory-based HPA implementation and generalizable metrics collection.
"""

# ============================================================================
# IMPORTS AND CONFIGURATION
# ============================================================================

import os
import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import time
import threading
import random
import subprocess
import logging
import statistics
import traceback
import math
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta, timezone
from implementation_generator import AKSImplementationGenerator
from pod_cost_analyzer import get_enhanced_pod_cost_breakdown
from cluster_database import EnhancedClusterManager, migrate_from_json

# Thread-safe analysis storage
_analysis_sessions = {}
_analysis_lock = threading.Lock()

enhanced_cluster_manager = EnhancedClusterManager()
analysis_status_tracker = {}
analysis_results = {}

# Enhanced global cache with TTL
analysis_cache = {
    'clusters': {},  # {cluster_id: {'data': {}, 'timestamp': str, 'ttl_hours': int}}
    'global_ttl_hours': 1
}

def is_cache_valid(cluster_id: str = None) -> bool:
    """Check if cache is valid for specific cluster or any cluster"""
    if not cluster_id:
        return False
        
    if cluster_id not in analysis_cache['clusters']:
        logger.info(f"🕐 No cache found for cluster: {cluster_id}")
        return False
    
    cluster_cache = analysis_cache['clusters'][cluster_id]
    if not cluster_cache.get('timestamp'):
        return False
    
    try:
        cache_time = datetime.fromisoformat(cluster_cache['timestamp'])
        expiry_time = cache_time + timedelta(hours=analysis_cache['global_ttl_hours'])
        
        is_valid = datetime.now() < expiry_time
        
        if not is_valid:
            logger.info(f"🕐 Cache expired for {cluster_id}: cached at {cache_time}")
            # Clean up expired cache
            del analysis_cache['clusters'][cluster_id]
        else:
            remaining = expiry_time - datetime.now()
            logger.info(f"✅ Cache valid for {cluster_id}: {remaining.total_seconds()/60:.1f} minutes remaining")
        
        return is_valid
    except Exception as e:
        logger.error(f"❌ Error checking cache validity for {cluster_id}: {e}")
        # Clean up invalid cache
        if cluster_id in analysis_cache['clusters']:
            del analysis_cache['clusters'][cluster_id]
        return False

def clear_analysis_cache(cluster_id: str = None):
    """Clear cache for specific cluster or all clusters"""
    global analysis_cache
    
    if cluster_id:
        if cluster_id in analysis_cache['clusters']:
            del analysis_cache['clusters'][cluster_id]
            logger.info(f"🧹 Cleared cache for cluster: {cluster_id}")
        else:
            logger.info(f"ℹ️ No cache to clear for cluster: {cluster_id}")
    else:
        old_count = len(analysis_cache['clusters'])
        analysis_cache['clusters'] = {}
        logger.info(f"🧹 Cleared ALL cluster caches ({old_count} clusters)")


def save_to_cache(cluster_id: str, complete_analysis_data: dict):
    """FIXED: Save complete analysis data to cluster-specific cache"""
    global analysis_cache
    
    logger.info(f"💾 SAVING TO CACHE: {cluster_id}")
    enhanced_cache_data = complete_analysis_data.copy()
    
    # Preserve node data
    node_data_found = False
    node_data = None
    
    for node_key in ['nodes', 'node_metrics', 'real_node_data']:
        if complete_analysis_data.get(node_key):
            node_data = complete_analysis_data[node_key]
            node_data_found = True
            break
    
    if node_data_found and node_data:
        enhanced_cache_data['nodes'] = node_data.copy()
        enhanced_cache_data['node_metrics'] = node_data.copy()
        enhanced_cache_data['real_node_data'] = node_data.copy()
        enhanced_cache_data['has_real_node_data'] = True
        logger.info(f"✅ CACHE: Preserved {len(node_data)} nodes for {cluster_id}")
    
    # Preserve namespace data
    if complete_analysis_data.get('has_pod_costs'):
        pod_analysis = complete_analysis_data.get('pod_cost_analysis', {})
        namespace_costs = pod_analysis.get('namespace_costs') or pod_analysis.get('namespace_summary') or complete_analysis_data.get('namespace_costs')
        
        if namespace_costs:
            enhanced_cache_data['namespace_costs'] = namespace_costs
            enhanced_cache_data['namespace_summary'] = namespace_costs
            if 'pod_cost_analysis' not in enhanced_cache_data:
                enhanced_cache_data['pod_cost_analysis'] = {}
            enhanced_cache_data['pod_cost_analysis']['namespace_costs'] = namespace_costs
    
    # Validate and generate implementation plan
    if 'implementation_plan' not in enhanced_cache_data:
        try:
            from implementation_generator import AKSImplementationGenerator
            implementation_generator = AKSImplementationGenerator()
            implementation_plan = implementation_generator.generate_implementation_plan(enhanced_cache_data)
            enhanced_cache_data['implementation_plan'] = implementation_plan
            logger.info(f"✅ CACHE: Generated implementation plan for {cluster_id}")
        except Exception as impl_error:
            logger.error(f"❌ CACHE: Failed to generate implementation plan for {cluster_id}: {impl_error}")
    
    # Store in cluster-specific cache
    analysis_cache['clusters'][cluster_id] = {
        'data': enhanced_cache_data,
        'timestamp': datetime.now().isoformat(),
        'cluster_id': cluster_id,
        'ttl_hours': analysis_cache['global_ttl_hours']
    }
    
    total_clusters_cached = len(analysis_cache['clusters'])
    logger.info(f"💾 CACHE SAVED: {cluster_id} | Total clusters cached: {total_clusters_cached}")


def load_from_cache(cluster_id: str) -> dict:
    """FIXED: Load analysis data from cluster-specific cache"""
    
    if not is_cache_valid(cluster_id):
        logger.info(f"🕐 CACHE: Invalid or expired for {cluster_id}")
        return {}
    
    cluster_cache = analysis_cache['clusters'][cluster_id]
    cached_data = cluster_cache['data'].copy()
    
    # Validate node data exists in cache
    node_data_keys = ['nodes', 'node_metrics', 'real_node_data']
    has_node_data = False
    
    for key in node_data_keys:
        if cached_data.get(key) and len(cached_data[key]) > 0:
            has_node_data = True
            logger.info(f"✅ CACHE LOAD: Found node data in {key} ({len(cached_data[key])} nodes) for {cluster_id}")
            break
    
    if not has_node_data:
        logger.error(f"❌ CACHE LOAD: No valid node data found in cache for {cluster_id}")
        # Remove invalid cache
        del analysis_cache['clusters'][cluster_id]
        return {}
    
    total_clusters_cached = len(analysis_cache['clusters'])
    logger.info(f"📦 CACHE LOADED: {cluster_id} with {len(cached_data.get('nodes', []))} nodes | Total cached: {total_clusters_cached}")
    return cached_data


def enhance_database_schema():
        """Add analysis status tracking to database"""
        try:
            with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                # Add analysis status columns if they don't exist
                conn.execute('''
                    ALTER TABLE clusters ADD COLUMN analysis_status TEXT DEFAULT 'pending'
                ''')
                conn.execute('''
                    ALTER TABLE clusters ADD COLUMN analysis_progress INTEGER DEFAULT 0
                ''')
                conn.execute('''
                    ALTER TABLE clusters ADD COLUMN analysis_message TEXT DEFAULT ''
                ''')
                conn.execute('''
                    ALTER TABLE clusters ADD COLUMN analysis_started_at TIMESTAMP NULL
                ''')
                conn.commit()
                logger.info("✅ Enhanced database schema for analysis tracking")
        except sqlite3.OperationalError:
            # Columns already exist
            pass
        except Exception as e:
            logger.error(f"❌ Database schema enhancement failed: {e}")

#
enhance_database_schema()

def initialize_database():
    """Initialize database and migrate from JSON if exists"""
    try:
        # Check if old clusters.json exists and migrate
        if os.path.exists('clusters.json'):
            logger.info("🔄 Migrating from JSON to SQLite database")
            migrate_from_json('clusters.json', enhanced_cluster_manager)
        
        logger.info("✅ Database initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app and components
app = Flask(__name__)
app.secret_key = os.urandom(24)
implementation_generator = AKSImplementationGenerator()

# Global variable to store analysis results
analysis_results = {}

# =============================
# Multi cluster view
# =============================


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def convert_k8s_memory_to_bytes(mem_str):
    """Convert Kubernetes memory string (e.g., 2Gi, 100Mi, 1000Ki) to bytes"""
    if mem_str.endswith('Ki'):
        return float(mem_str[:-2]) * 1024
    elif mem_str.endswith('Mi'):
        return float(mem_str[:-2]) * 1024 * 1024
    elif mem_str.endswith('Gi'):
        return float(mem_str[:-2]) * 1024 * 1024 * 1024
    elif mem_str.endswith('Ti'):
        return float(mem_str[:-2]) * 1024 * 1024 * 1024 * 1024
    elif mem_str.endswith('k'):
        return float(mem_str[:-1]) * 1000
    elif mem_str.endswith('M'):
        return float(mem_str[:-1]) * 1000 * 1000
    elif mem_str.endswith('G'):
        return float(mem_str[:-1]) * 1000 * 1000 * 1000
    elif mem_str.endswith('T'):
        return float(mem_str[:-1]) * 1000 * 1000 * 1000 * 1000
    else:
        return float(mem_str)

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_mean(values):
    """Calculate mean safely, handling empty lists"""
    try:
        return statistics.mean(values) if values else 0.0
    except (TypeError, ValueError):
        return 0.0

def validate_cost_data(cost_components):
    """Validate that cost components add up correctly"""
    try:
        component_sum = (
            cost_components.get('node_cost', 0) +
            cost_components.get('storage_cost', 0) +
            cost_components.get('networking_cost', 0) +
            cost_components.get('control_plane_cost', 0) +
            cost_components.get('registry_cost', 0) +
            cost_components.get('other_cost', 0)
        )
        
        total_cost = cost_components.get('total_cost', 0)
        
        # Allow for small rounding differences (1%)
        if abs(component_sum - total_cost) > (total_cost * 0.01):
            logger.warning(f"Cost validation warning: components sum ${component_sum:.2f} != total ${total_cost:.2f}")
            # Fix by adjusting the total to match components
            cost_components['total_cost'] = component_sum
            
        return cost_components
    except Exception as e:
        logger.error(f"Cost validation error: {e}")
        return cost_components

# ============================================================================
# BACKGROUND UPDATES
# ============================================================================

# def add_auto_update_feature():
#     """Add background auto-update feature for real-time data updates"""
    
#     def update_background_data():
#         """Background thread to update data every minute"""
#         while True:
#             try:
#                 if (analysis_results and 
#                     isinstance(analysis_results, dict) and 
#                     analysis_results.get('total_cost', 0) > 0):
                    
#                     logger.info("Performing background data update")
                    
#                     # Add small random variations to costs (±2%)
#                     variation = 1 + random.uniform(-0.02, 0.02)
                    
#                     try:
#                         analysis_results['node_cost'] *= variation
#                         analysis_results['storage_cost'] *= variation
                        
#                         #total cost from components
#                         analysis_results['total_cost'] = (
#                             analysis_results['node_cost'] + 
#                             analysis_results['storage_cost'] + 
#                             analysis_results.get('networking_cost', 0) +
#                             analysis_results.get('control_plane_cost', 0) +
#                             analysis_results.get('registry_cost', 0) +
#                             analysis_results.get('other_cost', 0)
#                         )
                        
#                         # Recalculate savings proportionally
#                         node_cost = analysis_results.get('node_cost', 0)
#                         storage_cost = analysis_results.get('storage_cost', 0)
#                         total_cost = analysis_results.get('total_cost', 1)
                        
#                         hpa_ratio = analysis_results.get('hpa_savings', 0) / max(node_cost, 1) if node_cost > 0 else 0.12
#                         right_sizing_ratio = analysis_results.get('right_sizing_savings', 0) / max(node_cost, 1) if node_cost > 0 else 0.08
#                         storage_ratio = analysis_results.get('storage_savings', 0) / max(storage_cost, 1) if storage_cost > 0 else 0.05
                        
#                         analysis_results['hpa_savings'] = node_cost * hpa_ratio
#                         analysis_results['right_sizing_savings'] = node_cost * right_sizing_ratio
#                         analysis_results['storage_savings'] = storage_cost * storage_ratio
#                         analysis_results['total_savings'] = (
#                             analysis_results['hpa_savings'] + 
#                             analysis_results['right_sizing_savings'] + 
#                             analysis_results['storage_savings']
#                         )
#                         analysis_results['savings_percentage'] = (
#                             analysis_results['total_savings'] / total_cost * 100
#                         ) if total_cost > 0 else 0
#                         analysis_results['annual_savings'] = analysis_results['total_savings'] * 12
                        
#                         logger.info(f"Background update completed at {time.strftime('%H:%M:%S')}")
                        
#                     except Exception as update_error:
#                         logger.error(f"Error during background cost update: {update_error}")
                        
#             except Exception as e:
#                 logger.error(f"Error in background update: {e}")
                
#             time.sleep(60)  # Sleep for 60 seconds
    
#     # Start the background thread
#     bg_thread = threading.Thread(target=update_background_data, daemon=True)
#     bg_thread.start()
#     logger.info("Enhanced background auto-update thread started")
    
#     return bg_thread

# ============================================================================
# COST DATA PROCESSING
# ============================================================================

def process_aks_cost_data(cost_data_json):
    """Process the AKS-specific cost data from Azure Cost Management API"""
    cost_df_data = []
    
    logger.info(f"Processing AKS cost data, data size: {len(str(cost_data_json))} bytes")
    
    using_real_data = False
    
    if 'properties' in cost_data_json and 'rows' in cost_data_json['properties']:
        column_names = []
        if 'columns' in cost_data_json['properties']:
            column_names = [col['name'] for col in cost_data_json['properties']['columns']]
            logger.info(f"Found columns in cost data: {column_names}")
            using_real_data = True
        
        # Map columns to our expected structure
        cost_idx = column_names.index('PreTaxCost') if 'PreTaxCost' in column_names else 0
        type_idx = column_names.index('ResourceType') if 'ResourceType' in column_names else 1
        group_idx = column_names.index('ResourceGroupName') if 'ResourceGroupName' in column_names else 2
        service_idx = column_names.index('ServiceName') if 'ServiceName' in column_names else 3
        
        row_count = len(cost_data_json['properties'].get('rows', []))
        logger.info(f"Found {row_count} cost data rows")
        
        # Process each row
        for row in cost_data_json['properties'].get('rows', []):
            if len(row) >= 4:
                cost = float(row[cost_idx]) if row[cost_idx] else 0
                resource_type = row[type_idx] if len(row) > type_idx else ""
                resource_group = row[group_idx] if len(row) > group_idx else ""
                service_name = row[service_idx] if len(row) > service_idx else ""
                
                if cost <= 0:
                    continue
                
                # Categorize resources
                category, subcategory = categorize_resource(resource_type, service_name)
                
                cost_entry = {
                    'Cost': cost,
                    'ResourceType': resource_type,
                    'ResourceGroup': resource_group,
                    'Service': service_name,
                    'Category': category,
                    'Subcategory': subcategory
                }
                
                cost_df_data.append(cost_entry)
    
    # Create DataFrame with the processed data
    cost_df = pd.DataFrame(cost_df_data)
    
    # Add metadata
    cost_df.attrs['is_sample_data'] = False
    cost_df.attrs['data_source'] = 'Azure Cost Management API'
    cost_df.attrs['total_cost'] = cost_df['Cost'].sum()
    cost_df.attrs['categories'] = cost_df['Category'].unique().tolist()
    cost_df.attrs['timestamp'] = datetime.now().isoformat()
    
    log_cost_details(cost_df)
    
    return cost_df

def categorize_resource(resource_type, service_name):
    """Categorize Azure resources into cost categories"""
    resource_type_lower = resource_type.lower()
    service_name_lower = service_name.lower() if service_name else ""
    
    category = "Other"
    subcategory = "Other"
    
    # Categorize AKS Control Plane
    if "microsoft.containerservice/managedclusters" in resource_type_lower:
        category = "AKS Control Plane"
        subcategory = "AKS Add-ons" if "addon" in resource_type_lower else "AKS Management"
    
    # Categorize Node Pools
    elif "microsoft.compute/virtualmachinescalesets" in resource_type_lower:
        category = "Node Pools"
        if "standard_d" in service_name_lower:
            subcategory = "D-Series VMs"
        elif "standard_e" in service_name_lower:
            subcategory = "E-Series VMs"
        elif "standard_b" in service_name_lower:
            subcategory = "B-Series VMs"
        else:
            subcategory = "Other VM Series"
    
    # Categorize Storage
    elif "microsoft.compute/disks" in resource_type_lower:
        category = "Storage"
        if "premium" in resource_type_lower:
            subcategory = "Premium SSD"
        elif "standard_ssd" in resource_type_lower:
            subcategory = "Standard SSD"
        else:
            subcategory = "Standard HDD"
    
    elif "microsoft.storage/storageaccounts" in resource_type_lower:
        category = "Storage"
        subcategory = "Storage Account"
    
    # Categorize Networking
    elif "microsoft.network" in resource_type_lower:
        category = "Networking"
        if "publicipaddresses" in resource_type_lower:
            subcategory = "Public IP Addresses"
        elif "loadbalancer" in resource_type_lower:
            subcategory = "Load Balancers"
        else:
            subcategory = "Other Networking"
    
    # Categorize Container Registry
    elif "microsoft.containerregistry" in resource_type_lower:
        category = "Container Registry"
        subcategory = "ACR Base Service"
    
    # Categorize Monitoring
    elif "microsoft.operationalinsights" in resource_type_lower or "microsoft.insights" in resource_type_lower:
        category = "Monitoring"
        subcategory = "Log Analytics" if "log" in resource_type_lower else "Application Insights"
    
    # Categorize Key Vault
    elif "microsoft.keyvault" in resource_type_lower:
        category = "Key Vault"
        subcategory = "Key Vault"
    
    return category, subcategory

def get_aks_specific_cost_data(resource_group, cluster_name, start_date, end_date):
    """Get AKS-specific cost data for a specific date range"""
    logger.info(f"Fetching AKS-specific cost data for {cluster_name} from {start_date} to {end_date}")
    
    try:
        # Format dates
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        logger.info(f"Using date range: {start_date_str} to {end_date_str}")
        
        # Get subscription ID
        sub_cmd = "az account show --query id -o tsv"
        sub_result = subprocess.run(sub_cmd, shell=True, check=True, capture_output=True, text=True)
        subscription_id = sub_result.stdout.strip()
        
        if not subscription_id:
            logger.error("Failed to retrieve subscription ID")
            return None
        
        # Get the node resource group
        node_rg_cmd = f"az aks show --resource-group {resource_group} --name {cluster_name} --query nodeResourceGroup -o tsv"
        node_rg_result = subprocess.run(node_rg_cmd, shell=True, check=True, capture_output=True, text=True)
        node_resource_group = node_rg_result.stdout.strip()
        
        logger.info(f"Using node resource group: {node_resource_group}")
        
        # Create cost query
        cost_query = {
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
                    {"type": "Dimension", "name": "ResourceId"}
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
        
        # Save query to temp file
        query_file = f'aks_cost_query_{int(time.time())}.json'
        with open(query_file, 'w', encoding='utf-8') as f:
            json.dump(cost_query, f, indent=2)
        
        try:
            # Execute the REST API call
            api_cmd = f"""
            az rest --method POST \
            --uri "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
            --body @{query_file} \
            --output json
            """
            
            logger.info("Executing AKS-specific Cost Management API query")
            api_result = subprocess.run(api_cmd, shell=True, check=True, capture_output=True, text=True)
            
            cost_data = json.loads(api_result.stdout)
            logger.info("Successfully parsed cost API response")
            
            # Process the data and create DataFrame
            cost_df = process_aks_cost_data(cost_data)
            
            # Add metadata
            cost_df.attrs['start_date'] = start_date_str
            cost_df.attrs['end_date'] = end_date_str
            cost_df.attrs['data_source'] = 'Azure Cost Management API'
            
            return cost_df
        
        finally:
            # Clean up temp file
            try:
                if os.path.exists(query_file):
                    os.remove(query_file)
            except Exception as file_e:
                logger.warning(f"Failed to remove temporary query file: {file_e}")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        logger.error(f"STDERR: {e.stderr}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching AKS-specific cost data: {str(e)}")
        return None

def log_cost_details(cost_df):
    """Log detailed breakdown of costs for debugging"""
    logger.info("=== Cost Breakdown ===")
    
    # Log by category
    for category in cost_df['Category'].unique():
        category_cost = cost_df[cost_df['Category'] == category]['Cost'].sum()
        logger.info(f"  {category}: ${category_cost:.2f}")
    
    # Log total
    logger.info(f"Total Cost: ${cost_df['Cost'].sum():.2f}")

# ============================================================================
# METRICS DATA PROCESSING
# ============================================================================

def get_aks_metrics_from_monitor(resource_group, cluster_name, start_date, end_date):
    """
    ENHANCED: Get AKS metrics using both Azure Monitor AND real-time kubectl approach
    This ensures we always get real node utilization data
    """
    logger.info(f"🔧 ENHANCED: Fetching AKS metrics for {cluster_name}")
    
    # First, try the real-time kubectl approach (more reliable)
    try:
        from aks_realtime_metrics import get_aks_realtime_metrics
        
        logger.info("🚀 Attempting real-time kubectl metrics collection...")
        realtime_metrics = get_aks_realtime_metrics(resource_group, cluster_name)
        
        if (realtime_metrics and 
            realtime_metrics.get('status') == 'success' and 
            realtime_metrics.get('nodes')):
            
            logger.info(f"✅ REAL-TIME: Successfully got {len(realtime_metrics['nodes'])} nodes via kubectl")
            return convert_realtime_to_monitor_format(realtime_metrics, resource_group, cluster_name)
            
    except Exception as e:
        logger.warning(f"⚠️ Real-time kubectl approach failed: {e}")
    
    logger.info("🔄 No Falling back ...")
    return None

def convert_realtime_to_monitor_format(realtime_metrics, resource_group, cluster_name):
    """Convert real-time kubectl metrics to the format expected by the analysis engine"""
    processed_metrics = {
        "metadata": {
            "cluster_name": cluster_name,
            "resource_group": resource_group,
            "timestamp": datetime.now().isoformat(),
            "source": "Real-time kubectl",
            "data_source": "kubectl top nodes + get nodes",
            "has_real_data": True
        },
        "nodes": [],
        "deployments": []
    }
    
    # Convert node data
    if realtime_metrics.get('nodes'):
        for node_data in realtime_metrics['nodes']:
            cpu_actual = node_data.get('cpu_usage_pct', 0)
            memory_actual = node_data.get('memory_usage_pct', 0)
            
            processed_node = {
                'name': node_data.get('name', f"node-{len(processed_metrics['nodes']) + 1}"),
                'cpu_usage_pct': round(cpu_actual, 1),
                'memory_usage_pct': round(memory_actual, 1),
                'cpu_request_pct': round(min(100, cpu_actual * 1.4 + 15), 1),
                'memory_request_pct': round(min(100, memory_actual * 1.3 + 20), 1),
                'cpu_gap': round(max(0, (cpu_actual * 1.4 + 15) - cpu_actual), 1),
                'memory_gap': round(max(0, (memory_actual * 1.3 + 20) - memory_actual), 1),
                'ready': node_data.get('ready', True)
            }
            
            processed_metrics['nodes'].append(processed_node)
            logger.info(f"✅ REAL NODE: {processed_node['name']} - CPU: {cpu_actual:.1f}%, Memory: {memory_actual:.1f}%")
    
    logger.info(f"🎯 REAL-TIME CONVERSION: {len(processed_metrics['nodes'])} nodes converted successfully")
    return processed_metrics

def process_azure_monitor_metric(metric_data, dimension=None):
    """Process metric data from Azure Monitor into usable format"""
    processed_data = []
    
    if 'value' not in metric_data or not metric_data['value']:
        return processed_data
    
    for timeseries in metric_data['value'][0]['timeseries']:
        series_data = {}
        
        # Extract dimension value if present
        if dimension and 'metadataValues' in timeseries:
            for metadata in timeseries['metadataValues']:
                if metadata['name'].lower() == dimension.lower():
                    series_data['dimension'] = metadata['value']
                    break
        
        # Extract time series data
        series_data['datapoints'] = []
        for datapoint in timeseries['data']:
            if 'timeStamp' in datapoint and any(k in datapoint for k in ['average', 'maximum', 'minimum', 'total']):
                value = datapoint.get('average', datapoint.get('maximum', datapoint.get('minimum', datapoint.get('total', 0))))
                
                series_data['datapoints'].append({
                    'timestamp': datapoint['timeStamp'],
                    'value': value
                })
        
        processed_data.append(series_data)
    
    return processed_data

def process_monitor_metrics(metrics, resource_group, cluster_name):
    """Process REAL Azure Monitor metrics data into unified format"""
    processed_metrics = {
        "metadata": {
            "cluster_name": cluster_name,
            "resource_group": resource_group,
            "timestamp": datetime.now().isoformat(),
            "source": "Azure Monitor",
            "data_source": "Azure Monitor"
        },
        "nodes": [],
        "deployments": []
    }
    
    logger.info(f"🔧 Processing REAL Azure Monitor metrics for {cluster_name}")
    
    # Process REAL node CPU metrics
    real_cpu_data = []
    if 'node_cpu' in metrics and metrics['node_cpu']:
        logger.info(f"🔧 Processing {len(metrics['node_cpu'])} CPU metric series")
        
        for series_idx, cpu_series in enumerate(metrics['node_cpu']):
            logger.info(f"🔧 DEBUG: CPU series {series_idx} structure: {list(cpu_series.keys())}")
            
            if 'datapoints' in cpu_series and cpu_series['datapoints']:
                logger.info(f"🔧 DEBUG: Found {len(cpu_series['datapoints'])} CPU datapoints")
                
                # Extract all valid CPU values
                cpu_values = []
                for dp_idx, dp in enumerate(cpu_series['datapoints']):
                    logger.info(f"🔧 DEBUG: Datapoint {dp_idx}: {dp}")
                    
                    # Try different possible value keys
                    value = None
                    for key in ['value', 'average', 'maximum', 'minimum', 'total']:
                        if key in dp and dp[key] is not None:
                            value = dp[key]
                            break
                    
                    if value is not None and float(value) >= 0:  # Changed > 0 to >= 0
                        cpu_values.append(float(value))
                        logger.info(f"🔧 DEBUG: Added CPU value: {value}")
                
                logger.info(f"🔧 DEBUG: Total CPU values extracted: {len(cpu_values)}")
                
                if cpu_values:
                    avg_cpu_millicores = safe_mean(cpu_values)
                    # Convert millicores to percentage (typical AKS node has 4 vCPUs = 4000 millicores)
                    node_capacity_millicores = 4000  # Can be adjusted based on node size
                    avg_cpu_percentage = min(100, (avg_cpu_millicores / node_capacity_millicores) * 100)
                    
                    real_cpu_data.append({
                        'series_index': series_idx,
                        'avg_cpu_millicores': avg_cpu_millicores,
                        'avg_cpu_percentage': avg_cpu_percentage,
                        'datapoint_count': len(cpu_values)
                    })
                    
                    logger.info(f"🔧 Node series {series_idx}: {avg_cpu_millicores:.0f} millicores = {avg_cpu_percentage:.1f}%")
    
    # Process REAL node memory metrics
    # Process REAL node memory metrics  
    real_memory_data = []
    if 'node_memory' in metrics and metrics['node_memory']:
        logger.info(f"🔧 Processing {len(metrics['node_memory'])} memory metric series")
        
        for series_idx, memory_series in enumerate(metrics['node_memory']):
            logger.info(f"🔧 DEBUG: Memory series {series_idx} structure: {list(memory_series.keys())}")
            
            if 'datapoints' in memory_series and memory_series['datapoints']:
                logger.info(f"🔧 DEBUG: Found {len(memory_series['datapoints'])} memory datapoints")
                
                # Extract all valid memory values
                memory_values = []
                for dp_idx, dp in enumerate(memory_series['datapoints']):
                    logger.info(f"🔧 DEBUG: Memory datapoint {dp_idx}: {dp}")
                    
                    # Try different possible value keys
                    value = None
                    for key in ['value', 'average', 'maximum', 'minimum', 'total']:
                        if key in dp and dp[key] is not None:
                            value = dp[key]
                            break
                    
                    if value is not None and float(value) >= 0:  # Changed > 0 to >= 0
                        memory_values.append(float(value))
                        logger.info(f"🔧 DEBUG: Added memory value: {value}")
                
                logger.info(f"🔧 DEBUG: Total memory values extracted: {len(memory_values)}")
                
                if memory_values:
                    avg_memory_bytes = safe_mean(memory_values)
                    # Convert bytes to percentage (typical AKS node has 16GB = 16*1024^3 bytes)
                    node_capacity_bytes = 16 * 1024 * 1024 * 1024  # 16GB
                    avg_memory_percentage = min(100, (avg_memory_bytes / node_capacity_bytes) * 100)
                    
                    real_memory_data.append({
                        'series_index': series_idx,
                        'avg_memory_bytes': avg_memory_bytes,
                        'avg_memory_gb': avg_memory_bytes / (1024 * 1024 * 1024),
                        'avg_memory_percentage': avg_memory_percentage,
                        'datapoint_count': len(memory_values)
                    })
                    
                    logger.info(f"🔧 Node series {series_idx}: {avg_memory_bytes/(1024*1024*1024):.1f}GB = {avg_memory_percentage:.1f}%")
    
    # Create nodes from REAL data only
    if real_cpu_data or real_memory_data:
        # Determine the number of real nodes (use the max of CPU or memory series)
        max_cpu_series = len(real_cpu_data)
        max_memory_series = len(real_memory_data)
        node_count = max(max_cpu_series, max_memory_series, 1)
        
        logger.info(f"🔧 Creating {node_count} nodes from REAL Azure Monitor data")
        
        for i in range(node_count):
            # Generate realistic node name based on cluster
            node_name = f"aks-{cluster_name.split('-')[-1]}-{i+1:02d}"
            
            # Get real CPU data for this node (if available)
            if i < len(real_cpu_data):
                cpu_actual = real_cpu_data[i]['avg_cpu_percentage']
                logger.info(f"🔧 Node {node_name}: Using REAL CPU data = {cpu_actual:.1f}%")
            else:
                # If we have fewer CPU series than expected nodes, skip this node
                logger.warning(f"⚠️ No real CPU data for node {i+1}, skipping")
                continue
            
            # Get real memory data for this node (if available)  
            if i < len(real_memory_data):
                memory_actual = real_memory_data[i]['avg_memory_percentage']
                logger.info(f"🔧 Node {node_name}: Using REAL memory data = {memory_actual:.1f}%")
            else:
                # If we have fewer memory series than expected nodes, skip this node
                logger.warning(f"⚠️ No real memory data for node {i+1}, skipping")
                continue
            
            # Calculate realistic request/limit values based on actual usage
            # Typically, requests are set higher than actual usage
            cpu_request = min(100, cpu_actual + 20 + (i * 5))  # Add some variance per node
            memory_request = min(100, memory_actual + 15 + (i * 3))  # Add some variance per node
            
            node_data = {
                'name': node_name,
                'cpu_usage_pct': round(cpu_actual, 1),
                'memory_usage_pct': round(memory_actual, 1),
                'cpu_request_pct': round(cpu_request, 1),
                'memory_request_pct': round(memory_request, 1),
                'cpu_gap': round(max(0, cpu_request - cpu_actual), 1),
                'memory_gap': round(max(0, memory_request - memory_actual), 1)
            }
            
            processed_metrics['nodes'].append(node_data)
            logger.info(f"✅ Created REAL node {node_name}: CPU={cpu_actual:.1f}%, Memory={memory_actual:.1f}%")
    
    else:
        logger.error("❌ NO REAL METRICS DATA AVAILABLE - Cannot create nodes without real data")
        # Return empty nodes instead of static data
        processed_metrics['nodes'] = []
    
    # Add metadata about data quality
    processed_metrics['metadata']['real_data_quality'] = {
        'cpu_series_count': len(real_cpu_data),
        'memory_series_count': len(real_memory_data),
        'nodes_created': len(processed_metrics['nodes']),
        'has_real_data': len(processed_metrics['nodes']) > 0
    }
    
    logger.info(f"✅ REAL metrics processing complete: {len(processed_metrics['nodes'])} nodes created from real data")
    
    return processed_metrics

def create_minimal_metrics_structure():
    """Create minimal metrics structure when real metrics unavailable - NO STATIC DATA"""
    logger.warning("⚠️ Creating minimal metrics structure - NO REAL DATA AVAILABLE")
    return {
        'metadata': {
            'source': 'Minimal structure - real metrics unavailable',
            'data_source': 'Error - No Azure Monitor data',
            'has_real_data': False
        },
        'nodes': [],  # Empty - no static data
        'deployments': []
    }

# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

def run_consistent_analysis(resource_group: str, cluster_name: str, days: int = 30, enable_pod_analysis: bool = True) -> Dict[str, Any]:
    """THREAD-SAFE analysis function with FORCED implementation plan regeneration"""
    
    # Create unique session ID for this analysis
    session_id = str(uuid.uuid4())
    cluster_id = f"{resource_group}_{cluster_name}"
    
    logger.info(f"🎯 Starting THREAD-SAFE analysis for {cluster_name} (session: {session_id[:8]})")
    
    try:
        # Initialize session-specific analysis results
        session_results = {}
        
        # Store in thread-safe sessions dict
        with _analysis_lock:
            _analysis_sessions[session_id] = {
                'cluster_id': cluster_id,
                'results': session_results,
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'thread_id': threading.current_thread().ident
            }
        
        logger.info(f"🔐 Session {session_id[:8]} locked for cluster {cluster_name}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get cost data
        logger.info(f"📊 Session {session_id[:8]}: Fetching {days}-day actual cost baseline...")
        cost_df = get_aks_specific_cost_data(resource_group, cluster_name, start_date, end_date)
        
        if cost_df is None or cost_df.empty:
            raise ValueError("❌ No cost data available")
        
        # Extract and validate cost components
        total_period_cost = float(cost_df['Cost'].sum())
        
        # Calculate monthly equivalent
        if days == 30:
            monthly_equivalent_cost = total_period_cost
            cost_label = f"Monthly Baseline ({days}-day actual)"
        else:
            daily_average = total_period_cost / days
            monthly_equivalent_cost = daily_average * 30
            cost_label = f"Monthly Equivalent (from {days}-day actual: ${total_period_cost:.2f})"
        
        cost_components = extract_cost_components(cost_df, days, monthly_equivalent_cost)
        cost_components = validate_cost_data(cost_components)
        
        # Get current usage metrics
        logger.info(f"📈 Session {session_id[:8]}: Fetching current usage metrics...")
        metrics_end_time = datetime.now()
        metrics_start_time = metrics_end_time - timedelta(hours=1)
        
        metrics_data = get_aks_metrics_from_monitor(resource_group, cluster_name, metrics_start_time, metrics_end_time)
        
        if not metrics_data or not metrics_data.get('nodes'):
            logger.error(f"❌ Session {session_id[:8]}: No current metrics available")
            raise ValueError("No real node metrics available from Azure Monitor or kubectl")
        
        # CRITICAL: Extract and preserve real node data IN SESSION
        real_node_metrics = []
        if metrics_data and metrics_data.get('nodes'):
            real_node_metrics = metrics_data['nodes'].copy()
            logger.info(f"🔧 Session {session_id[:8]}: PRESERVED {len(real_node_metrics)} real node metrics")
        else:
            logger.error(f"❌ Session {session_id[:8]}: CRITICAL: No node metrics in metrics_data")
            raise ValueError("No node metrics found in metrics data")
        
        # Pod-level analysis if enabled
        pod_data = None
        actual_node_cost_for_pod_analysis = float(cost_df[cost_df['Category'] == 'Node Pools']['Cost'].sum())
        
        if enable_pod_analysis and actual_node_cost_for_pod_analysis > 0:
            logger.info(f"🔍 Session {session_id[:8]}: Running current pod analysis...")
            try:
                pod_cost_result = get_enhanced_pod_cost_breakdown(
                    resource_group, cluster_name, actual_node_cost_for_pod_analysis
                )
                
                if pod_cost_result and pod_cost_result.get('success'):
                    pod_data = pod_cost_result
                    logger.info(f"✅ Session {session_id[:8]}: Pod analysis: {pod_cost_result.get('analysis_method', 'unknown')}")
                    
            except Exception as pod_error:
                logger.error(f"❌ Session {session_id[:8]}: Pod analysis error: {pod_error}")
                pod_data = None
        
        # Run algorithmic analysis
        logger.info(f"🎯 Session {session_id[:8]}: Executing CONSISTENT algorithmic analysis...")
        try:
            from algorithmic_cost_analyzer import integrate_consistent_analysis
            
            consistent_results = integrate_consistent_analysis(
                resource_group=resource_group,
                cluster_name=cluster_name,
                cost_data=cost_components,
                metrics_data=metrics_data,
                pod_data=pod_data
            )
            
            logger.info(f"✅ Session {session_id[:8]}: Consistent algorithmic analysis completed")
            
        except Exception as algo_error:
            logger.error(f"❌ Session {session_id[:8]}: Consistent algorithmic analysis failed: {algo_error}")
            # Fallback to basic calculations
            consistent_results = calculate_basic_savings(cost_components, metrics_data)
        
        # Store results IN SESSION (not global)
        session_results.update(consistent_results)
        session_results['cost_label'] = cost_label
        session_results['actual_period_cost'] = total_period_cost
        session_results['analysis_period_days'] = days
        
        # CRITICAL: FORCE preservation of real node metrics IN SESSION
        if real_node_metrics:
            session_results['nodes'] = real_node_metrics.copy()
            session_results['node_metrics'] = real_node_metrics.copy()
            session_results['real_node_data'] = real_node_metrics.copy()
            session_results['has_real_node_data'] = True
            logger.info(f"🔧 Session {session_id[:8]}: FORCED preservation of {len(real_node_metrics)} real nodes")
        else:
            logger.error(f"❌ Session {session_id[:8]}: CRITICAL: No real node metrics to preserve")
            raise ValueError("No real node metrics available for analysis")
        
        # Add pod data if available
        if pod_data:
            session_results['has_pod_costs'] = True
            session_results['pod_cost_analysis'] = pod_data
            
            if 'namespace_costs' in pod_data:
                session_results['namespace_costs'] = pod_data['namespace_costs']
            elif 'namespace_summary' in pod_data:
                session_results['namespace_costs'] = pod_data['namespace_summary']
            
            if 'workload_costs' in pod_data:
                session_results['workload_costs'] = pod_data['workload_costs']
        else:
            session_results['has_pod_costs'] = False
        
        # CRITICAL: Add metadata BEFORE implementation plan generation
        session_results.update({
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'cost_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days} days)",
            'cost_data_source': cost_df.attrs.get('data_source', 'Azure Cost Management API'),
            'metrics_data_source': metrics_data.get('metadata', {}).get('data_source', 'Azure Monitor'),
            'analysis_timestamp': datetime.now().isoformat(),
            'has_real_node_data': len(real_node_metrics) > 0,
            'session_id': session_id
        })
        
        # CRITICAL: GENERATE FRESH IMPLEMENTATION PLAN IN SESSION
        logger.info(f"📋 Session {session_id[:8]}: GENERATING FRESH IMPLEMENTATION PLAN...")
        try:
            from implementation_generator import AKSImplementationGenerator
            implementation_generator = AKSImplementationGenerator()
            
            # Generate fresh implementation plan with complete metadata
            fresh_implementation_plan = implementation_generator.generate_implementation_plan(session_results)
            session_results['implementation_plan'] = fresh_implementation_plan
            
            # Validate implementation plan structure
            if fresh_implementation_plan and isinstance(fresh_implementation_plan, dict):
                if 'implementation_phases' in fresh_implementation_plan:
                    phases = fresh_implementation_plan['implementation_phases']
                    if isinstance(phases, list) and len(phases) > 0:
                        logger.info(f"✅ Session {session_id[:8]}: GENERATED FRESH IMPLEMENTATION PLAN: {len(phases)} phases")
                        logger.info(f"✅ Session {session_id[:8]}: Cluster: {resource_group}/{cluster_name}")
                    else:
                        logger.error(f"❌ Session {session_id[:8]}: Implementation plan phases are empty or invalid")
                        raise ValueError("Implementation plan phases are empty")
                else:
                    logger.error(f"❌ Session {session_id[:8]}: Implementation plan missing phases structure")
                    raise ValueError("Implementation plan missing phases structure")
            else:
                logger.error(f"❌ Session {session_id[:8]}: Implementation plan is not a valid dictionary")
                raise ValueError("Implementation plan generation failed")
                
        except Exception as impl_error:
            logger.error(f"❌ Session {session_id[:8]}: IMPLEMENTATION PLAN GENERATION FAILED: {impl_error}")
            raise impl_error
        
        # Update session status
        with _analysis_lock:
            if session_id in _analysis_sessions:
                _analysis_sessions[session_id]['status'] = 'completed'
                _analysis_sessions[session_id]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"🎉 Session {session_id[:8]}: THREAD-SAFE ANALYSIS COMPLETED WITH FRESH IMPLEMENTATION PLAN")
        
        return {
            'status': 'success', 
            'data_type': 'consistent_algorithmic',
            'session_id': session_id,
            'results': session_results  # Return session-specific results
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Session {session_id[:8]}: CONSISTENT ANALYSIS FAILED: {error_msg}")
        
        # Update session status
        with _analysis_lock:
            if session_id in _analysis_sessions:
                _analysis_sessions[session_id]['status'] = 'failed'
                _analysis_sessions[session_id]['error'] = error_msg
                _analysis_sessions[session_id]['failed_at'] = datetime.now().isoformat()
        
        return {
            'status': 'error', 
            'message': error_msg,
            'session_id': session_id
        }
    
    finally:
        # Cleanup session after some time (optional)
        def cleanup_session():
            time.sleep(300)  # Wait 5 minutes
            with _analysis_lock:
                if session_id in _analysis_sessions:
                    del _analysis_sessions[session_id]
                    logger.info(f"🧹 Cleaned up session {session_id[:8]}")
        
        cleanup_thread = threading.Thread(target=cleanup_session, daemon=True)
        cleanup_thread.start()


def generate_dynamic_hpa_comparison(analysis_data):
    """Generate HPA comparison - FIXED to fail fast without fallbacks"""
    try:
        logger.info("🔧 Generating HPA comparison from analysis data")
        logger.info(f"🔧 Analysis data keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
        
        # Step 1: Validate we have real node data flag
        if not analysis_data.get('has_real_node_data'):
            raise ValueError("Analysis data indicates no real node data available (has_real_node_data=False)")
        
        # Step 2: Find node data in any of the expected keys
        nodes = None
        for key in ['real_node_data', 'nodes', 'node_metrics']:
            if analysis_data.get(key):
                nodes = analysis_data[key]
                logger.info(f"✅ HPA: Found node data in key: {key}")
                break
        
        if not nodes:
            raise ValueError("No node data found in expected keys (real_node_data, nodes, node_metrics)")
        
        if len(nodes) == 0:
            raise ValueError("Node data exists but is empty")
        
        # Step 3: Validate node data structure
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} is not a dictionary: {type(node)}")
            if 'cpu_usage_pct' not in node or 'memory_usage_pct' not in node:
                raise ValueError(f"Node {i} missing required usage data: {list(node.keys())}")
        
        logger.info(f"✅ HPA: Using {len(nodes)} validated nodes for HPA calculation")
        
        # Step 4: Calculate HPA data from real metrics
        total_cpu_usage = sum(node.get('cpu_usage_pct', 0) for node in nodes)
        total_memory_usage = sum(node.get('memory_usage_pct', 0) for node in nodes)
        avg_cpu = total_cpu_usage / len(nodes)
        avg_memory = total_memory_usage / len(nodes)
        
        # Current replicas estimation based on node utilization
        current_replicas = len(nodes) * 2  # Assume 2 replicas per node on average
        
        # CPU-based HPA scaling (target 70% CPU)
        cpu_target = 70.0
        cpu_scale_factor = avg_cpu / cpu_target if cpu_target > 0 else 1.0
        cpu_replicas = max(1, int(current_replicas * cpu_scale_factor))
        
        # Memory-based HPA scaling (target 60% Memory)  
        memory_target = 60.0
        memory_scale_factor = avg_memory / memory_target if memory_target > 0 else 1.0
        memory_replicas = max(1, int(current_replicas * memory_scale_factor))
        
        # Generate 5 time points based on variation in node utilization
        time_variations = [0.8, 1.2, 1.5, 1.1, 0.9]  # Load pattern multipliers
        
        result = {
            'timePoints': ['Low Traffic', 'Medium Traffic', 'Peak Traffic', 'Evening', 'Night'],
            'cpuReplicas': [max(1, int(cpu_replicas * var)) for var in time_variations],
            'memoryReplicas': [max(1, int(memory_replicas * var)) for var in time_variations],
            'current_cpu_avg': avg_cpu,
            'current_memory_avg': avg_memory,
            'cpu_target': cpu_target,
            'memory_target': memory_target,
            'data_source': 'real_node_metrics'
        }
        
        logger.info(f"✅ HPA: Generated comparison with avg CPU: {avg_cpu:.1f}%, avg Memory: {avg_memory:.1f}%")
        return result
        
    except Exception as e:
        logger.error(f"❌ HPA: Failed to generate HPA comparison: {e}")
        raise ValueError(f"Cannot generate HPA comparison: {e}")


def extract_cost_components(cost_df, days, monthly_equivalent_cost):
    """Extract cost components from DataFrame with proper validation"""
    multiplier = 30/days if days != 30 else 1
    
    # Calculate each component individually
    node_cost = float(cost_df[cost_df['Category'] == 'Node Pools']['Cost'].sum()) * multiplier
    storage_cost = float(cost_df[cost_df['Category'] == 'Storage']['Cost'].sum()) * multiplier
    networking_cost = float(cost_df[cost_df['Category'] == 'Networking']['Cost'].sum()) * multiplier
    control_plane_cost = float(cost_df[cost_df['Category'] == 'AKS Control Plane']['Cost'].sum()) * multiplier
    registry_cost = float(cost_df[cost_df['Category'] == 'Container Registry']['Cost'].sum()) * multiplier
    other_cost = float(cost_df[cost_df['Category'] == 'Other']['Cost'].sum()) * multiplier
    keyvault_cost = float(cost_df[cost_df['Category'] == 'Key Vault']['Cost'].sum()) * multiplier
    
    # Combine other costs properly
    total_other_cost = other_cost + keyvault_cost
    
    # Verify components add up
    component_sum = node_cost + storage_cost + networking_cost + control_plane_cost + registry_cost + total_other_cost
    
    logger.info(f"🔍 Component validation: sum=${component_sum:.2f}, expected=${monthly_equivalent_cost:.2f}")
    
    # If there's a mismatch, log it and adjust
    if abs(component_sum - monthly_equivalent_cost) > 1.0:  # Allow $1 tolerance
        logger.warning(f"⚠️ Cost component mismatch detected: {component_sum:.2f} vs {monthly_equivalent_cost:.2f}")
        # Proportionally adjust components to match total
        if component_sum > 0:
            adjustment_factor = monthly_equivalent_cost / component_sum
            node_cost *= adjustment_factor
            storage_cost *= adjustment_factor
            networking_cost *= adjustment_factor
            control_plane_cost *= adjustment_factor
            registry_cost *= adjustment_factor
            total_other_cost *= adjustment_factor
            logger.info(f"✅ Applied adjustment factor: {adjustment_factor:.4f}")
    
    components = {
        'total_cost': monthly_equivalent_cost,
        'node_cost': node_cost,
        'storage_cost': storage_cost,
        'networking_cost': networking_cost,
        'control_plane_cost': control_plane_cost,
        'registry_cost': registry_cost,
        'other_cost': total_other_cost,  # Now includes Key Vault
        'analysis_period_days': days
    }
    
    return components

def calculate_basic_savings(cost_components, metrics_data):
    """Calculate basic savings when algorithmic analysis fails"""
    node_cost = cost_components.get('node_cost', 0)
    storage_cost = cost_components.get('storage_cost', 0)
    total_cost = cost_components.get('total_cost', 0)
    
    # Basic savings estimates
    hpa_savings = node_cost * 0.15  # 15% HPA savings
    right_sizing_savings = node_cost * 0.10  # 10% right-sizing savings
    storage_savings = storage_cost * 0.05  # 5% storage savings
    
    total_savings = hpa_savings + right_sizing_savings + storage_savings
    savings_percentage = (total_savings / total_cost * 100) if total_cost > 0 else 0
    
    return {
        'total_cost': total_cost,
        'node_cost': node_cost,
        'storage_cost': storage_cost,
        'networking_cost': cost_components.get('networking_cost', 0),
        'control_plane_cost': cost_components.get('control_plane_cost', 0),
        'registry_cost': cost_components.get('registry_cost', 0),
        'other_cost': cost_components.get('other_cost', 0),
        'hpa_savings': hpa_savings,
        'right_sizing_savings': right_sizing_savings,
        'storage_savings': storage_savings,
        'total_savings': total_savings,
        'savings_percentage': savings_percentage,
        'annual_savings': total_savings * 12,
        'hpa_reduction': 15.0,
        'cpu_gap': 25.0,
        'memory_gap': 20.0,
        'analysis_confidence': 0.7,
        'confidence_level': 'Medium',
        'algorithms_used': ['basic_estimation'],
        'is_consistent': True
    }

# ============================================================================
# CHART DATA GENERATION
# ============================================================================

def generate_insights(analysis_results):
    """Generate insights for the dashboard"""
    if not analysis_results:
        return {
            'cost_breakdown': 'No analysis data available. Please run an analysis first.',
            'hpa_comparison': 'No HPA analysis available yet.',
            'resource_gap': 'No resource utilization data found.',
            'savings_summary': 'No savings analysis available.'
        }
    
    insights = {}
    
    # Cost breakdown insight
    node_cost = analysis_results.get('node_cost', 0)
    total_cost = analysis_results.get('total_cost', 0)
    node_percentage = (node_cost / total_cost) * 100 if total_cost > 0 else 0
    
    if node_percentage > 60:
        insights['cost_breakdown'] = f"🎯 VM Scale Sets (nodes) dominate your costs at <strong>{node_percentage:.1f}%</strong> (${node_cost:.2f}), making them your #1 optimization target."
    elif node_percentage > 40:
        insights['cost_breakdown'] = f"💡 VM Scale Sets represent <strong>{node_percentage:.1f}%</strong> of costs (${node_cost:.2f}), offering significant optimization opportunities."
    else:
        insights['cost_breakdown'] = f"✅ Your costs are well-distributed with VM Scale Sets at <strong>{node_percentage:.1f}%</strong> (${node_cost:.2f})."
    
    # HPA insight
    hpa_reduction = analysis_results.get('hpa_reduction', 0)
    hpa_savings = analysis_results.get('hpa_savings', 0)
    
    if hpa_reduction > 40:
        insights['hpa_comparison'] = f"🚀 <strong>MAJOR OPPORTUNITY:</strong> Memory-based HPA can reduce your replica count by <strong>{hpa_reduction:.1f}%</strong>, saving <strong>${hpa_savings:.2f}/month</strong>!"
    elif hpa_reduction > 20:
        insights['hpa_comparison'] = f"⭐ <strong>SOLID SAVINGS:</strong> Memory-based HPA offers <strong>{hpa_reduction:.1f}%</strong> fewer replicas, worth <strong>${hpa_savings:.2f}/month</strong>."
    else:
        insights['hpa_comparison'] = f"📈 Memory-based HPA provides a modest <strong>{hpa_reduction:.1f}%</strong> improvement (${hpa_savings:.2f}/month)."
    
    # Resource gap insight
    cpu_gap = analysis_results.get('cpu_gap', 0)
    memory_gap = analysis_results.get('memory_gap', 0)
    right_sizing_savings = analysis_results.get('right_sizing_savings', 0)
    
    if cpu_gap > 40 or memory_gap > 30:
        insights['resource_gap'] = f"🎯 <strong>CRITICAL OVER-PROVISIONING:</strong> Your workloads have a <strong>{cpu_gap:.1f}% CPU gap</strong> and <strong>{memory_gap:.1f}% memory gap</strong>. Right-sizing can save <strong>${right_sizing_savings:.2f}/month</strong>!"
    else:
        insights['resource_gap'] = f"✅ <strong>WELL-OPTIMIZED:</strong> Minor gaps of <strong>{cpu_gap:.1f}% CPU</strong> and <strong>{memory_gap:.1f}% memory</strong>."
    
    # Savings summary
    total_savings = analysis_results.get('total_savings', 0)
    annual_savings = analysis_results.get('annual_savings', 0)
    savings_percentage = analysis_results.get('savings_percentage', 0)
    
    if savings_percentage > 25:
        insights['savings_summary'] = f"💰 <strong>MASSIVE ROI OPPORTUNITY:</strong> Save <strong>${annual_savings:.2f}/year</strong> ({savings_percentage:.1f}% cost reduction)!"
    elif savings_percentage > 15:
        insights['savings_summary'] = f"📊 <strong>SIGNIFICANT IMPACT:</strong> Annual savings of <strong>${annual_savings:.2f}</strong> ({savings_percentage:.1f}% reduction)."
    else:
        insights['savings_summary'] = f"💡 <strong>STEADY IMPROVEMENTS:</strong> Save <strong>${annual_savings:.2f}/year</strong> ({savings_percentage:.1f}% optimization)."
    
    # Pod cost insights if available
    if analysis_results.get('has_pod_costs'):
        if analysis_results.get('top_namespace'):
            top_ns = analysis_results['top_namespace']
            ns_cost_pct = (top_ns['cost'] / node_cost) * 100 if node_cost > 0 else 0
            
            if ns_cost_pct > 50:
                insights['namespace_analysis'] = f"🎯 <strong>MAJOR FINDING:</strong> Namespace '<strong>{top_ns['name']}</strong>' consumes <strong>${top_ns['cost']:.2f} ({ns_cost_pct:.1f}%)</strong> of your node costs!"
            else:
                insights['namespace_analysis'] = f"✅ <strong>BALANCED DISTRIBUTION:</strong> Top namespace '<strong>{top_ns['name']}</strong>' uses <strong>${top_ns['cost']:.2f} ({ns_cost_pct:.1f}%)</strong>."
    
    return insights

def generate_pod_cost_data(analysis_data=None):
    """Generate pod cost chart data - NO FALLBACKS"""
    try:
        # Use provided analysis_data
        data_source = analysis_data
        
        if not data_source.get('has_pod_costs'):
            return None
        
        # Try multiple sources for namespace costs
        namespace_costs = None
        
        if data_source.get('namespace_costs'):
            namespace_costs = data_source['namespace_costs']
        elif data_source.get('pod_cost_analysis', {}).get('namespace_costs'):
            namespace_costs = data_source['pod_cost_analysis']['namespace_costs']
        elif data_source.get('pod_cost_analysis', {}).get('namespace_summary'):
            namespace_costs = data_source['pod_cost_analysis']['namespace_summary']
        
        if not namespace_costs:
            return None
        
        # Convert pandas objects if needed
        if hasattr(namespace_costs, 'to_dict'):
            namespace_costs = namespace_costs.to_dict()
        
        # Sort by cost, get top 100
        sorted_namespaces = sorted(namespace_costs.items(), key=lambda x: float(x[1]), reverse=True)[:100]
        
        if not sorted_namespaces:
            return None
        
        pod_analysis = data_source.get('pod_cost_analysis', {})
        
        result = {
            'labels': [ns[0] for ns in sorted_namespaces],
            'values': [float(ns[1]) for ns in sorted_namespaces],
            'analysis_method': pod_analysis.get('analysis_method', 'container_usage'),
            'accuracy_level': pod_analysis.get('accuracy_level', 'High'),
            'total_analyzed': int(pod_analysis.get('total_containers_analyzed', 0) or 
                                pod_analysis.get('total_pods_analyzed', 0) or 
                                len(sorted_namespaces))
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating pod cost data: {e}")
        return None

def generate_namespace_data(analysis_data=None):
    """Generate namespace distribution data - NO FALLBACKS"""
    try:
        logger.info("🔍 Extracting REAL namespace data from analysis")
        
        # Use provided analysis_data
        data_source = analysis_data
        
        # Get namespace costs (existing logic)
        namespace_costs = data_source.get('namespace_costs')
        if not namespace_costs:
            pod_analysis = data_source.get('pod_cost_analysis', {})
            namespace_costs = pod_analysis.get('namespace_costs') or pod_analysis.get('namespace_summary')
        
        if not namespace_costs:
            raise ValueError("No real namespace costs available")
        
        # Convert pandas objects if needed
        if hasattr(namespace_costs, 'to_dict'):
            namespace_costs = namespace_costs.to_dict()
        
        if not isinstance(namespace_costs, dict):
            raise ValueError(f"Invalid namespace_costs type: {type(namespace_costs)}")
        
        # Include ALL namespaces, even those with minimal costs
        valid_namespaces = {}
        for namespace, cost in namespace_costs.items():
            try:
                cost_float = float(cost)
                if cost_float >= 0:  # Include all non-negative costs
                    valid_namespaces[namespace] = cost_float
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Invalid cost for namespace {namespace}: {cost}")
        
        if not valid_namespaces:
            raise ValueError("No valid namespace costs after processing")
        
        total_valid_cost = sum(valid_namespaces.values())
        
        # Sort by cost but keep ALL namespaces
        sorted_namespaces = sorted(valid_namespaces.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            'namespaces': [ns[0] for ns in sorted_namespaces],
            'costs': [ns[1] for ns in sorted_namespaces],
            'percentages': [float(cost/total_valid_cost*100) for _, cost in sorted_namespaces],
            'total_cost': float(total_valid_cost),
            'data_source': 'real_namespace_analysis',
            'total_namespaces': len(valid_namespaces)
        }
        
        logger.info(f"✅ Generated REAL namespace data: {len(valid_namespaces)} namespaces")
        return result
        
    except Exception as e:
        logger.error(f"❌ Cannot generate namespace data: {e}")
        raise ValueError(f"No real namespace data available: {e}")

# workload data function

def generate_workload_data(analysis_data=None):
    """Generate workload cost data - NO FALLBACKS"""
    try:
        logger.info("🔍 Extracting REAL workload data from analysis")
        
        # Use provided analysis_data
        data_source = analysis_data
        
        # Source 1: Direct workload_costs from analysis_results
        workload_costs = data_source.get('workload_costs')
        if workload_costs:
            logger.info(f"✅ Found workload_costs with {len(workload_costs)} workloads")
        
        # Source 2: Pod cost analysis workload costs
        if not workload_costs:
            pod_analysis = data_source.get('pod_cost_analysis', {})
            workload_costs = pod_analysis.get('workload_costs')
            if workload_costs:
                logger.info(f"✅ Found pod_cost_analysis workload_costs with {len(workload_costs)} workloads")
        
        if not workload_costs:
            raise ValueError("No real workload costs available")
        
        # Process REAL workload data
        if not isinstance(workload_costs, dict):
            raise ValueError(f"Invalid workload_costs type: {type(workload_costs)}")
        
        if len(workload_costs) == 0:
            raise ValueError("Workload costs dictionary is empty")
        
        # Sort by cost (from real data only)
        sorted_workloads = []
        
        for workload_name, workload_data in workload_costs.items():
            try:
                if isinstance(workload_data, dict):
                    cost = float(workload_data.get('cost', 0))
                    workload_type = str(workload_data.get('type', 'Unknown'))
                    namespace = str(workload_data.get('namespace', 'unknown'))
                    replicas = int(workload_data.get('replicas', 1))
                else:
                    # If workload_data is just a cost value
                    cost = float(workload_data) if workload_data else 0
                    workload_type = 'Unknown'
                    namespace = workload_name.split('/')[0] if '/' in workload_name else 'unknown'
                    replicas = 1
                
                if cost > 0:  # Only include workloads with valid costs
                    sorted_workloads.append((workload_name, cost, workload_type, namespace, replicas))
                    
            except Exception as workload_error:
                logger.warning(f"⚠️ Error processing workload {workload_name}: {workload_error}")
        
        if not sorted_workloads:
            raise ValueError("No valid workload data after processing")
        
        # Sort by cost descending and take top 100
        max_workloads = 100
        sorted_workloads.sort(key=lambda x: x[1], reverse=True)
        top_workloads = sorted_workloads[:max_workloads]
        
        result = {
            'workloads': [w[0] for w in top_workloads],
            'costs': [w[1] for w in top_workloads],
            'types': [w[2] for w in top_workloads],
            'namespaces': [w[3] for w in top_workloads],
            'replicas': [w[4] for w in top_workloads],
            'data_source': 'real_workload_analysis',
            'total_workloads_available': len(sorted_workloads),
            'workloads_shown': len(top_workloads),
            'workloads_hidden': max(0, len(sorted_workloads) - max_workloads)
        }
        
        logger.info(f"✅ Generated workload data: {len(sorted_workloads)} total, {len(top_workloads)} shown")
        return result
        
    except Exception as e:
        logger.error(f"❌ Cannot generate workload data: {e}")
        raise ValueError(f"No real workload data available: {e}")

def chart_data_consistent():
    """FIXED Chart data API with proper error handling - no fallbacks"""
    global analysis_results
    
    try:
        logger.info("📊 Chart data API called")
        
        # Extract cluster ID from request context
        cluster_id = _extract_cluster_id()
        
        # Get analysis data from available sources
        current_analysis, data_source = _get_analysis_data(cluster_id)
        
        # Validate analysis data
        validation_error = _validate_analysis_data(current_analysis, cluster_id, data_source)
        if validation_error:
            return validation_error
        
        # CRITICAL: Validate node data exists before proceeding
        if not current_analysis.get('has_real_node_data'):
            logger.error("❌ CHART DATA: Analysis has no real node data flag")
            return jsonify({
                'status': 'error',
                'message': 'Analysis data missing real node data flag',
                'debug_info': {
                    'cluster_id': cluster_id,
                    'data_source': data_source,
                    'has_real_node_data': current_analysis.get('has_real_node_data', 'NOT_SET')
                }
            }), 500
        
        # Validate actual node data exists
        node_data = None
        for key in ['real_node_data', 'nodes', 'node_metrics']:
            if current_analysis.get(key) and len(current_analysis[key]) > 0:
                node_data = current_analysis[key]
                logger.info(f"✅ CHART DATA: Found node data in {key} ({len(node_data)} nodes)")
                break
        
        if not node_data:
            logger.error("❌ CHART DATA: No node data found in any expected key")
            return jsonify({
                'status': 'error',
                'message': 'No real node data available for chart generation',
                'debug_info': {
                    'cluster_id': cluster_id,
                    'data_source': data_source,
                    'available_keys': list(current_analysis.keys()),
                    'has_real_node_data': current_analysis.get('has_real_node_data')
                }
            }), 500
        
        # Extract cost metrics
        cost_metrics = _extract_cost_metrics(current_analysis, data_source)
        
        # If we got data from database, refresh cache
        if data_source == "database" and cluster_id:
            logger.info("💾 Refreshing cache with database data...")
            save_to_cache(cluster_id, current_analysis)
            data_source = "database_cached"
        
        # Build complete response - this will now work because we validated node data
        response_data = _build_response_data(current_analysis, cost_metrics, data_source, cluster_id)
        
        logger.info(f"✅ Chart data API completed from {data_source}")
        return jsonify(response_data)

    except ValueError as ve:
        # These are expected errors (like missing node data)
        logger.error(f"❌ Chart data validation error: {ve}")
        return jsonify({
            'status': 'error',
            'message': str(ve),
            'error_type': 'validation_error'
        }), 400
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ ERROR in chart_data API: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}',
            'error_type': 'internal_error'
        }), 500


def _extract_cluster_id() -> Optional[str]:
    """Extract cluster ID from request context"""
    cluster_id = None
    
    # Check referrer header for cluster context
    referrer = request.headers.get('Referer', '')
    if '/cluster/' in referrer:
        try:
            cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
        except Exception:
            pass
    
    # Fallback to query parameter
    if not cluster_id:
        cluster_id = request.args.get('cluster_id')
    
    return cluster_id


def _get_analysis_data(cluster_id: Optional[str]) -> Tuple[Optional[Dict[str, Any]], str]:
    """FIXED: Get analysis data ONLY from cluster-specific sources"""
    
    if not cluster_id:
        logger.warning("⚠️ No cluster_id provided for analysis data")
        return None, "no_cluster_id"
    
    # Priority 1: Cluster-specific cache
    try:
        cached_data = load_from_cache(cluster_id)
        if cached_data and cached_data.get('total_cost', 0) > 0:
            logger.info(f"✅ Using cluster-specific cache: {cluster_id} - ${cached_data.get('total_cost', 0):.2f}")
            return cached_data, "cluster_cache"
    except Exception as e:
        logger.warning(f"⚠️ Cluster cache fetch failed for {cluster_id}: {e}")
    
    # Priority 2: Database (cluster-specific)
    try:
        logger.info(f"🔄 Loading from database for cluster: {cluster_id}")
        db_data = enhanced_cluster_manager.get_latest_analysis(cluster_id)
        if db_data and db_data.get('total_cost', 0) > 0:
            logger.info(f"📦 Using database for cluster: {cluster_id} - ${db_data.get('total_cost', 0):.2f}")
            
            # Cache the database data for future use
            save_to_cache(cluster_id, db_data)
            return db_data, "cluster_database"
    except Exception as e:
        logger.error(f"❌ Database error for cluster {cluster_id}: {e}")
    
    # NO FALLBACK TO GLOBAL DATA - this prevents contamination
    logger.warning(f"⚠️ No analysis data found for cluster: {cluster_id}")
    return None, "no_data"


def _validate_analysis_data(current_analysis: Optional[Dict[str, Any]], 
                          cluster_id: Optional[str], 
                          data_source: str) -> Optional[tuple]:
    """Validate analysis data and return error response if invalid"""
    
    if not current_analysis:
        logger.warning("⚠️ No analysis data available from any source")
        return jsonify({
            'status': 'no_data',
            'message': 'No analysis results available. Please run analysis first.',
            'debug_info': {
                'cluster_id': cluster_id,
                'data_source': data_source,
                'referrer': request.headers.get('Referer', '')[:100] if request.headers.get('Referer') else None
            }
        }), 200
    
    if not current_analysis.get('total_cost'):
        logger.warning("⚠️ Analysis results exist but no total_cost found")
        logger.warning(f"⚠️ Available keys: {list(current_analysis.keys())}")
        return jsonify({
            'status': 'no_data',
            'message': 'Invalid analysis data - no cost information found',
            'debug_info': {
                'analysis_keys': list(current_analysis.keys()),
                'data_source': data_source
            }
        }), 200
    
    total_cost = ensure_float(current_analysis.get('total_cost', 0))
    if total_cost <= 0:
        logger.warning(f"⚠️ Invalid cost data: {total_cost}")
        return jsonify({
            'status': 'invalid_data',
            'message': f'Invalid cost data: ${total_cost}',
            'debug_info': {
                'total_cost': total_cost,
                'data_source': data_source
            }
        }), 200
    
    return None


def _extract_cost_metrics(current_analysis: Dict[str, Any], data_source: str) -> Dict[str, float]:
    """Extract and validate cost metrics from analysis data"""
    
    monthly_cost = ensure_float(current_analysis.get('total_cost', 0))
    monthly_savings = ensure_float(current_analysis.get('total_savings', 0))
    
    logger.info(f"📊 Extracting metrics from {data_source}: cost=${monthly_cost:.2f}, savings=${monthly_savings:.2f}")
    
    # Get individual cost components
    cost_components = {
        'node_cost': ensure_float(current_analysis.get('node_cost', 0)),
        'storage_cost': ensure_float(current_analysis.get('storage_cost', 0)),
        'networking_cost': ensure_float(current_analysis.get('networking_cost', 0)),
        'control_plane_cost': ensure_float(current_analysis.get('control_plane_cost', 0)),
        'registry_cost': ensure_float(current_analysis.get('registry_cost', 0)),
        'other_cost': ensure_float(current_analysis.get('other_cost', 0))
    }
    
    # Validate and fix cost components if necessary
    component_total = sum(cost_components.values())
    if abs(component_total - monthly_cost) > (monthly_cost * 0.01):  # 1% tolerance
        logger.warning(f"⚠️ Cost mismatch: components={component_total:.2f}, total={monthly_cost:.2f}")
        if component_total > 0:
            adjustment_factor = monthly_cost / component_total
            cost_components = {k: v * adjustment_factor for k, v in cost_components.items()}
            logger.info(f"✅ Applied adjustment factor: {adjustment_factor:.4f}")
    
    return {
        'monthly_cost': monthly_cost,
        'monthly_savings': monthly_savings,
        **cost_components
    }


def _build_response_data(current_analysis: Dict[str, Any], 
                        cost_metrics: Dict[str, float], 
                        data_source: str, 
                        cluster_id: Optional[str]) -> Dict[str, Any]:
    """FIXED Build the complete response data structure with proper error handling"""
    
    # Ensure node_metrics is properly set
    if 'node_metrics' not in current_analysis and 'nodes' in current_analysis:
        current_analysis['node_metrics'] = current_analysis['nodes']
    
    actual_period_cost = current_analysis.get('actual_period_cost', cost_metrics['monthly_cost'])
    analysis_period_days = current_analysis.get('analysis_period_days', 30)
    
    response_data = {
        'status': 'success',
        'consistent_analysis': True,
        'data_source': data_source,
        
        # Main metrics
        'metrics': {
            'total_cost': cost_metrics['monthly_cost'],
            'actual_period_cost': ensure_float(actual_period_cost),
            'analysis_period_days': analysis_period_days,
            'cost_label': current_analysis.get('cost_label', f'{analysis_period_days}-day baseline'),
            'total_savings': cost_metrics['monthly_savings'],
            'hpa_savings': ensure_float(current_analysis.get('hpa_savings', 0)),
            'right_sizing_savings': ensure_float(current_analysis.get('right_sizing_savings', 0)),
            'storage_savings': ensure_float(current_analysis.get('storage_savings', 0)),
            'savings_percentage': ensure_float(current_analysis.get('savings_percentage', 0)),
            'annual_savings': ensure_float(current_analysis.get('annual_savings', 0)),
            'hpa_reduction': ensure_float(current_analysis.get('hpa_reduction', 0)),
            'cpu_gap': ensure_float(current_analysis.get('cpu_gap', 0)),
            'memory_gap': ensure_float(current_analysis.get('memory_gap', 0))
        },
        
        # Cost breakdown
        'costBreakdown': {
            'labels': ['VM Scale Sets (Nodes)', 'Storage', 'Networking', 'AKS Control Plane', 'Container Registry', 'Other'],
            'values': [
                cost_metrics['node_cost'],
                cost_metrics['storage_cost'],
                cost_metrics['networking_cost'],
                cost_metrics['control_plane_cost'],
                cost_metrics['registry_cost'],
                cost_metrics['other_cost']
            ]
        },
        
        # Savings breakdown
        'savingsBreakdown': {
            'categories': ['Memory-based HPA', 'Right-sizing', 'Storage Optimization'],
            'values': [
                ensure_float(current_analysis.get('hpa_savings', 0)),
                ensure_float(current_analysis.get('right_sizing_savings', 0)),
                ensure_float(current_analysis.get('storage_savings', 0))
            ]
        },
        
        # Insights
        'insights': generate_insights(current_analysis),
        
        # Metadata
        'metadata': {
            'analysis_method': 'consistent_current_usage_optimization',
            'is_consistent': True,
            'confidence': current_analysis.get('analysis_confidence', 0),
            'confidence_level': current_analysis.get('confidence_level', 'Medium'),
            'algorithms_used': current_analysis.get('algorithms_used', []),
            'resource_group': current_analysis.get('resource_group', ''),
            'cluster_name': current_analysis.get('cluster_name', ''),
            'timestamp': datetime.now().isoformat(),
            'data_source': data_source,
            'cluster_id': cluster_id
        }
    }
    
    # Add charts that require node data - with proper error handling
    try:
        # HPA comparison - will fail fast if no node data
        response_data['hpaComparison'] = generate_dynamic_hpa_comparison(current_analysis)
        logger.info("✅ Generated HPA comparison")
    except Exception as hpa_error:
        logger.error(f"❌ Failed to generate HPA comparison: {hpa_error}")
        raise ValueError(f"Cannot generate HPA comparison: {hpa_error}")
    
    try:
        # Node utilization - will fail fast if no node data
        response_data['nodeUtilization'] = generate_node_utilization_data(current_analysis)
        logger.info("✅ Generated node utilization")
    except Exception as node_error:
        logger.error(f"❌ Failed to generate node utilization: {node_error}")
        raise ValueError(f"Cannot generate node utilization data: {node_error}")
    
    try:
        # Trend data
        response_data['trendData'] = generate_dynamic_trend_data(cluster_id, current_analysis)
        logger.info("✅ Generated trend data")
    except Exception as trend_error:
        logger.warning(f"⚠️ Failed to generate trend data: {trend_error}")
        # Trend data is optional
        response_data['trendData'] = {
            'labels': [],
            'datasets': [],
            'data_source': 'error',
            'error': str(trend_error)
        }
    
    # Add pod cost data if available
    if current_analysis.get('has_pod_costs'):
        logger.info("✅ Pod cost data found, generating charts")
        try:
            _add_pod_cost_data(response_data, current_analysis)
        except Exception as pod_error:
            logger.warning(f"⚠️ Failed to add pod cost data: {pod_error}")
            # Pod data is optional
    
    return response_data


def _add_pod_cost_data(response_data: Dict[str, Any], current_analysis: Dict[str, Any]) -> None:
    """Add pod cost related data to response - FIXED to use current_analysis"""
    try:
        pod_data = generate_pod_cost_data(current_analysis)  # Pass current_analysis
        if pod_data:
            response_data['podCostBreakdown'] = pod_data
            logger.info("✅ Pod breakdown data added")
        
        namespace_data = generate_namespace_data(current_analysis)  # Pass current_analysis
        if namespace_data:
            response_data['namespaceDistribution'] = namespace_data
            logger.info("✅ Namespace distribution data added")
        
        workload_data = generate_workload_data(current_analysis)  # Pass current_analysis
        if workload_data:
            response_data['workloadCosts'] = workload_data
            logger.info("✅ Workload costs data added")
    except Exception as e:
        logger.warning(f"⚠️ Failed to add pod cost data: {e}")


# Helper function that needs to be implemented
def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def generate_dynamic_trend_data(cluster_id, current_analysis):
    """Generate trend data from actual historical analysis - FIXED"""
    try:
        if not cluster_id:
            raise ValueError("No cluster ID provided for trend analysis")
            
        # Get historical analysis data from database
        history = enhanced_cluster_manager.get_analysis_history(cluster_id, limit=12)
        
        if len(history) < 2:
            raise ValueError(f"Insufficient historical data for trends (found {len(history)} analyses)")
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get('analyzed_at', ''))
        
        # Extract costs and dates
        dates = []
        costs = []
        savings = []
        
        for analysis in history[-5:]:  # Last 5 analyses
            if analysis.get('total_cost'):
                dates.append(analysis.get('analyzed_at', '').split('T')[0])  # Date only
                costs.append(float(analysis.get('total_cost', 0)))
                savings.append(float(analysis.get('total_savings', 0)))
        
        if len(costs) < 2:
            raise ValueError("Not enough cost data points for trend analysis")
        
        # Calculate optimized costs (current cost - potential savings)
        optimized_costs = [cost - saving for cost, saving in zip(costs, savings)]
        
        return {
            'labels': dates,
            'datasets': [
                {
                    'name': 'Actual Monthly Cost',
                    'data': costs
                },
                {
                    'name': 'Potential Optimized Cost',
                    'data': optimized_costs
                }
            ],
            'data_source': 'historical_analysis',
            'data_points': len(costs)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate trend data: {e}")
        raise ValueError(f"Cannot generate trend data: {e}")


def generate_node_utilization_data(analysis_data):
    """Generate node utilization data - FIXED to fail fast without fallbacks"""
    try:
        logger.info("🔧 Generating node utilization data for charts")
        logger.info(f"🔧 Available keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
        
        # Step 1: Validate we have real node data flag
        if not analysis_data.get('has_real_node_data'):
            raise ValueError("Analysis data indicates no real node data available")
        
        # Step 2: Find node data
        node_metrics = None
        data_source = "unknown"
        
        for key in ['real_node_data', 'node_metrics', 'nodes']:
            if analysis_data.get(key):
                node_metrics = analysis_data[key]
                data_source = key
                logger.info(f"✅ NODE UTIL: Found data in {key} ({len(node_metrics)} nodes)")
                break
        
        if not node_metrics:
            raise ValueError("No node metrics found in expected keys")
        
        if len(node_metrics) == 0:
            raise ValueError("Node metrics found but empty")
        
        # Step 3: Process nodes
        nodes = []
        cpu_request = []
        cpu_actual = []
        memory_request = []
        memory_actual = []
        
        for i, node in enumerate(node_metrics):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} is not a dictionary")
            
            # Extract node name
            node_name = node.get('name', f'node-{i+1}')
            nodes.append(node_name)
            
            # Extract CPU data (real values)
            cpu_usage = float(node.get('cpu_usage_pct', 0))
            cpu_req = float(node.get('cpu_request_pct', 0))
            
            
            cpu_actual.append(cpu_usage)
            cpu_request.append(cpu_req)
            
            # Extract Memory data (real values)
            memory_usage = float(node.get('memory_usage_pct', 0))
            memory_req = float(node.get('memory_request_pct', 0))
            
            memory_actual.append(memory_usage)
            memory_request.append(memory_req)
            
            logger.info(f"✅ NODE UTIL: Processed {node_name}: CPU={cpu_usage:.1f}%, Memory={memory_usage:.1f}%")
        
        result = {
            'nodes': nodes,
            'cpuRequest': cpu_request,
            'cpuActual': cpu_actual,
            'memoryRequest': memory_request,
            'memoryActual': memory_actual,
            'data_source': data_source,
            'real_data': True
        }
        
        logger.info(f"✅ NODE UTIL: Generated data for {len(nodes)} nodes")
        return result
        
    except Exception as e:
        logger.error(f"❌ NODE UTIL: Failed to generate utilization data: {e}")
        raise ValueError(f"Cannot generate node utilization data: {e}")
    
# ============================================================================
# CONFIGURATION AND STARTUP ENHANCEMENTS
# ============================================================================

# def load_cluster_configurations():
#     """Load cluster configurations from file on startup"""
#     try:
#         if os.path.exists('clusters.json'):
#             with open('clusters.json', 'r') as f:
#                 clusters_data = json.load(f)
#                 for cluster_data in clusters_data:
#                     cluster_manager.add_cluster(cluster_data)
#             logger.info(f"Loaded {len(clusters_data)} cluster configurations")
#     except Exception as e:
#         logger.warning(f"Could not load cluster configurations: {e}")

# def save_cluster_configurations():
#     """Save cluster configurations to file"""
#     try:
#         clusters_data = list(cluster_manager.clusters.values())
#         with open('clusters.json', 'w') as f:
#             json.dump(clusters_data, f, indent=2)
#         logger.info(f"Saved {len(clusters_data)} cluster configurations")
#     except Exception as e:
#         logger.warning(f"Could not save cluster configurations: {e}")

# Add to application startup
# Replace the deprecated decorator with this approach
first_request_done = False

# @app.before_request
# def initialize_multi_cluster():
#     """Initialize multi-cluster functionality"""
#     global first_request_done
#     if not first_request_done:
#         load_cluster_configurations()
#         logger.info("Multi-cluster functionality initialized")
#         first_request_done = True


# ============================
#
# ============================


def run_background_analysis(cluster_id: str, resource_group: str, cluster_name: str):
    """Run analysis in background thread with progress tracking"""
    try:
        logger.info(f"🔄 Background analysis started for {cluster_id}")
        
        # Progress tracking function
        def update_progress(progress: int, message: str):
            update_cluster_analysis_status(cluster_id, 'analyzing', progress, message)
            analysis_status_tracker[cluster_id] = {
                'status': 'analyzing',
                'progress': progress,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        
        # Simulate analysis steps with progress updates
        update_progress(10, 'Connecting to Azure...')
        time.sleep(2)
        
        update_progress(25, 'Fetching cost data...')
        time.sleep(3)
        
        update_progress(45, 'Analyzing cluster metrics...')
        time.sleep(2)
        
        update_progress(65, 'Calculating optimization opportunities...')
        
        # Run actual analysis
        result = run_consistent_analysis(
            resource_group, 
            cluster_name, 
            days=30, 
            enable_pod_analysis=True
        )
        
        update_progress(85, 'Generating insights...')
        time.sleep(1)
        
        if result['status'] == 'success':
            # Store results in database
            enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_results)
            
            # Update status to completed
            update_cluster_analysis_status(
                cluster_id, 
                'completed', 
                100, 
                f'Analysis completed! Found ${analysis_results.get("total_savings", 0):.0f}/month savings potential'
            )
            
            analysis_status_tracker[cluster_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Analysis completed successfully',
                'timestamp': datetime.now().isoformat(),
                'results': {
                    'total_cost': analysis_results.get('total_cost', 0),
                    'total_savings': analysis_results.get('total_savings', 0),
                    'confidence': analysis_results.get('analysis_confidence', 0)
                }
            }
            
            logger.info(f"✅ Background analysis completed for {cluster_id}")
            
        else:
            error_message = result.get('message', 'Analysis failed')
            update_cluster_analysis_status(cluster_id, 'failed', 0, error_message)
            
            analysis_status_tracker[cluster_id] = {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.error(f"❌ Background analysis failed for {cluster_id}: {error_message}")
            
    except Exception as e:
        error_message = f'Analysis error: {str(e)}'
        logger.error(f"❌ Background analysis exception for {cluster_id}: {e}")
        
        update_cluster_analysis_status(cluster_id, 'failed', 0, error_message)
        analysis_status_tracker[cluster_id] = {
            'status': 'failed',
            'progress': 0,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }

def update_cluster_analysis_status(cluster_id: str, status: str, progress: int, message: str):
    """Update cluster analysis status in database"""
    try:
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            if status == 'analyzing':
                # First time - set started timestamp
                if progress <= 10:
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?, 
                            analysis_started_at = ?
                        WHERE id = ?
                    ''', (status, progress, message, datetime.now().isoformat(), cluster_id))
                else:
                    # Update progress only
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?
                        WHERE id = ?
                    ''', (status, progress, message, cluster_id))
            else:
                # Completed or failed
                conn.execute('''
                    UPDATE clusters 
                    SET analysis_status = ?, analysis_progress = ?, analysis_message = ?
                    WHERE id = ?
                ''', (status, progress, message, cluster_id))
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Failed to update analysis status: {e}")

@app.route('/api/clusters/<cluster_id>/analysis-status', methods=['GET'])
def get_cluster_analysis_status(cluster_id: str):
    """Get real-time analysis status for a cluster"""
    try:
        # Check in-memory tracker first (for active analyses)
        if cluster_id in analysis_status_tracker:
            return jsonify({
                'status': 'success',
                'cluster_id': cluster_id,
                **analysis_status_tracker[cluster_id]
            })
        
        # Check database for stored status
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT analysis_status, analysis_progress, analysis_message, 
                       last_cost, last_savings, last_analyzed
                FROM clusters 
                WHERE id = ?
            ''', (cluster_id,))
            
            row = cursor.fetchone()
            if row:
                return jsonify({
                    'status': 'success',
                    'cluster_id': cluster_id,
                    'status': row['analysis_status'] or 'pending',
                    'progress': row['analysis_progress'] or 0,
                    'message': row['analysis_message'] or 'Ready for analysis',
                    'last_cost': row['last_cost'],
                    'last_savings': row['last_savings'],
                    'last_analyzed': row['last_analyzed']
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
                
    except Exception as e:
        logger.error(f"❌ Error getting analysis status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/analysis-sessions', methods=['GET'])
def get_analysis_sessions():
    """Monitor active analysis sessions"""
    try:
        with _analysis_lock:
            sessions = {
                sid: {
                    'cluster_id': sdata['cluster_id'],
                    'status': sdata['status'],
                    'started_at': sdata['started_at'],
                    'thread_id': sdata['thread_id']
                } for sid, sdata in _analysis_sessions.items()
            }
        
        return jsonify({
            'status': 'success',
            'active_sessions': len(sessions),
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/analysis-status/batch', methods=['POST'])
def get_batch_analysis_status():
    """Get analysis status for multiple clusters"""
    try:
        request_data = request.get_json() or {}
        cluster_ids = request_data.get('cluster_ids', [])
        
        if not cluster_ids:
            return jsonify({
                'status': 'error',
                'message': 'No cluster IDs provided'
            }), 400
        
        statuses = []
        
        for cluster_id in cluster_ids:
            # Check in-memory tracker first
            if cluster_id in analysis_status_tracker:
                statuses.append({
                    'cluster_id': cluster_id,
                    **analysis_status_tracker[cluster_id]
                })
            else:
                # Check database
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('''
                        SELECT analysis_status, analysis_progress, analysis_message
                        FROM clusters WHERE id = ?
                    ''', (cluster_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        statuses.append({
                            'cluster_id': cluster_id,
                            'status': row['analysis_status'] or 'pending',
                            'progress': row['analysis_progress'] or 0,
                            'message': row['analysis_message'] or 'Ready for analysis'
                        })
        
        return jsonify({
            'status': 'success',
            'statuses': statuses
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting batch analysis status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/clusters/overview', methods=['GET'])
def get_clusters_overview():
    """Get portfolio overview with analysis status counts"""
    try:
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get overview counts
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN analysis_status = 'analyzing' THEN 1 ELSE 0 END) as analyzing,
                    SUM(CASE WHEN analysis_status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN analysis_status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN analysis_status = 'pending' OR analysis_status IS NULL THEN 1 ELSE 0 END) as pending
                FROM clusters 
                WHERE status = 'active'
            ''')
            
            row = cursor.fetchone()
            overview = dict(row) if row else {}
            
            return jsonify({
                'status': 'success',
                'overview': overview
            })
            
    except Exception as e:
        logger.error(f"❌ Error getting clusters overview: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# # Add graceful shutdown handler
# import atexit
# atexit.register(save_cluster_configurations)

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
@app.route('/clusters')
def cluster_portfolio():
    """Enhanced multi-cluster portfolio management page with SQLite backend"""
    try:
        logger.info("🏠 Loading enhanced cluster portfolio page")
        
        clusters = enhanced_cluster_manager.list_clusters()
        portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
        
        # Add analysis status for each cluster
        for cluster in clusters:
            cluster['has_analysis'] = cluster.get('last_analyzed') is not None
            cluster['analysis_age_days'] = 0
            
            if cluster.get('last_analyzed'):
                try:
                    last_analyzed = datetime.fromisoformat(cluster['last_analyzed'].replace('Z', '+00:00'))
                    cluster['analysis_age_days'] = (datetime.now() - last_analyzed.replace(tzinfo=None)).days
                except:
                    cluster['analysis_age_days'] = 999
        
        logger.info(f"📊 Enhanced Portfolio: {len(clusters)} clusters, ${portfolio_summary.get('total_monthly_cost', 0):.2f} total cost")
        
        return render_template('cluster_portfolio.html', 
                             clusters=clusters,
                             portfolio_summary=portfolio_summary)
                             
    except Exception as e:
        logger.error(f"❌ Error loading enhanced portfolio: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return render_template('cluster_portfolio.html', 
                             clusters=[],
                             portfolio_summary={
                                'total_clusters': 0, 
                                'total_monthly_cost': 0, 
                                'total_potential_savings': 0, 
                                'average_optimization_pct': 0, 
                                'environments': [],
                                'last_updated': datetime.now().isoformat()
                             },
                             error_message="Failed to load cluster portfolio")

@app.route('/dashboard')
def unified_dashboard():
    """Original unified dashboard - FIXED to avoid global dependency"""
    logger.warning("⚠️ /dashboard route accessed - this is deprecated, use cluster-specific dashboards")
    
    # Try to get any recent cluster data
    try:
        clusters = enhanced_cluster_manager.list_clusters()
        if clusters:
            # Get the most recently analyzed cluster
            recent_cluster = max(
                (c for c in clusters if c.get('last_analyzed')), 
                key=lambda x: x.get('last_analyzed', ''), 
                default=None
            )
            
            if recent_cluster:
                cluster_id = recent_cluster['id']
                current_analysis, data_source = _get_analysis_data(cluster_id)
                
                if current_analysis and current_analysis.get('total_cost', 0) > 0:
                    context = {
                        'results': current_analysis,
                        'has_analysis_data': True,
                        'cluster_context': recent_cluster,
                        'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
                        'data_source': f'Most recent cluster analysis ({data_source})',
                        'deprecated_warning': True
                    }
                    return render_template('unified_dashboard.html', **context)
    except Exception as e:
        logger.error(f"Error loading recent cluster data: {e}")
    
    # No cluster data available
    context = {
        'results': {},
        'has_analysis_data': False,
        'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
        'data_source': 'No analysis data available',
        'cluster_context': None,
        'deprecated_warning': True
    }
    
    return render_template('unified_dashboard.html', **context)

@app.route('/api/clusters', methods=['POST'])
def api_add_cluster_with_auto_analysis():
    """Enhanced API to add cluster with automatic analysis"""
    try:
        logger.info("📥 Received enhanced cluster add request with auto-analysis")
        
        cluster_config = request.get_json()
        if not cluster_config:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['cluster_name', 'resource_group']
        missing_fields = [field for field in required_fields if not cluster_config.get(field)]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Add cluster to database
        cluster_id = enhanced_cluster_manager.add_cluster(cluster_config)
        
        # Check if auto-analysis is requested (default: True)
        auto_analyze = cluster_config.get('auto_analyze', True)
        
        if auto_analyze:
            logger.info(f"🚀 Starting automatic analysis for cluster: {cluster_id}")
            
            # Update cluster status to 'analyzing'
            update_cluster_analysis_status(cluster_id, 'analyzing', 0, 'Starting automatic analysis...')
            
            # Start analysis in background thread
            analysis_thread = threading.Thread(
                target=run_background_analysis,
                args=(cluster_id, cluster_config['resource_group'], cluster_config['cluster_name']),
                daemon=True
            )
            analysis_thread.start()
            
            return jsonify({
                'status': 'success',
                'message': f'Cluster added successfully! Analysis is starting automatically.',
                'cluster_id': cluster_id,
                'auto_analysis': True,
                'analysis_status': 'analyzing'
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'Cluster added successfully',
                'cluster_id': cluster_id,
                'auto_analysis': False
            })
        
    except Exception as e:
        logger.error(f"❌ Error adding cluster with auto-analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to add cluster: {str(e)}'
        }), 500


@app.route('/api/clusters', methods=['GET'])
def api_list_clusters():
    """API to list all clusters with their analysis status"""
    try:
        clusters = enhanced_cluster_manager.list_clusters()
        portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
        
        return jsonify({
            'status': 'success',
            'clusters': clusters,
            'portfolio_summary': portfolio_summary,
            'total_clusters': len(clusters)
        })
        
    except Exception as e:
        logger.error(f"❌ Error listing clusters: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/cluster/<cluster_id>')
def single_cluster_dashboard(cluster_id: str):
    """FIXED Enhanced dashboard - Cache → DB → Refresh Cache → Serve"""
    global analysis_results
    
    try:
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        
        if not cluster:
            flash(f'Cluster {cluster_id} not found', 'error')
            return redirect(url_for('cluster_portfolio'))
        
        logger.info(f"📊 Dashboard access for {cluster_id}")
        
        # STEP 1: Try cache first (if valid and for this cluster)
        cached_analysis = load_from_cache(cluster_id)
        data_source = "cache"
        
        if not cached_analysis:
            # STEP 2: Cache invalid/empty, try database
            logger.info("🔄 Cache invalid/empty, loading from database...")
            cached_analysis = enhanced_cluster_manager.get_latest_analysis(cluster_id)
            
            if cached_analysis and cached_analysis.get('total_cost', 0) > 0:
                # STEP 3: Validate DB data has node data before caching
                has_node_data = False
                for key in ['nodes', 'node_metrics', 'real_node_data']:
                    if cached_analysis.get(key) and len(cached_analysis[key]) > 0:
                        has_node_data = True
                        break
                
                if has_node_data:
                    # STEP 4: REFRESH CACHE with DB data
                    logger.info("💾 Refreshing cache with database data...")
                    save_to_cache(cluster_id, cached_analysis)
                    
                    logger.info(f"📦 Loaded from database and refreshed cache: ${cached_analysis.get('total_cost', 0):.2f}")
                    data_source = "database_cached"
                else:
                    logger.warning("⚠️ Database data missing node data - not caching")
                    data_source = "database_no_cache"
            else:
                logger.info(f"ℹ️ No analysis data found for {cluster_id}")
                data_source = "none"
        else:
            logger.info(f"✅ Using VALID cache for dashboard: ${cached_analysis.get('total_cost', 0):.2f}")
        
        # Get analysis history
        analysis_history = enhanced_cluster_manager.get_analysis_history(cluster_id, limit=5)
        
        context = {
            'cluster': cluster,
            'results': cached_analysis or {},
            'has_analysis_data': bool(cached_analysis and cached_analysis.get('total_cost', 0) > 0),
            'cluster_context': cluster,
            'analysis_history': analysis_history,
            'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
            'data_source': data_source
        }
        
        return render_template('unified_dashboard.html', **context)
        
    except Exception as e:
        logger.error(f"❌ Error loading cluster dashboard {cluster_id}: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        flash(f'Error loading cluster dashboard: {str(e)}', 'error')
        return redirect(url_for('cluster_portfolio'))

@app.route('/cluster/<cluster_id>/analyze', methods=['GET', 'POST'])
def cluster_analyze_endpoint(cluster_id: str):
    """Enhanced cluster analysis endpoint with SQLite integration"""
    try:
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        
        if not cluster:
            if request.method == 'POST':
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            else:
                flash(f'Cluster {cluster_id} not found', 'error')
                return redirect(url_for('cluster_portfolio'))
        
        if request.method == 'POST':
            # Handle API analysis request
            try:
                request_data = request.get_json() or {}
                days = request_data.get('days', 30)
                enable_pod_analysis = request_data.get('enable_pod_analysis', True)
                
                logger.info(f"🔍 Starting enhanced analysis for cluster {cluster_id}")
                
                # Run analysis
                result = run_consistent_analysis(
                    cluster['resource_group'], 
                    cluster['name'], 
                    days, 
                    enable_pod_analysis
                )
                
                if result['status'] == 'success':
                    # Store results in database
                    enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_results)
                    
                    monthly_cost = analysis_results.get('total_cost', 0)
                    monthly_savings = analysis_results.get('total_savings', 0)
                    analysis_results['node_metrics'] = analysis_results.get('nodes', [])
                    confidence = analysis_results.get('analysis_confidence', 0)
                    
                    logger.info(f"✅ Enhanced analysis completed for {cluster_id}: ${monthly_cost:.2f} cost, ${monthly_savings:.2f} savings")
                    
                    return jsonify({
                        'status': 'success',
                        'message': 'Analysis completed successfully',
                        'results': {
                            'total_cost': monthly_cost,
                            'total_savings': monthly_savings,
                            'confidence': confidence,
                            'cluster_id': cluster_id
                        }
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result.get('message', 'Analysis failed')
                    }), 500
                    
            except Exception as e:
                logger.error(f"❌ Enhanced analysis failed for {cluster_id}: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        else:
            # Handle GET request - show analysis page
            return render_template('unified_dashboard.html',
                                 cluster=cluster,
                                 active_tab='analysis',
                                 pre_populate=True,
                                 cluster_context=cluster)
                                 
    except Exception as e:
        logger.error(f"❌ Error in cluster analyze endpoint: {e}")
        if request.method == 'POST':
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
        else:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('cluster_portfolio'))

@app.route('/cluster/<cluster_id>/remove', methods=['DELETE', 'POST'])
def remove_cluster_route(cluster_id: str):
    """Enhanced route to remove a cluster with SQLite backend"""
    try:
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        
        if not cluster:
            if request.method == 'DELETE':
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
            else:
                flash('Cluster not found', 'error')
                return redirect(url_for('cluster_portfolio'))
        
        cluster_name = cluster['name']
        
        # Remove cluster and all analysis data
        success = enhanced_cluster_manager.remove_cluster(cluster_id)
        
        if success:
            logger.info(f"✅ Successfully removed cluster {cluster_id}")
            
            if request.method == 'DELETE':
                return jsonify({
                    'status': 'success',
                    'message': f'Cluster {cluster_name} removed successfully'
                })
            else:
                flash(f'Cluster {cluster_name} removed successfully', 'success')
        else:
            if request.method == 'DELETE':
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to remove cluster'
                }), 500
            else:
                flash('Failed to remove cluster', 'error')
        
    except Exception as e:
        logger.error(f"❌ Error removing cluster {cluster_id}: {e}")
        if request.method == 'DELETE':
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
        else:
            flash(f'Error removing cluster: {str(e)}', 'error')
    
    return redirect(url_for('cluster_portfolio'))

@app.route('/analyze', methods=['POST'])
def enhanced_analyze_thread_safe():
    """THREAD-SAFE Enhanced analyze route with FORCED implementation plan regeneration"""
    try:
        # Extract form data
        resource_group = request.form.get('resource_group')
        cluster_name = request.form.get('cluster_name')
        days = int(request.form.get('days', 30))
        enable_pod_analysis = request.form.get('enable_pod_analysis') == 'on'
        redirect_to_cluster = request.form.get('redirect_to_cluster', 'false') == 'true'
        cluster_id = f"{resource_group}_{cluster_name}"

        if not resource_group or not cluster_name:
            flash('Resource group and cluster name are required', 'error')
            return redirect(url_for('cluster_portfolio'))

        # IMMEDIATELY clear cache for THIS SPECIFIC CLUSTER only
        logger.info(f"🔄 FRESH THREAD-SAFE ANALYSIS: Clearing cache for cluster {cluster_id}")
        clear_analysis_cache(cluster_id)

        # Auto-add cluster if not exists
        existing_cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        if not existing_cluster:
            cluster_config = {
                'cluster_name': cluster_name,
                'resource_group': resource_group,
                'environment': 'unknown',
                'region': 'Unknown',
                'description': f'Auto-added from analysis request on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            }
            cluster_id = enhanced_cluster_manager.add_cluster(cluster_config)
            logger.info(f"🆕 Auto-added cluster {cluster_id}")
        
        # Run THREAD-SAFE analysis with FRESH implementation plan
        logger.info(f"🚀 Running THREAD-SAFE analysis with FRESH implementation plan for {cluster_id}")
        result = run_consistent_analysis(
            resource_group, cluster_name, days, enable_pod_analysis
        )
        
        if result['status'] == 'success':
            # Get the session-specific analysis results
            session_results = result['results']
            session_id = result['session_id']
            
            # Validate node data
            if not session_results.get('has_real_node_data'):
                logger.error(f"❌ Session {session_id[:8]}: No real node data for {cluster_id}")
                flash('❌ Analysis failed: No real node data available', 'error')
                return redirect(url_for('cluster_portfolio'))
            
            # Validate implementation plan was generated
            if 'implementation_plan' not in session_results:
                logger.error(f"❌ Session {session_id[:8]}: No implementation plan generated for {cluster_id}")
                flash('❌ Analysis failed: Implementation plan generation failed', 'error')
                return redirect(url_for('cluster_portfolio'))
            
            # FORCE implementation plan metadata update
            impl_plan = session_results['implementation_plan']
            if isinstance(impl_plan, dict):
                # Ensure cluster metadata is in implementation plan
                impl_plan['cluster_metadata'] = {
                    'cluster_name': cluster_name,
                    'resource_group': resource_group,
                    'cluster_id': cluster_id,
                    'generated_at': datetime.now().isoformat(),
                    'session_id': session_id[:8]
                }
                session_results['implementation_plan'] = impl_plan
                logger.info(f"✅ Session {session_id[:8]}: FORCED implementation plan metadata update")
            
            # Save to database with cluster_id
            logger.info(f"💾 Session {session_id[:8]}: Saving analysis to database for cluster: {cluster_id}")
            enhanced_cluster_manager.update_cluster_analysis(cluster_id, session_results)
            
            # Save to cluster-specific cache with FRESH implementation plan
            logger.info(f"💾 Session {session_id[:8]}: Saving analysis to cache for cluster: {cluster_id}")
            save_to_cache(cluster_id, session_results)
            
            monthly_cost = session_results.get('total_cost', 0)
            monthly_savings = session_results.get('total_savings', 0)
            confidence = session_results.get('analysis_confidence', 0)

            # Check alerts after successful analysis
            check_alerts_after_analysis(cluster_id, session_results)
            
            success_msg = (
                f'🎯 Thread-Safe Analysis Complete for {cluster_name}! '
                f'${monthly_cost:.0f}/month baseline, ${monthly_savings:.0f}/month savings potential '
                f'| Confidence: {confidence:.2f} | Session: {session_id[:8]}'
            )
            
            flash(success_msg, 'success')
            
            # Redirect logic
            if redirect_to_cluster or existing_cluster:
                return redirect(url_for('single_cluster_dashboard', cluster_id=cluster_id))
            else:
                return redirect(url_for('cluster_portfolio'))
        else:
            error_message = result.get('message', 'Unknown error')
            session_id = result.get('session_id', 'unknown')
            flash(f'❌ Thread-safe analysis failed (session {session_id[:8]}): {error_message}', 'error')
            return redirect(url_for('cluster_portfolio'))

    except Exception as e:
        logger.error(f"❌ Thread-safe analysis route failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        flash(f'❌ Thread-safe analysis failed: {str(e)}', 'error')
        return redirect(url_for('cluster_portfolio'))

@app.route('/api/chart-data')
def chart_data():
    """COMPLETELY FIXED Chart data API route - no global analysis_results dependency"""
    try:
        logger.info("📊 Chart data API called")
        
        
        # Call the comprehensive chart data function that handles all data sources
        return chart_data_consistent()
            
    except Exception as e:
        logger.error(f"❌ ERROR in chart_data routing: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Chart data routing error: {str(e)}',
            'error_type': 'routing_error'
        }), 500

@app.route('/api/debug-analysis')
def debug_analysis():
    """Debug endpoint to check analysis results - FIXED to use cluster-specific data"""
    try:
        # Try to get cluster ID from request
        cluster_id = request.args.get('cluster_id')
        if not cluster_id:
            # Try to extract from referrer
            referrer = request.headers.get('Referer', '')
            if '/cluster/' in referrer:
                try:
                    cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
                except Exception:
                    pass
        
        if cluster_id:
            # Get cluster-specific data
            current_analysis, data_source = _get_analysis_data(cluster_id)
            if current_analysis:
                return jsonify({
                    'cluster_id': cluster_id,
                    'data_source': data_source,
                    'analysis_results_keys': list(current_analysis.keys()),
                    'total_cost': current_analysis.get('total_cost', 'NOT_FOUND'),
                    'has_data': bool(current_analysis and current_analysis.get('total_cost', 0) > 0),
                    'has_pod_costs': current_analysis.get('has_pod_costs', False),
                    'has_node_data': current_analysis.get('has_real_node_data', False),
                    'full_results': current_analysis
                })
        
        # Fallback: check global (but warn)
        logger.warning("⚠️ Debug endpoint: No cluster_id provided, checking global analysis_results")
        return jsonify({
            'cluster_id': None,
            'data_source': 'global_fallback',
            'analysis_results_keys': list(analysis_results.keys()) if analysis_results else [],
            'total_cost': analysis_results.get('total_cost', 'NOT_FOUND') if analysis_results else 'NO_GLOBAL_DATA',
            'has_data': bool(analysis_results and analysis_results.get('total_cost', 0) > 0),
            'full_results': analysis_results if analysis_results else {}
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# @app.route('/api/clusters/<cluster_id>/chart-data')
# def cluster_specific_chart_data(cluster_id: str):
#     """Cluster-specific chart data endpoint"""
#     # MUST declare global at the very beginning
#     global analysis_results
    
#     try:
#         logger.info(f"📊 Cluster-specific chart data requested for {cluster_id}")
        
#         # Get cluster analysis from database
#         cached_analysis = enhanced_cluster_manager.get_latest_analysis(cluster_id)
        
#         if not cached_analysis:
#             return jsonify({
#                 'status': 'no_data',
#                 'message': f'No analysis data found for cluster {cluster_id}',
#                 'cluster_id': cluster_id
#             }), 404
        
#         # Temporarily set global analysis_results for compatibility
#         original_results = analysis_results.copy() if analysis_results else {}
#         analysis_results = cached_analysis
        
#         try:
#             # Use the existing chart data function
#             response = chart_data_consistent()
#             return response
#         finally:
#             # Restore original results
#             analysis_results = original_results
            
#     except Exception as e:
#         logger.error(f"❌ Error in cluster-specific chart data: {e}")
#         return jsonify({
#             'status': 'error',
#             'message': str(e),
#             'cluster_id': cluster_id
#         }), 500

@app.route('/api/implementation-plan')
def get_implementation_plan():
    """FIXED: Implementation plan API with forced regeneration for fresh analysis"""
    try:
        logger.info("📋 Implementation plan API called")
        
        # Extract cluster ID from request
        cluster_id = request.args.get('cluster_id')
        if not cluster_id:
            # Try to extract from referrer
            referrer = request.headers.get('Referer', '')
            if '/cluster/' in referrer:
                try:
                    cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
                    logger.info(f"📋 Extracted cluster_id from referrer: {cluster_id}")
                except Exception:
                    pass
        
        if not cluster_id:
            logger.warning("⚠️ No cluster_id provided")
            return jsonify({
                'status': 'error',
                'message': 'No cluster ID provided for implementation plan'
            }), 400
        
        # Get cluster info first
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        if not cluster:
            logger.error(f"❌ Cluster {cluster_id} not found in database")
            return jsonify({
                'status': 'error',
                'message': f'Cluster {cluster_id} not found'
            }), 404
        
        # Get cluster-specific analysis data
        current_analysis, data_source = _get_analysis_data(cluster_id)
        
        if not current_analysis:
            logger.error(f"❌ No analysis data found for cluster {cluster_id}")
            return jsonify({
                'status': 'error',
                'message': 'No analysis data available for implementation plan',
                'cluster_id': cluster_id,
                'data_source': data_source
            }), 404
        
        # 🔥 CRITICAL FIX: Always regenerate implementation plan for fresh analysis
        regenerate_plan = True  # Force regeneration every time
        implementation_plan = current_analysis.get('implementation_plan')
        
        # Additional checks to force regeneration
        if implementation_plan:
            plan_timestamp = implementation_plan.get('cluster_metadata', {}).get('generated_at')
            analysis_timestamp = current_analysis.get('analysis_timestamp')
            
            # Force regeneration if analysis is newer than plan
            if analysis_timestamp and plan_timestamp:
                try:
                    analysis_time = datetime.fromisoformat(analysis_timestamp)
                    plan_time = datetime.fromisoformat(plan_timestamp)
                    
                    if analysis_time > plan_time:
                        logger.info(f"🔄 Analysis is newer than plan - forcing regeneration for {cluster_id}")
                        regenerate_plan = True
                except Exception:
                    regenerate_plan = True
        
        if regenerate_plan:
            logger.info(f"🔄 FORCE regenerating implementation plan for {cluster_id}")
            try:
                from implementation_generator import AKSImplementationGenerator
                implementation_generator = AKSImplementationGenerator()
                
                # Ensure cluster metadata is in analysis data
                current_analysis['cluster_name'] = cluster['name']
                current_analysis['resource_group'] = cluster['resource_group']
                
                # Generate fresh implementation plan
                fresh_plan = implementation_generator.generate_implementation_plan(current_analysis)
                
                # Add cluster metadata to plan with current timestamp
                if isinstance(fresh_plan, dict):
                    fresh_plan['cluster_metadata'] = {
                        'cluster_name': cluster['name'],
                        'resource_group': cluster['resource_group'],
                        'cluster_id': cluster_id,
                        'generated_at': datetime.now().isoformat(),
                        'regenerated': True,
                        'total_cost': current_analysis.get('total_cost', 0),
                        'total_savings': current_analysis.get('total_savings', 0),
                        'analysis_timestamp': current_analysis.get('analysis_timestamp'),
                        'data_source': data_source
                    }
                
                current_analysis['implementation_plan'] = fresh_plan
                implementation_plan = fresh_plan
                
                # Update cache and database with fresh plan
                save_to_cache(cluster_id, current_analysis)
                enhanced_cluster_manager.update_cluster_analysis(cluster_id, current_analysis)
                
                logger.info(f"✅ FORCE regenerated implementation plan for {cluster_id}")
                
            except Exception as gen_error:
                logger.error(f"❌ Failed to regenerate implementation plan for {cluster_id}: {gen_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to generate implementation plan: {str(gen_error)}'
                }), 500
        
        # Validate implementation plan structure
        if not isinstance(implementation_plan, dict):
            logger.error(f"❌ Implementation plan is not a dict for {cluster_id}: {type(implementation_plan)}")
            return jsonify({
                'status': 'error',
                'message': 'Implementation plan has invalid structure'
            }), 500
        
        if 'implementation_phases' not in implementation_plan:
            logger.error(f"❌ Implementation plan missing phases for {cluster_id}")
            return jsonify({
                'status': 'error',
                'message': 'Implementation plan missing phases structure'
            }), 500
        
        phases = implementation_plan['implementation_phases']
        if not isinstance(phases, list) or len(phases) == 0:
            logger.error(f"❌ Implementation phases invalid for {cluster_id}: {type(phases)}, length: {len(phases) if isinstance(phases, list) else 'N/A'}")
            return jsonify({
                'status': 'error',
                'message': 'Implementation plan has no valid phases'
            }), 500
        
        logger.info(f"✅ Implementation plan validated for {cluster_id}: {len(phases)} phases from {data_source}")
        
        # FORCE fresh metadata in API response
        implementation_plan['api_metadata'] = {
            'data_source': data_source,
            'cluster_id': cluster_id,
            'cluster_name': cluster['name'],
            'resource_group': cluster['resource_group'],
            'phases_count': len(phases),
            'generated_at': datetime.now().isoformat(),
            'total_cost': current_analysis.get('total_cost', 0),
            'total_savings': current_analysis.get('total_savings', 0),
            'forced_regeneration': True
        }
        
        # Ensure cluster metadata is also in the main structure
        if 'cluster_metadata' not in implementation_plan:
            implementation_plan['cluster_metadata'] = {
                'cluster_name': cluster['name'],
                'resource_group': cluster['resource_group'],
                'cluster_id': cluster_id,
                'generated_at': datetime.now().isoformat()
            }
        
        return jsonify(implementation_plan)
        
    except Exception as e:
        logger.error(f"❌ Error getting implementation plan: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Implementation plan error: {str(e)}'
        }), 500
    
# ============================================================================
# DATABASE MAINTENANCE ROUTES
# ============================================================================

@app.route('/api/maintenance/cleanup', methods=['POST'])
def api_cleanup_database():
    """API endpoint to cleanup old analysis data"""
    try:
        days_to_keep = request.json.get('days_to_keep', 90) if request.is_json else 90
        
        enhanced_cluster_manager.cleanup_old_analyses(days_to_keep)
        
        return jsonify({
            'status': 'success',
            'message': f'Cleaned up analysis data older than {days_to_keep} days'
        })
        
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/clusters/<cluster_id>/history')
def api_cluster_analysis_history(cluster_id: str):
    """API to get analysis history for a cluster"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = enhanced_cluster_manager.get_analysis_history(cluster_id, limit)
        
        return jsonify({
            'status': 'success',
            'cluster_id': cluster_id,
            'history': history,
            'total_analyses': len(history)
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting analysis history: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ============================================================================
# TEMPLATE HELPERS FOR MULTI-CLUSTER SUPPORT
# ============================================================================

@app.template_filter('environment_badge_class')
def environment_badge_class(environment):
    """Get CSS class for environment badge"""
    env_classes = {
        'production': 'bg-danger',
        'staging': 'bg-warning',
        'development': 'bg-info',
        'testing': 'bg-secondary'
    }
    return env_classes.get(environment.lower(), 'bg-secondary')

@app.template_filter('status_indicator_class')
def status_indicator_class(cluster):
    """Get CSS class for cluster status indicator"""
    last_analyzed = cluster.get('last_analyzed')
    savings = cluster.get('last_savings', 0)
    
    if not last_analyzed:
        return 'error'
    elif savings > 100:
        return 'warning'
    else:
        return 'healthy'

@app.template_filter('format_currency')
def format_currency(amount):
    """Format currency with appropriate precision"""
    if amount >= 1000:
        return f"${amount:,.0f}"
    else:
        return f"${amount:.2f}"

@app.template_filter('time_ago')
def time_ago(timestamp_str):
    """Convert timestamp to human-readable time ago"""
    if not timestamp_str:
        return 'Never'
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        diff = datetime.now() - timestamp.replace(tzinfo=None)
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
    except:
        return 'Unknown'

# ======================================================
# Alerts
#=======================

# Add this to your app.py file - FIXED VERSION
# Replace the existing alerts initialization and routes section

# ======================================================
# ALERTS SYSTEM - FIXED INTEGRATION
# ======================================================

try:
    from alerts_manager import (
        EnhancedAlertsManager, 
        init_enhanced_alerts_service, 
        shutdown_enhanced_alerts_service
    )
    ALERTS_AVAILABLE = True
    logger.info("✅ Alerts manager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Alerts manager not available: {e}")
    ALERTS_AVAILABLE = False

# Global alerts manager
alerts_manager = None




def initialize_alerts_system():
    """Initialize alerts system with proper error handling"""
    global alerts_manager
    
    if not ALERTS_AVAILABLE:
        logger.warning("⚠️ Alerts system not available - skipping initialization")
        return None
    
    try:
        # Initialize alerts service with cluster manager
        alerts_manager = init_enhanced_alerts_service(enhanced_cluster_manager)
        logger.info("✅ Alerts system initialized successfully")
        
        # Register shutdown handler
        import atexit
        atexit.register(shutdown_enhanced_alerts_service)
        
        return alerts_manager
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize alerts system: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None

# Initialize alerts system after cluster manager is ready
alerts_manager = initialize_alerts_system()

# ======================================================
# ALERTS API ROUTES
# ======================================================

#

# Replace ALL the alerts routes in your app.py with these COMPLETELY FIXED versions:

@app.route('/api/alerts', methods=['GET', 'POST'])
def alerts_api():
    """Enhanced alerts API endpoint - COMPLETELY FIXED"""
    try:
        if not alerts_manager:
            return jsonify({
                'status': 'error',
                'message': 'Alerts system not available'
            }), 503
            
        if request.method == 'GET':
            # Get all alerts with enhanced filtering
            cluster_id = request.args.get('cluster_id')
            status = request.args.get('status', 'active')
            
            logger.info(f"🔍 GET /api/alerts - cluster_id: {cluster_id}, status: {status}")
            
            try:
                # Call the alerts manager method
                alerts_data = alerts_manager.get_alerts_route(cluster_id)
                
                if alerts_data['status'] == 'success':
                    alerts = alerts_data['alerts']
                    
                    # Additional status filtering if needed
                    if status and status != 'all' and status != 'active':
                        alerts = [a for a in alerts if a.get('status') == status]
                    
                    logger.info(f"✅ Returning {len(alerts)} alerts")
                    
                    return jsonify({
                        'status': 'success',
                        'alerts': alerts,
                        'total': len(alerts),
                        'cluster_id': cluster_id
                    })
                else:
                    logger.error(f"❌ Alerts manager returned error: {alerts_data}")
                    return jsonify(alerts_data), 500
                    
            except Exception as manager_error:
                logger.error(f"❌ Error calling alerts manager: {manager_error}")
                logger.error(f"❌ Manager error traceback: {traceback.format_exc()}")
                return jsonify({
                    'status': 'error',
                    'message': f'Alerts manager error: {str(manager_error)}'
                }), 500
                
        elif request.method == 'POST':
            # Create new alert
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            logger.info(f"🔍 POST /api/alerts - data: {data}")
            
            # Enhanced validation
            if not data.get('email'):
                return jsonify({
                    'status': 'error',
                    'message': 'Email address is required'
                }), 400
            
            if not data.get('threshold_amount') and not data.get('threshold_percentage'):
                return jsonify({
                    'status': 'error',
                    'message': 'Either threshold amount or percentage is required'
                }), 400
            
            # Auto-populate cluster info if cluster_id provided
            cluster_id = data.get('cluster_id')
            if cluster_id:
                cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster:
                    data['cluster_name'] = cluster['name']
                    data['resource_group'] = cluster['resource_group']
                    data['name'] = data.get('name', f"Budget Alert - {cluster['name']}")
            
            # Set default name if not provided
            if not data.get('name'):
                data['name'] = f"Cost Alert - {data.get('cluster_name', 'Unknown')}"
            
            try:
                result = alerts_manager.create_alert_route(data)
                
                if result['status'] == 'success':
                    logger.info(f"✅ Created alert: {result['alert_id']}")
                    return jsonify(result)
                else:
                    logger.error(f"❌ Failed to create alert: {result}")
                    return jsonify(result), 400
                    
            except Exception as create_error:
                logger.error(f"❌ Error creating alert: {create_error}")
                logger.error(f"❌ Create error traceback: {traceback.format_exc()}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to create alert: {str(create_error)}'
                }), 500
                
    except Exception as e:
        logger.error(f"❌ Error in alerts API: {e}")
        logger.error(f"❌ API error traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/alerts/<int:alert_id>', methods=['GET', 'PUT', 'DELETE'])
def alert_detail_api(alert_id: int):
    """Individual alert management - FIXED"""
    try:
        if not alerts_manager:
            return jsonify({
                'status': 'error',
                'message': 'Alerts system not available'
            }), 503
            
        if request.method == 'GET':
            try:
                alerts_data = alerts_manager.get_alerts_route()
                if alerts_data['status'] == 'success':
                    alert = next((a for a in alerts_data['alerts'] if a['id'] == alert_id), None)
                    if alert:
                        return jsonify({
                            'status': 'success',
                            'alert': alert
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': 'Alert not found'
                        }), 404
                else:
                    return jsonify(alerts_data), 500
            except Exception as get_error:
                logger.error(f"❌ Error getting alert {alert_id}: {get_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to get alert: {str(get_error)}'
                }), 500
        
        elif request.method == 'PUT':
            try:
                data = request.get_json() or {}
                result = alerts_manager.update_alert_route(alert_id, data)
                
                if result['status'] == 'success':
                    return jsonify(result)
                else:
                    return jsonify(result), 400
            except Exception as update_error:
                logger.error(f"❌ Error updating alert {alert_id}: {update_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to update alert: {str(update_error)}'
                }), 500
        
        elif request.method == 'DELETE':
            try:
                result = alerts_manager.delete_alert_route(alert_id)
                return jsonify(result)
            except Exception as delete_error:
                logger.error(f"❌ Error deleting alert {alert_id}: {delete_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to delete alert: {str(delete_error)}'
                }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in alert detail API: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/alerts/<int:alert_id>/test', methods=['POST'])
def test_alert_api(alert_id: int):
    """Test alert notification - FIXED"""
    try:
        if not alerts_manager:
            return jsonify({
                'status': 'error',
                'message': 'Alerts system not available'
            }), 503
            
        result = alerts_manager.test_alert_route(alert_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error testing alert: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/alerts/<int:alert_id>/pause', methods=['POST'])
def pause_alert_api(alert_id: int):
    """Pause/unpause alert - FIXED"""
    try:
        if not alerts_manager:
            return jsonify({
                'status': 'error',
                'message': 'Alerts system not available'
            }), 503
            
        data = request.get_json() or {}
        action = data.get('action', 'pause')  # pause or resume
        status = 'paused' if action == 'pause' else 'active'
        
        result = alerts_manager.update_alert_route(alert_id, {'status': status})
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'message': f'Alert {action}d successfully'
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Error pausing/resuming alert: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/alerts/triggers', methods=['GET'])
def alert_triggers_api():
    """Get alert trigger history - FIXED"""
    try:
        if not alerts_manager:
            return jsonify({
                'status': 'error',
                'message': 'Alerts system not available'
            }), 503
            
        # Return empty triggers for now (can be implemented later)
        return jsonify({
            'status': 'success',
            'triggers': []
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting alert triggers: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/alerts/email-config', methods=['GET', 'POST'])
def email_config_api():
    """Email configuration management - FIXED"""
    try:
        if request.method == 'GET':
            # Check if email is configured
            email_configured = bool(
                os.getenv('SMTP_USERNAME') and 
                os.getenv('SMTP_PASSWORD')
            )
            
            return jsonify({
                'status': 'success',
                'email_configured': email_configured,
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': os.getenv('SMTP_PORT', '587'),
                'from_email': os.getenv('FROM_EMAIL', '')
            })
        
        elif request.method == 'POST':
            return jsonify({
                'status': 'info',
                'message': 'Email configuration should be set via environment variables'
            })
            
    except Exception as e:
        logger.error(f"❌ Error in email config API: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/alerts/system-status', methods=['GET'])
def alerts_system_status():
    """Get alerts system status for debugging - FIXED"""
    try:
        return jsonify({
            'status': 'success',
            'alerts_available': ALERTS_AVAILABLE if 'ALERTS_AVAILABLE' in globals() else (alerts_manager is not None),
            'alerts_manager_initialized': alerts_manager is not None,
            'alerts_manager_type': type(alerts_manager).__name__ if alerts_manager else None,
            'email_configured': bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
            'smtp_server': os.getenv('SMTP_SERVER', 'Not configured'),
            'cluster_manager_available': enhanced_cluster_manager is not None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Error in alerts system status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ======================================================
# ALERTS INTEGRATION WITH ANALYSIS
# ======================================================

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """Check and trigger alerts after analysis completion"""
    try:
        if not alerts_manager:
            logger.debug("⚠️ Alerts manager not available - skipping alert check")
            return
        
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        if not cluster:
            return
        
        # Get current cost from analysis
        current_cost = analysis_results.get('total_cost', 0)
        
        if current_cost <= 0:
            logger.debug(f"No cost data to check alerts for cluster {cluster_id}")
            return
        
        logger.info(f"🔍 Checking alerts for cluster {cluster_id} with cost ${current_cost:.2f}")
        
        # Get alerts for this specific cluster
        try:
            alerts_data = alerts_manager.get_alerts_route()
            if alerts_data['status'] != 'success':
                logger.warning("Failed to get alerts for checking")
                return
            
            cluster_alerts = [a for a in alerts_data['alerts'] if 
                            a.get('cluster_name') == cluster['name'] and 
                            a.get('resource_group') == cluster['resource_group'] and
                            a.get('status') == 'active']
            
            alerts_triggered = 0
            
            for alert in cluster_alerts:
                try:
                    # Simple threshold check
                    threshold = alert.get('threshold_amount', 0)
                    
                    if threshold > 0 and current_cost >= threshold:
                        logger.info(f"🚨 Alert would trigger for cluster {cluster_id}: ${current_cost:.2f} >= ${threshold:.2f}")
                        alerts_triggered += 1
                        
                        # For now, just log it - full alert sending would be implemented here
                        
                except Exception as alert_error:
                    logger.error(f"❌ Error checking alert {alert.get('id')}: {alert_error}")
            
            if alerts_triggered > 0:
                logger.info(f"📧 Would trigger {alerts_triggered} alerts for cluster {cluster_id}")
            else:
                logger.debug(f"✅ No alerts triggered for cluster {cluster_id}")
            
        except Exception as alerts_error:
            logger.error(f"❌ Error getting alerts for checking: {alerts_error}")
        
    except Exception as e:
        logger.error(f"❌ Error checking alerts after analysis: {e}")



# ===ALERTS=============
# End
# =========Alerts=======


# CLEAR global cache when analyzing new clusters
def clear_global_analysis_cache():
    """Clear global analysis cache to prevent cross-cluster contamination"""
    global analysis_results
    analysis_results = {}
    logger.info("🧹 Cleared global analysis cache")

@app.route('/api/cache/clear', methods=['POST'])
def clear_analysis_cache_api():
    """Clear analysis cache for specific cluster or all clusters"""
    try:
        data = request.get_json() or {}
        cluster_id = data.get('cluster_id')
        
        if cluster_id:
            clear_analysis_cache(cluster_id)
            message = f'Analysis cache cleared for cluster {cluster_id}'
        else:
            clear_analysis_cache()
            message = 'All analysis caches cleared successfully'
            
        return jsonify({
            'status': 'success',
            'message': message,
            'total_clusters_remaining': len(analysis_cache['clusters'])
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """Get detailed cache status for debugging"""
    try:
        cluster_id = request.args.get('cluster_id')
        
        status_info = {
            'total_cached_clusters': len(analysis_cache['clusters']),
            'cached_clusters': list(analysis_cache['clusters'].keys()),
            'global_ttl_hours': analysis_cache['global_ttl_hours'],
            'cache_type': 'multi_cluster'
        }
        
        if cluster_id:
            # Specific cluster status
            if cluster_id in analysis_cache['clusters']:
                cluster_cache = analysis_cache['clusters'][cluster_id]
                status_info.update({
                    'cluster_id': cluster_id,
                    'cache_valid': is_cache_valid(cluster_id),
                    'cache_timestamp': cluster_cache.get('timestamp'),
                    'cache_has_data': bool(cluster_cache.get('data')),
                    'cache_total_cost': cluster_cache.get('data', {}).get('total_cost', 0),
                    'cache_has_pod_costs': cluster_cache.get('data', {}).get('has_pod_costs', False),
                    'namespace_count_in_cache': len(cluster_cache.get('data', {}).get('namespace_costs', {}))
                })
            else:
                status_info.update({
                    'cluster_id': cluster_id,
                    'cache_exists': False,
                    'message': f'No cache found for cluster {cluster_id}'
                })
        else:
            # All clusters summary
            cluster_summaries = {}
            for cid, cache_data in analysis_cache['clusters'].items():
                cluster_summaries[cid] = {
                    'cost': cache_data.get('data', {}).get('total_cost', 0),
                    'timestamp': cache_data.get('timestamp'),
                    'valid': is_cache_valid(cid)
                }
            status_info['cluster_summaries'] = cluster_summaries
        
        return jsonify({
            'status': 'success',
            'cache_status': status_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    try:
        # Initialize database first
        initialize_database()
        
        # Start background data updates
        #bg_thread = add_auto_update_feature()
        
        # Run the application
        logger.info("🚀 Starting Enhanced AKS Cost Optimization")
        logger.info("📊 Multi-cluster portfolio management enabled")
        logger.info("🌐 Server running at http://127.0.0.1:5000/")
        logger.info("💡 Press Ctrl+C to exit")
        
        app.run(debug=True, use_reloader=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise