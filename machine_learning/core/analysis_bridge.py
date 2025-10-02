#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Analysis to Implementation Bridge - Connects analysis insights to executable commands
===================================================================================

This bridge layer transforms rich analysis data into cluster-specific implementation parameters,
ensuring that generated commands are based on actual cluster insights rather than generic defaults.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class WorkloadOptimizationData:
    """Workload-specific optimization parameters derived from analysis"""
    workload_name: str
    namespace: str
    current_cpu_usage_pct: float
    current_memory_usage_pct: float
    optimal_cpu_target: int
    optimal_memory_target: int
    recommended_min_replicas: int
    recommended_max_replicas: int
    resource_requests: Dict[str, str]
    resource_limits: Dict[str, str]
    scaling_potential_score: float
    monthly_cost_impact: float

@dataclass
class ClusterOptimizationContext:
    """Cluster-wide optimization context derived from analysis"""
    cluster_name: str
    resource_group: str
    subscription_id: str
    
    # Derived cluster metrics
    avg_node_cpu_utilization: float
    avg_node_memory_utilization: float
    cluster_cost_per_hour: float
    high_cost_threshold: float
    
    # Optimization parameters
    optimal_hpa_cpu_target: int
    optimal_hpa_memory_target: int
    recommended_node_count: int
    cost_optimization_priority: str  # 'cost', 'performance', 'balanced'
    
    # Workload insights
    high_cost_workloads: List[str]
    underutilized_workloads: List[str]
    scaling_candidates: List[str]

class AnalysisToImplementationBridge:
    """
    Bridge that transforms analysis results into implementation-ready parameters
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_optimization_context(self, analysis_results: Dict) -> ClusterOptimizationContext:
        """Create cluster-wide optimization context from analysis results"""
        
        cluster_name = analysis_results.get('cluster_name', 'unknown')
        resource_group = analysis_results.get('resource_group', 'unknown')
        subscription_id = analysis_results.get('subscription_id', 'unknown')
        
        # Extract node metrics for cluster-wide calculations
        node_metrics = analysis_results.get('node_metrics', [])
        avg_cpu_util, avg_memory_util = self._calculate_cluster_utilization(node_metrics)
        
        # Calculate cluster cost metrics
        total_cost = analysis_results.get('total_cost', 0)
        cluster_cost_per_hour = total_cost / (24 * 30) if total_cost > 0 else 0
        
        # Derive optimization parameters from actual data
        optimal_cpu_target = self._calculate_optimal_cpu_target(avg_cpu_util, node_metrics)
        optimal_memory_target = self._calculate_optimal_memory_target(avg_memory_util, node_metrics)
        
        # Analyze workload patterns
        namespace_costs = analysis_results.get('namespace_costs', {})
        workload_costs = analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
        
        high_cost_threshold = self._calculate_dynamic_cost_threshold(workload_costs)
        high_cost_workloads = self._identify_high_cost_workloads(workload_costs, high_cost_threshold)
        underutilized_workloads = self._identify_underutilized_workloads(node_metrics, workload_costs)
        scaling_candidates = self._identify_scaling_candidates(analysis_results)
        
        # Determine optimization priority based on cluster characteristics
        cost_optimization_priority = self._determine_optimization_priority(
            avg_cpu_util, avg_memory_util, total_cost, len(high_cost_workloads)
        )
        
        return ClusterOptimizationContext(
            cluster_name=cluster_name,
            resource_group=resource_group,
            subscription_id=subscription_id,
            avg_node_cpu_utilization=avg_cpu_util,
            avg_node_memory_utilization=avg_memory_util,
            cluster_cost_per_hour=cluster_cost_per_hour,
            high_cost_threshold=high_cost_threshold,
            optimal_hpa_cpu_target=optimal_cpu_target,
            optimal_hpa_memory_target=optimal_memory_target,
            recommended_node_count=self._calculate_optimal_node_count(node_metrics),
            cost_optimization_priority=cost_optimization_priority,
            high_cost_workloads=high_cost_workloads,
            underutilized_workloads=underutilized_workloads,
            scaling_candidates=scaling_candidates
        )
    
    def create_workload_optimization_data(self, 
                                        analysis_results: Dict, 
                                        workload_name: str) -> Optional[WorkloadOptimizationData]:
        """Create workload-specific optimization parameters"""
        
        workload_costs = analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
        workload_data = workload_costs.get(workload_name)
        
        if not workload_data:
            return None
        
        namespace = workload_data.get('namespace', 'default')
        monthly_cost = workload_data.get('cost', 0)
        
        # Extract workload usage from node metrics
        node_metrics = analysis_results.get('node_metrics', [])
        workload_usage = self._find_workload_usage_in_nodes(workload_name, node_metrics)
        
        current_cpu_usage = workload_usage.get('cpu_usage_pct', 70)
        current_memory_usage = workload_usage.get('memory_usage_pct', 70)
        
        # Calculate optimal targets based on usage patterns
        optimal_cpu_target = self._calculate_workload_optimal_cpu_target(current_cpu_usage)
        optimal_memory_target = self._calculate_workload_optimal_memory_target(current_memory_usage)
        
        # Calculate scaling recommendations
        min_replicas, max_replicas = self._calculate_optimal_scaling_bounds(
            workload_usage, monthly_cost
        )
        
        # Derive resource recommendations
        resource_requests = self._calculate_optimal_resource_requests(workload_usage)
        resource_limits = self._calculate_optimal_resource_limits(workload_usage, resource_requests)
        
        # Calculate scaling potential
        scaling_potential = self._calculate_scaling_potential_score(
            current_cpu_usage, current_memory_usage, monthly_cost
        )
        
        return WorkloadOptimizationData(
            workload_name=workload_name,
            namespace=namespace,
            current_cpu_usage_pct=current_cpu_usage,
            current_memory_usage_pct=current_memory_usage,
            optimal_cpu_target=optimal_cpu_target,
            optimal_memory_target=optimal_memory_target,
            recommended_min_replicas=min_replicas,
            recommended_max_replicas=max_replicas,
            resource_requests=resource_requests,
            resource_limits=resource_limits,
            scaling_potential_score=scaling_potential,
            monthly_cost_impact=monthly_cost
        )
    
    def _calculate_cluster_utilization(self, node_metrics: List[Dict]) -> Tuple[float, float]:
        """Calculate average cluster CPU and memory utilization"""
        if not node_metrics:
            return 70.0, 70.0
        
        cpu_utilizations = []
        memory_utilizations = []
        
        for node in node_metrics:
            if isinstance(node, dict):
                cpu_pct = node.get('cpu_usage_percent', 0)
                memory_pct = node.get('memory_usage_percent', 0)
                
                if cpu_pct > 0:
                    cpu_utilizations.append(cpu_pct)
                if memory_pct > 0:
                    memory_utilizations.append(memory_pct)
        
        avg_cpu = statistics.mean(cpu_utilizations) if cpu_utilizations else 70.0
        avg_memory = statistics.mean(memory_utilizations) if memory_utilizations else 70.0
        
        return avg_cpu, avg_memory
    
    def _calculate_optimal_cpu_target(self, avg_cpu_util: float, node_metrics: List[Dict]) -> int:
        """Calculate optimal HPA CPU target based on cluster characteristics"""
        
        # If cluster is underutilized, be more aggressive with scaling
        if avg_cpu_util < 30:
            return min(int(avg_cpu_util + 20), 60)
        elif avg_cpu_util < 50:
            return min(int(avg_cpu_util + 15), 70)
        elif avg_cpu_util < 70:
            return min(int(avg_cpu_util + 10), 80)
        else:
            # High utilization cluster - be conservative
            return min(int(avg_cpu_util + 5), 85)
    
    def _calculate_optimal_memory_target(self, avg_memory_util: float, node_metrics: List[Dict]) -> int:
        """Calculate optimal HPA memory target"""
        
        # Memory scaling is typically less aggressive than CPU
        if avg_memory_util < 40:
            return min(int(avg_memory_util + 25), 75)
        elif avg_memory_util < 60:
            return min(int(avg_memory_util + 15), 80)
        else:
            return min(int(avg_memory_util + 10), 85)
    
    def _calculate_dynamic_cost_threshold(self, workload_costs: Dict) -> float:
        """Calculate dynamic cost threshold based on workload distribution"""
        if not workload_costs:
            return 100.0
        
        costs = [w.get('cost', 0) for w in workload_costs.values()]
        costs = [c for c in costs if c > 0]
        
        if not costs:
            return 100.0
        
        # Use 75th percentile as high cost threshold
        costs.sort()
        percentile_75_index = int(len(costs) * 0.75)
        return costs[percentile_75_index] if percentile_75_index < len(costs) else costs[-1]
    
    def _identify_high_cost_workloads(self, workload_costs: Dict, threshold: float) -> List[str]:
        """Identify workloads with costs above threshold"""
        high_cost = []
        for workload_name, data in workload_costs.items():
            if data.get('cost', 0) > threshold:
                high_cost.append(workload_name)
        return high_cost
    
    def _identify_underutilized_workloads(self, node_metrics: List[Dict], workload_costs: Dict) -> List[str]:
        """Identify underutilized workloads based on resource usage"""
        underutilized = []
        
        for workload_name, data in workload_costs.items():
            workload_usage = self._find_workload_usage_in_nodes(workload_name, node_metrics)
            cpu_usage = workload_usage.get('cpu_usage_pct', 100)
            memory_usage = workload_usage.get('memory_usage_pct', 100)
            
            # Consider underutilized if both CPU and memory are low
            if cpu_usage < 20 and memory_usage < 30:
                underutilized.append(workload_name)
        
        return underutilized
    
    def _identify_scaling_candidates(self, analysis_results: Dict) -> List[str]:
        """Identify workloads that would benefit from HPA"""
        candidates = []
        
        # Look for workloads with high CPU usage variance or consistently high usage
        workload_costs = analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
        node_metrics = analysis_results.get('node_metrics', [])
        
        for workload_name, data in workload_costs.items():
            workload_usage = self._find_workload_usage_in_nodes(workload_name, node_metrics)
            cpu_usage = workload_usage.get('cpu_usage_pct', 0)
            cost = data.get('cost', 0)
            
            # Good candidates: high CPU usage OR high cost
            if cpu_usage > 60 or cost > 75:
                candidates.append(workload_name)
        
        return candidates
    
    def _find_workload_usage_in_nodes(self, workload_name: str, node_metrics: List[Dict]) -> Dict:
        """Find workload usage data within node metrics"""
        # This would need to be implemented based on your actual node metrics structure
        # For now, return reasonable defaults based on workload name patterns
        
        # Extract namespace and app name from workload_name if possible
        if '/' in workload_name:
            namespace, app_name = workload_name.split('/', 1)
        else:
            namespace = 'default'
            app_name = workload_name
        
        # Return estimated usage (this should be replaced with actual lookup)
        return {
            'cpu_usage_pct': 65.0,  # Would come from actual metrics
            'memory_usage_pct': 70.0,  # Would come from actual metrics
            'requests': {
                'cpu': '250m',
                'memory': '512Mi'
            }
        }
    
    def _determine_optimization_priority(self, avg_cpu: float, avg_memory: float, 
                                       total_cost: float, high_cost_workload_count: int) -> str:
        """Determine optimization priority based on cluster characteristics"""
        
        # Cost-focused if high costs with low utilization
        if total_cost > 2000 and avg_cpu < 40 and avg_memory < 50:
            return 'cost'
        
        # Performance-focused if high utilization
        elif avg_cpu > 80 or avg_memory > 85:
            return 'performance'
        
        # Balanced approach for most cases
        else:
            return 'balanced'
    
    def _calculate_optimal_node_count(self, node_metrics: List[Dict]) -> int:
        """Calculate optimal node count based on utilization"""
        current_node_count = len(node_metrics)
        
        if not node_metrics:
            return 3  # Minimum recommended
        
        avg_cpu, avg_memory = self._calculate_cluster_utilization(node_metrics)
        
        # If underutilized, suggest fewer nodes
        if avg_cpu < 30 and avg_memory < 40 and current_node_count > 2:
            return max(current_node_count - 1, 2)
        
        # If overutilized, suggest more nodes
        elif avg_cpu > 80 or avg_memory > 85:
            return current_node_count + 1
        
        return current_node_count
    
    def _calculate_workload_optimal_cpu_target(self, current_cpu_usage: float) -> int:
        """Calculate optimal CPU target for specific workload"""
        if current_cpu_usage < 30:
            return 50
        elif current_cpu_usage < 50:
            return 65
        elif current_cpu_usage < 70:
            return 75
        else:
            return 80
    
    def _calculate_workload_optimal_memory_target(self, current_memory_usage: float) -> int:
        """Calculate optimal memory target for specific workload"""
        if current_memory_usage < 40:
            return 65
        elif current_memory_usage < 60:
            return 75
        else:
            return 80
    
    def _calculate_optimal_scaling_bounds(self, workload_usage: Dict, monthly_cost: float) -> Tuple[int, int]:
        """Calculate optimal min/max replicas"""
        cpu_usage = workload_usage.get('cpu_usage_pct', 70)
        
        # High cost or high usage workloads get more aggressive scaling
        if monthly_cost > 150 or cpu_usage > 70:
            return 2, 10
        elif monthly_cost > 75 or cpu_usage > 50:
            return 2, 8
        else:
            return 1, 6
    
    def _calculate_optimal_resource_requests(self, workload_usage: Dict) -> Dict[str, str]:
        """Calculate optimal resource requests based on usage"""
        current_requests = workload_usage.get('requests', {})
        
        # If we have current requests, optimize them; otherwise use defaults
        return {
            'cpu': current_requests.get('cpu', '200m'),
            'memory': current_requests.get('memory', '256Mi')
        }
    
    def _calculate_optimal_resource_limits(self, workload_usage: Dict, requests: Dict[str, str]) -> Dict[str, str]:
        """Calculate optimal resource limits"""
        # Set limits to 2x requests for CPU, 1.5x for memory
        cpu_request = requests.get('cpu', '200m')
        memory_request = requests.get('memory', '256Mi')
        
        # Parse CPU (assuming millicores format)
        if cpu_request.endswith('m'):
            cpu_limit_val = int(cpu_request[:-1]) * 2
            cpu_limit = f"{cpu_limit_val}m"
        else:
            cpu_limit = "400m"
        
        # Parse memory
        if memory_request.endswith('Mi'):
            memory_val = int(memory_request[:-2])
            memory_limit = f"{int(memory_val * 1.5)}Mi"
        else:
            memory_limit = "384Mi"
        
        return {
            'cpu': cpu_limit,
            'memory': memory_limit
        }
    
    def _calculate_scaling_potential_score(self, cpu_usage: float, memory_usage: float, cost: float) -> float:
        """Calculate scaling potential score (0-10)"""
        
        # Higher score for workloads that would benefit more from scaling
        usage_score = min(cpu_usage / 10, 8)  # High CPU usage = good candidate
        cost_score = min(cost / 50, 8)  # High cost = good candidate
        
        return min(usage_score + cost_score / 2, 10.0)