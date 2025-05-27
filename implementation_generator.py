"""
AKS Implementation Plan Generator - Fully Dynamic
=================================================
Generates implementation plans based ENTIRELY on actual analysis results.
No static configuration - everything is calculated from your real cluster data.
"""

import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AKSImplementationGenerator:
    """Generates implementation plans based purely on analysis results"""
    
    def generate_implementation_plan(self, analysis_results):
        """Generate implementation plan based ONLY on analysis data"""
        logger.info("Generating fully dynamic implementation plan from analysis")
        
        if not analysis_results or analysis_results.get('total_cost', 0) == 0:
            return self._no_analysis_plan()
        
        # Extract metrics from analysis
        metrics = AnalysisMetricsExtractor(analysis_results).extract()
        
        # Calculate everything dynamically from the analysis
        complexity = ComplexityCalculator(metrics).calculate()
        timeline = TimelineCalculator(metrics, complexity).calculate()
        phases = PhaseGenerator(metrics, complexity).generate()
        
        # Generate supporting plans based on actual metrics
        monitoring = MonitoringPlanGenerator(metrics).generate()
        governance = GovernancePlanGenerator(metrics).generate()
        success_metrics = SuccessMetricsGenerator(metrics).generate()
        contingency = ContingencyPlanGenerator(metrics).generate()
        
        return {
            'summary': {
                'total_phases': len(phases),
                'total_weeks': timeline,
                'total_savings': sum(p.get('savings', 0) for p in phases),
                'monthly_savings': metrics.total_savings,
                'annual_savings': metrics.total_savings * 12,
                'complexity_score': complexity.score,
                'risk_level': complexity.overall_risk,
                'resource_group': metrics.resource_group,
                'cluster_name': metrics.cluster_name,
                'generated_at': datetime.now().isoformat()
            },
            'phases': phases,
            'monitoring_plan': monitoring,
            'governance_plan': governance,
            'success_metrics': success_metrics,
            'contingency_plans': contingency
        }
    
    def _no_analysis_plan(self):
        """Return when no analysis data is available"""
        return {
            'summary': {
                'total_phases': 0,
                'total_weeks': 0,
                'total_savings': 0,
                'message': 'Run an analysis first to generate your implementation plan'
            },
            'phases': [], 'monitoring_plan': {}, 'governance_plan': {},
            'success_metrics': {}, 'contingency_plans': {}
        }


class AnalysisMetricsExtractor:
    """Extracts and structures metrics from analysis results"""
    
    def __init__(self, analysis_results):
        self.analysis = analysis_results
    
    def extract(self):
        """Extract structured metrics from analysis"""
        return AnalysisMetrics(
            total_cost=self.analysis.get('total_cost', 0),
            total_savings=self._calculate_total_savings(),
            hpa_savings=self.analysis.get('hpa_savings', 0),
            right_sizing_savings=self.analysis.get('right_sizing_savings', 0),
            storage_savings=self.analysis.get('storage_savings', 0),
            hpa_reduction=self.analysis.get('hpa_reduction', 0),
            cpu_gap=self.analysis.get('cpu_gap', 0),
            memory_gap=self.analysis.get('memory_gap', 0),
            node_metrics=self.analysis.get('node_metrics', []),
            resource_group=self.analysis.get('resource_group', 'your-resource-group'),
            cluster_name=self.analysis.get('cluster_name', 'your-cluster'),
            node_cost=self.analysis.get('node_cost', 0),
            storage_cost=self.analysis.get('storage_cost', 0)
        )
    
    def _calculate_total_savings(self):
        """Calculate total savings if not provided"""
        return (self.analysis.get('hpa_savings', 0) + 
                self.analysis.get('right_sizing_savings', 0) + 
                self.analysis.get('storage_savings', 0))


class AnalysisMetrics:
    """Structured metrics from analysis"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class ComplexityCalculator:
    """Calculates implementation complexity based on analysis metrics"""
    
    def __init__(self, metrics):
        self.metrics = metrics
    
    def calculate(self):
        """Calculate complexity based on actual cluster metrics"""
        # Start with base complexity
        base_score = 3
        
        # Node count impact (from actual metrics)
        node_count = len(self.metrics.node_metrics)
        if node_count == 0:
            node_factor = 1  # Unknown, assume simple
        elif node_count > 15:
            node_factor = 4  # Very complex
        elif node_count > 8:
            node_factor = 3  # Complex
        elif node_count > 3:
            node_factor = 2  # Medium
        else:
            node_factor = 1  # Simple
        
        # Savings magnitude impact (higher savings = more complex changes)
        if self.metrics.total_savings > 800:
            savings_factor = 4  # Major changes needed
        elif self.metrics.total_savings > 400:
            savings_factor = 3  # Significant changes
        elif self.metrics.total_savings > 100:
            savings_factor = 2  # Moderate changes
        else:
            savings_factor = 1  # Minor changes
        
        # Resource gap impact (bigger gaps = more dramatic changes)
        avg_gap = (self.metrics.cpu_gap + self.metrics.memory_gap) / 2
        if avg_gap > 60:
            gap_factor = 4  # Massive over-provisioning
        elif avg_gap > 40:
            gap_factor = 3  # Significant over-provisioning
        elif avg_gap > 20:
            gap_factor = 2  # Moderate over-provisioning
        else:
            gap_factor = 1  # Minor over-provisioning
        
        # HPA complexity (higher reduction = more complex HPA changes)
        if self.metrics.hpa_reduction > 60:
            hpa_factor = 3  # Major HPA restructuring
        elif self.metrics.hpa_reduction > 30:
            hpa_factor = 2  # Significant HPA changes
        else:
            hpa_factor = 1  # Minor HPA adjustments
        
        # Calculate weighted score
        complexity_score = min(10, base_score + 
                              (node_factor * 0.3) + 
                              (savings_factor * 0.3) + 
                              (gap_factor * 0.2) + 
                              (hpa_factor * 0.2))
        
        # Determine risk levels based on complexity
        if complexity_score >= 8:
            overall_risk = 'High'
            individual_risks = {'quick_wins': 'Medium', 'hpa': 'High', 'storage': 'Medium'}
        elif complexity_score >= 6:
            overall_risk = 'Medium'
            individual_risks = {'quick_wins': 'Low', 'hpa': 'Medium', 'storage': 'Low'}
        else:
            overall_risk = 'Low'
            individual_risks = {'quick_wins': 'Low', 'hpa': 'Low', 'storage': 'Low'}
        
        return ComplexityResult(
            score=complexity_score,
            overall_risk=overall_risk,
            individual_risks=individual_risks,
            node_factor=node_factor,
            savings_factor=savings_factor,
            gap_factor=gap_factor,
            hpa_factor=hpa_factor
        )


class ComplexityResult:
    """Results from complexity calculation"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TimelineCalculator:
    """Calculates implementation timeline based on complexity and savings"""
    
    def __init__(self, metrics, complexity):
        self.metrics = metrics
        self.complexity = complexity
    
    def calculate(self):
        """Calculate timeline based on actual complexity"""
        # Base timeline depends on how much work is needed
        if self.metrics.total_savings > 500:
            base_weeks = 6  # Major optimization project
        elif self.metrics.total_savings > 200:
            base_weeks = 4  # Moderate optimization
        else:
            base_weeks = 2  # Minor optimization
        
        # Adjust for complexity
        if self.complexity.score >= 8:
            complexity_adjustment = 4  # High complexity adds time
        elif self.complexity.score >= 6:
            complexity_adjustment = 2  # Medium complexity
        else:
            complexity_adjustment = 0  # Low complexity
        
        # Adjust for cluster size (more nodes = more coordination)
        node_count = len(self.metrics.node_metrics)
        if node_count > 10:
            coordination_time = 2
        elif node_count > 5:
            coordination_time = 1
        else:
            coordination_time = 0
        
        total_weeks = base_weeks + complexity_adjustment + coordination_time
        return min(16, total_weeks)  # Cap at 16 weeks maximum


class PhaseGenerator:
    """Generates implementation phases based on analysis metrics"""
    
    def __init__(self, metrics, complexity):
        self.metrics = metrics
        self.complexity = complexity
    
    def generate(self):
        """Generate phases based on actual optimization opportunities"""
        phases = []
        current_week = 0
        
        # Only create phases for optimizations that have actual savings potential
        
        # Phase 1: Quick Resource Wins (if significant gaps exist)
        if self.metrics.cpu_gap > 25 or self.metrics.memory_gap > 20:
            quick_wins_savings = self.metrics.right_sizing_savings * 0.6
            phases.append(self._create_quick_wins_phase(quick_wins_savings, current_week))
            current_week += 2
        
        # Phase 2: HPA Implementation (if HPA reduction is significant)
        if self.metrics.hpa_reduction > 15 and self.metrics.hpa_savings > 20:
            hpa_duration = 3 if self.complexity.score > 7 else 2
            phases.append(self._create_hpa_phase(current_week, hpa_duration))
            current_week += hpa_duration
        
        # Phase 3: Complete Right-sizing (remaining savings)
        remaining_savings = self.metrics.right_sizing_savings - (
            phases[0]['savings'] if phases and 'Resource' in phases[0]['title'] else 0
        )
        if remaining_savings > 15:
            phases.append(self._create_complete_optimization_phase(remaining_savings, current_week))
            current_week += 3
        
        # Phase 4: Storage Optimization (if storage savings exist)
        if self.metrics.storage_savings > 10:
            phases.append(self._create_storage_phase(current_week))
        
        return phases
    
    def _create_quick_wins_phase(self, savings, start_week):
        """Create quick wins phase based on actual gaps"""
        tasks = []
        
        # Generate tasks based on actual problems found
        if self.metrics.cpu_gap > 30:
            tasks.append({
                'task': f'Optimize High CPU Gap Workloads',
                'description': f'Target workloads with {self.metrics.cpu_gap:.1f}% average CPU over-provisioning',
                'command': f'kubectl top pods --sort-by=cpu -A | head -10',
                'expected_outcome': f'Identify top CPU over-provisioned workloads for immediate optimization'
            })
        
        if self.metrics.memory_gap > 25:
            tasks.append({
                'task': f'Optimize High Memory Gap Workloads',
                'description': f'Target workloads with {self.metrics.memory_gap:.1f}% average memory over-provisioning',
                'command': f'kubectl top pods --sort-by=memory -A | head -10',
                'expected_outcome': f'Identify top memory over-provisioned workloads'
            })
        
        # Calculate realistic resource adjustments based on gaps
        cpu_reduction = min(50, self.metrics.cpu_gap * 0.7)  # Conservative reduction
        memory_reduction = min(40, self.metrics.memory_gap * 0.6)
        
        tasks.append({
            'task': 'Apply Quick Resource Adjustments',
            'description': f'Reduce CPU requests by ~{cpu_reduction:.0f}% and memory by ~{memory_reduction:.0f}% for identified workloads',
            'expected_outcome': f'${savings:.2f}/month savings from resource right-sizing'
        })
        
        return {
            'phase': 1,
            'title': 'Resource Right-Sizing (Quick Wins)',
            'weeks': f'Weeks {start_week + 1}-{start_week + 2}',
            'duration': 2,
            'savings': savings,
            'risk': self.complexity.individual_risks['quick_wins'],
            'description': f'Address the most obvious over-provisioning issues. Analysis shows {self.metrics.cpu_gap:.1f}% CPU gap and {self.metrics.memory_gap:.1f}% memory gap.',
            'tasks': tasks,
            'validation': self._generate_validation('right_sizing'),
            'rollback_plan': self._generate_rollback('right_sizing')
        }
    
    def _create_hpa_phase(self, start_week, duration):
        """Create HPA phase based on actual HPA analysis"""
        # Calculate optimal memory target based on analysis
        target_utilization = max(60, min(85, 100 - (self.metrics.hpa_reduction / 2)))
        
        tasks = [
            {
                'task': 'Analyze Current HPA Performance',
                'description': f'Review existing HPA configurations that could benefit from {self.metrics.hpa_reduction:.1f}% reduction',
                'command': 'kubectl get hpa -A -o yaml > current-hpa-backup.yaml',
                'expected_outcome': 'Backup and analysis of current HPA settings'
            },
            {
                'task': 'Implement Memory-Based HPA',
                'description': f'Deploy memory-based HPA with {target_utilization:.0f}% target utilization',
                'template': f'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: memory-optimized-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{deployment_name}}
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {int(target_utilization)}''',
                'expected_outcome': f'${self.metrics.hpa_savings:.2f}/month savings from optimized scaling'
            }
        ]
        
        return {
            'phase': 2,
            'title': 'Memory-Based HPA Implementation',
            'weeks': f'Weeks {start_week + 1}-{start_week + duration}',
            'duration': duration,
            'savings': self.metrics.hpa_savings,
            'risk': self.complexity.individual_risks['hpa'],
            'description': f'Implement memory-based HPA scaling. Analysis shows {self.metrics.hpa_reduction:.1f}% replica reduction potential.',
            'tasks': tasks,
            'validation': self._generate_validation('hpa'),
            'rollback_plan': self._generate_rollback('hpa')
        }
    
    def _create_complete_optimization_phase(self, savings, start_week):
        """Create complete optimization phase"""
        return {
            'phase': 3,
            'title': 'Complete Resource Optimization',
            'weeks': f'Weeks {start_week + 1}-{start_week + 3}',
            'duration': 3,
            'savings': savings,
            'risk': 'Medium',
            'description': f'Complete remaining resource optimization worth ${savings:.2f}/month',
            'tasks': [
                {
                    'task': 'Comprehensive Resource Analysis',
                    'description': 'Analyze all remaining workloads for optimization opportunities',
                    'expected_outcome': 'Complete resource optimization plan'
                },
                {
                    'task': 'Gradual Resource Optimization',
                    'description': 'Apply optimizations to remaining workloads with careful monitoring',
                    'expected_outcome': f'${savings:.2f}/month additional savings'
                }
            ],
            'validation': self._generate_validation('complete'),
            'rollback_plan': self._generate_rollback('complete')
        }
    
    def _create_storage_phase(self, start_week):
        """Create storage optimization phase"""
        # Calculate storage optimization based on actual storage costs
        storage_percentage = (self.metrics.storage_cost / self.metrics.total_cost) * 100 if self.metrics.total_cost > 0 else 0
        
        tasks = [
            {
                'task': 'Storage Usage Analysis',
                'description': f'Analyze ${self.metrics.storage_cost:.2f}/month storage costs ({storage_percentage:.1f}% of total)',
                'command': 'kubectl get pv -o custom-columns=NAME:.metadata.name,STORAGECLASS:.spec.storageClassName,SIZE:.spec.capacity.storage',
                'expected_outcome': 'Identify premium storage that can be optimized'
            }
        ]
        
        # Add storage class creation if significant premium storage detected
        if self.metrics.storage_cost > 50:
            tasks.append({
                'task': 'Create Cost-Optimized Storage Class',
                'description': 'Set up StandardSSD storage class for non-critical workloads',
                'template': '''apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-standard-ssd
provisioner: kubernetes.io/azure-disk
parameters:
  storageaccounttype: StandardSSD_LRS
  kind: Managed
reclaimPolicy: Retain''',
                'expected_outcome': f'Enable ${self.metrics.storage_savings:.2f}/month storage savings'
            })
        
        return {
            'phase': 4,
            'title': 'Storage Optimization',
            'weeks': f'Weeks {start_week + 1}-{start_week + 2}',
            'duration': 2,
            'savings': self.metrics.storage_savings,
            'risk': self.complexity.individual_risks['storage'],
            'description': f'Optimize storage usage to save ${self.metrics.storage_savings:.2f}/month',
            'tasks': tasks,
            'validation': self._generate_validation('storage'),
            'rollback_plan': self._generate_rollback('storage')
        }
    
    def _generate_validation(self, phase_type):
        """Generate validation steps based on phase type and metrics"""
        base_validations = {
            'right_sizing': [
                f'Monitor resource utilization for 24 hours',
                f'Verify no performance degradation',
                f'Confirm ${self.metrics.right_sizing_savings:.2f}/month cost reduction'
            ],
            'hpa': [
                f'Validate HPA scaling with {self.metrics.hpa_reduction:.1f}% fewer replicas',
                f'Monitor memory utilization at target levels',
                f'Confirm ${self.metrics.hpa_savings:.2f}/month savings'
            ],
            'storage': [
                f'Verify storage I/O performance unchanged',
                f'Confirm ${self.metrics.storage_savings:.2f}/month cost reduction'
            ],
            'complete': [
                f'Comprehensive monitoring for 72 hours',
                f'Validate total savings of ${self.metrics.total_savings:.2f}/month'
            ]
        }
        return base_validations.get(phase_type, ['Monitor system behavior'])
    
    def _generate_rollback(self, phase_type):
        """Generate rollback plans based on actual risk levels"""
        return {
            'trigger_conditions': [
                f'Resource utilization > 90%',
                f'Application response time > 5% increase',
                f'Error rate > 1%'
            ],
            'rollback_steps': [
                f'Revert resource requests to original values',
                f'Monitor for 15 minutes',
                f'Escalate if issues persist'
            ],
            'recovery_time': '< 10 minutes'
        }


class MonitoringPlanGenerator:
    """Generates monitoring plan based on actual metrics"""
    
    def __init__(self, metrics):
        self.metrics = metrics
    
    def generate(self):
        """Generate monitoring plan based on optimization areas"""
        return {
            'daily_checks': [
                f'Monitor cost trends (target: ${self.metrics.total_cost - self.metrics.total_savings:.2f}/month)',
                f'Check resource utilization (target: 70-80%)',
                f'Verify application performance metrics'
            ],
            'weekly_reviews': [
                f'Validate ${self.metrics.total_savings:.2f}/month savings target',
                f'Review HPA scaling patterns',
                f'Analyze new optimization opportunities'
            ],
            'monthly_assessments': [
                f'Comprehensive cost analysis vs ${self.metrics.total_cost:.2f} baseline',
                f'Evaluate ${(self.metrics.total_savings/self.metrics.total_cost*100):.1f}% optimization target',
                f'Plan next optimization phase'
            ],
            'automated_alerts': [
                f'Cost increase > 10% from ${self.metrics.total_cost:.2f} baseline',
                f'Resource utilization > 90% for > 30 minutes',
                f'HPA scaling failures',
                f'Application response time > 20% increase'
            ]
        }


class GovernancePlanGenerator:
    """Generates governance plan based on cluster characteristics"""
    
    def __init__(self, metrics):
        self.metrics = metrics
    
    def generate(self):
        """Generate governance based on cluster size and savings"""
        node_count = len(self.metrics.node_metrics)
        
        policies = []
        if self.metrics.total_savings > 200:
            policies.append('Implement strict resource quota enforcement')
        if node_count > 5:
            policies.append('Require resource requests for all new deployments')
        if self.metrics.storage_savings > 50:
            policies.append('Mandatory storage class approval process')
        
        return {
            'resource_policies': policies or ['Basic resource governance'],
            'cost_controls': [
                f'Monthly budget alert at ${(self.metrics.total_cost - self.metrics.total_savings) * 1.1:.2f}',
                f'Track ${self.metrics.total_savings:.2f}/month savings target',
                'Quarterly optimization reviews'
            ],
            'operational_procedures': [
                f'Pre-deployment resource review for clusters with {node_count}+ nodes',
                'Performance validation after optimization changes',
                'Rollback procedures for changes > $100/month impact'
            ]
        }


class SuccessMetricsGenerator:
    """Generates success metrics based on analysis targets"""
    
    def __init__(self, metrics):
        self.metrics = metrics
    
    def generate(self):
        """Generate success metrics based on actual targets"""
        target_cost = self.metrics.total_cost - self.metrics.total_savings
        savings_percentage = (self.metrics.total_savings / self.metrics.total_cost * 100) if self.metrics.total_cost > 0 else 0
        
        return {
            'cost_metrics': {
                'target_monthly_cost': target_cost,
                'target_savings_percentage': savings_percentage,
                'roi_target': f'> {min(500, int(savings_percentage * 20))}% within 6 months'
            },
            'performance_metrics': {
                'application_availability': '> 99.9%',
                'response_time_impact': '< 5%',
                'resource_efficiency_target': f'{max(70, 100-self.metrics.cpu_gap/2):.0f}-85%'
            },
            'operational_metrics': {
                'implementation_success_rate': '> 90%',
                'rollback_incidents': f'< {max(1, len(self.metrics.node_metrics)//5)} per phase',
                'optimization_sustainability': '> 6 months'
            }
        }


class ContingencyPlanGenerator:
    """Generates contingency plans based on savings and risks"""
    
    def __init__(self, metrics):
        self.metrics = metrics
    
    def generate(self):
        """Generate realistic contingency plans"""
        return {
            'budget_constraints': {
                'scenario': 'If full optimization budget not approved',
                'alternative': f'Focus on quick wins only (${self.metrics.right_sizing_savings * 0.6:.2f}/month)',
                'impact': f'{((self.metrics.right_sizing_savings * 0.6)/self.metrics.total_savings*100):.0f}% of total savings'
            },
            'resource_constraints': {
                'scenario': 'If team has limited bandwidth',
                'alternative': 'Extend timeline by 50% with gradual implementation',
                'impact': 'Delayed benefits but reduced implementation risk'
            },
            'technical_risks': {
                'scenario': 'If critical applications show performance issues',
                'alternative': f'Skip high-risk optimizations, achieve ${self.metrics.total_savings * 0.7:.2f}/month',
                'impact': f'{70}% of planned savings with minimal risk'
            }
        }


def create_implementation_generator():
    """Factory function to create implementation generator"""
    return AKSImplementationGenerator()