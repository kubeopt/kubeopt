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
    
    # Enhanced actionable fields
    target_resource: Optional[str] = Field(None, description="Target K8s resource (deployment/pod/etc)")
    target_namespace: Optional[str] = Field(None, description="Target namespace")
    prerequisites: List[str] = Field(default=[], description="Prerequisites before execution")
    dependencies: List[str] = Field(default=[], description="Other action IDs this depends on")
    estimated_downtime: Optional[str] = Field(None, description="Expected downtime duration")
    business_impact: Optional[str] = Field(None, description="Business impact assessment")
    monitoring_commands: List[str] = Field(default=[], description="Commands to monitor after implementation")
    validation_timeout: Optional[str] = Field("5m", description="Timeout for validation steps")
    automation_ready: bool = Field(False, description="Whether action can be automated")
    requires_approval: bool = Field(False, description="Whether action requires stakeholder approval")


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
    actions: List[OptimizationAction] = Field(description="Phase actions")
    
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


# Utility functions for plan generation
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
            total_phases=0,
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