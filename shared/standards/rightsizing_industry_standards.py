"""
Right-sizing Industry Standards
===============================

Industry-standard values for Kubernetes right-sizing optimization.
Based on CNCF FinOps best practices and cloud provider recommendations.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""


class RightSizingOptimizationStandards:
    """Industry standards for CPU/memory right-sizing optimization"""
    
    # CPU Optimization Thresholds (percentages)
    CPU_OPTIMAL_UTILIZATION = 70  # Target CPU utilization for optimal performance
    CPU_UNDERUTILIZED_THRESHOLD = 30  # Below this is considered underutilized
    CPU_OVERUTILIZED_THRESHOLD = 85  # Above this is considered overutilized
    CPU_WASTE_CALCULATION_BASE = 70  # Base for waste calculation
    
    # Memory Optimization Thresholds (percentages)
    MEMORY_OPTIMAL_UTILIZATION = 75  # Target memory utilization
    MEMORY_UNDERUTILIZED_THRESHOLD = 35  # Below this is considered underutilized
    MEMORY_OVERUTILIZED_THRESHOLD = 90  # Above this is considered overutilized
    MEMORY_WASTE_CALCULATION_BASE = 75  # Base for waste calculation
    
    # Variability Thresholds for Right-sizing
    HIGH_VARIABILITY_THRESHOLD = 20  # Standard deviation threshold
    LOW_VARIABILITY_THRESHOLD = 10  # Low variability threshold
    
    # Recovery Factors (potential savings multipliers)
    HIGH_VARIABILITY_RECOVERY_FACTOR = 0.2  # Conservative when workload is variable
    MEDIUM_VARIABILITY_RECOVERY_FACTOR = 0.28  # Moderate variability
    LOW_VARIABILITY_RECOVERY_FACTOR = 0.35  # Aggressive when stable workload
    
    # Efficiency Score Calculations
    EFFICIENCY_SCORE_MAX_POINTS = 100
    EFFICIENCY_PENALTY_PER_PERCENT = 1.5  # Points lost per % away from optimal
    
    # Target Efficiency Calculations
    MAX_EFFICIENCY_IMPROVEMENT_AGGRESSIVE = 0.3  # 30% max improvement for high optimization
    MAX_EFFICIENCY_IMPROVEMENT_MODERATE = 0.2  # 20% max improvement for medium optimization
    MIN_EFFICIENCY_IMPROVEMENT = 0.1  # 10% minimum improvement


class RightSizingCostStandards:
    """Cost calculation standards for right-sizing optimization"""
    
    # Savings Calculation Multipliers
    CPU_WASTE_SAVINGS_MULTIPLIER = 0.6  # CPU waste contributes 60% to savings calculation
    MEMORY_WASTE_SAVINGS_MULTIPLIER = 0.4  # Memory waste contributes 40% to savings calculation
    
    # Conservative Factors for Different Scenarios
    PRODUCTION_WORKLOAD_CONSERVATIVE_FACTOR = 0.8  # More conservative for production
    DEVELOPMENT_WORKLOAD_FACTOR = 1.0  # Standard for development
    TESTING_WORKLOAD_FACTOR = 0.9  # Slightly conservative for testing
    
    # Minimum Savings Thresholds (to avoid tiny optimizations)
    MINIMUM_MONTHLY_SAVINGS_THRESHOLD = 10.0  # Don't recommend changes < $10/month
    MINIMUM_PERCENTAGE_SAVINGS_THRESHOLD = 0.05  # Don't recommend changes < 5%


class RightSizingRecommendationStandards:
    """Standards for generating right-sizing recommendations"""
    
    # Recommendation Confidence Levels
    HIGH_CONFIDENCE_THRESHOLD = 0.8  # 80% confidence for strong recommendations
    MEDIUM_CONFIDENCE_THRESHOLD = 0.6  # 60% confidence for moderate recommendations
    LOW_CONFIDENCE_THRESHOLD = 0.4  # 40% confidence minimum
    
    # Resource Adjustment Limits (safety bounds)
    MAX_CPU_REDUCTION_PERCENTAGE = 0.4  # Don't reduce CPU by more than 40%
    MAX_MEMORY_REDUCTION_PERCENTAGE = 0.35  # Don't reduce memory by more than 35%
    MIN_CPU_INCREASE_PERCENTAGE = 0.15  # Minimum 15% increase if scaling up
    MIN_MEMORY_INCREASE_PERCENTAGE = 0.2  # Minimum 20% increase if scaling up
    
    # Safety Margins
    CPU_SAFETY_MARGIN = 0.15  # 15% safety margin for CPU recommendations
    MEMORY_SAFETY_MARGIN = 0.2  # 20% safety margin for memory recommendations