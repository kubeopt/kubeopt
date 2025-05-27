def get_azure_advisor_recommendations(resource_group, cluster_name):
    """Get Azure Advisor cost recommendations for the AKS cluster"""
    logger.info(f"Getting Azure Advisor recommendations for cluster {cluster_name}")
    
    try:
        # First get the resource ID of the AKS cluster
        get_id_command = f"az aks show --resource-group {resource_group} --name {cluster_name} --query id -o tsv"
        id_result = subprocess.run(get_id_command, shell=True, check=True, capture_output=True, text=True)
        cluster_id = id_result.stdout.strip()
        
        # Query Azure Advisor for cost recommendations related to this cluster
        advisor_command = f"az advisor recommendation list --filter \"Category eq 'Cost' and ResourceIdString contains '{cluster_id}'\" -o json"
        advisor_result = subprocess.run(advisor_command, shell=True, check=True, capture_output=True, text=True)
        advisor_data = json.loads(advisor_result.stdout)
        
        # Process the recommendations
        processed_recommendations = []
        
        for rec in advisor_data:
            processed_recommendations.append({
                'title': rec.get('shortDescription', {}).get('solution', 'Azure Advisor Recommendation'),
                'description': rec.get('extendedProperties', {}).get('description', ''),
                'impact': rec.get('extendedProperties', {}).get('savingsAmount', '0'),
                'category': rec.get('category', 'Cost'),
                'resource': rec.get('resourceMetadata', {}).get('resourceName', ''),
                'problem': rec.get('shortDescription', {}).get('problem', ''),
                'id': rec.get('name', '')
            })
        
        logger.info(f"Retrieved {len(processed_recommendations)} Azure Advisor recommendations")
        return processed_recommendations
    
    except Exception as e:
        logger.error(f"Error getting Azure Advisor recommendations: {e}")
        return []
    

    def analyze_reserved_instance_potential(cost_data, node_metrics):
    """Analyze if reserved instances would be beneficial based on usage patterns"""
    stable_workload_percentage = 0
    total_nodes = len(node_metrics)
    
    # Calculate how stable the workload is
    for node in node_metrics:
        if 'cpu_pattern' in node and len(node['cpu_pattern']) > 0:
            values = [dp['value'] for dp in node['cpu_pattern']]
            stddev = np.std(values) if values else 0
            mean = np.mean(values) if values else 0
            
            # If coefficient of variation is low, workload is stable
            if mean > 0 and (stddev / mean) < 0.2:
                stable_workload_percentage += (1 / total_nodes) * 100
    
    # If more than 60% of workload is stable, recommend RI
    if stable_workload_percentage > 60:
        return {
            'recommended': True,
            'stable_percentage': stable_workload_percentage,
            'potential_savings': cost_data['node_cost'] * 0.4  # 40% typical RI savings
        }
    else:
        return {
            'recommended': False,
            'stable_percentage': stable_workload_percentage
        }
    


 def process_aks_cost_data(cost_data_json):
#     """Process raw AKS cost data from Azure API response"""
#     logger.info("Processing AKS cost data from API response")
    
#     try:
#         # Initialize dataframe structure
#         cost_records = []
        
#         # Extract columns and rows
#         columns = [col["name"] for col in cost_data_json["properties"]["columns"]]
#         rows = cost_data_json["properties"]["rows"]
        
#         # Create mapping for critical fields
#         field_mapping = {
#             "PreTaxCost": columns.index("PreTaxCost"),
#             "ResourceType": columns.index("ResourceType"),
#             "ResourceGroupName": columns.index("ResourceGroupName"),
#             "ServiceName": columns.index("ServiceName")
#         }
        
#         # Process each row
#         for row in rows:
#             record = {
#                 "Cost": float(row[field_mapping["PreTaxCost"]]),
#                 "ResourceType": row[field_mapping["ResourceType"]],
#                 "ResourceGroup": row[field_mapping["ResourceGroupName"]],
#                 "Service": row[field_mapping["ServiceName"]]
#             }
#             cost_records.append(record)
            
#         return pd.DataFrame(cost_records)
    
#     except Exception as e:
#         logger.error(f"Error processing cost data: {str(e)}")
#         raise RuntimeError("Failed to process cost data from API response")
    
################ adding new logic to get the metrics from azure monitor ###################

# def get_aks_metrics_from_monitor(resource_group, cluster_name, start_date, end_date):
#     """Get AKS metrics from Azure Monitor for a specific date range to align with cost data"""
#     logger.info(f"Fetching AKS metrics from Azure Monitor for {cluster_name} from {start_date} to {end_date}")
    
#     try:
#         # Format dates for API calls
#         start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
#         end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
#         # Get subscription ID
#         sub_cmd = "az account show --query id -o tsv"
#         sub_result = subprocess.run(sub_cmd, shell=True, check=True, capture_output=True, text=True)
#         subscription_id = sub_result.stdout.strip()
        
#         # Get AKS resource ID
#         aks_id_cmd = f"az aks show -g {resource_group} -n {cluster_name} --query id -o tsv"
#         aks_id_result = subprocess.run(aks_id_cmd, shell=True, check=True, capture_output=True, text=True)
#         aks_resource_id = aks_id_result.stdout.strip()
        
#         # Get metrics using Azure Monitor API
#         metrics = {}
        
#         # Get node CPU usage
#         node_cpu_cmd = f"""
#         az monitor metrics list \\
#           --resource {aks_resource_id} \\
#           --metric "node_cpu_usage_percentage" \\
#           --interval PT1H \\
#           --aggregation Maximum \\
#           --start-time {start_date_str} \\
#           --end-time {end_date_str} \\
#           -o json
#         """
        
#         cpu_result = subprocess.run(node_cpu_cmd, shell=True, check=True, capture_output=True, text=True)
#         cpu_data = json.loads(cpu_result.stdout)
#         metrics['node_cpu'] = process_azure_monitor_metric(cpu_data)
        
#         # Get node memory usage
#         node_memory_cmd = f"""
#         az monitor metrics list \\
#           --resource {aks_resource_id} \\
#           --metric "node_memory_working_set_percentage" \\
#           --interval PT1H \\
#           --aggregation Maximum \\
#           --start-time {start_date_str} \\
#           --end-time {end_date_str} \\
#           -o json
#         """
        
#         memory_result = subprocess.run(node_memory_cmd, shell=True, check=True, capture_output=True, text=True)
#         memory_data = json.loads(memory_result.stdout)
#         metrics['node_memory'] = process_azure_monitor_metric(memory_data)
        
#         # Get container CPU usage by controller (deployment) name
#         container_cpu_cmd = f"""
#         az monitor metrics list \\
#           --resource {aks_resource_id} \\
#           --metric "container_cpu_usage_percentage" \\
#           --interval PT1H \\
#           --aggregation Average \\
#           --start-time {start_date_str} \\
#           --end-time {end_date_str} \\
#           --dimension "controllerName" \\
#           -o json
#         """
        
#         container_cpu_result = subprocess.run(container_cpu_cmd, shell=True, check=True, capture_output=True, text=True)
#         container_cpu_data = json.loads(container_cpu_result.stdout)
#         metrics['container_cpu'] = process_azure_monitor_metric(container_cpu_data, dimension='controllerName')
        
#         # Get container memory usage by controller (deployment) name
#         container_memory_cmd = f"""
#         az monitor metrics list \\
#           --resource {aks_resource_id} \\
#           --metric "container_memory_working_set_percentage" \\
#           --interval PT1H \\
#           --aggregation Average \\
#           --start-time {start_date_str} \\
#           --end-time {end_date_str} \\
#           --dimension "controllerName" \\
#           -o json
#         """
        
#         container_memory_result = subprocess.run(container_memory_cmd, shell=True, check=True, capture_output=True, text=True)
#         container_memory_data = json.loads(container_memory_result.stdout)
#         metrics['container_memory'] = process_azure_monitor_metric(container_memory_data, dimension='controllerName')
        
#         # Process metrics into a unified format
#         processed_metrics = process_monitor_metrics(metrics, resource_group, cluster_name)
        
#         # Add date range info to the metrics
#         processed_metrics['metadata']['start_date'] = start_date_str
#         processed_metrics['metadata']['end_date'] = end_date_str
#         processed_metrics['metadata']['data_source'] = 'Azure Monitor'
        
#         return processed_metrics
        
#     except Exception as e:
#         logger.error(f"Error fetching metrics from Azure Monitor: {e}")
#         # Fall back to sample data
#         sample_metrics = create_sample_metrics_data()
#         sample_metrics['metadata']['data_source'] = 'Sample Data (Azure Monitor fetch failed)'
#         return sample_metrics

#### New implementation begins here