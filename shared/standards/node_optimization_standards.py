"""
Node Optimization Standards
===========================

Comprehensive standards for analyzing and optimizing Kubernetes nodes
including VM sizing, utilization thresholds, and cost efficiency metrics.
"""

class NodeOptimizationStandards:
    """Node optimization analysis and recommendation standards"""
    
    # =============================================
    # VM SIZE OPTIMIZATION STANDARDS
    # =============================================
    
    # Azure VM Series Categories
    VM_SERIES_GENERAL_PURPOSE = ["Standard_D", "Standard_B", "Standard_A"]
    VM_SERIES_COMPUTE_OPTIMIZED = ["Standard_F", "Standard_FX"]
    VM_SERIES_MEMORY_OPTIMIZED = ["Standard_E", "Standard_M", "Standard_G"]
    VM_SERIES_STORAGE_OPTIMIZED = ["Standard_L"]
    VM_SERIES_GPU_OPTIMIZED = ["Standard_NC", "Standard_ND", "Standard_NV"]
    VM_SERIES_HPC_OPTIMIZED = ["Standard_H", "Standard_HB", "Standard_HC"]
    
    # VM Size Recommendation Thresholds
    CPU_UTILIZATION_LOW_THRESHOLD = 20.0          # Below 20% = overprovisioned
    CPU_UTILIZATION_HIGH_THRESHOLD = 80.0         # Above 80% = underprovisioned
    MEMORY_UTILIZATION_LOW_THRESHOLD = 30.0       # Below 30% = overprovisioned
    MEMORY_UTILIZATION_HIGH_THRESHOLD = 85.0      # Above 85% = underprovisioned
    
    # Node Efficiency Metrics
    COST_PER_CORE_EFFICIENCY_THRESHOLD = 0.05     # Dollar per core per hour
    COST_PER_GB_EFFICIENCY_THRESHOLD = 0.01       # Dollar per GB per hour
    RESOURCE_WASTE_PERCENTAGE_THRESHOLD = 40.0    # Above 40% waste = optimize
    
    # =============================================
    # NODE UTILIZATION STANDARDS
    # =============================================
    
    # Utilization Analysis Windows
    UTILIZATION_ANALYSIS_WINDOW_HOURS = 168       # 7 days analysis window
    PEAK_UTILIZATION_WINDOW_HOURS = 24            # Peak analysis in 24h windows
    MINIMUM_DATA_POINTS_REQUIRED = 100            # Minimum metrics for analysis
    
    # Utilization Categories
    UTILIZATION_CATEGORY_IDLE = "idle"             # 0-10% utilization
    UTILIZATION_CATEGORY_LOW = "low"               # 10-30% utilization
    UTILIZATION_CATEGORY_MODERATE = "moderate"     # 30-60% utilization
    UTILIZATION_CATEGORY_HIGH = "high"             # 60-85% utilization
    UTILIZATION_CATEGORY_CRITICAL = "critical"     # 85%+ utilization
    
    # Utilization Thresholds by Category
    UTILIZATION_THRESHOLDS = {
        UTILIZATION_CATEGORY_IDLE: (0.0, 10.0),
        UTILIZATION_CATEGORY_LOW: (10.0, 30.0),
        UTILIZATION_CATEGORY_MODERATE: (30.0, 60.0),
        UTILIZATION_CATEGORY_HIGH: (60.0, 85.0),
        UTILIZATION_CATEGORY_CRITICAL: (85.0, 100.0)
    }
    
    # =============================================
    # COST EFFICIENCY STANDARDS
    # =============================================
    
    # Reserved Instance Optimization
    RESERVED_INSTANCE_BREAKEVEN_MONTHS = 12       # RI becomes cost-effective
    RESERVED_INSTANCE_UTILIZATION_THRESHOLD = 70.0  # Minimum utilization for RI
    SPOT_INSTANCE_SUITABILITY_THRESHOLD = 50.0    # Workload interruption tolerance
    
    # Cost Categories
    COST_CATEGORY_OPTIMIZED = "optimized"         # Cost-efficient configuration
    COST_CATEGORY_ACCEPTABLE = "acceptable"       # Reasonable cost efficiency
    COST_CATEGORY_WASTEFUL = "wasteful"           # Needs immediate optimization
    COST_CATEGORY_CRITICAL = "critical"           # Severely overprovisioned
    
    # Cost Efficiency Scoring
    COST_EFFICIENCY_SCORE_EXCELLENT = 90.0        # 90-100% efficiency
    COST_EFFICIENCY_SCORE_GOOD = 70.0             # 70-89% efficiency
    COST_EFFICIENCY_SCORE_FAIR = 50.0             # 50-69% efficiency
    COST_EFFICIENCY_SCORE_POOR = 30.0             # 30-49% efficiency
    # Below 30% = critical
    
    # =============================================
    # OPTIMIZATION RECOMMENDATION TYPES
    # =============================================
    
    # Recommendation Categories
    RECOMMENDATION_TYPE_DOWNSIZE = "downsize"     # Reduce VM size
    RECOMMENDATION_TYPE_UPSIZE = "upsize"         # Increase VM size
    RECOMMENDATION_TYPE_CHANGE_SERIES = "change_series"  # Different VM series
    RECOMMENDATION_TYPE_RESERVED_INSTANCE = "reserved_instance"  # Use RI
    RECOMMENDATION_TYPE_SPOT_INSTANCE = "spot_instance"  # Use spot instances
    RECOMMENDATION_TYPE_REMOVE_NODE = "remove_node"  # Delete unnecessary node
    RECOMMENDATION_TYPE_ADD_NODE = "add_node"     # Add capacity
    
    # Recommendation Priority Levels
    RECOMMENDATION_PRIORITY_CRITICAL = "critical"  # Immediate action required
    RECOMMENDATION_PRIORITY_HIGH = "high"         # High impact optimization
    RECOMMENDATION_PRIORITY_MEDIUM = "medium"     # Moderate impact
    RECOMMENDATION_PRIORITY_LOW = "low"           # Minor optimization
    
    # =============================================
    # WORKLOAD ANALYSIS STANDARDS
    # =============================================
    
    # Workload Types
    WORKLOAD_TYPE_STATELESS = "stateless"         # Web apps, APIs
    WORKLOAD_TYPE_STATEFUL = "stateful"           # Databases, storage
    WORKLOAD_TYPE_BATCH = "batch"                 # Batch processing
    WORKLOAD_TYPE_STREAMING = "streaming"         # Real-time processing
    WORKLOAD_TYPE_ML = "machine_learning"         # ML workloads
    
    # Resource Requirements by Workload Type
    WORKLOAD_RESOURCE_PROFILES = {
        WORKLOAD_TYPE_STATELESS: {
            "cpu_intensive": False,
            "memory_intensive": False,
            "network_intensive": True,
            "storage_intensive": False
        },
        WORKLOAD_TYPE_STATEFUL: {
            "cpu_intensive": False,
            "memory_intensive": True,
            "network_intensive": False,
            "storage_intensive": True
        },
        WORKLOAD_TYPE_BATCH: {
            "cpu_intensive": True,
            "memory_intensive": False,
            "network_intensive": False,
            "storage_intensive": False
        },
        WORKLOAD_TYPE_STREAMING: {
            "cpu_intensive": True,
            "memory_intensive": True,
            "network_intensive": True,
            "storage_intensive": False
        },
        WORKLOAD_TYPE_ML: {
            "cpu_intensive": True,
            "memory_intensive": True,
            "network_intensive": False,
            "storage_intensive": True
        }
    }
    
    # =============================================
    # VALIDATION AND CONSTRAINTS
    # =============================================
    
    # Data Validation Requirements
    REQUIRED_METRICS_FOR_ANALYSIS = [
        "cpu_usage_pct",
        "memory_usage_pct", 
        "vm_size"
    ]
    
    # Constraint Validation
    MIN_ANALYSIS_PERIOD_HOURS = 24               # Minimum analysis period
    MAX_RECOMMENDATION_AGE_HOURS = 48            # Recommendations expire after 48h
    CONFIDENCE_THRESHOLD_PERCENTAGE = 80.0       # Minimum confidence for recommendations
    
    @staticmethod
    def validate_utilization_data(cpu_utilization, memory_utilization):
        """Validate utilization metrics are within valid ranges"""
        if cpu_utilization is None:
            raise ValueError("CPU utilization parameter is required")
        if memory_utilization is None:
            raise ValueError("Memory utilization parameter is required")
        if not 0.0 <= cpu_utilization <= 100.0:
            raise ValueError("CPU utilization must be between 0 and 100")
        if not 0.0 <= memory_utilization <= 100.0:
            raise ValueError("Memory utilization must be between 0 and 100")
    
    @staticmethod
    def validate_vm_configuration(vm_size, vm_series):
        """Validate VM configuration parameters"""
        if vm_size is None:
            raise ValueError("VM size parameter is required")
        if vm_series is None:
            raise ValueError("VM series parameter is required")
        if not isinstance(vm_size, str) or len(vm_size.strip()) == 0:
            raise ValueError("VM size must be a non-empty string")
        if not isinstance(vm_series, str) or len(vm_series.strip()) == 0:
            raise ValueError("VM series must be a non-empty string")
    
    @staticmethod
    def validate_cost_data(cost_per_hour):
        """Validate cost data for analysis"""
        if cost_per_hour is None:
            raise ValueError("Cost per hour parameter is required")
        if not isinstance(cost_per_hour, (int, float)):
            raise ValueError("Cost per hour must be a numeric value")
        if cost_per_hour < 0:
            raise ValueError("Cost per hour cannot be negative")
    
    @staticmethod
    def get_utilization_category(utilization_percentage):
        """Get utilization category based on percentage"""
        if utilization_percentage is None:
            raise ValueError("Utilization percentage parameter is required")
        if not 0.0 <= utilization_percentage <= 100.0:
            raise ValueError("Utilization percentage must be between 0 and 100")
        
        for category, (min_val, max_val) in NodeOptimizationStandards.UTILIZATION_THRESHOLDS.items():
            if min_val <= utilization_percentage < max_val:
                return category
        return NodeOptimizationStandards.UTILIZATION_CATEGORY_CRITICAL
    
    @staticmethod
    def calculate_cost_efficiency_score(actual_utilization, cost_per_hour, baseline_cost_per_hour):
        """Calculate cost efficiency score for node"""
        if actual_utilization is None:
            raise ValueError("Actual utilization parameter is required")
        if cost_per_hour is None:
            raise ValueError("Cost per hour parameter is required")
        if baseline_cost_per_hour is None:
            raise ValueError("Baseline cost per hour parameter is required")
        
        NodeOptimizationStandards.validate_utilization_data(actual_utilization, 0)
        NodeOptimizationStandards.validate_cost_data(cost_per_hour)
        NodeOptimizationStandards.validate_cost_data(baseline_cost_per_hour)
        
        # Efficiency = (Utilization / 100) * (Baseline Cost / Actual Cost) * 100
        if cost_per_hour == 0:
            raise ValueError("Cost per hour cannot be zero for efficiency calculation")
        
        efficiency_score = (actual_utilization / 100.0) * (baseline_cost_per_hour / cost_per_hour) * 100.0
        return min(efficiency_score, 100.0)  # Cap at 100%