"""
Claude AI Plan Generator - Comprehensive Implementation Plan Generation

Generates extensive, production-ready cost optimization plans using Claude API
with deep analysis of all available cluster data, validated commands, and
comprehensive rollback procedures.

Key Improvements:
- Extracts and uses ALL available data from enhanced_input
- Generates 8 comprehensive implementation phases
- Creates specific, validated kubectl/az commands for each action
- Includes backup and rollback procedures for all changes
- Provides detailed ROI analysis and monitoring guidance
- Uses real workload names, namespaces, and cost figures
"""

import json
import asyncio
import os
import re
import requests
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, date, timedelta
import logging

from .plan_schema import (
    KubeOptImplementationPlan, PlanMetadata, ImplementationPhase,
    OptimizationAction, ActionStep, RiskLevel, StatusType,
    CostOptimizationCategory, MonitoringGuidance, MonitoringCommand,
    MonitoringMetric, ReviewScheduleItem,
    ClusterDNAAnalysis, BuildQualityAssessment, NamingConventionsAnalysis,
    ROIAnalysis, ImplementationSummary, ROICalculationBreakdown,
    ROISummaryMetric, ColorType, DataSource
)
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class AIImplementationPlanGenerator:
    """
    Claude AI plan generator with comprehensive analysis and cost tracking.
    
    This generator creates extensive, production-ready implementation plans by:
    1. Extracting all available data from cluster analysis
    2. Categorizing and prioritizing optimization opportunities
    3. Generating validated kubectl/az commands with rollback procedures
    4. Creating phased implementation approach with risk management
    5. Providing detailed ROI projections and monitoring guidance
    """
    
    # Phase definitions with priorities, durations, and focus areas
    OPTIMIZATION_PHASES = [
        {
            "name": "Emergency Stabilization & Baseline",
            "priority": 1,
            "duration_days": 3,
            "risk": "low",
            "focus": ["backup_creation", "monitoring_baseline", "critical_assessment"],
            "description": "Establish safety measures and document current cluster state"
        },
        {
            "name": "Quick Wins - Resource Right-Sizing",
            "priority": 2,
            "duration_days": 7,
            "risk": "low",
            "focus": ["over_provisioned_workloads", "cpu_optimization", "memory_optimization"],
            "description": "Low-risk, high-impact resource adjustments for immediate savings"
        },
        {
            "name": "HPA Implementation & Autoscaling",
            "priority": 3,
            "duration_days": 7,
            "risk": "medium",
            "focus": ["missing_hpa", "hpa_tuning", "scaling_policies", "vpa_evaluation"],
            "description": "Deploy and configure Horizontal Pod Autoscalers"
        },
        {
            "name": "Namespace Governance & Resource Quotas",
            "priority": 4,
            "duration_days": 7,
            "risk": "medium",
            "focus": ["resource_quotas", "limit_ranges", "namespace_policies", "rbac_optimization"],
            "description": "Establish comprehensive resource governance"
        },
        {
            "name": "Storage Optimization & Cleanup",
            "priority": 5,
            "duration_days": 7,
            "risk": "medium",
            "focus": ["pvc_rightsizing", "storage_class_optimization", "orphaned_volumes", "snapshot_cleanup"],
            "description": "Optimize persistent storage and clean up waste"
        },
        {
            "name": "Network Cost Reduction",
            "priority": 6,
            "duration_days": 7,
            "risk": "medium",
            "focus": ["load_balancer_consolidation", "ingress_optimization", "egress_reduction", "private_endpoints"],
            "description": "Optimize network architecture and reduce egress costs"
        },
        {
            "name": "Node Pool Optimization",
            "priority": 7,
            "duration_days": 14,
            "risk": "high",
            "focus": ["node_rightsizing", "spot_instances", "node_pool_consolidation", "autoscaler_tuning"],
            "description": "Optimize compute infrastructure and enable intelligent scaling"
        },
        {
            "name": "Advanced Optimization & Continuous Improvement",
            "priority": 8,
            "duration_days": 14,
            "risk": "medium",
            "focus": ["pod_disruption_budgets", "priority_classes", "advanced_scheduling", "cost_alerting"],
            "description": "Implement advanced features and establish ongoing optimization"
        }
    ]
    
    def __init__(self, ai_model: str = None, **kwargs):
        """
        Initialize Claude AI generator with comprehensive configuration.
        
        Args:
            ai_model: Claude model to use (defaults to claude-3-5-sonnet-20241022)
            **kwargs: Additional configuration options
        """
        self.model = ai_model or os.getenv("AI_MODEL", "claude-3-5-haiku-20241022")
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.context_builder = ContextBuilder(target_token_limit=12000)
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Claude pricing per 1K tokens (as of December 2024)
        self.pricing = {
            "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20241218": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075}
        }
        
        model_pricing = self.pricing.get(self.model, {"input": 0.003, "output": 0.015})
        self.input_cost_per_1k = model_pricing["input"]
        self.output_cost_per_1k = model_pricing["output"]
        
        if not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        print(f"✓ Initialized Claude AI Generator (Comprehensive Mode)")
        print(f"  Model: {self.model}")
        print(f"  Endpoint: {self.claude_url}")
        print(f"  Pricing: ${self.input_cost_per_1k}/1K input, ${self.output_cost_per_1k}/1K output")
        print(f"  Phases: {len(self.OPTIMIZATION_PHASES)} comprehensive phases configured")
    
    async def generate_plan(
        self,
        enhanced_input: Dict,
        cluster_name: str,
        cluster_id: str,
        **kwargs
    ) -> Dict:
        """
        Generate comprehensive optimization plan using Claude AI.
        
        This method orchestrates the complete plan generation process:
        1. Builds comprehensive context from all available data
        2. Generates detailed analysis sections
        3. Creates the implementation plan via Claude API
        4. Returns raw markdown for display
        
        Args:
            enhanced_input: Complete cluster analysis data from previous stages
            cluster_name: Name of the AKS cluster
            cluster_id: Unique cluster identifier
            **kwargs: Additional parameters for extensibility
            
        Returns:
            Dict: Raw markdown plan for UI display
        """
        try:
            print(f"\n🔍 Building comprehensive context for {cluster_name}...")
            
            # 1. Extract and structure all available data
            context = self._build_comprehensive_context(enhanced_input)
            
            print(f"   Found {context['total_optimization_count']} optimization opportunities")
            print(f"   Potential savings: ${context['total_potential_savings']:,.2f}/month")
            
            # 2. Generate detailed analysis sections for the prompt
            print(f"\n📊 Generating analysis sections...")
            analysis_sections = self._generate_analysis_sections(context)
            
            # 3. Generate implementation plan via Claude
            print(f"\n
            markdown_plan = await self._generate_comprehensive_plan(
                context, 
                analysis_sections, 
                cluster_name
            )
            
            # 4. Save raw markdown for debugging
            #timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # debug_file = f"debug_comprehensive_plan_{cluster_id}_{timestamp}.md"
            # with open(debug_file, 'w') as f:
            #     f.write(markdown_plan)
            # logger.info(f"Raw Claude response saved to: {debug_file}")
            # print(f"   📝 Debug output saved to: {debug_file}")
            
            # 5. Return raw markdown plan (no parsing needed)
            print(f"\n✅ Claude plan generation complete!")
            print(f"   📄 Raw markdown plan ready for UI display")
            #print(f"   📝 Plan saved to: {debug_file}")
            
            # Return plan object with the markdown
            return {
                'status': 'success',
                'plan_type': 'markdown',
                'raw_markdown': markdown_plan,
                'cluster_id': cluster_id,
                'cluster_name': cluster_name,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise ValueError(f"Plan generation failed for cluster {cluster_name}: {e}")
    
    # ==========================================================================
    # CONTEXT BUILDING METHODS
    # ==========================================================================
    
    def _build_comprehensive_context(self, enhanced_input: Dict) -> Dict:
        """
        Build comprehensive context extracting ALL available data points.
        
        This method performs deep extraction of every useful piece of information
        from the enhanced input to provide Claude with maximum context.
        """
        # Core analysis data
        cost_analysis = enhanced_input.get('cost_analysis', {})
        cluster_info = enhanced_input.get('cluster_info', {})
        node_pools = enhanced_input.get('node_pools', [])
        optimization_opportunities = enhanced_input.get('optimization_opportunities', [])
        
        # Cost metrics extraction
        current_cost = cost_analysis.get('total_cost', 0.0)
        cost_savings = cost_analysis.get('cost_savings', {})
        potential_savings = cost_savings.get('total_monthly_savings', 0.0)
        savings_breakdown = cost_savings.get('savings_breakdown', {})
        
        # Efficiency data
        optimization_potential = cost_savings.get('optimization_potential', {})
        efficiency_metrics = optimization_potential.get('efficiency_metrics', {})
        node_optimization = optimization_potential.get('node_optimization_potential', {})
        
        # Categorize opportunities with enriched metadata
        opportunities_by_type = self._categorize_opportunities(optimization_opportunities)
        
        # Deep workload analysis
        workloads = enhanced_input.get('workloads', [])
        workload_analysis = self._analyze_workloads(workloads, optimization_opportunities)
        
        # Namespace governance analysis
        namespaces = enhanced_input.get('namespaces', [])
        namespace_analysis = self._analyze_namespaces(namespaces)
        
        # Storage waste analysis
        storage_volumes = enhanced_input.get('storage_volumes', [])
        storage_analysis = self._analyze_storage(storage_volumes)
        
        # Network cost analysis
        network_resources = enhanced_input.get('network_resources', {})
        network_analysis = self._analyze_network(network_resources)
        
        # Inefficiency root cause analysis
        inefficient_workloads = enhanced_input.get('inefficient_workloads', {})
        inefficiency_analysis = self._analyze_inefficiencies(inefficient_workloads)
        
        # HPA coverage analysis
        existing_hpas = enhanced_input.get('existing_hpas', [])
        hpa_analysis = self._analyze_hpas(existing_hpas, workloads)
        
        # Cluster metadata
        metadata = enhanced_input.get('metadata', {})
        
        # Calculate derived metrics
        savings_percentage = (potential_savings / current_cost * 100) if current_cost > 0 else 0
        target_efficiency = efficiency_metrics.get('target_system_efficiency', 0.8)
        current_efficiency = efficiency_metrics.get('current_system_efficiency', 0)
        efficiency_gap = target_efficiency - current_efficiency
        
        return {
            # Cluster identification
            'cluster_info': cluster_info,
            'cluster_metadata': metadata,
            
            # Cost metrics
            'current_monthly_cost': current_cost,
            'total_potential_savings': potential_savings,
            'annual_savings': potential_savings * 12,
            'savings_percentage': savings_percentage,
            'savings_breakdown': savings_breakdown,
            
            # Infrastructure details
            'node_pools': node_pools,
            'node_pool_count': len(node_pools),
            'total_nodes': sum(pool.get('node_count', 0) for pool in node_pools),
            'node_optimization': node_optimization,
            
            # Efficiency metrics
            'efficiency_metrics': efficiency_metrics,
            'efficiency_gap': efficiency_gap,
            'target_efficiency': target_efficiency,
            'current_efficiency': current_efficiency,
            
            # Categorized opportunities
            'optimization_opportunities': opportunities_by_type,
            'total_optimization_count': len(optimization_opportunities),
            'raw_opportunities': optimization_opportunities,
            
            # Detailed analyses
            'workload_analysis': workload_analysis,
            'namespace_analysis': namespace_analysis,
            'storage_analysis': storage_analysis,
            'network_analysis': network_analysis,
            'inefficiency_analysis': inefficiency_analysis,
            'hpa_analysis': hpa_analysis,
            
            # Raw data for command generation
            'raw_workloads': workloads,
            'raw_namespaces': namespaces,
            'raw_storage': storage_volumes,
            'raw_network': network_resources,
            'raw_inefficient': inefficient_workloads,
            'raw_hpas': existing_hpas
        }
    
    def _categorize_opportunities(self, opportunities: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize and enrich optimization opportunities by type."""
        categorized = {
            'right_sizing': [],
            'hpa_optimization': [],
            'networking': [],
            'storage': [],
            'node_optimization': [],
            'governance': [],
            'security': [],
            'other': []
        }
        
        for opp in opportunities:
            opp_type = opp.get('type', 'other').lower()
            
            # Map to standard categories
            if any(x in opp_type for x in ['right', 'size', 'resource']):
                category = 'right_sizing'
            elif any(x in opp_type for x in ['hpa', 'autoscal', 'scaling']):
                category = 'hpa_optimization'
            elif any(x in opp_type for x in ['network', 'load', 'egress', 'ingress']):
                category = 'networking'
            elif any(x in opp_type for x in ['storage', 'pvc', 'volume', 'disk']):
                category = 'storage'
            elif any(x in opp_type for x in ['node', 'pool', 'vm', 'compute']):
                category = 'node_optimization'
            elif any(x in opp_type for x in ['quota', 'limit', 'governance']):
                category = 'governance'
            elif any(x in opp_type for x in ['security', 'policy', 'rbac']):
                category = 'security'
            else:
                category = 'other'
            
            # Enrich with priority and complexity
            enriched = {
                **opp,
                'category': category,
                'priority': self._calculate_priority(opp),
                'complexity': self._assess_complexity(opp),
                'estimated_effort_hours': self._estimate_effort(opp)
            }
            categorized[category].append(enriched)
        
        # Sort each category by priority
        for category in categorized:
            categorized[category].sort(key=lambda x: (x.get('priority', 5), -x.get('potential_monthly_savings', 0)))
        
        return categorized
    
    def _calculate_priority(self, opportunity: Dict) -> int:
        """Calculate priority (1=highest, 5=lowest) based on impact and risk."""
        savings = opportunity.get('potential_monthly_savings', 0)
        risk = opportunity.get('risk', 'medium').lower()
        confidence = opportunity.get('confidence', 0.7)
        
        # Savings-based priority
        if savings > 500:
            savings_score = 1
        elif savings > 200:
            savings_score = 2
        elif savings > 50:
            savings_score = 3
        elif savings > 10:
            savings_score = 4
        else:
            savings_score = 5
        
        # Risk adjustment
        risk_adjustment = {'low': 0, 'medium': 1, 'high': 2}.get(risk, 1)
        
        # Confidence adjustment
        if confidence < 0.5:
            confidence_adjustment = 1
        else:
            confidence_adjustment = 0
        
        return min(5, savings_score + risk_adjustment + confidence_adjustment)
    
    def _assess_complexity(self, opportunity: Dict) -> str:
        """Assess implementation complexity."""
        opp_type = opportunity.get('type', '').lower()
        
        if any(x in opp_type for x in ['right_sizing', 'resource']):
            return 'low'
        elif any(x in opp_type for x in ['hpa', 'quota', 'limit']):
            return 'medium'
        elif any(x in opp_type for x in ['node', 'network', 'storage']):
            return 'high'
        return 'medium'
    
    def _estimate_effort(self, opportunity: Dict) -> float:
        """Estimate implementation effort in hours."""
        complexity = self._assess_complexity(opportunity)
        base_hours = {'low': 1, 'medium': 2, 'high': 4}.get(complexity, 2)
        
        # Adjust for number of affected resources
        affected = opportunity.get('affected_resources', 1)
        if affected > 5:
            base_hours *= 1.5
        if affected > 10:
            base_hours *= 2
        
        return base_hours
    
    def _analyze_workloads(self, workloads: List[Dict], opportunities: List[Dict]) -> Dict:
        """Perform deep analysis of workloads for optimization."""
        opportunity_workloads = {opp.get('workload', '') for opp in opportunities}
        
        analyzed = {
            'total_count': len(workloads),
            'needing_optimization': 0,
            'with_hpa': 0,
            'without_hpa': 0,
            'over_provisioned': [],
            'under_provisioned': [],
            'right_sized': [],
            'by_namespace': {},
            'by_type': {},
            'total_monthly_cost': 0,
            'potential_savings': 0
        }
        
        for workload in workloads:
            name = workload.get('name', '')
            namespace = workload.get('namespace', 'default')
            workload_type = workload.get('type', 'Deployment')
            has_hpa = workload.get('has_hpa', False)
            
            # HPA tracking
            if has_hpa:
                analyzed['with_hpa'] += 1
            else:
                analyzed['without_hpa'] += 1
            
            # Usage metrics
            actual_usage = workload.get('actual_usage', {})
            cpu_usage = actual_usage.get('cpu', {}).get('avg_percentage', 50)
            memory_usage = actual_usage.get('memory', {}).get('avg_percentage', 50)
            
            # Cost tracking
            cost_estimate = workload.get('cost_estimate', {})
            monthly_cost = cost_estimate.get('monthly_cost', 0)
            analyzed['total_monthly_cost'] += monthly_cost
            
            # Resource details
            resources = workload.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            
            workload_detail = {
                'name': name,
                'namespace': namespace,
                'type': workload_type,
                'replicas': workload.get('replicas', 1),
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'monthly_cost': monthly_cost,
                'has_hpa': has_hpa,
                'cpu_request': requests.get('cpu', 'not set'),
                'memory_request': requests.get('memory', 'not set'),
                'cpu_limit': limits.get('cpu', 'not set'),
                'memory_limit': limits.get('memory', 'not set'),
                'needs_optimization': name in opportunity_workloads
            }
            
            # Categorize by efficiency
            if cpu_usage < 30 or memory_usage < 30:
                analyzed['over_provisioned'].append(workload_detail)
                analyzed['needing_optimization'] += 1
            elif cpu_usage > 85 or memory_usage > 85:
                analyzed['under_provisioned'].append(workload_detail)
                analyzed['needing_optimization'] += 1
            else:
                analyzed['right_sized'].append(workload_detail)
            
            # Track by namespace
            if namespace not in analyzed['by_namespace']:
                analyzed['by_namespace'][namespace] = {
                    'count': 0, 'cost': 0, 'workloads': []
                }
            analyzed['by_namespace'][namespace]['count'] += 1
            analyzed['by_namespace'][namespace]['cost'] += monthly_cost
            analyzed['by_namespace'][namespace]['workloads'].append(name)
            
            # Track by type
            if workload_type not in analyzed['by_type']:
                analyzed['by_type'][workload_type] = {'count': 0, 'cost': 0}
            analyzed['by_type'][workload_type]['count'] += 1
            analyzed['by_type'][workload_type]['cost'] += monthly_cost
        
        return analyzed
    
    def _analyze_namespaces(self, namespaces: List[Dict]) -> Dict:
        """Comprehensive namespace governance analysis."""
        analyzed = {
            'total_count': len(namespaces),
            'total_cost': 0,
            'with_quotas': 0,
            'without_quotas': 0,
            'with_limitranges': 0,
            'without_limitranges': 0,
            'governance_issues': [],
            'by_cost_center': {},
            'by_team': {},
            'by_environment': {},
            'inefficiency_summary': {},
            'high_cost_namespaces': []
        }
        
        for ns in namespaces:
            name = ns.get('name', '')
            cost = ns.get('monthly_cost_estimate', {}).get('total', 0)
            analyzed['total_cost'] += cost
            
            inefficiencies = ns.get('inefficiencies', [])
            
            # Quota tracking
            if 'missing_resource_limits' in inefficiencies or 'no_resource_quota' in inefficiencies:
                analyzed['without_quotas'] += 1
            else:
                analyzed['with_quotas'] += 1
            
            if 'missing_limit_range' in inefficiencies or 'no_limit_range' in inefficiencies:
                analyzed['without_limitranges'] += 1
            else:
                analyzed['with_limitranges'] += 1
            
            # Governance issues tracking
            if inefficiencies:
                analyzed['governance_issues'].append({
                    'namespace': name,
                    'issues': inefficiencies,
                    'issue_count': len(inefficiencies),
                    'cost': cost,
                    'score': ns.get('optimization_score', 0),
                    'owner': ns.get('team_owner', 'unknown'),
                    'environment': ns.get('environment', 'unknown')
                })
                
                for issue in inefficiencies:
                    if issue not in analyzed['inefficiency_summary']:
                        analyzed['inefficiency_summary'][issue] = {
                            'count': 0, 'cost': 0, 'namespaces': []
                        }
                    analyzed['inefficiency_summary'][issue]['count'] += 1
                    analyzed['inefficiency_summary'][issue]['cost'] += cost
                    analyzed['inefficiency_summary'][issue]['namespaces'].append(name)
            
            # Cost center tracking
            cost_center = ns.get('cost_center', 'unknown')
            if cost_center not in analyzed['by_cost_center']:
                analyzed['by_cost_center'][cost_center] = {
                    'count': 0, 'cost': 0, 'namespaces': []
                }
            analyzed['by_cost_center'][cost_center]['count'] += 1
            analyzed['by_cost_center'][cost_center]['cost'] += cost
            analyzed['by_cost_center'][cost_center]['namespaces'].append(name)
            
            # Team tracking
            team = ns.get('team_owner', 'unknown')
            if team not in analyzed['by_team']:
                analyzed['by_team'][team] = {'count': 0, 'cost': 0, 'namespaces': []}
            analyzed['by_team'][team]['count'] += 1
            analyzed['by_team'][team]['cost'] += cost
            analyzed['by_team'][team]['namespaces'].append(name)
            
            # Environment tracking
            env = ns.get('environment', 'unknown')
            if env not in analyzed['by_environment']:
                analyzed['by_environment'][env] = {'count': 0, 'cost': 0, 'namespaces': []}
            analyzed['by_environment'][env]['count'] += 1
            analyzed['by_environment'][env]['cost'] += cost
            analyzed['by_environment'][env]['namespaces'].append(name)
            
            # High-cost namespace tracking
            if cost > 100:
                analyzed['high_cost_namespaces'].append({
                    'name': name,
                    'cost': cost,
                    'issues': inefficiencies
                })
        
        # Sort governance issues by cost impact
        analyzed['governance_issues'].sort(key=lambda x: x['cost'], reverse=True)
        analyzed['high_cost_namespaces'].sort(key=lambda x: x['cost'], reverse=True)
        
        return analyzed
    
    def _analyze_storage(self, volumes: List[Dict]) -> Dict:
        """Storage waste and optimization analysis."""
        analyzed = {
            'total_volumes': len(volumes),
            'total_requested_gb': 0,
            'total_used_gb': 0,
            'total_waste_gb': 0,
            'waste_cost_monthly': 0,
            'average_utilization': 0,
            'under_utilized': [],
            'well_utilized': [],
            'orphaned': [],
            'by_storage_class': {},
            'by_namespace': {},
            'optimization_potential': 0
        }
        
        utilization_sum = 0
        utilized_count = 0
        
        for vol in volumes:
            size_info = vol.get('size', {}) if isinstance(vol.get('size'), dict) else {}
            requested = size_info.get('requested_gb', 0)
            used = size_info.get('used_gb', 0)
            
            namespace = vol.get('namespace', 'default')
            storage_class = vol.get('storage_class', 'default')
            
            analyzed['total_requested_gb'] += requested
            analyzed['total_used_gb'] += used
            
            if requested > 0:
                waste = max(0, requested - used)
                utilization = (used / requested * 100)
                
                utilization_sum += utilization
                utilized_count += 1
                
                analyzed['total_waste_gb'] += waste
                
                vol_detail = {
                    'name': vol.get('name', 'unknown'),
                    'namespace': namespace,
                    'requested_gb': requested,
                    'used_gb': used,
                    'utilization': utilization,
                    'waste_gb': waste,
                    'waste_cost': waste * 0.10,  # ~$0.10/GB/month for Azure managed disks
                    'storage_class': storage_class,
                    'access_mode': vol.get('access_mode', 'ReadWriteOnce'),
                    'status': vol.get('status', 'Bound')
                }
                
                if utilization < 50:
                    analyzed['under_utilized'].append(vol_detail)
                else:
                    analyzed['well_utilized'].append(vol_detail)
                
                # Track by storage class
                if storage_class not in analyzed['by_storage_class']:
                    analyzed['by_storage_class'][storage_class] = {
                        'count': 0, 'total_gb': 0, 'used_gb': 0, 'waste_gb': 0
                    }
                analyzed['by_storage_class'][storage_class]['count'] += 1
                analyzed['by_storage_class'][storage_class]['total_gb'] += requested
                analyzed['by_storage_class'][storage_class]['used_gb'] += used
                analyzed['by_storage_class'][storage_class]['waste_gb'] += waste
                
                # Track by namespace
                if namespace not in analyzed['by_namespace']:
                    analyzed['by_namespace'][namespace] = {
                        'count': 0, 'total_gb': 0, 'used_gb': 0
                    }
                analyzed['by_namespace'][namespace]['count'] += 1
                analyzed['by_namespace'][namespace]['total_gb'] += requested
                analyzed['by_namespace'][namespace]['used_gb'] += used
            
            # Check for orphaned volumes
            if vol.get('status') == 'Available' or vol.get('bound_pod') is None:
                analyzed['orphaned'].append({
                    'name': vol.get('name', 'unknown'),
                    'namespace': namespace,
                    'size_gb': requested,
                    'age_days': vol.get('age_days', 0),
                    'storage_class': storage_class
                })
        
        # Calculate waste cost and averages
        analyzed['waste_cost_monthly'] = analyzed['total_waste_gb'] * 0.10
        analyzed['average_utilization'] = utilization_sum / utilized_count if utilized_count > 0 else 0
        
        # Sort by waste
        analyzed['under_utilized'].sort(key=lambda x: x['waste_gb'], reverse=True)
        
        return analyzed
    
    def _analyze_network(self, network_data: Dict) -> Dict:
        """Network resource and cost analysis."""
        analyzed = {
            'total_cost': network_data.get('total_network_cost', 0),
            'egress_cost': network_data.get('egress_cost', 0),
            'ingress_cost': network_data.get('ingress_cost', 0),
            'public_ips': network_data.get('public_ips', []),
            'load_balancers': network_data.get('load_balancers', []),
            'public_ip_count': len(network_data.get('public_ips', [])),
            'load_balancer_count': len(network_data.get('load_balancers', [])),
            'public_ip_cost': 0,
            'load_balancer_cost': 0,
            'optimization_potential': 0,
            'recommendations': []
        }
        
        # Calculate costs
        analyzed['public_ip_cost'] = analyzed['public_ip_count'] * 3.65  # $3.65/month per static IP
        analyzed['load_balancer_cost'] = analyzed['load_balancer_count'] * 18.25  # $18.25/month base
        
        # Generate recommendations
        if analyzed['public_ip_count'] > 3:
            potential = (analyzed['public_ip_count'] - 3) * 3.65
            analyzed['recommendations'].append({
                'type': 'consolidate_public_ips',
                'description': f"Consolidate {analyzed['public_ip_count']} public IPs to 3 or fewer",
                'savings': potential,
                'priority': 'medium',
                'effort': 'medium'
            })
            analyzed['optimization_potential'] += potential
        
        if analyzed['load_balancer_count'] > 1:
            potential = (analyzed['load_balancer_count'] - 1) * 18.25
            analyzed['recommendations'].append({
                'type': 'consolidate_load_balancers',
                'description': f"Use shared ingress controller instead of {analyzed['load_balancer_count']} load balancers",
                'savings': potential,
                'priority': 'high',
                'effort': 'high'
            })
            analyzed['optimization_potential'] += potential
        
        if analyzed['egress_cost'] > 100:
            potential = analyzed['egress_cost'] * 0.3
            analyzed['recommendations'].append({
                'type': 'reduce_egress',
                'description': "Implement CDN, optimize inter-region traffic, review external API calls",
                'savings': potential,
                'priority': 'medium',
                'effort': 'medium'
            })
            analyzed['optimization_potential'] += potential
        
        return analyzed
    
    def _analyze_inefficiencies(self, inefficient_data: Dict) -> Dict:
        """Analyze and categorize all inefficiencies with root cause analysis."""
        analyzed = {
            'over_provisioned': {
                'count': 0,
                'total_waste_cost': 0,
                'workloads': [],
                'by_namespace': {}
            },
            'under_utilized': {
                'count': 0,
                'workloads': []
            },
            'missing_hpa': {
                'count': 0,
                'potential_savings': 0,
                'workloads': []
            },
            'orphaned_resources': {
                'count': 0,
                'potential_savings': 0,
                'resources': []
            },
            'summary': {
                'total_issues': 0,
                'total_waste_cost': 0,
                'priority_actions': []
            }
        }
        
        # Process over-provisioned workloads
        for item in inefficient_data.get('over_provisioned', []):
            workload = item.get('workload', {})
            details = item.get('inefficiency_details', {})
            waste_cost = details.get('monthly_waste_cost', 0)
            namespace = workload.get('namespace', 'default')
            
            analyzed['over_provisioned']['count'] += 1
            analyzed['over_provisioned']['total_waste_cost'] += waste_cost
            
            workload_info = {
                'name': workload.get('name', 'unknown'),
                'namespace': namespace,
                'type': workload.get('type', 'Deployment'),
                'cpu_waste': details.get('cpu_waste_percentage', 0),
                'memory_waste': details.get('memory_waste_percentage', 0),
                'monthly_waste': waste_cost,
                'current_cpu': details.get('current_cpu', 'unknown'),
                'current_memory': details.get('current_memory', 'unknown'),
                'recommended_cpu': details.get('recommended_cpu', '100m'),
                'recommended_memory': details.get('recommended_memory', '256Mi'),
                'confidence': item.get('confidence', 0.8),
                'priority': item.get('priority', 'medium')
            }
            analyzed['over_provisioned']['workloads'].append(workload_info)
            
            # Track by namespace
            if namespace not in analyzed['over_provisioned']['by_namespace']:
                analyzed['over_provisioned']['by_namespace'][namespace] = {
                    'count': 0, 'waste': 0
                }
            analyzed['over_provisioned']['by_namespace'][namespace]['count'] += 1
            analyzed['over_provisioned']['by_namespace'][namespace]['waste'] += waste_cost
        
        # Sort by waste cost
        analyzed['over_provisioned']['workloads'].sort(
            key=lambda x: x['monthly_waste'], reverse=True
        )
        
        # Process under-utilized workloads
        for item in inefficient_data.get('under_utilized', []):
            workload = item.get('workload', {})
            analyzed['under_utilized']['count'] += 1
            analyzed['under_utilized']['workloads'].append({
                'name': workload.get('name', 'unknown'),
                'namespace': workload.get('namespace', 'default'),
                'type': workload.get('type', 'Deployment'),
                'replicas': workload.get('replicas', 1),
                'recommendation': 'Consider scaling down or consolidating'
            })
        
        # Process missing HPA candidates
        for workload in inefficient_data.get('missing_hpa_candidates', []):
            analyzed['missing_hpa']['count'] += 1
            
            # Estimate HPA savings (typically 20-30% for variable workloads)
            replicas = workload.get('replicas', 2)
            cost_per_replica = 50  # Approximate
            potential_savings = replicas * cost_per_replica * 0.25
            analyzed['missing_hpa']['potential_savings'] += potential_savings
            
            analyzed['missing_hpa']['workloads'].append({
                'name': workload.get('name', 'unknown'),
                'namespace': workload.get('namespace', 'default'),
                'type': workload.get('type', 'Deployment'),
                'current_replicas': replicas,
                'estimated_savings': potential_savings
            })
        
        # Process orphaned resources
        for resource in inefficient_data.get('orphaned_resources', []):
            analyzed['orphaned_resources']['count'] += 1
            
            # Estimate cost based on resource type
            resource_type = resource.get('type', 'unknown')
            if 'pvc' in resource_type.lower() or 'volume' in resource_type.lower():
                estimated_cost = 10  # ~$10/month for average PVC
            elif 'service' in resource_type.lower():
                estimated_cost = 5
            else:
                estimated_cost = 2
            
            analyzed['orphaned_resources']['potential_savings'] += estimated_cost
            
            analyzed['orphaned_resources']['resources'].append({
                'name': resource.get('name', 'unknown'),
                'type': resource_type,
                'namespace': resource.get('namespace', 'default'),
                'age_days': resource.get('age_days', 0),
                'estimated_cost': estimated_cost
            })
        
        # Create summary
        analyzed['summary']['total_issues'] = (
            analyzed['over_provisioned']['count'] +
            analyzed['under_utilized']['count'] +
            analyzed['missing_hpa']['count'] +
            analyzed['orphaned_resources']['count']
        )
        analyzed['summary']['total_waste_cost'] = (
            analyzed['over_provisioned']['total_waste_cost'] +
            analyzed['missing_hpa']['potential_savings'] +
            analyzed['orphaned_resources']['potential_savings']
        )
        
        # Generate priority actions
        if analyzed['over_provisioned']['workloads']:
            top_waste = analyzed['over_provisioned']['workloads'][:3]
            for w in top_waste:
                analyzed['summary']['priority_actions'].append({
                    'action': f"Right-size {w['name']}",
                    'savings': w['monthly_waste'],
                    'priority': 'high'
                })
        
        return analyzed
    
    def _analyze_hpas(self, existing_hpas: List[Dict], workloads: List[Dict]) -> Dict:
        """Analyze HPA coverage and configuration quality."""
        analyzed = {
            'existing_count': len(existing_hpas),
            'workloads_with_hpa': set(),
            'workloads_without_hpa': [],
            'hpa_details': [],
            'configuration_issues': [],
            'recommendations': [],
            'coverage_percentage': 0,
            'potential_savings': 0
        }
        
        # Map existing HPAs
        for hpa in existing_hpas:
            target = hpa.get('target', {})
            workload_name = target.get('name', '')
            analyzed['workloads_with_hpa'].add(workload_name)
            
            min_replicas = hpa.get('min_replicas', 1)
            max_replicas = hpa.get('max_replicas', 10)
            metrics = hpa.get('metrics', [])
            
            hpa_detail = {
                'name': hpa.get('name', 'unknown'),
                'namespace': hpa.get('namespace', 'default'),
                'target_workload': workload_name,
                'min_replicas': min_replicas,
                'max_replicas': max_replicas,
                'current_replicas': hpa.get('current_replicas', min_replicas),
                'metrics_count': len(metrics),
                'metrics': metrics
            }
            analyzed['hpa_details'].append(hpa_detail)
            
            # Check for configuration issues
            if max_replicas <= min_replicas:
                analyzed['configuration_issues'].append({
                    'hpa': hpa.get('name'),
                    'issue': 'max_replicas <= min_replicas',
                    'recommendation': f'Set max_replicas > {min_replicas}'
                })
            
            if not metrics:
                analyzed['configuration_issues'].append({
                    'hpa': hpa.get('name'),
                    'issue': 'No metrics configured',
                    'recommendation': 'Add CPU or memory metrics'
                })
        
        # Find workloads without HPA
        deployment_count = 0
        for workload in workloads:
            name = workload.get('name', '')
            workload_type = workload.get('type', 'Deployment')
            
            if workload_type == 'Deployment':
                deployment_count += 1
                
                if name not in analyzed['workloads_with_hpa']:
                    replicas = workload.get('replicas', 1)
                    
                    # Check if good HPA candidate
                    if replicas >= 1:
                        # Estimate savings from HPA
                        cost_per_replica = 50  # Approximate monthly cost
                        potential_savings = replicas * cost_per_replica * 0.25
                        analyzed['potential_savings'] += potential_savings
                        
                        analyzed['workloads_without_hpa'].append({
                            'name': name,
                            'namespace': workload.get('namespace', 'default'),
                            'replicas': replicas,
                            'monthly_cost': workload.get('cost_estimate', {}).get('monthly_cost', 0),
                            'estimated_savings': potential_savings,
                            'priority': 'high' if replicas > 2 else 'medium'
                        })
        
        # Calculate coverage
        if deployment_count > 0:
            analyzed['coverage_percentage'] = (
                len(analyzed['workloads_with_hpa']) / deployment_count * 100
            )
        
        # Sort candidates by potential savings
        analyzed['workloads_without_hpa'].sort(
            key=lambda x: x['estimated_savings'], reverse=True
        )
        
        # Generate recommendations
        if analyzed['workloads_without_hpa']:
            analyzed['recommendations'].append({
                'type': 'add_hpa',
                'count': len(analyzed['workloads_without_hpa']),
                'description': f"Add HPA to {len(analyzed['workloads_without_hpa'])} workloads",
                'potential_savings': analyzed['potential_savings']
            })
        
        if analyzed['configuration_issues']:
            analyzed['recommendations'].append({
                'type': 'fix_hpa_config',
                'count': len(analyzed['configuration_issues']),
                'description': f"Fix configuration issues in {len(analyzed['configuration_issues'])} HPAs"
            })
        
        return analyzed
    
    # ==========================================================================
    # ANALYSIS SECTION GENERATION METHODS
    # ==========================================================================
    
    def _generate_analysis_sections(self, context: Dict) -> Dict[str, str]:
        """Generate detailed analysis sections for the Claude prompt."""
        sections = {}
        
        sections['executive_summary'] = self._format_executive_summary(context)
        sections['infrastructure'] = self._format_infrastructure_details(context)
        sections['cost_analysis'] = self._format_cost_analysis(context)
        sections['workload_analysis'] = self._format_workload_analysis(context)
        sections['namespace_governance'] = self._format_namespace_governance(context)
        sections['storage_analysis'] = self._format_storage_analysis(context)
        sections['network_analysis'] = self._format_network_analysis(context)
        sections['inefficiency_analysis'] = self._format_inefficiency_analysis(context)
        sections['hpa_analysis'] = self._format_hpa_analysis(context)
        sections['validated_commands'] = self._generate_all_validated_commands(context)
        
        return sections
    
    def _format_executive_summary(self, context: Dict) -> str:
        """Format executive summary with health assessment."""
        efficiency = context.get('efficiency_metrics', {})
        cpu_eff = efficiency.get('current_cpu_efficiency', 0) * 100
        mem_eff = efficiency.get('current_memory_efficiency', 0) * 100
        
        if cpu_eff < 50:
            health_status = "🔴 CRITICAL"
            health_desc = "Severe resource over-provisioning - immediate action required"
        elif cpu_eff < 70:
            health_status = "🟡 WARNING"
            health_desc = "Moderate inefficiency - optimization recommended"
        else:
            health_status = "🟢 GOOD"
            health_desc = "Cluster efficiency within acceptable range"
        
        return f"""
## EXECUTIVE SUMMARY

**Cluster Health Status:** {health_status}
**Assessment:** {health_desc}

### Key Performance Metrics
| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| CPU Efficiency | {cpu_eff:.1f}% | 80.0% | {max(0, 80 - cpu_eff):.1f}% |
| Memory Efficiency | {mem_eff:.1f}% | 80.0% | {max(0, 80 - mem_eff):.1f}% |
| Monthly Spend | ${context['current_monthly_cost']:,.2f} | ${context['current_monthly_cost'] - context['total_potential_savings']:,.2f} | -${context['total_potential_savings']:,.2f} |

### Financial Impact Summary
- **Monthly Savings Potential:** ${context['total_potential_savings']:,.2f}
- **Annual Savings Potential:** ${context['annual_savings']:,.2f}
- **Optimization Opportunities Identified:** {context['total_optimization_count']}
"""
    
    def _format_infrastructure_details(self, context: Dict) -> str:
        """Format infrastructure details section."""
        cluster_info = context['cluster_info']
        node_pools = context['node_pools']
        
        lines = ["## CLUSTER INFRASTRUCTURE\n"]
        lines.append(f"- **Cluster Name:** {cluster_info.get('cluster_name', 'unknown')}")
        lines.append(f"- **Resource Group:** {cluster_info.get('resource_group', 'unknown')}")
        lines.append(f"- **Kubernetes Version:** {cluster_info.get('kubernetes_version', 'unknown')}")
        lines.append(f"- **Node Pools:** {context['node_pool_count']}")
        lines.append(f"- **Total Nodes:** {context['total_nodes']}")
        
        if node_pools:
            lines.append("\n### Node Pool Details")
            for pool in node_pools:
                lines.append(f"- **{pool.get('name')}:** {pool.get('vm_sku')}, {pool.get('node_count')} nodes, ${pool.get('monthly_cost', 0):,.2f}/month")
        
        return '\n'.join(lines)
    
    def _format_cost_analysis(self, context: Dict) -> str:
        """Format comprehensive cost breakdown."""
        savings = context['savings_breakdown']
        lines = [f"## COST ANALYSIS\n**Total Monthly:** ${context['current_monthly_cost']:,.2f}\n"]
        
        for category, amount in sorted(savings.items(), key=lambda x: x[1], reverse=True):
            if amount > 0:
                lines.append(f"- {category.replace('_', ' ').title()}: ${amount:,.2f}/month")
        
        lines.append(f"\n**Total Potential Savings:** ${context['total_potential_savings']:,.2f}/month")
        return '\n'.join(lines)
    
    def _format_workload_analysis(self, context: Dict) -> str:
        """Format detailed workload analysis."""
        analysis = context['workload_analysis']
        lines = [f"## WORKLOAD ANALYSIS\n- Total: {analysis['total_count']}\n- Needing optimization: {analysis['needing_optimization']}\n"]
        
        if analysis['over_provisioned']:
            lines.append(f"\n### Over-Provisioned ({len(analysis['over_provisioned'])})")
            for w in analysis['over_provisioned'][:8]:
                lines.append(f"- **{w['name']}** ({w['namespace']}): CPU {w['cpu_usage']:.1f}%, Mem {w['memory_usage']:.1f}%, ${w['monthly_cost']:.2f}/mo")
        
        return '\n'.join(lines)
    
    def _format_namespace_governance(self, context: Dict) -> str:
        """Format namespace governance analysis."""
        analysis = context['namespace_analysis']
        lines = [f"## NAMESPACE GOVERNANCE\n- Total: {analysis['total_count']}\n- Without quotas: {analysis['without_quotas']}\n"]
        
        if analysis['governance_issues']:
            lines.append(f"\n### Issues ({len(analysis['governance_issues'])} namespaces)")
            for issue in analysis['governance_issues'][:8]:
                lines.append(f"- **{issue['namespace']}:** {', '.join(issue['issues'][:3])}")
        
        return '\n'.join(lines)
    
    def _format_storage_analysis(self, context: Dict) -> str:
        """Format storage waste analysis."""
        analysis = context['storage_analysis']
        return f"""## STORAGE ANALYSIS
- Total Volumes: {analysis['total_volumes']}
- Waste: {analysis['total_waste_gb']:.1f} GB (${analysis['waste_cost_monthly']:.2f}/month)
- Under-utilized: {len(analysis['under_utilized'])}
- Orphaned: {len(analysis['orphaned'])}
"""
    
    def _format_network_analysis(self, context: Dict) -> str:
        """Format network cost analysis."""
        analysis = context['network_analysis']
        return f"""## NETWORK ANALYSIS
- Total: ${analysis['total_cost']:,.2f}/month
- Public IPs ({analysis['public_ip_count']}): ${analysis['public_ip_cost']:,.2f}
- Load Balancers ({analysis['load_balancer_count']}): ${analysis['load_balancer_cost']:,.2f}
- Optimization Potential: ${analysis['optimization_potential']:,.2f}/month
"""
    
    def _format_inefficiency_analysis(self, context: Dict) -> str:
        """Format inefficiency root cause analysis."""
        analysis = context['inefficiency_analysis']
        lines = [f"## INEFFICIENCY ANALYSIS\n- Total Issues: {analysis['summary']['total_issues']}\n- Total Waste: ${analysis['summary']['total_waste_cost']:,.2f}/month\n"]
        
        if analysis['over_provisioned']['workloads']:
            lines.append(f"\n### Over-Provisioned ({analysis['over_provisioned']['count']})")
            for w in analysis['over_provisioned']['workloads'][:8]:
                lines.append(f"- **{w['name']}** ({w['namespace']}): ${w['monthly_waste']:.2f}/mo waste, recommend CPU={w['recommended_cpu']}, Mem={w['recommended_memory']}")
        
        return '\n'.join(lines)
    
    def _format_hpa_analysis(self, context: Dict) -> str:
        """Format HPA coverage analysis."""
        analysis = context['hpa_analysis']
        lines = [f"## HPA ANALYSIS\n- Existing: {analysis['existing_count']}\n- Coverage: {analysis['coverage_percentage']:.1f}%\n- Candidates: {len(analysis['workloads_without_hpa'])}\n"]
        
        if analysis['workloads_without_hpa']:
            lines.append("\n### HPA Candidates")
            for w in analysis['workloads_without_hpa'][:10]:
                lines.append(f"- **{w['name']}** ({w['namespace']}): {w['replicas']} replicas")
        
        return '\n'.join(lines)
    
    def _generate_all_validated_commands(self, context: Dict) -> str:
        """Generate all validated implementation commands."""
        cluster_info = context['cluster_info']
        rg = cluster_info.get('resource_group', 'myResourceGroup')
        cluster = cluster_info.get('cluster_name', 'myCluster')
        
        sections = [self._gen_backup_commands(rg, cluster)]
        sections.append(self._gen_rightsizing_commands(context))
        sections.append(self._gen_hpa_commands(context))
        sections.append(self._gen_governance_commands(context))
        
        return '\n'.join(sections)
    
    def _gen_backup_commands(self, rg: str, cluster: str) -> str:
        """Generate backup commands."""
        return f"""
## VALIDATED COMMANDS

### BACKUP (Execute First)
```bash
BACKUP_DIR="./backup-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
kubectl get deployments --all-namespaces -o yaml > $BACKUP_DIR/deployments.yaml
kubectl get hpa --all-namespaces -o yaml > $BACKUP_DIR/hpas.yaml
kubectl get resourcequotas --all-namespaces -o yaml > $BACKUP_DIR/quotas.yaml
```
"""
    
    def _gen_rightsizing_commands(self, context: Dict) -> str:
        """Generate right-sizing commands."""
        workloads = context['inefficiency_analysis']['over_provisioned']['workloads'][:5]
        lines = ["\n### RIGHT-SIZING COMMANDS\n"]
        
        for w in workloads:
            lines.append(f"""
**{w['name']}** ({w['namespace']}) - ${w['monthly_waste']:.2f}/month savings
```bash
kubectl patch deployment {w['name']} -n {w['namespace']} --type=strategic -p='
spec:
  template:
    spec:
      containers:
      - name: {w['name']}
        resources:
          requests:
            cpu: "{w['recommended_cpu']}"
            memory: "{w['recommended_memory']}"
'
# Rollback: kubectl rollout undo deployment/{w['name']} -n {w['namespace']}
```
""")
        return '\n'.join(lines)
    
    def _gen_hpa_commands(self, context: Dict) -> str:
        """Generate HPA commands."""
        candidates = context['hpa_analysis']['workloads_without_hpa'][:5]
        lines = ["\n### HPA COMMANDS\n"]
        
        for w in candidates:
            min_r = max(1, w['replicas'] - 1)
            max_r = w['replicas'] * 3
            lines.append(f"""
**{w['name']}** ({w['namespace']})
```bash
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {w['name']}-hpa
  namespace: {w['namespace']}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {w['name']}
  minReplicas: {min_r}
  maxReplicas: {max_r}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```
""")
        return '\n'.join(lines)
    
    def _gen_governance_commands(self, context: Dict) -> str:
        """Generate governance commands."""
        issues = context['namespace_analysis']['governance_issues'][:3]
        lines = ["\n### GOVERNANCE COMMANDS\n"]
        
        for issue in issues:
            ns = issue['namespace']
            lines.append(f"""
**{ns}**
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: {ns}-quota
  namespace: {ns}
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
EOF
```
""")
        return '\n'.join(lines)
    
    # ==========================================================================
    # CLAUDE API INTERACTION
    # ==========================================================================
    
    async def _generate_comprehensive_plan(self, context: Dict, analysis_sections: Dict[str, str], cluster_name: str) -> str:
        """Generate the implementation plan via Claude API."""
        prompt = self._build_prompt(context, analysis_sections, cluster_name)
        return await self._call_claude_api(prompt)
    
    def _build_prompt(self, context: Dict, sections: Dict[str, str], cluster_name: str) -> str:
        """Build the comprehensive prompt for Claude."""
        cluster_info = context['cluster_info']
        
        return f"""Generate a COMPREHENSIVE 8-phase implementation plan for AKS cluster "{cluster_name}". 

DO NOT ask questions. Generate the complete plan immediately based on the provided data.

# CLUSTER ANALYSIS DATA

{sections['executive_summary']}
{sections['infrastructure']}
{sections['cost_analysis']}
{sections['workload_analysis']}
{sections['namespace_governance']}
{sections['storage_analysis']}
{sections['network_analysis']}
{sections['inefficiency_analysis']}
{sections['hpa_analysis']}
{sections['validated_commands']}

---

# GENERATE 8 IMPLEMENTATION PHASES

Use this EXACT structure for each phase:

### Phase N: [Phase Name]
**Duration:** X days
**Risk Level:** Low/Medium/High
**Total Savings:** $X.XX/month

**Actions:**

##### N.1: [Action Title - $X.XX/month]
**Monthly Savings:** $X.XX
**Risk:** Low/Medium/High
**Effort:** X hours

**Implementation Steps:**
```bash
kubectl command 1
kubectl command 2
```

**Rollback:**
```bash
rollback command
```

---

Generate phases for:
1. Emergency Stabilization (Days 1-3) - Backup, baseline
2. Quick Wins (Days 4-10) - Right-sizing
3. HPA Implementation (Days 11-17) - Autoscaling
4. Namespace Governance (Days 18-24) - Quotas, limits
5. Storage Optimization (Days 25-31) - PVC cleanup
6. Network Optimization (Days 32-38) - LB consolidation
7. Node Pool Optimization (Days 39-52) - VM sizing
8. Continuous Improvement (Days 53-66) - Monitoring

## Post-Implementation Monitoring

```bash
kubectl top nodes
kubectl top pods --all-namespaces
kubectl get hpa --all-namespaces
```

## Review Schedule
- Day 7: Phase 1-2 Review
- Day 30: Month 1 Assessment
- Day 90: Quarter Review

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

REQUIREMENTS:
- Minimum 20 actions across all phases
- Use REAL workload names from analysis
- Include actual kubectl/az commands
- Every action needs specific $ savings
- Include backup and rollback procedures

GENERATE ALL 8 PHASES IMMEDIATELY. BE CONCISE BUT COMPLETE. DO NOT STOP OR ASK QUESTIONS."""
    
    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API and return response."""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 8000,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = await asyncio.to_thread(
                requests.post, self.claude_url, headers=headers, json=payload, timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                input_cost = (input_tokens / 1000) * self.input_cost_per_1k
                output_cost = (output_tokens / 1000) * self.output_cost_per_1k
                self.total_cost += input_cost + output_cost
                
                print(f"\n💰 Claude API: {input_tokens:,} in, {output_tokens:,} out, ${self.total_cost:.4f} total")
                
                text = result.get('content', [{}])[0].get('text', '')
                if not text:
                    raise ValueError("Empty response")
                return text
            else:
                raise ValueError(f"API error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Claude API failed: {e}")
            raise
    
    # ==========================================================================
    # OLD JSON PARSING METHODS - COMPLETELY REMOVED
    # ==========================================================================
    # All parsing methods removed - we now use pure markdown display
    
    def get_cost_summary(self) -> Dict:
        """Get API cost summary."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "model": self.model
        }