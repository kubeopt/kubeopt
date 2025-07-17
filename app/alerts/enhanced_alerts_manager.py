# enhanced_alerts_manager.py - Complete Enhanced Alerts Manager with Database Backend

import os
import json
import traceback
import requests
import smtplib
from email.mime.text import MIMEText  # Fixed: Capital letters
from email.mime.multipart import MIMEMultipart  # Fixed: Capital letters
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import the alerts database
from app.data.alerts_database import alerts_db

logger = logging.getLogger(__name__)

class EnhancedAlertsManager:
    """Complete alerts manager with database backend and multi-channel notifications"""
    
    def __init__(self, cluster_manager=None):
        self.cluster_manager = cluster_manager
        self.db = alerts_db
        self.logger = logging.getLogger(__name__)
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        
        # Slack configuration
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        
        self.logger.info("✅ Enhanced alerts manager initialized")

    def get_alerts_route(self) -> Dict:
        """Get all alerts (API route handler)"""
        try:
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
            # Validate required fields
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
            
            # Set defaults
            alert_data.setdefault('status', 'active')
            alert_data.setdefault('alert_type', 'cost_threshold')
            alert_data.setdefault('threshold_type', 'monthly')
            alert_data.setdefault('notification_channels', ['email'])
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
            if 'slack' in alert['notification_channels'] and self.slack_webhook_url:
                slack_sent = self._send_test_slack(alert)
            
            channels_tested = []
            if email_sent:
                channels_tested.append('email')
            if slack_sent:
                channels_tested.append('slack')
            
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
        """Check and trigger alerts for a cluster"""
        try:
            triggered_alerts = self.db.check_cluster_alerts(cluster_id, current_cost)
            
            for triggered_alert in triggered_alerts:
                alert = triggered_alert['alert']
                trigger_id = triggered_alert['trigger_id']
                
                # Send notifications
                notifications_sent = []
                
                # Email notification
                if 'email' in alert['notification_channels']:
                    if self._send_alert_email(alert, triggered_alert):
                        notifications_sent.append('email')
                
                # Slack notification
                if 'slack' in alert['notification_channels'] and self.slack_webhook_url:
                    if self._send_alert_slack(alert, triggered_alert):
                        notifications_sent.append('slack')
                
                # Update trigger with notification status
                self.db.update_trigger_notification_status(
                    trigger_id, 
                    len(notifications_sent) > 0,
                    notifications_sent
                )
                
                self.logger.info(f"🚨 Alert triggered: {alert['name']} for cluster {cluster_id}")
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"❌ Error checking cluster alerts: {e}")
            return []

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
            payload = {
                "text": f"🧪 Test Alert: {alert['name']}",
                "attachments": [
                    {
                        "color": "#36a64f",
                        "title": f"Test Alert: {alert['name']}",
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
                        "footer": "AKS Cost Intelligence - Test Mode"
                    }
                ]
            }
            
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            return response.status_code == 200
            
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
            current_cost = triggered_alert['current_cost']
            exceeded_by = triggered_alert['threshold_exceeded_by']
            
            color = "#ff9900"  # Orange for cost alerts
            if exceeded_by > alert['threshold_amount'] * 0.5:
                color = "#ff0000"  # Red for major overages
            
            payload = {
                "text": f"🚨 Cost Alert: {alert['name']}",
                "attachments": [
                    {
                        "color": color,
                        "title": f"Cost Alert: {alert['name']}",
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
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"❌ Error sending alert Slack: {e}")
            return False

    def _send_email(self, subject: str, body: str, recipients: List[str]) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()  # Fixed: Capital letters
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))  # Fixed: Capital letters
            
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