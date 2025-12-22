"""
KubeOpt Implementation Plan Schema

Comprehensive Pydantic models based on the custom KubeOpt implementation plan structure.
Designed for actionable cost optimization with detailed analysis and ROI tracking.
"""

from typing import List, Dict, Optional, Literal, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum


# Enums for validation
class StatusType(str, Enum):
    GOOD = "good"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class ComplianceLevel(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    INCONSISTENT = "INCONSISTENT"
    NEEDS_IMPROVEMENT = "NEEDS IMPROVEMENT"


class BadgeType(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"


class RiskLevel(str, Enum):
    VERY_LOW = "Very Low"
    LOW = "Low" 
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CostOptimizationCategory(str, Enum):
    """Primary cost optimization categories for AKS"""
    AZURE_PRICING_OPTIMIZATION = "azure_pricing_optimization"
    WORKLOAD_RIGHTSIZING = "workload_rightsizing"
    AUTO_SCALING_OPTIMIZATION = "auto_scaling_optimization"
    STORAGE_COST_OPTIMIZATION = "storage_cost_optimization"
    NETWORK_COST_OPTIMIZATION = "network_cost_optimization"
    RESOURCE_GOVERNANCE = "resource_governance"
    WORKLOAD_DECOMMISSIONING = "workload_decommissioning"


# New models for aggregate workload handling
class WorkloadCategoryStats(BaseModel):
    """Statistics for a category of workloads"""
    count: int = Field(..., description="Number of workloads in this category")
    avg_monthly_cost: float = Field(..., description="Average monthly cost per workload")
    total_monthly_cost: float = Field(..., description="Total monthly cost for category")
    avg_cpu_request_millicores: float = Field(0, description="Average CPU request in millicores")
    avg_memory_request_mb: float = Field(0, description="Average memory request in MB")
    avg_cpu_usage_percent: float = Field(0, description="Average CPU utilization percentage")
    avg_memory_usage_percent: float = Field(0, description="Average memory utilization percentage")


class GovernanceIssueStats(BaseModel):
    """Statistics for governance issues"""
    count: int = Field(..., description="Number of workloads with this issue")
    total_cost: float = Field(..., description="Total cost impact of this issue")
    sample_names: Optional[List[str]] = Field(None, description="Sample workload names with this issue")
    avg_cpu_waste: Optional[float] = Field(None, description="Average CPU waste percentage")
    avg_memory_waste: Optional[float] = Field(None, description="Average memory waste percentage")


class BulkOptimizationAction(BaseModel):
    """Action for bulk optimization of workload categories"""
    action_id: str = Field(..., description="Unique identifier for this bulk action")
    category: str = Field(..., description="Workload category this applies to")
    name: str = Field(..., description="Name of the bulk optimization action")
    description: str = Field(..., description="Description of what this action does")
    affected_workloads: int = Field(..., description="Number of workloads this action affects")
    estimated_savings: float = Field(0, description="Estimated monthly savings in USD")
    implementation_complexity: Literal["low", "medium", "high"] = Field(..., description="Implementation complexity")
    
    # Template commands for bulk application
    template_commands: Dict[str, List[str]] = Field(..., description="Template kubectl commands")
    validation_commands: List[str] = Field(default_factory=list, description="Commands to validate bulk changes")
    rollback_procedure: List[str] = Field(default_factory=list, description="Steps to rollback if issues arise")
    
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites before applying bulk changes")
    success_criteria: List[str] = Field(default_factory=list, description="Criteria to determine success")
    risks: List[str] = Field(default_factory=list, description="Potential risks of bulk changes")


class AzurePricingActionType(str, Enum):
    """Azure pricing optimization action types"""
    RESERVED_INSTANCES = "reserved_instances"
    SPOT_INSTANCES = "spot_instances"
    SAVINGS_PLANS = "savings_plans"
    HYBRID_BENEFIT = "hybrid_benefit"
    DEV_TEST_PRICING = "dev_test_pricing"
    COMPUTE_GALLERY = "compute_gallery"
    BURSTABLE_VMS = "burstable_vms"


class WorkloadOptimizationType(str, Enum):
    """Workload optimization action types"""
    CPU_RIGHTSIZING = "cpu_rightsizing"
    MEMORY_RIGHTSIZING = "memory_rightsizing"
    REPLICA_OPTIMIZATION = "replica_optimization"
    RESOURCE_LIMITS = "resource_limits"
    QUALITY_OF_SERVICE = "quality_of_service"
    VERTICAL_SCALING = "vertical_scaling"
    HORIZONTAL_SCALING = "horizontal_scaling"


class AutoScalingActionType(str, Enum):
    """Auto-scaling optimization action types"""
    HPA_CONFIGURATION = "hpa_configuration"
    VPA_CONFIGURATION = "vpa_configuration"
    CLUSTER_AUTOSCALER = "cluster_autoscaler"
    NODE_POOL_SCALING = "node_pool_scaling"
    PREDICTIVE_SCALING = "predictive_scaling"
    CUSTOM_METRICS_SCALING = "custom_metrics_scaling"


class StorageOptimizationType(str, Enum):
    """Storage cost optimization action types"""
    STORAGE_CLASS_OPTIMIZATION = "storage_class_optimization"
    VOLUME_RIGHTSIZING = "volume_rightsizing"
    SNAPSHOT_LIFECYCLE = "snapshot_lifecycle"
    BACKUP_OPTIMIZATION = "backup_optimization"
    STORAGE_TIERING = "storage_tiering"
    EPHEMERAL_STORAGE = "ephemeral_storage"


class NetworkOptimizationType(str, Enum):
    """Network cost optimization action types"""
    BANDWIDTH_OPTIMIZATION = "bandwidth_optimization"
    LOAD_BALANCER_OPTIMIZATION = "load_balancer_optimization"
    INGRESS_OPTIMIZATION = "ingress_optimization"
    INTER_AZ_TRAFFIC = "inter_az_traffic"
    EGRESS_OPTIMIZATION = "egress_optimization"
    CDN_INTEGRATION = "cdn_integration"


class ColorType(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    RED = "red"


# Base Models
class PlanMetadata(BaseModel):
    """Implementation plan metadata"""
    plan_id: str = Field(description="Unique plan identifier")
    cluster_name: str = Field(description="AKS cluster name")
    generated_date: datetime = Field(description="Plan generation timestamp")
    analysis_date: datetime = Field(description="Original analysis timestamp")
    last_analyzed_display: str = Field(description="Human-readable analysis age")


class DNAMetric(BaseModel):
    """Individual DNA analysis metric"""
    label: str = Field(description="Metric name")
    value: int = Field(ge=0, le=100, description="Metric score (0-100)")
    percentage: int = Field(ge=0, le=100, description="Percentage representation")
    rating: str = Field(description="Qualitative rating")
    color: ColorType = Field(description="Color coding for UI")


class DataSource(BaseModel):
    """Data source availability"""
    name: str = Field(description="Data source name")
    available: bool = Field(description="Whether source is available")


class ClusterDNAAnalysis(BaseModel):
    """Cluster DNA quality analysis"""
    overall_score: int = Field(ge=0, le=100, description="Overall cluster quality score")
    score_rating: str = Field(description="Overall rating")
    description: str = Field(description="Detailed assessment description")
    metrics: List[DNAMetric] = Field(description="Individual metric scores")
    data_sources: List[DataSource] = Field(description="Available data sources")


class QualityCheck(BaseModel):
    """Build quality assessment check"""
    label: str = Field(description="Check name")
    status: str = Field(description="Check result")
    status_type: StatusType = Field(description="Status classification")


class BestPracticeScore(BaseModel):
    """Best practices scorecard entry"""
    category: str = Field(description="Practice category")
    score: int = Field(ge=0, description="Current score")
    max_score: int = Field(ge=0, description="Maximum possible score")
    color: ColorType = Field(description="Color coding")
    
    @validator('score')
    def score_not_exceed_max(cls, v, values):
        if 'max_score' in values and v > values['max_score']:
            raise ValueError('Score cannot exceed max_score')
        return v


class BuildQualityAssessment(BaseModel):
    """Build quality and best practices assessment"""
    quality_checks: List[QualityCheck] = Field(description="Quality check results")
    strengths: List[str] = Field(description="Identified strengths")
    improvements: List[str] = Field(description="Areas for improvement")
    best_practices_scorecard: List[BestPracticeScore] = Field(description="Best practice scores")


class NamingConventionResource(BaseModel):
    """Naming convention analysis for specific resource type"""
    resource_type: str = Field(description="Type of resource")
    example: str = Field(description="Example resource name")
    pattern: str = Field(description="Identified naming pattern")
    compliance: ComplianceLevel = Field(description="Compliance level")
    badge_type: BadgeType = Field(description="UI badge type")


class NamingConventionsAnalysis(BaseModel):
    """Naming conventions analysis"""
    overall_score: int = Field(ge=0, le=100, description="Overall naming score")
    max_score: int = Field(ge=0, description="Maximum possible score")
    color: ColorType = Field(description="Color coding")
    resources: List[NamingConventionResource] = Field(description="Per-resource analysis")
    strengths: List[str] = Field(description="Naming strengths")
    recommendations: List[str] = Field(description="Naming recommendations")


class ROISummaryMetric(BaseModel):
    """ROI summary metric display"""
    label: str = Field(description="Metric label")
    value: str = Field(description="Formatted value")
    subtitle: str = Field(description="Additional context")
    color: ColorType = Field(description="Color coding")


class ROICalculationBreakdown(BaseModel):
    """Detailed ROI calculations"""
    total_effort_hours: float = Field(ge=0, description="Total implementation hours")
    hourly_rate: float = Field(ge=0, description="Hourly implementation rate")
    implementation_cost: float = Field(ge=0, description="Total implementation cost")
    monthly_savings: float = Field(ge=0, description="Monthly cost savings")
    annual_savings: float = Field(ge=0, description="Annual cost savings")
    payback_months: float = Field(ge=0, description="Months to break even")
    roi_percentage_year1: float = Field(description="Year 1 ROI percentage")
    net_savings_year1: float = Field(description="Net savings after year 1")
    projected_savings_3year: float = Field(description="3-year projected savings")


class PhaseROI(BaseModel):
    """ROI breakdown by implementation phase"""
    phase: str = Field(description="Phase name")
    duration: str = Field(description="Phase duration")
    effort_hours: float = Field(ge=0, description="Phase effort in hours")
    monthly_savings: float = Field(ge=0, description="Monthly savings from phase")
    annual_savings: float = Field(ge=0, description="Annual savings from phase")


class ROIAnalysis(BaseModel):
    """Complete ROI and financial analysis"""
    summary_metrics: List[ROISummaryMetric] = Field(description="Key ROI metrics")
    calculation_breakdown: ROICalculationBreakdown = Field(description="Detailed calculations")
    financial_summary: List[str] = Field(description="Financial summary statements")
    savings_by_phase: List[PhaseROI] = Field(description="Phase-by-phase ROI")


class ImplementationSummary(BaseModel):
    """High-level implementation summary"""
    cluster_name: str = Field(description="Target cluster name")
    environment: str = Field(description="Environment (Dev/UAT/Prod)")
    location: str = Field(description="Azure region")
    kubernetes_version: str = Field(description="K8s version")
    current_monthly_cost: float = Field(ge=0, description="Current monthly cost")
    projected_monthly_cost: float = Field(ge=0, description="Projected monthly cost")
    cost_reduction_percentage: float = Field(ge=0, le=100, description="Cost reduction %")
    implementation_duration: str = Field(description="Total implementation time")
    total_phases: int = Field(ge=1, description="Number of implementation phases")
    risk_level: RiskLevel = Field(description="Overall risk assessment")


class ActionStep(BaseModel):
    """Individual action step with command"""
    step_number: int = Field(ge=1, description="Step sequence number")
    label: str = Field(description="Step description")
    command: str = Field(description="Command to execute")
    expected_output: Optional[str] = Field(None, description="Expected command output")


class ActionNote(BaseModel):
    """Action note or annotation"""
    type: Literal["note", "warning", "info", "error"] = Field(description="Note type")
    text: str = Field(description="Note content")


class ActionRollback(BaseModel):
    """Rollback instructions for an action"""
    command: str = Field(description="Rollback command")
    description: str = Field(description="Rollback description")


class OptimizationAction(BaseModel):
    """Individual optimization action within a phase"""
    action_id: str = Field(description="Unique action identifier")
    title: str = Field(description="Action title")
    description: str = Field(description="Detailed description")
    savings_monthly: float = Field(ge=0, description="Monthly savings from action")
    risk: RiskLevel = Field(description="Risk level")
    effort_hours: float = Field(ge=0, description="Implementation effort")
    issue_type: StatusType = Field(description="Issue classification")
    issue_text: str = Field(description="Current issue description")
    steps: List[ActionStep] = Field(description="Implementation steps")
    notes: List[ActionNote] = Field(default=[], description="Additional notes")
    success_criteria: Optional[List[str]] = Field(None, description="Success criteria")
    rollback: Optional[ActionRollback] = Field(None, description="Rollback instructions")
    
    # Cost optimization categorization
    cost_category: CostOptimizationCategory = Field(description="Primary cost optimization category")
    azure_action_type: Optional[Union[AzurePricingActionType, WorkloadOptimizationType, AutoScalingActionType, StorageOptimizationType, NetworkOptimizationType]] = Field(None, description="Specific Azure action type")
    
    # Enhanced actionable fields
    target_resource: Optional[str] = Field(None, description="Target K8s resource (deployment/pod/etc)")
    target_namespace: Optional[str] = Field(None, description="Target namespace")
    target_node_pool: Optional[str] = Field(None, description="Target AKS node pool")
    target_resource_group: Optional[str] = Field(None, description="Target Azure resource group")
    prerequisites: List[str] = Field(default=[], description="Prerequisites before execution")
    dependencies: List[str] = Field(default=[], description="Other action IDs this depends on")
    estimated_downtime: Optional[str] = Field(None, description="Expected downtime duration")
    business_impact: Optional[str] = Field(None, description="Business impact assessment")
    monitoring_commands: List[str] = Field(default=[], description="Commands to monitor after implementation")
    validation_timeout: Optional[str] = Field("5m", description="Timeout for validation steps")
    automation_ready: bool = Field(False, description="Whether action can be automated")
    requires_approval: bool = Field(False, description="Whether action requires stakeholder approval")
    
    # Azure-specific cost tracking
    current_azure_cost_monthly: Optional[float] = Field(None, ge=0, description="Current Azure cost for this resource")
    projected_azure_cost_monthly: Optional[float] = Field(None, ge=0, description="Projected Azure cost after optimization")
    azure_resource_id: Optional[str] = Field(None, description="Azure resource ID for cost tracking")
    cost_allocation_tags: Dict[str, str] = Field(default={}, description="Azure tags for cost allocation")
    
    # Implementation tracking
    implementation_priority: int = Field(default=1, ge=1, le=5, description="Implementation priority (1=highest, 5=lowest)")
    cost_impact_score: int = Field(default=1, ge=1, le=10, description="Cost impact score (1=low, 10=high)")
    complexity_score: int = Field(default=1, ge=1, le=10, description="Implementation complexity (1=simple, 10=complex)")


class ImplementationPhase(BaseModel):
    """Implementation phase with grouped actions"""
    phase_number: int = Field(ge=1, description="Phase sequence number")
    phase_name: str = Field(description="Phase name")
    description: str = Field(description="Phase description")
    duration: str = Field(description="Phase duration")
    start_date: date = Field(description="Phase start date")
    end_date: date = Field(description="Phase end date")
    total_savings_monthly: float = Field(ge=0, description="Total monthly savings")
    risk_level: RiskLevel = Field(description="Phase risk level")
    effort_hours: float = Field(ge=0, description="Total phase effort")
    actions: List[OptimizationAction] = Field(description="Phase actions for individual workloads")
    bulk_actions: List[BulkOptimizationAction] = Field(default_factory=list, description="Bulk optimization actions for workload categories")
    
    # Enhanced actionable fields
    prerequisites: List[str] = Field(default=[], description="Phase-level prerequisites")
    success_criteria: List[str] = Field(default=[], description="Phase completion criteria")
    rollback_strategy: Optional[str] = Field(None, description="Phase-level rollback strategy")
    stakeholders: List[str] = Field(default=[], description="Required stakeholders for phase")
    communication_plan: Optional[str] = Field(None, description="Communication strategy for phase")
    monitoring_requirements: List[str] = Field(default=[], description="Monitoring needed during phase")
    compliance_requirements: List[str] = Field(default=[], description="Compliance considerations")
    automation_percentage: float = Field(default=0, ge=0, le=100, description="Percentage of phase that can be automated")


class MonitoringCommand(BaseModel):
    """Post-implementation monitoring command"""
    label: str = Field(description="Command description")
    command: str = Field(description="Command to execute")


class MonitoringMetric(BaseModel):
    """Key metric to monitor post-implementation"""
    metric: str = Field(description="Metric name")
    target: str = Field(description="Target value and alert conditions")


class MonitoringGuidance(BaseModel):
    """Post-implementation monitoring guidance"""
    title: str = Field(description="Monitoring section title")
    description: str = Field(description="Monitoring description")
    commands: List[MonitoringCommand] = Field(description="Monitoring commands")
    key_metrics: List[MonitoringMetric] = Field(description="Key metrics to track")


class ReviewScheduleItem(BaseModel):
    """Scheduled review checkpoint"""
    day: int = Field(ge=1, description="Day number for review")
    title: str = Field(description="Review checkpoint description")


# Main Implementation Plan Model
class KubeOptImplementationPlan(BaseModel):
    """Complete KubeOpt Implementation Plan"""
    
    # Core metadata
    metadata: PlanMetadata = Field(description="Plan metadata")
    
    # Additional required fields
    generated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the plan was generated"
    )
    cluster_id: Optional[str] = Field(
        default=None,
        description="ID of the cluster this plan is for"
    )
    version: Optional[str] = Field(
        default="1.0",
        description="Plan version"
    )
    generated_by: Optional[str] = Field(
        default=None,
        description="System that generated the plan"
    )
    
    # Analysis sections
    cluster_dna_analysis: ClusterDNAAnalysis = Field(description="Cluster quality analysis")
    build_quality_assessment: BuildQualityAssessment = Field(description="Build quality assessment")
    naming_conventions_analysis: NamingConventionsAnalysis = Field(description="Naming conventions")
    roi_analysis: ROIAnalysis = Field(description="ROI and financial analysis")
    implementation_summary: ImplementationSummary = Field(description="Implementation summary")
    
    # Implementation details
    phases: List[ImplementationPhase] = Field(description="Implementation phases")
    
    # Post-implementation guidance
    monitoring: MonitoringGuidance = Field(description="Monitoring guidance")
    review_schedule: List[ReviewScheduleItem] = Field(description="Review schedule")
    
    # Additional computed properties
    @property
    def total_monthly_savings(self) -> float:
        """Calculate total monthly savings across all phases"""
        return sum(phase.total_savings_monthly for phase in self.phases)
    
    @property
    def estimated_total_savings_monthly(self) -> float:
        """Alias for total_monthly_savings for backward compatibility"""
        return self.total_monthly_savings
    
    @property
    def total_actions(self) -> int:
        """Count total actions across all phases"""
        return sum(len(phase.actions) for phase in self.phases)
    
    @property
    def total_effort_hours(self) -> float:
        """Calculate total effort hours"""
        return sum(phase.effort_hours for phase in self.phases)
    
    @property
    def highest_risk_actions(self) -> List[OptimizationAction]:
        """Get high and critical risk actions"""
        high_risk_actions = []
        for phase in self.phases:
            for action in phase.actions:
                if action.risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    high_risk_actions.append(action)
        return high_risk_actions
    
    def get_actions_by_risk(self, risk_level: RiskLevel) -> List[OptimizationAction]:
        """Get all actions of a specific risk level"""
        actions = []
        for phase in self.phases:
            for action in phase.actions:
                if action.risk == risk_level:
                    actions.append(action)
        return actions
    
    def get_phase_by_number(self, phase_number: int) -> Optional[ImplementationPhase]:
        """Get phase by number"""
        return next((phase for phase in self.phases if phase.phase_number == phase_number), None)


# Root model for the complete JSON structure
class ImplementationPlanDocument(BaseModel):
    """Root document containing the implementation plan"""
    implementation_plan: KubeOptImplementationPlan = Field(description="The complete implementation plan")


# JSON Schema Export
KUBEOPT_IMPLEMENTATION_PLAN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "KubeOpt Implementation Plan Schema",
    "description": "Comprehensive implementation plan for AKS cost optimization",
    "properties": {
        "implementation_plan": KubeOptImplementationPlan.model_json_schema()
    },
    "required": ["implementation_plan"]
}


# Azure CLI and kubectl command templates for cost optimization
AZURE_COST_OPTIMIZATION_COMMANDS = {
    "azure_pricing_optimization": {
        "check_eligible_vms": "az vm list --query '[].{Name:name, Size:hardwareProfile.vmSize, Location:location}' --output table",
        "purchase_reservation": "az reservations reservation-order purchase --reserved-resource-type VirtualMachines --billing-scope-id {billing_scope} --term P1Y --billing-plan Monthly --quantity {quantity} --sku {vm_sku} --location {location}",
        "check_reservations": "az reservations reservation list --query '[].{Name:name, State:properties.provisioningState, Quantity:properties.quantity}' --output table",
        "create_spot_nodepool": "az aks nodepool add --resource-group {rg} --cluster-name {cluster} --name {nodepool} --priority Spot --eviction-policy Delete --spot-max-price {max_price} --enable-cluster-autoscaler --min-count {min} --max-count {max} --node-vm-size {vm_size}",
        "check_spot_pricing": "az vm list-skus --location {location} --size {vm_family} --query '[].{Name:name, Locations:locations[0]}' --output table",
        "enable_hybrid_benefit": "az aks update --resource-group {rg} --name {cluster} --enable-ahub"
    },
    "workload_rightsizing": {
        "get_resource_usage": "kubectl top pods --all-namespaces --containers",
        "patch_deployment_resources": "kubectl patch deployment {deployment} -n {namespace} -p '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"{container}\",\"resources\":{\"requests\":{\"cpu\":\"{cpu}\",\"memory\":\"{memory}\"},\"limits\":{\"cpu\":\"{cpu_limit}\",\"memory\":\"{memory_limit}\"}}}]}}}}'",
        "verify_deployment_status": "kubectl rollout status deployment/{deployment} -n {namespace}",
        "get_vpa_recommendations": "kubectl describe vpa {vpa_name} -n {namespace}"
    },
    "auto_scaling_optimization": {
        "create_hpa": "kubectl autoscale deployment {deployment} --cpu-percent={cpu_target} --min={min_replicas} --max={max_replicas} -n {namespace}",
        "create_vpa": "kubectl apply -f - <<EOF\\napiVersion: autoscaling.k8s.io/v1\\nkind: VerticalPodAutoscaler\\nmetadata:\\n  name: {name}-vpa\\n  namespace: {namespace}\\nspec:\\n  targetRef:\\n    apiVersion: apps/v1\\n    kind: Deployment\\n    name: {deployment}\\n  updatePolicy:\\n    updateMode: 'Auto'\\nEOF",
        "enable_cluster_autoscaler": "az aks nodepool update --resource-group {rg} --cluster-name {cluster} --name {nodepool} --enable-cluster-autoscaler --min-count {min} --max-count {max}",
        "configure_scale_down_delay": "kubectl patch configmap cluster-autoscaler-status -n kube-system -p '{\"data\":{\"scale-down-delay-after-add\":\"{delay}\"}}'"
    },
    "storage_cost_optimization": {
        "list_storage_classes": "kubectl get storageclass",
        "create_premium_ssd_v2": "kubectl apply -f - <<EOF\\napiVersion: storage.k8s.io/v1\\nkind: StorageClass\\nmetadata:\\n  name: premium-ssd-v2\\nprovisioner: disk.csi.azure.com\\nparameters:\\n  skuName: PremiumV2_LRS\\nEOF",
        "check_pv_usage": "kubectl get pv --no-headers | awk '{print $1}' | xargs -I {} kubectl describe pv {} | grep -E 'Name:|Capacity:|Used:'",
        "resize_pvc": "kubectl patch pvc {pvc_name} -n {namespace} -p '{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"{new_size}\"}}}}'"  
    },
    "network_cost_optimization": {
        "create_internal_lb": "kubectl apply -f - <<EOF\\napiVersion: v1\\nkind: Service\\nmetadata\\n  name: {service_name}\\n  annotations:\\n    service.beta.kubernetes.io/azure-load-balancer-internal: 'true'\\nspec:\\n  type: LoadBalancer\\n  ports:\\n  - port: 80\\n  selector:\\n    app: {app_label}\\nEOF",
        "check_network_policies": "kubectl get networkpolicy --all-namespaces",
        "analyze_egress_traffic": "kubectl top nodes --use-protocol-buffers",
        "optimize_service_mesh": "kubectl apply -f - <<EOF\\napiVersion: install.istio.io/v1alpha1\\nkind: IstioOperator\\nmetadata:\\n  name: control-plane\\nspec:\\n  values:\\n    pilot:\\n      env:\\n        EXTERNAL_ISTIOD: false\\nEOF"
    },
    "monitoring_cost_optimization": {
        "configure_log_retention": "kubectl patch configmap fluent-bit-config -n azure-system -p '{\"data\":{\"retention\":\"{days}d\"}}'",
        "reduce_metrics_frequency": "kubectl patch prometheus prometheus-kube-prometheus-prometheus -n monitoring --type='merge' -p '{\"spec\":{\"scrapeInterval\":\"{interval}\"}}'",
        "disable_unused_addons": "az aks disable-addons --resource-group {rg} --name {cluster} --addons {addon_list}"
    },
    "resource_cleanup": {
        "delete_unused_configmaps": "kubectl get configmaps --all-namespaces --no-headers | awk '{print $2 \" -n \" $1}' | xargs kubectl delete configmap",
        "cleanup_completed_jobs": "kubectl delete jobs --field-selector status.successful=1 --all-namespaces",
        "remove_unused_secrets": "kubectl get secrets --all-namespaces -o json | jq '.items[] | select(.metadata.name | startswith(\"default-token\") | not)' | kubectl delete -f -",
        "cleanup_evicted_pods": "kubectl get pods --all-namespaces --field-selector=status.phase=Failed -o json | kubectl delete -f -"
    },
    "schedule_based_optimization": {
        "create_cronjob_scaler": "kubectl apply -f - <<EOF\\napiVersion: batch/v1\\nkind: CronJob\\nmetadata:\\n  name: scale-down-{deployment}\\n  namespace: {namespace}\\nspec\\n  schedule: '{cron_schedule}'\\n  jobTemplate:\\n    spec:\\n      template:\\n        spec:\\n          containers:\\n          - name: kubectl\\n            image: bitnami/kubectl\\n            command: [\"kubectl\", \"scale\", \"deployment/{deployment}\", \"--replicas={replicas}\"]\\n          restartPolicy: Never\\nEOF",
        "schedule_node_pool_scaling": "az aks nodepool update --resource-group {rg} --cluster-name {cluster} --name {nodepool} --min-count {min_count} --max-count {max_count}"
    },
    "azure_best_practices": {
        "enable_managed_identity": "az aks update --resource-group {rg} --name {cluster} --enable-managed-identity",
        "configure_azure_policy": "az aks enable-addons --resource-group {rg} --name {cluster} --addons azure-policy",
        "enable_azure_defender": "az aks update --resource-group {rg} --name {cluster} --enable-defender",
        "optimize_vm_sizes": "az aks nodepool update --resource-group {rg} --cluster-name {cluster} --name {nodepool} --node-vm-size {optimized_size}"
    }
}


# Utility functions for plan generation
def get_command_template(category: CostOptimizationCategory, action_type: str) -> Optional[str]:
    """Get command template for specific optimization category and action"""
    category_key = category.value
    if category_key in AZURE_COST_OPTIMIZATION_COMMANDS:
        return AZURE_COST_OPTIMIZATION_COMMANDS[category_key].get(action_type)
    return None


def create_optimization_action_template(
    action_id: str,
    title: str,
    category: CostOptimizationCategory,
    action_type: str,
    target_resource: str = None,
    target_namespace: str = None
) -> OptimizationAction:
    """Create optimization action with command templates"""
    command_template = get_command_template(category, action_type)
    
    return OptimizationAction(
        action_id=action_id,
        title=title,
        description=f"Cost optimization action for {category.value}",
        savings_monthly=0.0,
        risk=RiskLevel.LOW,
        effort_hours=1.0,
        issue_type=StatusType.INFO,
        issue_text="Cost optimization opportunity identified",
        cost_category=category,
        target_resource=target_resource,
        target_namespace=target_namespace,
        steps=[
            ActionStep(
                step_number=1,
                label=f"Execute {action_type}",
                command=command_template or f"# Command template for {action_type}",
                command_type=CommandType.AZURE_CLI if "az " in (command_template or "") else CommandType.KUBECTL
            )
        ] if command_template else []
    )


def create_empty_plan(cluster_name: str, plan_id: str = None) -> KubeOptImplementationPlan:
    """Create an empty plan template"""
    if not plan_id:
        plan_id = f"KUBEOPT-{datetime.now().strftime('%Y-%m-%d')}-001"
    
    return KubeOptImplementationPlan(
        metadata=PlanMetadata(
            plan_id=plan_id,
            cluster_name=cluster_name,
            generated_date=datetime.now(),
            analysis_date=datetime.now(),
            last_analyzed_display="just now"
        ),
        cluster_dna_analysis=ClusterDNAAnalysis(
            overall_score=50,
            score_rating="PENDING_ANALYSIS",
            description="Analysis pending",
            metrics=[],
            data_sources=[]
        ),
        build_quality_assessment=BuildQualityAssessment(
            quality_checks=[],
            strengths=[],
            improvements=[],
            best_practices_scorecard=[]
        ),
        naming_conventions_analysis=NamingConventionsAnalysis(
            overall_score=50,
            max_score=100,
            color=ColorType.FAIR,
            resources=[],
            strengths=[],
            recommendations=[]
        ),
        roi_analysis=ROIAnalysis(
            summary_metrics=[],
            calculation_breakdown=ROICalculationBreakdown(
                total_effort_hours=0,
                hourly_rate=90,
                implementation_cost=0,
                monthly_savings=0,
                annual_savings=0,
                payback_months=0,
                roi_percentage_year1=0,
                net_savings_year1=0,
                projected_savings_3year=0
            ),
            financial_summary=[],
            savings_by_phase=[]
        ),
        implementation_summary=ImplementationSummary(
            cluster_name=cluster_name,
            environment="Unknown",
            location="Unknown",
            kubernetes_version="Unknown",
            current_monthly_cost=0,
            projected_monthly_cost=0,
            cost_reduction_percentage=0,
            implementation_duration="TBD",
            total_phases=1,
            risk_level=RiskLevel.LOW
        ),
        phases=[],
        monitoring=MonitoringGuidance(
            title="Post-Implementation Monitoring",
            description="Monitor optimization results",
            commands=[],
            key_metrics=[]
        ),
        review_schedule=[]
    )


def validate_plan_completeness(plan: KubeOptImplementationPlan) -> List[str]:
    """Validate plan completeness and return any issues"""
    issues = []
    
    if not plan.phases:
        issues.append("No implementation phases defined")
    
    if plan.total_monthly_savings <= 0:
        issues.append("No cost savings projected")
    
    if plan.total_actions == 0:
        issues.append("No optimization actions defined")
    
    for phase in plan.phases:
        if not phase.actions:
            issues.append(f"Phase {phase.phase_number} has no actions")
        
        for action in phase.actions:
            if not action.steps:
                issues.append(f"Action {action.action_id} has no implementation steps")
    
    return issues


def create_cost_optimization_phase(
    phase_number: int,
    category: CostOptimizationCategory,
    actions: List[OptimizationAction]
) -> ImplementationPhase:
    """Create a phase focused on specific cost optimization category"""
    category_names = {
        CostOptimizationCategory.AZURE_PRICING_OPTIMIZATION: "Azure Pricing Optimization",
        CostOptimizationCategory.WORKLOAD_RIGHTSIZING: "Workload Rightsizing",
        CostOptimizationCategory.AUTO_SCALING_OPTIMIZATION: "Auto-scaling Optimization",
        CostOptimizationCategory.STORAGE_COST_OPTIMIZATION: "Storage Cost Optimization",
        CostOptimizationCategory.NETWORK_COST_OPTIMIZATION: "Network Cost Optimization",
        CostOptimizationCategory.MONITORING_COST_OPTIMIZATION: "Monitoring Cost Optimization",
        CostOptimizationCategory.RESOURCE_CLEANUP: "Resource Cleanup",
        CostOptimizationCategory.SCHEDULE_BASED_OPTIMIZATION: "Schedule-based Optimization",
        CostOptimizationCategory.AZURE_BEST_PRACTICES: "Azure Best Practices"
    }
    
    total_savings = sum(action.savings_monthly for action in actions)
    total_effort = sum(action.effort_hours for action in actions)
    
    return ImplementationPhase(
        phase_number=phase_number,
        phase_name=category_names.get(category, category.value),
        description=f"Implementation phase for {category_names.get(category, category.value).lower()}",
        duration=f"{int(total_effort)}h",
        start_date=date.today(),
        end_date=date.today(),
        total_savings_monthly=total_savings,
        risk_level=RiskLevel.LOW,
        effort_hours=total_effort,
        actions=actions,
        primary_cost_categories=[category]
    )


# ═══════════════════════════════════════════════════════════════
# COST OPTIMIZATION COMMAND GENERATION UTILITIES
# ═══════════════════════════════════════════════════════════════

def generate_rightsizing_commands(deployment_name: str, namespace: str, new_cpu: str, new_memory: str) -> List[ActionStep]:
    """Generate kubectl commands for workload rightsizing"""
    return [
        ActionStep(
            step_number=1,
            label="Backup current deployment",
            command=f"kubectl get deployment {deployment_name} -n {namespace} -o yaml > {deployment_name}-backup.yaml",
            command_type=CommandType.KUBECTL
        ),
        ActionStep(
            step_number=2,
            label="Update resource requests and limits",
            command=f"kubectl patch deployment {deployment_name} -n {namespace} -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"containers\":[{{\"name\":\"{deployment_name}\",\"resources\":{{\"requests\":{{\"cpu\":\"{new_cpu}\",\"memory\":\"{new_memory}\"}},\"limits\":{{\"cpu\":\"{new_cpu}\",\"memory\":\"{new_memory}\"}}}}}}]}}}}}}}}'",
            command_type=CommandType.KUBECTL,
            validation_command=f"kubectl get deployment {deployment_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources}}'",
            success_indicators=[f"cpu: {new_cpu}", f"memory: {new_memory}"]
        ),
        ActionStep(
            step_number=3,
            label="Verify deployment rollout",
            command=f"kubectl rollout status deployment/{deployment_name} -n {namespace} --timeout=300s",
            command_type=CommandType.KUBECTL,
            success_indicators=["successfully rolled out"]
        )
    ]


def generate_spot_instance_commands(cluster_name: str, resource_group: str, nodepool_name: str, vm_size: str, max_price: str) -> List[ActionStep]:
    """Generate Azure CLI commands for spot instance node pool"""
    return [
        ActionStep(
            step_number=1,
            label="Check current node pool configuration",
            command=f"az aks nodepool show --resource-group {resource_group} --cluster-name {cluster_name} --name {nodepool_name}",
            command_type=CommandType.AZURE_CLI
        ),
        ActionStep(
            step_number=2,
            label="Create spot instance node pool",
            command=f"az aks nodepool add --resource-group {resource_group} --cluster-name {cluster_name} --name {nodepool_name}-spot --priority Spot --eviction-policy Delete --spot-max-price {max_price} --enable-cluster-autoscaler --min-count 1 --max-count 10 --node-vm-size {vm_size}",
            command_type=CommandType.AZURE_CLI,
            validation_command=f"az aks nodepool show --resource-group {resource_group} --cluster-name {cluster_name} --name {nodepool_name}-spot --query 'scaleSetPriority'",
            success_indicators=["Spot"]
        ),
        ActionStep(
            step_number=3,
            label="Verify node pool is ready",
            command=f"kubectl get nodes -l agentpool={nodepool_name}-spot",
            command_type=CommandType.KUBECTL,
            success_indicators=["Ready"]
        )
    ]


def generate_hpa_commands(deployment_name: str, namespace: str, min_replicas: int, max_replicas: int, cpu_target: int) -> List[ActionStep]:
    """Generate kubectl commands for Horizontal Pod Autoscaler"""
    return [
        ActionStep(
            step_number=1,
            label="Check if HPA already exists",
            command=f"kubectl get hpa {deployment_name} -n {namespace}",
            command_type=CommandType.KUBECTL
        ),
        ActionStep(
            step_number=2,
            label="Create Horizontal Pod Autoscaler",
            command=f"kubectl autoscale deployment {deployment_name} --cpu-percent={cpu_target} --min={min_replicas} --max={max_replicas} -n {namespace}",
            command_type=CommandType.KUBECTL,
            validation_command=f"kubectl get hpa {deployment_name} -n {namespace}",
            success_indicators=["TARGETS", f"{cpu_target}%"]
        ),
        ActionStep(
            step_number=3,
            label="Monitor HPA status",
            command=f"kubectl describe hpa {deployment_name} -n {namespace}",
            command_type=CommandType.KUBECTL,
            success_indicators=["ScalingActive", "True"]
        )
    ]


# ═══════════════════════════════════════════════════════════════
# SPLIT MODE SPECIFIC SCHEMAS
# ═══════════════════════════════════════════════════════════════

class SplitModeAction(BaseModel):
    """Simplified action for split mode validation"""
    name: Optional[str] = None
    step: Optional[str] = None
    steps: Optional[List[str]] = []
    rollback: Optional[Union[str, List[str]]] = None
    
    @validator('steps', pre=True)
    def ensure_steps_is_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []

class SplitModePhase(BaseModel):
    """Simplified phase for split mode validation"""
    phase_number: int
    name: Optional[str] = None
    actions: List[SplitModeAction] = []
    
    @validator('actions', pre=True)
    def convert_actions(cls, v):
        if not v:
            return []
        
        result = []
        for action in v:
            if isinstance(action, dict):
                result.append(SplitModeAction(**action))
            else:
                result.append(action)
        return result

class SplitModeMetadata(BaseModel):
    """Split mode metadata validation"""
    plan_id: str
    cluster_name: str
    generated_date: str

class SplitModeROISummary(BaseModel):
    """Split mode ROI validation"""
    monthly_savings: float = 0
    annual_savings: float = 0
    payback_months: Optional[int] = None
    roi_percentage: Optional[float] = None

class SplitModeMonitoring(BaseModel):
    """Split mode monitoring validation"""
    key_commands: List[str] = []
    success_metrics: List[str] = []

class SplitModeImplementationSummary(BaseModel):
    """Split mode implementation summary"""
    current_monthly_cost: float
    estimated_monthly_savings: float = 0
    duration: Optional[Union[str, int]] = None
    phases_count: Optional[int] = None

class SplitModePlanContent(BaseModel):
    """Validation schema for split mode plan content"""
    metadata: SplitModeMetadata
    implementation_summary: SplitModeImplementationSummary
    phases: List[SplitModePhase]
    roi_summary: SplitModeROISummary
    monitoring: SplitModeMonitoring
    next_steps: List[str] = []
    
    # Optional detailed analysis sections
    cluster_dna_analysis: Optional[Dict[str, Any]] = None
    build_quality_assessment: Optional[Dict[str, Any]] = None
    naming_conventions_analysis: Optional[Dict[str, Any]] = None
    roi_analysis: Optional[Dict[str, Any]] = None
    review_schedule: Optional[List[Dict[str, Any]]] = None
    
    @property
    def total_actions(self) -> int:
        """Calculate total actions across all phases"""
        return sum(len(phase.actions) for phase in self.phases)
    
    @property
    def total_monthly_savings(self) -> float:
        """Get total monthly savings"""
        return self.roi_summary.monthly_savings

class SplitModeImplementationPlan(BaseModel):
    """Complete split mode plan with metadata"""
    implementation_plan: SplitModePlanContent
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cluster_id: str
    generated_by: str
    version: str = "1.0"
    generation_method: str = "split_dual_call"
    schema_version: str = "1.0.0"
    validation_passed: bool = True
    validation_errors: Optional[List[str]] = None
    
    @property
    def total_actions(self) -> int:
        """Delegate to implementation plan"""
        return self.implementation_plan.total_actions
    
    @property
    def total_savings_monthly(self) -> float:
        """Delegate to implementation plan"""
        return self.implementation_plan.total_monthly_savings
    
    @property
    def estimated_total_savings_monthly(self) -> float:
        """Backward compatibility property for database storage"""
        return self.implementation_plan.total_monthly_savings
    
    @property
    def phases(self) -> List[SplitModePhase]:
        """Delegate to implementation plan"""
        return self.implementation_plan.phases
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def create_validated(cls, data: dict, cluster_id: str, generated_by: str):
        """Factory method that ensures validation"""
        from pydantic import ValidationError
        
        try:
            plan_content = SplitModePlanContent(**data)
            
            return cls(
                implementation_plan=plan_content,
                cluster_id=cluster_id,
                generated_by=generated_by,
                validation_passed=True,
                validation_errors=None
            )
            
        except ValidationError as e:
            # Log validation errors but create plan anyway
            errors = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
            
            minimal_data = {
                'metadata': data.get('metadata', {'plan_id': 'INVALID', 'cluster_name': cluster_id, 'generated_date': datetime.now().isoformat()}),
                'implementation_summary': data.get('implementation_summary', {'current_monthly_cost': 0, 'estimated_monthly_savings': 0}),
                'phases': data.get('phases', []),
                'roi_summary': data.get('roi_summary', {'monthly_savings': 0, 'annual_savings': 0}),
                'monitoring': data.get('monitoring', {'key_commands': [], 'success_metrics': []}),
                'next_steps': data.get('next_steps', [])
            }
            
            try:
                plan_content = SplitModePlanContent(**minimal_data)
                return cls(
                    implementation_plan=plan_content,
                    cluster_id=cluster_id,
                    generated_by=generated_by,
                    validation_passed=False,
                    validation_errors=errors
                )
            except:
                # Last resort - return with raw data (but mark as failed)
                raise ValueError(f"Critical validation failure: {errors}")