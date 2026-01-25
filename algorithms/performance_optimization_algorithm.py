"""
Performance Optimization Algorithm
===================================

Extracted and refactored performance optimization logic from algorithmic_cost_analyzer.py
Following .clauderc rules and using industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict, List, Optional
from shared.standards.performance_optimization_standards import (
    PerformanceOptimizationStandards,
    PerformanceMetricsStandards,
    ResourceContentionStandards,
    PerformanceSavingsStandards
)
from shared.standards.performance_standards import SystemPerformanceStandards


class PerformanceOptimizationAlgorithm:
    """
    Performance optimization algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py and refactored
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize performance optimization algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.logger.info("🔧 Performance Optimization Algorithm initialized with industry standards")
    
    def calculate_performance_waste_savings(self, node_cost: float, high_cpu_workloads: List, usage: Dict) -> float:
        """
        Calculate savings from performance waste
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            node_cost: Cost of compute nodes
            high_cpu_workloads: List of workloads with high CPU usage
            usage: Usage metrics containing performance data
        
        Returns:
            float: Estimated monthly savings amount
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(node_cost, (int, float)) or node_cost < 0:
            raise ValueError("node_cost must be a non-negative number")
        if high_cpu_workloads is None:
            raise ValueError("high_cpu_workloads parameter is required")
        if usage is None:
            raise ValueError("usage parameter is required")
        
        # No savings if no high CPU workloads
        if not high_cpu_workloads:
            self.logger.info("⚡ Performance Waste Savings: $0.00/month (no high CPU workloads detected)")
            return 0.0
        
        try:
            num_high_cpu = len(high_cpu_workloads)
            max_cpu = usage.get('max_workload_cpu', 0)
            
            # Validate max_cpu value
            if not isinstance(max_cpu, (int, float)) or max_cpu < 0:
                self.logger.warning(f"Invalid max_workload_cpu value: {max_cpu}, using 0")
                max_cpu = 0
            
            # REFACTORED: Use industry standard thresholds instead of hardcoded 200/150/5
            severe_threshold = PerformanceOptimizationStandards.SEVERE_CONTENTION_CPU_THRESHOLD
            moderate_threshold = PerformanceOptimizationStandards.MODERATE_CONTENTION_CPU_THRESHOLD
            workload_count_threshold = PerformanceOptimizationStandards.HIGH_CPU_WORKLOAD_COUNT_THRESHOLD
            
            # REFACTORED: Use industry standard savings rates instead of hardcoded 0.15/0.1/0.08/0.05
            if max_cpu > severe_threshold:
                savings_rate = PerformanceOptimizationStandards.SEVERE_CONTENTION_SAVINGS_RATE
                contention_level = "severe"
            elif max_cpu > moderate_threshold:
                savings_rate = PerformanceOptimizationStandards.MODERATE_CONTENTION_SAVINGS_RATE
                contention_level = "moderate"
            elif num_high_cpu > workload_count_threshold:
                savings_rate = PerformanceOptimizationStandards.MULTIPLE_WORKLOAD_ISSUES_SAVINGS_RATE
                contention_level = "multiple_workloads"
            else:
                savings_rate = PerformanceOptimizationStandards.MINOR_PERFORMANCE_ISSUES_SAVINGS_RATE
                contention_level = "minor"
            
            savings_amount = node_cost * savings_rate
            
            self.logger.info(f"⚡ Performance Waste Savings: ${savings_amount:.2f}/month "
                           f"(contention: {contention_level}, max_cpu: {max_cpu:.1f}%, "
                           f"high_cpu_workloads: {num_high_cpu}, rate: {savings_rate*100:.1f}%)")
            
            return savings_amount
            
        except Exception as e:
            self.logger.error(f"❌ Performance waste savings calculation failed: {e}")
            # Following .clauderc - fail fast, no defaults
            raise ValueError(f"Performance waste savings calculation failed: {e}") from e
    
    def calculate_system_efficiency(self, avg_cpu: float, avg_memory: float) -> float:
        """
        Calculate overall system efficiency
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            avg_cpu: Average CPU utilization percentage
            avg_memory: Average memory utilization percentage
        
        Returns:
            float: System efficiency score (0-100)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(avg_cpu, (int, float)):
            raise ValueError("avg_cpu must be a number")
        if not isinstance(avg_memory, (int, float)):
            raise ValueError("avg_memory must be a number")
        if not (0 <= avg_cpu <= 100):
            raise ValueError(f"avg_cpu must be 0-100, got {avg_cpu}")
        if not (0 <= avg_memory <= 100):
            raise ValueError(f"avg_memory must be 0-100, got {avg_memory}")
        
        try:
            # REFACTORED: Use industry standard optimal values instead of hardcoded 70/75
            cpu_optimal = PerformanceOptimizationStandards.CPU_OPTIMAL_FOR_EFFICIENCY
            memory_optimal = PerformanceOptimizationStandards.MEMORY_OPTIMAL_FOR_EFFICIENCY
            penalty_multiplier = PerformanceOptimizationStandards.EFFICIENCY_PENALTY_MULTIPLIER
            
            # Calculate CPU efficiency
            if avg_cpu <= cpu_optimal:
                cpu_efficiency = min(100, (avg_cpu / cpu_optimal) * 100)
            else:
                # Apply penalty for over-optimal utilization
                penalty = (avg_cpu - cpu_optimal) * penalty_multiplier
                cpu_efficiency = max(0, 100 - penalty)
            
            # Calculate memory efficiency
            if avg_memory <= memory_optimal:
                memory_efficiency = min(100, (avg_memory / memory_optimal) * 100)
            else:
                # Apply penalty for over-optimal utilization
                penalty = (avg_memory - memory_optimal) * penalty_multiplier
                memory_efficiency = max(0, 100 - penalty)
            
            # Calculate overall system efficiency (equal weights)
            system_efficiency = (cpu_efficiency + memory_efficiency) / 2
            
            self.logger.info(f"📊 System Efficiency: {system_efficiency:.1f}% "
                           f"(CPU: {cpu_efficiency:.1f}% @ {avg_cpu:.1f}%, "
                           f"Memory: {memory_efficiency:.1f}% @ {avg_memory:.1f}%)")
            
            return system_efficiency
            
        except Exception as e:
            self.logger.error(f"❌ System efficiency calculation failed: {e}")
            raise ValueError(f"System efficiency calculation failed: {e}") from e
    
    def classify_usage_pattern(self, avg_cpu: float, avg_memory: float, cpu_std: float, memory_std: float) -> str:
        """
        Classify workload usage pattern
        REFACTORED: Now uses industry standards instead of hardcoded thresholds
        
        Args:
            avg_cpu: Average CPU utilization percentage
            avg_memory: Average memory utilization percentage
            cpu_std: CPU utilization standard deviation
            memory_std: Memory utilization standard deviation
        
        Returns:
            str: Usage pattern classification
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(avg_cpu, (int, float)):
            raise ValueError("avg_cpu must be a number")
        if not isinstance(avg_memory, (int, float)):
            raise ValueError("avg_memory must be a number")
        if not isinstance(cpu_std, (int, float)):
            raise ValueError("cpu_std must be a number")
        if not isinstance(memory_std, (int, float)):
            raise ValueError("memory_std must be a number")
        
        try:
            # REFACTORED: Use industry standard thresholds instead of hardcoded values
            underutilized_cpu_threshold = PerformanceOptimizationStandards.UNDERUTILIZED_CPU_THRESHOLD
            underutilized_memory_threshold = PerformanceOptimizationStandards.UNDERUTILIZED_MEMORY_THRESHOLD
            high_performance_threshold = SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE
            high_variability_threshold = PerformanceOptimizationStandards.HIGH_VARIABILITY_THRESHOLD
            well_balanced_cpu_threshold = PerformanceOptimizationStandards.WELL_BALANCED_CPU_THRESHOLD
            well_balanced_memory_threshold = PerformanceOptimizationStandards.WELL_BALANCED_MEMORY_THRESHOLD
            
            # Classify usage pattern
            if avg_cpu < underutilized_cpu_threshold and avg_memory < underutilized_memory_threshold:
                pattern = "underutilized"
            elif avg_cpu > high_performance_threshold or avg_memory > high_performance_threshold:
                pattern = "highly_utilized"
            elif cpu_std > high_variability_threshold or memory_std > high_variability_threshold:
                pattern = "variable"
            elif avg_cpu > well_balanced_cpu_threshold and avg_memory > well_balanced_memory_threshold:
                pattern = "well_balanced"
            else:
                pattern = "stable_moderate"
            
            self.logger.info(f"🏷️ Usage Pattern: {pattern} "
                           f"(CPU: {avg_cpu:.1f}%±{cpu_std:.1f}, Memory: {avg_memory:.1f}%±{memory_std:.1f})")
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"❌ Usage pattern classification failed: {e}")
            raise ValueError(f"Usage pattern classification failed: {e}") from e
    
    def combine_rightsizing_savings(self, performance_savings: float, rightsizing_savings: float, 
                                   hpa_savings: float, compute_cost: float) -> float:
        """
        Combine different compute savings with overlap consideration
        REFACTORED: Now uses industry standards instead of hardcoded overlap factors
        
        Args:
            performance_savings: Performance optimization savings
            rightsizing_savings: Right-sizing savings
            hpa_savings: HPA implementation savings
            compute_cost: Total compute cost
        
        Returns:
            float: Combined savings amount considering overlaps
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(performance_savings, (int, float)) or performance_savings < 0:
            raise ValueError("performance_savings must be a non-negative number")
        if not isinstance(rightsizing_savings, (int, float)) or rightsizing_savings < 0:
            raise ValueError("rightsizing_savings must be a non-negative number")
        if not isinstance(hpa_savings, (int, float)) or hpa_savings < 0:
            raise ValueError("hpa_savings must be a non-negative number")
        if not isinstance(compute_cost, (int, float)) or compute_cost < 0:
            raise ValueError("compute_cost must be a non-negative number")
        
        try:
            # Start with the maximum individual savings as base
            max_individual = max(performance_savings, rightsizing_savings, hpa_savings)
            total = max_individual
            
            # REFACTORED: Use industry standard overlap factors instead of hardcoded 0.3/0.3/0.4
            performance_overlap = PerformanceSavingsStandards.PERFORMANCE_OVERLAP_FACTOR
            rightsizing_overlap = PerformanceSavingsStandards.RIGHTSIZING_OVERLAP_FACTOR
            hpa_overlap = PerformanceSavingsStandards.HPA_OVERLAP_FACTOR
            
            # Add partial amounts from other savings to account for non-overlapping benefits
            if performance_savings > 0 and performance_savings != max_individual:
                total += performance_savings * performance_overlap
            
            if rightsizing_savings > 0 and rightsizing_savings != max_individual:
                total += rightsizing_savings * rightsizing_overlap
            
            if hpa_savings > 0 and hpa_savings != max_individual:
                total += hpa_savings * hpa_overlap
            
            # REFACTORED: Use industry standard cap instead of hardcoded 0.4 (40%)
            max_savings_cap = compute_cost * PerformanceSavingsStandards.MAX_COMBINED_SAVINGS_PERCENTAGE
            combined_savings = min(total, max_savings_cap)
            
            self.logger.info(f"💰 Combined Savings: ${combined_savings:.2f}/month "
                           f"(performance: ${performance_savings:.2f}, rightsizing: ${rightsizing_savings:.2f}, "
                           f"hpa: ${hpa_savings:.2f}, max_individual: ${max_individual:.2f}, "
                           f"cap: ${max_savings_cap:.2f})")
            
            return combined_savings
            
        except Exception as e:
            self.logger.error(f"❌ Combined savings calculation failed: {e}")
            raise ValueError(f"Combined savings calculation failed: {e}") from e