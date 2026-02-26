#!/usr/bin/env python3
"""
Azure VM Pricing Service - Real-Time Pricing from Azure Retail Prices API
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Fetches real-time VM pricing from the free, unauthenticated Azure Retail Prices API.
Caches results per-region with a 24-hour TTL.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Azure Retail Prices API (free, no auth required)
AZURE_RETAIL_PRICES_URL = "https://prices.azure.com/api/retail/prices"

# VM naming convention: extract vCPU count from the numeric part of the series name
# Standard_D{n}s_v3 → n vCPUs, n×4 GB (general purpose)
# Standard_E{n}s_v3 → n vCPUs, n×8 GB (memory optimized)
# Standard_F{n}s_v2 → n vCPUs, n×2 GB (compute optimized)
# Standard_B{n}s    → n vCPUs, varies (burstable)
# Standard_B{n}ms   → n vCPUs, n×4 GB (burstable, more memory)
# Standard_L{n}s_v3 → n vCPUs, n×8 GB (storage optimized)

# Memory multiplier per VM series prefix
_SERIES_MEMORY_MULTIPLIER = {
    "D": 4,   # General purpose: n × 4 GB
    "E": 8,   # Memory optimized: n × 8 GB
    "F": 2,   # Compute optimized: n × 2 GB
    "L": 8,   # Storage optimized: n × 8 GB
    "M": 16,  # Memory intensive: varies, approximate
    "A": 2,   # Basic/general: n × 2 GB
}

# Burstable B-series has irregular memory - hardcode known sizes
_BURSTABLE_SPECS = {
    "B1s":   {"cpu_cores": 1, "memory_gb": 1},
    "B1ms":  {"cpu_cores": 1, "memory_gb": 2},
    "B1ls":  {"cpu_cores": 1, "memory_gb": 0.5},
    "B2s":   {"cpu_cores": 2, "memory_gb": 4},
    "B2ms":  {"cpu_cores": 2, "memory_gb": 8},
    "B2ts_v2": {"cpu_cores": 2, "memory_gb": 1},
    "B2ls_v2": {"cpu_cores": 2, "memory_gb": 4},
    "B2s_v2":  {"cpu_cores": 2, "memory_gb": 8},
    "B2als_v2": {"cpu_cores": 2, "memory_gb": 4},
    "B2as_v2":  {"cpu_cores": 2, "memory_gb": 8},
    "B4ms":  {"cpu_cores": 4, "memory_gb": 16},
    "B4ls_v2": {"cpu_cores": 4, "memory_gb": 8},
    "B4s_v2":  {"cpu_cores": 4, "memory_gb": 16},
    "B4als_v2": {"cpu_cores": 4, "memory_gb": 8},
    "B4as_v2":  {"cpu_cores": 4, "memory_gb": 16},
    "B8ms":  {"cpu_cores": 8, "memory_gb": 32},
    "B8ls_v2": {"cpu_cores": 8, "memory_gb": 16},
    "B8s_v2":  {"cpu_cores": 8, "memory_gb": 32},
    "B8als_v2": {"cpu_cores": 8, "memory_gb": 16},
    "B8as_v2":  {"cpu_cores": 8, "memory_gb": 32},
    "B12ms":  {"cpu_cores": 12, "memory_gb": 48},
    "B16ms":  {"cpu_cores": 16, "memory_gb": 64},
    "B16ls_v2": {"cpu_cores": 16, "memory_gb": 32},
    "B16s_v2":  {"cpu_cores": 16, "memory_gb": 64},
    "B16als_v2": {"cpu_cores": 16, "memory_gb": 32},
    "B16as_v2":  {"cpu_cores": 16, "memory_gb": 64},
    "B20ms":  {"cpu_cores": 20, "memory_gb": 80},
    "B32ls_v2": {"cpu_cores": 32, "memory_gb": 64},
    "B32s_v2":  {"cpu_cores": 32, "memory_gb": 128},
    "B32als_v2": {"cpu_cores": 32, "memory_gb": 64},
    "B32as_v2":  {"cpu_cores": 32, "memory_gb": 128},
}

# Regex to parse VM SKU names like "Standard_D2s_v3", "Standard_E4as_v5", "Standard_F8s_v2"
_VM_SKU_PATTERN = re.compile(
    r"Standard_([A-Z])(\d+)(.*)",
    re.IGNORECASE,
)


def _parse_vm_specs(sku_name: str) -> Optional[Dict]:
    """Extract cpu_cores and memory_gb from a VM SKU name using naming conventions.

    Returns dict with cpu_cores and memory_gb, or None if unparseable.
    """
    # Strip "Standard_" prefix for B-series lookup
    short_name = sku_name.replace("Standard_", "")
    if short_name in _BURSTABLE_SPECS:
        return dict(_BURSTABLE_SPECS[short_name])

    match = _VM_SKU_PATTERN.match(sku_name)
    if not match:
        return None

    series_letter = match.group(1).upper()
    try:
        vcpus = int(match.group(2))
    except (ValueError, TypeError):
        return None

    # B-series not in the hardcoded map: estimate with n×4 GB
    if series_letter == "B":
        return {"cpu_cores": vcpus, "memory_gb": vcpus * 4}

    multiplier = _SERIES_MEMORY_MULTIPLIER.get(series_letter)
    if multiplier is None:
        # Unknown series — estimate at n×4 GB (general purpose default)
        multiplier = 4

    return {"cpu_cores": vcpus, "memory_gb": vcpus * multiplier}


class VMPricingService:
    """Fetches real-time VM pricing from the Azure Retail Prices API.

    The API is free, unauthenticated, and region-aware.
    Results are cached in-memory per region with a 24-hour TTL.
    """

    _cache: Dict[str, List[Dict]] = {}
    _cache_timestamps: Dict[str, datetime] = {}
    CACHE_TTL_HOURS = 24
    REQUEST_TIMEOUT = 30  # seconds per API page request

    def get_vm_prices(self, region: str) -> List[Dict]:
        """Get all Linux VM pay-as-you-go prices for a region.

        Args:
            region: Azure region name (e.g. 'westeurope', 'eastus')

        Returns:
            List of dicts: [{vm_size, cost_per_hour, cpu_cores, memory_gb}, ...]
            Empty list if the API call fails.
        """
        if not region:
            return []

        # Normalize region name (remove spaces, lowercase)
        region = region.lower().replace(" ", "")

        # Check cache
        cached = self._get_from_cache(region)
        if cached is not None:
            return cached

        # Fetch from API
        try:
            prices = self._fetch_prices(region)
            if prices:
                self._put_in_cache(region, prices)
                logger.info(f"Fetched {len(prices)} VM prices for {region} from Azure Retail Prices API")
                return prices
            else:
                logger.warning(f"Azure Retail Prices API returned no VM prices for region '{region}'")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch VM prices from Azure Retail Prices API: {e}")
            return []

    def get_vm_price(self, region: str, sku_name: str) -> Optional[Dict]:
        """Get price info for a specific VM SKU in a region.

        Args:
            region: Azure region name
            sku_name: VM SKU name (e.g. 'Standard_D2s_v3')

        Returns:
            Dict with vm_size, cost_per_hour, cpu_cores, memory_gb or None
        """
        prices = self.get_vm_prices(region)
        for p in prices:
            if p["vm_size"].lower() == sku_name.lower():
                return p
        return None

    def _get_from_cache(self, region: str) -> Optional[List[Dict]]:
        """Return cached prices if present and not expired."""
        if region in self._cache and region in self._cache_timestamps:
            age = datetime.utcnow() - self._cache_timestamps[region]
            if age < timedelta(hours=self.CACHE_TTL_HOURS):
                logger.debug(f"VM pricing cache hit for region '{region}' (age: {age})")
                return self._cache[region]
            else:
                # Expired
                del self._cache[region]
                del self._cache_timestamps[region]
        return None

    def _put_in_cache(self, region: str, prices: List[Dict]):
        """Store prices in cache with current timestamp."""
        self._cache[region] = prices
        self._cache_timestamps[region] = datetime.utcnow()

    def _fetch_prices(self, region: str) -> List[Dict]:
        """Fetch VM prices from Azure Retail Prices API with pagination.

        Filters for:
        - serviceName eq 'Virtual Machines'
        - armRegionName eq '{region}'
        - priceType eq 'Consumption' (pay-as-you-go)
        - Excludes Spot and Low Priority meters
        """
        odata_filter = (
            f"serviceName eq 'Virtual Machines' "
            f"and armRegionName eq '{region}' "
            f"and priceType eq 'Consumption'"
        )

        all_items = []
        next_page_url = None
        page_count = 0
        max_pages = 50  # Safety limit to prevent runaway pagination

        url = AZURE_RETAIL_PRICES_URL
        params = {"$filter": odata_filter}

        while page_count < max_pages:
            page_count += 1

            try:
                if next_page_url:
                    response = requests.get(next_page_url, timeout=self.REQUEST_TIMEOUT)
                else:
                    response = requests.get(url, params=params, timeout=self.REQUEST_TIMEOUT)

                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                logger.error(f"Azure Retail Prices API request failed (page {page_count}): {e}")
                break

            items = data.get("Items", [])
            all_items.extend(items)

            next_page_url = data.get("NextPageLink")
            if not next_page_url:
                break

        # Filter and deduplicate
        return self._process_price_items(all_items)

    def _process_price_items(self, items: List[Dict]) -> List[Dict]:
        """Process raw API items into our standard format.

        Filters out:
        - Spot instances
        - Low Priority instances
        - Windows OS (keep only Linux)
        - Non-VM items

        Deduplicates by SKU name (keeps first/cheapest occurrence).
        """
        seen_skus = {}

        for item in items:
            meter_name = item.get("meterName", "")
            sku_name = item.get("armSkuName", "")
            retail_price = item.get("retailPrice", 0)
            product_name = item.get("productName", "")

            # Skip Spot and Low Priority
            if "Spot" in meter_name or "Low Priority" in meter_name:
                continue

            # Skip Windows (keep Linux only)
            if "Windows" in product_name:
                continue

            # Skip items with no SKU or zero price
            if not sku_name or retail_price <= 0:
                continue

            # Skip non-Standard VM SKUs
            if not sku_name.startswith("Standard_"):
                continue

            # Parse specs from naming convention
            specs = _parse_vm_specs(sku_name)
            if specs is None:
                continue

            # Deduplicate: keep lowest price per SKU
            if sku_name in seen_skus:
                if retail_price < seen_skus[sku_name]["cost_per_hour"]:
                    seen_skus[sku_name]["cost_per_hour"] = retail_price
            else:
                seen_skus[sku_name] = {
                    "vm_size": sku_name,
                    "cost_per_hour": retail_price,
                    "cpu_cores": specs["cpu_cores"],
                    "memory_gb": specs["memory_gb"],
                }

        # Sort by cost for easier consumption
        result = sorted(seen_skus.values(), key=lambda x: x["cost_per_hour"])
        return result
