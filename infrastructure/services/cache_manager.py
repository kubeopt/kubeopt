#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Cache Management System for AKS Cost Optimization
Complete implementation with subscription awareness, validation, and performance optimizations
"""

import threading
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Any, Optional
from shared.config.config import logger, analysis_cache, enhanced_cluster_manager, _analysis_lock, _analysis_sessions, analysis_results

# Performance optimization infrastructure
_cache_key_lookup = {}  # Cache for key variant lookups
_cache_key_lock = threading.Lock()

class CacheKeyStrategy:
    """cache key management strategy with performance optimizations"""
    
    @staticmethod
    @lru_cache(maxsize=1000)  # Cache frequently used key generations
    def generate_cache_key(cluster_id: str, subscription_id: str = None) -> str:
        """
        Generate consistent cache key based on strategy
        Strategy: Always use subscription-aware keys for consistency
        """
        if subscription_id:
            # Use subscription-aware key
            cache_key = f"{subscription_id}_{cluster_id}"
            return cache_key
        else:
            # Try to extract subscription from cluster_id if it's composite
            if '_' in cluster_id and len(cluster_id.split('_')[0]) > 20:  # UUID-like format
                return cluster_id
            else:
                # Simple key - try to enhance with subscription info (cached)
                enhanced_key = CacheKeyStrategy._get_enhanced_key(cluster_id)
                return enhanced_key if enhanced_key else cluster_id
    
    @staticmethod
    @lru_cache(maxsize=500)  # Cache enhanced key lookups
    def _get_enhanced_key(cluster_id: str) -> Optional[str]:
        """Get enhanced key with caching to avoid repeated database calls"""
        try:
            cluster_info = enhanced_cluster_manager.get_cluster(cluster_id)
            if cluster_info and cluster_info.get('subscription_id'):
                return f"{cluster_info['subscription_id']}_{cluster_id}"
        except Exception:
            pass
        return None
    
    @staticmethod
    def parse_cache_key(cache_key: str) -> Dict[str, str]:
        """Parse cache key to extract components with minimal processing"""
        # Use simple string operations instead of complex logic
        if '_' in cache_key:
            parts = cache_key.split('_', 1)
            if len(parts) == 2 and len(parts[0]) > 20:  # Likely subscription_cluster format
                return {
                    'subscription_id': parts[0],
                    'cluster_id': parts[1],
                    'is_subscription_aware': True,
                    'cache_key': cache_key
                }
        
        return {
            'subscription_id': None,
            'cluster_id': cache_key,
            'is_subscription_aware': False,
            'cache_key': cache_key
        }
    
    @staticmethod
    def find_cache_key_variants(cluster_id: str) -> List[str]:
        """Find all possible cache key variants for a cluster with caching"""
        
        # Check cache first
        with _cache_key_lock:
            if cluster_id in _cache_key_lookup:
                cached_variants, timestamp = _cache_key_lookup[cluster_id]
                # Use cached variants if less than 5 minutes old
                if datetime.now() - timestamp < timedelta(minutes=5):
                    return cached_variants
        
        variants = [cluster_id]  # Start with the provided key
        
        # If it's a simple key, try to find subscription-aware variants
        if not ('_' in cluster_id and len(cluster_id.split('_')[0]) > 20):
            enhanced_key = CacheKeyStrategy._get_enhanced_key(cluster_id)
            if enhanced_key:
                variants.append(enhanced_key)
        
        # Only check first 10 existing cache keys to avoid performance issues
        existing_keys = list(analysis_cache.get('clusters', {}).keys())[:10]
        for existing_key in existing_keys:
            key_info = CacheKeyStrategy.parse_cache_key(existing_key)
            if key_info['cluster_id'] == cluster_id or existing_key == cluster_id:
                if existing_key not in variants:
                    variants.append(existing_key)
        
        # Cache the result
        with _cache_key_lock:
            _cache_key_lookup[cluster_id] = (variants, datetime.now())
            
            # Cleanup old cache entries (keep only last 100)
            if len(_cache_key_lookup) > 100:
                oldest_keys = sorted(_cache_key_lookup.keys(), 
                                   key=lambda k: _cache_key_lookup[k][1])[:20]
                for old_key in oldest_keys:
                    del _cache_key_lookup[old_key]
        
        return variants

def is_cache_valid(cluster_id: str = None, subscription_id: str = None) -> bool:
    """cache validity check with reduced overhead"""
    if not cluster_id:
        return False
    
    # Generate proper cache key (now cached)
    cache_key = CacheKeyStrategy.generate_cache_key(cluster_id, subscription_id)
    
    # Direct lookup first (most common case)
    if cache_key in analysis_cache['clusters']:
        cluster_cache = analysis_cache['clusters'][cache_key]
        return _check_cache_timestamp(cluster_cache, cluster_id)
    
    # Only try variants if direct lookup fails
    key_variants = CacheKeyStrategy.find_cache_key_variants(cluster_id)
    
    for variant in key_variants:
        if variant in analysis_cache['clusters']:
            cluster_cache = analysis_cache['clusters'][variant]
            return _check_cache_timestamp(cluster_cache, cluster_id)
    
    logger.debug(f"🕐 No cache found for cluster: {cluster_id}")
    return False

def _check_cache_timestamp(cluster_cache: dict, cluster_id: str) -> bool:
    """Helper function to check cache timestamp"""
    if not cluster_cache.get('timestamp'):
        return False
    
    try:
        cache_time = datetime.fromisoformat(cluster_cache['timestamp'])
        expiry_time = cache_time + timedelta(hours=analysis_cache['global_ttl_hours'])
        
        is_valid = datetime.now() < expiry_time
        
        if not is_valid:
            logger.debug(f"🕐 Cache expired for {cluster_id}")
            # Don't delete here to avoid modifying dict during iteration
        else:
            remaining = expiry_time - datetime.now()
            logger.debug(f"✅ Cache valid for {cluster_id}: {remaining.total_seconds()/60:.1f} minutes remaining")
        
        return is_valid
    except Exception as e:
        logger.error(f"❌ Error checking cache validity for {cluster_id}: {e}")
        return False

def cleanup_expired_cache():
    """Batch cleanup of expired cache entries"""
    try:
        current_time = datetime.now()
        expired_keys = []
        
        for cache_key, cache_entry in analysis_cache.get('clusters', {}).items():
            if cache_entry.get('timestamp'):
                try:
                    cache_time = datetime.fromisoformat(cache_entry['timestamp'])
                    expiry_time = cache_time + timedelta(hours=analysis_cache['global_ttl_hours'])
                    
                    if current_time > expiry_time:
                        expired_keys.append(cache_key)
                except Exception:
                    expired_keys.append(cache_key)  # Remove invalid entries
        
        # Batch delete
        for key in expired_keys:
            analysis_cache['clusters'].pop(key, None)
        
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
        
        # Also cleanup key lookup cache
        with _cache_key_lock:
            if len(_cache_key_lookup) > 200:  # If getting too large
                # Keep only recent entries
                cutoff_time = current_time - timedelta(minutes=10)
                old_keys = [
                    k for k, (_, timestamp) in _cache_key_lookup.items()
                    if timestamp < cutoff_time
                ]
                for k in old_keys:
                    del _cache_key_lookup[k]
                    
                if old_keys:
                    logger.info(f"🧹 Cleaned up {len(old_keys)} cached key lookups")
        
        return len(expired_keys)
        
    except Exception as e:
        logger.error(f"❌ Error during cache cleanup: {e}")
        return 0

def clear_analysis_cache(cluster_id: str = None, subscription_id: str = None):
    """
    Complete cache clearing with subscription awareness
    """
    global analysis_cache
    
    if cluster_id:
        # Clear all variants of this cluster
        key_variants = CacheKeyStrategy.find_cache_key_variants(cluster_id)
        
        cleared_keys = []
        for variant in key_variants:
            if variant in analysis_cache['clusters']:
                del analysis_cache['clusters'][variant]
                cleared_keys.append(variant)
        
        if cleared_keys:
            logger.info(f"🧹 CACHE: Cleared cache for cluster {cluster_id}: {cleared_keys}")
        else:
            logger.info(f"ℹ️ CACHE: No cache to clear for cluster: {cluster_id}")
    else:
        old_count = len(analysis_cache['clusters'])
        analysis_cache['clusters'] = {}
        logger.info(f"🧹 CACHE: Cleared ALL cluster caches ({old_count} clusters)")

def force_fresh_analysis_with_complete_cache_clear(cluster_id: str):
    """
    Force fresh analysis with total cache clearing and subscription awareness
    """
    logger.info(f"🔄 COMPLETE FRESH: Starting total cache clear for {cluster_id}")
    
    # Step 1: Clear cluster-specific cache (all variants)
    clear_analysis_cache(cluster_id)
    
    # Step 2: Clear all session data for this cluster
    with _analysis_lock:
        sessions_to_remove = []
        for session_id, session_info in _analysis_sessions.items():
            if session_info.get('cluster_id') == cluster_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del _analysis_sessions[session_id]
            logger.info(f"🧹 COMPLETE FRESH: Cleared session {session_id[:8]} for {cluster_id}")
    
    # Step 3: Clear global analysis results if they match this cluster (thread-safe)
    try:
        with _analysis_lock:  # Thread-safe access to global analysis_results
            if analysis_results:
                # Check if global results belong to this cluster
                global_rg = analysis_results.get('resource_group', '')
                global_name = analysis_results.get('cluster_name', '')
                if global_rg and global_name:
                    global_cluster_id = f"{global_rg}_{global_name}"
                    if global_cluster_id == cluster_id:
                        # Only clear specific cluster keys instead of the entire dictionary
                        cluster_keys_to_clear = [k for k, v in analysis_results.items() 
                                               if isinstance(v, dict) and 
                                               (v.get('cluster_name') == global_name and v.get('resource_group') == global_rg)]
                        
                        if not cluster_keys_to_clear:
                            # If no cluster-specific keys found, clear the root level data
                            analysis_results.clear()
                            logger.info(f"🧹 COMPLETE FRESH: Cleared global analysis_results for {cluster_id}")
                        else:
                            # Remove only cluster-specific keys
                            for key in cluster_keys_to_clear:
                                del analysis_results[key]
                            logger.info(f"🧹 COMPLETE FRESH: Cleared {len(cluster_keys_to_clear)} cluster-specific keys for {cluster_id}")
                else:
                    logger.debug(f"ℹ️ Global analysis_results don't match cluster {cluster_id}, skipping clear")
            else:
                logger.debug(f"ℹ️ No global analysis_results to clear for {cluster_id}")
    except Exception as e:
        logger.warning(f"⚠️ Could not clear global analysis results for {cluster_id}: {e}")
    
    # Step 4: Clear any database cache if exists
    try:
        # Force database to refresh by updating timestamp
        enhanced_cluster_manager.touch_cluster(cluster_id)
        logger.info(f"🧹 COMPLETE FRESH: Updated database timestamp for {cluster_id}")
    except Exception as db_error:
        logger.warning(f"⚠️ Database timestamp update failed: {db_error}")
    
    logger.info(f"✅ COMPLETE FRESH: Total cache clearing completed for {cluster_id}")

def save_to_cache_with_validation(cluster_id: str, complete_analysis_data: dict, subscription_id: str = None):
    """
    Save to cache with consistent key strategy and comprehensive validation
    """
    global analysis_cache
    
    # Generate consistent cache key
    cache_key = CacheKeyStrategy.generate_cache_key(cluster_id, subscription_id)
    
    logger.info(f"💾 CACHE SAVE: Validating data for {cache_key}")
    
    # 🔍 CACHE SAVE: Log gap data before caching
    cpu_gap = complete_analysis_data.get('cpu_gap', 'NOT_FOUND')
    memory_gap = complete_analysis_data.get('memory_gap', 'NOT_FOUND')
    logger.info(f"🔍 CACHE SAVE: About to cache CPU gap: {cpu_gap}, Memory gap: {memory_gap}")
    logger.info(f"🔍 CACHE SAVE: Analysis data keys: {list(complete_analysis_data.keys())}")
    
    try:
        # STEP 1: Comprehensive data validation
        validation_errors = _validate_cache_data_structure(complete_analysis_data, cluster_id)
        if validation_errors:
            raise ValueError(f"Cache validation failed: {validation_errors}")
        
        # STEP 2: Clean and prepare data for caching
        cache_data = _prepare_cache_data(complete_analysis_data, cluster_id)
        
        # 🔍 CACHE PREP: Verify gap data preservation
        prep_cpu_gap = cache_data.get('cpu_gap', 'NOT_FOUND')
        prep_memory_gap = cache_data.get('memory_gap', 'NOT_FOUND')
        logger.info(f"🔍 CACHE PREP: After preparation - CPU gap: {prep_cpu_gap}, Memory gap: {prep_memory_gap}")
        
        # STEP 3: Store in cache with metadata
        cache_entry = {
            'data': cache_data,
            'timestamp': datetime.now().isoformat(),
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'cache_key': cache_key,
            'ttl_hours': analysis_cache['global_ttl_hours'],
            'cache_version': 'enterprise_subscription_aware',
            'validation_passed': True,
            'data_size': len(str(cache_data)),
            'components': list(cache_data.keys())
        }
        
        analysis_cache['clusters'][cache_key] = cache_entry
        
        # Also maintain a reverse lookup for simple keys
        if subscription_id and cache_key != cluster_id:
            # Create a reference entry for simple key lookup
            analysis_cache['clusters'][cluster_id] = {
                'reference_to': cache_key,
                'timestamp': datetime.now().isoformat(),
                'cache_type': 'reference'
            }
        
        logger.info(f"💾 CACHE SAVED: {cache_key} with validated data ({len(cache_data)} components)")
        return True
        
    except Exception as cache_error:
        logger.error(f"❌ CACHE SAVE FAILED for {cache_key}: {cache_error}")
        # Clean up any partial cache data
        if cache_key in analysis_cache.get('clusters', {}):
            del analysis_cache['clusters'][cache_key]
        return False

def load_from_cache_with_validation(cluster_id: str, subscription_id: str = None) -> dict:
    """
    Load from cache with fast path for common cases
    """
    try:
        # Fast path - direct key lookup
        cache_key = CacheKeyStrategy.generate_cache_key(cluster_id, subscription_id)
        
        logger.debug(f"📦 CACHE LOAD: Loading data for {cache_key}")
        
        # Try the primary cache key first
        cluster_cache = analysis_cache.get('clusters', {}).get(cache_key)
        
        if cluster_cache:
            # Check if it's a reference
            if cluster_cache.get('cache_type') == 'reference':
                reference_key = cluster_cache.get('reference_to')
                if reference_key and reference_key in analysis_cache['clusters']:
                    cluster_cache = analysis_cache['clusters'][reference_key]
                    cache_key = reference_key
                else:
                    logger.warning(f"⚠️ CACHE: Invalid reference from {cluster_id}")
                    return {}
            
            # Quick validity check
            if _check_cache_timestamp(cluster_cache, cluster_id):
                cached_data = cluster_cache.get('data', {})
                
                # Minimal validation - just check essential fields
                if cached_data.get('total_cost', 0) > 0 and cached_data.get('hpa_recommendations'):
                    # 🔍 CACHE LOAD: Log gap data being returned
                    cpu_gap = cached_data.get('cpu_gap', 'NOT_FOUND')
                    memory_gap = cached_data.get('memory_gap', 'NOT_FOUND')
                    logger.info(f"🔍 CACHE LOAD: Returning CPU gap: {cpu_gap}, Memory gap: {memory_gap}")
                    logger.debug(f"📦 CACHE HIT: {cache_key} - ${cached_data.get('total_cost', 0):.2f}")
                    return cached_data
        
        # Only try variants if fast path fails
        key_variants = CacheKeyStrategy.find_cache_key_variants(cluster_id)
        
        for variant in key_variants[1:]:  # Skip first variant (already tried)
            cluster_cache = analysis_cache.get('clusters', {}).get(variant)
            if cluster_cache and cluster_cache.get('cache_type') != 'reference':
                if _check_cache_timestamp(cluster_cache, cluster_id):
                    cached_data = cluster_cache.get('data', {})
                    
                    # Minimal validation
                    if cached_data.get('total_cost', 0) > 0 and cached_data.get('hpa_recommendations'):
                        logger.debug(f"📦 CACHE HIT (variant): {variant} - ${cached_data.get('total_cost', 0):.2f}")
                        return cached_data
        
        logger.debug(f"📦 CACHE MISS: No valid cache found for {cluster_id}")
        return {}
        
    except Exception as e:
        logger.error(f"❌ CACHE LOAD ERROR for {cluster_id}: {e}")
        return {}

def _validate_cache_data_structure(data: dict, cluster_id: str) -> List[str]:
    """Optimized validation with minimal checks"""
    errors = []
    
    # Only check critical fields
    if not isinstance(data.get('total_cost'), (int, float)) or data.get('total_cost', 0) <= 0:
        errors.append(f"Invalid total_cost: {data.get('total_cost')}")
    
    if not isinstance(data.get('hpa_recommendations'), dict):
        errors.append("Missing or invalid HPA recommendations")
    
    return errors

def _validate_loaded_cache_data(cached_data: dict, cluster_id: str) -> List[str]:
    """Minimal validation when loading from cache"""
    # Just ensure data is not completely broken
    if not cached_data.get('total_cost', 0) > 0:
        return ["Invalid cost data"]
    
    if not isinstance(cached_data.get('hpa_recommendations'), dict):
        return ["Invalid HPA structure"]
    
    return []  # Accept most cached data to improve performance

def _prepare_cache_data(complete_analysis_data: dict, cluster_id: str) -> dict:
    """Preserve ALL HPA efficiency data in cache"""
    
    # Create clean copy of essential data
    cache_data = {
        # Core analysis results
        'total_cost': float(complete_analysis_data.get('total_cost', 0)),
        'total_savings': float(complete_analysis_data.get('total_savings', 0)),
        'hpa_savings': float(complete_analysis_data.get('hpa_savings', 0)),
        'right_sizing_savings': float(complete_analysis_data.get('right_sizing_savings', 0)),
        'storage_savings': float(complete_analysis_data.get('storage_savings', 0)),
        'savings_percentage': float(complete_analysis_data.get('savings_percentage', 0)),
        'analysis_confidence': float(complete_analysis_data.get('analysis_confidence', 0)),
        
        # NEW CONSOLIDATED FIELDS - Standards-based categories and health scoring
        'savings_by_category': complete_analysis_data.get('savings_by_category', {}),
        'current_health_score': float(complete_analysis_data.get('current_health_score', 0)),
        'target_health_score': float(complete_analysis_data.get('target_health_score', 0)),
        'standards_compliance': complete_analysis_data.get('standards_compliance', {}),
        
        # Preserve ALL HPA efficiency fields
        'hpa_efficiency': complete_analysis_data.get('hpa_efficiency'),
        'hpa_efficiency_percentage': complete_analysis_data.get('hpa_efficiency_percentage'),
        'hpa_reduction': complete_analysis_data.get('hpa_reduction'),
        
        # Preserve gap data for rightsizing insights
        'cpu_gap': complete_analysis_data.get('cpu_gap'),
        'memory_gap': complete_analysis_data.get('memory_gap'),
        
        # Preserve current utilization data for enterprise metrics API
        'current_cpu_utilization': complete_analysis_data.get('current_cpu_utilization'),
        'current_memory_utilization': complete_analysis_data.get('current_memory_utilization'),
        
        # Cost breakdown
        'node_cost': float(complete_analysis_data.get('node_cost', 0)),
        'storage_cost': float(complete_analysis_data.get('storage_cost', 0)),
        'networking_cost': float(complete_analysis_data.get('networking_cost', 0)),
        'control_plane_cost': float(complete_analysis_data.get('control_plane_cost', 0)),
        'registry_cost': float(complete_analysis_data.get('registry_cost', 0)),
        'other_cost': float(complete_analysis_data.get('other_cost', 0)),
        
        # Node data (clean copy)
        'nodes': _clean_nodes_data(complete_analysis_data.get('nodes', [])),
        'has_real_node_data': bool(complete_analysis_data.get('has_real_node_data', False)),
        
        # HPA recommendations (PRESERVE ALL DATA)
        'hpa_recommendations': complete_analysis_data.get('hpa_recommendations', {}),
        
        # Metadata
        'ml_enhanced': bool(complete_analysis_data.get('ml_enhanced', False)),
        'resource_group': str(complete_analysis_data.get('resource_group', '')),
        'cluster_name': str(complete_analysis_data.get('cluster_name', '')),
        'analysis_timestamp': complete_analysis_data.get('analysis_timestamp', datetime.now().isoformat()),
        
        # Optional components (preserve everything)
        'implementation_plan': complete_analysis_data.get('implementation_plan'),
        'pod_cost_analysis': complete_analysis_data.get('pod_cost_analysis'),
        'namespace_costs': complete_analysis_data.get('namespace_costs'),
        'has_pod_costs': bool(complete_analysis_data.get('has_pod_costs', False)),
        'node_metrics': complete_analysis_data.get('node_metrics'),
        'real_node_data': complete_analysis_data.get('real_node_data')
    }
    
    # Log what HPA efficiency data we're caching
    hpa_eff = cache_data.get('hpa_efficiency')
    hpa_eff_pct = cache_data.get('hpa_efficiency_percentage')
    hpa_red = cache_data.get('hpa_reduction')
    
    logger.info(f"💾 CACHE PREP: HPA efficiency data for {cluster_id}:")
    logger.info(f"   - hpa_efficiency: {hpa_eff}")
    logger.info(f"   - hpa_efficiency_percentage: {hpa_eff_pct}")
    logger.info(f"   - hpa_reduction: {hpa_red}")
    
    # Remove None values but keep 0 values
    cache_data = {k: v for k, v in cache_data.items() if v is not None}
    
    return cache_data

def _clean_nodes_data(nodes_data: List) -> List[Dict]:
    """Clean and validate nodes data for caching"""
    if not isinstance(nodes_data, list):
        return []
    
    cleaned_nodes = []
    for node in nodes_data:
        if isinstance(node, dict):
            cleaned_node = {
                'name': str(node.get('name', 'unknown')),
                'cpu_usage_pct': float(node.get('cpu_usage_pct', 0)),
                'memory_usage_pct': float(node.get('memory_usage_pct', 0)),
                'cpu_request_pct': float(node.get('cpu_request_pct', 0)),
                'memory_request_pct': float(node.get('memory_request_pct', 0)),
                'ready': bool(node.get('ready', True))
            }
            cleaned_nodes.append(cleaned_node)
    
    return cleaned_nodes

# Background cache maintenance
def start_cache_maintenance():
    """Start background cache maintenance"""
    import time
    
    def maintenance_worker():
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                
                # Cleanup expired cache
                expired_count = cleanup_expired_cache()
                
                # Optimize cache if it's getting large
                total_entries = len(analysis_cache.get('clusters', {}))
                if total_entries > 100:
                    logger.info(f"🔧 Cache has {total_entries} entries, considering optimization")
                    optimize_cache_storage()
                
                # Clear LRU caches periodically to prevent memory leaks
                if total_entries > 200:
                    CacheKeyStrategy.generate_cache_key.cache_clear()
                    CacheKeyStrategy._get_enhanced_key.cache_clear()
                    logger.info("🧹 Cleared LRU caches due to high cache usage")
                
            except Exception as e:
                logger.error(f"❌ Cache maintenance error: {e}")
                time.sleep(300)  # Wait 5 minutes on error (reduced from 10)
    
    maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True, name="CacheMaintenance")
    maintenance_thread.start()
    logger.info("✅ Cache maintenance started")

# Cache Management APIs

def get_cache_health_status() -> Dict[str, Any]:
    """Get comprehensive cache health status"""
    try:
        total_clusters = len(analysis_cache.get('clusters', {}))
        valid_clusters = 0
        subscription_aware_clusters = 0
        reference_clusters = 0
        
        for cache_key, cache_entry in analysis_cache.get('clusters', {}).items():
            if cache_entry.get('cache_type') == 'reference':
                reference_clusters += 1
            else:
                key_info = CacheKeyStrategy.parse_cache_key(cache_key)
                if key_info['is_subscription_aware']:
                    subscription_aware_clusters += 1
                
                # Check if valid
                cluster_id = key_info['cluster_id']
                if is_cache_valid(cluster_id, key_info['subscription_id']):
                    valid_clusters += 1
        
        return {
            'total_cached_clusters': total_clusters,
            'valid_clusters': valid_clusters,
            'subscription_aware_clusters': subscription_aware_clusters,
            'reference_clusters': reference_clusters,
            'cache_health_percentage': (valid_clusters / total_clusters * 100) if total_clusters > 0 else 0,
            'enterprise_cache_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting cache health status: {e}")
        return {'error': str(e), 'enterprise_cache_enabled': True}

def optimize_cache_storage():
    """Optimize cache storage by removing expired entries and consolidating references"""
    try:
        logger.info("🔧 CACHE: Starting cache optimization...")
        
        removed_count = 0
        optimized_count = 0
        
        # Remove expired entries
        for cache_key in list(analysis_cache.get('clusters', {}).keys()):
            key_info = CacheKeyStrategy.parse_cache_key(cache_key)
            if not is_cache_valid(key_info['cluster_id'], key_info['subscription_id']):
                removed_count += 1
        
        # Consolidate references
        for cache_key, cache_entry in list(analysis_cache.get('clusters', {}).items()):
            if cache_entry.get('cache_type') == 'reference':
                reference_key = cache_entry.get('reference_to')
                if reference_key and reference_key not in analysis_cache.get('clusters', {}):
                    # Remove orphaned reference
                    del analysis_cache['clusters'][cache_key]
                    optimized_count += 1
        
        logger.info(f"✅ CACHE: Optimization complete - removed {removed_count} expired, optimized {optimized_count} references")
        
        return {
            'removed_expired': removed_count,
            'optimized_references': optimized_count,
            'total_clusters_remaining': len(analysis_cache.get('clusters', {}))
        }
    except Exception as e:
        logger.error(f"❌ Cache optimization failed: {e}")
        return {'error': str(e)}

def initialize_cache_optimization():
    """Initialize cache optimization system"""
    try:
        start_cache_maintenance()
        logger.info("✅ Cache optimization initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Cache optimization initialization failed: {e}")
        return False

# Main cache functions - Interface

def save_to_cache(cluster_id: str, complete_analysis_data: dict, subscription_id: str = None):
    """save_to_cache with subscription awareness"""
    return save_to_cache_with_validation(cluster_id, complete_analysis_data, subscription_id)

def load_from_cache(cluster_id: str, subscription_id: str = None) -> dict:
    """load_from_cache with subscription awareness"""
    return load_from_cache_with_validation(cluster_id, subscription_id)

def force_fresh_analysis_cache_clear(cluster_id: str):
    """force fresh analysis to use complete cache clear"""
    return force_fresh_analysis_with_complete_cache_clear(cluster_id)