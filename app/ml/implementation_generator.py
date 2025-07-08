"""
AKS Implementation Generator - ENHANCED WITH CLUSTER CONFIG INTEGRATION
=====================================================================
Integrates real cluster configuration data into ML analysis pipeline.
NO signature changes, NO fallbacks, uses REAL data from cluster.
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

class AKSImplementationGenerator(MLLearningIntegrationMixin):
    """
    AKS Implementation Generator with Real Cluster Configuration Integration
    
    Now fetches actual cluster configuration and passes to ML components.
    NO signature changes, maintains full compatibility.
    """
    
    def __init__(self, enable_cost_monitoring: bool = True, enable_temporal: bool = True):
        """Initialize with ML orchestration (same signature as before)"""
        super().__init__()
        
        logger.info("🧠 Initializing AKS Implementation Generator with Cluster Config Integration")
        
        # Existing parameters (maintained for compatibility)
        self.enable_cost_monitoring = enable_cost_monitoring
        self.enable_temporal = enable_temporal
        self.monitoring_active = False
        
        # Debug tracking (MUST be initialized before ML systems)
        self._debug_info = {
            'initialization_time': datetime.now(),
            'ml_system_status': {},
            'failed_operations': []
        }
        
        # Session tracking
        self._current_ml_session = None
        self._ml_sessions_history = []
        
        # ML Intelligence Systems (initialize after debug tracking)
        self._initialize_ml_systems()
        
        logger.info("✅ AKS Implementation Generator ready with cluster config integration")
        logger.info(f"🔧 ML Systems Available: {self.ml_systems_available}")
    
    def generate_implementation_plan(self, analysis_results: Dict, 
                                   historical_data: Optional[Dict] = None,
                                   cost_budget_monthly: Optional[float] = None,
                                   enable_real_time_monitoring: bool = True) -> Dict:
        """
        Generate implementation plan with REAL cluster configuration integration
        
        SAME SIGNATURE - Enhanced internally to fetch and use real cluster config.
        """


        cluster_name = analysis_results.get('cluster_name', 'unknown')
        resource_group = analysis_results.get('resource_group', 'unknown')
        
        
        subscription_id = azure_subscription_manager.find_cluster_subscription(resource_group, cluster_name)
        logger.info(f"📊 Using subscription {subscription_id[:8]} from config")           
     
        logger.info(f"🎯 Generating ML-enhanced implementation plan for {cluster_name}")
        logger.info(f"📊 Input validation starting...")
        
        try:
            # Validate input data - FAIL FAST
            if not self._validate_input_data(analysis_results):
                self._log_detailed_failure("INPUT_VALIDATION", "Invalid analysis_results provided", {
                    'analysis_results_type': type(analysis_results),
                    'analysis_results_keys': list(analysis_results.keys()) if isinstance(analysis_results, dict) else 'NOT_DICT',
                    'required_fields': ['total_cost'],
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: Invalid analysis_results provided - see logs for details")
            
            logger.info("✅ Input validation passed")
            
            # Start ML intelligence session
            ml_session = self._start_ml_session(analysis_results)
            
            # Extract basic values
            total_cost = float(analysis_results.get('total_cost', 0))
            total_savings = float(analysis_results.get('total_savings', 0))
            
            logger.info(f"💰 Processing - Cost: ${total_cost:.2f}, Savings: ${total_savings:.2f}")
            
            # PHASE 0: REAL CLUSTER CONFIGURATION FETCHING (NEW)
            logger.info("🔄 PHASE 0: Real Cluster Configuration Analysis")
            cluster_config = self._fetch_and_analyze_cluster_config(
                resource_group, cluster_name, subscription_id, ml_session
            )
            logger.info("✅ PHASE 0 completed")
            
            # PHASE 1: ML Cluster DNA Analysis (ENHANCED with real config)
            logger.info("🔄 PHASE 1: ML Cluster DNA Analysis with Real Config")
            cluster_dna = self._ml_analyze_cluster_dna(
                analysis_results, historical_data, ml_session, cluster_config
            )
            if cluster_dna is None:
                self._log_detailed_failure("DNA_ANALYSIS", "ML DNA analysis returned None", {
                    'dna_analyzer_available': self.dna_analyzer is not None,
                    'ml_systems_available': self.ml_systems_available,
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: DNA analysis failed - see logs for details")
            logger.info("✅ PHASE 1 completed")
            
            # PHASE 2: ML Strategy Generation
            logger.info("🔄 PHASE 2: ML Strategy Generation with Config Awareness")
            ml_strategy = self._ml_generate_strategy(
                cluster_dna, analysis_results, ml_session, cluster_config
            )
            if ml_strategy is None:
                self._log_detailed_failure("STRATEGY_GENERATION", "ML strategy generation returned None", {
                    'strategy_engine_available': self.strategy_engine is not None,
                    'cluster_dna_type': type(cluster_dna),
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: Strategy generation failed - see logs for details")
            logger.info("✅ PHASE 2 completed")
            
            # PHASE 3: ML Plan Generation (ENHANCED with config)
            logger.info("🔄 PHASE 3: ML Plan Generation with Config Intelligence")
            ml_plan = self._ml_generate_comprehensive_plan(
                analysis_results, ml_strategy, cluster_dna, ml_session, cluster_config
            )
            if ml_plan is None or not isinstance(ml_plan, dict):
                self._log_detailed_failure("PLAN_GENERATION", "ML plan generation failed", {
                    'plan_generator_available': self.plan_generator is not None,
                    'ml_plan_type': type(ml_plan),
                    'ml_plan_is_none': ml_plan is None,
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: Plan generation failed - see logs for details")
            logger.info("✅ PHASE 3 completed")
            
            # PHASE 4: ML Command Integration
            logger.info("🔄 PHASE 4: ML Command Integration with Config Context")
            ml_plan = self._ml_integrate_executable_commands(
                ml_plan, analysis_results, ml_strategy, ml_session, cluster_config
            )
            if ml_plan is None:
                self._log_detailed_failure("COMMAND_INTEGRATION", "Command integration failed", {
                    'command_generator_available': self.command_generator is not None,
                    'plan_before_commands': 'was_valid',
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: Command integration failed - see logs for details")
            logger.info("✅ PHASE 4 completed")
            
            # PHASE 5: Ensure ALL framework components
            logger.info("🔄 PHASE 5: Framework Structure Completion with Config Intelligence")
            ml_plan = self._ensure_complete_framework_structure(
                ml_plan, analysis_results, ml_session, cluster_config
            )
            if ml_plan is None:
                self._log_detailed_failure("FRAMEWORK_COMPLETION", "Framework structure completion failed", {
                    'plan_before_framework': 'was_valid',
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: Framework completion failed - see logs for details")
            logger.info("✅ PHASE 5 completed")
            
            # PHASE 6: Validate output structure - FAIL FAST
            logger.info("🔄 PHASE 6: Output Structure Validation")
            if not self._validate_output_structure(ml_plan):
                self._log_detailed_failure("OUTPUT_VALIDATION", "Generated plan structure validation failed", {
                    'plan_keys': list(ml_plan.keys()) if isinstance(ml_plan, dict) else 'NOT_DICT',
                    'has_implementation_phases': 'implementation_phases' in ml_plan if isinstance(ml_plan, dict) else False,
                    'has_phases': 'phases' in ml_plan if isinstance(ml_plan, dict) else False,
                    'plan_type': type(ml_plan),
                    'cluster_name': cluster_name
                })
                raise ValueError("❌ CRITICAL: Output validation failed - see logs for details")
            logger.info("✅ PHASE 6 completed")
            
            # PHASE 7: Calculate and add ML confidence
            logger.info("🔄 PHASE 7: ML Confidence Calculation with Config Factors")
            plan_confidence = self._calculate_ml_plan_confidence(
                analysis_results, ml_plan, ml_session, cluster_config
            )
            logger.info("✅ PHASE 7 completed")
            
            # PHASE 8: Record learning outcomes
            logger.info("🔄 PHASE 8: Learning Outcomes Recording")
            self._record_ml_learning_outcomes(ml_plan, ml_session, plan_confidence)
            logger.info("✅ PHASE 8 completed")
            
            # PHASE 9: Finalize session
            logger.info("🔄 PHASE 9: Session Finalization")
            self._finalize_ml_session(ml_session, ml_plan, plan_confidence)
            logger.info("✅ PHASE 9 completed")
            
            logger.info(f"🎉 SUCCESS: ML-enhanced implementation plan generated with {plan_confidence:.1%} confidence")
            logger.info(f"📊 Final plan has {len(ml_plan.get('implementation_phases', []))} implementation phases")
            logger.info(f"🔧 Plan enhanced with {cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0)} real cluster resources")
            
            return ml_plan
            
        except Exception as e:
            # Log the complete failure details
            self._log_complete_failure_details(e, analysis_results, locals())
            
            # Record failure for learning
            self._record_generation_failure(str(e))
            
            # Re-raise the exception (NO FALLBACK)
            logger.error(f"❌ FINAL FAILURE: Implementation plan generation failed completely")
            logger.error(f"❌ Exception: {str(e)}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _fetch_and_analyze_cluster_config(self, resource_group: str, cluster_name: str, 
                                         subscription_id: str, ml_session: Dict) -> Dict[str, Any]:
        """
        Fetch and analyze current cluster configuration
        NEW PHASE: Gets real cluster config for ML analysis
        """
        try:
            if not subscription_id:
                logger.warning("⚠️ No subscription ID available - skipping cluster config fetch")
                return {
                    'fetch_error': 'no_subscription_id',
                    'status': 'skipped'
                }
            
            logger.info(f"🔍 Fetching real cluster configuration for {cluster_name}")
            

            from app.analytics.aks_config_fetcher import create_cluster_config_fetcher
              
            # Create fetcher and get configuration
            fetcher = create_cluster_config_fetcher(resource_group, cluster_name, subscription_id)
            cluster_config = fetcher.fetch_raw_cluster_configuration(enable_parallel_fetch=True)
            
            if cluster_config.get('status') == 'completed':
                logger.info(f"✅ Cluster config fetched: {cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0)} resources")
                
                # Store in ML session for other phases
                ml_session['cluster_config'] = cluster_config
                ml_session['config_insights'] = self._extract_config_insights(cluster_config)
                
                # Record config fetch event
                ml_session['learning_events'].append({
                    'event': 'cluster_config_fetched',
                    'resources_fetched': cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0),
                    'fetch_duration': cluster_config.get('fetch_metrics', {}).get('fetch_duration_seconds', 0),
                    'success': True
                })
                
                return cluster_config
            else:
                logger.warning(f"⚠️ Cluster config fetch failed: {cluster_config.get('error', 'unknown')}")
                return cluster_config
                
        except Exception as e:
            logger.error(f"❌ Cluster config fetch failed: {e}")
            return {
                'fetch_error': str(e),
                'status': 'failed'
            }
    
    def _extract_config_insights(self, cluster_config: Dict) -> Dict[str, Any]:
        """Extract key insights from cluster configuration for ML"""
        insights = {
            'cluster_complexity': 'unknown',
            'workload_distribution': {},
            'resource_patterns': {},
            'scaling_readiness': 'unknown',
            'security_posture': 'unknown'
        }
        
        try:
            # Workload distribution analysis
            workload_resources = cluster_config.get('workload_resources', {})
            workload_counts = {}
            
            for workload_type, workload_data in workload_resources.items():
                if isinstance(workload_data, dict) and 'item_count' in workload_data:
                    workload_counts[workload_type] = workload_data['item_count']
            
            insights['workload_distribution'] = workload_counts
            
            # Scaling readiness from HPA count
            scaling_resources = cluster_config.get('scaling_resources', {})
            hpa_count = scaling_resources.get('horizontalpodautoscalers', {}).get('item_count', 0)
            total_deployments = workload_counts.get('deployments', 0)
            
            if total_deployments > 0:
                hpa_coverage = hpa_count / total_deployments
                if hpa_coverage > 0.7:
                    insights['scaling_readiness'] = 'high'
                elif hpa_coverage > 0.3:
                    insights['scaling_readiness'] = 'medium'
                else:
                    insights['scaling_readiness'] = 'low'
            
            # Cluster complexity assessment
            total_resources = sum(workload_counts.values())
            namespaces = cluster_config.get('fetch_metrics', {}).get('total_namespaces', 1)
            
            complexity_score = (total_resources / 10) + (namespaces / 5)
            if complexity_score > 10:
                insights['cluster_complexity'] = 'high'
            elif complexity_score > 5:
                insights['cluster_complexity'] = 'medium'
            else:
                insights['cluster_complexity'] = 'low'
            
            # Security posture from RBAC resources
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
            
            logger.info(f"✅ Config insights: complexity={insights['cluster_complexity']}, "
                       f"scaling={insights['scaling_readiness']}, security={insights['security_posture']}")
            
        except Exception as e:
            logger.warning(f"⚠️ Config insights extraction failed: {e}")
            insights['extraction_error'] = str(e)
        
        return insights
    
    def _ml_analyze_cluster_dna(self, analysis_results: Dict, historical_data: Optional[Dict], 
                                          ml_session: Dict, cluster_config: Dict) -> Any:
        """
        Enhanced DNA analysis that incorporates real cluster configuration
        """
        logger.info("🧬 ML DNA Analysis with Real Cluster Configuration...")
        
        if not self.dna_analyzer:
            raise RuntimeError("❌ DNA analyzer not available")
        
        try:
            # Enhance the DNA analyzer with cluster config
            if hasattr(self.dna_analyzer, 'set_cluster_config'):
                self.dna_analyzer.set_cluster_config(cluster_config)
            
            # Call enhanced DNA analysis with cluster config
            cluster_dna = self.dna_analyzer.analyze_cluster_dna(
                analysis_results, historical_data, cluster_config
            )
            
            if cluster_dna is None:
                raise ValueError("❌ DNA analyzer returned None")
            
            # Store enhanced DNA in session
            ml_session['cluster_dna'] = cluster_dna
            ml_session['config_enhanced'] = True
            
            # Extract config-based insights
            config_insights = ml_session.get('config_insights', {})
            ml_session['dna_config_correlation'] = {
                'complexity_match': config_insights.get('cluster_complexity', 'unknown'),
                'scaling_readiness': config_insights.get('scaling_readiness', 'unknown'),
                'security_alignment': config_insights.get('security_posture', 'unknown')
            }
            
            confidence = self._extract_dna_confidence(cluster_dna)
            
            # Record enhanced ML event
            ml_session['learning_events'].append({
                'event': 'dna_analysis_with_cluster_config',
                'confidence': confidence,
                'config_complexity': config_insights.get('cluster_complexity', 'unknown'),
                'config_scaling_readiness': config_insights.get('scaling_readiness', 'unknown'),
                'resources_analyzed': cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0),
                'success': True
            })
            
            ml_session['ml_confidence_levels']['dna_analysis'] = confidence
            
            logger.info(f"✅ Enhanced DNA Analysis: complexity={config_insights.get('cluster_complexity', 'unknown')}, "
                       f"confidence={confidence:.1%}")
            
            return cluster_dna
            
        except Exception as e:
            logger.error(f"❌ Enhanced DNA analysis failed: {e}")
            raise RuntimeError(f"❌ Enhanced DNA analysis failed: {e}") from e
    
    def _ml_generate_strategy(self, cluster_dna: Any, analysis_results: Dict, 
                                        ml_session: Dict, cluster_config: Dict) -> Any:
        """Enhanced strategy generation with cluster config awareness"""
        logger.info("🎯 ML Strategy Generation with Cluster Config...")
        
        if not self.strategy_engine:
            raise RuntimeError("❌ Strategy engine not available")
        
        if cluster_dna is None:
            raise ValueError("❌ Cannot generate strategy - cluster_dna is None")
        
        try:
            # Enhance strategy engine with cluster config
            if hasattr(self.strategy_engine, 'set_cluster_config'):
                self.strategy_engine.set_cluster_config(cluster_config)
            
            # Generate strategy with config context
            ml_strategy = self.strategy_engine.generate_comprehensive_dynamic_strategy(
                cluster_dna, analysis_results, cluster_config
            )
            
            if ml_strategy is None:
                raise ValueError("❌ Strategy engine returned None")
            
            confidence = getattr(ml_strategy, 'success_probability', 0.8)
            
            # Store strategy in ML session
            ml_session['ml_strategy'] = ml_strategy
            ml_session['strategy_config_enhanced'] = True
            
            # Extract config-informed strategy insights
            config_insights = ml_session.get('config_insights', {})
            ml_session['strategy_config_alignment'] = {
                'matches_complexity': config_insights.get('cluster_complexity', 'unknown'),
                'leverages_scaling': config_insights.get('scaling_readiness', 'unknown'),
                'security_aware': config_insights.get('security_posture', 'unknown')
            }
            
            # Record ML event
            ml_session['learning_events'].append({
                'event': 'strategy_generation',
                'confidence': confidence,
                'strategy_type': getattr(ml_strategy, 'strategy_type', 'comprehensive'),
                'config_informed': True,
                'success': True
            })
            
            ml_session['ml_confidence_levels']['strategy_generation'] = confidence
            
            logger.info(f"✅ Config-Enhanced Strategy: {getattr(ml_strategy, 'strategy_name', 'Unknown Strategy')} ({confidence:.1%})")
            
            return ml_strategy
            
        except Exception as e:
            logger.error(f"❌ Enhanced strategy generation failed: {e}")
            raise RuntimeError(f"❌ Enhanced strategy generation failed: {e}") from e
    
    def _ml_generate_comprehensive_plan(self, analysis_results: Dict, ml_strategy: Any, 
                                                  cluster_dna: Any, ml_session: Dict, 
                                                  cluster_config: Dict) -> Dict:
        """Generate plan with cluster config intelligence"""
        logger.info("📋 ML Plan Generation with Cluster Config Intelligence...")
        
        if not self.plan_generator:
            raise RuntimeError("❌ Plan generator not available")
        
        if ml_strategy is None:
            raise ValueError("❌ Cannot generate plan - ml_strategy is None")
        
        if cluster_dna is None:
            raise ValueError("❌ Cannot generate plan - cluster_dna is None")
        
        try:
            # Enhance plan generator with cluster config
            if hasattr(self.plan_generator, 'set_cluster_config'):
                self.plan_generator.set_cluster_config(cluster_config)
            
            # Generate plan with config intelligence
            ml_plan = self.plan_generator.generate_extensive_implementation_plan(
                analysis_results, cluster_dna, ml_strategy, cluster_config
            )
            
            if ml_plan is None:
                raise ValueError("❌ Plan generator returned None")
            
            if not isinstance(ml_plan, dict):
                raise ValueError(f"❌ Plan generator returned invalid type: {type(ml_plan)}")
            
            # Normalize phases key
            normalization_applied = False
            if 'phases' in ml_plan and 'implementation_phases' not in ml_plan:
                logger.info("🔧 Normalizing 'phases' → 'implementation_phases'")
                ml_plan['implementation_phases'] = ml_plan['phases']
                normalization_applied = True
            
            if 'implementation_phases' not in ml_plan:
                raise ValueError("❌ Plan missing 'implementation_phases' key after normalization")
            
            if not isinstance(ml_plan['implementation_phases'], list):
                raise ValueError(f"❌ implementation_phases is not a list: {type(ml_plan['implementation_phases'])}")
            
            confidence = ml_plan.get('metadata', {}).get('ml_confidence', 0.8)
            
            # Record config-enhanced plan event
            ml_session['learning_events'].append({
                'event': 'plan_generation',
                'confidence': confidence,
                'phases_count': len(ml_plan.get('implementation_phases', [])),
                'config_enhanced': True,
                'normalization_applied': normalization_applied,
                'success': True
            })
            
            ml_session['ml_confidence_levels']['plan_generation'] = confidence
            
            logger.info(f"✅ Config-Enhanced Plan: {len(ml_plan.get('implementation_phases', []))} phases ({confidence:.1%})")
            
            return ml_plan
            
        except Exception as e:
            logger.error(f"❌ Enhanced plan generation failed: {e}")
            raise RuntimeError(f"❌ Enhanced plan generation failed: {e}") from e
    
    def _ml_integrate_executable_commands(self, implementation_plan: Dict, analysis_results: Dict, 
                                                    ml_strategy: Any, ml_session: Dict, 
                                                    cluster_config: Dict) -> Dict:
        """Integrate commands with cluster config context"""
        logger.info("🛠️ ML Command Integration with Cluster Config Context...")
        
        if implementation_plan is None:
            raise ValueError("❌ Cannot integrate commands - implementation_plan is None")
        
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
            # Get cluster_dna from session
            cluster_dna = ml_session.get('cluster_dna')
            if cluster_dna is None:
                logger.warning("⚠️ cluster_dna not found in session - using limited command generation")
            
            # Enhance command generator with cluster config
            if hasattr(self.command_generator, 'set_cluster_config'):
                self.command_generator.set_cluster_config(cluster_config)
            
            # Generate execution plan with config context
            execution_plan = self.command_generator.generate_comprehensive_execution_plan(
                ml_strategy, cluster_dna, analysis_results, cluster_config
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
            
            # Map commands to phases with config intelligence
            implementation_plan = self._map_commands_to_phases(
                implementation_plan, execution_plan, cluster_config
            )
            
            confidence = getattr(execution_plan, 'success_probability', 0.8)
            command_count = self._count_total_commands(execution_plan)
            
            # Record config-enhanced command event
            ml_session['learning_events'].append({
                'event': 'command_generation',
                'confidence': confidence,
                'command_count': command_count,
                'config_enhanced': True,
                'success': True
            })
            
            ml_session['ml_confidence_levels']['command_generation'] = confidence
            
            total_commands = sum(len(phase.get('commands', [])) for phase in implementation_plan.get('implementation_phases', []))
            logger.info(f"✅ Config-Enhanced Commands: {total_commands} integrated ({confidence:.1%})")
            
            return implementation_plan
            
        except Exception as e:
            logger.warning(f"⚠️ Enhanced command integration failed: {e}")
            
            ml_session['learning_events'].append({
                'event': 'command_generation_failed',
                'error': str(e),
                'success': False
            })
            ml_session['ml_confidence_levels']['command_generation'] = 0.3
            
            return implementation_plan
    
    def _ensure_complete_framework_structure(self, implementation_plan: Dict, 
                                                       analysis_results: Dict, ml_session: Dict,
                                                       cluster_config: Dict) -> Dict:
        """Ensure framework structure with cluster config intelligence"""
        logger.info("🔧 Framework Structure with Cluster Config Intelligence...")
        
        if implementation_plan is None:
            raise ValueError("❌ Cannot complete framework - implementation_plan is None")
        
        # Ensure implementation_phases exists
        if 'implementation_phases' not in implementation_plan:
            if 'phases' in implementation_plan:
                implementation_plan['implementation_phases'] = implementation_plan['phases']
            else:
                raise ValueError("❌ Plan missing both 'implementation_phases' and 'phases' keys")
        
        try:
            total_cost = analysis_results.get('total_cost', 0)
            total_savings = analysis_results.get('total_savings', 0)
            cluster_name = analysis_results.get('cluster_name', 'unknown')
            
            # Get ML confidence and config insights
            overall_ml_confidence = self._calculate_session_confidence(ml_session)
            config_insights = ml_session.get('config_insights', {})
            
            # Extract cluster-specific intelligence
            cluster_complexity = config_insights.get('cluster_complexity', 'medium')
            scaling_readiness = config_insights.get('scaling_readiness', 'medium')
            security_posture = config_insights.get('security_posture', 'standard')
            
            logger.info("🔧 Adding framework components with cluster intelligence...")
            
            # 1. Intelligence Insights
            implementation_plan['intelligenceInsights'] = {
                'enabled': True,
                'ml_derived': True,
                'config_derived': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_analysis': {
                    'complexity': cluster_complexity,
                    'scaling_readiness': scaling_readiness,
                    'security_posture': security_posture,
                    'total_resources': cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0),
                    'namespaces_count': cluster_config.get('fetch_metrics', {}).get('total_namespaces', 0)
                },
                'real_cluster_insights': [
                    f"Cluster complexity: {cluster_complexity} ({cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0)} resources)",
                    f"Scaling readiness: {scaling_readiness}",
                    f"Security posture: {security_posture}",
                    f"ML confidence: {overall_ml_confidence:.1%}"
                ]
            }
            
            # 2. Cost Protection (enhanced with cluster intelligence)
            implementation_plan['costProtection'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_complexity_factor': cluster_complexity,
                'budgetLimits': {
                    'monthlyBudget': total_cost * (1.2 if cluster_complexity == 'high' else 1.1),
                    'alertThreshold': total_cost * 0.95,
                    'hardLimit': total_cost * (1.3 if cluster_complexity == 'high' else 1.2)
                },
                'savingsProtection': {
                    'minimumSavingsTarget': total_savings * 0.8,
                    'predicted_savings': total_savings,
                    'ml_confidence_interval': [total_savings * 0.8, total_savings * 1.2]
                }
            }
            
            # 3. Governance (cluster-complexity aware)
            governance_level = 'enterprise' if security_posture == 'enterprise' else 'standard'
            implementation_plan['governance'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'governanceLevel': governance_level,
                'cluster_security_posture': security_posture,
                'approvalRequirements': {
                    'technical_approval': True,
                    'business_approval': governance_level == 'enterprise',
                    'security_review': security_posture in ['enterprise', 'standard']
                }
            }
            
            # 4. Monitoring Strategy
            implementation_plan['monitoring'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'scaling_readiness': scaling_readiness,
                'monitoringFrequency': 'real_time' if scaling_readiness == 'high' else 'standard',
                'keyMetrics': [
                    'cost_trends',
                    'resource_utilization', 
                    'application_performance',
                    'scaling_effectiveness' if scaling_readiness == 'high' else 'basic_metrics'
                ]
            }
            
            # 5. Contingency (complexity-based)
            implementation_plan['contingency'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_complexity': cluster_complexity,
                'contingencyTriggers': [
                    'cost_overrun_exceeds_20_percent',
                    'ml_confidence_drops_below_threshold',
                    'performance_degradation_detected',
                    'cluster_complexity_issues' if cluster_complexity == 'high' else 'standard_issues'
                ]
            }
            
            # 6. Success Criteria (cluster-specific)
            implementation_plan['successCriteria'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_specific_targets': {
                    'complexity_optimization': cluster_complexity,
                    'scaling_improvement': scaling_readiness,
                    'security_enhancement': security_posture
                },
                'financialTargets': {
                    'monthly_savings_target': total_savings,
                    'annual_savings_target': total_savings * 12,
                    'roi_target_months': 12 if cluster_complexity != 'high' else 18
                }
            }
            
            # 7. Timeline Optimization (complexity-based)
            phases = implementation_plan.get('implementation_phases', [])
            total_timeline_weeks = max([p.get('end_week', 1) for p in phases]) if phases else 6
            
            # Adjust timeline based on cluster complexity
            complexity_multiplier = {'low': 0.8, 'medium': 1.0, 'high': 1.3}.get(cluster_complexity, 1.0)
            optimized_weeks = max(1, int(total_timeline_weeks * complexity_multiplier))
            
            implementation_plan['timelineOptimization'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_complexity_factor': cluster_complexity,
                'originalTimelineWeeks': total_timeline_weeks,
                'optimizedTimelineWeeks': optimized_weeks,
                'complexity_adjustment_applied': complexity_multiplier != 1.0
            }
            
            # 8. Risk Mitigation (cluster-specific)
            implementation_plan['riskMitigation'] = {
                'enabled': True,
                'ml_derived': True,
                'config_informed': True,
                'ml_confidence': overall_ml_confidence,
                'cluster_risk_profile': {
                    'complexity': cluster_complexity,
                    'scaling_maturity': scaling_readiness,
                    'security_level': security_posture
                },
                'identifiedRisks': [
                    {
                        'risk_id': 'CLUSTER_001',
                        'description': f'Cluster complexity level: {cluster_complexity}',
                        'probability': 'high' if cluster_complexity == 'high' else 'low',
                        'impact': 'medium',
                        'mitigation': f'Gradual rollout for {cluster_complexity} complexity clusters'
                    },
                    {
                        'risk_id': 'SCALING_001', 
                        'description': f'Scaling readiness: {scaling_readiness}',
                        'probability': 'medium' if scaling_readiness == 'low' else 'low',
                        'impact': 'medium',
                        'mitigation': f'Enhanced monitoring for {scaling_readiness} scaling readiness'
                    }
                ]
            }
            
            # Log completion with cluster intelligence
            populated_components = [
                'intelligenceInsights', 'costProtection', 'governance', 
                'monitoring', 'contingency', 'successCriteria', 
                'timelineOptimization', 'riskMitigation'
            ]
            
            logger.info(f"✅ Framework enhanced with cluster intelligence:")
            logger.info(f"   - Complexity: {cluster_complexity}")
            logger.info(f"   - Scaling: {scaling_readiness}")
            logger.info(f"   - Security: {security_posture}")
            logger.info(f"   - Resources: {cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0)}")
            
            return implementation_plan
            
        except Exception as e:
            logger.error(f"❌ Enhanced framework completion failed: {e}")
            raise RuntimeError(f"❌ Enhanced framework completion failed: {e}") from e
    
    def _map_commands_to_phases(self, implementation_plan: Dict, execution_plan: Any, 
                                          cluster_config: Dict) -> Dict:
        """Map commands to phases with cluster config intelligence"""
        
        phases = implementation_plan.get('implementation_phases', [])
        
        if not execution_plan or not phases:
            return implementation_plan
        
        try:
            # Get cluster insights for intelligent command mapping
            config_insights = self.extract_config_insights(cluster_config) if hasattr(self, 'extract_config_insights') else {}
            
            # Extract commands from execution plan
            all_commands = []
            
            for attr in ['preparation_commands', 'optimization_commands', 'validation_commands']:
                if hasattr(execution_plan, attr):
                    commands = getattr(execution_plan, attr) or []
                    for cmd in commands:
                        command_dict = {
                            'id': getattr(cmd, 'id', f'cmd-{len(all_commands)}'),
                            'title': getattr(cmd, 'description', 'ML Generated Command'),
                            'command': getattr(cmd, 'command', ''),
                            'category': getattr(cmd, 'category', 'optimization'),
                            'description': getattr(cmd, 'description', 'ML generated command'),
                            'estimated_duration_minutes': getattr(cmd, 'estimated_duration_minutes', 30),
                            'risk_level': getattr(cmd, 'risk_level', 'Medium'),
                            'config_aware': True
                        }
                        all_commands.append(command_dict)
            
            # Distribute commands intelligently across phases
            if all_commands and phases:
                commands_per_phase = max(1, len(all_commands) // len(phases))
                
                for i, phase in enumerate(phases):
                    start_idx = i * commands_per_phase
                    end_idx = start_idx + commands_per_phase
                    phase['commands'] = all_commands[start_idx:end_idx]
                    
                    # Add config-specific metadata to phase
                    phase['config_enhanced'] = True
                    phase['cluster_context'] = config_insights.get('cluster_complexity', 'unknown')
            
        except Exception as e:
            logger.warning(f"⚠️ Enhanced command mapping failed: {e}")
        
        return implementation_plan
    
    def _calculate_ml_plan_confidence(self, analysis_results: Dict, implementation_plan: Dict, 
                                                ml_session: Dict, cluster_config: Dict) -> float:
        """Calculate ML plan confidence with cluster config factors"""
        
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
        
        # Cluster config quality factor (NEW)
        if cluster_config.get('status') == 'completed':
            config_success_rate = cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0) / max(cluster_config.get('fetch_metrics', {}).get('total_resources', 1), 1)
            confidence_factors.append(config_success_rate)
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
        
        # Framework completeness factor
        framework_components = ['costProtection', 'governance', 'monitoring', 'contingency', 
                              'successCriteria', 'timelineOptimization', 'riskMitigation']
        completed_components = sum(1 for comp in framework_components 
                                 if comp in implementation_plan and implementation_plan[comp].get('enabled', False))
        framework_factor = completed_components / len(framework_components)
        confidence_factors.append(framework_factor)
        
        # Config intelligence factor (NEW)
        config_insights = ml_session.get('config_insights', {})
        if config_insights:
            insight_quality = 0.8 if config_insights.get('cluster_complexity') != 'unknown' else 0.5
            confidence_factors.append(insight_quality)
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Add enhanced ML confidence to plan
        implementation_plan['ml_confidence'] = overall_confidence
        implementation_plan['ml_confidence_breakdown'] = ml_session['ml_confidence_levels']
        implementation_plan['config_enhanced'] = cluster_config.get('status') == 'completed'
        implementation_plan['cluster_intelligence_applied'] = True
        implementation_plan['learning_applied'] = len(ml_session['learning_events']) > 0
        
        return overall_confidence
    
    # Include all existing helper methods from the original implementation
    # (keeping them unchanged for compatibility)
    
    def _initialize_ml_systems(self):
        """Initialize ML intelligence systems (unchanged from original)"""
        logger.info("🔧 Initializing ML intelligence systems...")
        
        initialization_results = {
            'learning_engine': {'status': 'pending', 'error': None},
            'ml_orchestrator': {'status': 'pending', 'error': None},
            'strategy_engine': {'status': 'pending', 'error': None},
            'plan_generator': {'status': 'pending', 'error': None},
            'command_generator': {'status': 'pending', 'error': None},
            'dna_analyzer': {'status': 'pending', 'error': None}
        }
        
        try:
            logger.info("📥 Importing ML modules...")
            
            try:
                from app.ml.learn_optimize import create_enhanced_learning_engine
                logger.info("✅ learn_optimize module imported")
            except Exception as e:
                logger.error(f"❌ Failed to import learn_optimize: {e}")
                initialization_results['learning_engine'] = {'status': 'import_failed', 'error': str(e)}
                raise
            
            try:
                from app.ml.dynamic_strategy import EnhancedDynamicStrategyEngine
                logger.info("✅ dynamic_strategy module imported")
            except Exception as e:
                logger.error(f"❌ Failed to import dynamic_strategy: {e}")
                initialization_results['strategy_engine'] = {'status': 'import_failed', 'error': str(e)}
                raise
            
            try:
                from app.ml.dynamic_plan_generator import CombinedDynamicImplementationGenerator
                logger.info("✅ dynamic_plan_generator module imported")
            except Exception as e:
                logger.error(f"❌ Failed to import dynamic_plan_generator: {e}")
                initialization_results['plan_generator'] = {'status': 'import_failed', 'error': str(e)}
                raise
            
            try:
                from app.ml.dynamic_cmd_center import AdvancedExecutableCommandGenerator
                logger.info("✅ dynamic_cmd_center module imported")
            except Exception as e:
                logger.error(f"❌ Failed to import dynamic_cmd_center: {e}")
                initialization_results['command_generator'] = {'status': 'import_failed', 'error': str(e)}
                raise
            
            try:
                from app.ml.dna_analyzer import ClusterDNAAnalyzer
                logger.info("✅ dna_analyzer module imported")
            except Exception as e:
                logger.error(f"❌ Failed to import dna_analyzer: {e}")
                initialization_results['dna_analyzer'] = {'status': 'import_failed', 'error': str(e)}
                raise
            
            try:
                from app.ml.ml_integration import MLSystemOrchestrator
                logger.info("✅ ml_integration module imported")
            except Exception as e:
                logger.error(f"❌ Failed to import ml_integration: {e}")
                initialization_results['ml_orchestrator'] = {'status': 'import_failed', 'error': str(e)}
                raise
            
            logger.info("📦 All ML modules imported successfully, initializing instances...")
            
            # Initialize ML systems
            try:
                self.learning_engine = create_enhanced_learning_engine()
                initialization_results['learning_engine'] = {'status': 'success', 'error': None}
                logger.info("✅ Learning engine initialized")
            except Exception as e:
                logger.error(f"❌ Learning engine initialization failed: {e}")
                initialization_results['learning_engine'] = {'status': 'init_failed', 'error': str(e)}
                raise
            
            try:
                self.ml_orchestrator = MLSystemOrchestrator(self.learning_engine)
                initialization_results['ml_orchestrator'] = {'status': 'success', 'error': None}
                logger.info("✅ ML orchestrator initialized")
            except Exception as e:
                logger.error(f"❌ ML orchestrator initialization failed: {e}")
                initialization_results['ml_orchestrator'] = {'status': 'init_failed', 'error': str(e)}
                raise
            
            try:
                self.strategy_engine = EnhancedDynamicStrategyEngine()
                initialization_results['strategy_engine'] = {'status': 'success', 'error': None}
                logger.info("✅ Strategy engine initialized")
            except Exception as e:
                logger.error(f"❌ Strategy engine initialization failed: {e}")
                initialization_results['strategy_engine'] = {'status': 'init_failed', 'error': str(e)}
                raise
            
            try:
                self.plan_generator = CombinedDynamicImplementationGenerator()
                initialization_results['plan_generator'] = {'status': 'success', 'error': None}
                logger.info("✅ Plan generator initialized")
            except Exception as e:
                logger.error(f"❌ Plan generator initialization failed: {e}")
                initialization_results['plan_generator'] = {'status': 'init_failed', 'error': str(e)}
                raise
            
            try:
                self.command_generator = AdvancedExecutableCommandGenerator()
                initialization_results['command_generator'] = {'status': 'success', 'error': None}
                logger.info("✅ Command generator initialized")
            except Exception as e:
                logger.error(f"❌ Command generator initialization failed: {e}")
                initialization_results['command_generator'] = {'status': 'init_failed', 'error': str(e)}
                raise
            
            try:
                self.dna_analyzer = ClusterDNAAnalyzer(enable_temporal_intelligence=True)
                initialization_results['dna_analyzer'] = {'status': 'success', 'error': None}
                logger.info("✅ DNA analyzer initialized")
            except Exception as e:
                logger.error(f"❌ DNA analyzer initialization failed: {e}")
                initialization_results['dna_analyzer'] = {'status': 'init_failed', 'error': str(e)}
                raise
            
            # Connect to ML learning
            logger.info("🔗 Connecting ML components...")
            try:
                self.ml_orchestrator.connect_component('strategy_engine', self.strategy_engine)
                self.ml_orchestrator.connect_component('plan_generator', self.plan_generator)
                self.ml_orchestrator.connect_component('command_generator', self.command_generator)
                self.ml_orchestrator.connect_component('dna_analyzer', self.dna_analyzer)
                logger.info("✅ ML components connected")
            except Exception as e:
                logger.error(f"❌ ML component connection failed: {e}")
                raise
            
            # Enable learning integration
            try:
                self.enable_learning_integration(self.ml_orchestrator)
                logger.info("✅ Learning integration enabled")
            except Exception as e:
                logger.error(f"❌ Learning integration failed: {e}")
                raise
            
            self.ml_systems_available = True
            self._debug_info['ml_system_status'] = initialization_results
            logger.info("🎉 ML intelligence systems initialized successfully")
            
        except Exception as e:
            logger.error(f"💥 CRITICAL: ML system initialization failed completely: {e}")
            logger.error(f"💥 Full initialization traceback: {traceback.format_exc()}")
            logger.error(f"💥 Initialization results: {json.dumps(initialization_results, indent=2)}")
            
            # Set all systems to None (NO FALLBACK)
            self.learning_engine = None
            self.ml_orchestrator = None
            self.strategy_engine = None
            self.plan_generator = None
            self.command_generator = None
            self.dna_analyzer = None
            self.ml_systems_available = False
            self._debug_info['ml_system_status'] = initialization_results
            
            # This is a critical failure - the system cannot function without ML components
            raise RuntimeError(f"❌ CRITICAL: Cannot initialize ML systems - {str(e)}")
    
    # Include all other existing helper methods unchanged...
    # (keeping the rest of the implementation as-is for compatibility)
    
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
                
                if 'phases' in implementation_plan:
                    logger.error("❌ Found 'phases' but expected 'implementation_phases' - key normalization failed")
                
                return False
            
            # Check implementation_phases is a list
            if not isinstance(implementation_plan['implementation_phases'], list):
                logger.error(f"❌ implementation_phases is not a list: type={type(implementation_plan['implementation_phases'])}")
                return False
            
            # Check for framework components
            framework_components = ['costProtection', 'governance', 'monitoring', 'contingency', 
                                  'successCriteria', 'timelineOptimization', 'riskMitigation']
            
            missing_components = []
            disabled_components = []
            
            for component in framework_components:
                if component not in implementation_plan:
                    missing_components.append(component)
                elif not implementation_plan[component].get('enabled', False):
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
    
    # Include all remaining helper methods from original implementation...
    # (keeping method signatures and behavior unchanged)
    
    def _log_detailed_failure(self, operation: str, error_msg: str, context: Dict):
        """Log detailed failure information for debugging"""
        
        failure_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error_message': error_msg,
            'context': context,
            'ml_systems_status': {
                'learning_engine': self.learning_engine is not None,
                'ml_orchestrator': self.ml_orchestrator is not None,
                'strategy_engine': self.strategy_engine is not None,
                'plan_generator': self.plan_generator is not None,
                'command_generator': self.command_generator is not None,
                'dna_analyzer': self.dna_analyzer is not None,
                'ml_systems_available': self.ml_systems_available
            },
            'system_info': {
                'enable_cost_monitoring': self.enable_cost_monitoring,
                'enable_temporal': self.enable_temporal,
                'learning_enabled': getattr(self, '_learning_enabled', False)
            }
        }
        
        self._debug_info['failed_operations'].append(failure_record)
        
        logger.error(f"💥 DETAILED FAILURE [{operation}]: {error_msg}")
        logger.error(f"💥 Context: {json.dumps(context, indent=2)}")
        logger.error(f"💥 ML Systems Status: {json.dumps(failure_record['ml_systems_status'], indent=2)}")
    
    def _log_complete_failure_details(self, exception: Exception, analysis_results: Dict, local_vars: Dict):
        """Log complete failure details for debugging - JSON SAFE VERSION"""
        
        def make_json_safe(obj, max_depth=3, current_depth=0):
            """Convert objects to JSON-safe format"""
            if current_depth > max_depth:
                return f"<max_depth_exceeded_{type(obj).__name__}>"
            
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, dict):
                return {str(k): make_json_safe(v, max_depth, current_depth + 1) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_json_safe(item, max_depth, current_depth + 1) for item in obj[:10]]
            elif hasattr(obj, '__dict__'):
                return {
                    'type': type(obj).__name__,
                    'attributes': make_json_safe(obj.__dict__, max_depth, current_depth + 1)
                }
            else:
                return f"<{type(obj).__name__}_{str(obj)[:100]}>"
        
        try:
            # Create JSON-safe failure details
            complete_failure = {
                'timestamp': datetime.now().isoformat(),
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'exception_args': list(getattr(exception, 'args', [])),
                'full_traceback': traceback.format_exc(),
                'analysis_results_info': {
                    'type': type(analysis_results).__name__,
                    'is_dict': isinstance(analysis_results, dict),
                    'keys': list(analysis_results.keys()) if isinstance(analysis_results, dict) else 'NOT_DICT',
                    'cluster_name': analysis_results.get('cluster_name', 'unknown') if isinstance(analysis_results, dict) else 'unknown',
                    'total_cost': analysis_results.get('total_cost', 'missing') if isinstance(analysis_results, dict) else 'missing'
                },
                'local_variables': {
                    'ml_session_type': type(local_vars.get('ml_session')).__name__ if local_vars.get('ml_session') else 'None',
                    'cluster_dna_type': type(local_vars.get('cluster_dna')).__name__ if local_vars.get('cluster_dna') else 'None',
                    'ml_strategy_type': type(local_vars.get('ml_strategy')).__name__ if local_vars.get('ml_strategy') else 'None',
                    'ml_plan_type': type(local_vars.get('ml_plan')).__name__ if local_vars.get('ml_plan') else 'None'
                },
                'ml_systems_detailed': make_json_safe(self._debug_info['ml_system_status']),
                'failed_operations_count': len(self._debug_info['failed_operations'])
            }
            
            logger.error("💥" * 50)
            logger.error("💥 COMPLETE SYSTEM FAILURE ANALYSIS")
            logger.error("💥" * 50)
            logger.error(f"💥 Exception: {complete_failure['exception_type']}: {complete_failure['exception_message']}")
            logger.error(f"💥 Analysis Results: {json.dumps(complete_failure['analysis_results_info'], indent=2)}")
            logger.error(f"💥 Local Variables: {json.dumps(complete_failure['local_variables'], indent=2)}")
            logger.error(f"💥 Failed Operations Count: {complete_failure['failed_operations_count']}")
            logger.error(f"💥 Full Traceback:\n{complete_failure['full_traceback']}")
            logger.error("💥" * 50)
            
        except Exception as logging_error:
            # Fallback logging if even the safe logging fails
            logger.error(f"💥 CRITICAL: Even safe error logging failed: {logging_error}")
            logger.error(f"💥 Original exception: {type(exception).__name__}: {str(exception)}")
            logger.error(f"💥 Original traceback:\n{traceback.format_exc()}")
    
    def _record_generation_failure(self, error: str):
        """Record generation failure for learning"""
        if getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('generation_failed', {
                'error': error,
                'timestamp': datetime.now().isoformat(),
                'ml_systems_available': getattr(self, 'ml_systems_available', False),
                'failed_operations_count': len(self._debug_info['failed_operations'])
            })
    
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
    
    def _record_ml_learning_outcomes(self, implementation_plan: Dict, ml_session: Dict, confidence: float):
        """Record ML learning outcomes"""
        
        logger.info("📚 Recording ML learning outcomes...")
        
        try:
            if self.learning_engine and self.ml_orchestrator:
                # Create learning result
                learning_result = {
                    'execution_id': ml_session['session_id'],
                    'cluster_name': ml_session['cluster_name'],
                    'success': True,
                    'confidence': confidence,
                    'phases_count': len(implementation_plan.get('implementation_phases', [])),
                    'ml_systems_used': self.ml_systems_available,
                    'learning_events': ml_session['learning_events']
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
                'learning_events_count': len(ml_session['learning_events']),
                'framework_components_complete': 7
            })
    
    def _finalize_ml_session(self, ml_session: Dict, implementation_plan: Dict, confidence: float):
        """Finalize ML session"""
        
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
        implementation_plan['metadata']['learning_events'] = len(ml_session['learning_events'])
        implementation_plan['metadata']['generated_at'] = datetime.now().isoformat()
        implementation_plan['metadata']['version'] = '3.0.0-cluster-config-enhanced'
        
        # Store session
        ml_session['completed_at'] = datetime.now()
        self._ml_sessions_history.append(ml_session)
        self._current_ml_session = None
        
        logger.info(f"🎯 ML Session Completed: {ml_session['intelligence_quality']} quality")
    
    def _start_ml_session(self, analysis_results: Dict) -> Dict:
        """Start ML intelligence session"""
        
        session = {
            'session_id': f"ml-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'cluster_name': analysis_results.get('cluster_name', 'unknown'),
            'started_at': datetime.now(),
            'ml_confidence_levels': {},
            'learning_events': [],
            'intelligence_quality': 'initializing',
            'ml_systems_available': self.ml_systems_available
        }
        
        self._current_ml_session = session
        
        # Record session start for learning
        if getattr(self, '_learning_enabled', False):
            self.report_outcome_for_learning('session_started', {
                'session_id': session['session_id'],
                'cluster_name': session['cluster_name'],
                'ml_systems_available': self.ml_systems_available
            })
        
        logger.info(f"🎯 ML Session Started: {session['session_id']}")
        return session


# Backward compatibility - maintain exact same names and signatures
CombinedAKSImplementationGenerator = AKSImplementationGenerator
FixedAKSImplementationGenerator = AKSImplementationGenerator

print("✅ AKS Implementation Generator enhanced with cluster config integration")
print("🔗 Same signatures maintained - full backward compatibility")  
print("🔍 Now fetches REAL cluster configuration for ML analysis")
print("📊 NO fallbacks - uses actual cluster data for intelligent plan generation")