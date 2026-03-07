# GKE Support Design

## Overview

Implement full GKE (Google Kubernetes Engine) support across all 6 cloud provider adapter interfaces, achieving feature parity with the existing EKS implementation. ~1,440 LOC across 6 files in `infrastructure/cloud_providers/gcp/`.

## Decision Record

- **Approach**: Full parity with EKS (all 30 methods implemented)
- **Cost strategy**: BigQuery billing export (label-filtered, standard GCP practice)
- **kubectl execution**: subprocess (assumes `gcloud container clusters get-credentials`)
- **Auth**: `google.auth.default()` credential chain with class-level singleton caching

## GCP Python Dependencies

```
google-auth
google-cloud-container       # GKE cluster/nodepool API
google-cloud-compute         # VMs, disks, IPs, LBs
google-cloud-monitoring      # Cloud Monitoring metrics
google-cloud-billing         # Billing Catalog API (pricing)
google-cloud-bigquery        # Cost analysis via billing export
google-cloud-logging         # Cloud Logging
google-cloud-resource-manager # Project discovery
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes* | Path to service account JSON (*or use gcloud auth) |
| `GOOGLE_CLOUD_PROJECT` | No | Default project (auto-detected from credentials) |
| `GCP_BILLING_DATASET` | For costs | BigQuery dataset with billing export |
| `GCP_BILLING_ACCOUNT_ID` | For costs | Billing account ID for export table name |
| `GKE_LOCATIONS` | No | Comma-separated locations to scan (default: all) |

## Adapter Designs

### 1. GCPAuthenticator (~90 LOC)

Credential chain via `google.auth.default()`:
1. `GOOGLE_APPLICATION_CREDENTIALS` env var (service account JSON)
2. gcloud CLI auth (`gcloud auth application-default login`)
3. GCE metadata server (when running on GCP)

- `authenticate()`: `google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])`, validate via ResourceManager
- Cache: `_credentials`, `_project_id`, `_authenticated`
- Class-level singleton pattern (same as AWSAuthenticator, bypasses ProviderRegistry)

### 2. GCPKubernetesExecutor (~130 LOC)

- `execute_kubectl()`: `subprocess.run()` (assumes `gcloud container clusters get-credentials` already run)
- `execute_managed_command()`: Intercept GKE SDK commands, fallback to kubectl
  - `describe-cluster` -> `ClusterManagerClient.get_cluster()`
  - `list-nodepools` -> `ClusterManagerClient.list_node_pools()`
  - `describe-nodepool` -> `ClusterManagerClient.get_node_pool()`
- `test_connectivity()`: `kubectl version --client=false`
- GKE cluster path: `projects/{project}/locations/{location}/clusters/{name}`

### 3. GCPMetricsCollector (~170 LOC)

- `get_node_metrics()`: `kubectl top nodes --no-headers` (same as AWS)
- `get_cluster_info()`: GKE `get_cluster()` mapped to standard schema
- `get_metric_data()`: Cloud Monitoring API
  - Resource type: `k8s_cluster` or `k8s_node`
  - Metric namespace: `kubernetes.io/`
  - Filter: `resource.labels.cluster_name = "{cluster}"`

### 4. GCPCostManager (~300 LOC)

- `get_cluster_costs()`: BigQuery billing export query
  ```sql
  SELECT service.description, SUM(cost) as total_cost
  FROM `{project}.{dataset}.gcp_billing_export_v1_{billing_account_id}`
  WHERE DATE(usage_start_time) BETWEEN @start AND @end
    AND labels.key = 'goog-k8s-cluster-name' AND labels.value = @cluster
  GROUP BY service.description
  ```
- `get_vm_pricing()`: Compute Engine `machine_types().list()` + Cloud Billing Catalog API
- `estimate_savings()`: Sum recommendation savings (same pattern as AWS)

### 5. GCPAccountManager (~200 LOC)

- `list_accounts()`: `ResourceManagerClient.search_projects()`
- `discover_clusters()`: `ClusterManagerClient.list_clusters(parent="projects/{p}/locations/-")` (wildcard = all locations in one call)
- `validate_cluster_access()`: `get_cluster()` success check
- `find_cluster_account()`: Scan accessible projects
- `execute_with_account_context()`: Pass-through (like AWS)

### 6. GCPInfrastructureInspector (~550 LOC)

**Cluster metadata (6 methods)**:
- Map GKE node pools to `agent_pool_profiles` schema:
  - `machineType` -> `vm_size`
  - `initialNodeCount` -> `count`
  - `autoscaling.enabled` -> `enable_auto_scaling`
  - `autoscaling.minNodeCount/maxNodeCount` -> `min_count/max_count`
  - Preemptible/Spot -> `scale_set_priority`

**Observability (4 methods)**:
- Cloud Logging sinks for cluster
- GKE monitoring add-ons (Managed Prometheus, etc.)
- Observability costs via BigQuery
- Daily consumption breakdown

**Waste detection (5 methods)**:
- Orphaned disks: `compute.disks().list()` + status=READY, no users
- Unused IPs: `compute.addresses().list()` + status=RESERVED
- Load balancers: forwarding rules + backend services
- Storage tiers: pd-standard -> pd-balanced/pd-ssd recommendations
- Network: multiple LoadBalancer services -> GKE Ingress consolidation

## Schema Normalization

GKE data must normalize to the same field names used by analysis_engine:

| GKE Field | Normalized Field |
|-----------|-----------------|
| `machineType` | `vm_size` |
| `initialNodeCount` | `count` |
| `autoscaling.minNodeCount` | `min_count` |
| `autoscaling.maxNodeCount` | `max_count` |
| `config.preemptible` / `config.spot` | `scale_set_priority` ('Spot' or 'Regular') |
| `config.imageType` | `os_type` |
| Node pool `name` | `name` |

## Integration Points

- **ProviderRegistry**: Auto-detects GCP from `GOOGLE_APPLICATION_CREDENTIALS` or `GOOGLE_CLOUD_PROJECT` env vars
- **Plan Generation**: Already has GKE config in `CLOUD_CONFIG` mapping
- **Standards**: `StandardsLoader` will try `gke_*` prefix, fall back to `aks_*` YAML files
- **Cache keys**: `gcp:{project_id}:{location}:{cluster_name}`
- **Cluster ID**: `{project_id}_{cluster_name}` (matches `ClusterIdentifier.unique_id`)

## Required GCP IAM Roles

```
roles/container.viewer        # GKE cluster/nodepool read
roles/compute.viewer          # VMs, disks, IPs, LBs
roles/monitoring.viewer       # Cloud Monitoring metrics
roles/logging.viewer          # Cloud Logging
roles/bigquery.dataViewer     # BigQuery billing export
roles/bigquery.jobUser        # Run BigQuery queries
roles/resourcemanager.projectViewer  # Project discovery
roles/billing.viewer          # Billing catalog (pricing)
```
