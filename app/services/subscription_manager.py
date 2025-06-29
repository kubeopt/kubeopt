"""
Azure Subscription Manager for Multi-Subscription AKS Cost Optimization
"""

import json
import subprocess
import logging
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import concurrent.futures
from dataclasses import dataclass

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
    """Manages multiple Azure subscriptions for parallel AKS analysis"""
    
    def __init__(self):
        self.subscriptions_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_expiry = timedelta(hours=1)
        self.last_cache_update = None
        
    def get_available_subscriptions(self, force_refresh: bool = False) -> List[SubscriptionInfo]:
        """Get all available Azure subscriptions"""
        with self.cache_lock:
            # Check cache validity
            if (not force_refresh and self.subscriptions_cache and 
                self.last_cache_update and 
                datetime.now() - self.last_cache_update < self.cache_expiry):
                logger.info(f"📋 Using cached subscriptions ({len(self.subscriptions_cache)} found)")
                return list(self.subscriptions_cache.values())
        
        logger.info("🔍 Fetching available Azure subscriptions...")
        
        try:
            # Get subscriptions using Azure CLI
            result = subprocess.run([
                'az', 'account', 'list', 
                '--query', '[].{id:id, name:name, tenantId:tenantId, state:state, isDefault:isDefault}',
                '--output', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to fetch subscriptions: {result.stderr}")
                return []
            
            subscriptions_data = json.loads(result.stdout)
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
        """Get specific subscription information"""
        with self.cache_lock:
            if subscription_id in self.subscriptions_cache:
                return self.subscriptions_cache[subscription_id]
        
        # Try to refresh cache and search again
        subscriptions = self.get_available_subscriptions(force_refresh=True)
        for sub in subscriptions:
            if sub.subscription_id == subscription_id:
                return sub
        
        return None
    
    def set_active_subscription(self, subscription_id: str) -> bool:
        """Set the active Azure subscription for current thread/session"""
        try:
            logger.info(f"🔄 Setting active subscription: {subscription_id}")
            
            result = subprocess.run([
                'az', 'account', 'set', 
                '--subscription', subscription_id
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully set active subscription: {subscription_id}")
                return True
            else:
                logger.error(f"❌ Failed to set subscription: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout while setting subscription")
            return False
        except Exception as e:
            logger.error(f"❌ Error setting subscription: {e}")
            return False
    
    def execute_with_subscription_context(self, subscription_id: str, func, *args, **kwargs):
        """Execute function with specific subscription context"""
        original_subscription = self.get_current_subscription()
        
        try:
            # Set target subscription
            if not self.set_active_subscription(subscription_id):
                raise Exception(f"Failed to set subscription {subscription_id}")
            
            # Execute function
            result = func(*args, **kwargs)
            return result
            
        finally:
            # Restore original subscription if it was different
            if original_subscription and original_subscription != subscription_id:
                self.set_active_subscription(original_subscription)
    
    def get_current_subscription(self) -> Optional[str]:
        """Get currently active subscription ID"""
        try:
            result = subprocess.run([
                'az', 'account', 'show', 
                '--query', 'id',
                '--output', 'tsv'
            ], capture_output=True, text=True, timeout=10)
            
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
        
        # Use thread pool to search in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_subscription = {
                executor.submit(self._check_cluster_in_subscription, sub.subscription_id, resource_group, cluster_name): sub
                for sub in subscriptions
            }
            
            for future in concurrent.futures.as_completed(future_to_subscription, timeout=60):
                subscription = future_to_subscription[future]
                try:
                    cluster_found = future.result()
                    if cluster_found:
                        logger.info(f"✅ Found cluster {cluster_name} in subscription: {subscription.subscription_name}")
                        return subscription.subscription_id
                except Exception as e:
                    logger.warning(f"⚠️ Error checking subscription {subscription.subscription_name}: {e}")
        
        logger.warning(f"❌ Cluster {cluster_name} not found in any subscription")
        return None
    
    def _check_cluster_in_subscription(self, subscription_id: str, resource_group: str, cluster_name: str) -> bool:
        """Check if cluster exists in specific subscription"""
        try:
            result = subprocess.run([
                'az', 'aks', 'show',
                '--subscription', subscription_id,
                '--resource-group', resource_group,
                '--name', cluster_name,
                '--query', 'name',
                '--output', 'tsv'
            ], capture_output=True, text=True, timeout=20)
            
            return result.returncode == 0 and result.stdout.strip() == cluster_name
            
        except Exception:
            return False
    
    def validate_cluster_access(self, subscription_id: str, resource_group: str, cluster_name: str) -> Dict[str, any]:
        """Validate that we can access the specified cluster"""
        try:
            logger.info(f"🔍 Validating access to cluster {cluster_name} in subscription {subscription_id}")
            
            result = subprocess.run([
                'az', 'aks', 'show',
                '--subscription', subscription_id,
                '--resource-group', resource_group,
                '--name', cluster_name,
                '--query', '{name:name, location:location, powerState:powerState, provisioningState:provisioningState}',
                '--output', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                cluster_info = json.loads(result.stdout)
                logger.info(f"✅ Cluster validation successful: {cluster_info}")
                return {
                    'valid': True,
                    'cluster_info': cluster_info,
                    'subscription_id': subscription_id
                }
            else:
                error_msg = result.stderr.strip()
                logger.error(f"❌ Cluster validation failed: {error_msg}")
                return {
                    'valid': False,
                    'error': error_msg,
                    'subscription_id': subscription_id
                }
                
        except json.JSONDecodeError as e:
            return {'valid': False, 'error': f'Invalid response format: {e}'}
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {e}'}

# Global subscription manager instance
azure_subscription_manager = AzureSubscriptionManager()