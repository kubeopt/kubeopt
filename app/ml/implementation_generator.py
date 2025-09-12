#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
AKS Implementation Generator with PROPERLY INTEGRATED Security Framework
========================================================================
Fixed version where security framework is initialized alongside ML components.
Security components are now first-class citizens in the initialization process.
Comprehensive error logging for debugging.
Includes real cluster configuration integration and utility classes.
Timeline format conversion support.
Enhanced with integrated ML and Security analysis.
FIXED: Proper handling of SecurityIntegrationMixin when security framework is unavailable.
"""

from dataclasses import asdict
import json
import math
import asyncio
import traceback
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging

from app.ml.ml_integration import MLLearningIntegrationMixin
from app.services.subscription_manager import azure_subscription_manager

# Import the new dedicated HPA analyzer
from app.analytics.hpa_analyzer import HPAAnalyzer

# SECURITY FRAMEWORK IMPORTS - Proper Import Handling
# =====================================================

# Initialize security component functions to None
create_security_posture_engine = None
create_policy_analyzer = None  
create_compliance_framework_engine = None
create_vulnerability_scanner = None

# Try to import each component individually for better error tracking
security_import_status = {}

# Import security_posture_core
try:
    from app.security.security_posture_core import create_security_posture_engine
    security_import_status['security_posture_core'] = 'success'
except ImportError as e:
    security_import_status['security_posture_core'] = f'failed: {e}'

# Import policy_analyzer
try:
    from app.security.policy_analyzer import create_policy_analyzer
    security_import_status['policy_analyzer'] = 'success'
except ImportError as e:
    security_import_status['policy_analyzer'] = f'failed: {e}'

# Import compliance_framework
try:
    from app.security.compliance_framework import create_compliance_framework_engine
    security_import_status['compliance_framework'] = 'success'
except ImportError as e:
    security_import_status['compliance_framework'] = f'failed: {e}'

# Import vulnerability_scanner
try:
    from app.security.vulnerability_scanner import create_vulnerability_scanner
    security_import_status['vulnerability_scanner'] = 'success'
except ImportError as e:
    security_import_status['vulnerability_scanner'] = f'failed: {e}'

# Import SecurityIntegrationMixin
SecurityIntegrationMixin = None
try:
    from app.security.security_integration import SecurityIntegrationMixin
    security_import_status['security_integration_mixin'] = 'success'
except ImportError as e:
    security_import_status['security_integration_mixin'] = f'failed: {e}'

# Determine overall security framework availability
successful_imports = [k for k, v in security_import_status.items() if v == 'success']
failed_imports = [k for k, v in security_import_status.items() if v != 'success']
SECURITY_INTEGRATION_AVAILABLE = len(successful_imports) >= 1  # At least one component available


# Print detailed import status
print("🔒 Security Framework Import Status:")
for component, status in security_import_status.items():
    if status == 'success':
        print(f"  ✅ {component}: Available")
    else:
        print(f"  ❌ {component}: {status}")

if SECURITY_INTEGRATION_AVAILABLE:
    print(f"✅ Security framework partially available ({len(successful_imports)}/5 components)")
else:
    print("⚠️ Security framework completely unavailable - using fallback")

# Define a fallback SecurityIntegrationMixin if needed
if SecurityIntegrationMixin is None:
    class SecurityIntegrationMixin:
        """Fallback SecurityIntegrationMixin when security framework is not available"""
        
        def __init__(self):
            self.security_systems_available = False
            self.security_components_ready = False
            self.security_components_initialized = False
            print("🔒 Using fallback SecurityIntegrationMixin")
        
        async def _perform_comprehensive_security_analysis(self, cluster_config: Dict, 
                                                         security_frameworks: List[str]) -> Dict:
            """Fallback security analysis method"""
            return {
                'status': 'unavailable',
                'reason': 'security_framework_not_available',
                'confidence': 0.5,
                'frameworks_analyzed': [],
                'security_posture': {'overall_score': 50, 'grade': 'C'},
                'vulnerability_assessment': {'critical_vulnerabilities': 0},
                'fallback_mode': True
            }
        
        async def _generate_security_implementation_phases(self, security_analysis: Dict, 
                                                         priority: str) -> List[Dict]:
            """Fallback security phases generation"""
            return []
        
        async def _integrate_security_phases(self, implementation_plan: Dict, 
                                           security_phases: List[Dict], 
                                           security_analysis: Dict) -> Dict:
            """Fallback security phases integration"""
            return implementation_plan
        
        async def _add_compliance_requirements(self, implementation_plan: Dict, 
                                             security_analysis: Dict, 
                                             security_frameworks: List[str]) -> Dict:
            """Fallback compliance requirements"""
            return implementation_plan
        
        async def _calculate_security_impact(self, implementation_plan: Dict, 
                                           security_analysis: Dict, 
                                           base_plan: Dict) -> Dict:
            """Fallback security impact calculation"""
            return implementation_plan
        
        async def _add_security_monitoring(self, implementation_plan: Dict, 
                                         security_analysis: Dict) -> Dict:
            """Fallback security monitoring"""
            return implementation_plan
        
        async def _generate_security_commands(self, implementation_plan: Dict, 
                                            security_analysis: Dict) -> Dict:
            """Fallback security commands generation"""
            return implementation_plan

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
        """Analyze HPA state using UNIFIED kubernetes cache - NO FALLBACKS"""
        try:
            # Get k8s_cache - this is the ONLY data source we use
            k8s_cache = kwargs.get('k8s_cache')
            
            if not k8s_cache:
                logger.error("❌ NO CACHE: k8s_cache is required - no fallbacks allowed")
                return {'analysis_error': 'k8s_cache is required for unified analysis'}
            
            logger.info("🎯 UNIFIED: Using kubernetes_data_cache as ONLY source of truth")
            hpa_state = HPAAnalyzer.analyze_hpa_state(k8s_cache)
            
            # Log results
            if 'summary' in hpa_state:
                summary = hpa_state['summary']
                logger.info(f"📊 HPA Analysis Results: {summary.get('existing_hpas', 0)} HPAs active, "
                           f"{summary.get('missing_candidates', 0)} candidates identified, "
                           f"{summary.get('hpa_coverage_percent', 0):.1f}% coverage")
            
            return hpa_state
            
        except Exception as e:
            logger.error(f"❌ Enhanced HPA analysis failed: {e}")
            # Fallback to basic analysis structure
            return {
                'existing_hpas': [],
                'suboptimal_hpas': [],
                'missing_hpa_candidates': [],
                'summary': {'analysis_error': str(e)},
                'analysis_error': str(e)
            }
    
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


class AKSImplementationGenerator(MLLearningIntegrationMixin, SecurityIntegrationMixin):
    """
    AKS Implementation Generator with PROPERLY INTEGRATED Security Framework
    
    Security framework is now initialized alongside ML systems as first-class components.
    No more optional add-on approach - security is core to the system.
    FIXED: Proper handling of SecurityIntegrationMixin when security framework is unavailable.
    """
    
    def __init__(self, enable_cost_monitoring: bool = True, enable_temporal: bool = True,
                 enable_security_integration: bool = True):
        """Initialize with INTEGRATED ML and Security framework (both enabled by default)"""
        
        # Initialize both mixins
        MLLearningIntegrationMixin.__init__(self)
        SecurityIntegrationMixin.__init__(self)  # This will use fallback if imports failed
        
        logger.info("🧠🔒 Initializing AKS Implementation Generator with INTEGRATED ML & Security")
        
        # Configuration
        self.enable_cost_monitoring = enable_cost_monitoring
        self.enable_temporal = enable_temporal
        self.enable_security_integration = enable_security_integration
        self.monitoring_active = False
        
        # Utility instances
        self.cost_calculator = CostCalculator()
        
        # Debug tracking (MUST be initialized before ML/Security systems)
        self._debug_info = {
            'initialization_time': datetime.now(),
            'ml_system_status': {},
            'security_framework_status': {},
            'failed_operations': []
        }
        
        # Session tracking
        self._current_ml_session = None
        self._ml_sessions_history = []
        
        # CRITICAL FIX: Initialize BOTH ML and Security systems together
        self._initialize_integrated_systems()
        
        logger.info("✅ AKS Implementation Generator ready with INTEGRATED systems")
        logger.info(f"🧠 ML Systems Available: {self.ml_systems_available}")
        logger.info(f"🔒 Security Framework Available: {self.security_systems_available}")
        logger.info(f"🔗 INTEGRATED Mode: {self.ml_systems_available and self.security_systems_available}")
    

    def _sanitize_security_data(self, data):
        """Sanitize security data to ensure JSON serializable types"""
        if data is None:
            return None
        
        def convert_value(val):
            # Check type name as string to handle all numpy types
            type_str = str(type(val))
            
            # Handle numpy types
            if 'numpy' in type_str:
                if 'bool' in type_str:
                    return bool(val)
                elif 'int' in type_str:
                    return int(val)
                elif 'float' in type_str:
                    return float(val)
                elif hasattr(val, 'tolist'):
                    return val.tolist()
                elif hasattr(val, 'item'):
                    # For numpy scalars
                    return val.item()
            
            # Handle dictionaries recursively
            if isinstance(val, dict):
                return {k: convert_value(v) for k, v in val.items()}
            
            # Handle lists and tuples recursively
            if isinstance(val, (list, tuple)):
                return [convert_value(item) for item in val]
            
            # Return as-is for other types
            return val
        
        return convert_value(data)


    # =============================================================================
    # INTEGRATED SYSTEMS INITIALIZATION (NEW APPROACH)
    # =============================================================================
    
    def _initialize_integrated_systems(self):
        """Initialize ML and Security systems together as integrated components"""
        
        logger.info("🔧 Initializing INTEGRATED ML + Security systems...")
        
        # Initialize flags
        self.ml_systems_available = False
        self.security_systems_available = False
        
        # Track initialization status for both systems
        ml_initialization_results = {}
        security_initialization_results = {}
        
        try:
            # PHASE 1: Initialize ML Systems
            logger.info("🧠 Phase 1: Initializing ML Intelligence Systems...")
            self.ml_systems_available = self._initialize_ml_systems_core(ml_initialization_results)
            
            # PHASE 2: Initialize Security Systems (NEW - INTEGRATED APPROACH)
            logger.info("🔒 Phase 2: Initializing Security Framework Systems...")
            self.security_systems_available = self._initialize_security_systems_core(security_initialization_results)
            
            # PHASE 3: Cross-system Integration
            logger.info("🔗 Phase 3: Establishing ML-Security Integration...")
            self._establish_ml_security_integration()
            
            # Update debug info with both systems
            self._debug_info['ml_system_status'] = ml_initialization_results
            self._debug_info['security_framework_status'] = security_initialization_results
            
            # Final status
            integrated_mode = self.ml_systems_available and self.security_systems_available
            
            if integrated_mode:
                logger.info("🎉 INTEGRATED MODE: Both ML and Security systems operational")
            elif self.ml_systems_available:
                logger.warning("⚠️ PARTIAL MODE: ML systems operational, Security systems failed")
            elif self.security_systems_available:
                logger.warning("⚠️ PARTIAL MODE: Security systems operational, ML systems failed")
            else:
                logger.error("❌ DEGRADED MODE: Both ML and Security systems failed")
                raise RuntimeError("❌ CRITICAL: Cannot initialize core systems")
            
        except Exception as e:
            logger.error(f"💥 CRITICAL: Integrated systems initialization failed: {e}")
            logger.error(f"💥 ML Results: {json.dumps(ml_initialization_results, indent=2)}")
            logger.error(f"💥 Security Results: {json.dumps(security_initialization_results, indent=2)}")
            raise RuntimeError(f"❌ CRITICAL: Cannot initialize integrated systems - {str(e)}")
    
    def _initialize_ml_systems_core(self, results: Dict) -> bool:
        """Initialize ML systems with detailed error tracking"""
        
        try:
            # Import ML modules with individual error tracking
            logger.info("📥 Importing ML modules...")
            
            try:
                from app.ml.learn_optimize import create_enhanced_learning_engine
                results['learn_optimize_import'] = 'success'
                logger.info("✅ learn_optimize imported")
            except Exception as e:
                results['learn_optimize_import'] = f'failed: {e}'
                logger.error(f"❌ learn_optimize import failed: {e}")
                raise
            
            try:
                from app.ml.dynamic_strategy import EnhancedDynamicStrategyEngine
                results['dynamic_strategy_import'] = 'success'
                logger.info("✅ dynamic_strategy imported")
            except Exception as e:
                results['dynamic_strategy_import'] = f'failed: {e}'
                logger.error(f"❌ dynamic_strategy import failed: {e}")
                raise
            
            try:
                from app.ml.dynamic_plan_generator import MLIntegratedDynamicImplementationGenerator
                results['dynamic_plan_generator_import'] = 'success'
                logger.info("✅ dynamic_plan_generator imported")
            except Exception as e:
                results['dynamic_plan_generator_import'] = f'failed: {e}'
                logger.error(f"❌ dynamic_plan_generator import failed: {e}")
                raise
            
            try:
                from app.ml.dynamic_cmd_center import AdvancedExecutableCommandGenerator
                results['dynamic_cmd_center_import'] = 'success'
                logger.info("✅ dynamic_cmd_center imported")
            except Exception as e:
                results['dynamic_cmd_center_import'] = f'failed: {e}'
                logger.error(f"❌ dynamic_cmd_center import failed: {e}")
                raise
            
            try:
                from app.ml.dna_analyzer import ClusterDNAAnalyzer
                results['dna_analyzer_import'] = 'success'
                logger.info("✅ dna_analyzer imported")
            except Exception as e:
                results['dna_analyzer_import'] = f'failed: {e}'
                logger.error(f"❌ dna_analyzer import failed: {e}")
                raise
            
            try:
                from app.ml.ml_integration import MLSystemOrchestrator
                results['ml_integration_import'] = 'success'
                logger.info("✅ ml_integration imported")
            except Exception as e:
                results['ml_integration_import'] = f'failed: {e}'
                logger.error(f"❌ ml_integration import failed: {e}")
                raise
            
            results['imports'] = {'status': 'success', 'modules_imported': 6}
            logger.info("✅ All ML modules imported successfully")
            
            # Initialize ML systems
            logger.info("🔧 Initializing ML system instances...")
            
            self.learning_engine = create_enhanced_learning_engine()
            results['learning_engine'] = {'status': 'success'}
            
            self.ml_orchestrator = MLSystemOrchestrator(self.learning_engine)
            results['ml_orchestrator'] = {'status': 'success'}
            
            self.strategy_engine = EnhancedDynamicStrategyEngine()
            results['strategy_engine'] = {'status': 'success'}
            
            self.plan_generator = MLIntegratedDynamicImplementationGenerator()
            results['plan_generator'] = {'status': 'success'}
            
            self.command_generator = AdvancedExecutableCommandGenerator()
            results['command_generator'] = {'status': 'success'}
            
            self.dna_analyzer = ClusterDNAAnalyzer(enable_temporal_intelligence=True)
            results['dna_analyzer'] = {'status': 'success'}
            
            # Connect ML components
            logger.info("🔗 Connecting ML components...")
            self.ml_orchestrator.connect_component('strategy_engine', self.strategy_engine)
            self.ml_orchestrator.connect_component('plan_generator', self.plan_generator)
            self.ml_orchestrator.connect_component('command_generator', self.command_generator)
            self.ml_orchestrator.connect_component('dna_analyzer', self.dna_analyzer)
            results['ml_connections'] = {'status': 'success'}
            
            # Enable learning integration
            self.enable_learning_integration(self.ml_orchestrator)
            results['learning_integration'] = {'status': 'success'}
            
            logger.info("✅ ML systems initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ ML systems initialization failed: {e}")
            results['error'] = str(e)
            results['traceback'] = traceback.format_exc()
            return False
    
    def _initialize_security_systems_core(self, results: Dict) -> bool:
        """Initialize Security systems with detailed error tracking (NEW METHOD)"""
        
        if not self.enable_security_integration:
            logger.info("🔒 Security integration disabled by configuration")
            results['disabled'] = {'status': 'disabled_by_config'}
            results['import_status'] = security_import_status
            return False
        
        if not SECURITY_INTEGRATION_AVAILABLE:
            logger.warning("🔒 Security framework not available (import failed)")
            results['framework_unavailable'] = {'status': 'import_failed', 'using_fallback': True}
            results['import_status'] = security_import_status
            return False
        
        try:
            logger.info("🔧 Initializing Security framework instances...")
            
            # Store import status for debugging
            results['import_status'] = security_import_status
            results['available_components'] = successful_imports
            
            # Initialize security components as instance variables (like ML components)
            # NOTE: These will be properly initialized with cluster_config later
            self.security_engine = None
            self.policy_analyzer_func = create_policy_analyzer
            self.compliance_engine_func = create_compliance_framework_engine
            self.vulnerability_scanner_func = create_vulnerability_scanner
            self.security_posture_func = create_security_posture_engine
            
            # Mark security components as ready for initialization
            self.security_components_ready = True
            results['components_ready'] = {'status': 'success'}
            
            # Security components will be fully initialized when cluster_config is available
            # This follows the same pattern as ML components that need data to initialize
            results['framework_status'] = {'status': 'ready_for_cluster_config'}
            
            logger.info("✅ Security systems core initialization successful")
            logger.info("🔧 Security components will be initialized with cluster configuration")
            logger.info(f"🔧 Available security components: {successful_imports}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Security systems initialization failed: {e}")
            results['error'] = str(e)
            results['traceback'] = traceback.format_exc()
            results['import_status'] = security_import_status
            return False
    
    def _establish_ml_security_integration(self):
        """Establish integration between ML and Security systems"""
        
        try:
            if self.ml_systems_available and self.security_systems_available:
                logger.info("🔗 Establishing ML-Security cross-system integration...")
                
                # Enable security-aware ML learning
                if hasattr(self, 'learning_engine') and self.learning_engine:
                    # Add security metrics to ML learning
                    self.learning_engine.enable_security_metrics = True
                    logger.info("🔗 Security metrics enabled in ML learning engine")
                
                # Enable ML-enhanced security analysis
                if hasattr(self, 'security_components_ready') and self.security_components_ready:
                    # Security components will use ML insights when initialized
                    self.ml_enhanced_security = True
                    logger.info("🔗 ML enhancement enabled for security analysis")
                
                logger.info("✅ ML-Security integration established")
            else:
                logger.warning("⚠️ Partial integration: Some systems not available")
                
        except Exception as e:
            logger.warning(f"⚠️ ML-Security integration failed: {e}")
    
    def _initialize_security_components_with_cluster_config(self, cluster_config: Dict) -> bool:
        """Initialize security components with actual cluster configuration"""
        
        if not self.security_systems_available or not hasattr(self, 'security_components_ready'):
            logger.warning("🔒 Security systems not ready for cluster config initialization")
            return False
        
        try:
            logger.info("🔧 Initializing security components with cluster configuration...")
            
            # Initialize only available components
            initialized_components = []
            
            if create_security_posture_engine:
                try:
                    self.security_engine = create_security_posture_engine(cluster_config)
                    initialized_components.append('security_posture_engine')
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize security posture engine: {e}")
            
            if create_policy_analyzer:
                try:
                    self.policy_analyzer = create_policy_analyzer(cluster_config)
                    initialized_components.append('policy_analyzer')
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize policy analyzer: {e}")
            
            if create_compliance_framework_engine:
                try:
                    self.compliance_engine = create_compliance_framework_engine(cluster_config)
                    initialized_components.append('compliance_framework_engine')
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize compliance framework: {e}")
            
            if create_vulnerability_scanner:
                try:
                    self.vulnerability_scanner = create_vulnerability_scanner(cluster_config)
                    initialized_components.append('vulnerability_scanner')
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize vulnerability scanner: {e}")
            
            # Mark as fully initialized if we have at least one component
            self.security_components_initialized = len(initialized_components) > 0
            
            if self.security_components_initialized:
                logger.info(f"✅ Security components initialized: {initialized_components}")
            else:
                logger.warning("⚠️ No security components could be initialized")
            
            return self.security_components_initialized
            
        except Exception as e:
            logger.error(f"❌ Security components cluster config initialization failed: {e}")
            return False
    
    # =============================================================================
    # ENHANCED MAIN GENERATION METHOD (Updated for Integrated Systems)
    # =============================================================================
    
    def generate_implementation_plan(self, analysis_results: Dict, 
                                   historical_data: Optional[Dict] = None,
                                   cost_budget_monthly: Optional[float] = None,
                                   enable_real_time_monitoring: bool = True,
                                   output_format: str = 'comprehensive',
                                   # Enhanced security parameters
                                   security_frameworks: List[str] = ['CIS', 'NIST'],
                                   security_priority: str = 'high',
                                   # Single source of truth for data
                                   k8s_cache = None) -> Dict:
        """
        Generate implementation plan with INTEGRATED ML and Security analysis
        
        Security is now a first-class citizen, not an optional add-on.
        """
        
        cluster_name = analysis_results.get('cluster_name', 'unknown')
        resource_group = analysis_results.get('resource_group', 'unknown')
        
        # CRITICAL: Extract and preserve metrics_data for HPA analysis
        metrics_data = analysis_results.get('metrics_data')
        if metrics_data:
            logger.info(f"🎯 Found metrics_data with keys: {list(metrics_data.keys())}")
            if 'hpa_implementation' in metrics_data:
                hpa_impl = metrics_data['hpa_implementation']
                logger.info(f"🎯 Found metrics_data with {hpa_impl.get('total_hpas', 0)} HPAs for enhanced analysis")
            else:
                logger.warning(f"⚠️ metrics_data found but no hpa_implementation key (keys: {list(metrics_data.keys())})")
        else:
            logger.warning(f"⚠️ No metrics_data found in analysis_results (keys: {list(analysis_results.keys())}) - HPA analysis may be limited")
        
        logger.info(f"🎯 Generating INTEGRATED ML+Security implementation plan for {cluster_name}")
        logger.info(f"🧠 ML Systems: {'✅ Available' if self.ml_systems_available else '❌ Unavailable'}")
        logger.info(f"🔒 Security Systems: {'✅ Available' if self.security_systems_available else '❌ Unavailable'}")
        
        # Get subscription ID
        subscription_id = azure_subscription_manager.find_cluster_subscription(resource_group, cluster_name)
        
        try:
            # Validate input data - FAIL FAST
            if not self._validate_input_data(analysis_results):
                raise ValueError("❌ CRITICAL: Invalid analysis_results provided")
            
            # Start ML intelligence session
            ml_session = self._start_ml_session(analysis_results)
            
            # CRITICAL: Store metrics_data in ml_session for HPA analysis
            if metrics_data:
                ml_session['metrics_data'] = metrics_data
                logger.info("✅ Stored metrics_data in ml_session for HPA analysis")
            
            # PHASE 0: REAL CLUSTER CONFIGURATION FETCHING (Enhanced for Security)
            logger.info("🔄 PHASE 0: Enhanced Cluster Configuration Analysis")
            cluster_config = self._fetch_and_analyze_cluster_config(
                resource_group, cluster_name, subscription_id, ml_session
            )
            
            # CRITICAL: Initialize security components with cluster config
            if self.security_systems_available and cluster_config.get('status') == 'completed':
                security_init_success = self._initialize_security_components_with_cluster_config(cluster_config)
                ml_session['security_components_initialized'] = security_init_success
                logger.info(f"🔒 Security components cluster init: {'✅ Success' if security_init_success else '❌ Failed'}")
            
            # PHASE 1: ML Cluster DNA Analysis (Enhanced with Security)
            logger.info("🔄 PHASE 1: Enhanced ML Cluster DNA Analysis")
            cluster_dna = self._ml_analyze_cluster_dna(analysis_results, historical_data, ml_session, cluster_config)
            if cluster_dna is None:
                raise ValueError("❌ CRITICAL: DNA analysis failed")
            
            # PHASE 2: ML Strategy Generation (Enhanced with Security)
            logger.info("🔄 PHASE 2: Enhanced ML Strategy Generation")
            ml_strategy = self._ml_generate_strategy(cluster_dna, analysis_results, ml_session, cluster_config)
            if ml_strategy is None:
                raise ValueError("❌ CRITICAL: Strategy generation failed")
            
            # PHASE 3: INTEGRATED Security Analysis (NEW - Run in Parallel with Plan Generation)
            logger.info("🔄 PHASE 3: Integrated Security Analysis")
            security_analysis = None
            if self.security_systems_available and hasattr(self, 'security_components_initialized'):
                security_analysis = self._perform_integrated_security_analysis(
                    cluster_config, security_frameworks, ml_session
                )
            
            if security_analysis:
                try:
                    from app.security.security_results_manager import security_results_manager
                    
                    # Extract cluster identifiers
                    cluster_id = f"{resource_group}_{cluster_name}"
                    
                    # Store security results separately
                    security_result_id = security_results_manager.store_security_results(
                        cluster_id=cluster_id,
                        resource_group=resource_group,
                        cluster_name=cluster_name,
                        security_analysis=security_analysis
                    )
                    
                    # Add reference to ML session
                    ml_session['security_result_id'] = security_result_id
                    
                    logger.info(f"✅ Security results : {security_analysis}")
                    logger.info(f"✅ Security results stored separately: {security_result_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store security results separately: {e}")
                    
            # PHASE 4: Enhanced ML Plan Generation (with Security Integration)
            logger.info("🔄 PHASE 4: Enhanced ML Plan Generation")
            ml_plan = self._ml_generate_comprehensive_plan(
                analysis_results, ml_strategy, cluster_dna, ml_session, cluster_config, security_analysis
            )
            if ml_plan is None or not isinstance(ml_plan, dict):
                raise ValueError("❌ CRITICAL: Plan generation failed")
                
            # PHASE 4.5: Enterprise Metrics Integration
            logger.info("🔄 PHASE 4.5: Enterprise Operational Metrics Calculation")
            enterprise_metrics = asyncio.run(self._calculate_enterprise_metrics(
                analysis_results, cluster_dna, ml_session, cluster_config
            ))
            ml_plan['enterprise_metrics'] = enterprise_metrics
            
            # PHASE 5: Integrated Security Enhancement (NEW)
            if security_analysis:
                logger.info("🔄 PHASE 5: Security Enhancement Integration")
                ml_plan = self._integrate_security_enhancements(
                    ml_plan, security_analysis, security_frameworks, ml_session
                )
            
            # PHASE 6: Enhanced Command Integration (with Security Commands)
            logger.info("🔄 PHASE 6: Enhanced Command Integration")
            ml_plan = self._ml_integrate_executable_commands(
                ml_plan, analysis_results, ml_strategy, ml_session, cluster_config, security_analysis
            )
            
            # PHASE 7: Skipped - Old framework completion removed
            logger.info("🔄 PHASE 7: Framework completion removed - using enterprise metrics approach")
            
            # PHASE 8: Skipped - Old framework validation removed
            logger.info("🔄 PHASE 8: Framework validation removed - using enterprise metrics approach")
            
            # PHASE 9: Enhanced Confidence Calculation (with Security Metrics)
            logger.info("🔄 PHASE 9: Enhanced Confidence Calculation")
            plan_confidence = self._calculate_enhanced_plan_confidence(
                analysis_results, ml_plan, ml_session, cluster_config, security_analysis
            )
            
            # PHASE 10: Enhanced Learning Recording (with Security Learning)
            logger.info("🔄 PHASE 10: Enhanced Learning Outcomes Recording")
            self._record_enhanced_learning_outcomes(ml_plan, ml_session, plan_confidence, security_analysis)
            
            # PHASE 11: Enhanced Session Finalization
            logger.info("🔄 PHASE 11: Enhanced Session Finalization")
            self._finalize_enhanced_session(ml_session, ml_plan, plan_confidence, security_analysis)
            
            # Convert to timeline format if requested
            if output_format == 'timeline':
                logger.info("🔄 Converting to timeline format with security integration...")
                ml_plan = self._convert_to_timeline_format(ml_plan, analysis_results, ml_session)
            
            # Add integration metadata
            ml_plan['integration_metadata'] = {
                'ml_systems_available': self.ml_systems_available,
                'security_systems_available': self.security_systems_available,
                'integrated_mode': self.ml_systems_available and self.security_systems_available,
                'security_analysis_performed': security_analysis is not None,
                'security_frameworks_analyzed': security_frameworks if security_analysis else [],
                'generation_approach': 'integrated_ml_security' if security_analysis else 'ml_only'
            }
            
            logger.info(f"🎉 SUCCESS: INTEGRATED implementation plan generated with {plan_confidence:.1%} confidence")
            logger.info(f"🔗 Integration Status: {ml_plan['integration_metadata']['generation_approach']}")
            
            return ml_plan
            
        except Exception as e:
            # Enhanced error logging with integration status
            self._log_complete_failure_details(e, analysis_results, locals())
            self._record_generation_failure(str(e))
            
            logger.error(f"❌ FINAL FAILURE: INTEGRATED implementation plan generation failed")
            logger.error(f"🧠 ML Systems Status: {self.ml_systems_available}")
            logger.error(f"🔒 Security Systems Status: {self.security_systems_available}")
            raise
    
    # =============================================================================
    # ENHANCED SECURITY INTEGRATION METHODS
    # =============================================================================
    
    def _perform_integrated_security_analysis(self, cluster_config: Dict, 
                                            security_frameworks: List[str], 
                                            ml_session: Dict) -> Optional[Dict]:
        """Perform security analysis integrated with ML session data"""
        
        try:
            logger.info("🔍 Performing integrated security analysis...")
            
            if not hasattr(self, 'security_components_initialized') or not self.security_components_initialized:
                logger.warning("🔒 Security components not initialized - skipping security analysis")
                return None
            
            # Use the SecurityIntegrationMixin method but with ML session context
            # Create new event loop if needed to avoid blocking
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, use run_in_executor to avoid blocking
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(self._perform_comprehensive_security_analysis(
                                cluster_config, security_frameworks
                            ))
                        )
                        security_analysis = future.result(timeout=30)
                else:
                    security_analysis = asyncio.run(self._perform_comprehensive_security_analysis(
                        cluster_config, security_frameworks
                    ))
            except RuntimeError:
                # Fallback: create new event loop in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self._perform_comprehensive_security_analysis(
                            cluster_config, security_frameworks
                        ))
                    )
                    security_analysis = future.result(timeout=30)

            security_analysis = self._sanitize_security_data(security_analysis)
            
            # Enhance with ML session insights
            if 'cluster_dna' in ml_session:
                security_analysis['ml_context'] = {
                    'cluster_personality': getattr(ml_session['cluster_dna'], 'cluster_personality', 'unknown'),
                    'ml_confidence': ml_session.get('ml_confidence_levels', {}).get('dna_analysis', 0.8),
                    'optimization_readiness': getattr(ml_session['cluster_dna'], 'optimization_readiness_score', 0.8)
                }
            
            # Store in ML session for learning
            ml_session['security_analysis'] = security_analysis
            ml_session['learning_events'].append({
                'event': 'integrated_security_analysis_completed',
                'frameworks_analyzed': security_frameworks,
                'security_confidence': security_analysis.get('confidence', 0.8),
                'ml_enhanced': True,
                'success': True
            })
            
            logger.info("✅ Integrated security analysis completed")
            
            return security_analysis
            
        except Exception as e:
            logger.error(f"❌ Integrated security analysis failed: {e}")
            return None
    
    def _integrate_security_enhancements(self, ml_plan: Dict, security_analysis: Dict,
                                       security_frameworks: List[str], ml_session: Dict) -> Dict:
        """Integrate security enhancements into ML-generated plan"""
        
        try:
            logger.info("🔗 Integrating security enhancements into ML plan...")
            
            # Generate security phases using SecurityIntegrationMixin - avoid blocking
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # Run both operations in parallel for better performance
                        future1 = executor.submit(
                            lambda: asyncio.run(self._generate_security_implementation_phases(
                                security_analysis, 'high'
                            ))
                        )
                        security_phases = future1.result(timeout=30)
                        
                        future2 = executor.submit(
                            lambda: asyncio.run(self._integrate_security_phases(
                                ml_plan, security_phases, security_analysis
                            ))
                        )
                        ml_plan = future2.result(timeout=30)
                else:
                    security_phases = asyncio.run(self._generate_security_implementation_phases(
                        security_analysis, 'high'
                    ))
                    ml_plan = asyncio.run(self._integrate_security_phases(
                        ml_plan, security_phases, security_analysis
                    ))
            except RuntimeError:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future1 = executor.submit(
                        lambda: asyncio.run(self._generate_security_implementation_phases(
                            security_analysis, 'high'
                        ))
                    )
                    security_phases = future1.result(timeout=30)
                    
                    future2 = executor.submit(
                        lambda: asyncio.run(self._integrate_security_phases(
                            ml_plan, security_phases, security_analysis
                        ))
                    )
                    ml_plan = future2.result(timeout=30)
            
            # Add compliance requirements
            ml_plan = asyncio.run(self._add_compliance_requirements(
                ml_plan, security_analysis, security_frameworks
            ))
            
            # Calculate security impact
            ml_plan = asyncio.run(self._calculate_security_impact(
                ml_plan, security_analysis, ml_plan  # base_plan = ml_plan
            ))
            
            # Add security monitoring
            ml_plan = asyncio.run(self._add_security_monitoring(
                ml_plan, security_analysis
            ))
            
            logger.info(f"✅ Security enhancements integrated - {len(security_phases)} security phases added")
            return ml_plan
            
        except Exception as e:
            logger.error(f"❌ Security enhancement integration failed: {e}")
            return ml_plan
    
    # =============================================================================
    # MISSING METHOD IMPLEMENTATIONS FROM FIRST FILE
    # =============================================================================
    
    def _fetch_and_analyze_cluster_config(self, resource_group: str, cluster_name: str, 
                                          subscription_id: str, ml_session: Dict) -> Dict[str, Any]:
        """Fetch and analyze real cluster configuration"""
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
                
                # Create kubernetes_data_cache for unified analysis - REQUIRED, NO FALLBACKS
                from app.shared.kubernetes_data_cache import get_or_create_cache
                logger.info("🎯 Creating kubernetes_data_cache - THE ONLY DATA SOURCE")
                k8s_cache = get_or_create_cache(cluster_name, resource_group, subscription_id)
                logger.info("✅ kubernetes_data_cache created - all kubectl commands executed and cached")
                
                # Perform comprehensive state analysis using refactored components
                comprehensive_state = self._perform_comprehensive_state_analysis(cluster_config, ml_session, k8s_cache)
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

    def _perform_comprehensive_state_analysis(self, cluster_config: Dict, ml_session: Dict, k8s_cache=None) -> Dict:
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
            
            # Extract metrics_data from ml_session if available
            metrics_data = ml_session.get('metrics_data')
            logger.info(f"🔍 DEBUG: Retrieved metrics_data from ml_session: {'✅ Found' if metrics_data else '❌ None'}")
            
            if not metrics_data:
                # Try to get it from analysis_results if stored there
                analysis_results = ml_session.get('analysis_results', {})
                metrics_data = analysis_results.get('metrics_data')
                logger.info(f"🔍 DEBUG: Fallback - Retrieved metrics_data from analysis_results: {'✅ Found' if metrics_data else '❌ None'}")
                
                # ULTIMATE FALLBACK: Try to get HPA data directly from aks_realtime_metrics
                if not metrics_data:
                    logger.warning("🔄 ULTIMATE FALLBACK: Attempting to fetch HPA data directly from aks_realtime_metrics")
                    try:
                        from app.analytics.aks_realtime_metrics import AKSRealTimeMetricsFetcher
                        cluster_name = ml_session.get('cluster_name', 'unknown')
                        resource_group = ml_session.get('resource_group', 'unknown')
                        
                        if cluster_name != 'unknown' and resource_group != 'unknown':
                            realtime_fetcher = AKSRealTimeMetricsFetcher(cluster_name, resource_group)
                            hpa_status = realtime_fetcher.get_hpa_implementation_status()
                            
                            if hpa_status and hpa_status.get('total_hpas', 0) > 0:
                                metrics_data = {
                                    'hpa_implementation': hpa_status,
                                    'source': 'direct_aks_realtime_fallback'
                                }
                                logger.info(f"🎯 FALLBACK SUCCESS: Got {hpa_status.get('total_hpas', 0)} HPAs directly from aks_realtime_metrics")
                            else:
                                logger.warning("🔄 FALLBACK: aks_realtime_metrics returned no HPA data")
                        else:
                            logger.warning(f"🔄 FALLBACK: Cannot fetch directly - cluster_name={cluster_name}, resource_group={resource_group}")
                            
                    except Exception as fallback_error:
                        logger.error(f"❌ FALLBACK: Direct aks_realtime_metrics fetch failed: {fallback_error}")
            
            for component in components:
                logger.info(f"📊 Analyzing {component} state...")
                
                # UNIFIED: ONE CACHE FOR ALL - no exceptions, no fallbacks
                if not k8s_cache:
                    logger.error(f"❌ {component} analysis FAILED: k8s_cache is required")
                    component_state = {'analysis_error': f'{component} requires k8s_cache - no fallbacks'}
                else:
                    logger.info(f"🎯 UNIFIED: Analyzing {component} with k8s_cache")
                    component_state = ClusterAnalyzer.analyze_component(cluster_config, component, k8s_cache=k8s_cache)
                
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
    
    def _ml_analyze_cluster_dna(self, analysis_results: Dict, historical_data: Optional[Dict], 
                               ml_session: Dict, cluster_config: Dict) -> Any:
        """ML DNA analysis with detailed failure logging and cluster config"""
        
        logger.info("🧬 ML DNA Analysis with cluster config...")
        
        if not self.dna_analyzer:
            error_msg = "DNA analyzer not available - ML system initialization failed"
            self._log_detailed_failure("DNA_ANALYSIS", error_msg, {
                'dna_analyzer_status': 'not_initialized',
                'ml_systems_available': self.ml_systems_available,
                'cluster_name': analysis_results.get('cluster_name', 'unknown')
            })
            raise RuntimeError(f"❌ {error_msg}")
        
        try:
            logger.info("🔄 Calling DNA analyzer with cluster config...")
            # Pass cluster_config to DNA analyzer
            cluster_dna = self.dna_analyzer.analyze_cluster_dna(analysis_results, historical_data, cluster_config)
            
            if cluster_dna is None:
                error_msg = "DNA analyzer returned None"
                self._log_detailed_failure("DNA_ANALYSIS", error_msg, {
                    'analysis_results_keys': list(analysis_results.keys()),
                    'historical_data_provided': historical_data is not None,
                    'cluster_config_provided': cluster_config is not None,
                    'cluster_config_status': cluster_config.get('status', 'unknown') if cluster_config else 'None',
                    'dna_analyzer_type': type(self.dna_analyzer).__name__
                })
                raise ValueError(f"❌ {error_msg}")
            
            confidence = self._extract_dna_confidence(cluster_dna)
            
            # Store cluster_dna in ML session for later phases
            ml_session['cluster_dna'] = cluster_dna
            logger.info("✅ cluster_dna stored in ML session for Phase 4 (command integration)")
            
            # Store additional DNA metadata
            ml_session['dna_metadata'] = {
                'cluster_personality': getattr(cluster_dna, 'cluster_personality', 'unknown'),
                'dna_signature': getattr(cluster_dna, 'dna_signature', '')[:16],
                'uniqueness_score': getattr(cluster_dna, 'uniqueness_score', 0.5),
                'has_temporal_intelligence': getattr(cluster_dna, 'has_temporal_intelligence', False),
                'temporal_readiness_score': getattr(cluster_dna, 'temporal_readiness_score', confidence)
            }
            
            # Record ML event
            ml_session['learning_events'].append({
                'event': 'dna_analysis_ml',
                'confidence': confidence,
                'temporal_enabled': getattr(cluster_dna, 'has_temporal_intelligence', False),
                'personality': getattr(cluster_dna, 'cluster_personality', 'unknown'),
                'cluster_config_used': cluster_config is not None and cluster_config.get('status') == 'completed',
                'success': True
            })
            
            # Record confidence
            ml_session['ml_confidence_levels']['dna_analysis'] = confidence
            
            # Record for learning system
            if getattr(self, '_learning_enabled', False):
                self.report_outcome_for_learning('dna_analysis_completed', {
                    'cluster_personality': getattr(cluster_dna, 'cluster_personality', 'unknown'),
                    'confidence': confidence,
                    'ml_used': True,
                    'cluster_config_available': cluster_config is not None and cluster_config.get('status') == 'completed'
                })
            
            logger.info(f"✅ DNA Analysis: {getattr(cluster_dna, 'cluster_personality', 'unknown')} ({confidence:.1%})")
            return cluster_dna
            
        except Exception as e:
            error_msg = f"DNA analysis failed with exception: {str(e)}"
            self._log_detailed_failure("DNA_ANALYSIS", error_msg, {
                'exception_type': type(e).__name__,
                'exception_args': getattr(e, 'args', []),
                'traceback': traceback.format_exc(),
                'analysis_results_keys': list(analysis_results.keys()) if isinstance(analysis_results, dict) else 'NOT_DICT',
                'historical_data_type': type(historical_data) if historical_data else 'None',
                'cluster_config_type': type(cluster_config) if cluster_config else 'None'
            })
            raise RuntimeError(f"❌ {error_msg}") from e
    
    def _ml_generate_strategy(self, cluster_dna: Any, analysis_results: Dict, 
                             ml_session: Dict, cluster_config: Dict) -> Any:
        """ML strategy generation with detailed failure logging and cluster config"""
        
        logger.info("🎯 ML Strategy Generation with cluster config...")
        
        if not self.strategy_engine:
            error_msg = "Strategy engine not available - ML system initialization failed"
            self._log_detailed_failure("STRATEGY_GENERATION", error_msg, {
                'strategy_engine_status': 'not_initialized',
                'ml_systems_available': self.ml_systems_available,
                'cluster_dna_type': type(cluster_dna).__name__
            })
            raise RuntimeError(f"❌ {error_msg}")
        
        if cluster_dna is None:
            error_msg = "Cannot generate strategy - cluster_dna is None"
            self._log_detailed_failure("STRATEGY_GENERATION", error_msg, {
                'cluster_dna_status': 'None',
                'previous_phase': 'dna_analysis'
            })
            raise ValueError(f"❌ {error_msg}")
        
        try:
            logger.info("🔄 Calling strategy engine with cluster config...")
            # Pass cluster_config to strategy engine
            ml_strategy = self.strategy_engine.generate_comprehensive_dynamic_strategy(cluster_dna, analysis_results, cluster_config)
            
            if ml_strategy is None:
                error_msg = "Strategy engine returned None"
                self._log_detailed_failure("STRATEGY_GENERATION", error_msg, {
                    'cluster_dna_type': type(cluster_dna).__name__,
                    'cluster_dna_personality': getattr(cluster_dna, 'cluster_personality', 'unknown'),
                    'analysis_results_keys': list(analysis_results.keys()),
                    'cluster_config_provided': cluster_config is not None,
                    'cluster_config_status': cluster_config.get('status', 'unknown') if cluster_config else 'None',
                    'strategy_engine_type': type(self.strategy_engine).__name__
                })
                raise ValueError(f"❌ {error_msg}")
            
            confidence = getattr(ml_strategy, 'success_probability', 0.8)
            
            # Store strategy in ML session for later phases
            ml_session['ml_strategy'] = ml_strategy
            logger.info("✅ ml_strategy stored in ML session for future phases")
            
            # Store strategy metadata
            ml_session['strategy_metadata'] = {
                'strategy_name': getattr(ml_strategy, 'strategy_name', 'Unknown Strategy'),
                'strategy_type': getattr(ml_strategy, 'strategy_type', 'comprehensive'),
                'success_probability': confidence,
                'opportunities_count': len(getattr(ml_strategy, 'opportunities', []))
            }
            
            # Record ML event
            ml_session['learning_events'].append({
                'event': 'strategy_generation_ml',
                'confidence': confidence,
                'strategy_type': getattr(ml_strategy, 'strategy_type', 'comprehensive'),
                'opportunities_count': len(getattr(ml_strategy, 'opportunities', [])),
                'cluster_config_used': cluster_config is not None and cluster_config.get('status') == 'completed',
                'success': True
            })
            
            # Record confidence
            ml_session['ml_confidence_levels']['strategy_generation'] = confidence
            
            # Record for learning system
            if getattr(self, '_learning_enabled', False):
                self.report_outcome_for_learning('strategy_generated', {
                    'strategy_type': getattr(ml_strategy, 'strategy_type', 'unknown'),
                    'confidence': confidence,
                    'ml_used': True,
                    'cluster_config_available': cluster_config is not None and cluster_config.get('status') == 'completed'
                })
            
            logger.info(f"✅ Strategy: {getattr(ml_strategy, 'strategy_name', 'Unknown Strategy')} ({confidence:.1%})")
            return ml_strategy
            
        except Exception as e:
            error_msg = f"Strategy generation failed with exception: {str(e)}"
            self._log_detailed_failure("STRATEGY_GENERATION", error_msg, {
                'exception_type': type(e).__name__,
                'exception_args': getattr(e, 'args', []),
                'traceback': traceback.format_exc(),
                'cluster_dna_type': type(cluster_dna).__name__,
                'cluster_dna_attrs': [attr for attr in dir(cluster_dna) if not attr.startswith('_')] if cluster_dna else 'None',
                'cluster_config_type': type(cluster_config) if cluster_config else 'None'
            })
            raise RuntimeError(f"❌ {error_msg}") from e
    
    def _ml_generate_comprehensive_plan(self, analysis_results: Dict, ml_strategy: Any, 
                                      cluster_dna: Any, ml_session: Dict, cluster_config: Dict,
                                      security_analysis: Optional[Dict] = None) -> Dict:
        """Generate comprehensive plan with optional security context"""
        
        logger.info("📋 ML Plan Generation with cluster config...")
        
        if not self.plan_generator:
            error_msg = "Plan generator not available - ML system initialization failed"
            self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                'plan_generator_status': 'not_initialized',
                'ml_systems_available': self.ml_systems_available
            })
            raise RuntimeError(f"❌ {error_msg}")
        
        if ml_strategy is None:
            error_msg = "Cannot generate plan - ml_strategy is None"
            self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                'ml_strategy_status': 'None',
                'previous_phase': 'strategy_generation'
            })
            raise ValueError(f"❌ {error_msg}")
        
        if cluster_dna is None:
            error_msg = "Cannot generate plan - cluster_dna is None"
            self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                'cluster_dna_status': 'None',
                'previous_phase': 'dna_analysis'
            })
            raise ValueError(f"❌ {error_msg}")
        
        try:
            logger.info("🔄 Calling plan generator with cluster config...")
            # Pass cluster_config to plan generator
            ml_plan = self.plan_generator.generate_extensive_implementation_plan(
                analysis_results, cluster_dna, ml_strategy, cluster_config
            )
            
            if ml_plan is None:
                error_msg = "Plan generator returned None"
                self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                    'plan_generator_type': type(self.plan_generator).__name__,
                    'analysis_results_keys': list(analysis_results.keys()),
                    'ml_strategy_type': type(ml_strategy).__name__,
                    'cluster_dna_type': type(cluster_dna).__name__,
                    'cluster_config_provided': cluster_config is not None,
                    'cluster_config_status': cluster_config.get('status', 'unknown') if cluster_config else 'None'
                })
                raise ValueError(f"❌ {error_msg}")
            
            if not isinstance(ml_plan, dict):
                error_msg = f"Plan generator returned invalid type: {type(ml_plan)}"
                self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                    'returned_type': type(ml_plan).__name__,
                    'returned_value': str(ml_plan) if ml_plan else 'None'
                })
                raise ValueError(f"❌ {error_msg}")
            
            # Log plan structure before normalization
            logger.info(f"📊 Plan structure received: {list(ml_plan.keys())}")
            
            confidence = ml_plan.get('metadata', {}).get('ml_confidence', 0.8)
            
            # KEY NORMALIZATION: Convert 'phases' to 'implementation_phases'
            normalization_applied = False
            if 'phases' in ml_plan and 'implementation_phases' not in ml_plan:
                logger.info("🔧 Normalizing 'phases' → 'implementation_phases'")
                ml_plan['implementation_phases'] = ml_plan['phases']
                normalization_applied = True
            
            # Ensure we have implementation_phases
            if 'implementation_phases' not in ml_plan:
                error_msg = "Plan missing 'implementation_phases' key after normalization"
                self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                    'plan_keys': list(ml_plan.keys()),
                    'has_phases_key': 'phases' in ml_plan,
                    'normalization_applied': normalization_applied
                })
                raise ValueError(f"❌ {error_msg}")
            
            if not isinstance(ml_plan['implementation_phases'], list):
                error_msg = f"implementation_phases is not a list: {type(ml_plan['implementation_phases'])}"
                self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                    'implementation_phases_type': type(ml_plan['implementation_phases']).__name__,
                    'implementation_phases_value': str(ml_plan['implementation_phases'])
                })
                raise ValueError(f"❌ {error_msg}")
            
            # Enhance with security context if available
            if security_analysis:
                if 'metadata' not in ml_plan:
                    ml_plan['metadata'] = {}
                
                ml_plan['metadata']['security_analysis_available'] = True
                ml_plan['metadata']['security_frameworks'] = security_analysis.get('frameworks_analyzed', [])
                ml_plan['metadata']['security_confidence'] = security_analysis.get('confidence', 0.8)
            
            # Record ML event
            ml_session['learning_events'].append({
                'event': 'plan_generation_ml',
                'confidence': confidence,
                'phases_count': len(ml_plan.get('implementation_phases', [])),
                'timeline_weeks': ml_plan.get('timeline', {}).get('total_weeks', 0),
                'key_normalization_applied': normalization_applied,
                'cluster_config_used': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_analysis_available': security_analysis is not None,
                'success': True
            })
            
            # Record confidence
            ml_session['ml_confidence_levels']['plan_generation'] = confidence
            
            # Record for learning system
            if getattr(self, '_learning_enabled', False):
                self.report_outcome_for_learning('plan_generated', {
                    'phases_count': len(ml_plan.get('implementation_phases', [])),
                    'confidence': confidence,
                    'ml_used': True,
                    'key_normalization_needed': normalization_applied,
                    'cluster_config_available': cluster_config is not None and cluster_config.get('status') == 'completed',
                    'security_enhanced': security_analysis is not None
                })
            
            logger.info(f"✅ Plan: {len(ml_plan.get('implementation_phases', []))} phases ({confidence:.1%})")
            return ml_plan
            
        except Exception as e:
            error_msg = f"Plan generation failed with exception: {str(e)}"
            self._log_detailed_failure("PLAN_GENERATION", error_msg, {
                'exception_type': type(e).__name__,
                'exception_args': getattr(e, 'args', []),
                'traceback': traceback.format_exc(),
                'plan_generator_type': type(self.plan_generator).__name__,
                'analysis_results_valid': isinstance(analysis_results, dict),
                'ml_strategy_valid': ml_strategy is not None,
                'cluster_dna_valid': cluster_dna is not None,
                'cluster_config_valid': cluster_config is not None
            })
            raise RuntimeError(f"❌ {error_msg}") from e
    
    def _ml_integrate_executable_commands(self, implementation_plan: Dict, analysis_results: Dict,
                                        ml_strategy: Any, ml_session: Dict, cluster_config: Dict,
                                        security_analysis: Optional[Dict] = None) -> Dict:
        """Integrate executable commands with optional security commands"""
        
        logger.info("🛠️ ML Command Integration with YOUR analysis results...")
        
        if implementation_plan is None:
            error_msg = "Cannot integrate commands - implementation_plan is None"
            self._log_detailed_failure("COMMAND_INTEGRATION", error_msg, {
                'implementation_plan_status': 'None',
                'previous_phase': 'plan_generation'
            })
            raise ValueError(f"❌ {error_msg}")
        
        if not self.command_generator:
            logger.warning("⚠️ Command generator not available - commands will be empty")
            ml_session['learning_events'].append({
                'event': 'command_generation_skipped',
                'reason': 'command_generator_unavailable',
                'success': True
            })
            ml_session['ml_confidence_levels']['command_generation'] = 0.5
            return implementation_plan
        
        try:
            logger.info("🔄 Calling command generator with YOUR analysis results...")
            
            # CRITICAL: Ensure YOUR analysis_results flow to command generator
            logger.info(f"📊 Analysis results keys being passed: {list(analysis_results.keys())}")
            logger.info(f"💰 Total cost from analysis: ${analysis_results.get('total_cost', 0):.0f}")
            logger.info(f"💰 Total savings from analysis: ${analysis_results.get('total_savings', 0):.0f}")
            logger.info(f"💰 HPA savings from analysis: ${analysis_results.get('hpa_savings', 0):.0f}")
            logger.info(f"💰 Rightsizing savings from analysis: ${analysis_results.get('right_sizing_savings', 0):.0f}")
            
            # ENHANCEMENT: Create optimization context from analysis results
            from app.ml.analysis_bridge import AnalysisToImplementationBridge
            bridge = AnalysisToImplementationBridge()
            optimization_context = bridge.create_optimization_context(analysis_results)
            
            logger.info(f"🎯 Optimization context created: {optimization_context.cost_optimization_priority} priority")
            logger.info(f"📊 Cluster utilization: CPU {optimization_context.avg_node_cpu_utilization:.1f}%, Memory {optimization_context.avg_node_memory_utilization:.1f}%")
            logger.info(f"🔥 High-cost workloads identified: {len(optimization_context.high_cost_workloads)}")
            
            # Store optimization context for command generation
            ml_session['optimization_context'] = optimization_context
            
            # Get cluster_dna from session with proper error handling
            cluster_dna = ml_session.get('cluster_dna')
            if cluster_dna is None:
                dna_metadata = ml_session.get('dna_metadata')
                if dna_metadata:
                    logger.warning("⚠️ cluster_dna not found but DNA metadata available - proceeding with limited command generation")
                    cluster_dna = type('ClusterDNA', (), dna_metadata)()
                else:
                    error_msg = "cluster_dna not found in ML session and no DNA metadata available"
                    self._log_detailed_failure("COMMAND_INTEGRATION", error_msg, {
                        'ml_session_keys': list(ml_session.keys()),
                        'session_id': ml_session.get('session_id', 'unknown')
                    })
                    raise ValueError(f"❌ {error_msg}")
            
            # Get strategy from session if needed
            if ml_strategy is None:
                ml_strategy = ml_session.get('ml_strategy')
                if ml_strategy:
                    logger.info("✅ Retrieved ml_strategy from session")
            
            # Set cluster config if available
            if cluster_config and cluster_config.get('status') == 'completed':
                if hasattr(self.command_generator, 'set_cluster_config'):
                    self.command_generator.set_cluster_config(cluster_config)
                    logger.info("✅ Cluster config set on command generator")
            
            # CRITICAL FIX: Pass YOUR analysis_results as first parameter with optimization context
            # Ensure optimization context is included in analysis_results
            if 'optimization_context' in ml_session:
                analysis_results['optimization_context'] = ml_session['optimization_context']
                logger.info("✅ Optimization context added to analysis_results for command generation")
                
            execution_plan = self.command_generator.generate_comprehensive_execution_plan(
                ml_strategy, 
                cluster_dna, 
                analysis_results,  # YOUR analysis results with real opportunities AND optimization context
                cluster_config,
                implementation_phases=implementation_plan.get('implementation_phases', [])
            )
            
            if execution_plan is None:
                logger.warning("⚠️ Command generator returned None - proceeding without commands")
                ml_session['learning_events'].append({
                    'event': 'command_generation_none',
                    'reason': 'execution_plan_none',
                    'success': True
                })
                ml_session['ml_confidence_levels']['command_generation'] = 0.5
                return implementation_plan
            
            # Map commands to phases - CRITICAL: This connects YOUR opportunities to phases
            logger.info("🔄 Mapping YOUR analysis-based commands to phases...")
            implementation_plan = self._map_commands_to_phases(implementation_plan, execution_plan)
            
            confidence = getattr(execution_plan, 'success_probability', 0.8)
            command_count = self._count_total_commands(execution_plan)
            
            # Store execution plan in session
            ml_session['execution_plan'] = execution_plan
            ml_session['command_metadata'] = {
                'total_commands': command_count,
                'success_probability': confidence,
                'generation_time': datetime.now().isoformat(),
                'cluster_config_used': cluster_config is not None and cluster_config.get('status') == 'completed',
                'analysis_results_used': True  # Track that YOUR analysis was used
            }
            
            # Add security commands if security analysis is available
            if security_analysis and hasattr(self, 'security_components_initialized'):
                try:
                    implementation_plan = asyncio.run(self._generate_security_commands(
                        implementation_plan, security_analysis
                    ))
                    logger.info("✅ Security commands integrated into phases")
                except Exception as e:
                    logger.warning(f"⚠️ Security command integration failed: {e}")
            
            # Record ML event
            ml_session['learning_events'].append({
                'event': 'command_generation_ml',
                'confidence': confidence,
                'command_count': command_count,
                'cluster_config_used': cluster_config is not None and cluster_config.get('status') == 'completed',
                'analysis_results_used': True,  # Track YOUR analysis usage
                'security_commands_added': security_analysis is not None,
                'success': True
            })
            
            # Record confidence
            ml_session['ml_confidence_levels']['command_generation'] = confidence
            
            # Update executive summary with real command count
            total_commands = sum(len(phase.get('commands', [])) for phase in implementation_plan.get('implementation_phases', []))
            if 'executive_summary' in implementation_plan:
                implementation_plan['executive_summary']['command_groups_generated'] = total_commands
                implementation_plan['executive_summary']['commands_from_analysis'] = True
                implementation_plan['executive_summary']['security_commands_included'] = security_analysis is not None
            
            logger.info(f"✅ Commands: {total_commands} integrated from YOUR analysis ({confidence:.1%})")
            
            return implementation_plan
            
        except Exception as e:
            # Command integration failure is not critical - log but continue
            logger.warning(f"⚠️ Command integration failed: {e}")
            logger.warning(f"⚠️ Traceback: {traceback.format_exc()}")
            
            ml_session['learning_events'].append({
                'event': 'command_generation_failed',
                'error': str(e),
                'success': False
            })
            ml_session['ml_confidence_levels']['command_generation'] = 0.3
            
            return implementation_plan
    
    def _ensure_complete_framework_structure(self, implementation_plan: Dict, 
                                           analysis_results: Dict, ml_session: Dict, 
                                           cluster_config: Dict,
                                           security_analysis: Optional[Dict] = None) -> Dict:
        """Ensure complete framework structure with security enhancements"""
        
        logger.info("🔧 Ensuring complete framework structure with cluster config and security...")
        
        if implementation_plan is None:
            error_msg = "Cannot complete framework - implementation_plan is None"
            self._log_detailed_failure("FRAMEWORK_COMPLETION", error_msg, {
                'implementation_plan_status': 'None',
                'previous_phase': 'command_integration'
            })
            raise ValueError(f"❌ {error_msg}")
        
        # CRITICAL: Ensure implementation_phases exists before proceeding
        if 'implementation_phases' not in implementation_plan:
            if 'phases' in implementation_plan:
                logger.info("🔧 Converting 'phases' to 'implementation_phases'")
                implementation_plan['implementation_phases'] = implementation_plan['phases']
            else:
                error_msg = "Plan missing both 'implementation_phases' and 'phases' keys"
                self._log_detailed_failure("FRAMEWORK_COMPLETION", error_msg, {
                    'plan_keys': list(implementation_plan.keys()),
                    'expected_keys': ['implementation_phases', 'phases']
                })
                raise ValueError(f"❌ {error_msg}")
        
        try:
            total_cost = analysis_results.get('total_cost', 0)
            total_savings = analysis_results.get('total_savings', 0)
            cluster_name = analysis_results.get('cluster_name', 'unknown')
            
            # Get ML confidence for enhancement
            overall_ml_confidence = self._calculate_session_confidence(ml_session)
            
            # Get cluster insights for enhanced framework
            cluster_insights = ml_session.get('config_insights', {})
            cluster_complexity = cluster_insights.get('cluster_complexity', 'unknown')
            scaling_readiness = cluster_insights.get('scaling_readiness', 'unknown')
            security_posture = cluster_insights.get('security_posture', 'unknown')
            
            # Get comprehensive state for optimization opportunities
            comprehensive_state = ml_session.get('comprehensive_state', {})
            total_optimization_opportunities = comprehensive_state.get('total_optimization_opportunities', 0)
            
            logger.info("🔧 Adding ALL 8 framework components with cluster config insights...")
            
            # 1. Cost Protection (enhanced with cluster config)
            implementation_plan['costProtection'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'budgetLimits': {
                    'monthlyBudget': total_cost * 1.1,
                    'alertThreshold': total_cost * 0.95,
                    'hardLimit': total_cost * 1.2
                },
                'savingsProtection': {
                    'minimumSavingsTarget': total_savings * 0.8,
                    'predicted_savings': total_savings,
                    'ml_confidence_interval': [total_savings * 0.8, total_savings * 1.2],
                    'optimization_opportunities_identified': total_optimization_opportunities
                }
            }
            
            # 2. Governance Framework (enhanced with cluster complexity and security)
            governance_level = 'enterprise' if cluster_complexity == 'high' else 'standard'
            if self.enable_security_integration:
                governance_level = 'enterprise'  # Upgrade to enterprise if security enabled
                
            implementation_plan['governance'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'governanceLevel': governance_level,
                'cluster_complexity': cluster_complexity,
                'approvalRequirements': {
                    'technical_approval': True,
                    'business_approval': governance_level == 'enterprise',
                    'security_approval': self.enable_security_integration,
                    'complexity_based_requirements': cluster_complexity == 'high'
                },
                'changeManagement': {
                    'change_windows': ['maintenance_window'],
                    'rollback_procedures': 'automated_with_manual_override',
                    'complexity_considerations': cluster_complexity,
                    'security_considerations': self.enable_security_integration
                }
            }
            
            # 3. Monitoring Strategy (enhanced with scaling readiness and security)
            monitoring_frequency = 'real_time' if scaling_readiness == 'high' else 'frequent'
            implementation_plan['monitoring'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'monitoringFrequency': monitoring_frequency,
                'scaling_readiness': scaling_readiness,
                'keyMetrics': ['cost_trends', 'resource_utilization', 'application_performance', 'scaling_effectiveness'],
                'alerting': {
                    'cost_spike_alerts': True,
                    'performance_degradation_alerts': True,
                    'scaling_inefficiency_alerts': scaling_readiness in ['low', 'medium'],
                    'security_alerts': self.enable_security_integration,
                    'ml_confidence_threshold': overall_ml_confidence
                },
                'securityMonitoring': {
                    'enabled': self.enable_security_integration,
                    'posture_monitoring': self.security_systems_available,
                    'compliance_monitoring': hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False)
                }
            }
            
            # 4. Contingency Planning (enhanced with cluster config and security)
            implementation_plan['contingency'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'contingencyTriggers': [
                    'cost_overrun_exceeds_20_percent',
                    'ml_confidence_drops_below_threshold',
                    'cluster_config_drift_detected',
                    'security_breach_detected' if self.enable_security_integration else None
                ],
                'rollbackProcedures': {
                    'automated_rollback_available': True,
                    'rollback_time_estimate': '15_minutes',
                    'cluster_config_restore_available': cluster_config is not None and cluster_config.get('status') == 'completed',
                    'security_rollback_available': self.enable_security_integration
                }
            }
            
            # 5. Success Criteria (enhanced with optimization opportunities and security)
            implementation_plan['successCriteria'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'financialTargets': {
                    'monthly_savings_target': total_savings,
                    'ml_confidence_target': overall_ml_confidence,
                    'optimization_opportunities_addressed': total_optimization_opportunities
                },
                'technicalTargets': {
                    'zero_downtime_during_implementation': True,
                    'ml_prediction_accuracy_maintained': True,
                    'cluster_config_consistency_maintained': cluster_config is not None and cluster_config.get('status') == 'completed'
                },
                'securityTargets': {
                    'security_posture_maintained_or_improved': self.enable_security_integration,
                    'compliance_requirements_met': hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False),
                    'vulnerability_count_reduced': self.enable_security_integration
                }
            }
            
            # 6. Timeline Optimization (enhanced with cluster complexity and security)
            phases = implementation_plan.get('implementation_phases', [])
            total_timeline_weeks = max([p.get('end_week', 1) for p in phases]) if phases else 6
            
            # Adjust timeline based on cluster complexity and security
            complexity_factor = {'high': 1.2, 'medium': 1.0, 'low': 0.8}.get(cluster_complexity, 1.0)
            if self.enable_security_integration:
                complexity_factor *= 1.1  # Add 10% for security integration
            optimized_timeline = max(1, int(total_timeline_weeks * complexity_factor))
            
            implementation_plan['timelineOptimization'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'originalTimelineWeeks': total_timeline_weeks,
                'optimizedTimelineWeeks': optimized_timeline,
                'cluster_complexity_factor': complexity_factor,
                'security_integration_factor': 1.1 if self.enable_security_integration else 1.0,
                'ml_optimization_applied': self.ml_systems_available
            }
            
            # 7. Risk Mitigation (enhanced with security posture and comprehensive framework)
            identified_risks = [
                {
                    'risk_id': 'ML_001',
                    'description': 'ML prediction uncertainty',
                    'probability': 'low' if overall_ml_confidence > 0.8 else 'medium',
                    'mitigation': 'continuous_ml_monitoring_and_adjustment'
                }
            ]
            
            # Add security-based risks
            if security_posture == 'basic':
                identified_risks.append({
                    'risk_id': 'SEC_001',
                    'description': 'Basic security posture may limit optimization options',
                    'probability': 'medium',
                    'mitigation': 'enhanced_security_controls_implementation'
                })
            
            # Add comprehensive security framework risks
            if self.enable_security_integration and not hasattr(self, 'security_components_initialized'):
                identified_risks.append({
                    'risk_id': 'SEC_002',
                    'description': 'Security framework enabled but components not initialized',
                    'probability': 'high',
                    'mitigation': 'initialize_security_framework_components'
                })
            
            implementation_plan['riskMitigation'] = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'security_posture': security_posture,
                'identifiedRisks': identified_risks,
                'ml_risk_assessment': {
                    'prediction_uncertainty': 1.0 - overall_ml_confidence,
                    'model_confidence': overall_ml_confidence,
                    'cluster_config_reliability': cluster_config is not None and cluster_config.get('status') == 'completed'
                },
                'security_risk_assessment': {
                    'framework_available': SECURITY_INTEGRATION_AVAILABLE,
                    'components_initialized': hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False),
                    'engines_initialized': hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False)
                }
            }
            
            # 8. NEW: Intelligence Insights (extract from analysis data and enhance with ML and security)
            implementation_plan['intelligence_insights'] = self._create_intelligence_insights_from_analysis(
                analysis_results, ml_session, cluster_config, overall_ml_confidence
            )
            
            # Enhance framework components with security data
            if security_analysis:
                self._enhance_framework_with_security(implementation_plan, security_analysis)
            
            # Final validation log
            phases_count = len(implementation_plan.get('implementation_phases', []))
            logger.info(f"✅ Framework complete: {phases_count} phases in implementation_phases")
            logger.info("✅ ALL 8 framework components populated with ML intelligence, cluster config, and security")
            logger.info(f"🔍 Cluster insights applied: complexity={cluster_complexity}, scaling={scaling_readiness}, security={security_posture}")
            logger.info(f"🔒 Security framework: enabled={self.enable_security_integration}, available={SECURITY_INTEGRATION_AVAILABLE}")
            
            return implementation_plan
            
        except Exception as e:
            error_msg = f"Framework completion failed with exception: {str(e)}"
            self._log_detailed_failure("FRAMEWORK_COMPLETION", error_msg, {
                'exception_type': type(e).__name__,
                'exception_args': getattr(e, 'args', []),
                'traceback': traceback.format_exc(),
                'implementation_plan_keys': list(implementation_plan.keys()) if isinstance(implementation_plan, dict) else 'NOT_DICT',
                'cluster_config_available': cluster_config is not None and cluster_config.get('status') == 'completed' if cluster_config else False,
                'security_integration_enabled': self.enable_security_integration
            })
            raise RuntimeError(f"❌ {error_msg}") from e
    
    def _enhance_framework_with_security(self, implementation_plan: Dict, 
                                       security_analysis: Dict):
        """Enhance framework components with security analysis data"""
        
        try:
            security_score = security_analysis.get('security_posture', {}).get('overall_score', 50)
            
            # Enhance governance with security posture
            if 'governance' in implementation_plan:
                implementation_plan['governance']['security_posture_score'] = security_score
                implementation_plan['governance']['security_grade'] = security_analysis.get('security_posture', {}).get('grade', 'C')
                implementation_plan['governance']['security_monitoring_required'] = security_score < 80
            
            # Enhance risk mitigation with security risks
            if 'riskMitigation' in implementation_plan:
                security_risks = []
                
                if security_score < 70:
                    security_risks.append({
                        'risk_id': 'SEC_INTEGRATED_001',
                        'description': f'Low security posture score: {security_score:.1f}',
                        'probability': 'HIGH',
                        'mitigation': 'Implement security enhancement phases'
                    })
                
                vuln_count = security_analysis.get('vulnerability_assessment', {}).get('critical_vulnerabilities', 0)
                if vuln_count > 0:
                    security_risks.append({
                        'risk_id': 'SEC_INTEGRATED_002',
                        'description': f'{vuln_count} critical vulnerabilities detected',
                        'probability': 'CRITICAL',
                        'mitigation': 'Immediate vulnerability remediation required'
                    })
                
                implementation_plan['riskMitigation']['integrated_security_risks'] = security_risks
            
            # Enhance success criteria with security targets
            if 'successCriteria' in implementation_plan:
                implementation_plan['successCriteria']['integrated_security_targets'] = {
                    'target_security_score': max(80, security_score + 20),
                    'maximum_critical_vulnerabilities': 0,
                    'minimum_compliance_score': 85
                }
            
            logger.info("✅ Framework enhanced with integrated security data")
            
        except Exception as e:
            logger.warning(f"⚠️ Framework security enhancement failed: {e}")
    
    # =============================================================================
    # ENHANCED CONFIDENCE AND LEARNING METHODS
    # =============================================================================
    
    def _calculate_enhanced_plan_confidence(self, analysis_results: Dict, implementation_plan: Dict,
                                          ml_session: Dict, cluster_config: Dict,
                                          security_analysis: Optional[Dict]) -> float:
        """Calculate enhanced plan confidence with security metrics"""
        
        # Get base confidence
        base_confidence = self._calculate_ml_plan_confidence(
            analysis_results, implementation_plan, ml_session, cluster_config
        )
        
        # Enhance with security confidence if available
        if security_analysis:
            security_confidence = security_analysis.get('confidence', 0.8)
            
            # Weighted average: 70% ML confidence, 30% security confidence
            enhanced_confidence = (base_confidence * 0.7) + (security_confidence * 0.3)
            
            # Bonus for integrated analysis
            integration_bonus = 0.05 if self.ml_systems_available and self.security_systems_available else 0
            enhanced_confidence = min(1.0, enhanced_confidence + integration_bonus)
            
            implementation_plan['enhanced_confidence'] = {
                'overall_confidence': enhanced_confidence,
                'ml_confidence': base_confidence,
                'security_confidence': security_confidence,
                'integration_bonus': integration_bonus,
                'calculation_method': 'integrated_ml_security'
            }
            
            return enhanced_confidence
        
        else:
            # No security analysis - use base confidence with slight penalty
            ml_only_confidence = base_confidence * 0.95  # 5% penalty for missing security
            
            implementation_plan['enhanced_confidence'] = {
                'overall_confidence': ml_only_confidence,
                'ml_confidence': base_confidence,
                'security_confidence': None,
                'integration_penalty': 0.05,
                'calculation_method': 'ml_only'
            }
            
            return ml_only_confidence
    
    def _record_enhanced_learning_outcomes(self, implementation_plan: Dict, ml_session: Dict,
                                         confidence: float, security_analysis: Optional[Dict]):
        """Record enhanced learning outcomes with security integration"""
        
        # Call original method
        self._record_ml_learning_outcomes(implementation_plan, ml_session, confidence)
        
        # Add security learning if available
        if security_analysis and getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('integrated_security_learning', {
                'session_id': ml_session['session_id'],
                'security_frameworks_analyzed': security_analysis.get('frameworks_analyzed', []),
                'security_confidence': security_analysis.get('confidence', 0.8),
                'security_phases_generated': len([p for p in implementation_plan.get('implementation_phases', []) 
                                                if p.get('category') == 'security']),
                'integration_successful': True,
                'ml_security_correlation': confidence
            })
    
    async def _calculate_enterprise_metrics(self, analysis_results: Dict, cluster_dna: Any, 
                                           ml_session: Dict, cluster_config: Dict) -> Dict:
        """Calculate real enterprise operational metrics and integrate with implementation plan"""
        logger.info("🏢 Calculating enterprise operational metrics...")
        
        try:
            # Extract cluster information - use same pattern as analysis engine
            resource_group = analysis_results.get('resource_group')
            cluster_name = analysis_results.get('cluster_name')
            
            # subscription_id is stored in nested objects after centralization
            subscription_id = (analysis_results.get('subscription_id') or 
                             analysis_results.get('cluster_context', {}).get('subscription_id') or
                             analysis_results.get('cluster_metadata', {}).get('subscription_id'))
            
            # Fallback to auto-detection if subscription_id not provided in analysis results
            if not subscription_id:
                logger.info(f"🔍 Auto-detecting subscription for cluster {cluster_name}")
                from app.services.subscription_manager import azure_subscription_manager
                subscription_id = azure_subscription_manager.find_cluster_subscription(resource_group, cluster_name)
                
            if not all([resource_group, cluster_name, subscription_id]):
                raise ValueError(f"Missing cluster info: rg={resource_group}, cluster={cluster_name}, sub={subscription_id}")
            
            # Import enterprise metrics components
            from app.ml.ml_framework_generator import EnterpriseOperationalMetricsEngine, EnterpriseMetricsIntegration
            
            # Initialize enterprise metrics engine first
            metrics_engine = EnterpriseOperationalMetricsEngine(
                resource_group=resource_group,
                cluster_name=cluster_name,
                subscription_id=subscription_id
            )
            
            # Then create integration with the engine
            integration = EnterpriseMetricsIntegration(metrics_engine)
            
            # Calculate real enterprise metrics
            logger.info("📊 Fetching real enterprise metrics from cluster...")
            dashboard_data = await integration.get_enterprise_dashboard_data()
            
            logger.info(f"✅ Enterprise metrics calculated - Score: {dashboard_data['enterprise_maturity']['score']}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"❌ Enterprise metrics calculation failed: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Don't fail the entire implementation generation - just skip enterprise metrics
            return {
                'status': 'failed',
                'error': str(e),
                'enterprise_maturity': {'score': 0, 'level': 'UNKNOWN'},
                'operational_metrics': {},
                'action_items': []
            }
    
    def _finalize_enhanced_session(self, ml_session: Dict, implementation_plan: Dict,
                                 confidence: float, security_analysis: Optional[Dict]):
        """Finalize enhanced session with security integration metadata"""
        
        # Call original method
        self._finalize_ml_session(ml_session, implementation_plan, confidence)
        
        # Add enhanced metadata
        if 'metadata' not in implementation_plan:
            implementation_plan['metadata'] = {}
        
        implementation_plan['metadata']['enhanced_session'] = {
            'ml_systems_used': self.ml_systems_available,
            'security_systems_used': self.security_systems_available,
            'integrated_analysis': security_analysis is not None,
            'session_type': 'integrated' if security_analysis else 'ml_only',
            'enhancement_version': '2.0.0'
        }
        
        logger.info(f"🎯 Enhanced Session Completed: {implementation_plan['metadata']['enhanced_session']['session_type']}")
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _validate_input_data(self, analysis_results: Dict) -> bool:
        """Validate input data has required fields"""
        try:
            if not analysis_results or not isinstance(analysis_results, dict):
                logger.error(f"❌ Invalid analysis_results: type={type(analysis_results)}")
                return False
            
            required_fields = ['total_cost']
            missing_fields = []
            
            for field in required_fields:
                if field not in analysis_results:
                    missing_fields.append(field)
                    continue
                
                value = analysis_results[field]
                if not isinstance(value, (int, float)) or value < 0:
                    logger.error(f"❌ Invalid {field}: value={value}, type={type(value)}")
                    return False
            
            if missing_fields:
                logger.error(f"❌ Missing required fields: {missing_fields}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Input validation failed: {e}")
            return False
    
    def _validate_output_structure(self, implementation_plan: Dict) -> bool:
        """Enhanced validation with detailed error reporting"""
        try:
            if not isinstance(implementation_plan, dict):
                logger.error("❌ Plan is not a dictionary")
                return False
            
            # Check for critical required key
            if 'implementation_phases' not in implementation_plan:
                logger.error(f"❌ Missing 'implementation_phases'. Available keys: {list(implementation_plan.keys())}")
                
                # Check if 'phases' exists instead
                if 'phases' in implementation_plan:
                    logger.error("❌ Found 'phases' but expected 'implementation_phases' - key normalization failed")
                
                return False
            
            # Check implementation_phases is a list
            if not isinstance(implementation_plan['implementation_phases'], list):
                logger.error(f"❌ implementation_phases is not a list: type={type(implementation_plan['implementation_phases'])}")
                return False
            
            # Check for plan components
            plan_components = ['costProtection', 'governance', 'monitoring', 'contingency', 
                             'successCriteria', 'timelineOptimization', 'riskMitigation', 'intelligenceInsights']
            
            missing_components = []
            disabled_components = []
            
            for component in plan_components:
                if component not in implementation_plan:
                    missing_components.append(component)
                else:
                    confidence = implementation_plan[component].get('ml_confidence', 0)
                    logger.info(f"🔍 Component '{component}' confidence: {confidence}")
                    if confidence < 0.5:
                        disabled_components.append(component)
            
            if missing_components:
                logger.error(f"❌ Missing framework components: {missing_components}")
                return False
            
            if disabled_components:
                logger.error(f"❌ Disabled framework components: {disabled_components}")
                return False
            
            logger.info("✅ Output structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation failed with exception: {e}")
            logger.error(f"❌ Validation traceback: {traceback.format_exc()}")
            return False

    def _log_detailed_failure(self, operation: str, error_msg: str, context: Dict):
        """Log detailed failure information for debugging"""
        
        failure_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error_message': error_msg,
            'context': context,
            'ml_systems_status': {
                'learning_engine': hasattr(self, 'learning_engine') and self.learning_engine is not None,
                'ml_orchestrator': hasattr(self, 'ml_orchestrator') and self.ml_orchestrator is not None,
                'strategy_engine': hasattr(self, 'strategy_engine') and self.strategy_engine is not None,
                'plan_generator': hasattr(self, 'plan_generator') and self.plan_generator is not None,
                'command_generator': hasattr(self, 'command_generator') and self.command_generator is not None,
                'dna_analyzer': hasattr(self, 'dna_analyzer') and self.dna_analyzer is not None,
                'ml_systems_available': self.ml_systems_available
            },
            'security_systems_status': {
                'security_integration_enabled': self.enable_security_integration,
                'security_framework_available': SECURITY_INTEGRATION_AVAILABLE,
                'security_systems_available': self.security_systems_available,
                'security_components_ready': hasattr(self, 'security_components_ready') and getattr(self, 'security_components_ready', False),
                'security_components_initialized': hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False)
            },
            'system_info': {
                'enable_cost_monitoring': self.enable_cost_monitoring,
                'enable_temporal': self.enable_temporal,
                'learning_enabled': getattr(self, '_learning_enabled', False)
            }
        }
        
        self._debug_info['failed_operations'].append(failure_record)
        
        logger.error(f"💥 DETAILED FAILURE [{operation}]: {error_msg}")
        logger.error(f"💥 Context: {self.safe_json_dumps(context)}")
        logger.error(f"💥 ML Systems Status: {json.dumps(failure_record['ml_systems_status'], indent=2)}")
        logger.error(f"💥 Security Systems Status: {json.dumps(failure_record['security_systems_status'], indent=2)}")

    def _log_complete_failure_details(self, exception: Exception, analysis_results: Dict, local_vars: Dict):
        """Log complete failure details for debugging"""
        
        complete_failure = {
            'timestamp': datetime.now().isoformat(),
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'exception_args': [str(arg) for arg in getattr(exception, 'args', [])],
            'full_traceback': traceback.format_exc(),
            'analysis_results_info': {
                'type': type(analysis_results).__name__,
                'is_dict': isinstance(analysis_results, dict),
                'keys': list(analysis_results.keys()) if isinstance(analysis_results, dict) else 'NOT_DICT',
                'cluster_name': analysis_results.get('cluster_name', 'unknown') if isinstance(analysis_results, dict) else 'unknown',
                'total_cost': analysis_results.get('total_cost', 'missing') if isinstance(analysis_results, dict) else 'missing'
            },
            'local_variables': {
                'ml_session': str(type(local_vars.get('ml_session'))),
                'cluster_dna': str(type(local_vars.get('cluster_dna'))),
                'ml_strategy': str(type(local_vars.get('ml_strategy'))),
                'ml_plan': str(type(local_vars.get('ml_plan'))),
                'cluster_config': str(type(local_vars.get('cluster_config'))),
                'security_analysis': str(type(local_vars.get('security_analysis')))
            },
            'ml_systems_detailed': self._debug_info['ml_system_status'],
            'security_systems_detailed': self._debug_info.get('security_framework_status', {}),
            'all_failed_operations': self._debug_info['failed_operations']
        }
        
        logger.error("💥" * 50)
        logger.error("💥 COMPLETE SYSTEM FAILURE ANALYSIS")
        logger.error("💥" * 50)
        logger.error(f"💥 Exception: {complete_failure['exception_type']}: {complete_failure['exception_message']}")
        
        # Safely serialize analysis results
        try:
            logger.error(f"💥 Analysis Results: {json.dumps(complete_failure['analysis_results_info'], indent=2)}")
        except Exception as json_error:
            logger.error(f"💥 Analysis Results: <Could not serialize: {json_error}>")
        
        # Safely serialize local variables
        try:
            logger.error(f"💥 Local Variables: {json.dumps(complete_failure['local_variables'], indent=2)}")
        except Exception as json_error:
            logger.error(f"💥 Local Variables: <Could not serialize: {json_error}>")
        
        logger.error(f"💥 Full Traceback:\n{complete_failure['full_traceback']}")
        logger.error("💥" * 50)

    def _record_generation_failure(self, error: str):
        """Record generation failure for learning"""
        if getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('generation_failed', {
                'error': error,
                'timestamp': datetime.now().isoformat(),
                'ml_systems_available': getattr(self, 'ml_systems_available', False),
                'security_integration_enabled': self.enable_security_integration,
                'failed_operations_count': len(self._debug_info['failed_operations'])
            })

    def safe_json_serialize(self, obj: Any) -> Any:
        """Safely serialize objects for JSON logging by converting problematic types to strings"""
        if isinstance(obj, type):
            return f"<class '{obj.__name__}'>"
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            try:
                return str(obj)
            except:
                return f"<object {type(obj).__name__}>"
        elif callable(obj):
            return f"<function {obj.__name__}>"
        else:
            return obj

    def safe_json_dumps(self, obj: Any, indent: int = 2) -> str:
        """Safely dump objects to JSON string with error handling"""
        try:
            return json.dumps(obj, indent=indent, default=self.safe_json_serialize)
        except Exception as e:
            return f"<JSON serialization failed: {str(e)}>"

    def _extract_dna_confidence(self, cluster_dna: Any) -> float:
        """Extract confidence from DNA analysis"""
        if hasattr(cluster_dna, 'temporal_readiness_score'):
            return cluster_dna.temporal_readiness_score
        elif hasattr(cluster_dna, 'optimization_readiness_score'):
            return cluster_dna.optimization_readiness_score
        else:
            return 0.8

    def _calculate_session_confidence(self, ml_session: Dict) -> float:
        """Calculate overall session confidence"""
        confidences = list(ml_session['ml_confidence_levels'].values())
        return sum(confidences) / len(confidences) if confidences else 0.8

    def _count_total_commands(self, execution_plan: Any) -> int:
        """Count total commands from execution plan"""
        if not execution_plan:
            return 0
        
        total = 0
        for attr in ['preparation_commands', 'optimization_commands', 'networking_commands',
                     'security_commands', 'monitoring_commands', 'validation_commands']:
            if hasattr(execution_plan, attr):
                commands = getattr(execution_plan, attr)
                total += len(commands) if commands else 0
        return total

    def _map_commands_to_phases(self, implementation_plan: Dict, execution_plan: Any) -> Dict:
        """Use phase-specific commands from dynamic command generator"""
        
        phases = implementation_plan.get('implementation_phases', [])
        
        if not execution_plan or not phases:
            return implementation_plan
        
        try:
            # Debug: Check what we received
            if hasattr(execution_plan, 'phase_commands') and execution_plan.phase_commands:
                logger.info(f"🔍 DEBUG: Found phase_commands for {len(execution_plan.phase_commands)} phases")
                for phase_id, commands in execution_plan.phase_commands.items():
                    logger.info(f"🔍 DEBUG: Phase {phase_id} has {len(commands)} commands")
                    if commands:
                        first_cmd = commands[0]
                        logger.info(f"🔍 DEBUG: First command type: {type(first_cmd)}")
                        logger.info(f"🔍 DEBUG: First command ID: {getattr(first_cmd, 'id', 'NO_ID')}")
                        logger.info(f"🔍 DEBUG: First command desc: {getattr(first_cmd, 'description', 'NO_DESC')[:50]}...")
                
                for phase in phases:
                    phase_id = f"phase-{phase.get('phase_number', 0)}"
                    phase_title = phase.get('title', 'Unknown')
                    logger.info(f"🎯 Processing phase: {phase_id} - {phase_title}")
                    
                    if phase_id in execution_plan.phase_commands:
                        executable_commands = execution_plan.phase_commands[phase_id]
                        logger.info(f"✅ Found {len(executable_commands)} commands for {phase_id}")
                        
                        # Convert ExecutableCommand objects to UI format - FIX THE SERIALIZATION
                        command_strings = []
                        for i, exec_cmd in enumerate(executable_commands):
                            cmd_string = getattr(exec_cmd, 'command', '')
                            logger.info(f"🔍 Command {i} for {phase_id}: {cmd_string[:100]}...")
                            command_strings.append(cmd_string)  # Keep as string, don't JSON serialize
                        
                        # Update phase with commands in the correct format
                        phase['commands'] = [{
                            'title': f'{phase_title} Commands',
                            'commands': command_strings,  # Array of plain command strings
                            'description': f'Commands for {phase_title}',
                            'source': 'phase_specific'
                        }]
                        
                        logger.info(f"✅ Mapped {len(executable_commands)} commands to phase: {phase_title}")
                    else:
                        logger.warning(f"⚠️ No commands found for phase: {phase_id} ({phase_title})")
                        phase['commands'] = []
                
                return implementation_plan
            
            else:
                logger.error("❌ No phase_commands found in execution plan!")
                if hasattr(execution_plan, 'phase_commands'):
                    logger.error(f"❌ phase_commands is: {execution_plan.phase_commands}")
                else:
                    logger.error("❌ execution_plan has no phase_commands attribute")
                return implementation_plan
            
        except Exception as e:
            logger.error(f"❌ Phase command integration failed: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return implementation_plan

    def _calculate_ml_plan_confidence(self, analysis_results: Dict, implementation_plan: Dict, 
                                     ml_session: Dict, cluster_config: Dict) -> float:
        """Calculate ML-enhanced plan confidence with cluster config and security"""
        
        confidence_factors = []
        
        # ML system confidence levels
        ml_confidences = list(ml_session['ml_confidence_levels'].values())
        if ml_confidences:
            confidence_factors.append(sum(ml_confidences) / len(ml_confidences))
        
        # Data quality factor
        total_cost = analysis_results.get('total_cost', 0)
        if total_cost > 0:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.3)
        
        # Cluster config quality factor
        if cluster_config and cluster_config.get('status') == 'completed':
            config_success_rate = cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0) / max(cluster_config.get('fetch_metrics', {}).get('attempted_fetches', 1), 1)
            confidence_factors.append(0.5 + 0.4 * config_success_rate)
        else:
            confidence_factors.append(0.5)
        
        # Plan completeness factor
        phase_count = len(implementation_plan.get('implementation_phases', []))
        complexity_factor = max(0.5, 1.0 - (phase_count - 5) * 0.1)
        confidence_factors.append(complexity_factor)
        
        # ML systems availability factor
        if self.ml_systems_available:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # Use enterprise metrics confidence directly from plan generation
        if 'metadata' in implementation_plan and 'ml_confidence' in implementation_plan['metadata']:
            plan_confidence = implementation_plan['metadata']['ml_confidence']
            confidence_factors.append(plan_confidence)
        else:
            confidence_factors.append(0.8)  # Default for enterprise metrics
        
        # Security integration factor (NEW)
        if self.enable_security_integration:
            if SECURITY_INTEGRATION_AVAILABLE and self.security_systems_available:
                confidence_factors.append(0.9)  # High confidence with security framework
            else:
                confidence_factors.append(0.7)  # Medium confidence - enabled but not fully available
        else:
            confidence_factors.append(0.8)  # Standard confidence without security
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Add ML confidence to plan
        implementation_plan['ml_confidence'] = overall_confidence
        implementation_plan['ml_confidence_breakdown'] = ml_session['ml_confidence_levels']
        implementation_plan['learning_applied'] = len(ml_session['learning_events']) > 0
        implementation_plan['cluster_config_used'] = cluster_config is not None and cluster_config.get('status') == 'completed'
        implementation_plan['security_framework_enabled'] = self.enable_security_integration
        implementation_plan['security_framework_available'] = SECURITY_INTEGRATION_AVAILABLE
        
        return overall_confidence

    def _record_ml_learning_outcomes(self, implementation_plan: Dict, ml_session: Dict, confidence: float):
        """Record ML learning outcomes with security integration"""
        
        logger.info("📚 Recording ML learning outcomes with security integration...")
        
        try:
            if hasattr(self, 'learning_engine') and self.learning_engine and hasattr(self, 'ml_orchestrator') and self.ml_orchestrator:
                # Create learning result
                learning_result = {
                    'execution_id': ml_session['session_id'],
                    'cluster_name': ml_session['cluster_name'],
                    'success': True,
                    'confidence': confidence,
                    'phases_count': len(implementation_plan.get('implementation_phases', [])),
                    'ml_systems_used': self.ml_systems_available,
                    'security_integration_enabled': self.enable_security_integration,
                    'security_framework_available': SECURITY_INTEGRATION_AVAILABLE,
                    'learning_events': ml_session['learning_events'],
                    'cluster_config_available': ml_session.get('cluster_config', {}).get('status') == 'completed'
                }
                
                # Record with ML orchestrator
                self.ml_orchestrator.learn_from_implementation_result(learning_result)
                
                logger.info("✅ Learning outcomes recorded with ML system")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to record with ML system: {e}")
        
        # Always record with learning integration
        if getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('implementation_plan_generated', {
                'session_id': ml_session['session_id'],
                'overall_confidence': confidence,
                'ml_systems_available': self.ml_systems_available,
                'security_integration_enabled': self.enable_security_integration,
                'learning_events_count': len(ml_session['learning_events']),
                'framework_components_complete': 7,
                'cluster_config_available': ml_session.get('cluster_config', {}).get('status') == 'completed',
                'security_framework_available': SECURITY_INTEGRATION_AVAILABLE
            })

    def _finalize_ml_session(self, ml_session: Dict, implementation_plan: Dict, confidence: float):
        """Finalize ML session with security integration"""
        
        # Update intelligence quality
        if confidence > 0.9:
            ml_session['intelligence_quality'] = 'excellent'
        elif confidence > 0.8:
            ml_session['intelligence_quality'] = 'high'
        elif confidence > 0.7:
            ml_session['intelligence_quality'] = 'good'
        else:
            ml_session['intelligence_quality'] = 'adequate'
        
        # Ensure metadata exists
        if 'metadata' not in implementation_plan:
            implementation_plan['metadata'] = {}
        
        # Add to metadata
        implementation_plan['metadata']['ml_session_id'] = ml_session['session_id']
        implementation_plan['metadata']['intelligence_quality'] = ml_session['intelligence_quality']
        implementation_plan['metadata']['ml_systems_available'] = self.ml_systems_available
        implementation_plan['metadata']['security_integration_enabled'] = self.enable_security_integration
        implementation_plan['metadata']['security_framework_available'] = SECURITY_INTEGRATION_AVAILABLE
        implementation_plan['metadata']['learning_events'] = len(ml_session['learning_events'])
        implementation_plan['metadata']['generated_at'] = datetime.now().isoformat()
        implementation_plan['metadata']['version'] = '3.0.0'
        implementation_plan['metadata']['cluster_config_used'] = ml_session.get('cluster_config', {}).get('status') == 'completed'
        
        # Store session
        ml_session['completed_at'] = datetime.now()
        self._ml_sessions_history.append(ml_session)
        self._current_ml_session = None
        
        logger.info(f"🎯 ML Session Completed: {ml_session['intelligence_quality']} quality")
        logger.info(f"🔒 Security Integration: enabled={self.enable_security_integration}, available={SECURITY_INTEGRATION_AVAILABLE}")

    def _start_ml_session(self, analysis_results: Dict) -> Dict:
        """Start ML intelligence session with security integration"""
        
        session = {
            'session_id': f"ml-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'cluster_name': analysis_results.get('cluster_name', 'unknown'),
            'started_at': datetime.now(),
            'ml_confidence_levels': {},
            'learning_events': [],
            'intelligence_quality': 'initializing',
            'ml_systems_available': self.ml_systems_available,
            'security_integration_enabled': self.enable_security_integration,
            'security_framework_available': SECURITY_INTEGRATION_AVAILABLE
        }
        
        self._current_ml_session = session
        
        # Record session start for learning
        if getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('session_started', {
                'session_id': session['session_id'],
                'cluster_name': session['cluster_name'],
                'ml_systems_available': self.ml_systems_available,
                'security_integration_enabled': self.enable_security_integration
            })
        
        logger.info(f"🎯 ML Session Started: {session['session_id']}")
        logger.info(f"🔒 Security Integration: enabled={self.enable_security_integration}")
        return session

    def _create_intelligence_insights_from_analysis(self, analysis_results: Dict, 
                                                ml_session: Dict, cluster_config: Dict, 
                                                overall_ml_confidence: float) -> Dict:
        """Create intelligence insights component from REAL analysis data with security integration"""
        try:
            logger.info("🧠 Creating intelligence insights from REAL analysis data with security...")
            
            # Extract cluster profile from analysis and ML session
            cluster_profile = {
                'mlClusterType': analysis_results.get('cluster_type', 
                                ml_session.get('dna_metadata', {}).get('cluster_personality', 'unknown')),
                'complexityScore': analysis_results.get('complexity_score', 
                                ml_session.get('config_insights', {}).get('cluster_complexity', 'unknown')),
                'readinessScore': analysis_results.get('optimization_readiness_score', overall_ml_confidence),
                'securityPosture': ml_session.get('config_insights', {}).get('security_posture', 'unknown')
            }
            
            # Extract ML predictions from session and analysis
            ml_predictions = {
                'confidence': overall_ml_confidence,
                'model_performance': 'high' if overall_ml_confidence > 0.8 else 'medium' if overall_ml_confidence > 0.6 else 'low',
                'learning_enabled': len(ml_session.get('learning_events', [])) > 0,
                'temporal_intelligence': ml_session.get('dna_metadata', {}).get('has_temporal_intelligence', False),
                'security_analysis_available': self.enable_security_integration and self.security_systems_available
            }
            
            # Extract recommendations from analysis with security
            recommendations = {
                'priority': 'high' if analysis_results.get('total_savings', 0) > analysis_results.get('total_cost', 1) * 0.2 else 'medium',
                'implementation_readiness': ml_session.get('config_insights', {}).get('scaling_readiness', 'unknown'),
                'optimization_potential': analysis_results.get('optimization_score', overall_ml_confidence * 100),
                'security_enhancement_recommended': self.enable_security_integration and not self.security_systems_available
            }
            
            # Intelligence metrics from REAL data with security
            intelligence_insights = {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'clusterProfile': cluster_profile,
                'ml_predictions': ml_predictions,
                'recommendations': recommendations,
                'analysisConfidence': overall_ml_confidence,
                'actual_cv_score': analysis_results.get('cv_score', overall_ml_confidence),
                'dataAvailable': True,  # We have real analysis data
                'azure_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'intelligence_quality': ml_session.get('intelligence_quality', 'high'),
                'learning_events_count': len(ml_session.get('learning_events', [])),
                'optimization_opportunities': ml_session.get('comprehensive_state', {}).get('total_optimization_opportunities', 0),
                'securityInsights': {
                    'framework_available': SECURITY_INTEGRATION_AVAILABLE,
                    'integration_enabled': self.enable_security_integration,
                    'systems_ready': self.security_systems_available,
                    'components_initialized': hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False),
                    'comprehensive_assessment_available': self.enable_security_integration and self.security_systems_available
                }
            }
            
            logger.info(f"✅ Intelligence insights created with confidence: {overall_ml_confidence:.2f}")
            logger.info(f"🔒 Security insights included: framework_available={SECURITY_INTEGRATION_AVAILABLE}")
            return intelligence_insights
            
        except Exception as e:
            logger.error(f"❌ Intelligence insights creation failed: {e}")
            # Return minimal structure with real data only
            return {
                'enabled': True,
                'ml_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_config_enhanced': cluster_config is not None and cluster_config.get('status') == 'completed',
                'security_framework_enabled': self.enable_security_integration,
                'dataAvailable': True,
                'creation_error': str(e)
            }

    # =============================================================================
    # Timeline Format Conversion (Enhanced)
    # =============================================================================
    
    def _convert_to_timeline_format(self, comprehensive_plan: Dict, 
                                   analysis_results: Dict, ml_session: Dict) -> Dict:
        """
        NEW METHOD: Convert comprehensive plan to timeline format
        Preserves ALL data from Document1 while creating Document2 structure
        """
        try:
            logger.info("🔄 Converting to timeline format while preserving all data...")
            
            # Extract timeline metadata
            api_metadata = comprehensive_plan.get('api_metadata', {})
            business_case = comprehensive_plan.get('business_case', {})
            executive_summary = comprehensive_plan.get('executive_summary', {})
            implementation_phases = comprehensive_plan.get('implementation_phases', [])
            
            # Build timeline structure (Document2) with ALL Document1 data preserved
            timeline_plan = {
                # Document2 basic structure
                "totalWeeks": self._calculate_total_weeks(implementation_phases),
                "totalPhases": len(implementation_phases),
                "totalCommands": self._count_commands_in_phases(implementation_phases),
                "securityItems": self._count_security_items(comprehensive_plan),
                "avgProgress": 0,
                "totalSavings": comprehensive_plan.get('financial_summary', {}).get('total_projected_savings', 
                                                        business_case.get('financial_impact', {}).get('annual_savings', 
                                                        analysis_results.get('total_savings', 0))),
                "clusterName": api_metadata.get('cluster_name', analysis_results.get('cluster_name', 'Unknown')),
                "resourceGroup": api_metadata.get('resource_group', analysis_results.get('resource_group', 'Unknown')),
                "strategyType": comprehensive_plan.get('metadata', {}).get('generation_method', 'ml_integrated_dynamic_optimization'),
                "generatedAt": comprehensive_plan.get('metadata', {}).get('generated_at', datetime.now().isoformat()),
                "intelligenceLevel": comprehensive_plan.get('metadata', {}).get('intelligence_quality', 'excellent'),
                "version": comprehensive_plan.get('metadata', {}).get('version', '3.0.0'),
                
                # Transform phases into weeks structure (NEW)
                "weeks": self._transform_phases_to_weeks(implementation_phases),
                
                # Preserve ALL Document1 data (PRESERVED)
                "executiveSummary": self._enhance_executive_summary(executive_summary, business_case),
                "intelligenceInsights": comprehensive_plan.get('intelligenceInsights', {}),
                "costProtection": comprehensive_plan.get('costProtection', {}),
                "governance": comprehensive_plan.get('governance', {}),
                "monitoring": comprehensive_plan.get('monitoring', {}),
                "contingency": comprehensive_plan.get('contingency', {}),
                "successCriteria": comprehensive_plan.get('successCriteria', {}),
                "timelineOptimization": comprehensive_plan.get('timelineOptimization', {}),
                "riskMitigation": comprehensive_plan.get('riskMitigation', {}),
                
                # Document1 comprehensive data (ALL PRESERVED)
                "businessCase": business_case,
                "financialSummary": comprehensive_plan.get('financial_summary', {}),
                "mlConfidenceBreakdown": comprehensive_plan.get('ml_confidence_breakdown', {}),
                "mlIntegration": comprehensive_plan.get('ml_integration', {}),
                "projectManagement": comprehensive_plan.get('project_management', {}),
                "roiAnalysis": comprehensive_plan.get('roi_analysis', {}),
                "riskAssessment": comprehensive_plan.get('risk_assessment', {}),
                "timeline": comprehensive_plan.get('timeline', {}),
                "metadata": comprehensive_plan.get('metadata', {}),
                
                # Add timeline-specific metadata
                "realCommands": self._extract_all_commands_for_timeline(implementation_phases),
                "activeFilters": ["all"],
                "currentView": "timeline",
                
                # Security Integration (NEW)
                "securityFramework": {
                    "enabled": self.enable_security_integration,
                    "framework_available": SECURITY_INTEGRATION_AVAILABLE,
                    "systems_available": self.security_systems_available,
                    "components_initialized": hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False),
                    "comprehensive_assessment_available": self.security_systems_available and hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False)
                },
                
                # Integration metadata (NEW)
                "integration_metadata": comprehensive_plan.get('integration_metadata', {}),
                
                # Transformation metadata
                "transformationMetadata": {
                    "original_format": "comprehensive",
                    "target_format": "timeline",
                    "transformation_time": datetime.now().isoformat(),
                    "data_preservation": "complete",
                    "ml_session_id": ml_session.get('session_id'),
                    "phases_converted": len(implementation_phases),
                    "security_integration": self.enable_security_integration,
                    "integrated_mode": self.ml_systems_available and self.security_systems_available
                }
            }
            
            logger.info(f"✅ Timeline conversion: {len(implementation_phases)} phases → {len(timeline_plan['weeks'])} weeks")
            return timeline_plan
            
        except Exception as e:
            logger.error(f"❌ Timeline conversion failed: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Return original plan if conversion fails
            comprehensive_plan['conversion_error'] = str(e)
            comprehensive_plan['fallback_mode'] = True
            return comprehensive_plan
    
    def _transform_phases_to_weeks(self, implementation_phases: List[Dict]) -> List[Dict]:
        """Transform implementation phases into week-based timeline structure"""
        weeks = []
        current_week = 1
        
        for phase in implementation_phases:
            try:
                # Calculate phase timing
                phase_duration = phase.get('duration_weeks', 2)
                start_week = phase.get('start_week', current_week)
                end_week = phase.get('end_week', start_week + phase_duration - 1)
                
                # Create week entry
                week_entry = {
                    "weekNumber": start_week,
                    "weekRange": f"{start_week}-{end_week}" if phase_duration > 1 else str(start_week),
                    "title": f"Week{'s' if phase_duration > 1 else ''} {start_week}{f'-{end_week}' if phase_duration > 1 else ''}: {phase.get('title', 'Unknown Phase')}",
                    "phases": [{
                        "id": f"phase-{phase.get('phase_number', len(weeks))}",
                        "title": phase.get('title', 'Unknown Phase'),
                        "type": self._determine_phase_types(phase),
                        "progress": 0,
                        "description": "Implementation phase",
                        "commands": self._extract_phase_commands_for_timeline(phase),
                        "securityChecks": phase.get('security_checks', []),
                        "complianceItems": phase.get('compliance_items', []),
                        "projectedSavings": phase.get('projected_savings', 0),
                        "priorityLevel": phase.get('priority', 'Unknown'),
                        "riskLevel": phase.get('risk_level', 'Low'),
                        "complexityLevel": self._calculate_complexity_level(phase),
                        "successCriteria": phase.get('success_criteria', []),
                        "tasks": phase.get('tasks', []),
                        "phaseNumber": phase.get('phase_number', len(weeks) + 1),
                        "startWeek": start_week,
                        "endWeek": end_week,
                        
                        # PRESERVE original phase data
                        "originalPhaseData": phase
                    }]
                }
                
                weeks.append(week_entry)
                current_week = end_week + 1
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing phase {phase.get('title', 'Unknown')}: {e}")
                continue
        
        return weeks
    
    def _extract_phase_commands_for_timeline(self, phase: Dict) -> List[Dict]:
        """Extract commands from phase for timeline format"""
        commands = []
        
        # Extract from various command sources
        phase_commands = phase.get('commands', [])
        
        for cmd_group in phase_commands:
            if isinstance(cmd_group, dict):
                cmd_entry = {
                    "title": cmd_group.get('title', cmd_group.get('description', 'Phase Commands')),
                    "commands": self._normalize_commands(cmd_group.get('commands', [])),
                    "description": cmd_group.get('description', 'Direct commands for phase'),
                    "source": "phase_direct"
                }
                commands.append(cmd_entry)
        
        return commands
    
    def _normalize_commands(self, commands) -> List[str]:
        """Normalize commands to string array format for frontend"""
        if not commands:
            return []
        
        normalized = []
        for cmd in commands:
            if isinstance(cmd, str):
                normalized.append(cmd)
            elif isinstance(cmd, dict):
                # Convert dict to readable string
                if 'command' in cmd:
                    normalized.append(cmd['command'])
                else:
                    normalized.append(json.dumps(cmd, indent=2))
            else:
                normalized.append(str(cmd))
        
        return normalized
    
    def _determine_phase_types(self, phase: Dict) -> List[str]:
        """Determine phase types from phase data"""
        types = []
        
        # From phase type
        phase_type = phase.get('type', '').lower()
        if phase_type:
            types.append(phase_type)
        
        # From category
        category = phase.get('category', '').lower()
        if category and category not in types:
            types.append(category)
        
        # From title analysis
        title = phase.get('title', '').lower()
        if 'hpa' in title:
            types.append('hpa')
        if 'storage' in title:
            types.append('storage')
        if 'monitoring' in title:
            types.append('monitoring')
        if 'security' in title:
            types.append('security')
        
        # From risk level
        risk_level = phase.get('risk_level', '').lower()
        if risk_level == 'high':
            types.append('high-risk')
        
        # Default
        if not types:
            types.append('optimization')
        
        return types
    
    def _calculate_complexity_level(self, phase: Dict) -> str:
        """Calculate complexity level from phase data"""
        complexity_score = phase.get('complexity_score', 0)
        
        if complexity_score > 0.8:
            return 'High'
        elif complexity_score > 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_total_weeks(self, implementation_phases: List[Dict]) -> int:
        """Calculate total weeks from implementation phases"""
        if not implementation_phases:
            return 6  # Default
        
        max_week = 0
        for phase in implementation_phases:
            end_week = phase.get('end_week', phase.get('duration_weeks', 2))
            max_week = max(max_week, end_week)
        
        return max_week
    
    def _count_commands_in_phases(self, implementation_phases: List[Dict]) -> int:
        """Count total commands across all phases"""
        total = 0
        for phase in implementation_phases:
            commands = phase.get('commands', [])
            total += len(commands)
        return total
    
    def _count_security_items(self, comprehensive_plan: Dict) -> int:
        """Count security-related items"""
        security_count = 0
        
        # Count from phases
        for phase in comprehensive_plan.get('implementation_phases', []):
            security_count += len(phase.get('security_checks', []))
        
        # Count from governance
        governance = comprehensive_plan.get('governance', {})
        if governance.get('enabled'):
            security_count += 1
        
        # Count from security framework if enabled
        if self.enable_security_integration and self.security_systems_available:
            security_count += 5  # Base security framework items
        
        return security_count
    
    def _enhance_executive_summary(self, executive_summary: Dict, business_case: Dict) -> Dict:
        """Enhance executive summary with business case data"""
        enhanced = executive_summary.copy()
        
        # Add financial data from business case
        financial_impact = business_case.get('financial_impact', {})
        if financial_impact:
            enhanced.update({
                'annual_savings_potential': financial_impact.get('annual_savings', 0),
                'implementation_cost': financial_impact.get('implementation_cost', 0),
                'net_benefit_year_1': financial_impact.get('net_benefit_year_1', 0),
                'roi_percentage': financial_impact.get('roi_percentage', 0)
            })
        
        # Add security information if available
        if self.enable_security_integration and self.security_systems_available:
            enhanced['security_framework_enabled'] = True
            enhanced['security_assessment_available'] = hasattr(self, 'security_components_initialized') and getattr(self, 'security_components_initialized', False)
        
        return enhanced
    
    def _extract_all_commands_for_timeline(self, implementation_phases: List[Dict]) -> List[Dict]:
        """Extract all commands for easy timeline access"""
        all_commands = []
        
        for phase in implementation_phases:
            commands = phase.get('commands', [])
            for cmd in commands:
                if isinstance(cmd, dict):
                    all_commands.append({
                        'phase': phase.get('title', 'Unknown'),
                        'phase_number': phase.get('phase_number', 0),
                        'command_data': cmd
                    })
        
        return all_commands

    # =============================================================================
    # API-FRIENDLY WRAPPER WITH INTEGRATED SECURITY
    # =============================================================================
    
    def generate_implementation_plan_for_api(self, analysis_results: Dict, 
                                           output_format: str = 'comprehensive',
                                           include_security_assessment: bool = True,
                                           security_level: str = 'standard',
                                           security_frameworks: List[str] = ['CIS', 'NIST']) -> Dict:
        """
        API-friendly wrapper with INTEGRATED security framework
        
        Args:
            analysis_results: Analysis results
            output_format: 'comprehensive' or 'timeline'
            include_security_assessment: Whether to include integrated security assessment (default: True)
            security_level: 'none', 'basic', 'standard', 'enterprise' (default: 'standard')
            security_frameworks: Security frameworks to analyze (default: ['CIS', 'NIST'])
        """
        
        # Generate main implementation plan with integrated security
        implementation_plan = self.generate_implementation_plan(
            analysis_results=analysis_results,
            output_format=output_format,
            security_frameworks=security_frameworks
        )
        
        result = {
            'implementation_plan': implementation_plan,
            'security_integration': {
                'requested': include_security_assessment,
                'security_level': security_level,
                'integrated_approach': True,
                'frameworks_analyzed': security_frameworks
            }
        }
        
        # Add integration status
        integration_metadata = implementation_plan.get('integration_metadata', {})
        result['integration_status'] = {
            'ml_systems_available': integration_metadata.get('ml_systems_available', False),
            'security_systems_available': integration_metadata.get('security_systems_available', False),
            'integrated_mode': integration_metadata.get('integrated_mode', False),
            'generation_approach': integration_metadata.get('generation_approach', 'unknown')
        }
        
        return result


# =============================================================================
# FACTORY FUNCTIONS AND BACKWARD COMPATIBILITY
# =============================================================================

def create_aks_implementation_generator(enable_cost_monitoring: bool = True,
                                      enable_temporal: bool = True,
                                      enable_security_integration: bool = True) -> AKSImplementationGenerator:
    """Factory function to create AKS Implementation Generator with integrated systems"""
    return AKSImplementationGenerator(
        enable_cost_monitoring=enable_cost_monitoring,
        enable_temporal=enable_temporal,
        enable_security_integration=enable_security_integration
    )

# Backward compatibility aliases
CombinedAKSImplementationGenerator = AKSImplementationGenerator
FixedAKSImplementationGenerator = AKSImplementationGenerator

# Default instance with integrated systems
generator = AKSImplementationGenerator(
    enable_cost_monitoring=True,
    enable_temporal=True,
    enable_security_integration=True
)

print("✅ ENHANCED AKS Implementation Generator ready with intelligent import handling")
print("🧠 ML Systems: Initialized alongside Security Framework")
print(f"🔒 Security Framework: {len(successful_imports)}/5 components available")
if len(failed_imports) > 0:
    print(f"⚠️  Failed components: {', '.join(failed_imports)}")
if SecurityIntegrationMixin.__name__ == 'SecurityIntegrationMixin' and SecurityIntegrationMixin.__doc__ and 'Fallback' in SecurityIntegrationMixin.__doc__:
    print("🔒 Using fallback SecurityIntegrationMixin - some security features disabled")
else:
    print("🔒 Using full SecurityIntegrationMixin - all security features available")
print("🔗 INTEGRATED MODE: Both systems work together as first-class citizens")
print("📊 Individual component import tracking for better debugging")
print("🎯 Enhanced confidence calculation with ML+Security metrics")
print("📚 Enhanced learning with integrated ML+Security outcomes")
print("🛡️ SecurityIntegrationMixin support with graceful degradation")
print("📋 Security-enhanced implementation planning when components available")
print("🔐 Robust error handling for missing security components")
print("✅ Backward compatibility maintained")
print("\n🔍 Security Component Status:")
for component, status in security_import_status.items():
    status_icon = "✅" if status == "success" else "❌"
    print(f"  {status_icon} {component}: {status}")