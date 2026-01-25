#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Azure Subscription Manager for Multi-Subscription AKS Cost Optimization
"""

import json
# Removed subprocess import - using Azure SDK instead  
import logging
import threading
import time
import queue
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from dataclasses import dataclass

import concurrent

logger = logging.getLogger(__name__)

@dataclass
class SubscriptionInfo:
    subscription_id: str
    subscription_name: str
    tenant_id: str
    state: str
    is_default: bool = False
    last_accessed: Optional[str] = None

class AzureSubscriptionManager:
    """Manages multiple Azure subscriptions for parallel AKS analysis with controlled threading"""
    
    def __init__(self):
        self.subscriptions_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_expiry = timedelta(hours=1)
        self.last_cache_update = None
        
        # Controlled thread pool for Azure SDK operations
        self.az_thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="AZ-SDK")
        self.operation_semaphore = threading.Semaphore(5)  # Max 5 concurrent operations
        self.operation_queue = queue.Queue(maxsize=20)
        
        # SDK-based operation management - no CLI rate limiting needed
        # Azure SDK has built-in rate limiting and retry policies
    
    @lru_cache(maxsize=100)
    def get_available_subscriptions(self, force_refresh: bool = False) -> List[SubscriptionInfo]:
        """Get all available Azure subscriptions using SDK"""
        
        # Check cache first (unless force refresh)
        with self.cache_lock:
            if (not force_refresh and self.subscriptions_cache and 
                self.last_cache_update and 
                datetime.now() - self.last_cache_update < self.cache_expiry):
                logger.info(f"📋 Using cached subscriptions ({len(self.subscriptions_cache)} found)")
                return list(self.subscriptions_cache.values())
        
        logger.info("🔍 Fetching available Azure subscriptions via SDK...")
        
        try:
            # Use Azure SDK instead of CLI
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager, AZURE_SDK_AVAILABLE
            
            if not AZURE_SDK_AVAILABLE:
                logger.error("❌ Azure SDK not available - CLI fallback removed")
                return []
            
            if not azure_sdk_manager.is_authenticated():
                logger.error("❌ Azure SDK not authenticated")
                logger.debug(f"❌ Credential available: {azure_sdk_manager.credential is not None}")
                logger.debug(f"❌ Auth time: {azure_sdk_manager._auth_time}")
                return []
            else:
                logger.info("✅ Azure SDK is authenticated, proceeding with subscription fetch")
            
            from azure.mgmt.resource import SubscriptionClient
            
            # Create subscription client
            subscription_client = SubscriptionClient(azure_sdk_manager.credential)
            
            # Get all subscriptions
            subscriptions_data = []
            for subscription in subscription_client.subscriptions.list():
                if subscription.state and subscription.state.lower() == 'enabled':
                    subscriptions_data.append({
                        'id': subscription.subscription_id,
                        'name': subscription.display_name,
                        'tenantId': subscription.tenant_id,
                        'state': subscription.state,
                        'isDefault': False  # SDK doesn't provide default info easily
                    })
            subscriptions = []
            
            with self.cache_lock:
                self.subscriptions_cache = {}
                
                for sub_data in subscriptions_data:
                    # Only include enabled subscriptions
                    if sub_data.get('state', '').lower() == 'enabled':
                        subscription = SubscriptionInfo(
                            subscription_id=sub_data['id'],
                            subscription_name=sub_data['name'],
                            tenant_id=sub_data['tenantId'],
                            state=sub_data['state'],
                            is_default=sub_data.get('isDefault', False)
                        )
                        subscriptions.append(subscription)
                        self.subscriptions_cache[subscription.subscription_id] = subscription
                
                self.last_cache_update = datetime.now()
            
            logger.info(f"✅ Found {len(subscriptions)} enabled subscriptions")
            return subscriptions
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse subscription data: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching subscriptions: {e}")
            return []
    
    def get_subscription_info(self, subscription_id: str) -> Optional[SubscriptionInfo]:
        """Get specific subscription information with caching"""
        with self.cache_lock:
            if subscription_id in self.subscriptions_cache:
                return self.subscriptions_cache[subscription_id]
        
        # Only refresh if not found in cache
        subscriptions = self.get_available_subscriptions(force_refresh=True)
        for sub in subscriptions:
            if sub.subscription_id == subscription_id:
                return sub
        
        return None
    
    def set_active_subscription(self, subscription_id: str) -> bool:
        """Validate subscription access using Azure SDK (no CLI switching needed)"""
        try:
            logger.info(f"🔄 Validating subscription access: {subscription_id}")
            
            # Import Azure SDK manager
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            
            # Test subscription access by trying to get a client
            # This validates both authentication and subscription access
            resource_client = azure_sdk_manager.get_resource_client(subscription_id)
            if resource_client:
                # Try a simple API call to validate access
                try:
                    # List resource groups (minimal operation to test access)
                    list(resource_client.resource_groups.list())
                    logger.info(f"✅ Successfully validated subscription access: {subscription_id}")
                    return True
                except Exception as api_error:
                    logger.error(f"❌ Cannot access subscription {subscription_id}: {api_error}")
                    return False
            else:
                logger.error(f"❌ Cannot create client for subscription: {subscription_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validating subscription {subscription_id}: {e}")
            return False
    
    def execute_with_subscription_context(self, subscription_id: str, func, *args, **kwargs):
        """Execute function with specific subscription context using Azure SDK"""
        
        # Limit concurrent subscription operations
        if not self.operation_semaphore.acquire(timeout=30):
            raise Exception("Too many concurrent subscription operations")
        
        try:
            # Validate subscription access first
            if not self.set_active_subscription(subscription_id):
                raise Exception(f"Cannot access subscription {subscription_id}")
            
            # Execute function with subscription_id passed as context
            # The function should use Azure SDK clients with the subscription_id parameter
            result = func(*args, **kwargs, subscription_id=subscription_id)
            return result
            
        finally:
            # No cleanup needed - Azure SDK manages per-client subscription context
            self.operation_semaphore.release()
    
    @lru_cache(maxsize=10, typed=False)
    def get_current_subscription(self) -> Optional[str]:
        """Get currently active subscription ID using Azure SDK with caching"""
        try:
            # Use centralized Azure SDK manager instead of creating new credentials
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            
            if not azure_sdk_manager.is_authenticated():
                logger.warning("⚠️ SDK: Azure SDK manager not authenticated")
                return None
            
            # Try SDK approach first
            try:
                from azure.mgmt.subscription import SubscriptionClient
                subscription_client = SubscriptionClient(azure_sdk_manager.credential)
                
                # Get the default subscription from the credential context
                # The SDK will use the default subscription from the authentication context
                subscriptions = list(subscription_client.subscriptions.list())
                
                if subscriptions:
                    default_subscription = subscriptions[0]
                    subscription_id = default_subscription.subscription_id
                    logger.info(f"✅ SDK: Got current subscription {subscription_id[:8]}...")
                    return subscription_id
                else:
                    logger.warning("⚠️ SDK: No subscriptions found in authentication context")
                    return None
                    
            except (AttributeError, ImportError) as e:
                # SDK version issue or module missing - try az CLI as alternative
                logger.debug(f"SDK issue ({type(e).__name__}), trying az CLI")
                import subprocess
                result = subprocess.run(
                    ["az", "account", "show", "--query", "id", "-o", "tsv"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    subscription_id = result.stdout.strip()
                    logger.info(f"✅ Got subscription from az CLI: {subscription_id[:8]}...")
                    return subscription_id
                return None
                
        except Exception as e:
            # Check if this is an authentication issue
            if "DefaultAzureCredential failed" in str(e) or "tenant" in str(e).lower():
                logger.error("❌ SDK: Azure authentication failed. Please either:")
                logger.error("   1. Run 'az login' to authenticate with Azure CLI, OR")
                logger.error("   2. Set proper values in .env file (remove placeholder values):")
                logger.error("      AZURE_TENANT_ID=your-real-tenant-id")
                logger.error("      AZURE_CLIENT_ID=your-real-client-id") 
                logger.error("      AZURE_CLIENT_SECRET=your-real-client-secret")
                logger.error("      AZURE_SUBSCRIPTION_ID=your-real-subscription-id")
            else:
                logger.error(f"❌ SDK: Error getting current subscription: {e}")
            return None
    
    def find_cluster_subscription(self, resource_group: str, cluster_name: str) -> Optional[str]:
        """Find which subscription contains the specified cluster"""
        subscriptions = self.get_available_subscriptions()
        
        logger.info(f"🔍 Searching for cluster {cluster_name} in {resource_group} across {len(subscriptions)} subscriptions")
        
        # Use our controlled thread pool instead of creating new one
        def search_subscription(subscription):
            """Search function to be run in controlled thread pool"""
            try:
                cluster_found = self._check_cluster_in_subscription(
                    subscription.subscription_id, resource_group, cluster_name
                )
                return (subscription, cluster_found)
            except Exception as e:
                logger.warning(f"⚠️ Error checking subscription {subscription.subscription_name}: {e}")
                return (subscription, False)
        
        # Submit searches to our controlled thread pool
        futures = []
        for subscription in subscriptions:
            future = self.az_thread_pool.submit(search_subscription, subscription)
            futures.append(future)
        
        # Collect results with timeout
        for future in concurrent.futures.as_completed(futures, timeout=120):  # 2 minute timeout
            try:
                subscription, cluster_found = future.result()
                if cluster_found is not None and cluster_found:
                    logger.info(f"✅ Found cluster {cluster_name} in subscription: {subscription.subscription_name}")
                    
                    # Cancel remaining futures to save resources
                    for remaining_future in futures:
                        if not remaining_future.done():
                            remaining_future.cancel()
                    
                    return subscription.subscription_id
            except Exception as e:
                logger.warning(f"⚠️ Error in subscription search: {e}")
        
        logger.warning(f"❌ Cluster {cluster_name} not found in any subscription")
        return None
    
    def _check_cluster_in_subscription(self, subscription_id: str, resource_group: str, cluster_name: str) -> bool:
        """Check if cluster exists in specific subscription using Azure SDK"""
        try:
            # Use Azure SDK instead of CLI
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            
            # Get AKS client for the subscription
            aks_client = azure_sdk_manager.get_aks_client(subscription_id)
            if not aks_client:
                return False
            
            # Try to get the cluster - if it exists, this won't throw an exception
            cluster = aks_client.managed_clusters.get(resource_group, cluster_name)
            return cluster is not None and cluster.name == cluster_name
            
        except Exception:
            return False
    
    def validate_cluster_access(self, subscription_id: str, resource_group: str, cluster_name: str) -> Dict[str, any]:
        """Validate that we can access the specified cluster with enhanced auto-discovery"""
        try:
            logger.info(f"🔍 Validating access to cluster {cluster_name} in subscription {subscription_id}")
            
            # First try with provided resource group if specified
            if resource_group and resource_group.strip():
                result = self._validate_cluster_in_rg(subscription_id, resource_group.strip(), cluster_name)
                if result['valid']:
                    return result
                    
                # If resource group not found, log and continue with auto-discovery
                if 'ResourceGroupNotFound' in result.get('error', ''):
                    logger.warning(f"🔍 Resource group '{resource_group}' not found in subscription {subscription_id}, attempting auto-discovery")
                else:
                    # Other errors (like cluster not found in RG) should return immediately
                    return result
            
            # Auto-discovery: search for cluster across all resource groups in subscription
            logger.info(f"🔍 Auto-discovering cluster {cluster_name} across all resource groups in subscription {subscription_id}")
            return self._auto_discover_cluster(subscription_id, cluster_name)
                
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {e}', 'subscription_id': subscription_id}
    
    def _validate_cluster_in_rg(self, subscription_id: str, resource_group: str, cluster_name: str) -> Dict[str, any]:
        """Validate cluster in specific resource group using Azure SDK"""
        try:
            # Use Azure SDK instead of CLI
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            
            # Get AKS client for the subscription
            aks_client = azure_sdk_manager.get_aks_client(subscription_id)
            if not aks_client:
                return {
                    'valid': False,
                    'error': f'Cannot get AKS client for subscription {subscription_id}',
                    'subscription_id': subscription_id
                }
            
            # Get cluster information
            cluster = aks_client.managed_clusters.get(resource_group, cluster_name)
            
            if cluster is not None and cluster:
                cluster_info = {
                    'name': cluster.name,
                    'location': cluster.location,
                    'powerState': cluster.power_state.code if cluster.power_state else 'Unknown',
                    'provisioningState': cluster.provisioning_state,
                    'resourceGroup': resource_group,
                    'tags': cluster.tags or {}
                }
                logger.info(f"✅ SDK: Cluster validation successful: {cluster_info}")
                return {
                    'valid': True,
                    'cluster_info': cluster_info,
                    'subscription_id': subscription_id,
                    'discovered_resource_group': resource_group
                }
            else:
                return {
                    'valid': False,
                    'error': f'Cluster {cluster_name} not found in resource group {resource_group}',
                    'subscription_id': subscription_id
                }
                
        except Exception as e:
            return {'valid': False, 'error': f'SDK Cluster validation error: {e}', 'subscription_id': subscription_id}
    
    def _auto_discover_cluster(self, subscription_id: str, cluster_name: str) -> Dict[str, any]:
        """Auto-discover cluster by searching all resource groups in subscription using Azure SDK"""
        try:
            # Use Azure SDK instead of CLI
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            
            # Get AKS client for the subscription
            aks_client = azure_sdk_manager.get_aks_client(subscription_id)
            if not aks_client:
                return {
                    'valid': False,
                    'error': f'Cannot get AKS client for subscription {subscription_id}',
                    'subscription_id': subscription_id
                }
            
            # List all AKS clusters in the subscription
            clusters = list(aks_client.managed_clusters.list())
            
            # Find matching cluster by name
            for cluster in clusters:
                if cluster.name == cluster_name:
                    cluster_info = {
                        'name': cluster.name,
                        'location': cluster.location,
                        'powerState': cluster.power_state.code if cluster.power_state else 'Unknown',
                        'provisioningState': cluster.provisioning_state,
                        'resourceGroup': cluster.id.split('/')[4]  # Extract RG from cluster ID
                    }
                    
                    logger.info(f"✅ SDK: Cluster auto-discovery successful: {cluster_info}")
                    return {
                        'valid': True,
                        'cluster_info': cluster_info,
                        'subscription_id': subscription_id,
                        'discovered_resource_group': cluster_info['resourceGroup'],
                        'auto_discovered': True
                    }
            
            # Cluster not found
            return {
                'valid': False,
                'error': f'Cluster "{cluster_name}" not found in subscription {subscription_id}',
                'subscription_id': subscription_id,
                'suggestion': 'Verify cluster name and subscription access'
            }
                
        except Exception as e:
            return {'valid': False, 'error': f'SDK Auto-discovery error: {e}', 'subscription_id': subscription_id}
    
    def cleanup_caches(self):
        """Cleanup cached data periodically"""
        try:
            # Clear LRU caches
            self.get_available_subscriptions.cache_clear()
            self.get_current_subscription.cache_clear()
            
            # Clear internal cache if old
            with self.cache_lock:
                if (self.last_cache_update and 
                    datetime.now() - self.last_cache_update > timedelta(hours=2)):
                    self.subscriptions_cache.clear()
                    self.last_cache_update = None
                    logger.info("🧹 Cleared subscription cache")
            
            # Clear rate limiting history
            current_time = time.time()
            old_operations = [
                op for op, last_time in self.last_az_call.items()
                if current_time - last_time > 300  # 5 minutes old
            ]
            for op in old_operations:
                del self.last_az_call[op]
                
            if old_operations is not None and old_operations:
                logger.info(f"🧹 Cleared {len(old_operations)} old rate limit entries")
                
        except Exception as e:
            logger.error(f"❌ Error during subscription manager cleanup: {e}")
    
    def get_thread_status(self) -> Dict[str, Any]:
        """Get thread pool status for monitoring"""
        try:
            return {
                'az_thread_pool_active': True,
                'max_workers': self.az_thread_pool._max_workers,
                'active_threads': len([t for t in self.az_thread_pool._threads if t.is_alive()]),
                'pending_operations': self.operation_queue.qsize() if hasattr(self, 'operation_queue') else 0,
                'available_permits': self.operation_semaphore._value,
                'rate_limited_operations': len(self.last_az_call),
                'cached_subscriptions': len(self.subscriptions_cache)
            }
        except Exception as e:
            logger.error(f"❌ Error getting thread status: {e}")
            return {'error': str(e)}

def start_subscription_manager_maintenance():
    """Start background maintenance for subscription manager"""
    import threading
    import time
    
    def maintenance_worker():
        while True:
            try:
                time.sleep(600)  # Run every 10 minutes
                
                # Cleanup caches
                azure_subscription_manager.cleanup_caches()
                
                # Log thread status
                status = azure_subscription_manager.get_thread_status()
                if status.get('active_threads', 0) > 2:
                    logger.info(f"🔧 Subscription manager: {status['active_threads']} active threads")
                
            except Exception as e:
                logger.error(f"❌ Subscription manager maintenance error: {e}")
                time.sleep(900)  # Wait 15 minutes on error
    
    maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True, name="SubManagerMaintenance")
    maintenance_thread.start()
    logger.info("✅ Subscription manager maintenance started")

def initialize_subscription_manager_optimization():
    """Initialize subscription manager optimization"""
    try:
        start_subscription_manager_maintenance()
        logger.info("✅ Subscription manager optimization initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Subscription manager optimization failed: {e}")
        return False

# Global subscription manager instance
azure_subscription_manager = AzureSubscriptionManager()