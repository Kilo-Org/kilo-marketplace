# Azure Region Mappings

Azure uses short codes in APIs that differ from display names in portal.

## Americas

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `brazilsouth` | Brazil South | São Paulo State, Brazil |
| `brazilus` | Brazil US | Brazil (US Geo) |
| `canadacentral` | Canada Central | Toronto, Canada |
| `canadaeast` | Canada East | Quebec City, Canada |
| `centralus` | Central US | Iowa, USA |
| `eastus` | East US | Virginia, USA |
| `eastus2` | East US 2 | Virginia, USA |
| `northcentralus` | North Central US | Illinois, USA |
| `southcentralus` | South Central US | Texas, USA |
| `westus` | West US | California, USA |
| `westus2` | West US 2 | Washington, USA |
| `westus3` | West US 3 | Arizona, USA |
| `westcentralus` | West Central US | Wyoming, USA |

## Europe

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `francecentral` | France Central | Paris, France |
| `francesouth` | France South | Marseille, France |
| `germanynorth` | Germany North | Berlin, Germany |
| `germanywestcentral` | Germany West Central | Frankfurt, Germany |
| `northeurope` | North Europe | Ireland |
| `norwayeast` | Norway East | Oslo, Norway |
| `norwaywest` | Norway West | Stavanger, Norway |
| `swedencentral` | Sweden Central | Gävle, Sweden |
| `switzerlandnorth` | Switzerland North | Zürich, Switzerland |
| `switzerlandwest` | Switzerland West | Geneva, Switzerland |
| `uksouth` | UK South | London, UK |
| `ukwest` | UK West | Cardiff, UK |
| `westeurope` | West Europe | Netherlands |
| `polandcentral` | Poland Central | Warsaw, Poland |
| `italynorth` | Italy North | Milan, Italy |

## Asia Pacific

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `australiacentral` | Australia Central | Canberra, Australia |
| `australiacentral2` | Australia Central 2 | Canberra, Australia |
| `australiaeast` | Australia East | New South Wales, Australia |
| `australiasoutheast` | Australia Southeast | Victoria, Australia |
| `centralindia` | Central India | Pune, India |
| `eastasia` | East Asia | Hong Kong SAR |
| `japaneast` | Japan East | Tokyo, Japan |
| `japanwest` | Japan West | Osaka, Japan |
| `koreacentral` | Korea Central | Seoul, South Korea |
| `koreasouth` | Korea South | Busan, South Korea |
| `southeastasia` | Southeast Asia | Singapore |
| `southindia` | South India | Chennai, India |
| `westindia` | West India | Mumbai, India |

## Middle East and Africa

| Region Code | Display Name | Location |
|-------------|--------------|----------|
| `israelcentral` | Israel Central | Israel |
| `qatarcentral` | Qatar Central | Doha, Qatar |
| `southafricanorth` | South Africa North | Johannesburg, South Africa |
| `southafricawest` | South Africa West | Cape Town, South Africa |
| `uaenorth` | UAE North | Dubai, UAE |
| `uaecentral` | UAE Central | Abu Dhabi, UAE |

## API Usage

### Filtering by Region

```bash
# Query VM prices in East US
curl -s "https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'eastus'"

# Query storage prices in West Europe
curl -s "https://prices.azure.com/api/retail/prices?$filter=serviceFamily eq 'Storage' and armRegionName eq 'westeurope'"
```

### Region Name Conversion

```python
def display_to_api_name(display_name):
    """Convert display name (e.g., 'East US') to API name (e.g., 'eastus')."""
    return display_name.lower().replace(' ', '')

def api_to_display_name(api_name):
    """Convert API name to display name."""
    # Requires lookup table or manual mapping
    region_map = {
        'eastus': 'East US',
        'westeurope': 'West Europe',
        # ... etc
    }
    return region_map.get(api_name, api_name)
```

## VM Series Availability

Not all VM series available in all regions. Check availability:

| Series | Description | Limited Regions |
|--------|-------------|-----------------|
| D-series | General purpose | Widely available |
| E-series | Memory optimized | Widely available |
| F-series | Compute optimized | Widely available |
| B-series | Burstable | Most regions |
| M-series | Memory optimized (large) | Limited (major regions only) |
| N-series | GPU enabled | Limited (compute-focused regions) |
| H-series | HPC | Very limited |

## Pricing Variations

Prices vary by region due to:
- Local infrastructure costs
- Demand/supply
- Regional taxes
- Currency fluctuations

Typical variation: ±20% from base region (e.g., East US).
