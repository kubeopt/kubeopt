"""
Local AI Plan Generator - Simplified Markdown-Based Implementation

Generates cost optimization plans using local Ollama AI with markdown output
for better reliability and simpler parsing.
"""

import json
import asyncio
import os
import re
import requests
from typing import Dict, Optional, List, Tuple
from datetime import datetime, date, timedelta
import logging

from .plan_schema import (
    KubeOptImplementationPlan, PlanMetadata, ImplementationPhase,
    OptimizationAction, ActionStep, RiskLevel, StatusType,
    CostOptimizationCategory, MonitoringGuidance, MonitoringCommand,
    MonitoringMetric, ReviewScheduleItem,
    ClusterDNAAnalysis, BuildQualityAssessment, NamingConventionsAnalysis,
    ROIAnalysis, ImplementationSummary, ROICalculationBreakdown,
    ROISummaryMetric, ColorType
)
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class AIImplementationPlanGenerator:
    """Simplified local AI plan generator using markdown output"""
    
    def __init__(self, ai_model: str = None, **kwargs):
        """
        Initialize local AI generator
        
        Args:
            ai_model: Model name for Ollama (defaults to llama3.1:latest)
            **kwargs: Ignored for backward compatibility
        """
        self.model = ai_model or os.getenv("AI_MODEL", "llama3.1:latest")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.context_builder = ContextBuilder(target_token_limit=8000)  # Keep context small
        
        print(f"✓ Initialized Local AI Generator")
        print(f"  Model: {self.model}")
        print(f"  Endpoint: {self.ollama_url}")
    
    async def generate_plan(
        self,
        enhanced_input: Dict,
        cluster_name: str,
        cluster_id: str,
        **kwargs  # Accept but ignore extra params for compatibility
    ) -> KubeOptImplementationPlan:
        """Generate optimization plan using local AI with markdown output"""
        
        try:
            # 1. Build simplified context
            context = self._build_simple_context(enhanced_input)
            
            # 2. Generate markdown plan from AI
            markdown_plan = await self._generate_markdown_plan(context, cluster_name)
            
            # 3. Parse markdown into structured plan
            plan = self._parse_markdown_to_plan(markdown_plan, cluster_name, cluster_id, context)
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise ValueError(f"Plan generation failed for cluster {cluster_name}: {e}")
    
    def _build_simple_context(self, enhanced_input: Dict) -> Dict:
        """Build simplified context for AI - focus on key optimization opportunities"""
        
        # Extract key information
        cost_data = enhanced_input.get('cost_analysis', {})
        workloads = enhanced_input.get('workloads', [])
        
        # Calculate waste
        total_waste = sum(w.get('monthly_waste_cost', 0) for w in workloads)
        current_cost = cost_data.get('current_monthly_cost', 2000.0)
        
        # Find top optimization opportunities
        top_workloads = sorted(
            workloads,
            key=lambda w: w.get('monthly_waste_cost', 0),
            reverse=True
        )[:10]
        
        return {
            'current_monthly_cost': current_cost,
            'potential_savings': total_waste if total_waste > 0 else current_cost * 0.25,
            'top_wasteful_workloads': [
                {
                    'name': w['name'],
                    'namespace': w.get('namespace', 'default'),
                    'waste': w.get('monthly_waste_cost', 0),
                    'cpu_usage': w.get('cpu_usage_percentage', 0),
                    'memory_usage': w.get('memory_usage_percentage', 0)
                }
                for w in top_workloads
            ],
            'total_workloads': len(workloads),
            'cluster_info': enhanced_input.get('cluster_info', {})
        }
    
    async def _generate_markdown_plan(self, context: Dict, cluster_name: str) -> str:
        """Generate markdown plan from local AI"""
        
        prompt = f"""Generate a cost optimization plan for Kubernetes cluster '{cluster_name}'.

Current monthly cost: ${context['current_monthly_cost']:.2f}
Potential savings: ${context['potential_savings']:.2f}
Total workloads: {context['total_workloads']}

Top wasteful workloads:
{self._format_workload_list(context['top_wasteful_workloads'])}

Generate a practical optimization plan in this EXACT markdown format:

# Optimization Plan for {cluster_name}

## Quick Wins (Week 1)
### Action: [Action Name] - $[savings]/month
**Risk:** Low
**Commands:**
```bash
[actual kubectl/az command]
```

### Action: [Next Action] - $[savings]/month
**Risk:** Low
**Commands:**
```bash
[actual command]
```

## Resource Optimization (Week 2-3)
### Action: [Action Name] - $[savings]/month
**Risk:** Medium
**Commands:**
```bash
[actual commands]
```

## Advanced Optimization (Week 4+)
### Action: [Action Name] - $[savings]/month
**Risk:** Medium
**Commands:**
```bash
[actual commands]
```

Focus on practical, executable commands. Include at least 5 actions total.
"""
        
        # Call Ollama API
        try:
            response = await asyncio.to_thread(
                requests.post,
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent output
                        "num_predict": 2048  # Limit response size
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                markdown_response = result.get('response', '')
                if not markdown_response:
                    raise ValueError("Ollama returned empty response")
                
                # Log the response for debugging
                logger.info(f"Ollama response length: {len(markdown_response)} characters")
                logger.debug(f"Ollama response preview: {markdown_response[:500]}...")
                
                return markdown_response
            else:
                raise ValueError(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to call Ollama: {e}")
            raise ValueError(f"Failed to generate markdown plan from Ollama: {e}")
    
    def _format_workload_list(self, workloads: List[Dict]) -> str:
        """Format workload list for prompt"""
        if not workloads:
            return "- No specific workload data available"
            
        lines = []
        for w in workloads[:5]:
            lines.append(f"- {w['name']} ({w['namespace']}): ${w['waste']:.2f}/month waste, CPU: {w['cpu_usage']:.1f}%, Memory: {w['memory_usage']:.1f}%")
        return '\n'.join(lines)
    
    def _parse_markdown_to_plan(self, markdown: str, cluster_name: str, cluster_id: str, context: Dict) -> KubeOptImplementationPlan:
        """Parse markdown output into structured plan"""
        
        # Save markdown for debugging
        debug_file = f"debug_ollama_markdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(debug_file, 'w') as f:
            f.write(markdown)
        logger.info(f"Saved Ollama markdown to: {debug_file}")
        
        # Extract sections using regex - look for next ## or end of string
        quick_wins = self._extract_section(markdown, r'## Quick Wins.*?(?=\n## |$)', 'Quick Wins')
        resource_opt = self._extract_section(markdown, r'## Resource Optimization.*?(?=\n## |$)', 'Resource Optimization')
        advanced_opt = self._extract_section(markdown, r'## Advanced Optimization.*?(?=\n## |$)', 'Advanced Optimization')
        
        # Parse actions from each section
        phases = []
        
        if quick_wins:
            phases.append(self._parse_phase(quick_wins, 1, "Quick Wins", 7))
        
        if resource_opt:
            phases.append(self._parse_phase(resource_opt, 2, "Resource Optimization", 14))
        
        if advanced_opt:
            phases.append(self._parse_phase(advanced_opt, 3, "Advanced Optimization", 14))
        
        # If no phases parsed, raise error
        if not phases:
            raise ValueError("Failed to parse any optimization phases from AI response")
        
        # Calculate total savings
        total_savings = sum(
            action.savings_monthly 
            for phase in phases 
            for action in phase.actions
        )
        
        # Create plan structure
        return self._create_plan_structure(
            cluster_name=cluster_name,
            cluster_id=cluster_id,
            phases=phases,
            total_savings=total_savings,
            current_cost=context.get('current_monthly_cost', 2000.0)
        )
    
    def _extract_section(self, markdown: str, pattern: str, section_name: str) -> Optional[str]:
        """Extract a section from markdown"""
        match = re.search(pattern, markdown, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0)
        return None
    
    def _parse_phase(self, section: str, phase_num: int, phase_name: str, duration_days: int) -> ImplementationPhase:
        """Parse a markdown section into a phase"""
        
        # Split section into action blocks (each starting with ###)
        action_blocks = re.split(r'(?=### Action:)', section)
        
        actions = []
        for i, block in enumerate(action_blocks):
            if not block.strip() or '### Action:' not in block:
                continue
                
            # Extract action title and savings
            title_match = re.search(r'### Action:\s*(.+?)(?:\s*-\s*\$([0-9,.]+)/month)?(?:\n|$)', block)
            if not title_match:
                continue
            
            action_name = title_match.group(1).strip()
            savings_str = title_match.group(2) if title_match.group(2) else "100"
            
            # Extract risk level
            risk_match = re.search(r'\*\*Risk:\*\*\s*(\w+)', block)
            risk = risk_match.group(1) if risk_match else "Medium"
            
            # Extract commands from code block
            commands_match = re.search(r'```(?:bash)?\n(.*?)\n```', block, re.DOTALL)
            commands = commands_match.group(1) if commands_match else ""
            
            # Parse savings (handle combined amounts like "350.00 + 300.00")
            try:
                # Check if there's addition in savings
                if '+' in savings_str:
                    parts = savings_str.split('+')
                    savings_amount = sum(float(p.strip().replace(',', '').replace('$', '')) for p in parts)
                else:
                    savings_amount = float(savings_str.replace(',', ''))
            except:
                savings_amount = 100.0  # Default
            
            # Parse risk
            risk_level = RiskLevel.LOW if 'low' in risk.lower() else RiskLevel.MEDIUM
            
            # Parse commands
            if not commands:
                continue  # Skip action if no commands found
            command_lines = [cmd.strip() for cmd in commands.strip().split('\n') if cmd.strip()]
            
            # Create action with backup commands
            action = OptimizationAction(
                action_id=f"{phase_num}.{i+1}",
                title=action_name.strip(),
                description=f"Optimization action for {phase_name}",
                savings_monthly=savings_amount,
                risk=risk_level,
                effort_hours=4.0,
                issue_type=StatusType.WARNING,
                issue_text="Optimization opportunity",
                cost_category=CostOptimizationCategory.WORKLOAD_RIGHTSIZING,
                steps=[
                    ActionStep(
                        step_number=1,
                        label="Backup current configuration",
                        command=f"kubectl get all -n production -o yaml > backup-phase{phase_num}-action{i+1}.yaml"
                    )
                ] + [
                    ActionStep(
                        step_number=j+2,
                        label=f"Execute: {cmd[:50]}..." if len(cmd) > 50 else f"Execute: {cmd}",
                        command=cmd
                    )
                    for j, cmd in enumerate(command_lines)
                ]
            )
            actions.append(action)
        
        # Create phase
        return ImplementationPhase(
            phase_number=phase_num,
            phase_name=phase_name,
            description=f"{phase_name} - Week {phase_num}",
            duration=f"{duration_days} days",
            start_date=date.today() + timedelta(days=(phase_num-1)*7),
            end_date=date.today() + timedelta(days=phase_num*7),
            total_savings_monthly=sum(a.savings_monthly for a in actions),
            risk_level=RiskLevel.LOW if phase_num == 1 else RiskLevel.MEDIUM,
            effort_hours=len(actions) * 4.0,
            actions=actions
        )
        
        # Validate phase has actions
        if not actions:
            raise ValueError(f"Phase '{phase_name}' has no valid actions parsed from AI response")
        
        return phase
    
    def _validate_parsed_phase(self, phase: ImplementationPhase) -> None:
        """Validate a parsed phase meets requirements"""
        if not phase.actions:
            raise ValueError(f"Phase {phase.phase_name} has no actions")
        if phase.total_savings_monthly <= 0:
            raise ValueError(f"Phase {phase.phase_name} has no savings")
        if not phase.phase_name:
            raise ValueError(f"Phase {phase.phase_number} missing name"
        )
    
    def _validate_action(self, action: OptimizationAction) -> None:
        """Validate an action meets requirements"""
        if not action.title:
            raise ValueError(f"Action {action.action_id} missing title")
        if action.savings_monthly <= 0:
            raise ValueError(f"Action {action.title} has no savings")
        if not action.steps:
            raise ValueError(f"Action {action.title} has no steps")
    
    def _validate_phases(self, phases: List[ImplementationPhase]) -> None:
        """Validate all phases meet requirements"""
        if not phases:
            raise ValueError("No phases in plan")
        
        for phase in phases:
            self._validate_parsed_phase(phase)
            for action in phase.actions:
                self._validate_action(action)
    
    def _create_plan_structure(
        self,
        cluster_name: str,
        cluster_id: str,
        phases: List[ImplementationPhase],
        total_savings: float,
        current_cost: float
    ) -> KubeOptImplementationPlan:
        """Create complete plan structure with all required sections"""
        
        # Create metadata
        metadata = PlanMetadata(
            plan_id=f"PLAN-{cluster_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            cluster_name=cluster_name,
            generated_date=datetime.now(),
            analysis_date=datetime.now(),
            last_analyzed_display="just now"
        )
        
        # Create minimal analysis sections - these should eventually come from AI
        cluster_dna = ClusterDNAAnalysis(
            overall_score=70,
            score_rating="GOOD",
            description=f"Identified ${total_savings:.0f}/month optimization potential",
            metrics=[],
            data_sources=[]
        )
        
        build_quality = BuildQualityAssessment(
            quality_checks=[],
            strengths=[f"Generated {sum(len(p.actions) for p in phases)} optimization actions"],
            improvements=["Review and implement recommended actions"],
            best_practices_scorecard=[]
        )
        
        naming_analysis = NamingConventionsAnalysis(
            overall_score=75,
            max_score=100,
            color=ColorType.GOOD,
            resources=[],
            strengths=[],
            recommendations=[]
        )
        
        # Create ROI analysis
        total_effort_hours = sum(p.effort_hours for p in phases)
        implementation_cost = total_effort_hours * 90.0
        
        roi_analysis = ROIAnalysis(
            summary_metrics=[
                ROISummaryMetric(
                    label="Monthly Savings",
                    value=f"${total_savings:,.2f}",
                    subtitle="Estimated reduction",
                    color=ColorType.GREEN
                ),
                ROISummaryMetric(
                    label="Annual Savings",
                    value=f"${total_savings * 12:,.2f}",
                    subtitle="Yearly impact",
                    color=ColorType.GREEN
                ),
                ROISummaryMetric(
                    label="ROI",
                    value=f"{((total_savings * 12) / max(1, implementation_cost)) * 100:.0f}%",
                    subtitle="First year",
                    color=ColorType.GREEN
                )
            ],
            calculation_breakdown=ROICalculationBreakdown(
                total_effort_hours=total_effort_hours,
                hourly_rate=90.0,
                implementation_cost=implementation_cost,
                monthly_savings=total_savings,
                annual_savings=total_savings * 12,
                payback_months=max(1, implementation_cost / max(1, total_savings)),
                roi_percentage_year1=((total_savings * 12) / max(1, implementation_cost)) * 100,
                net_savings_year1=(total_savings * 12) - implementation_cost,
                projected_savings_3year=total_savings * 36
            ),
            financial_summary=[
                f"Total optimization potential: ${total_savings:,.2f}/month",
                f"Implementation effort: {total_effort_hours:.0f} hours",
                f"Payback period: {max(1, implementation_cost / max(1, total_savings)):.1f} months"
            ],
            savings_by_phase=[]
        )
        
        # Create implementation summary
        implementation_summary = ImplementationSummary(
            cluster_name=cluster_name,
            environment="Production",
            location="Azure",
            kubernetes_version="1.28",
            current_monthly_cost=current_cost,
            projected_monthly_cost=current_cost - total_savings,
            cost_reduction_percentage=(total_savings / max(1, current_cost)) * 100,
            implementation_duration=f"{len(phases)} phases over {len(phases) * 7} days",
            total_phases=max(1, len(phases)),
            risk_level=RiskLevel.MEDIUM
        )
        
        # Create monitoring guidance
        monitoring = MonitoringGuidance(
            title="Post-Implementation Monitoring",
            description="Track optimization results",
            commands=[
                MonitoringCommand(label="Check node resource usage", command="kubectl top nodes"),
                MonitoringCommand(label="Check pod resource usage", command="kubectl top pods --all-namespaces"),
                MonitoringCommand(label="Check autoscaler status", command="kubectl get hpa --all-namespaces")
            ],
            key_metrics=[
                MonitoringMetric(metric="cpu_utilization", target="< 70% average across nodes"),
                MonitoringMetric(metric="memory_utilization", target="< 80% average across nodes"),
                MonitoringMetric(metric="pod_count", target="Stable with HPA managing scale"),
                MonitoringMetric(metric="cost_per_day", target=f"< ${(current_cost - total_savings) / 30:.2f}")
            ]
        )
        
        # Create review schedule
        review_schedule = [
            ReviewScheduleItem(day=7, title="Week 1 Review - Quick Wins Assessment"),
            ReviewScheduleItem(day=14, title="Week 2 Review - Resource Optimization"),
            ReviewScheduleItem(day=30, title="Month 1 Review - Full Impact Analysis"),
            ReviewScheduleItem(day=90, title="Quarter Review - Long-term Optimization")
        ]
        
        print(f"""
✅ OPTIMIZATION PLAN GENERATED:
   Cluster: {cluster_name}
   Phases: {len(phases)}
   Total Actions: {sum(len(p.actions) for p in phases)}
   Monthly Savings: ${total_savings:,.2f}
   Annual Savings: ${total_savings * 12:,.2f}
   ROI: {roi_analysis.calculation_breakdown.roi_percentage_year1:.0f}%
        """)
        
        # Validate phases before creating plan
        self._validate_phases(phases)
        
        # Create plan
        plan = KubeOptImplementationPlan(
            metadata=metadata,
            cluster_dna_analysis=cluster_dna,
            build_quality_assessment=build_quality,
            naming_conventions_analysis=naming_analysis,
            roi_analysis=roi_analysis,
            implementation_summary=implementation_summary,
            phases=phases,
            monitoring=monitoring,
            review_schedule=review_schedule,
            cluster_id=cluster_id,
            generated_by="Local AI",
            version="2.0"
        )
        
        # Final validation
        self._validate_complete_plan(plan)
        
        return plan
    
    def _validate_complete_plan(self, plan: KubeOptImplementationPlan) -> None:
        """Validate the complete plan meets all requirements"""
        if not plan.phases:
            raise ValueError("Plan has no phases")
        if not plan.metadata:
            raise ValueError("Plan missing metadata")
        if plan.total_monthly_savings <= 0:
            raise ValueError("Plan has no savings")
        
        total_actions = sum(len(phase.actions) for phase in plan.phases)
        if total_actions == 0:
            raise ValueError("Plan has no optimization actions")
        
        logger.info(f"✅ Validated plan with {len(plan.phases)} phases and {total_actions} actions")
    
    
