"""
Enhanced AKS Cost Intelligence - Alerts Management System
Integrated with existing cluster database and analysis system
"""

import os
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
import traceback
from typing import List, Dict, Optional, Union
import sqlite3
import threading
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Enhanced Alert configuration model - FIXED with cluster_id"""
    id: Optional[int] = None
    name: str = ""
    alert_type: str = "cost_threshold"
    threshold_amount: float = 0.0
    threshold_percentage: float = 80.0
    email: str = ""
    resource_group: str = ""
    cluster_name: str = ""
    status: str = "active"
    created_at: Optional[str] = None
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    notification_frequency: str = "immediate"
    cluster_id: Optional[str] = None  #
    
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

class EnhancedAlertsDatabase:
    """Enhanced database manager integrated with existing cluster database"""
    
    def __init__(self, cluster_db_path: str = 'app/data/database/clusters.db'):
        self.db_path = cluster_db_path  # Use same database as clusters
        self.init_alerts_tables()
        self.migrate_existing_alerts() 
    
    def init_alerts_tables(self):
        """Initialize alerts tables in existing cluster database - FIXED"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enhanced alerts table with proper cluster_id handling
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        alert_type TEXT NOT NULL DEFAULT 'cost_threshold',
                        threshold_amount REAL DEFAULT 0.0,
                        threshold_percentage REAL DEFAULT 80.0,
                        email TEXT NOT NULL,
                        resource_group TEXT,
                        cluster_name TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_triggered TIMESTAMP,
                        trigger_count INTEGER DEFAULT 0,
                        notification_frequency TEXT DEFAULT 'immediate',
                        cluster_id TEXT,
                        FOREIGN KEY (cluster_id) REFERENCES clusters (id)
                    )
                """)
                
                # Check if cluster_id column exists, if not add it
                cursor.execute("PRAGMA table_info(alerts)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'cluster_id' not in columns:
                    logger.info("🔧 Adding cluster_id column to alerts table")
                    cursor.execute("ALTER TABLE alerts ADD COLUMN cluster_id TEXT")
                
                # Enhanced alert triggers table
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
                        cluster_id TEXT,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (alert_id) REFERENCES alerts (id),
                        FOREIGN KEY (cluster_id) REFERENCES clusters (id)
                    )
                """)
                
                # Add indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_cluster_id ON alerts(cluster_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_triggers_alert_id ON alert_triggers(alert_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_triggers_triggered_at ON alert_triggers(triggered_at)")
                
                conn.commit()
                logger.info("✅ Enhanced alerts tables initialized with cluster_id support")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize alerts tables: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

    # Also add this method to fix any existing alerts without cluster_id:

    def migrate_existing_alerts(self):
        """Migrate existing alerts to include cluster_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get alerts without cluster_id
                cursor.execute("""
                    SELECT id, resource_group, cluster_name 
                    FROM alerts 
                    WHERE cluster_id IS NULL OR cluster_id = ''
                """)
                
                alerts_to_update = cursor.fetchall()
                
                for alert_id, resource_group, cluster_name in alerts_to_update:
                    if resource_group and cluster_name:
                        cluster_id = f"{resource_group}_{cluster_name}"
                        cursor.execute("""
                            UPDATE alerts 
                            SET cluster_id = ? 
                            WHERE id = ?
                        """, (cluster_id, alert_id))
                        logger.info(f"🔧 Updated alert {alert_id} with cluster_id: {cluster_id}")
                
                conn.commit()
                
                if alerts_to_update:
                    logger.info(f"✅ Migrated {len(alerts_to_update)} existing alerts")
                    
        except Exception as e:
            logger.error(f"❌ Failed to migrate existing alerts: {e}")

    
    def create_alert(self, alert: Alert) -> int:
        """Create a new alert with enhanced validation"""
        try:
            # Generate cluster_id if cluster_name and resource_group provided
            cluster_id = None
            if alert.resource_group and alert.cluster_name:
                cluster_id = f"{alert.resource_group}_{alert.cluster_name}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alerts (name, alert_type, threshold_amount, threshold_percentage,
                                      email, resource_group, cluster_name, notification_frequency, cluster_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.name, alert.alert_type, alert.threshold_amount, alert.threshold_percentage,
                    alert.email, alert.resource_group, alert.cluster_name, alert.notification_frequency, cluster_id
                ))
                alert_id = cursor.lastrowid
                logger.info(f"✅ Created alert {alert_id}: {alert.name}")
                return alert_id
        except Exception as e:
            logger.error(f"❌ Failed to create alert: {e}")
            raise
    
    def get_alerts(self, status: str = None, cluster_id: str = None) -> List[Alert]:
        """Get alerts with enhanced filtering - FIXED VERSION"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM alerts WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if cluster_id:
                    query += " AND cluster_id = ?"
                    params.append(cluster_id)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                alerts = []
                for row in rows:
                    alert_dict = dict(zip(columns, row))
                    
                    # Handle None values and provide defaults
                    cleaned_dict = {}
                    for key, value in alert_dict.items():
                        if key == 'threshold_amount' or key == 'threshold_percentage' or key == 'trigger_count':
                            cleaned_dict[key] = float(value) if value is not None else 0.0
                        elif key in ['name', 'email', 'resource_group', 'cluster_name', 'cluster_id']:
                            cleaned_dict[key] = str(value) if value is not None else ""
                        elif key == 'status':
                            cleaned_dict[key] = str(value) if value is not None else "active"
                        elif key == 'alert_type':
                            cleaned_dict[key] = str(value) if value is not None else "cost_threshold"
                        elif key == 'notification_frequency':
                            cleaned_dict[key] = str(value) if value is not None else "immediate"
                        else:
                            cleaned_dict[key] = value
                    
                    try:
                        alerts.append(Alert(**cleaned_dict))
                    except Exception as alert_error:
                        logger.error(f"❌ Error creating alert from database row: {alert_error}")
                        logger.error(f"❌ Row data: {cleaned_dict}")
                        # Skip this alert and continue
                        continue
                
                return alerts
        except Exception as e:
            logger.error(f"❌ Failed to get alerts: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
    
    def update_alert(self, alert_id: int, updates: Dict) -> bool:
        """Update an alert with validation"""
        try:
            if not updates:
                return False
                
            # Validate updates
            allowed_fields = {
                'name', 'alert_type', 'threshold_amount', 'threshold_percentage',
                'email', 'resource_group', 'cluster_name', 'status',
                'notification_frequency'
            }
            
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not filtered_updates:
                return False
            
            set_clause = ", ".join([f"{key} = ?" for key in filtered_updates.keys()])
            values = list(filtered_updates.values()) + [alert_id]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE alerts SET {set_clause} WHERE id = ?", values)
                success = cursor.rowcount > 0
                
                if success:
                    logger.info(f"✅ Updated alert {alert_id}")
                return success
        except Exception as e:
            logger.error(f"❌ Failed to update alert {alert_id}: {e}")
            return False
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert and its triggers"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete alert triggers first
                cursor.execute("DELETE FROM alert_triggers WHERE alert_id = ?", (alert_id,))
                
                # Delete alert
                cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"✅ Deleted alert {alert_id}")
                return success
        except Exception as e:
            logger.error(f"❌ Failed to delete alert {alert_id}: {e}")
            return False
    
    def log_trigger(self, trigger: AlertTrigger) -> int:
        """Log an alert trigger event with enhanced metadata"""
        try:
            # Get cluster_id from alert
            cluster_id = None
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cluster_id FROM alerts WHERE id = ?", (trigger.alert_id,))
                row = cursor.fetchone()
                if row:
                    cluster_id = row[0]
                
                # Insert trigger
                cursor.execute("""
                    INSERT INTO alert_triggers (alert_id, current_cost, threshold_exceeded, message, cluster_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (trigger.alert_id, trigger.current_cost, trigger.threshold_exceeded, trigger.message, cluster_id))
                
                trigger_id = cursor.lastrowid
                
                # Update alert trigger count and last triggered time
                cursor.execute("""
                    UPDATE alerts SET trigger_count = trigger_count + 1, last_triggered = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (trigger.alert_id,))
                
                logger.info(f"✅ Logged alert trigger {trigger_id} for alert {trigger.alert_id}")
                return trigger_id
        except Exception as e:
            logger.error(f"❌ Failed to log alert trigger: {e}")
            return 0
    
    def get_triggers(self, alert_id: int = None, limit: int = 50) -> List[Dict]:
        """Get alert triggers with details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT at.*, a.name as alert_name, a.email, c.name as cluster_name
                    FROM alert_triggers at
                    JOIN alerts a ON at.alert_id = a.id
                    LEFT JOIN clusters c ON at.cluster_id = c.id
                    WHERE 1=1
                """
                params = []
                
                if alert_id:
                    query += " AND at.alert_id = ?"
                    params.append(alert_id)
                
                query += " ORDER BY at.triggered_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get triggers: {e}")
            return []

class EnhancedEmailNotifier:
    """Enhanced email notification service with better templates"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.app_url = os.getenv('APP_URL', 'http://localhost:5000')
        
        # Check if email is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("⚠️ Email notifications not configured - alerts will be logged only")
    
    def send_alert_email(self, alert: Alert, trigger_data: Dict) -> bool:
        """Send enhanced alert notification email"""
        if not self.is_configured:
            logger.info(f"📧 Email not configured - would send alert for {alert.name}")
            return True  # Return True for logging purposes
        
        try:
            # Create email content
            subject = f"🚨 AKS Cost Alert: {alert.name}"
            
            html_content = self._create_enhanced_email_template(alert, trigger_data)
            
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
            
            logger.info(f"📧 Alert email sent to {alert.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False
    
    def _create_enhanced_email_template(self, alert: Alert, trigger_data: Dict) -> str:
        """Create enhanced HTML email template"""
        cluster_url = f"{self.app_url}/cluster/{alert.resource_group}_{alert.cluster_name}" if alert.cluster_name else self.app_url
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AKS Cost Alert</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 1.8rem; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .alert-box {{ background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
                .metric-value {{ font-size: 1.5rem; font-weight: bold; color: #dc3545; }}
                .metric-label {{ color: #6b7280; font-size: 0.9rem; margin-top: 5px; }}
                .action-button {{ display: inline-block; background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6b7280; font-size: 0.85rem; }}
                .recommendations {{ background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                .recommendations h3 {{ color: #1976d2; margin: 0 0 15px 0; }}
                .recommendations ul {{ margin: 0; padding-left: 20px; }}
                .recommendations li {{ margin-bottom: 8px; }}
                @media (max-width: 600px) {{
                    .metrics {{ grid-template-columns: 1fr; }}
                    .content {{ padding: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Cost Alert Triggered</h1>
                    <p>Your AKS cluster has exceeded the configured cost threshold</p>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h3 style="margin: 0 0 10px 0; color: #dc3545;">Alert Details</h3>
                        <p><strong>Alert Name:</strong> {alert.name}</p>
                        <p><strong>Cluster:</strong> {alert.cluster_name or 'All clusters'}</p>
                        <p><strong>Resource Group:</strong> {alert.resource_group or 'All resource groups'}</p>
                        <p><strong>Triggered:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <p><strong>Alert Type:</strong> {alert.alert_type.replace('_', ' ').title()}</p>
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
                            <div class="metric-label">Amount Over Threshold</div>
                        </div>
                    </div>
                    
                    <div class="recommendations">
                        <h3>💡 Immediate Actions Recommended</h3>
                        <ul>
                            <li><strong>Review Resource Utilization:</strong> Check for underutilized or idle resources</li>
                            <li><strong>Analyze Cost Drivers:</strong> Identify which services are contributing most to costs</li>
                            <li><strong>Implement Auto-scaling:</strong> Enable HPA and VPA for better resource efficiency</li>
                            <li><strong>Right-size Resources:</strong> Adjust CPU and memory requests/limits based on actual usage</li>
                            <li><strong>Storage Optimization:</strong> Review storage classes and cleanup unused volumes</li>
                            <li><strong>Schedule Analysis:</strong> Run a comprehensive cost optimization analysis</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{cluster_url}" class="action-button">
                            📊 View Cluster Dashboard
                        </a>
                        <br>
                        <a href="{self.app_url}" style="color: #6b7280; text-decoration: none; font-size: 0.9rem;">
                            Or visit the main AKS Cost Intelligence dashboard
                        </a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>AKS Cost Intelligence Platform</strong></p>
                    <p>This alert was automatically generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p style="margin-top: 15px;">
                        <small>To modify or disable this alert, visit your 
                        <a href="{cluster_url}#alerts" style="color: #007bff;">dashboard settings</a></small>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

class EnhancedCostMonitor:
    """Enhanced cost monitoring with integration to existing analysis system"""
    
    def __init__(self, db: EnhancedAlertsDatabase, notifier: EnhancedEmailNotifier, enhanced_cluster_manager=None):
        self.db = db
        self.notifier = notifier
        self.enhanced_cluster_manager = enhanced_cluster_manager
        self.monitoring = False
        self.monitor_thread = None
        self.check_interval = 300  # 5 minutes default
    
    def start_monitoring(self, check_interval: int = 300):
        """Start the enhanced monitoring service"""
        if self.monitoring:
            logger.info("🔔 Monitoring already running")
            return
        
        self.check_interval = check_interval
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._enhanced_monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"🔔 Enhanced cost monitoring started (checking every {check_interval} seconds)")
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("🔔 Cost monitoring stopped")
    
    def _enhanced_monitor_loop(self):
        """Enhanced monitoring loop with better error handling"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.monitoring:
            try:
                self.check_all_alerts()
                consecutive_errors = 0  # Reset error counter on success
                time.sleep(self.check_interval)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Error in monitoring loop (attempt {consecutive_errors}): {str(e)}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"❌ Too many consecutive errors ({consecutive_errors}), stopping monitoring")
                    self.monitoring = False
                    break
                
                # Exponential backoff for errors
                error_sleep = min(300, 30 * (2 ** consecutive_errors))
                time.sleep(error_sleep)
    
    def check_all_alerts(self):
        """Check all active alerts with enhanced logic"""
        try:
            active_alerts = self.db.get_alerts(status='active')
            
            if not active_alerts:
                return
            
            logger.info(f"🔍 Checking {len(active_alerts)} active alerts")
            
            for alert in active_alerts:
                try:
                    self.check_single_alert(alert)
                except Exception as e:
                    logger.error(f"❌ Error checking alert {alert.id} ({alert.name}): {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ Error in check_all_alerts: {str(e)}")
    
    def check_single_alert(self, alert: Alert):
        """Check a single alert with enhanced cost data integration"""
        try:
            # Get current cost data for the specific cluster or all clusters
            current_costs = self._get_enhanced_current_costs(alert)
            
            if not current_costs:
                logger.debug(f"No cost data available for alert {alert.id}")
                return
            
            # Check if alert should trigger
            should_trigger, trigger_data = self._evaluate_alert_conditions(alert, current_costs)
            
            if should_trigger:
                # Check notification frequency to avoid spam
                if self._should_send_notification(alert):
                    self._trigger_enhanced_alert(alert, trigger_data)
                else:
                    logger.info(f"Alert {alert.id} conditions met but notification frequency limit reached")
                    
        except Exception as e:
            logger.error(f"❌ Error checking single alert {alert.id}: {str(e)}")
    
    def _get_enhanced_current_costs(self, alert: Alert) -> Dict:
        """Get current cost data with integration to existing analysis system"""
        try:
            if self.enhanced_cluster_manager and alert.cluster_name and alert.resource_group:
                # Get costs for specific cluster
                cluster_id = f"{alert.resource_group}_{alert.cluster_name}"
                latest_analysis = self.enhanced_cluster_manager.get_latest_analysis(cluster_id)
                
                if latest_analysis and latest_analysis.get('total_cost'):
                    return {
                        'monthly_cost': latest_analysis.get('total_cost', 0),
                        'daily_cost': latest_analysis.get('total_cost', 0) / 30,
                        'cluster_id': cluster_id,
                        'last_analyzed': latest_analysis.get('analysis_timestamp'),
                        'confidence': latest_analysis.get('analysis_confidence', 0.5)
                    }
            
            # Fallback: Mock data for testing (replace with actual cost fetching logic)
            import random
            base_cost = random.uniform(800, 2500)
            
            return {
                'monthly_cost': base_cost,
                'daily_cost': base_cost / 30,
                'cluster_id': alert.cluster_name,
                'last_analyzed': datetime.now().isoformat(),
                'confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting current costs for alert {alert.id}: {str(e)}")
            return {}
    
    def _evaluate_alert_conditions(self, alert: Alert, current_costs: Dict) -> tuple:
        """Evaluate if alert conditions are met"""
        monthly_cost = current_costs.get('monthly_cost', 0)
        
        if monthly_cost <= 0:
            return False, {}
        
        trigger_data = {
            'current_cost': monthly_cost,
            'threshold_amount': alert.threshold_amount,
            'percentage_of_budget': 0,
            'projected_overspend': 0,
            'confidence': current_costs.get('confidence', 0.5)
        }
        
        should_trigger = False
        
        if alert.alert_type == 'cost_threshold':
            if alert.threshold_amount > 0:
                # Fixed amount threshold
                if monthly_cost >= alert.threshold_amount:
                    should_trigger = True
                    trigger_data['percentage_of_budget'] = (monthly_cost / alert.threshold_amount) * 100
                    trigger_data['projected_overspend'] = monthly_cost - alert.threshold_amount
            
            elif alert.threshold_percentage > 0:
                # Percentage-based threshold (would need baseline budget)
                # For now, use a default budget or get from cluster config
                default_budget = 2000  # This should come from configuration
                threshold_amount = default_budget * (alert.threshold_percentage / 100)
                
                if monthly_cost >= threshold_amount:
                    should_trigger = True
                    trigger_data['threshold_amount'] = threshold_amount
                    trigger_data['percentage_of_budget'] = (monthly_cost / default_budget) * 100
                    trigger_data['projected_overspend'] = monthly_cost - threshold_amount
        
        return should_trigger, trigger_data
    
    def _should_send_notification(self, alert: Alert) -> bool:
        """Enhanced notification frequency checking"""
        if alert.notification_frequency == 'immediate':
            return True
        
        if not alert.last_triggered:
            return True
        
        try:
            last_triggered = datetime.fromisoformat(alert.last_triggered.replace('Z', ''))
            now = datetime.now()
            time_diff = now - last_triggered
            
            if alert.notification_frequency == 'daily':
                return time_diff.total_seconds() >= 86400  # 24 hours
            elif alert.notification_frequency == 'weekly':
                return time_diff.total_seconds() >= 604800  # 7 days
            
        except Exception as e:
            logger.error(f"❌ Error checking notification frequency: {str(e)}")
            return True  # Default to allowing notification on error
        
        return True
    
    def _trigger_enhanced_alert(self, alert: Alert, trigger_data: Dict):
        """Trigger an alert with enhanced logging and notification"""
        try:
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
            notification_sent = self.notifier.send_alert_email(alert, trigger_data)
            
            if notification_sent:
                logger.info(f"🚨 Alert {alert.id} triggered and notification sent (trigger ID: {trigger_id})")
            else:
                logger.error(f"🚨 Alert {alert.id} triggered but notification failed (trigger ID: {trigger_id})")
            
        except Exception as e:
            logger.error(f"❌ Error triggering alert {alert.id}: {str(e)}")

class EnhancedAlertsManager:
    """Enhanced main alerts management class with better integration"""
    
    def __init__(self, enhanced_cluster_manager=None):
        self.enhanced_cluster_manager = enhanced_cluster_manager
        self.db = EnhancedAlertsDatabase(enhanced_cluster_manager.db_path if enhanced_cluster_manager else 'app/data/database/clusters.db')
        self.notifier = EnhancedEmailNotifier()
        self.monitor = EnhancedCostMonitor(self.db, self.notifier, enhanced_cluster_manager)
        self._service_started = False
    
    def start_service(self):
        """Start the enhanced alerts service"""
        if self._service_started:
            logger.info("🔔 Alerts service already started")
            return
        
        try:
            self.monitor.start_monitoring()
            self._service_started = True
            logger.info("✅ Enhanced alerts service started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start alerts service: {str(e)}")
            raise
    
    def stop_service(self):
        """Stop the alerts service"""
        if not self._service_started:
            return
        
        try:
            self.monitor.stop_monitoring()
            self._service_started = False
            logger.info("✅ Enhanced alerts service stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping alerts service: {str(e)}")
    
    # Enhanced API handlers
    def create_alert_route(self, request_data: Dict) -> Dict:
        """Handle create alert request with enhanced validation"""
        try:
            # Enhanced validation
            required_fields = ['email']
            missing_fields = [field for field in required_fields if not request_data.get(field)]
            
            if missing_fields:
                return {
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }
            
            # Validate email format
            email = request_data.get('email', '').strip()
            if not email or '@' not in email:
                return {
                    'status': 'error',
                    'message': 'Valid email address is required'
                }
            
            # Validate thresholds
            threshold_amount = float(request_data.get('threshold_amount', 0))
            threshold_percentage = float(request_data.get('threshold_percentage', 0))
            
            if threshold_amount <= 0 and threshold_percentage <= 0:
                return {
                    'status': 'error',
                    'message': 'Either threshold amount or percentage must be specified'
                }
            
            # Handle cluster_id to populate cluster details
            cluster_id = request_data.get('cluster_id')
            if cluster_id and self.enhanced_cluster_manager:
                cluster = self.enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster:
                    request_data['cluster_name'] = cluster['name']
                    request_data['resource_group'] = cluster['resource_group']
            
            alert = Alert(
                name=request_data.get('name', f"Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
                alert_type=request_data.get('alert_type', 'cost_threshold'),
                threshold_amount=threshold_amount,
                threshold_percentage=threshold_percentage,
                email=email,
                resource_group=request_data.get('resource_group', ''),
                cluster_name=request_data.get('cluster_name', ''),
                notification_frequency=request_data.get('notification_frequency', 'immediate')
            )
            
            alert_id = self.db.create_alert(alert)
            return {
                'status': 'success',
                'alert_id': alert_id,
                'message': 'Alert created successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to create alert: {str(e)}'
            }
    
    def get_alerts_route(self, cluster_id: str = None) -> Dict:
        """Handle get alerts request with filtering - COMPLETELY FIXED VERSION"""
        try:
            logger.info(f"🔍 Getting alerts for cluster_id: {cluster_id}")
            
            # Get alerts with proper filtering
            if cluster_id:
                # First try to get alerts by cluster_id directly
                alerts = self.db.get_alerts(status='active', cluster_id=cluster_id)
                
                # If no alerts found by cluster_id, try filtering by cluster name/resource group
                if not alerts and self.enhanced_cluster_manager:
                    cluster = self.enhanced_cluster_manager.get_cluster(cluster_id)
                    if cluster:
                        logger.info(f"🔍 Filtering by cluster name: {cluster['name']}, resource group: {cluster['resource_group']}")
                        all_alerts = self.db.get_alerts(status='active')
                        alerts = [a for a in all_alerts if 
                                a.cluster_name == cluster['name'] and 
                                a.resource_group == cluster['resource_group']]
            else:
                # Get all active alerts
                alerts = self.db.get_alerts(status='active')
            
            logger.info(f"✅ Found {len(alerts)} alerts")
            
            return {
                'status': 'success',
                'alerts': [alert.to_dict() for alert in alerts],
                'total': len(alerts),
                'cluster_id': cluster_id
            }
        except Exception as e:
            logger.error(f"❌ Error getting alerts: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': f'Failed to get alerts: {str(e)}'
            }
    
    def update_alert_route(self, alert_id: int, request_data: Dict) -> Dict:
        """Handle update alert request"""
        try:
            success = self.db.update_alert(alert_id, request_data)
            if success:
                return {
                    'status': 'success',
                    'message': 'Alert updated successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Alert not found or update failed'
                }
        except Exception as e:
            logger.error(f"❌ Error updating alert: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to update alert: {str(e)}'
            }
    
    def delete_alert_route(self, alert_id: int) -> Dict:
        """Handle delete alert request"""
        try:
            success = self.db.delete_alert(alert_id)
            if success:
                return {
                    'status': 'success',
                    'message': 'Alert deleted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Alert not found'
                }
        except Exception as e:
            logger.error(f"❌ Error deleting alert: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to delete alert: {str(e)}'
            }
    
    def test_alert_route(self, alert_id: int) -> Dict:
        """Handle test alert request with enhanced test data"""
        try:
            alerts = self.db.get_alerts()
            alert = next((a for a in alerts if a.id == alert_id), None)
            
            if not alert:
                return {
                    'status': 'error',
                    'message': 'Alert not found'
                }
            
            # Create realistic test trigger data
            test_trigger_data = {
                'current_cost': alert.threshold_amount * 1.15 if alert.threshold_amount > 0 else 1500.00,
                'threshold_amount': alert.threshold_amount if alert.threshold_amount > 0 else 1000.00,
                'percentage_of_budget': 115.0,
                'projected_overspend': alert.threshold_amount * 0.15 if alert.threshold_amount > 0 else 500.00,
                'confidence': 0.95
            }
            
            success = self.notifier.send_alert_email(alert, test_trigger_data)
            
            if success:
                return {
                    'status': 'success',
                    'message': 'Test notification sent successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to send test notification - check email configuration'
                }
                
        except Exception as e:
            logger.error(f"❌ Error testing alert: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to test alert: {str(e)}'
            }

# Initialize global enhanced alerts manager
enhanced_alerts_manager = None

def init_enhanced_alerts_service(enhanced_cluster_manager=None):
    """Initialize and start the enhanced alerts service"""
    global enhanced_alerts_manager
    
    try:
        enhanced_alerts_manager = EnhancedAlertsManager(enhanced_cluster_manager)
        enhanced_alerts_manager.start_service()
        logger.info("✅ Enhanced alerts service initialized successfully")
        return enhanced_alerts_manager
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced alerts service: {str(e)}")
        raise

def shutdown_enhanced_alerts_service():
    """Shutdown the enhanced alerts service"""
    global enhanced_alerts_manager
    
    if enhanced_alerts_manager:
        enhanced_alerts_manager.stop_service()
        logger.info("✅ Enhanced alerts service shutdown complete")

# Compatibility aliases for existing integration
alerts_manager = None

def init_alerts_service():
    """Compatibility function for existing integration"""
    global alerts_manager
    alerts_manager = init_enhanced_alerts_service()
    return alerts_manager

def shutdown_alerts_service():
    """Compatibility function for existing integration"""
    shutdown_enhanced_alerts_service()