#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

# Enhanced alerts_integration.py - Complete API with frequency management and notification support

import os
import traceback
from datetime import datetime
from flask import jsonify, request
from shared.config.config import logger, enhanced_cluster_manager, ALERTS_AVAILABLE

# Global alerts manager
alerts_manager = None

def initialize_alerts_system():
    """Initialize alerts system with proper error handling"""
    global alerts_manager
    
    if not ALERTS_AVAILABLE:
        logger.warning("⚠️ Alerts system not available - skipping initialization")
        return None
    
    try:
        # Import from the correct location
        from alerts.enhanced_alerts_manager import (
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
    """Register enhanced alerts API routes with complete functionality"""
    
    @app.route('/api/alerts', methods=['GET', 'POST'])
    def alerts_api():
        """Main alerts endpoint with enhanced frequency handling"""
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
                            # Ensure frequency is never undefined
                            if not alert.get('notification_frequency'):
                                alert['notification_frequency'] = 'daily'
                                alert['frequency_display_name'] = 'Daily'
                            
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
                    # Get all alerts and ensure frequency is set
                    result = alerts_manager.get_alerts_route()
                    if result['status'] == 'success':
                        for alert in result['alerts']:
                            if not alert.get('notification_frequency'):
                                alert['notification_frequency'] = 'daily'
                                alert['frequency_display_name'] = 'Daily'
                    return jsonify(result)
            
            elif request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided'
                    }), 400
                
                # 🆕 ENHANCED FREQUENCY VALIDATION AND DEFAULTS
                frequency = data.get('notification_frequency', 'daily')
                valid_frequencies = ['immediate', 'hourly', 'daily', 'weekly', 'monthly', 'custom_4h']
                
                if frequency not in valid_frequencies:
                    frequency = 'daily'
                    logger.warning(f"Invalid frequency '{data.get('notification_frequency')}' provided, defaulting to 'daily'")
                
                data['notification_frequency'] = frequency
                
                # Set frequency-related defaults
                if 'frequency_at_time' not in data:
                    data['frequency_at_time'] = '09:00'
                
                if 'max_notifications_per_day' not in data:
                    data['max_notifications_per_day'] = 3 if frequency != 'immediate' else None
                
                if 'cooldown_period_hours' not in data:
                    cooldown_map = {
                        'immediate': 0,
                        'hourly': 1,
                        'daily': 4,
                        'weekly': 24,
                        'monthly': 168,
                        'custom_4h': 4
                    }
                    data['cooldown_period_hours'] = cooldown_map.get(frequency, 4)
                
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
                
                # Log frequency information
                if result['status'] == 'success':
                    logger.info(f"✅ Created alert with frequency '{frequency}': {result.get('alert_id')}")
                
                return jsonify(result), status_code
                
        except Exception as e:
            logger.error(f"❌ Error in alerts API: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
        
    @app.route('/api/alerts/<int:alert_id>', methods=['GET', 'PUT', 'DELETE'])
    def alert_detail_api(alert_id: int):
        """Individual alert management with frequency support"""
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
                            # Ensure frequency is never undefined
                            if not alert.get('notification_frequency'):
                                alert['notification_frequency'] = 'daily'
                                alert['frequency_display_name'] = 'Daily'
                            
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
                    
                    # 🆕 VALIDATE FREQUENCY UPDATES
                    if 'notification_frequency' in data:
                        frequency = data['notification_frequency']
                        valid_frequencies = ['immediate', 'hourly', 'daily', 'weekly', 'monthly', 'custom_4h']
                        
                        if frequency not in valid_frequencies:
                            return jsonify({
                                'status': 'error',
                                'message': f'Invalid frequency. Must be one of: {", ".join(valid_frequencies)}'
                            }), 400
                    
                    # Set updated timestamp
                    data['updated_at'] = datetime.now().isoformat()
                    
                    result = alerts_manager.update_alert_route(alert_id, data)
                    
                    if result['status'] == 'success':
                        # Log frequency changes
                        if 'notification_frequency' in data:
                            logger.info(f"📅 Updated alert {alert_id} frequency to '{data['notification_frequency']}'")
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

    # 🆕 FREQUENCY MANAGEMENT ENDPOINTS
    @app.route('/api/alerts/frequency-configs', methods=['GET'])
    def frequency_configurations_api():
        """🆕 Get available notification frequency configurations"""
        try:
            if not alerts_manager or not alerts_manager.db:
                # Return default configurations if database not available
                default_configs = [
                    {
                        'frequency_type': 'immediate',
                        'display_name': 'Immediate',
                        'description': 'Send notification as soon as alert is triggered',
                        'interval_value': 0,
                        'interval_unit': 'minutes',
                        'max_per_day': None,
                        'cooldown_hours': 0,
                        'recommended_for': 'Critical alerts, Budget overruns'
                    },
                    {
                        'frequency_type': 'hourly',
                        'display_name': 'Hourly',
                        'description': 'Send notifications once per hour when triggered',
                        'interval_value': 1,
                        'interval_unit': 'hours',
                        'max_per_day': 24,
                        'cooldown_hours': 1,
                        'recommended_for': 'High-frequency monitoring'
                    },
                    {
                        'frequency_type': 'daily',
                        'display_name': 'Daily',
                        'description': 'Send one notification per day at 9:00 AM',
                        'interval_value': 1,
                        'interval_unit': 'days',
                        'max_per_day': 1,
                        'cooldown_hours': 24,
                        'recommended_for': 'Regular cost monitoring, Budget alerts'
                    },
                    {
                        'frequency_type': 'weekly',
                        'display_name': 'Weekly',
                        'description': 'Send notifications once per week on Mondays',
                        'interval_value': 7,
                        'interval_unit': 'days',
                        'max_per_day': 1,
                        'cooldown_hours': 168,
                        'recommended_for': 'Summary reports, Weekly cost reviews'
                    },
                    {
                        'frequency_type': 'monthly',
                        'display_name': 'Monthly',
                        'description': 'Send notifications once per month on the 1st',
                        'interval_value': 30,
                        'interval_unit': 'days',
                        'max_per_day': 1,
                        'cooldown_hours': 720,
                        'recommended_for': 'Monthly budget reviews, Long-term trends'
                    },
                    {
                        'frequency_type': 'custom_4h',
                        'display_name': 'Every 4 Hours',
                        'description': 'Send notifications every 4 hours during business hours',
                        'interval_value': 4,
                        'interval_unit': 'hours',
                        'max_per_day': 6,
                        'cooldown_hours': 4,
                        'recommended_for': 'Active monitoring, Development environments'
                    }
                ]
                
                return jsonify({
                    'status': 'success',
                    'configurations': default_configs,
                    'source': 'default'
                })
            
            # Get configurations from database
            configs = alerts_manager.db.get_frequency_configurations()
            
            return jsonify({
                'status': 'success',
                'configurations': configs,
                'source': 'database',
                'count': len(configs)
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting frequency configurations: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/frequency-preview', methods=['POST'])
    def frequency_preview_api():
        """🆕 Preview frequency settings and next notification times"""
        try:
            data = request.get_json() or {}
            frequency = data.get('frequency', 'daily')
            frequency_at_time = data.get('frequency_at_time', '09:00')
            max_notifications_per_day = data.get('max_notifications_per_day')
            cooldown_period_hours = data.get('cooldown_period_hours', 4)
            
            # Create a mock alert for preview
            mock_alert = {
                'notification_frequency': frequency,
                'frequency_at_time': frequency_at_time,
                'max_notifications_per_day': max_notifications_per_day,
                'cooldown_period_hours': cooldown_period_hours,
                'last_notification_sent': None
            }
            
            # Calculate next notification time
            next_notification = None
            if alerts_manager and alerts_manager.db:
                next_notification = alerts_manager.db._calculate_next_notification_time(mock_alert)
            
            # Generate preview text
            preview_parts = []
            
            if frequency == 'immediate':
                preview_parts.append("Notifications will be sent immediately when alerts are triggered")
            elif frequency == 'daily':
                preview_parts.append(f"Notifications will be sent daily at {frequency_at_time}")
            elif frequency == 'hourly':
                preview_parts.append("Notifications will be sent once per hour when triggered")
            elif frequency == 'weekly':
                preview_parts.append(f"Notifications will be sent weekly on Mondays at {frequency_at_time}")
            elif frequency == 'monthly':
                preview_parts.append(f"Notifications will be sent monthly on the 1st at {frequency_at_time}")
            elif frequency == 'custom_4h':
                preview_parts.append("Notifications will be sent every 4 hours during active monitoring")
            
            if max_notifications_per_day:
                preview_parts.append(f"Maximum {max_notifications_per_day} notifications per day")
            
            if cooldown_period_hours > 0:
                preview_parts.append(f"Minimum {cooldown_period_hours} hour(s) between notifications")
            
            return jsonify({
                'status': 'success',
                'preview_text': '. '.join(preview_parts),
                'next_notification_time': next_notification,
                'frequency_info': {
                    'type': frequency,
                    'display_name': frequency.replace('_', ' ').title(),
                    'will_repeat': frequency != 'immediate'
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Error generating frequency preview: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/alerts/validate-frequency', methods=['POST'])
    def validate_frequency_settings():
        """🆕 Validate frequency settings"""
        try:
            data = request.get_json() or {}
            
            errors = []
            warnings = []
            
            frequency = data.get('frequency')
            if not frequency:
                errors.append("Frequency is required")
            elif frequency not in ['immediate', 'hourly', 'daily', 'weekly', 'monthly', 'custom_4h']:
                errors.append("Invalid frequency type")
            
            max_per_day = data.get('max_notifications_per_day')
            if max_per_day is not None:
                try:
                    max_per_day = int(max_per_day)
                    if max_per_day < 1:
                        errors.append("Max notifications per day must be at least 1")
                    elif max_per_day > 24:
                        warnings.append("More than 24 notifications per day may be excessive")
                except ValueError:
                    errors.append("Max notifications per day must be a number")
            
            cooldown_hours = data.get('cooldown_period_hours')
            if cooldown_hours is not None:
                try:
                    cooldown_hours = int(cooldown_hours)
                    if cooldown_hours < 0:
                        errors.append("Cooldown period cannot be negative")
                    elif cooldown_hours > 168:  # 1 week
                        warnings.append("Cooldown period longer than 1 week may delay important alerts")
                except ValueError:
                    errors.append("Cooldown period must be a number")
            
            frequency_at_time = data.get('frequency_at_time')
            if frequency_at_time:
                try:
                    hour, minute = map(int, frequency_at_time.split(':'))
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        errors.append("Invalid time format")
                except (ValueError, AttributeError):
                    errors.append("Time must be in HH:MM format")
            
            # Cross-validation
            if frequency == 'immediate' and cooldown_hours and cooldown_hours > 1:
                warnings.append("Cooldown period may conflict with immediate notifications")
            
            if frequency == 'daily' and max_per_day and max_per_day > 1:
                warnings.append("Daily frequency with multiple notifications per day may be confusing")
            
            is_valid = len(errors) == 0
            
            return jsonify({
                'status': 'success',
                'valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'recommendations': generate_frequency_recommendations(frequency, max_per_day, cooldown_hours)
            })
            
        except Exception as e:
            logger.error(f"❌ Error validating frequency settings: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    def generate_frequency_recommendations(frequency, max_per_day, cooldown_hours):
        """Generate recommendations based on frequency settings"""
        recommendations = []
        
        if frequency == 'immediate':
            recommendations.append("Consider setting a cooldown period to prevent spam")
            recommendations.append("Immediate alerts are best for critical cost thresholds")
        elif frequency == 'daily':
            recommendations.append("Daily alerts are good for regular budget monitoring")
            recommendations.append("Consider setting the time to your business hours")
        elif frequency == 'hourly':
            recommendations.append("Hourly alerts are suitable for active development environments")
            recommendations.append("Consider limiting to business hours only")
        elif frequency == 'weekly':
            recommendations.append("Weekly alerts are ideal for summary reports")
            recommendations.append("Consider combining with monthly budget reviews")
        elif frequency == 'monthly':
            recommendations.append("Monthly alerts are perfect for budget review cycles")
            recommendations.append("Consider supplementing with more frequent monitoring")
        
        if not max_per_day:
            recommendations.append("Consider setting a daily limit to prevent notification overload")
        
        if not cooldown_hours or cooldown_hours == 0:
            recommendations.append("Adding a cooldown period can help reduce duplicate notifications")
        
        return recommendations

    # 🆕 INDIVIDUAL NOTIFICATION MANAGEMENT ENDPOINTS
    @app.route('/api/notifications/<notification_id>/mark-read', methods=['POST'])
    def mark_notification_read_api(notification_id: str):
        """Mark individual notification as read"""
        try:
            if not alerts_manager or not alerts_manager.db:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            # Update single notification
            success = alerts_manager.db.update_notification_status([notification_id], 'mark_read')
            
            if success:
                logger.info(f"📖 Marked notification {notification_id} as read")
                return jsonify({
                    'status': 'success',
                    'message': 'Notification marked as read'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to mark notification as read'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error marking notification as read: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/notifications/<notification_id>/dismiss', methods=['POST'])
    def dismiss_notification_api(notification_id: str):
        """Dismiss individual notification"""
        try:
            if not alerts_manager or not alerts_manager.db:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            # Update single notification
            success = alerts_manager.db.update_notification_status([notification_id], 'dismiss')
            
            if success:
                logger.info(f"🗑️ Dismissed notification {notification_id}")
                return jsonify({
                    'status': 'success',
                    'message': 'Notification dismissed'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to dismiss notification'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error dismissing notification: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # 🆕 BULK NOTIFICATION MANAGEMENT ENDPOINT
    @app.route('/api/notifications/mark-all-read', methods=['POST'])
    def mark_all_notifications_read_api():
        """Mark all notifications as read"""
        try:
            if not alerts_manager or not alerts_manager.db:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            data = request.get_json() or {}
            cluster_id = data.get('cluster_id')
            
            # Get all unread notifications for the cluster
            unread_notifications = alerts_manager.db.get_in_app_notifications(
                cluster_id=cluster_id,
                unread_only=True,
                limit=1000  # Large limit to get all
            )
            
            if not unread_notifications:
                return jsonify({
                    'status': 'success',
                    'message': 'No unread notifications to mark',
                    'updated_count': 0
                })
            
            # Get notification IDs
            notification_ids = [str(notif['id']) for notif in unread_notifications]
            
            # Mark all as read
            success = alerts_manager.db.update_notification_status(notification_ids, 'mark_read')
            
            if success:
                logger.info(f"📖 Marked {len(notification_ids)} notifications as read")
                return jsonify({
                    'status': 'success',
                    'message': f'Marked {len(notification_ids)} notifications as read',
                    'updated_count': len(notification_ids)
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to mark notifications as read'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error marking all notifications as read: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/notifications/in-app', methods=['GET', 'POST', 'PUT'])
    def in_app_notifications_api():
        """Enhanced in-app notifications management"""
        try:
            if request.method == 'GET':
                unread_only = request.args.get('unread_only', 'false').lower() == 'true'
                limit = int(request.args.get('limit', 50))
                cluster_id = request.args.get('cluster_id')
                
                # Get notifications from database via alerts manager
                if alerts_manager and alerts_manager.db:
                    notifications = alerts_manager.db.get_in_app_notifications(
                        cluster_id=cluster_id,
                        unread_only=unread_only,
                        limit=limit
                    )
                    unread_count = alerts_manager.db.get_unread_notifications_count(cluster_id)
                    
                    return jsonify({
                        'status': 'success',
                        'notifications': notifications,
                        'unread_count': unread_count,
                        'total_count': len(notifications),
                        'limit': limit,
                        'unread_only': unread_only
                    })
                else:
                    # Fallback for when alerts manager is not available
                    return jsonify({
                        'status': 'success',
                        'notifications': [],
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
                
                # Create notification in database
                notification_id = None
                if alerts_manager and alerts_manager.db:
                    notification_data = {
                        'title': data['title'],
                        'message': data['message'],
                        'type': data.get('type', 'info'),
                        'cluster_id': data.get('cluster_id'),
                        'alert_id': data.get('alert_id'),
                        'trigger_id': data.get('trigger_id'),
                        'timestamp': datetime.now().isoformat(),
                        'read': False,
                        'dismissed': False,
                        'metadata': data.get('metadata', {})
                    }
                    notification_id = alerts_manager.db.create_in_app_notification(notification_data)
                
                if notification_id:
                    logger.info(f"📱 In-app notification created: {notification_id}")
                    return jsonify({
                        'status': 'success',
                        'message': 'Notification created successfully',
                        'notification_id': notification_id
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to create notification'
                    }), 500
            
            elif request.method == 'PUT':
                data = request.get_json() or {}
                notification_ids = data.get('notification_ids', [])
                action = data.get('action', 'mark_read')
                
                if not notification_ids:
                    return jsonify({
                        'status': 'error',
                        'message': 'notification_ids required'
                    }), 400
                
                # Update notifications in database
                success = False
                if alerts_manager and alerts_manager.db:
                    success = alerts_manager.db.update_notification_status(notification_ids, action)
                
                if success:
                    logger.info(f"📱 Updated {len(notification_ids)} notifications: {action}")
                    return jsonify({
                        'status': 'success',
                        'message': f'Successfully {action} {len(notification_ids)} notifications',
                        'updated_count': len(notification_ids)
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to update notifications'
                    }), 500
                    
        except Exception as e:
            logger.error(f"❌ Error in in-app notifications API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # 🆕 ALERT MANAGEMENT & DEBUGGING ENDPOINTS
    @app.route('/api/alerts/check-and-notify', methods=['POST'])
    def check_and_notify_alerts_api():
        """Manual alert checking and notification triggering"""
        try:
            if not alerts_manager:
                return jsonify({
                    'status': 'error',
                    'message': 'Alerts system not available'
                }), 503
            
            data = request.get_json() or {}
            cluster_id = data.get('cluster_id')
            
            if not cluster_id:
                return jsonify({
                    'status': 'error',
                    'message': 'cluster_id required'
                }), 400
            
            # Get cluster info
            cluster = enhanced_cluster_manager.get_cluster(cluster_id) if enhanced_cluster_manager else None
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Get current cost - try multiple sources
            current_cost = data.get('current_cost')
            if not current_cost:
                # Try to get from cluster manager or analysis results
                try:
                    from shared import _get_analysis_data
                    analysis_data, data_source = _get_analysis_data(cluster_id)
                    if analysis_data:
                        current_cost = analysis_data.get('total_cost', 0)
                        logger.info(f"💰 Retrieved current cost from {data_source}: ${current_cost}")
                except Exception as cost_error:
                    logger.warning(f"⚠️ Could not retrieve current cost: {cost_error}")
                    current_cost = 0
            
            if not current_cost or current_cost <= 0:
                return jsonify({
                    'status': 'error',
                    'message': 'No current cost data available for alert checking'
                }), 400
            
            logger.info(f"🔍 Manual alert check for cluster {cluster_id} with cost ${current_cost}")
            
            # Check alerts
            triggered_alerts = alerts_manager.check_cluster_alerts(cluster_id, current_cost)
            
            return jsonify({
                'status': 'success',
                'message': f'Alert check completed for cluster {cluster_id}',
                'cluster_id': cluster_id,
                'current_cost': current_cost,
                'triggered_alerts_count': len(triggered_alerts),
                'triggered_alerts': [
                    {
                        'alert_id': ta['alert']['id'],
                        'alert_name': ta['alert']['name'],
                        'threshold_amount': ta['alert']['threshold_amount'],
                        'exceeded_by': ta['threshold_exceeded_by'],
                        'notifications_sent': ta.get('notifications_sent', [])
                    } for ta in triggered_alerts
                ]
            })
            
        except Exception as e:
            logger.error(f"❌ Error in manual alert check: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/cluster-costs', methods=['GET'])
    def cluster_costs_api():
        """Get current cluster costs for debugging"""
        try:
            cluster_id = request.args.get('cluster_id')
            
            if not cluster_id:
                return jsonify({
                    'status': 'error',
                    'message': 'cluster_id required'
                }), 400
            
            # Get cluster info
            cluster = enhanced_cluster_manager.get_cluster(cluster_id) if enhanced_cluster_manager else None
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Get current analysis data
            try:
                from shared import _get_analysis_data
                analysis_data, data_source = _get_analysis_data(cluster_id)
                
                if analysis_data:
                    current_cost = analysis_data.get('total_cost', 0)
                    return jsonify({
                        'status': 'success',
                        'cluster_id': cluster_id,
                        'cluster_name': cluster.get('name'),
                        'current_cost': current_cost,
                        'data_source': data_source,
                        'last_updated': analysis_data.get('timestamp', 'Unknown'),
                        'has_cost_data': current_cost > 0
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'No cost data available for this cluster',
                        'cluster_id': cluster_id,
                        'cluster_name': cluster.get('name'),
                        'current_cost': 0,
                        'data_source': 'none',
                        'has_cost_data': False
                    })
                    
            except Exception as cost_error:
                logger.error(f"❌ Error getting cluster costs: {cost_error}")
                return jsonify({
                    'status': 'error',
                    'message': f'Error retrieving cost data: {str(cost_error)}'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error in cluster costs API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # 🆕 SYSTEM MANAGEMENT ENDPOINTS
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

    # 🆕 TESTING & NOTIFICATION ENDPOINTS
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

    @app.route('/api/alerts/health', methods=['GET'])
    def alerts_health_check():
        """Enhanced health check endpoint with complete functionality info"""
        try:
            health_status = {
                'alerts_available': ALERTS_AVAILABLE,
                'alerts_manager_initialized': alerts_manager is not None,
                'enhanced_alerts_available': True,
                'frequency_management_available': True,
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
                'frequency_features': {
                    'custom_frequencies': True,
                    'cooldown_periods': True,
                    'daily_limits': True,
                    'scheduled_times': True,
                    'preview_available': True
                },
                'notification_features': {
                    'individual_management': True,
                    'bulk_operations': True,
                    'mark_read': True,
                    'dismiss': True
                },
                'debugging_features': {
                    'manual_alert_check': True,
                    'cluster_costs': True,
                    'test_triggers': True,
                    'statistics': True
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

    logger.info("✅ Complete alerts routes registered successfully")

    def check_alerts_after_analysis(cluster_id: str, analysis_results: dict):
        """Enhanced alert checking with complete notification support"""
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
            
            # Extract current cost
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
            
            if current_cost <= 0:
                logger.warning(f"⚠️ No valid cost data found for cluster {cluster_id}")
                return []
            
            logger.info(f"🔍 Checking alerts for cluster {cluster_id} with cost ${current_cost:.2f}")
            
            # Use the enhanced check_cluster_alerts method
            triggered_alerts = alerts_manager.check_cluster_alerts(cluster_id, current_cost)
            
            if triggered_alerts:
                logger.info(f"🚨 SUMMARY: Triggered {len(triggered_alerts)} alerts for cluster {cluster_id}")
                for triggered_alert in triggered_alerts:
                    alert = triggered_alert['alert']
                    logger.info(f"   - {alert['name']}: ${triggered_alert['current_cost']:.2f} > ${alert['threshold_amount']:.2f}")
                    logger.info(f"   - Notifications sent via: {alert.get('notification_channels', [])}")
            else:
                logger.info(f"✅ No alerts triggered for cluster {cluster_id}")
            
            return triggered_alerts
            
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