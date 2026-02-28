"""
Cloud Provider Abstract Base Classes
=====================================

All cloud providers (Azure, AWS, GCP) implement these interfaces.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime

from infrastructure.cloud_providers.types import ClusterIdentifier


class CloudAuthenticator(ABC):
    """Authenticate with a cloud provider and manage credentials."""

    @abstractmethod
    def authenticate(self) -> bool:
        """Initialize and validate credentials. Returns True if successful."""

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if current credentials are valid."""

    @abstractmethod
    def refresh_credentials(self) -> bool:
        """Force credential refresh. Returns True if successful."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier (e.g. 'azure', 'aws', 'gcp')."""


class KubernetesCommandExecutor(ABC):
    """Execute kubectl commands against a managed Kubernetes cluster."""

    @abstractmethod
    def execute_kubectl(
        self,
        cluster: ClusterIdentifier,
        command: str,
        timeout: int = 180,
    ) -> Optional[str]:
        """
        Execute a kubectl command against the specified cluster.

        Args:
            cluster: Target cluster identifier
            command: kubectl command string (e.g. 'kubectl get pods -A -o json')
            timeout: Maximum seconds to wait for execution

        Returns:
            Command output as string, or None on failure
        """

    @abstractmethod
    def execute_managed_command(
        self,
        cluster: ClusterIdentifier,
        command: str,
        timeout: int = 180,
    ) -> Optional[str]:
        """
        Execute a provider-managed command (e.g. 'az aks show', 'aws eks describe-cluster').

        Args:
            cluster: Target cluster identifier
            command: Provider CLI command string
            timeout: Maximum seconds to wait

        Returns:
            Command output as string, or None on failure
        """

    @abstractmethod
    def test_connectivity(self, cluster: ClusterIdentifier) -> bool:
        """Test if we can reach the cluster. Returns True if reachable."""


class CloudMetricsCollector(ABC):
    """Collect infrastructure metrics from cloud monitoring services."""

    @abstractmethod
    def get_node_metrics(
        self,
        cluster: ClusterIdentifier,
    ) -> Optional[Dict[str, Any]]:
        """
        Get node-level CPU and memory metrics.

        Returns dict with 'nodes' key containing list of:
            {'name': str, 'cpu_percent': float, 'memory_percent': float, ...}
        """

    @abstractmethod
    def get_cluster_info(
        self,
        cluster: ClusterIdentifier,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cluster metadata (version, node count, API server, etc.).

        Returns dict with 'cluster_info' key.
        """

    @abstractmethod
    def get_metric_data(
        self,
        cluster: ClusterIdentifier,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "PT1H",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Query time-series metrics.

        Args:
            cluster: Target cluster
            metric_name: Provider-specific metric name
            start_time: Query start
            end_time: Query end
            interval: Aggregation interval (ISO 8601 duration)

        Returns list of {'timestamp': datetime, 'value': float} dicts.
        """


class CloudCostManager(ABC):
    """Query cloud cost and pricing data."""

    @abstractmethod
    def get_cluster_costs(
        self,
        cluster: ClusterIdentifier,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cost breakdown for a cluster over a time range.

        Returns dict with keys: total_cost, currency, breakdown (by resource type).
        """

    @abstractmethod
    def get_vm_pricing(
        self,
        region: str,
        vm_sizes: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get VM/instance pricing for a region.

        Returns dict mapping instance type → {'hourly_cost': float, 'monthly_cost': float, ...}
        """

    @abstractmethod
    def estimate_savings(
        self,
        cluster: ClusterIdentifier,
        recommendations: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate estimated savings from a list of optimization recommendations.

        Returns dict with total_monthly_savings, breakdown by category.
        """


class CloudAccountManager(ABC):
    """Manage cloud accounts/subscriptions/projects."""

    @abstractmethod
    def list_accounts(self) -> List[Dict[str, Any]]:
        """
        List accessible accounts/subscriptions/projects.

        Returns list of {'id': str, 'name': str, 'provider': str, ...}
        """

    @abstractmethod
    def validate_cluster_access(
        self,
        cluster: ClusterIdentifier,
    ) -> bool:
        """Verify the current credentials can access the given cluster."""

    @abstractmethod
    def discover_clusters(
        self,
        account_id: Optional[str] = None,
    ) -> List[ClusterIdentifier]:
        """
        Discover all managed Kubernetes clusters in an account.

        Args:
            account_id: Optional filter to specific account/subscription/project

        Returns list of ClusterIdentifier for each discovered cluster.
        """
