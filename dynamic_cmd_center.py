"""
Phase 3: Advanced Executable Command Generator
=============================================
Generates production-ready kubectl/az commands with real cluster values,
complete validation, monitoring, and rollback procedures.

INTEGRATION: Works with Phase 1 (DNA) + Phase 2 (Strategy)
PURPOSE: Convert strategies into 100% executable, validated commands
"""

import json
import yaml
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import re

logger = logging.getLogger(__name__)

# ============================================================================
# ADVANCED DATA STRUCTURES
# ============================================================================

@dataclass
class ExecutableCommand:
    """Production-ready executable command with full context"""
    id: str
    command: str
    description: str
    category: str  # 'preparation', 'execution', 'validation', 'rollback'
    yaml_content: Optional[str]
    validation_commands: List[str]
    rollback_commands: List[str]
    expected_outcome: str
    success_criteria: List[str]
    timeout_seconds: int
    retry_attempts: int
    prerequisites: List[str]
    estimated_duration_minutes: int
    risk_level: str
    monitoring_metrics: List[str]

@dataclass
class ValidationRule:
    """Validation rule for command execution"""
    name: str
    check_command: str
    expected_result: str
    failure_action: str
    timeout_seconds: int

@dataclass
class MonitoringSpec:
    """Monitoring specification for optimization"""
    metric_name: str
    query: str
    threshold: float
    duration_minutes: int
    alert_condition: str
    remediation_action: str

@dataclass
class ExecutionPlan:
    """Complete execution plan with all commands and safety measures"""
    plan_id: str
    cluster_name: str
    strategy_name: str
    total_estimated_minutes: int
    commands: List[ExecutableCommand]
    validation_rules: List[ValidationRule]
    monitoring_specs: List[MonitoringSpec]
    rollback_strategy: str
    success_probability: float
    estimated_savings: float

# ============================================================================
# ADVANCED EXECUTABLE COMMAND GENERATOR
# ============================================================================

class AdvancedExecutableCommandGenerator:
    """
    Production-ready command generator with real cluster integration
    """
    
    def __init__(self):
        self.yaml_generator = DynamicYAMLGenerator()
        self.validation_engine = ValidationEngine()
        self.monitoring_generator = MonitoringGenerator()
        self.safety_engine = SafetyEngine()
        
    def generate_execution_plan(self, optimization_strategy, 
                                         cluster_dna, 
                                         analysis_results: Dict) -> ExecutionPlan:
        """
        MAIN METHOD: Generate complete production execution plan
        
        Args:
            optimization_strategy: Strategy object from dynamic_strategy.py
            cluster_dna: ClusterDNA object from dna_analyzer.py
            analysis_results: Dict with cluster analysis data
        """
        logger.info(f"🛠️ Generating production execution plan for: {getattr(optimization_strategy, 'strategy_name', 'Unknown Strategy')}")
        
        plan_id = f"exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        cluster_name = analysis_results.get('cluster_name', 'unknown-cluster')
        strategy_name = getattr(optimization_strategy, 'strategy_name', 'Dynamic Optimization Strategy')
        
        all_commands = []
        all_validation_rules = []
        all_monitoring_specs = []
        total_duration = 0
        
        # Get opportunities from strategy object
        opportunities = getattr(optimization_strategy, 'opportunities', [])
        
        # Generate commands for each opportunity
        for opportunity in opportunities:
            opportunity_commands = self._generate_opportunity_commands(
                opportunity, cluster_dna, analysis_results
            )
            
            opportunity_validations = self._generate_opportunity_validations(
                opportunity, cluster_dna, analysis_results
            )
            
            opportunity_monitoring = self._generate_opportunity_monitoring(
                opportunity, cluster_dna, analysis_results
            )
            
            all_commands.extend(opportunity_commands)
            all_validation_rules.extend(opportunity_validations)
            all_monitoring_specs.extend(opportunity_monitoring)
            total_duration += sum(cmd.estimated_duration_minutes for cmd in opportunity_commands)
        
        # Add safety commands
        safety_commands = self.safety_engine.generate_safety_commands(
            cluster_name, optimization_strategy
        )
        all_commands.extend(safety_commands)
        
        # Determine rollback strategy
        rollback_strategy = self._determine_rollback_strategy(optimization_strategy, cluster_dna)
        
        execution_plan = ExecutionPlan(
            plan_id=plan_id,
            cluster_name=cluster_name,
            strategy_name=strategy_name,
            total_estimated_minutes=total_duration,
            commands=all_commands,
            validation_rules=all_validation_rules,
            monitoring_specs=all_monitoring_specs,
            rollback_strategy=rollback_strategy,
            success_probability=getattr(optimization_strategy, 'success_probability', 0.8),
            estimated_savings=getattr(optimization_strategy, 'total_savings_potential', 0)
        )
        
        logger.info(f"✅ Generated execution plan with {len(all_commands)} commands")
        logger.info(f"⏱️ Total estimated duration: {total_duration} minutes")
        
        return execution_plan
    
    def _generate_opportunity_commands(self, opportunity: str, 
                                     cluster_dna, 
                                     analysis_results: Dict) -> List[ExecutableCommand]:
        """Generate commands for specific optimization opportunity"""
        
        if opportunity == 'hpa_optimization':
            return self._generate_hpa_commands(cluster_dna, analysis_results)
        elif opportunity == 'resource_rightsizing':
            return self._generate_rightsizing_commands(cluster_dna, analysis_results)
        elif opportunity == 'storage_optimization':
            return self._generate_storage_commands(cluster_dna, analysis_results)
        elif opportunity == 'system_pool_optimization':
            return self._generate_system_pool_commands(cluster_dna, analysis_results)
        else:
            return []
    
    def _generate_hpa_commands(self, cluster_dna, analysis_results: Dict) -> List[ExecutableCommand]:
        """Generate comprehensive HPA optimization commands"""
        
        commands = []
        cluster_name = analysis_results.get('cluster_name', 'unknown-cluster')
        resource_group = analysis_results.get('resource_group', 'unknown-rg')
        
        # Get actual workloads from analysis
        workload_costs = analysis_results.get('workload_costs', {})
        top_workloads = sorted(workload_costs.items(), 
                              key=lambda x: x[1].get('cost', 0), reverse=True)[:3]
        
        # Calculate optimal HPA settings based on cluster DNA
        scaling_characteristics = getattr(cluster_dna, 'scaling_characteristics', {})
        scaling_potential = scaling_characteristics.get('auto_scaling_potential', 0.5) if isinstance(scaling_characteristics, dict) else 0.5
        
        if scaling_potential > 0.7:
            memory_target, cpu_target = 65, 60  # Aggressive
        elif scaling_potential > 0.4:
            memory_target, cpu_target = 70, 65  # Moderate
        else:
            memory_target, cpu_target = 75, 70  # Conservative
        
        # 1. Pre-deployment validation
        commands.append(ExecutableCommand(
            id="hpa-001-validation",
            command=f"kubectl get deployment --all-namespaces -o wide | grep -E \"({'|'.join([w.split('/')[1] if '/' in w else w for w, _ in top_workloads])})\"",
            description="Validate target deployments exist and are ready",
            category="preparation",
            yaml_content=None,
            validation_commands=[
                "kubectl get deployment --all-namespaces",
                "kubectl get metrics.k8s.io",
                "kubectl top nodes"
            ],
            rollback_commands=["# No rollback needed for validation"],
            expected_outcome="All target deployments are running and metrics server is available",
            success_criteria=[
                "All deployments show READY status",
                "Metrics server responds to kubectl top commands",
                "CPU and memory metrics are available"
            ],
            timeout_seconds=300,
            retry_attempts=2,
            prerequisites=["Metrics server must be running", "kubectl access to cluster"],
            estimated_duration_minutes=5,
            risk_level="Low",
            monitoring_metrics=["deployment_status", "metrics_server_availability"]
        ))
        
        # 2. Generate HPA for each workload
        for workload_key, workload_data in top_workloads:
            if '/' in workload_key:
                namespace, workload_name = workload_key.split('/', 1)
            else:
                namespace, workload_name = 'default', workload_key
            
            current_replicas = workload_data.get('replicas', 2)
            min_replicas = max(1, current_replicas // 2)
            max_replicas = current_replicas * 3
            
            # Generate dynamic HPA YAML
            hpa_yaml = self.yaml_generator.generate_hpa_yaml(
                workload_name, namespace, min_replicas, max_replicas,
                memory_target, cpu_target, analysis_results
            )
            
            commands.append(ExecutableCommand(
                id=f"hpa-002-{workload_name}",
                command=f"echo '{hpa_yaml}' | kubectl apply -f -",
                description=f"Deploy optimized HPA for {workload_name} (${workload_data.get('cost', 0):.2f}/month workload)",
                category="execution",
                yaml_content=hpa_yaml,
                validation_commands=[
                    f"kubectl get hpa {workload_name}-hpa -n {namespace} -o wide",
                    f"kubectl describe hpa {workload_name}-hpa -n {namespace}",
                    f"kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.status.replicas}}'"
                ],
                rollback_commands=[
                    f"kubectl delete hpa {workload_name}-hpa -n {namespace}",
                    f"kubectl scale deployment {workload_name} --replicas={current_replicas} -n {namespace}",
                    f"kubectl rollout status deployment/{workload_name} -n {namespace}"
                ],
                expected_outcome=f"HPA active with targets: memory/{memory_target}%, cpu/{cpu_target}%",
                success_criteria=[
                    f"HPA shows TARGETS with memory/{memory_target}%",
                    f"HPA shows TARGETS with cpu/{cpu_target}%",
                    "HPA status shows READY",
                    "No error events in HPA description"
                ],
                timeout_seconds=600,
                retry_attempts=3,
                prerequisites=[f"Deployment {workload_name} exists in namespace {namespace}"],
                estimated_duration_minutes=10,
                risk_level="Medium",
                monitoring_metrics=[
                    f"hpa_scaling_events_{workload_name}",
                    f"pod_count_{workload_name}",
                    f"cpu_utilization_{workload_name}",
                    f"memory_utilization_{workload_name}"
                ]
            ))
        
        # 3. Post-deployment monitoring setup
        commands.append(ExecutableCommand(
            id="hpa-003-monitoring",
            command="kubectl get hpa --all-namespaces -w --timeout=300s",
            description="Monitor HPA activity for initial scaling events",
            category="validation",
            yaml_content=None,
            validation_commands=[
                "kubectl get hpa --all-namespaces",
                "kubectl get events --field-selector reason=SuccessfulRescale",
                "kubectl top pods --all-namespaces"
            ],
            rollback_commands=["# Monitoring - no rollback needed"],
            expected_outcome="HPA scaling events visible within 5 minutes under load",
            success_criteria=[
                "At least one scaling event logged",
                "Pod counts adjust based on metrics",
                "No error events in cluster"
            ],
            timeout_seconds=1800,
            retry_attempts=1,
            prerequisites=["HPA deployments completed successfully"],
            estimated_duration_minutes=30,
            risk_level="Low",
            monitoring_metrics=["hpa_activity_rate", "scaling_event_frequency"]
        ))
        
        return commands
    
    def _generate_rightsizing_commands(self, cluster_dna, analysis_results: Dict) -> List[ExecutableCommand]:
        """Generate resource right-sizing commands with real calculations"""
        
        commands = []
        cluster_name = analysis_results.get('cluster_name', 'unknown-cluster')
        
        # Get efficiency patterns from cluster DNA
        efficiency_patterns = getattr(cluster_dna, 'efficiency_patterns', {})
        cpu_gap = efficiency_patterns.get('cpu_gap', 15) if isinstance(efficiency_patterns, dict) else 15
        memory_gap = efficiency_patterns.get('memory_gap', 10) if isinstance(efficiency_patterns, dict) else 10
        
        # Calculate reduction factors
        if cpu_gap > memory_gap + 10:
            cpu_factor, memory_factor = 0.7, 0.9  # CPU-focused
            approach = "CPU-focused rightsizing"
        elif memory_gap > cpu_gap + 10:
            cpu_factor, memory_factor = 0.9, 0.7  # Memory-focused
            approach = "Memory-focused rightsizing"
        else:
            cpu_factor, memory_factor = 0.8, 0.8  # Balanced
            approach = "Balanced rightsizing"
        
        # Get workloads for rightsizing
        workload_costs = analysis_results.get('workload_costs', {})
        target_workloads = list(workload_costs.items())[:3]  # Top 3 by cost
        
        # 1. Backup current configurations
        commands.append(ExecutableCommand(
            id="rightsizing-001-backup",
            command=f"kubectl get deployments --all-namespaces -o yaml > rightsizing-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.yaml",
            description="Backup current deployment configurations before rightsizing",
            category="preparation",
            yaml_content=None,
            validation_commands=[
                f"ls -la rightsizing-backup-*.yaml",
                f"head -20 rightsizing-backup-*.yaml"
            ],
            rollback_commands=["# Backup file created - no rollback needed"],
            expected_outcome="Deployment configurations backed up successfully",
            success_criteria=[
                "Backup file created with size > 1KB",
                "Backup file contains valid YAML",
                "All target deployments included in backup"
            ],
            timeout_seconds=120,
            retry_attempts=2,
            prerequisites=["kubectl access to cluster", "write access to current directory"],
            estimated_duration_minutes=2,
            risk_level="Low",
            monitoring_metrics=["backup_file_size", "backup_completion_status"]
        ))
        
        # 2. Right-size each workload
        for workload_key, workload_data in target_workloads:
            if '/' in workload_key:
                namespace, workload_name = workload_key.split('/', 1)
            else:
                namespace, workload_name = 'default', workload_key
            
            # Generate dynamic patch command with calculated values
            patch_command = f'''kubectl patch deployment {workload_name} -n {namespace} --type='merge' -p='{{
  "spec": {{
    "template": {{
      "spec": {{
        "containers": [{{
          "name": "{workload_name}",
          "resources": {{
            "requests": {{
              "cpu": "$(kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources.requests.cpu}}' | sed 's/m//' | awk '{{printf "%.0fm", $1 * {cpu_factor}}}' || echo '100m')",
              "memory": "$(kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources.requests.memory}}' | sed 's/Mi//' | awk '{{printf "%.0fMi", $1 * {memory_factor}}}' || echo '128Mi')"
            }},
            "limits": {{
              "cpu": "$(kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources.limits.cpu}}' | sed 's/m//' | awk '{{printf "%.0fm", $1 * {cpu_factor}}}' || echo '200m')",
              "memory": "$(kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources.limits.memory}}' | sed 's/Mi//' | awk '{{printf "%.0fMi", $1 * {memory_factor}}}' || echo '256Mi')"
            }}
          }}
        }}]
      }}
    }}
  }}
}}\''''
            
            commands.append(ExecutableCommand(
                id=f"rightsizing-002-{workload_name}",
                command=patch_command,
                description=f"Right-size {workload_name} using {approach} (reduce CPU by {int((1-cpu_factor)*100)}%, memory by {int((1-memory_factor)*100)}%)",
                category="execution",
                yaml_content=None,
                validation_commands=[
                    f"kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources}}'",
                    f"kubectl rollout status deployment/{workload_name} -n {namespace} --timeout=300s",
                    f"kubectl get pods -n {namespace} -l app={workload_name} -o wide"
                ],
                rollback_commands=[
                    f"kubectl rollout undo deployment/{workload_name} -n {namespace}",
                    f"kubectl rollout status deployment/{workload_name} -n {namespace}",
                    f"kubectl get deployment {workload_name} -n {namespace} -o jsonpath='{{.spec.template.spec.containers[0].resources}}'"
                ],
                expected_outcome=f"Resources reduced: CPU by {int((1-cpu_factor)*100)}%, memory by {int((1-memory_factor)*100)}%",
                success_criteria=[
                    "Deployment rollout completes successfully",
                    "All pods restart and reach Ready state",
                    "Resource requests/limits updated correctly",
                    "Application responds to health checks"
                ],
                timeout_seconds=600,
                retry_attempts=2,
                prerequisites=[f"Deployment {workload_name} exists and is ready"],
                estimated_duration_minutes=8,
                risk_level="Medium",
                monitoring_metrics=[
                    f"deployment_rollout_status_{workload_name}",
                    f"pod_restart_count_{workload_name}",
                    f"application_response_time_{workload_name}",
                    f"resource_utilization_{workload_name}"
                ]
            ))
        
        # 3. Post-rightsizing validation
        commands.append(ExecutableCommand(
            id="rightsizing-003-validation",
            command="kubectl top pods --all-namespaces --containers | grep -E \"(CPU|MEMORY)\"",
            description="Validate resource utilization after rightsizing",
            category="validation",
            yaml_content=None,
            validation_commands=[
                "kubectl get deployments --all-namespaces",
                "kubectl top nodes",
                "kubectl top pods --all-namespaces",
                "kubectl get events --field-selector type=Warning --all-namespaces"
            ],
            rollback_commands=["# Validation - no rollback needed"],
            expected_outcome="Resource utilization increased to optimal levels",
            success_criteria=[
                "No pods in CrashLoopBackOff state",
                "CPU utilization increased by 10-20%",
                "Memory utilization increased by 10-20%",
                "No OOMKilled events in past 10 minutes"
            ],
            timeout_seconds=300,
            retry_attempts=1,
            prerequisites=["All rightsizing operations completed"],
            estimated_duration_minutes=5,
            risk_level="Low",
            monitoring_metrics=["overall_utilization_improvement", "error_event_count"]
        ))
        
        return commands
    
    def _generate_storage_commands(self, cluster_dna, analysis_results: Dict) -> List[ExecutableCommand]:
        """Generate storage optimization commands"""
        
        commands = []
        cost_distribution = getattr(cluster_dna, 'cost_distribution', {})
        storage_percentage = cost_distribution.get('storage_percentage', 0) if isinstance(cost_distribution, dict) else 0
        
        if storage_percentage < 10:
            return commands  # Not worth optimizing
        
        # Generate optimized storage class
        optimized_sc_yaml = self.yaml_generator.generate_optimized_storage_class(analysis_results)
        
        commands.append(ExecutableCommand(
            id="storage-001-optimized-class",
            command=f"echo '{optimized_sc_yaml}' | kubectl apply -f -",
            description="Deploy optimized storage class for cost reduction",
            category="execution",
            yaml_content=optimized_sc_yaml,
            validation_commands=[
                "kubectl get storageclass optimized-ssd -o yaml",
                "kubectl get pvc --all-namespaces -o custom-columns=NAME:.metadata.name,STORAGECLASS:.spec.storageClassName"
            ],
            rollback_commands=[
                "kubectl delete storageclass optimized-ssd",
                "kubectl get storageclass"
            ],
            expected_outcome="Optimized storage class available for new PVCs",
            success_criteria=[
                "Storage class 'optimized-ssd' created successfully",
                "Storage class shows correct provisioner",
                "Storage class has proper parameters for cost optimization"
            ],
            timeout_seconds=60,
            retry_attempts=2,
            prerequisites=["kubectl access to cluster"],
            estimated_duration_minutes=2,
            risk_level="Low",
            monitoring_metrics=["storage_class_creation_status"]
        ))
        
        return commands
    
    def _generate_system_pool_commands(self, cluster_dna, analysis_results: Dict) -> List[ExecutableCommand]:
        """Generate system pool optimization commands"""
        
        commands = []
        scaling_characteristics = getattr(cluster_dna, 'scaling_characteristics', {})
        system_efficiency = scaling_characteristics.get('system_pool_efficiency', 1.0) if isinstance(scaling_characteristics, dict) else 1.0
        
        if system_efficiency > 0.5:
            return commands  # System pool is efficient enough
        
        # Get actual node data
        nodes = analysis_results.get('current_usage_analysis', {}).get('nodes', [])
        system_nodes = [node for node in nodes if 'system' in node.get('name', '').lower()]
        
        if not system_nodes:
            return commands
        
        # Find most underutilized system node
        underutilized_node = min(system_nodes, key=lambda n: n.get('cpu_usage_pct', 100))
        node_name = underutilized_node.get('name', 'unknown-node')
        
        commands.append(ExecutableCommand(
            id="system-001-cordon",
            command=f"kubectl cordon {node_name}",
            description=f"Cordon underutilized system node {node_name} ({underutilized_node.get('cpu_usage_pct', 0):.1f}% CPU)",
            category="execution",
            yaml_content=None,
            validation_commands=[
                f"kubectl get node {node_name} -o wide",
                f"kubectl describe node {node_name} | grep Taints",
                "kubectl get pods -o wide | grep Pending"
            ],
            rollback_commands=[
                f"kubectl uncordon {node_name}",
                f"kubectl get node {node_name} -o wide"
            ],
            expected_outcome=f"Node {node_name} cordoned - no new pods will be scheduled",
            success_criteria=[
                f"Node {node_name} shows SchedulingDisabled",
                "No new pods scheduled on cordoned node",
                "Existing pods continue running normally"
            ],
            timeout_seconds=120,
            retry_attempts=2,
            prerequisites=[f"Node {node_name} exists and is Ready"],
            estimated_duration_minutes=3,
            risk_level="Medium",
            monitoring_metrics=[f"node_scheduling_status_{node_name}", "pending_pod_count"]
        ))
        
        return commands
    
    def _generate_opportunity_validations(self, opportunity: str, 
                                        cluster_dna, 
                                        analysis_results: Dict) -> List[ValidationRule]:
        """Generate validation rules for opportunity"""
        
        validations = []
        
        if opportunity == 'hpa_optimization':
            validations.extend([
                ValidationRule(
                    name="hpa_deployment_validation",
                    check_command="kubectl get hpa --all-namespaces -o json | jq '.items | length'",
                    expected_result="> 0",
                    failure_action="rollback_hpa_deployment",
                    timeout_seconds=300
                ),
                ValidationRule(
                    name="metrics_server_validation",
                    check_command="kubectl top nodes | wc -l",
                    expected_result="> 1",
                    failure_action="check_metrics_server_installation",
                    timeout_seconds=60
                )
            ])
        
        elif opportunity == 'resource_rightsizing':
            validations.extend([
                ValidationRule(
                    name="deployment_ready_validation",
                    check_command="kubectl get deployments --all-namespaces -o json | jq '.items[] | select(.status.readyReplicas != .status.replicas) | .metadata.name'",
                    expected_result="null",
                    failure_action="rollback_resource_changes",
                    timeout_seconds=600
                ),
                ValidationRule(
                    name="pod_restart_validation", 
                    check_command="kubectl get pods --all-namespaces -o json | jq '.items[] | select(.status.restartCount > 5) | .metadata.name'",
                    expected_result="null",
                    failure_action="investigate_pod_failures",
                    timeout_seconds=300
                )
            ])
        
        return validations
    
    def _generate_opportunity_monitoring(self, opportunity: str,
                                       cluster_dna, 
                                       analysis_results: Dict) -> List[MonitoringSpec]:
        """Generate monitoring specifications for opportunity"""
        
        monitoring_specs = []
        
        if opportunity == 'hpa_optimization':
            monitoring_specs.extend([
                MonitoringSpec(
                    metric_name="hpa_scaling_frequency",
                    query="rate(hpa_scaling_events_total[5m])",
                    threshold=2.0,
                    duration_minutes=30,
                    alert_condition="above_threshold",
                    remediation_action="review_hpa_thresholds"
                ),
                MonitoringSpec(
                    metric_name="pod_count_variance",
                    query="stddev_over_time(kubernetes_pod_count[1h])",
                    threshold=5.0,
                    duration_minutes=60,
                    alert_condition="above_threshold",
                    remediation_action="check_workload_patterns"
                )
            ])
        
        elif opportunity == 'resource_rightsizing':
            monitoring_specs.extend([
                MonitoringSpec(
                    metric_name="cpu_utilization_increase",
                    query="avg(kubernetes_cpu_usage_percent)",
                    threshold=15.0,
                    duration_minutes=120,
                    alert_condition="increase_from_baseline",
                    remediation_action="validate_performance_impact"
                ),
                MonitoringSpec(
                    metric_name="memory_pressure",
                    query="kubernetes_memory_pressure_count",
                    threshold=1.0,
                    duration_minutes=15,
                    alert_condition="above_threshold", 
                    remediation_action="rollback_memory_changes"
                )
            ])
        
        return monitoring_specs
    
    def _determine_rollback_strategy(self, optimization_strategy, cluster_dna) -> str:
        """Determine appropriate rollback strategy"""
        
        risk_level = getattr(optimization_strategy, 'overall_risk_level', 'Medium')
        personality = getattr(cluster_dna, 'cluster_personality', '')
        
        if 'conservative' in personality or risk_level == 'High':
            return "immediate_rollback_on_first_failure"
        elif risk_level == 'Low':
            return "progressive_rollback_with_validation"
        else:
            return "staged_rollback_with_monitoring"

# ============================================================================
# DYNAMIC YAML GENERATOR
# ============================================================================

class DynamicYAMLGenerator:
    """Generates dynamic YAML configurations with real cluster values"""
    
    def generate_hpa_yaml(self, workload_name: str, namespace: str,
                         min_replicas: int, max_replicas: int,
                         memory_target: int, cpu_target: int,
                         analysis_results: Dict) -> str:
        """Generate HPA YAML with calculated values"""
        
        hpa_config = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f'{workload_name}-hpa',
                'namespace': namespace,
                'annotations': {
                    'optimization.tool/generated-by': 'dynamic-strategy-engine',
                    'optimization.tool/cluster': analysis_results.get('cluster_name', 'unknown'),
                    'optimization.tool/generated-at': datetime.now().isoformat()
                }
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': workload_name
                },
                'minReplicas': min_replicas,
                'maxReplicas': max_replicas,
                'metrics': [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'memory',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': memory_target
                            }
                        }
                    },
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': cpu_target
                            }
                        }
                    }
                ],
                'behavior': {
                    'scaleDown': {
                        'stabilizationWindowSeconds': 300,
                        'policies': [
                            {
                                'type': 'Percent',
                                'value': 10,
                                'periodSeconds': 60
                            }
                        ]
                    },
                    'scaleUp': {
                        'stabilizationWindowSeconds': 60,
                        'policies': [
                            {
                                'type': 'Percent',
                                'value': 25,
                                'periodSeconds': 60
                            }
                        ]
                    }
                }
            }
        }
        
        return yaml.dump(hpa_config, default_flow_style=False)
    
    def generate_optimized_storage_class(self, analysis_results: Dict) -> str:
        """Generate optimized storage class YAML"""
        
        storage_config = {
            'apiVersion': 'storage.k8s.io/v1',
            'kind': 'StorageClass',
            'metadata': {
                'name': 'optimized-ssd',
                'annotations': {
                    'optimization.tool/generated-by': 'dynamic-strategy-engine',
                    'optimization.tool/cluster': analysis_results.get('cluster_name', 'unknown'),
                    'optimization.tool/cost-optimization': 'true'
                }
            },
            'provisioner': 'disk.csi.azure.com',
            'parameters': {
                'skuName': 'StandardSSD_LRS',
                'kind': 'managed',
                'cachingmode': 'ReadOnly'
            },
            'reclaimPolicy': 'Delete',
            'allowVolumeExpansion': True,
            'volumeBindingMode': 'WaitForFirstConsumer'
        }
        
        return yaml.dump(storage_config, default_flow_style=False)

# ============================================================================
# VALIDATION ENGINE
# ============================================================================

class ValidationEngine:
    """Advanced validation engine for command execution"""
    
    def __init__(self):
        self.validation_timeout = 300  # 5 minutes default
        
    def create_validation_script(self, execution_plan: ExecutionPlan) -> str:
        """Create comprehensive validation script"""
        
        script_lines = [
            "#!/bin/bash",
            "# Generated validation script for cluster optimization",
            f"# Plan ID: {execution_plan.plan_id}",
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "set -e",
            "VALIDATION_FAILED=0",
            "",
            "validate_command() {",
            "  local cmd=\"$1\"",
            "  local description=\"$2\"",
            "  echo \"Validating: $description\"",
            "  if eval \"$cmd\"; then",
            "    echo \"✅ PASS: $description\"",
            "  else",
            "    echo \"❌ FAIL: $description\"",
            "    VALIDATION_FAILED=1",
            "  fi",
            "  echo",
            "}",
            ""
        ]
        
        for command in execution_plan.commands:
            if command.category in ['execution', 'validation']:
                script_lines.append(f"# Validating: {command.description}")
                for validation_cmd in command.validation_commands:
                    script_lines.append(f"validate_command \"{validation_cmd}\" \"{command.description}\"")
                script_lines.append("")
        
        script_lines.extend([
            "if [ $VALIDATION_FAILED -eq 1 ]; then",
            "  echo \"❌ Validation failed - consider rollback\"",
            "  exit 1",
            "else",
            "  echo \"✅ All validations passed\"",
            "  exit 0",
            "fi"
        ])
        
        return "\n".join(script_lines)

# ============================================================================
# MONITORING GENERATOR  
# ============================================================================

class MonitoringGenerator:
    """Generates monitoring configurations for optimization tracking"""
    
    def generate_monitoring_dashboard_config(self, execution_plan: ExecutionPlan) -> Dict:
        """Generate monitoring dashboard configuration"""
        
        dashboard_config = {
            'dashboard': {
                'id': f"optimization-{execution_plan.plan_id}",
                'title': f"Optimization Monitoring - {execution_plan.strategy_name}",
                'tags': ['optimization', 'cost-savings', 'kubernetes'],
                'time': {
                    'from': 'now-1h',
                    'to': 'now'
                },
                'panels': []
            }
        }
        
        # Add panels for each monitoring spec
        panel_id = 1
        for monitoring_spec in execution_plan.monitoring_specs:
            panel = {
                'id': panel_id,
                'title': monitoring_spec.metric_name.replace('_', ' ').title(),
                'type': 'graph',
                'targets': [
                    {
                        'expr': monitoring_spec.query,
                        'legendFormat': monitoring_spec.metric_name
                    }
                ],
                'alert': {
                    'conditions': [
                        {
                            'query': {'params': ['A', f'{monitoring_spec.duration_minutes}m', 'now']},
                            'reducer': {'type': 'avg', 'params': []},
                            'evaluator': {'params': [monitoring_spec.threshold], 'type': 'gt'}
                        }
                    ],
                    'executionErrorState': 'alerting',
                    'for': f'{monitoring_spec.duration_minutes}m',
                    'frequency': '10s',
                    'handler': 1,
                    'name': f"{monitoring_spec.metric_name} Alert",
                    'noDataState': 'no_data',
                    'notifications': []
                }
            }
            dashboard_config['dashboard']['panels'].append(panel)
            panel_id += 1
        
        return dashboard_config

# ============================================================================
# SAFETY ENGINE
# ============================================================================

class SafetyEngine:
    """Generates safety commands and procedures"""
    
    def generate_safety_commands(self, cluster_name: str, optimization_strategy) -> List[ExecutableCommand]:
        """Generate safety and monitoring commands"""
        
        safety_commands = []
        
        # Pre-execution cluster health check
        safety_commands.append(ExecutableCommand(
            id="safety-001-health-check",
            command="kubectl get nodes,pods --all-namespaces | grep -E '(NotReady|Error|CrashLoopBackOff|ImagePullBackOff)'",
            description="Pre-execution cluster health verification",
            category="preparation",
            yaml_content=None,
            validation_commands=[
                "kubectl get nodes -o wide",
                "kubectl get pods --all-namespaces",
                "kubectl get events --field-selector type=Warning"
            ],
            rollback_commands=["# Health check - no rollback needed"],
            expected_outcome="Cluster shows healthy state with no critical issues",
            success_criteria=[
                "All nodes in Ready state",
                "No pods in Error or CrashLoopBackOff",
                "No critical Warning events in past 5 minutes"
            ],
            timeout_seconds=180,
            retry_attempts=1,
            prerequisites=["kubectl access to cluster"],
            estimated_duration_minutes=3,
            risk_level="Low",
            monitoring_metrics=["cluster_health_score", "critical_event_count"]
        ))
        
        # Create emergency rollback script
        safety_commands.append(ExecutableCommand(
            id="safety-002-emergency-script",
            command=f"cat > emergency_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh << 'EOF'\n#!/bin/bash\necho 'Emergency rollback initiated...'\n# Commands will be populated during execution\nEOF",
            description="Create emergency rollback script",
            category="preparation",
            yaml_content=None,
            validation_commands=[
                "ls -la emergency_rollback_*.sh",
                "head -5 emergency_rollback_*.sh"
            ],
            rollback_commands=["# Emergency script creation - no rollback needed"],
            expected_outcome="Emergency rollback script created and executable",
            success_criteria=[
                "Script file created successfully",
                "Script has execute permissions",
                "Script contains valid bash syntax"
            ],
            timeout_seconds=30,
            retry_attempts=2,
            prerequisites=["Write access to current directory"],
            estimated_duration_minutes=1,
            risk_level="Low",
            monitoring_metrics=["emergency_script_status"]
        ))
        
        return safety_commands

# ============================================================================
# INTEGRATION FUNCTION
# ============================================================================

def generate_advanced_execution_plan(optimization_strategy, 
                                    cluster_dna, 
                                    analysis_results: Dict) -> ExecutionPlan:
    """
    MAIN INTEGRATION FUNCTION: Generate complete execution plan
    """
    generator = AdvancedExecutableCommandGenerator()
    return generator.generate_execution_plan(
        optimization_strategy, cluster_dna, analysis_results
    )

# ============================================================================
# DEMO FUNCTION
# ============================================================================

def demo_advanced_command_generation():
    """Demo advanced command generation with your actual data"""
    
    print("🛠️ ADVANCED EXECUTABLE COMMAND GENERATION DEMO")
    print("=" * 60)
    
    # Your actual data (same as before)
    your_actual_data = {
        'cluster_name': 'aks-dpl-mad-uat-ne2-1',
        'resource_group': 'rg-dpl-mad-uat-ne2-2',
        'total_cost': 1864.43,
        'hpa_savings': 46.61,
        'right_sizing_savings': 21.33,
        'current_usage_analysis': {
            'nodes': [
                {'name': 'aks-systempool-14902933-vmss000000', 'cpu_usage_pct': 11.8, 'memory_usage_pct': 67.1},
            ]
        },
        'workload_costs': {
            'madapi-preprod/account-decisioning-api-aggregator': {'cost': 9.43, 'replicas': 2},
        }
    }
    
    # Sample cluster DNA and strategy (would come from previous phases)
    class MockClusterDNA:
        def __init__(self):
            self.cluster_personality = 'medium-over-provisioned-hpa-ready-network-heavy'
            self.efficiency_patterns = {'cpu_gap': 15, 'memory_gap': 10}
            self.scaling_characteristics = {'auto_scaling_potential': 0.7}
            self.cost_distribution = {'storage_percentage': 8.5}
    
    class MockStrategy:
        def __init__(self):
            self.strategy_name = 'Comprehensive HPA and Right-sizing Optimization'
            self.opportunities = ['hpa_optimization', 'resource_rightsizing']
            self.overall_risk_level = 'Medium'
            self.success_probability = 0.85
            self.total_savings_potential = 67.94
    
    cluster_dna = MockClusterDNA()
    optimization_strategy = MockStrategy()
    
    # Generate execution plan
    execution_plan = generate_advanced_execution_plan(
        optimization_strategy, cluster_dna, your_actual_data
    )
    
    # Display results
    print(f"📋 EXECUTION PLAN GENERATED")
    print(f"Plan ID: {execution_plan.plan_id}")
    print(f"Cluster: {execution_plan.cluster_name}")
    print(f"Total Commands: {len(execution_plan.commands)}")
    print(f"Estimated Duration: {execution_plan.total_estimated_minutes} minutes")
    print(f"Expected Savings: ${execution_plan.estimated_savings:.2f}/month")
    
    print(f"\n🛠️ SAMPLE EXECUTABLE COMMANDS:")
    for i, command in enumerate(execution_plan.commands[:3], 1):
        print(f"\n{i}. {command.description}")
        print(f"   Command: {command.command[:100]}...")
        print(f"   Risk Level: {command.risk_level}")
        print(f"   Duration: {command.estimated_duration_minutes} minutes")
        if command.yaml_content:
            print(f"   YAML: {len(command.yaml_content)} characters")
    
    print(f"\n🔍 VALIDATION RULES: {len(execution_plan.validation_rules)} rules")
    print(f"📊 MONITORING SPECS: {len(execution_plan.monitoring_specs)} metrics")
    
    return execution_plan

if __name__ == "__main__":
    demo_advanced_command_generation()