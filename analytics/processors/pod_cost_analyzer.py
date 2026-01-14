#!/usr/bin/env python3
"""
AKS Pod Cost Analyzer - Enhanced Version
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Analyzes and distributes costs across pods, workloads, and namespaces
using actual resource consumption data.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import yaml

# Import performance standards
try:
    from shared.standards.performance_standards import (
        SystemPerformanceStandards as SysPerf
    )
except ImportError:
    # Standards must be available - fail explicitly
    raise ImportError("Performance standards are required but not found")

logger = logging.getLogger(__name__)

# Azure VM specifications for dynamic detection
AZURE_VM_SPECS = {
    'Standard_B2s': {'cpu_coress': 2, 'memory_gb': 4},
    'Standard_B4ms': {'cpu_coress': 4, 'memory_gb': 16},
    'Standard_D2s_v3': {'cpu_coress': 2, 'memory_gb': 8},
    'Standard_D4s_v3': {'cpu_coress': 4, 'memory_gb': 16},
    'Standard_D8s_v3': {'cpu_coress': 8, 'memory_gb': 32},
    'Standard_D16s_v3': {'cpu_coress': 16, 'memory_gb': 64},
    'Standard_F4s_v2': {'cpu_coress': 4, 'memory_gb': 8},
    'Standard_F8s_v2': {'cpu_coress': 8, 'memory_gb': 16},
    'Standard_E4s_v3': {'cpu_coress': 4, 'memory_gb': 32},
    'Standard_E8s_v3': {'cpu_coress': 8, 'memory_gb': 64}
}


@dataclass
class ResourceMetrics:
    """Resource metrics for pods with consistent naming"""
    cpu_usage_millicores: float = 0.0
    memory_usage_bytes: int = 0
    cpu_request_millicores: float = 0.0
    memory_request_bytes: int = 0
    storage_allocated_bytes: int = 0
    storage_class: str = "standard"
    qos_class: str = "BestEffort"


@dataclass
class CostAllocationResult:
    """Cost allocation result structure"""
    namespace_costs: Dict[str, float]
    workload_costs: Dict[str, Dict]
    pod_costs: Dict[str, float]
    allocation_metadata: Dict
    success: bool = True
    analysis_method: str = "dynamic_allocation"


class KubernetesParsingUtils:
    """Utilities for parsing Kubernetes resource values"""
    
    @staticmethod
    def parse_cpu_safe(cpu_str: str) -> float:
        """Parse CPU string to millicores"""
        if not cpu_str or cpu_str.strip() == '':
            return 0.0
            
        cpu_str = cpu_str.strip().lower()
        
        # Skip non-numeric values
        if not any(c.isdigit() for c in cpu_str):
            return 0.0

        try:
            if cpu_str.endswith('m'):
                return max(0.0, float(cpu_str[:-1]))  # Already in millicores
            elif cpu_str.endswith('u'):
                return max(0.0, float(cpu_str[:-1]) / 1000)  # Microcores to millicores
            elif cpu_str.endswith('n'):
                return max(0.0, float(cpu_str[:-1]) / 1000000)  # Nanocores to millicores
            else:
                return max(0.0, float(cpu_str) * 1000)  # Cores to millicores
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_memory_safe(memory_str: str) -> int:
        """Parse memory string to bytes"""
        if not memory_str or memory_str.strip() == '':
            return 0
            
        memory_str = memory_str.strip()
        
        if not any(c.isdigit() for c in memory_str):
            return 0

        try:
            # Binary units (1024-based)
            if memory_str.endswith('Ki'):
                return max(0, int(float(memory_str[:-2]) * 1024))
            elif memory_str.endswith('Mi'):
                return max(0, int(float(memory_str[:-2]) * 1024 * 1024))
            elif memory_str.endswith('Gi'):
                return max(0, int(float(memory_str[:-2]) * 1024 * 1024 * 1024))
            elif memory_str.endswith('Ti'):
                return max(0, int(float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024))
            # Decimal units (1000-based)
            elif memory_str.endswith('k'):
                return max(0, int(float(memory_str[:-1]) * 1000))
            elif memory_str.endswith('M'):
                return max(0, int(float(memory_str[:-1]) * 1000 * 1000))
            elif memory_str.endswith('G'):
                return max(0, int(float(memory_str[:-1]) * 1000 * 1000 * 1000))
            else:
                return max(0, int(float(memory_str)))  # Assume bytes
        except (ValueError, TypeError):
            return 0


class DynamicCostDistributionEngine:
    """Engine for distributing costs based on actual resource consumption"""

    def __init__(self, resource_group: str, cluster_name: str, subscription_id: str, cache=None):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.subscription_id = subscription_id
        self.parser = KubernetesParsingUtils()
        
        # Use provided cache or create new one
        if cache:
            logger.info(f"Using shared cache instance for pod cost analysis")
            self.cache = cache
        else:
            from shared.kubernetes_data_cache import get_or_create_cache
            logger.info(f"Creating new cache instance for pod cost analysis")
            self.cache = get_or_create_cache(cluster_name, resource_group, subscription_id)
        
        # Cache for expensive operations
        self._instance_type_cache = {}
        self._storage_class_cache = None

    def analyze_pod_costs(self, total_costs: Dict[str, float]) -> Optional[CostAllocationResult]:
        """
        Main analysis method with dynamic cost distribution
        
        Args:
            total_costs: Dictionary with cost breakdown:
                {
                    'node_cost': float,        # Compute costs
                    'storage_cost': float,     # Storage costs
                    'networking_cost': float,  # Networking costs
                    'registry_cost': float,    # Registry costs
                    'monitoring_cost': float   # Monitoring costs
                }
        """
        logger.info(f"Starting pod cost analysis for {self.cluster_name}")
        
        total_cost = sum(total_costs.values())
        logger.info(f"Total costs to distribute: ${total_cost:.2f}")
        
        start_time = time.time()

        try:
            # Step 1: Collect resource data from cache
            resource_data = self._collect_resource_data()
            if not resource_data:
                logger.error("Failed to collect resource data")
                return None
            
            # Step 2: Analyze resource consumption patterns
            consumption_analysis = self._analyze_consumption_patterns(resource_data)
            
            # Step 3: Calculate allocation weights
            allocation_weights = self._calculate_allocation_weights(consumption_analysis)
            
            # Step 4: Distribute costs dynamically
            cost_distribution = self._distribute_costs(
                total_costs, consumption_analysis, allocation_weights
            )
            
            # Step 5: Generate results
            result = self._generate_results(
                cost_distribution, consumption_analysis, total_costs
            )
            
            logger.info(f"Cost analysis completed in {time.time() - start_time:.1f}s")
            logger.info(f"Distributed costs across {len(result.namespace_costs)} namespaces")
            
            return result

        except Exception as e:
            logger.error(f"Pod cost analysis failed: {e}")
            return None

    def _collect_resource_data(self) -> Optional[Dict]:
        """Collect resource data from cache"""
        try:
            logger.info("Collecting resource data from cache...")
            
            # Get all cost analysis data from cache
            cache_data = self.cache.get_cost_analysis_data()
            
            resource_data = {
                'pod_metrics': cache_data.get('pod_usage') or '',
                'pods_text': cache_data.get('pods_running') or '',
                'pvc_text': cache_data.get('pvc_text') or '',
                'services_text': cache_data.get('services_text') or '',
                'nodes': cache_data.get('nodes') or {},
                'storage_classes': cache_data.get('storage_classes') or {}
            }
            
            logger.info("Resource data collection completed")
            return resource_data
            
        except Exception as e:
            logger.error(f"Resource data collection failed: {e}")
            return None

    def _analyze_consumption_patterns(self, resource_data: Dict) -> Dict:
        """Analyze actual resource consumption patterns"""
        logger.info("Analyzing consumption patterns...")
        
        consumption_analysis = {
            'pods': {},
            'namespaces': {},
            'node_capacities': {},
            'storage_allocations': {},
            'networking_usage': {}
        }
        
        # Parse pod metrics (kubectl top pods output)
        pod_metrics = resource_data.get('pod_metrics')
        if pod_metrics is None:
            pod_metrics = ''
        if pod_metrics:
            for line in pod_metrics.split('\n'):
                if line.strip() and not line.startswith('NAMESPACE'):
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        pod_name = parts[1]
                        cpu_str = parts[2]
                        memory_str = parts[3]
                        
                        cpu_millicores = self.parser.parse_cpu_safe(cpu_str)
                        memory_bytes = self.parser.parse_memory_safe(memory_str)
                        
                        pod_key = f"{namespace}/{pod_name}"
                        consumption_analysis['pods'][pod_key] = ResourceMetrics(
                            cpu_usage_millicores=cpu_millicores,
                            memory_usage_bytes=memory_bytes
                        )
        
        # Analyze node capacities
        nodes_data = resource_data.get('nodes')
        if nodes_data is None:
            nodes_data = {}
        if nodes_data and 'items' in nodes_data:
            for node in nodes_data.get('items', []):
                node_name = node.get('metadata', {}).get('name', '')
                if node_name:
                    allocatable = node.get('status', {}).get('allocatable', {})
                    cpu_capacity = self.parser.parse_cpu_safe(allocatable.get('cpu', '0'))
                    memory_capacity = self.parser.parse_memory_safe(allocatable.get('memory', '0'))
                    
                    metadata = node.get('metadata')
                    if metadata:
                        labels = metadata.get('labels')
                        if labels:
                            instance_type = labels.get('node.kubernetes.io/instance-type')
                            if instance_type is None:
                                instance_type = 'unknown'
                        else:
                            instance_type = 'unknown'
                    else:
                        instance_type = 'unknown'
                    
                    consumption_analysis['node_capacities'][node_name] = {
                        'cpu_millicores': cpu_capacity,
                        'memory_bytes': memory_capacity,
                        'instance_type': instance_type
                    }
        
        # Parse PVC allocations
        pvc_text = resource_data.get('pvc_text', '')
        if pvc_text:
            for line in pvc_text.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        namespace = parts[0]
                        capacity = parts[4] if len(parts) > 4 else "10Gi"
                        storage_bytes = self.parser.parse_memory_safe(capacity)
                        
                        if namespace not in consumption_analysis['storage_allocations']:
                            consumption_analysis['storage_allocations'][namespace] = {
                                'total_bytes': 0,
                                'pvc_count': 0
                            }
                        
                        consumption_analysis['storage_allocations'][namespace]['total_bytes'] += storage_bytes
                        consumption_analysis['storage_allocations'][namespace]['pvc_count'] += 1
        
        # Parse services for networking
        services_text = resource_data.get('services_text', '')
        if services_text:
            for line in services_text.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        namespace = parts[0]
                        svc_type = parts[2]
                        
                        if namespace not in consumption_analysis['networking_usage']:
                            consumption_analysis['networking_usage'][namespace] = {
                                'load_balancer_count': 0,
                                'external_service_count': 0
                            }
                        
                        if svc_type == 'LoadBalancer':
                            consumption_analysis['networking_usage'][namespace]['load_balancer_count'] += 1
                            consumption_analysis['networking_usage'][namespace]['external_service_count'] += 1
                        elif svc_type == 'NodePort':
                            consumption_analysis['networking_usage'][namespace]['external_service_count'] += 1
        
        # Aggregate namespace-level consumption
        for pod_key, pod_metrics in consumption_analysis['pods'].items():
            namespace = pod_key.split('/')[0]
            
            if namespace not in consumption_analysis['namespaces']:
                consumption_analysis['namespaces'][namespace] = {
                    'total_cpu_millicores': 0,
                    'total_memory_bytes': 0,
                    'pod_count': 0
                }
            
            consumption_analysis['namespaces'][namespace]['total_cpu_millicores'] += pod_metrics.cpu_usage_millicores
            consumption_analysis['namespaces'][namespace]['total_memory_bytes'] += pod_metrics.memory_usage_bytes
            consumption_analysis['namespaces'][namespace]['pod_count'] += 1
        
        logger.info(f"Consumption analysis completed for {len(consumption_analysis['pods'])} pods")
        return consumption_analysis

    def _calculate_allocation_weights(self, consumption_analysis: Dict) -> Dict:
        """Calculate allocation weights based on consumption"""
        logger.info("Calculating allocation weights...")
        
        allocation_weights = {
            'compute_weights': {},
            'storage_weights': {},
            'networking_weights': {},
            'total_compute_weight': 0,
            'total_storage_weight': 0,
            'total_networking_weight': 0
        }
        
        # Calculate compute weights
        for namespace, ns_data in consumption_analysis['namespaces'].items():
            cpu_weight = ns_data['total_cpu_millicores']
            memory_weight = ns_data['total_memory_bytes'] / (1024 * 1024)  # Convert to MB
            
            # Composite compute weight
            compute_weight = cpu_weight + (memory_weight * 0.1)
            
            allocation_weights['compute_weights'][namespace] = compute_weight
            allocation_weights['total_compute_weight'] += compute_weight
        
        # Calculate storage weights
        for namespace, storage_data in consumption_analysis['storage_allocations'].items():
            storage_weight = storage_data['total_bytes'] / (1024 * 1024 * 1024)  # Convert to GB
            allocation_weights['storage_weights'][namespace] = storage_weight
            allocation_weights['total_storage_weight'] += storage_weight
        
        # Calculate networking weights
        for namespace, network_data in consumption_analysis['networking_usage'].items():
            network_weight = (
                network_data['load_balancer_count'] * 5.0 +
                network_data['external_service_count'] * 2.0
            )
            if network_weight == 0:
                network_weight = 1.0  # Minimum weight
            
            allocation_weights['networking_weights'][namespace] = network_weight
            allocation_weights['total_networking_weight'] += network_weight
        
        logger.info("Allocation weights calculated")
        return allocation_weights

    def _distribute_costs(self, total_costs: Dict[str, float],
                         consumption_analysis: Dict,
                         allocation_weights: Dict) -> Dict:
        """Distribute costs based on weights"""
        logger.info("Distributing costs...")
        
        cost_distribution = {
            'namespace_costs': {},
            'pod_costs': {}
        }
        
        # Get all namespaces
        all_namespaces = set()
        all_namespaces.update(consumption_analysis['namespaces'].keys())
        all_namespaces.update(consumption_analysis['storage_allocations'].keys())
        all_namespaces.update(consumption_analysis['networking_usage'].keys())
        
        # Initialize namespace costs
        for namespace in all_namespaces:
            cost_distribution['namespace_costs'][namespace] = {
                'compute_cost': 0.0,
                'storage_cost': 0.0,
                'networking_cost': 0.0,
                'other_cost': 0.0,
                'total_cost': 0.0
            }
        
        # Distribute compute costs
        node_cost = total_costs.get('node_cost', 0.0)
        if node_cost > 0 and allocation_weights['total_compute_weight'] > 0:
            for namespace in all_namespaces:
                compute_weight = allocation_weights['compute_weights'].get(namespace, 0)
                if compute_weight > 0:
                    compute_allocation = (compute_weight / allocation_weights['total_compute_weight']) * node_cost
                    cost_distribution['namespace_costs'][namespace]['compute_cost'] = compute_allocation
        
        # Distribute storage costs
        storage_cost = total_costs.get('storage_cost', 0.0)
        if storage_cost > 0 and allocation_weights['total_storage_weight'] > 0:
            for namespace in all_namespaces:
                storage_weight = allocation_weights['storage_weights'].get(namespace, 0)
                if storage_weight > 0:
                    storage_allocation = (storage_weight / allocation_weights['total_storage_weight']) * storage_cost
                    cost_distribution['namespace_costs'][namespace]['storage_cost'] = storage_allocation
        elif storage_cost > 0 and len(all_namespaces) > 0:
            # Equal distribution if no storage weights
            per_namespace = storage_cost / len(all_namespaces)
            for namespace in all_namespaces:
                cost_distribution['namespace_costs'][namespace]['storage_cost'] = per_namespace
        
        # Distribute networking costs
        networking_cost = total_costs.get('networking_cost', 0.0)
        if networking_cost > 0 and allocation_weights['total_networking_weight'] > 0:
            for namespace in all_namespaces:
                network_weight = allocation_weights['networking_weights'].get(namespace, 1.0)
                network_allocation = (network_weight / allocation_weights['total_networking_weight']) * networking_cost
                cost_distribution['namespace_costs'][namespace]['networking_cost'] = network_allocation
        elif networking_cost > 0 and len(all_namespaces) > 0:
            # Equal distribution if no networking weights
            per_namespace = networking_cost / len(all_namespaces)
            for namespace in all_namespaces:
                cost_distribution['namespace_costs'][namespace]['networking_cost'] = per_namespace
        
        # Distribute other costs equally
        other_costs = total_costs.get('registry_cost', 0.0) + total_costs.get('monitoring_cost', 0.0)
        if other_costs > 0 and len(all_namespaces) > 0:
            other_per_namespace = other_costs / len(all_namespaces)
            for namespace in all_namespaces:
                cost_distribution['namespace_costs'][namespace]['other_cost'] = other_per_namespace
        
        # Calculate totals
        for namespace in all_namespaces:
            ns_costs = cost_distribution['namespace_costs'][namespace]
            ns_costs['total_cost'] = (
                ns_costs['compute_cost'] +
                ns_costs['storage_cost'] +
                ns_costs['networking_cost'] +
                ns_costs['other_cost']
            )
        
        # Distribute to individual pods
        for pod_key, pod_metrics in consumption_analysis['pods'].items():
            namespace = pod_key.split('/')[0]
            namespace_total = cost_distribution['namespace_costs'].get(namespace, {}).get('total_cost', 0)
            pod_count = consumption_analysis['namespaces'].get(namespace, {}).get('pod_count', 1)
            
            if pod_count > 0:
                cost_distribution['pod_costs'][pod_key] = namespace_total / pod_count
        
        logger.info("Cost distribution completed")
        return cost_distribution

    def _generate_results(self, cost_distribution: Dict,
                         consumption_analysis: Dict,
                         total_costs: Dict[str, float]) -> CostAllocationResult:
        """Generate final results"""
        
        # Convert namespace costs to simple format
        namespace_costs = {}
        for namespace, costs in cost_distribution['namespace_costs'].items():
            namespace_costs[namespace] = costs['total_cost']
        
        # Generate workload costs
        workload_costs = {}
        for pod_key, pod_cost in cost_distribution['pod_costs'].items():
            namespace = pod_key.split('/')[0]
            pod_name = pod_key.split('/')[1]
            
            workload_costs[pod_key] = {
                'cost': pod_cost,
                'type': 'Pod',
                'namespace': namespace,
                'name': pod_name
            }
        
        # Add deployment-level aggregation
        deployment_costs = self._aggregate_to_deployments(workload_costs, consumption_analysis)
        workload_costs.update(deployment_costs)
        
        # Generate metadata
        total_input_cost = sum(total_costs.values())
        total_distributed_cost = sum(namespace_costs.values())
        
        allocation_metadata = {
            'total_input_cost': total_input_cost,
            'total_distributed_cost': total_distributed_cost,
            'distribution_accuracy': (total_distributed_cost / total_input_cost * 100) if total_input_cost > 0 else 0,
            'total_pods_analyzed': len(consumption_analysis['pods']),
            'total_namespaces': len(namespace_costs),
            'analysis_timestamp': datetime.now().isoformat(),
            'method': 'dynamic_allocation',
            'subscription_id': self.subscription_id,
            'features_used': [
                'actual_resource_consumption',
                'dynamic_node_detection',
                'pvc_storage_allocation',
                'service_networking_allocation'
            ]
        }
        
        return CostAllocationResult(
            namespace_costs=namespace_costs,
            workload_costs=workload_costs,
            pod_costs=cost_distribution['pod_costs'],
            allocation_metadata=allocation_metadata,
            success=True,
            analysis_method="dynamic_allocation"
        )
    
    def _aggregate_to_deployments(self, pod_costs: Dict[str, Dict],
                                 consumption_analysis: Dict) -> Dict[str, Dict]:
        """Aggregate pod costs to deployment level"""
        deployment_costs = {}
        
        try:
            # Get deployment data from cache if available
            deployments_data = self.cache.get('deployments') if hasattr(self.cache, 'get') else None
            
            if not deployments_data:
                return deployment_costs
            
            # Parse deployment data
            if isinstance(deployments_data, str):
                deployments_parsed = json.loads(deployments_data)
            elif isinstance(deployments_data, dict):
                deployments_parsed = deployments_data
            else:
                return deployment_costs
            
            deployments = deployments_parsed.get('items', [])
            
            # Create deployment mappings
            for deployment in deployments:
                namespace = deployment.get('metadata', {}).get('namespace', '')
                name = deployment.get('metadata', {}).get('name', '')
                
                if namespace and name:
                    deployment_key = f"{namespace}/{name}"
                    deployment_pods = []
                    
                    # Find pods belonging to this deployment
                    for pod_key in pod_costs.keys():
                        pod_namespace, pod_name = pod_key.split('/', 1)
                        
                        if pod_namespace == namespace and pod_name.startswith(f"{name}-"):
                            deployment_pods.append(pod_key)
                    
                    # Aggregate costs
                    if deployment_pods:
                        total_cost = sum(pod_costs[pk]['cost'] for pk in deployment_pods)
                        deployment_costs[deployment_key] = {
                            'cost': total_cost,
                            'type': 'Deployment',
                            'namespace': namespace,
                            'name': name,
                            'pod_count': len(deployment_pods)
                        }
            
            logger.info(f"Aggregated costs to {len(deployment_costs)} deployments")
            
        except Exception as e:
            logger.error(f"Failed to aggregate deployment costs: {e}")
        
        return deployment_costs


class WorkloadCostAnalyzer:
    """Workload-level cost analysis"""

    def __init__(self, resource_group: str, cluster_name: str, subscription_id: str = None, cache=None):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.subscription_id = subscription_id
        self.cost_engine = DynamicCostDistributionEngine(resource_group, cluster_name, subscription_id, cache)

    def analyze_workload_costs(self, total_costs: Dict[str, float]) -> Optional[Dict]:
        """Analyze workload costs"""
        logger.info(f"Starting workload cost analysis...")
        
        try:
            result = self.cost_engine.analyze_pod_costs(total_costs)
            
            if not result or not result.success:
                logger.warning("Cost analysis failed")
                return None
            
            # Convert to expected format
            return {
                'workload_costs': result.workload_costs,
                'namespace_costs': result.namespace_costs,
                'namespace_summary': result.namespace_costs,
                'analysis_method': result.analysis_method,
                'accuracy_level': 'High',
                'total_pods_analyzed': result.allocation_metadata.get('total_pods_analyzed', 0),
                'total_namespaces': len(result.namespace_costs),
                'subscription_aware': True,
                'features': result.allocation_metadata.get('features_used', [])
            }

        except Exception as e:
            logger.error(f"Workload analysis error: {e}")
            return None


def get_enhanced_pod_cost_breakdown(resource_group: str, cluster_name: str,
                                   total_cost_input: any,
                                   subscription_id: str = None, cache=None) -> Optional[Dict]:
    """
    Main entry point for pod cost analysis
    
    Args:
        resource_group: Azure resource group
        cluster_name: AKS cluster name
        total_cost_input: Either float (node cost) or dict with cost breakdown
        subscription_id: Azure subscription ID
        cache: Optional shared cache instance
    """
    
    # Handle input formats
    if isinstance(total_cost_input, (int, float)):
        total_costs = {'node_cost': float(total_cost_input)}
    elif isinstance(total_cost_input, dict):
        total_costs = total_cost_input
    else:
        logger.error(f"Invalid cost input format: {type(total_cost_input)}")
        return {'success': False, 'error': 'Invalid cost input format'}
    
    if not subscription_id:
        logger.error("subscription_id required for cost distribution")
        return {'success': False, 'error': 'subscription_id required'}
    
    logger.info(f"Pod cost breakdown for {cluster_name}")
    logger.info(f"Total costs: ${sum(total_costs.values()):.2f}")
    
    try:
        # Use workload analyzer
        workload_analyzer = WorkloadCostAnalyzer(resource_group, cluster_name, subscription_id, cache=cache)
        workload_result = workload_analyzer.analyze_workload_costs(total_costs)
        
        if workload_result:
            logger.info("Workload analysis successful")
            return {
                'analysis_type': 'workload_dynamic',
                'success': True,
                'subscription_id': subscription_id,
                'subscription_aware': True,
                'dynamic_allocation': True,
                **workload_result
            }

        # Fallback to basic analysis
        cost_engine = DynamicCostDistributionEngine(resource_group, cluster_name, subscription_id, cache)
        basic_result = cost_engine.analyze_pod_costs(total_costs)
        
        if basic_result and basic_result.success:
            logger.info("Basic analysis successful")
            return {
                'analysis_type': 'pod_dynamic',
                'success': True,
                'subscription_id': subscription_id,
                'subscription_aware': True,
                'dynamic_allocation': True,
                'namespace_costs': basic_result.namespace_costs,
                'allocation_metadata': basic_result.allocation_metadata
            }

        logger.warning("Pod cost analysis failed")
        return {
            'success': False,
            'error': 'Analysis failed',
            'subscription_id': subscription_id
        }

    except Exception as e:
        logger.error(f"Pod cost analysis failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'subscription_id': subscription_id
        }


# Backward compatibility
def get_subscription_aware_pod_cost_breakdown(resource_group: str, cluster_name: str,
                                            total_node_cost: float, subscription_id: str) -> Optional[Dict]:
    """Backward compatibility function"""
    return get_enhanced_pod_cost_breakdown(resource_group, cluster_name, total_node_cost, subscription_id)