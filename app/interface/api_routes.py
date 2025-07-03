"""
Unified API Routes for Multi-Subscription AKS Cost Optimization Tool
with Enhanced CPU Workload Integration - FIXED DUPLICATIONS
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
from app.services.background_processor import run_subscription_aware_background_analysis
from shared import _get_analysis_data  # Import from shared module
from app.services.subscription_manager import azure_subscription_manager
from app.data.processing.analysis_engine import multi_subscription_analysis_engine

# CPU Workload Integration imports with error handling
chart_generator_functions = {}
try:
    from chart_generator import generate_dynamic_hpa_comparison
    chart_generator_functions['hpa_comparison'] = generate_dynamic_hpa_comparison
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_dynamic_hpa_comparison: {e}")

try:
    from chart_generator import generate_insights
    chart_generator_functions['insights'] = generate_insights
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_insights: {e}")

try:
    from chart_generator import generate_node_utilization_data
    chart_generator_functions['node_utilization'] = generate_node_utilization_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_node_utilization_data: {e}")

try:
    from chart_generator import generate_pod_cost_data
    chart_generator_functions['pod_cost'] = generate_pod_cost_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_pod_cost_data: {e}")

try:
    from chart_generator import generate_namespace_data
    chart_generator_functions['namespace'] = generate_namespace_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_namespace_data: {e}")

try:
    from chart_generator import generate_workload_data
    chart_generator_functions['workload'] = generate_workload_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_workload_data: {e}")

try:
    from chart_generator import generate_dynamic_trend_data
    chart_generator_functions['trend'] = generate_dynamic_trend_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_dynamic_trend_data: {e}")

# Safe wrapper functions for chart generation
def safe_chart_function_call(func_name, func, *args, **kwargs):
    """Safely call a chart generation function with error handling"""
    try:
        logger.info(f"🔄 Starting {func_name} with args types: {[type(arg) for arg in args]}")
        
        # Special handling for trend data function which takes (cluster_id, analysis_data)
        if func_name == 'generate_dynamic_trend_data' and len(args) >= 2:
            cluster_id, analysis_data = args[0], args[1]
            if not isinstance(analysis_data, dict):
                logger.error(f"❌ {func_name}: Second argument (analysis_data) is {type(analysis_data)}, expected dict")
                debug_analysis_data_structure(analysis_data, f"{func_name}_validation_error")
                return None
            logger.info(f"✅ {func_name}: Trend data input validation passed (cluster_id: {type(cluster_id)}, analysis_data: {type(analysis_data)})")
        
        # Standard validation for other functions (first arg should be analysis_data dict)
        elif args:
            first_arg = args[0]
            if not validate_chart_input(first_arg, func_name):
                logger.error(f"❌ {func_name}: Input validation failed")
                return None
        
        # Additional logging for ML-integrated functions
        if 'ml' in func_name.lower() or 'generate_insights' in func_name:
            logger.info(f"🔄 {func_name}: ML-integrated function starting")
            debug_analysis_data_structure(args[0] if args else None, f"{func_name}_ml_input")
        
        result = func(*args, **kwargs)
        
        if result:
            logger.info(f"✅ {func_name} completed successfully with result type: {type(result)}")
        else:
            logger.warning(f"⚠️ {func_name} returned None/empty result")
            
        return result
        
    except AttributeError as attr_error:
        if "'str' object has no attribute 'get'" in str(attr_error):
            logger.error(f"❌ {func_name}: STRING INSTEAD OF DICT ERROR!")
            logger.error(f"❌ {func_name}: Error details: {attr_error}")
            if args:
                debug_analysis_data_structure(args[0], f"{func_name}_string_error")
        else:
            logger.error(f"❌ {func_name}: Attribute error - {attr_error}")
        return None
    except Exception as e:
        logger.error(f"❌ {func_name}: Unexpected error - {e}")
        logger.error(f"❌ {func_name}: Traceback: {traceback.format_exc()}")
        if args:
            logger.error(f"❌ {func_name}: Args types: {[type(arg) for arg in args]}")
            debug_analysis_data_structure(args[0], f"{func_name}_error")
        return None

# Cache management imports with fallback
try:
    from app.services.cache_manager import save_to_cache, is_cache_valid, clear_analysis_cache
    CACHE_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Cache manager not available, using fallback cache methods")
    CACHE_MANAGER_AVAILABLE = False


def register_api_routes(app):
    """Register all API routes with multi-subscription support and CPU workload integration - FIXED DUPLICATES"""
    
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
        """
        UNIFIED: Enhanced Chart data API with CPU workload integration and subscription awareness
        Combines functionality from both files
        """
        try:
            logger.info("📊 Enhanced chart data API called with CPU workload integration and subscription awareness")
            
            # Get cluster ID from request
            cluster_id = request.args.get('cluster_id')
            if not cluster_id:
                logger.error("❌ No cluster_id provided in chart data request")
                return jsonify({
                    'status': 'error',
                    'message': 'cluster_id parameter is required'
                }), 400
            
            logger.info(f"📊 ENHANCED: Chart data request for cluster: {cluster_id}")
            
            # Get cluster info with subscription context (with error handling)
            cluster = None
            try:
                cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster and cluster.get('subscription_id'):
                    logger.info(f"📊 Chart data for cluster {cluster_id} in subscription {cluster['subscription_id'][:8]}")
            except Exception as cluster_error:
                logger.warning(f"⚠️ Could not retrieve cluster info: {cluster_error}")
            
            # Get analysis data from database or cache
            analysis_data = get_cluster_analysis_data(cluster_id)
            
            if not analysis_data:
                logger.warning(f"⚠️ No analysis data found for cluster: {cluster_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available. Please run analysis first.'
                }), 404
            
            logger.info(f"✅ Found analysis data for cluster: {cluster_id}")
            
            # DEBUG: Log analysis data structure
            debug_analysis_data_structure(analysis_data, "chart_data_api")
            
            # Validate analysis_data is a dict before proceeding
            if not isinstance(analysis_data, dict):
                logger.error(f"❌ Chart API: analysis_data is {type(analysis_data)}, expected dict")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid analysis data format: expected dict, got {type(analysis_data)}',
                    'debug_info': {
                        'data_type': str(type(analysis_data)),
                        'data_preview': str(analysis_data)[:200] if isinstance(analysis_data, str) else str(analysis_data)
                    }
                }), 500
            
            # Extract basic metrics (now safe since we validated it's a dict)
            metrics = {
                'total_cost': ensure_float(analysis_data.get('total_cost', 0)),
                'total_savings': ensure_float(analysis_data.get('total_savings', 0)),
                'hpa_savings': ensure_float(analysis_data.get('hpa_savings', 0)),
                'right_sizing_savings': ensure_float(analysis_data.get('right_sizing_savings', 0)),
                'storage_savings': ensure_float(analysis_data.get('storage_savings', 0)),
                'savings_percentage': ensure_float(analysis_data.get('savings_percentage', 0)),
                'annual_savings': ensure_float(analysis_data.get('total_savings', 0)) * 12,
                'analysis_confidence': ensure_float(analysis_data.get('analysis_confidence', 0.8)),
                'hpa_efficiency': ensure_float(analysis_data.get('hpa_efficiency', 0)),
                'optimization_score': calculate_optimization_score(analysis_data),
                'cpu_gap': ensure_float(analysis_data.get('cpu_gap', 0)),
                'memory_gap': ensure_float(analysis_data.get('memory_gap', 0))
            }
            
            # ENHANCED: Generate comprehensive CPU workload data
            cpu_workload_data = extract_comprehensive_cpu_metrics(analysis_data)
            
            # Generate chart data with CPU awareness
            chart_data = {
                'status': 'success',
                'metrics': metrics,
                'cpuWorkloadMetrics': cpu_workload_data,  # NEW: CPU workload metrics
                'metadata': {
                    'cluster_id': cluster_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'is_real_data': True,
                    'has_cpu_analysis': cpu_workload_data['data_source'] != 'error_fallback',
                    'cpu_analysis_quality': cpu_workload_data.get('data_source', 'unknown'),
                    'subscription_id': cluster.get('subscription_id') if cluster else None,
                    'subscription_name': cluster.get('subscription_name') if cluster else None
                }
            }
            
            # Generate all chart datasets with error handling
            try:
                # Validate analysis_data type before chart generation
                if not isinstance(analysis_data, dict):
                    logger.error(f"❌ Chart generation: analysis_data is {type(analysis_data)}, expected dict")
                    raise ValueError(f"Invalid analysis_data type: {type(analysis_data)}")
                
                # Cost breakdown (internal function)
                try:
                    cost_breakdown = generate_cost_breakdown_chart_data(analysis_data)
                    if cost_breakdown:
                        chart_data['costBreakdown'] = cost_breakdown
                        logger.info("✅ Generated cost breakdown chart")
                except Exception as cost_error:
                    logger.warning(f"⚠️ Could not generate cost breakdown: {cost_error}")
                
                # Enhanced HPA comparison with CPU data (external function)
                if 'hpa_comparison' in chart_generator_functions:
                    try:
                        hpa_comparison = safe_chart_function_call(
                            'generate_dynamic_hpa_comparison', 
                            chart_generator_functions['hpa_comparison'], 
                            analysis_data
                        )
                        if hpa_comparison:
                            chart_data['hpaComparison'] = hpa_comparison
                            logger.info(f"✅ Generated HPA chart with CPU data: {hpa_comparison.get('has_high_cpu_alerts', False)}")
                    except Exception as hpa_error:
                        logger.warning(f"⚠️ Could not generate HPA comparison: {hpa_error}")
                
                # Node utilization (external function)
                if 'node_utilization' in chart_generator_functions:
                    try:
                        node_utilization = safe_chart_function_call(
                            'generate_node_utilization_data',
                            chart_generator_functions['node_utilization'],
                            analysis_data
                        )
                        if node_utilization:
                            chart_data['nodeUtilization'] = node_utilization
                            logger.info("✅ Generated node utilization chart")
                    except Exception as node_error:
                        logger.warning(f"⚠️ Could not generate node utilization: {node_error}")
                
                # Savings breakdown (internal function)
                try:
                    savings_breakdown = generate_savings_breakdown_data(analysis_data)
                    if savings_breakdown:
                        chart_data['savingsBreakdown'] = savings_breakdown
                        logger.info("✅ Generated savings breakdown chart")
                except Exception as savings_error:
                    logger.warning(f"⚠️ Could not generate savings breakdown: {savings_error}")
                
                # Trend data (external function)
                if 'trend' in chart_generator_functions:
                    try:
                        trend_data = safe_chart_function_call(
                            'generate_dynamic_trend_data',
                            chart_generator_functions['trend'],
                            cluster_id, analysis_data
                        )
                        if trend_data:
                            chart_data['trendData'] = trend_data
                            logger.info("✅ Generated trend data chart")
                    except Exception as trend_error:
                        logger.warning(f"⚠️ Could not generate trend data: {trend_error}")
                
                # Pod cost analysis (external functions)
                if analysis_data.get('has_pod_costs'):
                    if 'pod_cost' in chart_generator_functions:
                        try:
                            pod_cost_data = safe_chart_function_call(
                                'generate_pod_cost_data',
                                chart_generator_functions['pod_cost'],
                                analysis_data
                            )
                            if pod_cost_data:
                                chart_data['podCostBreakdown'] = pod_cost_data
                                logger.info("✅ Generated pod cost breakdown chart")
                        except Exception as pod_error:
                            logger.warning(f"⚠️ Could not generate pod cost data: {pod_error}")
                    
                    if 'namespace' in chart_generator_functions:
                        try:
                            namespace_data = safe_chart_function_call(
                                'generate_namespace_data',
                                chart_generator_functions['namespace'],
                                analysis_data
                            )
                            if namespace_data:
                                chart_data['namespaceDistribution'] = namespace_data
                                logger.info("✅ Generated namespace distribution chart")
                        except Exception as namespace_error:
                            logger.warning(f"⚠️ Could not generate namespace data: {namespace_error}")
                    
                    if 'workload' in chart_generator_functions:
                        try:
                            workload_data = safe_chart_function_call(
                                'generate_workload_data',
                                chart_generator_functions['workload'],
                                analysis_data
                            )
                            if workload_data:
                                chart_data['workloadCosts'] = workload_data
                                logger.info("✅ Generated workload costs chart")
                        except Exception as workload_error:
                            logger.warning(f"⚠️ Could not generate workload data: {workload_error}")
                
                # ENHANCED: Generate insights with CPU considerations (external function)
                if 'insights' in chart_generator_functions:
                    try:
                        insights = safe_chart_function_call(
                            'generate_insights',
                            chart_generator_functions['insights'],
                            analysis_data
                        )
                        if insights:
                            chart_data['insights'] = insights
                            logger.info(f"✅ Generated insights including CPU analysis")
                    except Exception as insights_error:
                        logger.warning(f"⚠️ Could not generate insights: {insights_error}")
                
            except Exception as chart_error:
                logger.error(f"❌ Error generating chart data: {chart_error}")
                # Continue with basic metrics even if chart generation fails
                chart_data['chart_generation_errors'] = str(chart_error)
                chart_data['chart_generation_debug'] = {
                    'analysis_data_type': str(type(analysis_data)),
                    'analysis_data_keys': list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'NOT_A_DICT'
                }
            
            logger.info(f"✅ ENHANCED: Chart data generated successfully for cluster: {cluster_id}")
            logger.info(f"📊 CPU Analysis: {cpu_workload_data['has_high_cpu_workloads']} high CPU workloads, "
                       f"avg: {cpu_workload_data['average_cpu_utilization']:.1f}%, "
                       f"max: {cpu_workload_data['max_cpu_utilization']:.1f}%")
            
            return jsonify(chart_data)
            
        except Exception as e:
            logger.error(f"❌ Enhanced chart data API error: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate enhanced chart data: {str(e)}',
                'error_type': 'enhanced_chart_data_error'
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

    @app.route('/api/clusters/<path:cluster_id>/analyze', methods=['POST'])
    def api_analyze_cluster(cluster_id: str):
        """Trigger subscription-aware analysis for specific cluster"""
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

    @app.route('/api/clusters/<path:cluster_id>/analysis-status', methods=['GET'])
    def get_cluster_analysis_status(cluster_id: str):
        """Get real-time analysis status for a cluster with subscription info"""
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
                    'multi_subscription_enabled': True,
                    'cpu_workload_support': True  # NEW: Indicate CPU workload support
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
                'multi_subscription_enabled': True,
                'cpu_workload_support': True
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'status': 'error',
                'multi_subscription_enabled': True,
                'cpu_workload_support': True
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


# UNIFIED: Helper functions combining functionality from both files
def get_cluster_analysis_data(cluster_id):
    """
    Get cluster analysis data from database/cache with subscription awareness
    """
    try:
        # Try cache first using the existing cache structure
        if cluster_id in analysis_cache.get('clusters', {}):
            cached_entry = analysis_cache['clusters'][cluster_id]
            
            # Check if cache is still valid (not expired)
            cache_valid = True
            if CACHE_MANAGER_AVAILABLE:
                try:
                    cache_valid = is_cache_valid(cluster_id)
                except Exception as cache_check_error:
                    logger.warning(f"⚠️ Could not check cache validity: {cache_check_error}")
                    cache_valid = True  # Assume valid if we can't check
            
            if cache_valid:
                cached_data = cached_entry.get('data')
                if cached_data:
                    logger.info(f"✅ Retrieved analysis data from cache for: {cluster_id}")
                    debug_analysis_data_structure(cached_data, f"cache_retrieval_{cluster_id}")
                    return cached_data
            else:
                logger.info(f"🔄 Cache expired for cluster: {cluster_id}")
        
        # Try database using the shared function
        logger.info(f"🔍 Retrieving analysis data from database for: {cluster_id}")
        current_analysis, data_source = _get_analysis_data(cluster_id)
        
        if current_analysis:
            logger.info(f"✅ Retrieved analysis data from {data_source} for: {cluster_id}")
            debug_analysis_data_structure(current_analysis, f"database_retrieval_{cluster_id}_{data_source}")
            
            # Validate the retrieved data is a dictionary
            if not isinstance(current_analysis, dict):
                logger.error(f"❌ Database returned {type(current_analysis)} instead of dict for {cluster_id}")
                logger.error(f"❌ Data preview: {str(current_analysis)[:200]}")
                return None
            
            # Cache for future requests using existing cache manager
            if CACHE_MANAGER_AVAILABLE:
                try:
                    save_to_cache(cluster_id, current_analysis)
                    logger.info(f"💾 Cached analysis data for: {cluster_id}")
                except Exception as cache_error:
                    logger.warning(f"⚠️ Could not cache data for {cluster_id}: {cache_error}")
            else:
                # Fallback: store directly in analysis_cache
                try:
                    if 'clusters' not in analysis_cache:
                        analysis_cache['clusters'] = {}
                    analysis_cache['clusters'][cluster_id] = {
                        'data': current_analysis,
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"💾 Cached analysis data (fallback) for: {cluster_id}")
                except Exception as fallback_cache_error:
                    logger.warning(f"⚠️ Could not fallback cache data for {cluster_id}: {fallback_cache_error}")
            
            return current_analysis
        
        logger.warning(f"⚠️ No analysis data found for cluster: {cluster_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error retrieving analysis data for {cluster_id}: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None


def extract_comprehensive_cpu_metrics(analysis_data):
    """
    Extract comprehensive CPU metrics from analysis data with enhanced workload integration
    """
    try:
        # Validate input data type
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ CPU metrics extraction: Expected dict, got {type(analysis_data)}")
            return {
                'has_high_cpu_workloads': False,
                'high_cpu_count': 0,
                'max_cpu_utilization': 0.0,
                'average_cpu_utilization': 0.0,
                'severity_level': 'none',
                'high_cpu_workloads': [],
                'data_source': 'type_error_fallback'
            }
        
        # Try to import and call the CPU workload function safely
        try:
            from chart_generator import _extract_cpu_workload_data_comprehensive
            logger.info("🔄 Calling _extract_cpu_workload_data_comprehensive")
            result = safe_chart_function_call(
                '_extract_cpu_workload_data_comprehensive',
                _extract_cpu_workload_data_comprehensive,
                analysis_data
            )
            if result:
                return result
            else:
                logger.warning("⚠️ CPU workload function returned None, using fallback")
        except ImportError as import_error:
            logger.warning(f"⚠️ Could not import CPU workload function: {import_error}")
        except Exception as cpu_error:
            logger.error(f"❌ Error in CPU workload extraction: {cpu_error}")
        
        # Fallback: extract basic CPU info from analysis_data
        logger.info("🔄 Using fallback CPU metrics extraction")
        return extract_fallback_cpu_metrics(analysis_data)
        
    except Exception as e:
        logger.error(f"❌ Error extracting CPU metrics: {e}")
        return {
            'has_high_cpu_workloads': False,
            'high_cpu_count': 0,
            'max_cpu_utilization': 0.0,
            'average_cpu_utilization': 0.0,
            'severity_level': 'none',
            'high_cpu_workloads': [],
            'data_source': 'error_fallback'
        }


def extract_fallback_cpu_metrics(analysis_data):
    """
    Fallback CPU metrics extraction from analysis data
    """
    try:
        # Look for CPU-related data in various places
        cpu_data = {
            'has_high_cpu_workloads': False,
            'high_cpu_count': 0,
            'max_cpu_utilization': 0.0,
            'average_cpu_utilization': 0.0,
            'severity_level': 'none',
            'high_cpu_workloads': [],
            'data_source': 'fallback_extraction'
        }
        
        # Check node metrics for CPU data
        if 'node_metrics' in analysis_data and isinstance(analysis_data['node_metrics'], dict):
            node_metrics = analysis_data['node_metrics']
            
            # Look for CPU utilization in node metrics
            for node_name, metrics in node_metrics.items():
                if isinstance(metrics, dict):
                    cpu_util = metrics.get('cpu_utilization', 0)
                    if cpu_util:
                        cpu_data['max_cpu_utilization'] = max(cpu_data['max_cpu_utilization'], ensure_float(cpu_util))
                        if ensure_float(cpu_util) > 80:
                            cpu_data['has_high_cpu_workloads'] = True
                            cpu_data['high_cpu_count'] += 1
        
        # Check for direct CPU fields
        for field in ['cpu_utilization', 'avg_cpu', 'cpu_usage']:
            if field in analysis_data:
                cpu_val = ensure_float(analysis_data[field])
                cpu_data['average_cpu_utilization'] = max(cpu_data['average_cpu_utilization'], cpu_val)
        
        # Determine severity
        if cpu_data['max_cpu_utilization'] > 90:
            cpu_data['severity_level'] = 'critical'
        elif cpu_data['max_cpu_utilization'] > 80:
            cpu_data['severity_level'] = 'high'
        elif cpu_data['max_cpu_utilization'] > 60:
            cpu_data['severity_level'] = 'medium'
        else:
            cpu_data['severity_level'] = 'low'
        
        logger.info(f"✅ Fallback CPU extraction: max={cpu_data['max_cpu_utilization']:.1f}%, avg={cpu_data['average_cpu_utilization']:.1f}%")
        return cpu_data
        
    except Exception as e:
        logger.error(f"❌ Fallback CPU extraction failed: {e}")
        return {
            'has_high_cpu_workloads': False,
            'high_cpu_count': 0,
            'max_cpu_utilization': 0.0,
            'average_cpu_utilization': 0.0,
            'severity_level': 'none',
            'high_cpu_workloads': [],
            'data_source': 'fallback_error'
        }


def generate_cost_breakdown_chart_data(analysis_data):
    """Generate cost breakdown chart data with subscription awareness"""
    try:
        # Validate input data type
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ Cost breakdown: Expected dict, got {type(analysis_data)}")
            return None
        
        cost_categories = []
        cost_values = []
        
        # Extract cost components
        cost_components = [
            ('Node Pools', analysis_data.get('node_cost', 0)),
            ('Storage', analysis_data.get('storage_cost', 0)),
            ('Networking', analysis_data.get('networking_cost', 0)),
            ('Control Plane', analysis_data.get('control_plane_cost', 0)),
            ('Container Registry', analysis_data.get('registry_cost', 0)),
            ('Key Vault', analysis_data.get('key_vault_cost', 0)),
            ('Other', analysis_data.get('other_cost', 0))
        ]
        
        # Filter out zero values
        for category, value in cost_components:
            if value and value > 0:
                cost_categories.append(category)
                cost_values.append(float(value))
        
        if not cost_categories:
            logger.info("ℹ️ No cost categories found for breakdown chart")
            return None
        
        return {
            'labels': cost_categories,
            'values': cost_values,
            'total_cost': sum(cost_values),
            'data_source': 'real_analysis',
            'subscription_aware': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating cost breakdown: {e}")
        return None


def generate_savings_breakdown_data(analysis_data):
    """Generate savings breakdown chart data with CPU workload considerations"""
    try:
        # Validate input data type
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ Savings breakdown: Expected dict, got {type(analysis_data)}")
            return None
        
        categories = []
        values = []
        
        # Extract savings components
        savings_components = [
            ('HPA Optimization', analysis_data.get('hpa_savings', 0)),
            ('Right-sizing', analysis_data.get('right_sizing_savings', 0)),
            ('Storage Optimization', analysis_data.get('storage_savings', 0)),
            ('CPU Optimization', analysis_data.get('cpu_optimization_savings', 0))  # NEW: CPU-specific savings
        ]
        
        # Filter out zero values
        for category, value in savings_components:
            if value and value > 0:
                categories.append(category)
                values.append(float(value))
        
        if not categories:
            logger.info("ℹ️ No savings categories found for breakdown chart")
            return None
        
        return {
            'categories': categories,
            'values': values,
            'total_savings': sum(values),
            'data_source': 'real_analysis',
            'cpu_workload_aware': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating savings breakdown: {e}")
        return None


def calculate_optimization_score(analysis_data):
    """Calculate optimization score based on analysis data with CPU workload factors"""
    try:
        # Validate input data type
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ Optimization score: Expected dict, got {type(analysis_data)}")
            return 50  # Default score
        
        total_cost = ensure_float(analysis_data.get('total_cost', 0))
        total_savings = ensure_float(analysis_data.get('total_savings', 0))
        
        if total_cost <= 0:
            return 0
        
        savings_percentage = (total_savings / total_cost) * 100
        
        # Factor in CPU workload efficiency
        cpu_efficiency_bonus = 0
        if analysis_data.get('has_cpu_analysis'):
            avg_cpu = ensure_float(analysis_data.get('average_cpu_utilization', 0))
            if avg_cpu > 80:  # High CPU utilization
                cpu_efficiency_bonus = -10  # Penalty for over-utilization
            elif avg_cpu < 30:  # Low CPU utilization
                cpu_efficiency_bonus = 5   # Bonus for under-utilization opportunity
        
        # Convert to 1-100 score with CPU considerations
        base_score = 0
        if savings_percentage > 25:
            base_score = min(100, 80 + (savings_percentage - 25))
        elif savings_percentage > 15:
            base_score = 60 + (savings_percentage - 15) * 2
        elif savings_percentage > 5:
            base_score = 40 + (savings_percentage - 5)
        else:
            base_score = max(10, savings_percentage * 8)
        
        final_score = max(0, min(100, base_score + cpu_efficiency_bonus))
        return final_score
        
    except Exception as e:
        logger.error(f"❌ Error calculating optimization score: {e}")
        return 50  # Default score


def ensure_float(value):
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def debug_analysis_data_structure(analysis_data, context="unknown"):
    """Debug helper to log analysis data structure"""
    try:
        logger.info(f"🔍 DEBUG [{context}]: analysis_data type = {type(analysis_data)}")
        
        if isinstance(analysis_data, dict):
            logger.info(f"🔍 DEBUG [{context}]: Keys = {list(analysis_data.keys())}")
            # Log a few key values for debugging
            key_values = {}
            for key in ['total_cost', 'total_savings', 'cluster_name', 'resource_group', 'node_metrics', 'real_node_data']:
                if key in analysis_data:
                    value = analysis_data[key]
                    key_values[key] = f"{type(value)} = {str(value)[:100] if isinstance(value, (str, list)) else value}"
            if key_values:
                logger.info(f"🔍 DEBUG [{context}]: Key values = {key_values}")
                
        elif isinstance(analysis_data, str):
            logger.warning(f"🔍 DEBUG [{context}]: STRING DETECTED! Content (first 200 chars): {analysis_data[:200]}")
            logger.warning(f"🔍 DEBUG [{context}]: Full string length: {len(analysis_data)}")
            
        elif isinstance(analysis_data, list):
            logger.info(f"🔍 DEBUG [{context}]: List length = {len(analysis_data)}")
            if analysis_data:
                logger.info(f"🔍 DEBUG [{context}]: First element type = {type(analysis_data[0])}")
        else:
            logger.warning(f"🔍 DEBUG [{context}]: Unexpected type, value = {str(analysis_data)[:200]}")
            
    except Exception as debug_error:
        logger.warning(f"⚠️ Debug logging failed for [{context}]: {debug_error}")


def validate_chart_input(analysis_data, function_name):
    """Validate that input data is appropriate for chart generation"""
    if not isinstance(analysis_data, dict):
        logger.error(f"❌ {function_name}: VALIDATION FAILED - Expected dict, got {type(analysis_data)}")
        debug_analysis_data_structure(analysis_data, f"{function_name}_validation_error")
        return False
    
    # Check for required keys
    required_keys = ['total_cost', 'total_savings']
    missing_keys = [key for key in required_keys if key not in analysis_data]
    if missing_keys:
        logger.warning(f"⚠️ {function_name}: Missing keys {missing_keys}, but proceeding")
    
    logger.info(f"✅ {function_name}: Input validation passed")
    return True