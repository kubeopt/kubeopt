from typing import Dict, List
from ..models.core import ExecutableCommand

class AKSCostCommandGenerator:
    """Generator for AKS cost management commands"""
    
    def extract_cost_data(self, analysis_results: Dict, cluster_dna, optimization_strategy) -> Dict:
        """Extract data for AKS cost management optimizations from actual analysis"""
        cost_data = {
            'spot_instances_eligible': 0,
            'reserved_instances_potential': 0,
            'unused_resources': [],
            'cost_allocation_tags_missing': 0,
            'budgets_configured': False,
            'total_cost_savings': 0,
            'cost_opportunities': []
        }
        
        # Extract from cluster DNA
        if hasattr(cluster_dna, 'spot_instance_analysis'):
            cost_data['spot_instances_eligible'] = cluster_dna.spot_instance_analysis.get('eligible_workloads', 0)
        elif cluster_dna and hasattr(cluster_dna, 'cost_analysis'):
            cost_data['spot_instances_eligible'] = cluster_dna.cost_analysis.get('spot_eligible_nodes', 0)
        
        # Extract comprehensive cost data from analysis results
        if 'cost_optimization' in analysis_results:
            cost_opt = analysis_results['cost_optimization']
            # NEW STANDARDS-BASED: Use compute optimization savings
            cost_data['reserved_instances_potential'] = cost_opt.get('compute_optimization_savings', 0)
            cost_data['unused_resources'] = cost_opt.get('unused_resources', [])
            cost_data['total_cost_savings'] = cost_opt.get('total_potential_savings', 0)
        
        # Look for cost opportunities in optimization results
        cost_opportunities = analysis_results.get('optimization_opportunities', {}).get('cost_reduction', [])
        cost_data['cost_opportunities'] = cost_opportunities
        
        # Calculate total savings from multiple sources
        if not cost_data['total_cost_savings']:
            savings_sources = [
                analysis_results.get('cpu_optimization', {}).get('potential_savings', 0),
                analysis_results.get('memory_optimization', {}).get('potential_savings', 0), 
                analysis_results.get('storage_optimization', {}).get('potential_savings', 0),
                sum(opp.get('monthly_savings', 0) for opp in cost_opportunities)
            ]
            cost_data['total_cost_savings'] = sum(savings_sources)
        
        # Check for spot instance eligibility from node analysis
        if not cost_data['spot_instances_eligible'] and 'node_analysis' in analysis_results:
            node_analysis = analysis_results['node_analysis']
            cost_data['spot_instances_eligible'] = node_analysis.get('spot_eligible_workloads', 0)
        
        return cost_data

    def generate_commands(self, cost_data: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate AKS cost management commands based on actual analysis data"""
        commands = []
        
        # Spot instance optimization with realistic savings
        if cost_data['spot_instances_eligible'] > 0:
            # Calculate realistic spot savings (typically 60-80% savings on compute)
            spot_savings = cost_data['spot_instances_eligible'] * 150  # More conservative estimate
            
            commands.append(ExecutableCommand(
                command=f"az aks nodepool add --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name spotpool --priority Spot --eviction-policy Delete --spot-max-price -1 --enable-cluster-autoscaler --min-count 1 --max-count {min(10, cost_data['spot_instances_eligible'] * 2)}",
                description=f"Add spot instance node pool for {cost_data['spot_instances_eligible']} eligible workloads (${spot_savings}/month savings)",
                category="aks_cost_management",
                priority_score=85,
                savings_estimate=spot_savings,
                estimated_duration_minutes=15,
                risk_level="medium",
                rollback_commands=[f"az aks nodepool delete --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name spotpool --no-wait"],
                validation_commands=[f"az aks nodepool show --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name spotpool --query 'scaleSetPriority'"]
            ))
        
        # Generate commands for specific cost opportunities
        for opportunity in cost_data['cost_opportunities'][:3]:  # Top 3 opportunities
            opp_type = opportunity.get('type', 'cost_reduction')
            description = opportunity.get('description', 'Cost optimization opportunity')
            savings = opportunity.get('monthly_savings', 100)
            command = opportunity.get('command', f"echo 'Cost optimization: {description}'")
            
            commands.append(ExecutableCommand(
                command=command,
                description=f"{description} (${savings}/month)",
                category="aks_cost_management",
                priority_score=80,
                savings_estimate=savings,
                estimated_duration_minutes=10,
                risk_level="low"
            ))
        
        # Reserved instance recommendations (if any potential savings)
        if cost_data['reserved_instances_potential'] > 0:
            commands.append(ExecutableCommand(
                command=f"az consumption reservation recommendation list --resource-group {variable_context['resource_group']} --look-back-period Last30Days",
                description=f"Analyze reserved instance opportunities (${cost_data['reserved_instances_potential']}/month potential)",
                category="aks_cost_management",
                priority_score=75,
                savings_estimate=cost_data['reserved_instances_potential'],
                estimated_duration_minutes=20,
                risk_level="low"
            ))
        
        # Cost allocation tags (if any cost savings expected)
        if cost_data['total_cost_savings'] > 0:
            commands.append(ExecutableCommand(
                command=f"az aks update --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --tags Environment=Production CostCenter=Engineering Owner=DevOps TotalOptimization=${cost_data['total_cost_savings']:.0f}",
                description=f"Add cost allocation tags for ${cost_data['total_cost_savings']:.0f}/month optimization tracking",
                category="aks_cost_management",
                priority_score=60,
                savings_estimate=0,  # Indirect savings through better tracking
                estimated_duration_minutes=5,
                risk_level="low"
            ))
        
        # Dynamic budget based on actual cost analysis
        if cost_data['total_cost_savings'] > 0:
            # Set budget as percentage of current estimated costs
            current_estimated_monthly = cost_data['total_cost_savings'] * 3  # Assume optimizing 33% of costs
            budget_amount = int(current_estimated_monthly * 1.2)  # 20% buffer
            
            commands.append(ExecutableCommand(
                command=f"az consumption budget create --resource-group {variable_context['resource_group']} --budget-name aks-optimized-budget --amount {budget_amount} --time-grain Monthly --start-date $(date -u -d 'first day of this month' '+%Y-%m-01T00:00:00Z') --end-date $(date -u -d 'first day of next month' '+%Y-%m-01T00:00:00Z')",
                description=f"Create optimized cost budget (${budget_amount}/month based on analysis)",
                category="aks_cost_management", 
                priority_score=70,
                savings_estimate=cost_data['total_cost_savings'] * 0.1,  # 10% additional savings from monitoring
                estimated_duration_minutes=8,
                risk_level="low"
            ))
        
        return commands