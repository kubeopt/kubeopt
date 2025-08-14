"""
Unified API Routes for Multi-Subscription AKS Cost Optimization Tool
with Enhanced Alerts Integration - FIXED REGISTRATION
"""

import traceback
from datetime import datetime
from flask import request, jsonify, Response
import sys
import os
import threading
import concurrent.futures
from typing import List

# Add the current directory to the path for imports
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# FIXED IMPORTS - use correct relative imports
from app.main.config import (
    logger, enhanced_cluster_manager, analysis_status_tracker, 
    _analysis_lock, _analysis_sessions, analysis_cache
)
from app.services.background_processor import run_subscription_aware_background_analysis
from app.main.shared import _get_analysis_data  # Import from shared module
from app.services.subscription_manager import azure_subscription_manager
from app.data.processing.analysis_engine import multi_subscription_analysis_engine

# FIXED: Import alerts integration
from app.services.alerts_integration import initialize_alerts_system, register_alerts_routes, get_alerts_manager

from app.interface.project_controls_api import integrate_project_controls_api
from app.security.security_api_blueprint import security_api

# FIXED: Import chart functions from correct location
chart_generator_functions = {}
try:
    from app.interface.chart_generator import generate_dynamic_hpa_comparison
    chart_generator_functions['hpa_comparison'] = generate_dynamic_hpa_comparison
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_dynamic_hpa_comparison: {e}")

try:
    from app.interface.chart_generator import generate_insights
    chart_generator_functions['insights'] = generate_insights
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_insights: {e}")

try:
    from app.interface.chart_generator import generate_node_utilization_data
    chart_generator_functions['node_utilization'] = generate_node_utilization_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_node_utilization_data: {e}")

try:
    from app.interface.chart_generator import generate_pod_cost_data
    chart_generator_functions['pod_cost'] = generate_pod_cost_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_pod_cost_data: {e}")

try:
    from app.interface.chart_generator import generate_namespace_data
    chart_generator_functions['namespace'] = generate_namespace_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_namespace_data: {e}")

try:
    from app.interface.chart_generator import generate_workload_data
    chart_generator_functions['workload'] = generate_workload_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_workload_data: {e}")

try:
    from app.interface.chart_generator import generate_dynamic_trend_data
    chart_generator_functions['trend'] = generate_dynamic_trend_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import generate_dynamic_trend_data: {e}")

# FIXED: Import CPU data extraction function
try:
    from app.interface.chart_generator import _extract_cpu_workload_data
    chart_generator_functions['cpu_workload'] = _extract_cpu_workload_data
except ImportError as e:
    logger.warning(f"⚠️ Could not import _extract_cpu_workload_data: {e}")

# Cache management imports with fallback
try:
    from app.services.cache_manager import save_to_cache, is_cache_valid, clear_analysis_cache
    CACHE_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Cache manager not available, using fallback cache methods")
    CACHE_MANAGER_AVAILABLE = False

# Global alerts manager
alerts_manager = None

def trigger_alert_checking_after_analysis(cluster_id: str, analysis_results: dict):
    """🆕 ENSURE ALERTS ARE CHECKED AFTER ANALYSIS COMPLETES"""
    try:
        logger.info(f"🚨 Triggering alert checking for cluster {cluster_id}")
        
        alerts_manager = get_alerts_manager()
        if not alerts_manager:
            logger.warning("⚠️ Alerts manager not available for alert checking")
            return []
        
        # Get cluster information
        cluster = enhanced_cluster_manager.get_cluster(cluster_id) if enhanced_cluster_manager else None
        if not cluster:
            logger.warning(f"⚠️ Cluster {cluster_id} not found")
            return []
        
        # Extract current cost from analysis results
        current_cost = 0.0
        cost_sources = ['total_cost', 'monthly_cost', 'current_month_cost', 'total_monthly_cost']
        
        for source in cost_sources:
            if source in analysis_results and analysis_results[source] is not None:
                try:
                    current_cost = float(analysis_results[source])
                    if current_cost > 0:
                        logger.info(f"💰 Found cost data from '{source}': ${current_cost:.2f}")
                        break
                except (ValueError, TypeError):
                    continue
        
        if current_cost <= 0:
            logger.warning(f"⚠️ No valid cost data found for cluster {cluster_id} - cannot check alerts")
            return []
        
        logger.info(f"🔍 Checking alerts for cluster {cluster_id} with cost ${current_cost:.2f}")
        
        # Check and trigger alerts
        triggered_alerts = alerts_manager.check_cluster_alerts(cluster_id, current_cost)
        
        if triggered_alerts:
            logger.info(f"🚨 Alert check completed: {len(triggered_alerts)} alerts triggered")
            for triggered_alert in triggered_alerts:
                alert = triggered_alert['alert']
                logger.info(f"   ✅ Alert '{alert['name']}': ${current_cost:.2f} > ${alert['threshold_amount']:.2f}")
        else:
            logger.info(f"✅ Alert check completed: No alerts triggered for cluster {cluster_id}")
        
        return triggered_alerts
        
    except Exception as e:
        logger.error(f"❌ Error in post-analysis alert checking: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return []

def register_api_routes(app):
    """Register all API routes with multi-subscription support and complete alerts integration"""
    
    # Initialize and register alerts system
    global alerts_manager
    try:
        alerts_manager = initialize_alerts_system()
        register_alerts_routes(app)
        integrate_project_controls_api(app)
        app.register_blueprint(security_api)
        logger.info("✅ Routes registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register alerts routes: {e}")

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
        
    @app.route('/api/clusters/<cluster_id>/analysis-progress-stream')
    def analysis_progress_stream(cluster_id):
        """Server-Sent Events endpoint for real-time analysis progress"""
        import time
        import json
        from flask import Response
        
        def generate():
            last_update = time.time()
            max_duration = 600  # 10 minutes max
            
            while time.time() - last_update < max_duration:
                try:
                    # Get current analysis status using existing method
                    status_data = enhanced_cluster_manager.get_analysis_status_for_sse(cluster_id)
                    
                    if status_data:
                        # Send SSE formatted data
                        yield f"data: {json.dumps(status_data)}\n\n"
                        
                        # Check if analysis is complete
                        if status_data.get('analysis_status') in ['completed', 'success', 'failed']:
                            logger.info(f"📊 SSE: Analysis {status_data.get('analysis_status')} for {cluster_id}")
                            break
                        
                        last_update = time.time()
                    
                    time.sleep(2)  # 2-second intervals instead of 20-second polling
                    
                except Exception as e:
                    logger.error(f"❌ SSE error for {cluster_id}: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break
        
        response = Response(
            generate(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        response.headers['Content-Type'] = 'text/event-stream'
        return response   

    @app.route('/api/chart-data')
    def api_chart_data():
        """
        Chart data API with CPU workload integration
        """
        try:
            logger.info("📊 Enhanced chart data API called")
            
            # Get cluster ID from request
            cluster_id = request.args.get('cluster_id')
            if not cluster_id:
                logger.error("❌ No cluster_id provided in chart data request")
                return jsonify({
                    'status': 'error',
                    'message': 'cluster_id parameter is required'
                }), 400
            
            logger.info(f"📊 REAL DATA: Chart data request for cluster: {cluster_id}")
            
            # Get cluster info with subscription context
            cluster = None
            try:
                cluster = enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster and cluster.get('subscription_id'):
                    logger.info(f"📊 Chart data for cluster {cluster_id} in subscription {cluster['subscription_id'][:8]}")
            except Exception as cluster_error:
                logger.warning(f"⚠️ Could not retrieve cluster info: {cluster_error}")
            
            # Get REAL analysis data from database or cache
            analysis_data = get_cluster_analysis_data(cluster_id)
            
            if not analysis_data:
                logger.warning(f"⚠️ No analysis data found for cluster: {cluster_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available. Please run analysis first.'
                }), 404
            
            logger.info(f"✅ Found REAL analysis data for cluster: {cluster_id}")
            
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
            
            # Extract basic metrics from REAL data
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
            
            # FIXED: Generate REAL CPU workload data with proper error handling
            cpu_workload_data = extract_real_cpu_metrics(analysis_data)
            
            # Generate chart data with REAL CPU awareness
            chart_data = {
                'status': 'success',
                'metrics': metrics,
                'cpuWorkloadMetrics': cpu_workload_data,  # REAL CPU workload metrics
                'metadata': {
                    'cluster_id': cluster_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'is_real_data': True,
                    'has_cpu_analysis': cpu_workload_data.get('cpu_analysis_available', False),
                    'cpu_analysis_quality': 'real_ml_data' if cpu_workload_data.get('has_high_cpu_workloads') else 'basic_analysis',
                    'subscription_id': cluster.get('subscription_id') if cluster else None,
                    'subscription_name': cluster.get('subscription_name') if cluster else None,
                    'real_data_only': True
                }
            }
            
            # Generate all chart datasets with REAL data validation
            try:
                # Validate analysis_data type before chart generation
                if not isinstance(analysis_data, dict):
                    logger.error(f"❌ Chart generation: analysis_data is {type(analysis_data)}, expected dict")
                    raise ValueError(f"Invalid analysis_data type: {type(analysis_data)}")
                
                # Cost breakdown (internal function) - REAL DATA ONLY
                try:
                    cost_breakdown = generate_real_cost_breakdown_chart_data(analysis_data)
                    if cost_breakdown:
                        chart_data['costBreakdown'] = cost_breakdown
                        logger.info("✅ Generated REAL cost breakdown chart")
                except Exception as cost_error:
                    logger.error(f"❌ Could not generate cost breakdown: {cost_error}")
                
                # Enhanced HPA comparison with CPU data (external function) - REAL DATA ONLY
                if 'hpa_comparison' in chart_generator_functions:
                    try:
                        hpa_comparison = safe_chart_function_call(
                            'generate_dynamic_hpa_comparison', 
                            chart_generator_functions['hpa_comparison'], 
                            analysis_data
                        )
                        if hpa_comparison:
                            chart_data['hpaComparison'] = hpa_comparison
                            logger.info(f"✅ Generated REAL HPA chart with CPU data: {hpa_comparison.get('has_high_cpu_alerts', False)}")
                    except Exception as hpa_error:
                        logger.error(f"❌ Could not generate HPA comparison: {hpa_error}")
                
                # Node utilization (external function) - REAL DATA ONLY
                if 'node_utilization' in chart_generator_functions:
                    try:
                        node_utilization = safe_chart_function_call(
                            'generate_node_utilization_data',
                            chart_generator_functions['node_utilization'],
                            analysis_data
                        )
                        if node_utilization:
                            chart_data['nodeUtilization'] = node_utilization
                            logger.info("✅ Generated REAL node utilization chart")
                    except Exception as node_error:
                        logger.error(f"❌ Could not generate node utilization: {node_error}")
                
                # Savings breakdown (internal function) - REAL DATA ONLY
                try:
                    savings_breakdown = generate_real_savings_breakdown_data(analysis_data)
                    if savings_breakdown:
                        chart_data['savingsBreakdown'] = savings_breakdown
                        logger.info("✅ Generated REAL savings breakdown chart")
                except Exception as savings_error:
                    logger.error(f"❌ Could not generate savings breakdown: {savings_error}")
                
                # Trend data (external function) - REAL DATA ONLY
                if 'trend' in chart_generator_functions:
                    try:
                        trend_data = safe_chart_function_call(
                            'generate_dynamic_trend_data',
                            chart_generator_functions['trend'],
                            cluster_id, analysis_data
                        )
                        if trend_data:
                            chart_data['trendData'] = trend_data
                            logger.info("✅ Generated REAL trend data chart")
                    except Exception as trend_error:
                        logger.error(f"❌ Could not generate trend data: {trend_error}")
                
                # Pod cost analysis (external functions) - REAL DATA ONLY
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
                                logger.info("✅ Generated REAL pod cost breakdown chart")
                        except Exception as pod_error:
                            logger.error(f"❌ Could not generate pod cost data: {pod_error}")
                    
                    if 'namespace' in chart_generator_functions:
                        try:
                            namespace_data = safe_chart_function_call(
                                'generate_namespace_data',
                                chart_generator_functions['namespace'],
                                analysis_data
                            )
                            if namespace_data:
                                chart_data['namespaceDistribution'] = namespace_data
                                logger.info("✅ Generated REAL namespace distribution chart")
                        except Exception as namespace_error:
                            logger.error(f"❌ Could not generate namespace data: {namespace_error}")
                    
                    if 'workload' in chart_generator_functions:
                        try:
                            workload_data = safe_chart_function_call(
                                'generate_workload_data',
                                chart_generator_functions['workload'],
                                analysis_data
                            )
                            if workload_data:
                                chart_data['workloadCosts'] = workload_data
                                logger.info("✅ Generated REAL workload costs chart")
                        except Exception as workload_error:
                            logger.error(f"❌ Could not generate workload data: {workload_error}")
                
                # Generate insights with CPU considerations (external function) - REAL DATA ONLY
                if 'insights' in chart_generator_functions:
                    try:
                        insights = safe_chart_function_call(
                            'generate_insights',
                            chart_generator_functions['insights'],
                            analysis_data
                        )
                        if insights:
                            chart_data['insights'] = insights
                            logger.info(f"✅ Generated REAL insights including CPU analysis")
                    except Exception as insights_error:
                        logger.error(f"❌ Could not generate insights: {insights_error}")
                
            except Exception as chart_error:
                logger.error(f"❌ Error generating chart data: {chart_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to generate chart data: {chart_error}',
                    'cluster_id': cluster_id
                }), 500
            
            logger.info(f"✅ REAL DATA: Chart data generated successfully for cluster: {cluster_id}")
            logger.info(f"📊 CPU Analysis: {cpu_workload_data.get('has_high_cpu_workloads', False)} high CPU workloads, "
                       f"avg: {cpu_workload_data.get('average_cpu_utilization', 0):.1f}%, "
                       f"max: {cpu_workload_data.get('max_cpu_utilization', 0):.1f}%")
            
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
        """ ENHANCED: Implementation plan API with format selection and better error handling"""
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
            
            # NEW: Check format parameter
            format_type = request.args.get('format', 'comprehensive')  # 'comprehensive' or 'timeline'
            logger.info(f"📋 Format requested: {format_type}")
            
            # Get cluster info
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Get analysis data
            current_analysis, data_source = _get_analysis_data(cluster_id)
            
            if not current_analysis:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available for implementation plan',
                    'cluster_id': cluster_id,
                    'data_source': data_source
                }), 404
            
            # Validate analysis data has required fields
            required_fields = ['total_cost', 'total_savings']
            missing_fields = [field for field in required_fields if field not in current_analysis]
            
            if missing_fields:
                logger.error(f"❌ Analysis data missing required fields: {missing_fields}")
                return jsonify({
                    'status': 'error',
                    'message': f'Analysis data incomplete. Missing: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }), 500
            
            # Add cluster metadata to analysis data
            current_analysis['cluster_name'] = cluster['name']
            current_analysis['resource_group'] = cluster['resource_group']
            
            # MODIFIED: Use enhanced generator with format support
            implementation_plan = current_analysis.get('implementation_plan')
            
            # Check if we need to generate/regenerate the plan
            needs_generation = (
                not implementation_plan or 
                not isinstance(implementation_plan, dict) or 
                'implementation_phases' not in implementation_plan or
                not implementation_plan['implementation_phases'] or
                not isinstance(implementation_plan['implementation_phases'], list) or
                len(implementation_plan['implementation_phases']) == 0
            )
            
            if needs_generation:
                logger.info(f"🔄 API: Generating implementation plan for {cluster_id} in {format_type} format")
                try:
                    from app.main.config import implementation_generator
                    from app.services.cache_manager import save_to_cache
                    
                    # MODIFIED: Generate with format parameter
                    fresh_plan = implementation_generator.generate_implementation_plan_for_api(
                        current_analysis, 
                        output_format=format_type
                    )
                    
                    # Validate the generated plan
                    if not isinstance(fresh_plan, dict):
                        logger.error(f"❌ Generator returned {type(fresh_plan)}, expected dict")
                        raise ValueError(f"Generator returned invalid type: {type(fresh_plan)}")
                    
                    # Validate based on format
                    if format_type == 'timeline':
                        if 'weeks' not in fresh_plan:
                            logger.error(f"❌ Timeline format missing 'weeks' key")
                            raise ValueError("Timeline format missing 'weeks' key")
                    else:
                        if 'implementation_phases' not in fresh_plan:
                            logger.error(f"❌ Comprehensive format missing 'implementation_phases' key")
                            raise ValueError("Comprehensive format missing 'implementation_phases' key")
                    
                    # Add API metadata
                    fresh_plan['api_metadata'] = {
                        'data_source': data_source,
                        'cluster_id': cluster_id,
                        'cluster_name': cluster['name'],
                        'resource_group': cluster['resource_group'],
                        'subscription_id': cluster.get('subscription_id'),
                        'subscription_name': cluster.get('subscription_name'),
                        'format_type': format_type,
                        'api_generated_at': datetime.now().isoformat(),
                        'total_cost': current_analysis.get('total_cost', 0),
                        'total_savings': current_analysis.get('total_savings', 0)
                    }
                    
                    # Update cache and database
                    current_analysis['implementation_plan'] = fresh_plan
                    implementation_plan = fresh_plan
                    
                    try:
                        subscription_id = azure_subscription_manager.get_current_subscription()
                        save_to_cache(cluster_id, current_analysis, subscription_id)
                        enhanced_cluster_manager.update_cluster_analysis(cluster_id, current_analysis)
                        logger.info(f"✅ API: Saved generated implementation plan for {cluster_id}")
                    except Exception as save_error:
                        logger.warning(f"⚠️ Failed to save generated plan: {save_error}")
                    
                except Exception as gen_error:
                    logger.error(f"❌ API: Failed to generate implementation plan: {gen_error}")
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to generate implementation plan: {str(gen_error)}',
                        'error_details': {
                            'cluster_id': cluster_id,
                            'data_source': data_source,
                            'format_type': format_type,
                            'error_type': type(gen_error).__name__
                        }
                    }), 500
            else:
                logger.info(f"✅ API: Using existing implementation plan for {cluster_id}")
                
                # If we have existing comprehensive plan but timeline format requested, convert it
                if format_type == 'timeline' and 'weeks' not in implementation_plan:
                    logger.info(f"🔄 Converting existing plan to timeline format for {cluster_id}")
                    try:
                        from app.main.config import implementation_generator
                        converted_plan = implementation_generator._convert_to_timeline_format(
                            implementation_plan, current_analysis, {'session_id': 'api-conversion'}
                        )
                        implementation_plan = converted_plan
                    except Exception as convert_error:
                        logger.warning(f"⚠️ Timeline conversion failed: {convert_error}")
                        # Continue with original plan
            
            # REMOVED: Problematic framework mapping logic - now handled by implementation generator
            
            # Final validation before returning - adapted for format
            if format_type == 'timeline':
                if 'weeks' not in implementation_plan or not isinstance(implementation_plan['weeks'], list):
                    logger.error(f"❌ Final validation failed for timeline format")
                    return jsonify({
                        'status': 'error',
                        'message': 'Timeline format validation failed',
                        'validation_details': {
                            'format_type': format_type,
                            'has_weeks': 'weeks' in implementation_plan,
                            'weeks_type': str(type(implementation_plan.get('weeks', 'missing'))),
                            'plan_keys': list(implementation_plan.keys())
                        }
                    }), 500
            else:
                phases = implementation_plan.get('implementation_phases', [])
                if not isinstance(phases, list) or len(phases) == 0:
                    logger.error(f"❌ Final validation failed - phases: {type(phases)}, count: {len(phases) if isinstance(phases, list) else 'N/A'}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Implementation plan validation failed',
                        'validation_details': {
                            'format_type': format_type,
                            'phases_type': str(type(phases)),
                            'phases_count': len(phases) if isinstance(phases, list) else 'N/A',
                            'plan_keys': list(implementation_plan.keys())
                        }
                    }), 500
            
            # Ensure API metadata exists
            if 'api_metadata' not in implementation_plan:
                implementation_plan['api_metadata'] = {
                    'data_source': data_source,
                    'cluster_id': cluster_id,
                    'cluster_name': cluster['name'],
                    'resource_group': cluster['resource_group'],
                    'subscription_id': cluster.get('subscription_id'),
                    'subscription_name': cluster.get('subscription_name'),
                    'format_type': format_type,
                    'api_called_at': datetime.now().isoformat(),
                    'total_cost': current_analysis.get('total_cost', 0),
                    'total_savings': current_analysis.get('total_savings', 0)
                }
            
            # Add format metadata
            implementation_plan['format_metadata'] = {
                'current_format': format_type,
                'supports_both_formats': True,
                'comprehensive_endpoint': f'/api/implementation-plan?cluster_id={cluster_id}&format=comprehensive',
                'timeline_endpoint': f'/api/implementation-plan?cluster_id={cluster_id}&format=timeline'
            }
            
            logger.info(f"✅ API: Returning {format_type} implementation plan for {cluster_id}")
            
            return jsonify(implementation_plan)
            
        except Exception as e:
            logger.error(f"❌ Error in implementation plan API: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Implementation plan API error: {str(e)}',
                'error_type': type(e).__name__,
                'format_type': request.args.get('format', 'comprehensive')
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
                    
                    # 🆕 ENHANCED: Start analysis with alert checking
                    analysis_thread = threading.Thread(
                        target=run_subscription_aware_background_analysis_with_alerts,
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
            
            # 🆕 ENHANCED: Start analysis with alert checking
            analysis_thread = threading.Thread(
                target=run_subscription_aware_background_analysis_with_alerts,
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
                    'cpu_workload_support': True,
                    'real_data_only': True
                }
                
                if request.args.get('include_full_results') == 'true':
                    debug_info['full_results'] = current_analysis
                
                return jsonify(debug_info)
            
            # NO FALLBACK - return error if no cluster_id
            return jsonify({
                'status': 'error',
                'message': 'No cluster_id provided for debug analysis',
                'multi_subscription_enabled': True,
                'cpu_workload_support': True,
                'real_data_only': True
            }), 400
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'status': 'error',
                'multi_subscription_enabled': True,
                'cpu_workload_support': True,
                'real_data_only': True
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

# 🆕 ENHANCED BACKGROUND ANALYSIS WITH ALERT INTEGRATION
def run_subscription_aware_background_analysis_with_alerts(cluster_id, resource_group, cluster_name, subscription_id, days=30, enable_pod_analysis=True):
    """Enhanced background analysis that triggers alert checking and stores security results"""
    try:
        logger.info(f"🚀 Starting subscription-aware analysis with alert checking for cluster: {cluster_id}")
        
        # Run the standard background analysis
        run_subscription_aware_background_analysis(cluster_id, resource_group, cluster_name, subscription_id, days, enable_pod_analysis)
        
        # After analysis completes: Check for alerts
        logger.info(f"🔍 Analysis completed, now checking alerts for cluster: {cluster_id}")
        
        # Get the completed analysis results
        analysis_data, data_source = _get_analysis_data(cluster_id)
        
        if analysis_data:
            logger.info(f"✅ Retrieved analysis data for alert checking: {data_source}")
            
            # NEW: Check if security analysis was performed and store results
            if 'security_analysis' in analysis_data and analysis_data['security_analysis']:
                try:
                    from app.security.security_results_manager import security_results_manager
                    
                    security_result_id = security_results_manager.store_security_results(
                        cluster_id=cluster_id,
                        resource_group=resource_group,
                        cluster_name=cluster_name,
                        security_analysis=analysis_data['security_analysis']
                    )
                    logger.info(f"✅ Security results stored: {security_result_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store security results: {e}")
            
            # Trigger alert checking
            triggered_alerts = trigger_alert_checking_after_analysis(cluster_id, analysis_data)
            
            if triggered_alerts:
                logger.info(f"🚨 Analysis completed with {len(triggered_alerts)} alerts triggered")
            else:
                logger.info(f"✅ Analysis completed with no alerts triggered")
        else:
            logger.warning(f"⚠️ No analysis data available for alert checking")
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced background analysis with alerts: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

# FIXED Helper functions - REAL DATA ONLY
def safe_chart_function_call(func_name, func, *args, **kwargs):
    """Safely call a chart generation function with REAL data validation"""
    try:
        logger.info(f"🔄 Starting {func_name} with REAL data validation")
        
        # Validate first argument is a dict for most functions
        if args and func_name != 'generate_dynamic_trend_data':
            first_arg = args[0]
            if not isinstance(first_arg, dict):
                logger.error(f"❌ {func_name}: Expected dict, got {type(first_arg)}")
                return None
        
        # Special handling for trend data function
        if func_name == 'generate_dynamic_trend_data' and len(args) >= 2:
            cluster_id, analysis_data = args[0], args[1]
            if not isinstance(analysis_data, dict):
                logger.error(f"❌ {func_name}: Second argument (analysis_data) is {type(analysis_data)}, expected dict")
                return None
        
        result = func(*args, **kwargs)
        
        if result:
            logger.info(f"✅ {func_name} completed successfully with REAL data")
        else:
            logger.warning(f"⚠️ {func_name} returned None - no REAL data available")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ {func_name}: Error with REAL data - {e}")
        return None

def get_cluster_analysis_data(cluster_id):
    """Get cluster analysis data from database/cache - REAL DATA ONLY"""
    try:
        # Try cache first
        if cluster_id in analysis_cache.get('clusters', {}):
            cached_entry = analysis_cache['clusters'][cluster_id]
            
            # Check if cache is still valid
            cache_valid = True
            if CACHE_MANAGER_AVAILABLE:
                try:
                    cache_valid = is_cache_valid(cluster_id)
                except Exception as cache_check_error:
                    logger.warning(f"⚠️ Could not check cache validity: {cache_check_error}")
                    cache_valid = True
            
            if cache_valid:
                cached_data = cached_entry.get('data')
                if cached_data and isinstance(cached_data, dict):
                    logger.info(f"✅ Retrieved REAL analysis data from cache for: {cluster_id}")
                    return cached_data
            else:
                logger.info(f"🔄 Cache expired for cluster: {cluster_id}")
        
        # Try database
        logger.info(f"🔍 Retrieving REAL analysis data from database for: {cluster_id}")
        current_analysis, data_source = _get_analysis_data(cluster_id)
        
        if current_analysis and isinstance(current_analysis, dict):
            logger.info(f"✅ Retrieved REAL analysis data from {data_source} for: {cluster_id}")
            
            # Cache for future requests
            if CACHE_MANAGER_AVAILABLE:
                try:
                    subscription_id = azure_subscription_manager.get_current_subscription()
                    save_to_cache(cluster_id, current_analysis, subscription_id)
                    logger.info(f"💾 Cached REAL analysis data for: {cluster_id}")
                except Exception as cache_error:
                    logger.warning(f"⚠️ Could not cache data for {cluster_id}: {cache_error}")
            
            return current_analysis
        
        logger.warning(f"⚠️ No REAL analysis data found for cluster: {cluster_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error retrieving REAL analysis data for {cluster_id}: {e}")
        return None

def extract_real_cpu_metrics(analysis_data):
    """Extract REAL CPU metrics from analysis data - NO FALLBACKS"""
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
                'cpu_analysis_available': False
            }
        
        # Try to call the REAL CPU workload function
        if 'cpu_workload' in chart_generator_functions:
            try:
                logger.info("🔄 Calling REAL _extract_cpu_workload_data")
                result = safe_chart_function_call(
                    '_extract_cpu_workload_data',
                    chart_generator_functions['cpu_workload'],
                    analysis_data
                )
                if result and isinstance(result, dict):
                    logger.info("✅ Successfully extracted REAL CPU workload data")
                    return result
                else:
                    logger.warning("⚠️ CPU workload function returned None or invalid data")
            except Exception as cpu_error:
                logger.error(f"❌ Error in REAL CPU workload extraction: {cpu_error}")
        else:
            logger.warning("⚠️ CPU workload function not available")
        
        # Return basic structure if no REAL CPU data available
        return {
            'has_high_cpu_workloads': False,
            'high_cpu_count': 0,
            'max_cpu_utilization': 0.0,
            'average_cpu_utilization': 0.0,
            'severity_level': 'none',
            'high_cpu_workloads': [],
            'cpu_analysis_available': False
        }
        
    except Exception as e:
        logger.error(f"❌ Error extracting REAL CPU metrics: {e}")
        return {
            'has_high_cpu_workloads': False,
            'high_cpu_count': 0,
            'max_cpu_utilization': 0.0,
            'average_cpu_utilization': 0.0,
            'severity_level': 'none',
            'high_cpu_workloads': [],
            'cpu_analysis_available': False
        }

def generate_real_cost_breakdown_chart_data(analysis_data):
    """Generate cost breakdown chart data from REAL analysis ONLY"""
    try:
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ Cost breakdown: Expected dict, got {type(analysis_data)}")
            return None
        
        # Check if we have valid cost data
        total_cost = ensure_float(analysis_data.get('total_cost', 0))
        if total_cost <= 0:
            logger.warning("⚠️ No valid total cost for breakdown chart")
            return None
        
        cost_categories = []
        cost_values = []
        
        # Extract REAL cost components
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
            logger.warning("⚠️ No cost categories found for breakdown chart")
            return None
        
        return {
            'labels': cost_categories,
            'values': cost_values,
            'total_cost': sum(cost_values),
            'data_source': 'real_analysis',
            'real_data_only': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating REAL cost breakdown: {e}")
        return None

def generate_real_savings_breakdown_data(analysis_data):
    """Generate savings breakdown chart data from REAL analysis ONLY"""
    try:
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ Savings breakdown: Expected dict, got {type(analysis_data)}")
            return None
        
        categories = []
        values = []
        
        # Extract REAL savings components
        savings_components = [
            ('HPA Optimization', analysis_data.get('hpa_savings', 0)),
            ('Right-sizing', analysis_data.get('right_sizing_savings', 0)),
            ('Storage Optimization', analysis_data.get('storage_savings', 0)),
            ('CPU Optimization', analysis_data.get('cpu_optimization_savings', 0))
        ]
        
        # Filter out zero values
        for category, value in savings_components:
            if value and value > 0:
                categories.append(category)
                values.append(float(value))
        
        if not categories:
            logger.warning("⚠️ No savings categories found for breakdown chart")
            return None
        
        return {
            'categories': categories,
            'values': values,
            'total_savings': sum(values),
            'data_source': 'real_analysis',
            'real_data_only': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating REAL savings breakdown: {e}")
        return None

def calculate_optimization_score(analysis_data):
    """Calculate optimization score based on REAL analysis data"""
    try:
        if not isinstance(analysis_data, dict):
            logger.error(f"❌ Optimization score: Expected dict, got {type(analysis_data)}")
            return 50
        
        total_cost = ensure_float(analysis_data.get('total_cost', 0))
        total_savings = ensure_float(analysis_data.get('total_savings', 0))
        
        if total_cost <= 0:
            return 0
        
        savings_percentage = (total_savings / total_cost) * 100
        
        # Factor in CPU workload efficiency from REAL data
        cpu_efficiency_bonus = 0
        if analysis_data.get('has_cpu_analysis'):
            avg_cpu = ensure_float(analysis_data.get('average_cpu_utilization', 0))
            if avg_cpu > 80:
                cpu_efficiency_bonus = -10
            elif avg_cpu < 30:
                cpu_efficiency_bonus = 5
        
        # Convert to 1-100 score
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
        return 50

def ensure_float(value):
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0