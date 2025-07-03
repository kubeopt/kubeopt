"""
Cache Management System for AKS Cost Optimization
Complete implementation with subscription awareness, and validation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.main.config import logger, analysis_cache, enhanced_cluster_manager, _analysis_lock, _analysis_sessions, analysis_results

class CacheKeyStrategy:
    """cache key management strategy"""
    
    @staticmethod
    def generate_cache_key(cluster_id: str, subscription_id: str = None) -> str:
        """
        Generate consistent cache key based on strategy
        Strategy: Always use subscription-aware keys for consistency
        """
        if subscription_id:
            # Use subscription-aware key
            cache_key = f"{subscription_id}_{cluster_id}"
            logger.debug(f"🔑 Generated subscription-aware cache key: {cache_key}")
            return cache_key
        else:
            # Try to extract subscription from cluster_id if it's composite
            if '_' in cluster_id and len(cluster_id.split('_')[0]) > 20:  # UUID-like format
                logger.debug(f"🔑 Using existing composite cache key: {cluster_id}")
                return cluster_id
            else:
                # Simple key - try to enhance with subscription info
                try:
                    cluster_info = enhanced_cluster_manager.get_cluster(cluster_id)
                    if cluster_info and cluster_info.get('subscription_id'):
                        subscription_aware_key = f"{cluster_info['subscription_id']}_{cluster_id}"
                        logger.debug(f"🔑 Enhanced simple key to subscription-aware: {subscription_aware_key}")
                        return subscription_aware_key
                except Exception as e:
                    logger.warning(f"⚠️ Could not enhance cache key: {e}")
                
                logger.debug(f"🔑 Using simple cache key: {cluster_id}")
                return cluster_id
    
    @staticmethod
    def parse_cache_key(cache_key: str) -> Dict[str, str]:
        """Parse cache key to extract components"""
        if '_' in cache_key and len(cache_key.split('_')[0]) > 20:
            parts = cache_key.split('_', 1)
            return {
                'subscription_id': parts[0],
                'cluster_id': parts[1],
                'is_subscription_aware': True,
                'cache_key': cache_key
            }
        else:
            return {
                'subscription_id': None,
                'cluster_id': cache_key,
                'is_subscription_aware': False,
                'cache_key': cache_key
            }
    
    @staticmethod
    def find_cache_key_variants(cluster_id: str) -> List[str]:
        """Find all possible cache key variants for a cluster"""
        variants = [cluster_id]  # Start with the provided key
        
        # If it's a simple key, try to find subscription-aware variants
        if not ('_' in cluster_id and len(cluster_id.split('_')[0]) > 20):
            try:
                cluster_info = enhanced_cluster_manager.get_cluster(cluster_id)
                if cluster_info and cluster_info.get('subscription_id'):
                    subscription_aware_key = f"{cluster_info['subscription_id']}_{cluster_id}"
                    variants.append(subscription_aware_key)
            except Exception:
                pass
        
        # Check existing cache for related keys
        for existing_key in analysis_cache.get('clusters', {}):
            key_info = CacheKeyStrategy.parse_cache_key(existing_key)
            if key_info['cluster_id'] == cluster_id or existing_key == cluster_id:
                if existing_key not in variants:
                    variants.append(existing_key)
        
        return variants

def is_cache_valid(cluster_id: str = None, subscription_id: str = None) -> bool:
    """cache validity check with subscription awareness"""
    if not cluster_id:
        return False
    
    # Generate proper cache key
    cache_key = CacheKeyStrategy.generate_cache_key(cluster_id, subscription_id)
    
    if cache_key not in analysis_cache['clusters']:
        # Try alternative key formats
        key_variants = CacheKeyStrategy.find_cache_key_variants(cluster_id)
        
        valid_key = None
        for variant in key_variants:
            if variant in analysis_cache['clusters']:
                valid_key = variant
                break
        
        if not valid_key:
            logger.info(f"🕐 No cache found for cluster: {cluster_id}")
            return False
        
        cache_key = valid_key
    
    cluster_cache = analysis_cache['clusters'][cache_key]
    if not cluster_cache.get('timestamp'):
        return False
    
    try:
        cache_time = datetime.fromisoformat(cluster_cache['timestamp'])
        expiry_time = cache_time + timedelta(hours=analysis_cache['global_ttl_hours'])
        
        is_valid = datetime.now() < expiry_time
        
        if not is_valid:
            logger.info(f"🕐 Cache expired for {cluster_id}: cached at {cache_time}")
            # Clean up expired cache
            del analysis_cache['clusters'][cache_key]
        else:
            remaining = expiry_time - datetime.now()
            logger.info(f"✅ Cache valid for {cluster_id}: {remaining.total_seconds()/60:.1f} minutes remaining")
        
        return is_valid
    except Exception as e:
        logger.error(f"❌ Error checking cache validity for {cluster_id}: {e}")
        # Clean up invalid cache
        if cache_key in analysis_cache['clusters']:
            del analysis_cache['clusters'][cache_key]
        return False

def clear_analysis_cache(cluster_id: str = None, subscription_id: str = None):
    """
    ENTERPRISE: Complete cache clearing with subscription awareness
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
    ENTERPRISE: Force fresh analysis with total cache clearing and subscription awareness
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
    
    # Step 3: Clear global analysis results if they match this cluster
    try:
        
        if analysis_results:
            # Check if global results belong to this cluster
            global_rg = analysis_results.get('resource_group', '')
            global_name = analysis_results.get('cluster_name', '')
            if global_rg and global_name:
                global_cluster_id = f"{global_rg}_{global_name}"
                if global_cluster_id == cluster_id:
                    analysis_results.clear()
                    logger.info(f"🧹 COMPLETE FRESH: Cleared global analysis_results for {cluster_id}")
    except Exception as e:
        logger.warning(f"⚠️ Could not clear global analysis results: {e}")
    
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
    ENTERPRISE: Save to cache with consistent key strategy and comprehensive validation
    """
    global analysis_cache
    
    # Generate consistent cache key
    cache_key = CacheKeyStrategy.generate_cache_key(cluster_id, subscription_id)
    
    logger.info(f"💾 CACHE SAVE: Validating data for {cache_key}")
    
    try:
        # STEP 1: Comprehensive data validation
        validation_errors = _validate_cache_data_structure(complete_analysis_data, cluster_id)
        if validation_errors:
            raise ValueError(f"Cache validation failed: {validation_errors}")
        
        # STEP 2: Clean and prepare data for caching
        cache_data = _prepare_cache_data(complete_analysis_data, cluster_id)
        
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
        
        # ENTERPRISE: Also maintain a reverse lookup for simple keys
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
    ENTERPRISE: Load from cache with consistent key strategy and comprehensive validation
    """
    try:
        # Generate consistent cache key
        cache_key = CacheKeyStrategy.generate_cache_key(cluster_id, subscription_id)
        
        logger.info(f"📦 CACHE LOAD: Loading data for {cache_key}")
        
        # Try the primary cache key
        if cache_key in analysis_cache['clusters']:
            cluster_cache = analysis_cache['clusters'][cache_key]
            
            # Check if it's a reference
            if cluster_cache.get('cache_type') == 'reference':
                reference_key = cluster_cache.get('reference_to')
                if reference_key and reference_key in analysis_cache['clusters']:
                    cluster_cache = analysis_cache['clusters'][reference_key]
                    cache_key = reference_key
                    logger.info(f"📦 CACHE: Following reference to {reference_key}")
                else:
                    logger.warning(f"⚠️ CACHE: Invalid reference from {cluster_id}")
                    return {}
            
            # Check if cache is still valid
            if not is_cache_valid(cluster_id, subscription_id):
                logger.info(f"🕐 CACHE: Invalid or expired for {cache_key}")
                return {}
            
            cached_data = cluster_cache['data']
            
            # Comprehensive validation on load
            validation_errors = _validate_loaded_cache_data(cached_data, cluster_id)
            if validation_errors:
                logger.error(f"❌ CACHE VALIDATION FAILED for {cache_key}: {validation_errors}")
                # Remove invalid cache
                del analysis_cache['clusters'][cache_key]
                return {}
            
            # Log successful load
            cache_size = cluster_cache.get('data_size', 'unknown')
            components = len(cluster_cache.get('components', []))
            logger.info(f"📦 CACHE LOADED: {cache_key} - ${cached_data.get('total_cost', 0):.2f}, {components} components, {cache_size} bytes")
            
            return cached_data
        
        # Try alternative key formats
        key_variants = CacheKeyStrategy.find_cache_key_variants(cluster_id)
        
        for variant in key_variants:
            if variant in analysis_cache['clusters']:
                logger.info(f"📦 CACHE: Found alternative key {variant} for {cluster_id}")
                cluster_cache = analysis_cache['clusters'][variant]
                
                if cluster_cache.get('cache_type') == 'reference':
                    continue  # Skip references in variants
                
                cached_data = cluster_cache.get('data', {})
                if cached_data:
                    # Validate the found data
                    validation_errors = _validate_loaded_cache_data(cached_data, cluster_id)
                    if not validation_errors:
                        logger.info(f"📦 CACHE LOADED (variant): {variant} - ${cached_data.get('total_cost', 0):.2f}")
                        return cached_data
        
        logger.info(f"📦 CACHE: No valid cache found for {cluster_id}")
        return {}
        
    except Exception as e:
        logger.error(f"❌ CACHE LOAD ERROR for {cluster_id}: {e}")
        return {}

def _validate_cache_data_structure(data: dict, cluster_id: str) -> List[str]:
    """ENTERPRISE: More lenient validation that preserves HPA efficiency data"""
    errors = []
    
    # Check required top-level components (relaxed validation)
    required_components = {
        'total_cost': (int, float),
        'hpa_recommendations': dict,
    }
    
    for component, expected_type in required_components.items():
        if component not in data:
            errors.append(f"Missing required component: {component}")
        elif not isinstance(data[component], expected_type):
            errors.append(f"Invalid type for {component}: expected {expected_type}, got {type(data[component])}")
    
    # Validate cost data
    total_cost = data.get('total_cost', 0)
    if not isinstance(total_cost, (int, float)) or total_cost <= 0:
        errors.append(f"Invalid total_cost: {total_cost}")
    
    # RELAXED HPA validation - just check if it exists and has some content
    hpa_recs = data.get('hpa_recommendations', {})
    if isinstance(hpa_recs, dict):
        if len(hpa_recs) == 0:
            errors.append("Empty HPA recommendations")
        # REMOVED: ml_enhanced requirement - this was causing cache to be rejected
        # REMOVED: optimization_recommendation requirement - too strict
    
    # Optional nodes validation (don't fail if missing)
    nodes = data.get('nodes', [])
    if nodes and isinstance(nodes, list) and len(nodes) == 0:
        logger.warning(f"⚠️ Empty nodes data for {cluster_id}")
    
    # KEY FIX: Preserve HPA efficiency at top level
    hpa_efficiency_found = False
    efficiency_keys = ['hpa_efficiency', 'hpa_efficiency_percentage', 'hpa_reduction']
    for key in efficiency_keys:
        if data.get(key) is not None and data.get(key) > 0:
            hpa_efficiency_found = True
            logger.info(f"✅ Found HPA efficiency in cache validation: {key}={data.get(key):.1f}%")
            break
    
    if not hpa_efficiency_found:
        logger.warning(f"⚠️ No HPA efficiency found during cache validation for {cluster_id}")
    
    return errors

def _validate_loaded_cache_data(cached_data: dict, cluster_id: str) -> List[str]:
    """ENTERPRISE: Relaxed validation when loading from cache"""
    errors = []
    
    # Check essential components
    if not cached_data.get('total_cost', 0) > 0:
        errors.append("Invalid or missing total_cost")
    
    if not isinstance(cached_data.get('hpa_recommendations'), dict):
        errors.append("Invalid HPA recommendations structure")
    
    # REMOVED: Strict ML enhancement requirement
    # REMOVED: Strict nodes requirement
    
    # Check if HPA efficiency exists in any form
    hpa_efficiency_found = False
    efficiency_keys = ['hpa_efficiency', 'hpa_efficiency_percentage', 'hpa_reduction']
    for key in efficiency_keys:
        if cached_data.get(key) is not None:
            hpa_efficiency_found = True
            logger.info(f"✅ Found HPA efficiency in loaded cache: {key}={cached_data.get(key)}")
            break
    
    if not hpa_efficiency_found:
        logger.warning(f"⚠️ No HPA efficiency in loaded cache for {cluster_id}")
    
    return errors

def _prepare_cache_data(complete_analysis_data: dict, cluster_id: str) -> dict:
    """ENTERPRISE: Preserve ALL HPA efficiency data in cache"""
    
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
        
        # CRITICAL FIX: Preserve ALL HPA efficiency fields
        'hpa_efficiency': complete_analysis_data.get('hpa_efficiency'),
        'hpa_efficiency_percentage': complete_analysis_data.get('hpa_efficiency_percentage'),
        'hpa_reduction': complete_analysis_data.get('hpa_reduction'),
        
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
    
    # CRITICAL: Log what HPA efficiency data we're caching
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

def _clean_hpa_data(hpa_data: Dict) -> Dict:
    """Clean and validate HPA data for caching"""
    if not isinstance(hpa_data, dict):
        return {}
    
    cleaned_hpa = {
        'ml_enhanced': bool(hpa_data.get('ml_enhanced', False)),
        'optimization_recommendation': hpa_data.get('optimization_recommendation', {}),
        'current_implementation': hpa_data.get('current_implementation', {}),
        'hpa_chart_data': hpa_data.get('hpa_chart_data', {}),
        'workload_characteristics': hpa_data.get('workload_characteristics', {})
    }
    
    return cleaned_hpa

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

# Legacy compatibility functions (maintained for backward compatibility)

def force_fresh_analysis_with_complete_cache_clear(cluster_id: str):
    """Legacy function name - redirects to latest version"""
    return force_fresh_analysis_with_complete_cache_clear(cluster_id)