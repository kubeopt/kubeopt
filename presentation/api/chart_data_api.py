#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Chart Data API Logic for AKS Cost Optimization
"""

import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify
from shared.config.config import logger, enhanced_cluster_manager, _analysis_lock, _analysis_sessions
from infrastructure.services.cache_manager import load_from_cache, save_to_cache
from presentation.api.chart_generator import (
    generate_insights, generate_dynamic_hpa_comparison, generate_node_utilization_data,
    generate_dynamic_trend_data, generate_pod_cost_data, generate_namespace_data, 
    generate_workload_data
)
from shared.utils.shared import ensure_float
from shared.utils.shared import _get_analysis_data

def chart_data_consistent():
    """Chart data generation with REAL data validation and NO FALLBACKS"""
    try:
        logger.info("📊 Chart data API called - REAL DATA ONLY")
        
        # Extract cluster ID with validation
        cluster_id = _extract_cluster_id()
        logger.info(f"📊 CHART DATA REQUEST: cluster_id={cluster_id}")
        
        if not cluster_id:
            return jsonify({
                'status': 'error',
                'message': 'No cluster ID provided. Please access this from a cluster dashboard.',
                'error_code': 'MISSING_CLUSTER_ID'
            }), 400
        
        # Get REAL analysis data - NO FALLBACKS
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
        
        # Validate REAL data requirements - STRICT VALIDATION
        validation_error = _validate_chart_data_requirements(current_analysis, cluster_id)
        if validation_error:
            return validation_error
        
        # Extract and validate REAL cost metrics
        try:
            cost_metrics = _extract_cost_metrics(current_analysis, data_source)
            logger.info(f"📊 REAL COST METRICS: ${cost_metrics['monthly_cost']:.2f} cost, ${cost_metrics['monthly_savings']:.2f} savings")
        except Exception as cost_error:
            logger.error(f"❌ Cost metrics extraction failed: {cost_error}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid cost data: {cost_error}',
                'cluster_id': cluster_id
            }), 500
        
        # Build response data with REAL data ONLY
        try:
            response_data = _build_enhanced_response_data(current_analysis, cost_metrics, data_source, cluster_id)
            logger.info(f"✅ Chart data API completed successfully from REAL {data_source}")
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

def _validate_chart_data_requirements(current_analysis: Dict, cluster_id: str) -> Optional[tuple]:
    """STRICT validation of REAL chart data requirements - NO COMPROMISES"""
    
    # Check total cost - MUST BE REAL AND POSITIVE
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
    
    # Check for REAL HPA recommendations (critical for charts)
    hpa_recommendations = current_analysis.get('hpa_recommendations')
    if not hpa_recommendations:
        logger.error(f"❌ Missing HPA recommendations for {cluster_id}")
        return jsonify({
            'status': 'incomplete_data',
            'message': 'Analysis incomplete - missing HPA recommendations',
            'cluster_id': cluster_id,
            'action_required': 'rerun_analysis'
        }), 200
    
    # Validate HPA structure - MUST BE REAL ML DATA
    if not isinstance(hpa_recommendations, dict):
        logger.error(f"❌ Invalid HPA recommendations structure for {cluster_id}")
        return jsonify({
            'status': 'invalid_data',
            'message': 'Invalid HPA recommendations structure',
            'cluster_id': cluster_id
        }), 200
    
    # Check for ML workload characteristics (required for REAL ML insights)
    workload_characteristics = hpa_recommendations.get('workload_characteristics')
    if not workload_characteristics:
        logger.error(f"❌ Missing ML workload characteristics for {cluster_id}")
        return jsonify({
            'status': 'incomplete_data',
            'message': 'Missing ML workload characteristics',
            'cluster_id': cluster_id,
            'action_required': 'rerun_analysis'
        }), 200
    
    # Check for REAL node data (required for utilization charts)
    has_real_node_data = current_analysis.get('has_real_node_data', False)
    if not has_real_node_data:
        logger.warning(f"⚠️ No real node data flag for {cluster_id}")
        return jsonify({
            'status': 'incomplete_data',
            'message': 'No real node utilization data available',
            'cluster_id': cluster_id,
            'has_cost_data': True,
            'action_required': 'rerun_analysis'
        }), 200
    
    node_data = current_analysis.get('real_node_data') or current_analysis.get('node_metrics') or current_analysis.get('nodes')
    if not node_data or len(node_data) == 0:
        logger.warning(f"⚠️ No node data for {cluster_id}")
        return jsonify({
            'status': 'incomplete_data',
            'message': 'No node utilization data available',
            'cluster_id': cluster_id,
            'has_cost_data': True,
            'action_required': 'rerun_analysis'
        }), 200
    
    logger.info(f"✅ STRICT chart data validation passed for {cluster_id}")
    return None

def _extract_cost_metrics(current_analysis: Dict[str, Any], data_source: str) -> Dict[str, float]:
    """Extract REAL cost metrics including high CPU workload detection"""
    
    monthly_cost = ensure_float(current_analysis.get('total_cost', 0))
    monthly_savings = ensure_float(current_analysis.get('total_savings', 0))
    # INTERNATIONAL STANDARDS-BASED: Use comprehensive 5-category framework
    core_savings = ensure_float(current_analysis.get('core_optimization_savings', 0))
    compute_savings = ensure_float(current_analysis.get('compute_optimization_savings', 0))
    infrastructure_savings = ensure_float(current_analysis.get('infrastructure_savings', 0))
    container_data_savings = ensure_float(current_analysis.get('container_data_savings', 0))
    security_monitoring_savings = ensure_float(current_analysis.get('security_monitoring_savings', 0))
    
    # Core optimization includes HPA, rightsizing, storage per CNCF standards
    optimization_efficiency = core_savings
    
    if monthly_cost <= 0:
        raise ValueError(f"Invalid monthly cost: {monthly_cost}")
    
    # Extract REAL HPA efficiency
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
    
    if hpa_efficiency == 0.0 and optimization_efficiency > 0 and monthly_cost > 0:
        hpa_efficiency = min(50.0, (optimization_efficiency / monthly_cost) * 100)
    
    # Extract high CPU workload data from consolidated structure ONLY
    high_cpu_summary = current_analysis.get('high_cpu_summary', {})
    if not high_cpu_summary:
        raise ValueError("Missing high_cpu_summary in consolidated analysis - system must provide this data")
    
    # DEBUG: Log the actual high_cpu_summary content
    logger.info(f"🔍 DEBUG HIGH_CPU_SUMMARY: type={type(high_cpu_summary)}, keys={list(high_cpu_summary.keys()) if isinstance(high_cpu_summary, dict) else 'Not dict'}")
    
    high_cpu_workloads = high_cpu_summary.get('high_cpu_workloads', [])
    high_cpu_hpas = high_cpu_summary.get('high_cpu_hpas', [])
    max_cpu_util = high_cpu_summary.get('max_cpu_utilization', 0)
    
    # DEBUG: Log what we extracted
    logger.info(f"🔍 DEBUG EXTRACTED: workloads={len(high_cpu_workloads)}, hpas={len(high_cpu_hpas)}, max_cpu={max_cpu_util}")
    if high_cpu_workloads:
        logger.info(f"🔍 DEBUG FIRST WORKLOAD: {high_cpu_workloads[0]}")
    
    # Combine HPA and workload high CPU data
    all_high_cpu = high_cpu_workloads + high_cpu_hpas
    
    workload_cpu_data = {
        'average_cpu_utilization': high_cpu_summary.get('average_cpu_utilization', 0),
        'max_cpu_utilization': max_cpu_util,
        'high_cpu_workloads': all_high_cpu,
        'total_workloads_analyzed': high_cpu_summary.get('total_high_cpu_count', len(all_high_cpu))
    }
    
    logger.info(f"📊 REAL CPU Analysis: avg={workload_cpu_data.get('average_cpu_utilization', 0):.1f}%, "
               f"max={workload_cpu_data.get('max_cpu_utilization', 0):.1f}%, "
               f"high_cpu_workloads={len(all_high_cpu)}")
    
    # Get REAL cost components
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
        'core_optimization_savings': core_savings,
        'compute_optimization_savings': compute_savings,
        'infrastructure_savings': infrastructure_savings,
        'container_data_savings': container_data_savings,
        'security_monitoring_savings': security_monitoring_savings,
        'hpa_efficiency': hpa_efficiency,
        'workload_cpu_data': workload_cpu_data,
        **cost_components
    }

def _build_enhanced_response_data(current_analysis: Dict[str, Any], 
                                cost_metrics: Dict[str, float], 
                                data_source: str, 
                                cluster_id: str) -> Dict[str, Any]:
    """Build response data from REAL analysis ONLY - NO SYNTHETIC DATA"""
    
    # Get REAL CPU workload data from cost metrics
    workload_cpu_data = cost_metrics.get('workload_cpu_data', {})
    high_cpu_workloads = workload_cpu_data.get('high_cpu_workloads', [])
    
    # Build response data with REAL data only
    response_data = {
        'status': 'success',
        'consistent_analysis': True,
        'data_source': data_source,
        'cluster_id': cluster_id,
        
        # REAL metrics
        'metrics': {
            'total_cost': cost_metrics['monthly_cost'],
            'total_savings': cost_metrics['monthly_savings'],
            'core_optimization_savings': cost_metrics.get('core_optimization_savings', 0),
            'hpa_efficiency': cost_metrics.get('hpa_efficiency', 0),
            'cpu_gap': ensure_float(current_analysis.get('cpu_gap', 0)),
            'memory_gap': ensure_float(current_analysis.get('memory_gap', 0)),
            'average_cpu_utilization': workload_cpu_data.get('average_cpu_utilization', 0),
            'max_cpu_utilization': workload_cpu_data.get('max_cpu_utilization', 0),
            'high_cpu_workloads_count': len(high_cpu_workloads),
        },
        
        # REAL cost breakdown
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
        
        # REAL high CPU workload alerts
        'highCpuWorkloads': {
            'workloads': high_cpu_workloads,
            'total_count': len(high_cpu_workloads),
            'requires_attention': len(high_cpu_workloads) > 0,
            'severity_level': _calculate_cpu_severity(high_cpu_workloads)
        },
        
        # REAL insights with CPU recommendations
        'insights': _generate_enhanced_insights(current_analysis, high_cpu_workloads),
        
        # Metadata
        'metadata': {
            'analysis_method': 'real_current_usage_optimization',
            'has_high_cpu_workloads': len(high_cpu_workloads) > 0,
            'cpu_analysis_available': True,
            'cluster_id': cluster_id,
            'data_source': data_source,
            'real_data_only': True
        }
    }
    
    # Add charts with REAL CPU workload data
    _add_charts_with_real_data(response_data, current_analysis, cluster_id, high_cpu_workloads)
    
    return response_data

def _calculate_cpu_severity(high_cpu_workloads: list) -> str:
    """Calculate severity level based on REAL high CPU workloads"""
    if not high_cpu_workloads:
        return 'none'
    
    max_cpu = 0
    for workload in high_cpu_workloads:
        if isinstance(workload, dict):
            cpu_util = workload.get('cpu_utilization', 0)
        else:
            continue
        max_cpu = max(max_cpu, cpu_util)
    
    if max_cpu > 1000:
        return 'critical'
    elif max_cpu > 500:
        return 'high'
    elif max_cpu > 200:
        return 'medium'
    else:
        return 'low'

def _generate_enhanced_insights(current_analysis: Dict, high_cpu_workloads: list) -> Dict:
    """Generate insights including REAL high CPU workload recommendations"""
    
    # Get REAL insights from chart generator
    insights = generate_insights(current_analysis)
    
    # Add REAL high CPU workload insights
    if high_cpu_workloads:
        cpu_insight = _generate_high_cpu_insight(high_cpu_workloads)
        insights['high_cpu_workloads'] = cpu_insight
    
    return insights

def _generate_high_cpu_insight(high_cpu_workloads: list) -> str:
    """Generate specific insight for REAL high CPU workloads"""
    
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

def _add_charts_with_real_data(response_data: Dict, current_analysis: Dict, cluster_id: str, high_cpu_workloads: list):
    """Add charts using REAL data ONLY - NO FALLBACKS"""
    
    # REAL HPA comparison chart
    try:
        response_data['hpaComparison'] = generate_dynamic_hpa_comparison(current_analysis)
        
        # Enhance HPA chart with REAL CPU workload data
        if response_data['hpaComparison'] and high_cpu_workloads:
            response_data['hpaComparison']['high_cpu_workloads'] = high_cpu_workloads
            response_data['hpaComparison']['has_high_cpu_alerts'] = True
            
        logger.info("✅ Generated REAL HPA comparison chart with CPU workload data")
    except Exception as hpa_error:
        logger.error(f"❌ HPA comparison generation failed: {hpa_error}")
        # Do not add chart if it fails - NO FALLBACKS
        response_data['hpaComparison'] = None
    
    # Add REAL CPU workload chart if there are high CPU workloads
    if high_cpu_workloads:
        try:
            response_data['cpuWorkloadChart'] = _generate_cpu_workload_chart(high_cpu_workloads)
            logger.info("✅ Generated REAL CPU workload chart")
        except Exception as cpu_error:
            logger.error(f"❌ CPU workload chart generation failed: {cpu_error}")
    
    # REAL node utilization chart
    try:
        response_data['nodeUtilization'] = generate_node_utilization_data(current_analysis)
        logger.info("✅ Generated REAL node utilization chart")
    except Exception as node_error:
        logger.error(f"❌ Node utilization generation failed: {node_error}")
        # Do not add chart if it fails - NO FALLBACKS
        response_data['nodeUtilization'] = None
    
    # REAL trend data
    try:
        response_data['trendData'] = generate_dynamic_trend_data(cluster_id, current_analysis)
        logger.info("✅ Generated REAL trend data")
    except Exception as trend_error:
        logger.warning(f"⚠️ Trend data generation failed: {trend_error}")
        # Do not add chart if it fails - NO FALLBACKS
        response_data['trendData'] = None
    
    # Add REAL pod cost data if available
    if current_analysis.get('has_pod_costs'):
        logger.info("✅ Pod cost data found, generating REAL charts")
        try:
            _add_pod_cost_data(response_data, current_analysis)
        except Exception as pod_error:
            logger.warning(f"⚠️ Failed to add pod cost data: {pod_error}")

def _generate_cpu_workload_chart(high_cpu_workloads: list) -> Dict:
    """Generate chart data for REAL high CPU workloads"""
    
    workload_names = []
    cpu_utilizations = []
    target_utilizations = []
    namespaces = []
    
    for workload in high_cpu_workloads[:10]:  # Top 10 high CPU workloads
        if isinstance(workload, dict):
            workload_names.append(workload.get('name', 'Unknown'))
            # Use the correct field names from the actual data structure
            cpu_util = workload.get('hpa_cpu_utilization', workload.get('cpu_utilization', 0))
            target_util = workload.get('hpa_cpu_target', workload.get('target', 80))
            cpu_utilizations.append(cpu_util)
            target_utilizations.append(target_util)
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
                'backgroundColor': 'rgba(30, 64, 175, 0.7)',
                'borderColor': '#1E40AF',
                'borderWidth': 2
            }
        ],
        'namespaces': namespaces,
        'chart_type': 'high_cpu_workloads',
        'requires_attention': True
    }

def _add_pod_cost_data(response_data: Dict[str, Any], current_analysis: Dict[str, Any]) -> None:
    """Add REAL pod cost related data to response"""
    try:
        pod_data = generate_pod_cost_data(current_analysis)
        if pod_data:
            response_data['podCostBreakdown'] = pod_data
            logger.info("✅ REAL Pod breakdown data added")
        
        namespace_data = generate_namespace_data(current_analysis)
        if namespace_data:
            response_data['namespaceDistribution'] = namespace_data
            logger.info("✅ REAL Namespace distribution data added")
        
        workload_data = generate_workload_data(current_analysis)
        if workload_data:
            response_data['workloadCosts'] = workload_data
            logger.info("✅ REAL Workload costs data added")
    except Exception as e:
        logger.warning(f"⚠️ Failed to add REAL pod cost data: {e}")
        raise