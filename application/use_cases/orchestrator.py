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
from pydantic import BaseModel, Field, validator

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
            hpa_cmds = self.core_generator.generate_hpa_commands(analysis_results, variable_context)
            rightsizing_cmds = self.core_generator.generate_rightsizing_commands(analysis_results, variable_context)
            node_cmds = self.core_generator.generate_node_optimization_commands(analysis_results, variable_context)
            storage_cmds = self.core_generator.generate_storage_optimization_commands(analysis_results, variable_context)
            networking_cmds = self.core_generator.generate_networking_commands(analysis_results, variable_context)
            monitoring_cmds = self.core_generator.generate_monitoring_commands(analysis_results, variable_context)
            
            core_commands.extend(hpa_cmds)
            core_commands.extend(rightsizing_cmds)
            core_commands.extend(node_cmds)
            core_commands.extend(storage_cmds)
            core_commands.extend(networking_cmds)
            core_commands.extend(monitoring_cmds)
            
            logger.info(f"🔧 Core commands: HPA={len(hpa_cmds)}, Rightsizing={len(rightsizing_cmds)}, Node={len(node_cmds)}, Storage={len(storage_cmds)}, Network={len(networking_cmds)}, Monitor={len(monitoring_cmds)}")
            all_commands.extend(core_commands)
        except Exception as e:
            logger.warning(f"Failed to generate core optimization commands: {e}")
        
        # Generate additional commands based on analysis results - no arbitrary thresholds
        
        # Cost management commands (if any cost optimizations detected)
        cost_opportunities = analysis_results.get('optimization_opportunities', {}).get('cost_reduction', [])
        total_potential_savings = analysis_results.get('total_savings', 0)
        if cost_opportunities or total_potential_savings > 0:
            try:
                cost_data = self.cost_generator.extract_cost_data(analysis_results, cluster_dna, optimization_strategy)
                cost_commands = self.cost_generator.generate_commands(cost_data, variable_context)
                all_commands.extend(cost_commands)
                logger.info(f"🔄 Generated cost management commands (${total_potential_savings:.2f} potential savings)")
            except Exception as e:
                logger.warning(f"Failed to generate cost commands: {e}")
        
        # Maintenance commands (based on actual cluster health or version issues)
        health_score = analysis_results.get('current_health_score', 100)
        kubernetes_version = analysis_results.get('kubernetes_version')
        cluster_issues = analysis_results.get('cluster_issues', [])
        if health_score < 90 or kubernetes_version or cluster_issues:
            try:
                maintenance_data = self.maintenance_generator.extract_maintenance_data(analysis_results, cluster_dna, optimization_strategy)
                maintenance_commands = self.maintenance_generator.generate_commands(maintenance_data, variable_context)
                all_commands.extend(maintenance_commands)
                logger.info(f"🔄 Generated maintenance commands (health: {health_score}, issues: {len(cluster_issues)})")
            except Exception as e:
                logger.warning(f"Failed to generate maintenance commands: {e}")
        
        # Security commands (if security analysis exists or security issues found)
        security_analysis = analysis_results.get('security_analysis', {})
        security_issues = analysis_results.get('security_issues', [])
        if security_analysis or security_issues:
            try:
                security_data = self.security_generator.extract_security_data(analysis_results, cluster_dna, optimization_strategy)
                security_commands = self.security_generator.generate_commands(security_data, variable_context)
                all_commands.extend(security_commands)
                security_score = security_analysis.get('security_posture', {}).get('overall_score', 'N/A')
                logger.info(f"🔄 Generated security commands (score: {security_score}, issues: {len(security_issues)})")
            except Exception as e:
                logger.warning(f"Failed to generate security commands: {e}")
        
        # Performance commands (if performance issues or metrics exist)
        performance_metrics = analysis_results.get('performance_metrics', {})
        avg_cpu = analysis_results.get('current_cpu_utilization', 0)
        avg_memory = analysis_results.get('current_memory_utilization', 0)
        networking_savings = analysis_results.get('networking_monthly_savings', 0)
        if performance_metrics or avg_cpu > 0 or avg_memory > 0 or networking_savings > 0:
            try:
                performance_data = self.performance_generator.extract_performance_data(analysis_results, cluster_dna, optimization_strategy)
                performance_commands = self.performance_generator.generate_commands(performance_data, variable_context)
                all_commands.extend(performance_commands)
                logger.info(f"🔄 Generated performance commands (CPU: {avg_cpu}%, Memory: {avg_memory}%)")
            except Exception as e:
                logger.warning(f"Failed to generate performance commands: {e}")
        
        # Addons commands (if specific addon opportunities or integrations detected)
        addon_opportunities = analysis_results.get('addon_opportunities', [])
        monitoring_gaps = analysis_results.get('monitoring_gaps', [])
        if addon_opportunities or monitoring_gaps:
            try:
                addons_data = self.addons_generator.extract_addons_data(analysis_results, cluster_dna, optimization_strategy)
                addons_commands = self.addons_generator.generate_commands(addons_data, variable_context)
                all_commands.extend(addons_commands)
                logger.info(f"🔄 Generated addons commands ({len(addon_opportunities)} opportunities, {len(monitoring_gaps)} gaps)")
            except Exception as e:
                logger.warning(f"Failed to generate addons commands: {e}")
        
        # Sort commands by priority score (highest first)
        all_commands.sort(key=lambda cmd: cmd.priority_score, reverse=True)
        
        # Categorize commands
        categorized_commands = self._categorize_commands(all_commands)
        
        # Log command distribution for debugging
        logger.info(f"📊 Command distribution: Total={len(all_commands)}")
        for category, cmds in categorized_commands.items():
            if cmds is not None and cmds:
                logger.info(f"   {category}: {len(cmds)} commands")
        
        # Calculate totals
        total_savings = sum(cmd.savings_estimate for cmd in all_commands)
        total_minutes = sum(cmd.estimated_duration_minutes for cmd in all_commands)
        
        # Create phase_commands mapping for backward compatibility
        phase_commands = self._create_phase_commands_mapping(all_commands)
        
        # Log final command distribution for UI debugging
        logger.info(f"🎯 Final UI Data: categories={len([k for k,v in categorized_commands.items() if v])}, phases={len([k for k,v in phase_commands.items() if v])}")
        logger.info(f"📊 Categories populated: {[k for k,v in categorized_commands.items() if v]}")
        logger.info(f"📅 Phases populated: {[k for k,v in phase_commands.items() if v]}")
        
        # Calculate enhanced timeline information
        timeline_info = self._calculate_enhanced_timeline(phase_commands, total_minutes)
        
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
            estimated_savings=total_savings,
            phase_commands=phase_commands,  # Add phase_commands for backward compatibility
            cluster_intelligence={'timeline_info': timeline_info}  # Enhanced timeline data
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
        if cluster_config is not None and cluster_config:
            context.update({
                'cluster_name': cluster_config.get('cluster_name', context['cluster_name']),
                'resource_group': cluster_config.get('resource_group', context['resource_group']),
                'subscription_id': cluster_config.get('subscription_id', context['subscription_id'])
            })
            
        # Log warning if still using default values (could indicate data flow issue)
        if 'unknown' in context.get('cluster_name', '') or 'unknown' in context.get('resource_group', ''):
            logger.warning(f"⚠️ Using default cluster context - cluster: {context.get('cluster_name')}, rg: {context.get('resource_group')}")
            logger.warning("⚠️ This may result in invalid commands. Check analysis_results data flow.")
        
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
            # Core optimization categories
            if cmd.category in ['hpa_optimization', 'resource_rightsizing', 'node_optimization', 'storage_optimization']:
                categories['optimization'].append(cmd)
            # Cost management and performance
            elif 'cost_management' in cmd.category or 'performance' in cmd.category:
                categories['optimization'].append(cmd)
            # Networking
            elif 'networking' in cmd.category:
                categories['networking'].append(cmd)
            # Security
            elif 'security' in cmd.category:
                categories['security'].append(cmd)
            # Maintenance and preparation
            elif 'maintenance' in cmd.category:
                categories['preparation'].append(cmd)
            # Monitoring and addons
            elif 'addons' in cmd.category or 'monitoring' in cmd.category:
                categories['monitoring'].append(cmd)
            # Validation commands
            elif 'validation' in cmd.category:
                categories['validation'].append(cmd)
            # Rollback commands  
            elif 'rollback' in cmd.category:
                categories['rollback'].append(cmd)
            # Default to optimization
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
    
    def _create_phase_commands_mapping(self, commands: List[ExecutableCommand]) -> Dict[str, List[ExecutableCommand]]:
        """Create phase_commands mapping for backward compatibility with implementation_generator"""
        
        # Map commands to the EXACT phases expected by implementation_generator
        # Include ALL phases to ensure UI doesn't skip any
        phase_mapping = {
            'phase-1': [],   # Environment Assessment and Preparation
            'phase-2': [],   # Configuration and Setup
            'phase-3': [],   # Dynamic HPA Implementation  
            'phase-4': [],   # Driven Resource Right-sizing Optimization
            'phase-5': [],   # Enhanced Storage Optimization
            'phase-6': [],   # Security Foundation Setup
            'phase-7': [],   # Compliance Framework Implementation
            'phase-8': [],   # Enhanced Monitoring and Observability
            'phase-9': [],   # Network Optimization
            'phase-10': [],  # Performance Optimization
            'phase-11': []   # Enhanced Final Validation and Optimization
        }
        
        # Distribute commands across phases intelligently using ALL command categories
        for cmd in commands:
            # Phase 1: Environment Assessment and Preparation
            if cmd.category in ['aks_maintenance'] or 'preparation' in cmd.category:
                phase_mapping['phase-1'].append(cmd)
            
            # Phase 2: Configuration and Setup
            elif cmd.category in ['aks_addons']:
                phase_mapping['phase-2'].append(cmd)
            
            # Phase 3: Dynamic HPA Implementation
            elif cmd.category in ['hpa_optimization']:
                phase_mapping['phase-3'].append(cmd)
            
            # Phase 4: Driven Resource Right-sizing Optimization  
            elif cmd.category in ['resource_rightsizing']:
                phase_mapping['phase-4'].append(cmd)
            
            # Phase 5: Enhanced Storage Optimization
            elif cmd.category in ['storage_optimization']:
                phase_mapping['phase-5'].append(cmd)
            
            # Phase 6: Security Foundation Setup
            elif cmd.category in ['aks_security']:
                phase_mapping['phase-6'].append(cmd)
            
            # Phase 7: Compliance Framework Implementation
            elif cmd.category in ['node_optimization']:
                phase_mapping['phase-7'].append(cmd)
            
            # Phase 8: Enhanced Monitoring and Observability
            elif cmd.category in ['monitoring_optimization']:
                phase_mapping['phase-8'].append(cmd)
            
            # Phase 9: Network Optimization
            elif cmd.category in ['networking_optimization']:
                phase_mapping['phase-9'].append(cmd)
            
            # Phase 10: Performance Optimization
            elif cmd.category in ['aks_performance']:
                phase_mapping['phase-10'].append(cmd)
            
            # Phase 11: Enhanced Final Validation and Optimization (cost management, validation)
            elif cmd.category in ['aks_cost_management'] or 'validation' in cmd.category:
                phase_mapping['phase-11'].append(cmd)
            
            else:
                # If no specific mapping, distribute to phase 1 (preparation)
                phase_mapping['phase-1'].append(cmd)
                logger.warning(f"⚠️ Unknown command category '{cmd.category}' mapped to phase-1")
        
        # Ensure balanced distribution - if a phase is empty, redistribute some commands
        self._balance_phase_distribution(phase_mapping)
        
        # Ensure each command has proper ID for tracking
        for phase_id, phase_commands in phase_mapping.items():
            for i, cmd in enumerate(phase_commands):
                if not cmd.id:
                    cmd.id = f"{phase_id}-cmd-{i+1}"
        
        # Log the mapping for debugging
        logger.info(f"📋 Created phase mapping for {len(commands)} total commands:")
        for phase_id, phase_commands in phase_mapping.items():
            logger.info(f"   {phase_id}: {len(phase_commands)} commands")
        
        return phase_mapping
    
    def _balance_phase_distribution(self, phase_mapping: Dict[str, List[ExecutableCommand]]):
        """Ensure phases have balanced command distribution"""
        
        # Get phases with commands and phases without
        populated_phases = {k: v for k, v in phase_mapping.items() if v}
        empty_phases = [k for k, v in phase_mapping.items() if not v]
        
        # If we have empty phases and commands to redistribute
        if empty_phases and populated_phases:
            # Find the phase with the most commands
            max_phase = max(populated_phases.keys(), key=lambda k: len(phase_mapping[k]))
            max_commands = phase_mapping[max_phase]
            
            # Redistribute commands to empty phases (max 2 per empty phase to keep it manageable)
            for empty_phase in empty_phases:
                if len(max_commands) > 2:
                    # Move 1-2 commands to empty phase
                    commands_to_move = min(2, len(max_commands) // 2)
                    moved_commands = max_commands[-commands_to_move:]
                    phase_mapping[empty_phase].extend(moved_commands)
                    phase_mapping[max_phase] = max_commands[:-commands_to_move]
                    
                    logger.info(f"🔄 Redistributed {commands_to_move} commands from {max_phase} to {empty_phase}")
                    
                    # Update max_commands for next iteration
                    max_commands = phase_mapping[max_phase]
    
    def _calculate_enhanced_timeline(self, phase_commands: Dict[str, List[ExecutableCommand]], 
                                   total_minutes: int) -> Dict:
        """Calculate enhanced timeline information aligned with cost savings and realistic implementation time"""
        
        # Calculate total savings to determine timeline urgency  
        total_savings = sum(
            cmd.savings_estimate for phase_cmds in phase_commands.values() 
            for cmd in phase_cmds
        )
        
        # Realistic timeline based on savings magnitude and complexity
        # Higher savings justify more aggressive timelines, but respect practical limits
        if total_savings > 5000:  # High impact optimization
            base_multiplier = 0.8  # Aggressive timeline
            max_weeks_per_phase = 2
        elif total_savings > 2000:  # Medium impact
            base_multiplier = 1.0  # Standard timeline  
            max_weeks_per_phase = 3
        elif total_savings > 500:  # Low-medium impact
            base_multiplier = 1.2  # Conservative timeline
            max_weeks_per_phase = 4
        else:  # Low impact
            base_multiplier = 1.5  # Extended timeline
            max_weeks_per_phase = 6
        
        timeline = {
            'total_weeks': 0,  # Will be calculated based on phase durations
            'total_phases': len([p for p in phase_commands.values() if p]),
            'phases_detail': {},
            'execution_schedule': [],
            'cost_savings_driven': True,
            'total_monthly_savings': total_savings,
            'implementation_urgency': 'high' if total_savings > 5000 else 'medium' if total_savings > 2000 else 'low'
        }
        
        current_week = 1
        phase_order = ['phase-1', 'phase-3', 'phase-4', 'phase-5', 'phase-7', 'phase-8', 'phase-11']
        
        for phase_id in phase_order:
            commands = phase_commands.get(phase_id, [])
            if not commands:
                continue
            
            # Calculate phase duration based on realistic implementation time
            phase_minutes = sum(cmd.estimated_duration_minutes for cmd in commands)
            phase_savings = sum(cmd.savings_estimate for cmd in commands)
            
            # Realistic phase duration calculation
            # Base: estimated minutes converted to hours, then to work weeks (assuming 20 productive hours/week for optimization work)
            base_hours = max(8, phase_minutes / 60)  # Minimum 8 hours per phase
            work_weeks = max(1, base_hours / 20)  # 20 productive hours per week for complex optimization
            
            # Apply savings-based multiplier
            phase_weeks = max(1, min(max_weeks_per_phase, int(work_weeks * base_multiplier)))
            
            # Adjust for high-value phases (more time if high savings)
            if phase_savings > 1000:
                phase_weeks = min(max_weeks_per_phase, phase_weeks + 1)
            
            # Calculate complexity and risk factors
            avg_priority = sum(cmd.priority_score for cmd in commands) / len(commands) if commands else 50
            high_risk_commands = len([cmd for cmd in commands if cmd.risk_level == 'high'])
            medium_risk_commands = len([cmd for cmd in commands if cmd.risk_level == 'medium'])
            
            # Risk-based duration adjustment
            if high_risk_commands > len(commands) / 2:  # Majority high risk
                phase_weeks = min(max_weeks_per_phase * 1.5, phase_weeks + 1)
            elif medium_risk_commands > len(commands) / 2:  # Majority medium risk
                phase_weeks = min(max_weeks_per_phase * 1.2, phase_weeks)
            
            timeline['phases_detail'][phase_id] = {
                'week_start': current_week,
                'week_end': current_week + phase_weeks - 1,
                'duration_weeks': phase_weeks,
                'command_count': len(commands),
                'estimated_hours': base_hours,
                'phase_savings': phase_savings,
                'avg_priority': avg_priority,
                'risk_level': 'high' if high_risk_commands > len(commands) / 2 else 'medium' if (high_risk_commands + medium_risk_commands) > 0 else 'low',
                'parallel_execution': len(commands) > 3 and phase_savings < 2000,  # Parallel only for lower-risk phases
                'savings_impact': 'high' if phase_savings > 1000 else 'medium' if phase_savings > 300 else 'low'
            }
            
            # Create execution schedule entry
            week_display = f"Week {current_week}" if phase_weeks == 1 else f"Weeks {current_week}-{current_week + phase_weeks - 1}"
            timeline['execution_schedule'].append({
                'phase': phase_id,
                'weeks': week_display,
                'focus': self._get_phase_focus(phase_id),
                'deliverables': self._get_phase_deliverables(commands),
                'expected_savings': f"${phase_savings:.0f}/month" if phase_savings > 0 else "Foundational",
                'risk_assessment': timeline['phases_detail'][phase_id]['risk_level']
            })
            
            current_week += phase_weeks
        
        timeline['total_weeks'] = current_week - 1
        
        # Add realistic timeline validation
        if timeline['total_weeks'] > 24:  # More than 6 months is unrealistic for AKS optimization
            logger.warning(f"Timeline too long ({timeline['total_weeks']} weeks), capping at 24 weeks")
            timeline['total_weeks'] = 24
            timeline['timeline_capped'] = True
        
        # Add ROI calculation
        if timeline['total_weeks'] > 0 and total_savings > 0:
            timeline['roi_months'] = timeline['total_weeks'] / 4  # Convert weeks to months
            timeline['breakeven_period'] = f"{timeline['roi_months']:.1f} months"
            timeline['annual_savings'] = total_savings * 12
            timeline['implementation_cost_weeks'] = timeline['total_weeks']
            
        logger.info(f"🕒 Calculated realistic timeline: {timeline['total_weeks']} weeks for ${total_savings}/month savings")
        
        return timeline
    
    def _get_phase_focus(self, phase_id: str) -> str:
        """Get the main focus area for a phase"""
        focus_map = {
            'phase-1': 'Environment Assessment & Setup',
            'phase-3': 'HPA Implementation & Auto-scaling',
            'phase-4': 'Resource Right-sizing & Node Optimization', 
            'phase-5': 'Storage Optimization & Cost Reduction',
            'phase-7': 'Security Hardening & Compliance',
            'phase-8': 'Monitoring & Observability Enhancement',
            'phase-11': 'Final Validation & Cost Management'
        }
        return focus_map.get(phase_id, 'Optimization Activities')
    
    def _get_phase_deliverables(self, commands: List[ExecutableCommand]) -> List[str]:
        """Extract key deliverables from phase commands"""
        deliverables = []
        
        for cmd in commands[:3]:  # Top 3 commands represent main deliverables
            if 'enable' in cmd.description.lower():
                deliverables.append(f"Enabled {cmd.description.split(' ')[-3:]}")
            elif 'create' in cmd.description.lower():
                deliverables.append(f"Created {cmd.description.split(' ')[-2:]}")
            elif 'optimize' in cmd.description.lower():
                deliverables.append(f"Optimized {cmd.category.replace('_', ' ').title()}")
            else:
                # Generic deliverable based on category
                deliverables.append(f"{cmd.category.replace('_', ' ').title()} Configuration")
        
        return deliverables[:3] if deliverables else ['Configuration Updates']