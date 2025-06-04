"""
AKS Cost Intelligence - Real Alerts Management System
Handles budget alerts, cost thresholds, and notification management
"""

import os
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Union
from flask import Flask, request, jsonify, render_template_string
import sqlite3
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Alert configuration model"""
    id: Optional[int] = None
    name: str = ""
    alert_type: str = "cost_threshold"  # cost_threshold, performance, optimization
    threshold_amount: float = 0.0
    threshold_percentage: float = 80.0
    email: str = ""
    resource_group: str = ""
    cluster_name: str = ""
    status: str = "active"  # active, paused, triggered
    created_at: Optional[str] = None
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    notification_frequency: str = "immediate"  # immediate, daily, weekly
    
    def to_dict(self):
        return asdict(self)

@dataclass
class AlertTrigger:
    """Alert trigger event model"""
    id: Optional[int] = None
    alert_id: int = 0
    triggered_at: str = ""
    current_cost: float = 0.0
    threshold_exceeded: float = 0.0
    message: str = ""
    action_taken: str = "notification_sent"
    acknowledged: bool = False

class AlertsDatabase:
    """Database manager for alerts system"""
    
    def __init__(self, db_path: str = "alerts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold_amount REAL DEFAULT 0.0,
                    threshold_percentage REAL DEFAULT 80.0,
                    email TEXT NOT NULL,
                    resource_group TEXT,
                    cluster_name TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0,
                    notification_frequency TEXT DEFAULT 'immediate'
                )
            """)
            
            # Alert triggers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id INTEGER,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_cost REAL,
                    threshold_exceeded REAL,
                    message TEXT,
                    action_taken TEXT DEFAULT 'notification_sent',
                    acknowledged BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (alert_id) REFERENCES alerts (id)
                )
            """)
            
            conn.commit()
    
    def create_alert(self, alert: Alert) -> int:
        """Create a new alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (name, alert_type, threshold_amount, threshold_percentage,
                                  email, resource_group, cluster_name, notification_frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.name, alert.alert_type, alert.threshold_amount, alert.threshold_percentage,
                alert.email, alert.resource_group, alert.cluster_name, alert.notification_frequency
            ))
            return cursor.lastrowid
    
    def get_alerts(self, status: str = None) -> List[Alert]:
        """Get all alerts or filter by status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM alerts WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [Alert(**dict(zip(columns, row))) for row in rows]
    
    def update_alert(self, alert_id: int, updates: Dict) -> bool:
        """Update an alert"""
        if not updates:
            return False
            
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [alert_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE alerts SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            return cursor.rowcount > 0
    
    def log_trigger(self, trigger: AlertTrigger) -> int:
        """Log an alert trigger event"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_triggers (alert_id, current_cost, threshold_exceeded, message)
                VALUES (?, ?, ?, ?)
            """, (trigger.alert_id, trigger.current_cost, trigger.threshold_exceeded, trigger.message))
            
            # Update alert trigger count
            cursor.execute("""
                UPDATE alerts SET trigger_count = trigger_count + 1, last_triggered = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (trigger.alert_id,))
            
            return cursor.lastrowid

class EmailNotifier:
    """Email notification service"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
    
    def send_alert_email(self, alert: Alert, trigger_data: Dict) -> bool:
        """Send alert notification email"""
        try:
            # Create email content
            subject = f"🚨 AKS Cost Alert: {alert.name}"
            
            html_content = self._create_email_template(alert, trigger_data)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = alert.email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {alert.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _create_email_template(self, alert: Alert, trigger_data: Dict) -> str:
        """Create HTML email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .alert-box {{ background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
                .metric-value {{ font-size: 1.5rem; font-weight: bold; color: #059669; }}
                .metric-label {{ color: #6b7280; font-size: 0.9rem; margin-top: 5px; }}
                .action-button {{ display: inline-block; background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6b7280; font-size: 0.85rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Cost Alert Triggered</h1>
                    <p>Your AKS cluster has exceeded the configured threshold</p>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h3>Alert: {alert.name}</h3>
                        <p><strong>Cluster:</strong> {alert.cluster_name}</p>
                        <p><strong>Resource Group:</strong> {alert.resource_group}</p>
                        <p><strong>Triggered:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">${trigger_data.get('current_cost', 0):,.2f}</div>
                            <div class="metric-label">Current Monthly Cost</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${trigger_data.get('threshold_amount', 0):,.2f}</div>
                            <div class="metric-label">Alert Threshold</div>
                        </div>
                    </div>
                    
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">{trigger_data.get('percentage_of_budget', 0):.1f}%</div>
                            <div class="metric-label">Budget Utilization</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${trigger_data.get('projected_overspend', 0):,.2f}</div>
                            <div class="metric-label">Projected Overspend</div>
                        </div>
                    </div>
                    
                    <h3>💡 Recommended Actions:</h3>
                    <ul>
                        <li>Review current resource utilization</li>
                        <li>Check for unused or oversized resources</li>
                        <li>Consider implementing auto-scaling policies</li>
                        <li>Review workload resource requests and limits</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}" class="action-button">
                            View Dashboard
                        </a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This alert was generated by AKS Cost Intelligence Platform</p>
                    <p>To modify or disable this alert, visit your dashboard settings</p>
                </div>
            </div>
        </body>
        </html>
        """

class CostMonitor:
    """Cost monitoring and alert checking service"""
    
    def __init__(self, db: AlertsDatabase, notifier: EmailNotifier):
        self.db = db
        self.notifier = notifier
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, check_interval: int = 300):  # 5 minutes
        """Start the monitoring service"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Cost monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Cost monitoring stopped")
    
    def _monitor_loop(self, check_interval: int):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self.check_all_alerts()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def check_all_alerts(self):
        """Check all active alerts"""
        active_alerts = self.db.get_alerts(status='active')
        
        for alert in active_alerts:
            try:
                self.check_single_alert(alert)
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {str(e)}")
    
    def check_single_alert(self, alert: Alert):
        """Check a single alert against current costs"""
        # Get current cost data (this would integrate with your existing cost analysis)
        current_costs = self._get_current_costs(alert.resource_group, alert.cluster_name)
        
        if not current_costs:
            return
        
        threshold_exceeded = False
        trigger_data = {
            'current_cost': current_costs.get('monthly_cost', 0),
            'threshold_amount': alert.threshold_amount,
            'percentage_of_budget': 0,
            'projected_overspend': 0
        }
        
        if alert.alert_type == 'cost_threshold':
            monthly_cost = current_costs.get('monthly_cost', 0)
            
            if alert.threshold_amount > 0:
                # Fixed amount threshold
                if monthly_cost >= alert.threshold_amount:
                    threshold_exceeded = True
                    trigger_data['percentage_of_budget'] = (monthly_cost / alert.threshold_amount) * 100
                    trigger_data['projected_overspend'] = monthly_cost - alert.threshold_amount
            else:
                # Percentage-based threshold (would need baseline budget)
                budget = current_costs.get('monthly_budget', 5000)  # Default or configured budget
                threshold_amount = budget * (alert.threshold_percentage / 100)
                
                if monthly_cost >= threshold_amount:
                    threshold_exceeded = True
                    trigger_data['threshold_amount'] = threshold_amount
                    trigger_data['percentage_of_budget'] = (monthly_cost / budget) * 100
                    trigger_data['projected_overspend'] = monthly_cost - threshold_amount
        
        if threshold_exceeded:
            self._trigger_alert(alert, trigger_data)
    
    def _get_current_costs(self, resource_group: str, cluster_name: str) -> Dict:
        """Get current cost data for the specified cluster"""
        # This would integrate with your existing cost analysis system
        # For now, return mock data - replace with actual cost fetching logic
        
        import random
        base_cost = random.uniform(800, 2500)  # Simulate varying costs
        
        return {
            'monthly_cost': base_cost,
            'daily_cost': base_cost / 30,
            'monthly_budget': 2000,  # This would come from configuration
            'last_updated': datetime.now().isoformat()
        }
    
    def _trigger_alert(self, alert: Alert, trigger_data: Dict):
        """Trigger an alert notification"""
        # Check if we should send notification based on frequency
        if not self._should_send_notification(alert):
            return
        
        # Create trigger record
        trigger = AlertTrigger(
            alert_id=alert.id,
            current_cost=trigger_data.get('current_cost', 0),
            threshold_exceeded=trigger_data.get('projected_overspend', 0),
            message=f"Cost threshold exceeded: ${trigger_data.get('current_cost', 0):,.2f} >= ${trigger_data.get('threshold_amount', 0):,.2f}"
        )
        
        # Log the trigger
        trigger_id = self.db.log_trigger(trigger)
        
        # Send notification
        if self.notifier.send_alert_email(alert, trigger_data):
            logger.info(f"Alert {alert.id} triggered and notification sent")
        else:
            logger.error(f"Failed to send notification for alert {alert.id}")
    
    def _should_send_notification(self, alert: Alert) -> bool:
        """Check if notification should be sent based on frequency settings"""
        if alert.notification_frequency == 'immediate':
            return True
        
        if not alert.last_triggered:
            return True
        
        last_triggered = datetime.fromisoformat(alert.last_triggered)
        now = datetime.now()
        
        if alert.notification_frequency == 'daily':
            return (now - last_triggered).days >= 1
        elif alert.notification_frequency == 'weekly':
            return (now - last_triggered).days >= 7
        
        return True

class AlertsManager:
    """Main alerts management class"""
    
    def __init__(self):
        self.db = AlertsDatabase()
        self.notifier = EmailNotifier()
        self.monitor = CostMonitor(self.db, self.notifier)
    
    def start_service(self):
        """Start the alerts service"""
        self.monitor.start_monitoring()
    
    def stop_service(self):
        """Stop the alerts service"""
        self.monitor.stop_monitoring()
    
    # Flask route handlers
    def create_alert_route(self, request_data: Dict) -> Dict:
        """Handle create alert request"""
        try:
            alert = Alert(
                name=request_data.get('name', ''),
                alert_type=request_data.get('alert_type', 'cost_threshold'),
                threshold_amount=float(request_data.get('threshold_amount', 0)),
                threshold_percentage=float(request_data.get('threshold_percentage', 80)),
                email=request_data.get('email', ''),
                resource_group=request_data.get('resource_group', ''),
                cluster_name=request_data.get('cluster_name', ''),
                notification_frequency=request_data.get('notification_frequency', 'immediate')
            )
            
            alert_id = self.db.create_alert(alert)
            return {'status': 'success', 'alert_id': alert_id, 'message': 'Alert created successfully'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_alerts_route(self) -> Dict:
        """Handle get alerts request"""
        try:
            alerts = self.db.get_alerts()
            return {
                'status': 'success', 
                'alerts': [alert.to_dict() for alert in alerts]
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def update_alert_route(self, alert_id: int, request_data: Dict) -> Dict:
        """Handle update alert request"""
        try:
            success = self.db.update_alert(alert_id, request_data)
            if success:
                return {'status': 'success', 'message': 'Alert updated successfully'}
            else:
                return {'status': 'error', 'message': 'Alert not found'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def delete_alert_route(self, alert_id: int) -> Dict:
        """Handle delete alert request"""
        try:
            success = self.db.delete_alert(alert_id)
            if success:
                return {'status': 'success', 'message': 'Alert deleted successfully'}
            else:
                return {'status': 'error', 'message': 'Alert not found'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_alert_route(self, alert_id: int) -> Dict:
        """Handle test alert request"""
        try:
            alerts = self.db.get_alerts()
            alert = next((a for a in alerts if a.id == alert_id), None)
            
            if not alert:
                return {'status': 'error', 'message': 'Alert not found'}
            
            # Send test notification
            test_trigger_data = {
                'current_cost': 1500.00,
                'threshold_amount': alert.threshold_amount,
                'percentage_of_budget': 85.0,
                'projected_overspend': 300.00
            }
            
            success = self.notifier.send_alert_email(alert, test_trigger_data)
            
            if success:
                return {'status': 'success', 'message': 'Test email sent successfully'}
            else:
                return {'status': 'error', 'message': 'Failed to send test email'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

# Initialize global alerts manager
alerts_manager = AlertsManager()

def init_alerts_service():
    """Initialize and start the alerts service"""
    alerts_manager.start_service()
    logger.info("Alerts service initialized")

def shutdown_alerts_service():
    """Shutdown the alerts service"""
    alerts_manager.stop_service()
    logger.info("Alerts service shutdown")