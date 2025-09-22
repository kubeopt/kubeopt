#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Enhanced Database and Cache Management Module - COMPLETE VERSION
==================================================================
Enhanced module for comprehensive database administration, analysis results management,
and implementation plan testing/validation.
"""

import json
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
import traceback
from typing import Dict, List, Optional, Any

# Import your existing components
try:
    from infrastructure.data.cluster_database import EnhancedClusterManager
    from alerts.enhanced_alerts_manager import EnhancedAlertsManager
except ImportError:
    # Fallback for development
    EnhancedClusterManager = None
    EnhancedAlertsManager = None

logger = logging.getLogger(__name__)

# Create Blueprint for database management
db_mgmt_bp = Blueprint('database_management', __name__, url_prefix='/api/db-mgmt')

# These will be set from the main app
enhanced_cluster_manager = None
alerts_manager = None
analysis_cache = None

def init_database_management(cluster_mgr, alert_mgr, cache):
    """Initialize the database management module with dependencies"""
    global enhanced_cluster_manager, alerts_manager, analysis_cache
    enhanced_cluster_manager = cluster_mgr
    alerts_manager = alert_mgr
    analysis_cache = cache
    logger.info("✅ Database management module initialized")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_cache_valid(cluster_id: str = None) -> bool:
    """Check if cache is valid for specific cluster"""
    if not cluster_id or not analysis_cache:
        return False
        
    if cluster_id not in analysis_cache.get('clusters', {}):
        return False
    
    cluster_cache = analysis_cache['clusters'][cluster_id]
    if not cluster_cache.get('timestamp'):
        return False
    
    try:
        from datetime import datetime, timedelta
        cache_time = datetime.fromisoformat(cluster_cache['timestamp'])
        expiry_time = cache_time + timedelta(hours=analysis_cache.get('global_ttl_hours', 1))
        return datetime.now() < expiry_time
    except Exception:
        return False

def clear_analysis_cache(cluster_id: str = None):
    """Clear analysis cache for specific cluster or all clusters"""
    if not analysis_cache:
        return
        
    if cluster_id:
        if cluster_id in analysis_cache.get('clusters', {}):
            del analysis_cache['clusters'][cluster_id]
            logger.info(f"🧹 Cleared cache for cluster: {cluster_id}")
    else:
        old_count = len(analysis_cache.get('clusters', {}))
        analysis_cache['clusters'] = {}
        logger.info(f"🧹 Cleared ALL cluster caches ({old_count} clusters)")

def validate_json_data(json_str: str) -> tuple:
    """Validate JSON data and return parsed result"""
    try:
        if not json_str:
            return False, "Empty JSON data"
        
        parsed_data = json.loads(json_str)
        return True, parsed_data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def test_implementation_plan_structure(plan: Dict) -> List[Dict]:
    """Test implementation plan structure and return test results"""
    tests = []
    
    # Test 1: Basic structure
    tests.append({
        'test_name': 'Basic Structure',
        'status': 'pass' if plan and isinstance(plan, dict) else 'fail',
        'details': 'Checks if plan is a valid dictionary object',
        'severity': 'critical'
    })
    
    # Test 2: Implementation phases
    phases = plan.get('implementation_phases', [])
    tests.append({
        'test_name': 'Implementation Phases',
        'status': 'pass' if phases and len(phases) > 0 else 'fail',
        'details': f'Found {len(phases)} implementation phases',
        'severity': 'critical'
    })
    
    # Test 3: Executive summary
    exec_summary = plan.get('executive_summary', {})
    tests.append({
        'test_name': 'Executive Summary',
        'status': 'pass' if exec_summary else 'warning',
        'details': 'Checks if executive summary exists',
        'severity': 'medium'
    })
    
    # Test 4: Phase structure validation
    if phases:
        valid_phases = 0
        for phase in phases:
            if (phase.get('title') and 
                phase.get('duration_weeks') and 
                phase.get('tasks')):
                valid_phases += 1
        
        tests.append({
            'test_name': 'Phase Structure',
            'status': 'pass' if valid_phases == len(phases) else 'warning',
            'details': f'{valid_phases}/{len(phases)} phases have complete structure',
            'severity': 'medium'
        })
    
    # Test 5: Timeline consistency
    timeline = plan.get('timeline_optimization', {})
    total_weeks = timeline.get('total_weeks')
    if phases and total_weeks:
        max_phase_week = max((phase.get('end_week', 0) for phase in phases), default=0)
        consistent = abs(total_weeks - max_phase_week) <= 1
        
        tests.append({
            'test_name': 'Timeline Consistency',
            'status': 'pass' if consistent else 'warning',
            'details': f'Total weeks: {total_weeks}, Max phase week: {max_phase_week}',
            'severity': 'low'
        })
    
    # Test 6: Savings projection
    opportunity = exec_summary.get('optimization_opportunity', {})
    projected_savings = opportunity.get('projected_monthly_savings', 0)
    tests.append({
        'test_name': 'Savings Projection',
        'status': 'pass' if projected_savings > 0 else 'warning',
        'details': f'Projected monthly savings: ${projected_savings:.2f}',
        'severity': 'medium'
    })
    
    # Test 7: Metadata validation
    metadata = plan.get('metadata', {})
    tests.append({
        'test_name': 'Metadata',
        'status': 'pass' if metadata.get('generation_method') else 'warning',
        'details': f'Generation method: {metadata.get("generation_method", "unknown")}',
        'severity': 'low'
    })
    
    return tests

def test_analysis_data_structure(analysis_data: Dict) -> List[Dict]:
    """Test analysis data structure and return test results"""
    tests = []
    
    # Test 1: Basic cost data
    tests.append({
        'test_name': 'Basic Cost Data',
        'status': 'pass' if analysis_data.get('total_cost') and analysis_data.get('total_savings') else 'fail',
        'details': f"Cost: ${analysis_data.get('total_cost', 0):.2f}, Savings: ${analysis_data.get('total_savings', 0):.2f}",
        'severity': 'critical'
    })
    
    # Test 2: HPA recommendations
    hpa_recs = analysis_data.get('hpa_recommendations')
    tests.append({
        'test_name': 'HPA Recommendations',
        'status': 'pass' if hpa_recs else 'warning',
        'details': 'Checks if HPA recommendations are present',
        'severity': 'medium'
    })
    
    # Test 3: Implementation plan
    impl_plan = analysis_data.get('implementation_plan')
    tests.append({
        'test_name': 'Implementation Plan',
        'status': 'pass' if impl_plan and impl_plan.get('implementation_phases') else 'warning',
        'details': f"Plan exists: {bool(impl_plan)}, Phases: {len(impl_plan.get('implementation_phases', [])) if impl_plan else 0}",
        'severity': 'medium'
    })
    
    # Test 4: Node data
    node_data = analysis_data.get('nodes') or analysis_data.get('real_node_data') or analysis_data.get('node_metrics')
    tests.append({
        'test_name': 'Node Data',
        'status': 'pass' if node_data else 'warning',
        'details': f"Node count: {len(node_data) if node_data else 0}",
        'severity': 'medium'
    })
    
    # Test 5: Cost breakdown
    cost_components = [
        analysis_data.get('node_cost', 0),
        analysis_data.get('storage_cost', 0),
        analysis_data.get('networking_cost', 0)
    ]
    has_breakdown = any(cost > 0 for cost in cost_components)
    
    tests.append({
        'test_name': 'Cost Breakdown',
        'status': 'pass' if has_breakdown else 'warning',
        'details': f"Node: ${cost_components[0]:.2f}, Storage: ${cost_components[1]:.2f}, Network: ${cost_components[2]:.2f}",
        'severity': 'low'
    })
    
    # Test 6: Savings calculation consistency
    hpa_savings = analysis_data.get('hpa_savings', 0)
    right_sizing_savings = analysis_data.get('right_sizing_savings', 0)
    storage_savings = analysis_data.get('storage_savings', 0)
    component_total = hpa_savings + right_sizing_savings + storage_savings
    total_savings = analysis_data.get('total_savings', 0)
    
    consistent = abs(component_total - total_savings) < 0.01
    tests.append({
        'test_name': 'Savings Consistency',
        'status': 'pass' if consistent else 'warning',
        'details': f"Components: ${component_total:.2f}, Total: ${total_savings:.2f}",
        'severity': 'medium'
    })
    
    # Test 7: Timestamps and metadata
    timestamp = analysis_data.get('analysis_timestamp')
    tests.append({
        'test_name': 'Metadata',
        'status': 'pass' if timestamp else 'warning',
        'details': f"Analysis timestamp: {timestamp or 'missing'}",
        'severity': 'low'
    })
    
    return tests

# ============================================================================
# EXISTING DATABASE ROUTES (Enhanced)
# ============================================================================

@db_mgmt_bp.route('/overview', methods=['GET'])
def api_overview_stats():
    """Get comprehensive overview statistics"""
    try:
        overview = {
            'database_stats': {},
            'cache_stats': {},
            'system_health': {},
            'analysis_stats': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Database statistics
        if enhanced_cluster_manager:
            try:
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    cursor = conn.execute('SELECT COUNT(*) FROM clusters')
                    cluster_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM clusters WHERE analysis_data IS NOT NULL')
                    analysis_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM alerts')
                    alert_count = cursor.fetchone()[0]
                    
                    # Get clusters with implementation plans
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM clusters 
                        WHERE analysis_data IS NOT NULL 
                        AND analysis_data LIKE '%implementation_plan%'
                    ''')
                    impl_plan_count = cursor.fetchone()[0]
                    
                    overview['database_stats'] = {
                        'total_clusters': cluster_count,
                        'total_analyses': analysis_count,
                        'total_alerts': alert_count,
                        'implementation_plans': impl_plan_count
                    }
                    
                    overview['analysis_stats'] = {
                        'clusters_with_analysis': analysis_count,
                        'clusters_with_plans': impl_plan_count,
                        'analysis_coverage': f"{(analysis_count/cluster_count*100):.1f}%" if cluster_count > 0 else "0%"
                    }
            except Exception as e:
                overview['database_stats'] = {'error': str(e)}
        
        # Cache statistics
        if analysis_cache:
            try:
                clusters = analysis_cache.get('clusters', {})
                valid_count = sum(1 for cid in clusters.keys() if is_cache_valid(cid))
                
                overview['cache_stats'] = {
                    'total_cached': len(clusters),
                    'valid_cached': valid_count,
                    'expired_cached': len(clusters) - valid_count
                }
            except Exception as e:
                overview['cache_stats'] = {'error': str(e)}
        
        # System health
        overview['system_health'] = {
            'cluster_manager_initialized': enhanced_cluster_manager is not None,
            'alerts_manager_initialized': alerts_manager is not None,
            'cache_system_initialized': analysis_cache is not None
        }
        
        return jsonify({
            'status': 'success',
            'overview': overview
        })
        
    except Exception as e:
        logger.error(f"Overview stats error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/health-check', methods=['GET'])
def api_database_health_check():
    """Comprehensive database health check"""
    try:
        health_status = {
            'overall_status': 'healthy',
            'checks': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Check main database
        try:
            if enhanced_cluster_manager:
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    cursor = conn.execute('SELECT COUNT(*) FROM clusters')
                    cluster_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM clusters WHERE analysis_data IS NOT NULL')
                    analysis_count = cursor.fetchone()[0]
                    
                    health_status['checks'].append({
                        'component': 'Main Database',
                        'status': 'healthy',
                        'details': f'{cluster_count} clusters, {analysis_count} with analysis data',
                        'path': enhanced_cluster_manager.db_path
                    })
            else:
                health_status['checks'].append({
                    'component': 'Main Database',
                    'status': 'error',
                    'details': 'Cluster manager not initialized'
                })
                health_status['overall_status'] = 'unhealthy'
        except Exception as e:
            health_status['checks'].append({
                'component': 'Main Database',
                'status': 'error',
                'details': str(e)
            })
            health_status['overall_status'] = 'unhealthy'
        
        # Check alerts database
        try:
            if alerts_manager and enhanced_cluster_manager:
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    cursor = conn.execute('SELECT COUNT(*) FROM alerts')
                    alert_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM alert_triggers')
                    trigger_count = cursor.fetchone()[0]
                    
                    health_status['checks'].append({
                        'component': 'Alerts Database',
                        'status': 'healthy',
                        'details': f'{alert_count} alerts, {trigger_count} triggers'
                    })
            else:
                health_status['checks'].append({
                    'component': 'Alerts Database',
                    'status': 'warning',
                    'details': 'Alerts manager not initialized'
                })
        except Exception as e:
            health_status['checks'].append({
                'component': 'Alerts Database',
                'status': 'error',
                'details': str(e)
            })
        
        # Check analysis data integrity
        try:
            if enhanced_cluster_manager:
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM clusters 
                        WHERE analysis_data IS NOT NULL 
                        AND analysis_data != ''
                        AND analysis_data != 'null'
                    ''')
                    valid_analysis_count = cursor.fetchone()[0]
                    
                    health_status['checks'].append({
                        'component': 'Analysis Data Integrity',
                        'status': 'healthy',
                        'details': f'{valid_analysis_count} clusters with valid analysis data'
                    })
        except Exception as e:
            health_status['checks'].append({
                'component': 'Analysis Data Integrity',
                'status': 'error',
                'details': str(e)
            })
        
        # Check cache status
        try:
            if analysis_cache:
                cache_clusters = len(analysis_cache.get('clusters', {}))
                health_status['checks'].append({
                    'component': 'Cache System',
                    'status': 'healthy',
                    'details': f'{cache_clusters} clusters cached'
                })
            else:
                health_status['checks'].append({
                    'component': 'Cache System',
                    'status': 'warning',
                    'details': 'Cache system not initialized'
                })
        except Exception as e:
            health_status['checks'].append({
                'component': 'Cache System',
                'status': 'error',
                'details': str(e)
            })
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'overall_status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@db_mgmt_bp.route('/clusters', methods=['GET'])
def api_get_clusters_detailed():
    """Get detailed cluster information for database viewer"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Cluster manager not initialized'
            }), 503
            
        # Get filters from query parameters
        status_filter = request.args.get('status')
        environment_filter = request.args.get('environment')
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT 
                    id, name, resource_group, environment, region, description,
                    status, created_at, last_analyzed, last_cost, last_savings,
                    last_confidence, analysis_count, analysis_status, 
                    analysis_progress, analysis_message, analysis_started_at,
                    auto_analyze_enabled, analysis_data
                FROM clusters 
                WHERE 1=1
            '''
            params = []
            
            if status_filter:
                query += ' AND status = ?'
                params.append(status_filter)
            
            if environment_filter:
                query += ' AND environment = ?'
                params.append(environment_filter)
            
            query += ' ORDER BY created_at DESC'
            
            cursor = conn.execute(query, params)
            clusters = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'status': 'success',
                'clusters': clusters,
                'total': len(clusters)
            })
            
    except Exception as e:
        logger.error(f"Error getting detailed clusters: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# ANALYSIS RESULTS MANAGEMENT ROUTES
# ============================================================================

@db_mgmt_bp.route('/analysis-results', methods=['GET'])
def api_get_analysis_results():
    """Get analysis results with enhanced filtering"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Cluster manager not initialized'
            }), 503
            
        cluster_id = request.args.get('cluster_id')
        days = request.args.get('days', type=int)
        has_implementation_plan = request.args.get('has_implementation_plan')
        has_hpa = request.args.get('has_hpa')
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT 
                    id, name, resource_group, environment,
                    last_analyzed, last_cost, last_savings, last_confidence,
                    analysis_status, analysis_data
                FROM clusters 
                WHERE analysis_data IS NOT NULL AND analysis_data != ''
            '''
            params = []
            
            if cluster_id:
                query += ' AND id = ?'
                params.append(cluster_id)
            
            if days:
                query += ' AND last_analyzed > datetime("now", "-{} days")'.format(days)
            
            if has_implementation_plan == 'true':
                query += ' AND analysis_data LIKE "%implementation_plan%"'
            elif has_implementation_plan == 'false':
                query += ' AND (analysis_data NOT LIKE "%implementation_plan%" OR analysis_data IS NULL)'
            
            if has_hpa == 'true':
                query += ' AND analysis_data LIKE "%hpa_recommendations%"'
            elif has_hpa == 'false':
                query += ' AND (analysis_data NOT LIKE "%hpa_recommendations%" OR analysis_data IS NULL)'
            
            query += ' ORDER BY last_analyzed DESC LIMIT 100'
            
            cursor = conn.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                cluster_data = dict(row)
                
                # Parse analysis data to extract summary info
                if cluster_data['analysis_data']:
                    try:
                        analysis_data = json.loads(cluster_data['analysis_data'])
                        cluster_data['has_hpa_recommendations'] = bool(analysis_data.get('hpa_recommendations'))
                        cluster_data['has_implementation_plan'] = bool(analysis_data.get('implementation_plan'))
                        cluster_data['has_real_node_data'] = bool(analysis_data.get('has_real_node_data', False))
                        cluster_data['ml_enhanced'] = bool(analysis_data.get('ml_enhanced', False))
                        
                        # Extract key metrics
                        cluster_data['analysis_summary'] = {
                            'total_cost': analysis_data.get('total_cost', 0),
                            'total_savings': analysis_data.get('total_savings', 0),
                            'hpa_savings': analysis_data.get('hpa_savings', 0),
                            'right_sizing_savings': analysis_data.get('right_sizing_savings', 0),
                            'storage_savings': analysis_data.get('storage_savings', 0)
                        }
                        
                        # Implementation plan summary
                        if analysis_data.get('implementation_plan'):
                            impl_plan = analysis_data['implementation_plan']
                            phases = impl_plan.get('implementation_phases', [])
                            cluster_data['implementation_summary'] = {
                                'phases_count': len(phases),
                                'estimated_weeks': impl_plan.get('timeline_optimization', {}).get('total_weeks'),
                                'complexity_level': impl_plan.get('executive_summary', {}).get('implementation_overview', {}).get('complexity_level'),
                                'risk_level': impl_plan.get('executive_summary', {}).get('implementation_overview', {}).get('risk_level')
                            }
                    except json.JSONDecodeError:
                        cluster_data['analysis_data_error'] = True
                
                results.append(cluster_data)
            
            return jsonify({
                'status': 'success',
                'results': results,
                'total': len(results)
            })
            
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/clusters/<cluster_id>/analysis-data', methods=['GET'])
def api_get_cluster_analysis_data(cluster_id):
    """Get complete analysis data for a specific cluster"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT analysis_data, name, resource_group, last_analyzed, last_cost, last_savings
                FROM clusters 
                WHERE id = ?
            ''', (cluster_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
            
            if not row['analysis_data']:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data found for this cluster'
                }), 404
            
            try:
                analysis_data = json.loads(row['analysis_data'])
                
                # Create summary of what's available in the analysis data
                data_summary = {
                    'has_implementation_plan': bool(analysis_data.get('implementation_plan')),
                    'has_hpa_recommendations': bool(analysis_data.get('hpa_recommendations')),
                    'has_nodes_data': bool(analysis_data.get('nodes')),
                    'has_pod_costs': bool(analysis_data.get('has_pod_costs')),
                    'total_cost': analysis_data.get('total_cost'),
                    'total_savings': analysis_data.get('total_savings'),
                    'analysis_timestamp': analysis_data.get('analysis_timestamp'),
                    'ml_enhanced': analysis_data.get('ml_enhanced', False),
                    'has_real_node_data': analysis_data.get('has_real_node_data', False)
                }
                
                # Add implementation plan summary if it exists
                if analysis_data.get('implementation_plan'):
                    impl_plan = analysis_data['implementation_plan']
                    data_summary['implementation_plan_summary'] = {
                        'phases_count': len(impl_plan.get('implementation_phases', [])),
                        'generation_method': impl_plan.get('metadata', {}).get('generation_method'),
                        'cluster_metadata': impl_plan.get('cluster_metadata'),
                        'executive_summary': impl_plan.get('executive_summary')
                    }
                
                response_data = {
                    'status': 'success',
                    'cluster_info': {
                        'id': cluster_id,
                        'name': row['name'],
                        'resource_group': row['resource_group'],
                        'last_analyzed': row['last_analyzed'],
                        'last_cost': row['last_cost'],
                        'last_savings': row['last_savings']
                    },
                    'data_summary': data_summary,
                    'analysis_data': analysis_data
                }
                
                return jsonify(response_data)
                
            except json.JSONDecodeError as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid JSON in analysis data: {str(e)}'
                }), 500
                
    except Exception as e:
        logger.error(f"Error getting analysis data for {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/clusters/<cluster_id>/test-analysis', methods=['POST'])
def api_test_analysis_data(cluster_id):
    """Test analysis data structure and validity"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT analysis_data, name, resource_group
                FROM clusters 
                WHERE id = ?
            ''', (cluster_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
            
            if not row['analysis_data']:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data to test'
                }), 404
            
            # Validate JSON
            is_valid, data_or_error = validate_json_data(row['analysis_data'])
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': f'JSON validation failed: {data_or_error}'
                }), 400
            
            # Run structure tests
            test_results = test_analysis_data_structure(data_or_error)
            
            # Calculate overall status
            critical_failures = [t for t in test_results if t['severity'] == 'critical' and t['status'] == 'fail']
            overall_status = 'fail' if critical_failures else 'pass'
            
            return jsonify({
                'status': 'success',
                'cluster_info': {
                    'id': cluster_id,
                    'name': row['name'],
                    'resource_group': row['resource_group']
                },
                'test_results': {
                    'overall_status': overall_status,
                    'tests_run': len(test_results),
                    'tests_passed': len([t for t in test_results if t['status'] == 'pass']),
                    'tests_failed': len([t for t in test_results if t['status'] == 'fail']),
                    'tests_warning': len([t for t in test_results if t['status'] == 'warning']),
                    'critical_failures': len(critical_failures),
                    'detailed_results': test_results
                }
            })
            
    except Exception as e:
        logger.error(f"Error testing analysis data for {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/clusters/<cluster_id>/clear-analysis', methods=['DELETE'])
def api_clear_analysis_data(cluster_id):
    """Clear analysis data for a specific cluster"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            cursor = conn.execute('''
                UPDATE clusters 
                SET analysis_data = NULL, 
                    last_cost = 0, 
                    last_savings = 0, 
                    last_confidence = 0,
                    analysis_status = 'pending',
                    analysis_progress = 0,
                    analysis_message = 'Analysis data cleared'
                WHERE id = ?
            ''', (cluster_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                
                # Also clear from cache
                clear_analysis_cache(cluster_id)
                
                logger.info(f"✅ Cleared analysis data for cluster {cluster_id}")
                return jsonify({
                    'status': 'success',
                    'message': f'Analysis data cleared for cluster {cluster_id}'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
                
    except Exception as e:
        logger.error(f"Error clearing analysis data for {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# IMPLEMENTATION PLAN MANAGEMENT ROUTES
# ============================================================================

@db_mgmt_bp.route('/implementation-plans', methods=['GET'])
def api_get_implementation_plans():
    """Get all implementation plans with filtering"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        status_filter = request.args.get('status')
        complexity_filter = request.args.get('complexity')
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT 
                    id, name, resource_group, environment,
                    last_analyzed, last_cost, last_savings,
                    analysis_data
                FROM clusters 
                WHERE analysis_data IS NOT NULL 
                AND analysis_data LIKE '%implementation_plan%'
            '''
            
            cursor = conn.execute(query)
            plans = []
            
            for row in cursor.fetchall():
                try:
                    analysis_data = json.loads(row['analysis_data'])
                    impl_plan = analysis_data.get('implementation_plan')
                    
                    if not impl_plan:
                        continue
                    
                    # Extract plan metadata
                    exec_summary = impl_plan.get('executive_summary', {})
                    impl_overview = exec_summary.get('implementation_overview', {})
                    opportunity = exec_summary.get('optimization_opportunity', {})
                    phases = impl_plan.get('implementation_phases', [])
                    
                    plan_data = {
                        'cluster_id': row['id'],
                        'cluster_name': row['name'],
                        'resource_group': row['resource_group'],
                        'environment': row['environment'],
                        'last_analyzed': row['last_analyzed'],
                        'phases_count': len(phases),
                        'estimated_duration_weeks': impl_overview.get('estimated_duration_weeks'),
                        'complexity_level': impl_overview.get('complexity_level', 'medium').lower(),
                        'risk_level': impl_overview.get('risk_level', 'medium').lower(),
                        'projected_monthly_savings': opportunity.get('projected_monthly_savings', 0),
                        'annual_savings_potential': opportunity.get('annual_savings_potential', 0),
                        'optimization_percentage': opportunity.get('optimization_percentage', 0),
                        'plan_status': 'generated',  # Could be enhanced with actual status tracking
                        'generation_method': impl_plan.get('metadata', {}).get('generation_method', 'unknown')
                    }
                    
                    # Apply filters
                    if complexity_filter and plan_data['complexity_level'] != complexity_filter.lower():
                        continue
                    
                    if status_filter and plan_data['plan_status'] != status_filter.lower():
                        continue
                    
                    plans.append(plan_data)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error parsing implementation plan for cluster {row['id']}: {e}")
                    continue
            
            return jsonify({
                'status': 'success',
                'plans': plans,
                'total': len(plans)
            })
            
    except Exception as e:
        logger.error(f"Error getting implementation plans: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/clusters/<cluster_id>/implementation-plan', methods=['GET'])
def api_get_implementation_plan(cluster_id):
    """Get implementation plan for a specific cluster"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT analysis_data, name, resource_group, last_analyzed, last_cost, last_savings
                FROM clusters 
                WHERE id = ?
            ''', (cluster_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
            
            if not row['analysis_data']:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data found for this cluster'
                }), 404
            
            try:
                analysis_data = json.loads(row['analysis_data'])
                implementation_plan = analysis_data.get('implementation_plan')
                
                if not implementation_plan:
                    return jsonify({
                        'status': 'error',
                        'message': 'No implementation plan found in analysis data'
                    }), 404
                
                # Add cluster metadata
                response_data = {
                    'status': 'success',
                    'cluster_info': {
                        'id': cluster_id,
                        'name': row['name'],
                        'resource_group': row['resource_group'],
                        'last_analyzed': row['last_analyzed'],
                        'last_cost': row['last_cost'],
                        'last_savings': row['last_savings']
                    },
                    'implementation_plan': implementation_plan,
                    'has_phases': bool(implementation_plan.get('implementation_phases')),
                    'phases_count': len(implementation_plan.get('implementation_phases', [])),
                    'plan_type': implementation_plan.get('metadata', {}).get('generation_method', 'unknown')
                }
                
                return jsonify(response_data)
                
            except json.JSONDecodeError as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid JSON in analysis data: {str(e)}'
                }), 500
                
    except Exception as e:
        logger.error(f"Error getting implementation plan for {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/clusters/<cluster_id>/test-implementation-plan', methods=['POST'])
def api_test_implementation_plan(cluster_id):
    """Test implementation plan structure and validity"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT analysis_data, name, resource_group
                FROM clusters 
                WHERE id = ?
            ''', (cluster_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
            
            if not row['analysis_data']:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data to test'
                }), 404
            
            # Validate JSON and extract implementation plan
            is_valid, data_or_error = validate_json_data(row['analysis_data'])
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': f'JSON validation failed: {data_or_error}'
                }), 400
            
            impl_plan = data_or_error.get('implementation_plan')
            if not impl_plan:
                return jsonify({
                    'status': 'error',
                    'message': 'No implementation plan found in analysis data'
                }), 404
            
            # Run structure tests
            test_results = test_implementation_plan_structure(impl_plan)
            
            # Calculate overall status
            critical_failures = [t for t in test_results if t['severity'] == 'critical' and t['status'] == 'fail']
            overall_status = 'fail' if critical_failures else 'pass'
            
            return jsonify({
                'status': 'success',
                'cluster_info': {
                    'id': cluster_id,
                    'name': row['name'],
                    'resource_group': row['resource_group']
                },
                'test_results': {
                    'overall_status': overall_status,
                    'tests_run': len(test_results),
                    'tests_passed': len([t for t in test_results if t['status'] == 'pass']),
                    'tests_failed': len([t for t in test_results if t['status'] == 'fail']),
                    'tests_warning': len([t for t in test_results if t['status'] == 'warning']),
                    'critical_failures': len(critical_failures),
                    'detailed_results': test_results
                }
            })
            
    except Exception as e:
        logger.error(f"Error testing implementation plan for {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/implementation-plans/test-all', methods=['POST'])
def api_test_all_implementation_plans():
    """Test all implementation plans and return summary"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT id, name, resource_group, analysis_data
                FROM clusters 
                WHERE analysis_data IS NOT NULL 
                AND analysis_data LIKE '%implementation_plan%'
            '''
            
            cursor = conn.execute(query)
            
            test_summary = {
                'total_plans': 0,
                'valid_plans': 0,
                'invalid_plans': 0,
                'plans_with_warnings': 0,
                'critical_failures': 0,
                'plan_results': []
            }
            
            for row in cursor.fetchall():
                try:
                    analysis_data = json.loads(row['analysis_data'])
                    impl_plan = analysis_data.get('implementation_plan')
                    
                    if not impl_plan:
                        continue
                    
                    test_summary['total_plans'] += 1
                    
                    # Run tests
                    test_results = test_implementation_plan_structure(impl_plan)
                    
                    # Analyze results
                    critical_failures = [t for t in test_results if t['severity'] == 'critical' and t['status'] == 'fail']
                    warnings = [t for t in test_results if t['status'] == 'warning']
                    
                    plan_status = 'invalid' if critical_failures else 'valid'
                    
                    if plan_status == 'valid':
                        test_summary['valid_plans'] += 1
                    else:
                        test_summary['invalid_plans'] += 1
                    
                    if warnings:
                        test_summary['plans_with_warnings'] += 1
                    
                    test_summary['critical_failures'] += len(critical_failures)
                    
                    test_summary['plan_results'].append({
                        'cluster_id': row['id'],
                        'cluster_name': row['name'],
                        'resource_group': row['resource_group'],
                        'status': plan_status,
                        'tests_passed': len([t for t in test_results if t['status'] == 'pass']),
                        'tests_failed': len([t for t in test_results if t['status'] == 'fail']),
                        'warnings': len(warnings),
                        'critical_failures': len(critical_failures)
                    })
                    
                except (json.JSONDecodeError, KeyError) as e:
                    test_summary['total_plans'] += 1
                    test_summary['invalid_plans'] += 1
                    test_summary['plan_results'].append({
                        'cluster_id': row['id'],
                        'cluster_name': row['name'],
                        'resource_group': row['resource_group'],
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Calculate success rate
            success_rate = (test_summary['valid_plans'] / test_summary['total_plans'] * 100) if test_summary['total_plans'] > 0 else 0
            
            return jsonify({
                'status': 'success',
                'test_summary': {
                    **test_summary,
                    'success_rate': round(success_rate, 1),
                    'overall_status': 'good' if success_rate >= 80 else 'warning' if success_rate >= 60 else 'poor'
                }
            })
            
    except Exception as e:
        logger.error(f"Error testing all implementation plans: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/clusters/<cluster_id>/validate-implementation-plan', methods=['POST'])
def api_validate_implementation_plan(cluster_id):
    """Validate implementation plan against business rules"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT analysis_data, name, resource_group
                FROM clusters 
                WHERE id = ?
            ''', (cluster_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found'
                }), 404
            
            if not row['analysis_data']:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data found'
                }), 404
            
            # Parse and validate
            is_valid, data_or_error = validate_json_data(row['analysis_data'])
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid analysis data: {data_or_error}'
                }), 400
            
            impl_plan = data_or_error.get('implementation_plan')
            if not impl_plan:
                return jsonify({
                    'status': 'error',
                    'message': 'No implementation plan found'
                }), 404
            
            # Business validation rules
            validation_results = []
            
            # Rule 1: Must have phases
            phases = impl_plan.get('implementation_phases', [])
            validation_results.append({
                'rule': 'Must have implementation phases',
                'status': 'pass' if len(phases) > 0 else 'fail',
                'details': f'Found {len(phases)} phases'
            })
            
            # Rule 2: Executive summary must exist
            exec_summary = impl_plan.get('executive_summary', {})
            validation_results.append({
                'rule': 'Must have executive summary',
                'status': 'pass' if exec_summary else 'fail',
                'details': 'Executive summary present' if exec_summary else 'Executive summary missing'
            })
            
            # Rule 3: Timeline must be reasonable (2-16 weeks)
            timeline = impl_plan.get('timeline_optimization', {})
            total_weeks = timeline.get('total_weeks', 0)
            reasonable_timeline = 2 <= total_weeks <= 16
            validation_results.append({
                'rule': 'Timeline must be reasonable (2-16 weeks)',
                'status': 'pass' if reasonable_timeline else 'warning',
                'details': f'Timeline: {total_weeks} weeks'
            })
            
            # Rule 4: Savings must be positive
            opportunity = exec_summary.get('optimization_opportunity', {})
            projected_savings = opportunity.get('projected_monthly_savings', 0)
            validation_results.append({
                'rule': 'Must have positive projected savings',
                'status': 'pass' if projected_savings > 0 else 'warning',
                'details': f'Projected savings: ${projected_savings:.2f}/month'
            })
            
            # Rule 5: Phases must have proper structure
            valid_phase_count = 0
            for phase in phases:
                if (phase.get('title') and 
                    phase.get('duration_weeks') and 
                    phase.get('tasks')):
                    valid_phase_count += 1
            
            validation_results.append({
                'rule': 'All phases must have complete structure',
                'status': 'pass' if valid_phase_count == len(phases) else 'warning',
                'details': f'{valid_phase_count}/{len(phases)} phases have complete structure'
            })
            
            # Calculate overall validation status
            failures = [r for r in validation_results if r['status'] == 'fail']
            warnings = [r for r in validation_results if r['status'] == 'warning']
            
            overall_status = 'fail' if failures else 'warning' if warnings else 'pass'
            
            return jsonify({
                'status': 'success',
                'cluster_info': {
                    'id': cluster_id,
                    'name': row['name'],
                    'resource_group': row['resource_group']
                },
                'validation_results': {
                    'overall_status': overall_status,
                    'rules_passed': len([r for r in validation_results if r['status'] == 'pass']),
                    'rules_failed': len(failures),
                    'rules_warning': len(warnings),
                    'total_rules': len(validation_results),
                    'detailed_results': validation_results
                }
            })
            
    except Exception as e:
        logger.error(f"Error validating implementation plan for {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# CACHE MANAGEMENT ROUTES (Enhanced)
# ============================================================================

@db_mgmt_bp.route('/cache/status', methods=['GET'])
def api_cache_status():
    """Get detailed cache status"""
    try:
        cluster_id = request.args.get('cluster_id')
        
        if not analysis_cache:
            return jsonify({
                'status': 'error',
                'message': 'Cache system not initialized'
            }), 503
        
        status_info = {
            'total_cached_clusters': len(analysis_cache.get('clusters', {})),
            'cached_clusters': list(analysis_cache.get('clusters', {}).keys()),
            'global_ttl_hours': analysis_cache.get('global_ttl_hours', 1),
            'cache_type': 'multi_cluster',
            'timestamp': datetime.now().isoformat()
        }
        
        if cluster_id:
            # Specific cluster status
            if cluster_id in analysis_cache.get('clusters', {}):
                cluster_cache = analysis_cache['clusters'][cluster_id]
                status_info.update({
                    'cluster_id': cluster_id,
                    'cache_valid': is_cache_valid(cluster_id),
                    'cache_timestamp': cluster_cache.get('timestamp'),
                    'cache_has_data': bool(cluster_cache.get('data')),
                    'cache_total_cost': cluster_cache.get('data', {}).get('total_cost', 0),
                    'cache_has_pod_costs': cluster_cache.get('data', {}).get('has_pod_costs', False),
                    'cache_has_hpa': bool(cluster_cache.get('data', {}).get('hpa_recommendations')),
                    'cache_has_implementation_plan': bool(cluster_cache.get('data', {}).get('implementation_plan')),
                    'namespace_count_in_cache': len(cluster_cache.get('data', {}).get('namespace_costs', {}))
                })
            else:
                status_info.update({
                    'cluster_id': cluster_id,
                    'cache_exists': False,
                    'message': f'No cache found for cluster {cluster_id}'
                })
        else:
            # All clusters summary
            cluster_summaries = {}
            for cid, cache_data in analysis_cache.get('clusters', {}).items():
                cluster_summaries[cid] = {
                    'cost': cache_data.get('data', {}).get('total_cost', 0),
                    'savings': cache_data.get('data', {}).get('total_savings', 0),
                    'timestamp': cache_data.get('timestamp'),
                    'valid': is_cache_valid(cid),
                    'has_hpa': bool(cache_data.get('data', {}).get('hpa_recommendations')),
                    'has_implementation_plan': bool(cache_data.get('data', {}).get('implementation_plan'))
                }
            status_info['cluster_summaries'] = cluster_summaries
        
        return jsonify({
            'status': 'success',
            'cache_status': status_info
        })
        
    except Exception as e:
        logger.error(f"Cache status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/cache/clear', methods=['POST'])
def api_cache_clear():
    """Clear analysis cache for specific cluster or all clusters"""
    try:
        if not analysis_cache:
            return jsonify({
                'status': 'error',
                'message': 'Cache system not initialized'
            }), 503
            
        data = request.get_json() or {}
        cluster_id = data.get('cluster_id') or request.args.get('cluster_id')
        
        if cluster_id:
            if cluster_id in analysis_cache.get('clusters', {}):
                clear_analysis_cache(cluster_id)
                message = f'Analysis cache cleared for cluster {cluster_id}'
                logger.info(f"🧹 API: {message}")
            else:
                message = f'No cache found for cluster {cluster_id}'
                logger.info(f"ℹ️ API: {message}")
        else:
            old_count = len(analysis_cache.get('clusters', {}))
            clear_analysis_cache()
            message = f'All analysis caches cleared successfully (cleared {old_count} clusters)'
            logger.info(f"🧹 API: {message}")
            
        return jsonify({
            'status': 'success',
            'message': message,
            'total_clusters_remaining': len(analysis_cache.get('clusters', {})),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Cache clear API error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/cache/stats', methods=['GET'])
def api_cache_stats():
    """Get cache statistics and metrics"""
    try:
        if not analysis_cache:
            return jsonify({
                'status': 'error',
                'message': 'Cache system not initialized'
            }), 503
        
        clusters = analysis_cache.get('clusters', {})
        
        # Calculate statistics
        total_clusters = len(clusters)
        valid_clusters = sum(1 for cid in clusters.keys() if is_cache_valid(cid))
        expired_clusters = total_clusters - valid_clusters
        
        # Cost statistics
        total_costs = []
        total_savings = []
        
        for cluster_data in clusters.values():
            data = cluster_data.get('data', {})
            if data.get('total_cost'):
                total_costs.append(data['total_cost'])
            if data.get('total_savings'):
                total_savings.append(data['total_savings'])
        
        stats = {
            'cache_health': {
                'total_clusters': total_clusters,
                'valid_clusters': valid_clusters,
                'expired_clusters': expired_clusters,
                'cache_hit_rate': (valid_clusters / total_clusters * 100) if total_clusters > 0 else 0
            },
            'cost_metrics': {
                'total_cached_cost': sum(total_costs),
                'total_cached_savings': sum(total_savings),
                'avg_cluster_cost': sum(total_costs) / len(total_costs) if total_costs else 0,
                'avg_cluster_savings': sum(total_savings) / len(total_savings) if total_savings else 0
            },
            'cache_metadata': {
                'global_ttl_hours': analysis_cache.get('global_ttl_hours', 1),
                'cache_type': 'multi_cluster',
                'generated_at': datetime.now().isoformat()
            }
        }
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# DELETE OPERATIONS (Enhanced)
# ============================================================================

@db_mgmt_bp.route('/clusters/<cluster_id>', methods=['DELETE'])
def api_delete_cluster(cluster_id):
    """Delete a cluster and all its data"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        success = enhanced_cluster_manager.remove_cluster(cluster_id)
        
        if success:
            # Also clear from cache
            clear_analysis_cache(cluster_id)
            
            logger.info(f"✅ Deleted cluster {cluster_id}")
            return jsonify({
                'status': 'success',
                'message': f'Cluster {cluster_id} deleted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Cluster not found'
            }), 404
                
    except Exception as e:
        logger.error(f"Error deleting cluster {cluster_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def api_delete_alert(alert_id):
    """Delete a specific alert"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            # Delete alert triggers first
            conn.execute('DELETE FROM alert_triggers WHERE alert_id = ?', (alert_id,))
            
            # Delete alert
            cursor = conn.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✅ Deleted alert {alert_id}")
                return jsonify({
                    'status': 'success',
                    'message': f'Alert {alert_id} deleted successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Alert not found'
                }), 404
                
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# ALERTS ROUTES (From original)
# ============================================================================

@db_mgmt_bp.route('/alerts-detailed', methods=['GET'])
def api_get_alerts_detailed():
    """Get detailed alerts information for database viewer"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT 
                    a.id, a.name, a.alert_type, a.threshold_amount, 
                    a.threshold_percentage, a.email, a.resource_group,
                    a.cluster_name, a.status, a.created_at, a.last_triggered,
                    a.trigger_count, a.notification_frequency, a.cluster_id
                FROM alerts a
                ORDER BY a.created_at DESC
            '''
            
            cursor = conn.execute(query)
            alerts = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'status': 'success',
                'alerts': alerts,
                'total': len(alerts)
            })
            
    except Exception as e:
        logger.error(f"Error getting detailed alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/alert-triggers', methods=['GET'])
def api_get_alert_triggers():
    """Get alert triggers history"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT 
                    at.id, at.alert_id, at.triggered_at, at.current_cost,
                    at.threshold_exceeded, at.message, at.action_taken,
                    at.acknowledged, at.cluster_id,
                    a.name as alert_name, a.email
                FROM alert_triggers at
                JOIN alerts a ON at.alert_id = a.id
                ORDER BY at.triggered_at DESC
                LIMIT 100
            '''
            
            cursor = conn.execute(query)
            triggers = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'status': 'success',
                'triggers': triggers,
                'total': len(triggers)
            })
            
    except Exception as e:
        logger.error(f"Error getting alert triggers: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@db_mgmt_bp.route('/learning-data', methods=['GET'])
def api_get_learning_data():
    """Get learning data from optimization database"""
    try:
        data_type = request.args.get('type', 'implementation_results')
        
        # This would connect to the learning database
        learning_db_path = 'machine_learning/data/optimization_learning.db'
        
        if not os.path.exists(learning_db_path):
            return jsonify({
                'status': 'info',
                'message': 'Learning database not found - no ML learning data available yet',
                'data': [],
                'path': learning_db_path
            })
        
        with sqlite3.connect(learning_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if data_type == 'implementation_results':
                query = '''
                    SELECT * FROM implementation_results 
                    ORDER BY created_at DESC LIMIT 100
                '''
            elif data_type == 'strategy_patterns':
                query = '''
                    SELECT * FROM strategy_patterns 
                    ORDER BY last_updated DESC
                '''
            elif data_type == 'cluster_archetypes':
                query = '''
                    SELECT * FROM cluster_archetypes 
                    ORDER BY sample_clusters DESC
                '''
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid data type'
                }), 400
            
            cursor = conn.execute(query)
            data = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'status': 'success',
                'data': data,
                'total': len(data),
                'type': data_type
            })
            
    except Exception as e:
        logger.error(f"Error getting learning data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# DEBUG AND UTILITY ROUTES
# ============================================================================

@db_mgmt_bp.route('/debug/routes', methods=['GET'])
def debug_routes():
    """Debug endpoint to see available routes in this blueprint"""
    from flask import current_app
    
    routes = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint.startswith('database_management.'):
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            line = f"{rule.endpoint:50s} {methods:20s} {rule}"
            routes.append(line)
    
    return {
        'blueprint_routes': routes,
        'total_routes': len(routes)
    }

@db_mgmt_bp.route('/system-info', methods=['GET'])
def api_system_info():
    """Get system information and component status"""
    try:
        system_info = {
            'database_management': {
                'version': '2.0.0',
                'enhanced_features': True,
                'components_initialized': {
                    'cluster_manager': enhanced_cluster_manager is not None,
                    'alerts_manager': alerts_manager is not None,
                    'analysis_cache': analysis_cache is not None
                },
                'features_available': {
                    'analysis_testing': True,
                    'implementation_plan_testing': True,
                    'cache_management': True,
                    'comprehensive_validation': True,
                    'enhanced_filtering': True
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'system_info': system_info
        })
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500