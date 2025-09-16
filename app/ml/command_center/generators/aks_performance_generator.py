from typing import Dict, List
from ..models.core import ExecutableCommand

class AKSPerformanceCommandGenerator:
    """Generator for AKS performance commands"""
    
    def extract_performance_data(self, analysis_results: Dict, cluster_dna, optimization_strategy) -> Dict:
        """Extract data for AKS performance optimizations"""
        performance_data = {
            'cpu_utilization': 0,
            'memory_utilization': 0,
            'disk_iops': 0,
            'network_throughput': 0,
            'pod_startup_time': 0,
            'high_cpu_workloads': [],
            'high_memory_workloads': []
        }
        
        # Extract from cluster DNA
        if hasattr(cluster_dna, 'performance_metrics'):
            perf_metrics = cluster_dna.performance_metrics
            performance_data['cpu_utilization'] = perf_metrics.get('avg_cpu_utilization', 0)
            performance_data['memory_utilization'] = perf_metrics.get('avg_memory_utilization', 0)
        
        # Extract from analysis results
        if 'performance_analysis' in analysis_results:
            perf_analysis = analysis_results['performance_analysis']
            performance_data['high_cpu_workloads'] = perf_analysis.get('high_cpu_workloads', [])
            performance_data['high_memory_workloads'] = perf_analysis.get('high_memory_workloads', [])
        
        return performance_data

    def generate_commands(self, performance_data: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate AKS performance optimization commands"""
        commands = []
        
        # Enable cluster insights
        commands.append(ExecutableCommand(
            command=f"az aks enable-addons --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --addons monitoring --workspace-resource-id /subscriptions/{variable_context['subscription_id']}/resourceGroups/{variable_context['resource_group']}/providers/Microsoft.OperationalInsights/workspaces/aks-workspace",
            description="Enable Container Insights for comprehensive performance monitoring",
            category="aks_performance",
            priority_score=80,
            savings_estimate=0
        ))
        
        # High CPU workload optimization - only if there are actual savings
        performance_savings = performance_data.get('potential_performance_savings', 0)
        if performance_data['high_cpu_workloads'] and performance_savings > 0:
            per_workload_savings = performance_savings / len(performance_data['high_cpu_workloads'])
            for workload in performance_data['high_cpu_workloads'][:3]:
                patch_json = '{"spec":{"template":{"spec":{"containers":[{"name":"' + workload + '","resources":{"limits":{"cpu":"2000m"},"requests":{"cpu":"1000m"}}}]}}}}'
                commands.append(ExecutableCommand(
                    command=f"kubectl patch deployment {workload} -p '{patch_json}'",
                    description=f"Optimize CPU resources for high-utilization workload {workload}",
                    category="aks_performance",
                    priority_score=75,
                    savings_estimate=per_workload_savings,
                    estimated_duration_minutes=10,
                    risk_level="medium"
                ))
        
        # Enable accelerated networking
        commands.append(ExecutableCommand(
            command=f"az aks nodepool update --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --name agentpool --enable-ultra-ssd",
            description="Enable ultra SSD for high-performance storage requirements",
            category="aks_performance", 
            priority_score=70,
            savings_estimate=0
        ))
        
        # Pod disruption budgets for high-priority workloads
        if performance_data['high_memory_workloads']:
            for workload in performance_data['high_memory_workloads'][:2]:
                pdb_yaml = f"""kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {workload}-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: {workload}
EOF"""
                commands.append(ExecutableCommand(
                    command=pdb_yaml,
                    description=f"Create pod disruption budget for critical workload {workload}",
                    category="aks_performance",
                    priority_score=65,
                    savings_estimate=0
                ))
        
        return commands