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
        enabled = os.getenv('AUTO_ANALYSIS_ENABLED', 'false').lower()
        return enabled in ['true', '1', 'yes', 'on']
        
    def _get_analysis_interval(self) -> int:
        """Get the analysis interval in hours"""
        try:
            interval = int(os.getenv('AUTO_ANALYSIS_INTERVAL', '1'))
            return max(1, min(interval, 168))  # Between 1 hour and 1 week
        except (ValueError, TypeError):
            logger.warning("Invalid AUTO_ANALYSIS_INTERVAL value, using default: 1 hour")
            return 1
            
    def _should_run_analysis(self, interval_hours: int) -> bool:
        """Check if it's time to run analysis"""
        if self.last_analysis_time is None:
            # First run - check if we should run immediately or wait
            return True
            
        next_run_time = self.last_analysis_time + timedelta(hours=interval_hours)
        return datetime.now() >= next_run_time
        
    def _run_scheduled_analysis(self):
        """Run the analysis for all available clusters"""
        try:
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

# Global scheduler instance
auto_scheduler = AutoAnalysisScheduler()