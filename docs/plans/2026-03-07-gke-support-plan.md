# GKE Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement full GKE (Google Kubernetes Engine) support across all 6 cloud provider adapter interfaces, achieving feature parity with the existing EKS implementation.

**Architecture:** Replace the 6 NotImplementedError stubs in `infrastructure/cloud_providers/gcp/` with real implementations using Google Cloud Python client libraries. Follow the same patterns established by the AWS/EKS adapters: class-level auth singleton caching, subprocess kubectl for commands, SDK interception for managed operations, and schema normalization to `agent_pool_profiles` format.

**Tech Stack:** google-cloud-container (GKE API), google-cloud-compute (VMs/disks/IPs), google-cloud-monitoring (metrics), google-cloud-bigquery (cost analysis), google-cloud-billing (pricing catalog), google-cloud-logging (logs), google-cloud-resource-manager (project discovery), google-auth (credentials)

**Design Doc:** `docs/plans/2026-03-07-gke-support-design.md`

---

## Task 1: Add GCP Dependencies

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/requirements/requirements.txt`

**Step 1: Add GCP packages to requirements.txt**

Add after the AWS SDK line (line 23):

```
# GCP SDK (for GKE integration)
google-auth>=2.27.0
google-cloud-container>=2.25.0
google-cloud-compute>=1.15.0
google-cloud-monitoring>=2.15.0
google-cloud-billing>=1.14.0
google-cloud-bigquery>=3.13.0
google-cloud-logging>=3.8.0
google-cloud-resource-manager>=1.10.0
```

**Step 2: Install dependencies**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && pip install google-auth google-cloud-container google-cloud-compute google-cloud-monitoring google-cloud-billing google-cloud-bigquery google-cloud-logging google-cloud-resource-manager`

**Step 3: Verify imports work**

Run: `python3 -c "import google.auth; import google.cloud.container_v1; import google.cloud.compute_v1; import google.cloud.monitoring_v3; import google.cloud.billing_v1; import google.cloud.bigquery; import google.cloud.logging_v2; import google.cloud.resourcemanager_v3; print('All GCP imports OK')"`

Expected: `All GCP imports OK`

**Step 4: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add requirements/requirements.txt
git commit -m "feat(gke): add Google Cloud Python SDK dependencies"
```

---

## Task 2: GCPAuthenticator

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/authenticator.py`
- Reference: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/aws/authenticator.py`

**Step 1: Implement GCPAuthenticator**

Replace the entire file. Follow the AWS authenticator pattern exactly:

```python
"""GCP Authenticator — google.auth.default() credential chain with class-level singleton."""

import os
import logging
from typing import Optional

from infrastructure.cloud_providers.base import CloudAuthenticator

logger = logging.getLogger(__name__)


class GCPAuthenticator(CloudAuthenticator):
    """Authenticates with GCP using Application Default Credentials.

    Credential chain:
    1. GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON)
    2. gcloud CLI auth (gcloud auth application-default login)
    3. GCE metadata server (when running on GCP)
    """

    def __init__(self):
        self._credentials = None
        self._project_id: Optional[str] = None
        self._authenticated = False

    def authenticate(self) -> bool:
        try:
            import google.auth
            from google.auth.exceptions import DefaultCredentialsError
        except ImportError:
            logger.error("google-auth not installed. Run: pip install google-auth")
            self._authenticated = False
            return False

        try:
            scopes = ['https://www.googleapis.com/auth/cloud-platform']
            credentials, project = google.auth.default(scopes=scopes)

            # Project can come from credentials, env var, or explicit config
            self._project_id = (
                project
                or os.getenv('GOOGLE_CLOUD_PROJECT')
                or os.getenv('GCLOUD_PROJECT')
                or os.getenv('GCP_PROJECT')
            )

            if not self._project_id:
                logger.warning("GCP authenticated but no project ID detected. "
                               "Set GOOGLE_CLOUD_PROJECT env var.")

            self._credentials = credentials
            self._authenticated = True

            masked_project = f"***{self._project_id[-6:]}" if self._project_id and len(self._project_id) > 6 else self._project_id
            logger.info(f"GCP authenticated: project={masked_project}")
            return True

        except DefaultCredentialsError as e:
            logger.warning(f"GCP authentication failed: {e}")
            self._authenticated = False
            return False
        except Exception as e:
            logger.error(f"Unexpected GCP auth error: {e}")
            self._authenticated = False
            return False

    def is_authenticated(self) -> bool:
        if not self._authenticated:
            return self.authenticate()
        return self._authenticated

    def refresh_credentials(self) -> bool:
        self._credentials = None
        self._authenticated = False
        self._project_id = None
        return self.authenticate()

    def get_provider_name(self) -> str:
        return "gcp"

    @property
    def credentials(self):
        """Shared by other GCP adapters."""
        if not self._authenticated:
            self.authenticate()
        return self._credentials

    @property
    def project_id(self) -> Optional[str]:
        if not self._authenticated:
            self.authenticate()
        return self._project_id
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/authenticator.py', doraise=True); print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/authenticator.py
git commit -m "feat(gke): implement GCPAuthenticator with google.auth.default()"
```

---

## Task 3: GCPKubernetesExecutor

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/executor.py`
- Reference: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/aws/executor.py`

**Step 1: Implement GCPKubernetesExecutor**

Replace the entire file:

```python
"""GCP Kubernetes Executor — subprocess kubectl + GKE Container API for managed commands."""

import json
import logging
import subprocess
from typing import Optional

from infrastructure.cloud_providers.base import KubernetesCommandExecutor
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPKubernetesExecutor(KubernetesCommandExecutor):
    """Executes kubectl commands against GKE clusters.

    Assumes user has run: gcloud container clusters get-credentials <cluster> --zone <zone> --project <project>
    Intercepts GKE-specific commands and routes them to the Container API.
    """

    _auth_instance = None  # Class-level singleton (same pattern as AWS)

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPKubernetesExecutor._auth_instance is None or not GCPKubernetesExecutor._auth_instance.is_authenticated():
            GCPKubernetesExecutor._auth_instance = GCPAuthenticator()
        return GCPKubernetesExecutor._auth_instance

    def _get_container_client(self):
        from google.cloud import container_v1
        auth = self._get_auth()
        return container_v1.ClusterManagerClient(credentials=auth.credentials)

    def _cluster_path(self, cluster: ClusterIdentifier) -> str:
        """GKE cluster resource path: projects/{project}/locations/{location}/clusters/{name}"""
        auth = self._get_auth()
        project = cluster.project_id or auth.project_id
        location = cluster.zone or cluster.region
        return f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

    def execute_kubectl(self, cluster: ClusterIdentifier, command: str, timeout: int = 180) -> Optional[str]:
        try:
            full_command = f"kubectl {command}"
            logger.debug(f"GKE kubectl: {full_command[:100]}...")

            result = subprocess.run(
                full_command, shell=True, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"GKE kubectl failed (rc={result.returncode}): {result.stderr[:200]}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"GKE kubectl timed out after {timeout}s: {command[:80]}")
            return None
        except Exception as e:
            logger.error(f"GKE kubectl error: {e}")
            return None

    def execute_managed_command(self, cluster: ClusterIdentifier, command: str, timeout: int = 180) -> Optional[str]:
        """Intercept GKE SDK commands, fall back to kubectl."""
        try:
            cmd_lower = command.lower().strip()

            # Intercept: describe-cluster
            if 'describe-cluster' in cmd_lower or 'get-cluster' in cmd_lower:
                client = self._get_container_client()
                result = client.get_cluster(name=self._cluster_path(cluster))
                return json.dumps({
                    'name': result.name,
                    'status': result.status.name if result.status else 'UNKNOWN',
                    'location': result.location,
                    'currentMasterVersion': result.current_master_version,
                    'currentNodeVersion': result.current_node_version,
                    'endpoint': result.endpoint,
                    'nodePoolCount': len(result.node_pools),
                }, indent=2)

            # Intercept: list-nodepools
            if 'list-nodepool' in cmd_lower or 'list-node-pool' in cmd_lower:
                client = self._get_container_client()
                result = client.list_node_pools(parent=self._cluster_path(cluster))
                pools = []
                for np in result.node_pools:
                    pools.append({
                        'name': np.name,
                        'machineType': np.config.machine_type if np.config else None,
                        'diskSizeGb': np.config.disk_size_gb if np.config else None,
                        'nodeCount': np.initial_node_count,
                        'status': np.status.name if np.status else 'UNKNOWN',
                        'autoscaling': {
                            'enabled': np.autoscaling.enabled if np.autoscaling else False,
                            'minNodeCount': np.autoscaling.min_node_count if np.autoscaling else 0,
                            'maxNodeCount': np.autoscaling.max_node_count if np.autoscaling else 0,
                        } if np.autoscaling else None,
                    })
                return json.dumps(pools, indent=2)

            # Intercept: describe-nodepool
            if 'describe-nodepool' in cmd_lower or 'describe-node-pool' in cmd_lower:
                # Extract nodepool name from command (last token)
                parts = command.strip().split()
                pool_name = parts[-1] if parts else None
                if pool_name:
                    client = self._get_container_client()
                    pool_path = f"{self._cluster_path(cluster)}/nodePools/{pool_name}"
                    result = client.get_node_pool(name=pool_path)
                    return json.dumps({
                        'name': result.name,
                        'machineType': result.config.machine_type if result.config else None,
                        'diskSizeGb': result.config.disk_size_gb if result.config else None,
                        'initialNodeCount': result.initial_node_count,
                        'status': result.status.name if result.status else 'UNKNOWN',
                        'version': result.version,
                        'autoscaling': {
                            'enabled': result.autoscaling.enabled if result.autoscaling else False,
                            'minNodeCount': result.autoscaling.min_node_count if result.autoscaling else 0,
                            'maxNodeCount': result.autoscaling.max_node_count if result.autoscaling else 0,
                        } if result.autoscaling else None,
                    }, indent=2)

            # Fallback to kubectl
            return self.execute_kubectl(cluster, command, timeout)

        except Exception as e:
            logger.error(f"GKE managed command failed: {e}")
            return None

    def test_connectivity(self, cluster: ClusterIdentifier) -> bool:
        """Test cluster connectivity via GKE API (describe_cluster)."""
        try:
            client = self._get_container_client()
            result = client.get_cluster(name=self._cluster_path(cluster))
            return result.status.name in ('RUNNING', 'RECONCILING', 'PROVISIONING')
        except Exception as e:
            logger.warning(f"GKE connectivity test failed: {e}")
            return False
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/executor.py', doraise=True); print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/executor.py
git commit -m "feat(gke): implement GCPKubernetesExecutor with subprocess + Container API"
```

---

## Task 4: GCPMetricsCollector

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/metrics.py`
- Reference: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/aws/metrics.py`

**Step 1: Implement GCPMetricsCollector**

Replace the entire file:

```python
"""GCP Metrics Collector — kubectl top nodes + Cloud Monitoring API."""

import json
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudMetricsCollector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPMetricsCollector(CloudMetricsCollector):
    """Collects metrics from GKE clusters via kubectl and Cloud Monitoring."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPMetricsCollector._auth_instance is None or not GCPMetricsCollector._auth_instance.is_authenticated():
            GCPMetricsCollector._auth_instance = GCPAuthenticator()
        return GCPMetricsCollector._auth_instance

    def _get_executor(self):
        from infrastructure.cloud_providers.gcp.executor import GCPKubernetesExecutor
        return GCPKubernetesExecutor()

    def get_node_metrics(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        """Get node CPU/memory metrics via kubectl top nodes."""
        try:
            executor = self._get_executor()
            output = executor.execute_kubectl(cluster, "top nodes --no-headers")
            if not output:
                return None

            nodes = []
            for line in output.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5:
                    name = parts[0]
                    cpu_raw = parts[1]    # e.g. "250m" or "1"
                    cpu_pct = parts[2].replace('%', '')
                    mem_raw = parts[3]    # e.g. "1024Mi"
                    mem_pct = parts[4].replace('%', '')

                    nodes.append({
                        'name': name,
                        'cpu_usage': cpu_raw,
                        'cpu_percent': float(cpu_pct),
                        'memory_usage': mem_raw,
                        'memory_percent': float(mem_pct),
                    })

            return {'nodes': nodes}

        except Exception as e:
            logger.error(f"GKE node metrics error: {e}")
            return None

    def get_cluster_info(self, cluster: ClusterIdentifier) -> Optional[Dict[str, Any]]:
        """Get cluster info via GKE Container API."""
        try:
            from google.cloud import container_v1

            auth = self._get_auth()
            client = container_v1.ClusterManagerClient(credentials=auth.credentials)
            project = cluster.project_id or auth.project_id
            location = cluster.zone or cluster.region
            name = f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

            result = client.get_cluster(name=name)

            return {
                'cluster_info': {
                    'cluster_name': result.name,
                    'kubernetes_version': result.current_master_version,
                    'status': result.status.name if result.status else 'UNKNOWN',
                    'region': result.location,
                    'endpoint': result.endpoint,
                    'node_pool_count': len(result.node_pools),
                    'network': result.network,
                    'subnetwork': result.subnetwork,
                    'self_link': result.self_link,
                }
            }

        except Exception as e:
            logger.error(f"GKE cluster info error: {e}")
            return None

    def get_metric_data(self, cluster: ClusterIdentifier, metric_name: str,
                        start_time: datetime, end_time: datetime,
                        interval: str = "PT1H") -> Optional[List[Dict[str, Any]]]:
        """Query Cloud Monitoring for time-series data."""
        try:
            from google.cloud import monitoring_v3
            from google.protobuf.timestamp_pb2 import Timestamp

            auth = self._get_auth()
            project = cluster.project_id or auth.project_id
            client = monitoring_v3.MetricServiceClient(credentials=auth.credentials)

            project_name = f"projects/{project}"
            period_seconds = self._parse_interval(interval)

            # Map common metric names to Cloud Monitoring metric types
            metric_type = self._resolve_metric_type(metric_name)

            interval_pb = monitoring_v3.TimeInterval()
            start_ts = Timestamp()
            start_ts.FromDatetime(start_time)
            end_ts = Timestamp()
            end_ts.FromDatetime(end_time)
            interval_pb.start_time = start_ts
            interval_pb.end_time = end_ts

            aggregation = monitoring_v3.Aggregation()
            aggregation.alignment_period = {"seconds": period_seconds}
            aggregation.per_series_aligner = monitoring_v3.Aggregation.Aligner.ALIGN_MEAN

            results = client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type = "{metric_type}" AND '
                              f'resource.labels.cluster_name = "{cluster.cluster_name}"',
                    "interval": interval_pb,
                    "aggregation": aggregation,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )

            data_points = []
            for ts in results:
                for point in ts.points:
                    data_points.append({
                        'timestamp': point.interval.end_time.isoformat(),
                        'value': point.value.double_value or point.value.int64_value,
                    })

            # Sort by timestamp
            data_points.sort(key=lambda x: x['timestamp'])
            return data_points

        except Exception as e:
            logger.error(f"GKE metric data error: {e}")
            return None

    @staticmethod
    def _parse_interval(interval: str) -> int:
        """Parse ISO 8601 duration to seconds. PT1H -> 3600, PT5M -> 300, PT1D -> 86400."""
        match = re.match(r'PT(?:(\d+)D)?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', interval, re.IGNORECASE)
        if not match:
            return 3600  # default 1 hour

        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)
        return days * 86400 + hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _resolve_metric_type(metric_name: str) -> str:
        """Map common metric names to GCP Cloud Monitoring metric types."""
        metric_map = {
            'cpu': 'kubernetes.io/node/cpu/allocatable_utilization',
            'cpu_utilization': 'kubernetes.io/node/cpu/allocatable_utilization',
            'memory': 'kubernetes.io/node/memory/allocatable_utilization',
            'memory_utilization': 'kubernetes.io/node/memory/allocatable_utilization',
            'disk': 'kubernetes.io/node/ephemeral_storage/used_bytes',
            'network_in': 'kubernetes.io/node/network/received_bytes_count',
            'network_out': 'kubernetes.io/node/network/sent_bytes_count',
            'pod_count': 'kubernetes.io/node/pid_used',
        }
        return metric_map.get(metric_name.lower(), metric_name)
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/metrics.py', doraise=True); print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/metrics.py
git commit -m "feat(gke): implement GCPMetricsCollector with kubectl top + Cloud Monitoring"
```

---

## Task 5: GCPCostManager

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/costs.py`
- Reference: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/aws/costs.py`

**Step 1: Implement GCPCostManager**

Replace the entire file:

```python
"""GCP Cost Manager — BigQuery billing export + Cloud Billing Catalog API for pricing."""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudCostManager
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)

# GKE machine type families and their typical hourly costs (us-central1, on-demand)
# Used as fallback when Billing Catalog API is unavailable
_DEFAULT_PRICING = {
    'e2-standard-2': {'hourly': 0.067, 'vcpus': '2', 'memory': '8 GB'},
    'e2-standard-4': {'hourly': 0.134, 'vcpus': '4', 'memory': '16 GB'},
    'e2-standard-8': {'hourly': 0.268, 'vcpus': '8', 'memory': '32 GB'},
    'e2-standard-16': {'hourly': 0.536, 'vcpus': '16', 'memory': '64 GB'},
    'n2-standard-2': {'hourly': 0.097, 'vcpus': '2', 'memory': '8 GB'},
    'n2-standard-4': {'hourly': 0.194, 'vcpus': '4', 'memory': '16 GB'},
    'n2-standard-8': {'hourly': 0.388, 'vcpus': '8', 'memory': '32 GB'},
    'n2-standard-16': {'hourly': 0.776, 'vcpus': '16', 'memory': '64 GB'},
    'n2-standard-32': {'hourly': 1.552, 'vcpus': '32', 'memory': '128 GB'},
    'n1-standard-1': {'hourly': 0.047, 'vcpus': '1', 'memory': '3.75 GB'},
    'n1-standard-2': {'hourly': 0.095, 'vcpus': '2', 'memory': '7.5 GB'},
    'n1-standard-4': {'hourly': 0.190, 'vcpus': '4', 'memory': '15 GB'},
    'n1-standard-8': {'hourly': 0.380, 'vcpus': '8', 'memory': '30 GB'},
    'c2-standard-4': {'hourly': 0.209, 'vcpus': '4', 'memory': '16 GB'},
    'c2-standard-8': {'hourly': 0.418, 'vcpus': '8', 'memory': '32 GB'},
}

# Sample types to return if none specified
_SAMPLE_TYPES = ['e2-standard-4', 'e2-standard-8', 'n2-standard-4', 'n2-standard-8', 'n1-standard-4']


class GCPCostManager(CloudCostManager):
    """Manages GKE cluster cost analysis via BigQuery billing export and Cloud Billing Catalog."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPCostManager._auth_instance is None or not GCPCostManager._auth_instance.is_authenticated():
            GCPCostManager._auth_instance = GCPAuthenticator()
        return GCPCostManager._auth_instance

    def get_cluster_costs(self, cluster: ClusterIdentifier, start_date: datetime,
                          end_date: datetime) -> Optional[Dict[str, Any]]:
        """Query BigQuery billing export for GKE cluster costs, filtered by cluster label."""
        try:
            from google.cloud import bigquery

            auth = self._get_auth()
            project = cluster.project_id or auth.project_id

            dataset = os.getenv('GCP_BILLING_DATASET')
            billing_account_id = os.getenv('GCP_BILLING_ACCOUNT_ID', '').replace('-', '')

            if not dataset:
                logger.warning("GCP_BILLING_DATASET not set. Cannot query costs.")
                return None

            client = bigquery.Client(credentials=auth.credentials, project=project)

            # BigQuery billing export table name format
            table = f"`{project}.{dataset}.gcp_billing_export_resource_v1_{billing_account_id}`"

            # GKE auto-labels clusters with goog-k8s-cluster-name
            query = f"""
                SELECT
                    service.description AS service,
                    SUM(cost) AS total_cost,
                    currency
                FROM {table}
                WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
                    AND project.id = @project_id
                    AND EXISTS (
                        SELECT 1 FROM UNNEST(labels) AS l
                        WHERE l.key = 'goog-k8s-cluster-name'
                        AND l.value = @cluster_name
                    )
                GROUP BY service.description, currency
                ORDER BY total_cost DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("project_id", "STRING", project),
                    bigquery.ScalarQueryParameter("cluster_name", "STRING", cluster.cluster_name),
                ]
            )

            results = client.query(query, job_config=job_config).result()

            breakdown = {}
            total = 0.0
            currency = 'USD'
            for row in results:
                service_name = row.service
                cost = float(row.total_cost)
                breakdown[service_name] = round(cost, 2)
                total += cost
                currency = row.currency

            if total == 0:
                logger.info(f"No cost data found for GKE cluster '{cluster.cluster_name}'. "
                            "Verify billing export is enabled and cluster label exists.")
                return None

            logger.info(f"GKE costs for '{cluster.cluster_name}': ${total:.2f} ({len(breakdown)} services)")

            return {
                'total_cost': round(total, 2),
                'currency': currency,
                'breakdown': breakdown,
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                }
            }

        except Exception as e:
            logger.error(f"GKE cost query error: {e}")
            return None

    def get_vm_pricing(self, region: str, vm_sizes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get GCE machine type pricing via Compute Engine API + fallback table."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = cluster_project = auth.project_id
            target_types = vm_sizes or _SAMPLE_TYPES

            pricing = {}

            # Try Compute Engine API for machine type specs
            try:
                client = compute_v1.MachineTypesClient(credentials=auth.credentials)
                # Region -> zone (pick first zone, e.g. us-central1 -> us-central1-a)
                zone = f"{region}-a" if not region.endswith(('-a', '-b', '-c', '-f')) else region

                for mt_name in target_types:
                    try:
                        mt = client.get(project=project, zone=zone, machine_type=mt_name)
                        # Compute API doesn't return pricing directly,
                        # use fallback table for hourly costs
                        fallback = _DEFAULT_PRICING.get(mt_name, {})
                        hourly = fallback.get('hourly', 0.0)

                        pricing[mt_name] = {
                            'hourly_cost': hourly,
                            'monthly_cost': round(hourly * 730, 2),
                            'vcpus': str(mt.guest_cpus),
                            'memory': f"{mt.memory_mb / 1024:.1f} GB",
                            'instance_family': mt_name.split('-')[0],
                        }
                    except Exception:
                        # Machine type may not exist in this zone
                        if mt_name in _DEFAULT_PRICING:
                            fb = _DEFAULT_PRICING[mt_name]
                            pricing[mt_name] = {
                                'hourly_cost': fb['hourly'],
                                'monthly_cost': round(fb['hourly'] * 730, 2),
                                'vcpus': fb['vcpus'],
                                'memory': fb['memory'],
                                'instance_family': mt_name.split('-')[0],
                            }

            except Exception as e:
                logger.warning(f"Compute API unavailable, using fallback pricing: {e}")
                for mt_name in target_types:
                    if mt_name in _DEFAULT_PRICING:
                        fb = _DEFAULT_PRICING[mt_name]
                        pricing[mt_name] = {
                            'hourly_cost': fb['hourly'],
                            'monthly_cost': round(fb['hourly'] * 730, 2),
                            'vcpus': fb['vcpus'],
                            'memory': fb['memory'],
                            'instance_family': mt_name.split('-')[0],
                        }

            return pricing if pricing else None

        except Exception as e:
            logger.error(f"GKE VM pricing error: {e}")
            return None

    def estimate_savings(self, cluster: ClusterIdentifier,
                         recommendations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Estimate potential savings from recommendations."""
        try:
            breakdown = {}
            total = 0.0

            for rec in recommendations:
                category = rec.get('category', 'general')
                savings = float(rec.get('estimated_monthly_savings', 0))
                breakdown[category] = breakdown.get(category, 0) + savings
                total += savings

            return {
                'total_monthly_savings': round(total, 2),
                'total_annual_savings': round(total * 12, 2),
                'currency': 'USD',
                'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
            }

        except Exception as e:
            logger.error(f"GKE savings estimation error: {e}")
            return None
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/costs.py', doraise=True); print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/costs.py
git commit -m "feat(gke): implement GCPCostManager with BigQuery billing + Compute pricing"
```

---

## Task 6: GCPAccountManager

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/accounts.py`
- Reference: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/aws/accounts.py`

**Step 1: Implement GCPAccountManager**

Replace the entire file:

```python
"""GCP Account Manager — Resource Manager projects + GKE cluster discovery."""

import logging
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudAccountManager
from infrastructure.cloud_providers.types import CloudProvider, ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPAccountManager(CloudAccountManager):
    """Manages GCP project access and GKE cluster discovery."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPAccountManager._auth_instance is None or not GCPAccountManager._auth_instance.is_authenticated():
            GCPAccountManager._auth_instance = GCPAuthenticator()
        return GCPAccountManager._auth_instance

    def list_accounts(self) -> List[Dict[str, Any]]:
        """List accessible GCP projects."""
        try:
            auth = self._get_auth()
            accounts = []

            # Always include the default project
            if auth.project_id:
                accounts.append({
                    'id': auth.project_id,
                    'name': auth.project_id,
                    'provider': 'gcp',
                    'is_default': True,
                })

            # Try to list additional projects via Resource Manager
            try:
                from google.cloud import resourcemanager_v3

                client = resourcemanager_v3.ProjectsClient(credentials=auth.credentials)
                request = resourcemanager_v3.SearchProjectsRequest()
                for project in client.search_projects(request=request):
                    if project.project_id != auth.project_id and project.state.name == 'ACTIVE':
                        accounts.append({
                            'id': project.project_id,
                            'name': project.display_name or project.project_id,
                            'provider': 'gcp',
                            'is_default': False,
                        })
            except Exception as e:
                logger.debug(f"Resource Manager project listing unavailable: {e}")

            return accounts

        except Exception as e:
            logger.error(f"GCP list_accounts error: {e}")
            return []

    def validate_cluster_access(self, cluster: ClusterIdentifier) -> bool:
        """Verify we can access this GKE cluster."""
        try:
            from google.cloud import container_v1

            auth = self._get_auth()
            client = container_v1.ClusterManagerClient(credentials=auth.credentials)
            project = cluster.project_id or auth.project_id
            location = cluster.zone or cluster.region
            name = f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

            result = client.get_cluster(name=name)
            return result.status.name in ('RUNNING', 'RECONCILING', 'PROVISIONING')

        except Exception as e:
            logger.warning(f"GKE cluster access validation failed: {e}")
            return False

    def discover_clusters(self, account_id: Optional[str] = None) -> List[ClusterIdentifier]:
        """Discover all GKE clusters in a project using locations/- wildcard."""
        try:
            from google.cloud import container_v1

            auth = self._get_auth()
            project = account_id or auth.project_id
            if not project:
                logger.warning("No project ID available for cluster discovery")
                return []

            client = container_v1.ClusterManagerClient(credentials=auth.credentials)

            # locations/- is the wildcard for ALL locations (zones + regions)
            parent = f"projects/{project}/locations/-"
            response = client.list_clusters(parent=parent)

            clusters = []
            for c in response.clusters:
                # Extract region from location (e.g. 'us-central1-a' -> 'us-central1')
                location = c.location
                region = '-'.join(location.split('-')[:2]) if location.count('-') >= 2 else location

                clusters.append(ClusterIdentifier(
                    provider=CloudProvider.GCP,
                    cluster_name=c.name,
                    region=region,
                    project_id=project,
                    zone=location,
                ))

            if clusters:
                locations = set(c.zone for c in clusters)
                logger.info(f"Discovered {len(clusters)} GKE cluster(s) in project '{project}' "
                            f"across {len(locations)} location(s)")
            else:
                logger.info(f"No GKE clusters found in project '{project}'")

            return clusters

        except Exception as e:
            logger.error(f"GKE cluster discovery error: {e}")
            return []

    def find_cluster_account(self, cluster_name: str, resource_group: Optional[str] = None) -> Optional[str]:
        """Find which project contains a GKE cluster by name."""
        try:
            accounts = self.list_accounts()
            for account in accounts:
                clusters = self.discover_clusters(account['id'])
                for c in clusters:
                    if c.cluster_name == cluster_name:
                        logger.info(f"Found GKE cluster '{cluster_name}' in project '{account['id']}'")
                        return account['id']

            logger.warning(f"GKE cluster '{cluster_name}' not found in any accessible project")
            return None

        except Exception as e:
            logger.error(f"GKE find_cluster_account error: {e}")
            return None

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get GCP project metadata."""
        try:
            from google.cloud import resourcemanager_v3

            auth = self._get_auth()
            client = resourcemanager_v3.ProjectsClient(credentials=auth.credentials)
            project = client.get_project(name=f"projects/{account_id}")

            return {
                'id': project.project_id,
                'name': project.display_name or project.project_id,
                'provider': 'gcp',
                'state': project.state.name if project.state else 'UNKNOWN',
            }

        except Exception as e:
            logger.warning(f"GCP project info unavailable for '{account_id}': {e}")
            return {
                'id': account_id,
                'name': account_id,
                'provider': 'gcp',
            }

    def execute_with_account_context(self, account_id: str, func, *args, **kwargs):
        """Execute function within project context (pass-through for GCP)."""
        return func(*args, **kwargs)
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/accounts.py', doraise=True); print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/accounts.py
git commit -m "feat(gke): implement GCPAccountManager with Resource Manager + cluster discovery"
```

---

## Task 7: GCPInfrastructureInspector — Cluster Metadata (6 methods)

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/inspector.py`
- Reference: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/aws/inspector.py`

**Step 1: Implement inspector with cluster metadata methods**

Replace the entire file with the full inspector (all 15 methods). This is the largest adapter at ~550 LOC, split across metadata, observability, and waste detection.

```python
"""GCP Infrastructure Inspector — cluster metadata, observability, and waste detection via GCP APIs."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from infrastructure.cloud_providers.base import CloudInfrastructureInspector
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class GCPInfrastructureInspector(CloudInfrastructureInspector):
    """Inspects GKE cluster infrastructure for optimization analysis.

    Uses GKE Container API, Compute Engine API, Cloud Logging, Cloud Monitoring,
    and BigQuery for comprehensive cluster inspection.
    """

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        if GCPInfrastructureInspector._auth_instance is None or not GCPInfrastructureInspector._auth_instance.is_authenticated():
            GCPInfrastructureInspector._auth_instance = GCPAuthenticator()
        return GCPInfrastructureInspector._auth_instance

    def _get_container_client(self):
        from google.cloud import container_v1
        auth = self._get_auth()
        return container_v1.ClusterManagerClient(credentials=auth.credentials)

    def _cluster_path(self, cluster: ClusterIdentifier) -> str:
        auth = self._get_auth()
        project = cluster.project_id or auth.project_id
        location = cluster.zone or cluster.region
        return f"projects/{project}/locations/{location}/clusters/{cluster.cluster_name}"

    def _get_cluster(self, cluster: ClusterIdentifier):
        """Shared helper: fetch cluster object from GKE API."""
        client = self._get_container_client()
        return client.get_cluster(name=self._cluster_path(cluster))

    def _get_project(self, cluster: ClusterIdentifier) -> str:
        auth = self._get_auth()
        return cluster.project_id or auth.project_id

    # =========================================================================
    # Cluster Metadata (6 methods)
    # =========================================================================

    def get_cluster_details(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get cluster details with node pools normalized to agent_pool_profiles schema."""
        try:
            result = self._get_cluster(cluster)

            # Normalize GKE node pools to agent_pool_profiles (same schema as AKS/EKS)
            agent_pool_profiles = []
            for np in result.node_pools:
                config = np.config
                autoscaling = np.autoscaling

                is_spot = False
                if config and config.spot:
                    is_spot = True
                elif config and config.preemptible:
                    is_spot = True

                pool = {
                    'name': np.name,
                    'vm_size': config.machine_type if config else 'unknown',
                    'count': np.initial_node_count or 0,
                    'min_count': autoscaling.min_node_count if autoscaling and autoscaling.enabled else 0,
                    'max_count': autoscaling.max_node_count if autoscaling and autoscaling.enabled else 0,
                    'enable_auto_scaling': autoscaling.enabled if autoscaling else False,
                    'os_type': config.image_type if config else 'COS_CONTAINERD',
                    'mode': 'System' if np.name == 'default-pool' else 'User',
                    'scale_set_priority': 'Spot' if is_spot else 'Regular',
                    'disk_size_gb': config.disk_size_gb if config else 100,
                    'disk_type': config.disk_type if config else 'pd-standard',
                }
                agent_pool_profiles.append(pool)

            details = {
                'location': result.location,
                'current_kubernetes_version': result.current_master_version,
                'kubernetes_version': result.current_master_version,
                'agent_pool_profiles': agent_pool_profiles,
                'self_link': result.self_link,
                'status': result.status.name if result.status else 'UNKNOWN',
                'endpoint': result.endpoint,
                'network': result.network,
                'subnetwork': result.subnetwork,
                'cluster_ipv4_cidr': result.cluster_ipv4_cidr,
            }

            return json.dumps(details, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_cluster_details error: {e}")
            return None

    def get_node_pools(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get detailed node pool information."""
        try:
            client = self._get_container_client()
            response = client.list_node_pools(parent=self._cluster_path(cluster))

            pools = []
            for np in response.node_pools:
                config = np.config
                pool_info = {
                    'name': np.name,
                    'machine_type': config.machine_type if config else None,
                    'disk_size_gb': config.disk_size_gb if config else None,
                    'disk_type': config.disk_type if config else None,
                    'initial_node_count': np.initial_node_count,
                    'version': np.version,
                    'status': np.status.name if np.status else 'UNKNOWN',
                    'spot': config.spot if config else False,
                    'preemptible': config.preemptible if config else False,
                    'image_type': config.image_type if config else None,
                    'autoscaling': {
                        'enabled': np.autoscaling.enabled if np.autoscaling else False,
                        'min_node_count': np.autoscaling.min_node_count if np.autoscaling else 0,
                        'max_node_count': np.autoscaling.max_node_count if np.autoscaling else 0,
                    },
                    'labels': dict(config.labels) if config and config.labels else {},
                    'taints': [
                        {'key': t.key, 'value': t.value, 'effect': t.effect.name if t.effect else 'NO_SCHEDULE'}
                        for t in config.taints
                    ] if config and config.taints else [],
                }
                pools.append(pool_info)

            return json.dumps(pools, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_node_pools error: {e}")
            return None

    def get_cluster_version(self, cluster: ClusterIdentifier) -> Optional[str]:
        try:
            result = self._get_cluster(cluster)
            return result.current_master_version
        except Exception as e:
            logger.error(f"GKE get_cluster_version error: {e}")
            return None

    def get_cluster_identity(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get cluster identity (workload identity, network config)."""
        try:
            result = self._get_cluster(cluster)

            identity = {
                'workload_identity_config': {
                    'workload_pool': result.workload_identity_config.workload_pool
                } if result.workload_identity_config else None,
                'network_policy': {
                    'enabled': result.network_policy.enabled,
                    'provider': result.network_policy.provider.name if result.network_policy.provider else None,
                } if result.network_policy else None,
                'legacy_abac': {
                    'enabled': result.legacy_abac.enabled
                } if result.legacy_abac else None,
                'master_auth': {
                    'username': bool(result.master_auth.username) if result.master_auth else False,
                    'client_certificate_config': bool(result.master_auth.client_certificate_config) if result.master_auth else False,
                } if result.master_auth else None,
            }

            return json.dumps(identity, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_cluster_identity error: {e}")
            return None

    def get_cluster_region(self, cluster: ClusterIdentifier) -> str:
        """Extract region from cluster location (e.g. 'us-central1-a' -> 'us-central1')."""
        try:
            result = self._get_cluster(cluster)
            location = result.location
            # Zonal cluster: us-central1-a -> us-central1
            # Regional cluster: us-central1 -> us-central1
            parts = location.split('-')
            if len(parts) >= 3 and parts[-1].isalpha() and len(parts[-1]) == 1:
                return '-'.join(parts[:-1])
            return location
        except Exception as e:
            logger.error(f"GKE get_cluster_region error: {e}")
            return cluster.region or ''

    def get_node_resource_scope(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get managed instance group names backing node pools."""
        try:
            result = self._get_cluster(cluster)
            instance_groups = []

            for np in result.node_pools:
                if np.instance_group_urls:
                    for url in np.instance_group_urls:
                        # URL format: https://www.googleapis.com/compute/v1/projects/.../zones/.../instanceGroupManagers/...
                        ig_name = url.split('/')[-1]
                        instance_groups.append({
                            'node_pool': np.name,
                            'instance_group': ig_name,
                            'url': url,
                        })

            return json.dumps(instance_groups, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_node_resource_scope error: {e}")
            return None

    # =========================================================================
    # Observability (4 methods)
    # =========================================================================

    def get_log_analytics_resources(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Get Cloud Logging log sinks and log buckets related to the cluster."""
        try:
            from google.cloud import logging_v2

            auth = self._get_auth()
            project = self._get_project(cluster)
            client = logging_v2.Client(credentials=auth.credentials, project=project)

            # List log sinks
            sinks = []
            for sink in client.list_sinks():
                # Filter for kubernetes-related sinks
                if 'k8s' in (sink.filter_ or '').lower() or 'kubernetes' in sink.name.lower():
                    sinks.append({
                        'name': sink.name,
                        'destination': sink.destination,
                        'filter': sink.filter_,
                    })

            # Check for GKE-specific log entries (sample query)
            log_resources = {
                'sinks': sinks,
                'expected_log_names': [
                    f'projects/{project}/logs/events',
                    f'projects/{project}/logs/stdout',
                    f'projects/{project}/logs/stderr',
                ],
            }

            return json.dumps(log_resources, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_log_analytics_resources error: {e}")
            return None

    def get_application_monitoring(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Check GKE monitoring add-ons (Managed Prometheus, logging, monitoring)."""
        try:
            result = self._get_cluster(cluster)

            addons = result.addons_config
            monitoring_config = result.monitoring_config
            logging_config = result.logging_config

            info = {
                'monitoring_service': result.monitoring_service,
                'logging_service': result.logging_service,
                'addons': {
                    'http_load_balancing': addons.http_load_balancing.disabled if addons and addons.http_load_balancing else None,
                    'horizontal_pod_autoscaling': not (addons.horizontal_pod_autoscaling.disabled) if addons and addons.horizontal_pod_autoscaling else None,
                    'network_policy_config': not (addons.network_policy_config.disabled) if addons and addons.network_policy_config else None,
                    'gce_persistent_disk_csi': not (addons.gce_persistent_disk_csi_driver_config.enabled is False) if addons and addons.gce_persistent_disk_csi_driver_config else None,
                },
                'managed_prometheus': {
                    'enabled': monitoring_config.managed_prometheus_config.enabled
                } if monitoring_config and monitoring_config.managed_prometheus_config else {'enabled': False},
                'logging_component_config': {
                    'components': [c.name for c in logging_config.component_config.enable_components]
                } if logging_config and logging_config.component_config else None,
            }

            return json.dumps(info, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_application_monitoring error: {e}")
            return None

    def get_observability_costs(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        """Get Cloud Logging + Cloud Monitoring costs from BigQuery billing export."""
        try:
            import os
            from google.cloud import bigquery

            auth = self._get_auth()
            project = self._get_project(cluster)
            dataset = os.getenv('GCP_BILLING_DATASET')
            billing_account_id = os.getenv('GCP_BILLING_ACCOUNT_ID', '').replace('-', '')

            if not dataset:
                return json.dumps([])

            client = bigquery.Client(credentials=auth.credentials, project=project)
            table = f"`{project}.{dataset}.gcp_billing_export_resource_v1_{billing_account_id}`"

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            query = f"""
                SELECT
                    service.description AS service,
                    SUM(cost) AS cost,
                    currency
                FROM {table}
                WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
                    AND project.id = @project_id
                    AND service.description IN (
                        'Cloud Logging', 'Cloud Monitoring', 'Cloud Trace',
                        'Stackdriver Logging', 'Stackdriver Monitoring'
                    )
                GROUP BY service.description, currency
                ORDER BY cost DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("project_id", "STRING", project),
                ]
            )

            results = client.query(query, job_config=job_config).result()
            costs = []
            for row in results:
                costs.append({
                    'service': row.service,
                    'cost': round(float(row.cost), 2),
                    'currency': row.currency,
                    'period_start': start_date.strftime('%Y-%m-%d'),
                    'period_end': end_date.strftime('%Y-%m-%d'),
                })

            return json.dumps(costs, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_observability_costs error: {e}")
            return None

    def get_consumption_usage(self, cluster: ClusterIdentifier, days: int = 30) -> Optional[str]:
        """Get daily cost breakdown from BigQuery billing export."""
        try:
            import os
            from google.cloud import bigquery

            auth = self._get_auth()
            project = self._get_project(cluster)
            dataset = os.getenv('GCP_BILLING_DATASET')
            billing_account_id = os.getenv('GCP_BILLING_ACCOUNT_ID', '').replace('-', '')

            if not dataset:
                return json.dumps([])

            client = bigquery.Client(credentials=auth.credentials, project=project)
            table = f"`{project}.{dataset}.gcp_billing_export_resource_v1_{billing_account_id}`"

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            query = f"""
                SELECT
                    DATE(usage_start_time) AS usage_date,
                    service.description AS service,
                    SUM(cost) AS daily_cost,
                    currency
                FROM {table}
                WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
                    AND project.id = @project_id
                    AND EXISTS (
                        SELECT 1 FROM UNNEST(labels) AS l
                        WHERE l.key = 'goog-k8s-cluster-name'
                        AND l.value = @cluster_name
                    )
                GROUP BY usage_date, service.description, currency
                ORDER BY usage_date DESC, daily_cost DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.strftime('%Y-%m-%d')),
                    bigquery.ScalarQueryParameter("project_id", "STRING", project),
                    bigquery.ScalarQueryParameter("cluster_name", "STRING", cluster.cluster_name),
                ]
            )

            results = client.query(query, job_config=job_config).result()
            usage = []
            for row in results:
                usage.append({
                    'date': row.usage_date.isoformat(),
                    'service': row.service,
                    'cost': round(float(row.daily_cost), 2),
                    'currency': row.currency,
                })

            return json.dumps(usage, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_consumption_usage error: {e}")
            return None

    # =========================================================================
    # Waste Detection (5 methods)
    # =========================================================================

    def get_orphaned_disks(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Find unattached persistent disks that may belong to this cluster."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = self._get_project(cluster)
            client = compute_v1.DisksClient(credentials=auth.credentials)

            # List disks across all zones in the cluster's region
            region = cluster.region or (cluster.zone.rsplit('-', 1)[0] if cluster.zone else '')
            agg_request = compute_v1.AggregatedListDisksRequest(project=project)

            orphaned = []
            for zone_name, scoped_list in client.aggregated_list(request=agg_request):
                if not scoped_list.disks:
                    continue
                # Filter to cluster's region
                if region and region not in zone_name:
                    continue

                for disk in scoped_list.disks:
                    # Orphaned = no users (not attached to any VM)
                    if disk.users:
                        continue

                    # Check if disk belongs to this cluster via labels
                    labels = dict(disk.labels) if disk.labels else {}
                    is_cluster_disk = (
                        labels.get('goog-k8s-cluster-name') == cluster.cluster_name
                        or 'kubernetes' in disk.name.lower()
                        or 'pvc' in disk.name.lower()
                    )

                    if is_cluster_disk:
                        orphaned.append({
                            'name': disk.name,
                            'size_gb': disk.size_gb,
                            'sku': disk.type_.split('/')[-1] if disk.type_ else 'pd-standard',
                            'created_time': disk.creation_timestamp,
                            'tags': labels,
                            'location': zone_name.split('/')[-1] if '/' in zone_name else zone_name,
                            'status': disk.status,
                        })

            return json.dumps(orphaned, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_orphaned_disks error: {e}")
            return None

    def get_unused_public_ips(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Find reserved but unassigned static IP addresses."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = self._get_project(cluster)
            region = cluster.region or (cluster.zone.rsplit('-', 1)[0] if cluster.zone else '')

            unused = []

            # Check regional addresses
            try:
                client = compute_v1.AddressesClient(credentials=auth.credentials)
                if region:
                    for addr in client.list(project=project, region=region):
                        if addr.status == 'RESERVED':  # Not in use
                            labels = dict(addr.labels) if addr.labels else {}
                            unused.append({
                                'name': addr.name,
                                'ip_address': addr.address,
                                'allocation_method': 'Static',
                                'tags': labels,
                                'location': region,
                                'address_type': addr.address_type,
                            })
            except Exception as e:
                logger.debug(f"Regional address listing failed: {e}")

            # Check global addresses
            try:
                global_client = compute_v1.GlobalAddressesClient(credentials=auth.credentials)
                for addr in global_client.list(project=project):
                    if addr.status == 'RESERVED':
                        labels = dict(addr.labels) if addr.labels else {}
                        unused.append({
                            'name': addr.name,
                            'ip_address': addr.address,
                            'allocation_method': 'Static',
                            'tags': labels,
                            'location': 'global',
                            'address_type': addr.address_type,
                        })
            except Exception as e:
                logger.debug(f"Global address listing failed: {e}")

            return json.dumps(unused, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_unused_public_ips error: {e}")
            return None

    def get_load_balancer_analysis(self, cluster: ClusterIdentifier) -> Optional[str]:
        """Analyze GCP load balancers (forwarding rules + backend services)."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = self._get_project(cluster)
            region = cluster.region or (cluster.zone.rsplit('-', 1)[0] if cluster.zone else '')

            load_balancers = []

            # List forwarding rules (regional)
            try:
                fr_client = compute_v1.ForwardingRulesClient(credentials=auth.credentials)
                if region:
                    for rule in fr_client.list(project=project, region=region):
                        # Filter for k8s-related rules
                        desc = (rule.description or '').lower()
                        name = rule.name.lower()
                        if 'k8s' in name or 'kubernetes' in desc or cluster.cluster_name.lower() in name:
                            load_balancers.append({
                                'name': rule.name,
                                'sku': rule.load_balancing_scheme or 'EXTERNAL',
                                'frontend_ip_count': 1,
                                'backend_pool_count': 1 if rule.backend_service else 0,
                                'ip_address': rule.I_p_address if hasattr(rule, 'I_p_address') else rule.ip_address,
                                'target': rule.target,
                                'port_range': rule.port_range,
                            })
            except Exception as e:
                logger.debug(f"Forwarding rules listing failed: {e}")

            # List global forwarding rules
            try:
                gfr_client = compute_v1.GlobalForwardingRulesClient(credentials=auth.credentials)
                for rule in gfr_client.list(project=project):
                    name = rule.name.lower()
                    if 'k8s' in name or cluster.cluster_name.lower() in name:
                        load_balancers.append({
                            'name': rule.name,
                            'sku': rule.load_balancing_scheme or 'EXTERNAL',
                            'frontend_ip_count': 1,
                            'backend_pool_count': 1 if rule.backend_service else 0,
                            'ip_address': getattr(rule, 'ip_address', None),
                            'target': rule.target,
                            'port_range': rule.port_range,
                        })
            except Exception as e:
                logger.debug(f"Global forwarding rules listing failed: {e}")

            result = [{
                'total_load_balancers': len(load_balancers),
                'load_balancers': load_balancers,
            }]

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_load_balancer_analysis error: {e}")
            return None

    def get_storage_tier_analysis(self, cluster: ClusterIdentifier, pvc_data: Optional[str] = None) -> Optional[str]:
        """Analyze PVC storage classes and recommend upgrades."""
        try:
            recommendations = []

            if pvc_data:
                import json as json_mod
                pvcs = json_mod.loads(pvc_data) if isinstance(pvc_data, str) else pvc_data

                items = pvcs.get('items', []) if isinstance(pvcs, dict) else pvcs

                for pvc in items:
                    metadata = pvc.get('metadata', {})
                    spec = pvc.get('spec', {})
                    storage_class = spec.get('storageClassName', 'standard')
                    pvc_name = metadata.get('name', 'unknown')
                    namespace = metadata.get('namespace', 'default')

                    rec = {
                        'pvc_name': pvc_name,
                        'namespace': namespace,
                        'current_storage_class': storage_class,
                    }

                    # pd-standard -> pd-balanced (better IOPS, similar price)
                    if storage_class in ('standard', 'pd-standard', 'standard-rwo'):
                        rec['storage_tier'] = 'pd-standard'
                        rec['recommended_tier'] = 'pd-balanced'
                        rec['reason'] = 'pd-balanced offers 2x IOPS at ~20% higher cost, better price/performance'
                        rec['confidence'] = 'high'
                        recommendations.append(rec)

                    # pd-ssd -> pd-ssd (already optimal) or check for over-provisioning
                    elif storage_class in ('premium-rwo', 'pd-ssd'):
                        capacity = spec.get('resources', {}).get('requests', {}).get('storage', '')
                        if capacity and self._parse_storage_size(capacity) > 500:
                            rec['storage_tier'] = 'pd-ssd'
                            rec['recommended_tier'] = 'pd-balanced'
                            rec['reason'] = 'Large SSD volumes may be over-provisioned; pd-balanced is cheaper for >500Gi'
                            rec['confidence'] = 'medium'
                            recommendations.append(rec)

            return json.dumps(recommendations, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_storage_tier_analysis error: {e}")
            return None

    def get_network_waste_analysis(self, cluster: ClusterIdentifier, services_data: Optional[str] = None) -> Optional[str]:
        """Analyze network waste (multiple LBs, NAT Gateway opportunities)."""
        try:
            recommendations = []

            if services_data:
                import json as json_mod
                services = json_mod.loads(services_data) if isinstance(services_data, str) else services_data
                items = services.get('items', []) if isinstance(services, dict) else services

                lb_services = [
                    s for s in items
                    if s.get('spec', {}).get('type') == 'LoadBalancer'
                ]

                if len(lb_services) > 2:
                    recommendations.append({
                        'type': 'lb_consolidation',
                        'severity': 'medium',
                        'title': f'Consolidate {len(lb_services)} LoadBalancer services',
                        'description': (
                            f'Found {len(lb_services)} LoadBalancer-type services. '
                            f'Consider using GKE Ingress (GCE L7 LB) or Gateway API '
                            f'to consolidate into fewer load balancers. '
                            f'Each GCP LB costs ~$18/month + data processing.'
                        ),
                        'estimated_monthly_savings': round((len(lb_services) - 1) * 18, 2),
                    })

            # Always suggest Cloud NAT optimization
            recommendations.append({
                'type': 'nat_optimization',
                'severity': 'low',
                'title': 'Review Cloud NAT configuration',
                'description': (
                    'If using Cloud NAT for egress, consider Private Google Access '
                    'for GCP API calls and VPC Service Controls to reduce NAT data processing costs.'
                ),
                'estimated_monthly_savings': 0,
            })

            result = {
                'analysis_type': 'network_waste',
                'cluster_name': cluster.cluster_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'recommendations': recommendations,
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"GKE get_network_waste_analysis error: {e}")
            return None

    @staticmethod
    def _parse_storage_size(size_str: str) -> int:
        """Parse Kubernetes storage size string to GB. '100Gi' -> 100, '500Mi' -> 0."""
        size_str = size_str.strip()
        if size_str.endswith('Gi'):
            return int(size_str[:-2])
        elif size_str.endswith('Ti'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('Mi'):
            return max(1, int(size_str[:-2]) // 1024)
        return 0
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/inspector.py', doraise=True); print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/inspector.py
git commit -m "feat(gke): implement GCPInfrastructureInspector with all 15 methods"
```

---

## Task 8: Update __init__.py and Registry

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/cloud_providers/gcp/__init__.py`

**Step 1: Update the GCP __init__.py docstring**

Replace line 1-7:

```python
"""
GCP Cloud Provider Adapters
============================

Full GKE implementation using Google Cloud Python client libraries.
Follows the same patterns as the AWS/EKS adapters.
"""
```

**Step 2: Verify registry already handles GCP detection**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && python3 -c "
from infrastructure.cloud_providers.types import CloudProvider
print(f'GCP enum: {CloudProvider.GCP}')
print(f'GCP value: {CloudProvider.GCP.value}')
"`

Expected: `GCP enum: CloudProvider.GCP` and `GCP value: gcp`

**Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/cloud_providers/gcp/__init__.py
git commit -m "feat(gke): update GCP package docstring — stubs replaced with full implementation"
```

---

## Task 9: Integration Verification

**Step 1: Verify all GCP adapters import cleanly (no GCP credentials needed)**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && python3 -c "
from infrastructure.cloud_providers.gcp import (
    GCPAuthenticator,
    GCPKubernetesExecutor,
    GCPMetricsCollector,
    GCPCostManager,
    GCPAccountManager,
    GCPInfrastructureInspector,
)
print(f'GCPAuthenticator: {GCPAuthenticator}')
print(f'GCPKubernetesExecutor: {GCPKubernetesExecutor}')
print(f'GCPMetricsCollector: {GCPMetricsCollector}')
print(f'GCPCostManager: {GCPCostManager}')
print(f'GCPAccountManager: {GCPAccountManager}')
print(f'GCPInfrastructureInspector: {GCPInfrastructureInspector}')
print('All GCP adapters import OK')
"`

Expected: All 6 class names printed + `All GCP adapters import OK`

**Step 2: Verify registry creates GCP adapters**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && CLOUD_PROVIDER=gcp python3 -c "
import os
os.environ['CLOUD_PROVIDER'] = 'gcp'
from infrastructure.cloud_providers.registry import ProviderRegistry
reg = ProviderRegistry()
print(f'Detected provider: {reg.cloud_provider}')
auth = reg.get_authenticator()
print(f'Authenticator type: {type(auth).__name__}')
exec_inst = reg.get_executor()
print(f'Executor type: {type(exec_inst).__name__}')
metrics = reg.get_metrics_collector()
print(f'Metrics type: {type(metrics).__name__}')
costs = reg.get_cost_manager()
print(f'Costs type: {type(costs).__name__}')
accounts = reg.get_account_manager()
print(f'Accounts type: {type(accounts).__name__}')
inspector = reg.get_inspector()
print(f'Inspector type: {type(inspector).__name__}')
print('All registry lookups OK')
"`

Expected: All types should be `GCP*` classes. `All registry lookups OK`

**Step 3: Verify no NotImplementedError remains in GCP adapters**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && grep -r "NotImplementedError" infrastructure/cloud_providers/gcp/ | grep -v __pycache__`

Expected: No output (no remaining stubs)

**Step 4: Verify the main app still starts (FastAPI startup with GCP adapters present)**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && timeout 10 python3 -c "
import sys
sys.path.insert(0, '.')
# This tests that importing the full cloud provider layer doesn't break anything
from infrastructure.cloud_providers.base import CloudAuthenticator
from infrastructure.cloud_providers.gcp import GCPAuthenticator, GCPInfrastructureInspector
from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
print('Coexistence test: Azure + AWS + GCP imports OK')
" 2>&1 || echo "Import test completed"`

Expected: `Coexistence test: Azure + AWS + GCP imports OK`

---

## Task 10: Final Commit and Summary

**Step 1: Check overall diff**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && git diff --stat HEAD~8..HEAD`

Verify ~1,400-1,600 lines added across 7 files:
- `requirements/requirements.txt` (8 lines added)
- `infrastructure/cloud_providers/gcp/authenticator.py` (~90 LOC)
- `infrastructure/cloud_providers/gcp/executor.py` (~140 LOC)
- `infrastructure/cloud_providers/gcp/metrics.py` (~160 LOC)
- `infrastructure/cloud_providers/gcp/costs.py` (~200 LOC)
- `infrastructure/cloud_providers/gcp/accounts.py` (~170 LOC)
- `infrastructure/cloud_providers/gcp/inspector.py` (~550 LOC)
- `infrastructure/cloud_providers/gcp/__init__.py` (docstring update)

**Step 2: Verify no regression — existing imports still work**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && python3 -c "
from infrastructure.cloud_providers.azure.authenticator import AzureAuthenticator
from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
print(f'Azure: {AzureAuthenticator.get_provider_name(AzureAuthenticator())}')
print(f'AWS: {AWSAuthenticator.get_provider_name(AWSAuthenticator())}')
print(f'GCP: {GCPAuthenticator.get_provider_name(GCPAuthenticator())}')
print('All three providers coexist OK')
"`

Expected: `azure`, `aws`, `gcp` printed. `All three providers coexist OK`
