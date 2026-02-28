"""
Service Container for FastAPI dependency injection.

Centralizes all service singletons that were previously imported inline
via `try: from X import singleton` inside endpoint functions.
"""

import os
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_container: Optional['ServiceContainer'] = None
_lock = threading.Lock()


class ServiceContainer:
    """Lazy-init container for all application services."""

    def __init__(self):
        self._cluster_manager = None
        self._auth_manager = None
        self._api_security = None
        self._settings_manager = None
        self._license_validator = None
        self._scheduler = None
        self._external_api_client = None
        self._cpu_report_exporter = None
        self._alerts_manager = None
        self._provider_registry = None

    # --- Lazy properties ---

    @property
    def cluster_manager(self):
        if self._cluster_manager is None:
            from shared.config.config import enhanced_cluster_manager
            self._cluster_manager = enhanced_cluster_manager
        return self._cluster_manager

    @property
    def auth_manager(self):
        if self._auth_manager is None:
            from infrastructure.services.auth_manager import auth_manager
            self._auth_manager = auth_manager
        return self._auth_manager

    @property
    def api_security(self):
        if self._api_security is None:
            from infrastructure.services.api_security import api_security
            self._api_security = api_security
        return self._api_security

    @property
    def settings_manager(self):
        if self._settings_manager is None:
            from infrastructure.services.settings_manager import settings_manager
            self._settings_manager = settings_manager
        return self._settings_manager

    @property
    def license_validator(self):
        if self._license_validator is None:
            from infrastructure.services.license_validator import get_license_validator
            self._license_validator = get_license_validator()
        return self._license_validator

    @property
    def scheduler(self):
        if self._scheduler is None:
            from infrastructure.services.auto_analysis_scheduler import auto_scheduler
            self._scheduler = auto_scheduler
        return self._scheduler

    @property
    def external_api_client(self):
        if self._external_api_client is None:
            from infrastructure.services.external_api_client import get_external_api_client
            self._external_api_client = get_external_api_client()
        return self._external_api_client

    @property
    def cpu_report_exporter(self):
        if self._cpu_report_exporter is None:
            from infrastructure.services.cpu_report_exporter import create_cpu_report_exporter
            self._cpu_report_exporter = create_cpu_report_exporter()
        return self._cpu_report_exporter

    @property
    def alerts_manager(self):
        if self._alerts_manager is None:
            from infrastructure.services.enhanced_alerts_manager import get_enhanced_alerts_manager, init_enhanced_alerts_service
            manager = get_enhanced_alerts_manager()
            if manager is None:
                manager = init_enhanced_alerts_service(self.cluster_manager)
            self._alerts_manager = manager
        return self._alerts_manager

    @property
    def provider_registry(self):
        if self._provider_registry is None:
            from infrastructure.cloud_providers.registry import ProviderRegistry
            self._provider_registry = ProviderRegistry()
        return self._provider_registry

    @property
    def cloud_provider(self) -> str:
        return os.getenv('CLOUD_PROVIDER', 'azure')

    @property
    def analysis_results(self) -> Dict[str, Any]:
        from shared.config.config import analysis_results
        return analysis_results

    @property
    def analysis_cache(self) -> Dict[str, Any]:
        from shared.config.config import analysis_cache
        return analysis_cache


def get_container() -> ServiceContainer:
    """Get the global service container (creates on first call)."""
    global _container
    if _container is None:
        with _lock:
            if _container is None:
                _container = ServiceContainer()
    return _container


def initialize_container() -> ServiceContainer:
    """Initialize the service container during app startup."""
    container = get_container()
    logger.info("Service container initialized")
    return container
