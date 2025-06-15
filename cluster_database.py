# cluster_database.py - Enhanced Cluster Manager with SQLite
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class EnhancedClusterManager:
    """Enhanced cluster manager with SQLite database for enterprise use"""
    
    def __init__(self, db_path="clusters.db"):
        self.db_path = db_path
        self.init_database()
        # Enhance schema for auto-analysis
        self.enhance_database_for_auto_analysis()
        # Clean up any stale analyses on startup
        self.cleanup_stale_analyses()
        
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                        analysis_count INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}'
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
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

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
    
    def update_cluster_analysis(self, cluster_id: str, analysis_results: Dict):
        """Update cluster with latest analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update cluster record
                conn.execute('''
                    UPDATE clusters 
                    SET last_analyzed = ?, last_cost = ?, last_savings = ?, analysis_count = analysis_count + 1
                    WHERE id = ?
                ''', (
                    datetime.now().isoformat(),
                    analysis_results.get('total_cost', 0),
                    analysis_results.get('total_savings', 0),
                    cluster_id
                ))
                
                # Store full analysis results
                conn.execute('''
                    INSERT INTO analysis_results 
                    (cluster_id, results, total_cost, total_savings, confidence_level)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    json.dumps(analysis_results),
                    analysis_results.get('total_cost', 0),
                    analysis_results.get('total_savings', 0),
                    analysis_results.get('confidence_level', 'Medium')
                ))
                
                conn.commit()
                logger.info(f"✅ Updated cluster analysis: {cluster_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update cluster analysis: {e}")
            raise
    
    def get_latest_analysis(self, cluster_id: str) -> Optional[Dict]:
        """Get latest analysis results for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM analysis_results 
                    WHERE cluster_id = ? 
                    ORDER BY analysis_date DESC 
                    LIMIT 1
                ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row:
                    analysis = dict(row)
                    analysis['results'] = json.loads(analysis['results'])
                    return analysis['results']
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get latest analysis for {cluster_id}: {e}")
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
                'average_optimization_pct': 0,
                'environments': [],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio summary: {e}")
            return {
                'total_clusters': 0,
                'total_monthly_cost': 0,
                'total_potential_savings': 0,
                'average_optimization_pct': 0,
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
        """Enhance database schema to support auto-analysis tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if columns already exist
                cursor = conn.execute("PRAGMA table_info(clusters)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                
                # Add new columns for analysis tracking
                if 'analysis_status' not in existing_columns:
                    conn.execute('ALTER TABLE clusters ADD COLUMN analysis_status TEXT DEFAULT "pending"')
                    logger.info("✅ Added analysis_status column")
                
                if 'analysis_progress' not in existing_columns:
                    conn.execute('ALTER TABLE clusters ADD COLUMN analysis_progress INTEGER DEFAULT 0')
                    logger.info("✅ Added analysis_progress column")
                
                if 'analysis_message' not in existing_columns:
                    conn.execute('ALTER TABLE clusters ADD COLUMN analysis_message TEXT DEFAULT ""')
                    logger.info("✅ Added analysis_message column")
                
                if 'analysis_started_at' not in existing_columns:
                    conn.execute('ALTER TABLE clusters ADD COLUMN analysis_started_at TIMESTAMP NULL')
                    logger.info("✅ Added analysis_started_at column")
                
                if 'auto_analyze_enabled' not in existing_columns:
                    conn.execute('ALTER TABLE clusters ADD COLUMN auto_analyze_enabled BOOLEAN DEFAULT 1')
                    logger.info("✅ Added auto_analyze_enabled column")
                
                conn.commit()
                logger.info("✅ Database schema enhanced for auto-analysis")
                
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