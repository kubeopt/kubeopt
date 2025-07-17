"""
Fixed Enhanced Alerts System Integration for AKS Cost Optimization
with Proper Database Backend and Route Registration
"""

import os
import json
import traceback
import requests
from datetime import datetime
from flask import jsonify, request
from app.main.config import logger, enhanced_cluster_manager, ALERTS_AVAILABLE

# Import the enhanced alerts manager
try:
    from app.alerts.enhanced_alerts_manager import (
        EnhancedAlertsManager, 
        init_enhanced_alerts_service, 
        shutdown_enhanced_alerts_service
    )
    ENHANCED_ALERTS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Enhanced alerts manager not available, using fallback")
    ENHANCED_ALERTS_AVAILABLE = False
    EnhancedAlertsManager = None

# Global alerts manager and notification systems
alerts_manager = None
in_app_notifications = []  # In-memory storage for in-app notifications
slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')

def initialize_alerts_system():
    """Initialize alerts system with enhanced database backend"""
    global alerts_manager
    
    if not ALERTS_AVAILABLE:
        logger.warning("⚠️ Alerts system not available - skipping initialization")
        return None
    
    try:
        if ENHANCED_ALERTS_AVAILABLE:
            # Use the new enhanced alerts manager
            alerts_manager = init_enhanced_alerts_service(enhanced_cluster_manager)
            if alerts_manager:
                logger.info("✅ Enhanced alerts system initialized successfully")
            else:
                logger.error("❌ Enhanced alerts manager initialization returned None")
                return None
        else:
            # Fallback to basic implementation
            logger.warning("⚠️ Using basic alerts implementation")
            return None
        
        # Register shutdown handler
        import atexit
        atexit.register(shutdown_enhanced_alerts_service)
        
        return alerts_manager
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize alerts system: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None

def send_in_app_notification(title, message, alert_type='info', cluster_id=None, alert_id=None, metadata=None):
    """Enhanced in-app notification with better metadata and categorization"""
    global in_app_notifications
    
    notification = {
        'id': f"notification_{datetime.now().timestamp()}",
        'title': title,
        'message': message,
        'type': alert_type,  # info, warning, error, success, critical
        'cluster_id': cluster_id,
        'alert_id': alert_id,
        'timestamp': datetime.now().isoformat(),
        'read': False,
        'dismissed': False,
        'metadata': metadata or {},
        'priority': _calculate_notification_priority(alert_type, metadata),
        'category': _categorize_notification(title, message, metadata),
        'actions': _generate_notification_actions(alert_type, cluster_id, alert_id)
    }
    
    # Add to in-memory storage (in production, you'd use a database)
    in_app_notifications.insert(0, notification)  # Insert at beginning for latest first
    
    # Keep only last 100 notifications
    if len(in_app_notifications) > 100:
        in_app_notifications = in_app_notifications[:100]
    
    logger.info(f"📱 Enhanced in-app notification: {title} - {message} (Priority: {notification['priority']})")
    return notification

def _calculate_notification_priority(alert_type, metadata):
    """Calculate notification priority based on type and metadata"""
    priority_map = {
        'critical': 1,
        'error': 2,
        'warning': 3,
        'success': 4,
        'info': 5
    }
    
    base_priority = priority_map.get(alert_type, 5)
    
    # Adjust based on metadata
    if metadata:
        cost_impact = metadata.get('cost_impact', 0)
        if cost_impact > 1000:
            base_priority = min(base_priority, 2)  # High cost impact = higher priority
        elif cost_impact > 500:
            base_priority = min(base_priority, 3)
    
    return base_priority

def _categorize_notification(title, message, metadata):
    """Categorize notification for better organization"""
    title_lower = title.lower()
    message_lower = message.lower()
    
    if 'cost' in title_lower or 'threshold' in title_lower:
        return 'cost_alert'
    elif 'analysis' in title_lower or 'optimization' in title_lower:
        return 'analysis'
    elif 'cluster' in title_lower:
        return 'cluster_management'
    elif 'alert' in title_lower:
        return 'alert_management'
    else:
        return 'general'

def _generate_notification_actions(alert_type, cluster_id, alert_id):
    """Generate contextual actions for notifications"""
    actions = []
    
    if cluster_id:
        actions.append({
            'label': 'View Cluster',
            'action': 'navigate',
            'url': f'/cluster/{cluster_id}'
        })
    
    if alert_id:
        actions.append({
            'label': 'Manage Alert',
            'action': 'navigate',
            'url': f'/alerts/{alert_id}'
        })
    
    if alert_type in ['error', 'critical', 'warning']:
        actions.append({
            'label': 'Acknowledge',
            'action': 'acknowledge',
            'endpoint': '/api/notifications/acknowledge'
        })
    
    return actions

def send_enhanced_slack_notification(title, message, alert_data=None, cluster_info=None, notification_config=None):
    """Enhanced Slack notification with better formatting and configuration options"""
    if not slack_webhook_url:
        logger.debug("📢 Slack webhook not configured, skipping Slack notification")
        return False
    
    try:
        # Enhanced configuration options
        config = notification_config or {}
        
        # Determine color based on alert severity and type
        color = _determine_slack_color(alert_data, config)
        
        # Create enhanced Slack payload
        slack_payload = {
            "text": f"🚨 AKS Cost Alert: {title}",
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": _build_slack_fields(alert_data, cluster_info),
                    "footer": "AKS Cost Intelligence Platform",
                    "footer_icon": config.get('footer_icon', ''),
                    "ts": int(datetime.now().timestamp()),
                    "mrkdwn_in": ["text", "fields"]
                }
            ]
        }
        
        # Add optional enhancements
        if config.get('include_actions', True):
            slack_payload["attachments"][0]["actions"] = _build_slack_actions(alert_data, cluster_info)
        
        # Add mention if critical
        if alert_data and alert_data.get('severity') == 'critical':
            mention = config.get('critical_mention', '')
            if mention:
                slack_payload["text"] = f"{mention} {slack_payload['text']}"
        
        response = requests.post(
            slack_webhook_url,
            json=slack_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"📢 Enhanced Slack notification sent successfully: {title}")
            return True
        else:
            logger.error(f"❌ Slack notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending enhanced Slack notification: {e}")
        return False

def _determine_slack_color(alert_data, config):
    """Determine Slack attachment color based on alert data and configuration"""
    if config.get('color'):
        return config['color']
    
    if alert_data:
        severity = alert_data.get('severity', 'medium')
        alert_type = alert_data.get('alert_type', '')
        
        if severity == 'critical' or alert_type == 'budget_exceeded':
            return "#ff0000"  # Red
        elif severity == 'high' or alert_type == 'cost_threshold':
            return "#ff9900"  # Orange
        elif severity == 'medium':
            return "#ffcc00"  # Yellow
        elif severity == 'low':
            return "#36a64f"  # Green
    
    return "#36a64f"  # Default green

def _build_slack_fields(alert_data, cluster_info):
    """Build enhanced Slack fields with more context"""
    fields = []
    
    if cluster_info:
        fields.extend([
            {
                "title": "Cluster",
                "value": cluster_info.get('name', 'Unknown'),
                "short": True
            },
            {
                "title": "Resource Group",
                "value": cluster_info.get('resource_group', 'Unknown'),
                "short": True
            }
        ])
        
        if cluster_info.get('subscription_name'):
            fields.append({
                "title": "Subscription",
                "value": cluster_info['subscription_name'],
                "short": True
            })
    
    if alert_data:
        if alert_data.get('current_cost'):
            fields.append({
                "title": "Current Cost",
                "value": f"${alert_data.get('current_cost', 0):,.2f}",
                "short": True
            })
        
        if alert_data.get('threshold_amount'):
            fields.append({
                "title": "Threshold",
                "value": f"${alert_data.get('threshold_amount', 0):,.2f}",
                "short": True
            })
        
        if alert_data.get('threshold_exceeded_by'):
            fields.append({
                "title": "Exceeded By",
                "value": f"${alert_data.get('threshold_exceeded_by', 0):,.2f}",
                "short": True
            })
    
    return fields

def _build_slack_actions(alert_data, cluster_info):
    """Build interactive Slack actions"""
    actions = []
    
    if cluster_info and cluster_info.get('name') and cluster_info.get('resource_group'):
        cluster_id = f"{cluster_info['resource_group']}_{cluster_info['name']}"
        app_url = os.getenv('APP_URL', 'http://localhost:5000')
        
        actions.append({
            "type": "button",
            "text": "View Dashboard",
            "url": f"{app_url}/cluster/{cluster_id}",
            "style": "primary"
        })
        
        actions.append({
            "type": "button",
            "text": "Run Analysis",
            "url": f"{app_url}/cluster/{cluster_id}?action=analyze",
            "style": "default"
        })
    
    if alert_data and alert_data.get('id'):
        actions.append({
            "type": "button",
            "text": "Manage Alert",
            "url": f"{app_url}/alerts/{alert_data['id']}",
            "style": "default"
        })
    
    return actions

def register_alerts_routes(app):
    """Register all alerts routes with proper error handling"""
    
    @app.route('/api/alerts/health', methods=['GET'])
    def alerts_health_check():
        """Health check endpoint for alerts system"""
        try:
            health_status = {
                'alerts_available': ALERTS_AVAILABLE,
                'enhanced_alerts_available': ENHANCED_ALERTS_AVAILABLE,
                'alerts_manager_initialized': alerts_manager is not None,
                'notification_channels': {
                    'email': {
                        'configured': bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
                        'status': 'ready' if bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')) else 'not_configured'
                    },
                    'slack': {
                        'configured': bool(slack_webhook_url),
                        'status': 'ready' if bool(slack_webhook_url) else 'not_configured'
                    },
                    'in_app': {
                        'available': True,
                        'current_notifications': len(in_app_notifications),
                        'status': 'ready'
                    }
                },
                'cluster_manager_available': enhanced_cluster_manager is not None,
                'database_backend': 'enhanced' if ENHANCED_ALERTS_AVAILABLE else 'basic',
                'timestamp': datetime.now().isoformat()
            }
            
            overall_status = 'healthy' if (
                ALERTS_AVAILABLE and 
                alerts_manager is not None and 
                enhanced_cluster_manager is not None
            ) else 'degraded'
            
            return jsonify({
                'status': overall_status,
                'health': health_status
            }), 200 if overall_status == 'healthy' else 503
            
        except Exception as e:
            logger.error(f"❌ Error in alerts health check: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    @app.route('/api/alerts', methods=['GET', 'POST'])
    def alerts_api():
        """Main alerts endpoint"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            if request.method == 'GET':
                return jsonify(alerts_manager.get_alerts_route())
            
            elif request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                result = alerts_manager.create_alert_route(data)
                status_code = 201 if result['status'] == 'success' else 400
                return jsonify(result), status_code
                
        except Exception as e:
            logger.error(f"❌ Error in alerts API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/<int:alert_id>', methods=['GET', 'PUT', 'DELETE'])
    def alert_detail_api(alert_id: int):
        """Individual alert management"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            if request.method == 'GET':
                alert = alerts_manager.db.get_alert(alert_id)
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
            
            elif request.method == 'PUT':
                data = request.get_json() or {}
                result = alerts_manager.update_alert_route(alert_id, data)
                
                if result['status'] == 'success':
                    # Send in-app notification for alert update
                    action = 'paused' if data.get('status') == 'paused' else 'updated'
                    send_in_app_notification(
                        f"Alert {action.title()}",
                        f"Alert '{data.get('name', alert_id)}' has been {action}",
                        'info',
                        alert_id=alert_id,
                        metadata={
                            'action': action,
                            'updated_fields': list(data.keys()),
                            'user_action': True
                        }
                    )
                    return jsonify(result)
                else:
                    return jsonify(result), 400
            
            elif request.method == 'DELETE':
                result = alerts_manager.delete_alert_route(alert_id)
                
                if result['status'] == 'success':
                    # Send in-app notification for alert deletion
                    send_in_app_notification(
                        "Alert Deleted",
                        f"Alert {alert_id} has been deleted successfully",
                        'warning',
                        alert_id=alert_id,
                        metadata={
                            'action': 'deleted',
                            'user_action': True,
                            'irreversible': True
                        }
                    )
                
                return jsonify(result)
                
        except Exception as e:
            logger.error(f"❌ Error in alert detail API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/<int:alert_id>/test', methods=['POST'])
    def test_alert_api(alert_id: int):
        """Test alert notification"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            result = alerts_manager.test_alert_route(alert_id)
            
            # Also send in-app notification for test
            if result['status'] == 'success':
                send_in_app_notification(
                    "Alert Test Completed",
                    f"Test notification sent for alert {alert_id}",
                    'info',
                    alert_id=alert_id,
                    metadata={
                        'test_notification': True,
                        'channels_tested': result.get('channels_tested', [])
                    }
                )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Error testing alert: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/<int:alert_id>/pause', methods=['POST'])
    def pause_alert_api(alert_id: int):
        """Pause/unpause alert"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            data = request.get_json() or {}
            action = data.get('action', 'pause')  # pause or resume
            status = 'paused' if action == 'pause' else 'active'
            
            result = alerts_manager.update_alert_route(alert_id, {'status': status})
            
            if result['status'] == 'success':
                # Send in-app notification
                send_in_app_notification(
                    f"Alert {action.title()}d",
                    f"Alert {alert_id} has been {action}d successfully",
                    'info',
                    alert_id=alert_id,
                    metadata={
                        'action': action,
                        'new_status': status,
                        'user_action': True
                    }
                )
                
                return jsonify({
                    'status': 'success',
                    'message': f'Alert {action}d successfully',
                    'new_status': status
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
        """Get alert trigger history"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            alert_id = request.args.get('alert_id')
            alert_id = int(alert_id) if alert_id else None
            
            result = alerts_manager.get_alert_triggers_route(alert_id)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Error getting alert triggers: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/statistics', methods=['GET'])
    def alerts_statistics_api():
        """Get alert statistics"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            result = alerts_manager.get_alert_statistics_route()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Error getting alert statistics: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/system-status', methods=['GET'])
    def alerts_system_status():
        """Get alerts system status"""
        try:
            return jsonify({
                'status': 'success',
                'alerts_available': ALERTS_AVAILABLE,
                'enhanced_alerts_available': ENHANCED_ALERTS_AVAILABLE,
                'alerts_manager_initialized': alerts_manager is not None,
                'alerts_manager_type': type(alerts_manager).__name__ if alerts_manager else None,
                'notification_channels': {
                    'email': {
                        'configured': bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
                        'smtp_server': os.getenv('SMTP_SERVER', 'Not configured'),
                        'smtp_port': os.getenv('SMTP_PORT', 'Not configured'),
                        'from_email': os.getenv('FROM_EMAIL', 'Not configured'),
                        'status': 'ready' if bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')) else 'not_configured'
                    },
                    'slack': {
                        'configured': bool(slack_webhook_url),
                        'webhook_configured': bool(slack_webhook_url),
                        'enhanced_features': True,
                        'status': 'ready' if bool(slack_webhook_url) else 'not_configured'
                    },
                    'in_app': {
                        'available': True,
                        'current_notifications': len(in_app_notifications),
                        'max_capacity': 100,
                        'status': 'ready'
                    }
                },
                'cluster_manager_available': enhanced_cluster_manager is not None,
                'database_backend': 'enhanced' if ENHANCED_ALERTS_AVAILABLE else 'basic',
                'routes_registered': True,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Error in alerts system status: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    @app.route('/api/notifications/in-app', methods=['GET', 'POST', 'PUT'])
    def in_app_notifications_api():
        """In-app notifications management"""
        try:
            if request.method == 'GET':
                # Enhanced filtering options
                unread_only = request.args.get('unread_only', 'false').lower() == 'true'
                cluster_id = request.args.get('cluster_id')
                category = request.args.get('category')
                priority = request.args.get('priority', type=int)
                limit = int(request.args.get('limit', 50))
                
                filtered_notifications = in_app_notifications
                
                # Apply filters
                if unread_only:
                    filtered_notifications = [n for n in filtered_notifications if not n['read']]
                
                if cluster_id:
                    filtered_notifications = [n for n in filtered_notifications if n.get('cluster_id') == cluster_id]
                
                if category:
                    filtered_notifications = [n for n in filtered_notifications if n.get('category') == category]
                
                if priority:
                    filtered_notifications = [n for n in filtered_notifications if n.get('priority') == priority]
                
                # Apply limit
                filtered_notifications = filtered_notifications[:limit]
                
                # Get summary statistics
                stats = {
                    'total_notifications': len(in_app_notifications),
                    'unread_count': len([n for n in in_app_notifications if not n['read']]),
                    'dismissed_count': len([n for n in in_app_notifications if n['dismissed']])
                }
                
                return jsonify({
                    'status': 'success',
                    'notifications': filtered_notifications,
                    'statistics': stats,
                    'filtered_count': len(filtered_notifications)
                })
            
            elif request.method == 'POST':
                # Create notification
                data = request.get_json()
                if not data:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                notification = send_in_app_notification(
                    data.get('title', 'Manual Notification'),
                    data.get('message', 'Test notification'),
                    data.get('type', 'info'),
                    data.get('cluster_id'),
                    data.get('alert_id'),
                    data.get('metadata', {})
                )
                
                return jsonify({
                    'status': 'success',
                    'message': 'In-app notification created',
                    'notification': notification
                }), 201
            
            elif request.method == 'PUT':
                # Update notifications
                data = request.get_json() or {}
                notification_ids = data.get('notification_ids', [])
                action = data.get('action', 'mark_read')
                
                updated_count = 0
                for notification in in_app_notifications:
                    if notification['id'] in notification_ids:
                        if action == 'mark_read':
                            notification['read'] = True
                        elif action == 'mark_unread':
                            notification['read'] = False
                        elif action == 'dismiss':
                            notification['dismissed'] = True
                        updated_count += 1
                
                return jsonify({
                    'status': 'success',
                    'message': f'{action.replace("_", " ").title()} applied to {updated_count} notifications',
                    'updated_count': updated_count
                })
                
        except Exception as e:
            logger.error(f"❌ Error in in-app notifications API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    logger.info("✅ Enhanced alerts routes registered successfully")

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """Enhanced alert checking after analysis completion"""
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
        
        logger.info(f"🔍 Enhanced alert checking for cluster {cluster_id} with cost ${current_cost:.2f}")
        
        # Check alerts using the enhanced alerts manager
        triggered_alerts = alerts_manager.check_cluster_alerts(cluster_id, current_cost)
        
        # Send additional in-app notifications for triggered alerts
        for triggered_alert in triggered_alerts:
            alert = triggered_alert['alert']
            
            send_in_app_notification(
                f"Cost Alert: {alert['name']}",
                f"Cluster {cluster['name']} has exceeded its cost threshold",
                'warning',
                cluster_id=cluster_id,
                alert_id=alert['id'],
                metadata={
                    'cost_impact': triggered_alert['threshold_exceeded_by'],
                    'threshold_exceeded': True,
                    'automated_trigger': True,
                    'analysis_triggered': True
                }
            )
        
        if triggered_alerts:
            logger.info(f"📧 Triggered {len(triggered_alerts)} enhanced alerts for cluster {cluster_id}")
        else:
            logger.debug(f"✅ No alerts triggered for cluster {cluster_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced alert checking after analysis: {e}")

def get_alerts_manager():
    """Get the alerts manager instance"""
    return alerts_manager

def is_alerts_available():
    """Check if alerts system is available"""
    return ALERTS_AVAILABLE and alerts_manager is not None

def get_in_app_notifications():
    """Get all in-app notifications"""
    return in_app_notifications

def clear_in_app_notifications():
    """Clear all in-app notifications"""
    global in_app_notifications
    in_app_notifications = []
    logger.info("🧹 Cleared all in-app notifications")

def get_notification_stats():
    """Get notification statistics"""
    return {
        'total_notifications': len(in_app_notifications),
        'unread_count': len([n for n in in_app_notifications if not n['read']]),
        'dismissed_count': len([n for n in in_app_notifications if n['dismissed']]),
        'email_configured': bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
        'slack_configured': bool(slack_webhook_url),
        'in_app_available': True,
        'enhanced_backend': ENHANCED_ALERTS_AVAILABLE
    }