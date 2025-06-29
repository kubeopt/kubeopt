"""
Multi-Subscription Analysis Engine - Enhanced for Parallel Analysis
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

# Import the new subscription manager
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
    """Enhanced AKS Analysis Engine with multi-subscription support"""
    
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
        self.subscription_locks = {}  # Per-subscription locks for thread safety
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
        Run analysis with subscription awareness and automatic detection
        """
        
        cluster_id = f"{resource_group}_{cluster_name}"
        
        # Step 1: Determine subscription if not provided
        cluster_lock = self.get_cluster_lock(cluster_id)
        
        with cluster_lock:
            logger.info(f"🔒 Acquired cluster lock for {cluster_id}")
            
            # Step 1: Determine subscription if not provided
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
                
                # Quick cost data validation before expensive work
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
            
            # Step 4: Run analysis with subscription context - PASS validation_result
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
        validation_result: Dict[str, Any]  # ADD validation_result parameter
    ) -> Dict[str, Any]:
        """Execute analysis within subscription context"""
        
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
                    return self._execute_core_analysis(
                        resource_group, cluster_name, days, enable_pod_analysis,
                        session_id, log_prefix, config
                    )
                
                # Execute with subscription context
                analysis_result = azure_subscription_manager.execute_with_subscription_context(
                    subscription_id, analysis_function
                )
                
                logger.info(f"🔓 Released subscription lock for {subscription_id[:8]}")
            
            if analysis_result['status'] == 'success':
                # Add subscription metadata to results - NOW validation_result is in scope
                analysis_result['results']['subscription_metadata'] = {
                    'subscription_id': subscription_id,
                    'subscription_name': self._get_subscription_name(subscription_id),
                    'cluster_validation': validation_result.get('cluster_info', {}),
                    'analysis_session_id': session_id,
                    'multi_subscription_enabled': True
                }
                
                # Update session and database with subscription info
                self._update_session_state_with_subscription(session_id, analysis_result['results'], config)
                
                if config.update_global_state:
                    self._update_global_state_with_subscription(cluster_id, analysis_result['results'], session_id, subscription_id)
            
            return analysis_result
            
        except Exception as e:
            return self._handle_subscription_error(e, session_id, subscription_id, config.analysis_type, log_prefix)
    
    def _execute_core_analysis(
        self, resource_group: str, cluster_name: str, days: int, 
        enable_pod_analysis: bool, session_id: str, log_prefix: str, config: AnalysisConfig
    ) -> Dict[str, Any]:
        """Execute the core analysis logic (same as before but with session context)"""
        
        cluster_id = f"{resource_group}_{cluster_name}"
        
        try:
            # Step 1: Get cost data
            cost_components, cost_label, total_period_cost, cost_df = self._get_cost_data(
                resource_group, cluster_name, days, session_id, log_prefix, cluster_id
            )
            
            # Step 2: Get metrics data
            metrics_data, real_node_metrics = self._get_metrics_data(
                resource_group, cluster_name, config, session_id, log_prefix
            )
            
            # Step 3: Get pod analysis (if enabled)
            pod_data = self._get_pod_analysis(
                resource_group, cluster_name, enable_pod_analysis, 
                cost_df, session_id, log_prefix
            )
            
            # Step 4: Run ML-enhanced algorithmic analysis
            consistent_results = self._run_ml_analysis(
                resource_group, cluster_name, cost_components, 
                metrics_data, pod_data, session_id, log_prefix
            )
            
            # Step 5: Compile comprehensive results
            final_results = self._compile_results(
                consistent_results, cost_label, total_period_cost, days,
                real_node_metrics, pod_data, resource_group, cluster_name,
                session_id, config, self.session_metadata[config.analysis_type]
            )
            
            # Step 6: Generate implementation plan
            self._generate_implementation_plan(final_results, session_id, log_prefix)
            
            logger.info(f"🎉 Session {session_id}: MULTI-SUBSCRIPTION ANALYSIS COMPLETED")
            
            return {
                'status': 'success',
                'data_type': self.session_metadata[config.analysis_type]['data_type'],
                'session_id': session_id,
                'results': final_results
            }
            
        except Exception as e:
            logger.error(f"❌ Core analysis failed for session {session_id}: {e}")
            raise
    
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
    
    # Include the existing helper methods with subscription awareness
    def _get_cost_data(self, resource_group: str, cluster_name: str, days: int, 
                      session_id: str, log_prefix: str, cluster_id: str = None) -> tuple:
        """Get cost data with current subscription context"""
        logger.info(f"📊 Session {session_id}: cost data fetch for {cluster_name} in current subscription context")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Use smart cost fetching with cluster_id for DB lookup
        cost_df = get_aks_specific_cost_data(
            resource_group, cluster_name, start_date, end_date, cluster_id
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
                         config: AnalysisConfig, session_id: str, log_prefix: str) -> tuple:
        """Get ML-ready metrics with subscription context"""
        logger.info(f"📈 Session {session_id}: Fetching ML-ready metrics in subscription context...")
        
        from app.analytics.aks_realtime_metrics import AKSRealTimeMetricsFetcher
        enhanced_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name)
        
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
    
    # Continue with the remaining helper methods from the original analysis engine...
    def _get_pod_analysis(self, resource_group: str, cluster_name: str, 
                         enable_pod_analysis: bool, cost_df,
                         session_id: str, log_prefix: str) -> Optional[Dict]:
        """Run pod-level cost analysis if enabled"""
        if not enable_pod_analysis:
            return None
        
        try:
            actual_node_cost_for_pod_analysis = float(cost_df[cost_df['Category'] == 'Node Pools']['Cost'].sum())
        except Exception as cost_extract_error:
            logger.error(f"❌ Session {session_id}: Failed to extract node costs: {cost_extract_error}")
            return None
        
        if actual_node_cost_for_pod_analysis <= 0:
            logger.info(f"⏭️ Session {session_id}: Skipping pod analysis - no node costs")
            return None
        
        logger.info(f"🔍 Session {session_id}: Running pod analysis with node cost: ${actual_node_cost_for_pod_analysis:.2f}")
        
        try:
            from app.analytics.pod_cost_analyzer import get_enhanced_pod_cost_breakdown
            pod_cost_result = get_enhanced_pod_cost_breakdown(
                resource_group, cluster_name, actual_node_cost_for_pod_analysis
            )
            
            if pod_cost_result and pod_cost_result.get('success'):
                logger.info(f"✅ Session {session_id}: Pod analysis completed")
                return pod_cost_result
            else:
                logger.warning(f"⚠️ Session {session_id}: Pod analysis returned no results")
                return None
                
        except Exception as pod_error:
            logger.error(f"❌ Session {session_id}: Pod analysis error: {pod_error}")
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
    
    def _compile_results(self, consistent_results: Dict, cost_label: str, 
                        total_period_cost: float, days: int, real_node_metrics: List,
                        pod_data: Optional[Dict], resource_group: str, cluster_name: str,
                        session_id: str, config: AnalysisConfig, metadata: Dict) -> Dict:
        """Compile comprehensive analysis results with subscription info"""
        
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
        
        # Add subscription-aware ML metadata
        ml_metadata = {
            'analysis_type': config.analysis_type.value,
            'subscription_id': config.subscription_id,
            'subscription_aware': True,
            'ml_models_used': True,
            'enterprise_analysis': True,
            'contradiction_free': True,
            'session_id': session_id,
            'multi_subscription_support': True
        }
        
        final_results['ml_analysis_metadata'] = ml_metadata
        
        if pod_data:
            final_results['has_pod_costs'] = True
            final_results['pod_cost_analysis'] = pod_data
            
            if 'namespace_costs' in pod_data:
                final_results['namespace_costs'] = pod_data['namespace_costs']
            elif 'namespace_summary' in pod_data:
                final_results['namespace_costs'] = pod_data['namespace_summary']
        else:
            final_results['has_pod_costs'] = False
        
        final_results.update({
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'cost_period': f"{datetime.now().strftime('%Y-%m-%d')} ({days} days analysis)",
            'cost_data_source': 'Azure Cost Management API',
            'metrics_data_source': metadata['metrics_source'],
            'analysis_timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'ml_enhanced': True,
            config.analysis_type.value: True
        })
        
        return final_results
    
    def _generate_implementation_plan(self, results: Dict, session_id: str, log_prefix: str) -> None:
        """Generate implementation plan"""
        logger.info(f"📋 Session {session_id}: Generating implementation plan...")
        
        try:
            implementation_plan = implementation_generator.generate_implementation_plan(results)
            results['implementation_plan'] = implementation_plan
            
            if implementation_plan and isinstance(implementation_plan, dict):
                phases = implementation_plan.get('implementation_phases', [])
                if isinstance(phases, list) and len(phases) > 0:
                    logger.info(f"✅ Session {session_id}: Generated implementation plan: {len(phases)} phases")
                else:
                    logger.error(f"❌ Session {session_id}: Implementation plan phases empty")
            else:
                logger.error(f"❌ Session {session_id}: Implementation plan missing phases")
                
        except Exception as impl_error:
            logger.error(f"❌ Session {session_id}: Implementation plan generation failed: {impl_error}")
    
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
    """Run analysis with automatic subscription detection"""
    return multi_subscription_analysis_engine.run_subscription_aware_analysis(
        resource_group, cluster_name, subscription_id, days, enable_pod_analysis
    )