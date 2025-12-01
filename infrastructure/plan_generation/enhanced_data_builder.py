#!/usr/bin/env python3
"""
Enhanced Analysis Data Structure Builder
Builds optimized input for Claude with high-cost workloads + aggregate summaries
"""
from typing import Dict, List, Any
import json

class EnhancedAnalysisDataBuilder:
    """Builds enhanced analysis input optimized for Claude plan generation"""
    
    def __init__(self, cost_threshold: float = 1.0):
        self.cost_threshold = cost_threshold
        
    def build_enhanced_analysis_input(self, raw_cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw cluster data into optimized enhanced analysis input
        
        Structure:
        - high_cost_workloads: Detailed workloads > $1/month for specific optimization
        - workload_summary: Aggregate data for cluster-wide recommendations
        - cluster_context: Infrastructure and policy information
        """
        workloads = raw_cluster_data.get('workloads', [])
        
        # Categorize workloads by cost and characteristics
        high_cost_workloads = []
        workload_categories = self._categorize_workloads(workloads)
        
        # Filter high-cost workloads for detailed analysis
        for workload in workloads:
            monthly_cost = workload.get('cost_estimate', {}).get('monthly_cost', 0.0)
            if monthly_cost > self.cost_threshold:
                high_cost_workloads.append(workload)
        
        # Build enhanced structure
        enhanced_input = {
            'metadata': {
                'cluster_id': raw_cluster_data.get('cluster_info', {}).get('cluster_id'),
                'cluster_name': raw_cluster_data.get('cluster_info', {}).get('name'),
                'total_workloads': len(workloads),
                'high_cost_workloads_count': len(high_cost_workloads),
                'analysis_timestamp': raw_cluster_data.get('metadata', {}).get('timestamp'),
                'cost_threshold': self.cost_threshold
            },
            
            # Detailed workloads for specific optimization
            'high_cost_workloads': high_cost_workloads,
            
            # Aggregate summaries for bulk recommendations
            'workload_summary': self._build_workload_summary(workload_categories),
            
            # Cluster context for infrastructure decisions
            'cluster_context': {
                'node_pools': raw_cluster_data.get('node_pools', []),
                'namespaces': raw_cluster_data.get('namespaces', []),
                'existing_hpas': raw_cluster_data.get('existing_hpas', []),
                'cost_analysis': raw_cluster_data.get('cost_analysis', {}),
                'optimization_opportunities': raw_cluster_data.get('optimization_opportunities', [])
            }
        }
        
        return enhanced_input
    
    def _categorize_workloads(self, workloads: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize workloads by cost and resource characteristics"""
        categories = {
            'high_cost': [],           # > $1/month
            'medium_cost': [],         # $0.5 - $1/month  
            'low_cost': [],            # $0.1 - $0.5/month
            'minimal_cost': [],        # < $0.1/month
            'no_resource_requests': [],
            'no_resource_limits': [],
            'zero_usage': [],
            'over_provisioned': []
        }
        
        for workload in workloads:
            monthly_cost = workload.get('cost_estimate', {}).get('monthly_cost', 0.0)
            resources = workload.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            actual_usage = workload.get('actual_usage', {})
            cpu_usage_pct = actual_usage.get('cpu', {}).get('avg_percentage', 0)
            memory_usage_pct = actual_usage.get('memory', {}).get('avg_percentage', 0)
            
            # Cost-based categorization
            if monthly_cost > 1.0:
                categories['high_cost'].append(workload)
            elif monthly_cost > 0.5:
                categories['medium_cost'].append(workload)
            elif monthly_cost > 0.1:
                categories['low_cost'].append(workload)
            else:
                categories['minimal_cost'].append(workload)
            
            # Resource governance issues
            if not requests.get('cpu') and not requests.get('memory'):
                categories['no_resource_requests'].append(workload)
            if not limits.get('cpu') and not limits.get('memory'):
                categories['no_resource_limits'].append(workload)
            
            # Usage-based issues
            if cpu_usage_pct < 5 and memory_usage_pct < 5:
                categories['zero_usage'].append(workload)
            if monthly_cost > 0.5 and (cpu_usage_pct < 30 or memory_usage_pct < 30):
                categories['over_provisioned'].append(workload)
        
        return categories
    
    def _build_workload_summary(self, categories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Build aggregate workload summary for Claude analysis"""
        
        def _calculate_resource_averages(workloads: List[Dict[str, Any]]) -> Dict[str, Any]:
            if not workloads:
                return {}
            
            cpu_requests = []
            memory_requests = []
            monthly_costs = []
            cpu_usages = []
            memory_usages = []
            
            for workload in workloads:
                cost = workload.get('cost_estimate', {}).get('monthly_cost', 0.0)
                monthly_costs.append(cost)
                
                resources = workload.get('resources', {})
                requests = resources.get('requests', {})
                
                # Parse CPU requests
                cpu_req = requests.get('cpu', '0m')
                if isinstance(cpu_req, str) and 'm' in cpu_req:
                    cpu_requests.append(int(cpu_req.replace('m', '')))
                
                # Parse memory requests
                mem_req = requests.get('memory', '0Mi')
                if isinstance(mem_req, str) and 'Mi' in mem_req:
                    memory_requests.append(int(mem_req.replace('Mi', '')))
                
                # Usage percentages
                usage = workload.get('actual_usage', {})
                cpu_usages.append(usage.get('cpu', {}).get('avg_percentage', 0))
                memory_usages.append(usage.get('memory', {}).get('avg_percentage', 0))
            
            return {
                'count': len(workloads),
                'avg_monthly_cost': sum(monthly_costs) / len(monthly_costs) if monthly_costs else 0,
                'total_monthly_cost': sum(monthly_costs),
                'avg_cpu_request_millicores': sum(cpu_requests) / len(cpu_requests) if cpu_requests else 0,
                'avg_memory_request_mb': sum(memory_requests) / len(memory_requests) if memory_requests else 0,
                'avg_cpu_usage_percent': sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0,
                'avg_memory_usage_percent': sum(memory_usages) / len(memory_usages) if memory_usages else 0
            }
        
        return {
            'cost_distribution': {
                'high_cost_workloads': _calculate_resource_averages(categories['high_cost']),
                'medium_cost_workloads': _calculate_resource_averages(categories['medium_cost']),
                'low_cost_workloads': _calculate_resource_averages(categories['low_cost']),
                'minimal_cost_workloads': _calculate_resource_averages(categories['minimal_cost'])
            },
            
            'governance_issues': {
                'no_resource_requests': {
                    'count': len(categories['no_resource_requests']),
                    'total_cost': sum(w.get('cost_estimate', {}).get('monthly_cost', 0) 
                                    for w in categories['no_resource_requests'])
                },
                'no_resource_limits': {
                    'count': len(categories['no_resource_limits']),
                    'total_cost': sum(w.get('cost_estimate', {}).get('monthly_cost', 0) 
                                    for w in categories['no_resource_limits'])
                },
                'zero_usage_workloads': {
                    'count': len(categories['zero_usage']),
                    'total_cost': sum(w.get('cost_estimate', {}).get('monthly_cost', 0) 
                                    for w in categories['zero_usage']),
                    'sample_names': [w.get('name', 'unknown') for w in categories['zero_usage'][:10]]
                },
                'over_provisioned_workloads': {
                    'count': len(categories['over_provisioned']),
                    'total_cost': sum(w.get('cost_estimate', {}).get('monthly_cost', 0) 
                                    for w in categories['over_provisioned']),
                    'avg_cpu_waste': self._calculate_cpu_waste(categories['over_provisioned']),
                    'avg_memory_waste': self._calculate_memory_waste(categories['over_provisioned'])
                }
            },
            
            'optimization_potential': {
                'total_cluster_cost': sum(
                    w.get('cost_estimate', {}).get('monthly_cost', 0) 
                    for category in categories.values() 
                    for w in category
                ),
                'high_impact_workloads': len(categories['high_cost']) + len(categories['medium_cost']),
                'governance_fixes_needed': len(categories['no_resource_requests']) + len(categories['no_resource_limits']),
                'decommission_candidates': len(categories['zero_usage'])
            }
        }
    
    def _calculate_cpu_waste(self, workloads: List[Dict[str, Any]]) -> float:
        """Calculate average CPU waste percentage for over-provisioned workloads"""
        if not workloads:
            return 0.0
        
        waste_percentages = []
        for workload in workloads:
            usage_pct = workload.get('actual_usage', {}).get('cpu', {}).get('avg_percentage', 0)
            if usage_pct < 100:  # Avoid negative waste
                waste_pct = 100 - usage_pct
                waste_percentages.append(waste_pct)
        
        return sum(waste_percentages) / len(waste_percentages) if waste_percentages else 0.0
    
    def _calculate_memory_waste(self, workloads: List[Dict[str, Any]]) -> float:
        """Calculate average memory waste percentage for over-provisioned workloads"""
        if not workloads:
            return 0.0
        
        waste_percentages = []
        for workload in workloads:
            usage_pct = workload.get('actual_usage', {}).get('memory', {}).get('avg_percentage', 0)
            if usage_pct < 100:  # Avoid negative waste
                waste_pct = 100 - usage_pct
                waste_percentages.append(waste_pct)
        
        return sum(waste_percentages) / len(waste_percentages) if waste_percentages else 0.0

def build_enhanced_analysis_input(raw_cluster_data: Dict[str, Any], cost_threshold: float = 1.0) -> Dict[str, Any]:
    """Convenience function to build enhanced analysis input"""
    builder = EnhancedAnalysisDataBuilder(cost_threshold)
    return builder.build_enhanced_analysis_input(raw_cluster_data)

if __name__ == "__main__":
    # Example usage
    print("Enhanced Analysis Data Builder - ready to transform cluster data for optimized Claude analysis")