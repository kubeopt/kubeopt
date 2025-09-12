#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
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
from app.main.config import (
    logger, enhanced_cluster_manager, _analysis_lock, _analysis_sessions,
    implementation_generator
)
from app.data.processing.cost_processor import get_aks_specific_cost_data, extract_cost_components
from app.data.processing.metrics_processor import get_aks_metrics_from_monitor
from app.services.cache_manager import save_to_cache
from app.main.utils import validate_cost_data

# Import the subscription manager
from app.services.subscription_manager import azure_subscription_manager

class AnalysisType(Enum):
    """Analysis type configurations"""
    CONSISTENT = "consistent"
    COMPLETELY_FIXED = "completely_fixed"

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
            AnalysisType.COMPLETELY_FIXED: {
                'data_type': 'completely_fixed_ml_enhanced_multi_subscription',
                'metrics_source': 'FIXED ML-Enhanced Multi-Subscription Real-time Collection',
                'log_prefix': '🌐 MULTI-SUB COMPLETELY FIXED'
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
    
    def _validate_cost_data_availability(self, resource_group: str, cluster_name: str, 
                                   subscription_id: str, days: int) -> Dict[str, Any]:
        """Quick validation that cost data is available before expensive analysis"""
        try:
            # Set subscription context for cost check
            if not azure_subscription_manager.set_active_subscription(subscription_id):
                return {'available': False, 'error': f'Cannot set subscription context: {subscription_id}'}
            
            # Quick cost availability check (without full fetch)
            from datetime import datetime, timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Test cost API access with minimal query
            import subprocess
            import json
            
            test_query = {
                "type": "ActualCost",
                "timeframe": "Custom", 
                "timePeriod": {
                    "from": start_date.strftime("%Y-%m-%d"),
                    "to": end_date.strftime("%Y-%m-%d")
                },
                "dataset": {
                    "granularity": "Monthly",
                    "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                    "filter": {
                        "dimensions": {
                            "name": "ResourceGroupName",
                            "operator": "In", 
                            "values": [resource_group]
                        }
                    }
                }
            }
            
            # Save query to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_query, f)
                query_file = f.name
            
            try:
                # Get subscription ID for API call
                sub_cmd = "az account show --query id -o tsv"
                sub_result = subprocess.run(sub_cmd, shell=True, check=True, capture_output=True, text=True, timeout=10)
                current_subscription_id = sub_result.stdout.strip()
                
                # Test cost API with timeout and proper headers
                api_cmd = f"""
                az rest --method POST \
                --uri "https://management.azure.com/subscriptions/{current_subscription_id}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
                --headers "ClientType=AKSCostOptimizer-v2.0" "x-ms-command-name=AKSCostOptimizer" \
                --body @{query_file} \
                --output json
                """
                
                result = subprocess.run(api_cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Parse response to ensure it's valid
                    response = json.loads(result.stdout)
                    if 'properties' in response:
                        return {'available': True, 'subscription_id': current_subscription_id}
                    else:
                        return {'available': False, 'error': 'Invalid cost API response format'}
                else:
                    error_msg = result.stderr.strip()
                    if "429" in error_msg or "Too Many Requests" in error_msg:
                        return {'available': False, 'error': 'Cost API rate limit exceeded - retry later'}
                    else:
                        return {'available': False, 'error': f'Cost API error: {error_msg}'}
                        
            finally:
                # Clean up temp file
                try:
                    import os
                    os.unlink(query_file)
                except:
                    pass
            
        except subprocess.TimeoutExpired:
            return {'available': False, 'error': 'Cost API timeout - Azure may be experiencing issues'}
        except Exception as e:
            return {'available': False, 'error': f'Cost validation error: {e}'}

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
        
            # Step 2: COST-FIRST VALIDATION (fail fast)
            try:
                logger.info(f"💰 COST-FIRST: Validating cost data availability for {cluster_name}")
                
                cost_validation_result = self._validate_cost_data_availability(
                    resource_group, cluster_name, subscription_id, days
                )
                
                if not cost_validation_result['available']:
                    return {
                        'status': 'error',
                        'message': f'Cost data not available: {cost_validation_result["error"]}',
                        'cluster_name': cluster_name,
                        'subscription_id': subscription_id
                    }
                
                logger.info(f"✅ COST-FIRST: Cost data validation passed for {cluster_name}")
                
            except Exception as cost_error:
                logger.error(f"❌ COST-FIRST: Cost validation failed for {cluster_name}: {cost_error}")
                return {
                    'status': 'error',
                    'message': f'Cost data validation failed: {cost_error}',
                    'cluster_name': cluster_name,
                    'subscription_id': subscription_id
                }
            
            # Step 3: Create subscription-aware config
            if config is None:
                config = AnalysisConfig(AnalysisType.COMPLETELY_FIXED, subscription_id)
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
                
                def analysis_function():
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
            from app.shared.kubernetes_data_cache import get_or_create_cache
            shared_cache = get_or_create_cache(cluster_name, resource_group, config.subscription_id)
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
                session_id, config, self.session_metadata[config.analysis_type]
            )
            
            # CRITICAL: Add metrics_data to final_results for implementation_generator
            if metrics_data:
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
                        session_id: str, config: AnalysisConfig, metadata: Dict) -> Dict:
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
        
        if pod_data:
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
            
            # Call implementation generator (SAME SIGNATURE - no changes)
            implementation_plan = implementation_generator.generate_implementation_plan(results)
            results['implementation_plan'] = implementation_plan
            
            if implementation_plan and isinstance(implementation_plan, dict):
                phases = implementation_plan.get('implementation_phases', [])
                if isinstance(phases, list) and len(phases) > 0:
                    # Check if cluster config was used
                    config_enhanced = implementation_plan.get('metadata', {}).get('version', '').endswith('cluster-config-enhanced')
                    cluster_intelligence = implementation_plan.get('intelligenceInsights', {}).get('config_derived', False)
                    
                    logger.info(f"✅ Session {session_id}: Generated implementation plan: {len(phases)} phases")
                    if config_enhanced:
                        logger.info(f"🔧 Session {session_id}: Plan enhanced with cluster configuration intelligence")
                    if cluster_intelligence:
                        logger.info(f"🧠 Session {session_id}: Plan includes cluster intelligence insights")
                else:
                    logger.error(f"❌ Session {session_id}: Implementation plan phases empty")
            else:
                logger.error(f"❌ Session {session_id}: Implementation plan missing phases")
                
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
            enhanced_cluster_manager.update_cluster_analysis(cluster_id, results)
            logger.info(f"✅ Session {session_id}: Updated database with subscription context")
            
            # Update cache with subscription-aware key
            subscription_cluster_key = f"{subscription_id}_{cluster_id}"
            save_to_cache(subscription_cluster_key, results)
            logger.info(f"✅ Session {session_id}: Updated cache with subscription context")
            
        except Exception as update_error:
            logger.error(f"❌ Session {session_id}: Global state update failed: {update_error}")
    
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

        logger.info(f" Using {cluster_name} in current subscription({subscription_id}) context")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # PASS SUBSCRIPTION ID to cost fetching
        cost_df = get_aks_specific_cost_data(
            resource_group, cluster_name, start_date, end_date, subscription_id, cluster_id
        )
        
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
        
        from app.analytics.aks_realtime_metrics import AKSRealTimeMetricsFetcher
        
        # CACHE-FIRST: Pass shared cache to avoid creating new cache instance
        if shared_cache:
            enhanced_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name, config.subscription_id, cache=shared_cache)
            logger.info(f"🎯 Session {session_id}: Using shared cache for metrics fetching")
        else:
            # Fallback to old behavior for backward compatibility
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
                from app.analytics.pod_cost_analyzer import get_enhanced_pod_cost_breakdown
                
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
            from app.analytics.algorithmic_cost_analyzer import integrate_consistent_analysis
            
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