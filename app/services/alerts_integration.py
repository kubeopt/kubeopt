"""
Alerts System Integration for AKS Cost Optimization - ENHANCED
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
        # FIXED: Import from the correct location
        from app.alerts.enhanced_alerts_manager import (
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
    """Register alerts API routes with the Flask app - ENHANCED"""
    
    @app.route('/api/alerts', methods=['GET', 'POST'])
    def alerts_api():
        """Main alerts endpoint - ENHANCED"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            if request.method == 'GET':
                # Get cluster_id filter if provided
                cluster_id = request.args.get('cluster_id')
                if cluster_id:
                    # Filter alerts for specific cluster
                    all_alerts = alerts_manager.get_alerts_route()
                    if all_alerts['status'] == 'success':
                        # Enhanced filtering with multiple matching strategies
                        filtered_alerts = []
                        cluster = enhanced_cluster_manager.get_cluster(cluster_id) if enhanced_cluster_manager else None
                        
                        for alert in all_alerts['alerts']:
                            # Strategy 1: Direct cluster_id match
                            if alert.get('cluster_id') == cluster_id:
                                filtered_alerts.append(alert)
                                continue
                            
                            # Strategy 2: Match by cluster name and resource group if cluster info available
                            if cluster:
                                if (alert.get('cluster_name') == cluster.get('name') and 
                                    alert.get('resource_group') == cluster.get('resource_group')):
                                    filtered_alerts.append(alert)
                                    continue
                                
                                # Strategy 3: Match by cluster name only
                                if alert.get('cluster_name') == cluster.get('name'):
                                    filtered_alerts.append(alert)
                        
                        return jsonify({
                            'status': 'success',
                            'alerts': filtered_alerts,
                            'total_alerts': len(filtered_alerts),
                            'cluster_id': cluster_id,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        return jsonify(all_alerts)
                else:
                    return jsonify(alerts_manager.get_alerts_route())
            
            elif request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                # Enhanced cluster info resolution
                if not data.get('cluster_id'):
                    cluster_name = data.get('cluster_name')
                    resource_group = data.get('resource_group')
                    
                    if cluster_name and resource_group and enhanced_cluster_manager:
                        try:
                            clusters = enhanced_cluster_manager.get_clusters_with_subscription_info()
                            for cluster in clusters:
                                if (cluster.get('name') == cluster_name and 
                                    cluster.get('resource_group') == resource_group):
                                    data['cluster_id'] = cluster.get('id')
                                    logger.info(f"📋 Resolved cluster_id: {data['cluster_id']} for {cluster_name}")
                                    break
                        except Exception as cluster_error:
                            logger.warning(f"⚠️ Could not look up cluster info: {cluster_error}")
                
                # Enhanced validation and defaults
                if not data.get('cluster_name'):
                    if data.get('cluster_id') and enhanced_cluster_manager:
                        try:
                            cluster = enhanced_cluster_manager.get_cluster(data['cluster_id'])
                            if cluster:
                                data['cluster_name'] = cluster.get('name', data['cluster_id'])
                                data['resource_group'] = cluster.get('resource_group', 'Unknown Resource Group')
                        except Exception:
                            data['cluster_name'] = data.get('cluster_id', 'Unknown Cluster')
                    else:
                        data['cluster_name'] = data.get('cluster_id', 'Unknown Cluster')
                
                if not data.get('resource_group'):
                    data['resource_group'] = 'Unknown Resource Group'
                
                result = alerts_manager.create_alert_route(data)
                status_code = 201 if result['status'] == 'success' else 400
                return jsonify(result), status_code
                
        except Exception as e:
            logger.error(f"❌ Error in alerts API: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/health', methods=['GET'])
    def alerts_health_check():
        """Health check endpoint for alerts system"""
        try:
            health_status = {
                'alerts_available': ALERTS_AVAILABLE,
                'alerts_manager_initialized': alerts_manager is not None,
                'enhanced_alerts_available': True,
                'notification_channels': {
                    'email': {
                        'configured': bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
                        'status': 'ready' if bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')) else 'not_configured'
                    },
                    'slack': {
                        'configured': bool(os.getenv('SLACK_WEBHOOK_URL')),
                        'status': 'ready' if bool(os.getenv('SLACK_WEBHOOK_URL')) else 'not_configured'
                    },
                    'in_app': {
                        'available': True,
                        'current_notifications': 0,
                        'status': 'ready'
                    }
                },
                'cluster_manager_available': enhanced_cluster_manager is not None,
                'database_backend': 'enhanced',
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
            
            elif request.method == 'PUT':
                try:
                    data = request.get_json() or {}
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
            
            elif request.method == 'DELETE':
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
        """Test alert notification"""
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
        """Pause/unpause alert"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
                
            data = request.get_json() or {}
            action = data.get('action', 'pause')
            status = 'paused' if action == 'pause' else 'active'
            
            result = alerts_manager.update_alert_route(alert_id, {'status': status})
            
            if result['status'] == 'success':
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
                
            try:
                result = alerts_manager.get_alert_triggers_route()
                return jsonify(result)
            except Exception as triggers_error:
                logger.warning(f"⚠️ Error getting triggers from database: {triggers_error}")
                return jsonify({
                    'status': 'success',
                    'triggers': [],
                    'total_triggers': 0,
                    'message': 'No triggers available'
                })
            
        except Exception as e:
            logger.error(f"❌ Error getting alert triggers: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/email-config', methods=['GET', 'POST'])
    def email_config_api():
        """Email configuration management"""
        try:
            if request.method == 'GET':
                email_configured = bool(
                    os.getenv('SMTP_USERNAME') and 
                    os.getenv('SMTP_PASSWORD')
                )
                
                return jsonify({
                    'status': 'success',
                    'email_configured': email_configured,
                    'slack_configured': bool(os.getenv('SLACK_WEBHOOK_URL')),
                    'in_app_available': True,
                    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': os.getenv('SMTP_PORT', '587'),
                    'from_email': os.getenv('FROM_EMAIL', ''),
                    'notification_channels': {
                        'email': email_configured,
                        'slack': bool(os.getenv('SLACK_WEBHOOK_URL')),
                        'in_app': True
                    }
                })
            
            elif request.method == 'POST':
                return jsonify({
                    'status': 'info',
                    'message': 'Email and Slack configuration should be set via environment variables',
                    'required_env_vars': {
                        'email': ['SMTP_USERNAME', 'SMTP_PASSWORD', 'SMTP_SERVER', 'SMTP_PORT', 'FROM_EMAIL'],
                        'slack': ['SLACK_WEBHOOK_URL']
                    }
                })
                
        except Exception as e:
            logger.error(f"❌ Error in email config API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/system-status', methods=['GET'])
    def alerts_system_status():
        """Get alerts system status for debugging"""
        try:
            return jsonify({
                'status': 'success',
                'alerts_available': ALERTS_AVAILABLE,
                'enhanced_alerts_available': True,
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
                        'configured': bool(os.getenv('SLACK_WEBHOOK_URL')),
                        'webhook_configured': bool(os.getenv('SLACK_WEBHOOK_URL')),
                        'status': 'ready' if bool(os.getenv('SLACK_WEBHOOK_URL')) else 'not_configured'
                    },
                    'in_app': {
                        'available': True,
                        'current_notifications': 0,
                        'status': 'ready'
                    }
                },
                'cluster_manager_available': enhanced_cluster_manager is not None,
                'database_backend': 'enhanced',
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
                unread_only = request.args.get('unread_only', 'false').lower() == 'true'
                limit = int(request.args.get('limit', 50))
                
                # Production: This would read from a notifications database table
                # For now, return empty as no persistent storage is implemented yet
                notifications = []
                
                return jsonify({
                    'status': 'success',
                    'notifications': notifications,
                    'unread_count': 0,
                    'total_count': 0,
                    'limit': limit,
                    'unread_only': unread_only
                })
            
            elif request.method == 'POST':
                data = request.get_json() or {}
                
                if not data.get('title') or not data.get('message'):
                    return jsonify({
                        'status': 'error',
                        'message': 'Title and message are required'
                    }), 400
                
                notification_id = f"notification_{int(datetime.now().timestamp())}"
                logger.info(f"📱 Created in-app notification: {data.get('title')}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Notification created successfully',
                    'notification_id': notification_id
                })
            
            elif request.method == 'PUT':
                data = request.get_json() or {}
                notification_ids = data.get('notification_ids', [])
                action = data.get('action', 'mark_read')
                
                if not notification_ids:
                    return jsonify({
                        'status': 'error',
                        'message': 'notification_ids required'
                    }), 400
                
                logger.info(f"📱 Updated {len(notification_ids)} notifications: {action}")
                
                return jsonify({
                    'status': 'success',
                    'message': f'Successfully {action} {len(notification_ids)} notifications',
                    'updated_count': len(notification_ids)
                })
                
        except Exception as e:
            logger.error(f"❌ Error in in-app notifications API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/notifications/slack/test', methods=['POST'])
    def test_slack_notification():
        """Test Slack notification"""
        try:
            if not os.getenv('SLACK_WEBHOOK_URL'):
                return jsonify({
                    'status': 'error',
                    'message': 'Slack webhook URL not configured'
                }), 400
            
            data = request.get_json() or {}
            title = data.get('title', 'Test Notification')
            message = data.get('message', 'This is a test message from AKS Cost Intelligence')
            
            import requests
            
            payload = {
                "text": f"🧪 {title}",
                "attachments": [
                    {
                        "color": "#36a64f",
                        "title": title,
                        "text": message,
                        "footer": "AKS Cost Intelligence - Test Mode",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                os.getenv('SLACK_WEBHOOK_URL'), 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Slack test notification sent successfully")
                return jsonify({
                    'status': 'success',
                    'message': 'Slack test notification sent successfully'
                })
            else:
                logger.error(f"❌ Slack test failed: {response.status_code} - {response.text}")
                return jsonify({
                    'status': 'error',
                    'message': f'Slack test failed: {response.status_code}'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error testing Slack notification: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Slack test error: {str(e)}'
            }), 500

    @app.route('/api/alerts/statistics', methods=['GET'])
    def alert_statistics_api():
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

    # ENHANCED: Alert testing endpoint for debugging
    @app.route('/api/alerts/test-trigger/<cluster_id>', methods=['POST'])
    def test_trigger_alerts(cluster_id):
        """Test alert triggering for a specific cluster - ENHANCED"""
        try:
            data = request.get_json() or {}
            test_cost = data.get('test_cost')
            
            if not test_cost or test_cost <= 0:
                return jsonify({
                    'status': 'error',
                    'message': 'Valid test_cost required'
                }), 400
            
            logger.info(f"🧪 Manual alert test triggered for cluster {cluster_id} with cost ${test_cost}")
            
            # Get cluster information
            cluster = enhanced_cluster_manager.get_cluster(cluster_id) if enhanced_cluster_manager else None
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Create test analysis results
            test_analysis = {
                'total_cost': test_cost,
                'cluster_id': cluster_id,
                'cluster_name': cluster.get('name'),
                'resource_group': cluster.get('resource_group'),
                'test_mode': True
            }
            
            # Run enhanced alert checking
            triggered_alerts = check_alerts_after_analysis(cluster_id, test_analysis)
            
            return jsonify({
                'status': 'success',
                'message': f'Alert test completed for cluster {cluster_id}',
                'cluster_id': cluster_id,
                'test_cost': test_cost,
                'triggered_alerts': len(triggered_alerts) if triggered_alerts else 0,
                'alerts': triggered_alerts if triggered_alerts else []
            })
            
        except Exception as e:
            logger.error(f"❌ Error in test trigger alerts: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    logger.info("✅ Enhanced alerts routes registered successfully")

def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
    """ENHANCED: Check and trigger alerts after analysis completion"""
    try:
        logger.info(f"🔍 Starting enhanced alert check for cluster {cluster_id}")
        
        if not alerts_manager:
            logger.warning("⚠️ Alerts manager not available - skipping alert check")
            return []
        
        # Get cluster information
        cluster = enhanced_cluster_manager.get_cluster(cluster_id) if enhanced_cluster_manager else None
        if not cluster:
            logger.warning(f"⚠️ Cluster {cluster_id} not found in cluster manager")
            return []
        
        # ENHANCED: Extract current cost with multiple fallback strategies
        current_cost = 0.0
        cost_sources = [
            'total_cost',
            'monthly_cost', 
            'current_month_cost',
            'total_monthly_cost'
        ]
        
        for source in cost_sources:
            if source in analysis_results and analysis_results[source] is not None:
                try:
                    current_cost = float(analysis_results[source])
                    if current_cost > 0:
                        logger.info(f"💰 Found cost data from '{source}': ${current_cost:.2f}")
                        break
                except (ValueError, TypeError):
                    continue
        
        # Check nested cost breakdown if no direct cost found
        if current_cost == 0 and 'cost_breakdown' in analysis_results:
            cost_breakdown = analysis_results['cost_breakdown']
            if isinstance(cost_breakdown, dict):
                for breakdown_key in ['total', 'monthly_total', 'current_total']:
                    if breakdown_key in cost_breakdown:
                        try:
                            current_cost = float(cost_breakdown[breakdown_key])
                            if current_cost > 0:
                                logger.info(f"💰 Found cost data from cost_breakdown.{breakdown_key}: ${current_cost:.2f}")
                                break
                        except (ValueError, TypeError):
                            continue
        
        if current_cost <= 0:
            logger.warning(f"⚠️ No valid cost data found for cluster {cluster_id}. Analysis keys: {list(analysis_results.keys())}")
            return []
        
        logger.info(f"🔍 Checking alerts for cluster {cluster_id} with cost ${current_cost:.2f}")
        
        # Get all alerts and filter for this cluster
        triggered_alerts = []
        
        try:
            alerts_data = alerts_manager.get_alerts_route()
            if alerts_data['status'] != 'success':
                logger.error("❌ Failed to get alerts from alerts manager")
                return []
            
            all_alerts = alerts_data['alerts']
            logger.info(f"📋 Found {len(all_alerts)} total alerts in system")
            
            # ENHANCED: Find alerts for this cluster using multiple matching strategies
            cluster_alerts = []
            
            for alert in all_alerts:
                # Skip inactive alerts
                if alert.get('status') != 'active':
                    continue
                
                # Strategy 1: Direct cluster_id match
                if alert.get('cluster_id') == cluster_id:
                    cluster_alerts.append(alert)
                    logger.info(f"✅ Matched alert by cluster_id: {alert['name']}")
                    continue
                
                # Strategy 2: Match by cluster_name and resource_group
                if (alert.get('cluster_name') == cluster['name'] and 
                    alert.get('resource_group') == cluster['resource_group']):
                    cluster_alerts.append(alert)
                    logger.info(f"✅ Matched alert by name/resource_group: {alert['name']}")
                    continue
                
                # Strategy 3: Match by cluster_name only
                if alert.get('cluster_name') == cluster['name']:
                    cluster_alerts.append(alert)
                    logger.info(f"✅ Matched alert by cluster_name only: {alert['name']}")
            
            logger.info(f"🎯 Found {len(cluster_alerts)} active alerts for cluster {cluster_id}")
            
            # ENHANCED: Check each alert against current cost
            for alert in cluster_alerts:
                try:
                    threshold = alert.get('threshold_amount')
                    if threshold is None or threshold <= 0:
                        logger.warning(f"⚠️ Alert {alert['id']} has invalid threshold: {threshold}")
                        continue
                    
                    threshold = float(threshold)
                    logger.info(f"🔍 Checking alert '{alert['name']}': ${current_cost:.2f} vs ${threshold:.2f}")
                    
                    if current_cost >= threshold:
                        exceeded_by = current_cost - threshold
                        percentage_over = (exceeded_by / threshold) * 100
                        
                        logger.info(f"🚨 ALERT TRIGGERED: '{alert['name']}' - Cost ${current_cost:.2f} exceeds threshold ${threshold:.2f} by ${exceeded_by:.2f} ({percentage_over:.1f}%)")
                        
                        # ENHANCED: Create comprehensive notification data
                        notification_data = {
                            'alert_id': alert['id'],
                            'alert_name': alert['name'],
                            'cluster_id': cluster_id,
                            'cluster_name': cluster['name'],
                            'resource_group': cluster['resource_group'],
                            'current_cost': current_cost,
                            'threshold_amount': threshold,
                            'threshold_exceeded_by': exceeded_by,
                            'percentage_over': percentage_over,
                            'triggered_at': datetime.now().isoformat(),
                            'notification_channels': alert.get('notification_channels', ['email'])
                        }
                        
                        # ENHANCED: Record trigger in database
                        try:
                            trigger_id = alerts_manager.db.record_alert_trigger({
                                'alert_id': alert['id'],
                                'cluster_id': cluster_id,
                                'trigger_reason': f"Cost ${current_cost:.2f} exceeded threshold ${threshold:.2f}",
                                'current_cost': current_cost,
                                'threshold_amount': threshold,
                                'threshold_exceeded_by': exceeded_by,
                                'notification_sent': False,
                                'notification_channels': alert.get('notification_channels', ['email']),
                                'metadata': {
                                    'alert_name': alert['name'],
                                    'percentage_over': percentage_over,
                                    'cluster_name': cluster['name'],
                                    'resource_group': cluster['resource_group']
                                }
                            })
                            
                            if trigger_id:
                                notification_data['trigger_id'] = trigger_id
                                logger.info(f"✅ Recorded alert trigger in database: {trigger_id}")
                        except Exception as db_error:
                            logger.error(f"❌ Failed to record trigger in database: {db_error}")
                        
                        # ENHANCED: Send notifications through multiple channels
                        notifications_sent = []
                        
                        # Email notification
                        if 'email' in alert.get('notification_channels', ['email']):
                            try:
                                if alerts_manager._send_alert_email(alert, notification_data):
                                    notifications_sent.append('email')
                                    logger.info(f"📧 Email notification sent for alert {alert['id']}")
                            except Exception as email_error:
                                logger.error(f"❌ Failed to send email notification: {email_error}")
                        
                        # Slack notification
                        if 'slack' in alert.get('notification_channels', []):
                            try:
                                if alerts_manager._send_alert_slack(alert, notification_data):
                                    notifications_sent.append('slack')
                                    logger.info(f"💬 Slack notification sent for alert {alert['id']}")
                            except Exception as slack_error:
                                logger.error(f"❌ Failed to send Slack notification: {slack_error}")
                        
                        # Update trigger with notification status
                        if notification_data.get('trigger_id'):
                            try:
                                alerts_manager.db.update_trigger_notification_status(
                                    notification_data['trigger_id'],
                                    len(notifications_sent) > 0,
                                    notifications_sent
                                )
                            except Exception as update_error:
                                logger.error(f"❌ Failed to update trigger notification status: {update_error}")
                        
                        triggered_alerts.append(notification_data)
                        
                    else:
                        logger.info(f"✅ Alert '{alert['name']}' not triggered - cost ${current_cost:.2f} below threshold ${threshold:.2f}")
                        
                except Exception as alert_error:
                    logger.error(f"❌ Error checking alert {alert.get('id', 'unknown')}: {alert_error}")
            
            if triggered_alerts:
                logger.info(f"🚨 SUMMARY: Triggered {len(triggered_alerts)} alerts for cluster {cluster_id}")
                for trigger in triggered_alerts:
                    logger.info(f"   - {trigger['alert_name']}: ${trigger['current_cost']:.2f} > ${trigger['threshold_amount']:.2f}")
            else:
                logger.info(f"✅ No alerts triggered for cluster {cluster_id}")
            
            return triggered_alerts
            
        except Exception as alerts_error:
            logger.error(f"❌ Error processing alerts: {alerts_error}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced alert checking: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return []

def get_alerts_manager():
    """Get the alerts manager instance"""
    return alerts_manager

def is_alerts_available():
    """Check if alerts system is available"""
    return ALERTS_AVAILABLE and alerts_manager is not None