"""
Cost Optimization Standards for AKS
===================================

Comprehensive cost optimization standards including FinOps practices,
cost calculation methodologies, savings targets, and financial governance.
"""

class CostCalculationStandards:
    """Cost calculation methodologies and formulas"""
    
    # =============================================
    # COST CALCULATION FORMULAS
    # =============================================
    
    # Basic Cost Calculations
    MONTHLY_HOURS = 730                    # Average hours per month
    DAILY_HOURS = 24                       # Hours per day
    WEEKLY_HOURS = 168                     # Hours per week
    ANNUAL_MONTHS = 12                     # Months per year
    
    # Azure Pricing Constants
    AZURE_COMPUTE_UNIT_MULTIPLIER = 1.0    # Base compute unit cost multiplier
    AZURE_STORAGE_GB_MONTHLY_BASE = 0.045  # Base storage cost per GB/month
    AZURE_BANDWIDTH_GB_COST = 0.087       # Bandwidth cost per GB
    AZURE_LOAD_BALANCER_MONTHLY = 22.00   # Standard Load Balancer monthly cost
    
    # Resource Cost Calculations
    CPU_COST_PER_CORE_HOUR = 0.0342       # Average CPU cost per core/hour
    MEMORY_COST_PER_GB_HOUR = 0.0046      # Average memory cost per GB/hour
    STORAGE_PREMIUM_SSD_GB_MONTH = 0.135  # Premium SSD cost per GB/month
    STORAGE_STANDARD_SSD_GB_MONTH = 0.045 # Standard SSD cost per GB/month
    
    # =============================================
    # COST OPTIMIZATION TARGETS
    # =============================================
    
    # Utilization-Based Cost Targets
    OPTIMAL_CPU_UTILIZATION = 70          # 70% optimal CPU utilization
    OPTIMAL_MEMORY_UTILIZATION = 75       # 75% optimal memory utilization
    OPTIMAL_STORAGE_UTILIZATION = 80      # 80% optimal storage utilization
    OPTIMAL_NETWORK_UTILIZATION = 65      # 65% optimal network utilization
    
    # Cost Efficiency Targets
    TARGET_COST_PER_WORKLOAD_MONTH = 45   # $45/month target cost per workload
    TARGET_COST_PER_CPU_CORE_MONTH = 15   # $15/month target cost per CPU core
    TARGET_COST_PER_GB_MEMORY_MONTH = 2   # $2/month target cost per GB memory
    TARGET_COST_PER_GB_STORAGE_MONTH = 0.1 # $0.10/month target cost per GB storage
    
    # =============================================
    # SAVINGS CALCULATION STANDARDS
    # =============================================
    
    # Maximum Savings Thresholds
    MAX_TOTAL_SAVINGS_PERCENTAGE = 60     # Maximum 60% total cost savings
    MAX_VALIDATED_SAVINGS_PERCENTAGE = 70 # Maximum 70% after validation
    MAX_SINGLE_CATEGORY_SAVINGS = 50      # Maximum 50% savings in one category
    
    # Savings Distribution Standards
    HPA_SAVINGS_WEIGHT = 0.3              # 30% weight for HPA savings
    RIGHTSIZING_SAVINGS_WEIGHT = 0.5      # 50% weight for right-sizing savings
    STORAGE_SAVINGS_WEIGHT = 0.15         # 15% weight for storage savings
    NETWORKING_SAVINGS_WEIGHT = 0.05      # 5% weight for networking savings
    
    # Conservative Savings Multipliers
    CONSERVATIVE_SAVINGS_FACTOR = 0.7     # 70% of calculated savings (conservative)
    MODERATE_SAVINGS_FACTOR = 0.85        # 85% of calculated savings (moderate)
    AGGRESSIVE_SAVINGS_FACTOR = 1.0       # 100% of calculated savings (aggressive)


class HorizontalPodAutoscalerCostStandards:
    """HPA-specific cost optimization standards"""
    
    # =============================================
    # HPA COST OPTIMIZATION
    # =============================================
    
    # HPA Scaling Cost Efficiency
    HPA_COST_EFFICIENCY_TARGET = 80       # 80% cost efficiency target
    HPA_OVER_PROVISIONING_THRESHOLD = 150 # 150% = over-provisioned
    HPA_UNDER_PROVISIONING_THRESHOLD = 90 # 90% = under-provisioned
    
    # HPA Savings Calculations
    TYPICAL_HPA_SAVINGS_PERCENTAGE = 15   # 15% typical HPA savings
    OPTIMAL_HPA_SAVINGS_PERCENTAGE = 25   # 25% optimal HPA savings
    MAXIMUM_HPA_SAVINGS_PERCENTAGE = 40   # 40% maximum HPA savings
    
    # HPA Cost Thresholds
    MIN_WORKLOAD_COST_FOR_HPA = 20        # $20/month minimum for HPA optimization
    HPA_IMPLEMENTATION_COST = 5           # $5/month HPA implementation overhead
    
    # Scaling Behavior Cost Impact
    SCALE_UP_COST_MULTIPLIER = 1.2        # 20% cost increase during scale up
    SCALE_DOWN_SAVINGS_MULTIPLIER = 0.8   # 20% savings during scale down
    IDLE_REPLICA_COST_FACTOR = 0.1        # 10% cost for idle replicas


class RightSizingCostStandards:
    """Resource right-sizing cost optimization standards"""
    
    # =============================================
    # RIGHT-SIZING COST OPTIMIZATION
    # =============================================
    
    # Right-sizing Opportunities
    OVERSIZED_CPU_THRESHOLD = 120         # 120% = oversized CPU
    UNDERSIZED_CPU_THRESHOLD = 80         # 80% = undersized CPU
    OVERSIZED_MEMORY_THRESHOLD = 125      # 125% = oversized memory
    UNDERSIZED_MEMORY_THRESHOLD = 85      # 85% = undersized memory
    
    # Right-sizing Savings Calculations
    TYPICAL_RIGHTSIZING_SAVINGS = 25      # 25% typical right-sizing savings
    OPTIMAL_RIGHTSIZING_SAVINGS = 35      # 35% optimal right-sizing savings
    MAXIMUM_RIGHTSIZING_SAVINGS = 50      # 50% maximum right-sizing savings
    
    # Right-sizing Cost Thresholds
    MIN_RESOURCE_COST_FOR_RIGHTSIZING = 10 # $10/month minimum for right-sizing
    RIGHTSIZING_ANALYSIS_COST = 2         # $2/month analysis overhead
    
    # Resource Adjustment Factors
    CPU_DOWNSIZE_SAVINGS_FACTOR = 0.6     # 60% savings when downsizing CPU
    MEMORY_DOWNSIZE_SAVINGS_FACTOR = 0.5  # 50% savings when downsizing memory
    UPSIZE_COST_PENALTY_FACTOR = 1.3      # 30% cost penalty when upsizing


class StorageCostStandards:
    """Storage cost optimization standards"""
    
    # =============================================
    # STORAGE COST OPTIMIZATION
    # =============================================
    
    # Storage Utilization Thresholds
    STORAGE_UNDERUTILIZED_THRESHOLD = 30  # 30% = underutilized storage
    STORAGE_OVERPROVISIONED_THRESHOLD = 90 # 90% = overprovisioned storage
    STORAGE_OPTIMAL_UTILIZATION = 80      # 80% optimal storage utilization
    
    # Storage Tier Optimization
    PREMIUM_TO_STANDARD_SAVINGS = 0.67    # 67% savings moving to standard
    STANDARD_TO_BASIC_SAVINGS = 0.33      # 33% savings moving to basic
    TIER_MIGRATION_COST = 5               # $5 one-time migration cost
    
    # Storage Cleanup Savings
    UNUSED_STORAGE_CLEANUP_SAVINGS = 1.0  # 100% savings from cleanup
    ORPHANED_DISK_CLEANUP_SAVINGS = 1.0   # 100% savings from orphaned disks
    SNAPSHOT_CLEANUP_SAVINGS = 0.8        # 80% savings from snapshot cleanup
    
    # Storage Performance vs Cost
    IOPS_COST_FACTOR = 0.0001             # $0.0001 per IOPS per month
    THROUGHPUT_COST_FACTOR = 0.01         # $0.01 per MB/s per month
    
    # REALISTIC Storage Optimization Standards (Used in Analysis)
    STORAGE_MIN_COST_FOR_OPTIMIZATION = 100   # $100 minimum storage cost for optimization
    STORAGE_RIGHTSIZING_OPTIMIZATION = 0.08   # 8% savings from volume right-sizing
    STORAGE_CLASS_OPTIMIZATION = 0.12         # 12% savings from storage class optimization
    STORAGE_MAX_OPTIMIZATION_PCT = 0.25       # Maximum 25% total storage optimization


class NetworkingCostStandards:
    """Networking cost optimization standards"""
    
    # =============================================
    # NETWORKING COST OPTIMIZATION
    # =============================================
    
    # Networking Cost Components
    LOAD_BALANCER_MONTHLY_COST = 22.0     # $22/month Standard Load Balancer
    PUBLIC_IP_MONTHLY_COST = 3.65         # $3.65/month Public IP
    NAT_GATEWAY_MONTHLY_COST = 45.0       # $45/month NAT Gateway
    VPN_GATEWAY_MONTHLY_COST = 27.0       # $27/month VPN Gateway
    
    # Bandwidth Cost Optimization
    INBOUND_BANDWIDTH_FREE_GB = 5120      # 5TB free inbound bandwidth
    OUTBOUND_BANDWIDTH_COST_PER_GB = 0.087 # $0.087 per GB outbound
    INTER_ZONE_BANDWIDTH_COST_PER_GB = 0.01 # $0.01 per GB inter-zone
    
    # Network Optimization Thresholds
    LOAD_BALANCER_UTILIZATION_THRESHOLD = 50 # 50% load balancer utilization
    BANDWIDTH_UTILIZATION_THRESHOLD = 70     # 70% bandwidth utilization
    
    # Network Savings Opportunities
    LOAD_BALANCER_CONSOLIDATION_SAVINGS = 0.4 # 40% savings from consolidation
    TRAFFIC_OPTIMIZATION_SAVINGS = 0.15       # 15% savings from traffic optimization
    CDN_IMPLEMENTATION_SAVINGS = 0.25         # 25% savings from CDN
    
    # REALISTIC Network Optimization Standards (Used in Analysis)
    NETWORK_CONSERVATIVE_OPTIMIZATION = 0.05  # 5% conservative networking optimization
    NETWORK_OPTIMIZATION_MIN_COST = 200       # $200 minimum networking cost for optimization
    NETWORK_OPTIMIZATION_MIN_NODES = 3        # Minimum 3 nodes for network optimization
    NETWORK_OPTIMIZATION_MAX_CPU = 50         # Maximum 50% CPU utilization for network optimization


class NodePoolCostStandards:
    """Node pool cost optimization standards"""
    
    # =============================================
    # NODE POOL COST OPTIMIZATION
    # =============================================
    
    # Node Pool Utilization Targets
    NODE_CPU_UTILIZATION_TARGET = 70      # 70% target CPU utilization
    NODE_MEMORY_UTILIZATION_TARGET = 75   # 75% target memory utilization
    NODE_EFFICIENCY_TARGET = 80           # 80% overall node efficiency
    
    # Node Pool Consolidation
    NODE_CONSOLIDATION_THRESHOLD = 40     # 40% utilization for consolidation
    MIN_NODES_FOR_CONSOLIDATION = 2       # Minimum 2 nodes for consolidation
    CONSOLIDATION_SAVINGS_FACTOR = 0.15   # 15% savings from consolidation
    
    # Spot Instance Savings
    SPOT_INSTANCE_SAVINGS = 0.8           # 80% savings with spot instances
    SPOT_INSTANCE_RISK_FACTOR = 0.1       # 10% risk factor for spot instances
    
    # Reserved Instance Savings
    RESERVED_INSTANCE_1_YEAR_SAVINGS = 0.25 # 25% savings 1-year reserved
    RESERVED_INSTANCE_3_YEAR_SAVINGS = 0.45 # 45% savings 3-year reserved


class FinOpsStandards:
    """Financial Operations (FinOps) standards and practices"""
    
    # =============================================
    # FINOPS MATURITY LEVELS
    # =============================================
    
    # FinOps Maturity Framework
    FINOPS_CRAWL_MATURITY = 1             # Basic cost visibility
    FINOPS_WALK_MATURITY = 2              # Process optimization
    FINOPS_RUN_MATURITY = 3               # Advanced cost management
    
    # Cost Visibility Standards
    COST_ALLOCATION_ACCURACY_TARGET = 95  # 95% cost allocation accuracy
    COST_TRANSPARENCY_TARGET = 98         # 98% cost transparency
    BUDGET_TRACKING_ACCURACY = 99         # 99% budget tracking accuracy
    
    # =============================================
    # FINOPS KPIS AND METRICS
    # =============================================
    
    # Financial KPIs
    UNIT_ECONOMICS_ACCURACY = 90          # 90% unit economics accuracy
    COST_PER_CUSTOMER_VARIANCE = 5        # 5% cost per customer variance
    RESOURCE_UTILIZATION_TARGET = 75      # 75% overall resource utilization
    
    # Budget Management
    BUDGET_VARIANCE_ALERT_THRESHOLD = 10  # 10% budget variance alert
    FORECAST_ACCURACY_TARGET = 95         # 95% forecast accuracy
    COST_ANOMALY_DETECTION_THRESHOLD = 20 # 20% cost anomaly threshold
    
    # =============================================
    # COST GOVERNANCE
    # =============================================
    
    # Approval Thresholds
    SMALL_COST_APPROVAL_THRESHOLD = 100   # $100 - No approval needed
    MEDIUM_COST_APPROVAL_THRESHOLD = 1000 # $1000 - Manager approval
    LARGE_COST_APPROVAL_THRESHOLD = 10000 # $10000 - Director approval
    
    # Cost Control Policies
    AUTO_SHUTDOWN_SAVINGS = 0.6           # 60% savings from auto-shutdown
    COST_OPTIMIZATION_REVIEW_FREQUENCY = 30 # 30 days review frequency
    WASTE_ELIMINATION_TARGET = 0.2        # 20% waste elimination target


class ControlPlaneCostStandards:
    """Control plane cost optimization standards"""
    
    # =============================================
    # CONTROL PLANE TIER OPTIMIZATION
    # =============================================
    
    # Control Plane Optimization Criteria
    CONTROL_PLANE_TIER_OPTIMIZATION = 0.3     # 30% potential tier savings
    CONTROL_PLANE_MAX_TIER_SAVINGS = 100      # $100 maximum tier savings
    CONTROL_PLANE_MIN_COST = 200              # $200 minimum cost for optimization
    
    # Small Cluster Criteria for Free Tier
    CONTROL_PLANE_MAX_NODES_FREE_TIER = 2     # Maximum 2 nodes for free tier
    CONTROL_PLANE_MAX_WORKLOADS_FREE_TIER = 10 # Maximum 10 workloads for free tier
    
    # SLA Considerations
    CONTROL_PLANE_FREE_TIER_SLA = 99.5        # 99.5% SLA for free tier
    CONTROL_PLANE_STANDARD_TIER_SLA = 99.95   # 99.95% SLA for standard tier


class ContainerRegistryCostStandards:
    """Container registry cost optimization standards"""
    
    # =============================================
    # REGISTRY CLEANUP OPTIMIZATION
    # =============================================
    
    # Registry Optimization Opportunities
    REGISTRY_CLEANUP_SAVINGS = 0.2            # 20% savings from cleanup
    REGISTRY_IMAGE_OPTIMIZATION = 0.15        # 15% savings from image optimization
    REGISTRY_DEDUPLICATION_SAVINGS = 0.40     # 40% savings from layer deduplication
    
    # REALISTIC Registry Optimization Standards (Used in Analysis)
    REGISTRY_CLEANUP_OPTIMIZATION = 0.10      # 10% conservative cleanup optimization
    REGISTRY_COST_PER_WORKLOAD_THRESHOLD = 2.0  # $2 per workload threshold
    REGISTRY_MIN_COST_FOR_OPTIMIZATION = 50   # $50 minimum registry cost for optimization
    REGISTRY_RETENTION_OPTIMIZATION = 0.1     # 10% savings from retention policies
    
    # Registry Size Criteria  
    REGISTRY_MIN_COST_OPTIMIZATION = 100      # $100 minimum registry cost
    REGISTRY_EXCESSIVE_COST_MULTIPLIER = 2    # 2x expected cost = excessive


class AdvancedOptimizationStandards:
    """Advanced optimization strategies for modern AKS environments"""
    
    # =============================================
    # BIN-PACKING AND CONSOLIDATION
    # =============================================
    
    # Node consolidation thresholds
    NODE_FRAGMENTATION_THRESHOLD = 0.4        # 40% fragmentation triggers bin-packing
    NODE_UTILIZATION_VARIANCE_THRESHOLD = 0.3 # 30% variance triggers consolidation
    BIN_PACKING_EFFICIENCY_TARGET = 0.85      # 85% bin-packing efficiency target
    
    # Savings from consolidation
    BIN_PACKING_BASE_SAVINGS = 0.12           # 12% base savings from bin-packing
    NODE_CONSOLIDATION_SAVINGS = 0.08         # 8% savings from consolidation
    
    # =============================================
    # PREDICTIVE AND COST-AWARE SCALING
    # =============================================
    
    # Seasonality and pattern detection
    WORKLOAD_SEASONALITY_THRESHOLD = 0.3      # 30% seasonality for predictive scaling
    PREDICTIVE_SCALING_ADDITIONAL_SAVINGS = 0.25  # 25% additional savings
    
    # Cross-zone optimization
    CROSS_ZONE_TRAFFIC_THRESHOLD = 50         # $50 threshold for zone optimization
    ZONE_OPTIMIZATION_SAVINGS = 0.4           # 40% of inter-zone costs can be saved
    
    # =============================================
    # SERVICE MESH AND ADDON OPTIMIZATION
    # =============================================
    
    # Service mesh overhead thresholds
    SERVICE_MESH_OVERHEAD_THRESHOLD = 15      # 15% overhead threshold
    SERVICE_MESH_OPTIMIZATION_SAVINGS = 0.08  # 8% savings from mesh optimization
    
    # Gateway and ingress optimization
    API_GATEWAY_MONTHLY_COST = 45             # $45/month per API Gateway
    INGRESS_CONTROLLER_MONTHLY_COST = 20      # $20/month per ingress controller
    
    # Container image optimization
    LARGE_IMAGE_OPTIMIZATION_SAVINGS = 3      # $3/month per large image
    STALE_IMAGE_CLEANUP_SAVINGS = 2           # $2/month per stale image
    
    # =============================================
    # IDLE RESOURCE DETECTION THRESHOLDS
    # =============================================
    
    # Advanced idle resource detection
    ZOMBIE_SERVICE_CLEANUP_SAVINGS = 8        # $8/month per zombie service
    LOAD_BALANCER_CONSOLIDATION_SAVINGS = 22  # $22/month per LB consolidated
    ORPHANED_PV_CLEANUP_SAVINGS = 15          # $15/month per orphaned PV


class CostSavingsTargetStandards:
    """Specific cost savings targets and benchmarks"""
    
    # =============================================
    # ANNUAL SAVINGS TARGETS
    # =============================================
    
    # Overall Savings Targets
    ANNUAL_COST_REDUCTION_TARGET = 30     # 30% annual cost reduction
    QUARTERLY_SAVINGS_TARGET = 8          # 8% quarterly savings
    MONTHLY_OPTIMIZATION_TARGET = 2       # 2% monthly optimization
    
    # Category-Specific Annual Targets
    COMPUTE_SAVINGS_TARGET = 25           # 25% compute savings target
    STORAGE_SAVINGS_TARGET = 20           # 20% storage savings target
    NETWORKING_SAVINGS_TARGET = 15        # 15% networking savings target
    LICENSING_SAVINGS_TARGET = 30         # 30% licensing savings target
    
    # =============================================
    # INDUSTRY BENCHMARK SAVINGS
    # =============================================
    
    # Industry Average Savings
    INDUSTRY_AVERAGE_CLOUD_SAVINGS = 23   # 23% industry average
    ENTERPRISE_TYPICAL_SAVINGS = 25       # 25% enterprise typical
    STARTUP_AGGRESSIVE_SAVINGS = 40       # 40% startup aggressive
    SMB_CONSERVATIVE_SAVINGS = 15         # 15% SMB conservative
    
    # Best-in-Class Savings
    BEST_IN_CLASS_TOTAL_SAVINGS = 45      # 45% best-in-class total
    BEST_IN_CLASS_COMPUTE_SAVINGS = 35    # 35% best-in-class compute
    BEST_IN_CLASS_STORAGE_SAVINGS = 40    # 40% best-in-class storage
    
    # =============================================
    # ROI AND PAYBACK STANDARDS
    # =============================================
    
    # Return on Investment Targets
    COST_OPTIMIZATION_ROI_TARGET = 300    # 300% ROI target (3:1 return)
    MINIMUM_ACCEPTABLE_ROI = 200          # 200% minimum ROI (2:1 return)
    EXCELLENT_ROI_THRESHOLD = 500         # 500% excellent ROI (5:1 return)
    
    # Payback Period Targets
    TARGET_PAYBACK_PERIOD_MONTHS = 6      # 6 months target payback
    MAXIMUM_PAYBACK_PERIOD_MONTHS = 12    # 12 months maximum payback
    EXCELLENT_PAYBACK_PERIOD_MONTHS = 3   # 3 months excellent payback


class CostAllocationStandards:
    """Cost allocation and chargeback standards"""
    
    # =============================================
    # COST ALLOCATION METHODOLOGY
    # =============================================
    
    # Allocation Methods
    DIRECT_COST_ALLOCATION = "Direct"      # Direct cost allocation
    PROPORTIONAL_ALLOCATION = "Proportional" # Proportional allocation
    USAGE_BASED_ALLOCATION = "Usage"       # Usage-based allocation
    
    # Allocation Accuracy Targets
    ALLOCATION_ACCURACY_TARGET = 95        # 95% allocation accuracy
    ALLOCATION_VARIANCE_THRESHOLD = 5      # 5% allocation variance
    
    # =============================================
    # CHARGEBACK AND SHOWBACK
    # =============================================
    
    # Chargeback Standards
    CHARGEBACK_FREQUENCY = "Monthly"       # Monthly chargeback
    CHARGEBACK_ACCURACY_TARGET = 98        # 98% chargeback accuracy
    CHARGEBACK_DISPUTE_THRESHOLD = 2       # 2% dispute threshold
    
    # Showback Standards
    SHOWBACK_DETAIL_LEVEL = "Resource"     # Resource-level showback
    SHOWBACK_UPDATE_FREQUENCY = "Daily"    # Daily showback updates
    SHOWBACK_RETENTION_MONTHS = 24         # 24 months showback retention


# =============================================
# COST OPTIMIZATION CALCULATION FORMULAS
# =============================================

class CostOptimizationFormulas:
    """Mathematical formulas for cost optimization calculations"""
    
    @staticmethod
    def calculate_monthly_savings(current_cost: float, optimized_cost: float) -> float:
        """Calculate monthly savings amount"""
        return max(0, current_cost - optimized_cost)
    
    @staticmethod
    def calculate_savings_percentage(current_cost: float, savings: float) -> float:
        """Calculate savings percentage"""
        if current_cost <= 0:
            return 0
        return min(100, (savings / current_cost) * 100)
    
    @staticmethod
    def calculate_annual_savings(monthly_savings: float) -> float:
        """Calculate annual savings from monthly"""
        return monthly_savings * CostCalculationStandards.ANNUAL_MONTHS
    
    @staticmethod
    def calculate_roi(savings: float, investment: float) -> float:
        """Calculate return on investment"""
        if investment <= 0:
            return 0
        return (savings / investment) * 100
    
    @staticmethod
    def calculate_payback_period_months(investment: float, monthly_savings: float) -> float:
        """Calculate payback period in months"""
        if monthly_savings <= 0:
            return float('inf')
        return investment / monthly_savings
    
    @staticmethod
    def apply_confidence_factor(savings: float, confidence: float) -> float:
        """Apply confidence factor to savings calculation"""
        return savings * max(0, min(1, confidence))


# =============================================
# USAGE EXAMPLES AND BEST PRACTICES
# =============================================
"""
USAGE EXAMPLES:
===============

from standards.cost_optimization_standards import CostCalculationStandards as CostStds
from standards.cost_optimization_standards import CostOptimizationFormulas as Formulas

# Calculate HPA savings
current_monthly_cost = 1000
optimized_monthly_cost = 750
hpa_savings = Formulas.calculate_monthly_savings(current_monthly_cost, optimized_monthly_cost)
savings_percentage = Formulas.calculate_savings_percentage(current_monthly_cost, hpa_savings)

# Validate against standards
if savings_percentage > CostStds.MAX_TOTAL_SAVINGS_PERCENTAGE:
    logger.warning(f"Savings percentage {savings_percentage}% exceeds maximum {CostStds.MAX_TOTAL_SAVINGS_PERCENTAGE}%")

# Calculate ROI
implementation_cost = 500
monthly_savings = 250
annual_savings = Formulas.calculate_annual_savings(monthly_savings)
roi = Formulas.calculate_roi(annual_savings, implementation_cost)

BEST PRACTICES:
===============

1. Always validate calculated savings against maximum thresholds
2. Apply appropriate confidence factors to savings estimates
3. Consider implementation costs in ROI calculations
4. Use conservative factors for customer-facing estimates
5. Document assumptions and methodologies used
6. Regular review and update of cost standards
7. Benchmark against industry standards
"""