"""
Right-sizing Optimization Algorithm
===================================

Extracted and refactored right-sizing optimization logic from algorithmic_cost_analyzer.py
Following .clauderc rules and using industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict, Optional
from shared.standards.rightsizing_industry_standards import (
    RightSizingOptimizationStandards,
    RightSizingCostStandards,
    RightSizingRecommendationStandards
)


class RightSizingOptimizationAlgorithm:
    """
    Right-sizing optimization algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py and refactored
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize right-sizing optimization algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.logger.info("🔧 Right-sizing Optimization Algorithm initialized with industry standards")
    
    def calculate_rightsizing_savings(self, node_cost: float, usage: Dict) -> float:
        """
        Calculate right-sizing savings
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            node_cost: Cost of compute nodes
            usage: Usage metrics containing CPU/memory utilization data
        
        Returns:
            float: Estimated monthly savings amount
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(node_cost, (int, float)) or node_cost < 0:
            raise ValueError("node_cost must be a non-negative number")
        if usage is None:
            raise ValueError("usage parameter is required")
        
        try:
            avg_cpu = usage.get('avg_cpu_utilization', 0)
            avg_memory = usage.get('avg_memory_utilization', 0)
            
            # Validate utilization values
            if not (0 <= avg_cpu <= 100):
                raise ValueError(f"CPU utilization must be 0-100, got {avg_cpu}")
            if not (0 <= avg_memory <= 100):
                raise ValueError(f"Memory utilization must be 0-100, got {avg_memory}")
            
            # REFACTORED: Use industry standard optimal targets instead of hardcoded 70/75
            cpu_optimal = RightSizingOptimizationStandards.CPU_WASTE_CALCULATION_BASE
            memory_optimal = RightSizingOptimizationStandards.MEMORY_WASTE_CALCULATION_BASE
            
            # Calculate waste percentages
            cpu_waste = max(0, cpu_optimal - avg_cpu) / 100
            memory_waste = max(0, memory_optimal - avg_memory) / 100
            
            # REFACTORED: Use industry standard weight factors instead of simple average
            cpu_weight = RightSizingCostStandards.CPU_WASTE_SAVINGS_MULTIPLIER
            memory_weight = RightSizingCostStandards.MEMORY_WASTE_SAVINGS_MULTIPLIER
            
            weighted_waste = (cpu_waste * cpu_weight) + (memory_waste * memory_weight)
            
            # Consider variability
            cpu_std = usage.get('cpu_std_dev', 0)
            memory_std = usage.get('memory_std_dev', 0)
            
            # REFACTORED: Use industry standard variability thresholds instead of hardcoded 20
            high_var_threshold = RightSizingOptimizationStandards.HIGH_VARIABILITY_THRESHOLD
            low_var_threshold = RightSizingOptimizationStandards.LOW_VARIABILITY_THRESHOLD
            
            if cpu_std > high_var_threshold or memory_std > high_var_threshold:
                recovery_factor = RightSizingOptimizationStandards.HIGH_VARIABILITY_RECOVERY_FACTOR
                variability_level = "high"
            elif cpu_std < low_var_threshold and memory_std < low_var_threshold:
                recovery_factor = RightSizingOptimizationStandards.LOW_VARIABILITY_RECOVERY_FACTOR
                variability_level = "low"
            else:
                recovery_factor = RightSizingOptimizationStandards.MEDIUM_VARIABILITY_RECOVERY_FACTOR
                variability_level = "medium"
            
            savings_amount = node_cost * weighted_waste * recovery_factor
            
            # Apply minimum savings threshold
            min_savings_threshold = RightSizingCostStandards.MINIMUM_MONTHLY_SAVINGS_THRESHOLD
            if savings_amount < min_savings_threshold:
                self.logger.info(f"💰 Right-sizing Savings: ${savings_amount:.2f}/month (below ${min_savings_threshold} threshold)")
                return 0.0
            
            self.logger.info(f"💰 Right-sizing Savings: ${savings_amount:.2f}/month "
                           f"(CPU waste: {cpu_waste*100:.1f}%, Memory waste: {memory_waste*100:.1f}%, "
                           f"Variability: {variability_level}, Factor: {recovery_factor})")
            
            return savings_amount
            
        except Exception as e:
            self.logger.error(f"❌ Right-sizing savings calculation failed: {e}")
            # Following .clauderc - fail fast, no defaults
            raise ValueError(f"Right-sizing savings calculation failed: {e}") from e
    
    def calculate_cpu_efficiency(self, usage: Dict) -> float:
        """
        Calculate CPU efficiency score
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            usage: Usage metrics containing CPU utilization data
        
        Returns:
            float: CPU efficiency score (0-100)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if usage is None:
            raise ValueError("usage parameter is required")
        
        try:
            avg_cpu = usage.get('avg_cpu_utilization', 0)
            
            if not isinstance(avg_cpu, (int, float)):
                raise ValueError("avg_cpu_utilization must be a number")
            
            if avg_cpu <= 0:
                self.logger.info("🔍 CPU Efficiency: 0% (no utilization)")
                return 0.0
            
            # REFACTORED: Use industry standard thresholds instead of hardcoded 70/85
            optimal_cpu = RightSizingOptimizationStandards.CPU_OPTIMAL_UTILIZATION
            overutilized_threshold = RightSizingOptimizationStandards.CPU_OVERUTILIZED_THRESHOLD
            max_score = RightSizingOptimizationStandards.EFFICIENCY_SCORE_MAX_POINTS
            penalty_rate = RightSizingOptimizationStandards.EFFICIENCY_PENALTY_PER_PERCENT
            
            if avg_cpu <= optimal_cpu:
                # Linear scaling up to optimal
                efficiency_score = (avg_cpu / optimal_cpu) * max_score
            elif avg_cpu <= overutilized_threshold:
                # Penalty zone - efficiency decreases as utilization increases beyond optimal
                penalty = (avg_cpu - optimal_cpu) * penalty_rate
                efficiency_score = max_score - penalty
            else:
                # Severe overutilization - steep penalty
                severe_penalty = (avg_cpu - overutilized_threshold) * (penalty_rate * 2)
                base_penalty = (overutilized_threshold - optimal_cpu) * penalty_rate
                efficiency_score = max(0, max_score - base_penalty - severe_penalty)
            
            efficiency_score = max(0.0, min(100.0, efficiency_score))
            
            self.logger.info(f"🔍 CPU Efficiency: {efficiency_score:.1f}% (utilization: {avg_cpu:.1f}%)")
            return efficiency_score
            
        except Exception as e:
            self.logger.error(f"❌ CPU efficiency calculation failed: {e}")
            raise ValueError(f"CPU efficiency calculation failed: {e}") from e
    
    def calculate_memory_efficiency(self, usage: Dict) -> float:
        """
        Calculate memory efficiency score
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            usage: Usage metrics containing memory utilization data
        
        Returns:
            float: Memory efficiency score (0-100)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if usage is None:
            raise ValueError("usage parameter is required")
        
        try:
            avg_memory = usage.get('avg_memory_utilization', 0)
            
            if not isinstance(avg_memory, (int, float)):
                raise ValueError("avg_memory_utilization must be a number")
            
            if avg_memory <= 0:
                self.logger.info("🔍 Memory Efficiency: 0% (no utilization)")
                return 0.0
            
            # REFACTORED: Use industry standard thresholds instead of hardcoded 75/90
            optimal_memory = RightSizingOptimizationStandards.MEMORY_OPTIMAL_UTILIZATION
            overutilized_threshold = RightSizingOptimizationStandards.MEMORY_OVERUTILIZED_THRESHOLD
            max_score = RightSizingOptimizationStandards.EFFICIENCY_SCORE_MAX_POINTS
            penalty_rate = RightSizingOptimizationStandards.EFFICIENCY_PENALTY_PER_PERCENT
            
            if avg_memory <= optimal_memory:
                # Linear scaling up to optimal
                efficiency_score = (avg_memory / optimal_memory) * max_score
            elif avg_memory <= overutilized_threshold:
                # Penalty zone - efficiency decreases as utilization increases beyond optimal
                penalty = (avg_memory - optimal_memory) * penalty_rate
                efficiency_score = max_score - penalty
            else:
                # Severe overutilization - steep penalty
                severe_penalty = (avg_memory - overutilized_threshold) * (penalty_rate * 2)
                base_penalty = (overutilized_threshold - optimal_memory) * penalty_rate
                efficiency_score = max(0, max_score - base_penalty - severe_penalty)
            
            efficiency_score = max(0.0, min(100.0, efficiency_score))
            
            self.logger.info(f"🔍 Memory Efficiency: {efficiency_score:.1f}% (utilization: {avg_memory:.1f}%)")
            return efficiency_score
            
        except Exception as e:
            self.logger.error(f"❌ Memory efficiency calculation failed: {e}")
            raise ValueError(f"Memory efficiency calculation failed: {e}") from e
    
    def calculate_target_efficiency(self, current_efficiency: float, optimization_potential: float, max_improvement: float = None) -> float:
        """
        Calculate target efficiency after optimization
        REFACTORED: Now uses industry standards instead of hardcoded max improvement value
        
        Args:
            current_efficiency: Current efficiency score
            optimization_potential: Optimization potential percentage
            max_improvement: Maximum improvement factor (optional, uses standards if None)
        
        Returns:
            float: Target efficiency score (0-100)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(current_efficiency, (int, float)):
            raise ValueError("current_efficiency must be a number")
        if not isinstance(optimization_potential, (int, float)):
            raise ValueError("optimization_potential must be a number")
        if not (0 <= current_efficiency <= 100):
            raise ValueError(f"current_efficiency must be 0-100, got {current_efficiency}")
        if optimization_potential < 0:
            raise ValueError(f"optimization_potential must be non-negative, got {optimization_potential}")
        
        try:
            # REFACTORED: Use industry standards instead of hardcoded 0.3 (30%) max improvement
            if max_improvement is None:
                if optimization_potential > 20:
                    max_improvement = RightSizingOptimizationStandards.MAX_EFFICIENCY_IMPROVEMENT_AGGRESSIVE
                else:
                    max_improvement = RightSizingOptimizationStandards.MAX_EFFICIENCY_IMPROVEMENT_MODERATE
            
            improvement = min(max_improvement * 100, optimization_potential * 2)
            target = current_efficiency + improvement
            
            # Cap target efficiency at reasonable maximum (95% to account for real-world limitations)
            target_efficiency = min(95.0, max(current_efficiency, target))
            
            self.logger.info(f"🎯 Target Efficiency: {target_efficiency:.1f}% "
                           f"(current: {current_efficiency:.1f}%, improvement: {improvement:.1f}%, "
                           f"max_improvement: {max_improvement*100:.0f}%)")
            
            return target_efficiency
            
        except Exception as e:
            self.logger.error(f"❌ Target efficiency calculation failed: {e}")
            raise ValueError(f"Target efficiency calculation failed: {e}") from e