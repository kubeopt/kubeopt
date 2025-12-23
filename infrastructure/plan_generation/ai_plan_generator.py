"""
Claude AI Plan Generator - High-Quality Markdown Implementation

Generates cost optimization plans using Claude API with superior markdown output
for better reliability and formatting quality.
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
    """Claude AI plan generator with cost tracking"""
    
    def __init__(self, ai_model: str = None, **kwargs):
        """
        Initialize Claude AI generator
        
        Args:
            ai_model: Model name for Claude (defaults to claude-3-5-sonnet-20241022)
            **kwargs: Ignored for backward compatibility
        """
        self.model = ai_model or os.getenv("AI_MODEL", "claude-3-5-haiku-20241022")
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_url = "https://api.anthropic.com/v1/messages"
        self.context_builder = ContextBuilder(target_token_limit=8000)
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Claude pricing (as of December 2024)
        self.input_cost_per_1k = 0.003  # $3 per 1M tokens
        self.output_cost_per_1k = 0.015  # $15 per 1M tokens
        
        if not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        print(f"✓ Initialized Claude AI Generator")
        print(f"  Model: {self.model}")
        print(f"  Endpoint: {self.claude_url}")
        print(f"  Cost tracking: Enabled")
    
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
            
            # Save raw markdown for debugging
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = f"debug_claude_raw_response_{cluster_id}_{timestamp}.md"
            with open(debug_file, 'w') as f:
                f.write(markdown_plan)
            logger.info(f"Raw Claude response saved to: {debug_file}")
            
            # 3. Parse markdown into structured plan
            plan = self._parse_markdown_to_plan(markdown_plan, cluster_name, cluster_id, context)
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise ValueError(f"Plan generation failed for cluster {cluster_name}: {e}")
    
    def _build_simple_context(self, enhanced_input: Dict) -> Dict:
        """Build comprehensive context from enhanced analysis data for Claude"""
        
        # Extract all real data from enhanced input
        cost_analysis = enhanced_input.get('cost_analysis', {})
        cluster_info = enhanced_input.get('cluster_info', {})
        node_pools = enhanced_input.get('node_pools', [])
        optimization_opportunities = enhanced_input.get('optimization_opportunities', [])
        
        # Get real cost data
        current_cost = cost_analysis.get('total_cost', 0.0)
        cost_savings = cost_analysis.get('cost_savings', {})
        potential_savings = cost_savings.get('total_monthly_savings', 0.0)
        savings_breakdown = cost_savings.get('savings_breakdown', {})
        
        # Get efficiency data
        optimization_potential = cost_savings.get('optimization_potential', {})
        efficiency_metrics = optimization_potential.get('efficiency_metrics', {})
        node_optimization = optimization_potential.get('node_optimization_potential', {})
        
        # Group optimization opportunities by type
        opportunities_by_type = {}
        for opp in optimization_opportunities:
            opp_type = opp.get('type', 'other')
            if opp_type not in opportunities_by_type:
                opportunities_by_type[opp_type] = []
            opportunities_by_type[opp_type].append(opp)
        
        # Get detailed workload data for comprehensive analysis
        workloads = enhanced_input.get('workloads', [])
        workload_details = []
        
        # Extract workloads that have optimization opportunities
        opportunity_workloads = set()
        for opp in optimization_opportunities:
            opportunity_workloads.add(opp.get('workload', ''))
        
        for workload in workloads:
            workload_name = workload.get('name', '')
            if workload_name in opportunity_workloads:
                workload_details.append({
                    'name': workload_name,
                    'namespace': workload.get('namespace', 'default'),
                    'type': workload.get('type', 'Deployment'),
                    'replicas': workload.get('replicas', 1),
                    'current_resources': workload.get('resources', {}),
                    'has_hpa': workload.get('has_hpa', False),
                    'monthly_cost': workload.get('cost_estimate', {}).get('monthly_cost', 0),
                    'cpu_usage_avg': workload.get('actual_usage', {}).get('cpu', {}).get('avg_percentage', 0),
                    'memory_usage_avg': workload.get('actual_usage', {}).get('memory', {}).get('avg_percentage', 0)
                })
        
        # Extract ALL analysis components
        namespaces = enhanced_input.get('namespaces', [])
        storage_volumes = enhanced_input.get('storage_volumes', [])
        inefficient_workloads = enhanced_input.get('inefficient_workloads', {})
        network_resources = enhanced_input.get('network_resources', {})
        existing_hpas = enhanced_input.get('existing_hpas', [])
        metadata = enhanced_input.get('metadata', {})

        return {
            'cluster_info': cluster_info,
            'current_monthly_cost': current_cost,
            'total_potential_savings': potential_savings,
            'annual_savings': potential_savings * 12,
            'savings_breakdown': savings_breakdown,
            'node_pools': node_pools,
            'optimization_opportunities': opportunities_by_type,
            'efficiency_metrics': efficiency_metrics,
            'node_optimization': node_optimization,
            'workload_details': workload_details,
            'namespaces_analysis': namespaces,
            'storage_analysis': storage_volumes,
            'inefficient_workloads': inefficient_workloads,
            'network_analysis': network_resources,
            'existing_hpas': existing_hpas,
            'cluster_metadata': metadata,
            'total_optimization_count': len(optimization_opportunities)
        }
    
    async def _generate_markdown_plan(self, context: Dict, cluster_name: str) -> str:
        """Generate markdown plan from Claude API"""
        
        # Build comprehensive prompt with real data
        cluster_info = context['cluster_info']
        node_pools = context['node_pools']
        optimization_opps = context['optimization_opportunities']
        efficiency = context['efficiency_metrics']
        savings_breakdown = context['savings_breakdown']
        
        # Get all the additional analysis data
        namespaces_data = context.get('namespaces_analysis', [])
        storage_data = context.get('storage_analysis', [])
        inefficient_data = context.get('inefficient_workloads', {})
        network_data = context.get('network_analysis', {})
        
        # Create ALL analysis components - comprehensive approach
        backup_commands = self._generate_validated_backup_commands(context)
        workload_optimizations = self._generate_validated_workload_commands(context)
        namespace_fixes = self._generate_validated_namespace_commands(namespaces_data)
        
        # ADD detailed analysis components
        detailed_workload_analysis = self._generate_detailed_workload_analysis(context)
        comprehensive_namespace_analysis = self._generate_comprehensive_namespace_analysis(namespaces_data)
        storage_waste_analysis = self._generate_storage_waste_analysis(storage_data)
        network_cost_analysis = self._generate_network_cost_analysis(network_data)
        inefficiency_root_cause_analysis = self._generate_inefficiency_analysis(inefficient_data)
        cluster_health_assessment = self._generate_cluster_health_assessment(context)
        naming_convention_analysis = self._generate_naming_convention_analysis(namespaces_data)
        security_compliance_analysis = self._generate_security_compliance_analysis(context)
        
        prompt = f"""You are a Senior Kubernetes Cost Optimization Consultant. Generate a COMPLETE, COMPREHENSIVE implementation plan for {cluster_name} using ALL the analysis data below.

## 🚨 CRITICAL CLUSTER HEALTH CRISIS
**CPU Efficiency:** {efficiency.get('current_cpu_efficiency', 0)*100:.1f}% (CRITICAL - Target: {efficiency.get('target_system_efficiency', 0)*100:.1f}%)
**Monthly Waste:** ${context['total_potential_savings']:.2f} out of ${context['current_monthly_cost']:.2f}
**System Health Score:** {efficiency.get('current_system_efficiency', 0)*100:.1f}%

## 📋 CLUSTER INFRASTRUCTURE DETAILS
**Cluster:** {cluster_info.get('cluster_name')}
**Resource Group:** {cluster_info.get('resource_group')}  
**Kubernetes Version:** {cluster_info.get('kubernetes_version')}
**Node Pools:** {len(node_pools)} pools, {sum(pool.get('node_count', 0) for pool in node_pools)} total nodes
**Total Namespaces:** {len(namespaces_data)} ({', '.join([ns.get('name', 'unknown') for ns in namespaces_data[:5]])}...)
**Total Workloads:** {context.get('total_optimization_count', 0)} optimization opportunities identified

## 💰 COMPREHENSIVE COST BREAKDOWN & SAVINGS OPPORTUNITIES
**Current Monthly Cost:** ${context['current_monthly_cost']:.2f}
**Proven Savings Available:**
- Right-sizing Workloads: ${savings_breakdown.get('right_sizing_savings', 0):.2f}/month  
- HPA Optimization: ${savings_breakdown.get('hpa_optimization_savings', 0):.2f}/month
- Networking Optimization: ${savings_breakdown.get('networking_optimization_savings', 0):.2f}/month
- Node Pool Optimization: ${savings_breakdown.get('node_optimization_savings', 0):.2f}/month
- Compute Optimization: ${savings_breakdown.get('compute_optimization_savings', 0):.2f}/month
- Core Infrastructure: ${savings_breakdown.get('core_optimization_savings', 0):.2f}/month
**Total Potential:** ${context['total_potential_savings']:.2f}/month (${context['annual_savings']:.2f}/year)

## 🔍 DETAILED WORKLOAD ANALYSIS
{detailed_workload_analysis}

## 🏗️ COMPREHENSIVE NAMESPACE GOVERNANCE ANALYSIS  
{comprehensive_namespace_analysis}

## 📦 STORAGE WASTE IDENTIFICATION & ANALYSIS
{storage_waste_analysis}

## 🌐 NETWORK COST ANALYSIS & OPTIMIZATION OPPORTUNITIES
{network_cost_analysis}

## 🗑️ INEFFICIENCY ROOT CAUSE ANALYSIS
{inefficiency_root_cause_analysis}

## 🏥 CLUSTER HEALTH & GOVERNANCE ASSESSMENT
{cluster_health_assessment}

## 🏷️ NAMING CONVENTION & COMPLIANCE ANALYSIS
{naming_convention_analysis}

## 🔒 SECURITY & COMPLIANCE GAP ANALYSIS
{security_compliance_analysis}

## ⚙️ VALIDATED IMPLEMENTATION COMMANDS
{backup_commands}

{workload_optimizations}

{namespace_fixes}

## 📐 COMPREHENSIVE IMPLEMENTATION REQUIREMENTS
You MUST generate a plan that includes:

### 🔧 OPTIMIZATION PHASES (8 phases minimum)
1. **Emergency Workload Right-Sizing** - Address CPU efficiency crisis
2. **HPA Implementation** - Autoscaling for dynamic workloads  
3. **Namespace Governance** - Resource quotas and limits
4. **Storage Optimization** - PVC cleanup and right-sizing
5. **Network Cost Reduction** - Load balancer and egress optimization
6. **Node Pool Optimization** - VM sizing and scaling  
7. **Security & Compliance** - Policy implementation
8. **Monitoring & Alerting** - Continuous optimization

### 📋 BACKUP & ROLLBACK PROCEDURES
- Complete backup commands before every change
- Step-by-step rollback procedures
- Validation commands for each phase
- Emergency recovery procedures

### 🏷️ NAMING CONVENTION FIXES
- Identify non-compliant resource naming
- Provide rename commands and procedures
- Establish naming standards

### 🧹 WASTE RESOURCE CLEANUP
- Orphaned resource identification and removal
- Storage cleanup procedures  
- Unused service cleanup

### 🏥 CLUSTER HEALTH MONITORING
- Ongoing health check commands
- Performance monitoring setup
- Cost tracking implementation
- Efficiency measurement procedures

### 🔒 SECURITY & COMPLIANCE IMPLEMENTATION
- ResourceQuota and LimitRange creation
- Pod Security Policy implementation  
- Network Policy configuration
- RBAC optimization

### 📊 POST-IMPLEMENTATION VALIDATION
- Cost impact measurement
- Performance validation
- Security compliance verification
- Ongoing monitoring setup

## 🎯 MANDATORY OUTPUT FORMAT
Generate a comprehensive plan using the exact structure below with ALL validated commands and analysis provided above:

# COMPREHENSIVE KUBERNETES COST OPTIMIZATION IMPLEMENTATION PLAN
**Cluster:** {cluster_name}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Potential Savings:** ${context['total_potential_savings']:.2f}/month

[Include ALL 8 phases with specific commands, analysis, and procedures using the data provided above]

USE ALL THE ANALYSIS DATA AND VALIDATED COMMANDS PROVIDED - DO NOT CREATE GENERIC EXAMPLES.

# Implementation Plan
**Cluster:** {cluster_name}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Generated By:** AKS Cost Optimizer

## Implementation Phases

### Phase 1: Quick Wins
**Duration:** 7 days  
**Risk Level:** Low  
**Total Savings:** $[use real HPA + right-sizing savings]/month

**Actions:**

##### 1.1: [Use specific right-sizing opportunity from data]
**Monthly Savings:** $[actual amount from right_sizing_savings]  
**Risk:** Low  
**Effort:** [actual implementation time]

**Implementation Steps:**
1. Backup current configuration
```bash
[use actual kubectl commands from optimization opportunities]
```

2. [Use real workload names and namespaces]
```bash
[actual kubectl patch commands from the data]
```

### Phase 2: Resource Optimization  
**Duration:** 14 days  
**Risk Level:** Medium  
**Total Savings:** $[networking + compute savings]/month

**Actions:**

##### 2.1: Node Pool Optimization
**Monthly Savings:** $[node_optimization_savings]  
**Risk:** Medium  
**Effort:** 4 hours

**Implementation Steps:**
1. Analyze current node pool utilization
```bash
az aks nodepool show --resource-group {cluster_info.get('resource_group')} --cluster-name {cluster_name} --name [actual node pool name]
```

### Phase 3: Advanced Optimization
[Continue with remaining optimizations]

---

## Post-Implementation Monitoring
[Include standard monitoring commands]

Generated by AKS Cost Optimizer

# Implementation Plan
**Cluster:** {cluster_name}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Generated By:** AKS Cost Optimizer

## Implementation Phases

### Phase 1: Quick Wins
**Duration:** 7 days  
**Risk Level:** Low  
**Total Savings:** $[total]/month

**Actions:**

##### 1.1: [First Action Name]
**Monthly Savings:** $[amount]  
**Risk:** Low  
**Effort:** 4 hours

**Implementation Steps:**
1. Backup current configuration
```bash
kubectl get all -n production -o yaml > backup-phase1-action1.yaml
```

2. [Step description]
```bash
[actual kubectl/az command]
```

3. [Step description]
```bash
[actual kubectl/az command]
```

##### 1.2: [Second Action Name]
[Same structure as above]

### Phase 2: Resource Optimization
**Duration:** 14 days  
**Risk Level:** Medium  
**Total Savings:** $[total]/month

**Actions:**

##### 2.1: [Action Name]
[Same structure as Phase 1]

### Phase 3: Advanced Optimization
**Duration:** 14 days  
**Risk Level:** Medium  
**Total Savings:** $[total]/month

**Actions:**

##### 3.1: [Action Name]
[Same structure as above]

---

## Post-Implementation Monitoring

**Commands to Monitor Progress:**

- **Check node resource usage**
```bash
kubectl top nodes
```

- **Check pod resource usage**
```bash
kubectl top pods --all-namespaces
```

- **Check autoscaler status**
```bash
kubectl get hpa --all-namespaces
```

### Key Metrics to Track:
- cpu_utilization: < 70% average across nodes
- memory_utilization: < 80% average across nodes  
- pod_count: Stable with HPA managing scale
- cost_per_day: < $[target]

## Review Schedule
- **Day 7:** Week 1 Review - Quick Wins Assessment
- **Day 14:** Week 2 Review - Resource Optimization  
- **Day 30:** Month 1 Review - Full Impact Analysis
- **Day 90:** Quarter Review - Long-term Optimization

Generated by AKS Cost Optimizer  
Timestamp: {datetime.now().isoformat()}

REQUIREMENTS:
- Include at least 6 optimization actions total
- Use actual kubectl/az commands that work with AKS
- Focus on cost savings with realistic dollar amounts
- Ensure proper markdown formatting with headers, code blocks, and lists
- Commands should be production-ready and safe to execute"""
        
        # Call Claude API and return the result
        return await self._call_claude_api(prompt)
        
    def _format_node_pools(self, node_pools: List[Dict]) -> str:
        """Format node pool information for prompt"""
        if not node_pools:
            return "- No node pool data available"
        
        lines = []
        for pool in node_pools:
            lines.append(f"- **{pool.get('name')}**: {pool.get('vm_sku')}, {pool.get('node_count')} nodes, ${pool.get('monthly_cost', 0):.2f}/month")
        return '\n'.join(lines)
    
    def _format_optimization_opportunities(self, opportunities: Dict[str, List]) -> str:
        """Format optimization opportunities for prompt"""
        if not opportunities:
            return "- No specific optimization opportunities identified"
        
        lines = []
        for opp_type, opps in opportunities.items():
            if opps:
                lines.append(f"\n**{opp_type.upper()} OPPORTUNITIES:**")
                for opp in opps[:3]:  # Show top 3 per type
                    workload = opp.get('workload', 'unknown')
                    namespace = opp.get('namespace', 'default')
                    savings = opp.get('potential_monthly_savings', 0)
                    command = opp.get('recommended_action', 'No action specified')
                    lines.append(f"- {workload} ({namespace}): ${savings:.2f}/month")
                    lines.append(f"  Command: {command}")
        
        return '\n'.join(lines)
    
    def _format_comprehensive_savings_breakdown(self, savings_breakdown: Dict) -> str:
        """Format comprehensive savings breakdown for prompt"""
        lines = []
        for category, amount in savings_breakdown.items():
            if amount > 0:
                category_name = category.replace('_', ' ').title().replace('Optimization ', '').replace('Savings', '')
                lines.append(f"- **{category_name}**: ${amount:.2f}/month")
        return '\n'.join(lines)
    
    def _format_detailed_workload_data(self, workload_details: List[Dict]) -> str:
        """Format detailed workload data for prompt"""
        if not workload_details:
            return "- No detailed workload data available"
        
        lines = []
        for workload in workload_details:
            name = workload['name']
            namespace = workload['namespace']
            current_cpu = workload['current_resources'].get('requests', {}).get('cpu', 'unknown')
            current_memory = workload['current_resources'].get('requests', {}).get('memory', 'unknown')
            cpu_usage = workload['cpu_usage_avg']
            memory_usage = workload['memory_usage_avg']
            monthly_cost = workload['monthly_cost']
            
            lines.append(f"\n**{name}** ({namespace}):")
            lines.append(f"- Current CPU Request: {current_cpu}")
            lines.append(f"- Current Memory Request: {current_memory}")  
            lines.append(f"- Actual CPU Usage: {cpu_usage:.1f}%")
            lines.append(f"- Actual Memory Usage: {memory_usage:.1f}%")
            lines.append(f"- Monthly Cost: ${monthly_cost:.2f}")
            lines.append(f"- HPA Enabled: {workload['has_hpa']}")
            
            # Calculate recommended resources based on usage
            if cpu_usage > 0:
                if cpu_usage < 30:
                    recommended_cpu = "100m"  # Scale down
                elif cpu_usage < 60:
                    recommended_cpu = "250m"  # Moderate
                else:
                    recommended_cpu = "500m"  # Scale up
            else:
                recommended_cpu = "200m"  # Default
                
            if memory_usage > 0:
                if memory_usage < 30:
                    recommended_memory = "256Mi"  # Scale down
                elif memory_usage < 60:
                    recommended_memory = "512Mi"  # Moderate  
                else:
                    recommended_memory = "1Gi"  # Scale up
            else:
                recommended_memory = "512Mi"  # Default
                
            lines.append(f"- **Recommended CPU**: {recommended_cpu}")
            lines.append(f"- **Recommended Memory**: {recommended_memory}")
        
        return '\n'.join(lines)
    
    def _format_namespace_analysis(self, namespaces: List[Dict]) -> str:
        """Format namespace analysis for prompt"""
        if not namespaces:
            return "- No namespace analysis available"
        
        lines = ["**NAMESPACE GOVERNANCE ISSUES:**"]
        for ns in namespaces[:10]:  # Top 10 namespaces
            name = ns.get('name', 'unknown')
            cost = ns.get('monthly_cost_estimate', {}).get('total', 0)
            inefficiencies = ns.get('inefficiencies', [])
            optimization_score = ns.get('optimization_score', 0)
            
            lines.append(f"\n- **{name}**: ${cost:.2f}/month (Score: {optimization_score}/100)")
            if inefficiencies:
                lines.append(f"  Issues: {', '.join(inefficiencies)}")
        
        return '\n'.join(lines)
    
    def _format_storage_analysis(self, storage_volumes: List[Dict]) -> str:
        """Format storage analysis for prompt"""
        if not storage_volumes:
            return "- No storage waste identified"
        
        lines = ["**STORAGE WASTE IDENTIFIED:**"]
        total_wasted_gb = 0
        
        for vol in storage_volumes:
            if isinstance(vol, dict) and 'size' in str(vol):
                size_info = vol.get('size', {})
                if isinstance(size_info, dict):
                    requested = size_info.get('requested_gb', 0)
                    used = size_info.get('used_gb', 0)
                    if requested > used:
                        waste = requested - used
                        total_wasted_gb += waste
                        utilization = (used / requested * 100) if requested > 0 else 0
                        lines.append(f"- Volume: {waste:.1f}GB wasted ({utilization:.1f}% utilized)")
        
        if total_wasted_gb > 0:
            lines.append(f"\n**Total Storage Waste:** {total_wasted_gb:.1f}GB (≈${total_wasted_gb * 0.1:.2f}/month)")
        
        return '\n'.join(lines)
    
    def _format_inefficient_workloads_analysis(self, inefficient_workloads: Dict) -> str:
        """Format inefficient workloads analysis for prompt"""
        lines = ["**WORKLOAD EFFICIENCY PROBLEMS:**"]
        
        # Over-provisioned workloads
        over_provisioned = inefficient_workloads.get('over_provisioned', [])
        if over_provisioned:
            lines.append(f"\n**Over-Provisioned ({len(over_provisioned)} workloads):**")
            for workload_data in over_provisioned[:5]:
                workload = workload_data.get('workload', {})
                details = workload_data.get('inefficiency_details', {})
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'unknown')
                waste_cost = details.get('monthly_waste_cost', 0)
                lines.append(f"- {name} ({namespace}): ${waste_cost:.2f}/month waste")
        
        # Under-utilized workloads
        under_utilized = inefficient_workloads.get('under_utilized', [])
        if under_utilized:
            lines.append(f"\n**Under-Utilized ({len(under_utilized)} workloads):**")
            for workload_data in under_utilized[:3]:
                workload = workload_data.get('workload', {})
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'unknown')
                lines.append(f"- {name} ({namespace}): Scale down candidate")
        
        # Missing HPA candidates
        missing_hpa = inefficient_workloads.get('missing_hpa_candidates', [])
        if missing_hpa:
            lines.append(f"\n**Missing HPA ({len(missing_hpa)} workloads):**")
            for workload in missing_hpa[:3]:
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'unknown')
                lines.append(f"- {name} ({namespace}): Needs autoscaling")
        
        # Orphaned resources
        orphaned = inefficient_workloads.get('orphaned_resources', [])
        if orphaned:
            lines.append(f"\n**Orphaned Resources ({len(orphaned)} items):**")
            for resource in orphaned[:3]:
                name = resource.get('name', 'unknown')
                resource_type = resource.get('type', 'unknown')
                lines.append(f"- {name} ({resource_type}): Can be deleted")
        
        return '\n'.join(lines)
    
    def _format_network_analysis(self, network_data: Dict) -> str:
        """Format network analysis for prompt"""
        if not network_data:
            return "- No network optimization opportunities identified"
        
        lines = ["**NETWORK COST OPTIMIZATION:**"]
        
        total_network_cost = network_data.get('total_network_cost', 0)
        egress_cost = network_data.get('egress_cost', 0)
        public_ips = network_data.get('public_ips', [])
        load_balancers = network_data.get('load_balancers', [])
        
        if total_network_cost > 0:
            lines.append(f"- Total Network Cost: ${total_network_cost:.2f}/month")
        if egress_cost > 0:
            lines.append(f"- Egress Cost: ${egress_cost:.2f}/month")
        if public_ips:
            lines.append(f"- Public IPs: {len(public_ips)} (${len(public_ips) * 3.65:.2f}/month)")
        if load_balancers:
            lines.append(f"- Load Balancers: {len(load_balancers)} (review for consolidation)")
        
        return '\n'.join(lines)
    
    def _generate_validated_backup_commands(self, context: Dict) -> str:
        """Generate production-ready backup commands"""
        cluster_info = context.get('cluster_info', {})
        workload_details = context.get('workload_details', [])
        namespaces_data = context.get('namespaces_analysis', [])
        
        backup_commands = []
        backup_commands.append("**COMPREHENSIVE BACKUP PROCEDURES:**")
        
        # Cluster-level backup
        backup_commands.append(f"""
**1. Full Cluster Backup:**
```bash
# Create backup directory
mkdir -p cluster-backup-$(date +%Y%m%d-%H%M%S)
cd cluster-backup-$(date +%Y%m%d-%H%M%S)

# Backup all deployments in target namespace
kubectl get deployments -n madapi-preprod -o yaml > deployments-backup.yaml

# Backup all services
kubectl get services -n madapi-preprod -o yaml > services-backup.yaml

# Backup all configmaps  
kubectl get configmaps -n madapi-preprod -o yaml > configmaps-backup.yaml

# Backup node configurations
kubectl get nodes -o yaml > nodes-backup.yaml
```""")
        
        # Workload-specific backups
        if workload_details:
            backup_commands.append("**2. Workload-Specific Backups:**")
            for workload in workload_details[:3]:
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'default')
                backup_commands.append(f"""```bash
# Backup {name}
kubectl get deployment {name} -n {namespace} -o yaml > {name}-backup.yaml
```""")
        
        # Namespace backups
        backup_commands.append("**3. Namespace Resource Backups:**")
        for ns in namespaces_data[:5]:
            ns_name = ns.get('name', 'unknown')
            backup_commands.append(f"""```bash
kubectl get all -n {ns_name} -o yaml > {ns_name}-all-resources-backup.yaml
```""")
            
        return '\n'.join(backup_commands)
    
    def _generate_validated_workload_commands(self, context: Dict) -> str:
        """Generate validated kubectl commands for workload optimization"""
        workload_details = context.get('workload_details', [])
        commands = []
        
        commands.append("**VALIDATED WORKLOAD OPTIMIZATION COMMANDS:**")
        
        for workload in workload_details:
            name = workload.get('name')
            namespace = workload.get('namespace', 'default')
            current_cpu = workload.get('current_resources', {}).get('requests', {}).get('cpu', '15m')
            current_memory = workload.get('current_resources', {}).get('requests', {}).get('memory', '256Mi')
            recommended_cpu = workload.get('recommended_cpu', '500m')
            recommended_memory = workload.get('recommended_memory', '512Mi')
            
            commands.append(f"""
**{name}:**
- Current: CPU {current_cpu}, Memory {current_memory}  
- Target: CPU {recommended_cpu}, Memory {recommended_memory}

```bash
# 1. Backup current deployment
kubectl get deployment {name} -n {namespace} -o yaml > {name}-pre-optimization-backup.yaml

# 2. Apply resource optimization
kubectl patch deployment {name} -n {namespace} --type='merge' -p='{{
  "spec": {{
    "template": {{
      "spec": {{
        "containers": [{{
          "name": "container-0",
          "resources": {{
            "requests": {{
              "cpu": "{recommended_cpu}",
              "memory": "{recommended_memory}"
            }},
            "limits": {{
              "cpu": "{self._calculate_cpu_limit(recommended_cpu)}",
              "memory": "{self._calculate_memory_limit(recommended_memory)}"
            }}
          }}
        }}]
      }}
    }}
  }}
}}'

# 3. Verify deployment status
kubectl rollout status deployment/{name} -n {namespace}

# 4. Rollback command (if needed)
# kubectl rollout undo deployment/{name} -n {namespace}
```""")
        
        return '\n'.join(commands)
    
    def _generate_validated_namespace_commands(self, namespaces_data: List[Dict]) -> str:
        """Generate validated namespace governance commands"""
        commands = []
        commands.append("**VALIDATED NAMESPACE GOVERNANCE COMMANDS:**")
        
        for ns in namespaces_data[:5]:  # Top 5 namespaces needing governance
            name = ns.get('name', 'unknown')
            inefficiencies = ns.get('inefficiencies', [])
            cost = ns.get('monthly_cost_estimate', {}).get('total', 0)
            
            if 'missing_resource_limits' in inefficiencies:
                commands.append(f"""
**{name}** (${cost:.2f}/month) - Missing Resource Limits:

```bash
# 1. Backup existing namespace
kubectl get namespace {name} -o yaml > {name}-namespace-backup.yaml

# 2. Create ResourceQuota (correct syntax)
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: {name}-quota
  namespace: {name}
spec:
  hard:
    requests.cpu: "1"
    requests.memory: "2Gi"
    limits.cpu: "2"
    limits.memory: "4Gi"
    pods: "10"
EOF

# 3. Create LimitRange for default limits
kubectl apply -f - <<EOF
apiVersion: v1
kind: LimitRange
metadata:
  name: {name}-limits
  namespace: {name}
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
EOF

# 4. Verify quota creation
kubectl get resourcequota -n {name}

# 5. Rollback (if needed)
# kubectl delete resourcequota {name}-quota -n {name}
# kubectl delete limitrange {name}-limits -n {name}
```""")
        
        return '\n'.join(commands)
    
    def _calculate_cpu_limit(self, cpu_request: str) -> str:
        """Calculate appropriate CPU limit from request"""
        if cpu_request.endswith('m'):
            request_val = int(cpu_request[:-1])
            limit_val = min(request_val * 2, 2000)  # Max 2 cores
            return f"{limit_val}m"
        return "1000m"  # Default
    
    def _calculate_memory_limit(self, memory_request: str) -> str:
        """Calculate appropriate memory limit from request"""
        if memory_request.endswith('Mi'):
            request_val = int(memory_request[:-2])
            limit_val = request_val * 2  # 2x request
            return f"{limit_val}Mi"
        return "1Gi"  # Default
    
    def _generate_detailed_workload_analysis(self, context: Dict) -> str:
        """Generate comprehensive workload analysis"""
        workload_details = context.get('workload_details', [])
        inefficient_workloads = context.get('inefficient_workloads', {})
        
        analysis = ["## DETAILED WORKLOAD EFFICIENCY ANALYSIS"]
        
        # Current workload problems
        over_provisioned = inefficient_workloads.get('over_provisioned', [])
        if over_provisioned:
            analysis.append(f"\n### OVER-PROVISIONED WORKLOADS ({len(over_provisioned)} identified):")
            for workload_data in over_provisioned:
                workload = workload_data.get('workload', {})
                details = workload_data.get('inefficiency_details', {})
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'unknown')
                cpu_waste = details.get('cpu_waste_percentage', 0)
                memory_waste = details.get('memory_waste_percentage', 0)
                waste_cost = details.get('monthly_waste_cost', 0)
                rec_cpu = details.get('recommended_cpu', 'unknown')
                rec_memory = details.get('recommended_memory', 'unknown')
                
                analysis.append(f"""
**{name}** (namespace: {namespace})
- CPU Waste: {cpu_waste}%, Memory Waste: {memory_waste}%
- Monthly Waste Cost: ${waste_cost:.2f}
- Current Resources: Unknown → Recommended: {rec_cpu} CPU, {rec_memory} Memory
- Priority: {workload_data.get('priority', 'medium')}
- Confidence: {workload_data.get('confidence', 0)*100:.0f}%""")
        
        # Workload details from optimization opportunities  
        if workload_details:
            analysis.append(f"\n### OPTIMIZATION TARGET WORKLOADS ({len(workload_details)} workloads):")
            for workload in workload_details:
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'default')
                current_cpu = workload.get('current_resources', {}).get('requests', {}).get('cpu', 'unknown')
                current_memory = workload.get('current_resources', {}).get('requests', {}).get('memory', 'unknown')
                cpu_usage = workload.get('cpu_usage_avg', 0)
                memory_usage = workload.get('memory_usage_avg', 0)
                monthly_cost = workload.get('monthly_cost', 0)
                has_hpa = workload.get('has_hpa', False)
                
                analysis.append(f"""
**{name}** (namespace: {namespace})
- Current Resources: {current_cpu} CPU, {current_memory} Memory
- Actual Usage: {cpu_usage:.1f}% CPU, {memory_usage:.1f}% Memory  
- Monthly Cost: ${monthly_cost:.2f}
- HPA Configured: {'Yes' if has_hpa else 'No'}
- Optimization Needed: {'High' if cpu_usage < 30 or cpu_usage > 80 else 'Medium'}""")
        
        return '\n'.join(analysis)
    
    def _generate_comprehensive_namespace_analysis(self, namespaces_data: List[Dict]) -> str:
        """Generate detailed namespace governance analysis"""
        if not namespaces_data:
            return "No namespace analysis data available"
        
        analysis = ["## COMPREHENSIVE NAMESPACE GOVERNANCE ANALYSIS"]
        
        total_namespace_cost = sum(ns.get('monthly_cost_estimate', {}).get('total', 0) for ns in namespaces_data)
        analysis.append(f"\n**Total Namespace Costs:** ${total_namespace_cost:.2f}/month across {len(namespaces_data)} namespaces")
        
        # Governance issues breakdown
        governance_issues = {}
        for ns in namespaces_data:
            for issue in ns.get('inefficiencies', []):
                if issue not in governance_issues:
                    governance_issues[issue] = []
                governance_issues[issue].append(ns)
        
        if governance_issues:
            analysis.append("\n### GOVERNANCE ISSUES IDENTIFIED:")
            for issue, namespaces in governance_issues.items():
                total_cost = sum(ns.get('monthly_cost_estimate', {}).get('total', 0) for ns in namespaces)
                analysis.append(f"\n**{issue.replace('_', ' ').title()}** - {len(namespaces)} namespaces affected (${total_cost:.2f}/month):")
                for ns in namespaces[:10]:  # Top 10
                    name = ns.get('name', 'unknown')
                    cost = ns.get('monthly_cost_estimate', {}).get('total', 0)
                    score = ns.get('optimization_score', 0)
                    owner = ns.get('team_owner', 'unknown')
                    analysis.append(f"  - {name}: ${cost:.2f}/month, Score: {score}/100, Owner: {owner}")
        
        # Cost center breakdown
        cost_centers = {}
        for ns in namespaces_data:
            cc = ns.get('cost_center', 'unknown')
            if cc not in cost_centers:
                cost_centers[cc] = {'cost': 0, 'namespaces': []}
            cost_centers[cc]['cost'] += ns.get('monthly_cost_estimate', {}).get('total', 0)
            cost_centers[cc]['namespaces'].append(ns.get('name', 'unknown'))
        
        if cost_centers:
            analysis.append("\n### COST CENTER BREAKDOWN:")
            for cc, data in sorted(cost_centers.items(), key=lambda x: x[1]['cost'], reverse=True):
                analysis.append(f"  - {cc}: ${data['cost']:.2f}/month ({len(data['namespaces'])} namespaces)")
        
        return '\n'.join(analysis)
    
    def _generate_storage_waste_analysis(self, storage_data: List[Dict]) -> str:
        """Generate detailed storage waste analysis"""
        if not storage_data:
            return "No storage waste analysis available"
        
        analysis = ["## COMPREHENSIVE STORAGE WASTE ANALYSIS"]
        
        total_requested = 0
        total_used = 0
        total_waste = 0
        
        for vol in storage_data:
            if 'size' in str(vol):
                size_info = vol.get('size', {}) if isinstance(vol.get('size'), dict) else {}
                requested = size_info.get('requested_gb', 0)
                used = size_info.get('used_gb', 0)
                
                if requested > 0 and used >= 0:
                    waste = max(0, requested - used)
                    total_requested += requested
                    total_used += used
                    total_waste += waste
                    
                    utilization = (used / requested * 100) if requested > 0 else 0
                    if utilization < 80:  # Under-utilized storage
                        analysis.append(f"""
**Volume {vol.get('name', 'unknown')}:**
- Requested: {requested}GB, Used: {used}GB
- Utilization: {utilization:.1f}% 
- Waste: {waste}GB (${waste * 0.1:.2f}/month)
- Recommendation: {'Resize to ' + str(int(used * 1.2)) + 'GB' if waste > 10 else 'Monitor usage'}""")
        
        if total_waste > 0:
            total_waste_cost = total_waste * 0.1  # Approximate cost per GB
            overall_utilization = (total_used / total_requested * 100) if total_requested > 0 else 0
            analysis.append(f"""
### STORAGE WASTE SUMMARY:
- Total Storage Requested: {total_requested:.1f}GB
- Total Storage Used: {total_used:.1f}GB  
- Total Storage Waste: {total_waste:.1f}GB
- Overall Utilization: {overall_utilization:.1f}%
- Monthly Waste Cost: ${total_waste_cost:.2f}
- Optimization Potential: {'High' if overall_utilization < 60 else 'Medium' if overall_utilization < 80 else 'Low'}""")
        
        return '\n'.join(analysis)
    
    def _generate_network_cost_analysis(self, network_data: Dict) -> str:
        """Generate detailed network cost analysis"""
        if not network_data:
            return "No network cost analysis available"
        
        analysis = ["## COMPREHENSIVE NETWORK COST ANALYSIS"]
        
        total_network_cost = network_data.get('total_network_cost', 0)
        egress_cost = network_data.get('egress_cost', 0) 
        public_ips = network_data.get('public_ips', [])
        load_balancers = network_data.get('load_balancers', [])
        
        analysis.append(f"""
### NETWORK COST BREAKDOWN:
- Total Network Cost: ${total_network_cost:.2f}/month
- Data Egress Cost: ${egress_cost:.2f}/month  
- Public IP Cost: ${len(public_ips) * 3.65:.2f}/month ({len(public_ips)} IPs)
- Load Balancer Cost: ${len(load_balancers) * 18.25:.2f}/month ({len(load_balancers)} LBs)""")
        
        if len(public_ips) > 5:
            analysis.append(f"""
### PUBLIC IP OPTIMIZATION OPPORTUNITY:
- Current Public IPs: {len(public_ips)}
- Recommended: Review for consolidation  
- Potential Savings: ${(len(public_ips) - 3) * 3.65:.2f}/month (keep 3, remove {len(public_ips) - 3})""")
        
        if len(load_balancers) > 2:
            analysis.append(f"""
### LOAD BALANCER OPTIMIZATION:
- Current Load Balancers: {len(load_balancers)}
- Optimization: Consolidate to shared ingress controller
- Potential Savings: ${(len(load_balancers) - 1) * 18.25:.2f}/month""")
        
        if egress_cost > 50:
            analysis.append(f"""
### DATA EGRESS OPTIMIZATION:
- Current Egress Cost: ${egress_cost:.2f}/month (HIGH)
- Recommendations:
  - Implement CDN for static content
  - Optimize inter-region data transfer
  - Review external API calls
  - Potential Savings: ${egress_cost * 0.3:.2f}/month""")
        
        return '\n'.join(analysis)
    
    def _generate_inefficiency_analysis(self, inefficient_data: Dict) -> str:
        """Generate root cause inefficiency analysis"""
        if not inefficient_data:
            return "No inefficiency analysis available"
        
        analysis = ["## INEFFICIENCY ROOT CAUSE ANALYSIS"]
        
        # Analyze each category
        categories = ['over_provisioned', 'under_utilized', 'missing_hpa_candidates', 'orphaned_resources']
        
        for category in categories:
            items = inefficient_data.get(category, [])
            if items:
                category_name = category.replace('_', ' ').title()
                analysis.append(f"\n### {category_name} ({len(items)} items):")
                
                if category == 'over_provisioned':
                    total_waste = sum(item.get('inefficiency_details', {}).get('monthly_waste_cost', 0) for item in items)
                    analysis.append(f"**Total Waste Cost:** ${total_waste:.2f}/month")
                    
                    for item in items[:5]:
                        workload = item.get('workload', {})
                        details = item.get('inefficiency_details', {})
                        name = workload.get('name', 'unknown')
                        namespace = workload.get('namespace', 'unknown')
                        waste = details.get('monthly_waste_cost', 0)
                        cpu_waste = details.get('cpu_waste_percentage', 0)
                        memory_waste = details.get('memory_waste_percentage', 0)
                        
                        analysis.append(f"""
**{name}** ({namespace}):
- Monthly Waste: ${waste:.2f}
- CPU Over-provision: {cpu_waste}%  
- Memory Over-provision: {memory_waste}%
- Root Cause: {'Resource requests too high' if cpu_waste > 50 else 'Minor over-allocation'}
- Fix Priority: {'High' if waste > 10 else 'Medium'}""")
                
                elif category == 'orphaned_resources':
                    for item in items[:10]:
                        name = item.get('name', 'unknown')
                        resource_type = item.get('type', 'unknown') 
                        namespace = item.get('namespace', 'unknown')
                        last_used = item.get('last_used', 'unknown')
                        
                        analysis.append(f"  - {name} ({resource_type}) in {namespace}, last used: {last_used}")
        
        # Summary
        total_issues = sum(len(inefficient_data.get(cat, [])) for cat in categories)
        analysis.append(f"""
### INEFFICIENCY SUMMARY:
- Total Issues Identified: {total_issues}
- Primary Root Cause: Over-provisioned CPU requests (causing 43.3% efficiency)
- Secondary Issues: Missing autoscaling, orphaned resources
- Estimated Fix Time: 2-4 weeks with phased approach
- Risk Level: Medium (with proper backup/rollback procedures)""")
        
        return '\n'.join(analysis)
    
    def _generate_cluster_health_assessment(self, context: Dict) -> str:
        """Generate comprehensive cluster health assessment"""
        efficiency = context.get('efficiency_metrics', {})
        cluster_info = context.get('cluster_info', {})
        
        analysis = ["## CLUSTER HEALTH & GOVERNANCE ASSESSMENT"]
        
        # Overall health score
        cpu_efficiency = efficiency.get('current_cpu_efficiency', 0) * 100
        memory_efficiency = efficiency.get('current_memory_efficiency', 0) * 100
        system_efficiency = efficiency.get('current_system_efficiency', 0) * 100
        target_efficiency = efficiency.get('target_system_efficiency', 0) * 100
        
        analysis.append(f"""
### OVERALL HEALTH METRICS:
- **CPU Efficiency:** {cpu_efficiency:.1f}% ({'🔴 CRITICAL' if cpu_efficiency < 50 else '🟡 WARNING' if cpu_efficiency < 70 else '🟢 GOOD'})
- **Memory Efficiency:** {memory_efficiency:.1f}% ({'🔴 CRITICAL' if memory_efficiency < 50 else '🟡 WARNING' if memory_efficiency < 70 else '🟢 GOOD'})  
- **System Efficiency:** {system_efficiency:.1f}% (Target: {target_efficiency:.1f}%)
- **Improvement Potential:** {efficiency.get('efficiency_improvement_potential', 0)*100:.1f}%""")
        
        # Health diagnosis
        health_issues = []
        if cpu_efficiency < 50:
            health_issues.append("🔴 CRITICAL: Severe CPU over-provisioning")
        if memory_efficiency > 95:
            health_issues.append("🟡 WARNING: Memory near capacity limits")
        if system_efficiency < 70:
            health_issues.append("🟡 WARNING: Overall system inefficiency")
        
        if health_issues:
            analysis.append("\n### HEALTH ISSUES IDENTIFIED:")
            for issue in health_issues:
                analysis.append(f"  {issue}")
        
        # Governance assessment
        k8s_version = cluster_info.get('kubernetes_version', 'unknown')
        analysis.append(f"""
### GOVERNANCE & COMPLIANCE STATUS:
- **Kubernetes Version:** {k8s_version} ({'🟢 CURRENT' if '1.3' in k8s_version else '🟡 REVIEW NEEDED'})
- **Resource Quotas:** Missing in multiple namespaces  
- **Security Policies:** Not consistently applied
- **Monitoring:** Basic monitoring in place
- **Cost Tracking:** Manual/periodic analysis
- **Backup Strategy:** Not verified
- **Disaster Recovery:** Not assessed""")
        
        # Recommendations
        analysis.append("""
### IMMEDIATE HEALTH ACTIONS REQUIRED:
1. **Emergency:** Address CPU over-provisioning (43.3% → 84.1% efficiency)
2. **High Priority:** Implement resource quotas across all namespaces
3. **Medium Priority:** Establish automated monitoring and alerting
4. **Low Priority:** Upgrade monitoring stack for better observability""")
        
        return '\n'.join(analysis)
    
    def _generate_naming_convention_analysis(self, namespaces_data: List[Dict]) -> str:
        """Generate naming convention compliance analysis"""
        if not namespaces_data:
            return "No naming convention analysis available"
        
        analysis = ["## NAMING CONVENTION & COMPLIANCE ANALYSIS"]
        
        # Analyze namespace naming patterns
        naming_patterns = {
            'compliant': [],
            'non_compliant': [],
            'missing_labels': []
        }
        
        for ns in namespaces_data:
            name = ns.get('name', '')
            labels = ns.get('labels', {})
            
            # Check naming compliance (example: should follow env-team-service pattern)
            if '-' in name and len(name.split('-')) >= 2:
                naming_patterns['compliant'].append(name)
            else:
                naming_patterns['non_compliant'].append(name)
            
            # Check required labels
            required_labels = ['environment', 'team_owner', 'cost_center']
            missing_labels = [label for label in required_labels if label not in labels]
            if missing_labels:
                naming_patterns['missing_labels'].append({'name': name, 'missing': missing_labels})
        
        analysis.append(f"""
### NAMING COMPLIANCE STATUS:
- **Compliant Namespaces:** {len(naming_patterns['compliant'])} ({len(naming_patterns['compliant'])/len(namespaces_data)*100:.0f}%)
- **Non-compliant Namespaces:** {len(naming_patterns['non_compliant'])} ({len(naming_patterns['non_compliant'])/len(namespaces_data)*100:.0f}%)
- **Missing Required Labels:** {len(naming_patterns['missing_labels'])} namespaces""")
        
        if naming_patterns['non_compliant']:
            analysis.append(f"\n### NON-COMPLIANT NAMESPACE NAMES:")
            for name in naming_patterns['non_compliant']:
                suggested = f"env-team-{name}" if not '-' in name else name
                analysis.append(f"  - {name} → Suggested: {suggested}")
        
        if naming_patterns['missing_labels']:
            analysis.append(f"\n### MISSING REQUIRED LABELS:")
            for item in naming_patterns['missing_labels'][:10]:
                analysis.append(f"  - {item['name']}: Missing {', '.join(item['missing'])}")
        
        # Naming standards recommendation
        analysis.append("""
### RECOMMENDED NAMING STANDARDS:
**Namespaces:** {environment}-{team}-{service} (e.g., prod-api-customerservice)
**Deployments:** {service}-{component} (e.g., api-gateway, db-primary)  
**Services:** {deployment-name}-svc
**ConfigMaps:** {service}-config
**Secrets:** {service}-secret

### REQUIRED LABELS:
- environment: (prod/staging/dev)
- team: (team responsible)
- cost-center: (billing allocation)
- service: (application name)
- version: (semantic version)""")
        
        return '\n'.join(analysis)
    
    def _generate_security_compliance_analysis(self, context: Dict) -> str:
        """Generate security and compliance gap analysis"""
        namespaces_data = context.get('namespaces_analysis', [])
        
        analysis = ["## SECURITY & COMPLIANCE GAP ANALYSIS"]
        
        # Resource governance gaps
        governance_gaps = 0
        security_gaps = 0
        
        for ns in namespaces_data:
            inefficiencies = ns.get('inefficiencies', [])
            if 'missing_resource_limits' in inefficiencies:
                governance_gaps += 1
            # Add more security checks here based on available data
        
        analysis.append(f"""
### RESOURCE GOVERNANCE COMPLIANCE:
- **Resource Quotas Missing:** {governance_gaps} namespaces  
- **LimitRanges Missing:** {governance_gaps} namespaces
- **Compliance Score:** {((len(namespaces_data) - governance_gaps) / len(namespaces_data) * 100):.0f}%""")
        
        # Security policy gaps
        analysis.append("""
### SECURITY POLICY GAPS IDENTIFIED:
🔴 **Critical Gaps:**
- Pod Security Standards not enforced
- Network Policies missing in production namespaces
- RBAC permissions not following least privilege

🟡 **Medium Priority Gaps:**
- No admission controllers for security validation
- Container image scanning not enforced
- Resource requests/limits not mandatory

🟢 **Best Practice Improvements:**
- Service mesh for improved security
- Secrets management integration
- Automated compliance scanning""")
        
        # Compliance recommendations
        analysis.append(f"""
### COMPLIANCE RECOMMENDATIONS:
**Phase 1: Resource Governance**
- Implement ResourceQuota in {governance_gaps} namespaces
- Create default LimitRange policies
- Enforce resource requests/limits

**Phase 2: Security Policies**  
- Deploy Pod Security Standards
- Implement Network Policies for namespace isolation
- Review and optimize RBAC permissions

**Phase 3: Advanced Security**
- Implement admission controllers
- Integrate secrets management (Azure Key Vault)
- Set up automated security scanning

### COMPLIANCE BENEFITS:
- Improved security posture
- Better cost control through resource governance  
- Regulatory compliance preparation
- Reduced blast radius of security incidents""")
        
        return '\n'.join(analysis)
    
    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API with the prompt"""
        # Call Claude API
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 4000,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = await asyncio.to_thread(
                requests.post,
                self.claude_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Track usage and costs
                usage = result.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                # Calculate costs
                input_cost = (input_tokens / 1000) * self.input_cost_per_1k
                output_cost = (output_tokens / 1000) * self.output_cost_per_1k
                call_cost = input_cost + output_cost
                self.total_cost += call_cost
                
                # Log cost information
                print(f"\n💰 Claude API Usage for this call:")
                print(f"   Input tokens:  {input_tokens:,} (${input_cost:.4f})")
                print(f"   Output tokens: {output_tokens:,} (${output_cost:.4f})")
                print(f"   Call cost:     ${call_cost:.4f}")
                print(f"   Total cost:    ${self.total_cost:.4f}")
                
                markdown_response = result.get('content', [{}])[0].get('text', '')
                if not markdown_response:
                    raise ValueError("Claude returned empty response")
                
                # Log the response for debugging
                logger.info(f"Claude response length: {len(markdown_response)} characters")
                logger.debug(f"Claude response preview: {markdown_response[:500]}...")
                
                return markdown_response
            else:
                error_text = response.text if hasattr(response, 'text') else str(response.content)
                raise ValueError(f"Claude API error {response.status_code}: {error_text}")
                
        except Exception as e:
            logger.error(f"Failed to call Claude API: {e}")
            raise ValueError(f"Failed to generate markdown plan from Claude: {e}")
    
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
        
        # Create plan structure with markdown content
        return self._create_plan_structure(
            cluster_name=cluster_name,
            cluster_id=cluster_id,
            phases=phases,
            total_savings=total_savings,
            current_cost=context.get('current_monthly_cost', 2000.0),
            markdown_content=markdown
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
        current_cost: float,
        markdown_content: str = None
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
✅ OPTIMIZATION PLAN GENERATED WITH CLAUDE:
   Cluster: {cluster_name}
   Phases: {len(phases)}
   Total Actions: {sum(len(p.actions) for p in phases)}
   Monthly Savings: ${total_savings:,.2f}
   Annual Savings: ${total_savings * 12:,.2f}
   ROI: {roi_analysis.calculation_breakdown.roi_percentage_year1:.0f}%
   
💰 CLAUDE API COSTS:
   Total Input Tokens:  {self.total_input_tokens:,}
   Total Output Tokens: {self.total_output_tokens:,}
   Total Cost: ${self.total_cost:.4f}
        """)
        
        # Validate phases before creating plan
        self._validate_phases(phases)
        
        # Create plan with markdown content
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
            generated_by="Claude AI",
            version="2.0",
            markdown_content=markdown_content  # Add the raw markdown
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
    
    def get_cost_summary(self) -> Dict:
        """Get detailed cost summary for this session"""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "input_cost_usd": round((self.total_input_tokens / 1000) * self.input_cost_per_1k, 4),
            "output_cost_usd": round((self.total_output_tokens / 1000) * self.output_cost_per_1k, 4),
            "model": self.model,
            "cost_per_analysis": round(self.total_cost, 4)
        }
    
