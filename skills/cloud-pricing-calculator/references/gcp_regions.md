# GCP Region Mappings

GCP uses region codes in APIs that may differ from display names in console.

## Americas

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `us-central1` | Iowa | Council Bluffs, Iowa, USA |
| `us-east1` | South Carolina | Moncks Corner, South Carolina, USA |
| `us-east4` | Northern Virginia | Ashburn, Virginia, USA |
| `us-east5` | Columbus | Columbus, Ohio, USA |
| `us-south1` | Dallas | Dallas, Texas, USA |
| `us-west1` | Oregon | The Dalles, Oregon, USA |
| `us-west2` | Los Angeles | Los Angeles, California, USA |
| `us-west3` | Salt Lake City | Salt Lake City, Utah, USA |
| `us-west4` | Las Vegas | Las Vegas, Nevada, USA |
| `northamerica-northeast1` | Montreal | Montreal, Quebec, Canada |
| `northamerica-northeast2` | Toronto | Toronto, Ontario, Canada |
| `southamerica-east1` | São Paulo | Osasco, São Paulo, Brazil |
| `southamerica-west1` | Santiago | Santiago, Chile |

## Europe

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `europe-central2` | Warsaw | Warsaw, Poland |
| `europe-north1` | Finland | Hamina, Finland |
| `europe-southwest1` | Madrid | Madrid, Spain |
| `europe-west1` | Belgium | St. Ghislain, Belgium |
| `europe-west2` | London | London, England, UK |
| `europe-west3` | Frankfurt | Frankfurt, Germany |
| `europe-west4` | Netherlands | Eemshaven, Netherlands |
| `europe-west6` | Zürich | Zürich, Switzerland |
| `europe-west8` | Milan | Milan, Italy |
| `europe-west9` | Paris | Paris, France |
| `europe-west10` | Berlin | Berlin, Germany |
| `europe-west12` | Turin | Turin, Italy |

## Asia Pacific

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `asia-east1` | Taiwan | Changhua County, Taiwan |
| `asia-east2` | Hong Kong | Hong Kong |
| `asia-northeast1` | Tokyo | Tokyo, Japan |
| `asia-northeast2` | Osaka | Osaka, Japan |
| `asia-northeast3` | Seoul | Seoul, South Korea |
| `asia-southeast1` | Singapore | Jurong West, Singapore |
| `asia-southeast2` | Jakarta | Jakarta, Indonesia |
| `asia-south1` | Mumbai | Mumbai, India |
| `asia-south2` | Delhi | Delhi, India |
| `australia-southeast1` | Sydney | Sydney, Australia |
| `australia-southeast2` | Melbourne | Melbourne, Australia |

## Middle East

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `me-central1` | Doha | Doha, Qatar |
| `me-central2` | Dammam | Dammam, Saudi Arabia |
| `me-west1` | Tel Aviv | Tel Aviv, Israel |

## Africa

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `africa-south1` | Johannesburg | Johannesburg, South Africa |

## Multi-Region

| Region Code | Description |
|-------------|-------------|
| `global` | Global resources (e.g., global load balancers) |
| `us` | Multi-region: United States |
| `europe` | Multi-region: Europe |
| `asia` | Multi-region: Asia |

## Region-Specific SKU Behavior

### Limitations by Region

Some instance types and services are NOT available in all regions:

**me-central2 (Dammam)**:
- N2: Only Sole Tenancy available (no regular N2 instances)
- C2: Not available
- M1/M2: Not available

**asia-southeast2 (Jakarta)**:
- Some older machine types may not be available

**africa-south1 (Johannesburg)**:
- Limited service availability

### SKU Region Filtering

When querying SKUs, filter by checking `serviceRegions` array:

```bash
# Check if SKU is available in region
curl -s "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=YOUR_KEY" | \
  jq '.skus[] | select(.serviceRegions[]? | contains("me-central2"))'
```

## Zone Naming Convention

Zones are sub-regions within a region:
- Format: `{region}-{zone_letter}`
- Example: `us-central1-a`, `us-central1-b`, `us-central1-c`

Most regions have 3+ zones for high availability.
