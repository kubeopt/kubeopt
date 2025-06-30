"""
Cache Management System for AKS Cost Optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from config import logger, analysis_cache, enhanced_cluster_manager, _analysis_lock, _analysis_sessions

def is_cache_valid(cluster_id: str = None) -> bool:
    """Check if cache is valid for specific cluster or any cluster"""
    if not cluster_id:
        return False
        
    if cluster_id not in analysis_cache['clusters']:
        logger.info(f"🕐 No cache found for cluster: {cluster_id}")
        return False
    
    cluster_cache = analysis_cache['clusters'][cluster_id]
    if not cluster_cache.get('timestamp'):
        return False
    
    try:
        cache_time = datetime.fromisoformat(cluster_cache['timestamp'])
        expiry_time = cache_time + timedelta(hours=analysis_cache['global_ttl_hours'])
        
        is_valid = datetime.now() < expiry_time
        
        if not is_valid:
            logger.info(f"🕐 Cache expired for {cluster_id}: cached at {cache_time}")
            # Clean up expired cache
            del analysis_cache['clusters'][cluster_id]
        else:
            remaining = expiry_time - datetime.now()
            logger.info(f"✅ Cache valid for {cluster_id}: {remaining.total_seconds()/60:.1f} minutes remaining")
        
        return is_valid
    except Exception as e:
        logger.error(f"❌ Error checking cache validity for {cluster_id}: {e}")
        # Clean up invalid cache
        if cluster_id in analysis_cache['clusters']:
            del analysis_cache['clusters'][cluster_id]
        return False

def clear_analysis_cache(cluster_id: str = None):
    """
    PURE CACHE CLEAR: Complete cache clearing with verification
    """
    global analysis_cache
    
    if cluster_id:
        if cluster_id in analysis_cache['clusters']:
            del analysis_cache['clusters'][cluster_id]
            logger.info(f"🧹 PURE CACHE: Cleared cache for cluster: {cluster_id}")
        else:
            logger.info(f"ℹ️ PURE CACHE: No cache to clear for cluster: {cluster_id}")
    else:
        old_count = len(analysis_cache['clusters'])
        analysis_cache['clusters'] = {}
        logger.info(f"🧹 PURE CACHE: Cleared ALL cluster caches ({old_count} clusters)")

def force_fresh_analysis_with_complete_cache_clear(cluster_id: str):
    """
    Force fresh analysis with total cache clearing
    """
    logger.info(f"🔄 COMPLETE FRESH: Starting total cache clear for {cluster_id}")
    
    # Step 1: Clear cluster-specific cache
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
    from config import analysis_results
    if analysis_results:
        # Check if global results belong to this cluster
        global_rg = analysis_results.get('resource_group', '')
        global_name = analysis_results.get('cluster_name', '')
        if global_rg and global_name:
            global_cluster_id = f"{global_rg}_{global_name}"
            if global_cluster_id == cluster_id:
                analysis_results.clear()
                logger.info(f"🧹 COMPLETE FRESH: Cleared global analysis_results for {cluster_id}")
    
    # Step 4: Clear any database cache if exists
    try:
        # Force database to refresh by updating timestamp
        enhanced_cluster_manager.touch_cluster(cluster_id)
        logger.info(f"🧹 COMPLETE FRESH: Updated database timestamp for {cluster_id}")
    except Exception as db_error:
        logger.warning(f"⚠️ Database timestamp update failed: {db_error}")
    
    logger.info(f"✅ COMPLETE FRESH: Total cache clearing completed for {cluster_id}")

def save_to_cache_with_validation(cluster_id: str, complete_analysis_data: dict):
    """
    COMPLETELY FIXED: Save to cache with comprehensive validation
    """
    global analysis_cache
    
    logger.info(f"💾 FIXED CACHE SAVE: Validating data for {cluster_id}")
    
    try:
        # STEP 1: Comprehensive data validation
        validation_errors = _validate_cache_data_structure(complete_analysis_data, cluster_id)
        if validation_errors:
            raise ValueError(f"Cache validation failed: {validation_errors}")
        
        # STEP 2: Clean and prepare data for caching
        cache_data = _prepare_cache_data(complete_analysis_data, cluster_id)
        
        # STEP 3: Store in cache with metadata
        analysis_cache['clusters'][cluster_id] = {
            'data': cache_data,
            'timestamp': datetime.now().isoformat(),
            'cluster_id': cluster_id,
            'ttl_hours': analysis_cache['global_ttl_hours'],
            'cache_version': 'fixed_validation',
            'validation_passed': True,
            'data_size': len(str(cache_data)),
            'components': list(cache_data.keys())
        }
        
        logger.info(f"💾 FIXED CACHE SAVED: {cluster_id} with validated data ({len(cache_data)} components)")
        return True
        
    except Exception as cache_error:
        logger.error(f"❌ FIXED CACHE SAVE FAILED for {cluster_id}: {cache_error}")
        # Clean up any partial cache data
        if cluster_id in analysis_cache.get('clusters', {}):
            del analysis_cache['clusters'][cluster_id]
        return False

def load_from_cache_with_validation(cluster_id: str) -> dict:
    """
    COMPLETELY FIXED: Load from cache with comprehensive validation
    """
    try:
        logger.info(f"📦 FIXED CACHE LOAD: Loading data for {cluster_id}")
        
        # Check if cache exists and is valid
        if not is_cache_valid(cluster_id):
            logger.info(f"🕐 FIXED CACHE: Invalid or expired for {cluster_id}")
            return {}
        
        cluster_cache = analysis_cache['clusters'][cluster_id]
        cached_data = cluster_cache['data']
        
        # Comprehensive validation on load
        validation_errors = _validate_loaded_cache_data(cached_data, cluster_id)
        if validation_errors:
            logger.error(f"❌ FIXED CACHE VALIDATION FAILED for {cluster_id}: {validation_errors}")
            # Remove invalid cache
            del analysis_cache['clusters'][cluster_id]
            return {}
        
        # Log successful load
        cache_size = cluster_cache.get('data_size', 'unknown')
        components = len(cluster_cache.get('components', []))
        logger.info(f"📦 FIXED CACHE LOADED: {cluster_id} - ${cached_data.get('total_cost', 0):.2f}, {components} components, {cache_size} bytes")
        
        return cached_data
        
    except Exception as e:
        logger.error(f"❌ FIXED CACHE LOAD ERROR for {cluster_id}: {e}")
        # Clean up problematic cache
        if cluster_id in analysis_cache.get('clusters', {}):
            del analysis_cache['clusters'][cluster_id]
        return {}

def _validate_cache_data_structure(data: dict, cluster_id: str) -> List[str]:
    """FIXED: More lenient validation that preserves HPA efficiency data"""
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
    """FIXED: Relaxed validation when loading from cache"""
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
    """FIXED: Preserve ALL HPA efficiency data in cache"""
    
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

# Main cache functions
def save_to_cache(cluster_id: str, complete_analysis_data: dict):
    """Updated save_to_cache to use fixed validation"""
    return save_to_cache_with_validation(cluster_id, complete_analysis_data)

def load_from_cache(cluster_id: str) -> dict:
    """Updated load_from_cache to use fixed validation"""
    return load_from_cache_with_validation(cluster_id)

def force_fresh_analysis_cache_clear(cluster_id: str):
    """Updated force fresh analysis to use complete cache clear"""
    return force_fresh_analysis_with_complete_cache_clear(cluster_id)