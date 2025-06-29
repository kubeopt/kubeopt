# cluster_database.py - Complete Enhanced Cluster Manager with Multi-Subscription Support

import sqlite3
import json
import logging
from datetime import datetime, timedelta
import traceback
from typing import Any, Dict, List, Optional
import os

# Set up logger
logger = logging.getLogger(__name__)

def migrate_database_schema(db_path: str = '../data/database/clusters.db'):
    """Migrate database schema to include analysis_data column and other required columns"""
    logger = logging.getLogger(__name__)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check current schema
            cursor.execute("PRAGMA table_info(clusters)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Define required columns
            required_columns = {
                'analysis_data': 'TEXT',
                'last_confidence': 'REAL DEFAULT 0'
            }
            
            # Add missing columns
            columns_added = 0
            for column_name, column_def in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE clusters ADD COLUMN {column_name} {column_def}"
                        cursor.execute(alter_sql)
                        logger.info(f"✅ Added column: {column_name}")
                        columns_added += 1
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e).lower():
                            logger.error(f"❌ Failed to add column {column_name}: {e}")
            
            conn.commit()
            
            if columns_added > 0:
                logger.info(f"✅ Database migration completed: {columns_added} columns added")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False

def migrate_database_for_multi_subscription(db_path: str = '../data/database/clusters.db'):
    """Comprehensive database migration for multi-subscription support"""
    logger = logging.getLogger(__name__)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check current schema
            cursor.execute("PRAGMA table_info(clusters)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Define all required columns for multi-subscription support
            required_columns = {
                'subscription_id': 'TEXT DEFAULT NULL',
                'subscription_name': 'TEXT DEFAULT NULL',
                'analysis_data': 'TEXT',
                'last_confidence': 'REAL DEFAULT 0',
                'analysis_status': 'TEXT DEFAULT "pending"',
                'analysis_progress': 'INTEGER DEFAULT 0',
                'analysis_message': 'TEXT DEFAULT ""',
                'analysis_started_at': 'TIMESTAMP NULL',
                'auto_analyze_enabled': 'BOOLEAN DEFAULT 1',
                'subscription_context_verified': 'BOOLEAN DEFAULT 0',
                'subscription_last_validated': 'TIMESTAMP NULL'
            }
            
            # Add missing columns
            columns_added = 0
            for column_name, column_def in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE clusters ADD COLUMN {column_name} {column_def}"
                        cursor.execute(alter_sql)
                        logger.info(f"✅ Added column: {column_name}")
                        columns_added += 1
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e).lower():
                            logger.error(f"❌ Failed to add column {column_name}: {e}")
            
            # Create subscription management table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    subscription_name TEXT NOT NULL,
                    tenant_id TEXT,
                    state TEXT DEFAULT 'Enabled',
                    is_default BOOLEAN DEFAULT 0,
                    last_used TIMESTAMP,
                    last_validated TIMESTAMP,
                    validation_status TEXT DEFAULT 'unknown',
                    cluster_count INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create subscription analysis sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_analysis_sessions (
                    session_id TEXT PRIMARY KEY,
                    cluster_id TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    resource_group TEXT NOT NULL,
                    cluster_name TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'completely_fixed',
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    message TEXT DEFAULT '',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    thread_id INTEGER,
                    subscription_context_set BOOLEAN DEFAULT 0,
                    results_size INTEGER DEFAULT 0,
                    FOREIGN KEY (cluster_id) REFERENCES clusters (id),
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
                )
            ''')
            
            # Create subscription performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
                )
            ''')
            
            # Create indexes for performance
            indexes_to_create = [
                'CREATE INDEX IF NOT EXISTS idx_clusters_subscription_id ON clusters(subscription_id)',
                'CREATE INDEX IF NOT EXISTS idx_clusters_analysis_status ON clusters(analysis_status)',
                'CREATE INDEX IF NOT EXISTS idx_subscription_sessions_cluster ON subscription_analysis_sessions(cluster_id)',
                'CREATE INDEX IF NOT EXISTS idx_subscription_sessions_subscription ON subscription_analysis_sessions(subscription_id)',
                'CREATE INDEX IF NOT EXISTS idx_subscription_sessions_status ON subscription_analysis_sessions(status)',
                'CREATE INDEX IF NOT EXISTS idx_subscription_performance_sub ON subscription_performance(subscription_id)',
                'CREATE INDEX IF NOT EXISTS idx_subscription_performance_metric ON subscription_performance(metric_name)'
            ]
            
            for index_sql in indexes_to_create:
                try:
                    cursor.execute(index_sql)
                except sqlite3.OperationalError:
                    pass  # Index might already exist
            
            conn.commit()
            
            if columns_added > 0:
                logger.info(f"✅ Multi-subscription database migration completed: {columns_added} columns added")
            
            # Verify migration
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            logger.info(f"✅ Database has {table_count} tables after migration")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Multi-subscription database migration failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def serialize_implementation_plan(plan_data):
    """Serialize implementation plan while preserving all ML/algorithmic data"""
    import pandas as pd
    from datetime import datetime
    
    def serialize_object(obj):
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: serialize_object(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [serialize_object(item) for item in obj]
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle complex objects like cluster_dna, dynamic_strategy
            serialized = {'__class_name__': obj.__class__.__name__}
            for key, value in obj.__dict__.items():
                serialized[key] = serialize_object(value)
            return serialized
        elif hasattr(obj, 'to_dict'):
            return serialize_object(obj.to_dict())
        else:
            return str(obj)
    
    return serialize_object(plan_data)

def deserialize_implementation_plan(serialized_data):
    """Deserialize implementation plan and reconstruct objects"""
    def deserialize_object(obj):
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            if '__class_name__' in obj:
                # Reconstruct complex object as dict (maintains functionality)
                reconstructed = {}
                for key, value in obj.items():
                    if key != '__class_name__':
                        reconstructed[key] = deserialize_object(value)
                reconstructed['__original_class__'] = obj['__class_name__']
                return reconstructed
            else:
                return {k: deserialize_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [deserialize_object(item) for item in obj]
        else:
            return obj
    
    return deserialize_object(serialized_data)

class EnhancedMultiSubscriptionClusterManager:
    """Complete enhanced cluster manager with comprehensive multi-subscription support"""
    
    def __init__(self, db_path='app/data/database/clusters.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize database with complete schema
        self.init_database()
        
        # Run all migrations
        migrate_database_schema(self.db_path)
        migrate_database_for_multi_subscription(self.db_path)
        
        # Clean up any stale analyses on startup
        self.cleanup_stale_analyses()
        
        # Initialize subscription tracking
        self.initialize_subscription_tracking()

    def init_database(self):
        """Initialize SQLite database with complete multi-subscription schema"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Create main clusters table with ALL required columns
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS clusters (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        resource_group TEXT NOT NULL,
                        environment TEXT DEFAULT 'development',
                        region TEXT DEFAULT 'Unknown',
                        description TEXT DEFAULT '',
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_analyzed TIMESTAMP NULL,
                        last_cost REAL DEFAULT 0,
                        last_savings REAL DEFAULT 0,
                        last_confidence REAL DEFAULT 0,
                        analysis_count INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}',
                        analysis_data TEXT,
                        analysis_status TEXT DEFAULT 'pending',
                        analysis_progress INTEGER DEFAULT 0,
                        analysis_message TEXT DEFAULT '',
                        analysis_started_at TIMESTAMP,
                        auto_analyze_enabled BOOLEAN DEFAULT 1,
                        subscription_id TEXT DEFAULT NULL,
                        subscription_name TEXT DEFAULT NULL,
                        subscription_context_verified BOOLEAN DEFAULT 0,
                        subscription_last_validated TIMESTAMP NULL
                    )
                ''')
                
                # Create analysis results table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cluster_id TEXT NOT NULL,
                        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        results TEXT NOT NULL,
                        total_cost REAL DEFAULT 0,
                        total_savings REAL DEFAULT 0,
                        confidence_level TEXT DEFAULT 'Medium',
                        FOREIGN KEY (cluster_id) REFERENCES clusters (id)
                    )
                ''')
                
                # Create indexes
                conn.execute('CREATE INDEX IF NOT EXISTS idx_cluster_id ON analysis_results(cluster_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date)')
                
                conn.commit()
                self.logger.info("✅ Complete multi-subscription database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise

    def touch_cluster(self, cluster_id: str):
        """Update cluster timestamp to invalidate cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE clusters 
                    SET last_analyzed = ? 
                    WHERE id = ?
                ''', (datetime.now().isoformat(), cluster_id))
                conn.commit()
                self.logger.info(f"✅ Updated timestamp for cluster {cluster_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to touch cluster {cluster_id}: {e}")

    def cleanup_stale_analyses(self, max_age_hours: int = 4):
        """Clean up stale analysis sessions (both general and subscription-specific)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            with sqlite3.connect(self.db_path) as conn:
                # Clean up stale cluster analyses
                cursor = conn.execute('''
                    SELECT id FROM clusters 
                    WHERE analysis_status IN ('running', 'analyzing', 'pending') 
                    AND analysis_started_at IS NOT NULL
                    AND analysis_started_at < ?
                ''', (cutoff_time.isoformat(),))
                
                stale_clusters = [row[0] for row in cursor.fetchall()]
                
                if stale_clusters:
                    # Update stale cluster analyses
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = 'failed',
                            analysis_progress = 0,
                            analysis_message = 'Analysis timed out and was cleaned up'
                        WHERE analysis_status IN ('running', 'analyzing', 'pending') 
                        AND analysis_started_at < ?
                    ''', (cutoff_time.isoformat(),))
                    
                    cleaned_count += len(stale_clusters)
                
                conn.commit()
            
            # Also clean up stale subscription sessions
            subscription_cleaned = self.cleanup_stale_subscription_sessions(max_age_hours)
            cleaned_count += subscription_cleaned
            
            if cleaned_count > 0:
                self.logger.info(f"🧹 Cleaned up {cleaned_count} stale analysis sessions")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up stale analyses: {e}")
            return 0

    def cleanup_stale_subscription_sessions(self, max_age_hours: int = 4):
        """Clean up stale subscription analysis sessions"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                # Find stale sessions
                cursor = conn.execute('''
                    SELECT session_id, cluster_id FROM subscription_analysis_sessions 
                    WHERE status IN ('running', 'pending') 
                    AND started_at < ?
                ''', (cutoff_time.isoformat(),))
                
                stale_sessions = cursor.fetchall()
                
                if stale_sessions:
                    # Update stale sessions
                    conn.execute('''
                        UPDATE subscription_analysis_sessions 
                        SET status = 'failed', 
                            message = 'Session timed out and was cleaned up',
                            completed_at = ?
                        WHERE status IN ('running', 'pending') 
                        AND started_at < ?
                    ''', (datetime.now().isoformat(), cutoff_time.isoformat()))
                    
                    # Also update corresponding clusters
                    for session_id, cluster_id in stale_sessions:
                        conn.execute('''
                            UPDATE clusters 
                            SET analysis_status = 'failed',
                                analysis_progress = 0,
                                analysis_message = 'Analysis session timed out'
                            WHERE id = ?
                        ''', (cluster_id,))
                    
                    conn.commit()
                    
                    self.logger.info(f"🧹 Cleaned up {len(stale_sessions)} stale subscription analysis sessions")
                    return len(stale_sessions)
                
                return 0
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up stale subscription sessions: {e}")
            return 0

    def initialize_subscription_tracking(self):
        """Initialize subscription tracking and discovery"""
        try:
            self.logger.info("🌐 Initializing subscription tracking...")
            
            # Try to import subscription manager, but handle gracefully if not available
            try:
                from app.services.subscription_manager import azure_subscription_manager
                
                # Get all available subscriptions
                subscriptions = azure_subscription_manager.get_available_subscriptions(force_refresh=True)
                
                # Update subscriptions table
                with sqlite3.connect(self.db_path) as conn:
                    for sub in subscriptions:
                        conn.execute('''
                            INSERT OR REPLACE INTO subscriptions 
                            (subscription_id, subscription_name, tenant_id, state, is_default, last_validated, validation_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            sub.subscription_id,
                            sub.subscription_name,
                            sub.tenant_id,
                            sub.state,
                            sub.is_default,
                            datetime.now().isoformat(),
                            'active'
                        ))
                    
                    conn.commit()
                
                self.logger.info(f"✅ Initialized tracking for {len(subscriptions)} subscriptions")
                
            except ImportError:
                self.logger.warning("⚠️ Subscription manager not available, skipping subscription discovery")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize subscription tracking: {e}")
            
            # Auto-detect subscription info for existing clusters
            self.detect_and_update_cluster_subscriptions()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize subscription tracking: {e}")

    def get_clusters_by_subscription(self, subscription_id: str) -> List[Dict]:
        """Get all clusters for a specific subscription (required by api_routes.py)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM clusters 
                    WHERE subscription_id = ? AND status = 'active'
                    ORDER BY created_at DESC
                ''', (subscription_id,))
                
                clusters = []
                for row in cursor.fetchall():
                    cluster = dict(row)
                    cluster['metadata'] = json.loads(cluster.get('metadata', '{}'))
                    clusters.append(cluster)
                
                self.logger.info(f"📊 Found {len(clusters)} clusters in subscription {subscription_id[:8] if subscription_id else 'unknown'}")
                return clusters
                
        except Exception as e:
            self.logger.error(f"❌ Error getting clusters for subscription {subscription_id}: {e}")
            return []

    def get_all_clusters(self) -> List[Dict]:
        """Get all clusters (alias for list_clusters for compatibility)"""
        return self.list_clusters()

    def detect_and_update_cluster_subscriptions(self):
        """Detect and update subscription info for existing clusters"""
        try:
            self.logger.info("🔍 Detecting subscription info for existing clusters...")
            
            # Get all clusters without subscription info
            clusters_to_update = []
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, name, resource_group 
                    FROM clusters 
                    WHERE (subscription_id IS NULL OR subscription_id = '') 
                    AND status = 'active'
                ''')
                clusters_to_update = [dict(row) for row in cursor.fetchall()]
            
            if not clusters_to_update:
                self.logger.info("✅ All clusters already have subscription info")
                return True
            
            self.logger.info(f"🔍 Found {len(clusters_to_update)} clusters to update")
            
            # Try to import subscription manager
            try:
                from app.services.subscription_manager import AzureSubscriptionManager
                sub_manager = AzureSubscriptionManager()
                
                updated_count = 0
                
                for cluster in clusters_to_update:
                    cluster_id = cluster['id']
                    cluster_name = cluster['name']
                    resource_group = cluster['resource_group']
                    
                    self.logger.info(f"🔍 Detecting subscription for cluster: {cluster_name}")
                    
                    # Find the subscription containing this cluster
                    subscription_id = sub_manager.find_cluster_subscription(resource_group, cluster_name)
                    
                    if subscription_id:
                        # Get subscription name
                        subscription_name = "Unknown"
                        try:
                            sub_info = sub_manager.get_subscription_info(subscription_id)
                            if sub_info:
                                subscription_name = sub_info['subscription_name']
                        except:
                            pass
                        
                        # Update the cluster with subscription info
                        with sqlite3.connect(self.db_path) as conn:
                            conn.execute('''
                                UPDATE clusters 
                                SET subscription_id = ?, subscription_name = ?
                                WHERE id = ?
                            ''', (subscription_id, subscription_name, cluster_id))
                            conn.commit()
                        
                        self.logger.info(f"✅ Updated {cluster_name} -> {subscription_name}")
                        updated_count += 1
                    else:
                        self.logger.warning(f"⚠️ Could not find subscription for cluster: {cluster_name}")
                
                self.logger.info(f"✅ Updated {updated_count} clusters with subscription info")
                return True
                
            except ImportError:
                self.logger.warning("⚠️ Subscription manager not available for auto-detection")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting cluster subscriptions: {e}")
            return False

    # ========================================
    # Multi-Subscription Methods
    # ========================================

    def add_cluster_with_subscription_validation(self, cluster_config: Dict, subscription_id: str, subscription_name: str) -> str:
        """Add a new cluster with comprehensive subscription validation"""
        try:
            cluster_id = f"{cluster_config['resource_group']}_{cluster_config['cluster_name']}"
            
            # Try to import and validate, but handle gracefully if not available
            validation_result = {'valid': True, 'cluster_info': {}}
            
            try:
                from app.services.subscription_manager import azure_subscription_manager
                
                # Validate cluster access
                validation_result = azure_subscription_manager.validate_cluster_access(
                    subscription_id, 
                    cluster_config['resource_group'], 
                    cluster_config['cluster_name']
                )
                
                if not validation_result['valid']:
                    raise ValueError(f"Cluster validation failed: {validation_result['error']}")
                    
            except ImportError:
                self.logger.warning("⚠️ Subscription manager not available for validation")
            
            with sqlite3.connect(self.db_path) as conn:
                # Insert cluster with subscription context
                conn.execute('''
                    INSERT OR REPLACE INTO clusters 
                    (id, name, resource_group, environment, region, description, status, 
                    subscription_id, subscription_name, subscription_context_verified, 
                    subscription_last_validated, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    cluster_config['cluster_name'],
                    cluster_config['resource_group'],
                    cluster_config.get('environment', 'development'),
                    cluster_config.get('region', 'Unknown'),
                    cluster_config.get('description', ''),
                    'active',
                    subscription_id,
                    subscription_name,
                    True,  # subscription_context_verified
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps({
                        **cluster_config.get('metadata', {}),
                        'cluster_validation': validation_result.get('cluster_info', {}),
                        'subscription_validation_timestamp': datetime.now().isoformat()
                    })
                ))
                
                # Update subscription cluster count
                conn.execute('''
                    UPDATE subscriptions 
                    SET cluster_count = (
                        SELECT COUNT(*) FROM clusters WHERE subscription_id = ? AND status = 'active'
                    ),
                    last_used = ?,
                    updated_at = ?
                    WHERE subscription_id = ?
                ''', (subscription_id, datetime.now().isoformat(), datetime.now().isoformat(), subscription_id))
                
                conn.commit()
                
            self.logger.info(f"✅ Added cluster with validated subscription: {cluster_id} -> {subscription_name}")
            return cluster_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add cluster with subscription validation: {e}")
            raise

    def track_subscription_analysis_session(self, session_data: Dict) -> bool:
        """Track subscription-aware analysis session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO subscription_analysis_sessions
                    (session_id, cluster_id, subscription_id, resource_group, cluster_name,
                     analysis_type, status, progress, message, started_at, thread_id, subscription_context_set)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_data.get('session_id'),
                    session_data.get('cluster_id'),
                    session_data.get('subscription_id'),
                    session_data.get('resource_group'),
                    session_data.get('cluster_name'),
                    session_data.get('analysis_type', 'completely_fixed'),
                    session_data.get('status', 'running'),
                    session_data.get('progress', 0),
                    session_data.get('message', ''),
                    session_data.get('started_at'),
                    session_data.get('thread_id'),
                    session_data.get('subscription_context_set', False)
                ))
                conn.commit()
                
            self.logger.info(f"✅ Tracked subscription analysis session: {session_data.get('session_id', 'unknown')[:8]}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to track subscription analysis session: {e}")
            return False

    def update_subscription_analysis_session(self, session_id: str, updates: Dict) -> bool:
        """Update subscription analysis session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['status', 'progress', 'message', 'completed_at', 'results_size']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if set_clauses:
                    values.append(session_id)
                    query = f"UPDATE subscription_analysis_sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
                    conn.execute(query, values)
                    conn.commit()
                    
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update subscription analysis session: {e}")
            return False

    def get_subscription_analysis_sessions(self, subscription_id: Optional[str] = None, 
                                          status: Optional[str] = None) -> List[Dict]:
        """Get subscription analysis sessions with filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = []
                params = []
                
                if subscription_id:
                    where_clauses.append("subscription_id = ?")
                    params.append(subscription_id)
                
                if status:
                    where_clauses.append("status = ?")
                    params.append(status)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                cursor = conn.execute(f'''
                    SELECT * FROM subscription_analysis_sessions
                    {where_sql}
                    ORDER BY started_at DESC
                    LIMIT 50
                ''', params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting subscription analysis sessions: {e}")
            return []

    def get_subscription_performance_metrics(self, subscription_id: str, 
                                           hours_back: int = 24) -> Dict[str, List]:
        """Get performance metrics for subscription"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT metric_name, metric_value, measured_at
                    FROM subscription_performance
                    WHERE subscription_id = ? AND measured_at > ?
                    ORDER BY measured_at DESC
                ''', (subscription_id, cutoff_time.isoformat()))
                
                metrics = {}
                for row in cursor.fetchall():
                    metric_name = row['metric_name']
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    
                    metrics[metric_name].append({
                        'value': row['metric_value'],
                        'timestamp': row['measured_at']
                    })
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"❌ Error getting subscription performance metrics: {e}")
            return {}

    def record_subscription_performance_metric(self, subscription_id: str, 
                                             metric_name: str, metric_value: float) -> bool:
        """Record a performance metric for subscription"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO subscription_performance
                    (subscription_id, metric_name, metric_value, measured_at)
                    VALUES (?, ?, ?, ?)
                ''', (subscription_id, metric_name, metric_value, datetime.now().isoformat()))
                conn.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record subscription performance metric: {e}")
            return False

    def get_subscription_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary with subscription breakdown"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Overall portfolio metrics
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_clusters,
                        COUNT(DISTINCT subscription_id) as total_subscriptions,
                        SUM(last_cost) as total_monthly_cost,
                        SUM(last_savings) as total_potential_savings,
                        AVG(CASE WHEN last_cost > 0 THEN (last_savings/last_cost)*100 ELSE 0 END) as avg_optimization_pct
                    FROM clusters 
                    WHERE status = 'active'
                ''')
                
                portfolio_summary = dict(cursor.fetchone())
                
                # Subscription breakdown
                cursor = conn.execute('''
                    SELECT 
                        c.subscription_id,
                        c.subscription_name,
                        COUNT(*) as cluster_count,
                        SUM(c.last_cost) as subscription_cost,
                        SUM(c.last_savings) as subscription_savings,
                        AVG(CASE WHEN c.last_cost > 0 THEN (c.last_savings/c.last_cost)*100 ELSE 0 END) as avg_optimization_pct,
                        s.state as subscription_state,
                        s.last_validated
                    FROM clusters c
                    LEFT JOIN subscriptions s ON c.subscription_id = s.subscription_id
                    WHERE c.status = 'active'
                    GROUP BY c.subscription_id, c.subscription_name
                    ORDER BY subscription_cost DESC
                ''')
                
                subscription_breakdown = [dict(row) for row in cursor.fetchall()]
                
                # Analysis status by subscription
                cursor = conn.execute('''
                    SELECT 
                        subscription_id,
                        analysis_status,
                        COUNT(*) as count
                    FROM clusters 
                    WHERE status = 'active' AND subscription_id IS NOT NULL
                    GROUP BY subscription_id, analysis_status
                ''')
                
                analysis_status_by_subscription = {}
                for row in cursor.fetchall():
                    sub_id = row['subscription_id']
                    if sub_id not in analysis_status_by_subscription:
                        analysis_status_by_subscription[sub_id] = {}
                    analysis_status_by_subscription[sub_id][row['analysis_status']] = row['count']
                
                # Recent analysis activity
                cursor = conn.execute('''
                    SELECT COUNT(*) as recent_analyses
                    FROM clusters 
                    WHERE status = 'active' 
                    AND last_analyzed > datetime('now', '-7 days')
                ''')
                
                recent_analyses = cursor.fetchone()['recent_analyses']
                
                # Environments across subscriptions
                cursor = conn.execute('''
                    SELECT DISTINCT environment 
                    FROM clusters 
                    WHERE status = 'active'
                ''')
                environments = [row[0] for row in cursor.fetchall()]
                
                return {
                    **portfolio_summary,
                    'total_monthly_cost': portfolio_summary['total_monthly_cost'] or 0,
                    'total_potential_savings': portfolio_summary['total_potential_savings'] or 0,
                    'avg_optimization_pct': portfolio_summary['avg_optimization_pct'] or 0,
                    'subscription_breakdown': subscription_breakdown,
                    'analysis_status_by_subscription': analysis_status_by_subscription,
                    'recent_analyses': recent_analyses,
                    'environments': environments,
                    'last_updated': datetime.now().isoformat(),
                    'multi_subscription_enabled': True
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get subscription portfolio summary: {e}")
            return {
                'total_clusters': 0,
                'total_subscriptions': 0,
                'total_monthly_cost': 0,
                'total_potential_savings': 0,
                'avg_optimization_pct': 0,
                'subscription_breakdown': [],
                'analysis_status_by_subscription': {},
                'recent_analyses': 0,
                'environments': [],
                'last_updated': datetime.now().isoformat(),
                'multi_subscription_enabled': True
            }

    def validate_all_subscription_contexts(self) -> Dict[str, bool]:
        """Validate subscription contexts for all clusters"""
        try:
            validation_results = {}
            
            # Try to import subscription manager
            try:
                from app.services.subscription_manager import azure_subscription_manager
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('''
                        SELECT id, name, resource_group, subscription_id, subscription_name
                        FROM clusters 
                        WHERE status = 'active' AND subscription_id IS NOT NULL
                    ''')
                    
                    clusters = cursor.fetchall()
                    
                    for cluster in clusters:
                        cluster_id = cluster['id']
                        subscription_id = cluster['subscription_id']
                        
                        try:
                            # Validate cluster access in subscription
                            validation_result = azure_subscription_manager.validate_cluster_access(
                                subscription_id, cluster['resource_group'], cluster['name']
                            )
                            
                            validation_results[cluster_id] = validation_result['valid']
                            
                            # Update database with validation result
                            conn.execute('''
                                UPDATE clusters 
                                SET subscription_context_verified = ?,
                                    subscription_last_validated = ?
                                WHERE id = ?
                            ''', (validation_result['valid'], datetime.now().isoformat(), cluster_id))
                            
                        except Exception as cluster_error:
                            self.logger.error(f"❌ Validation failed for cluster {cluster_id}: {cluster_error}")
                            validation_results[cluster_id] = False
                    
                    conn.commit()
                    
                valid_count = sum(1 for valid in validation_results.values() if valid)
                total_count = len(validation_results)
                
                self.logger.info(f"✅ Subscription validation complete: {valid_count}/{total_count} clusters valid")
                
            except ImportError:
                self.logger.warning("⚠️ Subscription manager not available for validation")
                return {}
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"❌ Failed to validate subscription contexts: {e}")
            return {}

    # ========================================
    # Core Cluster Management Methods
    # ========================================

    def add_cluster(self, cluster_config: Dict) -> str:
        """Add a new cluster configuration"""
        try:
            cluster_id = f"{cluster_config['resource_group']}_{cluster_config['cluster_name']}"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO clusters 
                    (id, name, resource_group, environment, region, description, status, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    cluster_config['cluster_name'],
                    cluster_config['resource_group'],
                    cluster_config.get('environment', 'development'),
                    cluster_config.get('region', 'Unknown'),
                    cluster_config.get('description', ''),
                    'active',
                    datetime.now().isoformat(),
                    json.dumps(cluster_config.get('metadata', {}))
                ))
                conn.commit()
                
            self.logger.info(f"✅ Added cluster: {cluster_id}")
            return cluster_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add cluster: {e}")
            raise

    def add_cluster_with_subscription(self, cluster_config: Dict, subscription_id: str, subscription_name: str) -> str:
        """Add a new cluster with subscription context"""
        try:
            cluster_id = f"{cluster_config['resource_group']}_{cluster_config['cluster_name']}"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO clusters 
                    (id, name, resource_group, environment, region, description, status, 
                    subscription_id, subscription_name, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    cluster_config['cluster_name'],
                    cluster_config['resource_group'],
                    cluster_config.get('environment', 'development'),
                    cluster_config.get('region', 'Unknown'),
                    cluster_config.get('description', ''),
                    'active',
                    subscription_id,
                    subscription_name,
                    datetime.now().isoformat(),
                    json.dumps(cluster_config.get('metadata', {}))
                ))
                conn.commit()
                
            self.logger.info(f"✅ Added cluster with subscription: {cluster_id} -> {subscription_name}")
            return cluster_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add cluster with subscription: {e}")
            raise

    def get_cluster(self, cluster_id: str) -> Optional[Dict]:
        """Get cluster configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM clusters WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row:
                    cluster = dict(row)
                    cluster['metadata'] = json.loads(cluster.get('metadata', '{}'))
                    return cluster
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get cluster {cluster_id}: {e}")
            return None

    def list_clusters(self) -> List[Dict]:
        """List all configured clusters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM clusters ORDER BY created_at DESC
                ''')
                
                clusters = []
                for row in cursor.fetchall():
                    cluster = dict(row)
                    cluster['metadata'] = json.loads(cluster.get('metadata', '{}'))
                    clusters.append(cluster)
                
                self.logger.info(f"📋 Listed {len(clusters)} clusters")
                return clusters
                
        except Exception as e:
            self.logger.error(f"❌ Failed to list clusters: {e}")
            return []

    def get_clusters_with_subscription_info(self) -> List[Dict]:
        """Get all clusters with subscription information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT c.*, s.subscription_name as sub_display_name
                    FROM clusters c
                    LEFT JOIN subscriptions s ON c.subscription_id = s.subscription_id
                    WHERE c.status = 'active'
                    ORDER BY s.subscription_name, c.created_at DESC
                ''')
                
                clusters = []
                for row in cursor.fetchall():
                    cluster = dict(row)
                    cluster['metadata'] = json.loads(cluster.get('metadata', '{}'))
                    clusters.append(cluster)
                
                self.logger.info(f"📋 Retrieved {len(clusters)} clusters with subscription info")
                return clusters
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get clusters with subscription info: {e}")
            return []

    def get_cluster_subscription_info(self, cluster_id: str) -> Optional[Dict]:
        """Get stored subscription info for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT subscription_id, subscription_name 
                    FROM clusters 
                    WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row and row['subscription_id']:
                    return {
                        'subscription_id': row['subscription_id'],
                        'subscription_name': row['subscription_name'] or 'Unknown'
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting cluster subscription info: {e}")
            return None

    def update_cluster_subscription_info(self, cluster_id: str, subscription_id: str, subscription_name: str):
        """Update cluster with its actual subscription information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE clusters 
                    SET subscription_id = ?, subscription_name = ?
                    WHERE id = ?
                ''', (subscription_id, subscription_name, cluster_id))
                conn.commit()
                
            self.logger.info(f"✅ Updated cluster {cluster_id} subscription info: {subscription_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update cluster subscription info: {e}")

    def update_cluster_analysis(self, cluster_id: str, analysis_data: dict):
        """Update cluster with analysis results - preserves implementation plan"""
        try:
            enhanced_analysis_data = analysis_data.copy()
            
            # Check for node data and set flag
            has_node_data = False
            for key in ['nodes', 'node_metrics', 'real_node_data']:
                if enhanced_analysis_data.get(key) and len(enhanced_analysis_data[key]) > 0:
                    has_node_data = True
                    self.logger.info(f"✅ DB SAVE: Found node data in {key} ({len(enhanced_analysis_data[key])} nodes)")
                    break
            
            enhanced_analysis_data['has_real_node_data'] = has_node_data
            
            if has_node_data:
                node_data = None
                for key in ['nodes', 'node_metrics', 'real_node_data']:
                    if enhanced_analysis_data.get(key):
                        node_data = enhanced_analysis_data[key]
                        break
                
                if node_data:
                    enhanced_analysis_data['nodes'] = node_data
                    enhanced_analysis_data['node_metrics'] = node_data
                    enhanced_analysis_data['real_node_data'] = node_data
            
            # CRITICAL: Generate implementation plan BEFORE serialization
            if 'implementation_plan' not in enhanced_analysis_data:
                try:
                    from app.ml.implementation_generator import AKSImplementationGenerator
                    implementation_generator = AKSImplementationGenerator()
                    implementation_plan = implementation_generator.generate_implementation_plan(enhanced_analysis_data)
                    enhanced_analysis_data['implementation_plan'] = implementation_plan
                    self.logger.info("✅ Generated implementation plan for database")
                    
                    # Validate the plan has phases
                    if implementation_plan and 'implementation_phases' in implementation_plan:
                        phases_count = len(implementation_plan['implementation_phases'])
                        self.logger.info(f"✅ Implementation plan has {phases_count} phases")
                        
                except Exception as impl_error:
                    self.logger.error(f"❌ Failed to generate implementation plan: {impl_error}")
                    self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Use specialized serialization for implementation plan
            serializable_data = serialize_implementation_plan(enhanced_analysis_data)
            
            total_cost = float(serializable_data.get('total_cost', 0))
            total_savings = float(serializable_data.get('total_savings', 0))
            confidence = float(serializable_data.get('analysis_confidence', 0))
            
            if 'hpa_recommendations' not in analysis_data:
                self.logger.warning(f"⚠️ DB SAVE: No HPA recommendations for {cluster_id}")
            else:
                self.logger.info(f"✅ DB SAVE: HPA recommendations found for {cluster_id}")
                
                # Validate HPA structure
                hpa_recs = analysis_data['hpa_recommendations']
                if isinstance(hpa_recs, dict) and 'optimization_recommendation' in hpa_recs:
                    self.logger.info(f"✅ DB SAVE: HPA structure validated for {cluster_id}")
                else:
                    self.logger.warning(f"⚠️ DB SAVE: HPA structure incomplete for {cluster_id}")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE clusters 
                    SET last_cost = ?, last_savings = ?, last_confidence = ?, 
                        last_analyzed = ?, analysis_data = ?
                    WHERE id = ?
                ''', (
                    total_cost, total_savings, confidence,
                    datetime.now().isoformat(),
                    json.dumps(serializable_data),
                    cluster_id
                ))
                conn.execute('''
                    INSERT INTO analysis_results 
                    (cluster_id, analysis_date, results, total_cost, total_savings, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    datetime.now().isoformat(),
                    json.dumps(serializable_data),  # Store full analysis
                    total_cost,
                    total_savings, 
                    confidence
                ))
                conn.commit()

            self.logger.info(f"✅ Updated cluster analysis with implementation plan: {cluster_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update cluster analysis: {e}")
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

    def get_latest_analysis(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis with proper implementation plan deserialization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT analysis_data, last_analyzed, last_cost, last_savings
                    FROM clusters 
                    WHERE id = ? AND analysis_data IS NOT NULL
                    ORDER BY last_analyzed DESC
                    LIMIT 1
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row and row['analysis_data']:
                    try:
                        serialized_data = json.loads(row['analysis_data'])
                        
                        # Use specialized deserialization
                        analysis_data = deserialize_implementation_plan(serialized_data)
                        
                        # Set node data flag
                        has_node_data = False
                        for key in ['nodes', 'node_metrics', 'real_node_data']:
                            if analysis_data.get(key) and len(analysis_data[key]) > 0:
                                has_node_data = True
                                break
                        
                        analysis_data['has_real_node_data'] = has_node_data
                        
                        if has_node_data:
                            node_data = None
                            for key in ['nodes', 'node_metrics', 'real_node_data']:
                                if analysis_data.get(key):
                                    node_data = analysis_data[key]
                                    break
                            
                            if node_data:
                                analysis_data['nodes'] = node_data
                                analysis_data['node_metrics'] = node_data
                                analysis_data['real_node_data'] = node_data
                        
                        # Validate HPA recommendations
                        if 'hpa_recommendations' not in analysis_data:
                            self.logger.warning(f"⚠️ DB LOAD: No HPA recommendations for {cluster_id}")
                        else:
                            self.logger.info(f"✅ DB LOAD: HPA recommendations found for {cluster_id}")
                        
                        # CRITICAL: Validate implementation plan structure
                        if 'implementation_plan' in analysis_data:
                            impl_plan = analysis_data['implementation_plan']
                            if isinstance(impl_plan, dict) and 'implementation_phases' in impl_plan:
                                phases = impl_plan['implementation_phases']
                                if isinstance(phases, list) and len(phases) > 0:
                                    self.logger.info(f"✅ DB LOAD: Implementation plan has {len(phases)} phases")
                                else:
                                    self.logger.warning("⚠️ DB LOAD: Implementation plan phases are empty")
                            else:
                                self.logger.warning("⚠️ DB LOAD: Implementation plan missing phases structure")
                        
                        self.logger.info(f"📦 Loaded COMPLETE analysis from database: {cluster_id}")
                        return analysis_data
                        
                    except json.JSONDecodeError as e:
                        self.logger.error(f"❌ Failed to decode analysis data: {e}")
                        return None
                else:
                    self.logger.info(f"ℹ️ No analysis data found for cluster: {cluster_id}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Database error getting analysis: {e}")
            return None

    def update_analysis_status(self, cluster_id: str, status: str, progress: int = 0, message: str = ""):
        """Update analysis status for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == 'analyzing' and progress <= 10:
                    # First time starting analysis
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?, 
                            analysis_started_at = ?
                        WHERE id = ?
                    ''', (status, progress, message, datetime.now().isoformat(), cluster_id))
                else:
                    # Update progress or completion
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?
                        WHERE id = ?
                    ''', (status, progress, message, cluster_id))
                
                conn.commit()
                self.logger.info(f"✅ Updated analysis status for {cluster_id}: {status} ({progress}%)")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update analysis status: {e}")
            raise

    def get_analysis_status(self, cluster_id: str) -> Optional[Dict]:
        """Get current analysis status for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT analysis_status, analysis_progress, analysis_message, 
                        analysis_started_at, last_cost, last_savings, last_analyzed
                    FROM clusters 
                    WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'cluster_id': cluster_id,
                        'status': row['analysis_status'] or 'pending',
                        'progress': row['analysis_progress'] or 0,
                        'message': row['analysis_message'] or 'Ready for analysis',
                        'started_at': row['analysis_started_at'],
                        'last_cost': row['last_cost'],
                        'last_savings': row['last_savings'],
                        'last_analyzed': row['last_analyzed']
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting analysis status for {cluster_id}: {e}")
            return None

    def get_clusters_by_status(self, status: str) -> List[Dict]:
        """Get all clusters with a specific analysis status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM clusters 
                    WHERE analysis_status = ? AND status = 'active'
                    ORDER BY analysis_started_at DESC
                ''', (status,))
                
                clusters = []
                for row in cursor.fetchall():
                    cluster = dict(row)
                    cluster['metadata'] = json.loads(cluster.get('metadata', '{}'))
                    clusters.append(cluster)
                
                return clusters
                
        except Exception as e:
            self.logger.error(f"❌ Error getting clusters by status {status}: {e}")
            return []

    def get_analysis_queue_status(self) -> Dict:
        """Get overview of analysis queue and status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get status counts
                cursor = conn.execute('''
                    SELECT 
                        analysis_status,
                        COUNT(*) as count,
                        AVG(analysis_progress) as avg_progress
                    FROM clusters 
                    WHERE status = 'active'
                    GROUP BY analysis_status
                ''')
                
                status_counts = {}
                for row in cursor.fetchall():
                    status_counts[row['analysis_status'] or 'pending'] = {
                        'count': row['count'],
                        'avg_progress': row['avg_progress'] or 0
                    }
                
                # Get currently analyzing clusters
                analyzing_cursor = conn.execute('''
                    SELECT id, name, analysis_progress, analysis_message, analysis_started_at
                    FROM clusters 
                    WHERE analysis_status = 'analyzing' AND status = 'active'
                    ORDER BY analysis_started_at ASC
                ''')
                
                analyzing_clusters = []
                for row in analyzing_cursor.fetchall():
                    analyzing_clusters.append({
                        'id': row['id'],
                        'name': row['name'],
                        'progress': row['analysis_progress'],
                        'message': row['analysis_message'],
                        'started_at': row['analysis_started_at']
                    })
                
                return {
                    'status_counts': status_counts,
                    'analyzing_clusters': analyzing_clusters,
                    'total_active': sum(s['count'] for s in status_counts.values()),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting analysis queue status: {e}")
            return {}

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio-wide summary statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_clusters,
                        SUM(last_cost) as total_monthly_cost,
                        SUM(last_savings) as total_potential_savings,
                        AVG(CASE WHEN last_cost > 0 THEN (last_savings/last_cost)*100 ELSE 0 END) as avg_optimization_pct
                    FROM clusters 
                    WHERE status = 'active'
                ''')
                
                row = cursor.fetchone()
                if row:
                    summary = dict(row)
                    summary['total_monthly_cost'] = summary['total_monthly_cost'] or 0
                    summary['total_potential_savings'] = summary['total_potential_savings'] or 0
                    summary['avg_optimization_pct'] = summary['avg_optimization_pct'] or 0
                    summary['last_updated'] = datetime.now().isoformat()
                    
                    # Get environments
                    env_cursor = conn.execute('SELECT DISTINCT environment FROM clusters WHERE status = "active"')
                    summary['environments'] = [row[0] for row in env_cursor.fetchall()]
                    
                    return summary
                
            return {
                'total_clusters': 0,
                'total_monthly_cost': 0,
                'total_potential_savings': 0,
                'avg_optimization_pct': 0,
                'environments': [],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get portfolio summary: {e}")
            return {
                'total_clusters': 0,
                'total_monthly_cost': 0,
                'total_potential_savings': 0,
                'avg_optimization_pct': 0,
                'environments': [],
                'last_updated': datetime.now().isoformat()
            }

    def get_enhanced_portfolio_summary(self) -> Dict:
        """Get enhanced portfolio summary with analysis status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Basic portfolio metrics
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_clusters,
                        SUM(last_cost) as total_monthly_cost,
                        SUM(last_savings) as total_potential_savings,
                        AVG(CASE WHEN last_cost > 0 THEN (last_savings/last_cost)*100 ELSE 0 END) as avg_optimization_pct
                    FROM clusters 
                    WHERE status = 'active'
                ''')
                
                summary = dict(cursor.fetchone())
                
                # Analysis status breakdown
                status_cursor = conn.execute('''
                    SELECT 
                        analysis_status,
                        COUNT(*) as count
                    FROM clusters 
                    WHERE status = 'active'
                    GROUP BY analysis_status
                ''')
                
                analysis_breakdown = {}
                for row in status_cursor.fetchall():
                    analysis_breakdown[row['analysis_status'] or 'pending'] = row['count']
                
                # Recent activity
                recent_cursor = conn.execute('''
                    SELECT COUNT(*) as recent_analyses
                    FROM clusters 
                    WHERE status = 'active' 
                    AND last_analyzed > datetime('now', '-7 days')
                ''')
                
                recent_analyses = recent_cursor.fetchone()['recent_analyses']
                
                # Environments
                env_cursor = conn.execute('''
                    SELECT DISTINCT environment 
                    FROM clusters 
                    WHERE status = 'active'
                ''')
                environments = [row[0] for row in env_cursor.fetchall()]
                
                return {
                    **summary,
                    'total_monthly_cost': summary['total_monthly_cost'] or 0,
                    'total_potential_savings': summary['total_potential_savings'] or 0,
                    'avg_optimization_pct': summary['avg_optimization_pct'] or 0,
                    'analysis_breakdown': analysis_breakdown,
                    'recent_analyses': recent_analyses,
                    'environments': environments,
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting enhanced portfolio summary: {e}")
            return {
                'total_clusters': 0,
                'total_monthly_cost': 0,
                'total_potential_savings': 0,
                'avg_optimization_pct': 0,
                'analysis_breakdown': {},
                'recent_analyses': 0,
                'environments': [],
                'last_updated': datetime.now().isoformat()
            }

    def remove_cluster(self, cluster_id: str) -> bool:
        """Remove a cluster and all its analysis data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove analysis results first
                conn.execute('DELETE FROM analysis_results WHERE cluster_id = ?', (cluster_id,))
                
                # Remove cluster
                cursor = conn.execute('DELETE FROM clusters WHERE id = ?', (cluster_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Removed cluster: {cluster_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Cluster not found: {cluster_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to remove cluster {cluster_id}: {e}")
            return False

    def get_analysis_history(self, cluster_id: str, limit: int = 10) -> List[Dict]:
        """Get analysis history for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT analysis_date, total_cost, total_savings, confidence_level
                    FROM analysis_results 
                    WHERE cluster_id = ? 
                    ORDER BY analysis_date DESC 
                    LIMIT ?
                ''', (cluster_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get analysis history for {cluster_id}: {e}")
            return []

    def cleanup_old_analyses(self, days_to_keep: int = 90):
        """Clean up old analysis results to maintain database size"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM analysis_results 
                    WHERE analysis_date < ? 
                    AND id NOT IN (
                        SELECT id FROM analysis_results 
                        WHERE cluster_id IN (
                            SELECT cluster_id FROM analysis_results 
                            GROUP BY cluster_id 
                            ORDER BY analysis_date DESC 
                            LIMIT 1
                        )
                    )
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                self.logger.info(f"🧹 Cleaned up {cursor.rowcount} old analysis records")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup old analyses: {e}")


# Migration function to convert from JSON to SQLite
def migrate_from_json(json_file_path: str, db_manager: EnhancedMultiSubscriptionClusterManager):
    """Migrate existing clusters.json data to SQLite database"""
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                clusters_data = json.load(f)
                
            for cluster_data in clusters_data:
                # Convert old format to new format if needed
                cluster_config = {
                    'cluster_name': cluster_data.get('name', cluster_data.get('cluster_name', '')),
                    'resource_group': cluster_data.get('resource_group', ''),
                    'environment': cluster_data.get('environment', 'development'),
                    'region': cluster_data.get('region', 'Unknown'),
                    'description': cluster_data.get('description', ''),
                    'metadata': cluster_data.get('metadata', {})
                }
                
                if cluster_config['cluster_name'] and cluster_config['resource_group']:
                    db_manager.add_cluster(cluster_config)
                    
            # Backup old file
            backup_path = f"{json_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(json_file_path, backup_path)
            logger.info(f"✅ Migrated {len(clusters_data)} clusters from JSON to SQLite")
            logger.info(f"📦 Backup created at: {backup_path}")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

# For backward compatibility, create an alias
EnhancedClusterManager = EnhancedMultiSubscriptionClusterManager