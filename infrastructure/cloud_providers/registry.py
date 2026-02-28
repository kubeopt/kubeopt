"""
Provider Registry
=================

Singleton that auto-detects the cloud provider from environment variables
and returns the appropriate adapter instances.
"""

import os
import logging
import threading
from typing import Optional

from infrastructure.cloud_providers.types import CloudProvider
from infrastructure.cloud_providers.base import (
    CloudAuthenticator,
    KubernetesCommandExecutor,
    CloudMetricsCollector,
    CloudCostManager,
    CloudAccountManager,
    CloudInfrastructureInspector,
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Singleton registry that detects the active cloud provider
    and provides factory methods for provider-specific adapters.

    Detection order:
      1. CLOUD_PROVIDER env var (explicit)
      2. AWS_ACCESS_KEY_ID or AWS_DEFAULT_REGION → AWS
      3. GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CLOUD_PROJECT → GCP
      4. Default → Azure (backwards-compatible)
    """

    _instance: Optional['ProviderRegistry'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ProviderRegistry':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._provider: Optional[CloudProvider] = None
        self._authenticator: Optional[CloudAuthenticator] = None
        self._executor: Optional[KubernetesCommandExecutor] = None
        self._metrics: Optional[CloudMetricsCollector] = None
        self._costs: Optional[CloudCostManager] = None
        self._accounts: Optional[CloudAccountManager] = None
        self._inspector: Optional[CloudInfrastructureInspector] = None

    @property
    def provider(self) -> CloudProvider:
        if self._provider is None:
            self._provider = self._detect_provider()
        return self._provider

    def set_provider(self, provider: CloudProvider) -> None:
        """Explicitly set the cloud provider, clearing cached adapters."""
        self._provider = provider
        self._authenticator = None
        self._executor = None
        self._metrics = None
        self._costs = None
        self._accounts = None
        self._inspector = None
        logger.info(f"Cloud provider set to: {provider.value}")

    def _detect_provider(self) -> CloudProvider:
        """Auto-detect cloud provider from environment."""
        explicit = os.getenv('CLOUD_PROVIDER', '').strip().lower()
        if explicit:
            try:
                provider = CloudProvider.from_string(explicit)
                logger.info(f"Cloud provider from CLOUD_PROVIDER env: {provider.value}")
                return provider
            except ValueError:
                logger.warning(f"Invalid CLOUD_PROVIDER='{explicit}', falling back to detection")

        # AWS detection
        if os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('AWS_DEFAULT_REGION'):
            logger.info("Detected AWS from environment variables")
            return CloudProvider.AWS

        # GCP detection
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('GOOGLE_CLOUD_PROJECT'):
            logger.info("Detected GCP from environment variables")
            return CloudProvider.GCP

        # Default: Azure (backwards-compatible)
        logger.info("Defaulting to Azure cloud provider")
        return CloudProvider.AZURE

    def get_authenticator(self) -> CloudAuthenticator:
        """Get the authenticator for the active cloud provider."""
        if self._authenticator is None:
            self._authenticator = self._create_authenticator()
        return self._authenticator

    def get_executor(self) -> KubernetesCommandExecutor:
        """Get the Kubernetes command executor for the active cloud provider."""
        if self._executor is None:
            self._executor = self._create_executor()
        return self._executor

    def get_metrics_collector(self) -> CloudMetricsCollector:
        """Get the metrics collector for the active cloud provider."""
        if self._metrics is None:
            self._metrics = self._create_metrics_collector()
        return self._metrics

    def get_cost_manager(self) -> CloudCostManager:
        """Get the cost manager for the active cloud provider."""
        if self._costs is None:
            self._costs = self._create_cost_manager()
        return self._costs

    def get_account_manager(self) -> CloudAccountManager:
        """Get the account manager for the active cloud provider."""
        if self._accounts is None:
            self._accounts = self._create_account_manager()
        return self._accounts

    def get_infrastructure_inspector(self) -> CloudInfrastructureInspector:
        """Get the infrastructure inspector for the active cloud provider."""
        if self._inspector is None:
            self._inspector = self._create_infrastructure_inspector()
        return self._inspector

    # --- Factory methods ---

    def _create_authenticator(self) -> CloudAuthenticator:
        if self.provider == CloudProvider.AZURE:
            from infrastructure.cloud_providers.azure.authenticator import AzureAuthenticator
            return AzureAuthenticator()
        elif self.provider == CloudProvider.AWS:
            from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
            return AWSAuthenticator()
        elif self.provider == CloudProvider.GCP:
            from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
            return GCPAuthenticator()
        raise ValueError(f"No authenticator for provider: {self.provider}")

    def _create_executor(self) -> KubernetesCommandExecutor:
        if self.provider == CloudProvider.AZURE:
            from infrastructure.cloud_providers.azure.executor import AzureKubernetesExecutor
            return AzureKubernetesExecutor()
        elif self.provider == CloudProvider.AWS:
            from infrastructure.cloud_providers.aws.executor import AWSKubernetesExecutor
            return AWSKubernetesExecutor()
        elif self.provider == CloudProvider.GCP:
            from infrastructure.cloud_providers.gcp.executor import GCPKubernetesExecutor
            return GCPKubernetesExecutor()
        raise ValueError(f"No executor for provider: {self.provider}")

    def _create_metrics_collector(self) -> CloudMetricsCollector:
        if self.provider == CloudProvider.AZURE:
            from infrastructure.cloud_providers.azure.metrics import AzureMetricsAdapter
            return AzureMetricsAdapter()
        elif self.provider == CloudProvider.AWS:
            from infrastructure.cloud_providers.aws.metrics import AWSMetricsCollector
            return AWSMetricsCollector()
        elif self.provider == CloudProvider.GCP:
            from infrastructure.cloud_providers.gcp.metrics import GCPMetricsCollector
            return GCPMetricsCollector()
        raise ValueError(f"No metrics collector for provider: {self.provider}")

    def _create_cost_manager(self) -> CloudCostManager:
        if self.provider == CloudProvider.AZURE:
            from infrastructure.cloud_providers.azure.costs import AzureCostAdapter
            return AzureCostAdapter()
        elif self.provider == CloudProvider.AWS:
            from infrastructure.cloud_providers.aws.costs import AWSCostManager
            return AWSCostManager()
        elif self.provider == CloudProvider.GCP:
            from infrastructure.cloud_providers.gcp.costs import GCPCostManager
            return GCPCostManager()
        raise ValueError(f"No cost manager for provider: {self.provider}")

    def _create_account_manager(self) -> CloudAccountManager:
        if self.provider == CloudProvider.AZURE:
            from infrastructure.cloud_providers.azure.accounts import AzureAccountAdapter
            return AzureAccountAdapter()
        elif self.provider == CloudProvider.AWS:
            from infrastructure.cloud_providers.aws.accounts import AWSAccountManager
            return AWSAccountManager()
        elif self.provider == CloudProvider.GCP:
            from infrastructure.cloud_providers.gcp.accounts import GCPAccountManager
            return GCPAccountManager()
        raise ValueError(f"No account manager for provider: {self.provider}")

    def _create_infrastructure_inspector(self) -> CloudInfrastructureInspector:
        if self.provider == CloudProvider.AZURE:
            from infrastructure.cloud_providers.azure.inspector import AzureInfrastructureInspector
            return AzureInfrastructureInspector()
        elif self.provider == CloudProvider.AWS:
            from infrastructure.cloud_providers.aws.inspector import AWSInfrastructureInspector
            return AWSInfrastructureInspector()
        elif self.provider == CloudProvider.GCP:
            from infrastructure.cloud_providers.gcp.inspector import GCPInfrastructureInspector
            return GCPInfrastructureInspector()
        raise ValueError(f"No infrastructure inspector for provider: {self.provider}")
