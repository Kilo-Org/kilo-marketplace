#!/usr/bin/env python3
"""
Azure Retail Prices API Helper

Query and parse Azure Retail Prices API for SKU pricing information.
Handles pagination, filtering, and price extraction.
"""

import json
import sys
import urllib.request
import urllib.parse
from typing import List, Optional

BASE_URL = "https://prices.azure.com/api/retail/prices"


def query_prices(filter_query: str) -> List[dict]:
    """Query Azure Retail Prices API with pagination handling.

    Args:
        filter_query: OData filter string

    Returns:
        List of price items
    """
    all_items = []
    url = f"{BASE_URL}?$filter={urllib.parse.quote(filter_query)}"

    while url:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            all_items.extend(data.get("Items", []))
            url = data.get("NextPageLink")

    return all_items


def get_vm_prices(
    region: str,
    vm_series: Optional[str] = None,
    sku_pattern: Optional[str] = None
) -> List[dict]:
    """Get VM pricing for a region.

    Args:
        region: Azure region code (e.g., "eastus")
        vm_series: VM series filter (e.g., "D", "E", "F")
        sku_pattern: Specific SKU pattern to match

    Returns:
        List of VM pricing items
    """
    filters = [f"serviceName eq 'Virtual Machines'", f"armRegionName eq '{region}'"]

    if vm_series:
        filters.append(f"contains(skuName, '{vm_series}')")

    if sku_pattern:
        filters.append(f"contains(skuName, '{sku_pattern}')")

    filter_query = " and ".join(filters)
    items = query_prices(filter_query)

    # Extract relevant fields
    return [
        {
            "product_name": item.get("productName"),
            "sku_name": item.get("skuName"),
            "retail_price": item.get("retailPrice"),
            "unit_of_measure": item.get("unitOfMeasure"),
            "service_family": item.get("serviceFamily"),
            "meter_name": item.get("meterName"),
            "type": item.get("type"),  # Consumption, Reservation, etc.
        }
        for item in items
    ]


def get_storage_prices(region: str, storage_type: Optional[str] = None) -> List[dict]:
    """Get storage pricing for a region.

    Args:
        region: Azure region code
        storage_type: Storage type filter (e.g., "Standard_LRS")

    Returns:
        List of storage pricing items
    """
    filters = [f"serviceFamily eq 'Storage'", f"armRegionName eq '{region}'"]

    if storage_type:
        filters.append(f"contains(productName, '{storage_type}')")

    filter_query = " and ".join(filters)
    items = query_prices(filter_query)

    return [
        {
            "product_name": item.get("productName"),
            "sku_name": item.get("skuName"),
            "retail_price": item.get("retailPrice"),
            "unit_of_measure": item.get("unitOfMeasure"),
            "meter_name": item.get("meterName"),
        }
        for item in items
    ]


def calculate_vm_cost(
    region: str,
    sku_name: str,
    hours_per_month: float = 730,
    quantity: int = 1
) -> Optional[dict]:
    """Calculate monthly cost for a specific VM SKU.

    Args:
        region: Azure region code
        sku_name: VM SKU name (e.g., "D2s_v5")
        hours_per_month: Hours per month
        quantity: Number of instances

    Returns:
        Cost breakdown or None if SKU not found
    """
    items = get_vm_prices(region, sku_pattern=sku_name)

    # Filter to exact SKU match
    matching = [i for i in items if sku_name.lower() in i["sku_name"].lower()]

    if not matching:
        return None

    # Get consumption (pay-as-you-go) price
    consumption_items = [i for i in matching if "Consumption" in i.get("type", "")]
    item = consumption_items[0] if consumption_items else matching[0]

    hourly_price = item["retail_price"]
    monthly_price = hourly_price * hours_per_month * quantity

    return {
        "region": region,
        "sku": sku_name,
        "quantity": quantity,
        "hourly_price": hourly_price,
        "monthly_price": monthly_price,
        "annual_estimate": monthly_price * 12,
        "unit": item.get("unit_of_measure"),
        "product_name": item.get("product_name"),
    }


def compare_regions(sku_name: str, regions: List[str]) -> dict:
    """Compare pricing for a SKU across multiple regions.

    Args:
        sku_name: VM SKU name
        regions: List of region codes

    Returns:
        Comparison results
    """
    results = {}

    for region in regions:
        cost = calculate_vm_cost(region, sku_name)
        if cost:
            results[region] = cost
        else:
            results[region] = {"error": "SKU not found in region"}

    return {
        "sku": sku_name,
        "comparisons": results,
        "cheapest": min(
            ((r, c["monthly_price"]) for r, c in results.items() if "monthly_price" in c),
            key=lambda x: x[1],
            default=None
        )
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python azure_pricing.py <command> [args...]")
        print("\nCommands:")
        print("  vm-prices <region> [series]     - List VM prices in region")
        print("  calculate <region> <sku>        - Calculate cost for SKU")
        print("  compare <sku> <region1> <region2>... - Compare across regions")
        print("\nExamples:")
        print('  python azure_pricing.py vm-prices eastus D')
        print('  python azure_pricing.py calculate eastus D2s_v5')
        print('  python azure_pricing.py compare D2s_v5 eastus westus northeurope')
        sys.exit(1)

    command = sys.argv[1]

    if command == "vm-prices":
        if len(sys.argv) < 3:
            print("Usage: python azure_pricing.py vm-prices <region> [series]")
            sys.exit(1)

        region = sys.argv[2]
        series = sys.argv[3] if len(sys.argv) > 3 else None

        prices = get_vm_prices(region, vm_series=series)
        print(json.dumps(prices, indent=2))

    elif command == "calculate":
        if len(sys.argv) < 4:
            print("Usage: python azure_pricing.py calculate <region> <sku>")
            sys.exit(1)

        region = sys.argv[2]
        sku = sys.argv[3]

        result = calculate_vm_cost(region, sku)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"error": f"SKU {sku} not found in {region}"}, indent=2))

    elif command == "compare":
        if len(sys.argv) < 4:
            print("Usage: python azure_pricing.py compare <sku> <region1> <region2>...")
            sys.exit(1)

        sku = sys.argv[2]
        regions = sys.argv[3:]

        result = compare_regions(sku, regions)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
