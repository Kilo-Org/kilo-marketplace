#!/usr/bin/env python3
"""
GCP Pricing API Helper

Query and parse GCP Cloud Billing API for SKU pricing information.
Handles SKU filtering, region matching, and price conversion.
"""

import json
import sys
import urllib.request
import urllib.parse
from typing import Optional

# GCP Compute Engine Service ID
COMPUTE_SERVICE_ID = "6F81-5844-456A"

BASE_URL = "https://cloudbilling.googleapis.com/v1"


def query_skus(service_id: str, api_key: str, currency: str = "USD", page_size: int = 5000) -> dict:
    """Query all SKUs for a given service."""
    base_url = f"{BASE_URL}/services/{service_id}/skus?currencyCode={currency}&pageSize={page_size}&key={api_key}"
    skus = []
    page_token = ""
    
    while True:
        url = base_url
        if page_token:
            url += f"&pageToken={page_token}"
            
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            skus.extend(data.get("skus", []))
            
            page_token = data.get("nextPageToken")
            if not page_token:
                break
                
    return {"skus": skus}


def filter_skus_by_region(skus: list, region: str) -> list:
    """Filter SKUs that are available in the specified region."""
    return [
        sku for sku in skus
        if any(region in r for r in sku.get("serviceRegions", []))
    ]


def filter_skus_by_description(skus: list, pattern: str, case_sensitive: bool = False) -> list:
    """Filter SKUs by description pattern (regex supported)."""
    import re
    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, flags)

    return [
        sku for sku in skus
        if regex.search(sku.get("description", ""))
    ]


def convert_price_to_dollars(units: str, nanos: int) -> float:
    """Convert GCP pricing units/nanos to dollar amount.

    GCP returns pricing as:
    - units: whole dollar amount (as string)
    - nanos: fractional dollars in nanoseconds (1 nanos = $0.000000001)

    Example: units="0", nanos=50577600 -> $0.0505776
    """
    return int(units) + (nanos / 1_000_000_000)


def extract_sku_pricing(sku: dict) -> Optional[dict]:
    """Extract pricing information from a SKU."""
    pricing_info = sku.get("pricingInfo", [])
    if not pricing_info:
        return None

    tiered_rates = pricing_info[0].get("pricingExpression", {}).get("tieredRates", [])
    if not tiered_rates:
        return None

    unit_price = tiered_rates[0].get("unitPrice", {})
    units = unit_price.get("units", "0")
    nanos = unit_price.get("nanos", 0)

    return {
        "description": sku.get("description"),
        "sku_id": sku.get("skuId"),
        "regions": sku.get("serviceRegions", []),
        "units": units,
        "nanos": nanos,
        "price_per_unit": convert_price_to_dollars(units, nanos),
        "usage_unit": pricing_info[0].get("pricingExpression", {}).get("usageUnitDescription"),
    }


def find_instance_pricing(
    api_key: str,
    region: str,
    instance_family: str = "N2",
    service_id: str = COMPUTE_SERVICE_ID
) -> dict:
    """Find core and RAM pricing for an instance family in a region.

    Args:
        api_key: GCP API key
        region: Region code (e.g., "us-central1")
        instance_family: Instance family (e.g., "N2", "E2", "C2")
        service_id: GCP service ID (default: Compute Engine)

    Returns:
        Dict with core_price, ram_price, and metadata
    """
    data = query_skus(service_id, api_key)
    skus = data.get("skus", [])

    # Filter by region
    region_skus = filter_skus_by_region(skus, region)

    # Find core pricing
    core_pattern = rf"{instance_family}.*Instance.*Core"
    core_skus = filter_skus_by_description(region_skus, core_pattern)

    # Find RAM pricing
    ram_pattern = rf"{instance_family}.*Instance.*Ram"
    ram_skus = filter_skus_by_description(region_skus, ram_pattern)

    result = {
        "region": region,
        "instance_family": instance_family,
        "core": None,
        "ram": None,
        "available_skus": [extract_sku_pricing(s) for s in region_skus
                          if instance_family.lower() in s.get("description", "").lower()]
    }

    if core_skus:
        result["core"] = extract_sku_pricing(core_skus[0])

    if ram_skus:
        result["ram"] = extract_sku_pricing(ram_skus[0])

    return result


def calculate_instance_cost(
    api_key: str,
    region: str,
    instance_family: str,
    vcpus: int,
    memory_gb: float,
    hours_per_month: float = 730
) -> dict:
    """Calculate monthly cost for an instance configuration.

    Args:
        api_key: GCP API key
        region: Region code
        instance_family: Instance family (N2, E2, etc.)
        vcpus: Number of vCPUs
        memory_gb: Memory in GB
        hours_per_month: Hours per month (default: 730)

    Returns:
        Cost breakdown with hourly and monthly estimates
    """
    pricing = find_instance_pricing(api_key, region, instance_family)

    if not pricing["core"] or not pricing["ram"]:
        return {
            "error": f"Could not find pricing for {instance_family} in {region}",
            "available_skus": pricing.get("available_skus", [])
        }

    core_price = pricing["core"]["price_per_unit"]
    ram_price = pricing["ram"]["price_per_unit"]

    hourly_core = core_price * vcpus
    hourly_ram = ram_price * memory_gb
    hourly_total = hourly_core + hourly_ram

    return {
        "region": region,
        "instance_family": instance_family,
        "configuration": {
            "vcpus": vcpus,
            "memory_gb": memory_gb,
        },
        "pricing": {
            "core_per_hour": core_price,
            "ram_per_gib_hour": ram_price,
        },
        "costs": {
            "hourly": {
                "core": hourly_core,
                "ram": hourly_ram,
                "total": hourly_total,
            },
            "monthly": {
                "core": hourly_core * hours_per_month,
                "ram": hourly_ram * hours_per_month,
                "total": hourly_total * hours_per_month,
            }
        }
    }


def main():
    if len(sys.argv) < 4:
        print("Usage: python gcp_pricing.py <api_key> <region> <instance_family> [vcpus] [memory_gb]")
        print("\nExamples:")
        print('  python gcp_pricing.py YOUR_KEY us-central1 N2')
        print('  python gcp_pricing.py YOUR_KEY us-central1 N2 4 16')
        sys.exit(1)

    api_key = sys.argv[1]
    region = sys.argv[2]
    instance_family = sys.argv[3]

    if len(sys.argv) >= 6:
        vcpus = int(sys.argv[4])
        memory_gb = float(sys.argv[5])
        result = calculate_instance_cost(api_key, region, instance_family, vcpus, memory_gb)
    else:
        result = find_instance_pricing(api_key, region, instance_family)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
