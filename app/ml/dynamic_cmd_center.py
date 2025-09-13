"""
Dynamic Command Center - Modular AKS Optimization System

This file now serves as the main orchestrator for the modular command generation system.
The original large implementation has been broken down into focused modules under command_center/.

Usage remains the same for backward compatibility:
    from app.ml.dynamic_cmd_center import AdvancedExecutableCommandGenerator
"""

import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

# Import the new modular components at class level to avoid circular imports
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

class AdvancedExecutableCommandGenerator:
    """
    Main command generator that orchestrates the modular system.
    
    This maintains backward compatibility while using the new modular architecture.
    The original 8700+ line implementation has been broken down into focused modules:
    
    - command_center/models/: Core data structures
    - command_center/generators/: Command generators by category
    - command_center/analyzers/: Analysis components  
    - command_center/orchestrator.py: Main coordination logic
    """
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.cluster_config = None  # For backward compatibility
        
        # Initialize the modular orchestrator
        try:
            from .command_center import AKSOptimizationOrchestrator
            self.orchestrator = AKSOptimizationOrchestrator(self.config)
            logger.info("✅ Modular AKS Optimization Orchestrator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}")
            # Fallback to basic functionality
            self.orchestrator = None
    
    def generate_priority_driven_execution_plan(self, optimization_strategy, cluster_dna,
                                              analysis_results: Dict, cluster_config: Optional[Dict] = None) -> ComprehensiveExecutionPlan:
        """
        Generate comprehensive priority-driven execution plan using the modular system.
        
        This method maintains the same interface as the original implementation
        but now uses the clean, modular architecture internally.
        
        Args:
            optimization_strategy: Strategy object with optimization opportunities
            cluster_dna: Cluster DNA analysis results
            analysis_results: Analysis results dictionary
            cluster_config: Optional cluster configuration
            
        Returns:
            ComprehensiveExecutionPlan: Complete execution plan with categorized commands
        """
        
        # Use stored cluster config if not provided as parameter
        effective_cluster_config = cluster_config or self.cluster_config
        
        if self.orchestrator:
            try:
                return self.orchestrator.generate_priority_driven_execution_plan(
                    optimization_strategy, cluster_dna, analysis_results, effective_cluster_config
                )
            except Exception as e:
                logger.error(f"❌ Orchestrator failed, using fallback: {e}")
        
        # Fallback implementation for backward compatibility
        return self._create_fallback_plan(analysis_results, effective_cluster_config)
    
    def generate_comprehensive_execution_plan(self, optimization_strategy, cluster_dna,
                                            analysis_results: Dict, cluster_config: Optional[Dict] = None,
                                            implementation_phases: List = None) -> ComprehensiveExecutionPlan:
        """
        Backward compatibility method for generate_comprehensive_execution_plan.
        
        This delegates to the new generate_priority_driven_execution_plan method.
        """
        logger.info("🔄 Using backward compatibility method: generate_comprehensive_execution_plan")
        
        return self.generate_priority_driven_execution_plan(
            optimization_strategy, cluster_dna, analysis_results, cluster_config
        )
    
    def set_cluster_config(self, cluster_config: Dict):
        """
        Backward compatibility method for set_cluster_config.
        
        In the modular system, cluster config is passed directly to the plan generation method.
        """
        logger.info("🔧 Cluster config will be used in next plan generation")
        self.cluster_config = cluster_config
    
    def _create_fallback_plan(self, analysis_results: Dict, cluster_config: Optional[Dict] = None) -> ComprehensiveExecutionPlan:
        """Create a basic fallback plan if the modular system fails"""
        
        variable_context = {
            'cluster_name': analysis_results.get('cluster_name', 'unknown-cluster'),
            'resource_group': analysis_results.get('resource_group', 'unknown-rg'),
            'subscription_id': analysis_results.get('subscription_id', 'unknown-subscription')
        }
        
        # Basic command for testing
        basic_command = ExecutableCommand(
            command="kubectl get nodes",
            description="Verify cluster connectivity",
            category="validation",
            priority_score=50
        )
        
        return ComprehensiveExecutionPlan(
            plan_id=str(uuid.uuid4()),
            cluster_name=variable_context['cluster_name'],
            resource_group=variable_context['resource_group'],
            subscription_id=variable_context['subscription_id'],
            strategy_name="Fallback AKS Optimization",
            total_estimated_minutes=5,
            preparation_commands=[],
            optimization_commands=[basic_command],
            networking_commands=[],
            security_commands=[],
            monitoring_commands=[],
            validation_commands=[],
            rollback_commands=[],
            variable_context=variable_context,
            azure_context={'resource_group': variable_context['resource_group']},
            kubernetes_context={'cluster_name': variable_context['cluster_name']},
            success_probability=0.8,
            estimated_savings=0
        )

# Additional classes that might be imported elsewhere
class HPAAnalyzer:
    """HPA analysis utilities"""
    @staticmethod
    def calculate_optimization_score(hpa: Dict, analysis_type: str = 'enhanced') -> float:
        try:
            from .command_center.analyzers.hpa_analyzer import HPAAnalyzer as ModularHPAAnalyzer
            return ModularHPAAnalyzer.calculate_optimization_score(hpa, analysis_type)
        except ImportError:
            # Fallback basic implementation
            return 0.5

# Export everything that was previously available
__all__ = [
    'AdvancedExecutableCommandGenerator',
    'OptimizationConfig',
    'ExecutableCommand',
    'ComprehensiveExecutionPlan', 
    'HPAAnalyzer'
]