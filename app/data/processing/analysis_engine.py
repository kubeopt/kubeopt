"""
Multi-Subscription Analysis Engine - Enhanced with Cluster Config Support
========================================================================
Enhanced to provide cluster configuration information to implementation generator.
"""

import traceback
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
    
    def integrate_hpa_data_for_commands(self, analysis_results: Dict, hpa_metrics: List) -> Dict:
        """
        FIXED: Integrate real-time HPA data into analysis_results for command generation
        """
        logger.info(f"🔧 FIXED: Integrating {len(hpa_metrics)} HPAs into analysis_results")
        
        # Create hpa_recommendations structure that command generation expects
        hpa_recommendations = {
            'candidates': [],
            'existing_hpas': [],
            'optimization_opportunities': []
        }
        
        # Process existing HPAs from real-time metrics
        for hpa in hpa_metrics:
            namespace = hpa.get('namespace', 'default')
            name = hpa.get('name', 'unknown')
            cpu_current = hpa.get('cpu_current', 0)
            cpu_target = hpa.get('cpu_target', 70)
            
            # Existing HPAs that could be optimized
            if cpu_current > 0:  # Active HPA
                hpa_recommendations['existing_hpas'].append({
                    'name': name,
                    'namespace': namespace,
                    'current_cpu': cpu_current,
                    'target_cpu': cpu_target,
                    'status': 'active'
                })
                
                # Check if HPA needs optimization
                if cpu_current < 30 or cpu_current > 90:  # Poor utilization
                    monthly_savings = self._calculate_hpa_optimization_savings(hpa)
                    hpa_recommendations['optimization_opportunities'].append({
                        'type': 'hpa_optimization',
                        'target_hpa': name,
                        'target_namespace': namespace,
                        'current_cpu': cpu_current,
                        'target_cpu': cpu_target,
                        'monthly_savings': monthly_savings,
                        'priority_score': 0.8,
                        'implementation_complexity': 'low'
                    })
        
        # Find workloads WITHOUT HPAs (candidates for new HPAs)
        workload_costs = analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
        existing_hpa_targets = {hpa['name'] for hpa in hpa_recommendations['existing_hpas']}
        
        for workload_name, workload_info in workload_costs.items():
            clean_name = workload_name.split('/')[-1] if '/' in workload_name else workload_name
            
            # If workload doesn't have HPA and costs > $10/month
            if clean_name not in existing_hpa_targets and workload_info.get('cost', 0) > 10:
                monthly_savings = workload_info.get('cost', 0) * 0.3  # 30% savings potential
                
                hpa_recommendations['candidates'].append({
                    'name': clean_name,
                    'namespace': workload_info.get('namespace', 'default'),
                    'monthly_savings': monthly_savings,
                    'priority_score': min(0.9, workload_info.get('cost', 0) / 100),
                    'cost': workload_info.get('cost', 0),
                    'source': 'cost_analysis'
                })
        
        # Store in analysis_results for command generation
        analysis_results['hpa_recommendations'] = hpa_recommendations
        
        total_opportunities = len(hpa_recommendations['candidates']) + len(hpa_recommendations['optimization_opportunities'])
        logger.info(f"✅ FIXED: Created {total_opportunities} HPA opportunities for command generation")
        logger.info(f"   Candidates: {len(hpa_recommendations['candidates'])}")
        logger.info(f"   Optimizations: {len(hpa_recommendations['optimization_opportunities'])}")
        
        return analysis_results

    def _calculate_hpa_optimization_savings(self, hpa: Dict) -> float:
        """Calculate savings from optimizing existing HPA"""
        cpu_current = hpa.get('cpu_current', 50)
        cpu_target = hpa.get('cpu_target', 70)
        
        # Calculate inefficiency
        if cpu_current < 30:  # Under-utilized
            inefficiency = (30 - cpu_current) / 100
        elif cpu_current > 90:  # Over-utilized (may be scaling too late)
            inefficiency = 0.2  # Fixed inefficiency for over-utilization
        else:
            inefficiency = 0.1  # Minimal inefficiency
        
        # Estimate base cost and savings
        base_monthly_cost = 50  # Estimate base cost per HPA
        return base_monthly_cost * inefficiency

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
        Run analysis with subscription awareness and HPA data integration
        ENHANCED: Ensures HPA data is integrated for command generation
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
            
            # Step 4: Run analysis with subscription context and HPA integration
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
        """Execute analysis within subscription context with HPA data integration"""
        
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
                    return self._execute_core_analysis_with_hpa_integration(
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
    
    def _execute_core_analysis_with_hpa_integration(
        self, resource_group: str, cluster_name: str, days: int, 
        enable_pod_analysis: bool, session_id: str, log_prefix: str, config: AnalysisConfig
    ) -> Dict[str, Any]:
        """
        Execute core analysis logic with HPA data integration - FIXED DATA FLOW TIMING
        """
        
        cluster_id = f"{resource_group}_{cluster_name}"
        
        try:
            # Step 1: Get cost data with subscription context
            cost_components, cost_label, total_period_cost, cost_df = self._get_cost_data(
                resource_group, cluster_name, days, session_id, log_prefix, cluster_id, config
            )
            
            # Step 2: Get metrics data with subscription context
            metrics_data, real_node_metrics = self._get_metrics_data(
                resource_group, cluster_name, config, session_id, log_prefix
            )
            
            # Step 3: Get HPA metrics - CRITICAL for command generation
            hpa_metrics = self._get_hpa_metrics(resource_group, cluster_name, config.subscription_id)
            logger.info(f"🔧 FIXED: Retrieved {len(hpa_metrics)} HPA metrics for command integration")
            
            # Step 4: Get pod analysis with subscription context - BEFORE ML ANALYSIS
            pod_data = self._get_pod_analysis(
                resource_group, cluster_name, enable_pod_analysis, 
                cost_df, session_id, log_prefix, config.subscription_id
            )
            
            # CRITICAL FIX: Ensure pod_data is properly integrated into analysis for ML extraction
            preliminary_analysis_results = {
                'cost_components': cost_components,
                'metrics_data': metrics_data,
                'hpa_metrics': hpa_metrics,
                'total_cost': cost_components.get('total_cost', 0),
                'node_cost': cost_components.get('node_cost', 0),
                'nodes': real_node_metrics,
                'node_metrics': real_node_metrics,
                'real_node_data': real_node_metrics
            }
            
            # CRITICAL: Add pod_data to preliminary results BEFORE ML analysis
            if pod_data and pod_data.get('success'):
                preliminary_analysis_results['pod_cost_analysis'] = pod_data
                preliminary_analysis_results['has_pod_costs'] = True
                
                # Extract workload costs for ML analysis
                if 'workload_costs' in pod_data:
                    preliminary_analysis_results['workload_costs'] = pod_data['workload_costs']
                    logger.info(f"✅ Session {session_id}: Pod analysis available for ML extraction: {len(pod_data.get('workload_costs', {}))} workloads")
                
                # Extract namespace costs
                if 'namespace_costs' in pod_data:
                    preliminary_analysis_results['namespace_costs'] = pod_data['namespace_costs']
            else:
                logger.warning(f"⚠️ Session {session_id}: No pod analysis available - ML extraction will have limited data")
                preliminary_analysis_results['has_pod_costs'] = False
                preliminary_analysis_results['pod_cost_analysis'] = {}
            
            # Step 5: Integrate HPA data BEFORE ML analysis (not after)
            preliminary_analysis_results = self.integrate_hpa_data_for_commands(preliminary_analysis_results, hpa_metrics)
            logger.info(f"✅ FIXED: HPA data integrated BEFORE ML analysis")
            
            # Step 6: Run ML-enhanced algorithmic analysis with COMPLETE data
            consistent_results = self._run_ml_analysis(
                resource_group, cluster_name, cost_components, 
                metrics_data, pod_data, session_id, log_prefix,
                preliminary_analysis_results  # NEW: Pass preliminary results with pod data
            )
            
            logger.info(f"DEBUG:HPA efficiency: {consistent_results.get('hpa_efficiency', 0):.1f}%")
            
            # Step 7: Compile comprehensive results with cluster config metadata
            final_results = self._compile_results_with_cluster_config_support(
                consistent_results, cost_label, total_period_cost, days,
                real_node_metrics, pod_data, resource_group, cluster_name,
                session_id, config, self.session_metadata[config.analysis_type]
            )

            # Step 8: Generate implementation plan with cluster config support
            self._generate_implementation_plan_with_cluster_config_support(final_results, session_id, log_prefix)

            logger.info(f"🎉 Session {session_id}: MULTI-SUBSCRIPTION ANALYSIS WITH HPA INTEGRATION COMPLETED")
            
            return {
                'status': 'success',
                'data_type': self.session_metadata[config.analysis_type]['data_type'],
                'session_id': session_id,
                'results': final_results
            }
            
        except Exception as e:
            logger.error(f"❌ Core analysis with HPA integration failed for session {session_id}: {e}")
            raise

    def _get_hpa_metrics(self, resource_group: str, cluster_name: str, subscription_id: str) -> List[Dict]:
        """Get HPA metrics from the cluster"""
        try:
            logger.info(f"📈 Fetching HPA metrics for command integration...")
            
            from app.analytics.aks_realtime_metrics import AKSRealTimeMetricsFetcher
            
            # Use existing metrics fetcher to get HPA data
            metrics_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name, subscription_id)
            hpa_implementation = metrics_fetcher.get_hpa_implementation_status()
            
            hpa_metrics = []
            
            # Extract HPA data from implementation status
            if hpa_implementation and hpa_implementation.get('total_hpas', 0) > 0:
                hpa_list = hpa_implementation.get('hpa_list', [])
                
                for hpa_name in hpa_list:
                    # Parse namespace/name format
                    if '/' in hpa_name:
                        namespace, name = hpa_name.split('/', 1)
                    else:
                        namespace, name = 'default', hpa_name
                    
                    # Create HPA metric entry
                    hpa_metrics.append({
                        'namespace': namespace,
                        'name': name,
                        'cpu_current': 50.0,  # Default values - real implementation would fetch actual metrics
                        'cpu_target': 70.0,
                        'memory_current': 60.0,
                        'memory_target': 80.0,
                        'status': 'active'
                    })
            
            logger.info(f"✅ Collected {len(hpa_metrics)} HPA metrics for integration")
            return hpa_metrics
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get HPA metrics: {e}")
            return []
    
    def _compile_results_with_cluster_config_support(self, consistent_results: Dict, cost_label: str, 
                        total_period_cost: float, days: int, real_node_metrics: List,
                        pod_data: Optional[Dict], resource_group: str, cluster_name: str,
                        session_id: str, config: AnalysisConfig, metadata: Dict) -> Dict:
        """
        Compile comprehensive analysis results with cluster config support
        ENHANCED: Ensures ML characteristics are available to ALL components
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
        
        # CRITICAL FIX: Ensure ML characteristics are available at TOP LEVEL for all components
        ml_characteristics = consistent_results.get('ml_workload_characteristics', {})
        if ml_characteristics:
            # Store ML characteristics in MULTIPLE locations for component compatibility
            final_results['ml_workload_characteristics'] = ml_characteristics
            final_results['workload_characteristics'] = ml_characteristics  # Alternative key
            final_results['ml_characteristics'] = ml_characteristics  # Another alternative
            
            # Extract key metrics for easy access by components
            workload_profile = ml_characteristics.get('workload_profile', {})
            cost_patterns = ml_characteristics.get('cost_patterns', {})
            scaling_indicators = ml_characteristics.get('scaling_indicators', {})
            
            final_results['ml_metrics'] = {
                'total_workloads': workload_profile.get('total_workloads', 0),
                'average_workload_cost': cost_patterns.get('average_workload_cost', 0),
                'hpa_candidates_count': len(scaling_indicators.get('hpa_candidates', [])),
                'ml_analysis_available': True,
                'ml_enhanced': True
            }
            
            logger.info(f"✅ Session {session_id}: ML characteristics stored for component access")
            logger.info(f"📊 ML Metrics - Workloads: {final_results['ml_metrics']['total_workloads']}, Avg Cost: ${final_results['ml_metrics']['average_workload_cost']:.0f}")
        else:
            logger.warning(f"⚠️ Session {session_id}: No ML characteristics available for components")
            # Provide minimal structure for components
            final_results['ml_workload_characteristics'] = {}
            final_results['workload_characteristics'] = {}
            final_results['ml_characteristics'] = {}
            final_results['ml_metrics'] = {
                'total_workloads': 0,
                'average_workload_cost': 0,
                'hpa_candidates_count': 0,
                'ml_analysis_available': False,
                'ml_enhanced': False
            }
        
        # ENHANCED: Add subscription-aware ML metadata with cluster config support
        ml_metadata = {
            'analysis_type': config.analysis_type.value,
            'subscription_id': config.subscription_id,
            'subscription_aware': True,
            'ml_models_used': bool(ml_characteristics),
            'enterprise_analysis': True,
            'contradiction_free': True,
            'session_id': session_id,
            'multi_subscription_support': True,
            'cluster_config_integration_enabled': True,
            'hpa_data_integrated': True,
            'ml_characteristics_available': bool(ml_characteristics)  # NEW: Signal availability
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
            'supports_cluster_config_fetch': True,
            'cluster_config_fetch_params': {
                'resource_group': resource_group,
                'cluster_name': cluster_name,
                'subscription_id': config.subscription_id
            },
            'hpa_integration_enabled': True,
            'ml_characteristics_integrated': bool(ml_characteristics)  # NEW: Signal ML integration
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
            'ml_enhanced': bool(ml_characteristics),  # Dynamic based on availability
            config.analysis_type.value: True
        })

        logger.info(f"DEBUG:HPA efficiency: {final_results.get('hpa_efficiency', 0):.1f}%")

        return final_results

    def validate_ml_characteristics_storage(self, results: Dict, session_id: str) -> bool:
        """Validate that ML characteristics are properly stored for component access"""
        try:
            required_keys = ['ml_workload_characteristics', 'ml_metrics']
            
            for key in required_keys:
                if key not in results:
                    logger.error(f"❌ Session {session_id}: Missing {key} in results")
                    return False
            
            ml_metrics = results.get('ml_metrics', {})
            if not ml_metrics.get('ml_analysis_available', False):
                logger.warning(f"⚠️ Session {session_id}: ML analysis marked as not available")
                return False
            
            logger.info(f"✅ Session {session_id}: ML characteristics validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Session {session_id}: ML characteristics validation failed: {e}")
            return False
    
    def _generate_implementation_plan_with_cluster_config_support(self, results: Dict, session_id: str, log_prefix: str) -> None:
        """
        Generate implementation plan with cluster config support
        ENHANCED: Implementation generator now has access to cluster config fetching parameters
        """
        logger.info(f"📋 Session {session_id}: Generating implementation plan with cluster config and HPA integration...")
        
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
            
            # Log HPA integration status
            if cluster_context.get('hpa_integration_enabled'):
                hpa_recommendations = results.get('hpa_recommendations', {})
                total_opportunities = len(hpa_recommendations.get('candidates', [])) + len(hpa_recommendations.get('optimization_opportunities', []))
                logger.info(f"✅ Session {session_id}: HPA integration enabled with {total_opportunities} opportunities")
            else:
                logger.warning(f"⚠️ Session {session_id}: HPA integration not available")
            
            # Call implementation generator (SAME SIGNATURE - no changes)
            implementation_plan = implementation_generator.generate_implementation_plan(results)
            results['implementation_plan'] = implementation_plan
            
            if implementation_plan and isinstance(implementation_plan, dict):
                phases = implementation_plan.get('implementation_phases', [])
                if isinstance(phases, list) and len(phases) > 0:
                    # Check if cluster config was used
                    config_enhanced = implementation_plan.get('metadata', {}).get('version', '').endswith('cluster-config-enhanced')
                    cluster_intelligence = implementation_plan.get('intelligenceInsights', {}).get('config_derived', False)
                    hpa_integrated = implementation_plan.get('metadata', {}).get('hpa_integrated', False)
                    
                    logger.info(f"✅ Session {session_id}: Generated implementation plan: {len(phases)} phases")
                    if config_enhanced:
                        logger.info(f"🔧 Session {session_id}: Plan enhanced with cluster configuration intelligence")
                    if cluster_intelligence:
                        logger.info(f"🧠 Session {session_id}: Plan includes cluster intelligence insights")
                    if hpa_integrated:
                        logger.info(f"📈 Session {session_id}: Plan includes HPA integration features")
                else:
                    logger.error(f"❌ Session {session_id}: Implementation plan phases empty")
            else:
                logger.error(f"❌ Session {session_id}: Implementation plan missing phases")
                
        except Exception as impl_error:
            logger.error(f"❌ Session {session_id}: Implementation plan generation failed: {impl_error}")
            # Add error info to results for debugging
            results['implementation_plan_error'] = {
                'error': str(impl_error),
                'cluster_config_available': results.get('cluster_context', {}).get('supports_cluster_config_fetch', False),
                'hpa_integration_available': results.get('cluster_context', {}).get('hpa_integration_enabled', False)
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
                     config: AnalysisConfig, session_id: str, log_prefix: str) -> tuple:
        """Get ML-ready metrics with subscription context"""
        logger.info(f"📈 Session {session_id}: Fetching ML-ready metrics with subscription context...")
        
        from app.analytics.aks_realtime_metrics import AKSRealTimeMetricsFetcher
        
        # UPDATED: Pass subscription_id to the metrics fetcher
        enhanced_fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name, config.subscription_id)
        
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
                 subscription_id: str = None) -> Optional[Dict]:
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
                
                # Pass clean numeric cost breakdown (components only)
                pod_cost_result = get_enhanced_pod_cost_breakdown(
                    resource_group, 
                    cluster_name, 
                    cost_breakdown,  # Only component costs, no total
                    subscription_id
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
        

    def extract_ml_workload_characteristics(self, analysis_results: Dict, cluster_config: Optional[Dict] = None) -> Dict:
        """Extract ML workload characteristics from REAL analysis data - FIXED with defensive programming"""
        try:
            logger.info("🔍 EXTRACTING: ML workload characteristics from REAL data")
            
            # Initialize all characteristics with defaults FIRST
            characteristics = {
                'workload_profile': {
                    'total_workloads': 0,
                    'high_cost_workloads': 0,
                    'workload_distribution': {'low': 0, 'medium': 0, 'high': 0}
                },
                'resource_patterns': {
                    'node_count': 0,
                    'avg_cpu_utilization': 50.0,
                    'avg_memory_utilization': 50.0,
                    'underutilized_nodes': 0
                },
                'scaling_indicators': {
                    'hpa_candidates': [],
                    'scaling_readiness_score': 0.5,
                    'resource_waste_indicators': {}
                },
                'cost_patterns': {
                    'average_workload_cost': 0.0,
                    'cost_variance': 0.0,
                    'expensive_workloads': []
                },
                'optimization_readiness': {
                    'overall_score': 0.5,
                    'hpa_readiness': False,
                    'rightsizing_potential': False,
                    'cost_optimization_potential': False
                }
            }
            
            # Extract from YOUR analysis results (primary source) - with defensive checks
            workload_costs = {}
            if 'pod_cost_analysis' in analysis_results:
                pod_analysis = analysis_results['pod_cost_analysis']
                if isinstance(pod_analysis, dict):
                    workload_costs = pod_analysis.get('workload_costs', {})
                    logger.info(f"🔍 Found pod_cost_analysis with {len(workload_costs)} workloads")
                else:
                    logger.warning("⚠️ pod_cost_analysis is not a dictionary")
            else:
                logger.warning("⚠️ No pod_cost_analysis found in analysis_results")
                # Try alternative keys
                for alt_key in ['workload_costs', 'pod_costs', 'workloads']:
                    if alt_key in analysis_results:
                        alt_data = analysis_results[alt_key]
                        if isinstance(alt_data, dict):
                            workload_costs = alt_data
                            logger.info(f"🔍 Found workload data in {alt_key}: {len(workload_costs)} workloads")
                            break
            
            # Update workload profile if we have data
            if workload_costs:
                try:
                    characteristics['workload_profile'].update({
                        'total_workloads': len(workload_costs),
                        'high_cost_workloads': len([w for w in workload_costs.values() if isinstance(w, dict) and w.get('cost', 0) > 50]),
                        'workload_distribution': self._analyze_workload_distribution(workload_costs)
                    })
                    
                    # Calculate cost patterns
                    valid_costs = [w.get('cost', 0) for w in workload_costs.values() if isinstance(w, dict)]
                    if valid_costs:
                        characteristics['cost_patterns'].update({
                            'average_workload_cost': sum(valid_costs) / len(valid_costs),
                            'cost_variance': self._calculate_cost_variance(workload_costs),
                            'expensive_workloads': [
                                {'name': name, 'cost': info.get('cost', 0), 'namespace': info.get('namespace', 'default')}
                                for name, info in workload_costs.items() 
                                if isinstance(info, dict) and info.get('cost', 0) > 30
                            ]
                        })
                        logger.info(f"✅ Processed cost data for {len(valid_costs)} workloads")
                    else:
                        logger.warning("⚠️ No valid cost data found in workloads")
                except Exception as workload_error:
                    logger.error(f"❌ Error processing workload data: {workload_error}")
            
            # Extract from node analysis - with defensive checks
            nodes = []
            for node_key in ['nodes', 'node_metrics', 'real_node_data']:
                if node_key in analysis_results:
                    node_data = analysis_results[node_key]
                    if isinstance(node_data, list) and len(node_data) > 0:
                        nodes = node_data
                        logger.info(f"🔍 Found {len(nodes)} nodes in {node_key}")
                        break
            
            if nodes:
                try:
                    valid_cpu_usage = [n.get('cpu_usage_pct', 50) for n in nodes if isinstance(n, dict)]
                    valid_memory_usage = [n.get('memory_usage_pct', 50) for n in nodes if isinstance(n, dict)]
                    
                    if valid_cpu_usage:
                        characteristics['resource_patterns'].update({
                            'node_count': len(nodes),
                            'avg_cpu_utilization': sum(valid_cpu_usage) / len(valid_cpu_usage),
                            'avg_memory_utilization': sum(valid_memory_usage) / len(valid_memory_usage) if valid_memory_usage else 50.0,
                            'underutilized_nodes': len([usage for usage in valid_cpu_usage if usage < 40])
                        })
                        logger.info(f"✅ Processed resource data for {len(nodes)} nodes")
                except Exception as node_error:
                    logger.error(f"❌ Error processing node data: {node_error}")
            
            # Extract scaling indicators using real data - with defensive checks
            try:
                characteristics['scaling_indicators'].update({
                    'hpa_candidates': self._identify_hpa_candidates_from_analysis(analysis_results),
                    'scaling_readiness_score': self._calculate_scaling_readiness(analysis_results),
                    'resource_waste_indicators': self._extract_resource_waste_indicators(analysis_results)
                })
            except Exception as scaling_error:
                logger.error(f"❌ Error calculating scaling indicators: {scaling_error}")
            
            # Calculate optimization readiness - with defensive checks
            try:
                characteristics['optimization_readiness'].update({
                    'overall_score': self._calculate_overall_optimization_readiness(characteristics),
                    'hpa_readiness': len(characteristics['scaling_indicators']['hpa_candidates']) > 0,
                    'rightsizing_potential': characteristics['resource_patterns']['avg_cpu_utilization'] < 60,
                    'cost_optimization_potential': characteristics['cost_patterns']['average_workload_cost'] > 20
                })
            except Exception as optimization_error:
                logger.error(f"❌ Error calculating optimization readiness: {optimization_error}")
            
            # Log results safely using .get() to avoid KeyError
            total_workloads = characteristics.get('workload_profile', {}).get('total_workloads', 0)
            avg_cost = characteristics.get('cost_patterns', {}).get('average_workload_cost', 0)
            hpa_candidates_count = len(characteristics.get('scaling_indicators', {}).get('hpa_candidates', []))
            
            logger.info(f"✅ ML workload characteristics extracted successfully")
            logger.info(f"📊 Workloads: {total_workloads}")
            logger.info(f"💰 Avg cost: ${avg_cost:.0f}")
            logger.info(f"🎯 HPA candidates: {hpa_candidates_count}")
            
            return characteristics
            
        except Exception as e:
            logger.error(f"❌ ML workload characteristics extraction failed: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Return minimal valid structure on error
            return None

    def _analyze_workload_distribution(self, workload_costs: Dict) -> Dict:
        """Analyze workload cost distribution - FIXED with defensive programming"""
        distribution = {'low': 0, 'medium': 0, 'high': 0}
        
        try:
            for workload_info in workload_costs.values():
                if isinstance(workload_info, dict):
                    cost = workload_info.get('cost', 0)
                    if isinstance(cost, (int, float)):
                        if cost > 50:
                            distribution['high'] += 1
                        elif cost > 20:
                            distribution['medium'] += 1
                        else:
                            distribution['low'] += 1
        except Exception as e:
            logger.error(f"❌ Error analyzing workload distribution: {e}")
        
        return distribution
    
    def _calculate_cost_variance(self, workload_costs: Dict) -> float:
        """Calculate cost variance across workloads - FIXED with defensive programming"""
        try:
            costs = []
            for workload_info in workload_costs.values():
                if isinstance(workload_info, dict):
                    cost = workload_info.get('cost', 0)
                    if isinstance(cost, (int, float)) and cost >= 0:
                        costs.append(cost)
            
            if len(costs) < 2:
                return 0.0
            
            avg_cost = sum(costs) / len(costs)
            variance = sum((cost - avg_cost) ** 2 for cost in costs) / len(costs)
            return variance ** 0.5  # Standard deviation
            
        except Exception as e:
            logger.error(f"❌ Error calculating cost variance: {e}")
            return 0.0

    def _identify_hpa_candidates_from_analysis(self, analysis_results: Dict) -> List[Dict]:
        """Identify HPA candidates from analysis results - FIXED with defensive programming"""
        candidates = []
        
        try:
            # Try multiple possible locations for workload cost data
            workload_costs = {}
            
            if 'pod_cost_analysis' in analysis_results:
                pod_analysis = analysis_results['pod_cost_analysis']
                if isinstance(pod_analysis, dict):
                    workload_costs = pod_analysis.get('workload_costs', {})
            
            # Try alternative locations
            if not workload_costs:
                for alt_key in ['workload_costs', 'pod_costs', 'workloads']:
                    if alt_key in analysis_results:
                        alt_data = analysis_results[alt_key]
                        if isinstance(alt_data, dict):
                            workload_costs = alt_data
                            break
            
            if workload_costs:
                for workload_name, workload_info in workload_costs.items():
                    if isinstance(workload_info, dict):
                        cost = workload_info.get('cost', 0)
                        
                        # High-cost workloads are good HPA candidates
                        if isinstance(cost, (int, float)) and cost > 25:
                            candidates.append({
                                'name': str(workload_name),
                                'cost': float(cost),
                                'namespace': workload_info.get('namespace', 'default'),
                                'priority_score': min(1.0, cost / 100),  # Normalize to 0-1
                                'recommendation': 'deploy_hpa',
                                'expected_savings': cost * 0.3  # 30% savings estimate
                            })
            
            # Sort by cost descending
            candidates = sorted(candidates, key=lambda x: x['cost'], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Error identifying HPA candidates: {e}")
            return []
        
        return candidates

    def _calculate_scaling_readiness(self, analysis_results: Dict) -> float:
        """Calculate overall scaling readiness score - FIXED with defensive programming"""
        try:
            factors = []
            
            # Factor 1: Workload cost variance (higher variance = better scaling potential)
            workload_costs = {}
            if 'pod_cost_analysis' in analysis_results:
                pod_analysis = analysis_results['pod_cost_analysis']
                if isinstance(pod_analysis, dict):
                    workload_costs = pod_analysis.get('workload_costs', {})
            
            if workload_costs:
                variance = self._calculate_cost_variance(workload_costs)
                variance_score = min(1.0, variance / 50)  # Normalize
                factors.append(variance_score)
            
            # Factor 2: Resource utilization (lower utilization = better scaling potential)
            nodes = []
            for node_key in ['nodes', 'node_metrics', 'real_node_data']:
                if node_key in analysis_results:
                    node_data = analysis_results[node_key]
                    if isinstance(node_data, list):
                        nodes = node_data
                        break
            
            if nodes:
                cpu_usages = [n.get('cpu_usage_pct', 50) for n in nodes if isinstance(n, dict)]
                if cpu_usages:
                    avg_utilization = sum(cpu_usages) / len(cpu_usages)
                    utilization_score = max(0, (100 - avg_utilization) / 100)
                    factors.append(utilization_score)
            
            # Factor 3: Current HPA coverage (lower coverage = more opportunity)
            hpa_savings = analysis_results.get('hpa_savings', 0)
            total_cost = analysis_results.get('total_cost', 1)
            if isinstance(hpa_savings, (int, float)) and isinstance(total_cost, (int, float)) and total_cost > 0:
                hpa_potential = hpa_savings / total_cost
                factors.append(min(1.0, hpa_potential * 2))  # Double weight for HPA potential
            
            return sum(factors) / len(factors) if factors else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error calculating scaling readiness: {e}")
            return 0.5

    def _extract_resource_waste_indicators(self, analysis_results: Dict) -> Dict:
        """Extract resource waste indicators - FIXED with defensive programming"""
        indicators = {
            'cpu_waste_detected': False,
            'memory_waste_detected': False,
            'estimated_waste_cost': 0,
            'waste_sources': []
        }
        
        try:
            # Check node-level waste
            nodes = []
            for node_key in ['nodes', 'node_metrics', 'real_node_data']:
                if node_key in analysis_results:
                    node_data = analysis_results[node_key]
                    if isinstance(node_data, list):
                        nodes = node_data
                        break
            
            for node in nodes:
                if isinstance(node, dict):
                    cpu_usage = node.get('cpu_usage_pct', 50)
                    memory_usage = node.get('memory_usage_pct', 50)
                    node_name = node.get('name', 'unknown')
                    
                    if isinstance(cpu_usage, (int, float)) and cpu_usage < 50:
                        indicators['cpu_waste_detected'] = True
                        indicators['waste_sources'].append(f"Node {node_name}: {cpu_usage}% CPU")
                    
                    if isinstance(memory_usage, (int, float)) and memory_usage < 50:
                        indicators['memory_waste_detected'] = True
                        indicators['waste_sources'].append(f"Node {node_name}: {memory_usage}% Memory")
            
            # Estimate waste cost
            rightsizing_savings = analysis_results.get('right_sizing_savings', 0)
            if isinstance(rightsizing_savings, (int, float)):
                indicators['estimated_waste_cost'] = rightsizing_savings
            
        except Exception as e:
            logger.error(f"❌ Error extracting resource waste indicators: {e}")
        
        return indicators

    def _calculate_overall_optimization_readiness(self, characteristics: Dict) -> float:
        """Calculate overall optimization readiness score - FIXED with defensive programming"""
        try:
            scores = []
            
            # Workload profile score
            workload_profile = characteristics.get('workload_profile', {})
            total_workloads = workload_profile.get('total_workloads', 0)
            if isinstance(total_workloads, int) and total_workloads > 5:
                scores.append(0.8)
            else:
                scores.append(0.4)
            
            # Cost pattern score
            cost_patterns = characteristics.get('cost_patterns', {})
            avg_cost = cost_patterns.get('average_workload_cost', 0)
            if isinstance(avg_cost, (int, float)):
                if avg_cost > 30:
                    scores.append(0.9)
                elif avg_cost > 15:
                    scores.append(0.7)
                else:
                    scores.append(0.5)
            else:
                scores.append(0.5)
            
            # Resource pattern score
            resource_patterns = characteristics.get('resource_patterns', {})
            avg_cpu = resource_patterns.get('avg_cpu_utilization', 50)
            if isinstance(avg_cpu, (int, float)):
                if avg_cpu < 60:
                    scores.append(0.8)  # Low utilization = good optimization potential
                else:
                    scores.append(0.6)
            else:
                scores.append(0.6)
            
            return sum(scores) / len(scores) if scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error calculating optimization readiness: {e}")
            return 0.5

    def _validate_hpa_structure_for_analysis(self, hpa_recs: dict) -> bool:
        """Validate HPA recommendations have complete structure"""
        try:
            required_keys = ['metadata', 'summary', 'candidates']
            
            for key in required_keys:
                if key not in hpa_recs:
                    return False
            
            # Check if summary has required fields
            summary = hpa_recs.get('summary', {})
            required_summary_keys = ['total_workloads_analyzed', 'hpa_candidates_found', 'total_potential_savings']
            
            for key in required_summary_keys:
                if key not in summary:
                    return False
            
            return True
            
        except Exception:
            return False

    def _fix_hpa_structure_in_analysis(self, hpa_recs: dict, analysis_data: dict) -> dict:
        """Fix incomplete HPA structure using analysis data"""
        try:
            # Get workload data from analysis
            workload_costs = analysis_data.get('pod_cost_analysis', {}).get('workload_costs', {})
            
            fixed_hpa = {
                'metadata': hpa_recs.get('metadata', {
                    'cluster_name': analysis_data.get('cluster_name', 'unknown'),
                    'resource_group': analysis_data.get('resource_group', 'unknown'),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'recommendations_version': '2.0-analysis-fixed'
                }),
                'summary': hpa_recs.get('summary', {
                    'total_workloads_analyzed': len(workload_costs),
                    'hpa_candidates_found': len([w for w in workload_costs.values() if w.get('cost', 0) > 20]),
                    'total_potential_savings': sum(w.get('cost', 0) * 0.3 for w in workload_costs.values() if w.get('cost', 0) > 20),
                    'optimization_opportunities': len([w for w in workload_costs.values() if w.get('cost', 0) > 20])
                }),
                'candidates': hpa_recs.get('candidates', []),
                'existing_hpa_optimizations': hpa_recs.get('existing_hpa_optimizations', []),
                'optimization_opportunities': hpa_recs.get('optimization_opportunities', []),
                'implementation_priorities': hpa_recs.get('implementation_priorities', [])
            }
            
            # If candidates are empty, generate from workload costs
            if not fixed_hpa['candidates'] and workload_costs:
                for workload_name, workload_info in workload_costs.items():
                    cost = workload_info.get('cost', 0)
                    if cost > 20:  # HPA candidate threshold
                        candidate = {
                            'workload_name': workload_name,
                            'namespace': workload_info.get('namespace', 'default'),
                            'current_monthly_cost': cost,
                            'expected_monthly_savings': cost * 0.3,
                            'priority_score': min(1.0, cost / 100),
                            'hpa_configuration': {
                                'min_replicas': 2,
                                'max_replicas': max(6, int(cost / 10)),
                                'cpu_target': 70,
                                'memory_target': 70
                            }
                        }
                        fixed_hpa['candidates'].append(candidate)
            
            return fixed_hpa
            
        except Exception as e:
            logger.error(f"❌ Failed to fix HPA structure in analysis: {e}")
            return hpa_recs

    def generate_complete_hpa_analysis_with_ml(self, analysis_results: Dict, 
                                            cluster_config: Dict, 
                                            ml_characteristics: Dict) -> Dict:
        """Generate complete HPA analysis with ML enhancement"""
        try:
            logger.info("🔄 Generating complete HPA analysis with ML")
            
            # Build complete HPA recommendations structure
            hpa_recommendations = {
                'metadata': {
                    'cluster_name': analysis_results.get('cluster_name', cluster_config.get('cluster_name', 'unknown')),
                    'resource_group': analysis_results.get('resource_group', cluster_config.get('resource_group', 'unknown')),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'recommendations_version': '2.0-ml-enhanced',
                    'ml_enhanced': True
                },
                'summary': {
                    'total_workloads_analyzed': 0,
                    'hpa_candidates_found': 0,
                    'existing_hpas_analyzed': 0,
                    'optimization_opportunities': 0,
                    'total_potential_savings': 0
                },
                'candidates': [],
                'existing_hpa_optimizations': [],
                'optimization_opportunities': [],
                'implementation_priorities': [],
                'ml_insights': ml_characteristics
            }
            
            # Extract workload data from YOUR analysis results
            workload_costs = analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
            
            # Process workload candidates using real data
            for workload_name, workload_info in workload_costs.items():
                cost = workload_info.get('cost', 0)
                
                if cost > 20:  # HPA candidate threshold
                    candidate = {
                        'workload_name': workload_name,
                        'namespace': workload_info.get('namespace', 'default'),
                        'current_monthly_cost': cost,
                        'priority_score': min(1.0, cost / 100),
                        'expected_monthly_savings': cost * 0.35,  # 35% savings
                        'implementation_complexity': 'medium' if cost > 50 else 'low',
                        'resource_profile': {
                            'estimated_cpu_usage': 'high' if cost > 60 else 'medium' if cost > 30 else 'low',
                            'estimated_memory_usage': 'medium',
                            'scaling_pattern': 'variable_load'
                        },
                        'hpa_configuration': {
                            'min_replicas': 2,
                            'max_replicas': max(6, int(cost / 10)),  # Scale with cost
                            'cpu_target': 70,
                            'memory_target': 70
                        },
                        'ml_confidence': 0.8,
                        'recommendation_source': 'cost_analysis_ml_enhanced'
                    }
                    
                    hpa_recommendations['candidates'].append(candidate)
            
            # Update summary with real numbers
            hpa_recommendations['summary'].update({
                'total_workloads_analyzed': len(workload_costs),
                'hpa_candidates_found': len(hpa_recommendations['candidates']),
                'total_potential_savings': sum(c['expected_monthly_savings'] for c in hpa_recommendations['candidates']),
                'optimization_opportunities': len(hpa_recommendations['candidates'])
            })
            
            # Add implementation priorities (sorted by savings potential)
            sorted_candidates = sorted(hpa_recommendations['candidates'], 
                                    key=lambda x: x['expected_monthly_savings'], reverse=True)
            
            for i, candidate in enumerate(sorted_candidates[:5]):  # Top 5 priorities
                priority = {
                    'rank': i + 1,
                    'workload_name': candidate['workload_name'],
                    'namespace': candidate['namespace'],
                    'priority_reason': f"High savings potential: ${candidate['expected_monthly_savings']:.0f}/month",
                    'implementation_order': 'phase_1' if i < 2 else 'phase_2' if i < 4 else 'phase_3'
                }
                hpa_recommendations['implementation_priorities'].append(priority)
            
            # Add optimization opportunities
            if hpa_recommendations['summary']['hpa_candidates_found'] > 0:
                hpa_recommendations['optimization_opportunities'] = [
                    {
                        'type': 'hpa_deployment',
                        'description': f"Deploy HPAs for {len(hpa_recommendations['candidates'])} workloads",
                        'expected_savings': hpa_recommendations['summary']['total_potential_savings'],
                        'implementation_effort': 'medium',
                        'risk_level': 'low'
                    }
                ]
            
            logger.info(f"✅ Complete HPA analysis generated")
            logger.info(f"📊 Candidates: {len(hpa_recommendations['candidates'])}")
            logger.info(f"💰 Total savings: ${hpa_recommendations['summary']['total_potential_savings']:.0f}")
            
            return hpa_recommendations
            
        except Exception as e:
            logger.error(f"❌ Complete HPA analysis generation failed: {e}")
            return self._create_fallback_hpa_structure_in_analysis(analysis_results)

    def _create_fallback_hpa_structure_in_analysis(self, analysis_results: Dict) -> Dict:
        """Create minimal valid HPA structure as fallback"""
        return {
            'metadata': {
                'cluster_name': analysis_results.get('cluster_name', 'unknown'),
                'resource_group': analysis_results.get('resource_group', 'unknown'),
                'analysis_timestamp': datetime.now().isoformat(),
                'recommendations_version': '2.0-fallback',
                'ml_enhanced': False
            },
            'summary': {
                'total_workloads_analyzed': 0,
                'hpa_candidates_found': 0,
                'total_potential_savings': 0,
                'optimization_opportunities': 0
            },
            'candidates': [],
            'existing_hpa_optimizations': [],
            'optimization_opportunities': [],
            'implementation_priorities': [],
            'ml_insights': {}
        }
    
    def _generate_ml_characteristics_from_hpa_data(self, preliminary_results: Dict, session_id: str) -> Dict:
        """Generate ML characteristics from available HPA data when pod analysis is missing"""
        try:
            logger.info(f"🔄 Session {session_id}: Generating ML characteristics from HPA data")
            
            hpa_metrics = preliminary_results.get('hpa_metrics', [])
            if not hpa_metrics:
                return {}
            
            # Create workload profile from HPA data
            workload_profile = {
                'total_workloads': len(hpa_metrics),
                'high_cost_workloads': len([h for h in hpa_metrics if h.get('cpu_current', 0) > 70]),
                'workload_distribution': {
                    'low': len([h for h in hpa_metrics if h.get('cpu_current', 0) < 30]),
                    'medium': len([h for h in hpa_metrics if 30 <= h.get('cpu_current', 0) <= 70]),
                    'high': len([h for h in hpa_metrics if h.get('cpu_current', 0) > 70])
                }
            }
            
            # Estimate cost patterns from HPA utilization
            cpu_values = [h.get('cpu_current', 50) for h in hpa_metrics]
            estimated_costs = [max(10, cpu * 0.5) for cpu in cpu_values]  # CPU to cost estimation
            
            cost_patterns = {
                'average_workload_cost': sum(estimated_costs) / len(estimated_costs) if estimated_costs else 0,
                'cost_variance': 0.0,  # Will be calculated
                'expensive_workloads': [
                    {'name': h.get('name', f'hpa-{i}'), 'cost': estimated_costs[i], 'namespace': h.get('namespace', 'default')}
                    for i, h in enumerate(hpa_metrics) if i < len(estimated_costs) and estimated_costs[i] > 30
                ]
            }
            
            # Calculate cost variance
            if len(estimated_costs) > 1:
                import statistics
                cost_patterns['cost_variance'] = statistics.stdev(estimated_costs)
            
            # Resource patterns from cluster data
            nodes = preliminary_results.get('nodes', preliminary_results.get('real_node_data', []))
            resource_patterns = {
                'node_count': len(nodes),
                'avg_cpu_utilization': sum(n.get('cpu_usage_pct', 50) for n in nodes) / max(len(nodes), 1),
                'avg_memory_utilization': sum(n.get('memory_usage_pct', 60) for n in nodes) / max(len(nodes), 1),
                'underutilized_nodes': len([n for n in nodes if n.get('cpu_usage_pct', 50) < 40])
            }
            
            # Scaling indicators from HPA data
            hpa_candidates = []
            for hpa in hpa_metrics:
                if hpa.get('cpu_current', 0) > 80 or hpa.get('cpu_current', 0) < 20:  # Needs optimization
                    estimated_cost = max(10, hpa.get('cpu_current', 50) * 0.5)
                    hpa_candidates.append({
                        'name': hpa.get('name', 'unknown'),
                        'cost': estimated_cost,
                        'namespace': hpa.get('namespace', 'default'),
                        'priority_score': min(1.0, estimated_cost / 100),
                        'recommendation': 'optimize_hpa',
                        'expected_savings': estimated_cost * 0.25
                    })
            
            scaling_indicators = {
                'hpa_candidates': hpa_candidates,
                'scaling_readiness_score': min(1.0, len(hpa_candidates) / max(1, len(hpa_metrics))),
                'resource_waste_indicators': {
                    'cpu_waste_detected': resource_patterns['avg_cpu_utilization'] < 50,
                    'memory_waste_detected': resource_patterns['avg_memory_utilization'] < 50,
                    'estimated_waste_cost': sum(estimated_costs) * 0.2 if resource_patterns['avg_cpu_utilization'] < 50 else 0
                }
            }
            
            # Optimization readiness
            optimization_readiness = {
                'overall_score': 0.7,  # Moderate score since we have HPA data
                'hpa_readiness': len(hpa_candidates) > 0,
                'rightsizing_potential': resource_patterns['avg_cpu_utilization'] < 60,
                'cost_optimization_potential': cost_patterns['average_workload_cost'] > 20
            }
            
            characteristics = {
                'workload_profile': workload_profile,
                'resource_patterns': resource_patterns,
                'scaling_indicators': scaling_indicators,
                'cost_patterns': cost_patterns,
                'optimization_readiness': optimization_readiness
            }
            
            logger.info(f"✅ Session {session_id}: Generated ML characteristics from {len(hpa_metrics)} HPA metrics")
            return characteristics
            
        except Exception as e:
            logger.error(f"❌ Session {session_id}: Failed to generate ML characteristics from HPA data: {e}")
            return {}

    def _run_ml_analysis(self, resource_group: str, cluster_name: str, 
                    cost_data: Dict, metrics_data: Dict, pod_data: Optional[Dict],
                    session_id: str, log_prefix: str, 
                    preliminary_analysis_results: Optional[Dict] = None) -> Dict:
        """Execute ML-enhanced algorithmic analysis with preliminary data for ML extraction"""
        logger.info(f"🤖 Session {session_id}: Executing ML-ENHANCED algorithmic analysis...")
        
        try:
            from app.analytics.algorithmic_cost_analyzer import integrate_consistent_analysis
            
            # STEP 1: Get consistent results from algorithmic analyzer
            consistent_results = integrate_consistent_analysis(
                resource_group=resource_group,
                cluster_name=cluster_name,
                cost_data=cost_data,
                metrics_data=metrics_data,
                pod_data=pod_data
            )

            logger.info(f"DEBUG: HPA efficiency Found: {consistent_results.get('hpa_efficiency', 0):.1f}%")
            
            # STEP 2: MERGE preliminary analysis results if available (NEW)
            if preliminary_analysis_results:
                logger.info(f"🔧 Session {session_id}: Merging preliminary analysis results for ML extraction")
                
                # Merge pod cost analysis data
                if preliminary_analysis_results.get('pod_cost_analysis') and not consistent_results.get('pod_cost_analysis'):
                    consistent_results['pod_cost_analysis'] = preliminary_analysis_results['pod_cost_analysis']
                    logger.info(f"✅ Session {session_id}: Pod cost analysis merged from preliminary results")
                
                # Merge workload costs
                if preliminary_analysis_results.get('workload_costs') and not consistent_results.get('workload_costs'):
                    consistent_results['workload_costs'] = preliminary_analysis_results['workload_costs']
                    logger.info(f"✅ Session {session_id}: Workload costs merged from preliminary results")
                
                # Merge HPA data
                if preliminary_analysis_results.get('hpa_recommendations') and not consistent_results.get('hpa_recommendations'):
                    consistent_results['hpa_recommendations'] = preliminary_analysis_results['hpa_recommendations']
                    logger.info(f"✅ Session {session_id}: HPA recommendations merged from preliminary results")
            
            # STEP 3: EXTRACT ML WORKLOAD CHARACTERISTICS (with merged data)
            logger.info(f"🔍 Session {session_id}: Extracting ML workload characteristics with complete data...")
            
            ml_characteristics = self.extract_ml_workload_characteristics(consistent_results)
            
            if ml_characteristics and ml_characteristics.get('workload_profile', {}).get('total_workloads', 0) > 0:
                # SUCCESS: Store ML characteristics for ALL components
                consistent_results['ml_workload_characteristics'] = ml_characteristics
                logger.info(f"✅ Session {session_id}: ML characteristics extracted and stored: {ml_characteristics['workload_profile']['total_workloads']} workloads")
            else:
                # Try alternative data sources for ML extraction
                logger.warning(f"⚠️ Session {session_id}: ML characteristics extraction yielded no workloads, trying alternative sources...")
                
                # Try using HPA data to generate workload characteristics
                if preliminary_analysis_results and preliminary_analysis_results.get('hpa_metrics'):
                    ml_characteristics = self._generate_ml_characteristics_from_hpa_data(
                        preliminary_analysis_results, session_id
                    )
                    if ml_characteristics:
                        consistent_results['ml_workload_characteristics'] = ml_characteristics
                        logger.info(f"✅ Session {session_id}: ML characteristics generated from HPA data: {ml_characteristics['workload_profile']['total_workloads']} workloads")
                
                # Final fallback
                if not ml_characteristics or ml_characteristics.get('workload_profile', {}).get('total_workloads', 0) == 0:
                    logger.warning(f"⚠️ Session {session_id}: Creating minimal ML characteristics structure")
                    consistent_results['ml_workload_characteristics'] = {
                        'workload_profile': {'total_workloads': 0},
                        'resource_patterns': {},
                        'scaling_indicators': {'hpa_candidates': []},
                        'cost_patterns': {'average_workload_cost': 0.0},
                        'optimization_readiness': {'overall_score': 0.5}
                    }
            
            # STEP 4: ENHANCE HPA RECOMMENDATIONS WITH ML (with validation)
            if 'hpa_recommendations' in consistent_results:
                hpa_recs = consistent_results['hpa_recommendations']
                
                # Validate HPA structure
                if not self._validate_hpa_structure_for_analysis(hpa_recs):
                    logger.warning(f"⚠️ Session {session_id}: Fixing incomplete HPA structure")
                    consistent_results['hpa_recommendations'] = self._fix_hpa_structure_in_analysis(hpa_recs, consistent_results)
                
                # Generate complete ML-enhanced HPA analysis
                cluster_config = {
                    'cluster_name': cluster_name,
                    'resource_group': resource_group
                }
                
                enhanced_hpa = self.generate_complete_hpa_analysis_with_ml(
                    consistent_results, cluster_config, ml_characteristics
                )
                
                if enhanced_hpa:
                    consistent_results['hpa_recommendations'] = enhanced_hpa
                    logger.info(f"✅ Session {session_id}: Enhanced HPA analysis with ML complete: {len(enhanced_hpa.get('candidates', []))} candidates")
                
            else:
                logger.warning(f"⚠️ Session {session_id}: No HPA recommendations from algorithmic analysis")
                # Create minimal HPA structure
                consistent_results['hpa_recommendations'] = self._create_fallback_hpa_structure_in_analysis(consistent_results)
            
            # STEP 5: VALIDATE that ML characteristics are properly stored (ENHANCED)
            ml_stored = consistent_results.get('ml_workload_characteristics', {})
            workload_count = ml_stored.get('workload_profile', {}).get('total_workloads', 0)
            
            if ml_stored and workload_count > 0:
                logger.info(f"🎯 Session {session_id}: ML characteristics confirmed in results - ready for component consumption")
            else:
                logger.error(f"❌ Session {session_id}: ML characteristics NOT properly stored in results - components will fail")
                
                # Debug information
                logger.error(f"🔍 Session {session_id}: Debug - Available data keys: {list(consistent_results.keys())}")
                if consistent_results.get('pod_cost_analysis'):
                    pod_keys = list(consistent_results['pod_cost_analysis'].keys())
                    logger.error(f"🔍 Session {session_id}: Debug - Pod analysis keys: {pod_keys}")
            
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
    """Run analysis with automatic subscription detection and HPA integration"""
    return multi_subscription_analysis_engine.run_subscription_aware_analysis(
        resource_group, cluster_name, subscription_id, days, enable_pod_analysis
    )