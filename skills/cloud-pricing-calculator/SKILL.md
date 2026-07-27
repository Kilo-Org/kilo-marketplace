---
name: cloud-pricing-calculator
description: >-
  Calculate accurate cloud infrastructure costs using GCP and Azure retail pricing APIs.
  Query SKUs, filter by regions/instance types, convert pricing units (units/nanos to dollars),
  and generate estimates. Use when user asks about cloud pricing, cost estimation, SKU lookups,
  GCP/Azure pricing APIs, or comparing cloud costs.
metadata:
  category: cloud-costing
  author: attiacloudgalaxy
  source:
    repository: 'https://github.com/attiacloudgalaxy/cloud-pricing-calculator'
    path: skills/cloud-pricing-calculator
    license_path: LICENSE
---

# Cloud Pricing Calculator

## Overview

Query and calculate accurate cloud infrastructure costs from GCP and Azure retail pricing APIs. Handle SKU lookups, regional pricing, instance sizing, and cost conversions with proper understanding of API structures and pricing units.

## When to Use

Trigger this skill when user asks about:
- Cloud pricing for GCP or Azure resources
- SKU lookups by service type, region, or instance family
- Converting pricing API responses (units/nanos) to dollar amounts
- Comparing costs between regions or instance types
- Cost estimation for infrastructure sizing
- Retail pricing API queries
- Understanding why certain SKUs don't appear in specific regions
- Validating disk inventory exports from `az disk list`
- Checking VM-to-cloud mappings for accuracy
- Detecting RAM mismatches in migration scenarios
- Cross-referencing storage account capacities

## GCP Pricing Workflow

### 1. Identify Service and SKU

Each GCP service has a unique service ID. Common compute service ID:
- **Compute Engine**: `6F81-5844-456A`

Load service ID reference: `references/gcp_service_ids.md`

Retrieve all SKUs for a service:
```bash
curl -s "https://cloudbilling.googleapis.com/v1/services/{SERVICE_ID}/skus?currencyCode=USD&pageSize=5000&key={API_KEY}"
```

### 2. Filter SKUs by Criteria

SKUs have complex structures. Key fields:
- `description`: Human-readable name (e.g., "N2 Instance Core running in Iowa")
- `serviceRegions`: Array of region codes (e.g., ["us-central1"])
- `category`: Service categorization
- `pricingInfo`: Array of pricing data

Filter by region and description:
```bash
curl -s "https://cloudbilling.googleapis.com/v1/services/{SERVICE_ID}/skus?currencyCode=USD&pageSize=5000&key={API_KEY}" | \
  jq '[.skus[] | select(.serviceRegions[]? | contains("{REGION}")) | select(.description | test("{PATTERN}"; "i"))]'
```

### 3. Extract Pricing Information

Pricing is in `pricingInfo[0].pricingExpression.tieredRates[0].unitPrice`:
- `units`: Dollar amount (as string)
- `nanos`: Fractional dollar amount (nanodollars)

**Convert nanos to dollars:**
```
Total Price = units + (nanos / 1,000,000,000)
```

Example: `units: "0"`, `nanos: 50577600` → $0.0505776/hour

Use helper script: `scripts/gcp_pricing.py` for automated conversion

### 4. Common GCP Challenges and Solutions

**Challenge**: Region codes in SKUs don't always match user-friendly names
- **Solution**: Reference `references/gcp_regions.md` for mappings
- Example: "me-central2" = Dammam, Saudi Arabia

**Challenge**: Instance types have multiple SKUs (cores, RAM, premiums)
- **Solution**: Query both cores and RAM separately, then combine
- N2 Standard = N2 Instance Core + N2 Instance Ram

**Challenge**: Some regions don't offer all instance types
- **Solution**: Always verify SKU existence before calculating
- Example: me-central2 only has N2 Sole Tenancy, not regular N2

**Challenge**: "Standard Instance" vs "Instance Core" naming
- **Solution**: Use regex `test("N2.*Instance.*Core"; "i")` not exact match
- GCP uses varied description formats

## Azure Pricing Workflow

### 1. Query Retail Prices API

Azure Retail Prices API endpoint:
```bash
curl -s "https://prices.azure.com/api/retail/prices?$filter=serviceName eq '{SERVICE}' and armRegionName eq '{REGION}'"
```

### 2. Filter and Parse Results

Azure returns paginated results with `NextPageLink`. Key fields:
- `productName`: Service description
- `skuName`: SKU identifier
- `retailPrice`: Direct price in currency
- `unitOfMeasure`: Billing unit (e.g., "1 Hour")
- `armRegionName`: Azure region code
- `serviceFamily`: Category (Compute, Storage, etc.)

### 3. Common Azure Challenges

**Challenge**: Pagination handling required
- **Solution**: Follow `NextPageLink` until null
- Use helper script: `scripts/azure_pricing.py`

**Challenge**: Region names differ between portal and API
- **Solution**: Use `armRegionName` format (e.g., "eastus" not "East US")
- Reference: `references/azure_regions.md`

**Challenge**: VM pricing requires understanding series/family
- **Solution**: Filter by `serviceName eq 'Virtual Machines'` and `skuName contains 'D2'`

## Price Calculation Reference

### GCP Price Formula
```javascript
// From API response
const units = parseInt(pricingInfo[0].pricingExpression.tieredRates[0].unitPrice.units);
const nanos = pricingInfo[0].pricingExpression.tieredRates[0].unitPrice.nanos;
const pricePerUnit = units + (nanos / 1000000000);

// Calculate monthly (730 hours average)
const monthlyPrice = pricePerUnit * 730;
```

### Azure Price Formula
```javascript
// Azure provides retailPrice directly
const pricePerUnit = Items[0].retailPrice;
const unitOfMeasure = Items[0].unitOfMeasure; // e.g., "1 Hour"
```

## Instance Sizing Guidelines

### GCP Machine Types
| Type | Use Case | vCPU:RAM Ratio |
|------|----------|----------------|
| N2 | General purpose | 1:3.75 |
| N2D | AMD-based general | 1:4 |
| C2 | Compute optimized | 1:4 |
| M1/M2 | Memory optimized | 1:24 |
| E2 | Cost-optimized | 1:4 |

### Azure VM Series
| Series | Use Case | vCPU:RAM Ratio |
|--------|----------|----------------|
| D-series | General purpose | 1:4 |
| E-series | Memory optimized | 1:8 |
| F-series | Compute optimized | 1:2 |
| B-series | Burstable | Variable |

## Quick Reference Commands

### GCP - List all SKUs in region
```bash
curl -s "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?currencyCode=USD&pageSize=5000&key=$API_KEY" | \
  jq '[.skus[] | select(.serviceRegions[]? | contains("us-central1"))] | map(.description) | unique'
```

### GCP - Get N2 pricing in region
```bash
curl -s "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?currencyCode=USD&pageSize=5000&key=$API_KEY" | \
  jq '[.skus[] | select(.serviceRegions[]? | contains("us-central1")) | 
      select(.description | test("N2 Instance (Core|Ram)"; "i")) | 
      {desc: .description, units: .pricingInfo[0].pricingExpression.tieredRates[0].unitPrice.units, nanos: .pricingInfo[0].pricingExpression.tieredRates[0].unitPrice.nanos, unit: .pricingInfo[0].pricingExpression.usageUnitDescription}]'
```

### Azure - Get VM pricing
```bash
curl -s "https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'eastus' and contains(skuName, 'D2')" | \
  jq '.Items[] | {name: .productName, sku: .skuName, price: .retailPrice, unit: .unitOfMeasure}'
```

## Resources

### scripts/
- `gcp_pricing.py`: Query and parse GCP pricing API
- `azure_pricing.py`: Query and parse Azure retail prices
- `price_calculator.py`: Convert units/nanos to dollar amounts
- `disk_inventory_validator.py`: Validate Azure disk CSV exports against pricing API
- `vm_mapping_validator.py`: Validate Azure-to-GCP VM mappings with RAM mismatch detection

### references/
- `gcp_service_ids.md`: Service ID mappings for GCP
- `gcp_regions.md`: Region code mappings
- `azure_regions.md`: Azure region name mappings
- `sku_patterns.md`: Common SKU filtering patterns
- `azure_disk_skus.md`: Azure managed disk tier mappings and meter names

## Lessons Learned

1. **Always verify SKU existence**: Regions may not offer all instance types
2. **Use case-insensitive regex**: GCP descriptions vary in capitalization
3. **Check units field type**: GCP returns units as string, not number
4. **Handle pagination**: Azure API paginates; follow NextPageLink
5. **Combine core + RAM**: Total instance cost requires both SKUs
6. **Region codes differ**: API uses codes ("us-central1"), not names ("Iowa")

## Advanced Lessons from Real-World Projects

### 10. Disk Inventory Validation (Critical)

Always verify disk types from source CSVs (Premium SSD, Standard SSD, Standard HDD)
- Azure disk SKUs: P1/P4/P10/P15/P20/P30 for Premium, E4/E10/E15/E20 for Standard SSD, S4/S10/S15/S20 for Standard HDD
- Cross-reference disk sizes with actual CSV export — don't estimate
- Example: NVA OS disk 2 GiB (P1), App server 127 GiB Standard SSD (E10), Print server 128 GiB HDD (S10)

### 11. VM-to-Cloud Mapping Accuracy

Map Azure vCPU → GCP n2-standard-X (not n2-highcpu unless specifically compute-optimized)
- **Critical**: Verify RAM matches exactly — D4lds_v5 = 8 GB, not 16 GB
- Document intentional upsizes/downsizes with justification
- GCP RAM options: n2-standard (4 GB per vCPU), n2-highmem (8 GB per vCPU), n2-highcpu (1 GB per vCPU)
- Use custom machine types (n2-custom-X-Y) when Azure VM doesn't match predefined GCP types

### 12. Windows License Surcharge (GCP Only)

GCP: Windows adds ~$0.046/vCPU/hour on top of base Linux price
- Calculate: (vCPU count × $0.046 × 730) = monthly Windows surcharge
- Example: 78 vCPUs × $0.046 × 730 = $2,621.64/month additional
- Azure: Windows license included in PAYG compute rate (no separate calculation)

### 13. Cross-Region SKU Validation

Always verify SKU availability in target region BEFORE calculating costs
- Use `az vm list-skus --location {region}` for Azure
- For GCP: query SKUs and filter by serviceRegions array
- Example: me-central2 (Dammam) lacks regular N2 — only N2 Sole Tenancy available

### 14. Storage Capacity Verification

Never estimate storage — always use actual capacity exports
- Azure Storage Account capacity often surprises (e.g. tens of TiB in backup accounts)
- Calculate: (capacity in TiB × 1024) × rate per GB
- Flag oversized storage for retention policy review

### 15. Excel Formula Accuracy Checklist

3-Year TCO must include: Year 1 + Year 2 + Year 3 (not Year 1 + Year 2 only)
- Verify subtotals sum correctly — VMSS should be in compute total
- Cross-check: Itemized one-time costs must equal TCO section input
- Round consistently — don't mix rounded and unrounded values in different sections

### 16. Special Component Handling

**NVA appliances (e.g. firewalls)**: Not ASR-replicable — requires fresh Marketplace deployment + license re-registration
**PAM/vault solutions**: May require vendor-native replication, not ASR
**VMSS**: Cannot protect via ASR — must redeploy from ARM template in DR
**SQL Express**: No additional license cost, but migrate strategy differs (VM-based vs Cloud SQL)

### 17. API Response Caching Strategy

Azure Retail API responses should be cached with timestamp
- Document query date in proposals: "Pricing verified via Azure Retail Prices API, [DATE]"
- Save raw API responses for audit trail
- GCP pricing calculator exports as backup evidence

### 18. Proposal-to-Workbook Alignment

Workbook can add analytical options (e.g., "1A+Rep") not in proposals
- But grand totals must match exactly between all documents
- Sub-category differences are OK if documented (e.g., "Storage includes RA-GRS replication")
- Add explanatory notes in workbook for any derivation from proposal

### 19. Validation Query Templates

Verify Azure disk inventory:
```bash
# Export actual disk list from subscription
az disk list --subscription {SUB_ID} --output table
```

Verify VM SKUs in target region:
```bash
az vm list-skus --location germanywestcentral --output table | grep -E "(D4lds_v5|F4s_v2|E8s_v3)"
```

Calculate monthly from hourly:
```python
monthly = hourly_rate * 730  # Azure standard month
```

### 20. Pre-Delivery Checklist

Before submitting BOQ to customer:
- [ ] All inventory items verified against source CSVs (VMs, disks, storage, MySQL)
- [ ] Pricing API query date documented
- [ ] 3-Year TCO formula verified (Year 1 + Year 2 + Year 3)
- [ ] Grand totals match across all documents (proposals + workbook)
- [ ] Special components flagged (NVAs, PAM/vault, VMSS)
- [ ] Windows license surcharge calculated (if GCP)
- [ ] Storage retention flagged if >10 TiB
- [ ] SKU availability verified in target region
- [ ] RAM mappings verified (no unexplained upsizes/downsizes)
