#!/usr/bin/env python3
"""
Azure VM to GCP Machine Type Mapping Validator

Validates Azure VM SKU mappings to GCP machine types and calculates pricing.
Includes example mappings for reference.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Tuple


class MatchType(Enum):
    PERFECT = "PERFECT MATCH"
    UPSIZE = "UPSIZE"
    DOWNSIZE = "DOWNSIZE"


class Severity(Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class AzureVMSpec:
    """Azure VM specification extracted from SKU."""
    sku: str
    vcpu: int
    ram_gb: float
    series: str
    generation: str
    is_windows: bool


@dataclass
class GCPMachineType:
    """GCP machine type recommendation."""
    name: str
    vcpu: int
    ram_gb: float
    family: str
    custom: bool


@dataclass
class MappingResult:
    """Result of VM mapping validation."""
    azure_sku: str
    azure_vcpu: int
    azure_ram_gb: float
    gcp_machine_type: str
    gcp_vcpu: int
    gcp_ram_gb: float
    gcp_region: str
    match_type: str
    severity: str
    ram_delta_gb: float
    ram_delta_percent: float
    gcp_hourly_price: float
    gcp_monthly_price: float
    windows_surcharge_hourly: float
    windows_surcharge_monthly: float
    total_hourly_price: float
    total_monthly_price: float
    warnings: list


# Azure VM SKU parsing patterns
AZURE_SKU_PATTERNS = {
    # D-series: General purpose (D4lds_v5 = 4 vCPU, 8 GB)
    r"Standard_D(\d+)l?d?s?_v(\d+)": lambda m: (int(m.group(1)), int(m.group(1)) * 2),
    # F-series: Compute optimized (F4s_v2 = 4 vCPU, 8 GB)
    r"Standard_F(\d+)s?_v(\d+)": lambda m: (int(m.group(1)), int(m.group(1)) * 2),
    # E-series: Memory optimized (E8s_v3 = 8 vCPU, 64 GB)
    r"Standard_E(\d+)s?_v(\d+)": lambda m: (int(m.group(1)), int(m.group(1)) * 8),
    # B-series: Burstable (B2s = 2 vCPU, 4 GB)
    r"Standard_B(\d+)s?": lambda m: (int(m.group(1)), int(m.group(1)) * 2),
    # A-series: Basic (A4_v2 = 4 vCPU, 8 GB)
    r"Standard_A(\d+)_v(\d+)": lambda m: (int(m.group(1)), int(m.group(1)) * 2),
    # M-series: Memory optimized (M64s = 64 vCPU, 1 TB)
    r"Standard_M(\d+)s?": lambda m: (int(m.group(1)), int(m.group(1)) * 16),
    # NC-series: GPU (NC6 = 6 vCPU, 56 GB)
    r"Standard_NC(\d+)": lambda m: (int(m.group(1)), int(m.group(1)) * 9),
}

# GCP N2 machine type pricing (approximate, per hour in USD)
GCP_N2_PRICING = {
    "us-central1": {
        "n2-standard": {"vcpu": 0.031611, "ram": 0.004237},
        "n2-highmem": {"vcpu": 0.031611, "ram": 0.008474},
        "n2-highcpu": {"vcpu": 0.031611, "ram": 0.002119},
        "n2-custom": {"vcpu": 0.031611, "ram": 0.004237},
    },
    "us-east1": {
        "n2-standard": {"vcpu": 0.031611, "ram": 0.004237},
        "n2-highmem": {"vcpu": 0.031611, "ram": 0.008474},
        "n2-highcpu": {"vcpu": 0.031611, "ram": 0.002119},
        "n2-custom": {"vcpu": 0.031611, "ram": 0.004237},
    },
    "us-west1": {
        "n2-standard": {"vcpu": 0.031611, "ram": 0.004237},
        "n2-highmem": {"vcpu": 0.031611, "ram": 0.008474},
        "n2-highcpu": {"vcpu": 0.031611, "ram": 0.002119},
        "n2-custom": {"vcpu": 0.031611, "ram": 0.004237},
    },
    "europe-west1": {
        "n2-standard": {"vcpu": 0.034848, "ram": 0.004671},
        "n2-highmem": {"vcpu": 0.034848, "ram": 0.009342},
        "n2-highcpu": {"vcpu": 0.034848, "ram": 0.002336},
        "n2-custom": {"vcpu": 0.034848, "ram": 0.004671},
    },
    "asia-east1": {
        "n2-standard": {"vcpu": 0.036926, "ram": 0.004949},
        "n2-highmem": {"vcpu": 0.036926, "ram": 0.009898},
        "n2-highcpu": {"vcpu": 0.036926, "ram": 0.002475},
        "n2-custom": {"vcpu": 0.036926, "ram": 0.004949},
    },
}

# Windows Server license surcharge per vCPU (hourly)
WINDOWS_SURCHARGE_PER_VCPU = 0.046

# Example Mappings
EXAMPLE_MAPPINGS = [
    {
        "name": "D4lds_v5 Example (Custom Match)",
        "sku": "Standard_D4lds_v5",
        "region": "us-central1",
        "description": "4 vCPU, 8 GB RAM → n2-custom-4-8192 (4 vCPU, 8 GB) = PERFECT MATCH via custom type",
        "expected": {
            "azure_vcpu": 4,
            "azure_ram_gb": 8,
            "gcp_machine": "n2-custom-4-8192",
            "gcp_vcpu": 4,
            "gcp_ram_gb": 8,
            "match_type": "PERFECT MATCH",
            "severity": "OK"
        }
    },
    {
        "name": "D4lds_v5 Example (Standard-4 Alternative)",
        "sku": "Standard_D4lds_v5",
        "region": "us-central1",
        "description": "4 vCPU, 8 GB RAM → n2-standard-4 (4 vCPU, 16 GB) = UPSIZE if forcing standard family",
        "force_family": "n2-standard",
        "expected": {
            "azure_vcpu": 4,
            "azure_ram_gb": 8,
            "gcp_machine": "n2-standard-4",
            "gcp_vcpu": 4,
            "gcp_ram_gb": 16,
            "match_type": "UPSIZE",
            "severity": "WARNING"
        }
    },
    {
        "name": "F4s_v2 Example (Highcpu Match)",
        "sku": "Standard_F4s_v2",
        "region": "us-central1",
        "description": "4 vCPU, 8 GB RAM → n2-highcpu-4 (4 vCPU, 4 GB) = DOWNSIZE if forcing compute-optimized",
        "force_family": "n2-highcpu",
        "expected": {
            "azure_vcpu": 4,
            "azure_ram_gb": 8,
            "gcp_machine": "n2-highcpu-4",
            "gcp_vcpu": 4,
            "gcp_ram_gb": 4,
            "match_type": "DOWNSIZE",
            "severity": "CRITICAL"
        }
    },
    {
        "name": "E8s_v3 Example (Highmem Match)",
        "sku": "Standard_E8s_v3",
        "region": "us-central1",
        "description": "8 vCPU, 64 GB RAM → n2-highmem-8 (8 vCPU, 64 GB) = PERFECT MATCH",
        "expected": {
            "azure_vcpu": 8,
            "azure_ram_gb": 64,
            "gcp_machine": "n2-highmem-8",
            "gcp_vcpu": 8,
            "gcp_ram_gb": 64,
            "match_type": "PERFECT MATCH",
            "severity": "OK"
        }
    },
]


def parse_azure_sku(sku: str, is_windows: bool = False) -> Optional[AzureVMSpec]:
    """
    Parse Azure VM SKU to extract vCPU and RAM specifications.

    Args:
        sku: Azure VM SKU (e.g., "Standard_D4lds_v5")
        is_windows: Whether the VM runs Windows

    Returns:
        AzureVMSpec with extracted specifications
    """
    sku_clean = sku.strip()

    for pattern, extractor in AZURE_SKU_PATTERNS.items():
        match = re.match(pattern, sku_clean, re.IGNORECASE)
        if match:
            vcpu, ram_gb = extractor(match)

            # Extract series and generation
            series_match = re.search(r"[DEFBAMN][A-Z]?", sku_clean)
            series = series_match.group(0) if series_match else "Unknown"

            gen_match = re.search(r"_v(\d+)", sku_clean)
            generation = f"v{gen_match.group(1)}" if gen_match else "v1"

            return AzureVMSpec(
                sku=sku_clean,
                vcpu=vcpu,
                ram_gb=ram_gb,
                series=series,
                generation=generation,
                is_windows=is_windows
            )

    return None


def determine_machine_family(azure_spec: AzureVMSpec) -> str:
    """
    Determine the appropriate GCP machine family based on Azure VM characteristics.

    Args:
        azure_spec: Azure VM specification

    Returns:
        GCP machine family (n2-standard, n2-highmem, n2-highcpu)
    """
    ram_per_vcpu = azure_spec.ram_gb / azure_spec.vcpu

    if ram_per_vcpu >= 6:
        return "n2-highmem"
    elif ram_per_vcpu <= 2:
        return "n2-highcpu"
    else:
        return "n2-standard"


def recommend_gcp_machine_type(azure_spec: AzureVMSpec, region: str, force_family: Optional[str] = None) -> GCPMachineType:
    """
    Recommend appropriate GCP machine type based on Azure VM specs.

    Args:
        azure_spec: Azure VM specification
        region: Target GCP region

    Returns:
        GCPMachineType recommendation
    """
    family = force_family if force_family else determine_machine_family(azure_spec)

    # Calculate expected RAM for the family
    if family == "n2-standard":
        expected_ram = azure_spec.vcpu * 4
    elif family == "n2-highmem":
        expected_ram = azure_spec.vcpu * 8
    elif family == "n2-highcpu":
        expected_ram = azure_spec.vcpu * 1
    else:
        expected_ram = azure_spec.ram_gb

    # If forcing a specific family, always use predefined type
    if force_family:
        return GCPMachineType(
            name=f"{family}-{azure_spec.vcpu}",
            vcpu=azure_spec.vcpu,
            ram_gb=expected_ram,
            family=family,
            custom=False
        )

    # Check if predefined type matches exactly
    if abs(expected_ram - azure_spec.ram_gb) < 0.5:
        # Use predefined type
        return GCPMachineType(
            name=f"{family}-{azure_spec.vcpu}",
            vcpu=azure_spec.vcpu,
            ram_gb=expected_ram,
            family=family,
            custom=False
        )
    else:
        # Use custom machine type
        ram_mb = int(azure_spec.ram_gb * 1024)
        return GCPMachineType(
            name=f"n2-custom-{azure_spec.vcpu}-{ram_mb}",
            vcpu=azure_spec.vcpu,
            ram_gb=azure_spec.ram_gb,
            family="n2-custom",
            custom=True
        )


def calculate_gcp_pricing(
    gcp_machine: GCPMachineType,
    region: str,
    is_windows: bool
) -> Tuple[float, float, float, float]:
    """
    Calculate GCP pricing for the recommended machine type.

    Args:
        gcp_machine: GCP machine type specification
        region: Target GCP region
        is_windows: Whether Windows license surcharge applies

    Returns:
        Tuple of (hourly_price, monthly_price, windows_hourly, windows_monthly)
    """
    if region not in GCP_N2_PRICING:
        raise ValueError(f"Pricing data not available for region: {region}")
        
    pricing = GCP_N2_PRICING[region]
    family_pricing = pricing.get(gcp_machine.family, pricing["n2-standard"])

    # Calculate base price
    vcpu_cost = gcp_machine.vcpu * family_pricing["vcpu"]
    ram_cost = gcp_machine.ram_gb * family_pricing["ram"]
    hourly_price = vcpu_cost + ram_cost
    monthly_price = hourly_price * 730  # Average hours per month

    # Calculate Windows surcharge
    if is_windows:
        windows_hourly = gcp_machine.vcpu * WINDOWS_SURCHARGE_PER_VCPU
        windows_monthly = windows_hourly * 730
    else:
        windows_hourly = 0.0
        windows_monthly = 0.0

    return hourly_price, monthly_price, windows_hourly, windows_monthly


def validate_mapping(
    azure_spec: AzureVMSpec,
    gcp_machine: GCPMachineType
) -> Tuple[MatchType, Severity, float, float, list]:
    """
    Validate the mapping and determine match quality.

    Args:
        azure_spec: Azure VM specification
        gcp_machine: GCP machine type recommendation

    Returns:
        Tuple of (match_type, severity, ram_delta_gb, ram_delta_percent, warnings)
    """
    warnings = []
    ram_delta_gb = gcp_machine.ram_gb - azure_spec.ram_gb
    ram_delta_percent = (ram_delta_gb / azure_spec.ram_gb) * 100 if azure_spec.ram_gb > 0 else 0

    if abs(ram_delta_gb) < 0.5:
        match_type = MatchType.PERFECT
        severity = Severity.OK
    elif ram_delta_gb > 0:
        match_type = MatchType.UPSIZE
        severity = Severity.WARNING
        warnings.append(
            f"GCP machine has {ram_delta_gb:.1f} GB more RAM than Azure VM "
            f"({ram_delta_percent:+.1f}%). Consider cost optimization."
        )
    else:
        match_type = MatchType.DOWNSIZE
        severity = Severity.CRITICAL
        warnings.append(
            f"GCP machine has {abs(ram_delta_gb):.1f} GB less RAM than Azure VM "
            f"({ram_delta_percent:.1f}%). Risk of performance degradation!"
        )

    # Additional warnings
    if gcp_machine.custom:
        warnings.append("Using custom machine type. Verify pricing with GCP Calculator.")

    if azure_spec.is_windows:
        warnings.append("Windows license surcharge applies.")

    return match_type, severity, ram_delta_gb, ram_delta_percent, warnings


def validate_vm_mapping(
    azure_sku: str,
    region: str,
    is_windows: bool = False,
    force_family: Optional[str] = None
) -> Optional[MappingResult]:
    """
    Main function to validate Azure to GCP VM mapping.

    Args:
        azure_sku: Azure VM SKU
        region: Target GCP region
        is_windows: Whether the VM runs Windows

    Returns:
        MappingResult with full validation details
    """
    # Parse Azure SKU
    azure_spec = parse_azure_sku(azure_sku, is_windows)
    if not azure_spec:
        print(f"Error: Could not parse Azure SKU: {azure_sku}", file=sys.stderr)
        return None

    # Recommend GCP machine type
    gcp_machine = recommend_gcp_machine_type(azure_spec, region, force_family)

    # Calculate pricing
    hourly, monthly, win_hourly, win_monthly = calculate_gcp_pricing(
        gcp_machine, region, is_windows
    )

    # Validate mapping
    match_type, severity, ram_delta, ram_delta_pct, warnings = validate_mapping(
        azure_spec, gcp_machine
    )

    return MappingResult(
        azure_sku=azure_spec.sku,
        azure_vcpu=azure_spec.vcpu,
        azure_ram_gb=azure_spec.ram_gb,
        gcp_machine_type=gcp_machine.name,
        gcp_vcpu=gcp_machine.vcpu,
        gcp_ram_gb=gcp_machine.ram_gb,
        gcp_region=region,
        match_type=match_type.value,
        severity=severity.value,
        ram_delta_gb=ram_delta,
        ram_delta_percent=ram_delta_pct,
        gcp_hourly_price=round(hourly, 4),
        gcp_monthly_price=round(monthly, 2),
        windows_surcharge_hourly=round(win_hourly, 4),
        windows_surcharge_monthly=round(win_monthly, 2),
        total_hourly_price=round(hourly + win_hourly, 4),
        total_monthly_price=round(monthly + win_monthly, 2),
        warnings=warnings
    )


def run_examples():
    """Run example mappings and display results."""
    print("=" * 80)
    print("VM MAPPING EXAMPLES")
    print("=" * 80)
    print()

    for example in EXAMPLE_MAPPINGS:
        print(f"Example: {example['name']}")
        print("-" * 40)

        force_family = example.get("force_family")
        result = validate_vm_mapping(example["sku"], example["region"], force_family=force_family)

        if result:
            exp = example["expected"]
            if "description" in example:
                print(f"  Description:      {example['description']}")
            print(f"  Azure SKU:        {result.azure_sku}")
            print(f"  Azure Specs:      {result.azure_vcpu} vCPU, {result.azure_ram_gb} GB RAM")
            print(f"  GCP Machine:      {result.gcp_machine_type}")
            print(f"  GCP Specs:        {result.gcp_vcpu} vCPU, {result.gcp_ram_gb} GB RAM")
            print(f"  Match Type:       {result.match_type}")
            print(f"  Severity:         {result.severity}")
            print(f"  RAM Delta:        {result.ram_delta_gb:+.1f} GB ({result.ram_delta_percent:+.1f}%)")
            print(f"  GCP Hourly:       ${result.gcp_hourly_price}/hr")
            print(f"  GCP Monthly:      ${result.gcp_monthly_price}/mo")

            # Validation against expected
            validations = [
                ("Azure vCPU", result.azure_vcpu, exp["azure_vcpu"]),
                ("Azure RAM", result.azure_ram_gb, exp["azure_ram_gb"]),
                ("GCP vCPU", result.gcp_vcpu, exp["gcp_vcpu"]),
                ("GCP RAM", result.gcp_ram_gb, exp["gcp_ram_gb"]),
                ("Match Type", result.match_type, exp["match_type"]),
                ("Severity", result.severity, exp["severity"]),
            ]

            all_pass = all(str(actual) == str(expected) for _, actual, expected in validations)
            print(f"  Validation:       {'PASS' if all_pass else 'FAIL'}")

            if not all_pass:
                for name, actual, expected in validations:
                    status = "OK" if str(actual) == str(expected) else "MISMATCH"
                    print(f"    - {name}: {actual} (expected: {expected}) [{status}]")
        else:
            print(f"  ERROR: Failed to validate {example['sku']}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Validate Azure VM to GCP Machine Type mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --sku Standard_D4lds_v5 --region us-central1
  %(prog)s --sku Standard_E8s_v3 --region europe-west1 --windows
  %(prog)s --examples
  %(prog)s --sku Standard_F4s_v2 --region us-central1 --output result.json
        """
    )

    parser.add_argument(
        "--sku",
        type=str,
        help="Azure VM SKU (e.g., Standard_D4lds_v5)"
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-central1",
        help="Target GCP region (default: us-central1)"
    )
    parser.add_argument(
        "--windows",
        action="store_true",
        help="Include Windows license surcharge"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Run example mappings"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Output format (default: table)"
    )

    args = parser.parse_args()

    if args.examples:
        run_examples()
        return

    if not args.sku:
        parser.error("--sku is required (or use --examples)")

    # Validate the mapping
    result = validate_vm_mapping(args.sku, args.region, args.windows)

    if not result:
        sys.exit(1)

    # Output results
    if args.format == "json":
        output = json.dumps(asdict(result), indent=2)
        print(output)
    else:
        print("=" * 60)
        print("AZURE TO GCP VM MAPPING VALIDATION")
        print("=" * 60)
        print()
        print(f"Azure VM:")
        print(f"  SKU:              {result.azure_sku}")
        print(f"  vCPU:             {result.azure_vcpu}")
        print(f"  RAM:              {result.azure_ram_gb} GB")
        print()
        print(f"GCP Recommendation:")
        print(f"  Region:           {result.gcp_region}")
        print(f"  Machine Type:     {result.gcp_machine_type}")
        print(f"  vCPU:             {result.gcp_vcpu}")
        print(f"  RAM:              {result.gcp_ram_gb} GB")
        print()
        print(f"Mapping Analysis:")
        print(f"  Match Type:       {result.match_type}")
        print(f"  Severity:         {result.severity}")
        print(f"  RAM Delta:        {result.ram_delta_gb:+.1f} GB ({result.ram_delta_percent:+.1f}%)")
        print()
        print(f"Pricing (Estimated):")
        print(f"  GCP Hourly:       ${result.gcp_hourly_price}/hr")
        print(f"  GCP Monthly:      ${result.gcp_monthly_price}/mo")
        if result.windows_surcharge_hourly > 0:
            print(f"  Windows Surcharge: ${result.windows_surcharge_hourly}/hr (${result.windows_surcharge_monthly}/mo)")
        print(f"  Total Hourly:     ${result.total_hourly_price}/hr")
        print(f"  Total Monthly:    ${result.total_monthly_price}/mo")
        print()
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  ! {warning}")
        print()
        print("=" * 60)

    # Export to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(asdict(result), f, indent=2)
        print(f"Results exported to: {args.output}")


if __name__ == "__main__":
    main()
