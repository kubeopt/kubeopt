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
                interval_minutes = self._get_analysis_interval()
                if self._should_run_analysis(interval_minutes):
                    # Format interval for display
                    if interval_minutes >= 60:
                        interval_display = f"{interval_minutes // 60}h {interval_minutes % 60}m" if interval_minutes % 60 else f"{interval_minutes // 60}h"
                    else:
                        interval_display = f"{interval_minutes}m"
                    
                    logger.info(f"⏰ Starting scheduled analysis (interval: {interval_display})")
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
        """Auto-analysis is always enabled - this is a mandatory system feature"""
        # Auto-analysis is now mandatory and always enabled
        # Only check if it's explicitly disabled for testing/debugging
        disabled_for_testing = os.getenv('DISABLE_AUTO_ANALYSIS_FOR_TESTING', 'false').lower()
        if disabled_for_testing in ['true', '1', 'yes', 'on']:
            logger.info("🧪 Auto-analysis disabled for testing purposes")
            return False
        
        # Always enabled for production
        return True
        
    def _get_analysis_interval(self) -> int:
        """Get the analysis interval in minutes"""
        try:
            # Support both old format (hours) and new format (minutes with suffix)
            interval_str = os.getenv('AUTO_ANALYSIS_INTERVAL', '60m')
            
            if interval_str.endswith('m') or interval_str.endswith('min'):
                # Minutes format: "30m" or "30min"
                interval_value = int(interval_str.rstrip('min').rstrip('m'))
                # Between 5 minutes and 7 days (10080 minutes)
                return max(5, min(interval_value, 10080))
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

# Global scheduler instance
auto_scheduler = AutoAnalysisScheduler()