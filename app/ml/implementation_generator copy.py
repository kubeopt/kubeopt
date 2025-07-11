"""
AKS Implementation Generator
==================================================
"""

import json
import math
import traceback
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging

from app.ml.ml_integration import MLLearningIntegrationMixin
from app.services.subscription_manager import azure_subscription_manager

logger = logging.getLogger(__name__)

# =============================================================================
# CORE UTILITY CLASSES - SINGLE SOURCE OF TRUTH
# =============================================================================

class ResourceParser:
    """Unified resource parsing utility - SINGLE SOURCE OF TRUTH"""
    
    @staticmethod
    def parse_cpu(cpu_str: str) -> float:
        """Parse CPU value to cores (single source of truth)"""
        if not cpu_str:
            return 0.1  # Default 100m
        
        try:
            cpu_str = str(cpu_str).strip()
            if cpu_str.endswith('m'):
                return float(cpu_str[:-1]) / 1000
            elif cpu_str.endswith('n'):
                return float(cpu_str[:-1]) / 1000000000
            elif cpu_str.endswith('u'):
                return float(cpu_str[:-1]) / 1000000
            else:
                return float(cpu_str)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Failed to parse CPU value: {cpu_str}, using default")
            return 0.1

    @staticmethod
    def parse_memory(memory_str: str) -> float:
        """Parse memory value to GB (single source of truth)"""
        if not memory_str:
            return 0.128  # Default 128Mi
        
        try:
            memory_str = str(memory_str).strip().upper()
            if memory_str.endswith('GI') or memory_str.endswith('G'):
                return float(memory_str[:-2] if memory_str.endswith('GI') else memory_str[:-1])
            elif memory_str.endswith('MI') or memory_str.endswith('M'):
                return float(memory_str[:-2] if memory_str.endswith('MI') else memory_str[:-1]) / 1024
            elif memory_str.endswith('KI') or memory_str.endswith('K'):
                return float(memory_str[:-2] if memory_str.endswith('KI') else memory_str[:-1]) / (1024 * 1024)
            elif memory_str.endswith('TI') or memory_str.endswith('T'):
                return float(memory_str[:-2] if memory_str.endswith('TI') else memory_str[:-1]) * 1024
            else:
                # Assume bytes
                return float(memory_str) / (1024 * 1024 * 1024)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Failed to parse memory value: {memory_str}, using default")
            return 0.128

    @staticmethod
    def parse_storage(storage_str: str) -> float:
        """Parse storage value to GB (single source of truth)"""
        if not storage_str:
            return 0
        
        try:
            storage_str = str(storage_str).strip().upper()
            if storage_str.endswith('GI') or storage_str.endswith('G'):
                return float(storage_str[:-2] if storage_str.endswith('GI') else storage_str[:-1])
            elif storage_str.endswith('TI') or storage_str.endswith('T'):
                return float(storage_str[:-2] if storage_str.endswith('TI') else storage_str[:-1]) * 1024
            elif storage_str.endswith('MI') or storage_str.endswith('M'):
                return float(storage_str[:-2] if storage_str.endswith('MI') else storage_str[:-1]) / 1024
            elif storage_str.endswith('KI') or storage_str.endswith('K'):
                return float(storage_str[:-2] if storage_str.endswith('KI') else storage_str[:-1]) / (1024 * 1024)
            else:
                return float(storage_str) / (1024 * 1024 * 1024)  # Assume bytes
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Failed to parse storage value: {storage_str}, using 0")
            return 0


class HPAAnalyzer:
    """Unified HPA analysis utility - SINGLE SOURCE OF TRUTH"""
    
    @staticmethod
    def calculate_optimization_score(hpa: Dict, analysis_type: str = 'enhanced') -> float:
        """Calculate HPA optimization score (consolidated implementation)"""
        score_factors = []
        
        # Analyze metrics configuration
        metrics = hpa.get('spec', {}).get('metrics', [])
        if len(metrics) >= 2:  # CPU and memory
            score_factors.append(0.8)
        elif len(metrics) == 1:
            score_factors.append(0.6)
        else:
            score_factors.append(0.3)
        
        # Analyze replica configuration
        min_replicas = hpa.get('spec', {}).get('minReplicas', 1)
        max_replicas = hpa.get('spec', {}).get('maxReplicas', 10)
        
        if min_replicas >= 2 and max_replicas >= min_replicas * 3:
            score_factors.append(0.9)
        elif min_replicas >= 1 and max_replicas >= min_replicas * 2:
            score_factors.append(0.7)
        else:
            score_factors.append(0.4)
        
        # Enhanced analysis includes behavior configuration
        if analysis_type == 'enhanced':
            behavior = hpa.get('spec', {}).get('behavior')
            score_factors.append(0.9 if behavior else 0.5)
        
        # CPU target analysis
        cpu_target = HPAAnalyzer.extract_cpu_target(hpa)
        if 60 <= cpu_target <= 80:
            score_factors.append(1.0)
        elif 50 <= cpu_target <= 90:
            score_factors.append(0.8)
        else:
            score_factors.append(0.4)
        
        return sum(score_factors) / len(score_factors)
    
    @staticmethod
    def extract_cpu_target(hpa: Dict) -> int:
        """Extract CPU target from HPA metrics"""
        metrics = hpa.get('spec', {}).get('metrics', [])
        for metric in metrics:
            if (metric.get('type') == 'Resource' and 
                metric.get('resource', {}).get('name') == 'cpu'):
                return metric.get('resource', {}).get('target', {}).get('averageUtilization', 70)
        return 70

    @staticmethod
    def extract_memory_target(hpa: Dict) -> int:
        """Extract memory target from HPA metrics"""
        metrics = hpa.get('spec', {}).get('metrics', [])
        for metric in metrics:
            if (metric.get('type') == 'Resource' and 
                metric.get('resource', {}).get('name') == 'memory'):
                return metric.get('resource', {}).get('target', {}).get('averageUtilization', 70)
        return 70

    @staticmethod
    def calculate_candidate_score(deployment: Dict) -> float:
        """Calculate HPA candidate score for deployment (consolidated implementation)"""
        score = 0.5  # Base score
        
        # Replica analysis
        replicas = deployment.get('spec', {}).get('replicas', 1)
        if replicas > 1:
            score += 0.2
        
        # Resource requests analysis
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        has_requests = any(c.get('resources', {}).get('requests') for c in containers)
        if has_requests:
            score += 0.3
        
        # Application type analysis
        name = deployment.get('metadata', {}).get('name', '').lower()
        if any(keyword in name for keyword in ['web', 'api', 'frontend', 'app', 'service']):
            score += 0.2
        
        # Label analysis
        labels = deployment.get('metadata', {}).get('labels', {})
        if labels.get('app.kubernetes.io/component') in ['frontend', 'backend', 'api']:
            score += 0.1
        
        return min(1.0, score)

    @staticmethod
    def generate_optimization_recommendations(hpa: Dict) -> Dict:
        """Generate HPA optimization recommendations (consolidated)"""
        optimizations = {}
        
        # CPU target improvements
        current_cpu = HPAAnalyzer.extract_cpu_target(hpa)
        if current_cpu < 60:
            optimizations['cpu_target'] = 70
            optimizations['cpu_rationale'] = 'Increase target for better resource utilization'
        elif current_cpu > 80:
            optimizations['cpu_target'] = 75
            optimizations['cpu_rationale'] = 'Decrease target to prevent over-scaling'
        
        # Memory target improvements
        current_memory = HPAAnalyzer.extract_memory_target(hpa)
        if current_memory < 60:
            optimizations['memory_target'] = 70
            optimizations['memory_rationale'] = 'Increase target for better memory utilization'
        elif current_memory > 80:
            optimizations['memory_target'] = 75
            optimizations['memory_rationale'] = 'Decrease target to prevent memory pressure'
        
        # Replica improvements
        current_max = hpa.get('spec', {}).get('maxReplicas', 10)
        current_min = hpa.get('spec', {}).get('minReplicas', 1)
        
        if current_max < current_min * 3:
            optimizations['max_replicas'] = current_min * 3
            optimizations['replica_rationale'] = 'Increase max replicas for better scaling headroom'
        
        if current_min < 2:
            optimizations['min_replicas'] = 2
            optimizations['min_replica_rationale'] = 'Increase min replicas for better availability'
        
        return optimizations


class CostCalculator:
    """Unified cost calculation utilities - SINGLE SOURCE OF TRUTH"""
    
    def __init__(self, cpu_cost_per_core: float = 25.0, memory_cost_per_gb: float = 3.5):
        self.cpu_cost_per_core_per_month = cpu_cost_per_core
        self.memory_cost_per_gb_per_month = memory_cost_per_gb
    
    def calculate_resource_waste_cost(self, waste_cpu_cores: float, waste_memory_gb: float) -> float:
        """Calculate estimated monthly cost of resource waste"""
        cpu_waste_cost = waste_cpu_cores * self.cpu_cost_per_core_per_month
        memory_waste_cost = waste_memory_gb * self.memory_cost_per_gb_per_month
        return (cpu_waste_cost + memory_waste_cost) * 1.15  # 15% overhead


class ClusterAnalyzer:
    """Unified cluster analysis utility - SINGLE SOURCE OF TRUTH"""
    
    @staticmethod
    def analyze_component(cluster_config: Dict, component: str, **kwargs) -> Dict:
        """Single method to analyze any cluster component"""
        analyzers = {
            'hpa': ClusterAnalyzer._analyze_hpa_state,
            'rightsizing': ClusterAnalyzer._analyze_rightsizing,
            'storage': ClusterAnalyzer._analyze_storage,
            'network': ClusterAnalyzer._analyze_network,
            'security': ClusterAnalyzer._analyze_security
        }
        
        if component not in analyzers:
            raise ValueError(f"Unknown component: {component}")
        
        return analyzers[component](cluster_config, **kwargs)
    
    @staticmethod
    def _analyze_hpa_state(cluster_config: Dict, **kwargs) -> Dict:
        """Analyze HPA state (consolidated from multiple implementations)"""
        hpa_state = {
            'existing_hpas': [],
            'suboptimal_hpas': [],
            'missing_hpa_candidates': [],
            'summary': {}
        }
        
        try:
            scaling_resources = cluster_config.get('scaling_resources', {})
            workload_resources = cluster_config.get('workload_resources', {})
            
            existing_hpas = scaling_resources.get('horizontalpodautoscalers', {}).get('items', [])
            deployments = workload_resources.get('deployments', {}).get('items', [])
            
            # Analyze existing HPAs
            for hpa in existing_hpas:
                optimization_score = HPAAnalyzer.calculate_optimization_score(hpa)
                
                hpa_analysis = {
                    'name': hpa.get('metadata', {}).get('name'),
                    'namespace': hpa.get('metadata', {}).get('namespace'),
                    'target': hpa.get('spec', {}).get('scaleTargetRef', {}).get('name'),
                    'optimization_score': optimization_score
                }
                
                if optimization_score < 0.7:
                    hpa_analysis['recommended_changes'] = HPAAnalyzer.generate_optimization_recommendations(hpa)
                    hpa_state['suboptimal_hpas'].append(hpa_analysis)
                else:
                    hpa_state['existing_hpas'].append(hpa_analysis)
            
            # Find missing HPA candidates
            existing_targets = {hpa.get('target') for hpa in hpa_state['existing_hpas'] + hpa_state['suboptimal_hpas']}
            
            for deployment in deployments:
                deployment_name = deployment.get('metadata', {}).get('name')
                if deployment_name and deployment_name not in existing_targets:
                    candidate_score = HPAAnalyzer.calculate_candidate_score(deployment)
                    if candidate_score > 0.6:
                        hpa_state['missing_hpa_candidates'].append({
                            'deployment_name': deployment_name,
                            'namespace': deployment.get('metadata', {}).get('namespace'),
                            'priority_score': candidate_score,
                            'should_have_hpa': True
                        })
            
            # Summary
            total_workloads = len(deployments)
            total_hpas = len(hpa_state['existing_hpas']) + len(hpa_state['suboptimal_hpas'])
            
            hpa_state['summary'] = {
                'total_workloads': total_workloads,
                'existing_hpas': len(hpa_state['existing_hpas']),
                'suboptimal_hpas': len(hpa_state['suboptimal_hpas']),
                'missing_candidates': len(hpa_state['missing_hpa_candidates']),
                'hpa_coverage_percent': (total_hpas / max(total_workloads, 1)) * 100,
                'optimization_potential': len(hpa_state['suboptimal_hpas']) + len(hpa_state['missing_hpa_candidates'])
            }
            
        except Exception as e:
            logger.error(f"❌ HPA analysis failed: {e}")
            hpa_state['analysis_error'] = str(e)
        
        return hpa_state
    
    @staticmethod
    def _analyze_rightsizing(cluster_config: Dict, **kwargs) -> Dict:
        """Analyze resource rightsizing opportunities"""
        rightsizing_state = {
            'overprovisioned_workloads': [],
            'optimization_potential': {}
        }
        
        try:
            workload_resources = cluster_config.get('workload_resources', {})
            deployments = workload_resources.get('deployments', {}).get('items', [])
            
            total_waste_cpu = 0
            total_waste_memory = 0
            cost_calculator = CostCalculator()
            
            for deployment in deployments:
                efficiency = ClusterAnalyzer._calculate_resource_efficiency(deployment)
                
                if efficiency < 0.7:  # Optimization threshold
                    waste_cpu = ClusterAnalyzer._estimate_cpu_waste(deployment)
                    waste_memory = ClusterAnalyzer._estimate_memory_waste(deployment)
                    
                    rightsizing_state['overprovisioned_workloads'].append({
                        'name': deployment.get('metadata', {}).get('name'),
                        'namespace': deployment.get('metadata', {}).get('namespace'),
                        'resource_efficiency': efficiency,
                        'waste_cpu_cores': waste_cpu,
                        'waste_memory_gb': waste_memory
                    })
                    
                    total_waste_cpu += waste_cpu
                    total_waste_memory += waste_memory
            
            rightsizing_state['optimization_potential'] = {
                'workloads_to_optimize': len(rightsizing_state['overprovisioned_workloads']),
                'total_waste_cpu_cores': total_waste_cpu,
                'total_waste_memory_gb': total_waste_memory,
                'estimated_monthly_savings': cost_calculator.calculate_resource_waste_cost(total_waste_cpu, total_waste_memory)
            }
            
        except Exception as e:
            logger.error(f"❌ Rightsizing analysis failed: {e}")
            rightsizing_state['analysis_error'] = str(e)
        
        return rightsizing_state
    
    @staticmethod
    def _analyze_storage(cluster_config: Dict, **kwargs) -> Dict:
        """Analyze storage optimization opportunities"""
        storage_state = {
            'optimization_opportunities': [],
            'cost_analysis': {}
        }
        
        try:
            storage_resources = cluster_config.get('storage_resources', {})
            storage_classes = storage_resources.get('storageclasses', {}).get('items', [])
            
            for sc in storage_classes:
                if ClusterAnalyzer._has_storage_optimization_potential(sc):
                    storage_state['optimization_opportunities'].append({
                        'type': 'optimize_storage_class',
                        'target': sc.get('metadata', {}).get('name'),
                        'recommendation': ClusterAnalyzer._generate_storage_recommendation(sc),
                        'potential_savings': 'Up to 40-60% cost reduction'
                    })
            
        except Exception as e:
            logger.error(f"❌ Storage analysis failed: {e}")
            storage_state['analysis_error'] = str(e)
        
        return storage_state
    
    @staticmethod
    def _analyze_network(cluster_config: Dict, **kwargs) -> Dict:
        """Analyze network optimization opportunities"""
        network_state = {
            'optimization_opportunities': []
        }
        
        try:
            network_resources = cluster_config.get('networking_resources', {})
            workload_resources = cluster_config.get('workload_resources', {})
            
            network_policies = network_resources.get('networkpolicies', {}).get('items', [])
            services = workload_resources.get('services', {}).get('items', [])
            
            if len(network_policies) == 0 and len(services) > 0:
                network_state['optimization_opportunities'].append({
                    'type': 'implement_network_policies',
                    'recommendation': 'Implement network policies for security and cost optimization',
                    'impact': 'Improved security and reduced attack surface'
                })
            
            external_services = [s for s in services if s.get('spec', {}).get('type') in ['LoadBalancer', 'NodePort']]
            if len(external_services) > 3:
                network_state['optimization_opportunities'].append({
                    'type': 'optimize_external_services',
                    'recommendation': 'Review external services for cost optimization',
                    'impact': f'{len(external_services)} external services may incur additional costs'
                })
            
        except Exception as e:
            logger.error(f"❌ Network analysis failed: {e}")
            network_state['analysis_error'] = str(e)
        
        return network_state
    
    @staticmethod
    def _analyze_security(cluster_config: Dict, **kwargs) -> Dict:
        """Analyze security optimization opportunities"""
        security_state = {
            'optimization_opportunities': [],
            'rbac_resources': {}
        }
        
        try:
            security_resources = cluster_config.get('security_resources', {})
            
            rbac_count = sum(
                security_resources.get(resource, {}).get('item_count', 0)
                for resource in ['roles', 'clusterroles', 'rolebindings', 'clusterrolebindings']
            )
            
            security_state['rbac_resources']['total'] = rbac_count
            
            if rbac_count < 10:
                security_state['optimization_opportunities'].append({
                    'type': 'enhance_rbac',
                    'recommendation': 'Implement more granular RBAC for better security',
                    'impact': 'Improved security and compliance'
                })
            
            service_accounts = security_resources.get('serviceaccounts', {}).get('item_count', 0)
            if service_accounts < 5:
                security_state['optimization_opportunities'].append({
                    'type': 'implement_service_accounts',
                    'recommendation': 'Implement dedicated service accounts for applications',
                    'impact': 'Enhanced security isolation'
                })
            
        except Exception as e:
            logger.error(f"❌ Security analysis failed: {e}")
            security_state['analysis_error'] = str(e)
        
        return security_state
    
    # Helper methods for analysis
    @staticmethod
    def _calculate_resource_efficiency(deployment: Dict) -> float:
        """Calculate resource efficiency for deployment"""
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        
        if not containers:
            return 0.5
        
        efficiency_factors = []
        for container in containers:
            resources = container.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            
            if requests and limits:
                efficiency_factors.append(0.7)
            elif requests:
                efficiency_factors.append(0.5)
            else:
                efficiency_factors.append(0.3)
        
        return sum(efficiency_factors) / len(efficiency_factors)
    
    @staticmethod
    def _estimate_cpu_waste(deployment: Dict) -> float:
        """Estimate CPU waste for deployment"""
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        total_waste = 0.0
        
        for container in containers:
            cpu_request = container.get('resources', {}).get('requests', {}).get('cpu', '100m')
            cpu_cores = ResourceParser.parse_cpu(cpu_request)
            estimated_waste = cpu_cores * 0.3  # 30% waste estimate
            total_waste += estimated_waste
        
        return total_waste
    
    @staticmethod
    def _estimate_memory_waste(deployment: Dict) -> float:
        """Estimate memory waste for deployment"""
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        total_waste = 0.0
        
        for container in containers:
            memory_request = container.get('resources', {}).get('requests', {}).get('memory', '128Mi')
            memory_gb = ResourceParser.parse_memory(memory_request)
            estimated_waste = memory_gb * 0.25  # 25% waste estimate
            total_waste += estimated_waste
        
        return total_waste
    
    @staticmethod
    def _has_storage_optimization_potential(storage_class: Dict) -> bool:
        """Check if storage class has optimization potential"""
        parameters = storage_class.get('parameters', {})
        sku_name = parameters.get('skuName', '')
        return 'Premium' in sku_name or 'Standard_LRS' in sku_name
    
    @staticmethod
    def _generate_storage_recommendation(storage_class: Dict) -> str:
        """Generate storage optimization recommendation"""
        parameters = storage_class.get('parameters', {})
        sku_name = parameters.get('skuName', '')
        
        if 'Premium_LRS' in sku_name:
            return 'Replace with StandardSSD_LRS for 40-60% cost reduction'
        elif 'Standard_LRS' in sku_name:
            return 'Optimize with lifecycle management for additional savings'
        else:
            return 'Implement cost-optimized storage configuration'


class ExecutionPlanBuilder:
    """Unified execution plan builder - consolidates multiple plan creation methods"""
    
    @staticmethod
    def create_execution_plan(commands: List, plan_type: str = 'standard', **kwargs) -> Any:
        """Create execution plan of specified type"""
        
        try:
            from dataclasses import dataclass
            from typing import List as TypingList
            
            @dataclass
            class UnifiedExecutionPlan:
                plan_id: str
                plan_type: str
                preparation_commands: TypingList
                optimization_commands: TypingList
                validation_commands: TypingList
                total_commands: int
                success_probability: float
        
            # Categorize commands
            preparation_commands = [cmd for cmd in commands if getattr(cmd, 'category', '') == 'preparation']
            optimization_commands = [cmd for cmd in commands if getattr(cmd, 'category', '') == 'execution']
            validation_commands = [cmd for cmd in commands if getattr(cmd, 'category', '') == 'validation']
            
            # Calculate success probability based on plan type and command quality
            base_probability = 0.8
            if plan_type == 'ml_enhanced':
                base_probability = 0.9
            elif plan_type == 'state_driven':
                base_probability = 0.85
            
            # Adjust based on command count
            command_quality_factor = min(1.0, len(commands) / 10)
            success_probability = base_probability * (0.7 + 0.3 * command_quality_factor)
            
            return UnifiedExecutionPlan(
                plan_id=f"{plan_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                plan_type=plan_type,
                preparation_commands=preparation_commands,
                optimization_commands=optimization_commands,
                validation_commands=validation_commands,
                total_commands=len(commands),
                success_probability=success_probability
            )
            
        except Exception as e:
            logger.error(f"❌ Execution plan creation failed: {e}")
            return None


# =============================================================================
# MAIN REFACTORED CLASS
# =============================================================================

class AKSImplementationGenerator(MLLearningIntegrationMixin):
    """
    AKS Implementation Generator - REFACTORED VERSION
    
    Core implementation plan generation with ML intelligence.
    Uses utilities from this file, delegates command generation to dynamic_cmd_center.py
    """
    
    def __init__(self, enable_cost_monitoring: bool = True, enable_temporal: bool = True):
        """Initialize with ML orchestration"""
        super().__init__()
        
        logger.info("🧠 Initializing REFACTORED AKS Implementation Generator")
        
        # Core configuration
        self.enable_cost_monitoring = enable_cost_monitoring
        self.enable_temporal = enable_temporal
        self.monitoring_active = False
        
        # Utility instances
        self.cost_calculator = CostCalculator()
        
        # Debug tracking
        self._debug_info = {
            'initialization_time': datetime.now(),
            'ml_system_status': {},
            'failed_operations': []
        }
        
        # Session tracking
        self._current_ml_session = None
        self._ml_sessions_history = []
        
        # ML Intelligence Systems
        self._initialize_ml_systems()
        
        logger.info("✅ REFACTORED AKS Implementation Generator ready")
        logger.info(f"🔧 ML Systems Available: {self.ml_systems_available}")

    def generate_implementation_plan(self, analysis_results: Dict, 
                               historical_data: Optional[Dict] = None,
                               cost_budget_monthly: Optional[float] = None,
                               enable_real_time_monitoring: bool = True) -> Dict:
        """
        Generate implementation plan with REAL cluster configuration integration
        WITH EXTENSIVE DEBUGGING FOR ML COMPONENT TRACKING
        """
        cluster_name = analysis_results.get('cluster_name', 'unknown')
        resource_group = analysis_results.get('resource_group', 'unknown')
        
        # DEBUG: Initial setup
        logger.info("🚀 === STARTING IMPLEMENTATION PLAN GENERATION ===")
        logger.info(f"📊 Cluster: {cluster_name}, Resource Group: {resource_group}")
        logger.info(f"🔧 ML Systems Available: {self.ml_systems_available}")
        
        subscription_id = azure_subscription_manager.find_cluster_subscription(resource_group, cluster_name)
        logger.info(f"📊 Using subscription {subscription_id[:8] if subscription_id else 'None'} from config")           
    
        logger.info(f"🎯 Generating ML-enhanced implementation plan for {cluster_name}")
        
        try:
            # DEBUG: Validate input data
            logger.info("🔍 PHASE 0: Input Validation")
            if not self._validate_input_data(analysis_results):
                raise ValueError("❌ CRITICAL: Invalid analysis_results provided")
            logger.info("✅ Input validation passed")
            
            # Start ML intelligence session
            logger.info("🔍 PHASE 0.5: ML Session Initialization")
            ml_session = self._start_ml_session(analysis_results)
            logger.info(f"✅ ML Session started: {ml_session['session_id']}")
            
            # Extract basic values
            total_cost = float(analysis_results.get('total_cost', 0))
            total_savings = float(analysis_results.get('total_savings', 0))
            
            logger.info(f"💰 Processing - Cost: ${total_cost:.2f}, Savings: ${total_savings:.2f}")
            
            # PHASE 0: REAL CLUSTER CONFIGURATION FETCHING
            logger.info("🔄 PHASE 1: Real Cluster Configuration Analysis")
            cluster_config = self._fetch_and_analyze_cluster_config(
                resource_group, cluster_name, subscription_id, ml_session
            )
            logger.info(f"📋 Cluster config status: {cluster_config.get('status', 'unknown')}")
            
            # PHASE 1: ML Cluster DNA Analysis
            logger.info("🔄 PHASE 2: ML Cluster DNA Analysis")
            cluster_dna = self._ml_analyze_cluster_dna(
                analysis_results, historical_data, ml_session, cluster_config
            )
            if cluster_dna is None:
                raise ValueError("❌ CRITICAL: DNA analysis failed")
            
            logger.info(f"✅ DNA Analysis complete - Type: {type(cluster_dna).__name__}")
            logger.info(f"🧬 DNA Confidence: {getattr(cluster_dna, 'optimization_readiness_score', 'N/A')}")
            
            # PHASE 2: ML Strategy Generation
            logger.info("🔄 PHASE 3: ML Strategy Generation")
            ml_strategy = self._ml_generate_strategy(
                cluster_dna, analysis_results, ml_session, cluster_config
            )
            if ml_strategy is None:
                raise ValueError("❌ CRITICAL: Strategy generation failed")
            
            logger.info(f"✅ Strategy Generation complete - Type: {type(ml_strategy).__name__}")
            logger.info(f"📊 Strategy Confidence: {getattr(ml_strategy, 'success_probability', 'N/A')}")
            
            # PHASE 3: ML Plan Generation
            logger.info("🔄 PHASE 4: ML Plan Generation")
            ml_plan = self._ml_generate_comprehensive_plan(
                analysis_results, ml_strategy, cluster_dna, ml_session, cluster_config
            )
            if ml_plan is None or not isinstance(ml_plan, dict):
                raise ValueError("❌ CRITICAL: Plan generation failed")
            
            # DEBUG: Check plan structure after generation
            logger.info("🔍 DEBUGGING: ML Plan after generation")
            logger.info(f"📋 Plan type: {type(ml_plan)}")
            logger.info(f"📋 Plan keys: {list(ml_plan.keys()) if isinstance(ml_plan, dict) else 'Not a dict'}")
            
            # Check for ML components already in plan
            ml_components = ['costProtection', 'governance', 'monitoring', 'contingency',
                            'successCriteria', 'timelineOptimization', 'riskMitigation', 'intelligenceInsights']
            
            components_in_plan_after_generation = []
            for comp in ml_components:
                if comp in ml_plan:
                    components_in_plan_after_generation.append(comp)
                    logger.info(f"   ✅ {comp}: Already in plan after generation")
                else:
                    logger.info(f"   ❌ {comp}: Missing after plan generation")
            
            logger.info(f"📊 ML Components after plan generation: {len(components_in_plan_after_generation)}/{len(ml_components)}")
            
            # PHASE 4: ML Command Integration (delegates to dynamic_cmd_center.py)
            logger.info("🔄 PHASE 5: ML Command Integration")
            ml_plan = self._ml_integrate_executable_commands(
                ml_plan, analysis_results, ml_strategy, ml_session, cluster_config
            )
            if ml_plan is None:
                raise ValueError("❌ CRITICAL: Command integration failed")
            
            # DEBUG: Check plan structure after command integration
            logger.info("🔍 DEBUGGING: ML Plan after command integration")
            logger.info(f"📋 Plan type: {type(ml_plan)}")
            logger.info(f"📋 Plan keys: {list(ml_plan.keys()) if isinstance(ml_plan, dict) else 'Not a dict'}")
            
            components_in_plan_after_commands = []
            for comp in ml_components:
                if comp in ml_plan:
                    components_in_plan_after_commands.append(comp)
                    logger.info(f"   ✅ {comp}: Still in plan after command integration")
                else:
                    logger.info(f"   ❌ {comp}: Missing after command integration")
            
            logger.info(f"📊 ML Components after command integration: {len(components_in_plan_after_commands)}/{len(ml_components)}")
            
            # PHASE 6: Framework Structure Completion
            logger.info("🔄 PHASE 6: Framework Structure Completion")
            logger.info("🤖 About to generate PURE ML framework structure...")
            
            # DEBUG: Pre-framework state
            logger.info("🔍 DEBUGGING: Before ML framework generation")
            logger.info(f"📋 Plan size before framework: {len(ml_plan)} keys")
            
            ml_plan = self._ensure_complete_framework_structure(
                ml_plan, analysis_results, ml_session, cluster_config
            )
            if ml_plan is None:
                raise ValueError("❌ CRITICAL: Framework completion failed")
            
            # DEBUG: Post-framework state - CRITICAL CHECK
            logger.info("🔍 DEBUGGING: After ML framework generation - CRITICAL CHECK")
            logger.info(f"📋 Plan type: {type(ml_plan)}")
            logger.info(f"📋 Plan size after framework: {len(ml_plan)} keys")
            logger.info(f"📋 All plan keys: {list(ml_plan.keys()) if isinstance(ml_plan, dict) else 'Not a dict'}")

            # PHASE 6.5: Frontend Formatting (add this AFTER ML framework completion)
            logger.info("🔄 PHASE 6(Continues): Frontend Formatting with ML Components")
            
            # Convert plan object to frontend format NOW (after ML components are added)
            if hasattr(ml_plan, '_format_for_frontend') and callable(getattr(ml_plan, '_format_for_frontend')):
                # If ml_plan is still a plan object, format it
                ml_plan = self.plan_generator._format_for_frontend(ml_plan, analysis_results)
                logger.info("✅ Plan object formatted for frontend with ML components")
            elif isinstance(ml_plan, dict):
                # If it's already a dict, ensure it has the right structure
                logger.info("✅ Plan is already a dictionary - checking ML component inclusion")
                
                # Debug: Check if ML components are in the dict
                ml_components = ['costProtection', 'governance', 'monitoring', 'contingency',
                                'successCriteria', 'timelineOptimization', 'riskMitigation', 'intelligenceInsights']
                
                components_found = [comp for comp in ml_components if comp in ml_plan]
                logger.info(f"🎯 ML components in plan dict: {len(components_found)}/8 - {components_found}")
                
                if len(components_found) < 8:
                    logger.error(f"❌ Missing ML components: {[comp for comp in ml_components if comp not in ml_plan]}")
                    # This shouldn't happen now, but log if it does
            
            # DETAILED ML COMPONENT CHECK
            logger.info("🎯 === DETAILED ML FRAMEWORK COMPONENT CHECK ===")
            components_after_framework = []
            components_with_issues = []
            
            for comp_name in ml_components:
                if comp_name in ml_plan:
                    components_after_framework.append(comp_name)
                    comp_data = ml_plan[comp_name]
                    
                    if isinstance(comp_data, dict):
                        enabled = comp_data.get('enabled', False)
                        has_data = comp_data.get('dataAvailable', False)
                        ml_conf = comp_data.get('ml_confidence', 'N/A')
                        ml_generated = comp_data.get('improved_ml_generated', False)
                        
                        logger.info(f"   ✅ {comp_name}:")
                        logger.info(f"      enabled={enabled}, data={has_data}")
                        logger.info(f"      ml_confidence={ml_conf}, ml_generated={ml_generated}")
                        
                        if not enabled:
                            components_with_issues.append(f"{comp_name}_disabled")
                        if not has_data:
                            components_with_issues.append(f"{comp_name}_no_data")
                    else:
                        logger.error(f"   ❌ {comp_name}: Invalid type {type(comp_data)}")
                        components_with_issues.append(f"{comp_name}_invalid_type")
                else:
                    logger.error(f"   ❌ {comp_name}: COMPLETELY MISSING")
                    components_with_issues.append(f"{comp_name}_missing")
            
            logger.info(f"📊 FRAMEWORK COMPONENT SUMMARY:")
            logger.info(f"   Found: {len(components_after_framework)}/{len(ml_components)}")
            logger.info(f"   Components: {components_after_framework}")
            if components_with_issues:
                logger.warning(f"   Issues: {components_with_issues}")
            
            # Check for framework metadata
            if 'ml_framework_metadata' in ml_plan:
                metadata = ml_plan['ml_framework_metadata']
                logger.info(f"🤖 ML Framework Metadata:")
                logger.info(f"   Pure ML Generated: {metadata.get('pure_ml_generated', False)}")
                logger.info(f"   ML Confidence: {metadata.get('ml_confidence', 'N/A')}")
                logger.info(f"   Components Generated: {metadata.get('components_generated', 0)}")
            else:
                logger.warning("⚠️ No ML framework metadata found")
            
            # CRITICAL VALIDATION
            # if len(components_after_framework) < 7:  # Should have at least 7 of 8 components
            #     logger.error(f"🚨 CRITICAL ISSUE: Only {len(components_after_framework)} ML components found!")
            #     logger.error("🚨 This will cause UI display issues!")
                
            #     # Emergency fix attempt
            #     logger.info("🆘 Attempting emergency ML component fix...")
            #     try:
            #         ml_plan = self._debug_and_fix_ml_components(ml_plan, "Emergency_Framework_Fix")
                    
            #         # Recheck after emergency fix
            #         emergency_fixed_count = len([comp for comp in ml_components if comp in ml_plan])
            #         logger.info(f"🆘 After emergency fix: {emergency_fixed_count} components")
            #     except Exception as e:
            #         logger.error(f"🆘 Emergency fix failed: {e}")
            # else:
            #     logger.info(f"✅ SUCCESS: {len(components_after_framework)} ML components ready")
            
            
            # PHASE 7: Validate output structure
            logger.info("🔄 PHASE 7: Output Structure Validation")
            if not self._validate_output_structure(ml_plan):
                raise ValueError("❌ CRITICAL: Output validation failed")
            logger.info("✅ Output structure validation passed")
            
            # PHASE 8: Calculate ML confidence
            logger.info("🔄 PHASE 8: ML Confidence Calculation")
            plan_confidence = self._calculate_ml_plan_confidence(
                analysis_results, ml_plan, ml_session, cluster_config
            )
            logger.info(f"🎯 Plan Confidence: {plan_confidence:.1%}")
            
            # PHASE 9: Record learning outcomes
            logger.info("🔄 PHASE 9: Learning Outcomes Recording")
            self._record_ml_learning_outcomes(ml_plan, ml_session, plan_confidence)
            logger.info("✅ Learning outcomes recorded")
            
            # PHASE 10: Finalize session
            logger.info("🔄 PHASE 10: Session Finalization")
            self._finalize_ml_session(ml_session, ml_plan, plan_confidence)
            logger.info("✅ ML session finalized")
            
            # === FINAL COMPREHENSIVE CHECK BEFORE RETURN ===
            logger.info("🔍 === FINAL COMPREHENSIVE CHECK BEFORE RETURN ===")
            
            # Check plan structure
            logger.info(f"📋 Final plan type: {type(ml_plan)}")
            logger.info(f"📋 Final plan size: {len(ml_plan) if isinstance(ml_plan, dict) else 'N/A'} keys")
            
            if isinstance(ml_plan, dict):
                final_plan_keys = list(ml_plan.keys())
                logger.info(f"📋 Final plan keys: {final_plan_keys}")
                
                # Check standard plan components
                standard_components = ['implementation_phases', 'executive_summary', 'business_case', 'roi_analysis']
                for std_comp in standard_components:
                    if std_comp in ml_plan:
                        logger.info(f"   ✅ {std_comp}: Present")
                    else:
                        logger.warning(f"   ⚠️ {std_comp}: Missing")
                
                # Final ML component check
                logger.info("🎯 === FINAL ML COMPONENT STATUS ===")
                final_ml_components = []
                final_ml_issues = []
                
                for comp_name in ml_components:
                    if comp_name in ml_plan:
                        final_ml_components.append(comp_name)
                        comp_data = ml_plan[comp_name]
                        
                        if isinstance(comp_data, dict):
                            enabled = comp_data.get('enabled', False)
                            logger.info(f"   ✅ {comp_name}: enabled={enabled}")
                            if not enabled:
                                final_ml_issues.append(f"{comp_name}_disabled")
                        else:
                            logger.error(f"   ❌ {comp_name}: Invalid structure")
                            final_ml_issues.append(f"{comp_name}_invalid")
                    else:
                        logger.error(f"   ❌ {comp_name}: MISSING FROM FINAL PLAN")
                        final_ml_issues.append(f"{comp_name}_missing")
                
                # Final summary
                logger.info(f"📊 FINAL ML COMPONENT STATUS:")
                logger.info(f"   Components Ready: {len(final_ml_components)}/{len(ml_components)}")
                logger.info(f"   Ready Components: {final_ml_components}")
                
                if final_ml_issues:
                    logger.error(f"   Issues Found: {final_ml_issues}")
                    logger.error("🚨 THESE ISSUES WILL CAUSE UI PROBLEMS!")
                
                # UI readiness assessment
                if len(final_ml_components) >= 7:
                    logger.info("✅ UI READINESS: GOOD - Most ML components available")
                elif len(final_ml_components) >= 4:
                    logger.warning("⚠️ UI READINESS: PARTIAL - Some ML components missing")
                else:
                    logger.error("❌ UI READINESS: POOR - Most ML components missing")
                    
                # Sample component data for verification
                if final_ml_components:
                    sample_comp_name = final_ml_components[0]
                    sample_comp_data = ml_plan[sample_comp_name]
                    logger.info(f"📋 Sample component {sample_comp_name}:")
                    logger.info(f"   Type: {type(sample_comp_data)}")
                    if isinstance(sample_comp_data, dict):
                        logger.info(f"   Keys: {list(sample_comp_data.keys())}")
                        logger.info(f"   Enabled: {sample_comp_data.get('enabled', 'N/A')}")
                        logger.info(f"   ML Confidence: {sample_comp_data.get('ml_confidence', 'N/A')}")
            else:
                logger.error(f"❌ CRITICAL: Final plan is not a dictionary! Type: {type(ml_plan)}")
                raise ValueError(f"❌ CRITICAL: Invalid plan type returned: {type(ml_plan)}")
            
            # Check total size for reasonableness
            if isinstance(ml_plan, dict) and len(ml_plan) < 10:
                logger.warning(f"⚠️ Final plan seems small: only {len(ml_plan)} top-level keys")
            elif isinstance(ml_plan, dict) and len(ml_plan) > 50:
                logger.warning(f"⚠️ Final plan seems large: {len(ml_plan)} top-level keys")
            else:
                logger.info(f"✅ Final plan size looks reasonable: {len(ml_plan)} keys")
            
            # === SUCCESS LOGGING ===
            logger.info("🎉 === IMPLEMENTATION PLAN GENERATION COMPLETE ===")
            logger.info(f"🎯 Generated with {plan_confidence:.1%} confidence")
            logger.info(f"📊 Plan contains {len(final_ml_components)} ML framework components")
            logger.info(f"🚀 Ready for frontend formatting and UI display")
            
            # RIGHT BEFORE: return ml_plan
            logger.info(f"🚨 FINAL API RESPONSE - costProtection: {ml_plan.get('costProtection', 'MISSING')}")
            return ml_plan
            
        except Exception as e:
            # === ERROR LOGGING ===
            logger.error("💥 === IMPLEMENTATION PLAN GENERATION FAILED ===")
            logger.error(f"💥 Error: {type(e).__name__}: {str(e)}")
            logger.error(f"💥 Traceback: {traceback.format_exc()}")
            
            self._log_complete_failure_details(e, analysis_results, locals())
            self._record_generation_failure(str(e))
            logger.error(f"❌ FINAL FAILURE: Implementation plan generation failed: {str(e)}")
            raise

    # =============================================================================
    # CORE ML METHODS
    # =============================================================================

    def _fetch_and_analyze_cluster_config(self, resource_group: str, cluster_name: str, 
                                          subscription_id: str, ml_session: Dict) -> Dict[str, Any]:
        """Fetch and analyze cluster configuration"""
        try:
            if not subscription_id:
                logger.warning("⚠️ No subscription ID available - skipping cluster config fetch")
                return {'fetch_error': 'no_subscription_id', 'status': 'skipped'}
            
            logger.info(f"🔍 Fetching real cluster configuration for {cluster_name}")
            
            from app.analytics.aks_config_fetcher import create_cluster_config_fetcher
            
            fetcher = create_cluster_config_fetcher(resource_group, cluster_name, subscription_id)
            cluster_config = fetcher.fetch_raw_cluster_configuration(enable_parallel_fetch=True)
            
            if cluster_config.get('status') == 'completed':
                logger.info(f"✅ Cluster config fetched: {cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0)} resources")
                
                # Store config and perform comprehensive analysis
                ml_session['cluster_config'] = cluster_config
                ml_session['config_insights'] = self._extract_config_insights(cluster_config)
                
                # Perform comprehensive state analysis using refactored components
                comprehensive_state = self._perform_comprehensive_state_analysis(cluster_config, ml_session)
                ml_session['comprehensive_state'] = comprehensive_state
                
                # Record learning event
                ml_session['learning_events'].append({
                    'event': 'enhanced_cluster_config_fetched',
                    'resources_fetched': cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0),
                    'optimization_opportunities': comprehensive_state.get('total_optimization_opportunities', 0),
                    'success': True
                })
                
                return cluster_config
            else:
                logger.warning(f"⚠️ Cluster config fetch failed: {cluster_config.get('error', 'unknown')}")
                return cluster_config
                
        except Exception as e:
            logger.error(f"❌ Cluster config fetch failed: {e}")
            return {'fetch_error': str(e), 'status': 'failed'}

    def _perform_comprehensive_state_analysis(self, cluster_config: Dict, ml_session: Dict) -> Dict:
        """Perform comprehensive state analysis using refactored components"""
        if not cluster_config or cluster_config.get('status') != 'completed':
            logger.warning("⚠️ Cluster config not available for state analysis")
            return {'analysis_available': False, 'reason': 'cluster_config_unavailable'}
        
        logger.info("🔍 Starting comprehensive state analysis with refactored components...")
        
        comprehensive_state = {
            'analysis_available': True,
            'total_optimization_opportunities': 0,
            'analysis_metadata': {
                'start_time': datetime.now().isoformat(),
                'refactored_version': True
            }
        }
        
        try:
            # Use refactored ClusterAnalyzer for all components
            components = ['hpa', 'rightsizing', 'storage', 'network', 'security']
            
            for component in components:
                logger.info(f"📊 Analyzing {component} state...")
                component_state = ClusterAnalyzer.analyze_component(cluster_config, component)
                comprehensive_state[f'{component}_state'] = component_state
                
                # Sum optimization opportunities
                if component == 'hpa':
                    opportunities = component_state.get('summary', {}).get('optimization_potential', 0)
                elif component == 'rightsizing':
                    opportunities = component_state.get('optimization_potential', {}).get('workloads_to_optimize', 0)
                else:
                    opportunities = len(component_state.get('optimization_opportunities', []))
                
                comprehensive_state['total_optimization_opportunities'] += opportunities
                logger.info(f"   {component.title()} Opportunities: {opportunities}")
            
            comprehensive_state['analysis_metadata']['end_time'] = datetime.now().isoformat()
            comprehensive_state['analysis_metadata']['total_opportunities'] = comprehensive_state['total_optimization_opportunities']
            
            logger.info(f"✅ Comprehensive state analysis completed with refactored components")
            logger.info(f"📊 Total optimization opportunities: {comprehensive_state['total_optimization_opportunities']}")
            
            return comprehensive_state
            
        except Exception as e:
            logger.error(f"❌ Comprehensive state analysis failed: {e}")
            comprehensive_state['analysis_available'] = False
            comprehensive_state['analysis_error'] = str(e)
            return comprehensive_state

    def _ml_integrate_executable_commands(self, implementation_plan: Dict, analysis_results: Dict, 
                                         ml_strategy: Any, ml_session: Dict, 
                                         cluster_config: Dict) -> Dict:
        """ML Command Integration - delegates to dynamic_cmd_center.py"""
        logger.info("🛠️ ML Command Integration - delegating to command generator...")
        
        if implementation_plan is None:
            raise ValueError("❌ Cannot integrate commands - implementation_plan is None")
        
        # Backup ML components before any processing
        ml_components = ['costProtection', 'governance', 'monitoring', 'contingency',
                        'successCriteria', 'timelineOptimization', 'riskMitigation', 'intelligenceInsights']
        
        ml_backup = {comp: implementation_plan.get(comp) for comp in ml_components if comp in implementation_plan}
        logger.info(f"💾 Backed up {len(ml_backup)} ML components")
        
        try:
            # Import command generator from dynamic_cmd_center.py
            from app.ml.dynamic_cmd_center import AdvancedExecutableCommandGenerator
            
            # Initialize command generator
            command_generator = AdvancedExecutableCommandGenerator()
            
            # Set cluster config if available
            if cluster_config and cluster_config.get('status') == 'completed':
                command_generator.set_cluster_config(cluster_config)
            
            # Extract session data
            cluster_dna = ml_session.get('cluster_dna')
            
            # Generate execution plan using command generator
            execution_plan = command_generator.generate_comprehensive_execution_plan(
                ml_strategy, cluster_dna, analysis_results, cluster_config
            )
            
            if execution_plan is None:
                raise RuntimeError("❌ Command generation failed")
            
            command_count = self._count_execution_plan_commands(execution_plan)
            logger.info(f"📊 Generated Commands: {command_count}")
            
            if command_count < 5:
                raise RuntimeError(f"Insufficient commands generated: {command_count}")
            
            # Distribute commands to phases
            implementation_plan = self._distribute_commands_to_phases(
                implementation_plan, execution_plan
            )

            # Restore ML components after command distribution
            for comp_name, comp_data in ml_backup.items():
                if comp_data:  # Only restore if we had valid data
                    implementation_plan[comp_name] = comp_data
                    logger.info(f"🔓 Restored {comp_name}")
            
            # Validate distribution
            total_distributed = sum(len(phase.get('commands', [])) for phase in implementation_plan.get('implementation_phases', []))
            
            if total_distributed < 5:
                raise RuntimeError(f"Command distribution failure: {total_distributed} commands")
            
            # Record success
            ml_session['learning_events'].append({
                'event': 'command_integration_success',
                'total_commands_generated': command_count,
                'total_commands_distributed': total_distributed,
                'delegated_to_cmd_center': True,
                'success': True
            })
            
            logger.info(f"✅ Command Integration Success: {total_distributed} commands distributed")
            
            return implementation_plan
            
        except Exception as e:
            logger.error(f"❌ ML command integration failed: {e}")
            raise RuntimeError(f"ML command integration failed: {e}") from e

    def _distribute_commands_to_phases(self, implementation_plan: Dict, execution_plan: Any) -> Dict:
        """Distribute commands from execution plan to implementation phases"""
        phases = implementation_plan.get('implementation_phases', [])
        
        if not execution_plan or not phases:
            return implementation_plan
        
        try:
            # Extract all commands from execution plan
            all_commands = []
            
            # Collect commands from execution plan attributes
            for attr_name in ['preparation_commands', 'optimization_commands', 'monitoring_commands', 
                            'security_commands', 'validation_commands']:
                if hasattr(execution_plan, attr_name):
                    commands = getattr(execution_plan, attr_name) or []
                    for cmd in commands:
                        command_dict = {
                            'id': getattr(cmd, 'id', f'cmd-{len(all_commands)}'),
                            'title': getattr(cmd, 'description', 'Generated Command'),
                            'command': getattr(cmd, 'command', ''),
                            'description': getattr(cmd, 'description', 'Generated command'),
                            'estimated_duration_minutes': getattr(cmd, 'estimated_duration_minutes', 5),
                            'risk_level': getattr(cmd, 'risk_level', 'Medium'),
                            'success_criteria': getattr(cmd, 'success_criteria', [])
                        }
                        all_commands.append(command_dict)
            
            # Distribute commands across phases
            if len(phases) >= 3 and len(all_commands) >= 3:
                commands_per_phase = max(1, len(all_commands) // len(phases))
                
                for i, phase in enumerate(phases):
                    start_idx = i * commands_per_phase
                    end_idx = start_idx + commands_per_phase
                    if i == len(phases) - 1:  # Last phase gets remaining
                        end_idx = len(all_commands)
                    
                    phase_commands = all_commands[start_idx:end_idx]
                    phase['commands'] = [{
                        'title': f"{phase['title']} Commands",
                        'commands': [cmd['command'] for cmd in phase_commands],
                        'description': f"Commands for {phase['title']}",
                        'command_details': phase_commands
                    }]
                    phase['total_commands'] = len(phase_commands)
            
            total_distributed = sum(len(phase.get('commands', [{}])[0].get('command_details', [])) for phase in phases)
            logger.info(f"✅ Command distribution: {total_distributed} commands across {len(phases)} phases")
            
            return implementation_plan
            
        except Exception as e:
            logger.error(f"❌ Command distribution failed: {e}")
            return implementation_plan

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _extract_config_insights(self, cluster_config: Dict) -> Dict[str, Any]:
        """Extract key insights from cluster configuration"""
        insights = {
            'cluster_complexity': 'unknown',
            'scaling_readiness': 'unknown',
            'security_posture': 'unknown'
        }
        
        try:
            # Simple complexity assessment
            workload_resources = cluster_config.get('workload_resources', {})
            total_workloads = sum(
                workload_data.get('item_count', 0) 
                for workload_data in workload_resources.values() 
                if isinstance(workload_data, dict)
            )
            
            if total_workloads > 20:
                insights['cluster_complexity'] = 'high'
            elif total_workloads > 10:
                insights['cluster_complexity'] = 'medium'
            else:
                insights['cluster_complexity'] = 'low'
            
            # Simple scaling readiness
            scaling_resources = cluster_config.get('scaling_resources', {})
            hpa_count = scaling_resources.get('horizontalpodautoscalers', {}).get('item_count', 0)
            deployments = workload_resources.get('deployments', {}).get('item_count', 0)
            
            if deployments > 0:
                hpa_coverage = hpa_count / deployments
                if hpa_coverage > 0.7:
                    insights['scaling_readiness'] = 'high'
                elif hpa_coverage > 0.3:
                    insights['scaling_readiness'] = 'medium'
                else:
                    insights['scaling_readiness'] = 'low'
            
            # Simple security posture
            security_resources = cluster_config.get('security_resources', {})
            rbac_count = sum(
                security_resources.get(resource, {}).get('item_count', 0)
                for resource in ['roles', 'clusterroles', 'rolebindings', 'clusterrolebindings']
            )
            
            if rbac_count > 20:
                insights['security_posture'] = 'enterprise'
            elif rbac_count > 5:
                insights['security_posture'] = 'standard'
            else:
                insights['security_posture'] = 'basic'
            
        except Exception as e:
            logger.warning(f"⚠️ Config insights extraction failed: {e}")
            insights['extraction_error'] = str(e)
        
        return insights

    def _count_execution_plan_commands(self, execution_plan: Any) -> int:
        """Count total commands in execution plan"""
        if not execution_plan:
            return 0
        
        total = 0
        command_attributes = ['preparation_commands', 'optimization_commands', 'validation_commands',
                            'monitoring_commands', 'security_commands']
        
        for attr in command_attributes:
            if hasattr(execution_plan, attr):
                commands = getattr(execution_plan, attr)
                total += len(commands) if commands else 0
        
        return total

    # =============================================================================
    # ML SYSTEM METHODS (UNCHANGED FOR COMPATIBILITY)
    # =============================================================================

    def _initialize_ml_systems(self):
        """Initialize ML intelligence systems"""
        logger.info("🔧 Initializing ML intelligence systems...")
        
        try:
            # Import ML modules
            from app.ml.learn_optimize import create_enhanced_learning_engine
            from app.ml.dynamic_strategy import EnhancedDynamicStrategyEngine
            from app.ml.dynamic_plan_generator import CombinedDynamicImplementationGenerator
            from app.ml.dna_analyzer import ClusterDNAAnalyzer
            from app.ml.ml_integration import MLSystemOrchestrator
            from app.ml.ml_framework_generator import create_ml_framework_generator
            
            # Initialize ML systems
            self.learning_engine = create_enhanced_learning_engine()
            self.ml_orchestrator = MLSystemOrchestrator(self.learning_engine)
            self.strategy_engine = EnhancedDynamicStrategyEngine()
            self.plan_generator = CombinedDynamicImplementationGenerator()
            self.dna_analyzer = ClusterDNAAnalyzer(enable_temporal_intelligence=True)
            
            # NEW: Initialize ML-driven framework generator
            self.ml_framework_generator = create_ml_framework_generator(self.learning_engine)
            
            # Connect components
            self.ml_orchestrator.connect_component('strategy_engine', self.strategy_engine)
            self.ml_orchestrator.connect_component('plan_generator', self.plan_generator)
            self.ml_orchestrator.connect_component('dna_analyzer', self.dna_analyzer)
            self.ml_orchestrator.connect_component('ml_framework_generator', self.ml_framework_generator)
            
            # Enable learning integration
            self.enable_learning_integration(self.ml_orchestrator)
            
            self.ml_systems_available = True
            logger.info("🎉 ML intelligence systems initialized successfully")
            
        except Exception as e:
            logger.error(f"💥 CRITICAL: ML system initialization failed: {e}")
            self.learning_engine = None
            self.ml_orchestrator = None
            self.strategy_engine = None
            self.plan_generator = None
            self.dna_analyzer = None
            self.ml_framework_generator = None
            self.ml_systems_available = False
            raise RuntimeError(f"❌ CRITICAL: Cannot initialize ML systems - {str(e)}")

    def _ml_analyze_cluster_dna(self, analysis_results: Dict, historical_data: Optional[Dict], 
                               ml_session: Dict, cluster_config: Dict) -> Any:
        """ML DNA analysis with cluster config"""
        if not self.dna_analyzer:
            raise RuntimeError("❌ DNA analyzer not available")
        
        try:
            cluster_dna = self.dna_analyzer.analyze_cluster_dna(
                analysis_results, historical_data, cluster_config
            )
            
            if cluster_dna is None:
                raise ValueError("❌ DNA analyzer returned None")
            
            ml_session['cluster_dna'] = cluster_dna
            confidence = self._extract_dna_confidence(cluster_dna)
            ml_session['ml_confidence_levels']['dna_analysis'] = confidence
            
            return cluster_dna
            
        except Exception as e:
            raise RuntimeError(f"❌ DNA analysis failed: {e}") from e

    def _ml_generate_strategy(self, cluster_dna: Any, analysis_results: Dict, 
                             ml_session: Dict, cluster_config: Dict) -> Any:
        """ML strategy generation"""
        if not self.strategy_engine:
            raise RuntimeError("❌ Strategy engine not available")
        
        try:
            ml_strategy = self.strategy_engine.generate_comprehensive_dynamic_strategy(
                cluster_dna, analysis_results, cluster_config
            )
            
            if ml_strategy is None:
                raise ValueError("❌ Strategy engine returned None")
            
            ml_session['ml_strategy'] = ml_strategy
            confidence = getattr(ml_strategy, 'success_probability', 0.8)
            ml_session['ml_confidence_levels']['strategy_generation'] = confidence
            
            return ml_strategy
            
        except Exception as e:
            raise RuntimeError(f"❌ Strategy generation failed: {e}") from e

    def _ml_generate_comprehensive_plan(self, analysis_results: Dict, ml_strategy: Any, 
                                       cluster_dna: Any, ml_session: Dict, 
                                       cluster_config: Dict) -> Dict:
        """Generate comprehensive plan"""
        if not self.plan_generator:
            raise RuntimeError("❌ Plan generator not available")
        
        try:
            ml_plan = self.plan_generator.generate_extensive_implementation_plan(
                analysis_results, cluster_dna, ml_strategy, cluster_config
            )
            
            if ml_plan is None or not isinstance(ml_plan, dict):
                raise ValueError("❌ Plan generator returned invalid result")
            
            # Convert plan object to dict if necessary
            if not isinstance(ml_plan, dict):
                if hasattr(ml_plan, 'to_dict') and callable(getattr(ml_plan, 'to_dict')):
                    ml_plan = ml_plan.to_dict()
                elif hasattr(ml_plan, '__dict__'):
                    ml_plan = ml_plan.__dict__.copy()
                else:
                    raise ValueError(f"❌ Plan generator returned invalid type: {type(ml_plan)}")
                
            # Normalize phases key
            if 'phases' in ml_plan and 'implementation_phases' not in ml_plan:
                ml_plan['implementation_phases'] = ml_plan['phases']
            
            if 'implementation_phases' not in ml_plan:
                raise ValueError("❌ Plan missing 'implementation_phases' key")
            
            confidence = ml_plan.get('metadata', {}).get('ml_confidence', 0.8)
            ml_session['ml_confidence_levels']['plan_generation'] = confidence
            
            # Debug: Check what's actually in costProtection before returning
            if 'costProtection' in ml_plan:
                logger.info(f"🔍 FINAL costProtection check: {ml_plan['costProtection']}")
            else:
                logger.info("🔍 FINAL costProtection: MISSING!")

            return ml_plan
            
        except Exception as e:
            raise RuntimeError(f"❌ Plan generation failed: {e}") from e

    def _ensure_complete_framework_structure(self, implementation_plan: Dict, 
                                    analysis_results: Dict, ml_session: Dict,
                                    cluster_config: Dict) -> Dict:
        """Generate framework structure using PURE ML"""
        if implementation_plan is None:
            raise ValueError("❌ Cannot complete framework - implementation_plan is None")
        
        logger.info("🤖 Generating framework structure using PURE ML...")
        
        try:
            # Validate ML system availability
            if not hasattr(self, 'ml_framework_generator') or self.ml_framework_generator is None:
                raise RuntimeError("❌ ML Framework Generator not available")
            
            # Extract required data
            cluster_dna = ml_session.get('cluster_dna')
            comprehensive_state = ml_session.get('comprehensive_state', {})
            
            if cluster_dna is None:
                raise ValueError("❌ Cluster DNA not available for ML framework generation")
            
            # Generate PURE ML-driven framework structure
            logger.info("🧠 Generating ML-driven framework structure...")
            ml_framework_structure = self.ml_framework_generator.generate_ml_framework_structure(
                cluster_dna, analysis_results, ml_session, comprehensive_state
            )
            
            # Validate ML structure
            if not ml_framework_structure or not isinstance(ml_framework_structure, dict):
                raise ValueError("❌ ML Framework Generator returned invalid structure")
            
            # Merge ML structure into implementation plan
            implementation_plan.update(ml_framework_structure)
            
            # Validate all required components are present
            required_components = [
                'costProtection', 'governance', 'monitoring', 'contingency',
                'successCriteria', 'timelineOptimization', 'riskMitigation', 'intelligenceInsights'
            ]
            
            missing_components = [comp for comp in required_components if comp not in implementation_plan]
            if missing_components:
                raise ValueError(f"❌ ML Framework missing components: {missing_components}")
            
            # Calculate overall ML confidence
            overall_ml_confidence = self._calculate_ml_framework_confidence(ml_framework_structure)
            
            # Add ML metadata
            implementation_plan['ml_framework_metadata'] = {
                'pure_ml_generated': True,
                'ml_confidence': overall_ml_confidence,
                'generation_timestamp': datetime.now().isoformat(),
                'ml_framework_version': '1.0.0',
                'components_generated': len(required_components)
            }
            
            # Record successful ML framework generation
            ml_session['learning_events'].append({
                'event': 'pure_ml_framework_generated',
                'success': True,
                'components_count': len(required_components),
                'ml_confidence': overall_ml_confidence
            })
            
            logger.info("✅ PURE ML Framework Structure Generated Successfully")
            logger.info(f"   🤖 ML Confidence: {overall_ml_confidence:.1%}")
            
            return implementation_plan
            
        except Exception as e:
            logger.error(f"❌ PURE ML Framework generation failed: {e}")
            
            # Record failure for learning
            ml_session['learning_events'].append({
                'event': 'pure_ml_framework_generation_failed',
                'success': False,
                'error': str(e)
            })
            
            # NO FALLBACKS - Fail fast if ML can't generate structure
            raise RuntimeError(f"❌ PURE ML Framework generation failed: {e}") from e

    # =============================================================================
    # VALIDATION & UTILITY METHODS
    # =============================================================================

    def _validate_input_data(self, analysis_results: Dict) -> bool:
        """Validate input data"""
        if not analysis_results or not isinstance(analysis_results, dict):
            return False
        
        if 'total_cost' not in analysis_results:
            return False
        
        value = analysis_results['total_cost']
        return isinstance(value, (int, float)) and value >= 0

    def _validate_output_structure(self, implementation_plan: Dict) -> bool:
        """Validate output structure"""
        if not isinstance(implementation_plan, dict):
            return False
        
        if 'implementation_phases' not in implementation_plan:
            return False
        
        if not isinstance(implementation_plan['implementation_phases'], list):
            return False
        
        framework_components = ['costProtection', 'governance', 'monitoring', 
                              'contingency', 'successCriteria', 'timelineOptimization', 
                              'riskMitigation']
        
        for component in framework_components:
            if component not in implementation_plan:
                return False
            if not implementation_plan[component].get('enabled', False):
                return False
        
        return True

    def _calculate_ml_plan_confidence(self, analysis_results: Dict, implementation_plan: Dict, 
                                     ml_session: Dict, cluster_config: Dict) -> float:
        """Calculate ML plan confidence"""
        confidence_factors = []
        
        # ML system confidence levels
        ml_confidences = list(ml_session['ml_confidence_levels'].values())
        if ml_confidences:
            confidence_factors.append(sum(ml_confidences) / len(ml_confidences))
        
        # Data quality factor
        if analysis_results.get('total_cost', 0) > 0:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.3)
        
        # Cluster config quality factor
        if cluster_config.get('status') == 'completed':
            config_success_rate = 0.8
            confidence_factors.append(config_success_rate)
        else:
            confidence_factors.append(0.5)
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        implementation_plan['ml_confidence'] = overall_confidence
        
        return overall_confidence

    def _calculate_ml_framework_confidence(self, ml_framework_structure: Dict) -> float:
        """Calculate overall ML framework confidence"""
        confidences = []
        
        for component_name, component_data in ml_framework_structure.items():
            if isinstance(component_data, dict):
                ml_confidence = component_data.get('ml_confidence')
                if ml_confidence is not None:
                    confidences.append(float(ml_confidence))
        
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _extract_dna_confidence(self, cluster_dna: Any) -> float:
        """Extract confidence from DNA analysis"""
        if hasattr(cluster_dna, 'temporal_readiness_score'):
            return cluster_dna.temporal_readiness_score
        elif hasattr(cluster_dna, 'optimization_readiness_score'):
            return cluster_dna.optimization_readiness_score
        else:
            return 0.8

    def _start_ml_session(self, analysis_results: Dict) -> Dict:
        """Start ML intelligence session"""
        session = {
            'session_id': f"ml-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'cluster_name': analysis_results.get('cluster_name', 'unknown'),
            'started_at': datetime.now(),
            'ml_confidence_levels': {},
            'learning_events': [],
            'ml_systems_available': self.ml_systems_available
        }
        
        self._current_ml_session = session
        return session

    def _record_ml_learning_outcomes(self, implementation_plan: Dict, ml_session: Dict, confidence: float):
        """Record ML learning outcomes"""
        try:
            if self.learning_engine and self.ml_orchestrator:
                learning_result = {
                    'execution_id': ml_session['session_id'],
                    'cluster_name': ml_session['cluster_name'],
                    'success': True,
                    'confidence': confidence,
                    'phases_count': len(implementation_plan.get('implementation_phases', [])),
                    'learning_events': ml_session['learning_events'],
                    'framework_ml_generated': implementation_plan.get('ml_framework_metadata', {}).get('pure_ml_generated', False),
                    'framework_confidence': implementation_plan.get('ml_framework_metadata', {}).get('ml_confidence', 0.0)
                }
                
                self.ml_orchestrator.learn_from_implementation_result(learning_result)
                
                # Framework-specific learning
                if hasattr(self, 'ml_framework_generator') and self.ml_framework_generator:
                    framework_outcome = {
                        'total_cost': implementation_plan.get('executiveSummary', {}).get('current_monthly_cost', 0),
                        'actual_savings': implementation_plan.get('executiveSummary', {}).get('projected_monthly_savings', 0),
                        'implementation_success': learning_result['success'],
                        'framework_ml_confidence': learning_result['framework_confidence']
                    }
                    
                    self.ml_framework_generator.learn_from_implementation_outcome(framework_outcome)
                    logger.info("📈 Framework ML models updated")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to record ML learning outcomes: {e}")

    def _finalize_ml_session(self, ml_session: Dict, implementation_plan: Dict, confidence: float):
        """Finalize ML session"""
        if 'metadata' not in implementation_plan:
            implementation_plan['metadata'] = {}
        
        implementation_plan['metadata']['ml_session_id'] = ml_session['session_id']
        implementation_plan['metadata']['ml_confidence'] = confidence
        implementation_plan['metadata']['generated_at'] = datetime.now().isoformat()
        implementation_plan['metadata']['version'] = '4.0.0-refactored'
        
        self._ml_sessions_history.append(ml_session)
        self._current_ml_session = None

    def _log_complete_failure_details(self, exception: Exception, analysis_results: Dict, local_vars: Dict):
        """Log failure details for debugging"""
        logger.error(f"💥 COMPLETE FAILURE: {type(exception).__name__}: {str(exception)}")
        logger.error(f"💥 Traceback:\n{traceback.format_exc()}")

    def _record_generation_failure(self, error: str):
        """Record generation failure for learning"""
        if getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('generation_failed', {
                'error': error,
                'timestamp': datetime.now().isoformat()
            })


# Backward compatibility - maintain exact same names and signatures
CombinedAKSImplementationGenerator = AKSImplementationGenerator
FixedAKSImplementationGenerator = AKSImplementationGenerator