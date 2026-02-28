"""
Cloud Provider Abstract Base Classes
=====================================

All cloud providers (Azure, AWS, GCP) implement these interfaces.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime

from infrastructure.cloud_providers.types import ClusterIdentifier, CloudProvider


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

    @abstractmethod
    def find_cluster_account(
        self,
        cluster_name: str,
        resource_group: Optional[str] = None,
    ) -> Optional[str]:
        """
        Auto-detect which account/subscription/project contains a cluster.

        Args:
            cluster_name: Name of the cluster to find
            resource_group: Optional resource group hint (Azure-specific)

        Returns account/subscription/project ID, or None if not found.
        """

    @abstractmethod
    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get account metadata for display.

        Returns dict with 'id', 'name', 'provider' keys, or None if not found.
        """

    @abstractmethod
    def execute_with_account_context(
        self,
        account_id: str,
        func,
        *args,
        **kwargs,
    ) -> Any:
        """
        Run a function within the scope of a specific account.
        Handles credential scoping, concurrency limits, and cleanup.

        Args:
            account_id: Account/subscription/project to scope to
            func: Callable to execute
            *args, **kwargs: Passed through to func
        """


class CloudInfrastructureInspector(ABC):
    """Query cloud infrastructure resources: cluster metadata, observability, waste detection."""

    # --- Cluster metadata ---

    @abstractmethod
    def get_cluster_details(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Full cluster metadata as JSON string (e.g. az aks show)."""

    @abstractmethod
    def get_node_pools(self, cluster: ClusterIdentifier) -> Optional[str]:
        """List node pools / managed node groups as JSON string."""

    @abstractmethod
    def get_cluster_version(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Running Kubernetes version string."""

    @abstractmethod
    def get_cluster_identity(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Cluster identity / IAM config as JSON string."""

    @abstractmethod
    def get_cluster_region(self, cluster: ClusterIdentifier) -> str:
        """Actual cloud region where the cluster runs."""

    @abstractmethod
    def get_node_resource_scope(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Provider-managed resource scope for nodes (e.g. Azure MC_ resource group)."""

    # --- Observability ---

    @abstractmethod
    def get_log_analytics_resources(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Log analytics / CloudWatch Log Groups as JSON string."""

    @abstractmethod
    def get_application_monitoring(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Application monitoring components (App Insights / X-Ray) as JSON string."""

    @abstractmethod
    def get_observability_costs(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        """Cost breakdown for observability resources as JSON string."""

    @abstractmethod
    def get_consumption_usage(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        """Detailed consumption / usage records as JSON string."""

    # --- Waste detection ---

    @abstractmethod
    def get_orphaned_disks(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Unattached disks related to the cluster as JSON string."""

    @abstractmethod
    def get_unused_public_ips(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Unassociated public IPs related to the cluster as JSON string."""

    @abstractmethod
    def get_load_balancer_analysis(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Load balancer configuration analysis as JSON string."""

    @abstractmethod
    def get_storage_tier_analysis(self, cluster: ClusterIdentifier, pvc_data: Optional[str] = None) -> Optional[str]:
        """Storage tier optimization opportunities as JSON string."""

    @abstractmethod
    def get_network_waste_analysis(self, cluster: ClusterIdentifier, services_data: Optional[str] = None) -> Optional[str]:
        """Network waste detection (LB consolidation etc.) as JSON string."""
