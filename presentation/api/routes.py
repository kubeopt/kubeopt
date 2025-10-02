#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer - Clean Architecture
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

from shared.config.config import (
    logger, enhanced_cluster_manager, analysis_results, 
    _analysis_lock, _analysis_sessions, analysis_status_tracker
)
from shared.utils.utils import format_currency, time_ago, environment_badge_class, status_indicator_class
from presentation.api.chart_generator import generate_insights
from infrastructure.services.cache_manager import (
    is_cache_valid, clear_analysis_cache, force_fresh_analysis_with_complete_cache_clear,
    load_from_cache, save_to_cache, analysis_cache
)
from infrastructure.services.background_processor import run_background_analysis, check_alerts_after_analysis
from shared.utils.shared import _get_analysis_data
from infrastructure.services.subscription_manager import azure_subscription_manager
from infrastructure.persistence.processing.analysis_engine import multi_subscription_analysis_engine
from infrastructure.services.auth_manager import auth_manager
from infrastructure.services.feature_guard import get_ui_feature_flags

def register_routes(app):
    """Register all routes with the Flask app - now with multi-subscription support"""
    
    # Template filters
    app.template_filter('format_currency')(format_currency)
    app.template_filter('time_ago')(time_ago)
    app.template_filter('environment_badge_class')(environment_badge_class)
    app.template_filter('status_indicator_class')(status_indicator_class)
    
    
    @app.route('/')
    @app.route('/clusters')
    @auth_manager.require_auth
    def cluster_portfolio():
        """Enhanced multi-subscription cluster portfolio management page"""
        try:
            # Get clusters with subscription info (using existing method)
            clusters_data = enhanced_cluster_manager.get_clusters_with_subscription_info()
            
            # Get portfolio summary (using existing method)
            portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
            
            # Get analysis status for all clusters
            analysis_statuses = {}
            for cluster in clusters_data:
                cluster_name = cluster.get('name', 'Unknown')
                subscription_id = cluster.get('subscription_id', 'default')
                
                # Check if analysis is running
                session_key = f"{subscription_id}_{cluster_name}"
                is_running = session_key in _analysis_sessions
                
                # Get last analysis time
                last_analysis = analysis_results.get(session_key, {}).get('timestamp')
                
                analysis_statuses[session_key] = {
                    'is_running': is_running,
                    'last_analysis': last_analysis
                }
            
            # Add feature flags for UI rendering
            feature_flags = get_ui_feature_flags()
            
            return render_template('cluster_portfolio.html', 
                                clusters=clusters_data,
                                analysis_statuses=analysis_statuses,
                                portfolio_summary=portfolio_summary,
                                feature_flags=feature_flags)
                                
        except Exception as e:
            logger.error(f"Error in cluster_portfolio: {e}")
            traceback.print_exc()
            return render_template('error.html', error=str(e))

    @app.route('/cluster/<cluster_id>')
    @auth_manager.require_auth
    def single_cluster_dashboard(cluster_id: str):
        """Enhanced cluster dashboard with subscription awareness"""
        try:
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            
            if not cluster:
                return render_template('error.html', error=f'Cluster {cluster_id} not found')
            
            logger.info(f"📊 Multi-subscription dashboard access for {cluster_id}")
            
            # Get subscription info
            subscription_info = None
            if cluster.get('subscription_id'):
                from infrastructure.services.subscription_manager import azure_subscription_manager
                subscription_info = azure_subscription_manager.get_subscription_info(cluster['subscription_id'])
            
            # Get analysis data
            cached_analysis, data_source = _get_analysis_data(cluster_id)
            
            # Enhanced logging for dashboard
            if cached_analysis:
                logger.info(f"📊 DASHBOARD: Using data from {data_source}")
                logger.info(f"📊 DASHBOARD: Cost=${cached_analysis.get('total_cost', 0):.2f}, "
                           f"HPA={bool(cached_analysis.get('hpa_recommendations'))}")
            
            # Add feature flags for UI rendering
            feature_flags = get_ui_feature_flags()
            
            return render_template('unified_dashboard.html',
                                cluster=cluster,
                                analysis=cached_analysis,
                                subscription_info=subscription_info,
                                data_source=data_source,
                                feature_flags=feature_flags)
                                
        except Exception as e:
            logger.error(f"Error in single_cluster_dashboard: {e}")
            traceback.print_exc()
            return render_template('error.html', error=str(e))

    @app.route('/analyze/<subscription_id>/<cluster_name>')
    @auth_manager.require_auth
    def analyze_cluster(subscription_id, cluster_name):
        """Enhanced cluster analysis with multi-subscription support"""
        try:
            session_key = f"{subscription_id}_{cluster_name}"
            
            # Check if analysis is already running
            with _analysis_lock:
                if session_key in _analysis_sessions:
                    return jsonify({
                        'status': 'running',
                        'message': f'Analysis already running for {cluster_name}'
                    })
            
            # Start background analysis
            run_background_analysis(cluster_name, subscription_id)
            
            return jsonify({
                'status': 'started',
                'message': f'Analysis started for {cluster_name}',
                'session_key': session_key
            })
            
        except Exception as e:
            logger.error(f"Error starting analysis: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/analysis_status/<session_key>')
    @auth_manager.require_auth
    def analysis_status(session_key):
        """Check analysis status for a specific cluster session"""
        try:
            with _analysis_lock:
                if session_key in _analysis_sessions:
                    status = analysis_status_tracker.get(session_key, {})
                    return jsonify({
                        'status': 'running',
                        'progress': status.get('progress', 0),
                        'current_task': status.get('current_task', 'Starting analysis...')
                    })
                elif session_key in analysis_results:
                    return jsonify({
                        'status': 'completed',
                        'redirect_url': f'/results/{session_key}'
                    })
                else:
                    return jsonify({
                        'status': 'not_found',
                        'message': 'Analysis session not found'
                    })
                    
        except Exception as e:
            logger.error(f"Error checking analysis status: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/results/<session_key>')
    @auth_manager.require_auth
    def analysis_results_page(session_key):
        """Enhanced analysis results page with multi-subscription support"""
        try:
            if session_key not in analysis_results:
                return render_template('error.html', 
                                     error=f'No analysis results found for session {session_key}')
            
            results = analysis_results[session_key]
            
            return render_template('analysis_results.html', 
                                 results=results,
                                 session_key=session_key)
                                 
        except Exception as e:
            logger.error(f"Error displaying results: {e}")
            return render_template('error.html', error=str(e))
    
    logger.info("✅ Routes registered successfully")