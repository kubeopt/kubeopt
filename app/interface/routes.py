"""
Flask Routes for AKS Cost Optimization Tool
"""

import traceback
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import (
    logger, enhanced_cluster_manager, analysis_results, 
    _analysis_lock, _analysis_sessions, analysis_status_tracker, alerts_manager
)
from app.main.utils import format_currency, time_ago, environment_badge_class, status_indicator_class
from app.interface.chart_generator import generate_insights
from app.services.cache_manager import (
    is_cache_valid, clear_analysis_cache, force_fresh_analysis_with_complete_cache_clear,
    load_from_cache, save_to_cache, analysis_cache
)
from app.services.background_processor import run_background_analysis, check_alerts_after_analysis

def register_routes(app: Flask):
    """Register all routes with the Flask app"""
    
    # Template filters
    app.template_filter('format_currency')(format_currency)
    app.template_filter('time_ago')(time_ago)
    app.template_filter('environment_badge_class')(environment_badge_class)
    app.template_filter('status_indicator_class')(status_indicator_class)
    
    @app.route('/')
    @app.route('/clusters')
    def cluster_portfolio():
        """Enhanced multi-cluster portfolio management page with SQLite backend"""
        try:
            logger.info("🏠 Loading enhanced cluster portfolio page")
            
            clusters = enhanced_cluster_manager.list_clusters()
            portfolio_summary = enhanced_cluster_manager.get_portfolio_summary()
            
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
            
            logger.info(f"📊 Enhanced Portfolio: {len(clusters)} clusters, ${portfolio_summary.get('total_monthly_cost', 0):.2f} total cost")
            
            return render_template('cluster_portfolio.html', 
                                 clusters=clusters,
                                 portfolio_summary=portfolio_summary)
                                 
        except Exception as e:
            logger.error(f"❌ Error loading enhanced portfolio: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            return render_template('cluster_portfolio.html', 
                                 clusters=[],
                                 portfolio_summary={
                                    'total_clusters': 0, 
                                    'total_monthly_cost': 0, 
                                    'total_potential_savings': 0, 
                                    'avg_optimization_pct': 0, 
                                    'environments': [],
                                    'last_updated': datetime.now().isoformat()
                                 },
                                 error_message="Failed to load cluster portfolio")

    @app.route('/dashboard')
    def unified_dashboard():
        """Original unified dashboard - FIXED to avoid global dependency"""
        logger.warning("⚠️ /dashboard route accessed - this is deprecated, use cluster-specific dashboards")
        
        # Try to get any recent cluster data
        try:
            clusters = enhanced_cluster_manager.list_clusters()
            if clusters:
                # Get the most recently analyzed cluster
                recent_cluster = max(
                    (c for c in clusters if c.get('last_analyzed')), 
                    key=lambda x: x.get('last_analyzed', ''), 
                    default=None
                )
                
                if recent_cluster:
                    cluster_id = recent_cluster['id']
                    current_analysis, data_source = _get_analysis_data(cluster_id)
                    
                    if current_analysis and current_analysis.get('total_cost', 0) > 0:
                        context = {
                            'results': current_analysis,
                            'has_analysis_data': True,
                            'cluster_context': recent_cluster,
                            'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
                            'data_source': f'Most recent cluster analysis ({data_source})',
                            'deprecated_warning': True
                        }
                        return render_template('unified_dashboard.html', **context)
        except Exception as e:
            logger.error(f"Error loading recent cluster data: {e}")
        
        # No cluster data available
        context = {
            'results': {},
            'has_analysis_data': False,
            'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
            'data_source': 'No analysis data available',
            'cluster_context': None,
            'deprecated_warning': True
        }
        
        return render_template('unified_dashboard.html', **context)

    @app.route('/cluster/<cluster_id>')
    def single_cluster_dashboard(cluster_id: str):
        """FIXED: Dashboard with session data priority"""
        global analysis_results
        
        try:
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            
            if not cluster:
                flash(f'Cluster {cluster_id} not found', 'error')
                return redirect(url_for('cluster_portfolio'))
            
            logger.info(f"📊 Dashboard access for {cluster_id} - USING FIXED SESSION PRIORITY")
            
            # Use the FIXED _get_analysis_data function that checks sessions first
            cached_analysis, data_source = _get_analysis_data(cluster_id)
            
            # Enhanced logging for dashboard
            if cached_analysis:
                logger.info(f"📊 DASHBOARD: Using data from {data_source}")
                logger.info(f"📊 DASHBOARD: Cost=${cached_analysis.get('total_cost', 0):.2f}, "
                           f"HPA={bool(cached_analysis.get('hpa_recommendations'))}")
                
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
            
            # Build context
            context = {
                'cluster': cluster,
                'results': cached_analysis or {},
                'has_analysis_data': bool(cached_analysis and cached_analysis.get('total_cost', 0) > 0),
                'cluster_context': cluster,
                'analysis_history': analysis_history,
                'timestamp': datetime.now().strftime('%B %d, %Y %H:%M:%S'),
                'data_source': data_source
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
            
            logger.info(f"📊 DASHBOARD CONTEXT: {data_source}, impl_plan: {context['impl_plan_status']} ({context['impl_plan_phases']} phases)")
            
            return render_template('unified_dashboard.html', **context)
            
        except Exception as e:
            logger.error(f"❌ Error loading cluster dashboard {cluster_id}: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            flash(f'Error loading cluster dashboard: {str(e)}', 'error')
            return redirect(url_for('cluster_portfolio'))

    @app.route('/analyze', methods=['POST'])
    def completely_fixed_analyze_route():
        """COMPLETELY FIXED: Enhanced analyze route with all fixes integrated"""
        try:
            # Extract form data
            resource_group = request.form.get('resource_group')
            cluster_name = request.form.get('cluster_name')
            days = int(request.form.get('days', 30))
            enable_pod_analysis = request.form.get('enable_pod_analysis') == 'on'
            redirect_to_cluster = request.form.get('redirect_to_cluster', 'false') == 'true'
            cluster_id = f"{resource_group}_{cluster_name}"

            if not resource_group or not cluster_name:
                flash('Resource group and cluster name are required', 'error')
                return redirect(url_for('cluster_portfolio'))

            logger.info(f"🚀 COMPLETELY FIXED ANALYSIS: Starting for {cluster_id}")

            # STEP 1: Complete cache clearing for fresh analysis
            force_fresh_analysis_with_complete_cache_clear(cluster_id)

            # STEP 2: Auto-add cluster if not exists
            existing_cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not existing_cluster:
                cluster_config = {
                    'cluster_name': cluster_name,
                    'resource_group': resource_group,
                    'environment': 'unknown',
                    'region': 'Unknown',
                    'description': f'Auto-added from analysis request on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                }
                cluster_id = enhanced_cluster_manager.add_cluster(cluster_config)
                logger.info(f"🆕 Auto-added cluster {cluster_id}")
            
            # STEP 3: Run the FIXED analysis
            logger.info(f"🔄 Running COMPLETELY FIXED analysis for {cluster_id}")
            from analysis_engine import run_completely_fixed_analysis
            
            result = run_completely_fixed_analysis(
                resource_group, cluster_name, days, enable_pod_analysis
            )
            
            if result['status'] == 'success':
                # STEP 4: Process successful results
                session_results = result['results']
                session_id = result['session_id']
                
                # STEP 5: Comprehensive validation
                validation_result = _validate_analysis_results_comprehensive(session_results, cluster_id, session_id)
                if not validation_result['valid']:
                    flash(f'❌ Analysis validation failed: {validation_result["errors"]}', 'error')
                    return redirect(url_for('cluster_portfolio'))
                
                # STEP 6: Save with fixed cache system
                logger.info(f"💾 Saving FIXED analysis results for {cluster_id}")
                
                # Save to database
                enhanced_cluster_manager.update_cluster_analysis(cluster_id, session_results)
                
                # Save to cache with validation
                cache_success = save_to_cache(cluster_id, session_results)
                if not cache_success:
                    logger.warning(f"⚠️ Cache save failed for {cluster_id}, but analysis succeeded")
                
                # STEP 7: Extract results for display
                monthly_cost = session_results.get('total_cost', 0)
                monthly_savings = session_results.get('total_savings', 0)
                confidence = session_results.get('analysis_confidence', 0)
                
                # STEP 8: Check alerts after successful analysis
                check_alerts_after_analysis(cluster_id, session_results)
                
                # STEP 9: Generate success message
                success_msg = (
                    f'🎯 COMPLETELY FIXED Analysis Complete for {cluster_name}! '
                    f'${monthly_cost:.0f}/month baseline, ${monthly_savings:.0f}/month savings potential '
                    f'| Confidence: {confidence:.2f} | Session: {session_id[:8]} | ML-Enhanced: ✅'
                )
                
                flash(success_msg, 'success')
                
                # STEP 10: Redirect logic
                if redirect_to_cluster or existing_cluster:
                    return redirect(url_for('single_cluster_dashboard', cluster_id=cluster_id))
                else:
                    return redirect(url_for('cluster_portfolio'))
            else:
                # Handle analysis failure
                error_message = result.get('message', 'Unknown error')
                session_id = result.get('session_id', 'unknown')
                flash(f'❌ FIXED analysis failed (session {session_id[:8]}): {error_message}', 'error')
                return redirect(url_for('cluster_portfolio'))

        except Exception as e:
            logger.error(f"❌ COMPLETELY FIXED analysis route failed: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            flash(f'❌ Analysis failed: {str(e)}', 'error')
            return redirect(url_for('cluster_portfolio'))

    # Helper functions for routes
    def _get_analysis_data(cluster_id):
        """HPA-aware analysis data loading with session priority"""
        if not cluster_id:
            logger.warning("⚠️ No cluster_id provided for analysis data")
            return None, "no_cluster_id"

        # PRIORITY 0: Check for fresh session data first (HIGHEST PRIORITY)
        fresh_session_data = None
        data_source = "none"
        with _analysis_lock:
            logger.info(f"🔍 CHART API: Checking {len(_analysis_sessions)} active sessions for cluster {cluster_id}")
            for session_id, session_info in _analysis_sessions.items():
                if (session_info.get('cluster_id') == cluster_id and 
                    session_info.get('status') == 'completed' and 
                    'results' in session_info):
                    fresh_session_data = session_info['results']
                    data_source = "fresh_session"
                    logger.info(f"🎯 CHART API: Found fresh session data for {cluster_id} (session: {session_id[:8]})")
                    break

        if fresh_session_data:
            # Validate HPA recommendations in fresh data
            if 'hpa_recommendations' in fresh_session_data:
                logger.info(f"✅ CHART API: Using fresh session data with HPA for {cluster_id}")
                # Optionally update cache with fresh data
                save_to_cache(cluster_id, fresh_session_data)
                return fresh_session_data, "fresh_session"
            else:
                logger.warning(f"⚠️ CHART API: Fresh session data missing HPA for {cluster_id}")

        # PRIORITY 1: Cluster-specific cache with HPA validation
        try:
            cached_data = load_from_cache(cluster_id)
            if cached_data and cached_data.get('total_cost', 0) > 0:
                # Validate HPA recommendations exist
                if 'hpa_recommendations' in cached_data:
                    logger.info(f"✅ CACHE: Complete data with HPA for {cluster_id} - ${cached_data.get('total_cost', 0):.2f}")
                    return cached_data, "cluster_cache"
                else:
                    logger.warning(f"⚠️ CACHE: Data exists but missing HPA for {cluster_id}")
                    # Clear incomplete cache
                    clear_analysis_cache(cluster_id)
        except Exception as e:
            logger.warning(f"⚠️ Cluster cache fetch failed for {cluster_id}: {e}")

        # PRIORITY 2: Database with HPA validation
        try:
            logger.info(f"🔄 Loading from database for cluster: {cluster_id}")
            db_data = enhanced_cluster_manager.get_latest_analysis(cluster_id)
            if db_data and db_data.get('total_cost', 0) > 0:
                # Validate HPA recommendations in database data
                if 'hpa_recommendations' in db_data:
                    logger.info(f"✅ DATABASE: Complete data with HPA for {cluster_id} - ${db_data.get('total_cost', 0):.2f}")
                    # Cache the complete database data
                    save_to_cache(cluster_id, db_data)
                    return db_data, "cluster_database"
                else:
                    logger.warning(f"⚠️ DATABASE: Data exists but missing HPA for {cluster_id}")
        except Exception as e:
            logger.error(f"❌ Database error for cluster {cluster_id}: {e}")

        logger.warning(f"⚠️ No complete analysis data (with HPA) found for cluster: {cluster_id}")
        return None, "no_complete_data"

    def _validate_analysis_results_comprehensive(session_results: dict, cluster_id: str, session_id: str) -> dict:
        """Comprehensive validation of analysis results"""
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
            'total_cost': session_results.get('total_cost', 0),
            'node_count': len(session_results.get('nodes', [])),
            'has_hpa': bool(session_results.get('hpa_recommendations')),
            'ml_enhanced': session_results.get('ml_enhanced', False)
        }
        
        if validation_result['valid']:
            logger.info(f"✅ Analysis validation passed for {cluster_id} (session: {session_id[:8]})")
        else:
            logger.error(f"❌ Analysis validation failed for {cluster_id} (session: {session_id[:8]}): {errors}")
        
        return validation_result

    # Register more API routes here...
    from app.interface.api_routes import register_api_routes
    register_api_routes(app)