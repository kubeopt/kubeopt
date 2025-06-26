"""
API Routes for AKS Cost Optimization Tool
"""

import traceback
from datetime import datetime
from flask import request, jsonify
from app.main.config import (
    logger, enhanced_cluster_manager, analysis_status_tracker, 
    _analysis_lock, _analysis_sessions, alerts_manager, analysis_cache
)
from app.interface.chart_data_api import chart_data_consistent
from app.services.background_processor import run_background_analysis
import threading

def register_api_routes(app):
    """Register all API routes"""
    
    @app.route('/api/chart-data')
    def chart_data():
        """COMPLETELY FIXED Chart data API route - no global analysis_results dependency"""
        try:
            logger.info("📊 Chart data API called")
            
            # Call the comprehensive chart data function that handles all data sources
            return chart_data_consistent()
                
        except Exception as e:
            logger.error(f"❌ ERROR in chart_data routing: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Chart data routing error: {str(e)}',
                'error_type': 'routing_error'
            }), 500

    @app.route('/api/implementation-plan')
    def get_implementation_plan():
        """COMPLETELY FIXED: Implementation plan API with session priority"""
        try:
            logger.info("📋 Implementation plan API called")
            
            # Extract cluster ID
            cluster_id = request.args.get('cluster_id')
            if not cluster_id:
                referrer = request.headers.get('Referer', '')
                if '/cluster/' in referrer:
                    try:
                        cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
                        logger.info(f"📋 Extracted cluster_id from referrer: {cluster_id}")
                    except Exception:
                        pass
            
            if not cluster_id:
                return jsonify({
                    'status': 'error',
                    'message': 'No cluster ID provided for implementation plan'
                }), 400
            
            # Get cluster info
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Import the helper function
            from routes import _get_analysis_data
            from config import implementation_generator
            from cache_manager import save_to_cache
            
            # PRIORITY 1: Check for fresh session data first
            fresh_session_data = None
            data_source = "none"
            
            with _analysis_lock:
                for session_id, session_info in _analysis_sessions.items():
                    if (session_info.get('cluster_id') == cluster_id and 
                        session_info.get('status') == 'completed' and
                        'results' in session_info):
                        
                        fresh_session_data = session_info['results']
                        data_source = "fresh_session"
                        logger.info(f"🎯 API: Found fresh session data for {cluster_id}")
                        break
            
            current_analysis = None
            
            if fresh_session_data:
                # Use fresh session data
                current_analysis = fresh_session_data
                logger.info(f"📋 API: Using fresh session data for implementation plan")
            else:
                # Fallback to cache/database
                current_analysis, data_source = _get_analysis_data(cluster_id)
            
            if not current_analysis:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available for implementation plan',
                    'cluster_id': cluster_id,
                    'data_source': data_source
                }), 404
            
            # Get implementation plan
            implementation_plan = current_analysis.get('implementation_plan')
            
            # ALWAYS regenerate if missing or invalid
            if (not implementation_plan or 
                not isinstance(implementation_plan, dict) or 
                'implementation_phases' not in implementation_plan or
                not implementation_plan['implementation_phases']):
                
                logger.info(f"🔄 API: Regenerating implementation plan for {cluster_id}")
                try:
                    current_analysis['cluster_name'] = cluster['name']
                    current_analysis['resource_group'] = cluster['resource_group']
                    
                    fresh_plan = implementation_generator.generate_implementation_plan(current_analysis)
                    
                    if isinstance(fresh_plan, dict):
                        fresh_plan['cluster_metadata'] = {
                            'cluster_name': cluster['name'],
                            'resource_group': cluster['resource_group'],
                            'cluster_id': cluster_id,
                            'generated_at': datetime.now().isoformat(),
                            'api_regenerated': True
                        }
                    
                    current_analysis['implementation_plan'] = fresh_plan
                    implementation_plan = fresh_plan
                    
                    # Update cache and database
                    save_to_cache(cluster_id, current_analysis)
                    enhanced_cluster_manager.update_cluster_analysis(cluster_id, current_analysis)
                    
                    logger.info(f"✅ API: Regenerated implementation plan for {cluster_id}")
                    
                except Exception as gen_error:
                    logger.error(f"❌ API: Failed to regenerate implementation plan: {gen_error}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to generate implementation plan: {str(gen_error)}'
                    }), 500
            
            # Final validation
            if not isinstance(implementation_plan, dict) or 'implementation_phases' not in implementation_plan:
                return jsonify({
                    'status': 'error',
                    'message': 'Implementation plan has invalid structure'
                }), 500
            
            phases = implementation_plan['implementation_phases']
            if not isinstance(phases, list) or len(phases) == 0:
                return jsonify({
                    'status': 'error',
                    'message': 'Implementation plan has no valid phases'
                }), 500
            
            # Add API metadata
            implementation_plan['api_metadata'] = {
                'data_source': data_source,
                'cluster_id': cluster_id,
                'cluster_name': cluster['name'],
                'resource_group': cluster['resource_group'],
                'phases_count': len(phases),
                'api_called_at': datetime.now().isoformat(),
                'total_cost': current_analysis.get('total_cost', 0),
                'total_savings': current_analysis.get('total_savings', 0)
            }
            
            logger.info(f"✅ API: Returning implementation plan for {cluster_id}: {len(phases)} phases from {data_source}")
            
            return jsonify(implementation_plan)
            
        except Exception as e:
            logger.error(f"❌ Error in implementation plan API: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Implementation plan API error: {str(e)}'
            }), 500

    @app.route('/api/clusters', methods=['GET', 'POST'])
    def api_clusters():
        """API for cluster management"""
        try:
            if request.method == 'GET':
                clusters = enhanced_cluster_manager.list_clusters()
                portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
                
                return jsonify({
                    'status': 'success',
                    'clusters': clusters,
                    'portfolio_summary': portfolio_summary,
                    'total_clusters': len(clusters)
                })
            
            elif request.method == 'POST':
                # Enhanced API to add cluster with automatic analysis
                logger.info("📥 Received enhanced cluster add request with auto-analysis")
                
                cluster_config = request.get_json()
                if not cluster_config:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                # Validate required fields
                required_fields = ['cluster_name', 'resource_group']
                missing_fields = [field for field in required_fields if not cluster_config.get(field)]
                
                if missing_fields:
                    return jsonify({
                        'status': 'error',
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
                
                # Add cluster to database
                cluster_id = enhanced_cluster_manager.add_cluster(cluster_config)
                
                # Check if auto-analysis is requested (default: True)
                auto_analyze = cluster_config.get('auto_analyze', True)
                
                if auto_analyze:
                    logger.info(f"🚀 Starting automatic analysis for cluster: {cluster_id}")
                    
                    # Update cluster status to 'analyzing'
                    from background_processor import update_cluster_analysis_status
                    update_cluster_analysis_status(cluster_id, 'analyzing', 0, 'Starting automatic analysis...')
                    
                    # Start analysis in background thread
                    analysis_thread = threading.Thread(
                        target=run_background_analysis,
                        args=(cluster_id, cluster_config['resource_group'], cluster_config['cluster_name']),
                        daemon=True
                    )
                    analysis_thread.start()
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Cluster added successfully! Analysis is starting automatically.',
                        'cluster_id': cluster_id,
                        'auto_analysis': True,
                        'analysis_status': 'analyzing'
                    })
                else:
                    return jsonify({
                        'status': 'success',
                        'message': 'Cluster added successfully',
                        'cluster_id': cluster_id,
                        'auto_analysis': False
                    })
                    
        except Exception as e:
            logger.error(f"❌ Error in clusters API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/clusters/<cluster_id>/analysis-status', methods=['GET'])
    def get_cluster_analysis_status(cluster_id: str):
        """Get real-time analysis status for a cluster"""
        try:
            # Check in-memory tracker first (for active analyses)
            if cluster_id in analysis_status_tracker:
                return jsonify({
                    'status': 'success',
                    'cluster_id': cluster_id,
                    **analysis_status_tracker[cluster_id]
                })
            
            # Check database for stored status
            import sqlite3
            with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT analysis_status, analysis_progress, analysis_message, 
                           last_cost, last_savings, last_analyzed
                    FROM clusters 
                    WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row:
                    return jsonify({
                        'status': 'success',
                        'cluster_id': cluster_id,
                        'status': row['analysis_status'] or 'pending',
                        'progress': row['analysis_progress'] or 0,
                        'message': row['analysis_message'] or 'Ready for analysis',
                        'last_cost': row['last_cost'],
                        'last_savings': row['last_savings'],
                        'last_analyzed': row['last_analyzed']
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Cluster not found'
                    }), 404
                    
        except Exception as e:
            logger.error(f"❌ Error getting analysis status: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/debug-analysis')
    def debug_analysis():
        """Debug endpoint to check analysis results - FIXED to use cluster-specific data"""
        try:
            # Try to get cluster ID from request
            cluster_id = request.args.get('cluster_id')
            if not cluster_id:
                # Try to extract from referrer
                referrer = request.headers.get('Referer', '')
                if '/cluster/' in referrer:
                    try:
                        cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
                    except Exception:
                        pass
            
            if cluster_id:
                # Get cluster-specific data
                from routes import _get_analysis_data
                current_analysis, data_source = _get_analysis_data(cluster_id)
                if current_analysis:
                    return jsonify({
                        'cluster_id': cluster_id,
                        'data_source': data_source,
                        'analysis_results_keys': list(current_analysis.keys()),
                        'total_cost': current_analysis.get('total_cost', 'NOT_FOUND'),
                        'has_data': bool(current_analysis and current_analysis.get('total_cost', 0) > 0),
                        'has_pod_costs': current_analysis.get('has_pod_costs', False),
                        'has_node_data': current_analysis.get('has_real_node_data', False),
                        'full_results': current_analysis
                    })
            
            # Fallback: check global (but warn)
            from config import analysis_results
            logger.warning("⚠️ Debug endpoint: No cluster_id provided, checking global analysis_results")
            return jsonify({
                'cluster_id': None,
                'data_source': 'global_fallback',
                'analysis_results_keys': list(analysis_results.keys()) if analysis_results else [],
                'total_cost': analysis_results.get('total_cost', 'NOT_FOUND') if analysis_results else 'NO_GLOBAL_DATA',
                'has_data': bool(analysis_results and analysis_results.get('total_cost', 0) > 0),
                'full_results': analysis_results if analysis_results else {}
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'status': 'error'
            }), 500

    # Cache management API routes
    @app.route('/api/cache/clear', methods=['GET', 'POST'])
    def clear_analysis_cache_api():
        """Clear analysis cache for specific cluster or all clusters"""
        try:
            if request.method == 'GET':
                # GET: Show what would be cleared (status)
                cluster_id = request.args.get('cluster_id')
                
                if cluster_id:
                    from cache_manager import is_cache_valid
                    cache_exists = cluster_id in analysis_cache['clusters']
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
                        'total_cached_clusters': len(analysis_cache['clusters']),
                        'cached_clusters': list(analysis_cache['clusters'].keys()),
                        'action': 'Use POST to actually clear all caches'
                    })
            
            elif request.method == 'POST':
                # POST: Actually clear the cache
                data = request.get_json() or {}
                cluster_id = data.get('cluster_id') or request.args.get('cluster_id')
                
                from cache_manager import clear_analysis_cache
                
                if cluster_id:
                    if cluster_id in analysis_cache['clusters']:
                        clear_analysis_cache(cluster_id)
                        message = f'Analysis cache cleared for cluster {cluster_id}'
                        logger.info(f"🧹 API: {message}")
                    else:
                        message = f'No cache found for cluster {cluster_id}'
                        logger.info(f"ℹ️ API: {message}")
                else:
                    old_count = len(analysis_cache['clusters'])
                    clear_analysis_cache()
                    message = f'All analysis caches cleared successfully (cleared {old_count} clusters)'
                    logger.info(f"🧹 API: {message}")
                    
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'total_clusters_remaining': len(analysis_cache['clusters']),
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"❌ Cache clear API error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Alerts API routes
    @app.route('/api/alerts', methods=['GET', 'POST'])
    def alerts_api():
        """Enhanced alerts API endpoint - COMPLETELY FIXED"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            if request.method == 'GET':
                # Get all alerts with enhanced filtering
                cluster_id = request.args.get('cluster_id')
                status = request.args.get('status', 'active')
                
                logger.info(f"🔍 GET /api/alerts - cluster_id: {cluster_id}, status: {status}")
                
                try:
                    # Call the alerts manager method
                    alerts_data = alerts_manager.get_alerts_route(cluster_id)
                    
                    if alerts_data['status'] == 'success':
                        alerts = alerts_data['alerts']
                        
                        # Additional status filtering if needed
                        if status and status != 'all' and status != 'active':
                            alerts = [a for a in alerts if a.get('status') == status]
                        
                        logger.info(f"✅ Returning {len(alerts)} alerts")
                        
                        return jsonify({
                            'status': 'success',
                            'alerts': alerts,
                            'total': len(alerts),
                            'cluster_id': cluster_id
                        })
                    else:
                        logger.error(f"❌ Alerts manager returned error: {alerts_data}")
                        return jsonify(alerts_data), 500
                        
                except Exception as manager_error:
                    logger.error(f"❌ Error calling alerts manager: {manager_error}")
                    logger.error(f"❌ Manager error traceback: {traceback.format_exc()}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Alerts manager error: {str(manager_error)}'
                    }), 500
                    
            elif request.method == 'POST':
                # Create new alert
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                logger.info(f"🔍 POST /api/alerts - data: {data}")
                
                # Enhanced validation
                if not data.get('email'):
                    return jsonify({
                        'status': 'error',
                        'message': 'Email address is required'
                    }), 400
                
                if not data.get('threshold_amount') and not data.get('threshold_percentage'):
                    return jsonify({
                        'status': 'error',
                        'message': 'Either threshold amount or percentage is required'
                    }), 400
                
                # Auto-populate cluster info if cluster_id provided
                cluster_id = data.get('cluster_id')
                if cluster_id:
                    cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                    if cluster:
                        data['cluster_name'] = cluster['name']
                        data['resource_group'] = cluster['resource_group']
                        data['name'] = data.get('name', f"Budget Alert - {cluster['name']}")
                
                # Set default name if not provided
                if not data.get('name'):
                    data['name'] = f"Cost Alert - {data.get('cluster_name', 'Unknown')}"
                
                try:
                    result = alerts_manager.create_alert_route(data)
                    
                    if result['status'] == 'success':
                        logger.info(f"✅ Created alert: {result['alert_id']}")
                        return jsonify(result)
                    else:
                        logger.error(f"❌ Failed to create alert: {result}")
                        return jsonify(result), 400
                        
                except Exception as create_error:
                    logger.error(f"❌ Error creating alert: {create_error}")
                    logger.error(f"❌ Create error traceback: {traceback.format_exc()}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to create alert: {str(create_error)}'
                    }), 500
                    
        except Exception as e:
            logger.error(f"❌ Error in alerts API: {e}")
            logger.error(f"❌ API error traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }), 500