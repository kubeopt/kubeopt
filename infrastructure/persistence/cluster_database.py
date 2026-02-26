#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

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
                'analysis_data': 'BLOB',
                'enhanced_analysis_data': 'BLOB',
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

def migrate_analysis_data_to_blob(db_path: str = '../data/database/clusters.db'):
    """Migrate analysis_data column from TEXT to BLOB to handle large JSON data"""
    logger = logging.getLogger(__name__)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if analysis_data column exists and get its type
            cursor.execute("PRAGMA table_info(clusters)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            if 'analysis_data' in columns:
                current_type = columns['analysis_data']
                logger.info(f"Current analysis_data column type: {current_type}")
                
                if current_type.upper() == 'TEXT':
                    logger.info("🔧 Migrating analysis_data from TEXT to BLOB for large JSON support...")
                    
                    # SQLite doesn't support ALTER COLUMN TYPE, so we need to recreate
                    # First, backup the data
                    cursor.execute("SELECT id, analysis_data FROM clusters WHERE analysis_data IS NOT NULL")
                    data_backup = cursor.fetchall()
                    logger.info(f"📦 Backing up {len(data_backup)} analysis records")
                    
                    # Create new column as BLOB
                    cursor.execute("ALTER TABLE clusters ADD COLUMN analysis_data_blob BLOB")
                    
                    # Copy data from TEXT to BLOB
                    for cluster_id, analysis_data in data_backup:
                        if analysis_data is not None and analysis_data:
                            try:
                                # Handle both string and bytes data types
                                if isinstance(analysis_data, str):
                                    blob_data = analysis_data.encode('utf-8')
                                elif isinstance(analysis_data, bytes):
                                    blob_data = analysis_data
                                else:
                                    # Convert other types to JSON string then encode
                                    blob_data = json.dumps(analysis_data).encode('utf-8')
                                
                                cursor.execute(
                                    "UPDATE clusters SET analysis_data_blob = ? WHERE id = ?",
                                    (blob_data, cluster_id)
                                )
                                logger.debug(f"✅ Migrated analysis data for cluster {cluster_id} ({len(blob_data)} bytes)")
                            except Exception as e:
                                logger.error(f"❌ Failed to migrate data for cluster {cluster_id}: {e}")
                    
                    # Drop old TEXT column and rename BLOB column
                    cursor.execute("PRAGMA foreign_keys=off")
                    
                    # Create new table with BLOB column
                    cursor.execute("""
                        CREATE TABLE clusters_new (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            resource_group TEXT NOT NULL,
                            environment TEXT DEFAULT 'unknown',
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
                            analysis_data BLOB,
                            enhanced_analysis_data BLOB,
                            analysis_status TEXT DEFAULT 'pending',
                            analysis_progress INTEGER DEFAULT 0,
                            analysis_message TEXT DEFAULT '',
                            analysis_started_at TIMESTAMP NULL,
                            auto_analyze_enabled BOOLEAN DEFAULT 1,
                            subscription_id TEXT DEFAULT NULL,
                            subscription_name TEXT DEFAULT NULL,
                            subscription_context_verified BOOLEAN DEFAULT 0,
                            subscription_last_validated TIMESTAMP NULL,
                            cost_fetched_at TIMESTAMP NULL
                        )
                    """)
                    
                    # Copy all data to new table (using BLOB data where available)
                    cursor.execute("""
                        INSERT INTO clusters_new 
                        SELECT id, name, resource_group, environment, region, description, status,
                               created_at, last_analyzed, last_cost, last_savings, last_confidence,
                               analysis_count, metadata, 
                               COALESCE(analysis_data_blob, analysis_data) as analysis_data,
                               NULL as enhanced_analysis_data,
                               analysis_status, analysis_progress, analysis_message, analysis_started_at,
                               auto_analyze_enabled, subscription_id, subscription_name,
                               subscription_context_verified, subscription_last_validated
                        FROM clusters
                    """)
                    
                    # Replace old table
                    cursor.execute("DROP TABLE clusters")
                    cursor.execute("ALTER TABLE clusters_new RENAME TO clusters")
                    
                    # Recreate indexes
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clusters_subscription_id ON clusters(subscription_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clusters_analysis_status ON clusters(analysis_status)')
                    
                    cursor.execute("PRAGMA foreign_keys=on")
                    conn.commit()
                    
                    logger.info("✅ Successfully migrated analysis_data to BLOB - can now store large JSON data")
                else:
                    logger.info("✅ analysis_data column already using BLOB type")
            else:
                logger.warning("⚠️ analysis_data column not found in schema")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to migrate analysis_data to BLOB: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
                'analysis_data': 'BLOB',
                'enhanced_analysis_data': 'BLOB',
                'last_confidence': 'REAL DEFAULT 0',
                'analysis_status': 'TEXT DEFAULT "pending"',
                'analysis_progress': 'INTEGER DEFAULT 0',
                'analysis_message': 'TEXT DEFAULT ""',
                'analysis_started_at': 'TIMESTAMP NULL',
                'auto_analyze_enabled': 'BOOLEAN DEFAULT 1',
                'subscription_context_verified': 'BOOLEAN DEFAULT 0',
                'subscription_last_validated': 'TIMESTAMP NULL',
                'cost_fetched_at': 'TIMESTAMP NULL'
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
                    analysis_type TEXT DEFAULT 'MULTI_SUBSCRIPTION',
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
    
    def __init__(self, db_path=None):
        import os
        from pathlib import Path
        
        if db_path is None:
            # Check for local development mode
            is_local_dev = os.getenv('LOCAL_DEV', 'false').lower() in ('true', '1', 'yes')
            
            if is_local_dev:
                # Local development: use local directory
                local_db_path = os.path.join(os.getcwd(), 'infrastructure', 'persistence', 'database', 'clusters.db')
                os.makedirs(os.path.dirname(local_db_path), exist_ok=True)
                db_path = local_db_path
                print(f"✅ LOCAL DEVELOPMENT: Using local database: {db_path}")
            else:
                # Production: require persistent volume
                volume_mount = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
                if volume_mount:
                    # Using Railway-provided volume path
                    db_path = os.path.join(volume_mount, 'clusters.db')
                    print(f"✅ Using persistent volume: {db_path}")
                elif Path('/data').exists():
                    # Standard volume mount at /data
                    db_path = '/data/clusters.db'
                    print(f"✅ Using mounted volume: {db_path}")
                else:
                    # NO FALLBACK for production - volume is required
                    raise ValueError(
                        "CRITICAL: No persistent volume detected! "
                        "Please attach a volume to this service at /data mount path. "
                        "Without a volume, all data will be lost on restart."
                    )
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize database with complete schema
        self.init_database()
        
        # Run all migrations
        migrate_database_schema(self.db_path)
        migrate_analysis_data_to_blob(self.db_path)
        migrate_database_for_multi_subscription(self.db_path)
        
        # Clean up any stale analyses on startup
        self.cleanup_stale_analyses()
        
        # Initialize subscription tracking
        self.initialize_subscription_tracking()

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection with WAL mode and busy timeout for concurrency."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")  # Wait up to 10s for locks
        return conn

    def init_database(self):
        """Initialize SQLite database with complete multi-subscription schema"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            with self._connect() as conn:
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
                        analysis_data BLOB,
                        enhanced_analysis_data BLOB,
                        analysis_status TEXT DEFAULT 'pending',
                        analysis_progress INTEGER DEFAULT 0,
                        analysis_message TEXT DEFAULT '',
                        analysis_started_at TIMESTAMP,
                        auto_analyze_enabled BOOLEAN DEFAULT 1,
                        subscription_id TEXT DEFAULT NULL,
                        subscription_name TEXT DEFAULT NULL,
                        subscription_context_verified BOOLEAN DEFAULT 0,
                        subscription_last_validated TIMESTAMP NULL,
                        cost_fetched_at TIMESTAMP NULL
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
                
                # Create implementation plans table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS implementation_plans (
                        plan_id TEXT PRIMARY KEY,
                        cluster_id TEXT NOT NULL,
                        analysis_id TEXT,
                        plan_data BLOB NOT NULL,
                        generated_at TEXT NOT NULL,
                        total_savings REAL,
                        total_actions INTEGER,
                        executed BOOLEAN DEFAULT 0,
                        execution_status TEXT,
                        version TEXT DEFAULT '1.0',
                        generated_by TEXT,
                        FOREIGN KEY (cluster_id) REFERENCES clusters(id)
                    )
                ''')
                
                # Create indexes
                conn.execute('CREATE INDEX IF NOT EXISTS idx_cluster_id ON analysis_results(cluster_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_plans_cluster ON implementation_plans(cluster_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_plans_generated ON implementation_plans(generated_at DESC)')
                
                conn.commit()
                self.logger.info("✅ Complete multi-subscription database initialized successfully")
                
                # Railway env file creation removed - not needed for local development
                # self._create_env_file_for_railway()
                
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise

    def touch_cluster(self, cluster_id: str):
        """Update cluster timestamp to invalidate cache"""
        try:
            with self._connect() as conn:
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
            
            with self._connect() as conn:
                # Clean up stale cluster analyses
                cursor = conn.execute('''
                    SELECT id FROM clusters 
                    WHERE analysis_status IN ('running', 'analyzing', 'pending') 
                    AND analysis_started_at IS NOT NULL
                    AND analysis_started_at < ?
                ''', (cutoff_time.isoformat(),))
                
                stale_clusters = [row[0] for row in cursor.fetchall()]
                
                if stale_clusters:
                    # Update stale cluster analyses but preserve previous analysis data
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = CASE 
                                WHEN last_analyzed IS NOT NULL THEN 'completed'
                                ELSE 'failed'
                            END,
                            analysis_progress = CASE 
                                WHEN last_analyzed IS NOT NULL THEN 100
                                ELSE 0
                            END,
                            analysis_message = CASE 
                                WHEN last_analyzed IS NOT NULL THEN 'Previous analysis restored after interruption'
                                ELSE 'Analysis timed out and was cleaned up'
                            END
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
            
            with self._connect() as conn:
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
                    
                    # Also update corresponding clusters - but preserve previous successful analyses
                    for session_id, cluster_id in stale_sessions:
                        conn.execute('''
                            UPDATE clusters 
                            SET analysis_status = CASE 
                                    WHEN last_analyzed IS NOT NULL THEN 'completed'
                                    ELSE 'failed'
                                END,
                                analysis_progress = CASE 
                                    WHEN last_analyzed IS NOT NULL THEN 100
                                    ELSE 0
                                END,
                                analysis_message = CASE 
                                    WHEN last_analyzed IS NOT NULL THEN 'Previous analysis restored after session cleanup'
                                    ELSE 'Analysis session timed out'
                                END
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
                from infrastructure.services.subscription_manager import azure_subscription_manager
                
                # Get all available subscriptions
                subscriptions = azure_subscription_manager.get_available_subscriptions(force_refresh=True)
                
                # Update subscriptions table
                with self._connect() as conn:
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
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, name, resource_group, environment, region, description, 
                           status, created_at, last_analyzed, last_cost, last_savings, 
                           last_confidence, analysis_count, metadata, analysis_status, 
                           analysis_progress, analysis_message, analysis_started_at, 
                           auto_analyze_enabled, subscription_id, subscription_name, 
                           subscription_context_verified, subscription_last_validated
                    FROM clusters 
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
            with self._connect() as conn:
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
                from infrastructure.services.subscription_manager import AzureSubscriptionManager
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
                            if sub_info is not None and sub_info:
                                subscription_name = sub_info['subscription_name']
                        except Exception as e:
                            logger.error(f"Unexpected error: {e}")
                            raise
                        
                        # Update the cluster with subscription info
                        with self._connect() as conn:
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
        """Add a new cluster with comprehensive subscription validation - DEPRECATED: Use add_cluster_with_subscription instead"""
        self.logger.warning("⚠️ DEPRECATED: add_cluster_with_subscription_validation is deprecated. Use add_cluster_with_subscription for enhanced validation.")
        
        # Redirect to the enhanced method
        return self.add_cluster_with_subscription(cluster_config, subscription_id, subscription_name)

    def track_subscription_analysis_session(self, session_data: Dict) -> bool:
        """Track subscription-aware analysis session"""
        try:
            with self._connect() as conn:
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
                    session_data.get('analysis_type', 'MULTI_SUBSCRIPTION'),
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
            with self._connect() as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['status', 'progress', 'message', 'completed_at', 'results_size']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if set_clauses is not None and set_clauses:
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
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = []
                params = []
                
                if subscription_id is not None and subscription_id:
                    where_clauses.append("subscription_id = ?")
                    params.append(subscription_id)
                
                if status is not None and status:
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
            
            with self._connect() as conn:
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
            with self._connect() as conn:
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
            with self._connect() as conn:
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
                from infrastructure.services.subscription_manager import azure_subscription_manager
                
                with self._connect() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('''
                        SELECT id, name, resource_group, subscription_id, subscription_name
                        FROM clusters 
                        WHERE status = 'active' AND subscription_id IS NOT NULL
                    ''')
                    
                    clusters = cursor.fetchall()
                    
                    for cluster_row in clusters:
                        # Convert SQLite Row to dictionary to enable .get() method
                        cluster = dict(cluster_row)
                        cluster_id = cluster['id']
                        subscription_id = cluster['subscription_id']
                        
                        try:
                            # Validate cluster access in subscription
                            validation_result = azure_subscription_manager.validate_cluster_access(
                                subscription_id, cluster['resource_group'], cluster['name']
                            )
                            
                            validation_results[cluster_id] = validation_result['valid']
                            
                            # Update database with validation result and discovered information
                            update_fields = ['subscription_context_verified = ?', 'subscription_last_validated = ?']
                            update_values = [validation_result['valid'], datetime.now().isoformat()]
                            
                            # Update location if discovered and different
                            if validation_result['valid'] and validation_result.get('cluster_info'):
                                cluster_info = validation_result['cluster_info']
                                discovered_location = cluster_info.get('location')
                                discovered_rg = validation_result.get('discovered_resource_group')
                                
                                if discovered_location and discovered_location != cluster.get('region'):
                                    update_fields.append('region = ?')
                                    update_values.append(discovered_location)
                                    self.logger.info(f"📍 Updated location for {cluster_id}: {discovered_location}")
                                
                                if discovered_rg and discovered_rg != cluster.get('resource_group'):
                                    update_fields.append('resource_group = ?')
                                    update_values.append(discovered_rg)
                                    self.logger.info(f"📁 Updated resource group for {cluster_id}: {discovered_rg}")
                            
                            update_values.append(cluster_id)
                            
                            conn.execute(f'''
                                UPDATE clusters 
                                SET {', '.join(update_fields)}
                                WHERE id = ?
                            ''', tuple(update_values))
                            
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
            
            with self._connect() as conn:
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
        """Add a new cluster with subscription context and enhanced validation"""
        try:
            # Perform validation to get accurate cluster information
            validation_result = self._validate_and_discover_cluster_info(
                subscription_id, 
                cluster_config.get('resource_group', ''), 
                cluster_config['cluster_name']
            )
            
            if validation_result['valid']:
                cluster_info = validation_result.get('cluster_info', {})
                discovered_rg = validation_result.get('discovered_resource_group', cluster_config.get('resource_group', ''))
                discovered_location = cluster_info.get('location', cluster_config.get('region', 'Unknown'))
                
                # Extract environment from cluster tags if available
                tags = cluster_info.get('tags', {})
                discovered_environment = None
                
                # Look for environment in common tag names
                if tags is not None and tags:
                    for tag_name in ['Environment', 'environment', 'env', 'Env']:
                        if tag_name in tags:
                            discovered_environment = str(tags[tag_name]).lower()
                            break
                
                # Update cluster config with discovered values
                cluster_config['resource_group'] = discovered_rg
                cluster_config['region'] = discovered_location
                if discovered_environment is not None and discovered_environment:
                    cluster_config['environment'] = discovered_environment
                
                self.logger.info(f"✅ Enhanced cluster info: {cluster_config['cluster_name']} -> RG: {discovered_rg}, Location: {discovered_location}, Environment: {cluster_config.get('environment', 'MISSING')}")
            else:
                self.logger.warning(f"⚠️ Validation failed, using provided data for cluster: {cluster_config['cluster_name']} (Environment: {cluster_config.get('environment', 'MISSING')})")
            
            cluster_id = f"{cluster_config['resource_group']}_{cluster_config['cluster_name']}"
            
            with self._connect() as conn:
                # Check if cluster already exists to preserve analysis data
                cursor = conn.execute('SELECT id, last_cost, last_savings, last_analyzed FROM clusters WHERE id = ?', (cluster_id,))
                existing_cluster = cursor.fetchone()
                
                if existing_cluster:
                    # Cluster exists - only update subscription-related fields to preserve analysis data
                    self.logger.info(f"🔄 Cluster exists, updating subscription info only (preserving analysis data): {cluster_id}")
                    conn.execute('''
                        UPDATE clusters 
                        SET subscription_id = ?, subscription_name = ?, subscription_context_verified = ?, 
                            subscription_last_validated = ?, environment = ?, region = ?, resource_group = ?, status = ?
                        WHERE id = ?
                    ''', (
                        subscription_id,
                        subscription_name,
                        validation_result['valid'],
                        datetime.now().isoformat() if validation_result['valid'] else None,
                        cluster_config.get('environment', 'unknown'),
                        cluster_config.get('region', 'unknown'),
                        cluster_config['resource_group'],
                        'active' if validation_result['valid'] else 'inactive',
                        cluster_id
                    ))
                else:
                    # New cluster - insert with full data
                    self.logger.info(f"➕ Creating new cluster: {cluster_id}")
                    conn.execute('''
                        INSERT INTO clusters 
                        (id, name, resource_group, environment, region, description, status, 
                        subscription_id, subscription_name, subscription_context_verified, 
                        subscription_last_validated, created_at, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    cluster_config['cluster_name'],
                    cluster_config['resource_group'],
                    cluster_config.get('environment', 'unknown'),
                    cluster_config.get('region', 'Unknown'),
                    cluster_config.get('description', ''),
                    'active',
                    subscription_id,
                    subscription_name,
                    validation_result['valid'],
                    datetime.now().isoformat() if validation_result['valid'] else None,
                    datetime.now().isoformat(),
                    json.dumps({
                        **cluster_config.get('metadata', {}),
                        'validation_info': validation_result,
                        'auto_discovered': validation_result.get('auto_discovered', False)
                    })
                ))
                conn.commit()
                
            self.logger.info(f"✅ Added cluster with subscription: {cluster_id} -> {subscription_name}")
            return cluster_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add cluster with subscription: {e}")
            raise
    
    def _validate_and_discover_cluster_info(self, subscription_id: str, resource_group: str, cluster_name: str) -> Dict:
        """Validate cluster and discover accurate information"""
        try:
            # Import here to avoid circular imports
            from infrastructure.services.subscription_manager import AzureSubscriptionManager
            azure_subscription_manager = AzureSubscriptionManager()
            
            return azure_subscription_manager.validate_cluster_access(
                subscription_id, resource_group, cluster_name
            )
            
        except ImportError:
            self.logger.warning("⚠️ Subscription manager not available for validation")
            return {'valid': False, 'error': 'Validation service unavailable'}
        except Exception as e:
            self.logger.error(f"❌ Validation error: {e}")
            return {'valid': False, 'error': str(e)}

    def get_cluster(self, cluster_id: str) -> Optional[Dict]:
        """Get cluster configuration"""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, name, resource_group, environment, region, description, 
                           status, created_at, last_analyzed, last_cost, last_savings, 
                           last_confidence, analysis_count, metadata, analysis_status, 
                           analysis_progress, analysis_message, analysis_started_at, 
                           auto_analyze_enabled, subscription_id, subscription_name, 
                           subscription_context_verified, subscription_last_validated
                    FROM clusters WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row is not None and row:
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
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, name, resource_group, environment, region, description, 
                           status, created_at, last_analyzed, last_cost, last_savings, 
                           last_confidence, analysis_count, metadata, analysis_status, 
                           analysis_progress, analysis_message, analysis_started_at, 
                           auto_analyze_enabled, subscription_id, subscription_name, 
                           subscription_context_verified, subscription_last_validated
                    FROM clusters ORDER BY created_at DESC
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
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT c.id, c.name, c.resource_group, c.environment, c.region, c.description, 
                           c.status, c.created_at, c.last_analyzed, c.last_cost, c.last_savings, 
                           c.last_confidence, c.analysis_count, c.metadata, c.analysis_status, 
                           c.analysis_progress, c.analysis_message, c.analysis_started_at, 
                           c.auto_analyze_enabled, c.subscription_id, c.subscription_name, 
                           c.subscription_context_verified, c.subscription_last_validated,
                           s.subscription_name as sub_display_name
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
                
                # Only log cluster retrieval in debug mode
                self.logger.debug(f"📋 Retrieved {len(clusters)} clusters with subscription info")
                return clusters
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get clusters with subscription info: {e}")
            return []

    def get_cluster_subscription_info(self, cluster_id: str) -> Optional[Dict]:
        """Get stored subscription info for a cluster"""
        try:
            with self._connect() as conn:
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
            with self._connect() as conn:
                conn.execute('''
                    UPDATE clusters 
                    SET subscription_id = ?, subscription_name = ?
                    WHERE id = ?
                ''', (subscription_id, subscription_name, cluster_id))
                conn.commit()
                
            self.logger.info(f"✅ Updated cluster {cluster_id} subscription info: {subscription_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update cluster subscription info: {e}")

    def update_cluster_analysis_without_plan_generation(self, cluster_id: str, analysis_data: dict, enhanced_input: dict = None):
        """
        Update cluster with analysis results - preserves ALL workload data
        (Implementation plans are generated separately via Claude API)
        """
        self.logger.info(f"🔍 DEBUG DATABASE: Received enhanced_input type: {type(enhanced_input)}, is_none: {enhanced_input is None}")
        if enhanced_input:
            self.logger.info(f"🔍 DEBUG DATABASE: Enhanced input keys: {list(enhanced_input.keys())}")
            workloads = enhanced_input.get('workloads', [])
            self.logger.info(f"🔍 DEBUG DATABASE: Enhanced input has {len(workloads)} workloads")
        return self._update_cluster_analysis_internal(cluster_id, analysis_data, enhanced_input)
    
    def _extract_enhanced_input_from_analysis(self, analysis_results: dict) -> dict:
        """
        DISABLED: This method caused data loss by truncating workloads to 100.
        Enhanced input should come from analysis_engine.generate_enhanced_analysis_input()
        """
        self.logger.error("❌ _extract_enhanced_input_from_analysis is disabled - use analysis engine enhanced input generation")
        raise NotImplementedError("This method is disabled - enhanced input should come from analysis engine")
        
        print(f"📦 Extracting enhanced input from analysis results...")
        print(f"   Input size: {len(json.dumps(analysis_results, default=str)):,} bytes")
        print(f"   Input keys: {len(analysis_results)}")
        print(f"🔍 DEBUG: Top-level analysis keys: {list(analysis_results.keys())[:20]}...")
        
        # Debug specific data we're looking for
        print(f"🔍 DEBUG: total_pods = {analysis_results.get('total_pods')}")
        print(f"🔍 DEBUG: total_namespaces = {analysis_results.get('total_namespaces')}")
        print(f"🔍 DEBUG: location = {analysis_results.get('location')}")
        print(f"🔍 DEBUG: kubernetes_version = {analysis_results.get('kubernetes_version')}")
        print(f"🔍 DEBUG: cluster_info = {analysis_results.get('cluster_info', {}).keys() if analysis_results.get('cluster_info') else 'None'}")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 1: CLUSTER INFO (nested structure)
        # ════════════════════════════════════════════════════════════
        
        cluster_info = {
            'cluster_name': analysis_results.get('cluster_name'),
            'resource_group': analysis_results.get('resource_group'),
            'subscription_id': analysis_results.get('subscription_id'),
            'location': analysis_results.get('location'),
            'kubernetes_version': analysis_results.get('kubernetes_version', 'Unknown'),
            'node_count': analysis_results.get('node_count', 0),
            'total_pods': analysis_results.get('total_pods', 0),
            'total_namespaces': analysis_results.get('total_namespaces', 0)
        }
        
        # Extract from nested cluster_info if exists
        nested_cluster_info = analysis_results.get('cluster_info', {})
        if isinstance(nested_cluster_info, dict):
            for key in cluster_info.keys():
                if nested_cluster_info.get(key) is not None:
                    cluster_info[key] = nested_cluster_info[key]
        
        # ════════════════════════════════════════════════════════════
        # SECTION 2: COST ANALYSIS (nested structure, no bloat)
        # ════════════════════════════════════════════════════════════
        
        cost_analysis = {
            'total_monthly_cost': analysis_results.get('total_cost', 0),
            'compute_cost': analysis_results.get('node_cost', 0),
            'storage_cost': analysis_results.get('storage_cost', 0),
            'network_cost': analysis_results.get('network_cost', 0),
            'potential_savings': analysis_results.get('potential_monthly_savings', 0),
            'cost_breakdown_by_namespace': analysis_results.get('namespace_costs', [])[:20],  # Limit to top 20
            'cost_trend': analysis_results.get('cost_trend_summary', {})
        }
        
        # ════════════════════════════════════════════════════════════
        # SECTION 3: WORKLOADS (limit to essentials)
        # ════════════════════════════════════════════════════════════
        
        raw_workloads = analysis_results.get('workloads', [])
        print(f"🔍 DEBUG: Initial workloads count = {len(raw_workloads)}")
        
        # Try different sources for workload data
        if not raw_workloads:
            workload_sources = [
                'hpa_recommendations.workload_characteristics.all_workloads',
                'workload_characteristics.all_workloads',
                'pod_resource_data.all_workloads',
                'workload_cpu_analysis.all_workloads',
                'workload_cpu_analysis.raw_workload_data'
            ]
            
            for source_path in workload_sources:
                try:
                    current_data = analysis_results
                    for part in source_path.split('.'):
                        if isinstance(current_data, dict) and part in current_data:
                            current_data = current_data[part]
                        else:
                            current_data = None
                            break
                    
                    if isinstance(current_data, list) and current_data:
                        raw_workloads = current_data
                        break
                except Exception:
                    continue
        
        # Clean workloads (removed arbitrary 100-workload limit to preserve all data)
        workloads = []
        for wl in raw_workloads:  # Process ALL workloads
            if not isinstance(wl, dict):
                continue
                
            workloads.append({
                'namespace': wl.get('namespace'),
                'name': wl.get('name'),
                'kind': wl.get('kind', 'Deployment'),
                'replicas': wl.get('replicas', 1),
                
                # Resource requests
                'cpu_request': wl.get('cpu_request'),
                'memory_request': wl.get('memory_request'),
                'cpu_limit': wl.get('cpu_limit'),
                'memory_limit': wl.get('memory_limit'),
                
                # Usage metrics
                'cpu_usage_avg': wl.get('cpu_usage_avg'),
                'memory_usage_avg': wl.get('memory_usage_avg'),
                'cpu_usage_p95': wl.get('cpu_usage_p95'),
                'memory_usage_p95': wl.get('memory_usage_p95'),
                
                # Analysis
                'is_over_provisioned': wl.get('over_provisioned', False),
                'is_under_provisioned': wl.get('under_provisioned', False),
                'optimization_potential': wl.get('optimization_potential', 0),
                'estimated_savings': wl.get('estimated_monthly_savings', 0),
                
                # HPA info
                'has_hpa': wl.get('has_hpa', False),
                'hpa_suitable': wl.get('hpa_suitability_score', 0) > 70
            })
        
        print(f"   Workloads: {len(raw_workloads)} → {len(workloads)} (limited)")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 4: HPAs (current state)
        # ════════════════════════════════════════════════════════════
        
        hpas = analysis_results.get('hpas', [])
        
        # Try alternate sources for HPA data
        if not hpas:
            hpa_sources = ['hpa_recommendations', 'hpa_analysis', 'hpa_data']
            for source in hpa_sources:
                hpa_data = analysis_results.get(source, {})
                if isinstance(hpa_data, dict):
                    hpas = hpa_data.get('hpas', []) or hpa_data.get('current_hpas', [])
                    if hpas:
                        break
        
        # Clean HPA data
        cleaned_hpas = []
        for hpa in hpas:
            if not isinstance(hpa, dict):
                continue
                
            cleaned_hpas.append({
                'name': hpa.get('name'),
                'namespace': hpa.get('namespace'),
                'target_deployment': hpa.get('target_ref'),
                'min_replicas': hpa.get('min_replicas'),
                'max_replicas': hpa.get('max_replicas'),
                'current_replicas': hpa.get('current_replicas'),
                'target_cpu': hpa.get('target_cpu_utilization'),
                'target_memory': hpa.get('target_memory_utilization'),
                'current_cpu': hpa.get('current_cpu_utilization'),
                'current_memory': hpa.get('current_memory_utilization'),
                'scaling_events_7d': hpa.get('scaling_events_last_7_days', 0)
            })
        
        print(f"   HPAs: {len(cleaned_hpas)}")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 5: OPTIMIZATION OPPORTUNITIES (top opportunities)
        # ════════════════════════════════════════════════════════════
        
        raw_opportunities = analysis_results.get('optimization_opportunities', [])
        
        # Sort by savings and take top 50
        sorted_opps = sorted(
            raw_opportunities,
            key=lambda x: x.get('potential_monthly_savings', 0) if isinstance(x, dict) else 0,
            reverse=True
        )[:50]
        
        opportunities = []
        for opp in sorted_opps:
            if not isinstance(opp, dict):
                continue
                
            opportunities.append({
                'type': opp.get('type'),
                'severity': opp.get('severity', 'medium'),
                'workload': opp.get('workload_name'),
                'namespace': opp.get('namespace'),
                'description': opp.get('description'),
                'current_state': opp.get('current_state'),
                'recommended_action': opp.get('recommended_action'),
                'potential_savings': opp.get('potential_monthly_savings', 0),
                'implementation_difficulty': opp.get('difficulty', 'medium'),
                'risk_level': opp.get('risk', 'low')
            })
        
        print(f"   Opportunities: {len(raw_opportunities)} → {len(opportunities)} (top 50)")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 6: NAMESPACE SUMMARY
        # ════════════════════════════════════════════════════════════
        
        namespace_summary = analysis_results.get('namespace_summary', [])
        
        cleaned_ns = []
        for ns in namespace_summary:
            if not isinstance(ns, dict):
                continue
                
            cleaned_ns.append({
                'name': ns.get('name'),
                'workload_count': ns.get('workload_count', 0),
                'total_cost': ns.get('total_cost', 0),
                'total_pods': ns.get('pod_count', 0),
                'cpu_request_total': ns.get('total_cpu_request'),
                'memory_request_total': ns.get('total_memory_request'),
                'optimization_opportunities': ns.get('optimization_count', 0)
            })
        
        print(f"   Namespaces: {len(cleaned_ns)}")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 7: NODE POOLS (if available)
        # ════════════════════════════════════════════════════════════
        
        node_pools = []
        if 'node_pools' in analysis_results:
            for pool in analysis_results['node_pools']:
                if not isinstance(pool, dict):
                    continue
                    
                node_pools.append({
                    'name': pool.get('name'),
                    'vm_size': pool.get('vm_size'),
                    'node_count': pool.get('count', 0),
                    'cpu_per_node': pool.get('cpu_cores'),
                    'memory_per_node': pool.get('memory_gb'),
                    'avg_cpu_utilization': pool.get('avg_cpu_utilization'),
                    'avg_memory_utilization': pool.get('avg_memory_utilization'),
                    'monthly_cost': pool.get('monthly_cost', 0)
                })
        
        # ════════════════════════════════════════════════════════════
        # ASSEMBLE ENHANCED INPUT (structured, nested)
        # ════════════════════════════════════════════════════════════
        
        enhanced_input = {
            'cluster_info': cluster_info,
            'cost_analysis': cost_analysis,
            'workloads': workloads,
            'hpas': cleaned_hpas,
            'optimization_opportunities': opportunities,
            'namespace_summary': cleaned_ns,
            'node_pools': node_pools
        }
        
        # Validate output
        output_size = len(json.dumps(enhanced_input, default=str))
        print(f"   Output size: {output_size:,} bytes")
        print(f"   Output keys: {len(enhanced_input)}")
        
        input_size = len(json.dumps(analysis_results, default=str))
        if input_size > 0:
            reduction = (1 - output_size/input_size)*100
            print(f"   Size reduction: {reduction:.1f}%")
        
        if output_size > 1_000_000:
            print(f"   ⚠️ WARNING: Output still over 1MB, may need more reduction")
        
        return enhanced_input

    def update_cluster_analysis(self, cluster_id: str, analysis_data: dict, enhanced_input: dict = None):
        """
        Update cluster with analysis results - preserves ALL workload data
        (Implementation plans are generated separately via Claude API)
        """
        return self._update_cluster_analysis_internal(cluster_id, analysis_data, enhanced_input)
    
    def _update_cluster_analysis_internal(self, cluster_id: str, analysis_data: dict, enhanced_input: dict = None):
        """
        Internal method for updating cluster analysis (plan generation is handled separately)
        """
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG: _update_cluster_analysis_internal called")
        print(f"  cluster_id: {cluster_id}")
        print(f"  analysis_data type: {type(analysis_data)}")
        print(f"  analysis_data keys: {list(analysis_data.keys())[:10]}...")  # First 10 keys
        
        # VALIDATE INPUTS FIRST
        if not cluster_id:
            raise ValueError("cluster_id is required")
        
        if not isinstance(analysis_data, dict):
            raise TypeError(f"analysis_data must be dict, got {type(analysis_data)}")
        
        if not analysis_data:
            raise ValueError("analysis_data cannot be empty")
        
        # Extract cluster_name from analysis_data with validation
        cluster_info = analysis_data.get("cluster_info", {})
        cluster_name = None
        
        if isinstance(cluster_info, dict):
            cluster_name = cluster_info.get("cluster_name")
            print(f"  cluster_info type: {type(cluster_info)}")
            print(f"  cluster_info keys: {list(cluster_info.keys())}")
            print(f"  cluster_name in cluster_info: {'cluster_name' in cluster_info}")
        else:
            print(f"  ⚠️ cluster_info NOT A DICT: {type(cluster_info)}")
        
        if not cluster_name:
            # Try alternate locations
            cluster_name = analysis_data.get("cluster_name")
            print(f"  cluster_name from root: {cluster_name}")
        
        if not cluster_name:
            cluster_name = cluster_id
            print(f"  ⚠️ cluster_name not found in analysis_data, using cluster_id: {cluster_id}")
        
        print(f"  ✓ Final cluster_name: {cluster_name}")
        print(f"{'='*60}\n")
        
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
            
            if has_node_data is not None and has_node_data:
                node_data = None
                for key in ['nodes', 'node_metrics', 'real_node_data']:
                    if enhanced_analysis_data.get(key):
                        node_data = enhanced_analysis_data[key]
                        break
                
                if node_data is not None and node_data:
                    enhanced_analysis_data['nodes'] = node_data
                    enhanced_analysis_data['node_metrics'] = node_data
                    enhanced_analysis_data['real_node_data'] = node_data
            
            # ===== CRITICAL FIX: PRESERVE ALL WORKLOAD DATA IN DATABASE =====
            workload_data_preserved = False
            total_workloads_saved = 0
            
            # Check for ALL workload data sources and preserve them
            workload_sources = [
                ('hpa_recommendations.workload_characteristics.all_workloads', 'HPA recommendations'),
                ('workload_characteristics.all_workloads', 'ML workload characteristics'),
                ('pod_resource_data.all_workloads', 'Pod resource data'),
                ('workload_cpu_analysis.all_workloads', 'Workload CPU analysis'),
                ('workload_cpu_analysis.raw_workload_data', 'Raw workload data')
            ]
            
            # Extract and preserve ALL workload data from various sources
            all_preserved_workloads = []
            
            for source_path, source_name in workload_sources:
                try:
                    # Navigate nested dictionary path
                    current_data = enhanced_analysis_data
                    path_parts = source_path.split('.')
                    
                    for part in path_parts:
                        if isinstance(current_data, dict) and part in current_data:
                            current_data = current_data[part]
                        else:
                            current_data = None
                            break
                    
                    if current_data and isinstance(current_data, list) and len(current_data) > 0:
                        # Found workload data - preserve it
                        for workload in current_data:
                            if isinstance(workload, dict):
                                # Ensure each workload has required fields
                                preserved_workload = {
                                    'name': workload.get('name', workload.get('pod', 'unknown')),
                                    'namespace': workload.get('namespace', 'unknown'),
                                    'cpu_utilization': workload.get('cpu_utilization', workload.get('cpu_percentage', 0)),
                                    'cpu_millicores': workload.get('cpu_millicores', 0),
                                    'memory_bytes': workload.get('memory_bytes', 0),
                                    'severity': workload.get('severity', 'normal'),
                                    'type': workload.get('type', 'unknown'),
                                    'source': source_name,
                                    'preserved_at': datetime.now().isoformat()
                                }
                                
                                # Avoid duplicates
                                existing = any(
                                    w['name'] == preserved_workload['name'] and 
                                    w['namespace'] == preserved_workload['namespace']
                                    for w in all_preserved_workloads
                                )
                                
                                if not existing:
                                    all_preserved_workloads.append(preserved_workload)
                        
                        self.logger.info(f"✅ DB SAVE: Preserved {len(current_data)} workloads from {source_name}")
                        workload_data_preserved = True
                    
                except Exception as source_error:
                    self.logger.debug(f"🔧 DB SAVE: Could not extract from {source_path}: {source_error}")
                    continue
            
            # Store ALL preserved workloads in the analysis data
            if all_preserved_workloads is not None and all_preserved_workloads:
                enhanced_analysis_data['all_workloads_preserved'] = all_preserved_workloads
                enhanced_analysis_data['total_workloads_preserved'] = len(all_preserved_workloads)
                total_workloads_saved = len(all_preserved_workloads)
                
                # Create namespace breakdown
                namespace_breakdown = {}
                severity_breakdown = {'normal': 0, 'moderate': 0, 'high': 0, 'critical': 0}
                
                for workload in all_preserved_workloads:
                    namespace = workload['namespace']
                    severity = workload['severity']
                    
                    namespace_breakdown[namespace] = namespace_breakdown.get(namespace, 0) + 1
                    severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
                
                enhanced_analysis_data['workload_namespace_breakdown'] = namespace_breakdown
                enhanced_analysis_data['workload_severity_breakdown'] = severity_breakdown
                
                self.logger.info(f"✅ DB SAVE: Preserved {total_workloads_saved} total workloads across {len(namespace_breakdown)} namespaces")
                self.logger.info(f"✅ DB SAVE: Severity breakdown - normal: {severity_breakdown['normal']}, moderate: {severity_breakdown['moderate']}, high: {severity_breakdown['high']}, critical: {severity_breakdown['critical']}")
            
            # ===== PRESERVE HIGH CPU DATA FOR COMPATIBILITY =====
            high_cpu_workloads_saved = 0
            if 'hpa_recommendations' not in analysis_data:
                self.logger.warning(f"⚠️ DB SAVE: No HPA recommendations for {cluster_id}")
            else:
                self.logger.info(f"✅ DB SAVE: HPA recommendations found for {cluster_id}")
                
                # Validate HPA structure
                hpa_recs = analysis_data['hpa_recommendations']
                if isinstance(hpa_recs, dict) and 'optimization_recommendation' in hpa_recs:
                    self.logger.info(f"✅ DB SAVE: HPA structure validated for {cluster_id}")
                    
                    # Extract high CPU workloads for compatibility
                    workload_chars = hpa_recs.get('workload_characteristics', {})
                    high_cpu_workloads = workload_chars.get('high_cpu_workloads', [])
                    
                    if high_cpu_workloads is not None and high_cpu_workloads:
                        enhanced_analysis_data['high_cpu_workloads_preserved'] = high_cpu_workloads
                        high_cpu_workloads_saved = len(high_cpu_workloads)
                        self.logger.info(f"✅ DB SAVE: Preserved {high_cpu_workloads_saved} high CPU workloads for compatibility")
                    
                else:
                    self.logger.warning(f"⚠️ DB SAVE: HPA structure incomplete for {cluster_id}")
            
            # Implementation plans are generated separately via Claude API after analysis
            
            # ===== ADD METADATA ABOUT SAVED DATA =====
            enhanced_analysis_data['database_save_metadata'] = {
                'total_workloads_saved': total_workloads_saved,
                'high_cpu_workloads_saved': high_cpu_workloads_saved,
                'workload_data_preserved': workload_data_preserved,
                'all_workloads_unconditionally_saved': True,  # 🆕 Flag indicating fix is applied
                'conditional_save_logic_disabled': True,      # 🆕 Flag indicating conditional logic bypassed
                'saved_at': datetime.now().isoformat(),
                'database_version': 'all_workloads_preserved'
            }
            
            # Use specialized serialization for implementation plan
            serializable_data = serialize_implementation_plan(enhanced_analysis_data)
            
            # 🔍 DATABASE SAVE: Log gap data before storing
            cpu_gap = serializable_data.get('cpu_gap', 'NOT_FOUND')
            memory_gap = serializable_data.get('memory_gap', 'NOT_FOUND')
            self.logger.info(f"🔍 DATABASE SAVE: About to store CPU gap: {cpu_gap}, Memory gap: {memory_gap}")
            self.logger.info(f"🔍 DATABASE SAVE: Serializable data keys: {list(serializable_data.keys())}")
            
            # DEBUG: Check if monitoring_cost is being preserved
            self.logger.info(f"🔍 DB SERIALIZE: monitoring_cost = ${serializable_data.get('monitoring_cost', 0):.2f}")
            self.logger.info(f"🔍 DB SERIALIZE: compute_cost = ${serializable_data.get('compute_cost', 0):.2f}")
            self.logger.info(f"🔍 DB SERIALIZE: total_cost = ${serializable_data.get('total_cost', 0):.2f}")
            
            total_cost = float(serializable_data.get('total_cost', 0))
            total_savings = float(serializable_data.get('total_savings', 0))
            confidence = float(serializable_data.get('analysis_confidence', 0))
            
            # Prepare enhanced analysis data for storage
            enhanced_analysis_blob = None
            
            # CRITICAL FIX: Always use the provided enhanced input (generated by analysis engine)
            # The analysis engine generates the correct enhanced input with full data
            enhanced_input_to_save = enhanced_input
            if not enhanced_input_to_save:
                self.logger.warning(f"⚠️ No enhanced input provided - this should not happen with current flow")
                enhanced_input_to_save = None
            
            if enhanced_input_to_save is not None and enhanced_input_to_save:
                try:
                    enhanced_analysis_blob = json.dumps(enhanced_input_to_save).encode('utf-8')
                    self.logger.info(f"✅ DB SAVE: Enhanced analysis data prepared for storage ({len(enhanced_input_to_save.keys())} sections)")
                except Exception as e:
                    self.logger.error(f"❌ Failed to serialize enhanced analysis data: {e}")
            else:
                self.logger.warning(f"⚠️ No enhanced analysis data to save for {cluster_id}")

            with self._connect() as conn:
                # Set cost_fetched_at timestamp only when cost data is actually present and updated
                current_time = datetime.now().isoformat()
                cost_fetched_time = current_time if total_cost > 0 else None
                
                conn.execute('''
                    UPDATE clusters 
                    SET last_cost = ?, last_savings = ?, last_confidence = ?, 
                        last_analyzed = ?, analysis_data = ?, enhanced_analysis_data = ?,
                        cost_fetched_at = ?
                    WHERE id = ?
                ''', (
                    total_cost, total_savings, confidence,
                    current_time,
                    json.dumps(serializable_data).encode('utf-8'),  # Store as BLOB
                    enhanced_analysis_blob,  # Store enhanced input as BLOB
                    cost_fetched_time,  # Only set if cost data is present
                    cluster_id
                ))
                conn.execute('''
                    INSERT INTO analysis_results 
                    (cluster_id, analysis_date, results, total_cost, total_savings, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    datetime.now().isoformat(),
                    json.dumps(serializable_data).encode('utf-8'),  # Store full analysis as BLOB
                    total_cost,
                    total_savings, 
                    confidence
                ))
                conn.commit()

            # ===== FINAL SUCCESS LOGGING =====
            self.logger.info(f"✅  Updated cluster analysis with ALL workload data preserved: {cluster_id}")
            if total_workloads_saved > 0:
                self.logger.info(f"✅ DATABASE: Saved {total_workloads_saved} total workloads (was only saving {high_cpu_workloads_saved} high CPU)")
            else:
                self.logger.warning(f"⚠️ DATABASE: No workload data found to save for {cluster_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update cluster analysis: {e}")
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

    def get_latest_analysis(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis with enhanced data when available"""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                
                # First try to get enhanced analysis data from clusters table
                cursor = conn.execute('''
                    SELECT analysis_data, enhanced_analysis_data, last_analyzed
                    FROM clusters 
                    WHERE id = ? AND analysis_data IS NOT NULL
                ''', (cluster_id,))
                
                cluster_row = cursor.fetchone()
                
                # If enhanced analysis data exists, return it
                if cluster_row and cluster_row['enhanced_analysis_data']:
                    try:
                        enhanced_data = json.loads(cluster_row['enhanced_analysis_data'].decode('utf-8'))
                        self.logger.info(f"✅ DB LOAD: Loaded enhanced analysis data for {cluster_id}")
                        return enhanced_data
                    except Exception as e:
                        self.logger.error(f"❌ Failed to load enhanced analysis data: {e}")
                        # Fall back to regular analysis data
                
                cursor = conn.execute('''
                    SELECT results, analysis_date, total_cost, total_savings
                    FROM analysis_results 
                    WHERE cluster_id = ? AND results IS NOT NULL
                    ORDER BY analysis_date DESC
                    LIMIT 1
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row and row['results']:
                    try:
                        # Handle both BLOB and TEXT data for compatibility
                        raw_data = row['results']
                        if isinstance(raw_data, bytes):
                            # New BLOB format
                            serialized_data = json.loads(raw_data.decode('utf-8'))
                        else:
                            # Legacy TEXT format
                            serialized_data = json.loads(raw_data)
                        
                        # Use specialized deserialization
                        analysis_data = deserialize_implementation_plan(serialized_data)
                        
                        # 🔍 DATABASE LOAD: Log gap data after loading
                        cpu_gap = analysis_data.get('cpu_gap', 'NOT_FOUND')
                        memory_gap = analysis_data.get('memory_gap', 'NOT_FOUND')
                        self.logger.info(f"🔍 DATABASE LOAD: Loaded CPU gap: {cpu_gap}, Memory gap: {memory_gap}")
                        self.logger.info(f"🔍 DATABASE LOAD: Analysis data keys: {list(analysis_data.keys())}")
                        
                        # Set node data flag
                        has_node_data = False
                        for key in ['nodes', 'node_metrics', 'real_node_data']:
                            if analysis_data.get(key) and len(analysis_data[key]) > 0:
                                has_node_data = True
                                break
                        
                        analysis_data['has_real_node_data'] = has_node_data
                        
                        if has_node_data is not None and has_node_data:
                            node_data = None
                            for key in ['nodes', 'node_metrics', 'real_node_data']:
                                if analysis_data.get(key):
                                    node_data = analysis_data[key]
                                    break
                            
                            if node_data is not None and node_data:
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
                            if isinstance(impl_plan, dict):
                                if 'implementation_phases' in impl_plan:
                                    phases = impl_plan['implementation_phases']
                                    if isinstance(phases, list) and len(phases) > 0:
                                        self.logger.info(f"✅ DB LOAD: Implementation plan has {len(phases)} phases")
                                    else:
                                        self.logger.warning("⚠️ DB LOAD: Implementation plan phases are empty")
                                
                                # ENTERPRISE METRICS: Check if enterprise metrics are present
                                if 'enterprise_metrics' in impl_plan:
                                    ent_metrics = impl_plan['enterprise_metrics']
                                    if isinstance(ent_metrics, dict):
                                        maturity_score = ent_metrics.get('enterprise_maturity', {}).get('score', 'N/A')
                                        self.logger.info(f"✅ DB LOAD: Enterprise metrics found with maturity score: {maturity_score}")
                                    else:
                                        self.logger.warning("⚠️ DB LOAD: Enterprise metrics not a dict")
                                else:
                                    self.logger.warning("⚠️ DB LOAD: No enterprise_metrics in implementation plan")
                            else:
                                self.logger.warning("⚠️ DB LOAD: Implementation plan missing phases structure")
                        else:
                            self.logger.warning("⚠️ DB LOAD: No implementation_plan found in analysis data")
                        
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
    
    def get_enhanced_analysis_data(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get enhanced analysis input for Claude API (NOT full analysis).
        
        Returns structured 200KB enhanced input, not 11MB full analysis.
        
        This is the method that should be called for plan generation.
        """
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT enhanced_analysis_data, analysis_data, last_analyzed
                    FROM clusters 
                    WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if not row:
                    self.logger.warning(f"⚠️ No analysis found for cluster: {cluster_id}")
                    return None
                
                # First try to get enhanced_analysis_data (correct column)
                enhanced_data = row['enhanced_analysis_data']
                
                if enhanced_data is not None and enhanced_data:
                    try:
                        enhanced_input = json.loads(enhanced_data.decode('utf-8'))
                        
                        # Validate it's the right structure
                        if isinstance(enhanced_input, dict):
                            size = len(json.dumps(enhanced_input, default=str))
                            
                            # Check for required keys
                            required = ['cluster_info', 'cost_analysis']
                            if all(k in enhanced_input for k in required):
                                self.logger.info(f"✅ Retrieved enhanced input: {size:,} bytes, {len(enhanced_input)} keys")
                                
                                if size > 1_000_000:
                                    self.logger.warning(f"⚠️ Enhanced input is large: {size:,} bytes")
                                
                                return enhanced_input
                            else:
                                self.logger.warning(f"⚠️ Enhanced input missing required keys: {[k for k in required if k not in enhanced_input]}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to decode enhanced analysis data: {e}")
                
                self.logger.info(f"🔧 enhanced_analysis_data is NULL, extracting from analysis_data...")
                
                analysis_data = row['analysis_data']
                if analysis_data is not None and analysis_data:
                    try:
                        # Load full analysis
                        full_analysis = json.loads(analysis_data.decode('utf-8'))
                        
                        # Disable problematic extraction - enhanced input should come from analysis engine
                        self.logger.warning(f"⚠️ {cluster_id}: No enhanced input available - analysis should provide this")
                        return None
                        return enhanced_input
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to extract enhanced input from analysis_data: {e}")
                
                self.logger.error(f"❌ No usable analysis data available for cluster: {cluster_id}")
                return None
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to get enhanced analysis data: {e}")
            return None

    def _update_enhanced_analysis_data(self, cluster_id: str, enhanced_input: dict):
        """Backfill enhanced_analysis_data for existing records"""
        
        if not cluster_id:
            raise ValueError("cluster_id is required")
        
        if not enhanced_input or not isinstance(enhanced_input, dict):
            raise ValueError("enhanced_input must be a non-empty dictionary")
        
        try:
            enhanced_blob = json.dumps(enhanced_input).encode('utf-8')
            
            with self._connect() as conn:
                conn.execute('''
                    UPDATE clusters
                    SET enhanced_analysis_data = ?
                    WHERE id = ?
                ''', (enhanced_blob, cluster_id))
                conn.commit()
            
            self.logger.info(f"✅ Backfilled enhanced_analysis_data for {cluster_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to backfill enhanced_analysis_data: {e}")
            raise RuntimeError(f"Failed to backfill enhanced analysis data for {cluster_id}: {e}") from e

    def get_enhanced_analysis_input(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get enhanced input for Claude API (NOT full analysis).
        
        Returns structured 200KB enhanced input, not 11MB full analysis.
        This is an alias for get_enhanced_analysis_data() for API consistency.
        """
        return self.get_enhanced_analysis_data(cluster_id)

    def update_analysis_status(self, cluster_id: str, status: str, progress: int = 0, message: str = ""):
        """Update analysis status for a cluster"""
        import traceback
        
        # Log WHO is calling this function when trying to set to failed
        if status == 'failed':
            stack = traceback.extract_stack()
            caller_info = []
            for frame in stack[-4:-1]:  # Get last few frames before this function
                caller_info.append(f"{frame.filename}:{frame.lineno} in {frame.name}")
            
            self.logger.warning(f"🚨 ATTEMPT TO SET {cluster_id} TO FAILED")
            self.logger.warning(f"🚨 Called from: {' -> '.join(caller_info)}")
            self.logger.warning(f"🚨 Message: {message}")
        
        try:
            with self._connect() as conn:
                # DEBUG: Check data before update
                cursor = conn.execute('SELECT last_cost, last_savings, last_analyzed FROM clusters WHERE id = ?', (cluster_id,))
                before_data = cursor.fetchone()
                if before_data is not None and before_data:
                    self.logger.info(f"🔍 BEFORE UPDATE: {cluster_id} → cost: ${before_data[0]}, savings: ${before_data[1]}, analyzed: {before_data[2]}")
                else:
                    self.logger.info(f"🔍 BEFORE UPDATE: {cluster_id} → cluster not found")
                if status == 'analyzing':
                    # Starting analysis - always set start time if not already set
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = ?, analysis_progress = ?, analysis_message = ?, 
                            analysis_started_at = COALESCE(analysis_started_at, ?)
                        WHERE id = ?
                    ''', (status, progress, message, datetime.now().isoformat(), cluster_id))
                else:
                    # Update progress or completion - but preserve successful previous analyses
                    if status == 'failed':
                        # Check current cluster state first
                        check_cursor = conn.execute('''
                            SELECT analysis_status, last_analyzed, last_cost, last_savings 
                            FROM clusters WHERE id = ?
                        ''', (cluster_id,))
                        current_data = check_cursor.fetchone()
                        
                        if current_data is not None and current_data:
                            current_status, last_analyzed, last_cost, last_savings = current_data
                            self.logger.info(f"🔍 BEFORE UPDATE: {cluster_id} → status={current_status}, last_analyzed={last_analyzed}, cost={last_cost}, savings={last_savings}")
                            
                            if last_analyzed is not None and last_analyzed:
                                self.logger.info(f"✅ PRESERVING previous successful analysis for {cluster_id}")
                            else:
                                self.logger.info(f"❌ NO previous analysis found for {cluster_id}, setting to failed")
                        
                        # Don't override successful previous analyses when setting to failed
                        conn.execute('''
                            UPDATE clusters 
                            SET analysis_status = CASE 
                                    WHEN last_analyzed IS NOT NULL THEN 'completed'
                                    ELSE 'failed'
                                END,
                                analysis_progress = CASE 
                                    WHEN last_analyzed IS NOT NULL THEN 100
                                    ELSE ?
                                END,
                                analysis_message = CASE 
                                    WHEN last_analyzed IS NOT NULL THEN 'Previous analysis restored - current attempt failed'
                                    ELSE ?
                                END
                            WHERE id = ?
                        ''', (progress, message, cluster_id))
                        
                        # Check what actually happened
                        check_cursor = conn.execute('''
                            SELECT analysis_status FROM clusters WHERE id = ?
                        ''', (cluster_id,))
                        final_status = check_cursor.fetchone()
                        if final_status is not None and final_status:
                            self.logger.info(f"🔍 AFTER UPDATE: {cluster_id} → final status={final_status[0]}")
                        
                    else:
                        # For non-failed statuses, update normally
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


    def update_analysis_status_with_sse(self, cluster_id: str, status: str, progress: int, message: str):
        """Enhanced status update that also triggers SSE events"""
        try:
            # Update database as before (call existing method)
            self.update_analysis_status(cluster_id, status, progress, message)
            
            # Store in memory for SSE streaming
            status_data = {
                'analysis_status': status,
                'progress': progress,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'cluster_id': cluster_id
            }
            
            # Store for SSE retrieval
            if not hasattr(self, '_sse_status_cache'):
                self._sse_status_cache = {}
            
            self._sse_status_cache[cluster_id] = status_data
            
            logger.info(f"📊 SSE progress update for {cluster_id}: {progress}% - {message}")
            
        except Exception as e:
            logger.error(f"❌ Error updating analysis status with SSE: {e}")

    def get_analysis_status_for_sse(self, cluster_id: str) -> Dict[str, Any]:
        """Get analysis status specifically for SSE streaming"""
        try:
            # Check memory cache first (for real-time updates)
            if hasattr(self, '_sse_status_cache') and cluster_id in self._sse_status_cache:
                return self._sse_status_cache[cluster_id]
            
            return self.get_analysis_status(cluster_id)
            
        except Exception as e:
            logger.error(f"❌ Error getting SSE status for {cluster_id}: {e}")
            return {}    

    def get_analysis_status(self, cluster_id: str) -> Optional[Dict]:
        """Get current analysis status for a cluster"""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT analysis_status, analysis_progress, analysis_message, 
                        analysis_started_at, last_cost, last_savings, last_analyzed
                    FROM clusters 
                    WHERE id = ?
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row is not None and row:
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
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, name, resource_group, environment, region, description, 
                           status, created_at, last_analyzed, last_cost, last_savings, 
                           last_confidence, analysis_count, metadata, analysis_status, 
                           analysis_progress, analysis_message, analysis_started_at, 
                           auto_analyze_enabled, subscription_id, subscription_name, 
                           subscription_context_verified, subscription_last_validated
                    FROM clusters 
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
            with self._connect() as conn:
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
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_clusters,
                        SUM(CASE WHEN (analysis_status = 'completed' OR (analysis_status IN ('analyzing', 'running') AND last_analyzed IS NOT NULL)) AND last_cost > 0 THEN last_cost ELSE 0 END) as total_monthly_cost,
                        SUM(CASE WHEN (analysis_status = 'completed' OR (analysis_status IN ('analyzing', 'running') AND last_analyzed IS NOT NULL)) AND last_savings > 0 THEN last_savings ELSE 0 END) as total_potential_savings,
                        AVG(CASE WHEN (analysis_status = 'completed' OR (analysis_status IN ('analyzing', 'running') AND last_analyzed IS NOT NULL)) AND last_cost > 0 THEN (last_savings/last_cost)*100 ELSE 0 END) as avg_optimization_pct,
                        COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as analyzed_clusters,
                        COUNT(CASE WHEN analysis_status = 'pending' THEN 1 END) as pending_clusters,
                        COUNT(CASE WHEN analysis_status IN ('analyzing', 'running') THEN 1 END) as analyzing_clusters,
                        COUNT(CASE WHEN analysis_status = 'failed' THEN 1 END) as failed_clusters
                    FROM clusters
                ''')
                
                row = cursor.fetchone()
                if row is not None and row:
                    summary = dict(row)
                    summary['total_monthly_cost'] = summary['total_monthly_cost'] or 0
                    summary['total_potential_savings'] = summary['total_potential_savings'] or 0
                    summary['avg_optimization_pct'] = summary['avg_optimization_pct'] or 0
                    summary['analyzed_clusters'] = summary['analyzed_clusters'] or 0
                    summary['pending_clusters'] = summary['pending_clusters'] or 0
                    summary['analyzing_clusters'] = summary['analyzing_clusters'] or 0
                    summary['failed_clusters'] = summary['failed_clusters'] or 0
                    summary['last_updated'] = datetime.now().isoformat()
                
                    
                    # DEBUG: Show actual cluster data (debug level only)
                    debug_cursor = conn.execute('SELECT id, name, status, analysis_status, last_cost, last_savings, last_analyzed, LENGTH(analysis_data) as data_size FROM clusters LIMIT 5')
                    self.logger.debug(f"🔍 Actual cluster data:")
                    for row in debug_cursor.fetchall():
                        self.logger.debug(f"   Cluster: {row[1]}, status: {row[2]}, analysis_status: {row[3]}, cost: ${row[4]}, savings: ${row[5]}, analyzed: {row[6]}, data_size: {row[7]} bytes")
                    
                    # Get environments
                    env_cursor = conn.execute('SELECT DISTINCT environment FROM clusters')
                    summary['environments'] = [row[0] for row in env_cursor.fetchall()]
                    
                    return summary
                
            raise ValueError("No cluster data found")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get portfolio summary: {e}")
            raise ValueError(f"Failed to get portfolio summary: {e}")

    def get_enhanced_portfolio_summary(self) -> Dict:
        """Get enhanced portfolio summary with analysis status"""
        try:
            with self._connect() as conn:
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
            with self._connect() as conn:
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
            with self._connect() as conn:
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
            
            with self._connect() as conn:
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

    # Old JSON-based plan storage methods removed - now using markdown-only approach

    # get_plan_by_id removed - use save_implementation_plan/markdown approach instead

    def list_plans_for_cluster(self, cluster_id: str, limit: int = 10) -> List[Dict]:
        """List recent plans for a cluster"""
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT plan_id, generated_at, total_savings, total_actions, 
                           executed, execution_status, version, generated_by
                    FROM implementation_plans
                    WHERE cluster_id = ?
                    ORDER BY generated_at DESC
                    LIMIT ?
                """, (cluster_id, limit))
                
                plans = []
                for row in cursor.fetchall():
                    plans.append({
                        'plan_id': row[0],
                        'generated_at': row[1],
                        'total_savings': row[2],
                        'total_actions': row[3],
                        'executed': bool(row[4]),
                        'execution_status': row[5],
                        'version': row[6],
                        'generated_by': row[7]
                    })
                
                return plans
                
        except Exception as e:
            self.logger.error(f"❌ Failed to list plans for cluster {cluster_id}: {e}")
            return []

    def mark_plan_executed(self, plan_id: str, execution_status: str = "completed"):
        """Mark a plan as executed"""
        try:
            with self._connect() as conn:
                conn.execute("""
                    UPDATE implementation_plans 
                    SET executed = 1, execution_status = ?
                    WHERE plan_id = ?
                """, (execution_status, plan_id))
                
                conn.commit()
                self.logger.info(f"✅ Marked plan {plan_id} as executed with status: {execution_status}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to mark plan {plan_id} as executed: {e}")

    def cleanup_old_plans(self, days_to_keep: int = 30):
        """Clean up old implementation plans to maintain database size"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self._connect() as conn:
                cursor = conn.execute('''
                    DELETE FROM implementation_plans 
                    WHERE generated_at < ? 
                    AND plan_id NOT IN (
                        SELECT plan_id FROM implementation_plans 
                        WHERE cluster_id IN (
                            SELECT cluster_id FROM implementation_plans 
                            GROUP BY cluster_id 
                            ORDER BY generated_at DESC 
                            LIMIT 1
                        )
                    )
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                self.logger.info(f"🧹 Cleaned up {cursor.rowcount} old implementation plans")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup old plans: {e}")

    def get_latest_plan(self, cluster_id: str) -> Optional[Dict]:
        """Retrieve most recent plan for cluster as raw dict (markdown format)"""
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT plan_data FROM implementation_plans
                    WHERE cluster_id = ?
                    ORDER BY generated_at DESC
                    LIMIT 1
                """, (cluster_id,))
                
                row = cursor.fetchone()
                if row is not None and row:
                    import json
                    plan_data = json.loads(row[0])
                    self.logger.info(f"✅ Retrieved latest implementation plan for cluster {cluster_id}")
                    return plan_data
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve latest plan for cluster {cluster_id}: {e}")
            return None

    def save_implementation_plan(self, cluster_id: str, plan_data: dict):
        """Save implementation plan to database (supports raw markdown format)"""
        try:
            import json
            from datetime import datetime
            
            # Log plan save
            self.logger.debug(f"📝 Saving plan for cluster {cluster_id}")
            if isinstance(plan_data, dict):
                # Quick validation that we have content
                has_content = 'markdown_content' in plan_data or 'raw_markdown' in plan_data
                if not has_content:
                    self.logger.warning(f"⚠️ Plan data missing markdown_content or raw_markdown fields!")
            
            # Generate plan ID
            plan_id = f"plan_{cluster_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Ensure plan_data is JSON serializable
            plan_json = json.dumps(plan_data, default=str)
            
            # Extract metadata for indexing
            total_savings = 0
            total_actions = 0
            generated_by = plan_data.get('plan_type', 'Claude')
            
            # Try to extract some metrics if available
            if 'total_monthly_savings' in plan_data:
                total_savings = plan_data['total_monthly_savings']
            
            with self._connect() as conn:
                conn.execute("""
                    INSERT INTO implementation_plans 
                    (plan_id, cluster_id, analysis_id, plan_data, generated_at, 
                     total_savings, total_actions, version, generated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_id,
                    cluster_id,
                    None,  # analysis_id
                    plan_json.encode('utf-8'),  # Store as BLOB
                    datetime.utcnow().isoformat(),
                    total_savings,
                    total_actions,
                    "2.0",  # version for new markdown format
                    generated_by
                ))
                
                conn.commit()
                self.logger.info(f"✅ Saved implementation plan {plan_id} for cluster {cluster_id}")
                return plan_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save implementation plan: {e}")
            raise

    def store_implementation_plan(self, cluster_id: str, implementation_plan, analysis_id: str = None) -> str:
        """
        Store implementation plan - wrapper for save_implementation_plan with analysis_engine compatibility
        Expected by analysis_engine.py for Claude-generated plans
        """
        try:
            # Convert plan object to dict if needed (for Pydantic models)
            if hasattr(implementation_plan, 'model_dump'):
                plan_data = implementation_plan.model_dump()
            elif hasattr(implementation_plan, 'dict'):
                plan_data = implementation_plan.dict()
            elif isinstance(implementation_plan, dict):
                plan_data = implementation_plan
            else:
                plan_data = {'raw_plan': str(implementation_plan)}
            
            # Add analysis_id if provided
            if analysis_id:
                plan_data['analysis_id'] = analysis_id
            
            # Use existing save_implementation_plan method
            plan_id = self.save_implementation_plan(cluster_id, plan_data)
            
            self.logger.info(f"✅ Stored implementation plan {plan_id} for cluster {cluster_id}")
            return plan_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store implementation plan for {cluster_id}: {e}")
            raise

    def _extract_enhanced_input_from_analysis(self, analysis_results: dict) -> dict:
        """
        DISABLED: This method caused data loss by truncating workloads to 100.
        Enhanced input should come from analysis_engine.generate_enhanced_analysis_input()
        """
        self.logger.error("❌ _extract_enhanced_input_from_analysis is disabled - use analysis engine enhanced input generation")
        raise NotImplementedError("This method is disabled - enhanced input should come from analysis engine")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 1: CLUSTER INFO (nested structure)
        # ════════════════════════════════════════════════════════════
        
        cluster_info = {
            'cluster_name': analysis_results.get('cluster_name'),
            'resource_group': analysis_results.get('resource_group'),
            'subscription_id': analysis_results.get('subscription_id'),
            'location': analysis_results.get('location', 'Unknown'),
            'kubernetes_version': analysis_results.get('kubernetes_version', 'Unknown'),
            'node_count': analysis_results.get('current_node_count', 0),
            'total_pods': analysis_results.get('total_pods', 0),
            'total_namespaces': analysis_results.get('total_namespaces', 0),
            'analysis_timestamp': analysis_results.get('analysis_timestamp', datetime.now().isoformat())
        }
        
        # ════════════════════════════════════════════════════════════
        # SECTION 2: COST ANALYSIS (nested structure, no bloat)
        # ════════════════════════════════════════════════════════════
        
        cost_analysis = {
            'total_monthly_cost': analysis_results.get('total_cost', 0),
            'compute_cost': analysis_results.get('node_cost', 0),
            'storage_cost': analysis_results.get('storage_cost', 0),
            'network_cost': analysis_results.get('networking_cost', 0),
            'control_plane_cost': analysis_results.get('control_plane_cost', 0),
            'registry_cost': analysis_results.get('registry_cost', 0),
            'other_cost': analysis_results.get('other_cost', 0),
            'potential_monthly_savings': analysis_results.get('total_savings', 0),
            'savings_percentage': analysis_results.get('savings_percentage', 0),
            'cost_period_days': analysis_results.get('analysis_period_days', 30),
            'currency': 'USD'
        }
        
        # Remove the massive cost_data array (6,194 items) - not needed!
        # Claude doesn't need every single cost data point
        
        # ════════════════════════════════════════════════════════════
        # SECTION 3: WORKLOADS (limit to essentials)
        # ════════════════════════════════════════════════════════════
        
        workloads = []
        
        # Get workloads from various sources in the analysis
        workload_sources = []
        if 'all_workloads_preserved' in analysis_results:
            workload_sources = analysis_results['all_workloads_preserved']
        elif 'workloadData' in analysis_results:
            workload_sources = analysis_results['workloadData'].get('workloads', [])
        elif 'workloads' in analysis_results:
            workload_sources = analysis_results['workloads']
        
        # Clean workloads (removed arbitrary 100-workload limit to preserve all data)
        for wl in workload_sources:  # Process ALL workloads
            workloads.append({
                'namespace': wl.get('namespace'),
                'name': wl.get('name'),
                'type': wl.get('kind', wl.get('type', 'Deployment')),
                'replicas': wl.get('replicas', 1),
                
                # Resource requests
                'resources': {
                    'requests': {
                        'cpu': wl.get('cpu_request', wl.get('cpu_millicores_request')),
                        'memory': wl.get('memory_request', wl.get('memory_bytes_request'))
                    },
                    'limits': {
                        'cpu': wl.get('cpu_limit'),
                        'memory': wl.get('memory_limit')
                    }
                },
                
                # Usage metrics
                'actual_usage': {
                    'cpu': {
                        'avg_millicores': wl.get('cpu_usage_avg'),
                        'avg_percentage': wl.get('cpu_percentage')
                    },
                    'memory': {
                        'avg_bytes': wl.get('memory_usage_avg'),
                        'avg_percentage': wl.get('memory_percentage')
                    }
                },
                
                # Analysis flags
                'optimization_candidate': wl.get('over_provisioned', False) or wl.get('under_provisioned', False),
                'optimization_reasons': [],
                'potential_monthly_savings': wl.get('estimated_monthly_savings', 0),
                
                # HPA info
                'has_hpa': wl.get('has_hpa', False),
                'hpa_suitable': wl.get('hpa_suitability_score', 0) > 0.7
            })
            
            # Add optimization reasons
            if wl.get('over_provisioned'):
                workloads[-1]['optimization_reasons'].append('over_provisioned')
            if wl.get('under_provisioned'):
                workloads[-1]['optimization_reasons'].append('under_provisioned')
            if wl.get('cpu_percentage', 0) < 20:
                workloads[-1]['optimization_reasons'].append('low_cpu_utilization')
            if wl.get('memory_percentage', 0) < 20:
                workloads[-1]['optimization_reasons'].append('low_memory_utilization')
        
        print(f"   Workloads: {len(workload_sources)} → {len(workloads)} (limited)")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 4: OPTIMIZATION OPPORTUNITIES (top opportunities)
        # ════════════════════════════════════════════════════════════
        
        opportunities = []
        
        # Get optimization opportunities from analysis
        raw_opportunities = analysis_results.get('optimization_opportunities', {})
        
        # Process different types of opportunities
        if isinstance(raw_opportunities, dict):
            # Process HPA opportunities
            hpa_ops = raw_opportunities.get('hpa_scaling', [])
            for opp in hpa_ops[:20]:  # Top 20 HPA opportunities
                opportunities.append({
                    'type': 'hpa_scaling',
                    'workload': opp.get('name'),
                    'namespace': opp.get('namespace'),
                    'description': f"Enable HPA scaling for {opp.get('name')}",
                    'current_state': f"Fixed replicas: {opp.get('current_replicas', 'unknown')}",
                    'recommended_action': f"Set HPA: {opp.get('min_replicas')}-{opp.get('max_replicas')} replicas, {opp.get('cpu_target', 70)}% CPU target",
                    'potential_monthly_savings': opp.get('monthly_savings', 0),
                    'implementation_difficulty': 'medium',
                    'risk_level': 'low'
                })
            
            # Process rightsizing opportunities
            rightsizing_ops = raw_opportunities.get('resource_rightsizing', [])
            for opp in rightsizing_ops[:20]:  # Top 20 rightsizing opportunities
                opportunities.append({
                    'type': 'resource_rightsizing',
                    'workload': opp.get('workload_name'),
                    'namespace': opp.get('namespace'),
                    'description': f"Rightsize {opp.get('resource_type')} for {opp.get('workload_name')}",
                    'current_state': f"Current {opp.get('resource_type')}: {opp.get('current_value')}",
                    'recommended_action': f"Reduce to {opp.get('recommended_value')} ({opp.get('optimization_ratio', '0%')} reduction)",
                    'potential_monthly_savings': opp.get('monthly_savings', 0),
                    'implementation_difficulty': 'low',
                    'risk_level': 'low'
                })
            
            # Process networking opportunities
            network_ops = raw_opportunities.get('networking', [])
            for opp in network_ops[:10]:  # Top 10 network opportunities
                opportunities.append({
                    'type': 'networking_optimization',
                    'workload': 'cluster-wide',
                    'namespace': 'all',
                    'description': opp.get('description', 'Network optimization'),
                    'current_state': f"Current configuration",
                    'recommended_action': opp.get('implementation', 'Optimize network configuration'),
                    'potential_monthly_savings': opp.get('monthly_savings', 0),
                    'implementation_difficulty': 'medium',
                    'risk_level': 'medium'
                })
        
        # ENHANCED: Add expert-level optimization opportunities from enhanced analysis
        #self._add_expert_optimization_opportunities(opportunities, analysis_results)
        
        # Sort by savings and take top 50
        opportunities = sorted(opportunities, key=lambda x: x.get('potential_monthly_savings', 0), reverse=True)[:50]
        
        print(f"   Opportunities: {len(opportunities)} (top opportunities)")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 5: NODE POOLS (if available)
        # ════════════════════════════════════════════════════════════
        
        node_pools = []
        if 'nodes' in analysis_results:
            # Extract node pool information
            nodes = analysis_results['nodes']
            if isinstance(nodes, list) and len(nodes) > 0:
                # Group nodes by VM SKU to create node pools
                node_groups = {}
                for node in nodes:
                    vm_sku = node.get('vm_sku', 'Unknown')
                    if vm_sku not in node_groups:
                        node_groups[vm_sku] = []
                    node_groups[vm_sku].append(node)
                
                for vm_sku, pool_nodes in node_groups.items():
                    if pool_nodes is not None and pool_nodes:
                        first_node = pool_nodes[0]
                        avg_cpu = sum(n.get('cpu_percentage', 0) for n in pool_nodes) / len(pool_nodes)
                        avg_memory = sum(n.get('memory_percentage', 0) for n in pool_nodes) / len(pool_nodes)
                        
                        node_pools.append({
                            'name': f"pool-{vm_sku.lower()}",
                            'vm_sku': vm_sku,
                            'node_count': len(pool_nodes),
                            'cpu_cores_per_node': first_node.get('cpu_cores', 0),
                            'memory_gb_per_node': first_node.get('memory_gb', 0),
                            'utilization': {
                                'cpu_percentage': round(avg_cpu, 1),
                                'memory_percentage': round(avg_memory, 1)
                            },
                            'monthly_cost': sum(n.get('monthly_cost', 0) for n in pool_nodes)
                        })
        
        print(f"   Node pools: {len(node_pools)}")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 6: NAMESPACE SUMMARY
        # ════════════════════════════════════════════════════════════
        
        namespace_summary = []
        namespace_data = analysis_results.get('namespaceData', {})
        if isinstance(namespace_data, dict):
            for ns_name, ns_info in namespace_data.items():
                if isinstance(ns_info, dict):
                    namespace_summary.append({
                        'name': ns_name,
                        'workload_count': ns_info.get('workload_count', 0),
                        'pod_count': ns_info.get('pod_count', 0),
                        'total_cost': ns_info.get('total_cost', 0),
                        'cpu_request_total': ns_info.get('total_cpu_request'),
                        'memory_request_total': ns_info.get('total_memory_request'),
                        'optimization_opportunities': ns_info.get('optimization_count', 0)
                    })
        
        # If no namespace data, try namespace_costs
        if not namespace_summary and 'namespace_costs' in analysis_results:
            ns_costs = analysis_results['namespace_costs']
            if isinstance(ns_costs, dict):
                for ns_name, cost in ns_costs.items():
                    namespace_summary.append({
                        'name': ns_name,
                        'workload_count': 0,
                        'pod_count': 0,
                        'total_cost': cost,
                        'optimization_opportunities': 0
                    })
        
        print(f"   Namespaces: {len(namespace_summary)}")
        
        # ════════════════════════════════════════════════════════════
        # SECTION 7: METADATA
        # ════════════════════════════════════════════════════════════
        
        metadata = {
            'schema_version': '2.0.0',
            'collection_timestamp': analysis_results.get('analysis_timestamp', datetime.now().isoformat()),
            'analysis_method': analysis_results.get('analysis_method', 'comprehensive_ml'),
            'data_quality_score': analysis_results.get('data_quality_score', 0),
            'analysis_confidence': analysis_results.get('analysis_confidence', 0),
            'analysis_scope': {
                'cost_analysis_period_days': analysis_results.get('analysis_period_days', 30),
                'metrics_lookback_days': 7,
                'include_system_namespaces': False
            }
        }
        
        # ════════════════════════════════════════════════════════════
        # ASSEMBLE ENHANCED INPUT (structured, nested)
        # ════════════════════════════════════════════════════════════
        
        enhanced_input = {
            'cluster_info': cluster_info,
            'cost_analysis': cost_analysis,
            'workloads': workloads,
            'optimization_opportunities': opportunities,
            'node_pools': node_pools,
            'namespace_summary': namespace_summary,
            'metadata': metadata
        }
        
        # Validate output
        output_size = len(json.dumps(enhanced_input, default=str))
        print(f"   Output size: {output_size:,} bytes")
        print(f"   Output keys: {len(enhanced_input)}")
        input_size = len(json.dumps(analysis_results, default=str))
        print(f"   Size reduction: {(1 - output_size/input_size)*100:.1f}%")
        
        if output_size > 1_000_000:
            print(f"   ⚠️ WARNING: Output still over 1MB, may need more reduction")
        
        return enhanced_input


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