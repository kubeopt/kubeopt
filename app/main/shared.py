#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
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
                logger.info(f"🔄 DEDUP: Request {request_key[:16]}... already in progress on thread {request_info['thread_id']}, waiting...")
                
                # Wait for the active request to complete
                event = request_info['completion_event']
                
        # Wait outside the lock to avoid blocking other requests
        if request_key in self.active_requests:
            event.wait(timeout=120)  # 2 minute timeout
            
            with self.lock:
                # Check if we have cached results
                if request_key in self.request_results:
                    result = self.request_results[request_key]['result']
                    logger.info(f"✅ DEDUP: Using cached result for {request_key[:16]}...")
                    return result
                
                # If no cached result, the request might have failed, so we'll execute
                logger.warning(f"⚠️ DEDUP: No cached result for {request_key[:16]}..., executing anyway")
        
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
            logger.info(f"🚀 DEDUP: Executing operation for {request_key[:16]}... on thread {threading.current_thread().ident}")
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
            
            logger.info(f"✅ DEDUP: Operation completed for {request_key[:16]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ DEDUP: Operation failed for {request_key[:16]}...: {e}")
            
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
            logger.warning(f"⚠️ DEDUP: Cleaning stale request {key[:16]}...")
            del self.active_requests[key]
        
        if expired_results or stale_requests:
            logger.info(f"🧹 DEDUP: Cleaned {len(expired_results)} expired results, {len(stale_requests)} stale requests")

# Global deduplicator instance
request_deduplicator = RequestDeduplicator()

# Import the shared global variables from config
def get_shared_globals():
    """Get shared global variables"""
    try:
        from config import (
            _analysis_sessions, _analysis_lock, analysis_cache, 
            enhanced_cluster_manager
        )
        return _analysis_sessions, _analysis_lock, analysis_cache, enhanced_cluster_manager
    except ImportError as e:
        logger.error(f"Failed to import shared globals: {e}")
        return {}, threading.Lock(), {'clusters': {}}, None

def _get_analysis_data(cluster_id: Optional[str]) -> Tuple[Optional[Dict[str, Any]], str]:
    """ENTERPRISE: HPA-aware analysis data loading with subscription awareness and deduplication"""
    if not cluster_id:
        logger.warning("⚠️ No cluster_id provided for analysis data")
        return None, "no_cluster_id"

    # Create deduplication key for this request
    dedup_key = f"analysis_data_{cluster_id}_{int(time.time() // 30)}"  # 30-second dedup window
    
    def _fetch_analysis_data_internal():
        """Internal function to fetch analysis data"""
        # Get shared globals
        _analysis_sessions, _analysis_lock, analysis_cache, enhanced_cluster_manager = get_shared_globals()
        
        if not enhanced_cluster_manager:
            logger.error("❌ Enhanced cluster manager not available")
            return None, "no_cluster_manager"

        # Get cluster info for subscription context
        cluster_info = enhanced_cluster_manager.get_cluster(cluster_id)
        subscription_id = cluster_info.get('subscription_id') if cluster_info else None

        # PRIORITY 0: Check for fresh session data first
        fresh_session_data = None
        data_source = "none"
        
        with _analysis_lock:
            logger.info(f"🔍 ENTERPRISE CHART API: Checking {len(_analysis_sessions)} active sessions for cluster {cluster_id}")
            for session_id, session_info in _analysis_sessions.items():
                if (session_info.get('cluster_id') == cluster_id and 
                    session_info.get('status') == 'completed' and 
                    'results' in session_info):
                    fresh_session_data = session_info['results']
                    data_source = "fresh_session"
                    logger.info(f"🎯 ENTERPRISE CHART API: Found fresh session data for {cluster_id}")
                    break

        if fresh_session_data:
            if 'hpa_recommendations' in fresh_session_data:
                logger.info(f"✅ ENTERPRISE CHART API: Using fresh session data with HPA for {cluster_id}")
                return fresh_session_data, "fresh_session"

        # PRIORITY 1: Enterprise cache with subscription awareness
        try:
            from app.services.cache_manager import load_from_cache, clear_analysis_cache
            cached_data = load_from_cache(cluster_id, subscription_id)
            if cached_data and cached_data.get('total_cost', 0) > 0:
                if 'hpa_recommendations' in cached_data:
                    logger.info(f"✅ ENTERPRISE CACHE: Complete data with HPA for {cluster_id} - ${cached_data.get('total_cost', 0):.2f}")
                    return cached_data, "enterprise_cache"
                else:
                    logger.warning(f"⚠️ ENTERPRISE CACHE: Data exists but missing HPA for {cluster_id}")
                    clear_analysis_cache(cluster_id, subscription_id)
        except Exception as e:
            logger.warning(f"⚠️ Enterprise cache fetch failed for {cluster_id}: {e}")

        # PRIORITY 2: Database with HPA validation
        try:
            logger.info(f"🔄 Loading from database for cluster: {cluster_id}")
            db_data = enhanced_cluster_manager.get_latest_analysis(cluster_id)
            if db_data and db_data.get('total_cost', 0) > 0:
                if 'hpa_recommendations' in db_data:
                    logger.info(f"✅ DATABASE: Complete data with HPA for {cluster_id} - ${db_data.get('total_cost', 0):.2f}")
                    # Cache with subscription context
                    from app.services.cache_manager import save_to_cache
                    save_to_cache(cluster_id, db_data, subscription_id)
                    return db_data, "cluster_database"
                else:
                    logger.warning(f"⚠️ DATABASE: Data exists but missing HPA for {cluster_id}")
        except Exception as e:
            logger.error(f"❌ Database error for cluster {cluster_id}: {e}")

        logger.warning(f"⚠️ No complete analysis data (with HPA) found for cluster: {cluster_id}")
        return None, "no_complete_data"
    
    # Use deduplicator to prevent duplicate calls
    try:
        return request_deduplicator.get_or_execute(dedup_key, _fetch_analysis_data_internal)
    except Exception as e:
        logger.error(f"❌ Deduplicated analysis data fetch failed for {cluster_id}: {e}")
        return None, "dedup_error"

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# ============================================================================
# CHART DATA
# ============================================================================

# def get_chart_data_deduplicated(cluster_id: str, operation_func, *args, **kwargs):
#     """Get chart data with deduplication to prevent duplicate expensive operations"""
    
#     dedup_key = f"chart_data_{cluster_id}_{int(time.time() // 45)}"  # 45-second dedup window for charts
    
#     logger.info(f"📊 CHART DEDUP: Requesting chart data for {cluster_id}")
    
#     try:
#         result = request_deduplicator.get_or_execute(dedup_key, operation_func, *args, **kwargs)
#         logger.info(f"✅ CHART DEDUP: Chart data delivered for {cluster_id}")
#         return result
#     except Exception as e:
#         logger.error(f"❌ CHART DEDUP: Chart data generation failed for {cluster_id}: {e}")
#         raise

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
                logger.info(f"🤖 ML DEDUP: Operation {operation_key} already running, waiting...")
                
        # Wait for completion if operation is active
        if operation_key in self.active_ml_operations:
            event.wait(timeout=60)  # 1 minute timeout for ML operations
            
            with self.lock:
                if operation_key in self.ml_results_cache:
                    logger.info(f"✅ ML DEDUP: Using cached ML result for {operation_key}")
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
            logger.info(f"🚀 ML DEDUP: Executing ML operation {operation_key}")
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
            logger.info(f"✅ ML DEDUP: ML operation {operation_key} completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ ML DEDUP: ML operation {operation_key} failed: {e}")
            
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