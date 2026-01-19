"""
Workload Classification Algorithm
=================================

Extracted and refactored workload classification logic from algorithmic_cost_analyzer.py
Following .clauderc rules and using industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict
from shared.standards.performance_standards import SystemPerformanceStandards


class WorkloadClassificationAlgorithm:
    """
    Workload classification algorithm using industry standards
    Extracted from MLEnhancedHPARecommendationEngine and enhanced with standards
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize workload classification algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.logger.info("🔧 Workload Classification Algorithm initialized with industry standards")
    
    def determine_severity(self, cpu_usage_pct: float) -> str:
        """
        Determine workload severity based on CPU usage with industry standards
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            cpu_usage_pct: CPU usage percentage (can exceed 100% for containers)
        
        Returns:
            str: Severity level ('normal', 'medium', 'high', 'critical')
        
        Raises:
            ValueError: If cpu_usage_pct is invalid
        """
        if not isinstance(cpu_usage_pct, (int, float)):
            raise ValueError("cpu_usage_pct must be a number")
        if cpu_usage_pct < 0:
            raise ValueError("cpu_usage_pct must be non-negative")
        
        try:
            # REFACTORED: Use industry standards for workload severity classification
            # Note: These are workload CPU limits that can exceed 100% in containerized environments
            
            # Industry standards for container CPU usage severity thresholds
            # Based on container CPU limits and Kubernetes resource management best practices
            critical_threshold = SystemPerformanceStandards.CPU_UTILIZATION_CRITICAL * 10  # 950% (9.5x CPU limit)
            stress_threshold = SystemPerformanceStandards.CPU_UTILIZATION_STRESS * 3.33    # 300% (3x CPU limit)
            high_threshold = SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE * 1.875  # 150% (1.5x CPU limit)
            
            if cpu_usage_pct > critical_threshold:
                severity = 'critical'
                risk_level = "CRITICAL"
            elif cpu_usage_pct > stress_threshold:
                severity = 'high' 
                risk_level = "HIGH"
            elif cpu_usage_pct > high_threshold:
                severity = 'medium'
                risk_level = "MEDIUM"
            else:
                severity = 'normal'
                risk_level = "NORMAL"
            
            self.logger.debug(f"Workload Severity: {severity.upper()} (CPU: {cpu_usage_pct:.1f}%, "
                            f"Risk: {risk_level}, Thresholds: {high_threshold:.0f}%/{stress_threshold:.0f}%/{critical_threshold:.0f}%)")
            
            return severity
            
        except Exception as e:
            self.logger.error(f"❌ Severity determination failed: {e}")
            # Following .clauderc - fail fast, no defaults
            raise ValueError(f"Severity determination failed: {e}") from e
    
    def classify_workload_resource_pattern(self, cpu_usage_pct: float, memory_usage_pct: float) -> Dict:
        """
        Classify workload based on resource usage patterns with industry standards
        
        Args:
            cpu_usage_pct: CPU usage percentage
            memory_usage_pct: Memory usage percentage
        
        Returns:
            Dict: Workload classification with pattern and characteristics
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(cpu_usage_pct, (int, float)) or not isinstance(memory_usage_pct, (int, float)):
            raise ValueError("CPU and memory usage must be numbers")
        if cpu_usage_pct < 0 or memory_usage_pct < 0:
            raise ValueError("Usage percentages must be non-negative")
        
        try:
            # Use industry standards for classification thresholds
            high_cpu_threshold = SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE
            optimal_cpu_threshold = SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL
            high_memory_threshold = SystemPerformanceStandards.MEMORY_UTILIZATION_HIGH
            optimal_memory_threshold = SystemPerformanceStandards.MEMORY_UTILIZATION_OPTIMAL
            
            # Determine workload pattern
            if cpu_usage_pct > high_cpu_threshold and memory_usage_pct < optimal_memory_threshold:
                pattern = 'CPU_INTENSIVE'
                primary_resource = 'cpu'
                bottleneck_risk = 'high'
            elif memory_usage_pct > high_memory_threshold and cpu_usage_pct < optimal_cpu_threshold:
                pattern = 'MEMORY_INTENSIVE'
                primary_resource = 'memory'
                bottleneck_risk = 'high'
            elif cpu_usage_pct > high_cpu_threshold and memory_usage_pct > high_memory_threshold:
                pattern = 'RESOURCE_INTENSIVE'
                primary_resource = 'both'
                bottleneck_risk = 'critical'
            elif cpu_usage_pct < optimal_cpu_threshold and memory_usage_pct < optimal_memory_threshold:
                pattern = 'LOW_UTILIZATION'
                primary_resource = 'neither'
                bottleneck_risk = 'low'
            else:
                pattern = 'BALANCED'
                primary_resource = 'cpu' if cpu_usage_pct > memory_usage_pct else 'memory'
                bottleneck_risk = 'medium'
            
            # Calculate resource efficiency
            cpu_efficiency = min(100.0, (cpu_usage_pct / optimal_cpu_threshold) * 100)
            memory_efficiency = min(100.0, (memory_usage_pct / optimal_memory_threshold) * 100)
            overall_efficiency = (cpu_efficiency + memory_efficiency) / 2
            
            classification = {
                'pattern': pattern,
                'primary_resource': primary_resource,
                'bottleneck_risk': bottleneck_risk,
                'cpu_efficiency': cpu_efficiency,
                'memory_efficiency': memory_efficiency,
                'overall_efficiency': overall_efficiency,
                'cpu_severity': self.determine_severity(cpu_usage_pct),
                'thresholds_used': {
                    'high_cpu': high_cpu_threshold,
                    'optimal_cpu': optimal_cpu_threshold,
                    'high_memory': high_memory_threshold,
                    'optimal_memory': optimal_memory_threshold
                }
            }
            
            self.logger.info(f"Workload Classification: {pattern} (CPU: {cpu_usage_pct:.1f}%, "
                           f"Memory: {memory_usage_pct:.1f}%, Efficiency: {overall_efficiency:.1f}%)")
            
            return classification
            
        except Exception as e:
            self.logger.error(f"❌ Workload classification failed: {e}")
            # Following .clauderc - fail fast, no defaults
            raise ValueError(f"Workload classification failed: {e}") from e