#!/usr/bin/env python3
"""
Price Calculator Utility

Convert between different pricing formats and calculate estimates.
Handles GCP units/nanos, hourly/monthly conversions, and cost projections.
"""

import json
import sys
from typing import Union, Optional


def gcp_nanos_to_dollars(units: Union[str, int], nanos: int) -> float:
    """Convert GCP pricing format to dollars.

    GCP returns prices as:
    - units: whole dollars (as string)
    - nanos: fractional dollars in nanoseconds

    Args:
        units: Dollar units (e.g., "0" or "5")
        nanos: Nanodollars (e.g., 50577600)

    Returns:
        Price in dollars (e.g., 0.0505776)
    """
    return int(units) + (nanos / 1_000_000_000)


def dollars_to_gcp_nanos(dollars: float) -> tuple:
    """Convert dollar amount to GCP units/nanos format.

    Args:
        dollars: Dollar amount (e.g., 0.0505776)

    Returns:
        Tuple of (units, nanos)
    """
    units = int(dollars)
    nanos = int((dollars - units) * 1_000_000_000)
    return units, nanos


def hourly_to_monthly(hourly_price: float, hours_per_month: float = 730) -> dict:
    """Convert hourly price to monthly estimate.

    Args:
        hourly_price: Price per hour
        hours_per_month: Average hours per month (default: 730)

    Returns:
        Dict with hourly, monthly, and annual prices
    """
    return {
        "hourly": hourly_price,
        "daily": hourly_price * 24,
        "monthly": hourly_price * hours_per_month,
        "annual": hourly_price * hours_per_month * 12,
    }


def calculate_gcp_instance_cost(
    core_units: str,
    core_nanos: int,
    ram_units: str,
    ram_nanos: int,
    vcpus: int,
    memory_gb: float,
    hours_per_month: float = 730
) -> dict:
    """Calculate total instance cost from GCP pricing components.

    Args:
        core_units: GCP units for core pricing
        core_nanos: GCP nanos for core pricing
        ram_units: GCP units for RAM pricing
        ram_nanos: GCP nanos for RAM pricing
        vcpus: Number of vCPUs
        memory_gb: Memory in GB
        hours_per_month: Hours per month

    Returns:
        Complete cost breakdown
    """
    core_price = gcp_nanos_to_dollars(core_units, core_nanos)
    ram_price = gcp_nanos_to_dollars(ram_units, ram_nanos)

    hourly_core = core_price * vcpus
    hourly_ram = ram_price * memory_gb
    hourly_total = hourly_core + hourly_ram

    monthly = hourly_to_monthly(hourly_total, hours_per_month)

    return {
        "components": {
            "core_per_hour": core_price,
            "ram_per_gib_hour": ram_price,
        },
        "configuration": {
            "vcpus": vcpus,
            "memory_gb": memory_gb,
        },
        "hourly": {
            "core": hourly_core,
            "ram": hourly_ram,
            "total": hourly_total,
        },
        "monthly": {
            "core": hourly_core * hours_per_month,
            "ram": hourly_ram * hours_per_month,
            "total": monthly["monthly"],
        },
        "annual": {
            "total": monthly["annual"],
        },
        "summary": {
            "hourly_total": hourly_total,
            "monthly_total": monthly["monthly"],
            "annual_total": monthly["annual"],
        }
    }


def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    if amount < 0.01:
        return f"${amount:.6f}"
    elif amount < 1:
        return f"${amount:.4f}"
    else:
        return f"${amount:.2f}"


def print_cost_summary(cost_data: dict):
    """Pretty print cost breakdown."""
    print("\n=== Cost Summary ===\n")

    if "configuration" in cost_data:
        config = cost_data["configuration"]
        print(f"Configuration: {config.get('vcpus', 'N/A')} vCPUs, {config.get('memory_gb', 'N/A')} GB RAM")

    if "components" in cost_data:
        comp = cost_data["components"]
        print(f"\nPricing Components:")
        print(f"  Core per hour: {format_currency(comp.get('core_per_hour', 0))}")
        print(f"  RAM per GiB hour: {format_currency(comp.get('ram_per_gib_hour', 0))}")

    if "hourly" in cost_data:
        hourly = cost_data["hourly"]
        print(f"\nHourly Costs:")
        if "core" in hourly:
            print(f"  Core: {format_currency(hourly['core'])}")
        if "ram" in hourly:
            print(f"  RAM: {format_currency(hourly['ram'])}")
        print(f"  Total: {format_currency(hourly.get('total', 0))}")

    if "monthly" in cost_data:
        monthly = cost_data["monthly"]
        print(f"\nMonthly Costs (730 hrs):")
        if "core" in monthly:
            print(f"  Core: {format_currency(monthly['core'])}")
        if "ram" in monthly:
            print(f"  RAM: {format_currency(monthly['ram'])}")
        print(f"  Total: {format_currency(monthly.get('total', 0))}")

    if "annual" in cost_data:
        annual = cost_data.get("annual", {})
        if "total" in annual:
            print(f"\nAnnual Estimate: {format_currency(annual['total'])}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python price_calculator.py <command> [args...]")
        print("\nCommands:")
        print("  convert-gcp <units> <nanos>     - Convert GCP units/nanos to dollars")
        print("  hourly-to-monthly <hourly>      - Convert hourly to monthly")
        print("  gcp-instance <core_u> <core_n> <ram_u> <ram_n> <vcpus> <ram_gb>")
        print("\nExamples:")
        print('  python price_calculator.py convert-gcp 0 50577600')
        print('  python price_calculator.py hourly-to-monthly 0.05')
        print('  python price_calculator.py gcp-instance 0 50577600 0 6779200 4 16')
        sys.exit(1)

    command = sys.argv[1]

    if command == "convert-gcp":
        if len(sys.argv) < 4:
            print("Usage: python price_calculator.py convert-gcp <units> <nanos>")
            sys.exit(1)

        units = sys.argv[2]
        nanos = int(sys.argv[3])

        dollars = gcp_nanos_to_dollars(units, nanos)
        print(f"${dollars:.10f}")

    elif command == "hourly-to-monthly":
        if len(sys.argv) < 3:
            print("Usage: python price_calculator.py hourly-to-monthly <hourly_price>")
            sys.exit(1)

        hourly = float(sys.argv[2])
        result = hourly_to_monthly(hourly)

        print(f"Hourly: {format_currency(result['hourly'])}")
        print(f"Daily: {format_currency(result['daily'])}")
        print(f"Monthly (730h): {format_currency(result['monthly'])}")
        print(f"Annual: {format_currency(result['annual'])}")

    elif command == "gcp-instance":
        if len(sys.argv) < 8:
            print("Usage: python price_calculator.py gcp-instance <core_u> <core_n> <ram_u> <ram_n> <vcpus> <ram_gb>")
            sys.exit(1)

        core_units = sys.argv[2]
        core_nanos = int(sys.argv[3])
        ram_units = sys.argv[4]
        ram_nanos = int(sys.argv[5])
        vcpus = int(sys.argv[6])
        ram_gb = float(sys.argv[7])

        result = calculate_gcp_instance_cost(
            core_units, core_nanos,
            ram_units, ram_nanos,
            vcpus, ram_gb
        )

        print_cost_summary(result)
        print("\n=== JSON Output ===")
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
