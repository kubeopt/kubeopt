import json
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

def import_metrics_from_json(json_file_path):
    """Import metrics from a JSON file exported from a monitoring tool"""
    logger.info(f"Importing metrics from JSON file: {json_file_path}")
    
    try:
        with open(json_file_path, 'r') as f:
            metrics_data = json.load(f)
        
        logger.info("Successfully loaded metrics JSON file")
        return metrics_data
    
    except Exception as e:
        logger.error(f"Error importing metrics from JSON: {e}")
        raise RuntimeError(f"Failed to import metrics: {str(e)}")

def process_node_metrics(metrics_data):
    """Extract and process node metrics from the imported data"""
    logger.info("Processing node metrics")
    
    node_metrics = []
    
    # Extract node metrics
    if 'nodes' in metrics_data:
        for node in metrics_data['nodes']:
            node_metric = {
                'node': node.get('name', 'unknown'),
                'vm_size': node.get('vm_size', 'unknown'),
                'cpu_cores': node.get('cpu_cores', 0),
                'memory_gb': node.get('memory_gb', 0),
                'cpu_usage_pct': node.get('cpu_usage_pct', 0),
                'memory_usage_pct': node.get('memory_usage_pct', 0),
                'cpu_request_pct': node.get('cpu_request_pct', 0),
                'memory_request_pct': node.get('memory_request_pct', 0),
                'pod_count': node.get('pod_count', 0)
            }
            
            # Calculate gaps between requested and actual usage
            node_metric['cpu_gap'] = node_metric['cpu_request_pct'] - node_metric['cpu_usage_pct']
            node_metric['memory_gap'] = node_metric['memory_request_pct'] - node_metric['memory_usage_pct']
            
            node_metrics.append(node_metric)
    
    logger.info(f"Processed metrics for {len(node_metrics)} nodes")
    return node_metrics

def analyze_hpa_potential(metrics_data):
    """Analyze deployments to determine HPA optimization potential"""
    logger.info("Analyzing deployments for HPA optimization potential")
    
    hpa_analysis = {
        'deployments': [],
        'time_points': [],
        'cpu_replicas': {},
        'memory_replicas': {},
        'overall_hpa_reduction': 0,
        'overall_cpu_memory_ratio': 0
    }
    
    if 'deployments' not in metrics_data:
        logger.warning("No deployment data found for HPA analysis")
        return hpa_analysis
    
    deployments = metrics_data['deployments']
    
    # Collect time points from the first deployment (assuming all use the same time points)
    if deployments and 'daily_usage_pattern' in deployments[0]:
        hpa_analysis['time_points'] = [p['time'] for p in deployments[0]['daily_usage_pattern']]
    
    total_cpu_to_memory_ratio = 0
    total_reduction_pct = 0
    
    # Analyze each deployment
    for deployment in deployments:
        name = deployment.get('name', 'unknown')
        cpu_request = parse_resource_value(deployment.get('cpu_request', '0'))  # in millicores
        memory_request = parse_resource_value(deployment.get('memory_request', '0'))  # in Mi
        cpu_usage_avg = deployment.get('cpu_usage_avg', 0)  # in millicores
        memory_usage_avg = parse_resource_value(deployment.get('memory_usage_avg', '0'))  # in Mi
        replicas = deployment.get('replicas', 1)
        
        # Calculate optimal replicas based on CPU vs Memory
        daily_pattern = deployment.get('daily_usage_pattern', [])
        cpu_replicas = {}
        memory_replicas = {}
        
        for point in daily_pattern:
            time_label = point.get('time', '')
            cpu_usage = point.get('cpu_usage', 0)
            memory_usage = parse_resource_value(point.get('memory_usage', '0'))
            
            # Calculate how many replicas we'd need based on CPU
            # Assuming 80% target utilization
            cpu_needed = max(1, int(cpu_usage / (cpu_request * 0.8)))
            
            # Calculate how many replicas we'd need based on Memory
            # Assuming 80% target utilization
            memory_needed = max(1, int(memory_usage / (memory_request * 0.8)))
            
            cpu_replicas[time_label] = cpu_needed
            memory_replicas[time_label] = memory_needed
        
        # Calculate normalized ratios of CPU to memory utilization
        if memory_usage_avg > 0 and cpu_usage_avg > 0:
            # Normalize to make them comparable
            normalized_cpu = cpu_usage_avg / 1000  # Convert millicores to cores
            normalized_memory = memory_usage_avg / 1024  # Convert Mi to Gi
            
            cpu_memory_ratio = normalized_cpu / normalized_memory if normalized_memory > 0 else 1
            total_cpu_to_memory_ratio += cpu_memory_ratio
            
            # Calculate potential reduction for this deployment
            if cpu_memory_ratio > 1.5:
                # CPU is significantly higher - good HPA potential
                reduction_pct = min(75, cpu_memory_ratio * 20)  # Cap at 75%
            elif cpu_memory_ratio > 1.2:
                # CPU is moderately higher
                reduction_pct = min(50, cpu_memory_ratio * 15)
            elif cpu_memory_ratio > 1.0:
                # CPU is slightly higher
                reduction_pct = min(30, cpu_memory_ratio * 10)
            else:
                # Memory is higher, limited benefit
                reduction_pct = max(5, cpu_memory_ratio * 5)
            
            total_reduction_pct += reduction_pct
        else:
            cpu_memory_ratio = 1
            reduction_pct = 0
        
        # Add deployment analysis
        hpa_analysis['deployments'].append({
            'name': name,
            'namespace': deployment.get('namespace', 'default'),
            'replicas': replicas,
            'cpu_request': deployment.get('cpu_request', ''),
            'memory_request': deployment.get('memory_request', ''),
            'cpu_usage_avg': cpu_usage_avg,
            'memory_usage_avg': deployment.get('memory_usage_avg', ''),
            'cpu_memory_ratio': cpu_memory_ratio,
            'reduction_potential': reduction_pct
        })
        
        # Add to overall CPU/Memory replica counts
        for time_label, replicas in cpu_replicas.items():
            if time_label not in hpa_analysis['cpu_replicas']:
                hpa_analysis['cpu_replicas'][time_label] = 0
            hpa_analysis['cpu_replicas'][time_label] += replicas
        
        for time_label, replicas in memory_replicas.items():
            if time_label not in hpa_analysis['memory_replicas']:
                hpa_analysis['memory_replicas'][time_label] = 0
            hpa_analysis['memory_replicas'][time_label] += replicas
    
    # Calculate overall metrics
    if deployments:
        hpa_analysis['overall_cpu_memory_ratio'] = total_cpu_to_memory_ratio / len(deployments)
        hpa_analysis['overall_hpa_reduction'] = total_reduction_pct / len(deployments)
    
    # Convert to lists for easier charting
    hpa_analysis['cpu_replicas_list'] = [hpa_analysis['cpu_replicas'].get(t, 0) for t in hpa_analysis['time_points']]
    hpa_analysis['memory_replicas_list'] = [hpa_analysis['memory_replicas'].get(t, 0) for t in hpa_analysis['time_points']]
    
    logger.info(f"HPA analysis complete. Overall reduction potential: {hpa_analysis['overall_hpa_reduction']:.1f}%")
    return hpa_analysis

def analyze_storage_optimization(metrics_data):
    """Analyze storage data to identify optimization opportunities"""
    logger.info("Analyzing storage for optimization opportunities")
    
    storage_analysis = {
        'premium_volumes': 0,
        'standard_volumes': 0,
        'unused_volumes': 0,
        'premium_cost': 0,
        'standard_cost': 0,
        'total_cost': 0,
        'savings_potential': 0
    }
    
    if 'storage' not in metrics_data:
        logger.warning("No storage data found for analysis")
        return storage_analysis
    
    storage = metrics_data['storage']
    
    # Extract storage metrics
    storage_analysis['premium_volumes'] = storage.get('premium_volumes', 0)
    storage_analysis['standard_volumes'] = storage.get('standard_volumes', 0)
    storage_analysis['unused_volumes'] = storage.get('unused_volumes', 0)
    storage_analysis['premium_cost'] = storage.get('premium_cost', 0)
    storage_analysis['standard_cost'] = storage.get('standard_cost', 0)
    storage_analysis['total_cost'] = storage_analysis['premium_cost'] + storage_analysis['standard_cost']
    
    # Calculate potential savings
    # 1. Savings from removing unused volumes
    unused_cost_ratio = storage_analysis['unused_volumes'] / (storage_analysis['premium_volumes'] + storage_analysis['standard_volumes'])
    unused_savings = storage_analysis['total_cost'] * unused_cost_ratio
    
    # 2. Savings from downgrading premium to standard (assume 40% can be downgraded with 65% cost reduction)
    premium_conversion_rate = 0.4
    premium_to_standard_savings_rate = 0.65
    premium_downgrade_savings = storage_analysis['premium_cost'] * premium_conversion_rate * premium_to_standard_savings_rate
    
    storage_analysis['savings_potential'] = unused_savings + premium_downgrade_savings
    
    logger.info(f"Storage analysis complete. Potential savings: ${storage_analysis['savings_potential']:.2f}")
    return storage_analysis

def calculate_savings(metrics_data, node_cost, storage_cost):
    """Calculate overall savings opportunities based on metrics analysis"""
    logger.info("Calculating overall savings opportunities")
    
    node_metrics = process_node_metrics(metrics_data)
    hpa_analysis = analyze_hpa_potential(metrics_data)
    storage_analysis = analyze_storage_optimization(metrics_data)
    
    # Calculate right-sizing savings
    right_sizing_result = calculate_right_sizing_savings(node_metrics, node_cost)
    right_sizing_savings = right_sizing_result.get('right_sizing_savings', 0)
    cpu_gap = right_sizing_result.get('cpu_gap', 0)
    memory_gap = right_sizing_result.get('memory_gap', 0)
    
    # Calculate HPA savings
    hpa_reduction = hpa_analysis['overall_hpa_reduction']
    hpa_savings = node_cost * (hpa_reduction / 100) * 0.7  # 70% applicability factor
    
    # Storage savings
    storage_savings = storage_analysis['savings_potential']
    
    # Total savings
    total_savings = hpa_savings + right_sizing_savings + storage_savings
    
    # Return the results
    return {
        'hpa_reduction': hpa_reduction,
        'hpa_savings': hpa_savings,
        'right_sizing_savings': right_sizing_savings,
        'storage_savings': storage_savings,
        'total_savings': total_savings,
        'cpu_gap': cpu_gap,
        'memory_gap': memory_gap,
        'cpu_memory_ratio': hpa_analysis['overall_cpu_memory_ratio'],
        'node_metrics': node_metrics,
        'hpa_analysis': hpa_analysis,
        'storage_analysis': storage_analysis
    }

def calculate_right_sizing_savings(node_metrics, node_cost):
    """Calculate potential savings from right-sizing resources based on actual metrics"""
    
    total_cpu_gap = 0
    total_memory_gap = 0
    valid_nodes = 0
    
    for node in node_metrics:
        if 'cpu_gap' in node and 'memory_gap' in node:
            total_cpu_gap += max(0, node['cpu_gap'])
            total_memory_gap += max(0, node['memory_gap'])
            valid_nodes += 1
    
    if valid_nodes == 0:
        return {
            'cpu_gap': 45.0,  # Default fallback
            'memory_gap': 22.0,  # Default fallback
            'right_sizing_savings': node_cost * 0.15  # Default fallback
        }
    
    avg_cpu_gap = total_cpu_gap / valid_nodes
    avg_memory_gap = total_memory_gap / valid_nodes
    
    # Calculate savings potential based on gaps
    # Assume we can reclaim 60% of the identified gap
    # (leaving some buffer for performance and burst capacity)
    reclamation_rate = 0.6
    
    # Weighted average of CPU and memory gaps (CPU typically has higher weight in node costs)
    weighted_gap = (avg_cpu_gap * 0.7) + (avg_memory_gap * 0.3)
    
    # Calculate savings as a percentage of node costs
    savings_pct = weighted_gap * reclamation_rate / 100
    right_sizing_savings = node_cost * savings_pct
    
    return {
        'cpu_gap': avg_cpu_gap,
        'memory_gap': avg_memory_gap,
        'right_sizing_savings': right_sizing_savings
    }

def generate_dynamic_hpa_comparison(hpa_analysis):
    """Generate HPA comparison data for charting based on analysis"""
    
    return {
        'timePoints': hpa_analysis['time_points'],
        'cpuReplicas': hpa_analysis['cpu_replicas_list'],
        'memoryReplicas': hpa_analysis['memory_replicas_list']
    }

def generate_implementation_recommendations(analysis_results):
    """Generate implementation recommendations based on analysis results"""
    recommendations = []
    
    # Get metrics for recommendations
    hpa_reduction = analysis_results.get('hpa_reduction', 0)
    hpa_savings = analysis_results.get('hpa_savings', 0)
    cpu_gap = analysis_results.get('cpu_gap', 0)
    memory_gap = analysis_results.get('memory_gap', 0)
    right_sizing_savings = analysis_results.get('right_sizing_savings', 0)
    storage_savings = analysis_results.get('storage_savings', 0)
    total_savings = analysis_results.get('total_savings', 0)
    
    # Helper function to determine priority
    def determine_priority(savings, total_savings):
        if total_savings == 0:
            return 'Medium'
        
        savings_pct = (savings / total_savings) * 100
        if savings_pct > 40:
            return 'High'
        elif savings_pct > 20:
            return 'Medium'
        else:
            return 'Low'
    
    # 1. Memory-based HPA recommendation
    if hpa_reduction > 15:
        priority = determine_priority(hpa_savings, total_savings)
        target_utilization = max(60, min(80, 100 - hpa_reduction/2))
        
        # Get most promising deployments from analysis
        hpa_analysis = analysis_results.get('hpa_analysis', {})
        promising_deployments = []
        
        for deployment in hpa_analysis.get('deployments', []):
            if deployment.get('reduction_potential', 0) > 20:
                promising_deployments.append(deployment['name'])
        
        deployment_text = ', '.join(promising_deployments[:3])
        if len(promising_deployments) > 3:
            deployment_text += f" and {len(promising_deployments) - 3} more"
        
        if not promising_deployments:
            deployment_text = "your deployments"
        
        recommendations.append({
            'title': 'Implement Memory-Based HPA',
            'benefit': f"Reduce replica count by {hpa_reduction:.1f}% and save ${hpa_savings:.2f}/month",
            'priority': priority,
            'implementation': f"""
                # Apply memory-based HPA for {deployment_text}
                apiVersion: autoscaling/v2
                kind: HorizontalPodAutoscaler
                metadata:
                  name: deployment-memory-hpa
                spec:
                  scaleTargetRef:
                    apiVersion: apps/v1
                    kind: Deployment
                    name: YOUR_DEPLOYMENT_NAME  # Replace with actual deployment name
                  minReplicas: 2  # Adjust based on your minimum requirements
                  maxReplicas: 10
                  metrics:
                  - type: Resource
                    resource:
                      name: memory
                      target:
                        type: Utilization
                        averageUtilization: {int(target_utilization)}
                """
        })
    
    # 2. Right-sizing recommendation
    if cpu_gap > 20 or memory_gap > 15:
        priority = determine_priority(right_sizing_savings, total_savings)
        
        # Calculate dynamic reduction percentages
        cpu_reduction_pct = min(70, max(30, cpu_gap * 0.6))  # Between 30-70%
        memory_reduction_pct = min(60, max(20, memory_gap * 0.5))  # Between 20-60%
        
        recommendations.append({
            'title': 'Right-Size Resource Requests',
            'benefit': f"Close the {cpu_gap:.1f}% CPU gap and {memory_gap:.1f}% memory gap to save ${right_sizing_savings:.2f}/month",
            'priority': priority,
            'implementation': f"""
                # Update deployment resources
                # Example for a typical deployment:
                resources:
                  requests:
                    # Current over-provisioned requests
                    # cpu: 500m
                    # memory: 1Gi
                    
                    # Right-sized based on actual usage (with safety buffer)
                    cpu: {int(500 * (1 - cpu_reduction_pct/100))}m  # {cpu_reduction_pct:.0f}% reduction
                    memory: {int(1024 * (1 - memory_reduction_pct/100))}Mi  # {memory_reduction_pct:.0f}% reduction
                  limits:
                    cpu: 1000m  # Maintain existing limits or adjust as needed
                    memory: 1.5Gi
                """
        })
    
    # 3. Storage optimization recommendation
    if storage_savings > 10:  # Only if savings are significant
        storage_analysis = analysis_results.get('storage_analysis', {})
        priority = determine_priority(storage_savings, total_savings)
        
        unused_volumes = storage_analysis.get('unused_volumes', 0)
        premium_volumes = storage_analysis.get('premium_volumes', 0)
        
        recommendations.append({
            'title': 'Optimize Storage Usage',
            'benefit': f"Save ${storage_savings:.2f}/month by optimizing storage",
            'priority': priority,
            'implementation': f"""
                # 1. Clean up {unused_volumes} unused volumes:
                kubectl get pv | grep Released  # Find volumes in Released state
                
                # 2. Downgrade applicable Premium disks to Standard:
                # First, identify premium disks that don't need premium performance:
                kubectl get pv -o custom-columns=NAME:.metadata.name,STORAGECLASS:.spec.storageClassName,CLAIM:.spec.claimRef.name
                
                # 3. For non-critical services, modify default storage class:
                apiVersion: storage.k8s.io/v1
                kind: StorageClass
                metadata:
                  name: managed-premium-retain
                provisioner: kubernetes.io/azure-disk
                parameters:
                  storageaccounttype: StandardSSD_LRS  # Change from Premium_LRS
                  kind: Managed
                reclaimPolicy: Retain
                """
        })
    
    # 4. Node pool optimization (if relevant)
    node_metrics = analysis_results.get('node_metrics', [])
    if len(node_metrics) >= 5:
        # Check for consistent underutilization
        avg_cpu_usage = sum(node.get('cpu_usage_pct', 0) for node in node_metrics) / len(node_metrics)
        avg_pod_count = sum(node.get('pod_count', 0) for node in node_metrics) / len(node_metrics)
        
        if avg_cpu_usage < 35 and avg_pod_count < 12:
            recommendations.append({
                'title': 'Optimize Node Count',
                'benefit': "Reduce the number of nodes in your cluster to save on unnecessary infrastructure costs",
                'priority': 'Medium',
                'implementation': """
                    # Reduce the node count in your cluster:
                    az aks scale --resource-group YOUR_RESOURCE_GROUP --name YOUR_CLUSTER_NAME --node-count 4
                    
                    # Or for a specific node pool:
                    az aks nodepool scale --resource-group YOUR_RESOURCE_GROUP --cluster-name YOUR_CLUSTER_NAME --name appusrpool --node-count 4
                    """
            })
    
    return recommendations

def generate_implementation_timeline(analysis_results):
    """Generate a dynamic implementation timeline based on cluster complexity"""
    logger.info("Generating implementation timeline")
    
    # Get metrics for timeline assessment
    node_metrics = analysis_results.get('node_metrics', [])
    node_count = len(node_metrics)
    deployments = analysis_results.get('hpa_analysis', {}).get('deployments', [])
    deployment_count = len(deployments)
    
    # Assess complexity
    complexity = 'low'
    if node_count > 10 or deployment_count > 15:
        complexity = 'high'
    elif node_count > 5 or deployment_count > 8:
        complexity = 'medium'
    
    # Create timeline based on complexity
    total_savings = analysis_results.get('total_savings', 0)
    
    if complexity == 'low':
        timeline = [
            {'month': 'Month 1', 'action': 'Implement memory-based HPA and right-sizing', 'savings_pct': 70},
            {'month': 'Month 2', 'action': 'Complete storage optimization', 'savings_pct': 100}
        ]
    elif complexity == 'medium':
        timeline = [
            {'month': 'Month 1', 'action': 'Implement memory-based HPA for critical services', 'savings_pct': 40},
            {'month': 'Month 2', 'action': 'Complete HPA rollout + begin right-sizing', 'savings_pct': 70},
            {'month': 'Month 3', 'action': 'Complete right-sizing + begin storage optimization', 'savings_pct': 90},
            {'month': 'Month 4', 'action': 'Complete all optimizations', 'savings_pct': 100}
        ]
    else:  # High complexity
        timeline = [
            {'month': 'Month 1', 'action': 'Implement memory-based HPA for test environments', 'savings_pct': 25},
            {'month': 'Month 2', 'action': 'Extend HPA to non-critical services', 'savings_pct': 45},
            {'month': 'Month 3', 'action': 'Complete HPA rollout + begin right-sizing', 'savings_pct': 60},
            {'month': 'Month 4', 'action': 'Continue right-sizing + begin storage optimization', 'savings_pct': 80},
            {'month': 'Month 5', 'action': 'Complete all optimizations', 'savings_pct': 100}
        ]
    
    # Calculate actual dollar amounts for each stage
    for stage in timeline:
        stage['savings_amount'] = total_savings * (stage['savings_pct'] / 100)
    
    return timeline

def parse_resource_value(value_str):
    """Convert Kubernetes resource strings to numeric values"""
    if not isinstance(value_str, str):
        return value_str  # Already a number
        
    # Remove any whitespace
    value_str = str(value_str).strip()
    
    # Extract the numeric part
    numeric_part = ""
    for char in value_str:
        if char.isdigit() or char == '.':
            numeric_part += char
        else:
            break
    
    if not numeric_part:
        return 0
        
    value = float(numeric_part)
    
    # Apply the unit multiplier
    if 'm' in value_str:  # millicores
        return value
    elif 'Ki' in value_str:
        return value * 1024
    elif 'Mi' in value_str:
        return value
    elif 'Gi' in value_str:
        return value * 1024
    elif 'Ti' in value_str:
        return value * 1024 * 1024
    
    return value

def integrate_metrics_with_analysis(metrics_file_path, analysis_results):
    """Main function to integrate metrics from JSON file with cost analysis"""
    logger.info(f"Integrating metrics from {metrics_file_path} with cost analysis")
    
    try:
        # Import and process metrics
        metrics_data = import_metrics_from_json(metrics_file_path)
        
        # Extract cluster info
        if 'cluster' in metrics_data:
            cluster_info = metrics_data['cluster']
            analysis_results['resource_group'] = cluster_info.get('resource_group', analysis_results.get('resource_group', ''))
            analysis_results['cluster_name'] = cluster_info.get('name', analysis_results.get('cluster_name', ''))
        
        # Calculate node and storage costs
        node_cost = analysis_results.get('node_cost', 0)
        storage_cost = analysis_results.get('storage_cost', 0)
        
        # Calculate savings
        savings_results = calculate_savings(metrics_data, node_cost, storage_cost)
        
        # Update analysis results with calculated metrics
        for key, value in savings_results.items():
            analysis_results[key] = value
        
        # Generate implementation recommendations
        recommendations = generate_implementation_recommendations(analysis_results)
        analysis_results['recommendations'] = recommendations
        
        # Generate implementation timeline
        timeline = generate_implementation_timeline(analysis_results)
        analysis_results['implementation_timeline'] = timeline
        
        # Calculate annual savings
        analysis_results['annual_savings'] = analysis_results.get('total_savings', 0) * 12
        
        # Calculate savings percentage
        total_cost = analysis_results.get('total_cost', 0)
        if total_cost > 0:
            analysis_results['savings_percentage'] = (analysis_results.get('total_savings', 0) / total_cost) * 100
        else:
            analysis_results['savings_percentage'] = 0
        
        logger.info("Successfully integrated metrics with cost analysis")
        return analysis_results
    
    except Exception as e:
        logger.error(f"Error integrating metrics with analysis: {e}")
        raise RuntimeError(f"Failed to integrate metrics: {str(e)}")