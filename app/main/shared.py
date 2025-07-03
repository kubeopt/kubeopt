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
    """ENTERPRISE: HPA-aware analysis data loading with subscription awareness"""
    if not cluster_id:
        logger.warning("⚠️ No cluster_id provided for analysis data")
        return None, "no_cluster_id"

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

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0