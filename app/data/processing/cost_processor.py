"""
Cost Data Processing for AKS Cost Optimization
"""

import json
import subprocess
import time
import os
import pandas as pd
from datetime import datetime
from config import logger
from utils import validate_cost_data

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

def get_aks_specific_cost_data(resource_group, cluster_name, start_date, end_date, cluster_id=None):
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