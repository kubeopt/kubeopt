# ============================================================================
# 1. Enhanced Subscription Manager with Auto-Detection
# ============================================================================

# UPDATE your app/services/subscription_manager.py with this enhanced version:

"""
Enhanced Azure Subscription Manager with Auto-Detection
"""

from datetime import datetime, timedelta
import os
import sqlite3
import subprocess
import json
import logging
import time
from typing import List, Dict, Optional, Tuple

from app.data.processing.cost_processor import extract_cost_components, process_aks_cost_data
from utils import validate_cost_data

logger = logging.getLogger(__name__)

class AzureSubscriptionManager:
    """Enhanced subscription manager with auto-detection capabilities"""
    
    def __init__(self):
        self.current_subscription = None
        self._subscription_cache = {}  # Cache subscription info
        logger.info("🔧 Enhanced AzureSubscriptionManager initialized")
    
    def get_current_subscription(self):
        """Get currently active subscription"""
        try:
            logger.info("🔍 Getting current Azure subscription...")
            
            cmd = "az account show --output json"
            result = subprocess.run(
                cmd, shell=True, check=True, capture_output=True, text=True, timeout=15
            )
            
            if not result.stdout.strip():
                return None
            
            current_sub = json.loads(result.stdout)
            
            formatted_sub = {
                'subscription_id': current_sub['id'],
                'subscription_name': current_sub.get('name', 'Unknown'),
                'is_default': current_sub.get('isDefault', False),
                'state': current_sub.get('state', 'Unknown')
            }
            
            self.current_subscription = formatted_sub
            return formatted_sub
            
        except Exception as e:
            logger.error(f"❌ Error getting current subscription: {e}")
            return None
    
    def find_cluster_subscription(self, resource_group: str, cluster_name: str) -> Optional[str]:
        """
        Find which subscription contains the specified cluster
        Returns subscription_id if found, None otherwise
        """
        logger.info(f"🔍 Searching for cluster {cluster_name} in resource group {resource_group}...")
        
        try:
            # Get all available subscriptions
            subscriptions = self.get_available_subscriptions()
            
            if not subscriptions:
                logger.warning("⚠️ No subscriptions available to search")
                return None
            
            # Current subscription first (optimization)
            current_sub = self.get_current_subscription()
            if current_sub:
                subscriptions_to_check = [current_sub] + [s for s in subscriptions if s['subscription_id'] != current_sub['subscription_id']]
            else:
                subscriptions_to_check = subscriptions
            
            for sub in subscriptions_to_check:
                subscription_id = sub['subscription_id']
                subscription_name = sub['subscription_name']
                
                logger.info(f"🔍 Checking subscription: {subscription_name}")
                
                # Switch to this subscription temporarily
                if not self.switch_subscription(subscription_id):
                    logger.warning(f"⚠️ Failed to switch to subscription: {subscription_name}")
                    continue
                
                # Check if the cluster exists in this subscription
                if self._cluster_exists_in_current_subscription(resource_group, cluster_name):
                    logger.info(f"✅ Found cluster {cluster_name} in subscription: {subscription_name}")
                    return subscription_id
                
                logger.info(f"❌ Cluster {cluster_name} not found in subscription: {subscription_name}")
            
            logger.warning(f"⚠️ Cluster {cluster_name} not found in any available subscription")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding cluster subscription: {e}")
            return None
    
    def _cluster_exists_in_current_subscription(self, resource_group: str, cluster_name: str) -> bool:
        """Check if cluster exists in the currently active subscription"""
        try:
            # First check if resource group exists
            rg_cmd = f"az group show --name {resource_group} --output json"
            rg_result = subprocess.run(
                rg_cmd, shell=True, check=True, capture_output=True, text=True, timeout=10
            )
            
            if rg_result.returncode != 0:
                return False
            
            # Then check if AKS cluster exists in the resource group
            cluster_cmd = f"az aks show --resource-group {resource_group} --name {cluster_name} --output json"
            cluster_result = subprocess.run(
                cluster_cmd, shell=True, check=True, capture_output=True, text=True, timeout=15
            )
            
            return cluster_result.returncode == 0
            
        except subprocess.CalledProcessError:
            # Expected when resource group or cluster doesn't exist
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error checking cluster existence: {e}")
            return False
    
    def ensure_correct_subscription_for_cluster(self, resource_group: str, cluster_name: str) -> Tuple[bool, str]:
        """
        Ensure we're in the correct subscription for the specified cluster
        Returns (success: bool, message: str)
        """
        logger.info(f"🔧 Ensuring correct subscription for cluster: {cluster_name}")
        
        try:
            # First, check if cluster exists in current subscription
            current_sub = self.get_current_subscription()
            if current_sub and self._cluster_exists_in_current_subscription(resource_group, cluster_name):
                logger.info(f"✅ Cluster {cluster_name} found in current subscription: {current_sub['subscription_name']}")
                return True, f"Using current subscription: {current_sub['subscription_name']}"
            
            # If not in current subscription, find the correct one
            logger.info(f"🔍 Cluster not in current subscription, searching...")
            correct_subscription_id = self.find_cluster_subscription(resource_group, cluster_name)
            
            if not correct_subscription_id:
                error_msg = f"Cluster {cluster_name} not found in any available subscription"
                logger.error(f"❌ {error_msg}")
                return False, error_msg
            
            # Switch to the correct subscription
            if self.switch_subscription(correct_subscription_id):
                current_sub = self.get_current_subscription()
                success_msg = f"Switched to correct subscription: {current_sub['subscription_name']}"
                logger.info(f"✅ {success_msg}")
                return True, success_msg
            else:
                error_msg = f"Failed to switch to subscription: {correct_subscription_id}"
                logger.error(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error ensuring correct subscription: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_available_subscriptions(self):
        """Get all available Azure subscriptions"""
        try:
            cmd = "az account list --output json"
            result = subprocess.run(
                cmd, shell=True, check=True, capture_output=True, text=True, timeout=30
            )
            
            if not result.stdout.strip():
                return []
            
            subscriptions = json.loads(result.stdout)
            
            formatted_subs = []
            for sub in subscriptions:
                if not sub.get('id'):
                    continue
                    
                formatted_subs.append({
                    'subscription_id': sub['id'],
                    'subscription_name': sub.get('name', 'Unknown'),
                    'is_default': sub.get('isDefault', False),
                    'state': sub.get('state', 'Unknown')
                })
            
            return formatted_subs
            
        except Exception as e:
            logger.error(f"❌ Error getting subscriptions: {e}")
            return []
    
    def switch_subscription(self, subscription_id: str) -> bool:
        """Switch to a specific subscription"""
        try:
            logger.info(f"🔄 Switching to subscription: {subscription_id}")
            
            cmd = f"az account set --subscription {subscription_id}"
            result = subprocess.run(
                cmd, shell=True, check=True, capture_output=True, text=True, timeout=15
            )
            
            # Verify the switch
            current_sub = self.get_current_subscription()
            if current_sub and current_sub['subscription_id'] == subscription_id:
                logger.info(f"✅ Successfully switched to: {current_sub['subscription_name']}")
                return True
            else:
                logger.error(f"❌ Failed to verify subscription switch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error switching subscription: {e}")
            return False

