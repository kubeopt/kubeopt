from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import uuid

from .models.core import ExecutableCommand, ComprehensiveExecutionPlan, OptimizationConfig
from .generators.aks_cost_generator import AKSCostCommandGenerator
from .generators.aks_maintenance_generator import AKSMaintenanceCommandGenerator
from .generators.aks_security_generator import AKSSecurityCommandGenerator
from .generators.aks_performance_generator import AKSPerformanceCommandGenerator
from .generators.aks_addons_generator import AKSAddonsCommandGenerator
from .generators.core_optimization_generator import CoreOptimizationCommandGenerator

logger = logging.getLogger(__name__)

class AKSOptimizationOrchestrator:
    """Main orchestrator for AKS optimization command generation"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        
        # Initialize command generators
        self.cost_generator = AKSCostCommandGenerator()
        self.maintenance_generator = AKSMaintenanceCommandGenerator()
        self.security_generator = AKSSecurityCommandGenerator()
        self.performance_generator = AKSPerformanceCommandGenerator()
        self.addons_generator = AKSAddonsCommandGenerator()
        self.core_generator = CoreOptimizationCommandGenerator()
    
    def generate_priority_driven_execution_plan(self, optimization_strategy, cluster_dna,
                                              analysis_results: Dict, cluster_config: Optional[Dict] = None) -> ComprehensiveExecutionPlan:
        """Generate comprehensive priority-driven execution plan"""
        
        # Create variable context
        variable_context = self._create_variable_context(analysis_results, cluster_config)
        
        # Generate commands from all categories
        all_commands = []
        
        # Core optimization commands (HPA, rightsizing, etc.)
        try:
            core_commands = []
            core_commands.extend(self.core_generator.generate_hpa_commands(analysis_results, variable_context))
            core_commands.extend(self.core_generator.generate_rightsizing_commands(analysis_results, variable_context))
            core_commands.extend(self.core_generator.generate_node_optimization_commands(analysis_results, variable_context))
            core_commands.extend(self.core_generator.generate_storage_optimization_commands(analysis_results, variable_context))
            core_commands.extend(self.core_generator.generate_monitoring_commands(analysis_results, variable_context))
            all_commands.extend(core_commands)
        except Exception as e:
            logger.warning(f"Failed to generate core optimization commands: {e}")
        
        # Cost management commands
        try:
            cost_data = self.cost_generator.extract_cost_data(analysis_results, cluster_dna, optimization_strategy)
            cost_commands = self.cost_generator.generate_commands(cost_data, variable_context)
            all_commands.extend(cost_commands)
        except Exception as e:
            logger.warning(f"Failed to generate cost commands: {e}")
        
        # Maintenance commands
        try:
            maintenance_data = self.maintenance_generator.extract_maintenance_data(analysis_results, cluster_dna, optimization_strategy)
            maintenance_commands = self.maintenance_generator.generate_commands(maintenance_data, variable_context)
            all_commands.extend(maintenance_commands)
        except Exception as e:
            logger.warning(f"Failed to generate maintenance commands: {e}")
        
        # Security commands
        try:
            security_data = self.security_generator.extract_security_data(analysis_results, cluster_dna, optimization_strategy)
            security_commands = self.security_generator.generate_commands(security_data, variable_context)
            all_commands.extend(security_commands)
        except Exception as e:
            logger.warning(f"Failed to generate security commands: {e}")
        
        # Performance commands
        try:
            performance_data = self.performance_generator.extract_performance_data(analysis_results, cluster_dna, optimization_strategy)
            performance_commands = self.performance_generator.generate_commands(performance_data, variable_context)
            all_commands.extend(performance_commands)
        except Exception as e:
            logger.warning(f"Failed to generate performance commands: {e}")
        
        # Addons commands
        try:
            addons_data = self.addons_generator.extract_addons_data(analysis_results, cluster_dna, optimization_strategy)
            addons_commands = self.addons_generator.generate_commands(addons_data, variable_context)
            all_commands.extend(addons_commands)
        except Exception as e:
            logger.warning(f"Failed to generate addons commands: {e}")
        
        # Sort commands by priority score (highest first)
        all_commands.sort(key=lambda cmd: cmd.priority_score, reverse=True)
        
        # Categorize commands
        categorized_commands = self._categorize_commands(all_commands)
        
        # Calculate totals
        total_savings = sum(cmd.savings_estimate for cmd in all_commands)
        total_minutes = sum(cmd.estimated_duration_minutes for cmd in all_commands)
        
        # Create execution plan
        plan = ComprehensiveExecutionPlan(
            plan_id=str(uuid.uuid4()),
            cluster_name=variable_context.get('cluster_name', 'unknown'),
            resource_group=variable_context.get('resource_group', 'unknown'),
            subscription_id=variable_context.get('subscription_id'),
            strategy_name=getattr(optimization_strategy, 'strategy_name', 'AKS Optimization'),
            total_estimated_minutes=total_minutes,
            preparation_commands=categorized_commands.get('preparation', []),
            optimization_commands=categorized_commands.get('optimization', []),
            networking_commands=categorized_commands.get('networking', []),
            security_commands=categorized_commands.get('security', []),
            monitoring_commands=categorized_commands.get('monitoring', []),
            validation_commands=categorized_commands.get('validation', []),
            rollback_commands=categorized_commands.get('rollback', []),
            variable_context=variable_context,
            azure_context=self._create_azure_context(variable_context),
            kubernetes_context=self._create_kubernetes_context(variable_context),
            success_probability=self._calculate_success_probability(all_commands),
            estimated_savings=total_savings
        )
        
        return plan
    
    def _create_variable_context(self, analysis_results: Dict, cluster_config: Optional[Dict] = None) -> Dict:
        """Create variable context for command substitution"""
        context = {
            'cluster_name': analysis_results.get('cluster_name', 'unknown-cluster'),
            'resource_group': analysis_results.get('resource_group', 'unknown-rg'),
            'subscription_id': analysis_results.get('subscription_id', 'unknown-subscription'),
            'location': analysis_results.get('location', 'eastus'),
            'node_count': analysis_results.get('node_count', 3)
        }
        
        # Enhance with cluster config if available
        if cluster_config:
            context.update({
                'cluster_name': cluster_config.get('cluster_name', context['cluster_name']),
                'resource_group': cluster_config.get('resource_group', context['resource_group']),
                'subscription_id': cluster_config.get('subscription_id', context['subscription_id'])
            })
        
        return context
    
    def _categorize_commands(self, commands: List[ExecutableCommand]) -> Dict[str, List[ExecutableCommand]]:
        """Categorize commands by their function"""
        categories = {
            'preparation': [],
            'optimization': [],
            'networking': [],
            'security': [],
            'monitoring': [],
            'validation': [],
            'rollback': []
        }
        
        for cmd in commands:
            if 'cost_management' in cmd.category or 'performance' in cmd.category:
                categories['optimization'].append(cmd)
            elif 'security' in cmd.category:
                categories['security'].append(cmd)
            elif 'maintenance' in cmd.category:
                categories['preparation'].append(cmd)
            elif 'addons' in cmd.category:
                categories['monitoring'].append(cmd)
            else:
                categories['optimization'].append(cmd)
        
        return categories
    
    def _create_azure_context(self, variable_context: Dict) -> Dict:
        """Create Azure-specific context"""
        return {
            'subscription_id': variable_context.get('subscription_id'),
            'resource_group': variable_context.get('resource_group'),
            'location': variable_context.get('location', 'eastus')
        }
    
    def _create_kubernetes_context(self, variable_context: Dict) -> Dict:
        """Create Kubernetes-specific context"""
        return {
            'cluster_name': variable_context.get('cluster_name'),
            'node_count': variable_context.get('node_count', 3)
        }
    
    def _calculate_success_probability(self, commands: List[ExecutableCommand]) -> float:
        """Calculate overall success probability"""
        if not commands:
            return 0.5
        
        # Base probability on command complexity and risk levels
        high_risk_count = len([cmd for cmd in commands if cmd.risk_level == 'high'])
        medium_risk_count = len([cmd for cmd in commands if cmd.risk_level == 'medium'])
        
        base_probability = 0.85
        risk_penalty = (high_risk_count * 0.1) + (medium_risk_count * 0.05)
        
        return max(0.3, min(0.95, base_probability - risk_penalty))