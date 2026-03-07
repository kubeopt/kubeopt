#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Enhanced Background Processing for Multi-Subscription AKS Cost Optimization
"""

import threading
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import queue
import uuid
import os
from shared.config.config import logger, enhanced_cluster_manager, analysis_status_tracker, analysis_results

# Use os.cpu_count() instead of psutil for CPU detection
cpu_count = os.cpu_count() or 4  # Default to 4 if unable to detect
MAX_CONCURRENT_ANALYSES = min(
    cpu_count // 2,  # Half your CPU cores
    12               # Reasonable upper limit
)
# Thread management globals
# MAX_CONCURRENT_ANALYSES = 3
ANALYSIS_THREAD_POOL = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_ANALYSES, thread_name_prefix="BG-Analysis")
analysis_queue = queue.Queue(maxsize=50)
active_analyses = {}
analysis_semaphore = threading.Semaphore(MAX_CONCURRENT_ANALYSES)
_status_lock = threading.Lock()  # Shared lock for analysis_status_tracker

def run_subscription_aware_background_analysis(cluster_id: str, resource_group: str, cluster_name: str,
                                              subscription_id: Optional[str] = None, days: int = 30,
                                              enable_pod_analysis: bool = True, cloud_provider: str = 'azure',
                                              region: str = ''):
    """Enhanced background analysis with thread management and subscription awareness"""
    
    # Thread-safe duplicate check with timeout
    with _status_lock:
        if cluster_id in analysis_status_tracker:
            current_status = analysis_status_tracker[cluster_id].get('status')
            if current_status in ['running', 'analyzing']:
                start_time = analysis_status_tracker[cluster_id].get('start_time', time.time())
                elapsed = time.time() - start_time
                
                if elapsed < 1800:  # 30 minutes timeout
                    logger.warning(f"⚠️ Analysis already running for cluster {cluster_id} ({elapsed:.0f}s), skipping duplicate")
                    return
                else:
                    logger.warning(f"⚠️ Stale analysis detected for {cluster_id}, proceeding with new analysis")
                    analysis_status_tracker.pop(cluster_id, None)
                    active_analyses.pop(cluster_id, None)
    
    # Check analysis capacity
    if not analysis_semaphore.acquire(blocking=False):
        logger.warning(f"⚠️ Analysis capacity full ({MAX_CONCURRENT_ANALYSES} running), queueing {cluster_id}")
        try:
            analysis_queue.put((cluster_id, resource_group, cluster_name, subscription_id, days, enable_pod_analysis, cloud_provider, region), timeout=5)
            logger.info(f"📋 Queued analysis for {cluster_id}")
            return
        except queue.Full:
            logger.error(f"❌ Analysis queue full, rejecting {cluster_id}")
            return
    
    session_id = None
    
    try:
        # Track analysis start time and thread
        with _status_lock:
            analysis_status_tracker[cluster_id] = {
                'status': 'starting',
                'start_time': time.time(),
                'thread_id': threading.current_thread().ident,
                'progress': 0
            }
            active_analyses[cluster_id] = {
                'session_id': None,
                'subscription_id': subscription_id,
                'start_time': time.time()
            }
        
        logger.info(f"🌐 Starting subscription-aware background analysis for {cluster_id} (Thread: {threading.current_thread().name})")
        
        # Import analysis engine and cloud provider types
        from infrastructure.persistence.processing.analysis_engine import multi_subscription_analysis_engine
        from infrastructure.cloud_providers.types import CloudProvider as CPEnum

        # Create provider-specific adapters directly (thread-safe, no singleton mutation)
        # IMPORTANT: Do NOT use ProviderRegistry() here — it auto-detects from env vars
        # and would return AWS adapters for Azure clusters once AWS creds are set.
        target_provider = CPEnum.from_string(cloud_provider)
        if target_provider == CPEnum.AWS:
            from infrastructure.cloud_providers.aws.accounts import AWSAccountManager
            from infrastructure.cloud_providers.aws.executor import AWSKubernetesExecutor
            from infrastructure.cloud_providers.aws.inspector import AWSInfrastructureInspector
            account_mgr = AWSAccountManager()
            command_executor = AWSKubernetesExecutor()
            infrastructure_inspector = AWSInfrastructureInspector()
        elif target_provider == CPEnum.GCP:
            from infrastructure.cloud_providers.gcp.accounts import GCPAccountManager
            from infrastructure.cloud_providers.gcp.executor import GCPKubernetesExecutor
            from infrastructure.cloud_providers.gcp.inspector import GCPInfrastructureInspector
            account_mgr = GCPAccountManager()
            command_executor = GCPKubernetesExecutor()
            infrastructure_inspector = GCPInfrastructureInspector()
        else:
            # Azure — explicit adapter creation (not ProviderRegistry which may detect wrong provider)
            from infrastructure.cloud_providers.azure.accounts import AzureAccountAdapter
            from infrastructure.cloud_providers.azure.executor import AzureKubernetesExecutor
            from infrastructure.cloud_providers.azure.inspector import AzureInfrastructureInspector
            account_mgr = AzureAccountAdapter()
            command_executor = AzureKubernetesExecutor()
            infrastructure_inspector = AzureInfrastructureInspector()

        # Auto-detect subscription if not provided
        if not subscription_id:
            logger.info(f"🔍 Auto-detecting subscription for cluster {cluster_name}")
            subscription_id = account_mgr.find_cluster_account(cluster_name, resource_group)

            if not subscription_id:
                raise Exception(f"Could not find cluster {cluster_name} in any accessible subscription")

        # Get subscription info for display
        account_info = account_mgr.get_account_info(subscription_id)
        subscription_name = account_info.get('name', subscription_id[:8]) if account_info else subscription_id[:8]
        
        # Create unique session ID for tracking
        session_id = f"{subscription_id[:8]}_{str(uuid.uuid4())[:8]}"
        
        # Update active analysis tracking
        with _status_lock:
            active_analyses[cluster_id]['session_id'] = session_id
        
        # Track session in database
        session_data = {
            'session_id': session_id,
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'analysis_type': 'MULTI_SUBSCRIPTION',
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

            # Thread-safe update of both in-memory tracker and database
            with _status_lock:
                analysis_status_tracker[cluster_id] = {
                    'status': 'analyzing',
                    'progress': progress,
                    'message': enhanced_message,
                    'timestamp': datetime.now().isoformat(),
                    'subscription_id': subscription_id,
                    'subscription_name': subscription_name,
                    'session_id': session_id,
                    'start_time': analysis_status_tracker.get(cluster_id, {}).get('start_time', time.time())
                }

            # Database updates outside lock (non-critical, best-effort)
            try:
                enhanced_cluster_manager.update_analysis_status(cluster_id, 'analyzing', progress, enhanced_message)
                enhanced_cluster_manager.update_subscription_analysis_session(session_id, {
                    'progress': progress,
                    'message': enhanced_message,
                    'status': 'running'
                })
            except Exception as e:
                logger.warning(f"⚠️ Failed to update DB status for {cluster_id}: {e}")

            logger.info(f"🌐 Session {session_id[:8]}: Progress {progress}% - {enhanced_message}")
        
        # Simulate analysis steps with enhanced progress updates
        update_progress(5, f'Validating cluster access in subscription...')
        
        # Validate cluster access
        from infrastructure.cloud_providers.types import ClusterIdentifier
        if target_provider == CPEnum.AWS:
            # For AWS, use the explicit region param (from DB), fall back to authenticator default
            aws_region = region
            if not aws_region:
                try:
                    from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
                    auth = AWSAuthenticator()
                    if auth.is_authenticated():
                        aws_region = auth.region
                except Exception:
                    pass
            aws_region = aws_region or 'us-east-1'
            cluster_ident = ClusterIdentifier(
                provider=target_provider,
                cluster_name=cluster_name,
                region=aws_region,
                account_id=subscription_id,
            )
        elif target_provider == CPEnum.GCP:
            cluster_ident = ClusterIdentifier(
                provider=target_provider,
                cluster_name=cluster_name,
                region=region or '',
                project_id=subscription_id,
                zone=region or '',
            )
        else:
            cluster_ident = ClusterIdentifier(
                provider=target_provider,
                cluster_name=cluster_name,
                region='',
                resource_group=resource_group,
                subscription_id=subscription_id,
            )
        if not account_mgr.validate_cluster_access(cluster_ident):
            raise Exception(f"Cluster validation failed for {cluster_name} in {subscription_id[:8]}")
        
        # CRITICAL FIX: Ensure cluster exists in database before analysis (from backup code)
        cluster_config = {
            'cluster_name': cluster_name,
            'resource_group': resource_group,
            'subscription_id': subscription_id,
            'cloud_provider': cloud_provider,
            'region': aws_region if target_provider == CPEnum.AWS else region,
            'status': 'active',
            'auto_analyze': True,
        }
        # For AWS, map subscription_id → account_id for cluster_id generation
        if cloud_provider == 'aws':
            cluster_config['account_id'] = subscription_id
        
        account_info = account_mgr.get_account_info(subscription_id)
        subscription_name = account_info.get('name', subscription_id[:8]) if account_info else subscription_id[:8]
        
        try:
            cluster_id_check = enhanced_cluster_manager.add_cluster_with_subscription(
                cluster_config, subscription_id, subscription_name
            )
            logger.info(f"✅ Ensured cluster exists in database: {cluster_id_check}")
        except Exception as cluster_add_error:
            logger.warning(f"⚠️ Cluster add failed (might already exist): {cluster_add_error}")
        
        update_progress(10, f'Setting subscription context...')
        
        # Record performance metric
        start_time = time.time()
        
        provider_label = {'aws': 'AWS account', 'gcp': 'GCP project'}.get(cloud_provider, 'Azure subscription')
        update_progress(20, f'Connecting to {provider_label}...')
        time.sleep(1)
        
        update_progress(30, f'Fetching cost data from subscription context...')
        time.sleep(0.5)  # Reduced from 2 seconds
        
        update_progress(50, f'Analyzing cluster metrics with subscription awareness...')
        time.sleep(0.5)  # Reduced from 2 seconds
        
        update_progress(70, f'Calculating ML-powered optimization opportunities...')

        # For non-Azure providers, align resource_group with the cluster_id prefix
        # so analysis_engine's f"{resource_group}_{cluster_name}" matches the DB cluster_id
        analysis_resource_group = resource_group
        if cloud_provider == 'aws' and not resource_group:
            analysis_resource_group = subscription_id  # account_id used as prefix
        elif cloud_provider == 'gcp' and not resource_group:
            analysis_resource_group = subscription_id  # project_id used as prefix

        # Pre-create cache with provider-specific adapters so analysis engine reuses it
        # IMPORTANT: use analysis_resource_group so the cache key matches what analysis_engine will look up
        from shared.kubernetes_data_cache import get_or_create_cache
        cache_region = ''
        if target_provider == CPEnum.AWS:
            cache_region = aws_region
        elif target_provider == CPEnum.GCP:
            cache_region = region
        get_or_create_cache(
            cluster_name, analysis_resource_group, subscription_id,
            force_fetch=False, cloud_provider=cloud_provider,
            command_executor=command_executor,
            infrastructure_inspector=infrastructure_inspector,
            region=cache_region,
        )

        # Run the actual subscription-aware analysis
        result = multi_subscription_analysis_engine.run_subscription_aware_analysis(
            analysis_resource_group, cluster_name, subscription_id, days, enable_pod_analysis,
            cloud_provider=cloud_provider, region=cache_region
        )
        
        update_progress(85, f'Generating Enhanced Analysis and implementation plan...')
        time.sleep(0.2)  # Reduced from 1 second
        
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
                    'cluster_validation': {},
                    'multi_subscription_enabled': True
                }
            
            # CRITICAL DEBUG: Check if top_cpu_summary is in analysis_results_data before DB save
            if 'top_cpu_summary' in analysis_results_data:
                logger.info(f"✅ BACKGROUND_PROCESSOR: top_cpu_summary IS present before DB save")
                summary = analysis_results_data['top_cpu_summary']
                logger.info(f"   - all_workloads: {len(summary.get('all_workloads', []))}")
                logger.info(f"   - all_hpas: {len(summary.get('all_hpas', []))}")
                logger.info(f"   - max_cpu_utilization: {summary.get('max_cpu_utilization', 'N/A')}")
            else:
                logger.error(f"❌ BACKGROUND_PROCESSOR: top_cpu_summary MISSING before DB save")
                logger.error(f"🔍 BACKGROUND_PROCESSOR: Available keys: {list(analysis_results_data.keys())[:20]}")
            
            # Store results in database with subscription context
            # NOTE: Database save is already handled by analysis engine with enhanced input
            # enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_results_data)  # REMOVED: Duplicate save
            
            # Update status to completed
            completion_message = f'Subscription-aware analysis completed! Found ${analysis_results_data.get("total_savings", 0):.0f}/month savings potential in {subscription_name}'
            
            enhanced_cluster_manager.update_analysis_status(
                cluster_id, 
                'completed', 
                100, 
                completion_message
            )
            
            # Thread-safe completion update
            with _status_lock:
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
            
            logger.info(f"DEBUG: From BackgroundProcessor - HPA efficiency: {analysis_results_data.get('hpa_efficiency', 0):.1f}%")
            logger.info(f"✅ Subscription-aware background analysis completed for {cluster_id} in {subscription_name}")
            
            # Clear kubernetes data cache after analysis completion
            try:
                from shared.kubernetes_data_cache import clear_cluster_cache
                clear_cluster_cache(cluster_name, resource_group, subscription_id, cloud_provider)
                logger.info(f"🗑️ Cleared kubernetes data cache for {cluster_name} after analysis completion")
            except Exception as cache_error:
                logger.warning(f"⚠️ Failed to clear cache for {cluster_name}: {cache_error}")
            
            # Check alerts after successful analysis
            check_subscription_aware_alerts_after_analysis(cluster_id, analysis_results_data, subscription_id)
            
        else:
            error_message = result.get('message', 'Subscription-aware analysis failed')
            enhanced_cluster_manager.update_analysis_status(cluster_id, 'failed', 0, error_message)
            
            with _status_lock:
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
            
            # Clear kubernetes data cache after failed analysis to ensure fresh data on retry
            try:
                from shared.kubernetes_data_cache import clear_cluster_cache
                clear_cluster_cache(cluster_name, resource_group, subscription_id, cloud_provider)
                logger.info(f"🗑️ Cleared kubernetes data cache for {cluster_name} after failed analysis")
            except Exception as cache_error:
                logger.warning(f"⚠️ Failed to clear cache for {cluster_name}: {cache_error}")
            
    except Exception as e:
        error_message = f'Subscription-aware analysis error: {str(e)}'
        logger.error(f"❌ Subscription-aware background analysis exception for {cluster_id}: {e}")
        
        if session_id is not None and session_id:
            enhanced_cluster_manager.update_subscription_analysis_session(session_id, {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'completed_at': datetime.now().isoformat()
            })
        
        enhanced_cluster_manager.update_analysis_status(cluster_id, 'failed', 0, error_message)
        
        # Clear kubernetes data cache after exception to ensure fresh data on retry
        try:
            from shared.kubernetes_data_cache import clear_cluster_cache
            clear_cluster_cache(cluster_name, resource_group, subscription_id, cloud_provider)
            logger.info(f"🗑️ Cleared kubernetes data cache for {cluster_name} after exception")
        except Exception as cache_error:
            logger.warning(f"⚠️ Failed to clear cache for {cluster_name}: {cache_error}")
        
        with _status_lock:
            analysis_status_tracker[cluster_id] = {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'timestamp': datetime.now().isoformat(),
                'subscription_id': subscription_id,
                'session_id': session_id
            }
        
        if subscription_id is not None and subscription_id:
            enhanced_cluster_manager.record_subscription_performance_metric(
                subscription_id, 'failed_analyses', 1
            )
    
    finally:
        # Always clean up resources
        try:
            with _status_lock:
                active_analyses.pop(cluster_id, None)
            analysis_semaphore.release()
            logger.info(f"🧹 Released analysis slot for {cluster_id}")
            
            # Process next item in queue if any
            try:
                next_analysis = analysis_queue.get_nowait()
                logger.info(f"📋 Processing queued analysis: {next_analysis[0]}")
                ANALYSIS_THREAD_POOL.submit(run_subscription_aware_background_analysis, *next_analysis)
            except queue.Empty:
                pass
                
        except Exception as cleanup_error:
            logger.error(f"❌ Error during analysis cleanup: {cleanup_error}")

def start_analysis_queue_processor():
    """Start background processor for queued analyses"""
    def queue_processor():
        while True:
            try:
                time.sleep(5)  # Reduced from 10 seconds for better responsiveness
                
                while not analysis_queue.empty():
                    try:
                        analysis_params = analysis_queue.get_nowait()
                        cluster_id = analysis_params[0]
                        
                        if cluster_id not in active_analyses:
                            future = ANALYSIS_THREAD_POOL.submit(run_subscription_aware_background_analysis, *analysis_params)
                            logger.info(f"📋 Submitted queued analysis for {cluster_id}")
                        else:
                            logger.info(f"⚠️ Skipping queued analysis for {cluster_id} - already active")
                            
                    except queue.Empty:
                        break
                    except Exception as e:
                        logger.error(f"❌ Error processing analysis queue: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Analysis queue processor error: {e}")
                time.sleep(30)  # Reduced from 60 seconds for faster recovery
    
    processor_thread = threading.Thread(target=queue_processor, daemon=True, name="AnalysisQueueProcessor")
    processor_thread.start()
    logger.info("✅ Analysis queue processor started")

def initialize_background_analysis_system():
    """Initialize the background analysis system with thread management"""
    try:
        start_analysis_queue_processor()
        logger.info(f"✅ Background analysis system initialized - Max concurrent: {MAX_CONCURRENT_ANALYSES}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize background analysis system: {e}")
        return False

def check_subscription_aware_alerts_after_analysis(cluster_id: str, analysis_results: dict, subscription_id: str):
    """Enhanced alert checking with subscription context"""
    try:
        from shared.config.config import alerts_manager
        
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
                    threshold = alert.get('threshold_amount', 0)
                    
                    if threshold > 0 and current_cost >= threshold:
                        subscription_info = enhanced_cluster_manager.get_cluster_subscription_info(cluster_id)
                        subscription_name = subscription_info.get('subscription_name', 'Unknown') if subscription_info else 'Unknown'
                        
                        logger.info(f"🚨 Alert would trigger for cluster {cluster_id} in {subscription_name}: ${current_cost:.2f} >= ${threshold:.2f}")
                        alerts_triggered += 1
                        
                        enhanced_cluster_manager.record_subscription_performance_metric(
                            subscription_id, 'alerts_triggered', 1
                        )
                        
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

def run_batch_subscription_analysis(cluster_configs: list, max_concurrent: int = 2):
    """Run analysis for multiple clusters with proper thread management"""
    
    effective_max = min(max_concurrent, MAX_CONCURRENT_ANALYSES)
    
    logger.info(f"🌐 Starting batch subscription-aware analysis for {len(cluster_configs)} clusters (max concurrent: {effective_max})")
    
    results = []
    
    for config in cluster_configs:
        try:
            cluster_id = config['cluster_id']
            resource_group = config['resource_group']
            cluster_name = config['cluster_name']
            subscription_id = config.get('subscription_id')
            days = config.get('days', 30)
            enable_pod_analysis = config.get('enable_pod_analysis', True)
            
            future = ANALYSIS_THREAD_POOL.submit(
                run_subscription_aware_background_analysis,
                cluster_id, resource_group, cluster_name, subscription_id, days, enable_pod_analysis
            )
            
            logger.info(f"📋 Submitted batch analysis for {cluster_id}")
            results.append({'cluster_id': cluster_id, 'status': 'submitted', 'future': future})
            
        except Exception as e:
            logger.error(f"❌ Failed to submit batch analysis for {config.get('cluster_id', 'unknown')}: {e}")
            results.append({'cluster_id': config.get('cluster_id', 'unknown'), 'status': 'failed', 'error': str(e)})
    
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
                time.sleep(1800)  # 30 minutes
                
                logger.info("🧹 Running scheduled subscription analysis maintenance...")
                
                stale_cleaned = enhanced_cluster_manager.cleanup_stale_subscription_sessions()
                
                validation_results = enhanced_cluster_manager.validate_all_subscription_contexts()
                
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
    
    maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
    maintenance_thread.start()
    
    logger.info("🧹 Subscription analysis maintenance scheduler started")

def run_background_analysis(cluster_id: str, resource_group: str, cluster_name: str):
    """Legacy function - redirects to subscription-aware analysis"""
    logger.info(f"⚠️ Legacy analysis call for {cluster_id} - upgrading to subscription-aware analysis")
    run_subscription_aware_background_analysis(cluster_id, resource_group, cluster_name)

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """Legacy function - redirects to subscription-aware alert checking"""
    logger.info(f"⚠️ Legacy alert check for {cluster_id} - upgrading to subscription-aware alerts")
    
    cluster = enhanced_cluster_manager.get_cluster(cluster_id)
    subscription_id = cluster.get('subscription_id') if cluster else None
    
    if subscription_id is not None and subscription_id:
        check_subscription_aware_alerts_after_analysis(cluster_id, analysis_results, subscription_id)