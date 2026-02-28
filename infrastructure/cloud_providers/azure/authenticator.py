"""
Azure Authenticator Adapter
============================

Delegates to the existing AzureSDKManager singleton.
"""

import logging
from infrastructure.cloud_providers.base import CloudAuthenticator

logger = logging.getLogger(__name__)


class AzureAuthenticator(CloudAuthenticator):
    """Wraps AzureSDKManager for the CloudAuthenticator interface."""

    def __init__(self):
        from infrastructure.services.azure_sdk_manager import azure_sdk_manager
        self._manager = azure_sdk_manager

    def authenticate(self) -> bool:
        return self._manager.is_authenticated()

    def is_authenticated(self) -> bool:
        return self._manager.is_authenticated()

    def refresh_credentials(self) -> bool:
        return self._manager.refresh_credentials()

    def get_provider_name(self) -> str:
        return "azure"

    @property
    def sdk_manager(self):
        """Direct access to underlying AzureSDKManager for Azure-specific operations."""
        return self._manager
