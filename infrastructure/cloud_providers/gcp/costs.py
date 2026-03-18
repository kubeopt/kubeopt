"""GCP Cost Manager — BigQuery billing export + Cloud Billing Catalog API for pricing."""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudCostManager
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)

_bigquery_module = None

def _get_bigquery_client_module():
    """Import google.cloud.bigquery with OpenTelemetry workaround.

    Some environments have an opentelemetry-api version conflict that causes
    StopIteration during bigquery module import. This patches the context
    runtime before importing.
    """
    global _bigquery_module
    if _bigquery_module is not None:
        return _bigquery_module
    try:
        from google.cloud import bigquery
        _bigquery_module = bigquery
        return bigquery
    except StopIteration:
        logger.warning("OpenTelemetry context conflict — patching before BigQuery import")
        try:
            from opentelemetry.context.contextvars_context import ContextVarsRuntimeContext
            import opentelemetry.context as otel_ctx
            otel_ctx._RUNTIME_CONTEXT = ContextVarsRuntimeContext()
        except Exception:
            pass
        from google.cloud import bigquery
        _bigquery_module = bigquery
        return bigquery


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
            bigquery = _get_bigquery_client_module()

            auth = self._get_auth()
            project = cluster.project_id or auth.project_id

            dataset = os.getenv('GCP_BILLING_DATASET')
            billing_account_id = os.getenv('GCP_BILLING_ACCOUNT_ID', '').replace('-', '_')

            if not dataset:
                logger.warning("GCP_BILLING_DATASET not set. Cannot query costs.")
                return None

            client = bigquery.Client(credentials=auth.credentials, project=project)

            # BigQuery billing export table name format
            table = f"`{project}.{dataset}.gcp_billing_export_resource_v1_{billing_account_id}`"

            # GKE auto-labels clusters with goog-k8s-cluster-name
            query = f"""
                SELECT
                    service.description AS service_name,
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
                GROUP BY service_name, currency
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
                service_name = row.service_name
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
            logger.error(f"GKE cost query error: {type(e).__name__}: {e}", exc_info=True)
            return None

    def get_vm_pricing(self, region: str, vm_sizes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get GCE machine type pricing via Compute Engine API + fallback table."""
        try:
            from google.cloud import compute_v1

            auth = self._get_auth()
            project = auth.project_id
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
