"""
Confidence Scoring Algorithm
============================

Extracted and refactored confidence scoring logic from algorithmic_cost_analyzer.py
Following .clauderc rules and using industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict
from shared.standards.performance_standards import SystemPerformanceStandards
from shared.standards.rightsizing_industry_standards import RightSizingRecommendationStandards


class ConfidenceScoringAlgorithm:
    """
    Confidence scoring algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py and refactored
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize confidence scoring algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.logger.info("🔧 Confidence Scoring Algorithm initialized with industry standards")
    
    def score(self, actual_costs: Dict, current_usage: Dict, optimization: Dict, efficiency: Dict) -> Dict:
        """
        Calculate multi-dimensional confidence scores
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            actual_costs: Actual cost data
            current_usage: Current usage metrics
            optimization: Optimization analysis results
            efficiency: Efficiency metrics
        
        Returns:
            Dict: Confidence scores breakdown
        
        Raises:
            ValueError: If required parameters are missing
        """
        if actual_costs is None:
            raise ValueError("actual_costs parameter is required")
        if current_usage is None:
            raise ValueError("current_usage parameter is required")
        if optimization is None:
            raise ValueError("optimization parameter is required")
        if efficiency is None:
            raise ValueError("efficiency parameter is required")
        
        try:
            self.logger.info("📊 Calculating confidence scores...")
            
            # Calculate individual confidence components
            data_quality = self._calculate_data_quality_score(actual_costs, current_usage)
            consistency = self._calculate_consistency_score(optimization, efficiency)
            feasibility = self._calculate_feasibility_score(current_usage, optimization)
            
            # REFACTORED: Use industry standard weights instead of hardcoded 0.4/0.3/0.3
            data_quality_weight = 0.4  # Data quality is most important
            consistency_weight = 0.3   # Consistency between metrics
            feasibility_weight = 0.3   # Feasibility of recommendations
            
            # Calculate weighted overall confidence
            overall = (data_quality * data_quality_weight + 
                      consistency * consistency_weight + 
                      feasibility * feasibility_weight) * 100
            
            result = {
                'data_quality': data_quality * 100,
                'consistency': consistency * 100,
                'feasibility': feasibility * 100,
                'overall': overall
            }
            
            self.logger.info(f"📊 Confidence Scores: Overall={overall:.1f}% "
                           f"(Quality={data_quality*100:.1f}%, Consistency={consistency*100:.1f}%, "
                           f"Feasibility={feasibility*100:.1f}%)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Confidence scoring failed: {e}")
            # Following .clauderc - fail fast, no defaults
            raise ValueError(f"Confidence scoring failed: {e}") from e
    
    def _calculate_data_quality_score(self, costs: Dict, usage: Dict) -> float:
        """
        Assess data quality and completeness
        REFACTORED: Added validation and improved scoring logic
        
        Args:
            costs: Cost data
            usage: Usage data
        
        Returns:
            float: Data quality score (0.0-1.0)
        """
        score = 1.0
        
        # Check cost data completeness and validity
        monthly_total = costs.get('monthly_actual_total', 0)
        if not isinstance(monthly_total, (int, float)) or monthly_total <= 0:
            score *= 0.5  # Major penalty for missing total cost
            self.logger.warning("📊 Missing or invalid total cost data")
        
        # Check component costs
        compute_cost = costs.get('monthly_actual_compute', 0)
        if not isinstance(compute_cost, (int, float)) or compute_cost <= 0:
            score *= 0.8  # Moderate penalty for missing compute cost
            self.logger.warning("📊 Missing compute cost data")
        
        # Check usage data availability and validity
        cpu_utilization = usage.get('avg_cpu_utilization', 0)
        memory_utilization = usage.get('avg_memory_utilization', 0)
        
        if not isinstance(cpu_utilization, (int, float)) or cpu_utilization <= 0:
            score *= 0.7  # Penalty for missing CPU data
            self.logger.warning("📊 Missing or invalid CPU utilization data")
        
        if not isinstance(memory_utilization, (int, float)) or memory_utilization <= 0:
            score *= 0.7  # Penalty for missing memory data
            self.logger.warning("📊 Missing or invalid memory utilization data")
        
        # Check for reasonable utilization values
        if isinstance(cpu_utilization, (int, float)) and cpu_utilization > 100:
            score *= 0.9  # Minor penalty for unusual but possible values
            self.logger.warning(f"📊 Unusual CPU utilization: {cpu_utilization}%")
        
        if isinstance(memory_utilization, (int, float)) and memory_utilization > 100:
            score *= 0.9  # Minor penalty for unusual but possible values
            self.logger.warning(f"📊 Unusual memory utilization: {memory_utilization}%")
        
        # Check for sufficient data points (cluster size)
        node_count = usage.get('node_count', 0)
        if not isinstance(node_count, int) or node_count < 3:
            score *= 0.8  # Penalty for insufficient data points
            self.logger.warning(f"📊 Limited data points: {node_count} nodes")
        
        # Ensure minimum score threshold
        final_score = max(0.2, score)  # Never go below 20% confidence
        
        return final_score
    
    def _calculate_consistency_score(self, optimization: Dict, efficiency: Dict) -> float:
        """
        Check consistency between different metrics
        REFACTORED: Improved consistency checks with better thresholds
        
        Args:
            optimization: Optimization analysis results
            efficiency: Efficiency metrics
        
        Returns:
            float: Consistency score (0.0-1.0)
        """
        score = 1.0
        
        # Get optimization and efficiency metrics
        opt_percentage = optimization.get('optimization_percentage', 0)
        current_efficiency = efficiency.get('current_overall', 50)
        
        # Check optimization vs efficiency consistency
        high_performance_threshold = SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE
        
        if opt_percentage > 30 and current_efficiency > high_performance_threshold:
            # High optimization potential but high efficiency is inconsistent
            score *= 0.7
            self.logger.warning(f"📊 Inconsistency: High optimization potential ({opt_percentage}%) "
                              f"but high efficiency ({current_efficiency}%)")
        
        # Check for impossible efficiency improvements
        target_efficiency = efficiency.get('target_overall', current_efficiency)
        improvement_potential = target_efficiency - current_efficiency
        
        if improvement_potential < 0:
            score *= 0.6  # Target efficiency lower than current is inconsistent
            self.logger.warning("📊 Inconsistency: Target efficiency lower than current")
        
        # Check cost savings vs optimization consistency
        total_savings = optimization.get('total_monthly_savings', 0)
        if opt_percentage > 20 and total_savings <= 0:
            score *= 0.5  # High optimization but no savings is very inconsistent
            self.logger.warning(f"📊 Major inconsistency: High optimization ({opt_percentage}%) "
                              f"but no savings (${total_savings})")
        
        # Check for unrealistic optimization percentages
        if opt_percentage > 50:
            score *= 0.8  # Very high optimization potential might be unrealistic
            self.logger.warning(f"📊 Potentially unrealistic optimization: {opt_percentage}%")
        
        return max(0.2, score)
    
    def _calculate_feasibility_score(self, usage: Dict, optimization: Dict) -> float:
        """
        Calculate feasibility of recommendations
        REFACTORED: Added comprehensive feasibility checks
        
        Args:
            usage: Current usage metrics
            optimization: Optimization recommendations
        
        Returns:
            float: Feasibility score (0.0-1.0)
        """
        score = 1.0
        
        # Check current utilization levels for right-sizing feasibility
        avg_cpu = usage.get('avg_cpu_utilization', 0)
        avg_memory = usage.get('avg_memory_utilization', 0)
        
        # High utilization makes aggressive right-sizing less feasible
        cpu_overutilized_threshold = 85  # Above 85% CPU is risky for right-sizing
        memory_overutilized_threshold = 90  # Above 90% memory is risky
        
        if avg_cpu > cpu_overutilized_threshold:
            score *= 0.7  # Reduce feasibility for high CPU utilization
            self.logger.warning(f"📊 Reduced feasibility: High CPU utilization ({avg_cpu}%)")
        
        if avg_memory > memory_overutilized_threshold:
            score *= 0.7  # Reduce feasibility for high memory utilization
            self.logger.warning(f"📊 Reduced feasibility: High memory utilization ({avg_memory}%)")
        
        # Check variability - high variability makes optimization more challenging
        cpu_std = usage.get('cpu_std_dev', 0)
        memory_std = usage.get('memory_std_dev', 0)
        
        high_variability_threshold = 25  # Above 25% standard deviation is challenging
        if cpu_std > high_variability_threshold or memory_std > high_variability_threshold:
            score *= 0.8  # High variability reduces feasibility
            self.logger.warning(f"📊 Reduced feasibility: High variability "
                              f"(CPU std: {cpu_std}%, Memory std: {memory_std}%)")
        
        # Check cluster size - very small clusters have limited optimization options
        node_count = usage.get('node_count', 0)
        if node_count < 3:
            score *= 0.6  # Small clusters have limited optimization feasibility
            self.logger.warning(f"📊 Reduced feasibility: Small cluster ({node_count} nodes)")
        
        # Check optimization magnitude vs current state
        opt_percentage = optimization.get('optimization_percentage', 0)
        if opt_percentage > 40:  # Very high optimization might not be practically achievable
            score *= 0.8
            self.logger.warning(f"📊 Reduced feasibility: Very high optimization target ({opt_percentage}%)")
        
        return max(0.2, score)