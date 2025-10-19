"""
Plan Validator

Validates Claude API responses against schema and business rules.
Ensures generated plans are safe, executable, and follow best practices.
"""

import re
from typing import Dict, List, Set
from pydantic import ValidationError
from .plan_schema import (
    KubeOptImplementationPlan, ImplementationPlanDocument, 
    OptimizationAction, validate_plan_completeness
)
import logging


class PlanValidator:
    """Validates Claude API responses against schema and business rules"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_monthly_savings = 100000  # Sanity check: $100k/month max
        self.valid_kubectl_prefixes = [
            "kubectl get", "kubectl apply", "kubectl patch", "kubectl scale",
            "kubectl top", "kubectl describe", "kubectl logs", "kubectl exec"
        ]
        self.valid_az_prefixes = [
            "az aks", "az vm", "az vmss", "az disk", "az network"
        ]
        
    def validate(self, plan_json: Dict, cluster_id: str, cluster_name: str, context_optimization: Dict = None) -> KubeOptImplementationPlan:
        """
        Validate and enrich the plan with enhanced validation for context-optimized plans.
        
        Validation checks:
        1. Schema compliance (Pydantic validation)
        2. Business rules (savings > 0, risk levels valid, etc.)
        3. Action dependencies are resolvable
        4. Commands are syntactically valid
        5. No duplicate action IDs
        6. Realistic savings estimates
        7. Context optimization quality (if applicable)
        """
        try:
            # Step 1: Sanitize the plan_json to fix common validation issues
            sanitized_plan_json = self._sanitize_plan_json(plan_json)
            
            # Handle both root document and direct plan formats
            if 'implementation_plan' in sanitized_plan_json:
                # Root document format
                document = ImplementationPlanDocument(**sanitized_plan_json)
                plan = document.implementation_plan
            else:
                # Direct plan format
                plan = KubeOptImplementationPlan(**sanitized_plan_json)
            
            # Step 2: Business logic validation
            self._validate_kubeopt_plan(plan)
            
            # Step 3: Context optimization validation (if provided)
            if context_optimization is not None and context_optimization:
                self._validate_context_optimization(plan, context_optimization)
            
            # Step 4: Enrich with cluster metadata
            plan.metadata.cluster_name = cluster_name
            
            self.logger.info(f"KubeOpt plan validation successful for cluster {cluster_name}")
            return plan
            
        except ValidationError as e:
            self.logger.error(f"Schema validation failed: {e}")
            raise ValueError(f"Plan validation failed: {e}")
        except Exception as e:
            self.logger.error(f"Business rule validation failed: {e}")
            raise ValueError(f"Plan validation failed: {e}")
    
    def _sanitize_plan_json(self, plan_json: Dict) -> Dict:
        """
        Sanitize plan JSON to fix common validation issues from Claude API
        """
        import copy
        sanitized = copy.deepcopy(plan_json)
        
        # Access the implementation_plan if it's nested
        if 'implementation_plan' in sanitized:
            impl_plan = sanitized['implementation_plan']
        else:
            impl_plan = sanitized
        
        # Fix 1: Clamp DNA metrics values to 100
        if 'cluster_dna_analysis' in impl_plan and 'metrics' in impl_plan['cluster_dna_analysis']:
            for metric in impl_plan['cluster_dna_analysis']['metrics']:
                if 'value' in metric and metric['value'] > 100:
                    self.logger.warning(f"DNA metric '{metric.get('label', 'unknown')}' value {metric['value']} clamped to 100")
                    metric['value'] = 100
                if 'percentage' in metric and metric['percentage'] > 100:
                    self.logger.warning(f"DNA metric '{metric.get('label', 'unknown')}' percentage {metric['percentage']} clamped to 100")
                    metric['percentage'] = 100
        
        # Fix 2: Convert invalid ROI analysis colors to valid enum values
        if 'roi_analysis' in impl_plan and 'summary_metrics' in impl_plan['roi_analysis']:
            color_mapping = {
                'warning': 'poor',
                'success': 'excellent', 
                'danger': 'poor',
                'primary': 'blue',
                'secondary': 'fair',
                'info': 'blue',
                'light': 'fair',
                'dark': 'poor'
            }
            for metric in impl_plan['roi_analysis']['summary_metrics']:
                if 'color' in metric and metric['color'] in color_mapping:
                    old_color = metric['color']
                    metric['color'] = color_mapping[old_color]
                    self.logger.warning(f"ROI metric color '{old_color}' mapped to '{metric['color']}'")
        
        # Fix 3: Set default kubernetes_version if None or missing
        if 'implementation_summary' in impl_plan:
            if 'kubernetes_version' not in impl_plan['implementation_summary'] or impl_plan['implementation_summary']['kubernetes_version'] is None:
                impl_plan['implementation_summary']['kubernetes_version'] = "Unknown"
                self.logger.warning("Kubernetes version was None or missing, set to 'Unknown'")
        
        # Fix 4: Ensure all required fields have valid values
        if 'metadata' in impl_plan:
            if 'plan_id' not in impl_plan['metadata'] or not impl_plan['metadata']['plan_id']:
                from datetime import datetime
                impl_plan['metadata']['plan_id'] = f"KUBEOPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                self.logger.warning("Generated missing plan_id")
        
        return sanitized
    
    def _validate_kubeopt_plan(self, plan: KubeOptImplementationPlan):
        """Validate KubeOpt-specific business rules"""
        
        # Validate completeness using schema utility
        issues = validate_plan_completeness(plan)
        if issues is not None and issues:
            raise ValueError(f"Plan completeness issues: {'; '.join(issues)}")
        
        # Validate savings calculations
        self._validate_kubeopt_savings(plan)
        
        # Validate action dependencies and commands
        self._validate_dependencies(plan)
        self._validate_commands(plan)
        self._validate_action_ids(plan)
        
        # Validate DNA scores
        self._validate_dna_scores(plan)
        
        self.logger.info("KubeOpt business rule validation passed")
    
    def _validate_context_optimization(self, plan: KubeOptImplementationPlan, context_optimization: Dict):
        """Validate context optimization impact on plan quality"""
        
        optimization_strategy = context_optimization.get('optimization_strategy', 'unknown')
        reduction_percentage = context_optimization.get('reduction_percentage', 0)
        original_tokens = context_optimization.get('original_tokens', 0)
        optimized_tokens = context_optimization.get('optimized_tokens', 0)
        
        self.logger.info(f"Validating context optimization: {optimization_strategy}, {reduction_percentage}% reduction")
        
        # Validate optimization metrics
        if reduction_percentage < 0 or reduction_percentage > 100:
            raise ValueError("Invalid reduction percentage in context optimization")
        
        if optimized_tokens > original_tokens:
            raise ValueError("Optimized tokens cannot exceed original tokens")
        
        # Set quality expectations based on optimization level
        if optimization_strategy == 'complete':
            # Full data - expect high-quality detailed plans
            self._validate_complete_plan_quality(plan)
        elif optimization_strategy == 'medium_optimization':
            # Top 30 resources - expect good quality with some generalizations
            self._validate_medium_optimized_plan_quality(plan, reduction_percentage)
        elif optimization_strategy == 'aggressive_optimization':
            # Top 10 resources - expect strategic focus on highest impact
            self._validate_aggressive_optimized_plan_quality(plan, reduction_percentage)
        
        # Log optimization impact assessment
        self._assess_optimization_impact(plan, context_optimization)
    
    def _validate_complete_plan_quality(self, plan: KubeOptImplementationPlan):
        """Validate plan quality for complete data (small clusters)"""
        
        # Expect detailed, specific recommendations
        if plan.total_actions < 5:
            self.logger.warning("Complete plan has fewer than 5 actions - may be under-analyzed")
        
        # Check for specific resource names in actions
        specific_resource_count = 0
        for phase in plan.phases:
            for action in phase.actions:
                if any(keyword in action.description.lower() for keyword in 
                      ['deployment/', 'pod/', 'service/', 'namespace/']):
                    specific_resource_count += 1
        
        if specific_resource_count < (plan.total_actions * 0.5):
            self.logger.warning("Complete plan lacks specific resource references")
    
    def _validate_medium_optimized_plan_quality(self, plan: KubeOptImplementationPlan, reduction_percentage: float):
        """Validate plan quality for medium optimization (30 resources)"""
        
        # Expect good balance of specific and general recommendations
        if plan.total_actions < 3:
            self.logger.warning("Medium-optimized plan has very few actions")
        
        # Check for mix of resource-specific and namespace-level recommendations
        resource_specific = 0
        namespace_general = 0
        
        for phase in plan.phases:
            for action in phase.actions:
                desc_lower = action.description.lower()
                if any(keyword in desc_lower for keyword in 
                      ['deployment/', 'pod/', 'service/']):
                    resource_specific += 1
                elif any(keyword in desc_lower for keyword in 
                        ['namespace', 'across', 'multiple']):
                    namespace_general += 1
        
        # Expect reasonable balance for medium optimization
        if resource_specific == 0 and namespace_general == 0:
            self.logger.warning("Medium-optimized plan lacks both specific and general recommendations")
        
        # Higher reduction should correlate with more general recommendations
        if reduction_percentage > 50 and resource_specific > namespace_general:
            self.logger.info("High reduction plan appropriately focuses on general optimizations")
    
    def _validate_aggressive_optimized_plan_quality(self, plan: KubeOptImplementationPlan, reduction_percentage: float):
        """Validate plan quality for aggressive optimization (10 resources)"""
        
        # Expect strategic, high-impact focus
        if plan.total_actions < 2:
            self.logger.warning("Aggressively-optimized plan has very few actions")
        
        # Check that actions focus on high-impact, strategic optimizations
        high_impact_keywords = [
            'cluster-wide', 'namespace-level', 'resource class', 'scaling policy',
            'node pool', 'autoscaler', 'resource quotas', 'limit ranges'
        ]
        
        strategic_actions = 0
        for phase in plan.phases:
            for action in phase.actions:
                desc_lower = action.description.lower()
                if any(keyword in desc_lower for keyword in high_impact_keywords):
                    strategic_actions += 1
                # Also count actions with high savings
                if hasattr(action, 'monthly_savings') and action.monthly_savings > 100:
                    strategic_actions += 1
        
        strategic_ratio = strategic_actions / plan.total_actions if plan.total_actions > 0 else 0
        if strategic_ratio < 0.5:
            self.logger.warning("Aggressively-optimized plan should focus more on strategic, high-impact actions")
        
        # Validate that high reduction correlates with appropriate focus
        if reduction_percentage > 70:
            self.logger.info("High reduction plan appropriately focuses on strategic optimizations")
    
    def _assess_optimization_impact(self, plan: KubeOptImplementationPlan, context_optimization: Dict):
        """Assess and log the impact of context optimization on plan quality"""
        
        reduction_percentage = context_optimization.get('reduction_percentage', 0)
        optimization_strategy = context_optimization.get('optimization_strategy', 'unknown')
        
        # Calculate plan comprehensiveness metrics
        total_actions = plan.total_actions
        total_savings = plan.total_monthly_savings
        avg_action_savings = total_savings / total_actions if total_actions > 0 else 0
        
        # Assess optimization impact
        impact_assessment = {
            "optimization_strategy": optimization_strategy,
            "data_reduction_percentage": reduction_percentage,
            "plan_metrics": {
                "total_actions": total_actions,
                "total_monthly_savings": total_savings,
                "average_action_savings": avg_action_savings,
                "phases": len(plan.phases)
            },
            "quality_indicators": {
                "actions_per_phase": total_actions / len(plan.phases) if plan.phases else 0,
                "savings_per_action": avg_action_savings,
                "has_rollback_procedures": self._count_rollback_procedures(plan),
                "command_specificity": self._assess_command_specificity(plan)
            }
        }
        
        # Log assessment
        self.logger.info(f"Optimization impact assessment: {impact_assessment}")
        
        # Provide recommendations based on assessment
        if reduction_percentage > 60 and avg_action_savings < 50:
            self.logger.warning("High data reduction may have impacted savings recommendations")
        
        if reduction_percentage > 80 and total_actions < 3:
            self.logger.warning("Aggressive optimization may have reduced plan comprehensiveness")
    
    def _count_rollback_procedures(self, plan: KubeOptImplementationPlan) -> int:
        """Count actions with proper rollback procedures"""
        count = 0
        for phase in plan.phases:
            for action in phase.actions:
                if hasattr(action, 'rollback') and action.rollback:
                    count += 1
        return count
    
    def _assess_command_specificity(self, plan: KubeOptImplementationPlan) -> float:
        """Assess how specific the kubectl commands are (0-1 scale)"""
        specific_commands = 0
        total_commands = 0
        
        specific_indicators = [
            'deployment/', 'service/', 'pod/', 'namespace/',
            '--namespace=', '-n ', 'get pods', 'describe'
        ]
        
        for phase in plan.phases:
            for action in phase.actions:
                if hasattr(action, 'steps'):
                    for step in action.steps:
                        if hasattr(step, 'command'):
                            total_commands += 1
                            if any(indicator in step.command.lower() for indicator in specific_indicators):
                                specific_commands += 1
        
        return specific_commands / total_commands if total_commands > 0 else 0
    
    def _validate_kubeopt_savings(self, plan: KubeOptImplementationPlan):
        """Validate KubeOpt savings calculations"""
        
        # Check total savings bounds
        total_savings = plan.total_monthly_savings
        if total_savings <= 0:
            raise ValueError("Total monthly savings must be positive")
            
        if total_savings > self.max_monthly_savings:
            raise ValueError(f"Monthly savings ${total_savings} exceeds maximum ${self.max_monthly_savings}")
        
        # Validate ROI calculations
        roi_calc = plan.roi_analysis.calculation_breakdown
        if abs(roi_calc.annual_savings - (roi_calc.monthly_savings * 12)) > 0.01:
            self.logger.warning("Annual savings calculation may be incorrect")
        
        # Validate phase-level savings
        total_phase_savings = sum(phase.total_savings_monthly for phase in plan.phases)
        if abs(total_phase_savings - total_savings) > 0.01:
            self.logger.warning("Phase savings don't match total savings")
    
    def _validate_dna_scores(self, plan: KubeOptImplementationPlan):
        """Validate DNA analysis scores"""
        
        dna = plan.cluster_dna_analysis
        if not (0 <= dna.overall_score <= 100):
            raise ValueError("DNA overall score must be between 0 and 100")
        
        for metric in dna.metrics:
            if not (0 <= metric.value <= 100):
                raise ValueError(f"DNA metric {metric.label} score must be between 0 and 100")
            if metric.value != metric.percentage:
                self.logger.warning(f"DNA metric {metric.label}: value and percentage don't match")
    
    def _validate_savings(self, plan: KubeOptImplementationPlan):
        """Ensure savings calculations are realistic"""
        
        # Check total savings bounds
        if plan.estimated_total_savings_monthly <= 0:
            raise ValueError("Total monthly savings must be positive")
            
        if plan.estimated_total_savings_monthly > self.max_monthly_savings:
            raise ValueError(f"Monthly savings ${plan.estimated_total_savings_monthly} exceeds maximum ${self.max_monthly_savings}")
        
        # Check individual action savings
        total_action_savings = 0
        for phase in plan.phases:
            for action in phase.actions:
                if action.estimated_monthly_savings <= 0:
                    raise ValueError(f"Action {action.id} must have positive savings")
                    
                if action.estimated_monthly_savings > self.max_monthly_savings:
                    raise ValueError(f"Action {action.id} savings ${action.estimated_monthly_savings} exceeds maximum")
                
                # Check ROI calculation
                expected_annual = action.estimated_monthly_savings * 12
                if abs(action.estimated_annual_savings - expected_annual) > 0.01:
                    self.logger.warning(f"Action {action.id}: Annual savings calculation may be incorrect")
                
                # Check ROI months
                if action.one_time_cost > 0:
                    expected_roi = action.one_time_cost / action.estimated_monthly_savings
                    if abs(action.roi_months - expected_roi) > 0.1:
                        self.logger.warning(f"Action {action.id}: ROI calculation may be incorrect")
                        
                total_action_savings += action.estimated_monthly_savings
        
        # Check total vs sum of actions (allow 10% variance for rounding)
        if abs(total_action_savings - plan.estimated_total_savings_monthly) > (plan.estimated_total_savings_monthly * 0.1):
            self.logger.warning("Total savings doesn't match sum of action savings")
        
    def _validate_dependencies(self, plan: KubeOptImplementationPlan):
        """Check that action dependencies form a valid DAG"""
        
        # Collect all action IDs
        all_action_ids = set()
        action_dependencies = {}
        
        for phase in plan.phases:
            for action in phase.actions:
                all_action_ids.add(action.action_id)
                action_dependencies[action.action_id] = getattr(action, 'dependencies', [])
        
        # Check all dependencies exist
        for action_id, deps in action_dependencies.items():
            for dep in deps:
                if dep not in all_action_ids:
                    raise ValueError(f"Action {action_id} depends on non-existent action {dep}")
        
        # Check for circular dependencies using DFS
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for dep in action_dependencies.get(node, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for action_id in all_action_ids:
            if action_id not in visited:
                if has_cycle(action_id, visited, set()):
                    raise ValueError(f"Circular dependency detected involving action {action_id}")
        
        self.logger.info("Dependency validation passed")
    
    def _validate_commands(self, plan: KubeOptImplementationPlan):
        """Basic syntax check for kubectl/az commands"""
        
        for phase in plan.phases:
            for action in phase.actions:
                # Validate step commands
                for step in action.steps:
                    self._validate_kubectl_command(step.command, action.action_id)
                
                # Validate rollback commands if present
                if action.rollback:
                    self._validate_kubectl_command(action.rollback.command, f"{action.action_id}-rollback")
    
    def _validate_kubectl_command(self, command: str, action_id: str):
        """Validate kubectl command syntax"""
        command = command.strip()
        
        # Check for valid kubectl prefix
        if not any(command.startswith(prefix) for prefix in self.valid_kubectl_prefixes):
            self.logger.warning(f"Action {action_id}: Potentially invalid kubectl command: {command}")
        
        # Check for dangerous operations
        dangerous_patterns = [
            r'kubectl\s+delete\s+namespace',
            r'kubectl\s+delete\s+node',
            r'--force\s+--grace-period=0',
            r'kubectl\s+drain.*--delete-emptydir-data.*--ignore-daemonsets.*--force'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                self.logger.warning(f"Action {action_id}: Potentially dangerous kubectl command: {command}")
    
    def _validate_az_command(self, command: str, action_id: str):
        """Validate Azure CLI command syntax"""
        command = command.strip()
        
        # Check for valid az prefix
        if not any(command.startswith(prefix) for prefix in self.valid_az_prefixes):
            self.logger.warning(f"Action {action_id}: Potentially invalid az command: {command}")
        
        # Check for dangerous operations
        dangerous_patterns = [
            r'az\s+group\s+delete',
            r'az\s+aks\s+delete',
            r'--yes\s+--no-wait'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                self.logger.warning(f"Action {action_id}: Potentially dangerous az command: {command}")
    
    def _validate_action_ids(self, plan: KubeOptImplementationPlan):
        """Check for duplicate action IDs"""
        seen_ids = set()
        
        for phase in plan.phases:
            for action in phase.actions:
                if action.action_id in seen_ids:
                    raise ValueError(f"Duplicate action ID: {action.action_id}")
                seen_ids.add(action.action_id)
        
        self.logger.info(f"Action ID validation passed: {len(seen_ids)} unique actions")
    
    def _validate_risk_levels(self, plan: KubeOptImplementationPlan):
        """Validate risk level distribution"""
        risk_counts = {"Very Low": 0, "Low": 0, "Medium": 0, "High": 0, "Critical": 0}
        
        for phase in plan.phases:
            for action in phase.actions:
                risk_level = action.risk.value if hasattr(action.risk, 'value') else str(action.risk)
                if risk_level in risk_counts:
                    risk_counts[risk_level] += 1
        
        # Warn if too many high-risk actions
        high_risk_count = risk_counts["High"] + risk_counts["Critical"]
        if high_risk_count > 3:
            self.logger.warning(f"Plan contains {high_risk_count} high/critical risk actions - consider reducing")
    
    def _validate_timeframes(self, plan: KubeOptImplementationPlan):
        """Validate implementation timeframes are realistic"""
        
        # Pattern to match time estimates (e.g., "2-4 hours", "30 minutes", "1 day")
        time_pattern = r'(\d+(?:-\d+)?)\s*(minutes?|hours?|days?|weeks?)'
        
        for phase in plan.phases:
            phase_duration = phase.duration
            if not re.search(time_pattern, phase_duration, re.IGNORECASE):
                self.logger.warning(f"Phase {phase.phase_number}: Invalid duration format: {phase_duration}")
            
            for action in phase.actions:
                effort_hours = action.effort_hours
                if effort_hours < 0 or effort_hours > 100:
                    self.logger.warning(f"Action {action.action_id}: Unrealistic effort hours: {effort_hours}")
    
    def generate_validation_report(self, plan: KubeOptImplementationPlan) -> Dict:
        """Generate a validation report for the plan"""
        
        report = {
            "cluster_name": plan.metadata.cluster_name,
            "plan_id": plan.metadata.plan_id,
            "validation_timestamp": plan.metadata.generated_date.isoformat(),
            "total_actions": plan.total_actions,
            "phases": len(plan.phases),
            "dna_score": plan.cluster_dna_analysis.overall_score,
            "savings_summary": {
                "monthly": plan.total_monthly_savings,
                "annual": plan.roi_analysis.calculation_breakdown.annual_savings
            },
            "warnings": [],
            "recommendations": []
        }
        
        # Add recommendations based on validation
        if plan.cluster_dna_analysis.overall_score < 60:
            report["recommendations"].append("Low DNA score - improve cluster configuration quality")
        
        if plan.total_monthly_savings > 1000:
            report["recommendations"].append("High savings potential - prioritize implementation")
        
        if plan.total_effort_hours > 40:
            report["recommendations"].append("High effort required - consider phased approach")
        
        return report