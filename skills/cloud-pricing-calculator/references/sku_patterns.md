# SKU Filtering Patterns

Common regex patterns for filtering cloud pricing SKUs.

## GCP SKU Patterns

### Instance Types

| Pattern | Description | Example Matches |
|---------|-------------|-----------------|
| `N2.*Instance.*Core` | N2 vCPU pricing | "N2 Instance Core running in Iowa" |
| `N2.*Instance.*Ram` | N2 RAM pricing | "N2 Instance Ram running in Iowa" |
| `E2.*Instance.*Core` | E2 vCPU pricing | "E2 Instance Core running in Iowa" |
| `C2.*Instance.*Core` | C2 compute-optimized | "C2 Instance Core running in Iowa" |
| `M1.*Instance.*Core` | M1 memory-optimized | "M1 Ultra Instance Core" |
| `N2D.*AMD.*Core` | N2D AMD-based | "N2D AMD Instance Core" |

### Instance Variants

| Pattern | Description |
|---------|-------------|
| `.*Spot.*` or `.*Preemptible.*` | Spot/preemptible instances |
| `.*Sole Tenancy.*` | Sole tenancy premium |
| `.*Custom.*` | Custom machine types |
| `.*Extended.*` | Extended memory |
| `.*Commitment.*` or `.*Committed.*` | Committed use discounts |

### Storage Patterns

| Pattern | Description |
|---------|-------------|
| `.*Persistent Disk.*` | Persistent disks |
| `.*SSD.*` or `.*pd-ssd.*` | SSD storage |
| `.*Balanced.*` or `.*pd-balanced.*` | Balanced PD |
| `.*Standard.*` or `.*pd-standard.*` | Standard PD |
| `.*Regional.*` | Regional disks |
| `.*Hyperdisk.*` | Hyperdisk volumes |

### Networking Patterns

| Pattern | Description |
|---------|-------------|
| `.*Network.*Egress.*` | Egress charges |
| `.*Load Balancer.*` | Load balancing |
| `.*VPN.*` | VPN tunnel |
| `.*NAT.*` | NAT gateway |
| `.*CDN.*` | CDN egress |

### Database Patterns

| Pattern | Description |
|---------|-------------|
| `.*Cloud SQL.*` | Cloud SQL instances |
| `.*Spanner.*` | Cloud Spanner |
| `.*Firestore.*` | Firestore |
| `.*Bigtable.*` | Cloud Bigtable |

## Azure SKU Patterns

### VM Patterns

| Pattern | Description |
|---------|-------------|
| `D2s_v5` | D-series v5, 2 vCPUs |
| `D4s_v4` | D-series v4, 4 vCPUs |
| `E2s_v5` | E-series v5, 2 vCPUs |
| `F2s_v2` | F-series v2, 2 vCPUs |
| `B2s` | B-series burstable, 2 vCPUs |
| `Standard_` | Standard tier prefix |
| `Basic_` | Basic tier prefix |

### Storage Patterns

| Pattern | Description |
|---------|-------------|
| `Standard_LRS` | Locally redundant storage |
| `Standard_GRS` | Geo-redundant storage |
| `Standard_ZRS` | Zone-redundant storage |
| `Premium_LRS` | Premium locally redundant |
| `Premium_ZRS` | Premium zone-redundant |
| `Block Blob` | Block blob storage |
| `Page Blob` | Page blob storage |

### Database Patterns

| Pattern | Description |
|---------|-------------|
| `SQL Database` | Azure SQL Database |
| `Cosmos DB` | Azure Cosmos DB |
| `MySQL` | Azure Database for MySQL |
| `PostgreSQL` | Azure Database for PostgreSQL |

## Common jq Filters

### GCP - Filter by Region and Pattern

```bash
# All N2 SKUs in a region
jq '[.skus[] | select(.serviceRegions[]? | contains("us-central1")) | select(.description | test("N2"; "i"))]'

# Core and RAM only
jq '[.skus[] | select(.serviceRegions[]? | contains("us-central1")) | select(.description | test("N2 Instance (Core|Ram)"; "i"))]'

# Exclude spot/preemptible
jq '[.skus[] | select(.serviceRegions[]? | contains("us-central1")) | select(.description | test("N2 Instance Core"; "i")) | select(.description | test("Spot|Preemptible|Sole Tenancy"; "i") | not)]'

# Get pricing only
jq '[.skus[] | select(.serviceRegions[]? | contains("us-central1")) | {desc: .description, units: .pricingInfo[0].pricingExpression.tieredRates[0].unitPrice.units, nanos: .pricingInfo[0].pricingExpression.tieredRates[0].unitPrice.nanos}]'
```

### Azure - Filter by Service and Region

```bash
# All VMs in region
jq '[.Items[] | select(.armRegionName == "eastus" and .serviceName == "Virtual Machines")]'

# Specific SKU
jq '[.Items[] | select(.skuName | contains("D2s_v5"))]'

# Get prices only
jq '.Items[] | {sku: .skuName, price: .retailPrice, unit: .unitOfMeasure}'
```

## Pattern Testing

Test patterns before running full queries:

```bash
# Get sample descriptions first
curl -s "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=YOUR_KEY" | \
  jq '.skus[0:20] | map(.description)'

# Then test pattern
curl -s "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=YOUR_KEY" | \
  jq '[.skus[] | select(.description | test("YOUR_PATTERN"; "i"))] | length'
```

## Case Sensitivity Notes

- **GCP**: Mixed case in descriptions, always use `test("pattern"; "i")`
- **Azure**: Generally consistent case, but safer to use case-insensitive matching
