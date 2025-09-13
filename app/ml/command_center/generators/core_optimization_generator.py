from typing import Dict, List
from ..models.core import ExecutableCommand

class CoreOptimizationCommandGenerator:
    """Generator for core AKS optimization commands (HPA, rightsizing, node optimization, etc.)"""
    
    def generate_hpa_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate HPA optimization commands"""
        commands = []
        
        # Extract HPA data
        hpa_count = analysis_results.get('hpa_count', 0)
        hpa_savings = analysis_results.get('hpa_savings', 0)
        
        if hpa_savings > 0:
            commands.append(ExecutableCommand(
                command=f"kubectl get deployments -A -o json | jq '.items[] | select(.spec.replicas > 1) | {{name: .metadata.name, namespace: .metadata.namespace}}'",
                description="Identify deployments suitable for HPA",
                category="hpa_optimization",
                priority_score=80,
                savings_estimate=hpa_savings
            ))
        
        return commands
    
    def generate_rightsizing_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate resource rightsizing commands"""
        commands = []
        
        rightsizing_savings = analysis_results.get('right_sizing_savings', 0)
        
        if rightsizing_savings > 0:
            commands.append(ExecutableCommand(
                command=f"kubectl top pods -A --sort-by=cpu",
                description="Analyze pod CPU usage for rightsizing opportunities",
                category="resource_rightsizing",
                priority_score=85,
                savings_estimate=rightsizing_savings
            ))
        
        return commands
    
    def generate_node_optimization_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate node optimization commands"""
        commands = []
        
        # Node pool optimization
        commands.append(ExecutableCommand(
            command=f"az aks nodepool update --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name agentpool --enable-cluster-autoscaler --min-count 1 --max-count 10",
            description="Enable cluster autoscaler for dynamic node scaling",
            category="node_optimization",
            priority_score=75,
            savings_estimate=500
        ))
        
        return commands
    
    def generate_storage_optimization_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate storage optimization commands"""
        commands = []
        
        # Storage class optimization
        commands.append(ExecutableCommand(
            command=f"kubectl get pvc -A -o json | jq '.items[] | select(.spec.storageClassName == \"premium-lrs\") | {{name: .metadata.name, namespace: .metadata.namespace}}'",
            description="Identify PVCs using premium storage for potential optimization",
            category="storage_optimization",
            priority_score=70,
            savings_estimate=300
        ))
        
        return commands
    
    def generate_monitoring_commands(self, analysis_results: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate monitoring optimization commands"""
        commands = []
        
        commands.append(ExecutableCommand(
            command=f"kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/master/examples/standard/cluster-role-binding.yaml",
            description="Deploy kube-state-metrics for enhanced monitoring",
            category="monitoring_optimization",
            priority_score=60,
            savings_estimate=0
        ))
        
        return commands