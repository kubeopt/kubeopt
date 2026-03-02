"""
AWS Cost Manager — Cost Explorer + Pricing API
=================================================

Cost Explorer for cluster cost breakdown (tag-filtered).
Pricing API for EC2 instance prices (On-Demand, region-mapped).
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from infrastructure.cloud_providers.base import CloudCostManager
from infrastructure.cloud_providers.types import ClusterIdentifier

logger = logging.getLogger(__name__)

# AWS region code → Pricing API "location" name
_REGION_TO_LOCATION = {
    'us-east-1': 'US East (N. Virginia)',
    'us-east-2': 'US East (Ohio)',
    'us-west-1': 'US West (N. California)',
    'us-west-2': 'US West (Oregon)',
    'ca-central-1': 'Canada (Central)',
    'eu-west-1': 'EU (Ireland)',
    'eu-west-2': 'EU (London)',
    'eu-west-3': 'EU (Paris)',
    'eu-central-1': 'EU (Frankfurt)',
    'eu-north-1': 'EU (Stockholm)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'ap-northeast-2': 'Asia Pacific (Seoul)',
    'ap-northeast-3': 'Asia Pacific (Osaka)',
    'ap-south-1': 'Asia Pacific (Mumbai)',
    'sa-east-1': 'South America (Sao Paulo)',
    'me-south-1': 'Middle East (Bahrain)',
    'af-south-1': 'Africa (Cape Town)',
}


class AWSCostManager(CloudCostManager):
    """AWS cost analysis via Cost Explorer and Pricing API."""

    _auth_instance = None

    def _get_auth(self):
        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        if AWSCostManager._auth_instance is None or not AWSCostManager._auth_instance.is_authenticated():
            AWSCostManager._auth_instance = AWSAuthenticator()
            if not AWSCostManager._auth_instance.is_authenticated():
                raise RuntimeError("AWS authentication failed — set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return AWSCostManager._auth_instance

    def get_cluster_costs(
        self,
        cluster: ClusterIdentifier,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Dict[str, Any]]:
        try:
            auth = self._get_auth()
            # Cost Explorer endpoint is always us-east-1
            ce = auth.session.client('ce', region_name='us-east-1')

            # Try multiple EKS tag patterns — different provisioning tools set different tags
            tag_filters = [
                # eksctl / CloudFormation standard tag
                {'Key': f'kubernetes.io/cluster/{cluster.cluster_name}', 'Values': ['owned', 'shared']},
                # AWS-applied tag (EKS auto-tags some resources)
                {'Key': f'aws:eks:cluster-name', 'Values': [cluster.cluster_name]},
                # Common user-applied tag
                {'Key': 'eks:cluster-name', 'Values': [cluster.cluster_name]},
            ]

            for tag_filter in tag_filters:
                try:
                    result = self._query_cost_explorer(ce, tag_filter, start_date, end_date)
                    if result and result.get('total_cost', 0) > 0:
                        logger.info(f"✅ Cost Explorer data found using tag: {tag_filter['Key']}")
                        return result
                except Exception as tag_err:
                    logger.debug(f"Tag filter {tag_filter['Key']} failed: {tag_err}")
                    continue

            # All tag filters returned no data
            logger.warning(
                f"AWS Cost Explorer returned no data for {cluster.cluster_name} with any tag pattern. "
                f"Ensure cost allocation tags are activated in AWS Billing console "
                f"(kubernetes.io/cluster/{cluster.cluster_name} or aws:eks:cluster-name)."
            )
            return None

        except Exception as e:
            error_str = str(e)
            if 'BillingSetup' in error_str or 'OptIn' in error_str or 'not subscribed' in error_str.lower():
                logger.warning(f"Cost Explorer not enabled for this account: {e}")
            else:
                logger.error(f"Failed to get cluster costs for {cluster.cluster_name}: {e}")
            return None

    def _query_cost_explorer(
        self,
        ce_client,
        tag_filter: Dict,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Dict[str, Any]]:
        """Execute a single Cost Explorer query with one tag filter."""
        resp = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d'),
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            Filter={'Tags': tag_filter},
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
        )

        total_cost = 0.0
        breakdown = {}
        currency = 'USD'

        for result in resp.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                currency = group['Metrics']['UnblendedCost'].get('Unit', 'USD')
                total_cost += cost
                breakdown[service] = breakdown.get(service, 0) + cost

        if total_cost == 0:
            return None

        return {
            'total_cost': round(total_cost, 2),
            'currency': currency,
            'breakdown': {k: round(v, 2) for k, v in sorted(breakdown.items(), key=lambda x: -x[1])},
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
            },
        }

    def get_vm_pricing(
        self,
        region: str,
        vm_sizes: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            auth = self._get_auth()
            # Pricing API is only available in us-east-1
            pricing = auth.session.client('pricing', region_name='us-east-1')

            location = _REGION_TO_LOCATION.get(region)
            if not location:
                logger.warning(f"Unknown region mapping for {region}, using raw region name")
                location = region

            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
            ]

            results = {}

            if vm_sizes:
                # Query specific instance types
                for instance_type in vm_sizes:
                    price_info = self._get_instance_price(pricing, filters, instance_type)
                    if price_info:
                        results[instance_type] = price_info
            else:
                # Get a sample of common instance types
                for instance_type in ['m5.large', 'm5.xlarge', 'm5.2xlarge', 'c5.large', 'c5.xlarge', 'r5.large']:
                    price_info = self._get_instance_price(pricing, filters, instance_type)
                    if price_info:
                        results[instance_type] = price_info

            return results if results else None
        except Exception as e:
            logger.error(f"Failed to get EC2 pricing for {region}: {e}")
            return None

    def _get_instance_price(
        self,
        pricing_client,
        base_filters: list,
        instance_type: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            filters = base_filters + [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            ]
            resp = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters,
                MaxResults=1,
            )
            price_list = resp.get('PriceList', [])
            if not price_list:
                return None

            product = json.loads(price_list[0])
            attributes = product.get('product', {}).get('attributes', {})
            on_demand = product.get('terms', {}).get('OnDemand', {})

            hourly_cost = 0.0
            for term in on_demand.values():
                for dimension in term.get('priceDimensions', {}).values():
                    price_str = dimension.get('pricePerUnit', {}).get('USD', '0')
                    hourly_cost = float(price_str)
                    break

            return {
                'hourly_cost': hourly_cost,
                'monthly_cost': round(hourly_cost * 730, 2),
                'vcpus': attributes.get('vcpu', ''),
                'memory': attributes.get('memory', ''),
                'instance_family': attributes.get('instanceFamily', ''),
            }
        except Exception as e:
            logger.debug(f"Could not get price for {instance_type}: {e}")
            return None

    def estimate_savings(
        self,
        cluster: ClusterIdentifier,
        recommendations: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        try:
            total_monthly = 0.0
            breakdown = {}

            for rec in recommendations:
                category = rec.get('category', 'general')
                savings = rec.get('estimated_monthly_savings', 0)
                total_monthly += savings
                breakdown[category] = breakdown.get(category, 0) + savings

            return {
                'total_monthly_savings': round(total_monthly, 2),
                'total_annual_savings': round(total_monthly * 12, 2),
                'currency': 'USD',
                'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
            }
        except Exception as e:
            logger.error(f"Failed to estimate savings: {e}")
            return None
