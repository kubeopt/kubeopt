"""
Chart Data API Logic for AKS Cost Optimization
"""

import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify
from app.main.config import logger, enhanced_cluster_manager, _analysis_lock, _analysis_sessions
from app.services.cache_manager import load_from_cache, save_to_cache
from app.interface.chart_generator import (
    generate_insights, generate_dynamic_hpa_comparison, generate_node_utilization_data,
    generate_dynamic_trend_data, generate_pod_cost_data, generate_namespace_data, 
    generate_workload_data
)
from app.main.utils import ensure_float
from app.main.shared import _get_analysis_data

def chart_data_consistent():
    """COMPLETELY FIXED Chart data generation with proper error handling and validation"""
    try:
        logger.info("📊 FIXED: Chart data API called with enhanced validation")
        
        # Extract cluster ID with better error handling
        cluster_id = _extract_cluster_id()
        logger.info(f"📊 CHART DATA REQUEST: cluster_id={cluster_id}")
        
        if not cluster_id:
            return jsonify({
                'status': 'error',
                'message': 'No cluster ID provided. Please access this from a cluster dashboard.',
                'error_code': 'MISSING_CLUSTER_ID'
            }), 400
        
        # Get analysis data with session priority
        current_analysis, data_source = _get_analysis_data(cluster_id)
        logger.info(f"📊 CHART DATA SOURCE: {data_source}, has_data={bool(current_analysis)}")
        
        if not current_analysis:
            return jsonify({
                'status': 'no_data',
                'message': 'No analysis data available. Please run analysis first.',
                'cluster_id': cluster_id,
                'data_source': data_source,
                'action_required': 'run_analysis'
            }), 200
        
        # Validate required data components
        validation_error = _validate_chart_data_requirements(current_analysis, cluster_id)
        if validation_error:
            return validation_error
        
        # Extract and validate cost metrics
        try:
            cost_metrics = _extract_cost_metrics(current_analysis, data_source)
            logger.info(f"📊 COST METRICS: ${cost_metrics['monthly_cost']:.2f} cost, ${cost_metrics['monthly_savings']:.2f} savings")
        except Exception as cost_error:
            logger.error(f"❌ Cost metrics extraction failed: {cost_error}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid cost data: {cost_error}',
                'cluster_id': cluster_id
            }), 500
        
        # Build response data with comprehensive error handling
        try:
            response_data = _build_enhanced_response_data(current_analysis, cost_metrics, data_source, cluster_id)
            logger.info(f"✅ Chart data API completed successfully from {data_source}")
            return jsonify(response_data)
            
        except Exception as build_error:
            logger.error(f"❌ Response data building failed: {build_error}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to build chart data: {build_error}',
                'cluster_id': cluster_id,
                'data_source': data_source
            }), 500

    except Exception as e:
        logger.error(f"❌ Chart data API critical error: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Chart data API error: {str(e)}',
            'error_type': 'critical_error'
        }), 500

def _extract_cluster_id() -> Optional[str]:
    """Extract cluster ID from request context"""
    cluster_id = None
    
    # Check referrer header for cluster context
    referrer = request.headers.get('Referer', '')
    if '/cluster/' in referrer:
        try:
            cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
        except Exception:
            pass
    
    # Fallback to query parameter
    if not cluster_id:
        cluster_id = request.args.get('cluster_id')
    
    return cluster_id

# def _get_analysis_data(cluster_id: Optional[str]) -> Tuple[Optional[Dict[str, Any]], str]:
#     """HPA-aware analysis data loading with session priority"""
#     if not cluster_id:
#         logger.warning("⚠️ No cluster_id provided for analysis data")
#         return None, "no_cluster_id"

#     # PRIORITY 0: Check for fresh session data first (HIGHEST PRIORITY)
#     fresh_session_data = None
#     data_source = "none"
#     with _analysis_lock:
#         logger.info(f"🔍 CHART API: Checking {len(_analysis_sessions)} active sessions for cluster {cluster_id}")
#         for session_id, session_info in _analysis_sessions.items():
#             if (session_info.get('cluster_id') == cluster_id and 
#                 session_info.get('status') == 'completed' and 
#                 'results' in session_info):
#                 fresh_session_data = session_info['results']
#                 data_source = "fresh_session"
#                 logger.info(f"🎯 CHART API: Found fresh session data for {cluster_id} (session: {session_id[:8]})")
#                 break

#     if fresh_session_data:
#         # Validate HPA recommendations in fresh data
#         if 'hpa_recommendations' in fresh_session_data:
#             logger.info(f"✅ CHART API: Using fresh session data with HPA for {cluster_id}")
#             # Optionally update cache with fresh data
#             save_to_cache(cluster_id, fresh_session_data)
#             return fresh_session_data, "fresh_session"
#         else:
#             logger.warning(f"⚠️ CHART API: Fresh session data missing HPA for {cluster_id}")

#     # PRIORITY 1: Cluster-specific cache with HPA validation
#     try:
#         cached_data = load_from_cache(cluster_id)
#         if cached_data and cached_data.get('total_cost', 0) > 0:
#             # Validate HPA recommendations exist
#             if 'hpa_recommendations' in cached_data:
#                 logger.info(f"✅ CACHE: Complete data with HPA for {cluster_id} - ${cached_data.get('total_cost', 0):.2f}")
#                 return cached_data, "cluster_cache"
#             else:
#                 logger.warning(f"⚠️ CACHE: Data exists but missing HPA for {cluster_id}")
#                 # Clear incomplete cache
#                 from app.services.cache_manager import clear_analysis_cache
#                 clear_analysis_cache(cluster_id)
#     except Exception as e:
#         logger.warning(f"⚠️ Cluster cache fetch failed for {cluster_id}: {e}")

#     # PRIORITY 2: Database with HPA validation
#     try:
#         logger.info(f"🔄 Loading from database for cluster: {cluster_id}")
#         db_data = enhanced_cluster_manager.get_latest_analysis(cluster_id)
#         if db_data and db_data.get('total_cost', 0) > 0:
#             # Validate HPA recommendations in database data
#             if 'hpa_recommendations' in db_data:
#                 logger.info(f"✅ DATABASE: Complete data with HPA for {cluster_id} - ${db_data.get('total_cost', 0):.2f}")
#                 # Cache the complete database data
#                 save_to_cache(cluster_id, db_data)
#                 return db_data, "cluster_database"
#             else:
#                 logger.warning(f"⚠️ DATABASE: Data exists but missing HPA for {cluster_id}")
#     except Exception as e:
#         logger.error(f"❌ Database error for cluster {cluster_id}: {e}")

#     logger.warning(f"⚠️ No complete analysis data (with HPA) found for cluster: {cluster_id}")
#     return None, "no_complete_data"

def _validate_chart_data_requirements(current_analysis: Dict, cluster_id: str) -> Optional[tuple]:
    """FIXED: Comprehensive validation of chart data requirements"""
    
    # Check total cost
    total_cost = current_analysis.get('total_cost', 0)
    if not total_cost or total_cost <= 0:
        logger.warning(f"⚠️ Invalid total cost for {cluster_id}: {total_cost}")
        return jsonify({
            'status': 'invalid_data',
            'message': 'Invalid cost data - total cost is zero or missing',
            'cluster_id': cluster_id,
            'available_keys': list(current_analysis.keys()),
            'action_required': 'rerun_analysis'
        }), 200
    
    # Check for HPA recommendations (critical for charts)
    if 'hpa_recommendations' not in current_analysis:
        logger.error(f"❌ Missing HPA recommendations for {cluster_id}")
        return jsonify({
            'status': 'incomplete_data',
            'message': 'Analysis incomplete - missing HPA recommendations',
            'cluster_id': cluster_id,
            'action_required': 'rerun_analysis'
        }), 200
    
    # Validate HPA structure
    hpa_recs = current_analysis['hpa_recommendations']
    if not isinstance(hpa_recs, dict):
        logger.error(f"❌ Invalid HPA recommendations structure for {cluster_id}")
        return jsonify({
            'status': 'invalid_data',
            'message': 'Invalid HPA recommendations structure',
            'cluster_id': cluster_id
        }), 200
    
    # Check for node data (required for utilization charts)
    node_data = current_analysis.get('nodes') or current_analysis.get('node_metrics') or current_analysis.get('real_node_data')
    if not node_data or len(node_data) == 0:
        logger.warning(f"⚠️ No node data for {cluster_id}")
        return jsonify({
            'status': 'incomplete_data',
            'message': 'No node utilization data available',
            'cluster_id': cluster_id,
            'has_cost_data': True,
            'action_required': 'rerun_analysis'
        }), 200
    
    logger.info(f"✅ Chart data validation passed for {cluster_id}")
    return None

# ==============================================================================
# CORRECT APPROACH: Update your EXISTING functions in chart_data_api.py
# ==============================================================================

# 1. UPDATE your existing _extract_cost_metrics() function:
def _extract_cost_metrics(current_analysis: Dict[str, Any], data_source: str) -> Dict[str, float]:
    """FIXED: Extract and validate cost metrics including proper HPA efficiency"""
    
    monthly_cost = ensure_float(current_analysis.get('total_cost', 0))
    monthly_savings = ensure_float(current_analysis.get('total_savings', 0))
    
    # Extract HPA savings from ML analysis
    hpa_savings = ensure_float(current_analysis.get('hpa_savings', 0))
    
    # Also check ML-specific locations if not found
    if hpa_savings == 0:
        hpa_recommendations = current_analysis.get('hpa_recommendations', {})
        if hpa_recommendations:
            ml_workload_characteristics = hpa_recommendations.get('workload_characteristics', {})
            ml_optimization_analysis = ml_workload_characteristics.get('optimization_analysis', {})
            ml_cost_analysis = ml_optimization_analysis.get('cost_analysis', {})
            hpa_savings = ensure_float(ml_cost_analysis.get('potential_monthly_savings', 0))
    
    # CRITICAL FIX: Extract HPA efficiency from multiple sources
    hpa_efficiency = 0.0
    hpa_recommendations = current_analysis.get('hpa_recommendations', {})
    
    # Try multiple efficiency sources
    efficiency_sources = [
        current_analysis.get('hpa_efficiency_percentage'),
        current_analysis.get('hpa_efficiency'),
        current_analysis.get('hpa_reduction'),
        hpa_recommendations.get('hpa_efficiency_percentage'),
        hpa_recommendations.get('hpa_efficiency'),
    ]
    
    # Also check within ML workload characteristics
    if hpa_recommendations:
        ml_workload_characteristics = hpa_recommendations.get('workload_characteristics', {})
        efficiency_sources.extend([
            ml_workload_characteristics.get('hpa_efficiency_percentage'),
            ml_workload_characteristics.get('efficiency_score'),
        ])
    
    for eff_val in efficiency_sources:
        if eff_val is not None and eff_val > 0:
            hpa_efficiency = ensure_float(eff_val)
            logger.info(f"✅ Found HPA efficiency: {hpa_efficiency:.1f}%")
            break
    
    # If still zero, calculate from savings
    if hpa_efficiency == 0.0 and hpa_savings > 0 and monthly_cost > 0:
        hpa_efficiency = min(50.0, (hpa_savings / monthly_cost) * 100)
        logger.info(f"🔧 Calculated HPA efficiency from savings: {hpa_efficiency:.1f}%")
    
    logger.info(f"📊 Extracting metrics from {data_source}: cost=${monthly_cost:.2f}, "
               f"total_savings=${monthly_savings:.2f}, hpa_savings=${hpa_savings:.2f}, "
               f"hpa_efficiency={hpa_efficiency:.1f}%")
    
    # Get individual cost components
    cost_components = {
        'node_cost': ensure_float(current_analysis.get('node_cost', 0)),
        'storage_cost': ensure_float(current_analysis.get('storage_cost', 0)),
        'networking_cost': ensure_float(current_analysis.get('networking_cost', 0)),
        'control_plane_cost': ensure_float(current_analysis.get('control_plane_cost', 0)),
        'registry_cost': ensure_float(current_analysis.get('registry_cost', 0)),
        'other_cost': ensure_float(current_analysis.get('other_cost', 0))
    }
    
    # Validate and fix cost components if necessary
    component_total = sum(cost_components.values())
    if abs(component_total - monthly_cost) > (monthly_cost * 0.01):
        logger.warning(f"⚠️ Cost mismatch: components={component_total:.2f}, total={monthly_cost:.2f}")
        if component_total > 0:
            adjustment_factor = monthly_cost / component_total
            cost_components = {k: v * adjustment_factor for k, v in cost_components.items()}
            logger.info(f"✅ Applied adjustment factor: {adjustment_factor:.4f}")
    
    return {
        'monthly_cost': monthly_cost,
        'monthly_savings': monthly_savings,
        'hpa_savings': hpa_savings,
        'hpa_efficiency': hpa_efficiency,  # ADDED: Include HPA efficiency
        **cost_components
    }

def _build_enhanced_response_data(current_analysis: Dict[str, Any], 
                                cost_metrics: Dict[str, float], 
                                data_source: str, 
                                cluster_id: str) -> Dict[str, Any]:
    """Build comprehensive response data"""
    
    # Ensure node data is available in multiple locations for compatibility
    node_data = current_analysis.get('nodes') or current_analysis.get('node_metrics') or current_analysis.get('real_node_data') or []
    if node_data and 'node_metrics' not in current_analysis:
        current_analysis['node_metrics'] = node_data
    if node_data and 'nodes' not in current_analysis:
        current_analysis['nodes'] = node_data
    
    # Extract metadata safely
    actual_period_cost = ensure_float(current_analysis.get('actual_period_cost', cost_metrics['monthly_cost']))
    analysis_period_days = current_analysis.get('analysis_period_days', 30)
    
    # Build base response structure
    response_data = {
        'status': 'success',
        'consistent_analysis': True,
        'data_source': data_source,
        'cluster_id': cluster_id,
        
        # Main metrics with validation
        'metrics': {
            'total_cost': cost_metrics['monthly_cost'],
            'actual_period_cost': actual_period_cost,
            'analysis_period_days': analysis_period_days,
            'cost_label': current_analysis.get('cost_label', f'{analysis_period_days}-day baseline'),
            'total_savings': cost_metrics['monthly_savings'],
            'hpa_savings': cost_metrics.get('hpa_savings', 0),
            'right_sizing_savings': ensure_float(current_analysis.get('right_sizing_savings', 0)),
            'storage_savings': ensure_float(current_analysis.get('storage_savings', 0)),
            'savings_percentage': ensure_float(current_analysis.get('savings_percentage', 0)),
            'annual_savings': ensure_float(current_analysis.get('annual_savings', 0)),
            'hpa_efficiency': cost_metrics.get('hpa_efficiency', 0),
            'hpa_reduction': cost_metrics.get('hpa_efficiency', 0),
            'hpa_efficiency_percentage': cost_metrics.get('hpa_efficiency', 0),
            'cpu_gap': ensure_float(current_analysis.get('cpu_gap', 0)),
            'memory_gap': ensure_float(current_analysis.get('memory_gap', 0))
        },
        
        # Cost breakdown with validation
        'costBreakdown': {
            'labels': ['VM Scale Sets (Nodes)', 'Storage', 'Networking', 'AKS Control Plane', 'Container Registry', 'Other'],
            'values': [
                cost_metrics.get('node_cost', 0),
                cost_metrics.get('storage_cost', 0),
                cost_metrics.get('networking_cost', 0),
                cost_metrics.get('control_plane_cost', 0),
                cost_metrics.get('registry_cost', 0),
                cost_metrics.get('other_cost', 0)
            ]
        },
        
        # Savings breakdown
        'savingsBreakdown': {
            'categories': ['Memory-based HPA', 'Right-sizing', 'Storage Optimization'],
            'values': [
                cost_metrics.get('hpa_savings', 0),
                ensure_float(current_analysis.get('right_sizing_savings', 0)),
                ensure_float(current_analysis.get('storage_savings', 0))
            ]
        },
        
        # HPA implementation data
        'hpa_implementation': _extract_hpa_implementation_safely(current_analysis),
        
        # Enhanced insights
        'insights': generate_insights(current_analysis),
        
        # Metadata
        'metadata': {
            'analysis_method': 'consistent_current_usage_optimization',
            'is_consistent': True,
            'confidence': current_analysis.get('analysis_confidence', 0),
            'confidence_level': current_analysis.get('confidence_level', 'Medium'),
            'algorithms_used': current_analysis.get('algorithms_used', []),
            'resource_group': current_analysis.get('resource_group', ''),
            'cluster_name': current_analysis.get('cluster_name', ''),
            'timestamp': datetime.now().isoformat(),
            'data_source': data_source,
            'cluster_id': cluster_id,
            'has_real_node_data': current_analysis.get('has_real_node_data', False),
            'ml_enhanced': current_analysis.get('ml_enhanced', False)
        }
    }
    
    # Add charts with comprehensive error handling
    _add_charts_with_error_handling(response_data, current_analysis, cluster_id)    
    
    return response_data

def _extract_hpa_implementation_safely(current_analysis: Dict) -> Dict:
    """FIXED: Safely extract HPA implementation data"""
    try:
        hpa_recs = current_analysis.get('hpa_recommendations', {})
        current_impl = hpa_recs.get('current_implementation', {})
        opt_rec = hpa_recs.get('optimization_recommendation', {})
        
        return {
            'current_pattern': current_impl.get('pattern', 'unknown'),
            'detection_confidence': current_impl.get('confidence', 'low'),
            'total_hpas': current_impl.get('total_hpas', 0),
            'recommendation_direction': opt_rec.get('action', 'unknown'),
            'optimization_title': opt_rec.get('title', 'HPA Analysis'),
            'ml_enhanced': hpa_recs.get('ml_enhanced', False)
        }
    except Exception as e:
        logger.warning(f"⚠️ Error extracting HPA implementation: {e}")
        return {
            'current_pattern': 'unknown',
            'detection_confidence': 'low',
            'total_hpas': 0,
            'recommendation_direction': 'unknown',
            'optimization_title': 'HPA Analysis Failed',
            'ml_enhanced': False
        }

def _add_charts_with_error_handling(response_data: Dict, current_analysis: Dict, cluster_id: str):
    """UPDATED: Add charts with comprehensive error handling - ML INTEGRATED"""
    
    # HPA comparison chart - USING ML-INTEGRATED FUNCTION ✅
    try:
        response_data['hpaComparison'] = generate_dynamic_hpa_comparison(current_analysis)
        logger.info("✅ Generated HPA comparison chart with ML data")
        
        # Log the actual ML values being sent to frontend ✅
        hpa_chart = response_data['hpaComparison']
        if hpa_chart:
            logger.info(f"📊 HPA CHART DATA: savings=${hpa_chart.get('actual_hpa_savings', 0):.2f}, "
                       f"efficiency={hpa_chart.get('actual_hpa_efficiency', 0):.1f}%, "
                       f"ml_workload={hpa_chart.get('ml_workload_type', 'unknown')}, "
                       f"ml_confidence={hpa_chart.get('ml_confidence', 0):.2f}, "
                       f"real_ml_data={hpa_chart.get('real_ml_data', False)}")
        
    except Exception as hpa_error:
        logger.error(f"❌ HPA comparison generation failed: {hpa_error}")
        response_data['hpaComparison'] = None
    
    # Node utilization chart (existing logic unchanged)
    try:
        response_data['nodeUtilization'] = generate_node_utilization_data(current_analysis)
        logger.info("✅ Generated node utilization chart")
    except Exception as node_error:
        logger.error(f"❌ Node utilization generation failed: {node_error}")
        response_data['nodeUtilization'] = None
    
    # Trend data (existing logic unchanged)
    try:
        response_data['trendData'] = generate_dynamic_trend_data(cluster_id, current_analysis)
        logger.info("✅ Generated trend data")
    except Exception as trend_error:
        logger.warning(f"⚠️ Trend data generation failed: {trend_error}")
        response_data['trendData'] = {
            'labels': [],
            'datasets': [],
            'data_source': 'unavailable',
            'error': str(trend_error)
        }
    
    # Add pod cost data if available (existing logic unchanged)
    if current_analysis.get('has_pod_costs'):
        logger.info("✅ Pod cost data found, generating charts")
        try:
            _add_pod_cost_data(response_data, current_analysis)
        except Exception as pod_error:
            logger.warning(f"⚠️ Failed to add pod cost data: {pod_error}")

def _add_pod_cost_data(response_data: Dict[str, Any], current_analysis: Dict[str, Any]) -> None:
    """Add pod cost related data to response - FIXED to use current_analysis"""
    try:
        pod_data = generate_pod_cost_data(current_analysis)  # Pass current_analysis
        if pod_data:
            response_data['podCostBreakdown'] = pod_data
            logger.info("✅ Pod breakdown data added")
        
        namespace_data = generate_namespace_data(current_analysis)  # Pass current_analysis
        if namespace_data:
            response_data['namespaceDistribution'] = namespace_data
            logger.info("✅ Namespace distribution data added")
        
        workload_data = generate_workload_data(current_analysis)  # Pass current_analysis
        if workload_data:
            response_data['workloadCosts'] = workload_data
            logger.info("✅ Workload costs data added")
    except Exception as e:
        logger.warning(f"⚠️ Failed to add pod cost data: {e}")