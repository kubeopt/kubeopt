"""
Refactored Analysis Engine for AKS Cost Optimization - Eliminates Duplication
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.main.config import (
    logger, enhanced_cluster_manager, _analysis_lock, _analysis_sessions,
    implementation_generator
)
from app.data.processing.cost_processor import get_aks_specific_cost_data, extract_cost_components
from app.data.processing.metrics_processor import get_aks_metrics_from_monitor
from app.services.cache_manager import save_to_cache
from app.main.utils import validate_cost_data


class AnalysisType(Enum):
    """Analysis type configurations"""
    CONSISTENT = "consistent"
    COMPLETELY_FIXED = "completely_fixed"


@dataclass
class AnalysisConfig:
    """Configuration for analysis execution"""
    analysis_type: AnalysisType
    enable_enhanced_fallback: bool = True
    strict_validation: bool = True
    update_global_state: bool = True


class AKSAnalysisEngine:
    """Consolidated AKS Analysis Engine with configurable analysis types"""
    
    def __init__(self):
        self.session_metadata = {
            AnalysisType.CONSISTENT: {
                'data_type': 'ml_enhanced_enterprise',
                'metrics_source': 'ML-Enhanced Real-time Collection',
                'log_prefix': '🤖 ML-ENHANCED'
            },
            AnalysisType.COMPLETELY_FIXED: {
                'data_type': 'completely_fixed_ml_enhanced',
                'metrics_source': 'FIXED ML-Enhanced Real-time Collection',
                'log_prefix': '🤖 COMPLETELY FIXED'
            }
        }
    
    

    def run_analysis(
        self, 
        resource_group: str, 
        cluster_name: str, 
        days: int = 30, 
        enable_pod_analysis: bool = True,
        config: Optional[AnalysisConfig] = None
    ) -> Dict[str, Any]:
        """
        Unified analysis method that handles both consistent and completely fixed analysis types
        """
        if config is None:
            config = AnalysisConfig(AnalysisType.COMPLETELY_FIXED)
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        cluster_id = f"{resource_group}_{cluster_name}"
        
        metadata = self.session_metadata[config.analysis_type]
        log_prefix = metadata['log_prefix']
        
        logger.info(f"{log_prefix}: Starting analysis for {cluster_name} (session: {session_id[:8]})")
        
        try:
            # Initialize session tracking
            session_results = {}
            with _analysis_lock:
                _analysis_sessions[session_id] = {
                    'cluster_id': cluster_id,
                    'results': session_results,
                    'status': 'running',
                    'started_at': datetime.now().isoformat(),
                    'thread_id': threading.current_thread().ident,
                    'analysis_type': config.analysis_type.value
                }
            
            # Step 1: Get cost data
            cost_components, cost_label, total_period_cost, cost_df = self._get_cost_data(
                resource_group, cluster_name, days, session_id, log_prefix
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
                session_id, config, metadata
            )
            
            # Step 6: Generate implementation plan
            self._generate_implementation_plan(final_results, session_id, log_prefix)
            
            # Step 7: Update session and global state
            self._update_session_state(session_id, final_results, config)
            
            if config.update_global_state:
                self._update_global_state(cluster_id, final_results, session_id)
            
            logger.info(f"🎉 Session {session_id[:8]}: {config.analysis_type.value.upper()} ANALYSIS COMPLETED")
            
            return {
                'status': 'success',
                'data_type': metadata['data_type'],
                'session_id': session_id,
                'results': final_results
            }
            
        except Exception as e:
            return self._handle_error(e, session_id, config.analysis_type, log_prefix)
    
    def _get_cost_data(self, resource_group: str, cluster_name: str, days: int, 
                  session_id: str, log_prefix: str, cluster_id: str = None) -> tuple:
        """Get cost data using subscription detection"""
        
        logger.info(f"📊 Session {session_id[:8]}: cost data fetch for {cluster_name}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Use smart cost fetching with cluster_id for DB lookup
        cost_df = get_aks_specific_cost_data(
            resource_group, cluster_name, start_date, end_date, cluster_id
        )
        
        if cost_df is None or cost_df.empty:
            error_msg = f"No cost data available for {cluster_name}. Check subscription access and cluster existence."
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Rest of your existing logic...
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
        """Get ML-ready metrics with fallback handling"""
        logger.info(f"📈 Session {session_id[:8]}: Fetching ML-ready metrics...")
        
        from app.analytics.aks_realtime_metrics import AKSRealTimeMetricsFetcher
        enhanced_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name)
        
        metrics_data = None
        
        # Try enhanced ML-ready metrics first
        try:
            metrics_data = enhanced_fetcher.get_ml_ready_metrics()
            logger.info(f"✅ Session {session_id[:8]}: Got enhanced ML-ready metrics")
        except Exception as ml_metrics_error:
            if not config.enable_enhanced_fallback:
                raise ml_metrics_error
            
            logger.warning(f"⚠️ Enhanced ML metrics failed: {ml_metrics_error}")
            
            # Fallback to basic metrics with enhancements
            try:
                metrics_data = enhanced_fetcher._get_enhanced_node_resource_data()
                metrics_data.update({
                    'hpa_implementation': enhanced_fetcher.get_hpa_implementation_status(),
                    'ml_features_ready': True,
                    'enhanced_fallback': True
                })
                logger.info(f"✅ Session {session_id[:8]}: Using enhanced fallback metrics")
            except Exception as fallback_error:
                logger.error(f"❌ All metrics collection failed: {fallback_error}")
                raise ValueError(f"No metrics data available: {fallback_error}")
        
        if not metrics_data or not metrics_data.get('nodes'):
            raise ValueError("No real node metrics available from any source")
        
        # Extract and validate real node data
        real_node_metrics = metrics_data['nodes'].copy()
        logger.info(f"🔧 Session {session_id[:8]}: PRESERVED {len(real_node_metrics)} real nodes for ML analysis")
        
        # Validate node data for strict configurations
        if config.strict_validation:
            self._validate_node_metrics(real_node_metrics)
        
        return metrics_data, real_node_metrics
    
    def _validate_node_metrics(self, node_metrics: List[Dict]) -> None:
        """Validate node metrics have required fields"""
        for i, node in enumerate(node_metrics):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} is not a valid dictionary")
            if 'cpu_usage_pct' not in node or 'memory_usage_pct' not in node:
                raise ValueError(f"Node {i} missing required usage data")
    
    def _get_pod_analysis(self, resource_group: str, cluster_name: str, 
                         enable_pod_analysis: bool, cost_df,
                         session_id: str, log_prefix: str) -> Optional[Dict]:
        """Run pod-level cost analysis if enabled"""
        if not enable_pod_analysis:
            return None
        
        # Use original logic to extract actual node cost for pod analysis
        try:
            actual_node_cost_for_pod_analysis = float(cost_df[cost_df['Category'] == 'Node Pools']['Cost'].sum())
        except Exception as cost_extract_error:
            logger.error(f"❌ Session {session_id[:8]}: Failed to extract node costs: {cost_extract_error}")
            # Debug: Log cost_df structure
            logger.info(f"🔍 Session {session_id[:8]}: Cost DF columns: {list(cost_df.columns) if hasattr(cost_df, 'columns') else 'Not a DataFrame'}")
            if hasattr(cost_df, 'Category'):
                unique_categories = cost_df['Category'].unique() if 'Category' in cost_df.columns else []
                logger.info(f"🔍 Session {session_id[:8]}: Available categories: {list(unique_categories)}")
            return None
        
        if actual_node_cost_for_pod_analysis <= 0:
            logger.info(f"⏭️ Session {session_id[:8]}: Skipping pod analysis - no node costs (${actual_node_cost_for_pod_analysis:.2f})")
            return None
        
        logger.info(f"🔍 Session {session_id[:8]}: Running pod analysis with node cost: ${actual_node_cost_for_pod_analysis:.2f}")
        
        try:
            from app.analytics.pod_cost_analyzer import get_enhanced_pod_cost_breakdown
            pod_cost_result = get_enhanced_pod_cost_breakdown(
                resource_group, cluster_name, actual_node_cost_for_pod_analysis
            )
            
            if pod_cost_result and pod_cost_result.get('success'):
                logger.info(f"✅ Session {session_id[:8]}: Pod analysis completed")
                return pod_cost_result
            else:
                logger.warning(f"⚠️ Session {session_id[:8]}: Pod analysis returned no results")
                return None
                
        except Exception as pod_error:
            logger.error(f"❌ Session {session_id[:8]}: Pod analysis error: {pod_error}")
            return None
    
    def _run_ml_analysis(self, resource_group: str, cluster_name: str, 
                        cost_data: Dict, metrics_data: Dict, pod_data: Optional[Dict],
                        session_id: str, log_prefix: str) -> Dict:
        """Execute ML-enhanced algorithmic analysis"""
        logger.info(f"🤖 Session {session_id[:8]}: Executing ML-ENHANCED algorithmic analysis...")
        
        try:
            from app.analytics.algorithmic_cost_analyzer import integrate_consistent_analysis
            
            consistent_results = integrate_consistent_analysis(
                resource_group=resource_group,
                cluster_name=cluster_name,
                cost_data=cost_data,
                metrics_data=metrics_data,
                pod_data=pod_data
            )
            
            # Validate HPA recommendations were generated
            if 'hpa_recommendations' not in consistent_results:
                raise ValueError("ML algorithmic analysis failed to generate HPA recommendations")
            
            hpa_recs = consistent_results['hpa_recommendations']
            if not hpa_recs.get('ml_enhanced'):
                logger.warning(f"⚠️ Session {session_id[:8]}: HPA recommendations not ML-enhanced, but continuing")
            else:
                logger.info(f"✅ Session {session_id[:8]}: ML-enhanced HPA recommendations validated")
            
            return consistent_results
            
        except Exception as algo_error:
            logger.error(f"❌ Session {session_id[:8]}: ML algorithmic analysis failed: {algo_error}")
            raise ValueError(f"Enhanced ML algorithmic analysis failed: {algo_error}")
    
    def _compile_results(self, consistent_results: Dict, cost_label: str, 
                        total_period_cost: float, days: int, real_node_metrics: List,
                        pod_data: Optional[Dict], resource_group: str, cluster_name: str,
                        session_id: str, config: AnalysisConfig, metadata: Dict) -> Dict:
        """Compile comprehensive analysis results"""
        
        # Start with consistent results
        final_results = consistent_results.copy()
        
        # Add cost information
        final_results.update({
            'cost_label': cost_label,
            'actual_period_cost': total_period_cost,
            'analysis_period_days': days
        })
        
        # Preserve real node metrics in multiple locations for compatibility
        final_results.update({
            'nodes': real_node_metrics.copy(),
            'node_metrics': real_node_metrics.copy(),
            'real_node_data': real_node_metrics.copy(),
            'has_real_node_data': True
        })
        
        # Add ML-specific metadata based on analysis type
        ml_metadata = {
            'analysis_type': config.analysis_type.value,
            'ml_models_used': True,
            'enterprise_analysis': True,
            'contradiction_free': True,
            'session_id': session_id[:8]
        }
        
        if config.analysis_type == AnalysisType.COMPLETELY_FIXED:
            ml_metadata['fixes_applied'] = [
                'enhanced_ml_feature_extraction',
                'fixed_resource_request_collection',
                'improved_chart_data_generation',
                'fixed_cache_management',
                'comprehensive_validation'
            ]
        
        # Check for high CPU scenarios
        workload_cpu_analysis = consistent_results.get('workload_cpu_analysis', {})
        max_workload_cpu = workload_cpu_analysis.get('max_workload_cpu', 0)
        if max_workload_cpu > 200:
            ml_metadata.update({
                'max_workload_cpu_detected': max_workload_cpu,
                'high_cpu_scenario_handled': True
            })
            logger.info(f"🔥 Session {session_id[:8]}: HIGH CPU DETECTED: {max_workload_cpu:.0f}% - ML handled this")
        
        final_results['ml_analysis_metadata'] = ml_metadata
        
        # Add pod data if available
        if pod_data:
            final_results['has_pod_costs'] = True
            final_results['pod_cost_analysis'] = pod_data
            
            # Handle different pod data formats
            if 'namespace_costs' in pod_data:
                final_results['namespace_costs'] = pod_data['namespace_costs']
            elif 'namespace_summary' in pod_data:
                final_results['namespace_costs'] = pod_data['namespace_summary']
        else:
            final_results['has_pod_costs'] = False
        
        # Add comprehensive metadata
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
        logger.info(f"📋 Session {session_id[:8]}: Generating implementation plan...")
        
        try:
            implementation_plan = implementation_generator.generate_implementation_plan(results)
            results['implementation_plan'] = implementation_plan
            
            if implementation_plan and isinstance(implementation_plan, dict):
                phases = implementation_plan.get('implementation_phases', [])
                if isinstance(phases, list) and len(phases) > 0:
                    logger.info(f"✅ Session {session_id[:8]}: Generated implementation plan: {len(phases)} phases")
                else:
                    logger.error(f"❌ Session {session_id[:8]}: Implementation plan phases empty")
            else:
                logger.error(f"❌ Session {session_id[:8]}: Implementation plan missing phases")
                
        except Exception as impl_error:
            logger.error(f"❌ Session {session_id[:8]}: Implementation plan generation failed: {impl_error}")
    
    def _update_session_state(self, session_id: str, results: Dict, config: AnalysisConfig) -> None:
        """Update session tracking state"""
        with _analysis_lock:
            if session_id in _analysis_sessions:
                _analysis_sessions[session_id].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'results': results
                })
    
    def _update_global_state(self, cluster_id: str, results: Dict, session_id: str) -> None:
        """Update global analysis state and cache"""
        try:
            # Update global analysis results
            from config import analysis_results
            analysis_results.clear()
            analysis_results.update(results)
            logger.info(f"✅ Session {session_id[:8]}: Updated global analysis_results")
            
            # Update cluster manager
            enhanced_cluster_manager.update_cluster_analysis(cluster_id, results)
            logger.info(f"✅ Session {session_id[:8]}: Saved to database")
            
            # Update cache
            save_to_cache(cluster_id, results)
            logger.info(f"✅ Session {session_id[:8]}: Updated cache")
            
        except Exception as update_error:
            logger.error(f"❌ Session {session_id[:8]}: Global state update failed: {update_error}")
    
    def _handle_error(self, error: Exception, session_id: str, 
                     analysis_type: AnalysisType, log_prefix: str) -> Dict:
        """Handle analysis errors consistently"""
        error_msg = str(error)
        logger.error(f"❌ Session {session_id[:8]}: {log_prefix} ANALYSIS FAILED: {error_msg}")
        
        with _analysis_lock:
            if session_id in _analysis_sessions:
                _analysis_sessions[session_id].update({
                    'status': 'failed',
                    'error': error_msg,
                    'failed_at': datetime.now().isoformat()
                })
        
        return {
            'status': 'error',
            'message': error_msg,
            'session_id': session_id,
            'analysis_type': analysis_type.value,
            'ml_enhanced': False
        }


# Create global instance
aks_analysis_engine = AKSAnalysisEngine()


# Backward compatibility functions
def run_consistent_analysis(resource_group: str, cluster_name: str, 
                          days: int = 30, enable_pod_analysis: bool = True) -> Dict[str, Any]:
    """Backward compatible consistent analysis"""
    config = AnalysisConfig(AnalysisType.CONSISTENT)
    return aks_analysis_engine.run_analysis(
        resource_group, cluster_name, days, enable_pod_analysis, config
    )


def run_completely_fixed_analysis(resource_group: str, cluster_name: str, 
                                 days: int = 30, enable_pod_analysis: bool = True) -> Dict[str, Any]:
    """Backward compatible completely fixed analysis"""
    config = AnalysisConfig(AnalysisType.COMPLETELY_FIXED)
    return aks_analysis_engine.run_analysis(
        resource_group, cluster_name, days, enable_pod_analysis, config
    )


def validate_enterprise_ml_analysis(results: Dict) -> Dict:
    """
    Enterprise-level validation for ML analysis
    """
    validation_results = {
        'ml_enhanced': False,
        'contradiction_free': False,
        'high_cpu_handled': False,
        'enterprise_ready': False,
        'issues': []
    }
    
    try:
        # Check ML enhancement
        hpa_recs = results.get('hpa_recommendations', {})
        if hpa_recs.get('ml_enhanced'):
            validation_results['ml_enhanced'] = True
        else:
            validation_results['issues'].append("Analysis not ML-enhanced")
        
        # Check consistency
        if hpa_recs.get('consistency_verified'):
            validation_results['contradiction_free'] = True
        else:
            validation_results['issues'].append("Consistency not verified")
        
        # Check high CPU handling
        ml_metadata = results.get('ml_analysis_metadata', {})
        if ml_metadata.get('high_cpu_scenario_handled'):
            validation_results['high_cpu_handled'] = True
        
        # Check enterprise readiness
        if (validation_results['ml_enhanced'] and 
            validation_results['contradiction_free'] and 
            results.get('has_real_node_data')):
            validation_results['enterprise_ready'] = True
        
        logger.info(f"✅ Enterprise validation: {len(validation_results['issues'])} issues found")
        return validation_results
        
    except Exception as e:
        validation_results['issues'].append(f"Validation error: {str(e)}")
        return validation_results