#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Updated Flask Routes for Multi-Subscription AKS Cost Optimization Tool
"""

import subprocess
import traceback
import sys
import os
from datetime import datetime
from flask import jsonify, render_template, request, redirect, url_for, flash

# Add the app directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main.config import (
    logger, enhanced_cluster_manager, analysis_results, 
    _analysis_lock, _analysis_sessions, analysis_status_tracker
)
from app.main.utils import format_currency, time_ago, environment_badge_class, status_indicator_class
from interface.chart_generator import generate_insights
from app.services.cache_manager import (
    is_cache_valid, clear_analysis_cache, force_fresh_analysis_with_complete_cache_clear,
    load_from_cache, save_to_cache, analysis_cache
)
from app.services.background_processor import run_background_analysis, check_alerts_after_analysis
from app.main.shared import _get_analysis_data
from app.services.subscription_manager import azure_subscription_manager
from app.data.processing.analysis_engine import multi_subscription_analysis_engine

def register_routes(app):
    """Register all routes with the Flask app - now with multi-subscription support"""
    
    # Template filters
    app.template_filter('format_currency')(format_currency)
    app.template_filter('time_ago')(time_ago)
    app.template_filter('environment_badge_class')(environment_badge_class)
    app.template_filter('status_indicator_class')(status_indicator_class)
    
    @app.route('/')
    @app.route('/clusters')
    def cluster_portfolio():
        """Enhanced multi-subscription cluster portfolio management page"""
        try:
            logger.info("🏠 Loading enhanced multi-subscription cluster portfolio page")
            
            # Detect and update subscription info for existing clusters
            enhanced_cluster_manager.detect_and_update_cluster_subscriptions()
            
            # Get clusters with subscription info
            clusters = enhanced_cluster_manager.get_clusters_with_subscription_info()
            portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
            
            # Get available subscriptions for dropdown
            available_subscriptions = azure_subscription_manager.get_available_subscriptions()
            
            # Add analysis status for each cluster
            for cluster in clusters:
                cluster['has_analysis'] = cluster.get('last_analyzed') is not None
                cluster['analysis_age_days'] = 0
                
                if cluster.get('last_analyzed'):
                    try:
                        last_analyzed = datetime.fromisoformat(cluster['last_analyzed'].replace('Z', '+00:00'))
                        cluster['analysis_age_days'] = (datetime.now() - last_analyzed.replace(tzinfo=None)).days
                    except:
                        cluster['analysis_age_days'] = 999
                
                # Add subscription display info
                if cluster.get('subscription_id'):
                    cluster['subscription_display'] = f"{cluster.get('subscription_name', 'Unknown')} ({cluster['subscription_id'][:8]})"
                else:
                    cluster['subscription_display'] = 'Unknown Subscription'
            
            # Group clusters by subscription for better organization
            clusters_by_subscription = {}
            for cluster in clusters:
                sub_id = cluster.get('subscription_id', 'unknown')
                sub_name = cluster.get('subscription_name', 'Unknown Subscription')
                
                if sub_id not in clusters_by_subscription:
                    clusters_by_subscription[sub_id] = {
                        'subscription_name': sub_name,
                        'subscription_id': sub_id,
                        'clusters': []
                    }
                clusters_by_subscription[sub_id]['clusters'].append(cluster)
            
            logger.info(f"📊 Enhanced Multi-Subscription Portfolio: {len(clusters)} clusters across {len(clusters_by_subscription)} subscriptions, ${portfolio_summary.get('total_monthly_cost', 0):.2f} total cost")
            
            return render_template('cluster_portfolio.html', 
                                 clusters=clusters,
                                 clusters_by_subscription=clusters_by_subscription,
                                 available_subscriptions=available_subscriptions,
                                 portfolio_summary=portfolio_summary,
                                 multi_subscription_enabled=True)
                                 
        except Exception as e:
            logger.error(f"❌ Error loading enhanced multi-subscription portfolio: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            return render_template('cluster_portfolio.html', 
                                 clusters=[],
                                 clusters_by_subscription={},
                                 available_subscriptions=[],
                                 portfolio_summary={
                                    'total_clusters': 0, 
                                    'total_monthly_cost': 0, 
                                    'total_potential_savings': 0, 
                                    'avg_optimization_pct': 0, 
                                    'environments': [],
                                    'last_updated': datetime.now().isoformat()
                                 },
                                 multi_subscription_enabled=True,
                                 error_message="Failed to load multi-subscription cluster portfolio")

    @app.route('/dashboard')
    def unified_dashboard():
        """DEPRECATED: Original unified dashboard - redirect to portfolio"""
        logger.warning("⚠️ /dashboard route accessed - redirecting to multi-subscription portfolio")
        flash('The unified dashboard has been deprecated. Use individual cluster dashboards for better multi-subscription support.', 'info')
        return redirect(url_for('cluster_portfolio'))

    @app.route('/cluster/<cluster_id>')
    def single_cluster_dashboard(cluster_id: str):
        """Enhanced cluster dashboard with subscription awareness"""
        global analysis_results
        
        try:
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            
            if not cluster:
                flash(f'Cluster {cluster_id} not found', 'error')
                return redirect(url_for('cluster_portfolio'))
            
            logger.info(f"📊 Multi-subscription dashboard access for {cluster_id}")
            
            # Get subscription info
            subscription_info = None
            if cluster.get('subscription_id'):
                subscription_info = azure_subscription_manager.get_subscription_info(cluster['subscription_id'])
            
            # Use the FIXED _get_analysis_data function that checks sessions first
            cached_analysis, data_source = _get_analysis_data(cluster_id)
            
            # Enhanced logging for dashboard
            if cached_analysis:
                logger.info(f"📊 DASHBOARD: Using data from {data_source}")
                logger.info(f"📊 DASHBOARD: Cost=${cached_analysis.get('total_cost', 0):.2f}, "
                           f"HPA={bool(cached_analysis.get('hpa_recommendations'))}")
                
                # Check for subscription metadata in analysis
                subscription_metadata = cached_analysis.get('subscription_metadata', {})
                if subscription_metadata:
                    logger.info(f"📊 DASHBOARD: Analysis has subscription metadata for {subscription_metadata.get('subscription_name', 'Unknown')}")
                
                # Validate implementation plan exists
                if 'implementation_plan' in cached_analysis:
                    impl_plan = cached_analysis['implementation_plan']
                    if isinstance(impl_plan, dict) and 'implementation_phases' in impl_plan:
                        phases_count = len(impl_plan['implementation_phases'])
                        logger.info(f"✅ DASHBOARD: Implementation plan with {phases_count} phases")
                    else:
                        logger.warning(f"⚠️ DASHBOARD: Implementation plan structure invalid")
                else:
                    logger.warning(f"⚠️ DASHBOARD: Missing implementation plan")
            else:
                logger.info(f"📊 DASHBOARD: No analysis data found for {cluster_id}")
            
            # Get analysis history
            analysis_history = enhanced_cluster_manager.get_analysis_history(cluster_id, limit=5)
            
            # Build context with subscription info
            context = {
                'cluster': cluster,
                'results': cached_analysis or {},
                'has_analysis_data': bool(cached_analysis and cached_analysis.get('total_cost', 0) > 0),
                'cluster_context': cluster,
                'analysis_history': analysis_history,
                'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
                'data_source': data_source,
                'active_tab': 'dashboard',
                'subscription_info': subscription_info,
                'multi_subscription_enabled': True,
                'subscription_metadata': cached_analysis.get('subscription_metadata', {}) if cached_analysis else {}
            }
            
            # Add implementation plan debug info
            if cached_analysis and 'implementation_plan' in cached_analysis:
                impl_plan = cached_analysis['implementation_plan']
                if isinstance(impl_plan, dict) and 'implementation_phases' in impl_plan:
                    context['impl_plan_phases'] = len(impl_plan['implementation_phases'])
                    context['impl_plan_status'] = 'valid'
                else:
                    context['impl_plan_phases'] = 0
                    context['impl_plan_status'] = 'invalid'
            else:
                context['impl_plan_phases'] = 0
                context['impl_plan_status'] = 'missing'
            
            logger.info(f"📊 MULTI-SUB DASHBOARD CONTEXT: {data_source}, subscription: {cluster.get('subscription_name', 'Unknown')}, impl_plan: {context['impl_plan_status']} ({context['impl_plan_phases']} phases)")
            
            return render_template('unified_dashboard.html', **context)
            
        except Exception as e:
            logger.error(f"❌ Error loading multi-subscription cluster dashboard {cluster_id}: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            flash(f'Error loading cluster dashboard: {str(e)}', 'error')
            return redirect(url_for('cluster_portfolio'))

    # REMOVED: /analyze route - analysis is now handled through cluster cards only
    # This supports the requirement to remove the analysis tab and default to 30 days

    @app.route('/cluster/<cluster_id>/remove', methods=['DELETE'])
    def remove_cluster_route(cluster_id: str):
        """Remove cluster with subscription awareness"""
        try:
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Log subscription context
            subscription_info = ""
            if cluster.get('subscription_id'):
                subscription_info = f" from subscription {cluster.get('subscription_name', 'Unknown')}"
            
            success = enhanced_cluster_manager.remove_cluster(cluster_id)
            
            if success:
                # Clear any cached data for this cluster
                clear_analysis_cache(cluster_id)
                
                # Clean up session data
                with _analysis_lock:
                    sessions_to_remove = []
                    for session_id, session_info in _analysis_sessions.items():
                        if session_info.get('cluster_id') == cluster_id:
                            sessions_to_remove.append(session_id)
                    
                    for session_id in sessions_to_remove:
                        del _analysis_sessions[session_id]
                
                logger.info(f"✅ Removed cluster {cluster_id}{subscription_info}")
                
                return jsonify({
                    'status': 'success',
                    'message': f'Cluster {cluster["name"]} removed successfully',
                    'cluster_id': cluster_id,
                    'subscription_info': subscription_info
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to remove cluster {cluster_id}'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error removing cluster {cluster_id}: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error removing cluster: {str(e)}'
            }), 500

    @app.route('/subscription-management')
    def subscription_management():
        """Subscription management interface"""
        try:
            logger.info("🌐 Loading subscription management interface")
            
            # Get all available subscriptions
            subscriptions = azure_subscription_manager.get_available_subscriptions(force_refresh=True)
            
            # Get current subscription
            current_subscription_id = azure_subscription_manager.get_current_subscription()
            
            # Get cluster distribution by subscription
            clusters = enhanced_cluster_manager.get_clusters_with_subscription_info()
            
            subscription_stats = {}
            for cluster in clusters:
                sub_id = cluster.get('subscription_id', 'unknown')
                if sub_id not in subscription_stats:
                    subscription_stats[sub_id] = {
                        'cluster_count': 0,
                        'total_cost': 0,
                        'total_savings': 0,
                        'subscription_name': cluster.get('subscription_name', 'Unknown')
                    }
                
                subscription_stats[sub_id]['cluster_count'] += 1
                subscription_stats[sub_id]['total_cost'] += cluster.get('last_cost', 0)
                subscription_stats[sub_id]['total_savings'] += cluster.get('last_savings', 0)
            
            return render_template('subscription_management.html',
                                 subscriptions=subscriptions,
                                 current_subscription_id=current_subscription_id,
                                 subscription_stats=subscription_stats,
                                 total_subscriptions=len(subscriptions))
                                 
        except Exception as e:
            logger.error(f"❌ Error loading subscription management: {e}")
            flash(f'Error loading subscription management: {str(e)}', 'error')
            return redirect(url_for('cluster_portfolio'))

    # Helper function for validation
    def _validate_subscription_aware_analysis_results(session_results: dict, cluster_id: str, session_id: str, subscription_id: str) -> dict:
        """Comprehensive validation of subscription-aware analysis results"""
        errors = []
        
        # Check core data
        if not session_results.get('total_cost', 0) > 0:
            errors.append("Missing or invalid total_cost")
        
        if not session_results.get('hpa_recommendations'):
            errors.append("Missing HPA recommendations")
        elif not isinstance(session_results['hpa_recommendations'], dict):
            errors.append("Invalid HPA recommendations structure")
        
        if not session_results.get('nodes') or len(session_results['nodes']) == 0:
            errors.append("Missing or empty nodes data")
        
        if not session_results.get('has_real_node_data'):
            errors.append("No real node data flag set")
        
        if not session_results.get('ml_enhanced'):
            errors.append("Analysis not ML-enhanced")
        
        # Check subscription metadata
        subscription_metadata = session_results.get('subscription_metadata', {})
        if not subscription_metadata.get('subscription_id'):
            errors.append("Missing subscription metadata")
        elif subscription_metadata['subscription_id'] != subscription_id:
            errors.append("Subscription metadata mismatch")
        
        # Check implementation plan
        impl_plan = session_results.get('implementation_plan')
        if not impl_plan or not isinstance(impl_plan, dict):
            errors.append("Missing or invalid implementation plan")
        elif not impl_plan.get('implementation_phases'):
            errors.append("Implementation plan missing phases")
        
        validation_result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'cluster_id': cluster_id,
            'session_id': session_id[:8],
            'subscription_id': subscription_id[:8],
            'total_cost': session_results.get('total_cost', 0),
            'node_count': len(session_results.get('nodes', [])),
            'has_hpa': bool(session_results.get('hpa_recommendations')),
            'ml_enhanced': session_results.get('ml_enhanced', False),
            'subscription_aware': bool(subscription_metadata)
        }
        
        if validation_result['valid']:
            logger.info(f"✅ Subscription-aware analysis validation passed for {cluster_id} (session: {session_id[:8]}, sub: {subscription_id[:8]})")
        else:
            logger.error(f"❌ Subscription-aware analysis validation failed for {cluster_id} (session: {session_id[:8]}, sub: {subscription_id[:8]}): {errors}")
        
        return validation_result

    # Additional utility routes
    @app.route('/api/subscription-health')
    def subscription_health():
        """Check health of all subscriptions"""
        try:
            subscriptions = azure_subscription_manager.get_available_subscriptions()
            health_status = []
            
            for sub in subscriptions:
                # Quick health check - try to list resource groups
                try:
                    result = subprocess.run([
                        'az', 'group', 'list',
                        '--subscription', sub.subscription_id,
                        '--query', 'length(@)',
                        '--output', 'tsv'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        rg_count = int(result.stdout.strip())
                        health_status.append({
                            'subscription_id': sub.subscription_id,
                            'subscription_name': sub.subscription_name,
                            'status': 'healthy',
                            'resource_group_count': rg_count,
                            'is_default': sub.is_default
                        })
                    else:
                        health_status.append({
                            'subscription_id': sub.subscription_id,
                            'subscription_name': sub.subscription_name,
                            'status': 'error',
                            'error': result.stderr.strip(),
                            'is_default': sub.is_default
                        })
                        
                except Exception as e:
                    health_status.append({
                        'subscription_id': sub.subscription_id,
                        'subscription_name': sub.subscription_name,
                        'status': 'unreachable',
                        'error': str(e),
                        'is_default': sub.is_default
                    })
            
            return jsonify({
                'status': 'success',
                'subscription_health': health_status,
                'total_subscriptions': len(health_status),
                'healthy_subscriptions': len([s for s in health_status if s['status'] == 'healthy'])
            })
            
        except Exception as e:
            logger.error(f"❌ Error checking subscription health: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500