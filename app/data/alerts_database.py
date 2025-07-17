# alerts_database.py - Dedicated Alerts Database Manager

import sqlite3
import json
import logging
from datetime import datetime, timedelta
import traceback
from typing import Any, Dict, List, Optional
import os

# Set up logger
logger = logging.getLogger(__name__)

class AlertsDatabase:
    """Dedicated database manager for alerts system"""
    
    def __init__(self, db_path='app/data/database/alerts.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.init_database()
        
        # Clean up any stale data on startup
        self.cleanup_old_data()

    def init_database(self):
        """Initialize SQLite database for alerts"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Create alerts table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT DEFAULT '',
                        cluster_id TEXT NOT NULL,
                        cluster_name TEXT NOT NULL,
                        resource_group TEXT NOT NULL,
                        subscription_id TEXT,
                        subscription_name TEXT,
                        alert_type TEXT DEFAULT 'cost_threshold',
                        threshold_amount REAL NOT NULL,
                        threshold_type TEXT DEFAULT 'monthly',
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system',
                        notification_channels TEXT DEFAULT '["email"]',
                        last_triggered TIMESTAMP NULL,
                        trigger_count INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Create alert triggers table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alert_triggers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id INTEGER NOT NULL,
                        cluster_id TEXT NOT NULL,
                        triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        trigger_reason TEXT NOT NULL,
                        current_cost REAL NOT NULL,
                        threshold_amount REAL NOT NULL,
                        threshold_exceeded_by REAL NOT NULL,
                        notification_sent BOOLEAN DEFAULT 0,
                        notification_channels TEXT DEFAULT '[]',
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (alert_id) REFERENCES alerts (id)
                    )
                ''')
                
                # Create alert configurations table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alert_configurations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_key TEXT UNIQUE NOT NULL,
                        config_value TEXT NOT NULL,
                        config_type TEXT DEFAULT 'string',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by TEXT DEFAULT 'system'
                    )
                ''')
                
                # Create indexes for performance
                indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_alerts_cluster_id ON alerts(cluster_id)',
                    'CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)',
                    'CREATE INDEX IF NOT EXISTS idx_alerts_subscription ON alerts(subscription_id)',
                    'CREATE INDEX IF NOT EXISTS idx_triggers_alert_id ON alert_triggers(alert_id)',
                    'CREATE INDEX IF NOT EXISTS idx_triggers_cluster_id ON alert_triggers(cluster_id)',
                    'CREATE INDEX IF NOT EXISTS idx_triggers_triggered_at ON alert_triggers(triggered_at)'
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(index_sql)
                    except sqlite3.OperationalError:
                        pass  # Index might already exist
                
                conn.commit()
                self.logger.info("✅ Alerts database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"❌ Alerts database initialization failed: {e}")
            raise

    def create_alert(self, alert_data: Dict) -> int:
        """Create a new alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO alerts 
                    (name, description, cluster_id, cluster_name, resource_group, 
                     subscription_id, subscription_name, alert_type, threshold_amount, 
                     threshold_type, status, created_by, notification_channels, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_data['name'],
                    alert_data.get('description', ''),
                    alert_data['cluster_id'],
                    alert_data['cluster_name'],
                    alert_data['resource_group'],
                    alert_data.get('subscription_id'),
                    alert_data.get('subscription_name'),
                    alert_data.get('alert_type', 'cost_threshold'),
                    alert_data['threshold_amount'],
                    alert_data.get('threshold_type', 'monthly'),
                    alert_data.get('status', 'active'),
                    alert_data.get('created_by', 'system'),
                    json.dumps(alert_data.get('notification_channels', ['email'])),
                    json.dumps(alert_data.get('metadata', {}))
                ))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Created alert: {alert_id} - {alert_data['name']}")
                return alert_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create alert: {e}")
            raise

    def get_alert(self, alert_id: int) -> Optional[Dict]:
        """Get a specific alert by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM alerts WHERE id = ?
                ''', (alert_id,))
                
                row = cursor.fetchone()
                if row:
                    alert = dict(row)
                    alert['notification_channels'] = json.loads(alert.get('notification_channels', '[]'))
                    alert['metadata'] = json.loads(alert.get('metadata', '{}'))
                    return alert
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get alert {alert_id}: {e}")
            return None

    def get_alerts(self, cluster_id: Optional[str] = None, 
                   status: Optional[str] = None,
                   subscription_id: Optional[str] = None) -> List[Dict]:
        """Get alerts with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = []
                params = []
                
                if cluster_id:
                    where_clauses.append("cluster_id = ?")
                    params.append(cluster_id)
                
                if status:
                    where_clauses.append("status = ?")
                    params.append(status)
                
                if subscription_id:
                    where_clauses.append("subscription_id = ?")
                    params.append(subscription_id)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                cursor = conn.execute(f'''
                    SELECT * FROM alerts
                    {where_sql}
                    ORDER BY created_at DESC
                ''', params)
                
                alerts = []
                for row in cursor.fetchall():
                    alert = dict(row)
                    alert['notification_channels'] = json.loads(alert.get('notification_channels', '[]'))
                    alert['metadata'] = json.loads(alert.get('metadata', '{}'))
                    alerts.append(alert)
                
                return alerts
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get alerts: {e}")
            return []

    def update_alert(self, alert_id: int, updates: Dict) -> bool:
        """Update an existing alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                
                # Handle specific fields
                for key, value in updates.items():
                    if key in ['name', 'description', 'threshold_amount', 'threshold_type', 'status', 'created_by']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                    elif key == 'notification_channels':
                        set_clauses.append("notification_channels = ?")
                        values.append(json.dumps(value))
                    elif key == 'metadata':
                        set_clauses.append("metadata = ?")
                        values.append(json.dumps(value))
                
                if set_clauses:
                    # Always update the updated_at timestamp
                    set_clauses.append("updated_at = ?")
                    values.append(datetime.now().isoformat())
                    
                    values.append(alert_id)
                    query = f"UPDATE alerts SET {', '.join(set_clauses)} WHERE id = ?"
                    conn.execute(query, values)
                    conn.commit()
                    
                    self.logger.info(f"✅ Updated alert {alert_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update alert {alert_id}: {e}")
            return False

    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert and its triggers"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete triggers first
                conn.execute('DELETE FROM alert_triggers WHERE alert_id = ?', (alert_id,))
                
                # Delete alert
                cursor = conn.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Deleted alert {alert_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Alert {alert_id} not found")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to delete alert {alert_id}: {e}")
            return False

    def record_alert_trigger(self, trigger_data: Dict) -> int:
        """Record an alert trigger event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO alert_triggers 
                    (alert_id, cluster_id, trigger_reason, current_cost, threshold_amount, 
                     threshold_exceeded_by, notification_sent, notification_channels, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trigger_data['alert_id'],
                    trigger_data['cluster_id'],
                    trigger_data['trigger_reason'],
                    trigger_data['current_cost'],
                    trigger_data['threshold_amount'],
                    trigger_data['threshold_exceeded_by'],
                    trigger_data.get('notification_sent', False),
                    json.dumps(trigger_data.get('notification_channels', [])),
                    json.dumps(trigger_data.get('metadata', {}))
                ))
                
                trigger_id = cursor.lastrowid
                
                # Update alert's last triggered and trigger count
                conn.execute('''
                    UPDATE alerts 
                    SET last_triggered = ?, trigger_count = trigger_count + 1
                    WHERE id = ?
                ''', (datetime.now().isoformat(), trigger_data['alert_id']))
                
                conn.commit()
                
                self.logger.info(f"✅ Recorded alert trigger: {trigger_id}")
                return trigger_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to record alert trigger: {e}")
            return 0

    def get_triggers(self, alert_id: Optional[int] = None, 
                     cluster_id: Optional[str] = None,
                     limit: int = 50) -> List[Dict]:
        """Get alert triggers with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = []
                params = []
                
                if alert_id:
                    where_clauses.append("alert_id = ?")
                    params.append(alert_id)
                
                if cluster_id:
                    where_clauses.append("cluster_id = ?")
                    params.append(cluster_id)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                cursor = conn.execute(f'''
                    SELECT t.*, a.name as alert_name
                    FROM alert_triggers t
                    LEFT JOIN alerts a ON t.alert_id = a.id
                    {where_sql}
                    ORDER BY t.triggered_at DESC
                    LIMIT ?
                ''', params + [limit])
                
                triggers = []
                for row in cursor.fetchall():
                    trigger = dict(row)
                    trigger['notification_channels'] = json.loads(trigger.get('notification_channels', '[]'))
                    trigger['metadata'] = json.loads(trigger.get('metadata', '{}'))
                    triggers.append(trigger)
                
                return triggers
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get triggers: {e}")
            return []

    def get_alert_statistics(self) -> Dict:
        """Get comprehensive alert statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Basic alert counts
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_alerts,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_alerts,
                        SUM(CASE WHEN status = 'paused' THEN 1 ELSE 0 END) as paused_alerts,
                        SUM(trigger_count) as total_triggers
                    FROM alerts
                ''')
                
                stats = dict(cursor.fetchone())
                
                # Alerts by type
                cursor = conn.execute('''
                    SELECT alert_type, COUNT(*) as count
                    FROM alerts
                    GROUP BY alert_type
                ''')
                
                stats['by_type'] = {row['alert_type']: row['count'] for row in cursor.fetchall()}
                
                # Recent triggers (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor = conn.execute('''
                    SELECT COUNT(*) as recent_triggers
                    FROM alert_triggers
                    WHERE triggered_at > ?
                ''', (week_ago,))
                
                stats['recent_triggers'] = cursor.fetchone()['recent_triggers']
                
                # Top triggered alerts
                cursor = conn.execute('''
                    SELECT a.id, a.name, a.trigger_count
                    FROM alerts a
                    WHERE a.trigger_count > 0
                    ORDER BY a.trigger_count DESC
                    LIMIT 5
                ''')
                
                stats['top_triggered'] = [dict(row) for row in cursor.fetchall()]
                
                stats['last_updated'] = datetime.now().isoformat()
                
                return stats
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get alert statistics: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old trigger data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM alert_triggers 
                    WHERE triggered_at < ?
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"🧹 Cleaned up {cursor.rowcount} old alert triggers")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup old alert data: {e}")

    def get_configuration(self, config_key: str) -> Optional[Any]:
        """Get alert configuration value"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT config_value, config_type 
                    FROM alert_configurations 
                    WHERE config_key = ?
                ''', (config_key,))
                
                row = cursor.fetchone()
                if row:
                    value = row['config_value']
                    config_type = row['config_type']
                    
                    # Convert based on type
                    if config_type == 'json':
                        return json.loads(value)
                    elif config_type == 'int':
                        return int(value)
                    elif config_type == 'float':
                        return float(value)
                    elif config_type == 'bool':
                        return value.lower() == 'true'
                    else:
                        return value
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get configuration {config_key}: {e}")
            return None

    def set_configuration(self, config_key: str, config_value: Any, config_type: str = 'string') -> bool:
        """Set alert configuration value"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Convert value to string for storage
                if config_type == 'json':
                    value_str = json.dumps(config_value)
                else:
                    value_str = str(config_value)
                
                conn.execute('''
                    INSERT OR REPLACE INTO alert_configurations
                    (config_key, config_value, config_type, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (config_key, value_str, config_type, datetime.now().isoformat()))
                
                conn.commit()
                
                self.logger.info(f"✅ Set configuration {config_key} = {config_value}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to set configuration {config_key}: {e}")
            return False

    def check_cluster_alerts(self, cluster_id: str, current_cost: float) -> List[Dict]:
        """Check if any alerts should be triggered for a cluster"""
        try:
            # Get active alerts for this cluster
            alerts = self.get_alerts(cluster_id=cluster_id, status='active')
            
            triggered_alerts = []
            
            for alert in alerts:
                threshold = alert['threshold_amount']
                
                if current_cost >= threshold:
                    # Calculate exceeded amount
                    exceeded_by = current_cost - threshold
                    
                    # Record the trigger
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
                            'percentage_over': (exceeded_by / threshold) * 100
                        }
                    }
                    
                    trigger_id = self.record_alert_trigger(trigger_data)
                    
                    if trigger_id:
                        triggered_alerts.append({
                            'alert': alert,
                            'trigger_id': trigger_id,
                            'current_cost': current_cost,
                            'threshold_exceeded_by': exceeded_by
                        })
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"❌ Failed to check cluster alerts: {e}")
            return []

    def update_trigger_notification_status(self, trigger_id: int, 
                                         notification_sent: bool,
                                         notification_channels: List[str]) -> bool:
        """Update trigger notification status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE alert_triggers 
                    SET notification_sent = ?, notification_channels = ?
                    WHERE id = ?
                ''', (notification_sent, json.dumps(notification_channels), trigger_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update trigger notification status: {e}")
            return False

# Create a global instance
alerts_db = AlertsDatabase()