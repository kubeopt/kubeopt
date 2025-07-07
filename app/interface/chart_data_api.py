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
        logger.info("📊  Chart data API called with enhanced validation")
        
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
    """ Comprehensive validation of chart data requirements"""
    
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
    """ENHANCED: Extract cost metrics including high CPU workload detection"""
    
    monthly_cost = ensure_float(current_analysis.get('total_cost', 0))
    monthly_savings = ensure_float(current_analysis.get('total_savings', 0))
    hpa_savings = ensure_float(current_analysis.get('hpa_savings', 0))
    
    # Extract HPA efficiency
    hpa_efficiency = 0.0
    hpa_recommendations = current_analysis.get('hpa_recommendations', {})
    
    efficiency_sources = [
        current_analysis.get('hpa_efficiency_percentage'),
        current_analysis.get('hpa_efficiency'),
        hpa_recommendations.get('hpa_efficiency_percentage'),
    ]
    
    for eff_val in efficiency_sources:
        if eff_val is not None and eff_val > 0:
            hpa_efficiency = ensure_float(eff_val)
            break
    
    if hpa_efficiency == 0.0 and hpa_savings > 0 and monthly_cost > 0:
        hpa_efficiency = min(50.0, (hpa_savings / monthly_cost) * 100)
    
    # NEW: Extract high CPU workload data
    high_cpu_workloads = []
    workload_cpu_data = {}
    
    if hpa_recommendations:
        ml_workload_characteristics = hpa_recommendations.get('workload_characteristics', {})
        
        # Extract high CPU workloads from ML analysis
        if 'high_cpu_workloads' in ml_workload_characteristics:
            high_cpu_workloads = ml_workload_characteristics['high_cpu_workloads']
        
        # Extract average CPU utilization
        avg_cpu_util = ml_workload_characteristics.get('cpu_utilization', 0)
        max_cpu_util = ml_workload_characteristics.get('max_cpu_utilization', avg_cpu_util)
        
        workload_cpu_data = {
            'average_cpu_utilization': avg_cpu_util,
            'max_cpu_utilization': max_cpu_util,
            'high_cpu_workloads': high_cpu_workloads,
            'total_workloads_analyzed': len(high_cpu_workloads) if high_cpu_workloads else 0
        }
    
    logger.info(f"📊 CPU Analysis: avg={workload_cpu_data.get('average_cpu_utilization', 0):.1f}%, "
               f"max={workload_cpu_data.get('max_cpu_utilization', 0):.1f}%, "
               f"high_cpu_workloads={len(high_cpu_workloads)}")
    
    # Get cost components
    cost_components = {
        'node_cost': ensure_float(current_analysis.get('node_cost', 0)),
        'storage_cost': ensure_float(current_analysis.get('storage_cost', 0)),
        'networking_cost': ensure_float(current_analysis.get('networking_cost', 0)),
        'control_plane_cost': ensure_float(current_analysis.get('control_plane_cost', 0)),
        'registry_cost': ensure_float(current_analysis.get('registry_cost', 0)),
        'other_cost': ensure_float(current_analysis.get('other_cost', 0))
    }
    
    return {
        'monthly_cost': monthly_cost,
        'monthly_savings': monthly_savings,
        'hpa_savings': hpa_savings,
        'hpa_efficiency': hpa_efficiency,
        'workload_cpu_data': workload_cpu_data,  # NEW: Include CPU workload data
        **cost_components
    }

def _build_enhanced_response_data(current_analysis: Dict[str, Any], 
                                cost_metrics: Dict[str, float], 
                                data_source: str, 
                                cluster_id: str) -> Dict[str, Any]:
    """ENHANCED: Build response data including high CPU workload alerts"""
    
    # Get CPU workload data from cost metrics
    workload_cpu_data = cost_metrics.get('workload_cpu_data', {})
    high_cpu_workloads = workload_cpu_data.get('high_cpu_workloads', [])
    
    # Existing response data structure
    response_data = {
        'status': 'success',
        'consistent_analysis': True,
        'data_source': data_source,
        'cluster_id': cluster_id,
        
        # Main metrics with CPU data
        'metrics': {
            'total_cost': cost_metrics['monthly_cost'],
            'total_savings': cost_metrics['monthly_savings'],
            'hpa_savings': cost_metrics.get('hpa_savings', 0),
            'hpa_efficiency': cost_metrics.get('hpa_efficiency', 0),
            'cpu_gap': ensure_float(current_analysis.get('cpu_gap', 0)),
            'memory_gap': ensure_float(current_analysis.get('memory_gap', 0)),
            # NEW: Add CPU workload metrics
            'average_cpu_utilization': workload_cpu_data.get('average_cpu_utilization', 0),
            'max_cpu_utilization': workload_cpu_data.get('max_cpu_utilization', 0),
            'high_cpu_workloads_count': len(high_cpu_workloads),
        },
        
        # Cost breakdown (existing)
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
        
        # NEW: High CPU workload alerts
        'highCpuWorkloads': {
            'workloads': high_cpu_workloads,
            'total_count': len(high_cpu_workloads),
            'requires_attention': len(high_cpu_workloads) > 0,
            'severity_level': _calculate_cpu_severity(high_cpu_workloads)
        },
        
        # Enhanced insights with CPU recommendations
        'insights': _generate_enhanced_insights(current_analysis, high_cpu_workloads),
        
        # Metadata
        'metadata': {
            'analysis_method': 'consistent_current_usage_optimization',
            'has_high_cpu_workloads': len(high_cpu_workloads) > 0,
            'cpu_analysis_available': True,
            'cluster_id': cluster_id,
            'data_source': data_source
        }
    }
    
    # Add charts with CPU workload data
    _add_charts_with_cpu_data(response_data, current_analysis, cluster_id, high_cpu_workloads)
    
    return response_data

def _calculate_cpu_severity(high_cpu_workloads: list) -> str:
    """Calculate severity level based on high CPU workloads"""
    if not high_cpu_workloads:
        return 'none'
    
    max_cpu = 0
    for workload in high_cpu_workloads:
        if isinstance(workload, dict):
            cpu_util = workload.get('cpu_utilization', 0)
        else:
            continue
        max_cpu = max(max_cpu, cpu_util)
    
    if max_cpu > 1000:  # 1000%+ 
        return 'critical'
    elif max_cpu > 500:  # 500%+
        return 'high'
    elif max_cpu > 200:  # 200%+
        return 'medium'
    else:
        return 'low'

def _generate_enhanced_insights(current_analysis: Dict, high_cpu_workloads: list) -> Dict:
    """Generate insights including high CPU workload recommendations"""
    
    # Get standard insights
    insights = generate_insights(current_analysis)
    
    # Add high CPU workload insights
    if high_cpu_workloads:
        cpu_insight = _generate_high_cpu_insight(high_cpu_workloads)
        insights['high_cpu_workloads'] = cpu_insight
    
    return insights

def _generate_high_cpu_insight(high_cpu_workloads: list) -> str:
    """Generate specific insight for high CPU workloads"""
    
    if not high_cpu_workloads:
        return ""
    
    workload_count = len(high_cpu_workloads)
    
    # Find the highest CPU workload
    max_cpu_workload = None
    max_cpu = 0
    
    for workload in high_cpu_workloads:
        if isinstance(workload, dict):
            cpu_util = workload.get('cpu_utilization', 0)
            if cpu_util > max_cpu:
                max_cpu = cpu_util
                max_cpu_workload = workload
    
    if max_cpu_workload:
        workload_name = max_cpu_workload.get('name', 'Unknown')
        namespace = max_cpu_workload.get('namespace', 'Unknown')
        target_cpu = max_cpu_workload.get('target', 80)
        
        if max_cpu > 1000:
            severity = "🚨 CRITICAL"
            action = "immediate application optimization"
        elif max_cpu > 500:
            severity = "⚠️ HIGH PRIORITY"
            action = "application review and optimization"
        else:
            severity = "💡 OPTIMIZATION OPPORTUNITY"
            action = "consider right-sizing"
        
        return (f"{severity}: Workload <strong>{workload_name}</strong> in namespace "
                f"<strong>{namespace}</strong> is running at <strong>{max_cpu:.0f}%</strong> CPU "
                f"(target: {target_cpu}%). Recommend {action} before implementing HPA scaling.")
    
    return f"🔍 Detected {workload_count} high CPU workload(s) requiring optimization attention."

def _add_charts_with_cpu_data(response_data: Dict, current_analysis: Dict, cluster_id: str, high_cpu_workloads: list):
    """Add charts including high CPU workload visualizations"""
    
    # Existing chart generation
    try:
        response_data['hpaComparison'] = generate_dynamic_hpa_comparison(current_analysis)
        
        # Enhance HPA chart with CPU workload data
        if response_data['hpaComparison'] and high_cpu_workloads:
            response_data['hpaComparison']['high_cpu_workloads'] = high_cpu_workloads
            response_data['hpaComparison']['has_high_cpu_alerts'] = True
            
        logger.info("✅ Generated HPA comparison chart with CPU workload data")
    except Exception as hpa_error:
        logger.error(f"❌ HPA comparison generation failed: {hpa_error}")
        response_data['hpaComparison'] = None
    
    # Add CPU workload chart if there are high CPU workloads
    if high_cpu_workloads:
        try:
            response_data['cpuWorkloadChart'] = _generate_cpu_workload_chart(high_cpu_workloads)
            logger.info("✅ Generated CPU workload chart")
        except Exception as cpu_error:
            logger.error(f"❌ CPU workload chart generation failed: {cpu_error}")
    
    # Continue with other charts...
    try:
        response_data['nodeUtilization'] = generate_node_utilization_data(current_analysis)
        logger.info("✅ Generated node utilization chart")
    except Exception as node_error:
        logger.error(f"❌ Node utilization generation failed: {node_error}")
        response_data['nodeUtilization'] = None

def _generate_cpu_workload_chart(high_cpu_workloads: list) -> Dict:
    """Generate chart data for high CPU workloads"""
    
    workload_names = []
    cpu_utilizations = []
    target_utilizations = []
    namespaces = []
    
    for workload in high_cpu_workloads[:10]:  # Top 10 high CPU workloads
        if isinstance(workload, dict):
            workload_names.append(workload.get('name', 'Unknown'))
            cpu_utilizations.append(workload.get('cpu_utilization', 0))
            target_utilizations.append(workload.get('target', 80))
            namespaces.append(workload.get('namespace', 'Unknown'))
    
    return {
        'labels': workload_names,
        'datasets': [
            {
                'label': 'Current CPU %',
                'data': cpu_utilizations,
                'backgroundColor': 'rgba(231, 76, 60, 0.7)',
                'borderColor': '#e74c3c',
                'borderWidth': 2
            },
            {
                'label': 'Target CPU %',
                'data': target_utilizations,
                'backgroundColor': 'rgba(46, 204, 113, 0.7)',
                'borderColor': '#2ecc71',
                'borderWidth': 2
            }
        ],
        'namespaces': namespaces,
        'chart_type': 'high_cpu_workloads',
        'requires_attention': True
    }

def _extract_hpa_implementation_safely(current_analysis: Dict) -> Dict:
    """ Safely extract HPA implementation data"""
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