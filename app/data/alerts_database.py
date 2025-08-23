#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

# Enhanced alerts_database.py - Fixed frequency handling and improved notification system

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
    """Enhanced database manager for alerts system with proper frequency handling"""
    
    def __init__(self, db_path='app/data/database/alerts.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.init_database()
        
        # Clean up any stale data on startup
        self.cleanup_old_data()

    def init_database(self):
        """Initialize SQLite database with enhanced frequency support"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Create enhanced alerts table with proper frequency handling
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
                        
                        -- 🆕 ENHANCED FREQUENCY FIELDS
                        notification_frequency TEXT DEFAULT 'daily',
                        frequency_interval INTEGER DEFAULT 1,
                        frequency_unit TEXT DEFAULT 'days',
                        frequency_at_time TEXT DEFAULT '09:00',
                        max_notifications_per_day INTEGER DEFAULT 3,
                        cooldown_period_hours INTEGER DEFAULT 4,
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system',
                        notification_channels TEXT DEFAULT '["email", "inapp"]',
                        last_triggered TIMESTAMP NULL,
                        last_notification_sent TIMESTAMP NULL,
                        trigger_count INTEGER DEFAULT 0,
                        notification_count INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Add frequency columns to existing tables if they don't exist
                self._add_frequency_columns_if_missing(conn)
                
                # Create alert triggers table with frequency tracking
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
                        
                        -- 🆕 FREQUENCY TRACKING
                        notification_frequency TEXT DEFAULT 'immediate',
                        next_notification_time TIMESTAMP NULL,
                        notification_suppressed BOOLEAN DEFAULT 0,
                        suppression_reason TEXT DEFAULT '',
                        
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (alert_id) REFERENCES alerts (id)
                    )
                ''')
                
                # Enhanced notification frequency configurations table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS notification_frequency_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        frequency_type TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        interval_value INTEGER NOT NULL,
                        interval_unit TEXT NOT NULL,
                        max_per_day INTEGER DEFAULT NULL,
                        cooldown_hours INTEGER DEFAULT 0,
                        recommended_for TEXT DEFAULT '',
                        is_active BOOLEAN DEFAULT 1,
                        sort_order INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 🆕 IN-APP NOTIFICATIONS with frequency tracking
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS in_app_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        type TEXT DEFAULT 'info',
                        cluster_id TEXT,
                        alert_id INTEGER,
                        trigger_id INTEGER,
                        
                        -- 🆕 FREQUENCY FIELDS
                        frequency_type TEXT DEFAULT 'immediate',
                        scheduled_for TIMESTAMP NULL,
                        next_occurrence TIMESTAMP NULL,
                        
                        timestamp TEXT NOT NULL,
                        read BOOLEAN DEFAULT FALSE,
                        dismissed BOOLEAN DEFAULT FALSE,
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (alert_id) REFERENCES alerts (id),
                        FOREIGN KEY (trigger_id) REFERENCES alert_triggers (id)
                    )
                ''')
                
                # Insert default frequency configurations
                self._insert_default_frequency_configs(conn)
                
                # Create indexes for performance
                indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_alerts_cluster_id ON alerts(cluster_id)',
                    'CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)',
                    'CREATE INDEX IF NOT EXISTS idx_alerts_frequency ON alerts(notification_frequency)',
                    'CREATE INDEX IF NOT EXISTS idx_triggers_alert_id ON alert_triggers(alert_id)',
                    'CREATE INDEX IF NOT EXISTS idx_triggers_frequency ON alert_triggers(notification_frequency)',
                    'CREATE INDEX IF NOT EXISTS idx_triggers_next_notification ON alert_triggers(next_notification_time)',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_frequency ON in_app_notifications(frequency_type)',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_scheduled ON in_app_notifications(scheduled_for)'
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(index_sql)
                    except sqlite3.OperationalError:
                        pass  # Index might already exist
                
                conn.commit()
                self.logger.info("✅ Enhanced alerts database initialized with frequency support")
                
        except Exception as e:
            self.logger.error(f"❌ Enhanced alerts database initialization failed: {e}")
            raise

    def _add_frequency_columns_if_missing(self, conn):
        """Add frequency columns to existing alerts table if they don't exist"""
        try:
            # Get existing columns
            cursor = conn.execute("PRAGMA table_info(alerts)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            # Define new frequency columns
            new_columns = [
                ('notification_frequency', 'TEXT DEFAULT "daily"'),
                ('frequency_interval', 'INTEGER DEFAULT 1'),
                ('frequency_unit', 'TEXT DEFAULT "days"'),
                ('frequency_at_time', 'TEXT DEFAULT "09:00"'),
                ('max_notifications_per_day', 'INTEGER DEFAULT 3'),
                ('cooldown_period_hours', 'INTEGER DEFAULT 4'),
                ('last_notification_sent', 'TIMESTAMP NULL'),
                ('notification_count', 'INTEGER DEFAULT 0')
            ]
            
            # Add missing columns
            for column_name, column_def in new_columns:
                if column_name not in existing_columns:
                    try:
                        conn.execute(f'ALTER TABLE alerts ADD COLUMN {column_name} {column_def}')
                        self.logger.info(f"✅ Added frequency column: {column_name}")
                    except sqlite3.OperationalError as e:
                        self.logger.warning(f"⚠️ Could not add column {column_name}: {e}")
            
            # Update existing records with default frequency if NULL
            conn.execute('''
                UPDATE alerts 
                SET notification_frequency = 'daily' 
                WHERE notification_frequency IS NULL OR notification_frequency = ''
            ''')
            
            conn.execute('''
                UPDATE alerts 
                SET frequency_interval = 1 
                WHERE frequency_interval IS NULL
            ''')
            
            conn.execute('''
                UPDATE alerts 
                SET frequency_unit = 'days' 
                WHERE frequency_unit IS NULL OR frequency_unit = ''
            ''')
            
        except Exception as e:
            self.logger.error(f"❌ Error adding frequency columns: {e}")

    def _insert_default_frequency_configs(self, conn):
        """Insert default frequency configuration options"""
        try:
            # Check if configs already exist
            cursor = conn.execute('SELECT COUNT(*) FROM notification_frequency_configs')
            if cursor.fetchone()[0] > 0:
                return  # Already populated
            
            default_configs = [
                {
                    'frequency_type': 'immediate',
                    'display_name': 'Immediate',
                    'description': 'Send notification as soon as alert is triggered',
                    'interval_value': 0,
                    'interval_unit': 'minutes',
                    'max_per_day': None,
                    'cooldown_hours': 0,
                    'recommended_for': 'Critical alerts, Budget overruns',
                    'sort_order': 1
                },
                {
                    'frequency_type': 'hourly',
                    'display_name': 'Hourly',
                    'description': 'Send notifications once per hour when triggered',
                    'interval_value': 1,
                    'interval_unit': 'hours',
                    'max_per_day': 24,
                    'cooldown_hours': 1,
                    'recommended_for': 'High-frequency monitoring',
                    'sort_order': 2
                },
                {
                    'frequency_type': 'daily',
                    'display_name': 'Daily',
                    'description': 'Send one notification per day at 9:00 AM',
                    'interval_value': 1,
                    'interval_unit': 'days',
                    'max_per_day': 1,
                    'cooldown_hours': 24,
                    'recommended_for': 'Regular cost monitoring, Budget alerts',
                    'sort_order': 3
                },
                {
                    'frequency_type': 'weekly',
                    'display_name': 'Weekly',
                    'description': 'Send notifications once per week on Mondays',
                    'interval_value': 7,
                    'interval_unit': 'days',
                    'max_per_day': 1,
                    'cooldown_hours': 168,
                    'recommended_for': 'Summary reports, Weekly cost reviews',
                    'sort_order': 4
                },
                {
                    'frequency_type': 'monthly',
                    'display_name': 'Monthly',
                    'description': 'Send notifications once per month on the 1st',
                    'interval_value': 30,
                    'interval_unit': 'days',
                    'max_per_day': 1,
                    'cooldown_hours': 720,
                    'recommended_for': 'Monthly budget reviews, Long-term trends',
                    'sort_order': 5
                },
                {
                    'frequency_type': 'custom_4h',
                    'display_name': 'Every 4 Hours',
                    'description': 'Send notifications every 4 hours during business hours',
                    'interval_value': 4,
                    'interval_unit': 'hours',
                    'max_per_day': 6,
                    'cooldown_hours': 4,
                    'recommended_for': 'Active monitoring, Development environments',
                    'sort_order': 6
                }
            ]
            
            for config in default_configs:
                conn.execute('''
                    INSERT INTO notification_frequency_configs 
                    (frequency_type, display_name, description, interval_value, interval_unit, 
                     max_per_day, cooldown_hours, recommended_for, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    config['frequency_type'],
                    config['display_name'],
                    config['description'],
                    config['interval_value'],
                    config['interval_unit'],
                    config['max_per_day'],
                    config['cooldown_hours'],
                    config['recommended_for'],
                    config['sort_order']
                ))
            
            self.logger.info("✅ Default frequency configurations inserted")
            
        except Exception as e:
            self.logger.error(f"❌ Error inserting default frequency configs: {e}")

    def get_frequency_configurations(self) -> List[Dict]:
        """Get all available notification frequency configurations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM notification_frequency_configs 
                    WHERE is_active = 1 
                    ORDER BY sort_order
                ''')
                
                configs = []
                for row in cursor.fetchall():
                    configs.append(dict(row))
                
                return configs
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get frequency configurations: {e}")
            return []

    def create_alert(self, alert_data: Dict) -> int:
        """Create a new alert with enhanced frequency handling"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Set frequency defaults if not provided
                frequency = alert_data.get('notification_frequency', 'daily')
                frequency_interval = alert_data.get('frequency_interval', 1)
                frequency_unit = alert_data.get('frequency_unit', 'days')
                frequency_at_time = alert_data.get('frequency_at_time', '09:00')
                max_notifications_per_day = alert_data.get('max_notifications_per_day', 3)
                cooldown_period_hours = alert_data.get('cooldown_period_hours', 4)
                
                # Validate frequency settings
                if frequency not in ['immediate', 'hourly', 'daily', 'weekly', 'monthly', 'custom_4h']:
                    frequency = 'daily'
                
                cursor = conn.execute('''
                    INSERT INTO alerts 
                    (name, description, cluster_id, cluster_name, resource_group, 
                     subscription_id, subscription_name, alert_type, threshold_amount, 
                     threshold_type, status, created_by, notification_channels, 
                     notification_frequency, frequency_interval, frequency_unit, 
                     frequency_at_time, max_notifications_per_day, cooldown_period_hours, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(alert_data.get('notification_channels', ['email', 'inapp'])),
                    frequency,
                    frequency_interval,
                    frequency_unit,
                    frequency_at_time,
                    max_notifications_per_day,
                    cooldown_period_hours,
                    json.dumps(alert_data.get('metadata', {}))
                ))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Created alert with frequency '{frequency}': {alert_id} - {alert_data['name']}")
                return alert_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create alert: {e}")
            raise

    def get_alert(self, alert_id: int) -> Optional[Dict]:
        """Get a specific alert by ID with frequency information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT a.*, 
                           nfc.display_name as frequency_display_name,
                           nfc.description as frequency_description
                    FROM alerts a
                    LEFT JOIN notification_frequency_configs nfc ON a.notification_frequency = nfc.frequency_type
                    WHERE a.id = ?
                ''', (alert_id,))
                
                row = cursor.fetchone()
                if row:
                    alert = dict(row)
                    alert['notification_channels'] = json.loads(alert.get('notification_channels', '[]'))
                    alert['metadata'] = json.loads(alert.get('metadata', '{}'))
                    
                    # Ensure frequency is never undefined
                    if not alert.get('notification_frequency'):
                        alert['notification_frequency'] = 'daily'
                        alert['frequency_display_name'] = 'Daily'
                    
                    return alert
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get alert {alert_id}: {e}")
            return None

    def get_alerts(self, cluster_id: Optional[str] = None, 
                   status: Optional[str] = None,
                   subscription_id: Optional[str] = None) -> List[Dict]:
        """Get alerts with frequency information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = []
                params = []
                
                if cluster_id:
                    where_clauses.append("a.cluster_id = ?")
                    params.append(cluster_id)
                
                if status:
                    where_clauses.append("a.status = ?")
                    params.append(status)
                
                if subscription_id:
                    where_clauses.append("a.subscription_id = ?")
                    params.append(subscription_id)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                cursor = conn.execute(f'''
                    SELECT a.*, 
                           nfc.display_name as frequency_display_name,
                           nfc.description as frequency_description,
                           nfc.recommended_for as frequency_recommended_for
                    FROM alerts a
                    LEFT JOIN notification_frequency_configs nfc ON a.notification_frequency = nfc.frequency_type
                    {where_sql}
                    ORDER BY a.created_at DESC
                ''', params)
                
                alerts = []
                for row in cursor.fetchall():
                    alert = dict(row)
                    alert['notification_channels'] = json.loads(alert.get('notification_channels', '[]'))
                    alert['metadata'] = json.loads(alert.get('metadata', '{}'))
                    
                    # Ensure frequency is never undefined
                    if not alert.get('notification_frequency'):
                        alert['notification_frequency'] = 'daily'
                        alert['frequency_display_name'] = 'Daily'
                    
                    # Calculate next notification time based on frequency
                    alert['next_notification_time'] = self._calculate_next_notification_time(alert)
                    
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
                # Delete related notifications first
                conn.execute('DELETE FROM in_app_notifications WHERE alert_id = ?', (alert_id,))
                
                # Delete triggers
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
                
                # 🆕 IN-APP NOTIFICATIONS STATISTICS
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_notifications,
                        SUM(CASE WHEN read = 0 THEN 1 ELSE 0 END) as unread_notifications,
                        SUM(CASE WHEN dismissed = 0 THEN 1 ELSE 0 END) as active_notifications
                    FROM in_app_notifications
                ''')
                
                notification_stats = dict(cursor.fetchone())
                stats.update(notification_stats)
                
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
        """Clean up old trigger data and notifications"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                # Clean up old triggers
                cursor = conn.execute('''
                    DELETE FROM alert_triggers 
                    WHERE triggered_at < ?
                ''', (cutoff_date.isoformat(),))
                
                triggers_deleted = cursor.rowcount
                
                # 🆕 CLEAN UP OLD NOTIFICATIONS (keep dismissed ones for shorter period)
                notification_cutoff = datetime.now() - timedelta(days=30)  # Keep for 30 days
                cursor = conn.execute('''
                    DELETE FROM in_app_notifications 
                    WHERE created_at < ? AND dismissed = 1
                ''', (notification_cutoff.isoformat(),))
                
                notifications_deleted = cursor.rowcount
                
                conn.commit()
                
                if triggers_deleted > 0:
                    self.logger.info(f"🧹 Cleaned up {triggers_deleted} old alert triggers")
                
                if notifications_deleted > 0:
                    self.logger.info(f"🧹 Cleaned up {notifications_deleted} old notifications")
                
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

    # 🆕 ===== IN-APP NOTIFICATIONS METHODS =====

    def create_in_app_notification(self, notification_data: Dict) -> Optional[str]:
        """Create in-app notification"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO in_app_notifications 
                    (title, message, type, cluster_id, alert_id, trigger_id, timestamp, read, dismissed, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_data['title'],
                    notification_data['message'],
                    notification_data.get('type', 'info'),
                    notification_data.get('cluster_id'),
                    notification_data.get('alert_id'),
                    notification_data.get('trigger_id'),
                    notification_data['timestamp'],
                    notification_data.get('read', False),
                    notification_data.get('dismissed', False),
                    json.dumps(notification_data.get('metadata', {}))
                ))
                
                conn.commit()
                notification_id = cursor.lastrowid
                
                self.logger.info(f"📱 Created in-app notification: {notification_id}")
                return str(notification_id)
                
        except Exception as e:
            self.logger.error(f"❌ Error creating in-app notification: {e}")
            return None

    def get_in_app_notifications(self, cluster_id: Optional[str] = None, 
                               unread_only: bool = False, 
                               limit: int = 50) -> List[Dict]:
        """Get in-app notifications"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = ['dismissed = 0']  # Don't show dismissed notifications
                params = []
                
                if cluster_id:
                    where_clauses.append('cluster_id = ?')
                    params.append(cluster_id)
                
                if unread_only:
                    where_clauses.append('read = 0')
                
                where_sql = ' WHERE ' + ' AND '.join(where_clauses)
                
                cursor = conn.execute(f'''
                    SELECT id, title, message, type, cluster_id, alert_id, trigger_id, 
                           timestamp, read, dismissed, metadata, created_at
                    FROM in_app_notifications
                    {where_sql}
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', params + [limit])
                
                notifications = []
                for row in cursor.fetchall():
                    notification = dict(row)
                    notification['metadata'] = json.loads(notification.get('metadata', '{}'))
                    notifications.append(notification)
                
                return notifications
                
        except Exception as e:
            self.logger.error(f"❌ Error getting in-app notifications: {e}")
            return []

    def update_notification_status(self, notification_ids: List[str], action: str) -> bool:
        """Update notification status (mark as read/dismissed)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if action == 'mark_read':
                    update_sql = f'''
                        UPDATE in_app_notifications 
                        SET read = 1, updated_at = ? 
                        WHERE id IN ({','.join(['?' for _ in notification_ids])})
                    '''
                    params = [datetime.now().isoformat()] + notification_ids
                    
                elif action == 'dismiss':
                    update_sql = f'''
                        UPDATE in_app_notifications 
                        SET dismissed = 1, updated_at = ? 
                        WHERE id IN ({','.join(['?' for _ in notification_ids])})
                    '''
                    params = [datetime.now().isoformat()] + notification_ids
                    
                else:
                    return False
                
                cursor = conn.execute(update_sql, params)
                conn.commit()
                
                self.logger.info(f"📱 Updated {cursor.rowcount} notifications: {action}")
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"❌ Error updating notification status: {e}")
            return False

    def get_unread_notifications_count(self, cluster_id: Optional[str] = None) -> int:
        """Get count of unread notifications"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                where_clauses = ['read = 0', 'dismissed = 0']
                params = []
                
                if cluster_id:
                    where_clauses.append('cluster_id = ?')
                    params.append(cluster_id)
                
                where_sql = ' WHERE ' + ' AND '.join(where_clauses)
                
                cursor = conn.execute(f'''
                    SELECT COUNT(*) as count 
                    FROM in_app_notifications 
                    {where_sql}
                ''', params)
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"❌ Error getting unread notifications count: {e}")
            return 0

    def create_notification_for_trigger(self, trigger_id: int, alert: Dict, 
                                      current_cost: float, exceeded_by: float) -> Optional[str]:
        """Create in-app notification for an alert trigger"""
        try:
            percentage_over = (exceeded_by / alert['threshold_amount']) * 100
            
            notification_data = {
                'title': f"🚨 Cost Alert: {alert['name']}",
                'message': f"Cluster {alert['cluster_name']} cost ${current_cost:,.2f} exceeded threshold ${alert['threshold_amount']:,.2f} by ${exceeded_by:,.2f} ({percentage_over:.1f}% over)",
                'type': 'warning',
                'cluster_id': alert['cluster_id'],
                'alert_id': alert['id'],
                'trigger_id': trigger_id,
                'timestamp': datetime.now().isoformat(),
                'read': False,
                'dismissed': False,
                'metadata': {
                    'current_cost': current_cost,
                    'threshold_amount': alert['threshold_amount'],
                    'exceeded_by': exceeded_by,
                    'percentage_over': percentage_over,
                    'resource_group': alert['resource_group'],
                    'alert_type': alert['alert_type']
                }
            }
            
            return self.create_in_app_notification(notification_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating notification for trigger: {e}")
            return None

    def clear_old_notifications(self, days_to_keep: int = 30):
        """Clear old notifications (separate from general cleanup)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM in_app_notifications 
                    WHERE created_at < ? AND (dismissed = 1 OR read = 1)
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"🧹 Cleared {cursor.rowcount} old notifications")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to clear old notifications: {e}")

    def _calculate_next_notification_time(self, alert: Dict) -> Optional[str]:
        """Calculate when the next notification should be sent"""
        try:
            frequency = alert.get('notification_frequency', 'daily')
            last_notification = alert.get('last_notification_sent')
            
            if frequency == 'immediate':
                return None  # No scheduled time for immediate notifications
            
            if not last_notification:
                return datetime.now().isoformat()  # Next notification can be immediate
            
            last_time = datetime.fromisoformat(last_notification.replace('Z', '+00:00'))
            
            # Calculate based on frequency
            if frequency == 'hourly':
                next_time = last_time + timedelta(hours=1)
            elif frequency == 'daily':
                next_time = last_time + timedelta(days=1)
                # Set to specific time if configured
                time_str = alert.get('frequency_at_time', '09:00')
                hour, minute = map(int, time_str.split(':'))
                next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif frequency == 'weekly':
                next_time = last_time + timedelta(weeks=1)
            elif frequency == 'monthly':
                next_time = last_time + timedelta(days=30)
            elif frequency == 'custom_4h':
                next_time = last_time + timedelta(hours=4)
            else:
                next_time = last_time + timedelta(days=1)  # Default to daily
            
            return next_time.isoformat()
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating next notification time: {e}")
            return None

    def should_send_notification(self, alert: Dict) -> bool:
        """Check if a notification should be sent based on frequency rules"""
        try:
            frequency = alert.get('notification_frequency', 'daily')
            
            if frequency == 'immediate':
                return True
            
            last_notification = alert.get('last_notification_sent')
            if not last_notification:
                return True  # First notification
            
            last_time = datetime.fromisoformat(last_notification.replace('Z', '+00:00'))
            now = datetime.now()
            
            # Check cooldown period
            cooldown_hours = alert.get('cooldown_period_hours', 4)
            if (now - last_time).total_seconds() < cooldown_hours * 3600:
                return False
            
            # Check daily limit
            max_per_day = alert.get('max_notifications_per_day', 3)
            if max_per_day and max_per_day > 0:
                # Count notifications sent today
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                notifications_today = self._count_notifications_since(alert['id'], today_start.isoformat())
                
                if notifications_today >= max_per_day:
                    return False
            
            # Check frequency interval
            interval = alert.get('frequency_interval', 1)
            unit = alert.get('frequency_unit', 'days')
            
            if unit == 'minutes':
                min_interval = timedelta(minutes=interval)
            elif unit == 'hours':
                min_interval = timedelta(hours=interval)
            elif unit == 'days':
                min_interval = timedelta(days=interval)
            else:
                min_interval = timedelta(days=1)  # Default
            
            return (now - last_time) >= min_interval
            
        except Exception as e:
            self.logger.error(f"❌ Error checking notification frequency: {e}")
            return True  # Default to allowing notification

    def _count_notifications_since(self, alert_id: int, since_time: str) -> int:
        """Count notifications sent for an alert since a specific time"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM alert_triggers 
                    WHERE alert_id = ? AND triggered_at >= ? AND notification_sent = 1
                ''', (alert_id, since_time))
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"❌ Error counting notifications: {e}")
            return 0

    def update_notification_sent_time(self, alert_id: int):
        """Update the last notification sent time for an alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE alerts 
                    SET last_notification_sent = ?, notification_count = notification_count + 1
                    WHERE id = ?
                ''', (datetime.now().isoformat(), alert_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Error updating notification sent time: {e}")

# Create a global instance
alerts_db = AlertsDatabase()