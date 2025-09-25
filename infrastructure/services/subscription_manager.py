#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Azure Subscription Manager for Multi-Subscription AKS Cost Optimization
"""

import json
import subprocess  
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
        
        # Controlled thread pool for Azure CLI operations
        self.az_thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="AZ-CLI")
        self.operation_semaphore = threading.Semaphore(5)  # Max 5 concurrent operations
        self.operation_queue = queue.Queue(maxsize=20)
        
        # Rate limiting for Azure CLI calls
        self.last_az_call = {}  # Track last call time per operation type
        self.min_interval = 2.0  # Minimum 2 seconds between similar calls
        
    def _rate_limited_az_call(self, operation_type: str, az_command: list, timeout: int = 30):
        """Rate-limited Azure CLI call with thread management"""
        
        # Rate limiting
        current_time = time.time()
        last_call = self.last_az_call.get(operation_type, 0)
        
        if current_time - last_call < self.min_interval:
            sleep_time = self.min_interval - (current_time - last_call)
            logger.debug(f"🔄 Rate limiting {operation_type}, sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        # Semaphore control
        if not self.operation_semaphore.acquire(timeout=10):
            raise Exception(f"Too many concurrent Azure operations for {operation_type}")
        
        try:
            self.last_az_call[operation_type] = time.time()
            
            logger.debug(f"🔄 Azure CLI: {' '.join(az_command[:3])}... (timeout: {timeout}s)")
            
            result = subprocess.run(
                az_command, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            return result
            
        finally:
            self.operation_semaphore.release()
    
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
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            from azure.mgmt.resource import SubscriptionClient
            
            if not azure_sdk_manager.is_authenticated():
                logger.error("❌ Azure SDK not authenticated")
                return []
            
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
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout while fetching subscriptions")
            return []
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
        """Set the active Azure subscription with rate limiting"""
        try:
            logger.info(f"🔄 Setting active subscription: {subscription_id}")
            
            # Use controlled Azure CLI call
            result = self._rate_limited_az_call(
                'set_subscription',
                ['az', 'account', 'set', '--subscription', subscription_id],
                timeout=15
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully set active subscription: {subscription_id}")
                return True
            else:
                logger.error(f"❌ Failed to set subscription: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting subscription: {e}")
            return False
    
    def execute_with_subscription_context(self, subscription_id: str, func, *args, **kwargs):
        """Execute function with specific subscription context"""
        
        # Limit concurrent context switches
        if not self.operation_semaphore.acquire(timeout=30):
            raise Exception("Too many concurrent subscription operations")
        
        original_subscription = None
        try:
            # Get current subscription (cached call)
            original_subscription = self.get_current_subscription()
            
            # Set target subscription if different
            if original_subscription != subscription_id:
                if not self.set_active_subscription(subscription_id):
                    raise Exception(f"Failed to set subscription {subscription_id}")
            
            # Execute function
            result = func(*args, **kwargs)
            return result
            
        finally:
            try:
                # Restore original subscription if it was different
                if original_subscription and original_subscription != subscription_id:
                    self.set_active_subscription(original_subscription)
            finally:
                self.operation_semaphore.release()
    
    @lru_cache(maxsize=10, typed=False)
    def get_current_subscription(self) -> Optional[str]:
        """Get currently active subscription ID with caching"""
        try:
            result = self._rate_limited_az_call(
                'get_current',
                ['az', 'account', 'show', '--query', 'id', '--output', 'tsv'],
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"Failed to get current subscription: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current subscription: {e}")
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
                if cluster_found:
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
        """Check if cluster exists in specific subscription"""
        try:
            result = self._rate_limited_az_call(
                'check_cluster',
                [
                    'az', 'aks', 'show',
                    '--subscription', subscription_id,
                    '--resource-group', resource_group,
                    '--name', cluster_name,
                    '--query', 'name',
                    '--output', 'tsv'
                ],
                timeout=20
            )
            
            return result.returncode == 0 and result.stdout.strip() == cluster_name
            
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
        """Validate cluster in specific resource group"""
        try:
            result = self._rate_limited_az_call(
                'validate_cluster',
                [
                    'az', 'aks', 'show',
                    '--subscription', subscription_id,
                    '--resource-group', resource_group,
                    '--name', cluster_name,
                    '--query', '{name:name, location:location, powerState:powerState, provisioningState:provisioningState, resourceGroup:resourceGroup}',
                    '--output', 'json'
                ],
                timeout=30
            )
            
            if result.returncode == 0:
                cluster_info = json.loads(result.stdout)
                logger.info(f"✅ Cluster validation successful: {cluster_info}")
                return {
                    'valid': True,
                    'cluster_info': cluster_info,
                    'subscription_id': subscription_id,
                    'discovered_resource_group': resource_group
                }
            else:
                error_msg = result.stderr.strip()
                return {
                    'valid': False,
                    'error': error_msg,
                    'subscription_id': subscription_id
                }
                
        except json.JSONDecodeError as e:
            return {'valid': False, 'error': f'Invalid response format: {e}', 'subscription_id': subscription_id}
        except Exception as e:
            return {'valid': False, 'error': f'Cluster validation error: {e}', 'subscription_id': subscription_id}
    
    def _auto_discover_cluster(self, subscription_id: str, cluster_name: str) -> Dict[str, any]:
        """Auto-discover cluster by searching all resource groups in subscription"""
        try:
            # List all AKS clusters in the subscription
            result = self._rate_limited_az_call(
                'list_aks_clusters',
                [
                    'az', 'aks', 'list',
                    '--subscription', subscription_id,
                    '--query', f"[?name=='{cluster_name}'].[name,location,powerState,provisioningState,resourceGroup]",
                    '--output', 'json'
                ],
                timeout=60
            )
            
            if result.returncode == 0:
                clusters = json.loads(result.stdout)
                if clusters and len(clusters) > 0:
                    cluster_data = clusters[0]
                    cluster_info = {
                        'name': cluster_data[0],
                        'location': cluster_data[1],
                        'powerState': cluster_data[2],
                        'provisioningState': cluster_data[3],
                        'resourceGroup': cluster_data[4]
                    }
                    
                    logger.info(f"✅ Cluster auto-discovery successful: {cluster_info}")
                    return {
                        'valid': True,
                        'cluster_info': cluster_info,
                        'subscription_id': subscription_id,
                        'discovered_resource_group': cluster_data[4],
                        'auto_discovered': True
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'Cluster "{cluster_name}" not found in subscription {subscription_id}',
                        'subscription_id': subscription_id,
                        'suggestion': 'Verify cluster name and subscription access'
                    }
            else:
                error_msg = result.stderr.strip()
                return {
                    'valid': False,
                    'error': f'Failed to list clusters: {error_msg}',
                    'subscription_id': subscription_id
                }
                
        except json.JSONDecodeError as e:
            return {'valid': False, 'error': f'Invalid response format: {e}', 'subscription_id': subscription_id}
        except Exception as e:
            return {'valid': False, 'error': f'Auto-discovery error: {e}', 'subscription_id': subscription_id}
    
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
                
            if old_operations:
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