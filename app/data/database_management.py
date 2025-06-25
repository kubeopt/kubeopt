"""
Database and Cache Management Module
====================================
Separate module for database administration and cache management functionality.
This keeps app.py clean and focused on core business logic.
"""

import json
import os
import sqlite3
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
import traceback

# Import your existing components
# Note: Adjust these imports based on your actual project structure
try:
    from app.data.cluster_database import EnhancedClusterManager
    from app.alerts.alerts_manager import EnhancedAlertsManager
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

# ============================================================================
# DATABASE ROUTES
# ============================================================================

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
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM analysis_results')
                    analysis_count = cursor.fetchone()[0]
                    
                    health_status['checks'].append({
                        'component': 'Main Database',
                        'status': 'healthy',
                        'details': f'{cluster_count} clusters, {analysis_count} analysis records',
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
        
        # Check learning database
        learning_db_path = 'app/data/database/optimization_learning.db'
        try:
            if os.path.exists(learning_db_path):
                with sqlite3.connect(learning_db_path) as conn:
                    cursor = conn.execute('SELECT COUNT(*) FROM implementation_results')
                    impl_count = cursor.fetchone()[0]
                    
                    health_status['checks'].append({
                        'component': 'Learning Database',
                        'status': 'healthy',
                        'details': f'{impl_count} implementation results',
                        'path': learning_db_path
                    })
            else:
                health_status['checks'].append({
                    'component': 'Learning Database',
                    'status': 'info',
                    'details': 'Database not created yet - no learning data',
                    'path': f'{learning_db_path} (not found)'
                })
        except Exception as e:
            health_status['checks'].append({
                'component': 'Learning Database',
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
                    auto_analyze_enabled
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

@db_mgmt_bp.route('/analysis-results', methods=['GET'])
def api_get_analysis_results():
    """Get analysis results from database"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Cluster manager not initialized'
            }), 503
            
        cluster_id = request.args.get('cluster_id')
        days = request.args.get('days', type=int)
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT 
                    ar.id, ar.cluster_id, ar.analysis_date, ar.total_cost,
                    ar.total_savings, ar.confidence_level,
                    c.name as cluster_name, c.resource_group
                FROM analysis_results ar
                JOIN clusters c ON ar.cluster_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if cluster_id:
                query += ' AND ar.cluster_id = ?'
                params.append(cluster_id)
            
            if days:
                query += ' AND ar.analysis_date > datetime("now", "-{} days")'.format(days)
            
            query += ' ORDER BY ar.analysis_date DESC LIMIT 500'
            
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
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
        learning_db_path = 'app/data/database/optimization_learning.db'
        
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
# CACHE ROUTES
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

@db_mgmt_bp.route('/cache/clear', methods=['GET', 'POST'])
def api_cache_clear():
    """Clear analysis cache for specific cluster or all clusters"""
    try:
        if not analysis_cache:
            return jsonify({
                'status': 'error',
                'message': 'Cache system not initialized'
            }), 503
            
        if request.method == 'GET':
            # GET: Show what would be cleared (status)
            cluster_id = request.args.get('cluster_id')
            
            if cluster_id:
                cache_exists = cluster_id in analysis_cache.get('clusters', {})
                if cache_exists:
                    cluster_cache = analysis_cache['clusters'][cluster_id]
                    cache_info = {
                        'cluster_id': cluster_id,
                        'cache_exists': True,
                        'cache_timestamp': cluster_cache.get('timestamp'),
                        'cache_valid': is_cache_valid(cluster_id),
                        'total_cost': cluster_cache.get('data', {}).get('total_cost', 0)
                    }
                else:
                    cache_info = {
                        'cluster_id': cluster_id,
                        'cache_exists': False
                    }
                
                return jsonify({
                    'status': 'info',
                    'message': f'Cache status for cluster {cluster_id}',
                    'cache_info': cache_info,
                    'action': 'Use POST to actually clear the cache'
                })
            else:
                return jsonify({
                    'status': 'info',
                    'message': 'Current cache status',
                    'total_cached_clusters': len(analysis_cache.get('clusters', {})),
                    'cached_clusters': list(analysis_cache.get('clusters', {}).keys()),
                    'action': 'Use POST to actually clear all caches'
                })
        
        elif request.method == 'POST':
            # POST: Actually clear the cache
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
# OVERVIEW AND STATISTICS
# ============================================================================

@db_mgmt_bp.route('/analysis-results/<int:analysis_id>', methods=['DELETE'])
def api_delete_analysis_result(analysis_id):
    """Delete a specific analysis result"""
    try:
        if not enhanced_cluster_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database not available'
            }), 503
        
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            cursor = conn.execute('DELETE FROM analysis_results WHERE id = ?', (analysis_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✅ Deleted analysis result {analysis_id}")
                return jsonify({
                    'status': 'success',
                    'message': f'Analysis result {analysis_id} deleted successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Analysis result not found'
                }), 404
                
    except Exception as e:
        logger.error(f"Error deleting analysis result {analysis_id}: {e}")
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

@db_mgmt_bp.route('/analysis-results/<int:analysis_id>', methods=['DELETE'])
def api_delete_analysis_result_alt(analysis_id):
    """Alternative delete route for analysis results"""
    return api_delete_analysis_result(analysis_id)

@db_mgmt_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])  
def api_delete_alert_alt(alert_id):
    """Alternative delete route for alerts"""
    return api_delete_alert(alert_id)

@db_mgmt_bp.route('/clusters/<cluster_id>', methods=['DELETE'])
def api_delete_cluster_alt(cluster_id):
    """Alternative delete route for clusters"""
    return api_delete_cluster(cluster_id)

@db_mgmt_bp.route('/debug/routes', methods=['GET'])
def debug_routes():
    """Debug endpoint to see available routes in this blueprint"""
    from flask import current_app
    import urllib.parse
    
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

@db_mgmt_bp.route('/overview', methods=['GET'])
def api_overview_stats():
    """Get comprehensive overview statistics"""
    try:
        overview = {
            'database_stats': {},
            'cache_stats': {},
            'system_health': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Database statistics
        if enhanced_cluster_manager:
            try:
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    cursor = conn.execute('SELECT COUNT(*) FROM clusters')
                    cluster_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM analysis_results')
                    analysis_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute('SELECT COUNT(*) FROM alerts')
                    alert_count = cursor.fetchone()[0]
                    
                    overview['database_stats'] = {
                        'total_clusters': cluster_count,
                        'total_analyses': analysis_count,
                        'total_alerts': alert_count
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