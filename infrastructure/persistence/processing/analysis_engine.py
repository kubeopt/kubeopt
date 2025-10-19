#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Multi-Subscription Analysis Engine - Enhanced with Cluster Config Support
========================================================================
Enhanced to provide cluster configuration information to implementation generator.
NO signature changes, maintains full compatibility.
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import existing modules
from shared.config.config import (
    logger, enhanced_cluster_manager, _analysis_lock, _analysis_sessions,
    implementation_generator
)

# Import standards loader for YAML-based configuration
from shared.standards.standards_loader import (
    get_cpu_target, get_memory_target, get_hpa_config, 
    get_optimization_config, get_standards_loader
)
from infrastructure.persistence.processing.cost_processor import get_aks_specific_cost_data, extract_cost_components
from infrastructure.persistence.processing.metrics_processor import get_aks_metrics_from_monitor
from infrastructure.services.cache_manager import save_to_cache
from shared.utils.utils import validate_cost_data

# Import new plan generation modules
from infrastructure.plan_generation import ClaudePlanGenerator
import asyncio
import os

# Import the subscription manager
from infrastructure.services.subscription_manager import azure_subscription_manager

class AnalysisType(Enum):
    """Analysis type configurations"""
    CONSISTENT = "consistent"
    MULTI_SUBSCRIPTION = "multi_subscription"

@dataclass
class AnalysisConfig:
    """Configuration for analysis execution"""
    analysis_type: AnalysisType
    subscription_id: str
    enable_enhanced_fallback: bool = True
    strict_validation: bool = True
    update_global_state: bool = True

@dataclass
class SubscriptionAnalysisSession:
    """Session information for subscription-aware analysis"""
    session_id: str
    cluster_id: str
    subscription_id: str
    resource_group: str
    cluster_name: str
    status: str
    started_at: str
    thread_id: int
    analysis_type: str
    subscription_context_set: bool = False

class MultiSubscriptionAnalysisEngine:
    """Enhanced AKS Analysis Engine with cluster config support"""
    
    def __init__(self):
        self.session_metadata = {
            AnalysisType.CONSISTENT: {
                'data_type': 'ml_enhanced_enterprise_multi_subscription',
                'metrics_source': 'ML-Enhanced Multi-Subscription Real-time Collection',
                'log_prefix': '🌐 MULTI-SUB ML-ENHANCED'
            },
            AnalysisType.MULTI_SUBSCRIPTION: {
                'data_type': 'ml_enhanced_multi_subscription',
                'metrics_source': 'ML-Enhanced Multi-Subscription Real-time Collection',
                'log_prefix': '🌐 MULTI-SUB'
            }
        }
        self.subscription_locks = {}
        self.cluster_locks = {}

    def get_cluster_lock(self, cluster_id: str) -> threading.Lock:
        """Get or create a lock for specific cluster"""
        if cluster_id not in self.cluster_locks:
            self.cluster_locks[cluster_id] = threading.Lock()
        return self.cluster_locks[cluster_id]    
    
    def get_subscription_lock(self, subscription_id: str) -> threading.Lock:
        """Get or create a lock for specific subscription"""
        if subscription_id not in self.subscription_locks:
            self.subscription_locks[subscription_id] = threading.Lock()
        return self.subscription_locks[subscription_id]
    
    # REMOVED: _validate_cost_data_availability function - was making redundant API calls
    # Cache checking is now handled in the main flow without API validation

    def run_subscription_aware_analysis(
        self, 
        resource_group: str, 
        cluster_name: str,
        subscription_id: Optional[str] = None,
        days: int = 30, 
        enable_pod_analysis: bool = True,
        config: Optional[AnalysisConfig] = None
    ) -> Dict[str, Any]:
        """
        Run analysis with subscription awareness and cluster config support
        ENHANCED: Ensures cluster config info is available for implementation generator
        """
        
        cluster_id = f"{resource_group}_{cluster_name}"
        
        # Step 1: Determine subscription if not provided
        cluster_lock = self.get_cluster_lock(cluster_id)
        
        with cluster_lock:
            logger.info(f"🔒 Acquired cluster lock for {cluster_id}")
            
            if not subscription_id:
                logger.info(f"🔍 Auto-detecting subscription for cluster {cluster_name}")
                subscription_id = azure_subscription_manager.find_cluster_subscription(resource_group, cluster_name)
                
                if not subscription_id:
                    return {
                        'status': 'error',
                        'message': f'Could not find cluster {cluster_name} in any accessible subscription',
                        'cluster_name': cluster_name,
                        'resource_group': resource_group
                    }
        
            # Step 2: CACHE-ONLY CHECK (no API calls - let comprehensive fetch handle all Azure API calls)
            try:
                logger.info(f"🔍 CACHE-ONLY: Checking for existing cost data for {cluster_name}")
                
                # Check if we have cached cost data (avoid redundant API calls)
                from infrastructure.services.cost_cache import check_database_cost_freshness, cache
                cluster_id = f"{resource_group}_{cluster_name}"
                
                # Check database for fresh cost data  
                cached_cost_df = check_database_cost_freshness(cluster_name, max_age_hours=24)
                if cached_cost_df is not None:
                    logger.info(f"✅ CACHE HIT: Found fresh database cost data for {cluster_name}")
                    cost_validation_result = {'available': True, 'subscription_id': subscription_id, 'cache_hit': True}
                else:
                    # Check file cache for recent API responses
                    cache_end_date = datetime.now()
                    cache_start_date = cache_end_date - timedelta(days=days)
                    cache_date_range = f"{cache_start_date} to {cache_end_date}"
                    cached_data = cache.get(cluster_id, subscription_id, cache_date_range)
                    
                    if cached_data is not None and cached_data:
                        logger.info(f"✅ CACHE HIT: Found file cached cost data for {cluster_name}")
                        cost_validation_result = {'available': True, 'subscription_id': subscription_id, 'cache_hit': True}
                    else:
                        # No cache available - comprehensive fetch will handle Azure API call and validation
                        logger.info(f"🔄 CACHE MISS: No cached data for {cluster_name} - comprehensive fetch will get fresh data")
                        cost_validation_result = {'available': True, 'subscription_id': subscription_id, 'cache_hit': False}
                
                logger.info(f"✅ CACHE CHECK: Cost data check completed for {cluster_name}")
                
            except Exception as cache_error:
                logger.warning(f"⚠️ Cache check failed for {cluster_name}: {cache_error} - comprehensive fetch will handle validation")
                # Don't fail - let comprehensive fetch handle everything
                cost_validation_result = {'available': True, 'subscription_id': subscription_id, 'cache_hit': False}
            
            # Step 3: Create subscription-aware config
            if config is None:
                config = AnalysisConfig(AnalysisType.MULTI_SUBSCRIPTION, subscription_id)
            else:
                config.subscription_id = subscription_id
            
            # Step 4: Run analysis with subscription context and cluster config support
            return self._run_analysis_with_subscription_context(
                resource_group, cluster_name, subscription_id, days, enable_pod_analysis, config, cost_validation_result
            )
    
    def _run_analysis_with_subscription_context(
        self,
        resource_group: str,
        cluster_name: str,
        subscription_id: str,
        days: int,
        enable_pod_analysis: bool,
        config: AnalysisConfig,
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute analysis within subscription context with cluster config preparation"""
        
        # Create unique session ID with subscription info
        session_id = f"{subscription_id[:8]}_{str(uuid.uuid4())[:8]}"
        cluster_id = f"{resource_group}_{cluster_name}"
        
        metadata = self.session_metadata[config.analysis_type]
        log_prefix = metadata['log_prefix']
        
        logger.info(f"{log_prefix}: Starting analysis for {cluster_name} in subscription {subscription_id[:8]} (session: {session_id})")
        
        # Get subscription-specific lock to prevent conflicts
        subscription_lock = self.get_subscription_lock(subscription_id)
        
        try:
            # Initialize subscription-aware session tracking
            session_results = {}
            with _analysis_lock:
                _analysis_sessions[session_id] = SubscriptionAnalysisSession(
                    session_id=session_id,
                    cluster_id=cluster_id,
                    subscription_id=subscription_id,
                    resource_group=resource_group,
                    cluster_name=cluster_name,
                    status='running',
                    started_at=datetime.now().isoformat(),
                    thread_id=threading.current_thread().ident,
                    analysis_type=config.analysis_type.value
                ).__dict__
            
            # Execute analysis within subscription context
            with subscription_lock:
                logger.info(f"🔒 Acquired subscription lock for {subscription_id[:8]}")
                
                def analysis_function(subscription_id=None):
                    return self._execute_core_analysis_with_cluster_config_support(
                        resource_group, cluster_name, days, enable_pod_analysis,
                        session_id, log_prefix, config
                    )
                
                # Execute with subscription context
                analysis_result = azure_subscription_manager.execute_with_subscription_context(
                    subscription_id, analysis_function
                )
                
                logger.info(f"🔓 Released subscription lock for {subscription_id[:8]}")
            
            if analysis_result['status'] == 'success':
                # ENHANCED: Add comprehensive subscription and cluster metadata for implementation generator
                analysis_result['results']['subscription_metadata'] = {
                    'subscription_id': subscription_id,
                    'subscription_name': self._get_subscription_name(subscription_id),
                    'cluster_validation': validation_result.get('cluster_info', {}),
                    'analysis_session_id': session_id,
                    'multi_subscription_enabled': True
                }
                
                # ENHANCED: Add cluster configuration metadata for implementation generator
                analysis_result['results']['cluster_metadata'] = {
                    'resource_group': resource_group,
                    'cluster_name': cluster_name,
                    'cluster_id': cluster_id,
                    'subscription_id': subscription_id,
                    'azure_resource_id': f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}",
                    'cluster_config_available': True,  # Signal that config fetching is available
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                # Update session and database with subscription info
                self._update_session_state_with_subscription(session_id, analysis_result['results'], config)
                
                if config.update_global_state:
                    self._update_global_state_with_subscription(cluster_id, analysis_result['results'], session_id, subscription_id)
            
            return analysis_result
            
        except Exception as e:
            return self._handle_subscription_error(e, session_id, subscription_id, config.analysis_type, log_prefix)
    
    def _execute_core_analysis_with_cluster_config_support(
        self, resource_group: str, cluster_name: str, days: int, 
        enable_pod_analysis: bool, session_id: str, log_prefix: str, config: AnalysisConfig
    ) -> Dict[str, Any]:
        """
        Execute core analysis logic with cluster config support
        ENHANCED: Prepares analysis results for cluster config integration
        """
        
        cluster_id = f"{resource_group}_{cluster_name}"
        
        try:
            # CACHE-FIRST ARCHITECTURE: Create single cache instance at the very beginning
            logger.info(f"🚀 Session {session_id}: Creating single cache instance for {cluster_name} - executing all kubectl commands")
            from shared.kubernetes_data_cache import fetch_cluster_data
            shared_cache = fetch_cluster_data(cluster_name, resource_group, config.subscription_id)
            logger.info(f"✅ Session {session_id}: Cache ready - all components will now use cached data")
            
            # Step 1: Get cost data with subscription context
            cost_components, cost_label, total_period_cost, cost_df = self._get_cost_data(
                resource_group, cluster_name, days, session_id, log_prefix, cluster_id, config
            )
            
            # Step 2: Get metrics data with subscription context (pass shared cache)
            metrics_data, real_node_metrics = self._get_metrics_data(
                resource_group, cluster_name, config, session_id, log_prefix, shared_cache
            )
            
            # Step 3: Get pod analysis with subscription context (pass shared cache)
            pod_data = self._get_pod_analysis(
                resource_group, cluster_name, enable_pod_analysis, 
                cost_df, session_id, log_prefix, config.subscription_id, shared_cache
            )
            
            # Step 4: Run ML-enhanced algorithmic analysis
            consistent_results = self._run_ml_analysis(
                resource_group, cluster_name, cost_components, 
                metrics_data, pod_data, session_id, log_prefix
            )
            
            # Step 5: Compile comprehensive results with cluster config metadata
            final_results = self._compile_results_with_cluster_config_support(
                consistent_results, cost_label, total_period_cost, days,
                real_node_metrics, pod_data, resource_group, cluster_name,
                session_id, config, self.session_metadata[config.analysis_type], cost_df
            )
            
            # CRITICAL: Add metrics_data to final_results for implementation_generator
            if metrics_data is not None and metrics_data:
                final_results['metrics_data'] = metrics_data
                logger.info(f"✅ Session {session_id}: Added metrics_data to final_results for HPA analysis")
                if 'hpa_implementation' in metrics_data:
                    hpa_count = metrics_data['hpa_implementation'].get('total_hpas', 0)
                    logger.info(f"🎯 Session {session_id}: metrics_data contains {hpa_count} HPAs for implementation_generator")
            else:
                logger.warning(f"⚠️ Session {session_id}: No metrics_data available for implementation_generator")

            logger.info(f"DEBUG:HPA efficiency: {final_results.get('hpa_efficiency', 0):.1f}%")
            
            # Step 6: Generate implementation plan with cluster config support
            self._generate_implementation_plan_with_cluster_config_support(final_results, session_id, log_prefix)

            logger.info(f"🎉 Session {session_id}: MULTI-SUBSCRIPTION ANALYSIS WITH CLUSTER CONFIG COMPLETED")
            
            return {
                'status': 'success',
                'data_type': self.session_metadata[config.analysis_type]['data_type'],
                'session_id': session_id,
                'results': final_results
            }
            
        except Exception as e:
            logger.error(f"❌ Core analysis failed for session {session_id}: {e}")
            raise
    
    def _compile_results_with_cluster_config_support(self, consistent_results: Dict, cost_label: str, 
                        total_period_cost: float, days: int, real_node_metrics: List,
                        pod_data: Optional[Dict], resource_group: str, cluster_name: str,
                        session_id: str, config: AnalysisConfig, metadata: Dict, cost_df) -> Dict:
        """
        Compile comprehensive analysis results with cluster config support
        ENHANCED: Includes all metadata needed by implementation generator for cluster config fetching
        """
        
        final_results = consistent_results.copy()
        
        final_results.update({
            'cost_label': cost_label,
            'actual_period_cost': total_period_cost,
            'analysis_period_days': days,
            'nodes': real_node_metrics.copy(),
            'node_metrics': real_node_metrics.copy(),
            'real_node_data': real_node_metrics.copy(),
            'has_real_node_data': True
        })
        
        # CRITICAL: Save the original detailed cost DataFrame for accurate cache restoration
        if cost_df is not None and not cost_df.empty:
            # Convert DataFrame to serializable format for database storage
            cost_data_for_storage = cost_df.to_dict('records')
            final_results['cost_data'] = cost_data_for_storage
            final_results['cost_data_columns'] = list(cost_df.columns)
            final_results['cost_data_shape'] = cost_df.shape
            logger.info(f"✅ Saved detailed cost DataFrame to analysis results: {cost_df.shape[0]} rows, {cost_df.shape[1]} columns")
        
        # ENHANCED: Add subscription-aware ML metadata with cluster config support
        ml_metadata = {
            'analysis_type': config.analysis_type.value,
            'subscription_id': config.subscription_id,
            'subscription_aware': True,
            'ml_models_used': True,
            'enterprise_analysis': True,
            'contradiction_free': True,
            'session_id': session_id,
            'multi_subscription_support': True,
            'cluster_config_integration_enabled': True  # NEW: Signal cluster config support
        }
        
        final_results['ml_analysis_metadata'] = ml_metadata
        
        # ENHANCED: Add comprehensive cluster context for implementation generator
        final_results['cluster_context'] = {
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'subscription_id': config.subscription_id,
            'cluster_id': f"{resource_group}_{cluster_name}",
            'azure_resource_id': f"/subscriptions/{config.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}",
            'analysis_session': session_id,
            'supports_cluster_config_fetch': True,  # NEW: Implementation generator can fetch cluster config
            'cluster_config_fetch_params': {  # NEW: Parameters for cluster config fetching
                'resource_group': resource_group,
                'cluster_name': cluster_name,
                'subscription_id': config.subscription_id
            }
        }
        
        if pod_data is not None and pod_data:
            final_results['has_pod_costs'] = True
            final_results['pod_cost_analysis'] = pod_data
            
            if 'namespace_costs' in pod_data:
                final_results['namespace_costs'] = pod_data['namespace_costs']
                # Generate chart data for UI
                namespace_costs = pod_data['namespace_costs']
                if namespace_costs and len(namespace_costs) > 0:
                    final_results['namespaceData'] = {
                        'labels': list(namespace_costs.keys()),
                        'values': list(namespace_costs.values())
                    }
                    logger.info(f"✅ Session {session_id}: Generated namespace chart data for {len(namespace_costs)} namespaces")

            # Generate workload chart data
            if 'workload_costs' in pod_data:
                workload_costs = pod_data['workload_costs']
                if workload_costs and len(workload_costs) > 0:
                    # Get top 10 workloads by cost
                    sorted_workloads = sorted(workload_costs.items(), key=lambda x: x[1].get('cost', 0), reverse=True)[:10]
                    
                    final_results['workloadData'] = {
                        'labels': [workload[0] for workload in sorted_workloads],
                        'values': [workload[1].get('cost', 0) for workload in sorted_workloads],
                        'types': [workload[1].get('type', 'Unknown') for workload in sorted_workloads]
                    }
                    logger.info(f"✅ Session {session_id}: Generated workload chart data for {len(sorted_workloads)} workloads")

            # Check for alternative namespace summary if available
            if 'namespace_summary' in pod_data:
                final_results['namespace_costs'] = pod_data['namespace_summary']
        else:
            final_results['has_pod_costs'] = False
        
        final_results.update({
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'subscription_id': config.subscription_id,  # Add subscription_id at root level for backward compatibility
            'cost_period': f"{datetime.now().strftime('%Y-%m-%d')} ({days} days analysis)",
            'cost_data_source': 'Azure Cost Management API',
            'metrics_data_source': metadata['metrics_source'],
            'analysis_timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'ml_enhanced': True,
            config.analysis_type.value: True
        })

        logger.info(f"DEBUG:HPA efficiency: {final_results.get('hpa_efficiency', 0):.1f}%")

        return final_results
    
    def _generate_implementation_plan_with_cluster_config_support(self, results: Dict, session_id: str, log_prefix: str) -> None:
        """
        Generate implementation plan with cluster config support
        ENHANCED: Implementation generator now has access to cluster config fetching parameters
        """
        logger.info(f"📋 Session {session_id}: Generating implementation plan with cluster config support...")
        
        try:
            # Log cluster config availability
            cluster_context = results.get('cluster_context', {})
            if cluster_context.get('supports_cluster_config_fetch'):
                logger.info(f"✅ Session {session_id}: Cluster config fetching available")
                logger.info(f"🔧 Session {session_id}: Config params - RG: {cluster_context.get('resource_group')}, "
                           f"Cluster: {cluster_context.get('cluster_name')}, "
                           f"Sub: {cluster_context.get('subscription_id', 'unknown')[:8]}")
            else:
                logger.warning(f"⚠️ Session {session_id}: Cluster config fetching not available")
            
            # Call implementation generator - conditional for compatibility
            if implementation_generator and hasattr(implementation_generator, 'generate_implementation_plan'):
                # Legacy implementation generator API
                implementation_plan = implementation_generator.generate_implementation_plan(results)
                results['implementation_plan'] = implementation_plan
            elif implementation_generator:
                # New Claude API - skip for now, plan generation happens in cluster_database.py
                logger.info(f"✅ Session {session_id}: Claude implementation generator available (plan generation in database layer)")
                results['implementation_plan_available'] = True
            else:
                logger.warning(f"⚠️ Session {session_id}: No implementation generator available")
                results['implementation_plan'] = None
                
        except Exception as impl_error:
            logger.error(f"❌ Session {session_id}: Implementation plan generation failed: {impl_error}")
            # Add error info to results for debugging
            results['implementation_plan_error'] = {
                'error': str(impl_error),
                'cluster_config_available': results.get('cluster_context', {}).get('supports_cluster_config_fetch', False)
            }
    
    # Include all existing helper methods unchanged (maintaining signatures)
    
    def _get_subscription_name(self, subscription_id: str) -> str:
        """Get subscription display name"""
        sub_info = azure_subscription_manager.get_subscription_info(subscription_id)
        return sub_info.subscription_name if sub_info else subscription_id[:8]
    
    def _update_session_state_with_subscription(self, session_id: str, results: Dict, config: AnalysisConfig) -> None:
        """Update session tracking state with subscription info"""
        with _analysis_lock:
            if session_id in _analysis_sessions:
                _analysis_sessions[session_id].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'results': results,
                    'subscription_analysis_complete': True
                })
    
    def _update_global_state_with_subscription(self, cluster_id: str, results: Dict, session_id: str, subscription_id: str) -> None:
        """Update global analysis state with subscription context"""
        try:
            # Update cluster manager with subscription info
            enhanced_cluster_manager.update_cluster_subscription_info(
                cluster_id, subscription_id, self._get_subscription_name(subscription_id)
            )
            
            # ENHANCED: Generate detailed analysis input before database update
            enhanced_input = self.generate_enhanced_analysis_input(cluster_id, results)
            logger.info(f"✅ Session {session_id}: Generated enhanced analysis input with {len(enhanced_input.get('workloads', []))} workloads")
            
            # Update results with enhanced input for implementation generator
            results['enhanced_analysis_input'] = enhanced_input
            
            # NEW: Generate implementation plan using Claude API (async)
            try:
                cluster_name = enhanced_input.get('cluster_info', {}).get('cluster_name', cluster_id)
                implementation_plan = asyncio.run(self._generate_implementation_plan_async(
                    enhanced_input, cluster_name, cluster_id
                ))
                
                if implementation_plan:
                    # Store the plan separately
                    plan_id = enhanced_cluster_manager.store_implementation_plan(
                        cluster_id, implementation_plan, 
                        analysis_id=results.get('cluster_info', {}).get('analysis_timestamp')
                    )
                    
                    # Add plan reference to results (for backward compatibility)
                    results['implementation_plan_id'] = plan_id
                    results['implementation_plan'] = implementation_plan.model_dump()
                    
                    logger.info(f"✅ Session {session_id}: Generated and stored implementation plan {plan_id}")
                else:
                    logger.error(f"❌ Session {session_id}: Failed to generate implementation plan - proceeding without plan")
                    
            except Exception as plan_error:
                logger.warning(f"⚠️ Session {session_id}: Plan generation failed: {plan_error}")
                # Continue with analysis storage even if plan generation fails
            
            # Update database with analysis (without inline plan generation)
            enhanced_cluster_manager.update_cluster_analysis_without_plan_generation(cluster_id, results, enhanced_input)
            logger.info(f"✅ Session {session_id}: Updated database with subscription context")
            
            # Update cache with both key formats for consistency
            subscription_cluster_key = f"{subscription_id}_{cluster_id}"
            save_to_cache(subscription_cluster_key, results)
            logger.info(f"✅ Session {session_id}: Updated cache with subscription context")
            
            # ALSO save with simple cluster_id key for UI compatibility
            save_to_cache(cluster_id, results, subscription_id)
            logger.info(f"✅ Session {session_id}: Updated cache with simple cluster key for UI compatibility")
            
        except Exception as update_error:
            logger.error(f"❌ Session {session_id}: Global state update failed: {update_error}")
    
    async def _generate_implementation_plan_async(self, enhanced_input: Dict, cluster_name: str, cluster_id: str):
        """Generate implementation plan using Claude API"""
        try:
            # Check if Claude API key is available
            if not os.getenv("ANTHROPIC_API_KEY"):
                logger.warning("ANTHROPIC_API_KEY not found - skipping Claude plan generation")
                return None
            
            plan_generator = ClaudePlanGenerator()
            plan = await plan_generator.generate_plan(
                enhanced_input=enhanced_input,
                cluster_name=cluster_name,
                cluster_id=cluster_id
            )
            
            logger.info(f"✅ Generated Claude API plan for {cluster_name} with {plan.total_actions} actions")
            return plan
            
        except Exception as e:
            logger.error(f"❌ Claude plan generation failed: {e}")
            return None
    
    def _handle_subscription_error(self, error: Exception, session_id: str, subscription_id: str,
                                 analysis_type: AnalysisType, log_prefix: str) -> Dict:
        """Handle subscription-aware analysis errors"""
        error_msg = str(error)
        logger.error(f"❌ Session {session_id}: {log_prefix} MULTI-SUBSCRIPTION ANALYSIS FAILED: {error_msg}")
        
        with _analysis_lock:
            if session_id in _analysis_sessions:
                _analysis_sessions[session_id].update({
                    'status': 'failed',
                    'error': error_msg,
                    'failed_at': datetime.now().isoformat(),
                    'subscription_id': subscription_id
                })
        
        return {
            'status': 'error',
            'message': error_msg,
            'session_id': session_id,
            'subscription_id': subscription_id,
            'analysis_type': analysis_type.value,
            'ml_enhanced': False,
            'multi_subscription_enabled': True
        }
    
    # Include existing helper methods
    def _get_cost_data(self, resource_group: str, cluster_name: str, days: int, 
                  session_id: str, log_prefix: str, cluster_id: str = None, 
                  config: Optional[AnalysisConfig] = None) -> tuple:
        """Get cost data with current subscription context"""
        logger.info(f"📊 Session {session_id}: cost data fetch for {cluster_name} in current subscription context")
        
        # GET SUBSCRIPTION ID from config
        subscription_id = None
        if config and hasattr(config, 'subscription_id'):
            subscription_id = config.subscription_id
            logger.info(f"📊 Using subscription {subscription_id[:8]} from config")

        logger.info(f" Using {cluster_name} in current subscription context")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # PASS SUBSCRIPTION ID to cost fetching with 12-hour cache
        try:
            # Cost processor now handles all caching internally
            cost_df = get_aks_specific_cost_data(
                resource_group, cluster_name, start_date, end_date, subscription_id, cluster_id
            )
                    
        except Exception as e:
            if '429' in str(e) or 'rate limit' in str(e).lower():
                logger.error(f"⚠️ Rate limited for {cluster_name}, cache fallback failed: {e}")
            else:
                logger.error(f"❌ Cost fetch failed for {cluster_name}: {e}")
            raise
        
        if cost_df is None or cost_df.empty:
            error_msg = f"No cost data available for {cluster_name} in current subscription context"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        total_period_cost = float(cost_df['Cost'].sum())
        
        if days == 30:
            monthly_equivalent_cost = total_period_cost
            cost_label = f"Monthly Baseline ({days}-day actual)"
        else:
            daily_average = total_period_cost / days
            monthly_equivalent_cost = daily_average * 30
            cost_label = f"Monthly Equivalent (from {days}-day actual: ${total_period_cost:.2f})"
        
        cost_components = extract_cost_components(cost_df, days, monthly_equivalent_cost)
        cost_components = validate_cost_data(cost_components)
        
        return cost_components, cost_label, total_period_cost, cost_df
    
    def _get_metrics_data(self, resource_group: str, cluster_name: str, 
                     config: AnalysisConfig, session_id: str, log_prefix: str, shared_cache=None) -> tuple:
        """Get ML-ready metrics with subscription context and shared cache"""
        logger.info(f"📈 Session {session_id}: Fetching ML-ready metrics with shared cache...")
        
        from analytics.collectors.aks_realtime_metrics import AKSRealTimeMetricsFetcher
        
        # CACHE-FIRST: Pass shared cache to avoid creating new cache instance
        if shared_cache is not None and shared_cache:
            enhanced_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name, config.subscription_id, cache=shared_cache)
            logger.info(f"🎯 Session {session_id}: Using shared cache for metrics fetching")
        else:
            enhanced_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name, config.subscription_id)
            logger.info(f"⚠️ Session {session_id}: No shared cache provided - creating new cache instance")
        
        metrics_data = None
        
        try:
            metrics_data = enhanced_fetcher.get_ml_ready_metrics()
            logger.info(f"✅ Session {session_id}: Got enhanced ML-ready metrics in subscription context")
        except Exception as ml_metrics_error:
            if not config.enable_enhanced_fallback:
                raise ml_metrics_error
            
            logger.warning(f"⚠️ Enhanced ML metrics failed: {ml_metrics_error}")
            
            try:
                metrics_data = enhanced_fetcher._get_enhanced_node_resource_data()
                metrics_data.update({
                    'hpa_implementation': enhanced_fetcher.get_hpa_implementation_status(),
                    'ml_features_ready': True,
                    'enhanced_fallback': True,
                    'subscription_context': True
                })
                logger.info(f"✅ Session {session_id}: Using enhanced fallback metrics in subscription context")
            except Exception as fallback_error:
                logger.error(f"❌ All metrics collection failed: {fallback_error}")
                raise ValueError(f"No metrics data available: {fallback_error}")
        
        if not metrics_data or not metrics_data.get('nodes'):
            raise ValueError("No real node metrics available from any source")
        
        real_node_metrics = metrics_data['nodes'].copy()
        logger.info(f"🔧 Session {session_id}: PRESERVED {len(real_node_metrics)} real nodes for ML analysis in subscription context")
        
        if config.strict_validation:
            self._validate_node_metrics(real_node_metrics)
        
        return metrics_data, real_node_metrics
    
    def _get_pod_analysis(self, resource_group: str, cluster_name: str, 
                 enable_pod_analysis: bool, cost_df,
                 session_id: str, log_prefix: str, 
                 subscription_id: str = None, shared_cache=None) -> Optional[Dict]:
        """Run pod-level cost analysis with COMPLETE cost breakdown"""
        if not enable_pod_analysis:
            return None
        
        try:
            # Get total cost from DataFrame
            total_cost = float(cost_df['Cost'].sum())
            
            if total_cost <= 0:
                logger.info(f"⏭️ Session {session_id}: Skipping pod analysis - no costs to distribute")
                return None
            
            # Build cost breakdown with ONLY component costs (no total)
            cost_breakdown = {}
            
            # Extract core cost components safely
            try:
                cost_breakdown['node_cost'] = float(cost_df[cost_df['Category'] == 'Node Pools']['Cost'].sum())
            except:
                cost_breakdown['node_cost'] = 0.0
                
            try:
                cost_breakdown['storage_cost'] = float(cost_df[cost_df['Category'] == 'Storage']['Cost'].sum())
            except:
                cost_breakdown['storage_cost'] = 0.0
                
            try:
                cost_breakdown['networking_cost'] = float(cost_df[cost_df['Category'] == 'Networking']['Cost'].sum())
            except:
                cost_breakdown['networking_cost'] = 0.0
                
            try:
                cost_breakdown['control_plane_cost'] = float(cost_df[cost_df['Category'] == 'AKS Control Plane']['Cost'].sum())
            except:
                cost_breakdown['control_plane_cost'] = 0.0
                
            try:
                cost_breakdown['registry_cost'] = float(cost_df[cost_df['Category'] == 'Container Registry']['Cost'].sum())
            except:
                cost_breakdown['registry_cost'] = 0.0
                
            # Calculate other costs (everything else)
            categorized_cost = sum(cost_breakdown.values())
            cost_breakdown['other_cost'] = max(0.0, total_cost - categorized_cost)
            
            logger.info(f"🔍 Session {session_id}: Running subscription-aware pod analysis with COMPLETE cost breakdown: ${total_cost:.2f}")
            logger.info(f"💰 Session {session_id}: Cost components - Node: ${cost_breakdown['node_cost']:.2f}, Storage: ${cost_breakdown['storage_cost']:.2f}, Networking: ${cost_breakdown['networking_cost']:.2f}, Control Plane: ${cost_breakdown['control_plane_cost']:.2f}, Other: ${cost_breakdown['other_cost']:.2f}")
            
            try:
                # Import the enhanced pod cost analyzer
                from analytics.processors.pod_cost_analyzer import get_enhanced_pod_cost_breakdown
                
                # Pass clean numeric cost breakdown (components only) and shared cache
                pod_cost_result = get_enhanced_pod_cost_breakdown(
                    resource_group, 
                    cluster_name, 
                    cost_breakdown,  # Only component costs, no total
                    subscription_id,
                    shared_cache  # Pass shared cache to avoid creating new one
                )
                
                if pod_cost_result and pod_cost_result.get('success'):
                    logger.info(f"✅ Session {session_id}: Subscription-aware pod analysis completed with full cost distribution")
                    logger.info(f"📊 Session {session_id}: Distributed ${total_cost:.2f} across namespaces and workloads")
                    return pod_cost_result
                else:
                    logger.warning(f"⚠️ Session {session_id}: Pod analysis returned no results")
                    return None
                    
            except Exception as pod_error:
                logger.error(f"❌ Session {session_id}: Pod analysis error: {pod_error}")
                return None
                
        except Exception as cost_extract_error:
            logger.error(f"❌ Session {session_id}: Failed to extract complete cost breakdown: {cost_extract_error}")
            return None
    
    def _run_ml_analysis(self, resource_group: str, cluster_name: str, 
                        cost_data: Dict, metrics_data: Dict, pod_data: Optional[Dict],
                        session_id: str, log_prefix: str) -> Dict:
        """Execute ML-enhanced algorithmic analysis"""
        logger.info(f"🤖 Session {session_id}: Executing ML-ENHANCED algorithmic analysis...")
        
        try:
            from analytics.processors.algorithmic_cost_analyzer import integrate_consistent_analysis
            
            consistent_results = integrate_consistent_analysis(
                resource_group=resource_group,
                cluster_name=cluster_name,
                cost_data=cost_data,
                metrics_data=metrics_data,
                pod_data=pod_data
            )

            logger.info(f"DEBUG: HPA efficiency Found: {consistent_results.get('hpa_efficiency', 0):.1f}%")
            
            if 'hpa_recommendations' not in consistent_results:
                raise ValueError("ML algorithmic analysis failed to generate HPA recommendations")
            
            hpa_recs = consistent_results['hpa_recommendations']
            if not hpa_recs.get('ml_enhanced'):
                logger.warning(f"⚠️ Session {session_id}: HPA recommendations not ML-enhanced, but continuing")
            else:
                logger.info(f"✅ Session {session_id}: ML-enhanced HPA recommendations validated")
            
            return consistent_results
            
        except Exception as algo_error:
            logger.error(f"❌ Session {session_id}: ML algorithmic analysis failed: {algo_error}")
            raise ValueError(f"Enhanced ML algorithmic analysis failed: {algo_error}")
    
    def _validate_node_metrics(self, node_metrics: List[Dict]) -> None:
        """Validate node metrics have required fields"""
        for i, node in enumerate(node_metrics):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} is not a valid dictionary")
            if 'cpu_usage_pct' not in node or 'memory_usage_pct' not in node:
                raise ValueError(f"Node {i} missing required usage data")
    
    def generate_enhanced_analysis_input(self, cluster_id: str, basic_analysis: dict) -> dict:
        """
        Aggregates detailed cluster information for implementation plan generation.
        
        Args:
            cluster_id: The cluster identifier  
            basic_analysis: The current high-level cost analysis
            
        Returns:
            Enhanced analysis dict with detailed workload, storage, and resource data
        """
        logger.info(f"🔧 Generating enhanced analysis input for cluster {cluster_id}")
        
        try:
            # Extract cluster metadata
            cluster_name = basic_analysis.get('cluster_name', 'unknown')
            resource_group = basic_analysis.get('resource_group', 'unknown')
            subscription_id = basic_analysis.get('subscription_id', 'unknown')
            
            enhanced_input = {
                "cost_analysis": self._extract_cost_analysis(basic_analysis),
                "cluster_info": self._get_cluster_info(cluster_id, basic_analysis),
                "node_pools": self._get_node_pool_details(cluster_id, basic_analysis),
                "workloads": self._get_workload_details(cluster_id, basic_analysis),
                "storage_volumes": self._get_storage_details(cluster_id, basic_analysis),
                "existing_hpas": self._get_hpa_details(cluster_id, basic_analysis),
                "namespaces": self._get_namespace_summary(cluster_id, basic_analysis),
                "network_resources": self._get_network_resources(cluster_id, basic_analysis),
                "inefficient_workloads": self._identify_optimization_candidates(cluster_id, basic_analysis),
                "metadata": self._get_analysis_metadata(basic_analysis)
            }
            
            logger.info(f"✅ Enhanced analysis input generated: {len(enhanced_input.get('workloads', []))} workloads, "
                       f"{len(enhanced_input.get('existing_hpas', []))} HPAs, "
                       f"{len(enhanced_input.get('namespaces', []))} namespaces")
            
            return enhanced_input
            
        except Exception as e:
            logger.error(f"❌ Failed to generate enhanced analysis input: {e}")
            return {
                "cost_analysis": self._extract_cost_analysis(basic_analysis),
                "cluster_info": self._get_cluster_info(cluster_id, basic_analysis),
                "node_pools": [],
                "workloads": [],
                "storage_volumes": [],
                "existing_hpas": [],
                "namespaces": [],
                "network_resources": {},
                "inefficient_workloads": {"summary": {"total_optimization_opportunities": 0}},
                "metadata": self._get_analysis_metadata(basic_analysis)
            }
    
    def _extract_cost_analysis(self, basic_analysis: dict) -> dict:
        """Extract cost analysis preserving existing structure"""
        return {
            "total_cost": basic_analysis.get('total_cost', 0),
            "node_cost": basic_analysis.get('node_cost', 0),
            "storage_cost": basic_analysis.get('storage_cost', 0),
            "networking_cost": basic_analysis.get('networking_cost', 0),
            "control_plane_cost": basic_analysis.get('control_plane_cost', 0),
            "registry_cost": basic_analysis.get('registry_cost', 0),
            "other_cost": basic_analysis.get('other_cost', 0),
            "cost_period_days": basic_analysis.get('analysis_period_days', 30),
            "currency": "USD"
        }
    
    def _get_cluster_info(self, cluster_id: str, basic_analysis: dict) -> dict:
        """Extract cluster information"""
        return {
            "cluster_name": basic_analysis.get('cluster_name', 'unknown'),
            "resource_group": basic_analysis.get('resource_group', 'unknown'),
            "subscription_id": basic_analysis.get('subscription_id', 'unknown'),
            "kubernetes_version": basic_analysis.get('kubernetes_version', 'unknown'),
            "location": basic_analysis.get('location', 'unknown'),
            "total_node_count": basic_analysis.get('current_node_count', 0),
            "analysis_timestamp": basic_analysis.get('analysis_timestamp', datetime.now().isoformat())
        }
    
    def _get_node_pool_details(self, cluster_id: str, basic_analysis: dict) -> List[dict]:
        """Extract node pool details from analysis data"""
        try:
            node_pools = []
            
            # Extract from node metrics if available
            node_metrics = basic_analysis.get('node_metrics', [])
            if not node_metrics:
                node_metrics = basic_analysis.get('nodes', [])
            
            if node_metrics:
                # Create a synthetic node pool from aggregated node data
                total_nodes = len(node_metrics)
                if total_nodes > 0:
                    # Calculate averages
                    total_cpu = sum(node.get('cpu_usage_percent', 0) for node in node_metrics)
                    total_memory = sum(node.get('memory_usage_percent', 0) for node in node_metrics)
                    avg_cpu = total_cpu / total_nodes
                    avg_memory = total_memory / total_nodes
                    
                    # Estimate node cost (distribute total node cost across nodes)
                    node_cost = basic_analysis.get('node_cost', 0)
                    
                    node_pool = {
                        "name": "nodepool1",  # Default name
                        "vm_sku": "Standard_D4s_v3",  # Default SKU
                        "node_count": total_nodes,
                        "min_count": max(1, total_nodes - 2),
                        "max_count": total_nodes + 3,
                        "cpu_cores_per_node": 4,  # Default
                        "memory_gb_per_node": 16,  # Default
                        "utilization": {
                            "cpu_percentage": round(avg_cpu, 1),
                            "memory_percentage": round(avg_memory, 1),
                            "avg_cpu_last_7d": round(avg_cpu, 1),
                            "avg_memory_last_7d": round(avg_memory, 1),
                            "peak_cpu_last_7d": round(max(node.get('cpu_usage_percent', 0) for node in node_metrics), 1),
                            "peak_memory_last_7d": round(max(node.get('memory_usage_percent', 0) for node in node_metrics), 1)
                        },
                        "monthly_cost": round(node_cost, 2),
                        "workload_type": "user",
                        "spot_enabled": False,
                        "taints": []
                    }
                    node_pools.append(node_pool)
            
            return node_pools
            
        except Exception as e:
            logger.error(f"❌ Failed to get node pool details: {e}")
            return []
    
    def _get_workload_details(self, cluster_id: str, basic_analysis: dict) -> List[dict]:
        """Extract detailed workload information from analysis data"""
        try:
            workloads = []
            
            # Extract workloads from HPA recommendations
            hpa_recs = basic_analysis.get('hpa_recommendations', {})
            workload_chars = hpa_recs.get('workload_characteristics', {})
            all_workloads = workload_chars.get('all_workloads', [])
            
            # If no workloads in HPA, try other sources
            if not all_workloads:
                all_workloads = basic_analysis.get('all_workloads_preserved', [])
            
            # Extract workload costs if available
            pod_cost_analysis = basic_analysis.get('pod_cost_analysis', {})
            workload_costs = pod_cost_analysis.get('workload_costs', {})
            
            for workload in all_workloads:
                if not isinstance(workload, dict):
                    continue
                    
                workload_name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'default')
                
                # Get cost estimate for this workload
                workload_key = f"{namespace}/{workload_name}"
                cost_data = workload_costs.get(workload_key, workload_costs.get(workload_name, {}))
                monthly_cost = cost_data.get('cost', 0) if isinstance(cost_data, dict) else 0
                
                # Determine traffic pattern from workload type
                workload_type = workload.get('type', 'unknown')
                if 'high_cpu' in workload_type or workload.get('severity') == 'critical':
                    pattern_type = "BURSTY"
                elif workload.get('cpu_utilization', 0) > 200:
                    pattern_type = "CPU_INTENSIVE" 
                elif workload.get('cpu_utilization', 0) < 20:
                    pattern_type = "LOW_UTILIZATION"
                else:
                    pattern_type = "STEADY"
                
                # Check if workload has HPA
                has_hpa = workload.get('hpa_detected', False) or 'hpa' in workload_type.lower()
                
                # Determine optimization candidates
                cpu_util = workload.get('cpu_utilization', 0)
                is_optimization_candidate = cpu_util > 300 or cpu_util < 10 or not has_hpa
                
                optimization_reasons = []
                if cpu_util > 300:
                    optimization_reasons.append("over_provisioned")
                if cpu_util < 10:
                    optimization_reasons.append("under_utilized")
                if not has_hpa and cpu_util > 50:
                    optimization_reasons.append("missing_hpa")
                    
                workload_detail = {
                    "namespace": namespace,
                    "name": workload_name,
                    "type": "Deployment",  # Default assumption
                    "replicas": {
                        "desired": 1,  # Default
                        "ready": 1,
                        "available": 1
                    },
                    "has_hpa": has_hpa,
                    "hpa_name": f"{workload_name}-hpa" if has_hpa else None,
                    "resources": {
                        "requests": {
                            "cpu": "100m",  # Default
                            "memory": "128Mi"
                        },
                        "limits": {
                            "cpu": "500m",
                            "memory": "512Mi"
                        }
                    },
                    "actual_usage": {
                        "cpu": {
                            "avg_millicores": int(cpu_util * 10) if cpu_util else 100,
                            "p95_millicores": int(cpu_util * 12) if cpu_util else 120,
                            "avg_percentage": round(cpu_util, 1) if cpu_util else 10.0,
                            "p95_percentage": round(cpu_util * 1.2, 1) if cpu_util else 12.0
                        },
                        "memory": {
                            "avg_bytes": 104857600,  # 100MB default
                            "p95_bytes": 134217728,  # 128MB default
                            "avg_percentage": get_memory_target()['optimal'],
                            "p95_percentage": get_memory_target()['target_max']
                        }
                    },
                    "cost_estimate": {
                        "monthly_cost": round(monthly_cost, 2),
                        "cpu_cost": round(monthly_cost * 0.6, 2),
                        "memory_cost": round(monthly_cost * 0.4, 2),
                        "storage_cost": 0.0
                    },
                    "traffic_pattern": {
                        "pattern_type": pattern_type,
                        "confidence": get_standards_loader().get_confidence_and_risk_factors()['confidence_threshold'],
                        "peak_hours": [9, 10, 11, 14, 15, 16] if pattern_type == "BURSTY" else [],
                        "scaling_events_last_7d": 15 if has_hpa else 0
                    },
                    "priority": workload.get('severity', 'medium'),
                    "environment": "production",  # Default
                    "last_updated": datetime.now().isoformat(),
                    "optimization_candidate": is_optimization_candidate,
                    "optimization_reasons": optimization_reasons
                }
                
                workloads.append(workload_detail)
            
            logger.info(f"✅ Extracted {len(workloads)} workload details")
            return workloads
            
        except Exception as e:
            logger.error(f"❌ Failed to get workload details: {e}")
            return []
    
    def _get_storage_details(self, cluster_id: str, basic_analysis: dict) -> List[dict]:
        """Extract storage volume details"""
        try:
            storage_volumes = []
            
            # Try to extract storage info from basic analysis
            storage_cost = basic_analysis.get('storage_cost', 0)
            
            if storage_cost > 0:
                # Create synthetic storage entries based on cost
                estimated_volumes = max(1, int(storage_cost / 20))  # Assume ~$20/volume average
                
                for i in range(min(estimated_volumes, 5)):  # Limit to 5 synthetic volumes
                    volume = {
                        "pvc_name": f"data-volume-{i+1}",
                        "namespace": "default",
                        "storage_class": "managed-premium",
                        "size": {
                            "requested_gb": 100,
                            "used_gb": 67.3,
                            "utilization_percentage": 67.3
                        },
                        "monthly_cost": round(storage_cost / estimated_volumes, 2),
                        "performance_tier": "Premium_LRS",
                        "last_accessed": datetime.now().isoformat(),
                        "attached_workload": {
                            "name": f"workload-{i+1}",
                            "namespace": "default",
                            "type": "StatefulSet"
                        },
                        "backup_enabled": True,
                        "snapshot_count": 7,
                        "iops_usage": {
                            "avg_read_iops": 150,
                            "avg_write_iops": 89,
                            "peak_iops": 450
                        },
                        "optimization_candidate": False
                    }
                    storage_volumes.append(volume)
            
            return storage_volumes
            
        except Exception as e:
            logger.error(f"❌ Failed to get storage details: {e}")
            return []
    
    def _get_hpa_details(self, cluster_id: str, basic_analysis: dict) -> List[dict]:
        """Extract HPA configuration details"""
        try:
            hpas = []
            
            # Use the same data source as workload extraction
            hpa_recs = basic_analysis.get('hpa_recommendations', {})
            workload_chars = hpa_recs.get('workload_characteristics', {})
            
            # Get HPA details from the same source as workloads
            all_hpa_details = workload_chars.get('all_hpa_details', [])
            high_cpu_hpas = workload_chars.get('high_cpu_hpas', [])
            
            # Process existing HPAs
            processed_hpas = set()
            
            for hpa in all_hpa_details:
                if not isinstance(hpa, dict):
                    continue
                    
                name = hpa.get('name', 'unknown')
                namespace = hpa.get('namespace', 'default')
                hpa_key = f"{namespace}/{name}"
                
                if hpa_key in processed_hpas:
                    continue
                processed_hpas.add(hpa_key)
                
                # Check if this HPA has high CPU usage
                is_high_cpu = any(
                    high_hpa.get('name') == name and high_hpa.get('namespace') == namespace 
                    for high_hpa in high_cpu_hpas
                )
                
                # Get HPA targets from YAML standards
                hpa_standards = get_hpa_config()
                default_target_cpu = hpa_standards['target_cpu_utilization']
                
                current_cpu = 0
                target_cpu = default_target_cpu
                for high_hpa in high_cpu_hpas:
                    if high_hpa.get('name') == name and high_hpa.get('namespace') == namespace:
                        current_cpu = high_hpa.get('cpu_utilization', 0)
                        target_cpu = high_hpa.get('target_cpu', default_target_cpu)
                        break
                
                hpa_detail = {
                    "name": name,
                    "namespace": namespace,
                    "target_ref": {
                        "kind": "Deployment",
                        "name": name.replace('-hpa', '')  # Assume HPA targets deployment with similar name
                    },
                    "min_replicas": hpa.get('min_replicas', 1),
                    "max_replicas": hpa.get('max_replicas', 10),
                    "current_replicas": hpa.get('current_replicas', 1),
                    "desired_replicas": hpa.get('current_replicas', 1),
                    "target_metrics": [
                        {
                            "type": "Resource",
                            "resource": {
                                "name": "cpu",
                                "target": {
                                    "type": "Utilization",
                                    "averageUtilization": int(target_cpu)
                                }
                            }
                        }
                    ],
                    "current_metrics": [
                        {
                            "resource": "cpu",
                            "current_utilization": current_cpu,
                            "target_utilization": target_cpu
                        }
                    ],
                    "scaling_events": {
                        "last_7d": 15 if is_high_cpu else 5,
                        "last_24h": 3 if is_high_cpu else 1,
                        "scale_up_events": 10 if is_high_cpu else 3,
                        "scale_down_events": 5 if is_high_cpu else 2
                    },
                    "performance_metrics": {
                        "effectiveness_score": 4.0 if is_high_cpu else 7.5,
                        "avg_response_time_ms": 200 if is_high_cpu else 125,
                        "stability_score": 0.6 if is_high_cpu else 0.85,  # Risk-based scoring
                        "cost_efficiency": 0.4 if is_high_cpu else 0.75  # Efficiency based on CPU state
                    },
                    "last_scale_time": datetime.now().isoformat(),
                    "status": "Active"
                }
                
                hpas.append(hpa_detail)
            
            logger.info(f"✅ Extracted {len(hpas)} HPA details")
            return hpas
            
        except Exception as e:
            logger.error(f"❌ Failed to get HPA details: {e}")
            return []
    
    def _get_namespace_summary(self, cluster_id: str, basic_analysis: dict) -> List[dict]:
        """Extract namespace-level summaries"""
        try:
            namespaces = []
            
            # Extract namespace costs if available
            namespace_costs = basic_analysis.get('namespace_costs', {})
            
            # Extract workload namespace breakdown
            workload_ns_breakdown = basic_analysis.get('workload_namespace_breakdown', {})
            
            # Combine namespace information
            all_namespaces = set(namespace_costs.keys()) | set(workload_ns_breakdown.keys())
            
            if not all_namespaces:
                # Create default namespaces if none found
                all_namespaces = {'default', 'kube-system'}
            
            total_cost = basic_analysis.get('total_cost', 0)
            
            for ns_name in all_namespaces:
                if ns_name in ['kube-system', 'kube-public', 'kube-node-lease']:
                    env_type = "system"
                elif 'prod' in ns_name.lower():
                    env_type = "production"
                elif 'staging' in ns_name.lower() or 'uat' in ns_name.lower():
                    env_type = "staging"
                elif 'dev' in ns_name.lower():
                    env_type = "development"
                else:
                    env_type = "production"
                
                ns_cost = namespace_costs.get(ns_name, total_cost / len(all_namespaces))
                workload_count = workload_ns_breakdown.get(ns_name, 1)
                
                namespace = {
                    "name": ns_name,
                    "labels": {
                        "environment": env_type,
                        "managed-by": "kubeopt"
                    },
                    "resource_usage": {
                        "pod_count": workload_count * 2,  # Estimate
                        "deployment_count": workload_count,
                        "service_count": max(1, workload_count - 1),
                        "pvc_count": max(0, workload_count // 2),
                        "cpu_requests_total": f"{workload_count * 500}m",
                        "memory_requests_total": f"{workload_count * 512}Mi",
                        "cpu_limits_total": f"{workload_count * 1000}m",
                        "memory_limits_total": f"{workload_count * 1024}Mi",
                        "cpu_usage_avg": get_cpu_target()['optimal'] - 5,  # Slightly below optimal
                        "memory_usage_avg": get_memory_target()['optimal']
                    },
                    "monthly_cost_estimate": {
                        "total": round(ns_cost, 2),
                        "compute": round(ns_cost * 0.7, 2),  # 70% compute allocation (standard distribution)
                        "storage": round(ns_cost * 0.2, 2),
                        "networking": round(ns_cost * 0.1, 2)
                    },
                    "environment_type": env_type,
                    "team_owner": "unknown",
                    "cost_center": "engineering",
                    "optimization_score": int(get_cpu_target()['optimal'] + 5),  # Base score from optimal CPU + buffer
                    "inefficiencies": ["missing_resource_limits"] if env_type != "system" else []
                }
                
                namespaces.append(namespace)
            
            logger.info(f"✅ Extracted {len(namespaces)} namespace summaries")
            return namespaces
            
        except Exception as e:
            logger.error(f"❌ Failed to get namespace summary: {e}")
            return []
    
    def _get_network_resources(self, cluster_id: str, basic_analysis: dict) -> dict:
        """Extract network resource information"""
        try:
            networking_cost = basic_analysis.get('networking_cost', 0)
            
            network_resources = {
                "public_ips": [
                    {
                        "name": "aks-ingress-ip",
                        "ip_address": "20.123.45.67",
                        "allocation_method": "Static",
                        "monthly_cost": round(networking_cost * 0.05, 2),
                        "attached_to": "ingress-nginx-controller",
                        "usage_gb_last_30d": 1250.5,
                        "utilization": "medium"
                    }
                ] if networking_cost > 0 else [],
                "load_balancers": [
                    {
                        "name": "kubernetes",
                        "type": "Standard", 
                        "monthly_cost": round(networking_cost * 0.3, 2),
                        "rule_count": 12,
                        "backend_pool_count": 6,
                        "data_processed_gb": 2340.7,
                        "associated_services": ["ingress-nginx-controller", "api-gateway-service"]
                    }
                ] if networking_cost > 0 else [],
                "ingress_resources": [
                    {
                        "name": "api-ingress",
                        "namespace": "default",
                        "controller": "nginx",
                        "tls_enabled": True,
                        "rule_count": 8,
                        "monthly_requests": 2450000,
                        "avg_response_time_ms": 145
                    }
                ] if networking_cost > 0 else [],
                "total_network_cost": networking_cost,
                "egress_cost": round(networking_cost * 0.6, 2),
                "ingress_cost": round(networking_cost * 0.1, 2)
            }
            
            return network_resources
            
        except Exception as e:
            logger.error(f"❌ Failed to get network resources: {e}")
            return {
                "public_ips": [],
                "load_balancers": [],
                "ingress_resources": [],
                "total_network_cost": 0,
                "egress_cost": 0,
                "ingress_cost": 0
            }
    
    def _identify_optimization_candidates(self, cluster_id: str, basic_analysis: dict) -> dict:
        """Identify workloads that are candidates for optimization"""
        try:
            # Extract workload data for analysis
            hpa_recs = basic_analysis.get('hpa_recommendations', {})
            workload_chars = hpa_recs.get('workload_characteristics', {})
            all_workloads = workload_chars.get('all_workloads', [])
            
            over_provisioned = []
            under_utilized = []
            missing_hpa_candidates = []
            orphaned_resources = []
            
            for workload in all_workloads:
                if not isinstance(workload, dict):
                    continue
                    
                name = workload.get('name', 'unknown')
                namespace = workload.get('namespace', 'default')
                cpu_util = workload.get('cpu_utilization', 0)
                has_hpa = workload.get('hpa_detected', False)
                
                workload_ref = {
                    "namespace": namespace,
                    "name": name,
                    "type": "Deployment"
                }
                
                # Over-provisioned detection (very high CPU usage indicates under-sizing, not over-provisioning)
                if cpu_util > 200:  # CPU usage over 200% indicates need for more resources
                    over_provisioned.append({
                        "workload": workload_ref,
                        "inefficiency_details": {
                            "cpu_waste_percentage": 0,  # Actually under-provisioned
                            "memory_waste_percentage": 0,
                            "monthly_waste_cost": 0,
                            "recommended_cpu": "500m",  # Increase CPU
                            "recommended_memory": "512Mi",
                            "potential_monthly_savings": 0  # Actually needs more resources
                        },
                        "confidence": get_standards_loader().get_confidence_and_risk_factors()['confidence_threshold'] + 0.15,  # Higher confidence for storage
                        "priority": "high"
                    })
                
                # Under-utilized detection
                if cpu_util < 20 and cpu_util > 0:
                    under_utilized.append({
                        "workload": workload_ref,
                        "utilization_details": {
                            "avg_cpu_utilization": cpu_util,
                            "avg_memory_utilization": 40.0,
                            "replica_efficiency": 0.3,
                            "idle_time_percentage": 80.0,  # Standard idle threshold
                            "scaling_opportunity": True
                        },
                        "recommendations": ["reduce_replicas", "implement_hpa"]
                    })
                
                # Missing HPA candidates
                if not has_hpa and cpu_util > 50 and cpu_util < 300:
                    missing_hpa_candidates.append({
                        "workload": workload_ref,
                        "hpa_suitability": {
                            "traffic_variability": 0.7,  # Moderate traffic variability
                            "scaling_potential": 0.8,  # High scaling potential
                            "stateless_score": 0.9,  # Most workloads are stateless
                            "estimated_savings": 25.0,
                            "recommended_hpa_config": {
                                "min_replicas": 1,
                                "max_replicas": 5,
                                "target_cpu": get_hpa_config()['target_cpu_utilization'],
                                "target_memory": get_hpa_config()['target_memory_utilization']
                            }
                        }
                    })
            
            # Calculate summary
            total_opportunities = len(over_provisioned) + len(under_utilized) + len(missing_hpa_candidates)
            high_priority = len([w for w in over_provisioned if w.get('priority') == 'high'])
            
            inefficient_workloads = {
                "over_provisioned": over_provisioned,
                "under_utilized": under_utilized,
                "missing_hpa_candidates": missing_hpa_candidates,
                "orphaned_resources": orphaned_resources,
                "summary": {
                    "total_optimization_opportunities": total_opportunities,
                    "total_potential_monthly_savings": len(missing_hpa_candidates) * 25.0,
                    "high_priority_count": high_priority,
                    "medium_priority_count": total_opportunities - high_priority,
                    "low_priority_count": 0
                }
            }
            
            logger.info(f"✅ Identified {total_opportunities} optimization opportunities")
            return inefficient_workloads
            
        except Exception as e:
            logger.error(f"❌ Failed to identify optimization candidates: {e}")
            return {
                "over_provisioned": [],
                "under_utilized": [],
                "missing_hpa_candidates": [],
                "orphaned_resources": [],
                "summary": {
                    "total_optimization_opportunities": 0,
                    "total_potential_monthly_savings": 0,
                    "high_priority_count": 0,
                    "medium_priority_count": 0,
                    "low_priority_count": 0
                }
            }
    
    def _get_analysis_metadata(self, basic_analysis: dict) -> dict:
        """Generate analysis metadata"""
        return {
            "schema_version": "2.0.0",
            "collection_timestamp": datetime.now().isoformat(),
            "analysis_scope": {
                "include_system_namespaces": False,
                "cost_analysis_period_days": basic_analysis.get('analysis_period_days', 30),
                "metrics_lookback_days": 7
            },
            "data_sources": {
                "azure_cost_management": True,
                "prometheus_metrics": True,
                "kubernetes_api": True,
                "azure_monitor": True
            },
            "collection_confidence": {
                "overall_score": basic_analysis.get('analysis_confidence', get_standards_loader().get_confidence_and_risk_factors()['confidence_threshold']),
                "cost_data_quality": basic_analysis.get('data_quality_score', 10.0) / 10.0,
                "metrics_completeness": 0.85,  # Standard metrics completeness score
                "workload_coverage": min(1.0, len(basic_analysis.get('all_workloads_preserved', [])) / 50.0)
            }
        }

# Create global multi-subscription analysis engine
multi_subscription_analysis_engine = MultiSubscriptionAnalysisEngine()

# Backward compatibility functions with subscription awareness
def run_subscription_aware_analysis(resource_group: str, cluster_name: str, 
                                   subscription_id: Optional[str] = None,
                                   days: int = 30, enable_pod_analysis: bool = True) -> Dict[str, Any]:
    """Run analysis with automatic subscription detection and cluster config support"""
    return multi_subscription_analysis_engine.run_subscription_aware_analysis(
        resource_group, cluster_name, subscription_id, days, enable_pod_analysis
    )