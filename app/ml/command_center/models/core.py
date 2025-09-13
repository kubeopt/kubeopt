from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class OptimizationConfig:
    """Centralized configuration to eliminate magic numbers"""
    cpu_cost_per_core_per_month: float = 25.0
    memory_cost_per_gb_per_month: float = 3.5
    default_hpa_cpu_target: int = 70
    default_hpa_memory_target: int = 70
    aggressive_efficiency_threshold: float = 0.6
    conservative_efficiency_threshold: float = 0.8
    default_min_replicas: int = 2
    default_max_replicas_multiplier: int = 3

@dataclass
class ExecutableCommand:
    """Enhanced executable command with cluster config awareness"""
    command: str
    description: str
    category: str
    priority_score: int = 50
    savings_estimate: float = 0
    id: str = ""
    subcategory: str = ""
    yaml_content: Optional[str] = None
    validation_commands: List[str] = None
    rollback_commands: List[str] = None
    expected_outcome: str = ""
    success_criteria: List[str] = None
    timeout_seconds: int = 300
    retry_attempts: int = 3
    prerequisites: List[str] = None
    estimated_duration_minutes: int = 5
    risk_level: str = "low"
    monitoring_metrics: List[str] = None
    variable_substitutions: Dict[str, Any] = None
    azure_specific: bool = False
    kubectl_specific: bool = False
    cluster_specific: bool = False
    real_workload_targets: Optional[List[str]] = None
    config_derived_complexity: Optional[float] = None

    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.validation_commands is None:
            self.validation_commands = []
        if self.rollback_commands is None:
            self.rollback_commands = []
        if self.success_criteria is None:
            self.success_criteria = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.monitoring_metrics is None:
            self.monitoring_metrics = []
        if self.variable_substitutions is None:
            self.variable_substitutions = {}

@dataclass
class ComprehensiveExecutionPlan:
    """Enhanced execution plan with cluster config intelligence"""
    plan_id: str
    cluster_name: str
    resource_group: str
    strategy_name: str
    total_estimated_minutes: int
    
    preparation_commands: List[ExecutableCommand]
    optimization_commands: List[ExecutableCommand]
    networking_commands: List[ExecutableCommand]
    security_commands: List[ExecutableCommand]
    monitoring_commands: List[ExecutableCommand]
    validation_commands: List[ExecutableCommand]
    rollback_commands: List[ExecutableCommand]
    
    variable_context: Dict[str, Any]
    azure_context: Dict[str, Any]
    kubernetes_context: Dict[str, Any]
    success_probability: float
    estimated_savings: float
    
    subscription_id: Optional[str] = None
    cluster_intelligence: Optional[Dict[str, Any]] = None
    config_enhanced: bool = False
    phase_commands: Optional[Dict[str, List[ExecutableCommand]]] = None

    @property
    def total_timeline_weeks(self) -> int:
        """Convert total estimated minutes to weeks (assuming 40 hours per week)"""
        total_hours = self.total_estimated_minutes / 60
        weeks = max(1, int(total_hours / 40))
        return weeks
    
    @property
    def total_timeline_hours(self) -> float:
        """Convert total estimated minutes to hours"""
        return self.total_estimated_minutes / 60
    
    @property 
    def total_effort_hours(self) -> float:
        """Alias for total_timeline_hours for compatibility"""
        return self.total_timeline_hours