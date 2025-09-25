#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Enhanced Utility Functions for AKS Cost Optimization Tool
Added subscription-aware kubectl execution to prevent context conflicts
Updated with enhanced cost validation matching the enhanced categorization
"""

import statistics
import subprocess
import threading
import time
from typing import Any, Optional, Dict
from contextlib import contextmanager
from shared.config.config import logger

# ============================================================================
# EXISTING UTILITY FUNCTIONS
# ============================================================================

def convert_k8s_memory_to_bytes(mem_str):
    """Convert Kubernetes memory string (e.g., 2Gi, 100Mi, 1000Ki) to bytes"""
    if mem_str.endswith('Ki'):
        return float(mem_str[:-2]) * 1024
    elif mem_str.endswith('Mi'):
        return float(mem_str[:-2]) * 1024 * 1024
    elif mem_str.endswith('Gi'):
        return float(mem_str[:-2]) * 1024 * 1024 * 1024
    elif mem_str.endswith('Ti'):
        return float(mem_str[:-2]) * 1024 * 1024 * 1024 * 1024
    elif mem_str.endswith('k'):
        return float(mem_str[:-1]) * 1000
    elif mem_str.endswith('M'):
        return float(mem_str[:-1]) * 1000 * 1000
    elif mem_str.endswith('G'):
        return float(mem_str[:-1]) * 1000 * 1000 * 1000
    elif mem_str.endswith('T'):
        return float(mem_str[:-1]) * 1000 * 1000 * 1000 * 1000
    else:
        return float(mem_str)

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_mean(values):
    """Calculate mean safely, handling empty lists"""
    try:
        return statistics.mean(values) if values else 0.0
    except (TypeError, ValueError):
        return 0.0

def validate_cost_data(cost_components):
    """Enhanced validation that matches the enhanced cost categorization"""
    try:
        # Enhanced validation with all new categories
        component_sum = (
            cost_components.get('node_cost', 0) +
            cost_components.get('storage_cost', 0) +
            cost_components.get('networking_cost', 0) +
            cost_components.get('control_plane_cost', 0) +
            cost_components.get('registry_cost', 0) +
            cost_components.get('other_cost', 0) +
            # NEW Enhanced categories
            cost_components.get('application_services_cost', 0) +
            cost_components.get('data_services_cost', 0) +
            cost_components.get('integration_services_cost', 0) +
            cost_components.get('devops_cost', 0) +
            cost_components.get('backup_recovery_cost', 0) +
            cost_components.get('governance_cost', 0) +
            cost_components.get('support_management_cost', 0) +
            # Enhanced add-on services
            cost_components.get('monitoring_cost', 0) +
            cost_components.get('security_cost', 0) +
            cost_components.get('keyvault_cost', 0)
        )
        
        total_cost = cost_components.get('total_cost', 0)
        
        # Allow for small rounding differences (1%)
        if abs(component_sum - total_cost) > (total_cost * 0.01):
            logger.warning(f"Enhanced cost validation warning: components sum ${component_sum:.2f} != total ${total_cost:.2f}")
            logger.warning(f"Difference: ${abs(component_sum - total_cost):.2f} ({abs(component_sum - total_cost)/total_cost*100:.1f}%)")
            
            # Enhanced debugging - show what's contributing to costs
            logger.info("💰 Cost breakdown for validation:")
            for category, cost in [
                ('node_cost', cost_components.get('node_cost', 0)),
                ('storage_cost', cost_components.get('storage_cost', 0)),
                ('networking_cost', cost_components.get('networking_cost', 0)),
                ('control_plane_cost', cost_components.get('control_plane_cost', 0)),
                ('registry_cost', cost_components.get('registry_cost', 0)),
                ('application_services_cost', cost_components.get('application_services_cost', 0)),
                ('data_services_cost', cost_components.get('data_services_cost', 0)),
                ('integration_services_cost', cost_components.get('integration_services_cost', 0)),
                ('devops_cost', cost_components.get('devops_cost', 0)),
                ('backup_recovery_cost', cost_components.get('backup_recovery_cost', 0)),
                ('governance_cost', cost_components.get('governance_cost', 0)),
                ('support_management_cost', cost_components.get('support_management_cost', 0)),
                ('monitoring_cost', cost_components.get('monitoring_cost', 0)),
                ('security_cost', cost_components.get('security_cost', 0)),
                ('keyvault_cost', cost_components.get('keyvault_cost', 0)),
                ('other_cost', cost_components.get('other_cost', 0))
            ]:
                if cost > 0:
                    logger.info(f"  - {category}: ${cost:.2f}")
            
            # Fix by adjusting the total to match components
            cost_components['total_cost'] = component_sum
            logger.info(f"✅ Enhanced validation: Adjusted total cost to match components: ${component_sum:.2f}")
        else:
            logger.info(f"✅ Enhanced cost validation passed: ${component_sum:.2f} = ${total_cost:.2f}")
            
        return cost_components
    except Exception as e:
        logger.error(f"Enhanced cost validation error: {e}")
        return cost_components

def format_currency(amount):
    """Format currency with appropriate precision"""
    if amount >= 1000:
        return f"${amount:,.0f}"
    else:
        return f"${amount:.2f}"

def time_ago(timestamp_str):
    """Convert timestamp to human-readable time ago"""
    if not timestamp_str:
        return 'Never'
    
    try:
        from datetime import datetime
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        diff = datetime.now() - timestamp.replace(tzinfo=None)
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
    except:
        return 'Unknown'

def environment_badge_class(environment):
    """Get CSS class for environment badge"""
    env_classes = {
        'production': 'bg-danger',
        'staging': 'bg-warning',
        'development': 'bg-info',
        'testing': 'bg-secondary'
    }
    return env_classes.get(environment.lower(), 'bg-secondary')

def status_indicator_class(cluster):
    """Get CSS class for cluster status indicator"""
    last_analyzed = cluster.get('last_analyzed')
    savings = cluster.get('last_savings', 0)
    
    if not last_analyzed:
        return 'error'
    elif savings > 100:
        return 'warning'
    else:
        return 'healthy'

# ============================================================================
# NEW SUBSCRIPTION-AWARE KUBECTL UTILITIES
# ============================================================================

class SubscriptionAwareKubectlExecutor:
    """
    Thread-safe kubectl executor that maintains subscription context isolation
    Prevents subscription context conflicts during parallel analysis
    """
    
    def __init__(self, resource_group: str, cluster_name: str, subscription_id: str):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.subscription_id = subscription_id
        self.thread_id = threading.get_ident()
        self._local = threading.local()
        
        logger.info(f"🌐 Created subscription-aware kubectl executor for {cluster_name} in {subscription_id[:8]} (thread: {self.thread_id})")
    
    def execute_command(self, kubectl_cmd: str, timeout: int = 120) -> Optional[str]:
        """
        Execute kubectl command via centralized kubernetes_data_cache
        DEPRECATED: Use kubernetes_data_cache directly instead
        """
        try:
            from shared.kubernetes_data_cache import execute_cluster_command
            
            logger.debug(f"🔄 Thread {self.thread_id}: Executing via centralized cache: {kubectl_cmd}")
            return execute_cluster_command(
                cluster_name=self.cluster_name,
                resource_group=self.resource_group,
                subscription_id=self.subscription_id,
                kubectl_cmd=kubectl_cmd
            )
                
        except Exception as e:
            logger.error(f"❌ Thread {self.thread_id}: kubectl command error via cache: {e}")
            return None
    
    def execute_with_fallback(self, primary_cmd: str, fallback_cmd: str = None, timeout: int = 120) -> Optional[str]:
        """
        Execute kubectl command with fallback option for better reliability
        """
        # Try primary command
        result = self.execute_command(primary_cmd, timeout)
        if result:
            return result
        
        # Try fallback if provided
        if fallback_cmd:
            logger.info(f"🔄 Thread {self.thread_id}: Primary command failed, trying fallback...")
            return self.execute_command(fallback_cmd, timeout)
        
        return None
    
    def _clean_output(self, raw_output: str) -> str:
        """Clean kubectl output from Azure CLI metadata"""
        if not raw_output:
            return ""
        
        lines = raw_output.split('\n')
        clean_lines = []
        
        for line in lines:
            # Skip Azure CLI command metadata
            if any(skip_pattern in line.lower() for skip_pattern in [
                'command started at', 'command finished at', 'exitcode=',
                'command started', 'command finished'
            ]):
                continue
            clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()
    
    def validate_subscription_context(self) -> bool:
        """
        Validate that the subscription context is correct for this executor
        """
        try:
            # Quick validation command
            result = self.execute_command("kubectl cluster-info", timeout=30)
            if result and "Kubernetes" in result:
                logger.info(f"✅ Thread {self.thread_id}: Subscription context validated for {self.subscription_id[:8]}")
                return True
            else:
                logger.warning(f"⚠️ Thread {self.thread_id}: Subscription context validation failed for {self.subscription_id[:8]}")
                return False
        except Exception as e:
            logger.error(f"❌ Thread {self.thread_id}: Subscription context validation error: {e}")
            return False

class SubscriptionContextManager:
    """
    Manages subscription contexts across multiple threads to prevent conflicts
    """
    
    _active_contexts = {}  # Thread ID -> Subscription ID mapping
    _context_lock = threading.Lock()
    
    @classmethod
    def register_thread_context(cls, subscription_id: str) -> str:
        """Register subscription context for current thread"""
        thread_id = threading.get_ident()
        
        with cls._context_lock:
            if thread_id in cls._active_contexts:
                old_subscription = cls._active_contexts[thread_id]
                if old_subscription != subscription_id:
                    logger.warning(f"⚠️ Thread {thread_id}: Changing subscription context from {old_subscription[:8]} to {subscription_id[:8]}")
            
            cls._active_contexts[thread_id] = subscription_id
            logger.debug(f"🌐 Thread {thread_id}: Registered subscription context {subscription_id[:8]}")
            
        return subscription_id
    
    @classmethod
    def unregister_thread_context(cls) -> None:
        """Unregister subscription context for current thread"""
        thread_id = threading.get_ident()
        
        with cls._context_lock:
            if thread_id in cls._active_contexts:
                subscription_id = cls._active_contexts.pop(thread_id)
                logger.debug(f"🌐 Thread {thread_id}: Unregistered subscription context {subscription_id[:8]}")
    
    @classmethod
    def get_active_contexts(cls) -> Dict[int, str]:
        """Get all active subscription contexts"""
        with cls._context_lock:
            return cls._active_contexts.copy()
    
    @classmethod
    def check_context_conflicts(cls) -> Dict[str, list]:
        """Check for potential subscription context conflicts"""
        with cls._context_lock:
            subscription_threads = {}
            
            for thread_id, subscription_id in cls._active_contexts.items():
                if subscription_id not in subscription_threads:
                    subscription_threads[subscription_id] = []
                subscription_threads[subscription_id].append(thread_id)
            
            # Report conflicts (multiple threads using same subscription)
            conflicts = {sub_id: threads for sub_id, threads in subscription_threads.items() if len(threads) > 1}
            
            if conflicts:
                logger.warning(f"⚠️ Subscription context conflicts detected: {conflicts}")
            
            return conflicts

# ============================================================================
# CONVENIENCE FUNCTIONS FOR SUBSCRIPTION-AWARE OPERATIONS
# ============================================================================

def create_subscription_aware_executor(resource_group: str, cluster_name: str, subscription_id: str) -> SubscriptionAwareKubectlExecutor:
    """
    Create a subscription-aware kubectl executor for safe parallel operations
    """
    if not subscription_id:
        raise ValueError("Subscription ID is required for subscription-aware operations")
    
    # Register context for current thread
    SubscriptionContextManager.register_thread_context(subscription_id)
    
    return SubscriptionAwareKubectlExecutor(resource_group, cluster_name, subscription_id)

def validate_subscription_id_format(subscription_id: str) -> bool:
    """
    Validate that subscription ID has proper Azure GUID format
    """
    import re
    
    if not subscription_id:
        return False
    
    # Azure subscription IDs are GUIDs: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(guid_pattern, subscription_id, re.IGNORECASE))

def get_subscription_context_status() -> Dict:
    """
    Get comprehensive status of subscription contexts across all threads
    """
    active_contexts = SubscriptionContextManager.get_active_contexts()
    conflicts = SubscriptionContextManager.check_context_conflicts()
    
    return {
        'active_threads': len(active_contexts),
        'active_contexts': active_contexts,
        'conflicts': conflicts,
        'total_subscriptions': len(set(active_contexts.values())) if active_contexts else 0,
        'has_conflicts': len(conflicts) > 0
    }

@contextmanager
def subscription_context(subscription_id: str):
    """
    Context manager for temporary subscription context registration
    
    Usage:
        with subscription_context(subscription_id):
            # All operations in this block use the specified subscription
            executor = create_subscription_aware_executor(rg, cluster, subscription_id)
            result = executor.execute_command("kubectl get nodes")
    """
    SubscriptionContextManager.register_thread_context(subscription_id)
    try:
        yield subscription_id
    finally:
        SubscriptionContextManager.unregister_thread_context()

# ============================================================================
# SUBSCRIPTION ID VALIDATION AND UTILITIES
# ============================================================================

def extract_subscription_from_cluster_id(cluster_id: str) -> Optional[str]:
    """
    Extract subscription ID from composite cluster IDs if present
    """
    if not cluster_id:
        return None
    
    # Check if cluster_id contains subscription info (format: subscription_resourcegroup_clustername)
    parts = cluster_id.split('_')
    if len(parts) >= 3:
        potential_sub_id = parts[0]
        if validate_subscription_id_format(potential_sub_id):
            return potential_sub_id
    
    return None

def safe_subscription_operation(func, subscription_id: str, *args, **kwargs):
    """
    Safely execute function with subscription context, with error handling
    """
    if not validate_subscription_id_format(subscription_id):
        logger.error(f"❌ Invalid subscription ID format: {subscription_id}")
        return None
    
    try:
        with subscription_context(subscription_id):
            return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"❌ Subscription operation failed for {subscription_id[:8]}: {e}")
        return None

# ============================================================================
# DEBUGGING AND MONITORING UTILITIES
# ============================================================================

def log_subscription_context_debug():
    """
    Log current subscription context status for debugging
    """
    status = get_subscription_context_status()
    
    logger.info("=" * 60)
    logger.info("🌐 SUBSCRIPTION CONTEXT DEBUG")
    logger.info("=" * 60)
    logger.info(f"Active threads: {status['active_threads']}")
    logger.info(f"Total subscriptions: {status['total_subscriptions']}")
    logger.info(f"Has conflicts: {status['has_conflicts']}")
    
    if status['active_contexts']:
        logger.info("Active contexts:")
        for thread_id, sub_id in status['active_contexts'].items():
            logger.info(f"  Thread {thread_id}: {sub_id[:8]}...")
    
    if status['conflicts']:
        logger.warning("CONFLICTS DETECTED:")
        for sub_id, threads in status['conflicts'].items():
            logger.warning(f"  Subscription {sub_id[:8]}: {len(threads)} threads ({threads})")
    
    logger.info("=" * 60)

def cleanup_thread_contexts():
    """
    Clean up subscription contexts for completed threads
    """
    import threading
    
    active_thread_ids = {t.ident for t in threading.enumerate()}
    registered_contexts = SubscriptionContextManager.get_active_contexts()
    
    cleanup_count = 0
    for thread_id in list(registered_contexts.keys()):
        if thread_id not in active_thread_ids:
            # Thread is dead, clean up its context
            with SubscriptionContextManager._context_lock:
                if thread_id in SubscriptionContextManager._active_contexts:
                    subscription_id = SubscriptionContextManager._active_contexts.pop(thread_id)
                    logger.info(f"🧹 Cleaned up subscription context for dead thread {thread_id}: {subscription_id[:8]}")
                    cleanup_count += 1
    
    if cleanup_count > 0:
        logger.info(f"🧹 Cleaned up {cleanup_count} dead thread subscription contexts")
    
    return cleanup_count