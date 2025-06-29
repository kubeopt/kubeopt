"""
Updated API Routes for Multi-Subscription AKS Cost Optimization Tool - FIXED DUPLICATES
"""

import traceback
from datetime import datetime
from flask import request, jsonify
import sys
import os
import threading
import concurrent.futures
from typing import List

# Add the current directory to the path for imports
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# FIXED IMPORTS - use relative imports for current structure
from config import (
    logger, enhanced_cluster_manager, analysis_status_tracker, 
    _analysis_lock, _analysis_sessions, alerts_manager, analysis_cache
)
from app.interface.chart_data_api import chart_data_consistent
from app.services.background_processor import run_subscription_aware_background_analysis
from shared import _get_analysis_data  # Import from shared module
from app.services.subscription_manager import azure_subscription_manager
from app.data.processing.analysis_engine import multi_subscription_analysis_engine


def register_api_routes(app):
    """Register all API routes with multi-subscription support - FIXED DUPLICATES"""
    
    @app.route('/api/subscriptions', methods=['GET'])
    def api_get_subscriptions():
        """Get all available Azure subscriptions"""
        try:
            logger.info("🌐 Fetching available Azure subscriptions")
            
            force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
            subscriptions = azure_subscription_manager.get_available_subscriptions(force_refresh)
            
            subscription_list = []
            for sub in subscriptions:
                subscription_list.append({
                    'subscription_id': sub.subscription_id,
                    'subscription_name': sub.subscription_name,
                    'tenant_id': sub.tenant_id,
                    'state': sub.state,
                    'is_default': sub.is_default
                })
            
            return jsonify({
                'status': 'success',
                'subscriptions': subscription_list,
                'total_subscriptions': len(subscription_list),
                'default_subscription': next((s for s in subscription_list if s['is_default']), None)
            })
            
        except Exception as e:
            logger.error(f"❌ Error fetching subscriptions: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to fetch subscriptions: {str(e)}'
            }), 500

    @app.route('/api/subscriptions/dropdown', methods=['GET'])
    def api_get_subscriptions_dropdown():
        """Get subscriptions formatted for dropdown - maps to existing functionality"""
        try:
            logger.info("🌐 Fetching subscriptions for dropdown")
            
            force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
            subscriptions = azure_subscription_manager.get_available_subscriptions(force_refresh)
            
            # Format for dropdown (matches what frontend expects)
            dropdown_subscriptions = []
            for sub in subscriptions:
                dropdown_subscriptions.append({
                    'id': sub.subscription_id,  # Frontend expects 'id' 
                    'display_name': f"{sub.subscription_name} ({sub.subscription_id[:8]})",  # Frontend expects 'display_name'
                    'subscription_name': sub.subscription_name,
                    'subscription_id': sub.subscription_id,
                    'is_default': sub.is_default
                })
            
            return jsonify({
                'status': 'success',
                'subscriptions': dropdown_subscriptions,
                'total': len(dropdown_subscriptions)
            })
            
        except Exception as e:
            logger.error(f"❌ Error fetching subscriptions for dropdown: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to fetch subscriptions: {str(e)}'
            }), 500

    @app.route('/api/subscriptions/<subscription_id>/validate', methods=['POST'])
    def api_validate_subscription_cluster():
        """Validate cluster access in specific subscription"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            resource_group = data.get('resource_group')
            cluster_name = data.get('cluster_name')
            subscription_id = request.view_args['subscription_id']
            
            if not resource_group or not cluster_name:
                return jsonify({
                    'status': 'error',
                    'message': 'Resource group and cluster name are required'
                }), 400
            
            logger.info(f"🔍 Validating cluster {cluster_name} in subscription {subscription_id[:8]}")
            
            validation_result = azure_subscription_manager.validate_cluster_access(
                subscription_id, resource_group, cluster_name
            )
            
            return jsonify({
                'status': 'success' if validation_result['valid'] else 'error',
                'validation_result': validation_result,
                'subscription_id': subscription_id
            })
            
        except Exception as e:
            logger.error(f"❌ Error validating cluster: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Validation error: {str(e)}'
            }), 500

    @app.route('/api/chart-data')
    def api_chart_data():
        """COMPLETELY FIXED Chart data API route with subscription awareness"""
        try:
            logger.info("📊 Chart data API called with subscription awareness")
            
            # Get cluster ID and subscription context
            cluster_id = request.args.get('cluster_id')
            if cluster_id:
                # Get subscription info for this cluster
                cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster and cluster.get('subscription_id'):
                    logger.info(f"📊 Chart data for cluster {cluster_id} in subscription {cluster['subscription_id'][:8]}")
            
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
        """COMPLETELY FIXED: Implementation plan API with subscription awareness"""
        try:
            logger.info("📋 Implementation plan API called with subscription support")
            
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
            
            # Get cluster info with subscription context
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Use the shared _get_analysis_data function
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
                    from app.main.config import implementation_generator
                    from app.services.cache_manager import save_to_cache
                    
                    current_analysis['cluster_name'] = cluster['name']
                    current_analysis['resource_group'] = cluster['resource_group']
                    
                    fresh_plan = implementation_generator.generate_implementation_plan(current_analysis)
                    
                    if isinstance(fresh_plan, dict):
                        fresh_plan['cluster_metadata'] = {
                            'cluster_name': cluster['name'],
                            'resource_group': cluster['resource_group'],
                            'cluster_id': cluster_id,
                            'subscription_id': cluster.get('subscription_id'),
                            'subscription_name': cluster.get('subscription_name'),
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
            
            # Add API metadata with subscription info
            implementation_plan['api_metadata'] = {
                'data_source': data_source,
                'cluster_id': cluster_id,
                'cluster_name': cluster['name'],
                'resource_group': cluster['resource_group'],
                'subscription_id': cluster.get('subscription_id'),
                'subscription_name': cluster.get('subscription_name'),
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
        """API for cluster management with subscription support"""
        try:
            if request.method == 'GET':
                # Get clusters with subscription info
                clusters = enhanced_cluster_manager.get_clusters_with_subscription_info()
                portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
                
                return jsonify({
                    'status': 'success',
                    'clusters': clusters,
                    'portfolio_summary': portfolio_summary,
                    'total_clusters': len(clusters),
                    'multi_subscription_enabled': True
                })
            
            elif request.method == 'POST':
                # Enhanced API to add cluster with subscription context
                logger.info("📥 Received cluster add request with subscription support")
                
                cluster_config = request.get_json()
                if not cluster_config:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                # Validate required fields including subscription
                required_fields = ['cluster_name', 'resource_group', 'subscription_id']
                missing_fields = [field for field in required_fields if not cluster_config.get(field)]
                
                if missing_fields:
                    return jsonify({
                        'status': 'error',
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
                
                subscription_id = cluster_config['subscription_id']
                
                # Validate subscription access
                subscription_info = azure_subscription_manager.get_subscription_info(subscription_id)
                if not subscription_info:
                    return jsonify({
                        'status': 'error',
                        'message': f'Invalid subscription ID: {subscription_id}'
                    }), 400
                
                # Validate cluster access in the subscription
                validation_result = azure_subscription_manager.validate_cluster_access(
                    subscription_id, 
                    cluster_config['resource_group'], 
                    cluster_config['cluster_name']
                )
                
                if not validation_result['valid']:
                    return jsonify({
                        'status': 'error',
                        'message': f'Cannot access cluster in specified subscription: {validation_result["error"]}'
                    }), 400
                
                # Add cluster with subscription context
                cluster_id = enhanced_cluster_manager.add_cluster_with_subscription(
                    cluster_config, subscription_id, subscription_info.subscription_name
                )
                
                # Check if auto-analysis is requested (default: True)
                auto_analyze = cluster_config.get('auto_analyze', True)
                
                if auto_analyze:
                    logger.info(f"🚀 Starting automatic subscription-aware analysis for cluster: {cluster_id}")
                    
                    # Update cluster status to 'analyzing'
                    enhanced_cluster_manager.update_analysis_status(
                        cluster_id, 'analyzing', 0, 'Starting automatic subscription-aware analysis...'
                    )
                    
                    # Start analysis in background thread with subscription context
                    analysis_thread = threading.Thread(
                        target=run_subscription_aware_background_analysis,
                        args=(cluster_id, cluster_config['resource_group'], cluster_config['cluster_name'], subscription_id),
                        daemon=True
                    )
                    analysis_thread.start()
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Cluster added successfully! Subscription-aware analysis is starting automatically.',
                        'cluster_id': cluster_id,
                        'subscription_id': subscription_id,
                        'subscription_name': subscription_info.subscription_name,
                        'auto_analysis': True,
                        'analysis_status': 'analyzing'
                    })
                else:
                    return jsonify({
                        'status': 'success',
                        'message': 'Cluster added successfully',
                        'cluster_id': cluster_id,
                        'subscription_id': subscription_id,
                        'subscription_name': subscription_info.subscription_name,
                        'auto_analysis': False
                    })
                    
        except Exception as e:
            logger.error(f"❌ Error in clusters API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # FIXED: Only ONE definition of api_analyze_cluster - using the better one with path parameter
    @app.route('/api/clusters/<path:cluster_id>/analyze', methods=['POST'])
    def api_analyze_cluster(cluster_id: str):
        """Trigger subscription-aware analysis for specific cluster - FIXED SINGLE DEFINITION"""
        try:
            # Clean and validate cluster ID
            cluster_id = cluster_id.strip()
            
            # Allow various cluster ID formats
            if not cluster_id or len(cluster_id) < 3:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid cluster ID format'
                }), 400
            
            logger.info(f"🚀 Starting subscription-aware analysis for cluster {cluster_id}")
            
            data = request.get_json() or {}
            
            # Get cluster info
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Extract analysis parameters
            days = data.get('days', 30)
            enable_pod_analysis = data.get('enable_pod_analysis', True)
            
            logger.info(f"🚀 Analysis parameters: days={days}, pod_analysis={enable_pod_analysis}")
            
            # Update analysis status
            enhanced_cluster_manager.update_analysis_status(
                cluster_id, 'analyzing', 0, 'Starting subscription-aware analysis...'
            )
            
            # Get subscription context
            subscription_id = cluster.get('subscription_id')
            
            # Start analysis in background thread
            analysis_thread = threading.Thread(
                target=run_subscription_aware_background_analysis,
                args=(cluster_id, cluster['resource_group'], cluster['name'], subscription_id, days, enable_pod_analysis),
                daemon=True
            )
            analysis_thread.start()
            
            return jsonify({
                'status': 'success',
                'message': 'Subscription-aware analysis started',
                'cluster_id': cluster_id,
                'subscription_id': subscription_id,
                'analysis_parameters': {
                    'days': days,
                    'enable_pod_analysis': enable_pod_analysis
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Error starting analysis for cluster {cluster_id}: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to start analysis: {str(e)}'
            }), 500

    # FIXED: Only ONE definition of get_cluster_analysis_status - using the better one with path parameter
    @app.route('/api/clusters/<path:cluster_id>/analysis-status', methods=['GET'])
    def get_cluster_analysis_status(cluster_id: str):
        """Get real-time analysis status for a cluster with subscription info - FIXED SINGLE DEFINITION"""
        try:
            # Clean cluster ID
            cluster_id = cluster_id.strip()
            
            logger.info(f"📊 Getting analysis status for cluster: {cluster_id}")
            
            # Check in-memory tracker first (for active analyses)
            if cluster_id in analysis_status_tracker:
                status_info = analysis_status_tracker[cluster_id].copy()
                
                # Add subscription context if available
                cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster:
                    status_info.update({
                        'subscription_id': cluster.get('subscription_id'),
                        'subscription_name': cluster.get('subscription_name')
                    })
                
                return jsonify({
                    'status': 'success',
                    'cluster_id': cluster_id,
                    'analysis_status': status_info.get('status', 'unknown'),
                    **status_info
                })
            
            # Check database for stored status
            status_info = enhanced_cluster_manager.get_analysis_status(cluster_id)
            if status_info:
                return jsonify({
                    'status': 'success',
                    'analysis_status': status_info.get('status', 'unknown'),
                    **status_info
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Cluster not found',
                    'analysis_status': 'not_found'
                }), 404
                        
        except Exception as e:
            logger.error(f"❌ Error getting analysis status for {cluster_id}: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'analysis_status': 'error'
            }), 500

    @app.route('/api/debug-analysis')
    def debug_analysis():
        """Debug endpoint to check analysis results with subscription info"""
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
                # Get cluster-specific data with subscription context
                cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                current_analysis, data_source = _get_analysis_data(cluster_id)
                
                debug_info = {
                    'cluster_id': cluster_id,
                    'data_source': data_source,
                    'subscription_id': cluster.get('subscription_id') if cluster else None,
                    'subscription_name': cluster.get('subscription_name') if cluster else None,
                    'analysis_results_keys': list(current_analysis.keys()) if current_analysis else [],
                    'total_cost': current_analysis.get('total_cost', 'NOT_FOUND') if current_analysis else None,
                    'has_data': bool(current_analysis and current_analysis.get('total_cost', 0) > 0),
                    'has_pod_costs': current_analysis.get('has_pod_costs', False) if current_analysis else False,
                    'has_node_data': current_analysis.get('has_real_node_data', False) if current_analysis else False,
                    'subscription_metadata': current_analysis.get('subscription_metadata', {}) if current_analysis else {},
                    'multi_subscription_enabled': True
                }
                
                if request.args.get('include_full_results') == 'true':
                    debug_info['full_results'] = current_analysis
                
                return jsonify(debug_info)
            
            # Fallback: check global (but warn)
            from config import analysis_results
            logger.warning("⚠️ Debug endpoint: No cluster_id provided, checking global analysis_results")
            return jsonify({
                'cluster_id': None,
                'data_source': 'global_fallback',
                'analysis_results_keys': list(analysis_results.keys()) if analysis_results else [],
                'total_cost': analysis_results.get('total_cost', 'NOT_FOUND') if analysis_results else 'NO_GLOBAL_DATA',
                'has_data': bool(analysis_results and analysis_results.get('total_cost', 0) > 0),
                'full_results': analysis_results if analysis_results else {},
                'multi_subscription_enabled': True
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'status': 'error',
                'multi_subscription_enabled': True
            }), 500

    # Cache management API routes with subscription awareness
    @app.route('/api/cache/clear', methods=['GET', 'POST'])
    def clear_analysis_cache_api():
        """Clear analysis cache for specific cluster or all clusters with subscription awareness"""
        try:
            if request.method == 'GET':
                # GET: Show what would be cleared (status)
                cluster_id = request.args.get('cluster_id')
                
                from app.services.cache_manager import is_cache_valid
                
                if cluster_id:
                    cache_exists = cluster_id in analysis_cache['clusters']
                    if cache_exists:
                        cluster_cache = analysis_cache['clusters'][cluster_id]
                        cache_info = {
                            'cluster_id': cluster_id,
                            'cache_exists': True,
                            'cache_timestamp': cluster_cache.get('timestamp'),
                            'cache_valid': is_cache_valid(cluster_id),
                            'total_cost': cluster_cache.get('data', {}).get('total_cost', 0),
                            'subscription_id': cluster_cache.get('data', {}).get('subscription_metadata', {}).get('subscription_id')
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
                
                from app.services.cache_manager import clear_analysis_cache
                
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

# def run_subscription_aware_background_analysis(cluster_id: str, resource_group: str, cluster_name: str, 
#                                              subscription_id: str, days: int = 30, enable_pod_analysis: bool = True):
#     """Run subscription-aware analysis in background thread with progress tracking"""
#     try:
#         logger.info(f"🔄 Background subscription-aware analysis started for {cluster_id}")
        
#         # Progress tracking function
#         def update_progress(progress: int, message: str):
#             enhanced_cluster_manager.update_analysis_status(cluster_id, 'analyzing', progress, message)
#             analysis_status_tracker[cluster_id] = {
#                 'status': 'analyzing',
#                 'progress': progress,
#                 'message': message,
#                 'timestamp': datetime.now().isoformat(),
#                 'subscription_id': subscription_id
#             }
        
#         # Simulate analysis steps with progress updates
#         update_progress(10, f'Connecting to Azure subscription {subscription_id[:8]}...')
        
#         update_progress(25, 'Fetching cost data from subscription context...')
        
#         update_progress(45, 'Analyzing cluster metrics with subscription awareness...')
        
#         update_progress(65, 'Calculating optimization opportunities...')
        
#         # Run actual subscription-aware analysis
#         result = multi_subscription_analysis_engine.run_subscription_aware_analysis(
#             resource_group, cluster_name, subscription_id, days, enable_pod_analysis
#         )
        
#         update_progress(85, 'Generating insights...')
        
#         if result['status'] == 'success':
#             analysis_results = result['results']
            
#             # Store results in database with subscription context
#             enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_results)
            
#             # Update status to completed
#             enhanced_cluster_manager.update_analysis_status(
#                 cluster_id, 
#                 'completed', 
#                 100, 
#                 f'Subscription-aware analysis completed! Found ${analysis_results.get("total_savings", 0):.0f}/month savings potential'
#             )
            
#             analysis_status_tracker[cluster_id] = {
#                 'status': 'completed',
#                 'progress': 100,
#                 'message': 'Subscription-aware analysis completed successfully',
#                 'timestamp': datetime.now().isoformat(),
#                 'subscription_id': subscription_id,
#                 'results': {
#                     'total_cost': analysis_results.get('total_cost', 0),
#                     'total_savings': analysis_results.get('total_savings', 0),
#                     'confidence': analysis_results.get('analysis_confidence', 0)
#                 }
#             }
            
#             logger.info(f"✅ Background subscription-aware analysis completed for {cluster_id}")
            
#         else:
#             error_message = result.get('message', 'Subscription-aware analysis failed')
#             enhanced_cluster_manager.update_analysis_status(cluster_id, 'failed', 0, error_message)
            
#             analysis_status_tracker[cluster_id] = {
#                 'status': 'failed',
#                 'progress': 0,
#                 'message': error_message,
#                 'timestamp': datetime.now().isoformat(),
#                 'subscription_id': subscription_id
#             }
            
#             logger.error(f"❌ Background subscription-aware analysis failed for {cluster_id}: {error_message}")
            
#     except Exception as e:
#         error_message = f'Subscription-aware analysis error: {str(e)}'
#         logger.error(f"❌ Background subscription-aware analysis exception for {cluster_id}: {e}")
        
#         enhanced_cluster_manager.update_analysis_status(cluster_id, 'failed', 0, error_message)
#         analysis_status_tracker[cluster_id] = {
#             'status': 'failed',
#             'progress': 0,
#             'message': error_message,
#             'timestamp': datetime.now().isoformat(),
#             'subscription_id': subscription_id
#         }