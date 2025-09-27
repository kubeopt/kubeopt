#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Auto Analysis Scheduler for AKS Cost Optimizer
=============================================

Manages automatic analysis scheduling and execution at configurable intervals.
"""

import os
import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AutoAnalysisScheduler:
    """
    Automatic analysis scheduler that runs analysis at configured intervals
    """
    
    # Fixed interval for monitoring (change this constant for testing)
    ANALYSIS_INTERVAL_HOURS = 1  # Change to 0.05 (3 minutes) for testing
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler_thread = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.last_analysis_time = None
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Auto-start scheduler for continuous monitoring
        # Use a delayed startup to ensure app is fully initialized
        def delayed_startup():
            import time
            time.sleep(30)  # Wait 30 seconds to ensure app initialization (scheduler handles proper timing)
            if self._is_auto_analysis_enabled() and not self.is_running:
                logger.info("🚀 Starting continuous monitoring scheduler")
                try:
                    self.start_scheduler()
                except Exception as e:
                    logger.error(f"Failed to start monitoring scheduler: {e}")
        
        # Start scheduler in background thread after app initialization
        import threading
        startup_thread = threading.Thread(target=delayed_startup, daemon=True, name="SchedulerStartup")
        startup_thread.start()
        
        # Also start data preloading for monitoring readiness
        preload_thread = threading.Thread(target=self._preload_cluster_data, daemon=True, name="DataPreloader")
        preload_thread.start()
        
    def start_scheduler(self):
        """Start the automatic analysis scheduler"""
        if self.is_running:
            logger.warning("Auto analysis scheduler is already running")
            raise ValueError("Auto analysis scheduler is already running")
            
        # Check if auto analysis is enabled
        if not self._is_auto_analysis_enabled():
            error_msg = "Auto analysis is disabled. Please enable AUTO_ANALYSIS_ENABLED in environment settings"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
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
        
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("🔄 Auto analysis scheduler loop started")
        
        while not self.stop_event.is_set():
            try:
                # Check if auto analysis is still enabled
                if not self._is_auto_analysis_enabled():
                    logger.info("Auto analysis has been disabled, stopping scheduler")
                    break
                
                # Get interval and check if it's time to run
                interval_hours = self._get_analysis_interval()
                if self._should_run_analysis(interval_hours):
                    logger.info(f"⏰ Starting scheduled analysis (interval: {interval_hours}h)")
                    self._run_scheduled_analysis()
                    self.last_analysis_time = datetime.now()
                
                # Wait for 1 minute before checking again
                self.stop_event.wait(60)
                
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}")
                # Wait a bit before continuing to avoid rapid errors
                self.stop_event.wait(300)  # 5 minutes
                
        self.is_running = False
        logger.info("🔄 Auto analysis scheduler loop ended")
        
    def _is_auto_analysis_enabled(self) -> bool:
        """Check if automatic analysis is enabled"""
        # Auto-analysis is enabled by default for monitoring tools
        # Allow disabling only via explicit environment setting
        disabled = os.getenv('AUTO_ANALYSIS_DISABLED', 'false').lower()
        env_disabled = disabled in ['true', '1', 'yes', 'on']
        
        # If explicitly disabled, respect that
        if env_disabled:
            return False
        
        # Check license feature access (but default to enabled)
        try:
            from infrastructure.services.license_manager import license_manager, FeatureFlag
            feature_enabled = license_manager.is_feature_enabled(FeatureFlag.AUTO_ANALYSIS)
            return feature_enabled
        except Exception as e:
            logger.warning(f"Could not check license for auto-analysis, defaulting to enabled: {e}")
            return True  # Default to enabled for monitoring tools
        
    def _get_analysis_interval(self) -> float:
        """Get the analysis interval in hours (fixed for monitoring)"""
        return self.ANALYSIS_INTERVAL_HOURS
            
    def _should_run_analysis(self, interval_hours: float) -> bool:
        """Check if it's time to run analysis"""
        if self.last_analysis_time is None:
            # First run - set initial time and wait for the full interval
            # This ensures data loading completes before first analysis
            self.last_analysis_time = datetime.now()
            logger.info(f"🕐 Scheduler initialized. First analysis scheduled in {interval_hours} hours")
            return False
            
        # Check if enough time has passed
        next_run_time = self.last_analysis_time + timedelta(hours=interval_hours)
        time_ready = datetime.now() >= next_run_time
        
        # Also ensure system is ready (basic check)
        system_ready = self._is_system_ready()
        
        return time_ready and system_ready
    
    def _is_system_ready(self) -> bool:
        """Check if the system is ready for analysis (basic readiness check)"""
        try:
            # Basic check - ensure app context is available
            if not self.app:
                return False
            
            # Additional checks can be added here if needed
            # For now, we rely on the startup delay to ensure readiness
            return True
            
        except Exception as e:
            logger.warning(f"System readiness check failed: {e}")
            return False
        
    def _run_scheduled_analysis(self):
        """Run the analysis for all available clusters"""
        try:
            # Check if app context is available
            if not self.app:
                logger.error("❌ Flask app not available for scheduled analysis")
                return
                
            with self.app.app_context():
                # Get list of clusters to analyze
                clusters = self._get_available_clusters()
                
                if not clusters:
                    logger.info("📋 No clusters available for automatic analysis")
                    return
                
                # Run analysis for each cluster
                for cluster_id in clusters:
                    try:
                        logger.info(f"🚀 Running automatic analysis for cluster: {cluster_id}")
                        success = self._trigger_cluster_analysis(cluster_id)
                        
                        if success:
                            logger.info(f"✅ Automatic analysis started successfully for cluster: {cluster_id}")
                        else:
                            logger.error(f"❌ Failed to start automatic analysis for cluster: {cluster_id}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error analyzing cluster {cluster_id}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error running scheduled analysis: {e}")
            
    def _get_available_clusters(self) -> list:
        """Get list of available clusters"""
        try:
            # Try to get clusters from the application
            # This is a simplified approach - adjust based on your cluster management logic
            from shared.config.config import enhanced_cluster_manager
            
            if enhanced_cluster_manager and hasattr(enhanced_cluster_manager, 'get_all_clusters'):
                clusters = enhanced_cluster_manager.get_all_clusters()
                return [cluster.get('id', 'demo') for cluster in clusters if cluster.get('id')]
            else:
                # Fallback to demo cluster
                logger.info("Using demo cluster for automatic analysis")
                return ['demo']
                
        except Exception as e:
            logger.error(f"Error getting available clusters: {e}")
            return ['demo']  # Fallback to demo cluster
            
    def _trigger_cluster_analysis(self, cluster_id: str) -> bool:
        """Trigger analysis for a specific cluster"""
        try:
            # Use internal API call to trigger analysis
            with self.app.test_client() as client:
                response = client.post(
                    f'/api/clusters/{cluster_id}/analyze',
                    json={
                        'days': 30,
                        'enable_pod_analysis': True,
                        'auto_triggered': True
                    },
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.get_json()
                    return data.get('status') == 'success'
                else:
                    logger.error(f"Analysis API returned status code: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error triggering cluster analysis: {e}")
            return False
            
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'is_enabled': self._is_auto_analysis_enabled(),
            'interval_hours': self._get_analysis_interval(),
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'next_analysis_time': (
                self.last_analysis_time + timedelta(hours=self._get_analysis_interval())
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
    
    def _preload_cluster_data(self):
        """Preload cluster data in background so it's ready when users need it"""
        try:
            import time
            time.sleep(10)  # Small delay to ensure app is fully started
            
            logger.info("📊 Starting background data preloading for monitoring readiness")
            
            # Get available clusters
            clusters = self._get_available_clusters()
            
            for cluster_id in clusters:
                try:
                    logger.info(f"📈 Preloading data for cluster: {cluster_id}")
                    
                    # Trigger data loading through existing analysis pipeline
                    # This will populate caches without running full analysis
                    self._preload_cluster_cache(cluster_id)
                    
                    # Small delay between clusters to avoid overwhelming system
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to preload data for cluster {cluster_id}: {e}")
                    continue
            
            logger.info("✅ Background data preloading completed")
            
        except Exception as e:
            logger.error(f"❌ Error during data preloading: {e}")
    
    def _preload_cluster_cache(self, cluster_id: str):
        """Preload cache for a specific cluster"""
        try:
            if not self.app:
                return
                
            with self.app.app_context():
                # Import the exact same functions used by the UI
                from presentation.api.api_routes import get_cluster_analysis_data
                from shared.config.config import analysis_cache
                
                # Follow the exact same cache → database → UI flow
                logger.info(f"🔍 Checking cache and database for {cluster_id}")
                
                # Call the same function that the UI calls
                analysis_data = get_cluster_analysis_data(cluster_id)
                
                if analysis_data:
                    logger.info(f"✅ Successfully preloaded data for {cluster_id}")
                    logger.info(f"📊 Data contains: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else type(analysis_data)}")
                    
                    # IMPORTANT: Update database summary fields to ensure portfolio shows data
                    # This ensures last_cost and last_savings are populated for portfolio summary
                    try:
                        from shared.config.config import enhanced_cluster_manager
                        enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_data)
                        logger.info(f"💾 Updated database summary fields for {cluster_id}")
                    except Exception as db_update_error:
                        logger.warning(f"⚠️ Failed to update database summary for {cluster_id}: {db_update_error}")
                        
                else:
                    logger.warning(f"⚠️ No data available for {cluster_id} - may need fresh analysis")
                    
                    # If no data available, could trigger a new analysis here if needed
                    # For now, just log that data needs to be generated
                
        except Exception as e:
            logger.warning(f"Failed to preload cache for {cluster_id}: {e}")

# Global scheduler instance
auto_scheduler = AutoAnalysisScheduler()