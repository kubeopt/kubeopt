#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

# enhanced_alerts_manager.py - Complete Enhanced Alerts Manager with Database Backend

import os
import json
import traceback
from flask import request
import requests
import smtplib
from email.mime.text import MIMEText  #  Capital letters
from email.mime.multipart import MIMEMultipart  #  Capital letters
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import the alerts database
from infrastructure.persistence.alerts_database import alerts_db
from shared.standards.implementation_cost_calculator import implementation_cost_calculator

logger = logging.getLogger(__name__)

class EnhancedAlertsManager:
    """Complete alerts manager with database backend and multi-channel notifications using standards"""
    
    def __init__(self, cluster_manager=None):
        self.cluster_manager = cluster_manager
        self.db = alerts_db
        self.logger = logging.getLogger(__name__)
        
        # Load standards for configuration
        self.standards = implementation_cost_calculator.load_standards()
        monitoring_config = self.standards.get('monitoring_alerting', {})
        notification_config = monitoring_config.get('notifications', {})
        
        # Settings manager for both email and Slack configuration
        from infrastructure.services.settings_manager import settings_manager
        self.settings_manager = settings_manager
        
        # Email configuration - get from settings manager
        self.smtp_server = self.settings_manager.get_setting('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(self.settings_manager.get_setting('SMTP_PORT', '587'))
        self.smtp_username = self.settings_manager.get_setting('SMTP_USERNAME', '')
        self.smtp_password = self.settings_manager.get_setting('SMTP_PASSWORD', '')
        self.from_email = self.settings_manager.get_setting('FROM_EMAIL', self.smtp_username or self.smtp_username)
        
        # Slack configuration - get from settings manager
        self.slack_webhook_url = self.settings_manager.get_setting('SLACK_WEBHOOK_URL', '')
        
        # Load notification settings from standards
        self.notification_retry_attempts = notification_config.get('retry_attempts', 3)
        self.notification_timeout = notification_config.get('timeout_seconds', 10)
        self.default_channels = notification_config.get('default_channels', ['email', 'inapp'])
        
        self.logger.info("✅ Enhanced alerts manager initialized with standards")

    def get_alerts_route(self, cluster_id: Optional[str] = None) -> Dict:
        """Get all alerts (API route handler)"""
        try:
            if cluster_id:
                alerts = self.db.get_alerts(cluster_id=cluster_id)
            else:
                alerts = self.db.get_alerts()
            
            return {
                'status': 'success',
                'alerts': alerts,
                'total_alerts': len(alerts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting alerts: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'alerts': []
            }

    def create_alert_route(self, alert_data: Dict) -> Dict:
        """Create new alert (API route handler)"""
        try:
            # Validate required fields based on alert type
            alert_type = alert_data.get('alert_type', 'cost_threshold')
            
            if alert_type == 'cpu_monitoring':
                required_fields = ['name', 'cluster_id', 'threshold_amount']
            else:
                required_fields = ['name', 'cluster_id', 'cluster_name', 'resource_group', 'threshold_amount']
            
            missing_fields = [field for field in required_fields if field not in alert_data]
            
            if missing_fields:
                return {
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }
            
            # Get cluster info if cluster_manager is available
            if self.cluster_manager:
                cluster = self.cluster_manager.get_cluster(alert_data['cluster_id'])
                if cluster:
                    alert_data['subscription_id'] = cluster.get('subscription_id')
                    alert_data['subscription_name'] = cluster.get('subscription_name')
            
            # Set defaults using standards
            alert_data.setdefault('status', 'active')
            alert_data.setdefault('alert_type', 'cost_threshold')
            alert_data.setdefault('threshold_type', 'monthly')
            alert_data.setdefault('notification_channels', self.default_channels)
            alert_data.setdefault('created_by', 'user')
            
            alert_id = self.db.create_alert(alert_data)
            
            return {
                'status': 'success',
                'message': 'Alert created successfully',
                'alert_id': alert_id,
                'alert': self.db.get_alert(alert_id)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error creating alert: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def update_alert_route(self, alert_id: int, updates: Dict) -> Dict:
        """Update alert (API route handler)"""
        try:
            # Check if alert exists
            existing_alert = self.db.get_alert(alert_id)
            if not existing_alert:
                return {
                    'status': 'error',
                    'message': 'Alert not found'
                }
            
            # Update the alert
            success = self.db.update_alert(alert_id, updates)
            
            if success:
                updated_alert = self.db.get_alert(alert_id)
                return {
                    'status': 'success',
                    'message': 'Alert updated successfully',
                    'alert': updated_alert
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to update alert'
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error updating alert {alert_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def delete_alert_route(self, alert_id: int) -> Dict:
        """Delete alert (API route handler)"""
        try:
            # Check if alert exists
            existing_alert = self.db.get_alert(alert_id)
            if not existing_alert:
                return {
                    'status': 'error',
                    'message': 'Alert not found'
                }
            
            # Delete the alert
            success = self.db.delete_alert(alert_id)
            
            if success:
                return {
                    'status': 'success',
                    'message': 'Alert deleted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to delete alert'
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting alert {alert_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def test_alert_route(self, alert_id: int) -> Dict:
        """Test alert notifications (API route handler)"""
        try:
            # Get alert details
            alert = self.db.get_alert(alert_id)
            if not alert:
                return {
                    'status': 'error',
                    'message': 'Alert not found'
                }
            
            # Test email notification
            email_sent = False
            if 'email' in alert['notification_channels']:
                email_sent = self._send_test_email(alert)
            
            # Test Slack notification
            slack_sent = False
            slack_enabled = self.settings_manager.get_setting('SLACK_ENABLED', 'false').lower() == 'true'
            if 'slack' in alert['notification_channels'] and self.slack_webhook_url and slack_enabled:
                slack_sent = self._send_test_slack(alert)
            
            # 🆕 TEST IN-APP NOTIFICATION
            inapp_sent = False
            if ('inapp' in alert['notification_channels'] or 
                'in_app' in alert['notification_channels'] or 
                'in-app' in alert['notification_channels']):
                inapp_sent = self._send_test_in_app_notification(alert)
            
            channels_tested = []
            if email_sent:
                channels_tested.append('email')
            if slack_sent:
                channels_tested.append('slack')
            if inapp_sent:
                channels_tested.append('in_app')
            
            if channels_tested:
                return {
                    'status': 'success',
                    'message': f'Test notifications sent via: {", ".join(channels_tested)}',
                    'channels_tested': channels_tested
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'No notifications could be sent (check configuration)',
                    'channels_tested': []
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error testing alert {alert_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_alert_triggers_route(self, alert_id: Optional[int] = None) -> Dict:
        """Get alert triggers (API route handler)"""
        try:
            triggers = self.db.get_triggers(alert_id=alert_id)
            
            return {
                'status': 'success',
                'triggers': triggers,
                'total_triggers': len(triggers),
                'alert_id': alert_id
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting alert triggers: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'triggers': []
            }

    def get_alert_statistics_route(self) -> Dict:
        """Get alert statistics (API route handler)"""
        try:
            stats = self.db.get_alert_statistics()
            
            # Add configuration status
            stats['configuration'] = {
                'email_configured': bool(self.smtp_username and self.smtp_password),
                'slack_configured': bool(self.slack_webhook_url),
                'cluster_manager_available': self.cluster_manager is not None
            }
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting alert statistics: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def check_cluster_alerts(self, cluster_id: str, current_cost: float) -> List[Dict]:
        """🆕 ENHANCED: Check and trigger alerts for a cluster with proper in-app notifications"""
        try:
            self.logger.info(f"🔍 Enhanced alert checking for cluster {cluster_id} with cost ${current_cost:.2f}")
            
            # Get active alerts for this cluster using the database
            alerts = self.db.get_alerts(cluster_id=cluster_id, status='active')
            
            if not alerts:
                self.logger.info(f"ℹ️ No active alerts found for cluster {cluster_id}")
                return []
            
            self.logger.info(f"🔍 Found {len(alerts)} active alerts to check for cluster {cluster_id}")
            
            triggered_alerts = []
            
            for alert in alerts:
                threshold = alert['threshold_amount']
                self.logger.info(f"🔍 Checking alert '{alert['name']}': ${current_cost:.2f} vs ${threshold:.2f}")
                
                if current_cost >= threshold:
                    exceeded_by = current_cost - threshold
                    
                    self.logger.info(f"🚨 ALERT TRIGGERED: '{alert['name']}' - Cost ${current_cost:.2f} exceeds ${threshold:.2f} by ${exceeded_by:.2f}")
                    
                    # Record the trigger in database
                    trigger_data = {
                        'alert_id': alert['id'],
                        'cluster_id': cluster_id,
                        'trigger_reason': f"Cost ${current_cost:.2f} exceeded threshold ${threshold:.2f}",
                        'current_cost': current_cost,
                        'threshold_amount': threshold,
                        'threshold_exceeded_by': exceeded_by,
                        'notification_sent': False,
                        'notification_channels': alert['notification_channels'],
                        'metadata': {
                            'alert_name': alert['name'],
                            'alert_type': alert['alert_type'],
                            'percentage_over': (exceeded_by / threshold) * 100 if threshold > 0 else 0
                        }
                    }
                    
                    trigger_id = self.db.record_alert_trigger(trigger_data)
                    
                    if trigger_id:
                        triggered_alert = {
                            'alert': alert,
                            'trigger_id': trigger_id,
                            'current_cost': current_cost,
                            'threshold_exceeded_by': exceeded_by
                        }
                        
                        # Send notifications through ALL configured channels
                        notifications_sent = []
                        
                        # Email notification
                        if 'email' in alert['notification_channels']:
                            if self._send_alert_email(alert, triggered_alert):
                                notifications_sent.append('email')
                                self.logger.info(f"✅ Email notification sent for alert {alert['id']}")
                            else:
                                self.logger.warning(f"⚠️ Email notification failed for alert {alert['id']}")
                        
                        # Slack notification
                        slack_enabled = self.settings_manager.get_setting('SLACK_ENABLED', 'false').lower() == 'true'
                        if 'slack' in alert['notification_channels'] and self.slack_webhook_url and slack_enabled:
                            if self._send_alert_slack(alert, triggered_alert):
                                notifications_sent.append('slack')
                                self.logger.info(f"✅ Slack notification sent for alert {alert['id']}")
                            else:
                                self.logger.warning(f"⚠️ Slack notification failed for alert {alert['id']}")
                        elif 'slack' in alert['notification_channels'] and not slack_enabled:
                            self.logger.warning(f"⚠️ Slack notification skipped for alert {alert['id']} - Slack is disabled")
                        elif 'slack' in alert['notification_channels'] and not self.slack_webhook_url:
                            self.logger.warning(f"⚠️ Slack notification skipped for alert {alert['id']} - No webhook URL configured")
                        
                        # 🆕 IN-APP NOTIFICATION - THE KEY FIX!
                        if ('inapp' in alert['notification_channels'] or 
                            'in_app' in alert['notification_channels'] or 
                            'in-app' in alert['notification_channels']):
                            if self._send_alert_in_app(alert, triggered_alert):
                                notifications_sent.append('in_app')
                                self.logger.info(f"✅ In-app notification sent for alert {alert['id']}")
                            else:
                                self.logger.warning(f"⚠️ In-app notification failed for alert {alert['id']}")
                        
                        # Update trigger with notification status
                        self.db.update_trigger_notification_status(
                            trigger_id, 
                            len(notifications_sent) > 0,
                            notifications_sent
                        )
                        
                        # Update alert's last notification sent time
                        if notifications_sent:
                            self.db.update_notification_sent_time(alert['id'])
                        
                        triggered_alert['notifications_sent'] = notifications_sent
                        triggered_alerts.append(triggered_alert)
                        
                        self.logger.info(f"🚨 Alert '{alert['name']}' processed: notifications sent via {', '.join(notifications_sent) if notifications_sent else 'NONE'}")
                    else:
                        self.logger.error(f"❌ Failed to record trigger for alert {alert['id']}")
                else:
                    self.logger.info(f"✅ Alert '{alert['name']}' not triggered: ${current_cost:.2f} < ${threshold:.2f}")
            
            if triggered_alerts:
                self.logger.info(f"🚨 SUMMARY: {len(triggered_alerts)} alerts triggered for cluster {cluster_id}")
            else:
                self.logger.info(f"✅ No alerts triggered for cluster {cluster_id}")
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"❌ Error checking cluster alerts: {e}")
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []

    def check_cpu_monitoring_alerts(self, cluster_id: str, cpu_metrics: Dict) -> List[Dict]:
        """Check and trigger CPU monitoring alerts"""
        try:
            self.logger.info(f"🔍 CPU monitoring check for cluster {cluster_id}")
            
            # Get active CPU monitoring alerts for this cluster
            alerts = self.db.get_alerts(cluster_id=cluster_id, status='active')
            cpu_alerts = [alert for alert in alerts if alert.get('alert_type') == 'cpu_monitoring']
            
            if not cpu_alerts:
                self.logger.info(f"ℹ️ No active CPU monitoring alerts for cluster {cluster_id}")
                return []
            
            self.logger.info(f"🔍 Found {len(cpu_alerts)} CPU monitoring alerts to check")
            
            triggered_alerts = []
            
            for alert in cpu_alerts:
                alert_metadata = alert.get('metadata', {})
                thresholds = alert_metadata.get('thresholds', {})
                conditions = alert_metadata.get('alert_conditions', {})
                
                cpu_triggers = []
                
                # Check high CPU usage using standards
                if conditions.get('high_cpu_usage', False):
                    avg_cpu = cpu_metrics.get('average_cpu_utilization', 0)
                    cpu_monitoring = self.standards.get('monitoring_alerting', {}).get('cpu_monitoring', {})
                    warning_threshold = thresholds.get('cpu_warning', cpu_monitoring.get('warning_threshold', 75))
                    critical_threshold = thresholds.get('cpu_critical', cpu_monitoring.get('critical_threshold', 90))
                    
                    if avg_cpu >= critical_threshold:
                        cpu_triggers.append({
                            'type': 'critical',
                            'reason': f"Average CPU {avg_cpu:.1f}% exceeds critical threshold {critical_threshold}%",
                            'severity': 'critical'
                        })
                    elif avg_cpu >= warning_threshold:
                        cpu_triggers.append({
                            'type': 'warning', 
                            'reason': f"Average CPU {avg_cpu:.1f}% exceeds warning threshold {warning_threshold}%",
                            'severity': 'warning'
                        })
                
                # Check low efficiency using standards
                if conditions.get('low_efficiency', False):
                    efficiency = cpu_metrics.get('cpu_efficiency', 0)
                    cpu_monitoring = self.standards.get('monitoring_alerting', {}).get('cpu_monitoring', {})
                    min_efficiency = thresholds.get('efficiency_minimum', cpu_monitoring.get('efficiency_minimum', 40))
                    
                    if efficiency < min_efficiency:
                        cpu_triggers.append({
                            'type': 'efficiency',
                            'reason': f"CPU efficiency {efficiency:.1f}% below minimum {min_efficiency}%",
                            'severity': 'warning'
                        })
                
                # If any triggers, create notification
                if cpu_triggers:
                    for trigger in cpu_triggers:
                        trigger_data = {
                            'alert_id': alert['id'],
                            'cluster_id': cluster_id,
                            'trigger_reason': trigger['reason'],
                            'trigger_type': trigger['type'],
                            'severity': trigger['severity'],
                            'current_metrics': cpu_metrics,
                            'thresholds': thresholds
                        }
                        
                        trigger_id = self.db.create_alert_trigger(trigger_data)
                        
                        if trigger_id:
                            # Send notifications
                            notifications_sent = []
                            channels = alert.get('notification_channels', ['inapp'])
                            
                            for channel in channels:
                                if channel == 'inapp':
                                    if self._send_cpu_alert_in_app(alert, trigger_data):
                                        notifications_sent.append('inapp')
                                elif channel == 'email':
                                    if self._send_cpu_alert_email(alert, trigger_data):
                                        notifications_sent.append('email')
                            
                            triggered_alerts.append({
                                'alert_id': alert['id'],
                                'trigger_id': trigger_id,
                                'notifications_sent': notifications_sent,
                                'trigger_type': trigger['type']
                            })
                            
                            self.logger.info(f"🚨 CPU Alert triggered: {trigger['reason']}")
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"❌ Error checking CPU monitoring alerts: {e}")
            return []

    def _send_alert_in_app(self, alert: Dict, triggered_alert: Dict) -> bool:
        """🆕 ENHANCED: Send in-app notification with proper error handling"""
        try:
            current_cost = triggered_alert['current_cost']
            exceeded_by = triggered_alert['threshold_exceeded_by']
            trigger_id = triggered_alert.get('trigger_id')
            
            self.logger.info(f"📱 Creating in-app notification for alert {alert['id']} (trigger {trigger_id})")
            
            # Create in-app notification using the database method
            notification_id = self.db.create_notification_for_trigger(
                trigger_id=trigger_id,
                alert=alert,
                current_cost=current_cost,
                exceeded_by=exceeded_by
            )
            
            if notification_id:
                self.logger.info(f"📱 ✅ In-app notification created successfully: {notification_id}")
                return True
            else:
                self.logger.error(f"📱 ❌ Failed to create in-app notification for alert {alert['id']}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error creating in-app notification for alert {alert['id']}: {e}")
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def _send_test_in_app_notification(self, alert: Dict) -> bool:
        """🆕 Send test in-app notification"""
        try:
            test_notification_data = {
                'title': f"🧪 Test Alert: {alert['name']}",
                'message': f"This is a test notification for alert '{alert['name']}' on cluster {alert['cluster_name']}. Threshold: ${alert['threshold_amount']:,.2f}",
                'type': 'info',
                'cluster_id': alert['cluster_id'],
                'alert_id': alert['id'],
                'trigger_id': None,  # No trigger for test
                'timestamp': datetime.now().isoformat(),
                'read': False,
                'dismissed': False,
                'metadata': {
                    'test_notification': True,
                    'alert_name': alert['name'],
                    'threshold_amount': alert['threshold_amount']
                }
            }
            
            notification_id = self.db.create_in_app_notification(test_notification_data)
            
            if notification_id:
                self.logger.info(f"📱 Test in-app notification created: {notification_id}")
                return True
            else:
                self.logger.error(f"📱 Failed to create test in-app notification")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending test in-app notification: {e}")
            return False

    def _send_test_email(self, alert: Dict) -> bool:
        """Send test email notification"""
        try:
            if not (self.smtp_username and self.smtp_password):
                self.logger.warning("Email not configured")
                return False
            
            subject = f"Test Alert: {alert['name']}"
            body = f"""
This is a test notification for your AKS cost alert.

Alert Details:
- Name: {alert['name']}
- Cluster: {alert['cluster_name']}
- Resource Group: {alert['resource_group']}
- Threshold: ${alert['threshold_amount']:,.2f}
- Status: {alert['status']}

This is a test message. No action is required.

Best regards,
AKS Cost Intelligence Team
            """
            
            return self._send_email(subject, body, [self.from_email])
            
        except Exception as e:
            self.logger.error(f"❌ Error sending test email: {e}")
            return False

    def _send_test_slack(self, alert: Dict) -> bool:
        """Send test Slack notification"""
        try:
            # Get fresh webhook URL and channel from settings
            webhook_url = self.settings_manager.get_setting('SLACK_WEBHOOK_URL', '')
            slack_channel = self.settings_manager.get_setting('SLACK_CHANNEL', '#all-kubeopt')
            
            if not webhook_url:
                self.logger.error("❌ Slack webhook URL not configured in settings")
                return False
            
            # Get app URL for dashboard links
            app_url = os.getenv('APP_URL', 'http://localhost:5000')
            cluster_dashboard_url = f"{app_url}/cluster/{alert['cluster_id']}"
            portfolio_url = f"{app_url}/"
            
            payload = {
                "channel": slack_channel,
                "username": "AKS Cost Optimizer",
                "icon_emoji": ":cloud:",
                "text": f"🧪 Test Alert: {alert['name']}",
                "attachments": [
                    {
                        "color": "#36a64f",
                        "title": f"Test Alert: {alert['name']}",
                        "title_link": cluster_dashboard_url,
                        "text": "This is a test notification for your AKS cost alert.",
                        "fields": [
                            {
                                "title": "Cluster",
                                "value": alert['cluster_name'],
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"${alert['threshold_amount']:,.2f}",
                                "short": True
                            }
                        ],
                        "footer": "AKS Cost Intelligence - Test Mode",
                        "actions": [
                            {
                                "type": "button",
                                "text": "View Cluster Dashboard",
                                "url": cluster_dashboard_url,
                                "style": "primary"
                            },
                            {
                                "type": "button",
                                "text": "View Portfolio", 
                                "url": portfolio_url,
                                "style": "default"
                            }
                        ]
                    }
                ]
            }
            
            self.logger.info(f"📤 Sending test Slack notification to {slack_channel}")
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"✅ Test Slack notification sent successfully to {slack_channel}")
                return True
            else:
                self.logger.error(f"❌ Slack API returned status {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error sending test Slack: {e}")
            return False

    def _send_alert_email(self, alert: Dict, triggered_alert: Dict) -> bool:
        """Send actual alert email notification"""
        try:
            if not (self.smtp_username and self.smtp_password):
                return False
            
            current_cost = triggered_alert['current_cost']
            exceeded_by = triggered_alert['threshold_exceeded_by']
            
            subject = f"🚨 Cost Alert: {alert['name']} - Threshold Exceeded"
            body = f"""
COST ALERT: Your AKS cluster has exceeded its cost threshold.

Alert Details:
- Alert Name: {alert['name']}
- Cluster: {alert['cluster_name']}
- Resource Group: {alert['resource_group']}
- Subscription: {alert.get('subscription_name', 'Unknown')}

Cost Information:
- Current Cost: ${current_cost:,.2f}
- Threshold: ${alert['threshold_amount']:,.2f}
- Exceeded By: ${exceeded_by:,.2f}
- Percentage Over: {(exceeded_by / alert['threshold_amount']) * 100:.1f}%

Recommended Actions:
1. Review your cluster resources and utilization
2. Consider scaling down underutilized resources
3. Review and optimize your workloads
4. Check for cost optimization recommendations

Dashboard: {os.getenv('APP_URL', 'http://localhost:5000')}/cluster/{alert['cluster_id']}

This alert was triggered automatically by the AKS Cost Intelligence system.

Best regards,
AKS Cost Intelligence Team
            """
            
            return self._send_email(subject, body, [self.from_email])
            
        except Exception as e:
            self.logger.error(f"❌ Error sending alert email: {e}")
            return False

    def _send_alert_slack(self, alert: Dict, triggered_alert: Dict) -> bool:
        """Send actual alert Slack notification"""
        try:
            # Get fresh webhook URL and channel from settings
            webhook_url = self.settings_manager.get_setting('SLACK_WEBHOOK_URL', '')
            slack_channel = self.settings_manager.get_setting('SLACK_CHANNEL', '#all-kubeopt')
            
            if not webhook_url:
                self.logger.error("❌ Slack webhook URL not configured in settings")
                return False
            
            current_cost = triggered_alert['current_cost']
            exceeded_by = triggered_alert['threshold_exceeded_by']
            
            # Get app URL for dashboard links
            app_url = os.getenv('APP_URL', 'http://localhost:5000')
            cluster_dashboard_url = f"{app_url}/cluster/{alert['cluster_id']}"
            portfolio_url = f"{app_url}/"
            
            color = "#ff9900"  # Orange for cost alerts
            if exceeded_by > alert['threshold_amount'] * 0.5:
                color = "#ff0000"  # Red for major overages
            
            payload = {
                "channel": slack_channel,
                "username": "AKS Cost Optimizer",
                "icon_emoji": ":cloud:",
                "text": f"🚨 Cost Alert: {alert['name']}",
                "attachments": [
                    {
                        "color": color,
                        "title": f"Cost Alert: {alert['name']}",
                        "title_link": cluster_dashboard_url,
                        "text": f"Cluster {alert['cluster_name']} has exceeded its cost threshold.",
                        "fields": [
                            {
                                "title": "Cluster",
                                "value": alert['cluster_name'],
                                "short": True
                            },
                            {
                                "title": "Resource Group",
                                "value": alert['resource_group'],
                                "short": True
                            },
                            {
                                "title": "Current Cost",
                                "value": f"${current_cost:,.2f}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"${alert['threshold_amount']:,.2f}",
                                "short": True
                            },
                            {
                                "title": "Exceeded By",
                                "value": f"${exceeded_by:,.2f}",
                                "short": True
                            },
                            {
                                "title": "Percentage Over",
                                "value": f"{(exceeded_by / alert['threshold_amount']) * 100:.1f}%",
                                "short": True
                            }
                        ],
                        "footer": "AKS Cost Intelligence",
                        "ts": int(datetime.now().timestamp()),
                        "actions": [
                            {
                                "type": "button",
                                "text": "View Cluster Dashboard",
                                "url": cluster_dashboard_url,
                                "style": "primary"
                            },
                            {
                                "type": "button", 
                                "text": "View Portfolio",
                                "url": portfolio_url,
                                "style": "default"
                            }
                        ]
                    }
                ]
            }
            
            self.logger.info(f"📤 Sending cost alert Slack notification to {slack_channel}")
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"✅ Cost alert Slack notification sent successfully to {slack_channel}")
                return True
            else:
                self.logger.error(f"❌ Slack API returned status {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error sending alert Slack: {e}")
            return False

    def _send_email(self, subject: str, body: str, recipients: List[str]) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()  #  Capital letters
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))  #  Capital letters
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, recipients, text)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending email: {e}")
            return False

    def _send_cpu_alert_in_app(self, alert: Dict, triggered_alert: Dict) -> bool:
        """Send CPU monitoring in-app notification"""
        try:
            metrics = triggered_alert['current_metrics']
            severity = triggered_alert['severity']
            
            # Determine alert icon and message based on trigger type
            if triggered_alert['trigger_type'] == 'critical':
                icon = '🔴'
                title = 'Critical CPU Alert'
            elif triggered_alert['trigger_type'] == 'efficiency':
                icon = '⚠️'
                title = 'CPU Efficiency Alert'
            else:
                icon = '📊'
                title = 'CPU Monitoring Alert'
            
            # Create CPU-specific in-app notification
            cpu_notification_data = {
                'title': f"{icon} {title}",
                'message': triggered_alert['trigger_reason'],
                'type': severity,
                'cluster_id': triggered_alert['cluster_id'],
                'alert_id': alert['id'],
                'trigger_id': triggered_alert.get('trigger_id'),
                'metadata': {
                    'alert_type': 'cpu_monitoring',
                    'trigger_type': triggered_alert['trigger_type'],
                    'current_cpu': metrics.get('average_cpu_utilization', 0),
                    'max_cpu': metrics.get('max_cpu_utilization', 0), 
                    'cpu_efficiency': metrics.get('cpu_efficiency', 0),
                    'thresholds': triggered_alert['thresholds']
                }
            }
            
            notification_id = self.db.create_notification(cpu_notification_data)
            
            if notification_id:
                self.logger.info(f"📱 ✅ CPU in-app notification created: {notification_id}")
                return True
            else:
                self.logger.error(f"📱 ❌ Failed to create CPU in-app notification")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error sending CPU alert in-app: {e}")
            return False

    def _send_cpu_alert_email(self, alert: Dict, triggered_alert: Dict) -> bool:
        """Send CPU monitoring email notification"""
        try:
            metrics = triggered_alert['current_metrics']
            cluster_id = triggered_alert['cluster_id']
            
            subject = f"🖥️ CPU Alert: {alert['name']}"
            
            body = f"""
CPU Monitoring Alert

Cluster: {cluster_id}
Alert: {triggered_alert['trigger_reason']}

Current Metrics:
• Average CPU: {metrics.get('average_cpu_utilization', 0):.1f}%
• Peak CPU: {metrics.get('max_cpu_utilization', 0):.1f}%
• CPU Efficiency: {metrics.get('cpu_efficiency', 0):.1f}%
• High CPU Workloads: {metrics.get('high_cpu_count', 0)}

Thresholds:
• Warning: {triggered_alert['thresholds'].get('cpu_warning', 75)}%
• Critical: {triggered_alert['thresholds'].get('cpu_critical', 90)}%
• Min Efficiency: {triggered_alert['thresholds'].get('efficiency_minimum', 40)}%

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return self._send_email(subject, body, [self.from_email])
            
        except Exception as e:
            self.logger.error(f"❌ Error sending CPU alert email: {e}")
            return False

# Global instance
_alerts_manager_instance = None

def init_enhanced_alerts_service(cluster_manager=None):
    """Initialize the enhanced alerts service"""
    global _alerts_manager_instance
    try:
        _alerts_manager_instance = EnhancedAlertsManager(cluster_manager)
        logger.info("✅ Enhanced alerts service initialized")
        return _alerts_manager_instance
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced alerts service: {e}")
        return None

def shutdown_enhanced_alerts_service():
    """Shutdown the enhanced alerts service"""
    global _alerts_manager_instance
    if _alerts_manager_instance:
        logger.info("🔄 Enhanced alerts service shutdown")
        _alerts_manager_instance = None

def get_enhanced_alerts_manager():
    """Get the enhanced alerts manager instance"""
    return _alerts_manager_instance

def initialize_alerts_system(cluster_manager=None):
    """Initialize the alerts system - compatibility function"""
    return init_enhanced_alerts_service(cluster_manager)