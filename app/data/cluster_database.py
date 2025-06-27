# cluster_database.py - Enhanced Cluster Manager with SQLite
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import traceback
from typing import Any, Dict, List, Optional
import os
from app.ml.implementation_generator import AKSImplementationGenerator

def migrate_database_schema(db_path: str = '../data/database/clusters.db'):
    """Migrate database schema to include analysis_data column and other required columns"""
    import sqlite3
    import logging
    
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

def enhance_database_for_subscriptions(db_path: str = '../data/database/clusters.db'):
    """Add subscription support to database schema"""
    import sqlite3
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if subscription_id column exists
            cursor.execute("PRAGMA table_info(clusters)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            if 'subscription_id' not in existing_columns:
                # Add subscription_id column
                cursor.execute('''
                    ALTER TABLE clusters 
                    ADD COLUMN subscription_id TEXT DEFAULT NULL
                ''')
                logger.info("✅ Added subscription_id column to clusters table")
            
            if 'subscription_name' not in existing_columns:
                # Add subscription_name for display purposes
                cursor.execute('''
                    ALTER TABLE clusters 
                    ADD COLUMN subscription_name TEXT DEFAULT NULL
                ''')
                logger.info("✅ Added subscription_name column to clusters table")
            
            # Create subscription tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    subscription_name TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("✅ Database enhanced for subscription management")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database subscription enhancement failed: {e}")
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
    
logger = logging.getLogger(__name__)

# ==================================================================================================
#
# ==================================================================================================

class EnhancedClusterManager:
    """Enhanced cluster manager with SQLite database for enterprise use"""
    
    def __init__(self, db_path='app/data/database/clusters.db'):
        self.db_path = db_path
        self.init_database()
        # Enhance schema for auto-analysis
        self.enhance_database_for_auto_analysis()
        # Clean up any stale analyses on startup
        self.cleanup_stale_analyses()

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
                logger.info(f"✅ Updated timestamp for cluster {cluster_id}")
        except Exception as e:
            logger.error(f"❌ Failed to touch cluster {cluster_id}: {e}")
                
    def init_database(self):
        """Initialize SQLite database with proper schema including analysis_data"""
        try:
            # First run migration to ensure schema is up to date
            migrate_database_schema(self.db_path)
            
            with sqlite3.connect(self.db_path) as conn:
                # Create clusters table with ALL required columns
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
                        auto_analyze_enabled BOOLEAN DEFAULT 1
                    )
                ''')
                
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
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_cluster_id ON analysis_results(cluster_id);
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date);
                ''')
                
                conn.commit()
                logger.info("✅ Database initialized successfully with complete schema")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def detect_and_update_cluster_subscriptions(self):
        """Detect and update subscription info for existing clusters"""
        logger.info("🔍 Detecting subscription info for existing clusters...")
        
        try:
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
                logger.info("✅ All clusters already have subscription info")
                return True
            
            logger.info(f"🔍 Found {len(clusters_to_update)} clusters to update")
            
            # Import subscription manager
            from app.services.subscription_manager import AzureSubscriptionManager
            sub_manager = AzureSubscriptionManager()
            
            updated_count = 0
            
            for cluster in clusters_to_update:
                cluster_id = cluster['id']
                cluster_name = cluster['name']
                resource_group = cluster['resource_group']
                
                logger.info(f"🔍 Detecting subscription for cluster: {cluster_name}")
                
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
                    
                    logger.info(f"✅ Updated {cluster_name} -> {subscription_name}")
                    updated_count += 1
                else:
                    logger.warning(f"⚠️ Could not find subscription for cluster: {cluster_name}")
            
            logger.info(f"✅ Updated {updated_count} clusters with subscription info")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error detecting cluster subscriptions: {e}")
            return False

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
            logger.error(f"❌ Error getting cluster subscription info: {e}")
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
                
            logger.info(f"✅ Updated cluster {cluster_id} subscription info: {subscription_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update cluster subscription info: {e}")

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
                
            logger.info(f"✅ Added cluster with subscription: {cluster_id} -> {subscription_name}")
            return cluster_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add cluster with subscription: {e}")
            raise

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
                
                logger.info(f"📋 Retrieved {len(clusters)} clusters with subscription info")
                return clusters
                
        except Exception as e:
            logger.error(f"❌ Failed to get clusters with subscription info: {e}")
            return []
    
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
                
            logger.info(f"✅ Added cluster: {cluster_id}")
            return cluster_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add cluster: {e}")
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
            logger.error(f"❌ Failed to get cluster {cluster_id}: {e}")
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
                
                logger.info(f"📋 Listed {len(clusters)} clusters")
                return clusters
                
        except Exception as e:
            logger.error(f"❌ Failed to list clusters: {e}")
            return []
    
    def update_cluster_analysis(self, cluster_id: str, analysis_data: dict):
        """FIXED: Update cluster with analysis results - preserves implementation plan"""
        try:
            enhanced_analysis_data = analysis_data.copy()
            
            # Check for node data and set flag
            has_node_data = False
            for key in ['nodes', 'node_metrics', 'real_node_data']:
                if enhanced_analysis_data.get(key) and len(enhanced_analysis_data[key]) > 0:
                    has_node_data = True
                    logger.info(f"✅ DB SAVE: Found node data in {key} ({len(enhanced_analysis_data[key])} nodes)")
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
                    
                    implementation_generator = AKSImplementationGenerator()
                    implementation_plan = implementation_generator.generate_implementation_plan(enhanced_analysis_data)
                    enhanced_analysis_data['implementation_plan'] = implementation_plan
                    logger.info("✅ Generated implementation plan for database")
                    
                    # Validate the plan has phases
                    if implementation_plan and 'implementation_phases' in implementation_plan:
                        phases_count = len(implementation_plan['implementation_phases'])
                        logger.info(f"✅ Implementation plan has {phases_count} phases")
                        
                except Exception as impl_error:
                    logger.error(f"❌ Failed to generate implementation plan: {impl_error}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Use specialized serialization for implementation plan
            serializable_data = serialize_implementation_plan(enhanced_analysis_data)
            
            total_cost = float(serializable_data.get('total_cost', 0))
            total_savings = float(serializable_data.get('total_savings', 0))
            confidence = float(serializable_data.get('analysis_confidence', 0))
            
            if 'hpa_recommendations' not in analysis_data:
                logger.warning(f"⚠️ DB SAVE: No HPA recommendations for {cluster_id}")
                # Continue saving but log the issue
            else:
                logger.info(f"✅ DB SAVE: HPA recommendations found for {cluster_id}")
                
                # Validate HPA structure
                hpa_recs = analysis_data['hpa_recommendations']
                if isinstance(hpa_recs, dict) and 'optimization_recommendation' in hpa_recs:
                    logger.info(f"✅ DB SAVE: HPA structure validated for {cluster_id}")
                else:
                    logger.warning(f"⚠️ DB SAVE: HPA structure incomplete for {cluster_id}")

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

            # Ensure HPA data is in the JSON that gets saved
            if 'hpa_recommendations' in analysis_data:
                logger.info(f"✅ DB SAVE: Saving analysis with HPA recommendations for {cluster_id}")
            else:
                logger.warning(f"⚠️ DB SAVE: Saving analysis WITHOUT HPA recommendations for {cluster_id}")
            
            logger.info(f"✅ Updated cluster analysis with implementation plan: {cluster_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update cluster analysis: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

    def get_latest_analysis(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """FIXED: Get latest analysis with proper implementation plan deserialization"""
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
                            logger.warning(f"⚠️ DB LOAD: No HPA recommendations for {cluster_id}")
                            # Return data anyway, but log the issue
                        else:
                            logger.info(f"✅ DB LOAD: HPA recommendations found for {cluster_id}")
                    
                        
                        # CRITICAL: Validate implementation plan structure
                        if 'implementation_plan' in analysis_data:
                            impl_plan = analysis_data['implementation_plan']
                            if isinstance(impl_plan, dict) and 'implementation_phases' in impl_plan:
                                phases = impl_plan['implementation_phases']
                                if isinstance(phases, list) and len(phases) > 0:
                                    logger.info(f"✅ DB LOAD: Implementation plan has {len(phases)} phases")
                                else:
                                    logger.warning("⚠️ DB LOAD: Implementation plan phases are empty")
                            else:
                                logger.warning("⚠️ DB LOAD: Implementation plan missing phases structure")
                        
                        logger.info(f"📦 Loaded COMPLETE analysis from database: {cluster_id}")
                           
                        return analysis_data
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Failed to decode analysis data: {e}")
                        return None
                else:
                    logger.info(f"ℹ️ No analysis data found for cluster: {cluster_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Database error getting analysis: {e}")
            return None
    
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
            logger.error(f"❌ Failed to get portfolio summary: {e}")
            return {
                'total_clusters': 0,
                'total_monthly_cost': 0,
                'total_potential_savings': 0,
                'avg_optimization_pct': 0,
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
                    logger.info(f"✅ Removed cluster: {cluster_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Cluster not found: {cluster_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to remove cluster {cluster_id}: {e}")
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
            logger.error(f"❌ Failed to get analysis history for {cluster_id}: {e}")
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
                logger.info(f"🧹 Cleaned up {cursor.rowcount} old analysis records")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old analyses: {e}")

        
    # Enhanced cluster_database.py - Add these methods to your EnhancedClusterManager class

    def enhance_database_for_auto_analysis(self):
        """Enhanced method that uses the migration function"""
        try:
            # Use the standardized migration function
            migration_success = migrate_database_schema(self.db_path)
            
            if migration_success:
                logger.info("✅ Database schema enhanced for auto-analysis via migration")
            else:
                logger.warning("⚠️ Some database schema enhancements may have failed")
                
        except Exception as e:
            logger.error(f"❌ Database schema enhancement failed: {e}")
            raise

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
                logger.info(f"✅ Updated analysis status for {cluster_id}: {status} ({progress}%)")
                
        except Exception as e:
            logger.error(f"❌ Failed to update analysis status: {e}")
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
            logger.error(f"❌ Error getting analysis status for {cluster_id}: {e}")
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
            logger.error(f"❌ Error getting clusters by status {status}: {e}")
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
            logger.error(f"❌ Error getting analysis queue status: {e}")
            return {}

    def cleanup_stale_analyses(self, max_age_hours: int = 2):
        """Clean up analyses that have been running too long (likely stale)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                # Find stale analyzing clusters
                cursor = conn.execute('''
                    SELECT id, name FROM clusters 
                    WHERE analysis_status = 'analyzing' 
                    AND analysis_started_at < ?
                ''', (cutoff_time.isoformat(),))
                
                stale_clusters = cursor.fetchall()
                
                if stale_clusters:
                    # Reset stale analyses
                    conn.execute('''
                        UPDATE clusters 
                        SET analysis_status = 'failed', 
                            analysis_progress = 0,
                            analysis_message = 'Analysis timed out and was reset'
                        WHERE analysis_status = 'analyzing' 
                        AND analysis_started_at < ?
                    ''', (cutoff_time.isoformat(),))
                    
                    conn.commit()
                    
                    logger.info(f"🧹 Cleaned up {len(stale_clusters)} stale analyses")
                    return len(stale_clusters)
                
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up stale analyses: {e}")
            return 0

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
            logger.error(f"❌ Error getting enhanced portfolio summary: {e}")
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



# Migration function to convert from JSON to SQLite
def migrate_from_json(json_file_path: str, db_manager: EnhancedClusterManager):
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