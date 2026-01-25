#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
CPU Optimization Plan Generator with Executable Commands
=======================================================
Generates comprehensive CPU optimization plans with real executable commands
for addressing high CPU scenarios like the 806% average and 2359% peak CPU issues.
"""

import json
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import os
import subprocess

logger = logging.getLogger(__name__)

class CPUOptimizationScenario(Enum):
    """CPU optimization scenarios"""
    CRITICAL_OVERUTILIZATION = "critical_overutilization"  # >200% CPU
    HIGH_USAGE = "high_usage"  # 80-200% CPU
    INEFFICIENT_ALLOCATION = "inefficient_allocation"  # Poor request/limit ratios
    WORKLOAD_IMBALANCE = "workload_imbalance"  # Uneven distribution
    RESOURCE_CONTENTION = "resource_contention"  # Multiple pods competing
    SCALING_ISSUES = "scaling_issues"  # HPA/VPA not configured properly

@dataclass
class OptimizationCommand:
    """Represents an executable optimization command"""
    command: str
    description: str
    execution_order: int
    risk_level: str  # low, medium, high
    prerequisite_commands: List[str] = field(default_factory=list)
    validation_command: Optional[str] = None
    rollback_command: Optional[str] = None
    estimated_impact: str = ""
    category: str = "general"

@dataclass
class CPUOptimizationPlan:
    """Complete CPU optimization plan"""
    cluster_id: str
    scenario: CPUOptimizationScenario
    severity_level: str
    current_metrics: Dict[str, Any]
    optimization_commands: List[OptimizationCommand]
    monitoring_commands: List[str]
    validation_steps: List[str]
    estimated_savings: Dict[str, Any]
    timeline: str
    created_at: datetime = field(default_factory=datetime.now)

class CPUOptimizationPlanner:
    """Generates comprehensive CPU optimization plans with executable commands"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.kubectl_context = None
        self.cluster_config = {}
        self.optimization_config = config or {}
        
        # Default configurable thresholds - can be overridden per organization
        self.thresholds = {
            'critical_cpu': self.optimization_config.get('critical_cpu_threshold', 200),
            'high_cpu': self.optimization_config.get('high_cpu_threshold', 80),
            'target_cpu': self.optimization_config.get('target_cpu_utilization', 70),
            'efficiency_low': self.optimization_config.get('low_efficiency_threshold', 50),
            'efficiency_target': self.optimization_config.get('target_efficiency', 80),
            'peak_critical': self.optimization_config.get('peak_critical_threshold', 400),
            'peak_high': self.optimization_config.get('peak_high_threshold', 150)
        }
        
    def generate_optimization_plan(self, 
                                 cluster_id: str, 
                                 cpu_metrics: Dict[str, Any],
                                 cluster_config: Dict[str, Any] = None) -> CPUOptimizationPlan:
        """Generate comprehensive CPU optimization plan with executable commands"""
        
        try:
            logger.info(f"🔧 Generating CPU optimization plan for cluster: {cluster_id}")
            
            # Analyze CPU metrics to determine scenario
            scenario = self._determine_optimization_scenario(cpu_metrics)
            severity_level = self._calculate_severity_level(cpu_metrics)
            
            # Set cluster context
            self.cluster_config = cluster_config or {}
            self._set_kubectl_context(cluster_id)
            
            # Generate optimization commands based on scenario
            optimization_commands = self._generate_optimization_commands(scenario, cpu_metrics, cluster_id)
            
            # Generate monitoring and validation commands
            monitoring_commands = self._generate_monitoring_commands(cluster_id)
            validation_steps = self._generate_validation_steps(scenario, cluster_id)
            
            # Calculate estimated savings
            estimated_savings = self._calculate_estimated_savings(cpu_metrics, scenario)
            
            # Determine implementation timeline
            timeline = self._calculate_implementation_timeline(scenario, len(optimization_commands))
            
            plan = CPUOptimizationPlan(
                cluster_id=cluster_id,
                scenario=scenario,
                severity_level=severity_level,
                current_metrics=cpu_metrics,
                optimization_commands=optimization_commands,
                monitoring_commands=monitoring_commands,
                validation_steps=validation_steps,
                estimated_savings=estimated_savings,
                timeline=timeline
            )
            
            logger.info(f"✅ Generated optimization plan with {len(optimization_commands)} commands")
            return plan
            
        except Exception as e:
            logger.error(f"❌ Failed to generate optimization plan: {e}")
            raise
    
    def _determine_optimization_scenario(self, cpu_metrics: Dict[str, Any]) -> CPUOptimizationScenario:
        """Determine the optimization scenario based on configurable CPU metrics thresholds"""
        
        avg_cpu = cpu_metrics.get('average_cpu_usage', 0)
        peak_cpu = cpu_metrics.get('peak_cpu_usage', 0)
        cpu_efficiency = cpu_metrics.get('cpu_efficiency', 100)
        
        # Critical overutilization - configurable threshold
        if avg_cpu > self.thresholds['critical_cpu'] or peak_cpu > self.thresholds['peak_critical']:
            return CPUOptimizationScenario.CRITICAL_OVERUTILIZATION
        
        # High usage scenarios - configurable threshold
        elif avg_cpu > self.thresholds['high_cpu'] or peak_cpu > self.thresholds['peak_high']:
            return CPUOptimizationScenario.HIGH_USAGE
        
        # Inefficient allocation - configurable efficiency threshold
        elif cpu_efficiency < self.thresholds['efficiency_low']:
            return CPUOptimizationScenario.INEFFICIENT_ALLOCATION
        
        # Workload imbalance - check for high variance in usage
        elif self._detect_workload_imbalance(cpu_metrics):
            return CPUOptimizationScenario.WORKLOAD_IMBALANCE
        
        # Resource contention - multiple pods competing
        elif self._detect_resource_contention(cpu_metrics):
            return CPUOptimizationScenario.RESOURCE_CONTENTION
        
        # Default to scaling issues
        else:
            return CPUOptimizationScenario.SCALING_ISSUES
    
    def _detect_workload_imbalance(self, cpu_metrics: Dict[str, Any]) -> bool:
        """Detect workload imbalance across nodes"""
        # Check if there's significant variance in node utilization
        nodes_data = cpu_metrics.get('nodes_utilization', [])
        if len(nodes_data) < 2:
            return False
        
        utilizations = [node.get('cpu_usage_pct', 0) for node in nodes_data]
        if not utilizations:
            return False
        
        avg_util = sum(utilizations) / len(utilizations)
        variance = sum((u - avg_util) ** 2 for u in utilizations) / len(utilizations)
        
        # High variance indicates imbalance
        return variance > 300  # Configurable threshold
    
    def _detect_resource_contention(self, cpu_metrics: Dict[str, Any]) -> bool:
        """Detect resource contention scenarios"""
        high_cpu_workloads = cpu_metrics.get('high_cpu_workloads', 0)
        total_pods = cpu_metrics.get('total_pods', 0)
        
        # High percentage of pods with CPU issues indicates contention
        if total_pods > 0:
            contention_ratio = high_cpu_workloads / total_pods
            return contention_ratio > 0.3  # 30% of pods having CPU issues
        
        return False
    
    def _calculate_severity_level(self, cpu_metrics: Dict[str, Any]) -> str:
        """Calculate severity level based on configurable CPU metrics thresholds"""
        
        avg_cpu = cpu_metrics.get('average_cpu_usage', 0)
        peak_cpu = cpu_metrics.get('peak_cpu_usage', 0)
        
        # Configurable severity thresholds
        critical_multiplier = self.thresholds['critical_cpu'] * 1.5  # 1.5x critical threshold
        high_multiplier = self.thresholds['critical_cpu'] * 0.75    # 0.75x critical threshold
        
        if avg_cpu > critical_multiplier or peak_cpu > (self.thresholds['peak_critical'] * 2.5):
            return "CRITICAL"
        elif avg_cpu > self.thresholds['critical_cpu'] or peak_cpu > self.thresholds['peak_critical']:
            return "HIGH"
        elif avg_cpu > self.thresholds['high_cpu'] or peak_cpu > self.thresholds['peak_high']:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _set_kubectl_context(self, cluster_id: str):
        """Set kubectl context for the cluster"""
        try:
            # Extract context from cluster_id (format: subscription-resourcegroup-cluster)
            parts = cluster_id.split('-')
            if len(parts) >= 3:
                resource_group = '-'.join(parts[1:-1])
                cluster_name = parts[-1]
                self.kubectl_context = f"{cluster_name}"
                logger.info(f"🔧 Set kubectl context: {self.kubectl_context}")
        except Exception as e:
            logger.warning(f"⚠️ Could not determine kubectl context: {e}")
            self.kubectl_context = "current-context"
    
    def _generate_optimization_commands(self, 
                                      scenario: CPUOptimizationScenario, 
                                      cpu_metrics: Dict[str, Any],
                                      cluster_id: str) -> List[OptimizationCommand]:
        """Generate optimization commands based on scenario"""
        
        commands = []
        
        # Common assessment commands
        commands.extend(self._get_assessment_commands(cluster_id))
        
        if scenario == CPUOptimizationScenario.CRITICAL_OVERUTILIZATION:
            commands.extend(self._get_critical_overutilization_commands(cpu_metrics, cluster_id))
        
        elif scenario == CPUOptimizationScenario.HIGH_USAGE:
            commands.extend(self._get_high_usage_commands(cpu_metrics, cluster_id))
        
        elif scenario == CPUOptimizationScenario.INEFFICIENT_ALLOCATION:
            commands.extend(self._get_inefficient_allocation_commands(cpu_metrics, cluster_id))
        
        elif scenario == CPUOptimizationScenario.SCALING_ISSUES:
            commands.extend(self._get_scaling_optimization_commands(cpu_metrics, cluster_id))
        
        # Add monitoring and cleanup commands
        commands.extend(self._get_post_optimization_commands(cluster_id))
        
        return sorted(commands, key=lambda x: x.execution_order)
    
    def _get_assessment_commands(self, cluster_id: str) -> List[OptimizationCommand]:
        """Get initial assessment commands - generic for any Kubernetes cluster"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        return [
            OptimizationCommand(
                command=f"kubectl top nodes {context_flag}",
                description="Check current node resource utilization across all nodes",
                execution_order=1,
                risk_level="low",
                category="assessment",
                estimated_impact="Baseline understanding of cluster resource usage"
            ),
            OptimizationCommand(
                command=f"kubectl top pods --all-namespaces --sort-by=cpu {context_flag}",
                description="Identify top CPU consuming pods across all namespaces",
                execution_order=2,
                risk_level="low",
                category="assessment",
                estimated_impact="Identify specific workloads causing high CPU usage"
            ),
            OptimizationCommand(
                command=f"kubectl get pods --all-namespaces -o wide --field-selector=status.phase=Running {context_flag}",
                description="List all running pods and their node assignments",
                execution_order=3,
                risk_level="low",
                category="assessment",
                estimated_impact="Understand workload distribution across cluster"
            ),
            OptimizationCommand(
                command=f"kubectl describe nodes {context_flag} | grep -A 5 'Allocated resources'",
                description="Check resource requests vs capacity on all nodes",
                execution_order=4,
                risk_level="low",
                category="assessment",
                estimated_impact="Identify over/under-provisioned nodes"
            ),
            OptimizationCommand(
                command=f"kubectl get limitrange --all-namespaces {context_flag}",
                description="Review existing resource limits and quotas",
                execution_order=5,
                risk_level="low",
                category="assessment",
                estimated_impact="Understand current resource governance policies"
            )
        ]
    
    def _get_critical_overutilization_commands(self, cpu_metrics: Dict[str, Any], cluster_id: str) -> List[OptimizationCommand]:
        """Commands for critical CPU overutilization scenarios - generic for any organization"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        # Calculate recommended CPU limits based on current usage
        avg_cpu = cpu_metrics.get('average_cpu_usage', 100)
        target_cpu_limit = min(max(int(avg_cpu * 0.3), 500), 2000)  # 30% of current usage, min 500m, max 2000m
        target_cpu_request = int(target_cpu_limit * 0.5)  # Request = 50% of limit
        
        return [
            # Immediate emergency actions
            OptimizationCommand(
                command=f"kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,CPU_REQUEST:.spec.containers[*].resources.requests.cpu,CPU_LIMIT:.spec.containers[*].resources.limits.cpu --sort-by=.metadata.namespace {context_flag}",
                description="EMERGENCY: Audit all pod CPU requests and limits",
                execution_order=10,
                risk_level="low",
                category="emergency_audit",
                estimated_impact="Identify pods without proper resource constraints"
            ),
            
            # Scale down non-critical workloads
            OptimizationCommand(
                command=f"kubectl get deployments --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,REPLICAS:.spec.replicas {context_flag}",
                description="Identify deployments for potential replica reduction",
                execution_order=11,
                risk_level="low",
                category="emergency_scaling",
                estimated_impact="Prepare for emergency scaling decisions"
            ),
            
            # Generic emergency pod resource limits template
            OptimizationCommand(
                command=f'''# TEMPLATE: Replace variables with actual values
# kubectl patch deployment <DEPLOYMENT_NAME> -n <NAMESPACE> -p '{{"spec":{{"template":{{"spec":{{"containers":[{{"name":"<CONTAINER_NAME>","resources":{{"limits":{{"cpu":"{target_cpu_limit}m"}},"requests":{{"cpu":"{target_cpu_request}m"}}}}}}]}}}}}}' {context_flag}
echo "Replace <DEPLOYMENT_NAME>, <NAMESPACE>, <CONTAINER_NAME> with actual values"''',
                description="TEMPLATE: Apply emergency CPU limits to high-consuming workloads",
                execution_order=15,
                risk_level="high",
                category="emergency_limits",
                estimated_impact=f"Constrain CPU usage to {target_cpu_limit}m limit, {target_cpu_request}m request",
                prerequisite_commands=["Identify specific high-CPU deployments first"],
                validation_command=f"kubectl top pods -n <NAMESPACE> {context_flag}"
            ),
            
            # Generic cloud provider node scaling template
            OptimizationCommand(
                command='''# TEMPLATE: Choose your cloud provider command
# For Azure AKS:
# az aks nodepool scale --cluster-name <CLUSTER_NAME> --name <NODEPOOL_NAME> --resource-group <RESOURCE_GROUP> --node-count <NEW_COUNT>
# For AWS EKS:
# aws eks update-nodegroup-config --cluster-name <CLUSTER_NAME> --nodegroup-name <NODEGROUP_NAME> --scaling-config minSize=<MIN>,maxSize=<MAX>,desiredSize=<DESIRED>
# For GCP GKE:
# gcloud container clusters resize <CLUSTER_NAME> --num-nodes=<NEW_COUNT> --zone=<ZONE>
echo "Replace variables with your cloud provider specific values"''',
                description="TEMPLATE: Scale node pool to distribute CPU load",
                execution_order=20,
                risk_level="medium",
                category="infrastructure_scaling",
                estimated_impact="Add compute capacity to handle overutilization",
                validation_command=f"kubectl get nodes {context_flag}"
            ),
            
            # Priority-based pod eviction
            OptimizationCommand(
                command=f"kubectl get pods --all-namespaces --sort-by=.metadata.creationTimestamp -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,PRIORITY:.spec.priority {context_flag}",
                description="Identify low-priority pods for potential eviction",
                execution_order=25,
                risk_level="medium",
                category="workload_management",
                estimated_impact="Free up CPU resources by evicting non-critical workloads"
            ),
            
            # Generic HPA template
            OptimizationCommand(
                command=f'''# TEMPLATE: Create HPA for deployment
# kubectl autoscale deployment <DEPLOYMENT_NAME> --cpu-percent={self.thresholds['target_cpu']} --min=<MIN_REPLICAS> --max=<MAX_REPLICAS> -n <NAMESPACE> {context_flag}
# Alternative YAML approach:
# cat <<EOF | kubectl apply -f - {context_flag}
# apiVersion: autoscaling/v2
# kind: HorizontalPodAutoscaler
# metadata:
#   name: <HPA_NAME>
#   namespace: <NAMESPACE>
# spec:
#   scaleTargetRef:
#     apiVersion: apps/v1
#     kind: Deployment
#     name: <DEPLOYMENT_NAME>
#   minReplicas: <MIN_REPLICAS>
#   maxReplicas: <MAX_REPLICAS>
#   metrics:
#   - type: Resource
#     resource:
#       name: cpu
#       target:
#         type: Utilization
#         averageUtilization: {self.thresholds['target_cpu']}
# EOF
echo "Replace placeholder values with your deployment details"''',
                description="TEMPLATE: Create Horizontal Pod Autoscaler for workloads",
                execution_order=30,
                risk_level="medium",
                category="autoscaling",
                estimated_impact=f"Enable automatic scaling at {self.thresholds['target_cpu']}% CPU target"
            ),
            
            # Generic resource quotas template
            OptimizationCommand(
                command=f'''# TEMPLATE: Create resource quota for namespace
# Calculate appropriate CPU quota based on namespace needs
NAMESPACE="<NAMESPACE>"
CPU_QUOTA="<CPU_LIMIT_CORES>"  # e.g., "10" for 10 CPU cores
MEMORY_QUOTA="<MEMORY_LIMIT>"  # e.g., "20Gi" for 20GB RAM

cat <<EOF | kubectl apply -f - {context_flag}
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: $NAMESPACE
spec:
  hard:
    requests.cpu: $CPU_QUOTA
    requests.memory: $MEMORY_QUOTA
    limits.cpu: $CPU_QUOTA
    limits.memory: $MEMORY_QUOTA
EOF
echo "Resource quota applied to namespace $NAMESPACE"''',
                description="TEMPLATE: Apply resource quotas to control CPU consumption",
                execution_order=35,
                risk_level="high",
                category="resource_governance",
                estimated_impact="Enforce CPU and memory limits at namespace level",
                validation_command=f"kubectl describe quota -n <NAMESPACE> {context_flag}"
            )
        ]
    
    def _get_high_usage_commands(self, cpu_metrics: Dict[str, Any], cluster_id: str) -> List[OptimizationCommand]:
        """Commands for high CPU usage optimization"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        return [
            OptimizationCommand(
                command=f"kubectl get hpa --all-namespaces {context_flag}",
                description="Check existing Horizontal Pod Autoscaler configurations",
                execution_order=10,
                risk_level="low",
                category="scaling_audit"
            ),
            
            OptimizationCommand(
                command=f'''kubectl autoscale deployment <DEPLOYMENT_NAME> --cpu-percent=70 --min=2 --max=20 --namespace=<NAMESPACE> {context_flag}''',
                description="TEMPLATE: Configure HPA for high-CPU workloads",
                execution_order=15,
                risk_level="medium",
                category="autoscaling",
                estimated_impact="Auto-scale pods based on CPU utilization"
            ),
            
            OptimizationCommand(
                command=f"kubectl get vpa --all-namespaces {context_flag} || echo 'VPA not installed'",
                description="Check Vertical Pod Autoscaler availability",
                execution_order=20,
                risk_level="low",
                category="scaling_audit"
            ),
            
            # Node affinity optimization
            OptimizationCommand(
                command=f"kubectl get nodes --show-labels {context_flag}",
                description="Review node labels for workload distribution",
                execution_order=25,
                risk_level="low",
                category="workload_distribution"
            ),
            
            # CPU request/limit optimization
            OptimizationCommand(
                command=f'''kubectl patch deployment <DEPLOYMENT_NAME> -n <NAMESPACE> -p '{{"spec":{{"template":{{"spec":{{"containers":[{{"name":"<CONTAINER_NAME>","resources":{{"limits":{{"cpu":"2000m"}},"requests":{{"cpu":"1000m"}}}}}}]}}}}}}' {context_flag}''',
                description="TEMPLATE: Optimize CPU requests and limits",
                execution_order=30,
                risk_level="medium",
                category="resource_tuning",
                estimated_impact="Right-size CPU allocation for workloads"
            )
        ]
    
    def _get_inefficient_allocation_commands(self, cpu_metrics: Dict[str, Any], cluster_id: str) -> List[OptimizationCommand]:
        """Commands for inefficient CPU allocation optimization"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        return [
            OptimizationCommand(
                command=f"kubectl describe nodes {context_flag} | grep -E '(Allocated resources|cpu|memory)'",
                description="Analyze resource allocation efficiency across nodes",
                execution_order=10,
                risk_level="low",
                category="efficiency_analysis"
            ),
            
            OptimizationCommand(
                command=f"kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,NODE:.spec.nodeName,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu {context_flag}",
                description="Review pod CPU requests vs limits ratios",
                execution_order=15,
                risk_level="low",
                category="efficiency_analysis"
            ),
            
            # Right-sizing recommendations
            OptimizationCommand(
                command=f"kubectl top pods --all-namespaces --sort-by=cpu --no-headers {context_flag} | head -20",
                description="Identify top CPU consumers for right-sizing",
                execution_order=20,
                risk_level="low",
                category="rightsizing"
            ),
            
            # Pod disruption budgets
            OptimizationCommand(
                command=f"kubectl get pdb --all-namespaces {context_flag}",
                description="Check Pod Disruption Budgets affecting scaling",
                execution_order=25,
                risk_level="low",
                category="scaling_constraints"
            )
        ]
    
    def _get_scaling_optimization_commands(self, cpu_metrics: Dict[str, Any], cluster_id: str) -> List[OptimizationCommand]:
        """Commands for scaling optimization"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        return [
            OptimizationCommand(
                command=f"kubectl get hpa --all-namespaces -o wide {context_flag}",
                description="Audit existing HPA configurations and targets",
                execution_order=10,
                risk_level="low",
                category="autoscaling_audit"
            ),
            
            OptimizationCommand(
                command=f"kubectl describe hpa --all-namespaces {context_flag}",
                description="Review HPA scaling events and behavior",
                execution_order=15,
                risk_level="low",
                category="autoscaling_audit"
            ),
            
            # Cluster autoscaler configuration
            OptimizationCommand(
                command="az aks show --resource-group <RESOURCE_GROUP> --name <CLUSTER_NAME> --query 'autoScalerProfile'",
                description="Check cluster autoscaler configuration",
                execution_order=20,
                risk_level="low",
                category="cluster_scaling"
            ),
            
            # Enable cluster autoscaler
            OptimizationCommand(
                command="az aks update --resource-group <RESOURCE_GROUP> --name <CLUSTER_NAME> --enable-cluster-autoscaler --min-count 1 --max-count 10",
                description="Enable cluster autoscaler for dynamic node scaling",
                execution_order=25,
                risk_level="medium",
                category="cluster_scaling",
                estimated_impact="Automatically scale nodes based on pod demands"
            )
        ]
    
    def _get_post_optimization_commands(self, cluster_id: str) -> List[OptimizationCommand]:
        """Commands for post-optimization monitoring and validation"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        return [
            OptimizationCommand(
                command=f"kubectl top nodes {context_flag}",
                description="Validate node CPU utilization after optimization",
                execution_order=90,
                risk_level="low",
                category="validation",
                estimated_impact="Confirm optimization effectiveness"
            ),
            
            OptimizationCommand(
                command=f"kubectl get events --sort-by=.metadata.creationTimestamp --all-namespaces {context_flag}",
                description="Monitor cluster events for scaling activities",
                execution_order=91,
                risk_level="low",
                category="monitoring"
            ),
            
            OptimizationCommand(
                command=f"kubectl get pods --all-namespaces --field-selector=status.phase!=Running {context_flag}",
                description="Check for any pods in non-running states",
                execution_order=92,
                risk_level="low",
                category="validation"
            ),
            
            OptimizationCommand(
                command="# Set up continuous monitoring with Azure Monitor or Prometheus",
                description="Configure continuous CPU monitoring and alerting",
                execution_order=95,
                risk_level="low",
                category="monitoring_setup",
                estimated_impact="Prevent future CPU overutilization incidents"
            )
        ]
    
    def _generate_monitoring_commands(self, cluster_id: str) -> List[str]:
        """Generate monitoring commands for ongoing observation"""
        
        context_flag = f"--context {self.kubectl_context}" if self.kubectl_context != "current-context" else ""
        
        return [
            f"watch -n 30 'kubectl top nodes {context_flag}'",
            f"kubectl get hpa --all-namespaces -w {context_flag}",
            f"kubectl logs -f -l app=cluster-autoscaler -n kube-system {context_flag}",
            f"kubectl get events --watch --all-namespaces --field-selector reason=ScalingReplicaSet {context_flag}",
            "az monitor metrics list --resource <CLUSTER_RESOURCE_ID> --metric 'node_cpu_usage_percentage' --interval PT5M"
        ]
    
    def _generate_validation_steps(self, scenario: CPUOptimizationScenario, cluster_id: str) -> List[str]:
        """Generate validation steps to confirm optimization success"""
        
        return [
            "1. Verify average CPU utilization has decreased by at least 30%",
            "2. Confirm no pods are in pending state due to resource constraints",
            "3. Check that HPA is scaling pods appropriately during load spikes",
            "4. Validate that node CPU utilization is distributed evenly",
            "5. Ensure application response times have not degraded",
            "6. Monitor for any OOMKilled events or CPU throttling",
            "7. Verify cluster autoscaler is adding/removing nodes as needed",
            "8. Confirm cost per CPU hour has improved post-optimization"
        ]
    
    def _calculate_estimated_savings(self, cpu_metrics: Dict[str, Any], scenario: CPUOptimizationScenario) -> Dict[str, Any]:
        """Calculate estimated cost and performance savings based on configurable targets"""
        
        current_cpu = cpu_metrics.get('average_cpu_usage', 100)
        current_cost = cpu_metrics.get('monthly_cost', 1000)
        target_cpu = self.thresholds['target_cpu']
        
        # Calculate CPU reduction based on scenario and configurable targets
        if scenario == CPUOptimizationScenario.CRITICAL_OVERUTILIZATION:
            # For critical scenarios, aim for target CPU utilization
            cpu_reduction = max(0, current_cpu - target_cpu)
            efficiency_factor = 0.6  # 60% of CPU reduction translates to cost savings
            performance_improvement = "40-60% reduction in response times"
        elif scenario == CPUOptimizationScenario.HIGH_USAGE:
            # For high usage, moderate reduction
            cpu_reduction = max(0, current_cpu - (target_cpu * 1.1))  # 10% above target
            efficiency_factor = 0.4
            performance_improvement = "20-40% reduction in response times"
        elif scenario == CPUOptimizationScenario.INEFFICIENT_ALLOCATION:
            # Focus on efficiency improvements
            cpu_reduction = max(0, current_cpu - target_cpu)
            efficiency_factor = 0.3
            performance_improvement = "15-30% improvement in resource efficiency"
        elif scenario == CPUOptimizationScenario.WORKLOAD_IMBALANCE:
            # Rebalancing workloads
            cpu_reduction = current_cpu * 0.15  # 15% improvement through better distribution
            efficiency_factor = 0.25
            performance_improvement = "Better workload distribution and stability"
        else:
            # Default scaling improvements
            cpu_reduction = current_cpu * 0.1  # 10% improvement
            efficiency_factor = 0.2
            performance_improvement = "Improved auto-scaling and resource utilization"
        
        # Calculate cost savings
        cost_savings = (cpu_reduction / 100) * current_cost * efficiency_factor
        
        # Ensure realistic savings (cap at 80% of current cost)
        max_savings = current_cost * 0.8
        cost_savings = min(cost_savings, max_savings)
        
        return {
            "estimated_cpu_reduction_percent": round(cpu_reduction, 1),
            "estimated_monthly_savings_usd": round(max(0, cost_savings), 2),
            "estimated_annual_savings_usd": round(max(0, cost_savings * 12), 2),
            "expected_performance_improvement": performance_improvement,
            "stability_improvement": "Reduced risk of pod evictions and service disruptions",
            "target_cpu_utilization": f"{target_cpu}%",
            "optimization_scenario": scenario.value
        }
    
    def _calculate_implementation_timeline(self, scenario: CPUOptimizationScenario, command_count: int) -> str:
        """Calculate implementation timeline based on scenario complexity"""
        
        if scenario == CPUOptimizationScenario.CRITICAL_OVERUTILIZATION:
            return "IMMEDIATE (0-2 hours emergency response, 1-2 days full optimization)"
        elif scenario == CPUOptimizationScenario.HIGH_USAGE:
            return "URGENT (4-8 hours for immediate fixes, 3-5 days full implementation)"
        else:
            return "PLANNED (1-2 weeks for thorough testing and gradual rollout)"
    
    def export_plan_to_script(self, plan: CPUOptimizationPlan, output_path: str = None) -> str:
        """Export optimization plan as executable bash script"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/cpu_optimization_{plan.cluster_id}_{timestamp}.sh"
        
        script_content = f"""#!/bin/bash
# CPU Optimization Plan for {plan.cluster_id}
# Generated: {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}
# Scenario: {plan.scenario.value}
# Severity: {plan.severity_level}

set -e  # Exit on any error

echo "🚀 Starting CPU optimization for {plan.cluster_id}"
echo "📊 Current metrics: Avg CPU: {plan.current_metrics.get('average_cpu_usage', 'N/A')}%"
echo "⚡ Scenario: {plan.scenario.value}"
echo "🎯 Expected savings: ${plan.estimated_savings.get('estimated_monthly_savings_usd', 0)}/month"
echo ""

# Set error handling
trap 'echo "❌ Script failed at line $LINENO"' ERR

"""
        
        # Add commands by category
        categories = {}
        for cmd in plan.optimization_commands:
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)
        
        for category, commands in categories.items():
            script_content += f"\n# {category.upper().replace('_', ' ')} COMMANDS\n"
            script_content += f"echo \"📋 Executing {category.replace('_', ' ')} commands...\"\n\n"
            
            for cmd in sorted(commands, key=lambda x: x.execution_order):
                script_content += f"# {cmd.description}\n"
                script_content += f"echo \"🔧 {cmd.description}\"\n"
                
                if cmd.risk_level == "high":
                    script_content += f'read -p "⚠️  HIGH RISK: Continue with this command? (y/N) " -n 1 -r\necho\nif [[ ! $REPLY =~ ^[Yy]$ ]]; then echo "Skipping high-risk command"; else\n'
                
                # Handle template commands
                if "<" in cmd.command and ">" in cmd.command:
                    script_content += f"# TEMPLATE COMMAND - REQUIRES MANUAL CONFIGURATION:\n"
                    script_content += f"# {cmd.command}\n"
                    script_content += f'echo "⚠️  Template command requires manual configuration"\n'
                else:
                    script_content += f"{cmd.command}\n"
                
                if cmd.validation_command:
                    script_content += f"echo \"✅ Validating: {cmd.validation_command}\"\n"
                    script_content += f"{cmd.validation_command}\n"
                
                if cmd.risk_level == "high":
                    script_content += f"fi\n"
                
                script_content += f"\nsleep 2\n\n"
        
        # Add monitoring section
        script_content += f"""
# MONITORING SETUP
echo "📊 Setting up monitoring..."
echo "Run these commands in separate terminals for continuous monitoring:"
"""
        
        for monitor_cmd in plan.monitoring_commands[:3]:  # Include first 3 monitoring commands
            script_content += f'echo "  {monitor_cmd}"\n'
        
        script_content += f"""
echo ""
echo "✅ Optimization plan execution completed!"
echo "💰 Expected savings: ${plan.estimated_savings.get('estimated_monthly_savings_usd', 0)}/month"
echo "📈 Monitor the cluster for the next 24-48 hours to validate improvements"
echo "🔍 Use the monitoring commands above to track progress"
"""
        
        # Write script to file
        try:
            with open(output_path, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(output_path, 0o755)
            
            logger.info(f"✅ Optimization script exported to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to export script: {e}")
            raise
    
    def export_plan_to_json(self, plan: CPUOptimizationPlan, output_path: str = None) -> str:
        """Export optimization plan as JSON for API consumption"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/cpu_optimization_plan_{plan.cluster_id}_{timestamp}.json"
        
        # Convert plan to dictionary
        plan_dict = {
            "cluster_id": plan.cluster_id,
            "scenario": plan.scenario.value,
            "severity_level": plan.severity_level,
            "current_metrics": plan.current_metrics,
            "optimization_commands": [
                {
                    "command": cmd.command,
                    "description": cmd.description,
                    "execution_order": cmd.execution_order,
                    "risk_level": cmd.risk_level,
                    "category": cmd.category,
                    "estimated_impact": cmd.estimated_impact,
                    "prerequisite_commands": cmd.prerequisite_commands,
                    "validation_command": cmd.validation_command,
                    "rollback_command": cmd.rollback_command
                }
                for cmd in plan.optimization_commands
            ],
            "monitoring_commands": plan.monitoring_commands,
            "validation_steps": plan.validation_steps,
            "estimated_savings": plan.estimated_savings,
            "timeline": plan.timeline,
            "created_at": plan.created_at.isoformat()
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(plan_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Optimization plan exported to JSON: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to export JSON: {e}")
            raise

# Factory function for easy integration
def create_cpu_optimization_planner(config: Dict[str, Any] = None) -> CPUOptimizationPlanner:
    """Factory function to create CPU optimization planner instance with optional configuration
    
    Args:
        config: Optional configuration dictionary with organization-specific thresholds
                Example config:
                {
                    'critical_cpu_threshold': 150,      # CPU % that triggers critical scenario
                    'high_cpu_threshold': 80,           # CPU % that triggers high usage scenario  
                    'target_cpu_utilization': 70,       # Target CPU utilization after optimization
                    'low_efficiency_threshold': 40,     # CPU efficiency % that triggers inefficient allocation
                    'target_efficiency': 85,            # Target CPU efficiency
                    'peak_critical_threshold': 300,     # Peak CPU % for critical scenario
                    'peak_high_threshold': 120,         # Peak CPU % for high usage scenario
                    'organization_name': 'Your Org',    # For customized reporting
                    'cloud_provider': 'azure|aws|gcp',  # For provider-specific commands
                    'enable_emergency_actions': True,   # Enable high-risk emergency commands
                    'max_replica_scale': 20,            # Maximum replicas for HPA
                    'default_cpu_limit': '1000m',       # Default CPU limit for emergency scenarios
                    'default_memory_limit': '2Gi'       # Default memory limit
                }
    """
    return CPUOptimizationPlanner(config)

def get_default_configuration_template() -> Dict[str, Any]:
    """Get default configuration template for organizations to customize"""
    return {
        # CPU Thresholds (percentage)
        'critical_cpu_threshold': 200,        # Triggers emergency response
        'high_cpu_threshold': 80,             # Triggers high usage optimization
        'target_cpu_utilization': 70,         # Target after optimization
        'low_efficiency_threshold': 50,       # Triggers efficiency optimization
        'target_efficiency': 80,              # Target efficiency percentage
        'peak_critical_threshold': 400,       # Peak CPU for critical scenario
        'peak_high_threshold': 150,           # Peak CPU for high usage scenario
        
        # Organization Settings
        'organization_name': 'Your Organization',
        'cloud_provider': 'multi',            # 'azure', 'aws', 'gcp', or 'multi' for templates
        'cluster_naming_pattern': 'auto',     # 'auto' to detect from cluster_id
        
        # Safety Settings
        'enable_emergency_actions': True,     # Allow high-risk emergency commands
        'require_manual_confirmation': True,  # Add confirmation prompts for high-risk actions
        'max_replica_scale': 20,             # Maximum replicas for autoscaling
        
        # Default Resource Limits
        'default_cpu_request': '100m',        # Default CPU request for templates
        'default_cpu_limit': '1000m',         # Default CPU limit for templates
        'default_memory_request': '128Mi',    # Default memory request
        'default_memory_limit': '2Gi',        # Default memory limit
        
        # Cost Calculation
        'cost_per_cpu_hour': 0.05,           # Cost per CPU hour for savings calculation
        'cost_efficiency_factor': 0.4,       # Factor for calculating cost savings from CPU reduction
        
        # Monitoring and Validation
        'monitoring_interval_seconds': 30,    # Default monitoring interval
        'validation_timeout_minutes': 10,     # Timeout for validation commands
        
        # Custom Commands (optional)
        'custom_assessment_commands': [],     # Additional assessment commands
        'custom_monitoring_commands': [],     # Additional monitoring commands
        'custom_validation_steps': []        # Additional validation steps
    }