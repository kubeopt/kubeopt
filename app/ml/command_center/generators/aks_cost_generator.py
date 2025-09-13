from typing import Dict, List
from ..models.core import ExecutableCommand

class AKSCostCommandGenerator:
    """Generator for AKS cost management commands"""
    
    def extract_cost_data(self, analysis_results: Dict, cluster_dna, optimization_strategy) -> Dict:
        """Extract data for AKS cost management optimizations"""
        cost_data = {
            'spot_instances_eligible': 0,
            'reserved_instances_potential': 0,
            'unused_resources': [],
            'cost_allocation_tags_missing': 0,
            'budgets_configured': False
        }
        
        # Extract from cluster DNA
        if hasattr(cluster_dna, 'spot_instance_analysis'):
            cost_data['spot_instances_eligible'] = cluster_dna.spot_instance_analysis.get('eligible_workloads', 0)
        
        # Extract from analysis results
        if 'cost_optimization' in analysis_results:
            cost_opt = analysis_results['cost_optimization']
            cost_data['reserved_instances_potential'] = cost_opt.get('reserved_instance_savings', 0)
            cost_data['unused_resources'] = cost_opt.get('unused_resources', [])
        
        return cost_data

    def generate_commands(self, cost_data: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate AKS cost management commands"""
        commands = []
        
        # Spot instance optimization
        if cost_data['spot_instances_eligible'] > 0:
            commands.append(ExecutableCommand(
                command=f"az aks nodepool add --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name spotpool --priority Spot --eviction-policy Delete --spot-max-price -1 --enable-cluster-autoscaler --min-count 1 --max-count 10",
                description="Add spot instance node pool for cost optimization",
                category="aks_cost_management",
                priority_score=85,
                savings_estimate=cost_data['spot_instances_eligible'] * 200
            ))
        
        # Cost allocation tags
        commands.append(ExecutableCommand(
            command=f"az aks update --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --tags Environment=Production CostCenter=Engineering Owner=DevOps",
            description="Add cost allocation tags to AKS cluster",
            category="aks_cost_management",
            priority_score=60,
            savings_estimate=0
        ))
        
        # Budget monitoring
        commands.append(ExecutableCommand(
            command=f"az consumption budget create --resource-group {variable_context['resource_group']} --budget-name aks-monthly-budget --amount 1000 --time-grain Monthly --start-date $(date -u -d 'first day of this month' '+%Y-%m-01T00:00:00Z') --end-date $(date -u -d 'first day of next month' '+%Y-%m-01T00:00:00Z')",
            description="Create cost budget for AKS cluster monitoring",
            category="aks_cost_management", 
            priority_score=70,
            savings_estimate=0
        ))
        
        return commands