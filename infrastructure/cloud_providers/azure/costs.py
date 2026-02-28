"""
Azure Cost Adapter
===================

Delegates to EnhancedAKSCostProcessor and VMPricingService.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudCostManager
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)


class AzureCostAdapter(CloudCostManager):
    """Wraps Azure cost processing for the CloudCostManager interface."""

    def get_cluster_costs(
        self,
        cluster: ClusterIdentifier,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Dict[str, Any]]:
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager

            cost_client = azure_sdk_manager.get_cost_client(cluster.subscription_id)
            if not cost_client:
                return None

            # Build scope for cost query
            scope = (
                f"/subscriptions/{cluster.subscription_id}"
                f"/resourceGroups/{cluster.resource_group}"
            )

            from azure.mgmt.costmanagement.models import (
                QueryDefinition,
                QueryTimePeriod,
                QueryDataset,
                QueryAggregation,
                QueryGrouping,
            )

            query = QueryDefinition(
                type="ActualCost",
                timeframe="Custom",
                time_period=QueryTimePeriod(
                    from_property=start_date,
                    to=end_date,
                ),
                dataset=QueryDataset(
                    granularity="Daily",
                    aggregation={
                        "totalCost": QueryAggregation(name="Cost", function="Sum"),
                    },
                    grouping=[
                        QueryGrouping(type="Dimension", name="ResourceType"),
                    ],
                ),
            )

            result = cost_client.query.usage(scope=scope, parameters=query)

            # Process with EnhancedAKSCostProcessor
            from infrastructure.persistence.processing.cost_processor import EnhancedAKSCostProcessor
            processor = EnhancedAKSCostProcessor()

            rows = result.rows if hasattr(result, 'rows') else []
            columns = [c.name for c in result.columns] if hasattr(result, 'columns') else []

            total_cost = sum(row[0] for row in rows) if rows else 0.0

            return {
                'total_cost': round(total_cost, 2),
                'currency': 'USD',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'provider': 'azure',
                'raw_rows': rows,
                'columns': columns,
            }

        except Exception as e:
            logger.error(f"Failed to get cluster costs for {cluster.cluster_name}: {e}")
            return None

    def get_vm_pricing(
        self,
        region: str,
        vm_sizes: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            from infrastructure.services.vm_pricing_service import VMPricingService
            service = VMPricingService()
            all_prices = service.get_vm_prices(region)

            if all_prices is None:
                return None

            pricing = {}
            for vm in all_prices:
                vm_size = vm.get('vm_size', '')
                if vm_sizes and vm_size not in vm_sizes:
                    continue
                pricing[vm_size] = {
                    'hourly_cost': vm.get('cost_per_hour', 0),
                    'monthly_cost': vm.get('cost_per_hour', 0) * 730,
                    'cpu_cores': vm.get('cpu_cores', 0),
                    'memory_gb': vm.get('memory_gb', 0),
                }

            return pricing

        except Exception as e:
            logger.error(f"Failed to get VM pricing for region {region}: {e}")
            return None

    def estimate_savings(
        self,
        cluster: ClusterIdentifier,
        recommendations: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        total_savings = 0.0
        breakdown = {}

        for rec in recommendations:
            category = rec.get('category', 'other')
            savings = rec.get('savings_estimate', 0.0)
            total_savings += savings
            breakdown[category] = breakdown.get(category, 0.0) + savings

        return {
            'total_monthly_savings': round(total_savings, 2),
            'currency': 'USD',
            'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        }
