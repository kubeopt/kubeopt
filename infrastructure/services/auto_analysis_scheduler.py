#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer - KubeOpt
"""

"""
Auto Analysis Scheduler for KubeOpt
===================================

Robust automatic analysis scheduler with:
- Intelligent cluster detection and validation
- Stale status cleanup and recovery
- Comprehensive error handling and logging
- No fallback/static logic - production ready
"""

import os
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class AutoAnalysisScheduler:
    """
    Production-ready automatic analysis scheduler with robust error handling
    """
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler_thread = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.last_analysis_time = None
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
    def start_scheduler(self):
        """Start the automatic analysis scheduler"""
        if self.is_running:
            logger.warning("Auto analysis scheduler is already running")
            return
            
        # Check if auto analysis is enabled
        if not self._is_auto_analysis_enabled():
            logger.info("Auto analysis is disabled in settings")
            return
            
        self.is_running = True
        self.stop_event.clear()
        
        # Start scheduler in a separate thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="AutoAnalysisScheduler"
        )
        self.scheduler_thread.start()
        
        logger.info("🕐 Auto analysis scheduler started")
        
    def stop_scheduler(self):
        """Stop the automatic analysis scheduler"""
        if not self.is_running:
            return
            
        logger.info("🛑 Stopping auto analysis scheduler...")
        self.is_running = False
        self.stop_event.set()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            
        logger.info("✅ Auto analysis scheduler stopped")
    
    def restart_scheduler(self):
        """Restart the scheduler (useful when settings change)"""
        logger.info("🔄 Restarting auto analysis scheduler...")
        self.stop_scheduler()
        time.sleep(1)  # Brief pause to ensure clean shutdown
        self.start_scheduler()
        
    def _scheduler_loop(self):
        """Main scheduler loop with robust error handling"""
        logger.info("🔄 Auto analysis scheduler loop started")
        
        while not self.stop_event.is_set():
            try:
                # Check if auto-analysis is still enabled (user can disable it anytime)
                if not self._is_auto_analysis_enabled():
                    logger.info("🚫 Auto-analysis has been disabled, stopping scheduler...")
                    break
                
                # Validate prerequisites
                if not self._validate_scheduler_prerequisites():
                    logger.warning("📋 Scheduler prerequisites not met, waiting...")
                    self.stop_event.wait(60)
                    continue
                
                # Periodic cleanup of stale statuses (every 10 minutes)
                if not hasattr(self, '_last_cleanup_time') or \
                   (datetime.now() - self._last_cleanup_time).total_seconds() > 600:
                    self._cleanup_stale_analysis_statuses()
                    self._last_cleanup_time = datetime.now()
                
                # Check if it's time to run analysis
                interval_minutes = self._get_analysis_interval()
                if self._should_run_analysis(interval_minutes):
                    # Format interval for display
                    interval_display = self._format_interval_display(interval_minutes)
                    
                    logger.info(f"⏰ Starting scheduled analysis (interval: {interval_display})")
                    
                    # Run analysis with comprehensive error handling
                    success = self._run_scheduled_analysis()
                    
                    if success:
                        self.last_analysis_time = datetime.now()
                        logger.info(f"✅ Scheduled analysis completed successfully")
                    else:
                        logger.error(f"❌ Scheduled analysis failed")
                
                # Wait for 1 minute before checking again
                self.stop_event.wait(60)
                
            except Exception as e:
                logger.error(f"❌ Critical error in scheduler loop: {e}")
                logger.error(f"📋 Exception details: {type(e).__name__}: {str(e)}")
                # Wait longer before continuing to avoid rapid errors
                self.stop_event.wait(300)  # 5 minutes
                
        self.is_running = False
        logger.info("🔄 Auto analysis scheduler loop ended")
        
    def _is_auto_analysis_enabled(self) -> bool:
        """Check if auto-analysis is enabled from environment variables (like it used to work)"""
        try:
            # Check environment variable first (your original working method)
            env_enabled = os.getenv('AUTO_ANALYSIS_ENABLED', 'true').lower()
            logger.info(f"🔍 DEBUG: AUTO_ANALYSIS_ENABLED = '{env_enabled}'")
            
            if env_enabled in ['false', '0', 'no', 'off', 'disabled']:
                logger.info("🚫 Auto-analysis disabled by AUTO_ANALYSIS_ENABLED environment variable")
                return False
            
            # Also check testing override
            disabled_for_testing = os.getenv('DISABLE_AUTO_ANALYSIS_FOR_TESTING', 'false').lower()
            if disabled_for_testing in ['true', '1', 'yes', 'on']:
                logger.info("🧪 Auto-analysis disabled for testing purposes")
                return False
            
            logger.info("✅ Auto-analysis enabled by environment variables")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking auto-analysis environment variables: {e}")
            return False
        
    def _get_analysis_interval(self) -> int:
        """Get the analysis interval in minutes"""
        try:
            # Support both old format (hours) and new format (minutes with suffix)
            interval_str = os.getenv('AUTO_ANALYSIS_INTERVAL', '1m')
            logger.info(f"🔍 DEBUG: Reading AUTO_ANALYSIS_INTERVAL = '{interval_str}'")
            
            if interval_str.endswith('m') or interval_str.endswith('min'):
                # Minutes format: "30m" or "30min"
                interval_value = int(interval_str.rstrip('min').rstrip('m'))
                final_minutes = max(1, min(interval_value, 10080))  # Allow 1-minute minimum for testing
                logger.info(f"🔍 DEBUG: Parsed {interval_str} as {interval_value} minutes, final: {final_minutes} minutes")
                # Between 5 minutes and 7 days (10080 minutes)
                return final_minutes
            elif interval_str.endswith('h') or interval_str.endswith('hour'):
                # Hours format: "1h" or "1hour"
                interval_value = int(interval_str.rstrip('hour').rstrip('h'))
                # Convert hours to minutes
                return max(5, min(interval_value * 60, 10080))
            else:
                # Legacy format (assume hours for backward compatibility)
                interval_value = int(interval_str)
                logger.info(f"Legacy interval format detected, treating {interval_value} as hours")
                return max(60, min(interval_value * 60, 10080))  # Convert to minutes
        except (ValueError, TypeError):
            logger.warning("Invalid AUTO_ANALYSIS_INTERVAL value, using default: 60 minutes")
            return 60
            
    def _should_run_analysis(self, interval_minutes: int) -> bool:
        """Check if it's time to run analysis"""
        if self.last_analysis_time is None:
            # First run - check if we should run immediately or wait
            return True
            
        next_run_time = self.last_analysis_time + timedelta(minutes=interval_minutes)
        return datetime.now() >= next_run_time
        
    def _run_scheduled_analysis(self) -> bool:
        """Run analysis for all available clusters with comprehensive error handling"""
        try:
            # Validate app context
            if not self.app:
                logger.error("❌ Flask app not available for scheduled analysis")
                return False
                
            with self.app.app_context():
                # Get and validate clusters
                clusters = self._get_available_clusters()
                
                if not clusters:
                    logger.warning("📋 No clusters available for automatic analysis")
                    return False
                
                logger.info(f"📋 Found {len(clusters)} cluster(s) for automatic analysis")
                
                # Track analysis results
                successful_analyses = 0
                failed_analyses = 0
                skipped_analyses = 0
                
                # Run analysis for each cluster
                for cluster_data in clusters:
                    cluster_id = cluster_data.get('id')
                    cluster_name = cluster_data.get('name', cluster_id)
                    analysis_status = cluster_data.get('analysis_status', 'unknown')
                    
                    try:
                        logger.info(f"🚀 Running automatic analysis for cluster: {cluster_name} (ID: {cluster_id})")
                        logger.info(f"📋 Current status: {analysis_status}")
                        
                        result = self._trigger_cluster_analysis(cluster_id)
                        
                        if result == 'success':
                            successful_analyses += 1
                            logger.info(f"✅ Automatic analysis started successfully for cluster: {cluster_name}")
                        elif result == 'skipped':
                            skipped_analyses += 1
                            logger.info(f"⏸️ Analysis skipped for cluster: {cluster_name} (already in progress)")
                        else:
                            failed_analyses += 1
                            logger.error(f"❌ Failed to start automatic analysis for cluster: {cluster_name}")
                            
                    except Exception as e:
                        failed_analyses += 1
                        logger.error(f"❌ Error analyzing cluster {cluster_name}: {e}")
                        continue
                
                # Log summary
                total_clusters = len(clusters)
                logger.info(f"📊 Analysis summary: {successful_analyses} started, {skipped_analyses} skipped, {failed_analyses} failed (total: {total_clusters})")
                
                # Consider successful if at least some analyses were started or skipped
                return (successful_analyses + skipped_analyses) > 0
                        
        except Exception as e:
            logger.error(f"❌ Error running scheduled analysis: {e}")
            logger.error(f"📋 Exception details: {type(e).__name__}: {str(e)}")
            return False
            
    def _get_available_clusters(self) -> List[Dict[str, Any]]:
        """Get list of available clusters with full metadata"""
        try:
            # Get clusters from the enhanced cluster manager
            from shared.config.config import enhanced_cluster_manager
            
            if not enhanced_cluster_manager:
                logger.error("❌ Enhanced cluster manager not available")
                return []
                
            if not hasattr(enhanced_cluster_manager, 'get_clusters_with_subscription_info'):
                logger.error("❌ Cluster manager missing required method")
                return []
            
            # Get all clusters with subscription info
            all_clusters = enhanced_cluster_manager.get_clusters_with_subscription_info()
            
            if not all_clusters:
                logger.warning("⚠️ No clusters found in database")
                return []
            
            # Filter and validate clusters for auto-analysis
            valid_clusters = []
            for cluster in all_clusters:
                cluster_id = cluster.get('id')
                cluster_name = cluster.get('name')
                cluster_status = cluster.get('status', 'unknown')
                
                if not cluster_id:
                    logger.warning(f"⚠️ Skipping cluster without ID: {cluster}")
                    continue
                    
                if cluster_status not in ['active', 'pending']:
                    logger.info(f"📋 Skipping inactive cluster: {cluster_name} (status: {cluster_status})")
                    continue
                
                # Add cluster to valid list
                valid_clusters.append(cluster)
                logger.info(f"📋 Found valid cluster: {cluster_name} (ID: {cluster_id}, status: {cluster_status})")
            
            if valid_clusters:
                cluster_names = [c.get('name', c.get('id')) for c in valid_clusters]
                logger.info(f"✅ Auto-analysis will monitor {len(valid_clusters)} cluster(s): {', '.join(cluster_names)}")
            else:
                logger.warning("⚠️ No valid clusters found for auto-analysis")
            
            return valid_clusters
                
        except Exception as e:
            logger.error(f"❌ Error getting available clusters: {e}")
            logger.error(f"📋 Exception details: {type(e).__name__}: {str(e)}")
            return []
            
    def _trigger_cluster_analysis(self, cluster_id: str) -> str:
        """
        Trigger analysis for a specific cluster
        
        Returns:
            'success': Analysis started successfully
            'skipped': Analysis skipped (already running)
            'failed': Analysis failed to start
        """
        try:
            if not cluster_id:
                logger.error("❌ Cannot trigger analysis: cluster_id is empty")
                return 'failed'
            
            # Clean up any stale analysis statuses before triggering
            self._cleanup_stale_analysis_statuses()
            
            # Use internal API call to trigger analysis
            with self.app.test_client() as client:
                payload = {
                    'days': 30,
                    'enable_pod_analysis': True,
                    'auto_triggered': True,
                    'force_refresh': False  # Don't force refresh unless necessary
                }
                
                logger.info(f"📤 Triggering analysis for cluster {cluster_id} with payload: {payload}")
                
                response = client.post(
                    f'/api/clusters/{cluster_id}/analyze',
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                logger.info(f"📥 API response: status={response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    status = data.get('status')
                    message = data.get('message', 'No message')
                    
                    logger.info(f"📋 API response data: status={status}, message={message}")
                    
                    if status == 'success':
                        return 'success'
                    elif status == 'skipped':
                        logger.info(f"⏸️ Analysis skipped for {cluster_id}: {message}")
                        return 'skipped'
                    else:
                        logger.warning(f"❓ Unexpected API status: {status} - {message}")
                        return 'failed'
                        
                elif response.status_code == 409:
                    logger.info(f"⏸️ Analysis already running for {cluster_id}, skipping this interval")
                    return 'skipped'
                else:
                    try:
                        error_data = response.get_json()
                        error_message = error_data.get('message', 'Unknown error')
                    except:
                        error_message = f"HTTP {response.status_code}"
                    
                    logger.error(f"❌ Analysis API error: {error_message}")
                    return 'failed'
                    
        except Exception as e:
            logger.error(f"❌ Exception while triggering cluster analysis: {e}")
            logger.error(f"📋 Exception details: {type(e).__name__}: {str(e)}")
            return 'failed'
            
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        interval_minutes = self._get_analysis_interval()
        
        # Format interval display
        if interval_minutes >= 60:
            interval_display = f"{interval_minutes // 60}h {interval_minutes % 60}m" if interval_minutes % 60 else f"{interval_minutes // 60}h"
        else:
            interval_display = f"{interval_minutes}m"
        
        return {
            'is_running': self.is_running,
            'is_enabled': self._is_auto_analysis_enabled(),
            'interval_minutes': interval_minutes,
            'interval_display': interval_display,
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'next_analysis_time': (
                self.last_analysis_time + timedelta(minutes=interval_minutes)
            ).isoformat() if self.last_analysis_time else "Soon",
        }
        
    def force_analysis_now(self):
        """Force an immediate analysis run"""
        if not self.is_running:
            logger.warning("Scheduler is not running, cannot force analysis")
            return False
            
        try:
            logger.info("🚀 Forcing immediate analysis...")
            self._run_scheduled_analysis()
            self.last_analysis_time = datetime.now()
            return True
        except Exception as e:
            logger.error(f"❌ Error forcing immediate analysis: {e}")
            return False
            
    def _validate_scheduler_prerequisites(self) -> bool:
        """Validate that all prerequisites for running the scheduler are met"""
        try:
            # Check if auto analysis is enabled
            if not self._is_auto_analysis_enabled():
                logger.info("Auto analysis has been disabled, stopping scheduler")
                return False
            
            # Check if Flask app is available
            if not self.app:
                logger.error("❌ Flask app not available")
                return False
            
            # Check if cluster manager is available
            from shared.config.config import enhanced_cluster_manager
            if not enhanced_cluster_manager:
                logger.error("❌ Enhanced cluster manager not available")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating prerequisites: {e}")
            return False
    
    def _format_interval_display(self, interval_minutes: int) -> str:
        """Format interval for display"""
        if interval_minutes >= 60:
            hours = interval_minutes // 60
            minutes = interval_minutes % 60
            if minutes > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{hours}h"
        else:
            return f"{interval_minutes}m"
    
    def _cleanup_stale_analysis_statuses(self):
        """Cleanup stale analysis statuses"""
        try:
            from shared.config.config import enhanced_cluster_manager
            if enhanced_cluster_manager and hasattr(enhanced_cluster_manager, 'cleanup_stale_analyses'):
                stale_count = enhanced_cluster_manager.cleanup_stale_analyses(max_age_hours=1)  # 1 hour
                if stale_count > 0:
                    logger.info(f"🧹 Cleaned up {stale_count} stale analysis statuses")
            else:
                logger.debug("🧹 Stale cleanup method not available")
        except Exception as e:
            logger.error(f"❌ Error during stale cleanup: {e}")
    
    def cleanup_stale_statuses(self):
        """Manually cleanup stale analysis statuses"""
        try:
            from shared.config.config import enhanced_cluster_manager
            if enhanced_cluster_manager and hasattr(enhanced_cluster_manager, 'cleanup_stale_analyses'):
                stale_count = enhanced_cluster_manager.cleanup_stale_analyses(max_age_hours=0.5)  # 30 minutes
                logger.info(f"🧹 Manual cleanup: Reset {stale_count} stale analysis statuses")
                return stale_count
            else:
                logger.error("❌ Enhanced cluster manager not available")
                return 0
        except Exception as e:
            logger.error(f"❌ Error during manual cleanup: {e}")
            return 0

# Global scheduler instance
auto_scheduler = AutoAnalysisScheduler()