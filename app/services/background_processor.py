"""
Background Processing for AKS Cost Optimization
"""

import threading
import time
import sqlite3
from datetime import datetime
from config import logger, enhanced_cluster_manager, analysis_status_tracker, analysis_results

def run_background_analysis(cluster_id: str, resource_group: str, cluster_name: str):
    """Run analysis in background thread with progress tracking"""
    try:
        logger.info(f"🔄 Background analysis started for {cluster_id}")
        
        # Progress tracking function
        def update_progress(progress: int, message: str):
            update_cluster_analysis_status(cluster_id, 'analyzing', progress, message)
            analysis_status_tracker[cluster_id] = {
                'status': 'analyzing',
                'progress': progress,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        
        # Simulate analysis steps with progress updates
        update_progress(10, 'Connecting to Azure...')
        time.sleep(2)
        
        update_progress(25, 'Fetching cost data...')
        time.sleep(3)
        
        update_progress(45, 'Analyzing cluster metrics...')
        time.sleep(2)
        
        update_progress(65, 'Calculating optimization opportunities...')
        
        # Import and run actual analysis
        from analysis_engine import run_consistent_analysis
        result = run_consistent_analysis(
            resource_group, 
            cluster_name, 
            days=30, 
            enable_pod_analysis=True
        )
        
        update_progress(85, 'Generating insights...')
        time.sleep(1)
        
        if result['status'] == 'success':
            # Store results in database
            enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_results)
            
            # Update status to completed
            update_cluster_analysis_status(
                cluster_id, 
                'completed', 
                100, 
                f'Analysis completed! Found ${analysis_results.get("total_savings", 0):.0f}/month savings potential'
            )
            
            analysis_status_tracker[cluster_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Analysis completed successfully',
                'timestamp': datetime.now().isoformat(),
                'results': {
                    'total_cost': analysis_results.get('total_cost', 0),
                    'total_savings': analysis_results.get('total_savings', 0),
                    'confidence': analysis_results.get('analysis_confidence', 0)
                }
            }
            
            logger.info(f"✅ Background analysis completed for {cluster_id}")
            
        else:
            error_message = result.get('message', 'Analysis failed')
            update_cluster_analysis_status(cluster_id, 'failed', 0, error_message)
            
            analysis_status_tracker[cluster_id] = {
                'status': 'failed',
                'progress': 0,
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.error(f"❌ Background analysis failed for {cluster_id}: {error_message}")
            
    except Exception as e:
        error_message = f'Analysis error: {str(e)}'
        logger.error(f"❌ Background analysis exception for {cluster_id}: {e}")
        
        update_cluster_analysis_status(cluster_id, 'failed', 0, error_message)
        analysis_status_tracker[cluster_id] = {
            'status': 'failed',
            'progress': 0,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }

def update_cluster_analysis_status(cluster_id: str, status: str, progress: int, message: str):
    """Update cluster analysis status in database"""
    try:
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            if status == 'analyzing':
                # First time - set started timestamp
                if progress <= 10:
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?, 
                            analysis_started_at = ?
                        WHERE id = ?
                    ''', (status, progress, message, datetime.now().isoformat(), cluster_id))
                else:
                    # Update progress only
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?
                        WHERE id = ?
                    ''', (status, progress, message, cluster_id))
            else:
                # Completed or failed
                conn.execute('''
                    UPDATE clusters 
                    SET analysis_status = ?, analysis_progress = ?, analysis_message = ?
                    WHERE id = ?
                ''', (status, progress, message, cluster_id))
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Failed to update analysis status: {e}")

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """Check and trigger alerts after analysis completion"""
    try:
        from config import alerts_manager
        
        if not alerts_manager:
            logger.debug("⚠️ Alerts manager not available - skipping alert check")
            return
        
        cluster = enhanced_cluster_manager.get_cluster(cluster_id)
        if not cluster:
            return
        
        # Get current cost from analysis
        current_cost = analysis_results.get('total_cost', 0)
        
        if current_cost <= 0:
            logger.debug(f"No cost data to check alerts for cluster {cluster_id}")
            return
        
        logger.info(f"🔍 Checking alerts for cluster {cluster_id} with cost ${current_cost:.2f}")
        
        # Get alerts for this specific cluster
        try:
            alerts_data = alerts_manager.get_alerts_route()
            if alerts_data['status'] != 'success':
                logger.warning("Failed to get alerts for checking")
                return
            
            cluster_alerts = [a for a in alerts_data['alerts'] if 
                            a.get('cluster_name') == cluster['name'] and 
                            a.get('resource_group') == cluster['resource_group'] and
                            a.get('status') == 'active']
            
            alerts_triggered = 0
            
            for alert in cluster_alerts:
                try:
                    # Simple threshold check
                    threshold = alert.get('threshold_amount', 0)
                    
                    if threshold > 0 and current_cost >= threshold:
                        logger.info(f"🚨 Alert would trigger for cluster {cluster_id}: ${current_cost:.2f} >= ${threshold:.2f}")
                        alerts_triggered += 1
                        
                        # For now, just log it - full alert sending would be implemented here
                        
                except Exception as alert_error:
                    logger.error(f"❌ Error checking alert {alert.get('id')}: {alert_error}")
            
            if alerts_triggered > 0:
                logger.info(f"📧 Would trigger {alerts_triggered} alerts for cluster {cluster_id}")
            else:
                logger.debug(f"✅ No alerts triggered for cluster {cluster_id}")
            
        except Exception as alerts_error:
            logger.error(f"❌ Error getting alerts for checking: {alerts_error}")
        
    except Exception as e:
        logger.error(f"❌ Error checking alerts after analysis: {e}")