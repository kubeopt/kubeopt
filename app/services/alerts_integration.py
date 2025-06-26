"""
Alerts System Integration for AKS Cost Optimization
"""

import os
import traceback
from datetime import datetime
from flask import jsonify, request
from app.main.config import logger, enhanced_cluster_manager, ALERTS_AVAILABLE

# Global alerts manager
alerts_manager = None

def initialize_alerts_system():
    """Initialize alerts system with proper error handling"""
    global alerts_manager
    
    if not ALERTS_AVAILABLE:
        logger.warning("⚠️ Alerts system not available - skipping initialization")
        return None
    
    try:
        from app.alerts.alerts_manager import (
            EnhancedAlertsManager, 
            init_enhanced_alerts_service, 
            shutdown_enhanced_alerts_service
        )
        
        # Initialize alerts service with cluster manager
        alerts_manager = init_enhanced_alerts_service(enhanced_cluster_manager)
        logger.info("✅ Alerts system initialized successfully")
        
        # Register shutdown handler
        import atexit
        atexit.register(shutdown_enhanced_alerts_service)
        
        return alerts_manager
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize alerts system: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None

def register_alerts_routes(app):
    """Register alerts API routes with the Flask app"""
    
    @app.route('/api/alerts/<int:alert_id>', methods=['GET', 'PUT', 'DELETE'])
    def alert_detail_api(alert_id: int):
        """Individual alert management - FIXED"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            if app.request.method == 'GET':
                try:
                    alerts_data = alerts_manager.get_alerts_route()
                    if alerts_data['status'] == 'success':
                        alert = next((a for a in alerts_data['alerts'] if a['id'] == alert_id), None)
                        if alert:
                            return jsonify({
                                'status': 'success',
                                'alert': alert
                            })
                        else:
                            return jsonify({
                                'status': 'error',
                                'message': 'Alert not found'
                            }), 404
                    else:
                        return jsonify(alerts_data), 500
                except Exception as get_error:
                    logger.error(f"❌ Error getting alert {alert_id}: {get_error}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to get alert: {str(get_error)}'
                    }), 500
            
            elif app.request.method == 'PUT':
                try:
                    data = app.request.get_json() or {}
                    result = alerts_manager.update_alert_route(alert_id, data)
                    
                    if result['status'] == 'success':
                        return jsonify(result)
                    else:
                        return jsonify(result), 400
                except Exception as update_error:
                    logger.error(f"❌ Error updating alert {alert_id}: {update_error}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to update alert: {str(update_error)}'
                    }), 500
            
            elif app.request.method == 'DELETE':
                try:
                    result = alerts_manager.delete_alert_route(alert_id)
                    return jsonify(result)
                except Exception as delete_error:
                    logger.error(f"❌ Error deleting alert {alert_id}: {delete_error}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to delete alert: {str(delete_error)}'
                    }), 500
                
        except Exception as e:
            logger.error(f"❌ Error in alert detail API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/<int:alert_id>/test', methods=['POST'])
    def test_alert_api(alert_id: int):
        """Test alert notification - FIXED"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            result = alerts_manager.test_alert_route(alert_id)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Error testing alert: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/<int:alert_id>/pause', methods=['POST'])
    def pause_alert_api(alert_id: int):
        """Pause/unpause alert - FIXED"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            data = app.request.get_json() or {}
            action = data.get('action', 'pause')  # pause or resume
            status = 'paused' if action == 'pause' else 'active'
            
            result = alerts_manager.update_alert_route(alert_id, {'status': status})
            
            if result['status'] == 'success':
                return jsonify({
                    'status': 'success',
                    'message': f'Alert {action}d successfully'
                })
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"❌ Error pausing/resuming alert: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/triggers', methods=['GET'])
    def alert_triggers_api():
        """Get alert trigger history - FIXED"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            # Return empty triggers for now (can be implemented later)
            return jsonify({
                'status': 'success',
                'triggers': []
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting alert triggers: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/email-config', methods=['GET', 'POST'])
    def email_config_api():
        """Email configuration management - FIXED"""
        try:
            if app.request.method == 'GET':
                # Check if email is configured
                email_configured = bool(
                    os.getenv('SMTP_USERNAME') and 
                    os.getenv('SMTP_PASSWORD')
                )
                
                return jsonify({
                    'status': 'success',
                    'email_configured': email_configured,
                    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': os.getenv('SMTP_PORT', '587'),
                    'from_email': os.getenv('FROM_EMAIL', '')
                })
            
            elif app.request.method == 'POST':
                return jsonify({
                    'status': 'info',
                    'message': 'Email configuration should be set via environment variables'
                })
                
        except Exception as e:
            logger.error(f"❌ Error in email config API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/system-status', methods=['GET'])
    def alerts_system_status():
        """Get alerts system status for debugging - FIXED"""
        try:
            return jsonify({
                'status': 'success',
                'alerts_available': ALERTS_AVAILABLE,
                'alerts_manager_initialized': alerts_manager is not None,
                'alerts_manager_type': type(alerts_manager).__name__ if alerts_manager else None,
                'email_configured': bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
                'smtp_server': os.getenv('SMTP_SERVER', 'Not configured'),
                'cluster_manager_available': enhanced_cluster_manager is not None,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Error in alerts system status: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """Check and trigger alerts after analysis completion"""
    try:
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

def get_alerts_manager():
    """Get the alerts manager instance"""
    return alerts_manager

def is_alerts_available():
    """Check if alerts system is available"""
    return ALERTS_AVAILABLE and alerts_manager is not None