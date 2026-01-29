"""
Anomaly Detection Standards
===========================

Comprehensive standards for anomaly detection in Kubernetes workloads
including thresholds, severity levels, and detection parameters.
"""

class AnomalyDetectionStandards:
    """Anomaly detection standards and thresholds"""
    
    # =============================================
    # MEMORY LEAK DETECTION STANDARDS
    # =============================================
    
    # Memory leak detection thresholds
    MEMORY_LEAK_MIN_SLOPE_THRESHOLD = 2.0          # 2% increase per data point
    MEMORY_LEAK_MIN_TOTAL_INCREASE = 30.0          # 30% total increase required
    MEMORY_LEAK_CRITICAL_THRESHOLD = 95.0          # 95% memory usage is critical
    MEMORY_LEAK_MIN_DATA_POINTS = 10               # Minimum data points needed
    
    # Memory leak severity levels
    MEMORY_LEAK_SEVERITY_LOW = 3.0                 # Below 3% slope = low severity
    MEMORY_LEAK_SEVERITY_MEDIUM = 5.0              # 3-5% slope = medium severity
    MEMORY_LEAK_SEVERITY_HIGH = 8.0                # Above 8% slope = high severity
    
    # =============================================
    # CPU SPIKE DETECTION STANDARDS
    # =============================================
    
    # CPU spike detection thresholds
    CPU_SPIKE_BASELINE_MULTIPLIER = 3.0            # 3x baseline = spike
    CPU_SPIKE_ABSOLUTE_THRESHOLD = 80.0            # Above 80% is always spike
    CPU_SPIKE_MIN_DATA_POINTS = 5                  # Minimum data points needed
    CPU_SPIKE_BASELINE_PERCENTILE = 70.0           # Use 70th percentile as baseline
    
    # CPU spike severity levels
    CPU_SPIKE_SEVERITY_MEDIUM_THRESHOLD = 90.0     # Below 90% = medium severity
    CPU_SPIKE_SEVERITY_HIGH_THRESHOLD = 95.0       # Above 95% = high severity
    
    # =============================================
    # RESOURCE DRIFT DETECTION STANDARDS
    # =============================================
    
    # Resource drift detection thresholds
    RESOURCE_DRIFT_SIGNIFICANT_THRESHOLD = 25.0    # 25% change is significant
    RESOURCE_DRIFT_MIN_DATA_POINTS = 20            # Minimum data points needed
    RESOURCE_DRIFT_COMPARISON_RATIO = 0.25         # Compare first/last 25% of data
    
    # Resource drift severity levels
    RESOURCE_DRIFT_SEVERITY_DIVISOR = 50.0         # Divide drift % by 50 for severity
    
    # =============================================
    # UNUSUAL PATTERN DETECTION STANDARDS
    # =============================================
    
    # Unusual pattern detection thresholds
    UNUSUAL_PATTERN_CV_THRESHOLD = 1.0             # CV > 1.0 = high variability
    UNUSUAL_PATTERN_MIN_DATA_POINTS = 10           # Minimum data points needed
    UNUSUAL_PATTERN_SEVERITY_DIVISOR = 2.0         # Divide CV by 2 for severity
    
    # =============================================
    # COST ANOMALY DETECTION STANDARDS
    # =============================================
    
    # Cost anomaly detection thresholds
    COST_ANOMALY_SPIKE_MULTIPLIER = 2.0            # 2x median cost = spike
    COST_ANOMALY_MIN_SPIKE_AMOUNT = 100.0          # Minimum $100 for significance
    COST_ANOMALY_SEVERITY_DIVISOR = 5.0            # Divide multiplier by 5 for severity
    
    # =============================================
    # CONFIDENCE SCORING STANDARDS
    # =============================================
    
    # Confidence calculation parameters
    CONFIDENCE_BASE_SCORE = 100.0                  # Base confidence score
    CONFIDENCE_NO_ANOMALIES = 100.0                # Confidence when no anomalies
    CONFIDENCE_MIN_SCORE = 50.0                    # Minimum confidence score
    CONFIDENCE_SEVERITY_IMPACT = 50.0              # Max impact of severity on confidence
    
    # =============================================
    # ANOMALY SEVERITY LEVELS
    # =============================================
    
    # Severity level definitions
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    
    # Severity thresholds (0.0 to 1.0 scale)
    SEVERITY_LOW_THRESHOLD = 0.3
    SEVERITY_MEDIUM_THRESHOLD = 0.6
    SEVERITY_HIGH_THRESHOLD = 0.8
    
    # =============================================
    # ANOMALY IMPACT LEVELS
    # =============================================
    
    # Impact level definitions
    IMPACT_LOW = "low"
    IMPACT_MEDIUM = "medium"
    IMPACT_HIGH = "high"
    IMPACT_CRITICAL = "critical"
    
    # =============================================
    # TIME-BASED THRESHOLDS
    # =============================================
    
    # Time thresholds for predictions
    TIME_TO_CRITICAL_IMMEDIATE_THRESHOLD = 1       # Less than 1 hour = immediate
    TIME_TO_CRITICAL_URGENT_THRESHOLD = 24         # Less than 24 hours = urgent
    TIME_TO_CRITICAL_WARNING_THRESHOLD = 168       # Less than 1 week = warning
    
    # =============================================
    # VALIDATION METHODS
    # =============================================
    
    @staticmethod
    def validate_memory_leak_data(memory_history, min_points=None):
        """Validate memory history data for leak detection"""
        if memory_history is None:
            raise ValueError("Memory history parameter is required")
        if not isinstance(memory_history, list):
            raise ValueError("Memory history must be a list")
        
        min_required = min_points if min_points is not None else AnomalyDetectionStandards.MEMORY_LEAK_MIN_DATA_POINTS
        if len(memory_history) < min_required:
            raise ValueError(f"Memory history needs at least {min_required} data points, got {len(memory_history)}")
        
        # Validate all values are numeric and non-negative
        for i, value in enumerate(memory_history):
            if not isinstance(value, (int, float)):
                raise ValueError(f"Memory history item {i} must be numeric")
            if value < 0:
                raise ValueError(f"Memory history item {i} cannot be negative")
            if value > 100:
                raise ValueError(f"Memory history item {i} cannot exceed 100%")
    
    @staticmethod
    def validate_cpu_spike_data(cpu_history, min_points=None):
        """Validate CPU history data for spike detection"""
        if cpu_history is None:
            raise ValueError("CPU history parameter is required")
        if not isinstance(cpu_history, list):
            raise ValueError("CPU history must be a list")
        
        min_required = min_points if min_points is not None else AnomalyDetectionStandards.CPU_SPIKE_MIN_DATA_POINTS
        if len(cpu_history) < min_required:
            raise ValueError(f"CPU history needs at least {min_required} data points, got {len(cpu_history)}")
        
        # Validate all values are numeric and non-negative
        for i, value in enumerate(cpu_history):
            if not isinstance(value, (int, float)):
                raise ValueError(f"CPU history item {i} must be numeric")
            if value < 0:
                raise ValueError(f"CPU history item {i} cannot be negative")
    
    @staticmethod
    def validate_cost_anomaly_data(cost_history):
        """Validate cost history data for anomaly detection"""
        if cost_history is None:
            raise ValueError("Cost history parameter is required")
        if not isinstance(cost_history, list):
            raise ValueError("Cost history must be a list")
        if len(cost_history) == 0:
            raise ValueError("Cost history cannot be empty")
        
        # Validate cost data structure
        for i, cost_point in enumerate(cost_history):
            if not isinstance(cost_point, dict):
                raise ValueError(f"Cost history item {i} must be a dictionary")
            if "amount" not in cost_point:
                raise KeyError(f"Cost history item {i} missing required 'amount' field")
            if "timestamp" not in cost_point:
                raise KeyError(f"Cost history item {i} missing required 'timestamp' field")
            
            amount = cost_point["amount"]
            if not isinstance(amount, (int, float)):
                raise ValueError(f"Cost amount in item {i} must be numeric")
            if amount < 0:
                raise ValueError(f"Cost amount in item {i} cannot be negative")
    
    @staticmethod
    def get_severity_level(severity_score):
        """Get severity level based on numeric severity score"""
        if severity_score is None:
            raise ValueError("Severity score parameter is required")
        if not isinstance(severity_score, (int, float)):
            raise ValueError("Severity score must be numeric")
        if not 0.0 <= severity_score <= 1.0:
            raise ValueError("Severity score must be between 0.0 and 1.0")
        
        if severity_score >= AnomalyDetectionStandards.SEVERITY_HIGH_THRESHOLD:
            return AnomalyDetectionStandards.SEVERITY_HIGH
        elif severity_score >= AnomalyDetectionStandards.SEVERITY_MEDIUM_THRESHOLD:
            return AnomalyDetectionStandards.SEVERITY_MEDIUM
        elif severity_score >= AnomalyDetectionStandards.SEVERITY_LOW_THRESHOLD:
            return AnomalyDetectionStandards.SEVERITY_LOW
        else:
            return AnomalyDetectionStandards.SEVERITY_LOW
    
    @staticmethod
    def get_time_urgency_level(hours_to_critical):
        """Get urgency level based on time to critical threshold"""
        if hours_to_critical is None:
            raise ValueError("Hours to critical parameter is required")
        if not isinstance(hours_to_critical, (int, float)):
            raise ValueError("Hours to critical must be numeric")
        if hours_to_critical < 0:
            raise ValueError("Hours to critical cannot be negative")
        
        if hours_to_critical <= AnomalyDetectionStandards.TIME_TO_CRITICAL_IMMEDIATE_THRESHOLD:
            return "immediate"
        elif hours_to_critical <= AnomalyDetectionStandards.TIME_TO_CRITICAL_URGENT_THRESHOLD:
            return "urgent"
        elif hours_to_critical <= AnomalyDetectionStandards.TIME_TO_CRITICAL_WARNING_THRESHOLD:
            return "warning"
        else:
            return "low_priority"