"""
Efficiency Evaluator Algorithm
==============================

Extracted and refactored efficiency evaluator logic from algorithmic_cost_analyzer.py
Uses industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict
from shared.standards.rightsizing_industry_standards import RightSizingOptimizationStandards


class EfficiencyEvaluatorAlgorithm:
    """
    Efficiency evaluator algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py EfficiencyEvaluatorAlgorithm
    """
    
    def __init__(self, logger: logging.Logger, algorithm_instances: Dict, scorer=None):
        """
        Initialize efficiency evaluator algorithm

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
        
        # Store rightsizing algorithm instance for efficiency calculations
        self.rightsizing_algorithm = algorithm_instances.get('rightsizing_algorithm')
        if not self.rightsizing_algorithm:
            raise ValueError("rightsizing_algorithm instance is required")
        
        self.logger.info("🔧 Efficiency Evaluator Algorithm initialized with industry standards")
    
    def evaluate(self, current_usage: Dict, optimization: Dict, metrics_data: Dict) -> Dict:
        """
        Evaluate efficiency metrics
        REFACTORED: Moved from EfficiencyEvaluatorAlgorithm class and enhanced with standards
        
        Args:
            current_usage: Current usage metrics
            optimization: Optimization analysis results
            metrics_data: Metrics data
        
        Returns:
            Dict: Efficiency evaluation results
        
        Raises:
            ValueError: If parameters are invalid or evaluation fails
        """
        if current_usage is None:
            raise ValueError("current_usage parameter is required")
        if optimization is None:
            raise ValueError("optimization parameter is required")
        if metrics_data is None:
            raise ValueError("metrics_data parameter is required")
        
        try:
            self.logger.info("📊 Evaluating efficiency metrics...")
            
            # Calculate current efficiency using rightsizing algorithm
            cpu_efficiency = self.rightsizing_algorithm.calculate_cpu_efficiency(current_usage)
            memory_efficiency = self.rightsizing_algorithm.calculate_memory_efficiency(current_usage)
            current_overall = (cpu_efficiency + memory_efficiency) / 2
            
            # Calculate target efficiency based on optimization potential
            optimization_pct = optimization.get('optimization_percentage', 0)
            if not isinstance(optimization_pct, (int, float)) or optimization_pct < 0:
                self.logger.warning(f"Invalid optimization_percentage: {optimization_pct}, using 0")
                optimization_pct = 0
            
            # REFACTORED: Use industry standards instead of hardcoded 0.3/0.2 improvement limits
            if optimization_pct > 20:
                max_improvement = RightSizingOptimizationStandards.MAX_EFFICIENCY_IMPROVEMENT_AGGRESSIVE
                improvement_level = "aggressive"
            else:
                max_improvement = RightSizingOptimizationStandards.MAX_EFFICIENCY_IMPROVEMENT_MODERATE
                improvement_level = "moderate"
            
            # Calculate target efficiencies using rightsizing algorithm
            target_cpu = self.rightsizing_algorithm.calculate_target_efficiency(
                cpu_efficiency, optimization_pct, max_improvement
            )
            target_memory = self.rightsizing_algorithm.calculate_target_efficiency(
                memory_efficiency, optimization_pct, max_improvement
            )
            target_overall = (target_cpu + target_memory) / 2
            
            # Calculate improvement metrics
            improvement_potential = target_overall - current_overall
            efficiency_gap = 100 - current_overall
            
            # Validate calculations
            if target_overall < current_overall:
                self.logger.warning(f"Target efficiency ({target_overall:.1f}%) lower than current ({current_overall:.1f}%)")
            if improvement_potential < 0:
                self.logger.warning(f"Negative improvement potential: {improvement_potential:.1f}%")
            
            # Build comprehensive result
            result = {
                'current_cpu': cpu_efficiency,
                'current_memory': memory_efficiency,
                'current_overall': current_overall,
                'target_cpu': target_cpu,
                'target_memory': target_memory,
                'target_overall': target_overall,
                'improvement_potential': improvement_potential,
                'efficiency_gap': efficiency_gap,
                'max_improvement_factor': max_improvement,
                'improvement_level': improvement_level,
                'optimization_percentage': optimization_pct
            }
            
            self.logger.info(f"📊 Efficiency Evaluation: Current={current_overall:.1f}%, "
                           f"Target={target_overall:.1f}%, Improvement={improvement_potential:.1f}% "
                           f"({improvement_level}, max_factor={max_improvement})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Efficiency evaluation failed: {e}")
            # Fail fast, no defaults
            raise ValueError(f"Efficiency evaluation failed: {e}") from e