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
        EnvironmentCredential
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

logger = logging.getLogger(__name__)

class AzureSDKManager:
    """
    Centralized Azure SDK authentication and client management
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
        self.clients: Dict[str, Any] = {}
        self.subscription_id: Optional[str] = None
        self._auth_time: Optional[datetime] = None
        self._lock = threading.Lock()
        
        if AZURE_SDK_AVAILABLE:
            self._initialize_credentials()
        else:
            logger.warning("⚠️ Azure SDK not available - some features will use fallbacks")
    
    def _initialize_credentials(self) -> bool:
        """Initialize Azure credentials following best practices"""
        try:
            logger.info("🔐 Initializing Azure credentials with standard chain...")
            
            # Build credential chain based on environment
            credential_chain = []
            
            # 1. Environment credentials (for CI/CD, service principals) - but skip if placeholder values
            try:
                import os
                tenant_id = os.getenv('AZURE_TENANT_ID', '')
                if tenant_id and not tenant_id.startswith('your-') and 'placeholder' not in tenant_id.lower():
                    env_credential = EnvironmentCredential()
                    credential_chain.append(env_credential)
                    logger.info("✅ Added environment credential to chain")
                else:
                    logger.debug("Skipping environment credential due to placeholder/missing tenant ID")
            except Exception as e:
                logger.debug(f"Environment credential not available: {e}")
            
            # 2. Managed identity (for Azure-hosted applications)
            try:
                mi_credential = ManagedIdentityCredential()
                credential_chain.append(mi_credential)
                logger.info("✅ Added managed identity credential to chain")
            except Exception as e:
                logger.debug(f"Managed identity credential not available: {e}")
            
            # 3. Azure CLI credential (for development)
            try:
                cli_credential = AzureCliCredential()
                credential_chain.append(cli_credential)
                logger.info("✅ Added Azure CLI credential to chain")
            except Exception as e:
                logger.debug(f"Azure CLI credential not available: {e}")
            
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
        import subprocess
        
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
        
        # Try Azure CLI as fallback - but cache the result
        try:
            result = subprocess.run(['az', 'account', 'show', '--query', 'id', '-o', 'tsv'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                self.subscription_id = result.stdout.strip()
                self._cached_subscription_id = self.subscription_id  # Cache it
                logger.info(f"✅ Using subscription ID from Azure CLI: {self.subscription_id[:8]}...")
                return
        except Exception as e:
            logger.debug(f"Could not get subscription from Azure CLI: {e}")
        
        logger.error("❌ No subscription ID available. Set AZURE_SUBSCRIPTION_ID or run 'az login'")
        raise RuntimeError("Azure subscription ID not available")
    
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
    
    def get_client(self, client_type: str) -> Optional[Any]:
        """Get Azure client by type, with caching"""
        if not self.is_authenticated():
            logger.warning(f"⚠️ Cannot create {client_type} client - not authenticated")
            return None
        
        with self._lock:
            # Return cached client if available
            if client_type in self.clients:
                return self.clients[client_type]
            
            # Create new client
            try:
                if client_type == 'cost':
                    client = CostManagementClient(self.credential)
                elif client_type == 'monitor':
                    client = MonitorManagementClient(self.credential, self.subscription_id)
                elif client_type == 'resource':
                    client = ResourceManagementClient(self.credential, self.subscription_id)
                elif client_type == 'aks':
                    client = ContainerServiceClient(self.credential, self.subscription_id)
                elif client_type == 'logs':
                    client = LogsQueryClient(self.credential)
                else:
                    logger.error(f"❌ Unknown client type: {client_type}")
                    return None
                
                # Cache the client
                self.clients[client_type] = client
                logger.info(f"✅ Created {client_type} client")
                return client
                
            except Exception as e:
                logger.error(f"❌ Failed to create {client_type} client: {e}")
                return None
    
    def get_cost_client(self) -> Optional[CostManagementClient]:
        """Get Azure Cost Management client"""
        return self.get_client('cost')
    
    def get_monitor_client(self) -> Optional[MonitorManagementClient]:
        """Get Azure Monitor client"""
        return self.get_client('monitor')
    
    def get_resource_client(self) -> Optional[ResourceManagementClient]:
        """Get Azure Resource Management client"""
        return self.get_client('resource')
    
    def get_aks_client(self) -> Optional[ContainerServiceClient]:
        """Get Azure Container Service (AKS) client"""
        return self.get_client('aks')
    
    def get_logs_client(self) -> Optional[LogsQueryClient]:
        """Get Azure Monitor Logs client"""
        return self.get_client('logs')
    
    def get_subscription_id(self) -> Optional[str]:
        """Get current Azure subscription ID"""
        return self.subscription_id
    
    def clear_clients(self):
        """Clear cached clients (useful for subscription switches)"""
        with self._lock:
            self.clients.clear()
            logger.info("🧹 Cleared Azure client cache")

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