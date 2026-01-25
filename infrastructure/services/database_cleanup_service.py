#!/usr/bin/env python3
"""
Database Cleanup Service for AKS Cost Optimizer
===============================================

Automatically cleans up old data from SQLite databases based on retention policies.
Configurable via environment variables and settings page.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

import os
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from pathlib import Path

from infrastructure.services.settings_manager import settings_manager

logger = logging.getLogger(__name__)

class DatabaseCleanupService:
    """
    Service for automatically cleaning up old data from databases
    """
    
    def __init__(self):
        self.cleanup_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Database paths
        self.database_dir = Path("infrastructure/persistence/database")
        self.cache_dir = Path("infrastructure/persistence/cache") 
        
        # Cleanup configuration tables by database
        self.cleanup_tables = {
            "clusters.db": [
                ("cluster_analysis_results", "timestamp"),
                ("cluster_metrics_cache", "timestamp"),
                ("hpa_analysis_results", "timestamp"),
                ("node_metrics_cache", "timestamp"),
                ("pod_metrics_cache", "timestamp"),
                ("workload_metrics_cache", "timestamp")
            ],
            "costs.db": [
                ("cost_analysis_cache", "timestamp"),
                ("daily_cost_breakdown", "date"),
                ("monthly_cost_trends", "month_start")
            ],
            "alerts.db": [
                ("alert_history", "timestamp"),
                ("notification_log", "timestamp")
            ],
            "learning_data.db": [
                ("ml_training_data", "timestamp"),
                ("performance_metrics", "timestamp")
            ]
        }
    
    def start(self):
        """Start the cleanup service"""
        if self.is_running:
            logger.warning("Database cleanup service is already running")
            return
        
        if not self._is_cleanup_enabled():
            logger.info("Database cleanup is disabled in settings")
            return
        
        self.stop_event.clear()
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        self.is_running = True
        
        logger.info("🧹 Database cleanup service started")
    
    def stop(self):
        """Stop the cleanup service"""
        if not self.is_running:
            return
        
        self.stop_event.set()
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        self.is_running = False
        logger.info("🛑 Database cleanup service stopped")
    
    def restart(self):
        """Restart the cleanup service with new settings"""
        logger.info("♻️ Restarting database cleanup service...")
        self.stop()
        time.sleep(1)
        self.start()
    
    def _is_cleanup_enabled(self) -> bool:
        """Check if cleanup is enabled in settings"""
        enabled = settings_manager.get_setting('DATABASE_CLEANUP_ENABLED', 'true')
        return enabled.lower() == 'true'
    
    def _get_retention_days(self) -> int:
        """Get retention period in days from settings"""
        try:
            return int(settings_manager.get_setting('DATABASE_RETENTION_DAYS', '90'))
        except ValueError:
            logger.warning("Invalid DATABASE_RETENTION_DAYS value, using default 90")
            return 90
    
    def _get_cleanup_interval_hours(self) -> int:
        """Get cleanup interval in hours from settings"""
        try:
            return int(settings_manager.get_setting('DATABASE_CLEANUP_INTERVAL_HOURS', '24'))
        except ValueError:
            logger.warning("Invalid DATABASE_CLEANUP_INTERVAL_HOURS value, using default 24")
            return 24
    
    def _cleanup_loop(self):
        """Main cleanup loop that runs in background thread"""
        logger.info("🔄 Database cleanup loop started")
        
        while not self.stop_event.is_set():
            try:
                if self._is_cleanup_enabled():
                    self._perform_cleanup()
                else:
                    logger.debug("Cleanup disabled, skipping")
                
                # Wait for the configured interval or until stop event
                interval_hours = self._get_cleanup_interval_hours()
                interval_seconds = interval_hours * 3600
                
                if self.stop_event.wait(timeout=interval_seconds):
                    break  # Stop event was set
                
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")
                # Wait 1 hour before retrying on error
                if self.stop_event.wait(timeout=3600):
                    break
    
    def _perform_cleanup(self):
        """Perform database cleanup operation"""
        logger.info("🧹 Starting database cleanup operation...")
        
        retention_days = self._get_retention_days()
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        logger.info(f"📅 Cleaning data older than {retention_days} days (before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")
        
        total_deleted = 0
        databases_processed = 0
        
        # Process each database
        for db_name, tables in self.cleanup_tables.items():
            db_path = self.database_dir / db_name
            
            if not db_path.exists():
                logger.debug(f"Database {db_name} does not exist, skipping")
                continue
            
            try:
                deleted_count = self._cleanup_database(db_path, tables, cutoff_date)
                total_deleted += deleted_count
                databases_processed += 1
                
                if deleted_count > 0:
                    logger.info(f"🗑️ Cleaned {deleted_count:,} records from {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to cleanup {db_name}: {e}")
        
        # Clean cache files
        cache_deleted = self._cleanup_cache_files(cutoff_date)
        
        # Log summary
        if total_deleted > 0 or cache_deleted > 0:
            logger.info(f"✅ Cleanup completed: {total_deleted:,} database records + {cache_deleted} cache files deleted from {databases_processed} databases")
        else:
            logger.debug("✅ Cleanup completed: no old data found")
        
        # Log database sizes after cleanup
        self._log_database_sizes()
    
    def _cleanup_database(self, db_path: Path, tables: List[Tuple[str, str]], cutoff_date: datetime) -> int:
        """
        Clean up a specific database
        
        Args:
            db_path: Path to database file
            tables: List of (table_name, timestamp_column) tuples
            cutoff_date: Delete records older than this date
            
        Returns:
            Total number of records deleted
        """
        total_deleted = 0
        
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                for table_name, timestamp_column in tables:
                    try:
                        # Check if table exists
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                        if not cursor.fetchone():
                            logger.debug(f"Table {table_name} does not exist in {db_path.name}")
                            continue
                        
                        # Check if timestamp column exists
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [row[1] for row in cursor.fetchall()]
                        if timestamp_column not in columns:
                            logger.debug(f"Column {timestamp_column} does not exist in {table_name}")
                            continue
                        
                        # Count records to be deleted (for logging)
                        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            f"SELECT COUNT(*) FROM {table_name} WHERE {timestamp_column} < ?",
                            (cutoff_str,)
                        )
                        count_to_delete = cursor.fetchone()[0]
                        
                        if count_to_delete > 0:
                            # Delete old records
                            cursor.execute(
                                f"DELETE FROM {table_name} WHERE {timestamp_column} < ?",
                                (cutoff_str,)
                            )
                            
                            deleted = cursor.rowcount
                            total_deleted += deleted
                            
                            logger.debug(f"  Deleted {deleted:,} records from {table_name}")
                        
                    except sqlite3.Error as e:
                        logger.error(f"❌ Error cleaning table {table_name}: {e}")
                        continue
                
                # Vacuum database to reclaim space if any deletions occurred
                if total_deleted > 0:
                    logger.debug(f"🔧 Vacuuming {db_path.name} to reclaim space...")
                    cursor.execute("VACUUM")
                    
        except sqlite3.Error as e:
            logger.error(f"❌ Error accessing database {db_path}: {e}")
            raise
        
        return total_deleted
    
    def _cleanup_cache_files(self, cutoff_date: datetime) -> int:
        """
        Clean up old cache files
        
        Args:
            cutoff_date: Delete files older than this date
            
        Returns:
            Number of files deleted
        """
        if not self.cache_dir.exists():
            return 0
        
        deleted_count = 0
        
        try:
            for cache_file in self.cache_dir.rglob("*"):
                if cache_file.is_file():
                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                        
                        if mtime < cutoff_date:
                            cache_file.unlink()
                            deleted_count += 1
                            logger.debug(f"🗑️ Deleted cache file: {cache_file.relative_to(self.cache_dir)}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to delete cache file {cache_file}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error cleaning cache directory: {e}")
        
        if deleted_count > 0:
            logger.info(f"🗑️ Cleaned {deleted_count} cache files")
        
        return deleted_count
    
    def _log_database_sizes(self):
        """Log current database sizes for monitoring"""
        try:
            total_size = 0
            size_info = []
            
            for db_name in self.cleanup_tables.keys():
                db_path = self.database_dir / db_name
                if db_path.exists():
                    size_mb = db_path.stat().st_size / (1024 * 1024)
                    total_size += size_mb
                    size_info.append(f"{db_name}: {size_mb:.1f}MB")
            
            # Add cache size
            if self.cache_dir.exists():
                cache_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file())
                cache_mb = cache_size / (1024 * 1024)
                total_size += cache_mb
                size_info.append(f"cache: {cache_mb:.1f}MB")
            
            logger.info(f"📊 Database sizes after cleanup: {', '.join(size_info)} (total: {total_size:.1f}MB)")
            
        except Exception as e:
            logger.error(f"❌ Error calculating database sizes: {e}")
    
    def get_database_sizes(self) -> Dict[str, float]:
        """
        Get current database sizes in MB
        
        Returns:
            Dictionary with database names and sizes in MB
        """
        sizes = {}
        
        try:
            for db_name in self.cleanup_tables.keys():
                db_path = self.database_dir / db_name
                if db_path.exists():
                    sizes[db_name] = db_path.stat().st_size / (1024 * 1024)
                else:
                    sizes[db_name] = 0.0
            
            # Add cache size
            if self.cache_dir.exists():
                cache_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file())
                sizes["cache"] = cache_size / (1024 * 1024)
            else:
                sizes["cache"] = 0.0
                
        except Exception as e:
            logger.error(f"❌ Error getting database sizes: {e}")
        
        return sizes
    
    def force_cleanup(self) -> Dict[str, int]:
        """
        Force an immediate cleanup operation
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("🚀 Forcing immediate database cleanup...")
        
        if not self._is_cleanup_enabled():
            return {"error": "Database cleanup is disabled in settings"}
        
        try:
            retention_days = self._get_retention_days()
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            results = {"total_deleted": 0, "databases_processed": 0, "cache_files_deleted": 0}
            
            # Process each database
            for db_name, tables in self.cleanup_tables.items():
                db_path = self.database_dir / db_name
                
                if not db_path.exists():
                    continue
                
                try:
                    deleted_count = self._cleanup_database(db_path, tables, cutoff_date)
                    results["total_deleted"] += deleted_count
                    results["databases_processed"] += 1
                    results[db_name] = deleted_count
                    
                except Exception as e:
                    logger.error(f"❌ Failed to cleanup {db_name}: {e}")
                    results[f"{db_name}_error"] = str(e)
            
            # Clean cache files
            results["cache_files_deleted"] = self._cleanup_cache_files(cutoff_date)
            
            logger.info(f"✅ Force cleanup completed: {results['total_deleted']} records deleted")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during force cleanup: {e}")
            return {"error": str(e)}

# Global cleanup service instance
cleanup_service = DatabaseCleanupService()

def start_cleanup_service():
    """Start the global cleanup service"""
    cleanup_service.start()

def stop_cleanup_service():
    """Stop the global cleanup service"""
    cleanup_service.stop()

def restart_cleanup_service():
    """Restart the global cleanup service"""
    cleanup_service.restart()