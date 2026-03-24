"""
Usage Analysis Algorithm
========================

Extracted and refactored current usage analysis logic from algorithmic_cost_analyzer.py
Uses industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
import numpy as np
from typing import Dict, Optional
from shared.standards.performance_standards import SystemPerformanceStandards
from shared.standards.performance_optimization_standards import PerformanceOptimizationStandards


class UsageAnalysisAlgorithm:
    """
    Usage analysis algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py CurrentUsageAnalysisAlgorithm
    """
    
    def __init__(self, logger: logging.Logger, algorithm_instances: Dict, scorer=None):
        """
        Initialize usage analysis algorithm

        Args:
            logger: Logger instance (required, no default)
            algorithm_instances: Dictionary of algorithm instances
            scorer: Cluster scorer instance (optional)

        Raises:
            ValueError: If logger or algorithm_instances is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        if algorithm_instances is None:
            raise ValueError("algorithm_instances parameter is required")

        self.logger = logger
        self.scorer = scorer
        
        # Store algorithm instances for calculations
        self.hpa_algorithm = algorithm_instances.get('hpa_algorithm')
        self.performance_algorithm = algorithm_instances.get('performance_algorithm')
        
        # Validate required algorithms are present
        if not self.hpa_algorithm:
            raise ValueError("hpa_algorithm instance is required")
        if not self.performance_algorithm:
            raise ValueError("performance_algorithm instance is required")
        
        self.logger.info("🔧 Usage Analysis Algorithm initialized with industry standards")
    
    def analyze(self, metrics_data: Dict, pod_data: Dict = None) -> Dict:
        """
        Analyze current usage with consistent naming
        REFACTORED: Moved from CurrentUsageAnalysisAlgorithm class and enhanced with standards
        
        Args:
            metrics_data: Metrics data containing node information
            pod_data: Pod data (optional)
        
        Returns:
            Dict: Current usage analysis results
        
        Raises:
            ValueError: If parameters are invalid or analysis fails
        """
        if metrics_data is None:
            raise ValueError("metrics_data parameter is required")
        
        try:
            self.logger.info("🔍 Analyzing current usage patterns...")
            
            nodes = metrics_data.get('nodes')
            
            # DEBUG: Log what nodes data we received
            self.logger.info(f"🔍 DEBUG ANALYZER: Received nodes data:")
            self.logger.info(f"🔍 DEBUG ANALYZER: nodes type: {type(nodes)}")
            self.logger.info(f"🔍 DEBUG ANALYZER: nodes count: {len(nodes) if nodes else 0}")
            
            if nodes and len(nodes) > 0:
                for i, node in enumerate(nodes[:2]):  # Show first 2 nodes
                    cpu_pct = node.get('cpu_usage_pct', 'MISSING')
                    try:
                        node_name = node.get('name', 'UNKNOWN')
                        self.logger.info(f"🔍 DEBUG ANALYZER: nodes[{i}] = name: {node_name}, cpu_usage_pct: {cpu_pct}")
                    except Exception as e:
                        self.logger.info(f"🔍 DEBUG ANALYZER: nodes[{i}] access error: {e}, cpu_usage_pct: {cpu_pct}")
                        if hasattr(node, 'keys'):
                            self.logger.info(f"🔍 DEBUG ANALYZER: node[{i}] keys: {list(node.keys())}")
            else:
                self.logger.warning("🔍 DEBUG ANALYZER: nodes is empty or None!")
            
            # Validate nodes data
            if nodes is None:
                raise ValueError("nodes is required in metrics_data")
            if not nodes:
                raise ValueError("No node data available for analysis")
            
            # Extract CPU and memory values with validation
            cpu_values = []
            memory_values = []
            
            for i, node in enumerate(nodes):
                if 'cpu_usage_pct' not in node:
                    raise ValueError(f"Node {i} missing 'cpu_usage_pct' field")
                if 'memory_usage_pct' not in node:
                    raise ValueError(f"Node {i} missing 'memory_usage_pct' field")
                
                cpu = node['cpu_usage_pct']
                memory = node['memory_usage_pct']
                
                # Validate data types
                if not isinstance(cpu, (int, float)):
                    raise ValueError(f"Node {i} cpu_usage_pct must be numeric, got {type(cpu).__name__}")
                if not isinstance(memory, (int, float)):
                    raise ValueError(f"Node {i} memory_usage_pct must be numeric, got {type(memory).__name__}")
                
                cpu_values.append(cpu)
                memory_values.append(memory)
            
            if not cpu_values or not memory_values:
                raise ValueError("No valid usage data available")
            
            # Calculate statistics - STANDARDIZED FIELD NAMES
            avg_cpu = np.mean(cpu_values)
            avg_memory = np.mean(memory_values)
            cpu_std = np.std(cpu_values) if len(cpu_values) > 1 else 0
            memory_std = np.std(memory_values) if len(memory_values) > 1 else 0
            
            result = {
                'avg_cpu_utilization': avg_cpu,
                'avg_memory_utilization': avg_memory,
                'max_cpu_utilization': max(cpu_values),
                'max_memory_utilization': max(memory_values),
                'min_cpu_utilization': min(cpu_values),
                'min_memory_utilization': min(memory_values),
                'cpu_std_dev': cpu_std,
                'memory_std_dev': memory_std,
                'cpu_variance': np.var(cpu_values) if len(cpu_values) > 1 else 0,
                'memory_variance': np.var(memory_values) if len(memory_values) > 1 else 0,
                'node_count': len(nodes)
            }
            
            # Classify usage pattern using performance algorithm
            result['usage_pattern'] = self.performance_algorithm.classify_usage_pattern(
                avg_cpu, avg_memory, cpu_std, memory_std
            )
            
            # Calculate optimization potential
            result['cpu_optimization_potential'] = self._calculate_cpu_optimization_potential(avg_cpu, cpu_std)
            result['memory_optimization_potential'] = self._calculate_memory_optimization_potential(avg_memory, memory_std)
            
            # Calculate HPA suitability using HPA algorithm
            result['hpa_suitability'] = self.hpa_algorithm.calculate_hpa_suitability(
                cpu_std, memory_std, len(nodes)
            )
            
            # Calculate system efficiency using performance algorithm
            result['system_efficiency'] = self.performance_algorithm.calculate_system_efficiency(
                avg_cpu, avg_memory
            )
            
            # Extract high CPU workloads - REQUIRED by design
            if 'top_cpu_summary' not in metrics_data:
                raise ValueError("top_cpu_summary missing from metrics_data - required for usage analysis")
            
            top_cpu_summary = metrics_data['top_cpu_summary']
            
            # Extract workloads - use all_workloads (new field name)
            if 'all_workloads' in top_cpu_summary:
                result['high_cpu_workloads'] = top_cpu_summary['all_workloads']
            else:
                result['high_cpu_workloads'] = []
            
            # Extract max CPU
            if 'max_cpu_utilization' in top_cpu_summary:
                result['max_workload_cpu'] = top_cpu_summary['max_cpu_utilization']
            else:
                raise ValueError("max_cpu_utilization missing from top_cpu_summary")
            
            self.logger.info(f"🔍 Usage Analysis: CPU={avg_cpu:.1f}%±{cpu_std:.1f}, "
                           f"Memory={avg_memory:.1f}%±{memory_std:.1f}, Pattern={result['usage_pattern']}, "
                           f"HPA Suitability={result['hpa_suitability']:.1f}%")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Current usage analysis failed: {e}")
            # Fail fast, no defaults
            raise ValueError(f"Current usage analysis failed: {e}") from e
    
    def _calculate_cpu_optimization_potential(self, avg_cpu: float, cpu_std: float) -> float:
        """
        Calculate CPU optimization potential
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            avg_cpu: Average CPU utilization percentage
            cpu_std: CPU utilization standard deviation
        
        Returns:
            float: CPU optimization potential (0-100)
        """
        try:
            # REFACTORED: Use industry standard optimal CPU instead of hardcoded 70
            optimal_cpu = SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL
            
            if avg_cpu >= optimal_cpu:
                return 0.0  # Well utilized, no optimization potential
            
            # Calculate waste percentage
            waste_pct = (optimal_cpu - avg_cpu) / optimal_cpu
            
            # REFACTORED: Use industry standard variability threshold instead of hardcoded 20
            high_variability_threshold = PerformanceOptimizationStandards.HIGH_VARIABILITY_THRESHOLD
            
            if cpu_std > high_variability_threshold:
                # High variability increases optimization potential
                multiplier = 1.5
                variability_level = "high"
            else:
                multiplier = 1.0
                variability_level = "low"
            
            optimization_potential = min(100.0, waste_pct * 100 * multiplier)
            
            self.logger.debug(f"CPU Optimization Potential: {optimization_potential:.1f}% "
                            f"(avg: {avg_cpu:.1f}%, optimal: {optimal_cpu}%, "
                            f"variability: {variability_level}, std: {cpu_std:.1f})")
            
            return optimization_potential
            
        except Exception as e:
            self.logger.error(f"❌ CPU optimization potential calculation failed: {e}")
            raise ValueError(f"CPU optimization potential calculation failed: {e}") from e
    
    def _calculate_memory_optimization_potential(self, avg_memory: float, memory_std: float) -> float:
        """
        Calculate memory optimization potential
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            avg_memory: Average memory utilization percentage
            memory_std: Memory utilization standard deviation
        
        Returns:
            float: Memory optimization potential (0-100)
        """
        try:
            # REFACTORED: Use industry standard optimal memory instead of hardcoded 75
            optimal_memory = SystemPerformanceStandards.MEMORY_UTILIZATION_OPTIMAL
            
            if avg_memory >= optimal_memory:
                return 0.0  # Well utilized, no optimization potential
            
            # Calculate waste percentage
            waste_pct = (optimal_memory - avg_memory) / optimal_memory
            
            # REFACTORED: Use industry standard variability threshold instead of hardcoded 20
            high_variability_threshold = PerformanceOptimizationStandards.HIGH_VARIABILITY_THRESHOLD
            
            if memory_std > high_variability_threshold:
                # High variability increases optimization potential
                multiplier = 1.5
                variability_level = "high"
            else:
                multiplier = 1.0
                variability_level = "low"
            
            optimization_potential = min(100.0, waste_pct * 100 * multiplier)
            
            self.logger.debug(f"Memory Optimization Potential: {optimization_potential:.1f}% "
                            f"(avg: {avg_memory:.1f}%, optimal: {optimal_memory}%, "
                            f"variability: {variability_level}, std: {memory_std:.1f})")
            
            return optimization_potential
            
        except Exception as e:
            self.logger.error(f"❌ Memory optimization potential calculation failed: {e}")
            raise ValueError(f"Memory optimization potential calculation failed: {e}") from e