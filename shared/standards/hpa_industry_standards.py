"""
Kubernetes HPA (Horizontal Pod Autoscaler) Industry Standards
============================================================

Industry-standard HPA configurations, metrics, and optimization practices
based on Kubernetes HPA v2 specification, CNCF best practices, and 
FinOps cost optimization guidelines.

Sources:
- Kubernetes HPA v2 API Specification
- CNCF FinOps for Kubernetes Best Practices
- Google Cloud Platform HPA Best Practices
- AWS EKS Scaling Best Practices
- Azure AKS Autoscaling Guidelines
"""

class HPAAlgorithmStandards:
    """Official Kubernetes HPA algorithm standards and behaviors"""
    
    # =============================================
    # KUBERNETES HPA V2 ALGORITHM SPECIFICATIONS
    # =============================================
    
    # Core HPA Formula: desiredReplicas = ceil[currentReplicas * (currentMetricValue / desiredMetricValue)]
    HPA_REPLICA_CALCULATION_FORMULA = "ceil(currentReplicas * (currentMetricValue / desiredMetricValue))"
    
    # Tolerance Band - HPA won't scale if metric is within this percentage of target
    HPA_TOLERANCE_PERCENTAGE = 10.0  # 10% tolerance band (Kubernetes default)
    
    # Stabilization Windows (seconds)
    HPA_SCALE_UP_STABILIZATION_SECONDS = 0      # Immediate scale-up (default)
    HPA_SCALE_DOWN_STABILIZATION_SECONDS = 300  # 5 minutes scale-down delay (default)
    
    # Scaling Velocity Limits
    HPA_SCALE_UP_PERCENT_POLICY = 100    # 100% increase allowed per scaling event
    HPA_SCALE_UP_PODS_POLICY = 4         # Maximum 4 pods added per scaling event
    HPA_SCALE_DOWN_PERCENT_POLICY = 50   # 50% decrease allowed per scaling event
    HPA_SCALE_DOWN_PODS_POLICY = 2       # Maximum 2 pods removed per scaling event
    
    # Metrics Collection and Decision Making
    HPA_METRICS_AGGREGATION_INTERVAL_SECONDS = 15  # 15s metrics collection interval
    HPA_SYNC_PERIOD_SECONDS = 15                   # 15s HPA controller sync period
    HPA_DOWNSCALE_DELAY_SECONDS = 180             # 3 minutes before considering downscale
    HPA_UPSCALE_DELAY_SECONDS = 30                # 30 seconds before considering upscale
    
    # Multi-Metric Behavior
    HPA_MULTI_METRIC_SELECTION = "max"  # Take MAX of all metrics for scaling decision
    
    # Resource Metric Defaults
    HPA_DEFAULT_CPU_UTILIZATION_TARGET = 80     # 80% CPU target (conservative)
    HPA_DEFAULT_MEMORY_UTILIZATION_TARGET = 70  # 70% memory target (avoid OOM)


class HPAConfigurationStandards:
    """Industry standard HPA configuration patterns"""
    
    # =============================================
    # REPLICA CONFIGURATION STANDARDS
    # =============================================
    
    # Minimum Replicas (High Availability)
    HPA_MIN_REPLICAS_PRODUCTION = 2      # Minimum 2 replicas for HA
    HPA_MIN_REPLICAS_DEVELOPMENT = 1     # Development can use 1 replica
    HPA_MIN_REPLICAS_CRITICAL_SYSTEM = 3 # Critical systems need 3+ replicas
    
    # Maximum Replicas (Cost Control)
    HPA_MAX_REPLICAS_SMALL_WORKLOAD = 10    # Small workloads max 10 replicas
    HPA_MAX_REPLICAS_MEDIUM_WORKLOAD = 50   # Medium workloads max 50 replicas  
    HPA_MAX_REPLICAS_LARGE_WORKLOAD = 200   # Large workloads max 200 replicas
    HPA_MAX_REPLICAS_ENTERPRISE = 1000     # Enterprise workloads max 1000 replicas
    
    # Replica Scaling Ratios
    HPA_REPLICA_SCALE_UP_MULTIPLIER = 2.0    # Double replicas when scaling up aggressively
    HPA_REPLICA_SCALE_DOWN_MULTIPLIER = 0.5  # Halve replicas when scaling down aggressively
    HPA_REPLICA_CONSERVATIVE_SCALE_FACTOR = 1.2  # 20% increase for conservative scaling
    
    # =============================================
    # METRICS CONFIGURATION STANDARDS
    # =============================================
    
    # CPU Utilization Targets by Workload Type
    HPA_CPU_TARGET_WEB_SERVERS = 70          # Web servers 70% CPU
    HPA_CPU_TARGET_API_SERVICES = 65         # API services 65% CPU
    HPA_CPU_TARGET_BATCH_PROCESSING = 85     # Batch processing 85% CPU
    HPA_CPU_TARGET_DATABASE_WORKLOADS = 60   # Database workloads 60% CPU
    HPA_CPU_TARGET_ML_INFERENCE = 75         # ML inference 75% CPU
    
    # Memory Utilization Targets by Workload Type  
    HPA_MEMORY_TARGET_WEB_SERVERS = 75       # Web servers 75% memory
    HPA_MEMORY_TARGET_API_SERVICES = 70      # API services 70% memory
    HPA_MEMORY_TARGET_CACHE_SERVICES = 80    # Cache services 80% memory
    HPA_MEMORY_TARGET_DATABASE_WORKLOADS = 65 # Database workloads 65% memory
    HPA_MEMORY_TARGET_ML_INFERENCE = 70      # ML inference 70% memory
    
    # Custom Metrics Standards
    HPA_REQUESTS_PER_SECOND_TARGET = 1000    # 1000 RPS target for web services
    HPA_QUEUE_LENGTH_TARGET = 10             # 10 items max queue length
    HPA_RESPONSE_TIME_TARGET_MS = 200        # 200ms max response time
    HPA_ERROR_RATE_THRESHOLD_PERCENT = 1     # 1% error rate threshold
    
    # =============================================
    # SCALING BEHAVIOR CONFIGURATION
    # =============================================
    
    # Scale-Up Policies (Conservative)
    HPA_SCALE_UP_CONSERVATIVE_PERCENT = 25   # 25% increase per scaling event
    HPA_SCALE_UP_CONSERVATIVE_PODS = 2       # 2 pods added per scaling event
    HPA_SCALE_UP_CONSERVATIVE_PERIOD = 60    # 60s between scale-up events
    
    # Scale-Up Policies (Aggressive) 
    HPA_SCALE_UP_AGGRESSIVE_PERCENT = 100    # 100% increase per scaling event
    HPA_SCALE_UP_AGGRESSIVE_PODS = 5         # 5 pods added per scaling event
    HPA_SCALE_UP_AGGRESSIVE_PERIOD = 30      # 30s between scale-up events
    
    # Scale-Down Policies (Conservative)
    HPA_SCALE_DOWN_CONSERVATIVE_PERCENT = 10 # 10% decrease per scaling event
    HPA_SCALE_DOWN_CONSERVATIVE_PODS = 1     # 1 pod removed per scaling event
    HPA_SCALE_DOWN_CONSERVATIVE_PERIOD = 300 # 5 minutes between scale-down events
    
    # Scale-Down Policies (Aggressive)
    HPA_SCALE_DOWN_AGGRESSIVE_PERCENT = 50   # 50% decrease per scaling event  
    HPA_SCALE_DOWN_AGGRESSIVE_PODS = 3       # 3 pods removed per scaling event
    HPA_SCALE_DOWN_AGGRESSIVE_PERIOD = 120   # 2 minutes between scale-down events


class HPAPerformanceStandards:
    """Performance optimization and efficiency standards for HPA"""
    
    # =============================================
    # EFFICIENCY CALCULATION STANDARDS
    # =============================================
    
    # HPA Efficiency Metrics
    HPA_EFFICIENCY_EXCELLENT_THRESHOLD = 90  # 90%+ efficiency is excellent
    HPA_EFFICIENCY_GOOD_THRESHOLD = 75       # 75%+ efficiency is good
    HPA_EFFICIENCY_ACCEPTABLE_THRESHOLD = 60 # 60%+ efficiency is acceptable
    HPA_EFFICIENCY_POOR_THRESHOLD = 40       # Below 40% efficiency is poor
    
    # Resource Utilization Targets for Efficiency
    HPA_OPTIMAL_CPU_UTILIZATION = 70         # 70% CPU utilization is optimal
    HPA_OPTIMAL_MEMORY_UTILIZATION = 75      # 75% memory utilization is optimal
    HPA_MAXIMUM_SAFE_CPU_UTILIZATION = 85    # 85% CPU max for safety margin
    HPA_MAXIMUM_SAFE_MEMORY_UTILIZATION = 90 # 90% memory max to avoid OOM
    
    # Scaling Event Quality Metrics
    HPA_SCALING_ACCURACY_TARGET = 95         # 95% scaling accuracy target
    HPA_THRASHING_THRESHOLD_EVENTS_PER_HOUR = 6  # Max 6 scaling events per hour
    HPA_STABLE_PERIOD_MINIMUM_MINUTES = 10   # 10 minutes stable period desired
    
    # =============================================
    # WORKLOAD CLASSIFICATION FOR HPA SUITABILITY
    # =============================================
    
    # Variability Thresholds for HPA Suitability
    HPA_HIGH_VARIABILITY_THRESHOLD = 30      # 30%+ coefficient of variation = high variability
    HPA_MEDIUM_VARIABILITY_THRESHOLD = 15    # 15%+ coefficient of variation = medium variability
    HPA_LOW_VARIABILITY_THRESHOLD = 5        # Below 5% coefficient of variation = low variability
    
    # Traffic Pattern Classification
    HPA_SUITABLE_TRAFFIC_PATTERNS = [
        "periodic_daily",      # Daily traffic patterns
        "periodic_weekly",     # Weekly traffic patterns  
        "event_driven",        # Event-driven spikes
        "gradual_growth",      # Gradual traffic growth
        "bursty_irregular"     # Irregular burst patterns
    ]
    
    HPA_UNSUITABLE_TRAFFIC_PATTERNS = [
        "constant_load",       # Constant steady load
        "extremely_volatile",  # Too volatile to scale effectively
        "single_spike",        # One-time events
        "declining"           # Declining traffic
    ]
    
    # Node Count Requirements
    HPA_MINIMUM_CLUSTER_NODES_FOR_EFFECTIVENESS = 2  # Need at least 2 nodes
    HPA_OPTIMAL_CLUSTER_NODES_FOR_SCALING = 5        # 5+ nodes for optimal scaling
    HPA_LARGE_CLUSTER_NODES_THRESHOLD = 10           # 10+ nodes = large cluster
    
    # Cluster Size Efficiency Impact (efficiency penalties for small clusters)
    HPA_SMALL_CLUSTER_EFFICIENCY_PENALTY = 0.15      # 15% efficiency penalty for small clusters
    HPA_MEDIUM_CLUSTER_EFFICIENCY_PENALTY = 0.05     # 5% efficiency penalty for medium clusters
    HPA_LARGE_CLUSTER_EFFICIENCY_PENALTY = 0.0       # No penalty for large clusters
    
    # =============================================
    # PERFORMANCE SCORING ALGORITHMS
    # =============================================
    
    # Distance-Based Performance Scoring
    HPA_PERFORMANCE_SCORE_MAX_POINTS = 100           # Maximum performance score
    HPA_PERFORMANCE_PENALTY_PER_PERCENT_DEVIATION = 1.5  # 1.5 points lost per % away from target
    
    # Workload Type Weights for Performance Calculation
    HPA_CPU_INTENSIVE_CPU_WEIGHT = 0.8        # 80% weight for CPU in CPU-intensive workloads
    HPA_CPU_INTENSIVE_MEMORY_WEIGHT = 0.2     # 20% weight for memory in CPU-intensive workloads
    HPA_MEMORY_INTENSIVE_CPU_WEIGHT = 0.2     # 20% weight for CPU in memory-intensive workloads  
    HPA_MEMORY_INTENSIVE_MEMORY_WEIGHT = 0.8  # 80% weight for memory in memory-intensive workloads
    HPA_BALANCED_WORKLOAD_CPU_WEIGHT = 0.5    # 50% weight for CPU in balanced workloads
    HPA_BALANCED_WORKLOAD_MEMORY_WEIGHT = 0.5 # 50% weight for memory in balanced workloads
    
    # Coverage Scoring (HPA deployment coverage)
    HPA_COVERAGE_OPTIMAL_PERCENTAGE = 80      # 80% of suitable workloads should have HPA
    HPA_COVERAGE_SCORE_SCALING_FACTOR = 1.25  # Scale factor for coverage impact


class HPACostOptimizationStandards:
    """FinOps cost optimization standards for HPA implementations"""
    
    # =============================================
    # COST SAVINGS CALCULATION STANDARDS
    # =============================================
    
    # Baseline Savings Percentages (Conservative estimates)
    HPA_NO_EXISTING_HPA_SAVINGS_HIGH_SUITABILITY = 0.25    # 25% savings for high-suitability workloads
    HPA_NO_EXISTING_HPA_SAVINGS_MEDIUM_SUITABILITY = 0.15  # 15% savings for medium-suitability workloads
    HPA_NO_EXISTING_HPA_SAVINGS_LOW_SUITABILITY = 0.08     # 8% savings for low-suitability workloads
    
    # Optimization Savings (When HPA already exists)
    HPA_EXISTING_HPA_OPTIMIZATION_SAVINGS = 0.05           # 5% additional optimization savings
    HPA_EXISTING_POORLY_CONFIGURED_SAVINGS = 0.12          # 12% savings from fixing poor HPA config
    HPA_EXISTING_WELL_CONFIGURED_SAVINGS = 0.03            # 3% savings from fine-tuning good HPA config
    
    # Savings Overlap Factors (When combining with other optimizations)
    HPA_SAVINGS_OVERLAP_WITH_RIGHTSIZING = 0.3             # 30% overlap with right-sizing
    HPA_SAVINGS_OVERLAP_WITH_VPA = 0.7                     # 70% overlap with VPA (high conflict)
    HPA_SAVINGS_OVERLAP_WITH_CLUSTER_AUTOSCALER = 0.1      # 10% overlap with cluster autoscaler
    
    # =============================================
    # ROI AND BUSINESS VALUE CALCULATIONS
    # =============================================
    
    # Implementation Costs (Time-based)
    HPA_IMPLEMENTATION_HOURS_SIMPLE = 4         # 4 hours for simple HPA implementation
    HPA_IMPLEMENTATION_HOURS_COMPLEX = 12       # 12 hours for complex HPA with custom metrics
    HPA_IMPLEMENTATION_HOURS_ENTERPRISE = 40    # 40 hours for enterprise-grade HPA setup
    
    # Operational Overhead
    HPA_MONTHLY_OPERATIONAL_OVERHEAD_PERCENT = 0.02  # 2% monthly operational overhead
    HPA_MONITORING_COST_INCREASE_PERCENT = 0.05      # 5% increase in monitoring costs
    
    # Payback Period Targets
    HPA_TARGET_PAYBACK_PERIOD_MONTHS = 3        # 3-month target payback period
    HPA_ACCEPTABLE_PAYBACK_PERIOD_MONTHS = 6    # 6-month acceptable payback period
    HPA_MAXIMUM_PAYBACK_PERIOD_MONTHS = 12      # 12-month maximum payback period
    
    # =============================================
    # COST IMPACT FACTORS
    # =============================================
    
    # Workload Size Impact on Savings
    HPA_LARGE_WORKLOAD_SAVINGS_MULTIPLIER = 1.2      # 20% more savings for large workloads
    HPA_MEDIUM_WORKLOAD_SAVINGS_MULTIPLIER = 1.0     # Standard savings for medium workloads
    HPA_SMALL_WORKLOAD_SAVINGS_MULTIPLIER = 0.8      # 20% less savings for small workloads
    
    # Environment Impact on Savings  
    HPA_PRODUCTION_ENVIRONMENT_MULTIPLIER = 1.0      # Standard savings in production
    HPA_STAGING_ENVIRONMENT_MULTIPLIER = 0.7         # 30% less savings in staging
    HPA_DEVELOPMENT_ENVIRONMENT_MULTIPLIER = 0.5     # 50% less savings in development
    
    # Geographic Region Cost Factors
    HPA_HIGH_COST_REGION_MULTIPLIER = 1.3            # 30% more savings in expensive regions
    HPA_MEDIUM_COST_REGION_MULTIPLIER = 1.0          # Standard savings in medium-cost regions
    HPA_LOW_COST_REGION_MULTIPLIER = 0.8             # 20% less savings in low-cost regions


class HPAMonitoringStandards:
    """Monitoring and observability standards for HPA implementations"""
    
    # =============================================
    # KEY PERFORMANCE INDICATORS (KPIs)
    # =============================================
    
    # Scaling Event Metrics
    HPA_SCALING_SUCCESS_RATE_TARGET = 0.98      # 98% scaling success rate
    HPA_SCALING_LATENCY_TARGET_SECONDS = 45     # 45 seconds max scaling latency
    HPA_FALSE_POSITIVE_SCALING_RATE_MAX = 0.05  # 5% max false positive scaling
    
    # Resource Efficiency Metrics
    HPA_RESOURCE_WASTE_PERCENTAGE_MAX = 10      # Maximum 10% resource waste
    HPA_RESOURCE_SHORTAGE_PERCENTAGE_MAX = 5    # Maximum 5% resource shortage
    HPA_UTILIZATION_VARIANCE_TARGET = 0.15      # 15% max variance in utilization
    
    # Business Impact Metrics
    HPA_SERVICE_AVAILABILITY_TARGET = 0.999     # 99.9% service availability
    HPA_RESPONSE_TIME_DEGRADATION_MAX = 0.1     # Maximum 10% response time increase
    HPA_ERROR_RATE_INCREASE_MAX = 0.01          # Maximum 1% error rate increase
    
    # =============================================
    # ALERTING THRESHOLDS
    # =============================================
    
    # Critical Alerts
    HPA_CRITICAL_SCALING_FAILURE_THRESHOLD = 3       # 3 consecutive scaling failures
    HPA_CRITICAL_RESOURCE_EXHAUSTION_THRESHOLD = 95  # 95% resource utilization
    HPA_CRITICAL_RESPONSE_TIME_INCREASE = 2.0        # 200% response time increase
    
    # Warning Alerts
    HPA_WARNING_FREQUENT_SCALING_THRESHOLD = 10      # 10 scaling events per hour
    HPA_WARNING_SUBOPTIMAL_UTILIZATION_THRESHOLD = 30 # 30% deviation from target
    HPA_WARNING_COST_INCREASE_THRESHOLD = 0.15       # 15% cost increase
    
    # =============================================
    # DASHBOARD AND REPORTING REQUIREMENTS
    # =============================================
    
    # Real-time Metrics (Update frequency)
    HPA_REALTIME_METRICS_UPDATE_SECONDS = 15    # 15-second real-time updates
    HPA_HISTORICAL_METRICS_RETENTION_DAYS = 90  # 90 days historical data retention
    HPA_DETAILED_LOGS_RETENTION_DAYS = 30       # 30 days detailed logs retention
    
    # Dashboard Components Required
    HPA_REQUIRED_DASHBOARD_COMPONENTS = [
        "replica_count_over_time",      # Replica count timeline
        "resource_utilization_metrics", # CPU/Memory utilization
        "scaling_events_timeline",      # Scaling events history
        "cost_impact_visualization",    # Cost savings visualization
        "performance_impact_metrics",   # Performance impact metrics
        "efficiency_score_trending",    # HPA efficiency trending
        "alert_summary_panel"          # Active alerts summary
    ]


class HPAComplianceStandards:
    """Compliance and governance standards for HPA implementations"""
    
    # =============================================
    # SECURITY AND COMPLIANCE REQUIREMENTS
    # =============================================
    
    # RBAC Requirements
    HPA_RBAC_MINIMUM_REQUIRED_PERMISSIONS = [
        "autoscaling/horizontalpodautoscalers/get",
        "autoscaling/horizontalpodautoscalers/list", 
        "autoscaling/horizontalpodautoscalers/watch",
        "apps/deployments/scale",
        "apps/replicasets/scale",
        "metrics.k8s.io/pods/get",
        "metrics.k8s.io/nodes/get"
    ]
    
    # Audit Requirements
    HPA_AUDIT_LOG_RETENTION_DAYS = 365          # 1 year audit log retention
    HPA_CONFIGURATION_CHANGE_APPROVAL = True    # Require approval for config changes
    HPA_SCALING_EVENT_AUDIT_LOGGING = True      # Log all scaling events
    
    # =============================================
    # POLICY ENFORCEMENT
    # =============================================
    
    # Resource Limits Policy
    HPA_ENFORCE_MAXIMUM_REPLICAS_LIMIT = True        # Enforce max replica limits
    HPA_ENFORCE_MINIMUM_REPLICAS_REQUIREMENT = True  # Enforce min replica requirements
    HPA_ENFORCE_RESOURCE_QUOTA_COMPLIANCE = True     # Enforce namespace resource quotas
    
    # Configuration Validation Policy
    HPA_REQUIRE_VALID_METRICS_CONFIGURATION = True   # Validate metrics config
    HPA_REQUIRE_SCALING_POLICY_DEFINITION = True     # Require scaling policies
    HPA_PROHIBIT_AGGRESSIVE_SCALING_IN_PROD = True   # Prevent aggressive scaling in production


# =============================================
# IMPLEMENTATION GUIDANCE AND EXAMPLES
# =============================================

class HPAImplementationPatterns:
    """Common HPA implementation patterns and examples"""
    
    # =============================================
    # BASIC HPA CONFIGURATIONS
    # =============================================
    
    BASIC_CPU_HPA_TEMPLATE = {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler", 
        "metadata": {"name": "example-hpa"},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": "Deployment", 
                "name": "example-deployment"
            },
            "minReplicas": HPAConfigurationStandards.HPA_MIN_REPLICAS_PRODUCTION,
            "maxReplicas": HPAConfigurationStandards.HPA_MAX_REPLICAS_SMALL_WORKLOAD,
            "metrics": [
                {
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": HPAConfigurationStandards.HPA_CPU_TARGET_WEB_SERVERS
                        }
                    }
                }
            ]
        }
    }
    
    # =============================================
    # ADVANCED HPA CONFIGURATIONS
    # =============================================
    
    ADVANCED_MULTI_METRIC_HPA_TEMPLATE = {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {"name": "advanced-hpa"},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1", 
                "kind": "Deployment",
                "name": "example-deployment"
            },
            "minReplicas": HPAConfigurationStandards.HPA_MIN_REPLICAS_PRODUCTION,
            "maxReplicas": HPAConfigurationStandards.HPA_MAX_REPLICAS_MEDIUM_WORKLOAD,
            "metrics": [
                {
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": HPAConfigurationStandards.HPA_CPU_TARGET_API_SERVICES
                        }
                    }
                },
                {
                    "type": "Resource", 
                    "resource": {
                        "name": "memory",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": HPAConfigurationStandards.HPA_MEMORY_TARGET_API_SERVICES
                        }
                    }
                }
            ],
            "behavior": {
                "scaleUp": {
                    "stabilizationWindowSeconds": HPAAlgorithmStandards.HPA_SCALE_UP_STABILIZATION_SECONDS,
                    "policies": [
                        {
                            "type": "Percent",
                            "value": HPAConfigurationStandards.HPA_SCALE_UP_CONSERVATIVE_PERCENT,
                            "periodSeconds": HPAConfigurationStandards.HPA_SCALE_UP_CONSERVATIVE_PERIOD
                        },
                        {
                            "type": "Pods",
                            "value": HPAConfigurationStandards.HPA_SCALE_UP_CONSERVATIVE_PODS,
                            "periodSeconds": HPAConfigurationStandards.HPA_SCALE_UP_CONSERVATIVE_PERIOD
                        }
                    ],
                    "selectPolicy": "Max"
                },
                "scaleDown": {
                    "stabilizationWindowSeconds": HPAAlgorithmStandards.HPA_SCALE_DOWN_STABILIZATION_SECONDS,
                    "policies": [
                        {
                            "type": "Percent", 
                            "value": HPAConfigurationStandards.HPA_SCALE_DOWN_CONSERVATIVE_PERCENT,
                            "periodSeconds": HPAConfigurationStandards.HPA_SCALE_DOWN_CONSERVATIVE_PERIOD
                        },
                        {
                            "type": "Pods",
                            "value": HPAConfigurationStandards.HPA_SCALE_DOWN_CONSERVATIVE_PODS,
                            "periodSeconds": HPAConfigurationStandards.HPA_SCALE_DOWN_CONSERVATIVE_PERIOD
                        }
                    ],
                    "selectPolicy": "Min"
                }
            }
        }
    }


# =============================================
# USAGE EXAMPLES
# =============================================

"""
HPA STANDARDS USAGE EXAMPLES:
=============================

BASIC VALIDATION:
-----------------
from shared.standards.hpa_industry_standards import HPAAlgorithmStandards

def validate_hpa_tolerance(current_utilization, target_utilization):
    tolerance = HPAAlgorithmStandards.HPA_TOLERANCE_PERCENTAGE / 100
    difference_percent = abs(current_utilization - target_utilization) / target_utilization
    return difference_percent <= tolerance

EFFICIENCY CALCULATION:
----------------------
from shared.standards.hpa_industry_standards import HPAPerformanceStandards

def calculate_hpa_efficiency(cpu_utilization, memory_utilization, workload_type):
    optimal_cpu = HPAPerformanceStandards.HPA_OPTIMAL_CPU_UTILIZATION
    optimal_memory = HPAPerformanceStandards.HPA_OPTIMAL_MEMORY_UTILIZATION
    
    cpu_deviation = abs(cpu_utilization - optimal_cpu)
    memory_deviation = abs(memory_utilization - optimal_memory)
    
    penalty_per_percent = HPAPerformanceStandards.HPA_PERFORMANCE_PENALTY_PER_PERCENT_DEVIATION
    
    cpu_score = max(0, 100 - (cpu_deviation * penalty_per_percent))
    memory_score = max(0, 100 - (memory_deviation * penalty_per_percent))
    
    if workload_type == "CPU_INTENSIVE":
        return (cpu_score * HPAPerformanceStandards.HPA_CPU_INTENSIVE_CPU_WEIGHT + 
                memory_score * HPAPerformanceStandards.HPA_CPU_INTENSIVE_MEMORY_WEIGHT)
    elif workload_type == "MEMORY_INTENSIVE": 
        return (cpu_score * HPAPerformanceStandards.HPA_MEMORY_INTENSIVE_CPU_WEIGHT +
                memory_score * HPAPerformanceStandards.HPA_MEMORY_INTENSIVE_MEMORY_WEIGHT)
    else:
        return (cpu_score * HPAPerformanceStandards.HPA_BALANCED_WORKLOAD_CPU_WEIGHT +
                memory_score * HPAPerformanceStandards.HPA_BALANCED_WORKLOAD_MEMORY_WEIGHT)

COST SAVINGS CALCULATION:
-------------------------
from shared.standards.hpa_industry_standards import HPACostOptimizationStandards

def calculate_hpa_savings(node_cost, hpa_exists, suitability_score, workload_size):
    if hpa_exists:
        base_savings = node_cost * HPACostOptimizationStandards.HPA_EXISTING_HPA_OPTIMIZATION_SAVINGS
    else:
        if suitability_score > 80:
            savings_rate = HPACostOptimizationStandards.HPA_NO_EXISTING_HPA_SAVINGS_HIGH_SUITABILITY
        elif suitability_score > 50:
            savings_rate = HPACostOptimizationStandards.HPA_NO_EXISTING_HPA_SAVINGS_MEDIUM_SUITABILITY
        else:
            savings_rate = HPACostOptimizationStandards.HPA_NO_EXISTING_HPA_SAVINGS_LOW_SUITABILITY
        base_savings = node_cost * savings_rate
    
    # Apply workload size multiplier
    if workload_size == "large":
        multiplier = HPACostOptimizationStandards.HPA_LARGE_WORKLOAD_SAVINGS_MULTIPLIER
    elif workload_size == "small":
        multiplier = HPACostOptimizationStandards.HPA_SMALL_WORKLOAD_SAVINGS_MULTIPLIER
    else:
        multiplier = HPACostOptimizationStandards.HPA_MEDIUM_WORKLOAD_SAVINGS_MULTIPLIER
    
    return base_savings * multiplier
"""