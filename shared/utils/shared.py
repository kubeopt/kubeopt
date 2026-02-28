#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Shared utilities and functions for AKS Cost Optimization Tool
"""

import threading
import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import global components
try:
    from shared.config.config import enhanced_cluster_manager, analysis_cache, _analysis_sessions, _analysis_lock
    logger.info("✅ Successfully imported shared globals")
except ImportError as e:
    logger.error(f"❌ Failed to import shared globals: {e}")
    enhanced_cluster_manager = None
    analysis_cache = {}
    _analysis_sessions = {}
    _analysis_lock = threading.Lock()

# ============================================================================
# REQUEST SYSTEM
# ============================================================================

class RequestDeduplicator:
    """Prevents duplicate expensive operations from running simultaneously"""
    
    def __init__(self):
        self.active_requests = {}
        self.request_results = {}
        self.lock = threading.Lock()
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def get_or_execute(self, request_key: str, operation_func, *args, **kwargs):
        """Execute operation only once for duplicate requests"""
        current_time = time.time()
        
        with self.lock:
            # Cleanup old entries periodically
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_entries(current_time)
                self.last_cleanup = current_time
            
            # Check if request is already in progress
            if request_key in self.active_requests:
                request_info = self.active_requests[request_key]
                logger.info(f"🔄  Request {request_key[:16]}... already in progress on thread {request_info['thread_id']}, waiting...")
                
                # Wait for the active request to complete
                event = request_info['completion_event']
                
        # Wait outside the lock to avoid blocking other requests
        if request_key in self.active_requests:
            event.wait(timeout=120)  # 2 minute timeout
            
            with self.lock:
                # Check if we have cached results
                if request_key in self.request_results:
                    result = self.request_results[request_key]['result']
                    logger.info(f"✅  Using cached result for {request_key[:16]}...")
                    return result
                
                # If no cached result, the request might have failed, so we'll execute
                logger.warning(f"⚠️  No cached result for {request_key[:16]}..., executing anyway")
        
        # Execute the operation
        completion_event = threading.Event()
        
        with self.lock:
            # Mark request as active
            self.active_requests[request_key] = {
                'thread_id': threading.current_thread().ident,
                'start_time': current_time,
                'completion_event': completion_event
            }
        
        try:
            logger.info(f"🚀  Executing operation for {request_key[:16]}... on thread {threading.current_thread().ident}")
            result = operation_func(*args, **kwargs)
            
            with self.lock:
                # Cache the result for a short time
                self.request_results[request_key] = {
                    'result': result,
                    'timestamp': current_time,
                    'ttl': 60  # 1 minute TTL for chart data
                }
                
                # Remove from active requests
                self.active_requests.pop(request_key, None)
            
            # Signal completion to waiting threads
            completion_event.set()
            
            logger.info(f"✅  Operation completed for {request_key[:16]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌  Operation failed for {request_key[:16]}...: {e}")
            
            with self.lock:
                # Remove from active requests on failure
                self.active_requests.pop(request_key, None)
            
            # Signal completion even on failure
            completion_event.set()
            raise
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove old cached results and stale active requests"""
        # Clean old results
        expired_results = [
            key for key, data in self.request_results.items()
            if current_time - data['timestamp'] > data.get('ttl', 300)
        ]
        
        for key in expired_results:
            del self.request_results[key]
        
        # Clean stale active requests (older than 10 minutes)
        stale_requests = [
            key for key, data in self.active_requests.items()
            if current_time - data['start_time'] > 600
        ]
        
        for key in stale_requests:
            logger.warning(f"⚠️  Cleaning stale request {key[:16]}...")
            del self.active_requests[key]
        
        if expired_results or stale_requests:
            logger.info(f"🧹  Cleaned {len(expired_results)} expired results, {len(stale_requests)} stale requests")

# Global deduplicator instance
request_deduplicator = RequestDeduplicator()

# Import the shared global variables from config
def get_shared_globals():
    """Get shared global variables"""
    try:
        from shared.config.config import (
            _analysis_sessions, _analysis_lock, analysis_cache, 
            enhanced_cluster_manager
        )
        return _analysis_sessions, _analysis_lock, analysis_cache, enhanced_cluster_manager
    except ImportError as e:
        logger.error(f"Failed to import shared globals: {e}")
        return {}, threading.Lock(), {'clusters': {}}, None

def _get_analysis_data(cluster_id: Optional[str]) -> Tuple[Optional[Dict[str, Any]], str]:
    """Load analysis data for a cluster. Tries: session → cache → database."""
    if not cluster_id:
        return None, "no_cluster_id"

    if not enhanced_cluster_manager:
        logger.error("Enhanced cluster manager not available")
        return None, "no_cluster_manager"

    cluster_info = enhanced_cluster_manager.get_cluster(cluster_id)
    subscription_id = cluster_info.get('subscription_id') if cluster_info else None

    try:
        # 1. Fresh session data (in-memory, from recent analysis)
        with _analysis_lock:
            for session_id, session_info in _analysis_sessions.items():
                if (session_info.get('cluster_id') == cluster_id and
                    session_info.get('status') == 'completed' and
                    'results' in session_info):
                    results = session_info['results']
                    if isinstance(results, dict) and results.get('cluster_name') and results.get('resource_group'):
                        expected_id = f"{results['resource_group']}_{results['cluster_name']}"
                        if expected_id == cluster_id:
                            logger.info(f"Using fresh session data for {cluster_id}")
                            return results, "fresh_session"

        # 2. Cache
        from infrastructure.services.cache_manager import load_from_cache
        cached_data = load_from_cache(cluster_id, subscription_id)
        if cached_data and cached_data.get('total_cost', 0) > 0:
            logger.info(f"Using cached data for {cluster_id}")
            return cached_data, "enterprise_cache"

        # 3. Database
        import sqlite3
        import json
        from infrastructure.persistence.cluster_database import deserialize_implementation_plan

        db_path = enhanced_cluster_manager.db_path
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT results FROM analysis_results WHERE cluster_id = ? AND results IS NOT NULL ORDER BY analysis_date DESC LIMIT 1',
                (cluster_id,),
            )
            row = cursor.fetchone()
            if row and row['results']:
                raw = row['results']
                serialized = json.loads(raw.decode('utf-8') if isinstance(raw, bytes) else raw)
                db_data = deserialize_implementation_plan(serialized)
                if db_data and db_data.get('total_cost', 0) > 0:
                    logger.info(f"Using database data for {cluster_id}")
                    from infrastructure.services.cache_manager import save_to_cache
                    save_to_cache(cluster_id, db_data, subscription_id)
                    return db_data, "analysis_results_table"

    except Exception as e:
        logger.error(f"Analysis data fetch failed for {cluster_id}: {e}")
        return None, "fetch_error"

    return None, "no_data"

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# ============================================================================
# ML OPERATION
# ============================================================================

class MLOperationDeduplicator:
    """Prevents duplicate ML operations from running simultaneously"""
    
    def __init__(self):
        self.active_ml_operations = {}
        self.ml_results_cache = {}
        self.lock = threading.Lock()
    
    def execute_ml_operation_once(self, operation_key: str, operation_func, *args, **kwargs):
        """Execute ML operation only once for duplicate requests"""
        
        with self.lock:
            # Check if operation is already running
            if operation_key in self.active_ml_operations:
                event = self.active_ml_operations[operation_key]['completion_event']
                logger.info(f"🤖 ML  Operation {operation_key} already running, waiting...")
                
        # Wait for completion if operation is active
        if operation_key in self.active_ml_operations:
            event.wait(timeout=60)  # 1 minute timeout for ML operations
            
            with self.lock:
                if operation_key in self.ml_results_cache:
                    logger.info(f"✅ ML  Using cached ML result for {operation_key}")
                    return self.ml_results_cache[operation_key]['result']
        
        # Execute the ML operation
        completion_event = threading.Event()
        
        with self.lock:
            self.active_ml_operations[operation_key] = {
                'thread_id': threading.current_thread().ident,
                'start_time': time.time(),
                'completion_event': completion_event
            }
        
        try:
            logger.info(f"🚀 ML  Executing ML operation {operation_key}")
            result = operation_func(*args, **kwargs)
            
            with self.lock:
                # Cache result for 2 minutes
                self.ml_results_cache[operation_key] = {
                    'result': result,
                    'timestamp': time.time(),
                    'ttl': 120
                }
                
                # Remove from active operations
                self.active_ml_operations.pop(operation_key, None)
            
            completion_event.set()
            logger.info(f"✅ ML  ML operation {operation_key} completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ ML  ML operation {operation_key} failed: {e}")
            
            with self.lock:
                self.active_ml_operations.pop(operation_key, None)
            
            completion_event.set()
            raise

# Global ML deduplicator
ml_deduplicator = MLOperationDeduplicator()

def execute_ml_operation_deduplicated(cluster_id: str, operation_name: str, operation_func, *args, **kwargs):
    """Execute ML operation with deduplication"""
    operation_key = f"ml_{operation_name}_{cluster_id}_{int(time.time() // 60)}"  # 1-minute dedup window
    return ml_deduplicator.execute_ml_operation_once(operation_key, operation_func, *args, **kwargs)