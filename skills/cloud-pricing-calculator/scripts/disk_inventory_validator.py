#!/usr/bin/env python3
"""
Azure Disk Inventory Validator

Validates Azure managed disk inventory against Azure Retail Prices API.
Maps disk SKUs and sizes to pricing tiers, calculates monthly costs,
and flags unusual configurations.

Real-World Lessons Learned:
- Azure disk SKUs (Standard_LRS, Premium_LRS, etc.) don't directly map to
  pricing meter names (P1, P4, P10, E4, E10, S4, S10, etc.)
- Size ranges determine the pricing tier, not the exact disk size
- The API uses meterName like "P10 LRS Disk" or "E10 LRS Disk" for billing
- Always filter by isPrimaryMeterRegion to avoid duplicate entries
- Premium SSD v2 and Ultra SSD use different pricing models (per-GiB)
- Zone redundancy (ZRS) has different meter names than LRS

Usage:
    python disk_inventory_validator.py --input disks.csv --region uaenorth
    python disk_inventory_validator.py --input disks.csv --region uaenorth --currency USD --output results.json
    python disk_inventory_validator.py --input disks.csv --region uaenorth --flag-unusual --summary

CSV Input Format (from 'az disk list --output csv' or similar):
    Name,ResourceGroup,Location,SkuName,DiskSizeGB,DiskIOPSReadWrite,DiskMBpsReadWrite,Zones,DiskState
"""

import argparse
import csv
import json
import sys
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict


BASE_URL = "https://prices.azure.com/api/retail/prices"


# Disk tier mappings based on size ranges
# These mappings reflect how Azure bills managed disks
# Size is in GiB, tiers are based on provisioned size boundaries
DISK_TIER_MAPPINGS = {
    # Premium SSD (P-series): High-performance SSD for I/O intensive workloads
    # meterName pattern: "P{ tier } LRS Disk" or "P{ tier } ZRS Disk"
    "Premium_LRS": {
        "type": "Premium SSD",
        "prefix": "P",
        "size_ranges": [
            (0, 32, "P1"),      # 4-32 GiB maps to P1
            (32, 64, "P4"),     # 32-64 GiB maps to P4
            (64, 128, "P10"),   # 64-128 GiB maps to P10
            (128, 256, "P15"),  # 128-256 GiB maps to P15
            (256, 512, "P20"),  # 256-512 GiB maps to P20
            (512, 1024, "P30"), # 512-1024 GiB maps to P30
            (1024, 2048, "P40"), # 1-2 TiB maps to P40
            (2048, 8192, "P50"), # 2-8 TiB maps to P50
            (8192, 32768, "P60"), # 8-32 TiB maps to P60
        ],
        "product_name": "Premium SSD Managed Disks",
    },
    "Premium_ZRS": {
        "type": "Premium SSD",
        "prefix": "P",
        "size_ranges": [
            (0, 32, "P1"),
            (32, 64, "P4"),
            (64, 128, "P10"),
            (128, 256, "P15"),
            (256, 512, "P20"),
            (512, 1024, "P30"),
            (1024, 2048, "P40"),
            (2048, 8192, "P50"),
            (8192, 32768, "P60"),
        ],
        "product_name": "Premium SSD Managed Disks",
    },
    # Standard SSD (E-series): Cost-effective SSD for consistent performance
    # meterName pattern: "E{ tier } LRS Disk" or "E{ tier } ZRS Disk"
    "StandardSSD_LRS": {
        "type": "Standard SSD",
        "prefix": "E",
        "size_ranges": [
            (0, 32, "E1"),      # Minimum billing tier
            (32, 64, "E4"),     # 32-64 GiB maps to E4
            (64, 128, "E10"),   # 64-128 GiB maps to E10
            (128, 256, "E15"),  # 128-256 GiB maps to E15
            (256, 512, "E20"),  # 256-512 GiB maps to E20
            (512, 1024, "E30"), # 512-1024 GiB maps to E30
            (1024, 2048, "E40"), # 1-2 TiB maps to E40
            (2048, 8192, "E50"), # 2-8 TiB maps to E50
            (8192, 32768, "E60"), # 8-32 TiB maps to E60
        ],
        "product_name": "Standard SSD Managed Disks",
    },
    "StandardSSD_ZRS": {
        "type": "Standard SSD",
        "prefix": "E",
        "size_ranges": [
            (0, 32, "E1"),
            (32, 64, "E4"),
            (64, 128, "E10"),
            (128, 256, "E15"),
            (256, 512, "E20"),
            (512, 1024, "E30"),
            (1024, 2048, "E40"),
            (2048, 8192, "E50"),
            (8192, 32768, "E60"),
        ],
        "product_name": "Standard SSD Managed Disks",
    },
    # Standard HDD (S-series): Lowest cost for infrequent access
    # meterName pattern: "S{ tier } LRS Disk" or "S{ tier } ZRS Disk"
    "Standard_LRS": {
        "type": "Standard HDD",
        "prefix": "S",
        "size_ranges": [
            (0, 32, "S4"),      # 4-32 GiB maps to S4
            (32, 64, "S6"),     # 32-64 GiB maps to S6
            (64, 128, "S10"),   # 64-128 GiB maps to S10
            (128, 256, "S15"),  # 128-256 GiB maps to S15
            (256, 512, "S20"),  # 256-512 GiB maps to S20
            (512, 1024, "S30"), # 512-1024 GiB maps to S30
            (1024, 2048, "S40"), # 1-2 TiB maps to S40
            (2048, 8192, "S50"), # 2-8 TiB maps to S50
            (8192, 32768, "S60"), # 8-32 TiB maps to S60
        ],
        "product_name": "Standard HDD Managed Disks",
    },
    "Standard_ZRS": {
        "type": "Standard HDD",
        "prefix": "S",
        "size_ranges": [
            (0, 32, "S4"),
            (32, 64, "S6"),
            (64, 128, "S10"),
            (128, 256, "S15"),
            (256, 512, "S20"),
            (512, 1024, "S30"),
            (1024, 2048, "S40"),
            (2048, 8192, "S50"),
            (8192, 32768, "S60"),
        ],
        "product_name": "Standard HDD Managed Disks",
    },
    # Premium SSD v2: Per-GiB pricing model (different from P-series)
    # Note: v2 disks don't use tier-based pricing - they bill per GiB
    "PremiumV2_LRS": {
        "type": "Premium SSD v2",
        "prefix": "v2",
        "size_ranges": [],  # Per-GiB pricing, no tiers
        "product_name": "Premium SSD v2 Managed Disks",
        "pricing_model": "per_gib",
    },
    # Ultra Disk: Per-GiB pricing with additional IOPS/MBps charges
    # Note: Ultra disks have complex pricing - base + IOPS + MBps
    "UltraSSD_LRS": {
        "type": "Ultra Disk",
        "prefix": "Ultra",
        "size_ranges": [],  # Per-GiB pricing, no tiers
        "product_name": "Ultra Disk",
        "pricing_model": "per_gib_with_iops",
    },
}


@dataclass
class DiskInfo:
    """Represents a single Azure managed disk from inventory."""
    name: str
    resource_group: str
    location: str
    sku_name: str
    disk_size_gb: int
    disk_iops: Optional[int] = None
    disk_mbps: Optional[int] = None
    zones: Optional[str] = None
    disk_state: str = "Unattached"
    tier: str = ""  # Calculated pricing tier (P10, E4, etc.)
    meter_name: str = ""  # Azure billing meter name
    monthly_cost: float = 0.0
    warnings: list = field(default_factory=list)


@dataclass
class PricingCache:
    """Caches pricing lookups to minimize API calls."""
    prices: dict = field(default_factory=dict)
    
    def get_key(self, region: str, meter_name: str, currency: str = "USD") -> str:
        return f"{region}:{meter_name}:{currency}"
    
    def get(self, region: str, meter_name: str, currency: str = "USD") -> Optional[dict]:
        return self.prices.get(self.get_key(region, meter_name, currency))
    
    def set(self, region: str, meter_name: str, price_data: dict, currency: str = "USD"):
        self.prices[self.get_key(region, meter_name, currency)] = price_data


# Global pricing cache
_pricing_cache = PricingCache()


def get_tier_from_size(sku_name: str, size_gb: int) -> tuple[str, str]:
    """
    Maps disk size and SKU to pricing tier and meter name.
    
    Args:
        sku_name: Azure disk SKU (e.g., "Premium_LRS", "StandardSSD_LRS")
        size_gb: Disk size in GiB
    
    Returns:
        Tuple of (tier_name, meter_name)
        
    Note: Azure bills based on tier boundaries, not exact size.
    A 100 GiB Premium disk bills as P10 (64-128 GiB tier), not per-GiB.
    """
    mapping = DISK_TIER_MAPPINGS.get(sku_name)
    
    if not mapping:
        return ("Unknown", "")
    
    # Handle per-GiB pricing models (Premium v2, Ultra)
    if mapping.get("pricing_model") == "per_gib":
        return ("Per-GiB", f"{mapping['type']} Provisioned Capacity")
    
    if mapping.get("pricing_model") == "per_gib_with_iops":
        return ("Per-GiB+IOPS", f"{mapping['type']} Provisioned Capacity")
    
    # Find the appropriate tier based on size ranges
    prefix = mapping["prefix"]
    for min_size, max_size, tier in mapping["size_ranges"]:
        if min_size <= size_gb <= max_size:
            # Determine redundancy suffix for meter name
            if "ZRS" in sku_name:
                redundancy = "ZRS"
            else:
                redundancy = "LRS"
            meter_name = f"{tier} {redundancy} Disk"
            return (tier, meter_name)
    
    # Size exceeds max defined range
    return (f"{prefix}60+", f"{prefix}60 LRS Disk")


def fetch_disk_price(region: str, meter_name: str, currency: str = "USD") -> Optional[dict]:
    """
    Fetches disk pricing from Azure Retail Prices API.
    
    Note: Use isPrimaryMeterRegion=true to avoid duplicate entries.
    The API returns multiple meter regions but we only need the primary.
    """
    # Check cache first
    cached = _pricing_cache.get(region, meter_name, currency)
    if cached:
        return cached
    
    # Build OData filter for disk pricing
    # Note: meterName is the key field for disk pricing lookup
    filter_parts = [
        "serviceName eq 'Storage'",
        f"armRegionName eq '{region}'",
        f"meterName eq '{meter_name}'",
        "priceType eq 'Consumption'",
        "isPrimaryMeterRegion eq true"
    ]
    
    odata_filter = " and ".join(filter_parts)
    params = {"$filter": odata_filter}
    if currency != "USD":
        params["currencyCode"] = f"'{currency}'"
    
    safe_chars = "$'"
    url = f"{BASE_URL}?{urllib.parse.urlencode(params, safe=safe_chars)}"
    
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        
        items = data.get("Items", [])
        if items:
            # Cache and return first match
            price_data = {
                "retail_price": items[0].get("retailPrice", 0),
                "unit_of_measure": items[0].get("unitOfMeasure", ""),
                "product_name": items[0].get("productName", ""),
                "sku_name": items[0].get("skuName", ""),
            }
            _pricing_cache.set(region, meter_name, price_data, currency)
            return price_data
        
        return None
    except Exception as e:
        print(f"Warning: Failed to fetch price for {meter_name} in {region}: {e}", file=sys.stderr)
        return None


def calculate_monthly_cost(disk: DiskInfo, price_data: Optional[dict]) -> float:
    """
    Calculates monthly cost based on pricing data.
    
    Note: Disk pricing is per disk/month, not hourly.
    Unit of measure is typically "1/Month" for tiered disks.
    """
    if not price_data:
        return 0.0
    
    retail_price = price_data.get("retail_price", 0)
    unit_of_measure = price_data.get("unit_of_measure", "").lower()
    
    # Tier-based disks: price is per disk per month
    if "month" in unit_of_measure:
        return retail_price
    
    # Per-GiB pricing (Premium v2, Ultra)
    if "gb" in unit_of_measure or "gib" in unit_of_measure:
        # Extract per-GiB rate and multiply by disk size
        # Unit is typically "1 GB/Month" or "1 GiB/Month"
        return retail_price * disk.disk_size_gb
    
    # Default: assume monthly
    return retail_price


def check_unusual_config(disk: DiskInfo) -> list[str]:
    """
    Flags disk configurations that may be unusual or worth reviewing.
    
    Common optimization opportunities in disk inventory:
    - Oversized disks (using P20 when P10 would suffice)
    - Unattached disks still incurring charges
    - Premium disks for non-production workloads
    - Disks in wrong regions
    """
    warnings = []
    
    # Check for unattached disks (waste alert)
    if disk.disk_state.lower() in ["unattached", "detached"]:
        warnings.append("UNATTACHED: Disk not attached to any VM - costs incurred with no benefit")
    
    # Check for potential over-provisioning
    mapping = DISK_TIER_MAPPINGS.get(disk.sku_name)
    if mapping and disk.tier:
        # Find the tier's size range
        for min_size, max_size, tier_name in mapping["size_ranges"]:
            if tier_name == disk.tier:
                utilization = (disk.disk_size_gb / max_size) * 100
                if utilization < 50:
                    warnings.append(f"UNDERSIZED: Using only {utilization:.1f}% of tier capacity - consider downsizing")
                break
    
    # Premium disk warnings for small sizes
    if "Premium" in disk.sku_name and disk.disk_size_gb < 64:
        warnings.append("COST_OPPORTUNITY: Small Premium disk - consider Standard SSD if IOPS not critical")
    
    # Large Standard HDD warning (performance concern)
    if "Standard_LRS" == disk.sku_name and disk.disk_size_gb > 512:
        warnings.append("PERFORMANCE: Large HDD disk may have latency issues - consider Standard SSD")
    
    # ZRS premium warning (expensive)
    if "Premium_ZRS" in disk.sku_name:
        warnings.append("COST: ZRS Premium is ~2x LRS cost - verify zone redundancy is required")
    
    return warnings


def read_disk_inventory(csv_path: str) -> list[DiskInfo]:
    """
    Reads disk inventory from CSV file.
    
    Expected CSV columns (flexible matching):
    - Name, ResourceGroup, Location, SkuName/Sku/Name (for SKU)
    - DiskSizeGB, SizeGb, Size (for size)
    - Optional: DiskIOPSReadWrite, DiskMBpsReadWrite, Zones, DiskState
    """
    disks = []
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Flexible column name matching
            name = row.get('Name', row.get('name', ''))
            resource_group = row.get('ResourceGroup', row.get('resourceGroup', row.get('resource_group', '')))
            location = row.get('Location', row.get('location', ''))
            
            # SKU name variations
            sku_name = (row.get('SkuName', row.get('skuName', row.get('Sku', row.get('sku', '')))))
            
            # Size variations
            size_str = row.get('DiskSizeGB', row.get('diskSizeGB', row.get('SizeGb', row.get('sizeGb', row.get('Size', row.get('size', '0'))))))
            disk_size = int(float(size_str)) if size_str else 0
            
            # Optional fields
            iops_str = row.get('DiskIOPSReadWrite', row.get('diskIOPSReadWrite', ''))
            disk_iops = int(float(iops_str)) if iops_str else None
            
            mbps_str = row.get('DiskMBpsReadWrite', row.get('diskMBpsReadWrite', ''))
            disk_mbps = int(float(mbps_str)) if mbps_str else None
            
            zones = row.get('Zones', row.get('zones', ''))
            disk_state = row.get('DiskState', row.get('diskState', 'Unknown'))
            
            disk = DiskInfo(
                name=name,
                resource_group=resource_group,
                location=location,
                sku_name=sku_name,
                disk_size_gb=disk_size,
                disk_iops=disk_iops,
                disk_mbps=disk_mbps,
                zones=zones,
                disk_state=disk_state
            )
            disks.append(disk)
    
    return disks


def process_disks(disks: list[DiskInfo], region: str, currency: str, flag_unusual: bool) -> list[DiskInfo]:
    """
    Processes all disks: maps tiers, fetches prices, calculates costs.
    """
    processed = []
    
    for disk in disks:
        # Map to pricing tier
        tier, meter_name = get_tier_from_size(disk.sku_name, disk.disk_size_gb)
        disk.tier = tier
        disk.meter_name = meter_name
        
        # Fetch pricing (uses cache for duplicates)
        if meter_name:
            price_data = fetch_disk_price(region, meter_name, currency)
            disk.monthly_cost = calculate_monthly_cost(disk, price_data)
        
        # Check for unusual configs
        if flag_unusual:
            disk.warnings = check_unusual_config(disk)
        
        processed.append(disk)
    
    return processed


def generate_summary(disks: list[DiskInfo]) -> dict:
    """Generates summary statistics from processed disks."""
    total_cost = sum(d.monthly_cost for d in disks)
    total_disks = len(disks)
    
    # Group by SKU
    sku_breakdown = defaultdict(lambda: {"count": 0, "cost": 0.0, "size_gb": 0})
    for disk in disks:
        sku_breakdown[disk.sku_name]["count"] += 1
        sku_breakdown[disk.sku_name]["cost"] += disk.monthly_cost
        sku_breakdown[disk.sku_name]["size_gb"] += disk.disk_size_gb
    
    # Group by tier
    tier_breakdown = defaultdict(lambda: {"count": 0, "cost": 0.0})
    for disk in disks:
        if disk.tier:
            tier_breakdown[disk.tier]["count"] += 1
            tier_breakdown[disk.tier]["cost"] += disk.monthly_cost
    
    # Warnings summary
    warning_count = sum(len(d.warnings) for d in disks)
    disks_with_warnings = [d for d in disks if d.warnings]
    
    return {
        "total_disks": total_disks,
        "total_monthly_cost": round(total_cost, 2),
        "total_annual_cost": round(total_cost * 12, 2),
        "sku_breakdown": dict(sku_breakdown),
        "tier_breakdown": dict(tier_breakdown),
        "warning_count": warning_count,
        "disks_with_warnings": len(disks_with_warnings),
    }


def print_summary_table(summary: dict):
    """Prints formatted summary to stdout."""
    print("\n" + "=" * 70)
    print("AZURE DISK INVENTORY VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\nTotal Disks: {summary['total_disks']}")
    print(f"Total Monthly Cost: ${summary['total_monthly_cost']:,.2f}")
    print(f"Total Annual Cost: ${summary['total_annual_cost']:,.2f}")
    print(f"Warnings Found: {summary['warning_count']} ({summary['disks_with_warnings']} disks)")
    
    print("\n--- SKU Breakdown ---")
    print(f"{'SKU':<25} {'Count':<8} {'Total Size (GB)':<15} {'Monthly Cost':<15}")
    print("-" * 65)
    for sku, data in sorted(summary['sku_breakdown'].items(), key=lambda x: -x[1]['cost']):
        print(f"{sku:<25} {data['count']:<8} {data['size_gb']:<15} ${data['cost']:>12,.2f}")
    
    print("\n--- Tier Breakdown ---")
    print(f"{'Tier':<10} {'Count':<8} {'Monthly Cost':<15}")
    print("-" * 35)
    for tier, data in sorted(summary['tier_breakdown'].items(), key=lambda x: -x[1]['cost']):
        print(f"{tier:<10} {data['count']:<8} ${data['cost']:>12,.2f}")
    print("=" * 70)


def export_to_json(disks: list[DiskInfo], summary: dict, output_path: str):
    """Exports full results to JSON file."""
    output = {
        "summary": summary,
        "disks": [asdict(d) for d in disks]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Azure disk inventory against Azure Retail Prices API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --input disks.csv --region uaenorth
    %(prog)s --input disks.csv --region uaenorth --currency USD --output results.json
    %(prog)s --input disks.csv --region uaenorth --flag-unusual --summary
    
CSV Format:
    Name,ResourceGroup,Location,SkuName,DiskSizeGB,DiskState
        """
    )
    
    parser.add_argument("--input", "-i", required=True,
                        help="Path to CSV file with disk inventory")
    parser.add_argument("--region", "-r", required=True,
                        help="Azure region (e.g., uaenorth, westeurope)")
    parser.add_argument("--currency", "-c", default="USD",
                        help="Currency code (default: USD)")
    parser.add_argument("--output", "-o",
                        help="Output JSON file path")
    parser.add_argument("--flag-unusual", "-f", action="store_true",
                        help="Flag unusual disk configurations")
    parser.add_argument("--summary", "-s", action="store_true",
                        help="Print summary table")
    parser.add_argument("--max-pages", type=int, default=5,
                        help="Max API pages to fetch per query (default: 5)")
    
    args = parser.parse_args()
    
    # Read inventory
    print(f"Reading disk inventory from: {args.input}")
    try:
        disks = read_disk_inventory(args.input)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(disks)} disks")
    
    # Process disks
    print(f"Querying Azure pricing for region: {args.region}")
    processed_disks = process_disks(disks, args.region, args.currency, args.flag_unusual)
    
    # Generate summary
    summary = generate_summary(processed_disks)
    
    # Print summary if requested or by default
    if args.summary or not args.output:
        print_summary_table(summary)
    
    # Export to JSON if requested
    if args.output:
        export_to_json(processed_disks, summary, args.output)
    
    # Print warnings
    if args.flag_unusual and summary['disks_with_warnings'] > 0:
        print("\n--- WARNINGS ---")
        for disk in processed_disks:
            if disk.warnings:
                print(f"\n{disk.name} ({disk.resource_group}):")
                for warning in disk.warnings:
                    print(f"  ⚠ {warning}")


if __name__ == "__main__":
    main()
