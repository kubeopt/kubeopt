from typing import Dict, List
from ..models.core import ExecutableCommand

class CoreOptimizationCommandGenerator:
    """Generator for core AKS optimization commands (HPA, rightsizing, node optimization, etc.)"""
    
    def generate_hpa_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate HPA optimization commands based on actual analysis data"""
        commands = []
        
        # Extract HPA data from multiple potential sources
        hpa_data = analysis_results.get('hpa_optimization', {})
        hpa_count = hpa_data.get('count', analysis_results.get('hpa_count', 0))
        hpa_savings = hpa_data.get('savings', analysis_results.get('hpa_savings', 0))
        
        # Look for actual HPA opportunities in analysis results
        hpa_opportunities = analysis_results.get('optimization_opportunities', {}).get('hpa_scaling', [])
        cpu_optimization = analysis_results.get('cpu_optimization', {})
        
        # Calculate realistic savings based on analysis
        if not hpa_savings and cpu_optimization:
            hpa_savings = cpu_optimization.get('potential_savings', 0) * 0.3  # HPA typically saves 30% of CPU optimization
        
        if hpa_savings > 0 or hpa_opportunities:
            # Calculate realistic duration based on number of deployments
            estimated_minutes = max(15, len(hpa_opportunities) * 10) if hpa_opportunities else 20
            
            commands.append(ExecutableCommand(
                command=f"kubectl get deployments -A -o json | jq '.items[] | select(.spec.replicas > 1) | {{name: .metadata.name, namespace: .metadata.namespace}}'",
                description=f"Identify {len(hpa_opportunities) if hpa_opportunities else 'potential'} deployments suitable for HPA",
                category="hpa_optimization",
                priority_score=80,
                savings_estimate=hpa_savings,
                estimated_duration_minutes=estimated_minutes,
                risk_level="medium" if hpa_savings > 1000 else "low",
                rollback_commands=["# Read-only command - no rollback needed"],
                validation_commands=["kubectl get deployments -A --no-headers | wc -l"]
            ))
            
            # Add actual HPA creation commands if specific opportunities exist
            for opportunity in hpa_opportunities[:3]:  # Limit to top 3 for practicality
                deployment_name = opportunity.get('name', 'deployment')
                namespace = opportunity.get('namespace', 'default')
                commands.append(ExecutableCommand(
                    command=f"kubectl autoscale deployment {deployment_name} --cpu-percent={opportunity.get('cpu_target', 70)} --min={opportunity.get('min_replicas', 2)} --max={opportunity.get('max_replicas', 10)} -n {namespace}",
                    description=f"Create HPA for {deployment_name} (estimated ${opportunity.get('monthly_savings', 100)}/month savings)",
                    category="hpa_optimization",
                    priority_score=85,
                    savings_estimate=opportunity.get('monthly_savings', 100),
                    estimated_duration_minutes=5,
                    risk_level="low",
                    rollback_commands=[f"kubectl delete hpa {deployment_name} -n {namespace}"],
                    validation_commands=[f"kubectl get hpa {deployment_name} -n {namespace} -o jsonpath='{{.status.currentReplicas}}'"]
                ))
        
        return commands
    
    def generate_rightsizing_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate resource rightsizing commands based on actual analysis data"""
        commands = []
        
        # Extract rightsizing data from multiple sources
        rightsizing_savings = analysis_results.get('right_sizing_savings', 0)
        cpu_optimization = analysis_results.get('cpu_optimization', {})
        memory_optimization = analysis_results.get('memory_optimization', {})
        
        # Look for specific rightsizing opportunities
        rightsizing_opportunities = analysis_results.get('optimization_opportunities', {}).get('resource_rightsizing', [])
        
        # Calculate total potential savings
        total_savings = rightsizing_savings
        if not total_savings:
            cpu_savings = cpu_optimization.get('potential_savings', 0)
            memory_savings = memory_optimization.get('potential_savings', 0)
            total_savings = cpu_savings + memory_savings
        
        if total_savings > 0 or rightsizing_opportunities:
            # Base analysis command
            analysis_duration = max(10, len(rightsizing_opportunities) * 5) if rightsizing_opportunities else 15
            
            commands.append(ExecutableCommand(
                command=f"kubectl top pods -A --sort-by=cpu",
                description=f"Analyze pod CPU usage for {len(rightsizing_opportunities) if rightsizing_opportunities else 'potential'} rightsizing opportunities",
                category="resource_rightsizing",
                priority_score=85,
                savings_estimate=total_savings * 0.2,  # Analysis step saves 20% of potential
                estimated_duration_minutes=analysis_duration,
                risk_level="low",
                rollback_commands=["# Read-only command - no rollback needed"],
                validation_commands=["kubectl top pods -A --no-headers | wc -l"]
            ))
            
            # Memory analysis command
            commands.append(ExecutableCommand(
                command=f"kubectl top pods -A --sort-by=memory",
                description="Analyze pod memory usage patterns",
                category="resource_rightsizing", 
                priority_score=80,
                savings_estimate=memory_optimization.get('potential_savings', total_savings * 0.3),
                estimated_duration_minutes=10,
                risk_level="low",
                rollback_commands=["# Read-only command - no rollback needed"],
                validation_commands=["kubectl top pods -A --no-headers | wc -l"]
            ))
            
            # Generate specific rightsizing commands
            for opportunity in rightsizing_opportunities[:5]:  # Top 5 opportunities
                resource_type = opportunity.get('resource_type', 'cpu')
                workload_name = opportunity.get('workload_name', 'workload')
                namespace = opportunity.get('namespace', 'default')
                recommended_value = opportunity.get('recommended_value', '100m' if resource_type == 'cpu' else '128Mi')
                monthly_savings = opportunity.get('monthly_savings', 50)
                
                patch_json = f'{{"spec":{{"template":{{"spec":{{"containers":[{{"name":"{workload_name}","resources":{{"requests":{{"{resource_type}":"{recommended_value}"}}}}}}]}}}}}}}}'
                current_value = opportunity.get('current_value', '200m' if resource_type == 'cpu' else '256Mi')
                rollback_json = f'{{"spec":{{"template":{{"spec":{{"containers":[{{"name":"{workload_name}","resources":{{"requests":{{"{resource_type}":"{current_value}"}}}}}}]}}}}}}}}'
                
                commands.append(ExecutableCommand(
                    command=f"kubectl patch deployment {workload_name} -n {namespace} -p '{patch_json}'",
                    description=f"Optimize {resource_type} for {workload_name} (save ${monthly_savings}/month)",
                    category="resource_rightsizing",
                    priority_score=90,
                    savings_estimate=monthly_savings,
                    estimated_duration_minutes=8,
                    risk_level="medium",
                    rollback_commands=[f"kubectl patch deployment {workload_name} -n {namespace} -p '{rollback_json}'"],
                    validation_commands=[f"kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources.requests.{resource_type}}}'"]
                ))
        
        return commands
    
    def generate_node_optimization_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate node optimization commands based on actual analysis data"""
        commands = []
        
        # Extract node optimization data
        node_analysis = analysis_results.get('node_analysis', {})
        node_savings = node_analysis.get('potential_savings', 0)
        current_nodes = variable_context.get('node_count', 3)
        
        # Only add node optimization if there's actual potential
        if current_nodes > 2:  # Only optimize if more than 2 nodes
            # Calculate realistic savings based on cluster size
            estimated_savings = min(node_savings, current_nodes * 50)  # Max $50/node/month from autoscaling
            
            if estimated_savings > 0:
                commands.append(ExecutableCommand(
                    command=f"az aks nodepool update --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name agentpool --enable-cluster-autoscaler --min-count 1 --max-count {min(10, current_nodes * 2)}",
                    description=f"Enable cluster autoscaler for {current_nodes} nodes (save ${estimated_savings}/month)",
                    category="node_optimization",
                    priority_score=75,
                    savings_estimate=estimated_savings,
                    estimated_duration_minutes=12,
                    risk_level="medium",
                    rollback_commands=[f"az aks nodepool update --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name agentpool --disable-cluster-autoscaler"],
                    validation_commands=[f"az aks nodepool show --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name agentpool --query 'enableAutoScaling'"]
                ))
        
        return commands
    
    def generate_storage_optimization_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate storage optimization commands based on actual analysis data"""
        commands = []
        
        # Extract storage optimization data
        storage_optimization = analysis_results.get('storage_optimization', {})
        storage_savings = storage_optimization.get('potential_savings', 0)
        
        # Only add storage optimization if there are actual savings
        if storage_savings > 0:
            commands.append(ExecutableCommand(
                command=f"kubectl get pvc -A -o json | jq '.items[] | select(.spec.storageClassName == \"premium-lrs\") | {{name: .metadata.name, namespace: .metadata.namespace}}'",
                description=f"Identify PVCs using premium storage (save ${storage_savings}/month potential)",
                category="storage_optimization",
                priority_score=70,
                savings_estimate=storage_savings,
                estimated_duration_minutes=8,
                risk_level="low",
                rollback_commands=["# Read-only command - no rollback needed"],
                validation_commands=["kubectl get pvc -A --no-headers | wc -l"]
            ))
        
        return commands
    
    def generate_monitoring_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate monitoring optimization commands based on actual analysis data"""
        commands = []
        
        # Only add monitoring if there are significant optimizations to track
        total_savings = (
            analysis_results.get('cpu_optimization', {}).get('potential_savings', 0) +
            analysis_results.get('memory_optimization', {}).get('potential_savings', 0) +
            analysis_results.get('storage_optimization', {}).get('potential_savings', 0)
        )
        
        # Add monitoring infrastructure if any savings to track
        if total_savings > 0:
            commands.append(ExecutableCommand(
                command=f"kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/master/examples/standard/cluster-role-binding.yaml",
                description=f"Deploy monitoring to track ${total_savings}/month optimization progress",
                category="monitoring_optimization",
                priority_score=60,
                savings_estimate=0,  # Monitoring doesn't save money directly
                estimated_duration_minutes=10,
                risk_level="low",
                rollback_commands=["kubectl delete -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/master/examples/standard/cluster-role-binding.yaml"],
                validation_commands=["kubectl get clusterrolebinding kube-state-metrics"]
            ))
        
        return commands
    
    def generate_networking_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate networking optimization commands based on actual analysis data"""
        commands = []
        
        # Extract networking savings from analysis results
        networking_savings = analysis_results.get('networking_monthly_savings', 0)
        networking_cost = analysis_results.get('networking_cost', 0)
        
        # Only generate networking commands if actual savings found
        if networking_savings > 0:
            # Network policy optimization
            commands.append(ExecutableCommand(
                command=f"kubectl get services -A -o wide",
                description=f"Analyze networking configuration for ${networking_savings:.2f}/month optimization",
                category="networking_optimization", 
                priority_score=75,
                savings_estimate=networking_savings * 0.3,  # Analysis provides 30% of savings
                estimated_duration_minutes=10,
                risk_level="low",
                rollback_commands=["# Read-only command - no rollback needed"],
                validation_commands=["kubectl get services -A --no-headers | wc -l"]
            ))
            
            # Load balancer optimization if significant networking costs
            if networking_cost > 100:  # If >$100/month in networking costs
                commands.append(ExecutableCommand(
                    command=f"az network lb list --resource-group {variable_context['resource_group']} --query '[].{{name:name,sku:sku.name,frontend:frontendIpConfigurations[].publicIpAddress.id}}'",
                    description=f"Optimize load balancer configuration (${networking_savings * 0.7:.2f}/month potential)",
                    category="networking_optimization",
                    priority_score=80,
                    savings_estimate=networking_savings * 0.7,
                    estimated_duration_minutes=15,
                    risk_level="medium",
                    rollback_commands=[f"# Manual rollback required - document current LB configuration before changes"],
                    validation_commands=[f"az network lb list --resource-group {variable_context['resource_group']} --query '[].provisioningState'"]
                ))
        
        return commands