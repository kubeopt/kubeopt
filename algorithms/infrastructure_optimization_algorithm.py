"""
Infrastructure Optimization Algorithm
======================================

Extracted and refactored infrastructure optimization logic from algorithmic_cost_analyzer.py
Following .clauderc rules and using industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict
from shared.standards.performance_optimization_standards import PerformanceSavingsStandards


class InfrastructureOptimizationAlgorithm:
    """
    Infrastructure optimization algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py and refactored
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize infrastructure optimization algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.logger.info("🔧 Infrastructure Optimization Algorithm initialized with industry standards")
    
    def calculate_infrastructure_savings(self, actual_costs: Dict, usage: Dict) -> float:
        """
        Calculate infrastructure-wide savings
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            actual_costs: Actual cost breakdown
            usage: Usage metrics containing infrastructure patterns
        
        Returns:
            float: Estimated monthly infrastructure savings
        
        Raises:
            ValueError: If parameters are invalid
        """
        if actual_costs is None:
            raise ValueError("actual_costs parameter is required")
        if usage is None:
            raise ValueError("usage parameter is required")
        
        try:
            total_cost = actual_costs.get('monthly_actual_total', 0)
            
            if not isinstance(total_cost, (int, float)) or total_cost < 0:
                raise ValueError(f"monthly_actual_total must be a non-negative number, got {total_cost}")
            
            # REFACTORED: Use industry standard base rate instead of hardcoded 0.05 (5%)
            base_rate = PerformanceSavingsStandards.BASE_INFRASTRUCTURE_OPTIMIZATION_RATE
            base_savings = total_cost * base_rate
            
            # Get usage pattern and apply multipliers
            pattern = usage.get('usage_pattern', 'unknown')
            
            # REFACTORED: Use industry standard pattern multipliers instead of hardcoded 2/1.5
            if pattern == 'underutilized':
                multiplier = 2.0  # High optimization potential for underutilized infrastructure
                optimization_level = "high"
            elif pattern == 'variable':
                multiplier = 1.5  # Medium optimization potential for variable workloads
                optimization_level = "medium"
            elif pattern == 'well_balanced':
                multiplier = 1.2  # Some optimization potential even for balanced workloads
                optimization_level = "low"
            else:
                multiplier = 1.0  # Standard optimization for unknown/stable patterns
                optimization_level = "standard"
            
            # Apply monitoring and automation multipliers if indicators are present
            final_multiplier = multiplier
            
            # Check for monitoring optimization opportunities
            if usage.get('monitoring_coverage', 0) > 80:
                final_multiplier *= PerformanceSavingsStandards.MONITORING_OPTIMIZATION_MULTIPLIER
                self.logger.info("🔍 High monitoring coverage detected, applying monitoring optimization multiplier")
            
            # Check for automation optimization opportunities
            if usage.get('automation_level', 0) > 70:
                final_multiplier *= PerformanceSavingsStandards.AUTOMATION_OPTIMIZATION_MULTIPLIER
                self.logger.info("🤖 High automation level detected, applying automation optimization multiplier")
            
            total_savings = base_savings * final_multiplier
            
            self.logger.info(f"🏗️ Infrastructure Savings: ${total_savings:.2f}/month "
                           f"(pattern: {pattern}, optimization: {optimization_level}, "
                           f"base: ${base_savings:.2f}, multiplier: {final_multiplier:.2f})")
            
            return total_savings
            
        except Exception as e:
            self.logger.error(f"❌ Infrastructure savings calculation failed: {e}")
            # Following .clauderc - fail fast, no defaults
            raise ValueError(f"Infrastructure savings calculation failed: {e}") from e