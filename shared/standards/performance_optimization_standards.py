"""
Performance Optimization Standards
===================================

Industry-standard values for Kubernetes performance optimization.
Based on CNCF FinOps best practices and cloud provider recommendations.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""


class PerformanceOptimizationStandards:
    """Industry standards for performance optimization"""
    
    # Performance Waste Detection Thresholds
    SEVERE_CONTENTION_CPU_THRESHOLD = 200  # CPU % threshold for severe resource contention
    MODERATE_CONTENTION_CPU_THRESHOLD = 150  # CPU % threshold for moderate contention
    HIGH_CPU_WORKLOAD_COUNT_THRESHOLD = 5  # Number of high CPU workloads indicating issues
    
    # Performance Waste Savings Rates
    SEVERE_CONTENTION_SAVINGS_RATE = 0.15  # 15% savings for severe resource contention
    MODERATE_CONTENTION_SAVINGS_RATE = 0.1  # 10% savings for moderate contention
    MULTIPLE_WORKLOAD_ISSUES_SAVINGS_RATE = 0.08  # 8% savings for multiple workload issues
    MINOR_PERFORMANCE_ISSUES_SAVINGS_RATE = 0.05  # 5% savings for minor issues
    
    # System Efficiency Calculation Standards
    CPU_OPTIMAL_FOR_EFFICIENCY = 70  # Optimal CPU utilization for efficiency calculation
    MEMORY_OPTIMAL_FOR_EFFICIENCY = 75  # Optimal memory utilization for efficiency calculation
    EFFICIENCY_PENALTY_MULTIPLIER = 1.0  # Penalty multiplier for over-optimal utilization
    
    # Workload Classification Thresholds
    UNDERUTILIZED_CPU_THRESHOLD = 30  # Below this is underutilized
    UNDERUTILIZED_MEMORY_THRESHOLD = 30  # Below this is underutilized
    HIGH_VARIABILITY_THRESHOLD = 20  # Standard deviation threshold for variable workloads
    WELL_BALANCED_CPU_THRESHOLD = 60  # Above this (with memory) is well balanced
    WELL_BALANCED_MEMORY_THRESHOLD = 60  # Above this (with CPU) is well balanced


class PerformanceMetricsStandards:
    """Standards for performance metrics and monitoring"""
    
    # Response Time Standards (milliseconds)
    EXCELLENT_RESPONSE_TIME = 100  # Below 100ms is excellent
    GOOD_RESPONSE_TIME = 500  # Below 500ms is good
    ACCEPTABLE_RESPONSE_TIME = 1000  # Below 1000ms is acceptable
    POOR_RESPONSE_TIME = 2000  # Above 2000ms is poor
    
    # Throughput Standards (requests per second)
    HIGH_THROUGHPUT_THRESHOLD = 1000  # Above 1000 RPS is high throughput
    MEDIUM_THROUGHPUT_THRESHOLD = 100  # Above 100 RPS is medium throughput
    LOW_THROUGHPUT_THRESHOLD = 10  # Above 10 RPS is low throughput
    
    # Error Rate Standards (percentages)
    EXCELLENT_ERROR_RATE = 0.01  # Below 0.01% error rate is excellent
    GOOD_ERROR_RATE = 0.1  # Below 0.1% error rate is good
    ACCEPTABLE_ERROR_RATE = 1.0  # Below 1% error rate is acceptable
    POOR_ERROR_RATE = 5.0  # Above 5% error rate is poor


class ResourceContentionStandards:
    """Standards for detecting and measuring resource contention"""
    
    # CPU Contention Indicators
    CPU_THROTTLING_THRESHOLD = 5.0  # 5% throttling indicates contention
    CPU_WAIT_TIME_THRESHOLD = 10.0  # 10% wait time indicates contention
    CONTEXT_SWITCH_RATE_THRESHOLD = 50000  # High context switches per second
    
    # Memory Contention Indicators
    PAGE_FAULT_RATE_THRESHOLD = 100  # Page faults per second indicating memory pressure
    SWAP_USAGE_THRESHOLD = 10.0  # 10% swap usage indicates memory contention
    MEMORY_PRESSURE_THRESHOLD = 0.8  # 80% memory pressure score threshold
    
    # I/O Contention Indicators
    DISK_QUEUE_DEPTH_THRESHOLD = 10  # Average disk queue depth indicating I/O contention
    IOPS_UTILIZATION_THRESHOLD = 80.0  # 80% IOPS utilization threshold
    NETWORK_BANDWIDTH_THRESHOLD = 80.0  # 80% network bandwidth utilization


class PerformanceSavingsStandards:
    """Standards for calculating performance optimization savings"""
    
    # Savings Overlap Factors (when combining different optimization types)
    PERFORMANCE_OVERLAP_FACTOR = 0.3  # 30% of performance savings can be combined
    RIGHTSIZING_OVERLAP_FACTOR = 0.3  # 30% of rightsizing savings can be combined
    HPA_OVERLAP_FACTOR = 0.4  # 40% of HPA savings can be combined
    
    # Maximum Combined Savings Cap
    MAX_COMBINED_SAVINGS_PERCENTAGE = 0.4  # Cap combined savings at 40% of compute cost
    
    # Infrastructure-wide Optimization
    BASE_INFRASTRUCTURE_OPTIMIZATION_RATE = 0.05  # 5% base infrastructure optimization
    MONITORING_OPTIMIZATION_MULTIPLIER = 1.2  # 20% additional savings with good monitoring
    AUTOMATION_OPTIMIZATION_MULTIPLIER = 1.3  # 30% additional savings with automation
    
    # Workload-specific Performance Multipliers
    BATCH_WORKLOAD_OPTIMIZATION_MULTIPLIER = 1.4  # Batch workloads have higher optimization potential
    REALTIME_WORKLOAD_OPTIMIZATION_MULTIPLIER = 0.8  # Real-time workloads have lower optimization potential
    WEB_APPLICATION_OPTIMIZATION_MULTIPLIER = 1.1  # Web apps have moderate optimization potential