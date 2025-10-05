#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Azure SDK Manager - Centralized Azure authentication and client management
=========================================================================

Provides centralized Azure SDK authentication following Azure best practices:
- DefaultAzureCredential chain
- Proper error handling
- Client caching and reuse
- Support for multiple authentication methods
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading

try:
    from azure.identity import (
        DefaultAzureCredential, 
        ChainedTokenCredential, 
        ManagedIdentityCredential, 
        AzureCliCredential, 
        EnvironmentCredential,
        UsernamePasswordCredential,
        InteractiveBrowserCredential
    )
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.containerservice import ContainerServiceClient
    from azure.monitor.query import LogsQueryClient
    from azure.core.credentials import TokenCredential
    from azure.core.exceptions import ClientAuthenticationError
    AZURE_SDK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Azure SDK not available: {e}")
    AZURE_SDK_AVAILABLE = False
    # Define dummy classes for type hints when SDK not available
    class CostManagementClient: pass
    class MonitorManagementClient: pass
    class ResourceManagementClient: pass
    class ContainerServiceClient: pass
    class LogsQueryClient: pass

logger = logging.getLogger(__name__)

class AzureSDKManager:
    """
    Centralized Azure SDK authentication and client management with multi-subscription support
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AzureSDKManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.credential: Optional[TokenCredential] = None
        self.clients: Dict[str, Dict[str, Any]] = {}  # {subscription_id: {client_type: client}}
        self.subscription_id: Optional[str] = None
        self._auth_time: Optional[datetime] = None
        self._lock = threading.Lock()
        self._subscription_cache: Dict[str, str] = {}  # Cache for subscription access
        
        if AZURE_SDK_AVAILABLE:
            self._initialize_credentials()
        else:
            logger.warning("⚠️ Azure SDK not available - some features will use fallbacks")
    
    def _initialize_credentials(self) -> bool:
        """Initialize Azure credentials with testing support"""
        try:
            logger.info("🔐 Initializing Azure credentials with testing support...")
            
            # Build credential chain based on environment
            credential_chain = []
            import os
            
            # Get environment variables for service principal
            tenant_id = os.getenv('AZURE_TENANT_ID', '')
            client_id = os.getenv('AZURE_CLIENT_ID', '')
            client_secret = os.getenv('AZURE_CLIENT_SECRET', '')
            username = os.getenv('AZURE_USERNAME')
            password = os.getenv('AZURE_PASSWORD')
            
            # 1. PRIORITY: Environment credentials (for service principals)
            if tenant_id and not tenant_id.startswith('your-') and 'placeholder' not in tenant_id.lower():
                try:
                    env_credential = EnvironmentCredential()
                    credential_chain.append(env_credential)
                    logger.info("✅ Added environment credential to chain (PRIORITY)")
                    
                    # Test if service principal env vars are set
                    if client_id and client_secret:
                        logger.info(f"🔑 Service principal detected: {client_id[:8]}...")
                    
                except Exception as e:
                    logger.debug(f"Environment credential not available: {e}")
            else:
                logger.debug("Skipping environment credential due to placeholder/missing tenant ID")
            
            # 2. Username/password testing credentials (secondary)
            if username and password and tenant_id:
                try:
                    user_pass_credential = UsernamePasswordCredential(
                        username=username,
                        password=password,
                        tenant_id=tenant_id
                    )
                    credential_chain.append(user_pass_credential)
                    logger.info("✅ Added username/password credential for testing")
                except Exception as e:
                    logger.warning(f"⚠️ Username/password credential failed: {e}")
            
            # 3. Interactive browser credential ONLY if no other credentials worked
            if not credential_chain and tenant_id and not tenant_id.startswith('your-') and 'placeholder' not in tenant_id.lower():
                try:
                    browser_credential = InteractiveBrowserCredential(tenant_id=tenant_id)
                    credential_chain.append(browser_credential)
                    logger.info("✅ Added interactive browser credential as fallback")
                except Exception as e:
                    logger.debug(f"Interactive browser credential not available: {e}")
            else:
                if credential_chain:
                    logger.debug("Skipping interactive browser credential - other credentials available")
                else:
                    logger.debug("Skipping interactive browser credential due to placeholder/missing tenant ID")
            
            # 2. Managed identity (for Azure-hosted applications)
            try:
                mi_credential = ManagedIdentityCredential()
                credential_chain.append(mi_credential)
                logger.info("✅ Added managed identity credential to chain")
            except Exception as e:
                logger.debug(f"Managed identity credential not available: {e}")
            
            # 3. Azure CLI credential (for development) - PRIORITY
            try:
                cli_credential = AzureCliCredential()
                # Test if CLI is actually logged in
                cli_credential.get_token("https://management.azure.com/.default")
                credential_chain.append(cli_credential)
                logger.info("✅ Added Azure CLI credential to chain (verified working)")
            except Exception as e:
                logger.debug(f"Azure CLI credential not available or not logged in: {e}")
                logger.info("💡 Hint: Run 'az login' to authenticate with Azure CLI")
            
            if not credential_chain:
                logger.error("❌ No Azure credentials available")
                return False
            
            # Create chained credential
            self.credential = ChainedTokenCredential(*credential_chain)
            
            # Test credential by getting a token
            try:
                token = self.credential.get_token("https://management.azure.com/.default")
                self._auth_time = datetime.now()
                logger.info("✅ Azure credentials successfully authenticated")
                
                # Try to get subscription ID
                self._get_subscription_id()
                
                return True
                
            except ClientAuthenticationError as e:
                logger.error(f"❌ Azure authentication failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure credentials: {e}")
            return False
    
    def _get_subscription_id(self):
        """Get current Azure subscription ID with caching"""
        import os
        
        # Try environment variable first
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if self.subscription_id:
            logger.info(f"✅ Using subscription ID from environment: {self.subscription_id[:8]}...")
            return
        
        # Check if we already cached the subscription ID
        if hasattr(self, '_cached_subscription_id') and self._cached_subscription_id:
            self.subscription_id = self._cached_subscription_id
            logger.debug(f"✅ Using cached subscription ID: {self.subscription_id[:8]}...")
            return
        
        # Try Azure SDK to get default subscription - no CLI fallback
        try:
            from azure.mgmt.subscription import SubscriptionClient
            from azure.identity import DefaultAzureCredential
            
            credential = DefaultAzureCredential()
            subscription_client = SubscriptionClient(credential)
            
            # Get first enabled subscription as default
            subscriptions = list(subscription_client.subscriptions.list())
            if subscriptions:
                default_subscription = subscriptions[0]
                self.subscription_id = default_subscription.subscription_id
                self._cached_subscription_id = self.subscription_id  # Cache it
                logger.info(f"✅ SDK: Using default subscription ID: {self.subscription_id[:8]}...")
                return
        except Exception as e:
            logger.debug(f"Could not get subscription from Azure SDK: {e}")
        
        # No subscription ID needed at startup - will be set dynamically during analysis
        logger.info("ℹ️ No subscription ID set at startup - will be set dynamically during analysis from cluster context")
        self.subscription_id = None
    
    def is_authenticated(self) -> bool:
        """Check if Azure credentials are available and valid - optimized"""
        if not AZURE_SDK_AVAILABLE or not self.credential:
            return False
        
        # Check if authentication is recent (extended to 4 hours for performance)
        if self._auth_time and datetime.now() - self._auth_time < timedelta(hours=4):
            return True
        
        # Test authentication only if needed
        try:
            token = self.credential.get_token("https://management.azure.com/.default")
            self._auth_time = datetime.now()
            return True
        except Exception as e:
            logger.debug(f"Authentication failed: {e}")
            return False
    
    def get_client(self, client_type: str, subscription_id: Optional[str] = None) -> Optional[Any]:
        """Get Azure client by type and subscription, with caching"""
        if not self.is_authenticated():
            logger.warning(f"⚠️ Cannot create {client_type} client - not authenticated")
            return None
        
        # Use default subscription if none specified
        target_subscription = subscription_id or self.subscription_id
        if not target_subscription:
            logger.error("❌ No subscription ID available")
            return None
        
        with self._lock:
            # Initialize subscription cache if needed
            if target_subscription not in self.clients:
                self.clients[target_subscription] = {}
            
            # Return cached client if available
            if client_type in self.clients[target_subscription]:
                return self.clients[target_subscription][client_type]
            
            # Create new client with timeout configuration
            try:
                # Configure connection timeouts for stability
                from azure.core.pipeline.policies import HttpLoggingPolicy
                from azure.core.pipeline.transport import RequestsTransport
                
                # Create transport with timeout settings
                transport = RequestsTransport(
                    connection_timeout=30,  # 30 second connection timeout
                    read_timeout=60        # 60 second read timeout
                )
                
                if client_type == 'cost':
                    client = CostManagementClient(self.credential, transport=transport)
                elif client_type == 'monitor':
                    client = MonitorManagementClient(self.credential, target_subscription, transport=transport)
                elif client_type == 'resource':
                    client = ResourceManagementClient(self.credential, target_subscription, transport=transport)
                elif client_type == 'aks':
                    client = ContainerServiceClient(self.credential, target_subscription, transport=transport)
                elif client_type == 'logs':
                    client = LogsQueryClient(self.credential, transport=transport)
                else:
                    logger.error(f"❌ Unknown client type: {client_type}")
                    return None
                
                # Cache the client
                self.clients[target_subscription][client_type] = client
                logger.info(f"✅ Created {client_type} client for subscription {target_subscription[:8]}...")
                return client
                
            except Exception as e:
                logger.error(f"❌ Failed to create {client_type} client for subscription {target_subscription[:8]}...: {e}")
                return None
    
    def get_cost_client(self, subscription_id: Optional[str] = None) -> Optional[CostManagementClient]:
        """Get Azure Cost Management client for specified subscription"""
        return self.get_client('cost', subscription_id)
    
    def get_monitor_client(self, subscription_id: Optional[str] = None) -> Optional[MonitorManagementClient]:
        """Get Azure Monitor client for specified subscription"""
        return self.get_client('monitor', subscription_id)
    
    def get_resource_client(self, subscription_id: Optional[str] = None) -> Optional[ResourceManagementClient]:
        """Get Azure Resource Management client for specified subscription"""
        return self.get_client('resource', subscription_id)
    
    def get_aks_client(self, subscription_id: Optional[str] = None) -> Optional[ContainerServiceClient]:
        """Get Azure Container Service (AKS) client for specified subscription"""
        return self.get_client('aks', subscription_id)
    
    def get_logs_client(self, subscription_id: Optional[str] = None) -> Optional[LogsQueryClient]:
        """Get Azure Monitor Logs client for specified subscription"""
        return self.get_client('logs', subscription_id)
    
    def get_log_analytics_client(self, subscription_id: Optional[str] = None):
        """Get Log Analytics client - alias for Monitor client"""
        return self.get_monitor_client(subscription_id)
    
    def get_application_insights_client(self, subscription_id: Optional[str] = None):
        """Get Application Insights client - alias for Monitor client"""
        return self.get_monitor_client(subscription_id)
    
    def get_cost_management_client(self, subscription_id: Optional[str] = None):
        """Get Cost Management client - alias for cost client"""
        return self.get_cost_client(subscription_id)
    
    def get_consumption_client(self, subscription_id: Optional[str] = None):
        """Get Consumption client - alias for cost client"""
        return self.get_cost_client(subscription_id)
    
    def get_subscription_id(self) -> Optional[str]:
        """Get current Azure subscription ID"""
        return self.subscription_id
    
    def set_subscription_context(self, subscription_id: str):
        """Set subscription ID dynamically for analysis context"""
        self.subscription_id = subscription_id
        logger.debug(f"🔄 Set subscription context to: {subscription_id[:8]}...")
    
    def clear_clients(self, subscription_id: Optional[str] = None):
        """Clear cached clients (useful for subscription switches)"""
        with self._lock:
            if subscription_id:
                if subscription_id in self.clients:
                    del self.clients[subscription_id]
                    logger.info(f"🧹 Cleared Azure client cache for subscription {subscription_id[:8]}...")
            else:
                self.clients.clear()
                logger.info("🧹 Cleared all Azure client caches")
    
    def refresh_credentials(self) -> bool:
        """
        Refresh Azure credentials - useful after settings are updated
        
        Returns:
            bool: True if credentials were successfully refreshed
        """
        try:
            logger.info("🔄 Refreshing Azure credentials...")
            
            # Clear current state
            self.credential = None
            self._auth_time = None
            self.clear_clients()
            
            # Reinitialize credentials with new settings
            if AZURE_SDK_AVAILABLE:
                success = self._initialize_credentials()
                if success:
                    logger.info("✅ Azure credentials refreshed successfully")
                else:
                    logger.warning("⚠️ Failed to refresh Azure credentials")
                return success
            else:
                logger.warning("⚠️ Azure SDK not available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error refreshing Azure credentials: {e}")
            return False
    
    def validate_subscription_access(self, subscription_id: str) -> bool:
        """Validate that the service principal has access to the specified subscription"""
        try:
            # Try to get a resource client for the subscription
            resource_client = self.get_resource_client(subscription_id)
            if not resource_client:
                return False
            
            # Try to list resource groups (minimal permission test)
            list(resource_client.resource_groups.list())
            logger.info(f"✅ Validated access to subscription {subscription_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ No access to subscription {subscription_id[:8]}...: {e}")
            return False
    
    def execute_aks_command(self, subscription_id: str, resource_group: str, 
                                      cluster_name: str, kubectl_command: str) -> Optional[str]:
        """
        Execute kubectl command using Azure SDK Run Command API
        
        This provides the SAME server-side execution as 'az aks command invoke':
        - Works with private AKS clusters
        - No VNet connectivity required  
        - Secure execution through Azure's network
        - Container-friendly (pure SDK implementation)
        """
        try:
            import os
            production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
            
            logger.debug(f"🔧 Executing kubectl command via SDK server-side: {kubectl_command}")
            
            # Get AKS client for the subscription
            aks_client = self.get_aks_client(subscription_id)
            if not aks_client:
                logger.error(f"❌ Cannot get AKS client for subscription {subscription_id[:8]}...")
                return None
            
            # Create run command request with AAD cluster token support
            from azure.mgmt.containerservice.models import RunCommandRequest
            
            # Get cluster token for AAD-enabled clusters
            cluster_token = self._get_cluster_token_for_aad(subscription_id, resource_group, cluster_name)
            
            if cluster_token:
                run_command_request = RunCommandRequest(
                    command=kubectl_command,
                    cluster_token=cluster_token
                )
                logger.debug(f"🔐 Using AAD cluster token for {cluster_name}")
            else:
                run_command_request = RunCommandRequest(command=kubectl_command)
                logger.debug(f"🔓 No AAD cluster token needed for {cluster_name}")
            
            logger.debug(f"🚀 Server-side execution starting for cluster {cluster_name}")
            
            # Execute command server-side (same as CLI command invoke)
            result_operation = aks_client.managed_clusters.begin_run_command(
                resource_group_name=resource_group,
                resource_name=cluster_name,
                request_payload=run_command_request
            )
            
            # Wait for server-side execution to complete
            command_result = result_operation.result(timeout=180)  # 3 minute timeout for server-side execution
            
            # Process results
            if command_result.exit_code == 0:
                output = command_result.logs or ""
                logger.debug(f"✅ Server-side kubectl execution successful: {kubectl_command}")
                return output.strip()
            else:
                # Handle expected failures gracefully
                if "kubectl top" in kubectl_command and "Metrics not available" in command_result.logs:
                    logger.debug(f"⚠️ Server-side kubectl top command failed (metrics not available): {kubectl_command}")
                    if command_result.logs:
                        logger.debug(f"Metrics error details: {command_result.logs}")
                elif "kubectl get" in kubectl_command and ("NotFound" in command_result.logs or "not found" in command_result.logs):
                    logger.debug(f"📋 Server-side kubectl get failed (resource not found): {kubectl_command}")
                else:
                    # Unexpected failures should still be logged as errors
                    logger.error(f"❌ Server-side kubectl command failed (exit {command_result.exit_code}): {kubectl_command}")
                    if command_result.logs:
                        logger.error(f"Error logs: {command_result.logs}")
                
                return None
                
        except Exception as e:
            # Handle exceptions gracefully based on command type
            if "kubectl top" in kubectl_command:
                logger.debug(f"⚠️ Server-side kubectl top execution failed: {e}")
            else:
                logger.error(f"❌ Server-side kubectl execution failed: {e}")
            
            return None
    
    
    def _get_cluster_token_for_aad(self, subscription_id: str, resource_group: str, cluster_name: str) -> Optional[str]:
        """Get cluster token for AAD-enabled AKS clusters"""
        try:
            # Get a token scoped to the AKS cluster
            # This is equivalent to what 'az aks get-credentials' does for AAD clusters
            cluster_resource_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}"
            
            # Try to get an AAD token for the cluster
            try:
                # Get token for AKS cluster access
                token = self.credential.get_token("6dae42f8-4368-4678-94ff-3960e28e3630/.default")  # AKS AAD Server App ID
                
                if token and token.token:
                    logger.debug(f"✅ Successfully obtained AAD cluster token for {cluster_name}")
                    return token.token
                else:
                    logger.debug(f"⚠️ No AAD token obtained for {cluster_name}")
                    return None
                    
            except Exception as token_error:
                logger.debug(f"⚠️ AAD token acquisition failed for {cluster_name}: {token_error}")
                
                # Try alternative token scope
                try:
                    token = self.credential.get_token("https://management.azure.com/.default")
                    if token and token.token:
                        logger.debug(f"✅ Using management token as fallback for {cluster_name}")
                        return token.token
                except Exception:
                    pass
                    
                return None
                
        except Exception as e:
            logger.debug(f"⚠️ Cluster token acquisition failed: {e}")
            return None

# Global instance
azure_sdk_manager = AzureSDKManager()

def get_azure_client(client_type: str):
    """Convenience function to get Azure client"""
    return azure_sdk_manager.get_client(client_type)

def is_azure_authenticated() -> bool:
    """Check if Azure authentication is available"""
    return azure_sdk_manager.is_authenticated()

def get_subscription_id() -> Optional[str]:
    """Get current Azure subscription ID"""
    return azure_sdk_manager.get_subscription_id()