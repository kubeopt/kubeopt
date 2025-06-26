"""
Shared utilities and functions for AKS Cost Optimization Tool
"""

import threading
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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
    """HPA-aware analysis data loading with session priority"""
    if not cluster_id:
        logger.warning("⚠️ No cluster_id provided for analysis data")
        return None, "no_cluster_id"

    # Get shared globals
    _analysis_sessions, _analysis_lock, analysis_cache, enhanced_cluster_manager = get_shared_globals()
    
    if not enhanced_cluster_manager:
        logger.error("❌ Enhanced cluster manager not available")
        return None, "no_cluster_manager"

    # PRIORITY 0: Check for fresh session data first (HIGHEST PRIORITY)
    fresh_session_data = None
    data_source = "none"
    
    with _analysis_lock:
        logger.info(f"🔍 CHART API: Checking {len(_analysis_sessions)} active sessions for cluster {cluster_id}")
        for session_id, session_info in _analysis_sessions.items():
            if (session_info.get('cluster_id') == cluster_id and 
                session_info.get('status') == 'completed' and 
                'results' in session_info):
                fresh_session_data = session_info['results']
                data_source = "fresh_session"
                logger.info(f"🎯 CHART API: Found fresh session data for {cluster_id} (session: {session_id[:8]})")
                break

    if fresh_session_data:
        # Validate HPA recommendations in fresh data
        if 'hpa_recommendations' in fresh_session_data:
            logger.info(f"✅ CHART API: Using fresh session data with HPA for {cluster_id}")
            # Optionally update cache with fresh data
            from app.services.cache_manager import save_to_cache
            #save_to_cache(cluster_id, fresh_session_data)
            return fresh_session_data, "fresh_session"
        else:
            logger.warning(f"⚠️ CHART API: Fresh session data missing HPA for {cluster_id}")

    # PRIORITY 1: Cluster-specific cache with HPA validation
    try:
        from app.services.cache_manager import load_from_cache, clear_analysis_cache
        cached_data = load_from_cache(cluster_id)
        if cached_data and cached_data.get('total_cost', 0) > 0:
            # Validate HPA recommendations exist
            if 'hpa_recommendations' in cached_data:
                logger.info(f"✅ CACHE: Complete data with HPA for {cluster_id} - ${cached_data.get('total_cost', 0):.2f}")
                return cached_data, "cluster_cache"
            else:
                logger.warning(f"⚠️ CACHE: Data exists but missing HPA for {cluster_id}")
                # Clear incomplete cache
                clear_analysis_cache(cluster_id)
    except Exception as e:
        logger.warning(f"⚠️ Cluster cache fetch failed for {cluster_id}: {e}")

    # PRIORITY 2: Database with HPA validation
    try:
        logger.info(f"🔄 Loading from database for cluster: {cluster_id}")
        db_data = enhanced_cluster_manager.get_latest_analysis(cluster_id)
        if db_data and db_data.get('total_cost', 0) > 0:
            # Validate HPA recommendations in database data
            if 'hpa_recommendations' in db_data:
                logger.info(f"✅ DATABASE: Complete data with HPA for {cluster_id} - ${db_data.get('total_cost', 0):.2f}")
                # Cache the complete database data
                from app.services.cache_manager import save_to_cache
                save_to_cache(cluster_id, db_data)
                return db_data, "cluster_database"
            else:
                logger.warning(f"⚠️ DATABASE: Data exists but missing HPA for {cluster_id}")
    except Exception as e:
        logger.error(f"❌ Database error for cluster {cluster_id}: {e}")

    logger.warning(f"⚠️ No complete analysis data (with HPA) found for cluster: {cluster_id}")
    return None, "no_complete_data"

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0