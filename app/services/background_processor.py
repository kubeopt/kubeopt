"""
Enhanced Background Processing for Multi-Subscription AKS Cost Optimization
"""

import threading
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import logger, enhanced_cluster_manager, analysis_status_tracker, analysis_results

def run_subscription_aware_background_analysis(cluster_id: str, resource_group: str, cluster_name: str, 
                                              subscription_id: Optional[str] = None, days: int = 30, 
                                              enable_pod_analysis: bool = True):
    """Enhanced background analysis with full subscription awareness and tracking"""
    
    
    # ✅ ADD: Check if analysis is already running for this cluster
    if cluster_id in analysis_status_tracker:
        current_status = analysis_status_tracker[cluster_id].get('status')
        if current_status in ['running', 'analyzing']:
            logger.warning(f"⚠️ Analysis already running for cluster {cluster_id}, skipping duplicate request")
            return
    
    session_id = None
    
    try:
        logger.info(f"🌐 Starting subscription-aware background analysis for {cluster_id}")
        
        # Import subscription manager and analysis engine
        from app.services.subscription_manager import azure_subscription_manager
        from app.data.processing.analysis_engine import multi_subscription_analysis_engine
        
        # Auto-detect subscription if not provided
        if not subscription_id:
            logger.info(f"🔍 Auto-detecting subscription for cluster {cluster_name}")
            subscription_id = azure_subscription_manager.find_cluster_subscription(resource_group, cluster_name)
            
            if not subscription_id:
                raise Exception(f"Could not find cluster {cluster_name} in any accessible subscription")
        
        # Get subscription info for display
        subscription_info = azure_subscription_manager.get_subscription_info(subscription_id)
        subscription_name = subscription_info.subscription_name if subscription_info else subscription_id[:8]
        
        # Create unique session ID for tracking
        import uuid
        session_id = f"{subscription_id[:8]}_{str(uuid.uuid4())[:8]}"
        
        # Track session in database
        session_data = {
            'session_id': session_id,
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'analysis_type': 'completely_fixed',
            'status': 'running',
            'progress': 0,
            'message': f'Starting subscription-aware analysis in {subscription_name}',
            'started_at': datetime.now().isoformat(),
            'thread_id': threading.current_thread().ident,
            'subscription_context_set': False
        }
        
        # Track in database
        enhanced_cluster_manager.track_subscription_analysis_session(session_data)
        
        # Progress tracking function with subscription context
        def update_progress(progress: int, message: str):
            enhanced_message = f"[{subscription_name}] {message}"
            
            # Update cluster status
            enhanced_cluster_manager.update_analysis_status(cluster_id, 'analyzing', progress, enhanced_message)
            
            # Update in-memory tracker
            analysis_status_tracker[cluster_id] = {
                'status': 'analyzing',
                'progress': progress,
                'message': enhanced_message,
                'timestamp': datetime.now().isoformat(),
                'subscription_id': subscription_id,
                'subscription_name': subscription_name,
                'session_id': session_id
            }
            
            # Update session in database
            enhanced_cluster_manager.update_subscription_analysis_session(session_id, {
                'progress': progress,
                'message': enhanced_message,
                'status': 'running'
            })
            
            logger.info(f"🌐 Session {session_id[:8]}: Progress {progress}% - {enhanced_message}")
        
        # Simulate analysis steps with enhanced progress updates
        update_progress(5, f'Validating cluster access in subscription...')
        
        # Validate cluster access
        validation_result = azure_subscription_manager.validate_cluster_access(
            subscription_id, resource_group, cluster_name
        )
        
        if not validation_result['valid']:
            raise Exception(f"Cluster validation failed: {validation_result['error']}")
        
        update_progress(10, f'Setting subscription context...')
        
        # Record performance metric
        start_time = time.time()
        
        update_progress(20, f'Connecting to Azure subscription...')
        time.sleep(1)
        
        update_progress(30, f'Fetching cost data from subscription context...')
        time.sleep(2)
        
        update_progress(50, f'Analyzing cluster metrics with subscription awareness...')
        time.sleep(2)
        
        update_progress(70, f'Calculating ML-powered optimization opportunities...')
        
        # Run the actual subscription-aware analysis
        result = multi_subscription_analysis_engine.run_subscription_aware_analysis(
            resource_group, cluster_name, subscription_id, days, enable_pod_analysis
        )
        
        update_progress(85, f'Generating AI insights and implementation plan...')
        time.sleep(1)
        
        # Record analysis duration
        analysis_duration = time.time() - start_time
        enhanced_cluster_manager.record_subscription_performance_metric(
            subscription_id, 'analysis_duration_seconds', analysis_duration
        )
        
        if result['status'] == 'success':
            analysis_results_data = result['results']
            
            # Ensure subscription metadata is included
            if 'subscription_metadata' not in analysis_results_data:
                analysis_results_data['subscription_metadata'] = {
                    'subscription_id': subscription_id,
                    'subscription_name': subscription_name,
                    'analysis_session_id': session_id,
                    'cluster_validation': validation_result.get('cluster_info', {}),
                    'multi_subscription_enabled': True
                }
            
            # Store results in database with subscription context
            enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_results_data)
            
            # Update status to completed
            completion_message = f'Subscription-aware analysis completed! Found ${analysis_results_data.get("total_savings", 0):.0f}/month savings potential in {subscription_name}'
            
            enhanced_cluster_manager.update_analysis_status(
                cluster_id, 
                'completed', 
                100, 
                completion_message
            )
            
            # Update in-memory tracker
            analysis_status_tracker[cluster_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Multi-subscription analysis completed successfully',
                'timestamp': datetime.now().isoformat(),
                'subscription_id': subscription_id,
                'subscription_name': subscription_name,
                'session_id': session_id,
                'results': {
                    'total_cost': analysis_results_data.get('total_cost', 0),
                    'total_savings': analysis_results_data.get('total_savings', 0),
                    'confidence': analysis_results_data.get('analysis_confidence', 0)
                }
            }
            
            # Update session in database
            enhanced_cluster_manager.update_subscription_analysis_session(session_id, {
                'status': 'completed',
                'progress': 100,
                'message': completion_message,
                'completed_at': datetime.now().isoformat(),
                'results_size': len(str(analysis_results_data))
            })
            
            # Record successful analysis metrics
            enhanced_cluster_manager.record_subscription_performance_metric(
                subscription_id, 'successful_analyses', 1
            )
            enhanced_cluster_manager.record_subscription_performance_metric(
                subscription_id, 'total_cost_analyzed', analysis_results_data.get('total_cost', 0)
            )
            enhanced_cluster_manager.record_subscription_performance_metric(
                subscription_id, 'total_savings_identified', analysis_results_data.get('total_savings', 0)
            )
            
            logger.info(f"✅ Subscription-aware background analysis completed for {cluster_id} in {subscription_name}")
            
            # Check alerts after successful analysis
            check_subscription_aware_alerts_after_analysis(cluster_id, analysis_results_data, subscription_id)
            
        else:
            error_message = result.get('message', 'Subscription-aware analysis failed')
            enhanced_cluster_manager.update_analysis_status(cluster_id, 'failed', 0, error_message)
            
            analysis_status_tracker[cluster_id] = {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'timestamp': datetime.now().isoformat(),
                'subscription_id': subscription_id,
                'subscription_name': subscription_name,
                'session_id': session_id
            }
            
            # Update session in database
            enhanced_cluster_manager.update_subscription_analysis_session(session_id, {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'completed_at': datetime.now().isoformat()
            })
            
            # Record failed analysis metric
            enhanced_cluster_manager.record_subscription_performance_metric(
                subscription_id, 'failed_analyses', 1
            )
            
            logger.error(f"❌ Subscription-aware background analysis failed for {cluster_id} in {subscription_name}: {error_message}")
            
    except Exception as e:
        error_message = f'Subscription-aware analysis error: {str(e)}'
        logger.error(f"❌ Subscription-aware background analysis exception for {cluster_id}: {e}")
        
        if session_id:
            enhanced_cluster_manager.update_subscription_analysis_session(session_id, {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'completed_at': datetime.now().isoformat()
            })
        
        enhanced_cluster_manager.update_analysis_status(cluster_id, 'failed', 0, error_message)
        
        analysis_status_tracker[cluster_id] = {
            'status': 'failed',
            'progress': 0,
            'message': error_message,
            'timestamp': datetime.now().isoformat(),
            'subscription_id': subscription_id,
            'session_id': session_id
        }
        
        if subscription_id:
            enhanced_cluster_manager.record_subscription_performance_metric(
                subscription_id, 'failed_analyses', 1
            )

def check_subscription_aware_alerts_after_analysis(cluster_id: str, analysis_results: dict, subscription_id: str):
    """Enhanced alert checking with subscription context"""
    try:
        from config import alerts_manager
        
        if not alerts_manager:
            logger.debug("⚠️ Alerts manager not available - skipping subscription-aware alert check")
            return
        
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        if not cluster:
            return
        
        # Get current cost from analysis
        current_cost = analysis_results.get('total_cost', 0)
        
        if current_cost <= 0:
            logger.debug(f"No cost data to check alerts for cluster {cluster_id} in subscription {subscription_id[:8]}")
            return
        
        logger.info(f"🔍 Checking subscription-aware alerts for cluster {cluster_id} (${current_cost:.2f}) in subscription {subscription_id[:8]}")
        
        # Get alerts for this specific cluster
        try:
            alerts_data = alerts_manager.get_alerts_route()
            if alerts_data['status'] != 'success':
                logger.warning("Failed to get alerts for subscription-aware checking")
                return
            
            cluster_alerts = [a for a in alerts_data['alerts'] if 
                            a.get('cluster_name') == cluster['name'] and 
                            a.get('resource_group') == cluster['resource_group'] and
                            a.get('status') == 'active']
            
            alerts_triggered = 0
            
            for alert in cluster_alerts:
                try:
                    # Enhanced threshold check with subscription context
                    threshold = alert.get('threshold_amount', 0)
                    
                    if threshold > 0 and current_cost >= threshold:
                        subscription_info = enhanced_cluster_manager.get_cluster_subscription_info(cluster_id)
                        subscription_name = subscription_info.get('subscription_name', 'Unknown') if subscription_info else 'Unknown'
                        
                        logger.info(f"🚨 Alert would trigger for cluster {cluster_id} in {subscription_name}: ${current_cost:.2f} >= ${threshold:.2f}")
                        alerts_triggered += 1
                        
                        # Record alert trigger metric
                        enhanced_cluster_manager.record_subscription_performance_metric(
                            subscription_id, 'alerts_triggered', 1
                        )
                        
                        # For now, just log it - full alert sending would be implemented here
                        
                except Exception as alert_error:
                    logger.error(f"❌ Error checking subscription-aware alert {alert.get('id')}: {alert_error}")
            
            if alerts_triggered > 0:
                logger.info(f"📧 Would trigger {alerts_triggered} subscription-aware alerts for cluster {cluster_id}")
            else:
                logger.debug(f"✅ No subscription-aware alerts triggered for cluster {cluster_id}")
            
        except Exception as alerts_error:
            logger.error(f"❌ Error getting alerts for subscription-aware checking: {alerts_error}")
        
    except Exception as e:
        logger.error(f"❌ Error checking subscription-aware alerts after analysis: {e}")

def run_batch_subscription_analysis(cluster_configs: list, max_concurrent: int = 3):
    """Run analysis for multiple clusters across subscriptions with concurrency control"""
    import concurrent.futures
    
    logger.info(f"🌐 Starting batch subscription-aware analysis for {len(cluster_configs)} clusters")
    
    def analyze_single_cluster(config):
        """Wrapper for single cluster analysis"""
        try:
            cluster_id = config['cluster_id']
            resource_group = config['resource_group']
            cluster_name = config['cluster_name']
            subscription_id = config.get('subscription_id')
            days = config.get('days', 30)
            enable_pod_analysis = config.get('enable_pod_analysis', True)
            
            run_subscription_aware_background_analysis(
                cluster_id, resource_group, cluster_name, subscription_id, days, enable_pod_analysis
            )
            
            return {'cluster_id': cluster_id, 'status': 'success'}
            
        except Exception as e:
            logger.error(f"❌ Batch analysis failed for cluster {config.get('cluster_id', 'unknown')}: {e}")
            return {'cluster_id': config.get('cluster_id', 'unknown'), 'status': 'failed', 'error': str(e)}
    
    # Group clusters by subscription for better resource management
    clusters_by_subscription = {}
    for config in cluster_configs:
        sub_id = config.get('subscription_id', 'unknown')
        if sub_id not in clusters_by_subscription:
            clusters_by_subscription[sub_id] = []
        clusters_by_subscription[sub_id].append(config)
    
    logger.info(f"🌐 Batch analysis across {len(clusters_by_subscription)} subscriptions")
    
    results = []
    
    # Use ThreadPoolExecutor for concurrent analysis
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all analysis tasks
        future_to_config = {
            executor.submit(analyze_single_cluster, config): config 
            for config in cluster_configs
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_config, timeout=1800):  # 30 min timeout
            config = future_to_config[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['status'] == 'success':
                    logger.info(f"✅ Batch analysis completed for cluster {result['cluster_id']}")
                else:
                    logger.error(f"❌ Batch analysis failed for cluster {result['cluster_id']}")
                    
            except Exception as exc:
                logger.error(f"❌ Batch analysis exception for cluster {config.get('cluster_id', 'unknown')}: {exc}")
                results.append({
                    'cluster_id': config.get('cluster_id', 'unknown'),
                    'status': 'failed',
                    'error': str(exc)
                })
    
    # Summary
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    
    logger.info(f"🌐 Batch subscription analysis completed: {successful} successful, {failed} failed")
    
    return results

def monitor_subscription_analysis_health():
    """Monitor health of subscription analysis processes"""
    try:
        logger.info("🌐 Running subscription analysis health check...")
        
        # Get active analysis sessions
        active_sessions = enhanced_cluster_manager.get_subscription_analysis_sessions(status='running')
        
        # Check for sessions running too long
        stale_count = enhanced_cluster_manager.cleanup_stale_subscription_sessions(max_age_hours=2)
        
        # Get performance metrics for all subscriptions
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            cursor = conn.execute('''
                SELECT subscription_id, COUNT(*) as active_clusters
                FROM clusters 
                WHERE status = 'active' AND subscription_id IS NOT NULL
                GROUP BY subscription_id
            ''')
            
            subscription_health = {}
            for row in cursor.fetchall():
                sub_id = row['subscription_id']
                subscription_health[sub_id] = {
                    'active_clusters': row['active_clusters'],
                    'performance_metrics': enhanced_cluster_manager.get_subscription_performance_metrics(sub_id, hours_back=24)
                }
        
        health_summary = {
            'active_analysis_sessions': len(active_sessions),
            'stale_sessions_cleaned': stale_count,
            'subscriptions_monitored': len(subscription_health),
            'subscription_health': subscription_health,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"🌐 Health check complete: {len(active_sessions)} active sessions, {len(subscription_health)} subscriptions monitored")
        
        return health_summary
        
    except Exception as e:
        logger.error(f"❌ Subscription analysis health check failed: {e}")
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}

def schedule_subscription_analysis_maintenance():
    """Schedule regular maintenance for subscription analysis"""
    import threading
    
    def maintenance_worker():
        while True:
            try:
                # Run health check every 30 minutes
                time.sleep(1800)  # 30 minutes
                
                logger.info("🧹 Running scheduled subscription analysis maintenance...")
                
                # Clean up stale sessions
                stale_cleaned = enhanced_cluster_manager.cleanup_stale_subscription_sessions()
                
                # Validate subscription contexts
                validation_results = enhanced_cluster_manager.validate_all_subscription_contexts()
                
                # Clean up old performance metrics (keep last 7 days)
                cutoff_time = datetime.now() - timedelta(days=7)
                with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                    cursor = conn.execute('''
                        DELETE FROM subscription_performance 
                        WHERE measured_at < ?
                    ''', (cutoff_time.isoformat(),))
                    
                    metrics_cleaned = cursor.rowcount
                    conn.commit()
                
                logger.info(f"🧹 Maintenance complete: {stale_cleaned} stale sessions, {metrics_cleaned} old metrics cleaned")
                
            except Exception as e:
                logger.error(f"❌ Subscription analysis maintenance error: {e}")
    
    # Start maintenance thread
    maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
    maintenance_thread.start()
    
    logger.info("🧹 Subscription analysis maintenance scheduler started")

# Legacy compatibility functions
def run_background_analysis(cluster_id: str, resource_group: str, cluster_name: str):
    """Legacy function - redirects to subscription-aware analysis"""
    logger.info(f"⚠️ Legacy analysis call for {cluster_id} - upgrading to subscription-aware analysis")
    run_subscription_aware_background_analysis(cluster_id, resource_group, cluster_name)

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """Legacy function - redirects to subscription-aware alert checking"""
    logger.info(f"⚠️ Legacy alert check for {cluster_id} - upgrading to subscription-aware alerts")
    
    # Try to get subscription ID from cluster
    cluster = enhanced_cluster_manager.get_cluster(cluster_id)
    subscription_id = cluster.get('subscription_id') if cluster else None
    
    if subscription_id:
        check_subscription_aware_alerts_after_analysis(cluster_id, analysis_results, subscription_id)
    else:
        logger.warning(f"⚠️ No subscription context for cluster {cluster_id} - using legacy alert check")
        # Fall back to original logic if needed
        pass