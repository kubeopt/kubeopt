"""
AKS Cost Optimization Input Schema
Comprehensive Pydantic models for enhanced cluster analysis data input to Claude API.
Replaces JSON schemas with type-safe, validated input models.
"""

from typing import List, Dict, Optional, Literal, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class PricingTier(str, Enum):
    PAY_AS_YOU_GO = "pay-as-you-go"
    RESERVED_1YR = "reserved-1yr"
    RESERVED_3YR = "reserved-3yr"
    SPOT = "spot"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkloadType(str, Enum):
    SYSTEM = "system"
    USER = "user"
    MIXED = "mixed"


class TrafficPattern(str, Enum):
    STEADY = "STEADY"
    BURSTY = "BURSTY"
    PERIODIC = "PERIODIC"
    LOW_UTILIZATION = "LOW_UTILIZATION"
    CPU_INTENSIVE = "CPU_INTENSIVE"
    MEMORY_INTENSIVE = "MEMORY_INTENSIVE"


class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionType(str, Enum):
    DOWNSIZE = "downsize"
    UPSIZE = "upsize"
    SPLIT = "split"
    CONSOLIDATE = "consolidate"
    MAINTAIN = "maintain"
    ADD_SPOT = "add_spot"


class UsageStatus(str, Enum):
    UNUSED = "unused"
    LOW_USAGE = "low_usage"
    ACTIVE = "active"


class CertificateStatus(str, Enum):
    VALID = "valid"
    EXPIRING = "expiring"
    EXPIRED = "expired"


class ScalingStrategy(str, Enum):
    HPA_ONLY = "hpa_only"
    VPA_ONLY = "vpa_only"
    HPA_VPA_COMBINED = "hpa_vpa_combined"
    PREDICTIVE = "predictive"


class PlacementType(str, Enum):
    STATEFUL = "stateful"
    STATELESS = "stateless"


# =============================================================================
# BASE MODELS
# =============================================================================

class CostAnalysis(BaseModel):
    """Current cost breakdown structure"""
    total_cost: float = Field(ge=0, description="Total monthly cost")
    node_cost: float = Field(ge=0, description="Node pool costs")
    storage_cost: float = Field(ge=0, description="Storage costs")
    networking_cost: float = Field(ge=0, description="Network costs")
    control_plane_cost: float = Field(ge=0, description="Control plane costs")
    registry_cost: float = Field(ge=0, description="Container registry costs")
    other_cost: float = Field(ge=0, description="Other Azure costs")
    cost_period_days: int = Field(ge=1, description="Cost measurement period")
    currency: str = Field(default="USD", description="Cost currency")


class ClusterInfo(BaseModel):
    """Basic cluster identification and metadata"""
    cluster_name: str = Field(description="AKS cluster name")
    resource_group: str = Field(description="Azure resource group")
    subscription_id: str = Field(description="Azure subscription ID")
    kubernetes_version: Optional[str] = Field(None, description="Kubernetes version")
    location: Optional[str] = Field(None, description="Azure region")
    total_node_count: int = Field(ge=0, description="Total nodes in cluster")
    analysis_timestamp: datetime = Field(description="When analysis was performed")


# =============================================================================
# COST OPTIMIZATION MODELS
# =============================================================================

class PotentialSavings(BaseModel):
    """Savings breakdown by pricing model"""
    reserved_1yr: float = Field(ge=0, description="1-year reserved instance savings")
    reserved_3yr: float = Field(ge=0, description="3-year reserved instance savings")
    spot_instances: float = Field(ge=0, description="Spot instance savings")


class NodePoolPricing(BaseModel):
    """Node pool pricing analysis"""
    node_pool: str = Field(description="Node pool name")
    vm_size: str = Field(description="VM size (e.g., Standard_D4s_v3)")
    pricing_tier: PricingTier = Field(description="Current pricing model")
    spot_enabled: bool = Field(description="Whether spot is enabled")
    current_monthly_cost: float = Field(ge=0, description="Current monthly cost")
    potential_savings: PotentialSavings = Field(description="Potential savings breakdown")


class ReservedInstances(BaseModel):
    """Reserved instance optimization data"""
    current_pay_as_you_go_cost: float = Field(ge=0, description="Current PAYG cost")
    reserved_1yr_savings: float = Field(ge=0, description="1-year RI savings")
    reserved_3yr_savings: float = Field(ge=0, description="3-year RI savings")
    recommendation: str = Field(description="RI recommendation")


class SpotInstances(BaseModel):
    """Spot instance optimization data"""
    eligible_node_pools: List[str] = Field(description="Node pools eligible for spot")
    potential_savings: float = Field(ge=0, description="Potential monthly savings")
    risk_assessment: str = Field(description="Risk level assessment")
    recommendation: str = Field(description="Spot recommendation")


class AzureHybridBenefit(BaseModel):
    """Azure Hybrid Benefit analysis"""
    eligible: bool = Field(description="Whether cluster is eligible")
    potential_savings: float = Field(ge=0, description="Potential monthly savings")
    recommendation: str = Field(description="AHB recommendation")


class AzurePricingOptimization(BaseModel):
    """Azure-specific pricing optimizations"""
    reserved_instances: ReservedInstances
    spot_instances: SpotInstances
    azure_hybrid_benefit: AzureHybridBenefit


class OverProvisionedWorkload(BaseModel):
    """Over-provisioned workload analysis"""
    name: str = Field(description="Workload name")
    namespace: str = Field(description="Kubernetes namespace")
    current_cost: float = Field(ge=0, description="Current monthly cost")
    cpu_waste_percent: float = Field(ge=0, le=100, description="CPU waste percentage")
    memory_waste_percent: float = Field(ge=0, le=100, description="Memory waste percentage")
    recommended_cpu: str = Field(description="Recommended CPU allocation")
    recommended_memory: str = Field(description="Recommended memory allocation")
    monthly_savings: float = Field(ge=0, description="Potential monthly savings")


class NodePoolOptimization(BaseModel):
    """Node pool optimization recommendation"""
    node_pool: str = Field(description="Node pool name")
    current_vm_size: str = Field(description="Current VM size")
    recommended_vm_size: str = Field(description="Recommended VM size")
    utilization_avg: float = Field(ge=0, le=100, description="Average utilization")
    monthly_savings: float = Field(description="Monthly savings (can be negative)")
    action: ActionType = Field(description="Recommended action")


class WorkloadRightsizing(BaseModel):
    """Workload rightsizing recommendations"""
    over_provisioned_workloads: List[OverProvisionedWorkload]
    node_pool_optimization: List[NodePoolOptimization]


class HPAOpportunity(BaseModel):
    """HPA implementation opportunity"""
    workload: str = Field(description="Workload name")
    namespace: str = Field(description="Namespace")
    traffic_pattern: str = Field(description="Traffic pattern description")
    potential_monthly_savings: float = Field(ge=0, description="Potential savings")
    recommended_min_replicas: int = Field(ge=1, description="Recommended min replicas")
    recommended_max_replicas: int = Field(ge=1, description="Recommended max replicas")


class CurrentResourceConfig(BaseModel):
    """Current resource configuration"""
    cpu: str = Field(description="Current CPU allocation")
    memory: str = Field(description="Current memory allocation")


class VPARecommendations(BaseModel):
    """VPA resource recommendations"""
    cpu: str = Field(description="Recommended CPU")
    memory: str = Field(description="Recommended memory")


class VPAOpportunity(BaseModel):
    """VPA implementation opportunity"""
    workload: str = Field(description="Workload name")
    namespace: str = Field(description="Namespace")
    current_requests: CurrentResourceConfig
    vpa_recommendations: VPARecommendations
    monthly_savings: float = Field(ge=0, description="Potential monthly savings")
    confidence: ConfidenceLevel = Field(description="Recommendation confidence")


class ClusterAutoscalerTuning(BaseModel):
    """Cluster autoscaler optimization"""
    current_settings: Dict[str, Any] = Field(description="Current autoscaler settings")
    recommended_settings: Dict[str, Any] = Field(description="Recommended settings")
    monthly_savings: float = Field(ge=0, description="Potential monthly savings")


class ZoneDistributionOptimization(BaseModel):
    """Zone distribution optimization"""
    node_pool: str = Field(description="Node pool name")
    current_zones: List[str] = Field(description="Current availability zones")
    recommended_zones: List[str] = Field(description="Recommended zones")
    cost_impact: float = Field(description="Cost impact (can be negative)")


class MixedScalingStrategy(BaseModel):
    """Mixed scaling strategy recommendation"""
    workload: str = Field(description="Workload name")
    recommended_strategy: ScalingStrategy = Field(description="Recommended strategy")
    cost_benefit: float = Field(ge=0, description="Cost benefit")


class AutoscalingStrategies(BaseModel):
    """Advanced autoscaling strategies"""
    zone_distribution_optimization: List[ZoneDistributionOptimization]
    mixed_scaling_strategies: List[MixedScalingStrategy]


class AutoScalingOptimization(BaseModel):
    """Auto-scaling optimization recommendations"""
    missing_hpa_opportunities: List[HPAOpportunity]
    vpa_opportunities: List[VPAOpportunity]
    cluster_autoscaler_tuning: ClusterAutoscalerTuning
    autoscaling_strategies: AutoscalingStrategies


class DiskTierDowngrade(BaseModel):
    """Storage tier downgrade opportunity"""
    pvc_name: str = Field(description="PVC name")
    current_tier: str = Field(description="Current storage tier")
    recommended_tier: str = Field(description="Recommended tier")
    current_cost: float = Field(ge=0, description="Current monthly cost")
    monthly_savings: float = Field(ge=0, description="Monthly savings")
    performance_impact: str = Field(description="Performance impact assessment")


class UnusedStorage(BaseModel):
    """Unused storage resource"""
    pvc_name: str = Field(description="PVC name")
    namespace: str = Field(description="Namespace")
    monthly_cost: float = Field(ge=0, description="Monthly cost")
    last_accessed: datetime = Field(description="Last access time")
    safe_to_delete: bool = Field(description="Whether safe to delete")


class StorageCostOptimization(BaseModel):
    """Storage cost optimization opportunities"""
    disk_tier_downgrades: List[DiskTierDowngrade]
    unused_storage: List[UnusedStorage]


class LoadBalancerOptimization(BaseModel):
    """Load balancer optimization"""
    current_type: str = Field(description="Current load balancer type")
    recommended_type: str = Field(description="Recommended type")
    monthly_savings: float = Field(ge=0, description="Monthly savings")
    recommendation: str = Field(description="Detailed recommendation")


class PublicIPOptimization(BaseModel):
    """Public IP optimization"""
    ip_name: str = Field(description="Public IP name")
    usage_status: UsageStatus = Field(description="Usage status")
    monthly_cost: float = Field(ge=0, description="Monthly cost")
    recommendation: str = Field(description="Optimization recommendation")


class DataTransferOptimization(BaseModel):
    """Data transfer cost optimization"""
    monthly_egress_gb: float = Field(ge=0, description="Monthly egress in GB")
    egress_cost: float = Field(ge=0, description="Monthly egress cost")
    optimization_opportunities: List[str] = Field(description="Optimization opportunities")


class NetworkCostOptimization(BaseModel):
    """Network cost optimization opportunities"""
    load_balancer_optimization: LoadBalancerOptimization
    public_ip_optimization: List[PublicIPOptimization]
    data_transfer_optimization: DataTransferOptimization


class LogAnalyticsOptimization(BaseModel):
    """Log Analytics cost optimization"""
    current_monthly_cost: float = Field(ge=0, description="Current monthly cost")
    data_retention_optimization: float = Field(ge=0, description="Retention savings")
    log_filtering_savings: float = Field(ge=0, description="Log filtering savings")
    recommendations: List[str] = Field(description="Optimization recommendations")


class ContainerInsightsOptimization(BaseModel):
    """Container Insights optimization"""
    current_cost: float = Field(ge=0, description="Current monthly cost")
    optimization_opportunities: List[str] = Field(description="Optimization opportunities")


class MonitoringCostOptimization(BaseModel):
    """Monitoring and observability cost optimization"""
    log_analytics_optimization: LogAnalyticsOptimization
    container_insights_optimization: ContainerInsightsOptimization


class OrphanedResource(BaseModel):
    """Orphaned resource for cleanup"""
    resource_type: str = Field(description="Type of resource")
    resource_name: str = Field(description="Resource name")
    namespace: str = Field(description="Namespace")
    monthly_cost: float = Field(ge=0, description="Monthly cost")
    last_used: datetime = Field(description="Last used timestamp")
    safe_to_delete: bool = Field(description="Whether safe to delete")


class UnusedImage(BaseModel):
    """Unused container image"""
    image_name: str = Field(description="Image name")
    size_mb: float = Field(ge=0, description="Size in MB")
    monthly_cost: float = Field(ge=0, description="Monthly storage cost")
    last_pulled: datetime = Field(description="Last pulled timestamp")


class ResourceCleanup(BaseModel):
    """Resource cleanup opportunities"""
    orphaned_resources: List[OrphanedResource]
    unused_images: List[UnusedImage]


class DevTestScaling(BaseModel):
    """Dev/test environment scaling opportunity"""
    namespace: str = Field(description="Namespace")
    environment: str = Field(description="Environment type")
    current_cost: float = Field(ge=0, description="Current monthly cost")
    off_hours_savings: float = Field(ge=0, description="Off-hours savings")
    weekend_savings: float = Field(ge=0, description="Weekend savings")
    total_potential_savings: float = Field(ge=0, description="Total potential savings")


class ScheduleBasedOptimization(BaseModel):
    """Schedule-based cost optimizations"""
    dev_test_scaling: List[DevTestScaling]


class BudgetRecommendation(BaseModel):
    """Budget recommendation"""
    scope: str = Field(description="Budget scope")
    recommended_budget: float = Field(ge=0, description="Recommended budget amount")
    alert_thresholds: List[float] = Field(description="Alert threshold percentages")


class CostAllocationTags(BaseModel):
    """Cost allocation tagging"""
    missing_tags: List[str] = Field(description="Missing cost tags")
    tag_recommendations: List[str] = Field(description="Tag recommendations")


class NamespaceLevelCostTracking(BaseModel):
    """Namespace-level cost tracking"""
    namespace: str = Field(description="Namespace name")
    monthly_cost: float = Field(ge=0, description="Monthly cost")
    cost_per_workload: float = Field(ge=0, description="Cost per workload")
    team: str = Field(description="Owning team")
    cost_center: str = Field(description="Cost center")
    chargeback_enabled: bool = Field(description="Whether chargeback is enabled")


class AzureCostManagementIntegration(BaseModel):
    """Azure Cost Management integration"""
    budget_recommendations: List[BudgetRecommendation]
    cost_allocation_tags: CostAllocationTags
    namespace_level_cost_tracking: List[NamespaceLevelCostTracking]


class WorkloadDensity(BaseModel):
    """Workload density optimization"""
    current_pods_per_node: float = Field(ge=0, description="Current pods per node")
    optimal_pods_per_node: float = Field(ge=0, description="Optimal pods per node")
    density_improvement_potential: float = Field(ge=0, description="Improvement potential")


class StatefulVsStatelessPlacement(BaseModel):
    """Stateful vs stateless placement optimization"""
    workload: str = Field(description="Workload name")
    current_placement: PlacementType = Field(description="Current placement type")
    recommended_placement: PlacementType = Field(description="Recommended placement")
    cost_impact: float = Field(description="Cost impact")


class MultiTenancyOptimization(BaseModel):
    """Multi-tenancy optimization"""
    shared_node_pools: List[str] = Field(description="Shared node pools")
    dedicated_node_pools: List[str] = Field(description="Dedicated node pools")
    multi_tenancy_savings: float = Field(ge=0, description="Multi-tenancy savings")


class WorkloadSchedulingOptimization(BaseModel):
    """Workload scheduling optimization"""
    workload: str = Field(description="Workload name")
    current_schedule: str = Field(description="Current schedule")
    optimized_schedule: str = Field(description="Optimized schedule")
    scheduling_savings: float = Field(ge=0, description="Scheduling savings")


class WorkloadOptimization(BaseModel):
    """Advanced workload optimization strategies"""
    workload_density: WorkloadDensity
    stateful_vs_stateless_placement: List[StatefulVsStatelessPlacement]
    multi_tenancy_optimization: MultiTenancyOptimization
    workload_scheduling_optimization: List[WorkloadSchedulingOptimization]


class ClusterAutoscalerAdvanced(BaseModel):
    """Advanced cluster autoscaler settings"""
    scale_down_delay: str = Field(description="Scale down delay")
    scale_down_unneeded_time: str = Field(description="Scale down unneeded time")
    scale_down_utilization_threshold: float = Field(ge=0, le=1, description="Scale down threshold")
    max_node_provision_time: str = Field(description="Max node provision time")
    optimization_recommendations: List[str] = Field(description="Optimization recommendations")


class PredictiveScaling(BaseModel):
    """Predictive scaling recommendation"""
    workload: str = Field(description="Workload name")
    traffic_pattern: str = Field(description="Traffic pattern")
    predicted_peak_times: List[str] = Field(description="Predicted peak times")
    pre_scaling_recommendations: str = Field(description="Pre-scaling recommendations")
    cost_benefit: float = Field(description="Cost benefit")


class IdleResourceDetection(BaseModel):
    """Idle resource detection"""
    idle_cpu_threshold: float = Field(ge=0, le=100, description="Idle CPU threshold")
    idle_memory_threshold: float = Field(ge=0, le=100, description="Idle memory threshold")
    idle_workloads: List[str] = Field(description="Idle workloads")
    idle_cost_monthly: float = Field(ge=0, description="Monthly idle cost")


class BurstCapacityManagement(BaseModel):
    """Burst capacity management"""
    burst_capable_workloads: List[str] = Field(description="Burst capable workloads")
    burst_cost_optimization: float = Field(ge=0, description="Burst cost optimization")
    burst_scheduling_recommendations: List[str] = Field(description="Burst scheduling recommendations")


class ScalingAndPerformance(BaseModel):
    """Advanced scaling and performance optimizations"""
    cluster_autoscaler_advanced: ClusterAutoscalerAdvanced
    predictive_scaling: List[PredictiveScaling]
    idle_resource_detection: IdleResourceDetection
    burst_capacity_management: BurstCapacityManagement


class NetworkPolicyOverhead(BaseModel):
    """Network policy overhead analysis"""
    policies_count: int = Field(ge=0, description="Number of policies")
    performance_impact: str = Field(description="Performance impact")
    optimization_opportunities: List[str] = Field(description="Optimization opportunities")


class SecurityScanningOptimization(BaseModel):
    """Security scanning optimization"""
    scanning_frequency: str = Field(description="Current scanning frequency")
    scanning_cost_monthly: float = Field(ge=0, description="Monthly scanning cost")
    optimization_recommendations: List[str] = Field(description="Optimization recommendations")


class ComplianceMonitoringCosts(BaseModel):
    """Compliance monitoring costs"""
    compliance_tools_cost: float = Field(ge=0, description="Compliance tools cost")
    audit_frequency: str = Field(description="Audit frequency")
    cost_optimization_opportunities: List[str] = Field(description="Cost optimization opportunities")


class RBACOptimization(BaseModel):
    """RBAC optimization"""
    over_privileged_users: int = Field(ge=0, description="Over-privileged users count")
    unused_roles: int = Field(ge=0, description="Unused roles count")
    rbac_complexity_score: float = Field(ge=0, le=100, description="RBAC complexity score")


class SecurityComplianceCostOptimization(BaseModel):
    """Security and compliance cost optimization"""
    network_policy_overhead: NetworkPolicyOverhead
    security_scanning_optimization: SecurityScanningOptimization
    compliance_monitoring_costs: ComplianceMonitoringCosts
    rbac_optimization: RBACOptimization


class OptimizationSummary(BaseModel):
    """Cost optimization summary"""
    total_monthly_cost: float = Field(ge=0, description="Current total monthly cost")
    total_potential_savings: float = Field(ge=0, description="Total potential savings")
    savings_percentage: float = Field(ge=0, le=100, description="Savings percentage")
    top_opportunities: List[str] = Field(description="Top optimization opportunities")


class CostOptimization(BaseModel):
    """PRIMARY: Comprehensive AKS cost optimization analysis"""
    optimization_summary: OptimizationSummary
    azure_pricing_optimization: AzurePricingOptimization
    workload_rightsizing: WorkloadRightsizing
    auto_scaling_optimization: AutoScalingOptimization
    storage_cost_optimization: StorageCostOptimization
    network_cost_optimization: NetworkCostOptimization
    monitoring_cost_optimization: MonitoringCostOptimization
    resource_cleanup: ResourceCleanup
    schedule_based_optimization: ScheduleBasedOptimization
    azure_cost_management_integration: AzureCostManagementIntegration
    workload_optimization: WorkloadOptimization
    scaling_and_performance: ScalingAndPerformance
    security_compliance_cost_optimization: SecurityComplianceCostOptimization


# =============================================================================
# ADDITIONAL ANALYSIS MODELS (SUPPORTING DATA)
# =============================================================================

class NodeCondition(BaseModel):
    """Node condition status"""
    node: str = Field(description="Node name")
    memory_pressure: bool = Field(description="Memory pressure status")
    disk_pressure: bool = Field(description="Disk pressure status")
    pid_pressure: bool = Field(description="PID pressure status")
    network_unavailable: bool = Field(description="Network unavailable status")


class NodeHealth(BaseModel):
    """Node health metrics"""
    total_nodes: int = Field(ge=0, description="Total nodes")
    ready: int = Field(ge=0, description="Ready nodes")
    not_ready: int = Field(ge=0, description="Not ready nodes")
    node_conditions: List[NodeCondition] = Field(description="Node conditions")
    node_age_days: List[int] = Field(description="Node ages in days")


class PodRestartSummary(BaseModel):
    """Pod restart summary"""
    pod: str = Field(description="Pod name")
    namespace: str = Field(description="Namespace")
    restarts: int = Field(ge=0, description="Restart count")
    last_restart_reason: str = Field(description="Last restart reason")


class PodHealth(BaseModel):
    """Pod health metrics"""
    total_pods: int = Field(ge=0, description="Total pods")
    running: int = Field(ge=0, description="Running pods")
    pending: int = Field(ge=0, description="Pending pods")
    failed: int = Field(ge=0, description="Failed pods")
    succeeded: int = Field(ge=0, description="Succeeded pods")
    pod_restart_summary: List[PodRestartSummary] = Field(description="Pod restart summary")
    crashloop_backoff: List[str] = Field(description="Pods in crashloop backoff")


class CriticalEvent(BaseModel):
    """Critical cluster event"""
    type: str = Field(description="Event type")
    reason: str = Field(description="Event reason")
    message: str = Field(description="Event message")
    count: int = Field(ge=0, description="Event count")


class EventsLast24h(BaseModel):
    """Events in last 24 hours"""
    warnings: int = Field(ge=0, description="Warning events count")
    errors: int = Field(ge=0, description="Error events count")
    critical_events: List[CriticalEvent] = Field(description="Critical events")


class Events(BaseModel):
    """Cluster events summary"""
    last_24h: EventsLast24h


class PVCUtilization(BaseModel):
    """PVC utilization details"""
    pvc: str = Field(description="PVC name")
    capacity: str = Field(description="PVC capacity")
    used: str = Field(description="Used space")
    used_percent: float = Field(ge=0, le=100, description="Used percentage")


class PersistentVolumes(BaseModel):
    """Persistent volume status"""
    total_pvcs: int = Field(ge=0, description="Total PVCs")
    bound: int = Field(ge=0, description="Bound PVCs")
    pending: int = Field(ge=0, description="Pending PVCs")
    failed: int = Field(ge=0, description="Failed PVCs")
    utilization: List[PVCUtilization] = Field(description="PVC utilization details")


class CertificateStatus(BaseModel):
    """TLS certificate status"""
    name: str = Field(description="Certificate name")
    expiry_date: date = Field(description="Expiry date")
    days_until_expiry: int = Field(description="Days until expiry")
    status: CertificateStatus = Field(description="Certificate status")


class ClusterHealth(BaseModel):
    """Comprehensive cluster health assessment"""
    overall_score: float = Field(ge=0, le=100, description="Overall health score")
    node_health: NodeHealth
    pod_health: PodHealth
    events: Events
    persistent_volumes: PersistentVolumes
    certificate_status: List[CertificateStatus] = Field(description="Certificate status")


class Utilization(BaseModel):
    """Node pool utilization metrics"""
    cpu_percentage: float = Field(ge=0, le=100, description="CPU utilization percentage")
    memory_percentage: float = Field(ge=0, le=100, description="Memory utilization percentage")
    avg_cpu_last_7d: float = Field(ge=0, le=100, description="Average CPU last 7 days")
    avg_memory_last_7d: float = Field(ge=0, le=100, description="Average memory last 7 days")
    peak_cpu_last_7d: float = Field(ge=0, le=100, description="Peak CPU last 7 days")
    peak_memory_last_7d: float = Field(ge=0, le=100, description="Peak memory last 7 days")


class Taint(BaseModel):
    """Kubernetes node taint"""
    key: str = Field(description="Taint key")
    value: str = Field(description="Taint value")
    effect: Literal["NoSchedule", "PreferNoSchedule", "NoExecute"] = Field(description="Taint effect")


class NodePool(BaseModel):
    """Node pool configuration and utilization"""
    name: str = Field(description="Node pool name")
    vm_sku: str = Field(description="VM SKU")
    node_count: int = Field(ge=0, description="Current node count")
    min_count: Optional[int] = Field(None, ge=0, description="Minimum node count")
    max_count: Optional[int] = Field(None, ge=0, description="Maximum node count")
    cpu_cores_per_node: float = Field(ge=0, description="CPU cores per node")
    memory_gb_per_node: float = Field(ge=0, description="Memory GB per node")
    utilization: Optional[Utilization] = Field(None, description="Utilization metrics")
    monthly_cost: float = Field(ge=0, description="Monthly cost")
    workload_type: WorkloadType = Field(default=WorkloadType.USER, description="Workload type")
    spot_enabled: bool = Field(default=False, description="Spot instances enabled")
    taints: List[Taint] = Field(default=[], description="Node taints")


class ReplicaStatus(BaseModel):
    """Replica status"""
    desired: int = Field(ge=0, description="Desired replicas")
    ready: int = Field(ge=0, description="Ready replicas")
    available: int = Field(ge=0, description="Available replicas")


class ResourceRequests(BaseModel):
    """Resource requests"""
    cpu: Optional[str] = Field(None, description="CPU request")
    memory: Optional[str] = Field(None, description="Memory request")


class ResourceLimits(BaseModel):
    """Resource limits"""
    cpu: Optional[str] = Field(None, description="CPU limit")
    memory: Optional[str] = Field(None, description="Memory limit")


class Resources(BaseModel):
    """Resource configuration"""
    requests: Optional[ResourceRequests] = Field(None, description="Resource requests")
    limits: Optional[ResourceLimits] = Field(None, description="Resource limits")


class CPUUsage(BaseModel):
    """CPU usage metrics"""
    avg_millicores: float = Field(ge=0, description="Average millicores")
    p95_millicores: float = Field(ge=0, description="95th percentile millicores")
    avg_percentage: float = Field(ge=0, le=100, description="Average percentage")
    p95_percentage: float = Field(ge=0, le=100, description="95th percentile percentage")


class MemoryUsage(BaseModel):
    """Memory usage metrics"""
    avg_bytes: float = Field(ge=0, description="Average bytes")
    p95_bytes: float = Field(ge=0, description="95th percentile bytes")
    avg_percentage: float = Field(ge=0, le=100, description="Average percentage")
    p95_percentage: float = Field(ge=0, le=100, description="95th percentile percentage")


class ActualUsage(BaseModel):
    """Actual resource usage"""
    cpu: CPUUsage
    memory: MemoryUsage


class CostEstimate(BaseModel):
    """Cost estimation"""
    monthly_cost: float = Field(ge=0, description="Monthly cost")
    cpu_cost: float = Field(ge=0, description="CPU cost")
    memory_cost: float = Field(ge=0, description="Memory cost")
    storage_cost: float = Field(ge=0, description="Storage cost")


class TrafficPatternDetails(BaseModel):
    """Traffic pattern details"""
    pattern_type: TrafficPattern = Field(default=TrafficPattern.STEADY, description="Pattern type")
    confidence: float = Field(ge=0, le=1, description="Pattern confidence")
    peak_hours: List[int] = Field(description="Peak hours (0-23)")
    scaling_events_last_7d: int = Field(ge=0, description="Scaling events last 7 days")


class Workload(BaseModel):
    """Detailed workload configuration and metrics"""
    namespace: str = Field(description="Kubernetes namespace")
    name: str = Field(description="Workload name")
    type: Literal["Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"] = Field(description="Workload type")
    replicas: Optional[ReplicaStatus] = Field(None, description="Replica status")
    has_hpa: bool = Field(default=False, description="Has HPA configured")
    hpa_name: Optional[str] = Field(None, description="HPA name")
    resources: Optional[Resources] = Field(None, description="Resource configuration")
    actual_usage: Optional[ActualUsage] = Field(None, description="Actual usage metrics")
    cost_estimate: Optional[CostEstimate] = Field(None, description="Cost estimation")
    traffic_pattern: Optional[TrafficPatternDetails] = Field(None, description="Traffic pattern")
    priority: Priority = Field(default=Priority.MEDIUM, description="Workload priority")
    environment: Environment = Field(default=Environment.PRODUCTION, description="Environment")
    last_updated: datetime = Field(description="Last updated timestamp")
    optimization_candidate: bool = Field(default=False, description="Optimization candidate")
    optimization_reasons: List[str] = Field(default=[], description="Optimization reasons")


class AnalysisScope(BaseModel):
    """Analysis scope configuration"""
    include_system_namespaces: bool = Field(default=False, description="Include system namespaces")
    cost_analysis_period_days: int = Field(default=30, ge=1, description="Cost analysis period")
    metrics_lookback_days: int = Field(default=7, ge=1, description="Metrics lookback period")


class DataSources(BaseModel):
    """Available data sources"""
    azure_cost_management: bool = Field(description="Azure Cost Management available")
    prometheus_metrics: bool = Field(description="Prometheus metrics available")
    kubernetes_api: bool = Field(description="Kubernetes API available")
    azure_monitor: bool = Field(description="Azure Monitor available")


class CollectionConfidence(BaseModel):
    """Data collection confidence"""
    overall_score: float = Field(ge=0, le=1, description="Overall confidence score")
    cost_data_quality: float = Field(ge=0, le=1, description="Cost data quality")
    metrics_completeness: float = Field(ge=0, le=1, description="Metrics completeness")
    workload_coverage: float = Field(ge=0, le=1, description="Workload coverage")


class Metadata(BaseModel):
    """Analysis metadata and configuration"""
    schema_version: str = Field(default="3.0.0", description="Schema version")
    collection_timestamp: datetime = Field(description="Collection timestamp")
    analysis_scope: AnalysisScope = Field(description="Analysis scope")
    data_sources: DataSources = Field(description="Data sources")
    collection_confidence: CollectionConfidence = Field(description="Collection confidence")


# =============================================================================
# ROOT INPUT MODEL
# =============================================================================

class AKSCostOptimizationInput(BaseModel):
    """Complete AKS cost optimization input model"""
    
    # Core required sections
    cost_analysis: CostAnalysis = Field(description="Current cost breakdown")
    cluster_info: ClusterInfo = Field(description="Cluster identification")
    cost_optimization: CostOptimization = Field(description="PRIMARY: Cost optimization data")
    
    # Health and infrastructure data
    cluster_health: Optional[ClusterHealth] = Field(None, description="Cluster health metrics")
    node_pools: List[NodePool] = Field(description="Node pool configurations")
    workloads: List[Workload] = Field(description="Workload details")
    
    # Metadata
    metadata: Metadata = Field(description="Analysis metadata")
    
    # Computed properties
    @property
    def total_monthly_cost(self) -> float:
        """Calculate total monthly cost"""
        return self.cost_analysis.total_cost
    
    @property
    def total_potential_savings(self) -> float:
        """Calculate total potential savings"""
        return self.cost_optimization.optimization_summary.total_potential_savings
    
    @property
    def savings_percentage(self) -> float:
        """Calculate savings percentage"""
        if self.total_monthly_cost > 0:
            return (self.total_potential_savings / self.total_monthly_cost) * 100
        return 0
    
    @property
    def high_priority_workloads(self) -> List[Workload]:
        """Get high priority workloads"""
        return [w for w in self.workloads if w.priority in [Priority.CRITICAL, Priority.HIGH]]
    
    @property
    def optimization_candidates(self) -> List[Workload]:
        """Get workloads that are optimization candidates"""
        return [w for w in self.workloads if w.optimization_candidate]
    
    # Validation
    @validator('workloads')
    def validate_workloads(cls, v):
        """Validate workload list"""
        if not v:
            raise ValueError("At least one workload must be provided")
        return v
    
    @validator('node_pools')
    def validate_node_pools(cls, v):
        """Validate node pool list"""
        if not v:
            raise ValueError("At least one node pool must be provided")
        return v


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_sample_input(cluster_name: str = "aks-sample-cluster") -> AKSCostOptimizationInput:
    """Create a sample input for testing"""
    return AKSCostOptimizationInput(
        cost_analysis=CostAnalysis(
            total_cost=2111.71,
            node_cost=1650.00,
            storage_cost=410.21,
            networking_cost=51.50,
            control_plane_cost=0.0,
            registry_cost=0.0,
            other_cost=0.0,
            cost_period_days=30
        ),
        cluster_info=ClusterInfo(
            cluster_name=cluster_name,
            resource_group="rg-sample",
            subscription_id="12345678-1234-1234-1234-123456789012",
            kubernetes_version="1.28.9",
            location="northeurope",
            total_node_count=3,
            analysis_timestamp=datetime.utcnow()
        ),
        cost_optimization=CostOptimization(
            optimization_summary=OptimizationSummary(
                total_monthly_cost=2111.71,
                total_potential_savings=342.85,
                savings_percentage=16.2,
                top_opportunities=["Implement HPA", "Rightsize workloads", "Reserved instances"]
            ),
            azure_pricing_optimization=AzurePricingOptimization(
                reserved_instances=ReservedInstances(
                    current_pay_as_you_go_cost=1650.00,
                    reserved_1yr_savings=165.00,
                    reserved_3yr_savings=330.00,
                    recommendation="Purchase 1-year reserved instances for steady workloads"
                ),
                spot_instances=SpotInstances(
                    eligible_node_pools=["nodepool1"],
                    potential_savings=578.50,
                    risk_assessment="Medium risk for dev/test workloads",
                    recommendation="Implement spot instances for batch workloads"
                ),
                azure_hybrid_benefit=AzureHybridBenefit(
                    eligible=False,
                    potential_savings=0.0,
                    recommendation="Not applicable for AKS compute"
                )
            ),
            workload_rightsizing=WorkloadRightsizing(
                over_provisioned_workloads=[],
                node_pool_optimization=[]
            ),
            auto_scaling_optimization=AutoScalingOptimization(
                missing_hpa_opportunities=[],
                vpa_opportunities=[],
                cluster_autoscaler_tuning=ClusterAutoscalerTuning(
                    current_settings={},
                    recommended_settings={},
                    monthly_savings=0.0
                ),
                autoscaling_strategies=AutoscalingStrategies(
                    zone_distribution_optimization=[],
                    mixed_scaling_strategies=[]
                )
            ),
            storage_cost_optimization=StorageCostOptimization(
                disk_tier_downgrades=[],
                unused_storage=[]
            ),
            network_cost_optimization=NetworkCostOptimization(
                load_balancer_optimization=LoadBalancerOptimization(
                    current_type="Standard",
                    recommended_type="Basic",
                    monthly_savings=25.00,
                    recommendation="Switch to Basic load balancer for dev environment"
                ),
                public_ip_optimization=[],
                data_transfer_optimization=DataTransferOptimization(
                    monthly_egress_gb=100.0,
                    egress_cost=10.0,
                    optimization_opportunities=[]
                )
            ),
            monitoring_cost_optimization=MonitoringCostOptimization(
                log_analytics_optimization=LogAnalyticsOptimization(
                    current_monthly_cost=75.00,
                    data_retention_optimization=15.00,
                    log_filtering_savings=10.00,
                    recommendations=["Reduce retention to 30 days", "Filter debug logs"]
                ),
                container_insights_optimization=ContainerInsightsOptimization(
                    current_cost=25.00,
                    optimization_opportunities=["Disable for dev namespaces"]
                )
            ),
            resource_cleanup=ResourceCleanup(
                orphaned_resources=[],
                unused_images=[]
            ),
            schedule_based_optimization=ScheduleBasedOptimization(
                dev_test_scaling=[]
            ),
            azure_cost_management_integration=AzureCostManagementIntegration(
                budget_recommendations=[],
                cost_allocation_tags=CostAllocationTags(
                    missing_tags=["cost-center", "team"],
                    tag_recommendations=["Add cost-center tag", "Add team tag"]
                ),
                namespace_level_cost_tracking=[]
            ),
            workload_optimization=WorkloadOptimization(
                workload_density=WorkloadDensity(
                    current_pods_per_node=15.0,
                    optimal_pods_per_node=25.0,
                    density_improvement_potential=40.0
                ),
                stateful_vs_stateless_placement=[],
                multi_tenancy_optimization=MultiTenancyOptimization(
                    shared_node_pools=["nodepool1"],
                    dedicated_node_pools=[],
                    multi_tenancy_savings=50.0
                ),
                workload_scheduling_optimization=[]
            ),
            scaling_and_performance=ScalingAndPerformance(
                cluster_autoscaler_advanced=ClusterAutoscalerAdvanced(
                    scale_down_delay="10m",
                    scale_down_unneeded_time="10m",
                    scale_down_utilization_threshold=0.5,
                    max_node_provision_time="15m",
                    optimization_recommendations=[]
                ),
                predictive_scaling=[],
                idle_resource_detection=IdleResourceDetection(
                    idle_cpu_threshold=10.0,
                    idle_memory_threshold=15.0,
                    idle_workloads=[],
                    idle_cost_monthly=0.0
                ),
                burst_capacity_management=BurstCapacityManagement(
                    burst_capable_workloads=[],
                    burst_cost_optimization=0.0,
                    burst_scheduling_recommendations=[]
                )
            ),
            security_compliance_cost_optimization=SecurityComplianceCostOptimization(
                network_policy_overhead=NetworkPolicyOverhead(
                    policies_count=5,
                    performance_impact="Minimal",
                    optimization_opportunities=[]
                ),
                security_scanning_optimization=SecurityScanningOptimization(
                    scanning_frequency="Daily",
                    scanning_cost_monthly=10.0,
                    optimization_recommendations=["Reduce to weekly for dev"]
                ),
                compliance_monitoring_costs=ComplianceMonitoringCosts(
                    compliance_tools_cost=50.0,
                    audit_frequency="Monthly",
                    cost_optimization_opportunities=[]
                ),
                rbac_optimization=RBACOptimization(
                    over_privileged_users=2,
                    unused_roles=5,
                    rbac_complexity_score=75.0
                )
            )
        ),
        node_pools=[
            NodePool(
                name="nodepool1",
                vm_sku="Standard_D4s_v3",
                node_count=3,
                min_count=1,
                max_count=5,
                cpu_cores_per_node=4.0,
                memory_gb_per_node=16.0,
                monthly_cost=550.0,
                workload_type=WorkloadType.USER
            )
        ],
        workloads=[
            Workload(
                namespace="default",
                name="sample-app",
                type="Deployment",
                priority=Priority.MEDIUM,
                environment=Environment.PRODUCTION,
                last_updated=datetime.utcnow()
            )
        ],
        metadata=Metadata(
            collection_timestamp=datetime.utcnow(),
            analysis_scope=AnalysisScope(),
            data_sources=DataSources(
                azure_cost_management=True,
                prometheus_metrics=True,
                kubernetes_api=True,
                azure_monitor=True
            ),
            collection_confidence=CollectionConfidence(
                overall_score=0.95,
                cost_data_quality=0.98,
                metrics_completeness=0.92,
                workload_coverage=0.95
            )
        )
    )


# Export the main input schema for JSON Schema generation
def get_input_json_schema() -> Dict[str, Any]:
    """Generate JSON Schema from Pydantic model"""
    return AKSCostOptimizationInput.model_json_schema()


# Export for easy importing
__all__ = [
    "AKSCostOptimizationInput",
    "CostOptimization", 
    "ClusterInfo",
    "CostAnalysis",
    "create_sample_input",
    "get_input_json_schema"
]