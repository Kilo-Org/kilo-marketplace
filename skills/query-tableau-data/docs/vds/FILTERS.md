## Filters

Filters narrow the result set. All filters support an optional `context` property (boolean).


### The `FilterField` Type

The `field` property in every filter accepts one of three shapes:

| Variant | Required Properties | When to Use |
|---------|---------------------|-------------|
| **Dimension** | `fieldCaption` | Filtering on a dimension (e.g., `Category`, `Region`) |
| **Measure** | `fieldCaption`, `function` | Filtering on an aggregated measure (e.g., `SUM(Sales) > 1000`) |
| **Calculated** | `calculation` | Filtering on an ad-hoc calculation formula |

**Examples:**

```json
// Dimension filter field
{ "fieldCaption": "Category" }

// Measure filter field
{ "fieldCaption": "Sales", "function": "SUM" }

// Calculated filter field
{ "calculation": "DATEDIFF('day', [Order Date], TODAY())" }
```

> _Note_: Pre-2026.1, `SET`, `MATCH`, and `DATE` filters cannot have `function` or `calculation` on the field. See [LIMITATIONS.md — Filter Limitations](./LIMITATIONS.md#filter-limitations) for version-specific restrictions.


### Filter Context Property

| `context` value | Behavior |
|-----------------|----------|
| `true` | Filter applies to the overall query context (dimension/scope filters) |
| `false` | Filter applies after context is established (ranking/limiting filters) |

**When to use:**
- Set `context: true` on dimension filters (`SET`, `DATE`, `QUANTITATIVE` on dimensions) that define the scope of analysis.
- Set `context: false` on `TOP` filters to rank/limit results within the established context.
- Omit `context` for simple queries with a single filter.

**Example: Finding top products within a region:**

```json
{
  "filters": [
    {
      "field": { "fieldCaption": "State" },
      "filterType": "SET",
      "values": ["California"],
      "context": true
    },
    {
      "field": { "fieldCaption": "Product Name" },
      "filterType": "TOP",
      "howMany": 1,
      "direction": "TOP",
      "context": false,
      "fieldToMeasure": { "fieldCaption": "Sales", "function": "SUM" }
    }
  ]
}
```

### Filter Validation Rules

- Only one filter per field is allowed.
- `SET`, `MATCH`, and `DATE` filters cannot have functions or calculations applied to the field (pre-2026.1 restriction; see [Version Gating](#version-gating)).
- `MATCH` filters must include at least one of `startsWith`, `endsWith`, or `contains`.
- Quantitative `MIN`/`MAX` operators are **inclusive**. For strictly greater-than or less-than logic, use a small offset (for example, `min: 10.01` for `> 10`).
- `TOP` filters must include `fieldToMeasure`.
- `SET` filter `values` array must not be empty.


### SET Filter

Filter by specific values:

**REQUEST PAYLOAD:**

```json
{
  "field": { "fieldCaption": "Category" },
  "filterType": "SET",
  "values": ["Technology", "Furniture"],
  "exclude": false
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `field` | `FilterField` | Yes | Field to filter |
| `filterType` | `"SET"` | Yes | Filter type |
| `values` | array | Yes | Array of string, number, or boolean values |
| `exclude` | boolean | No | If `true`, exclude the specified values |


### MATCH Filter

Filter strings using patterns:

**REQUEST PAYLOAD:**

```json
{
  "field": { "fieldCaption": "Product Name" },
  "filterType": "MATCH",
  "startsWith": "Desk",
  "endsWith": "Chair",
  "contains": "Office",
  "exclude": false
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `startsWith` | string | No* | Match strings starting with this value |
| `endsWith` | string | No* | Match strings ending with this value |
| `contains` | string | No* | Match strings containing this value |
| `exclude` | boolean | No | If `true`, exclude matches |

> _Note_: At least one of `startsWith`, `endsWith`, or `contains` is required.


### TOP Filter

Get top or bottom N records by a measure:

**REQUEST PAYLOAD:**

```json
{
  "field": { "fieldCaption": "Customer Name" },
  "filterType": "TOP",
  "howMany": 10,
  "direction": "TOP",
  "fieldToMeasure": { "fieldCaption": "Sales", "function": "SUM" }
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `howMany` | integer | Yes | Number of records to return |
| `direction` | `"TOP"` \| `"BOTTOM"` | No | Direction (default: `TOP`) |
| `fieldToMeasure` | `FilterField` | Yes | Field and optional function to measure by |


### QUANTITATIVE_NUMERICAL Filter

Filter numeric values:

**REQUEST PAYLOAD:**

```json
{
  "field": { "fieldCaption": "Sales" },
  "filterType": "QUANTITATIVE_NUMERICAL",
  "quantitativeFilterType": "RANGE",
  "min": 1000,
  "max": 50000,
  "includeNulls": false
}
```

| `quantitativeFilterType` | Required Properties | Description |
|--------------------------|---------------------|-------------|
| `RANGE` | `min`, `max` | Between min and max (inclusive) |
| `MIN` | `min` | Greater than or equal to min |
| `MAX` | `max` | Less than or equal to max |
| `ONLY_NULL` | — | Only null values |
| `ONLY_NON_NULL` | — | Only non-null values |

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `includeNulls` | boolean | No | Include null values in the result |


### QUANTITATIVE_DATE Filter

Filter date values using quantitative operators:

**REQUEST PAYLOAD:**

```json
{
  "field": { "fieldCaption": "Order Date" },
  "filterType": "QUANTITATIVE_DATE",
  "quantitativeFilterType": "RANGE",
  "minDate": "2023-01-01",
  "maxDate": "2023-12-31",
  "includeNulls": true
}
```

| `quantitativeFilterType` | Required Properties | Description |
|--------------------------|---------------------|-------------|
| `RANGE` | `minDate`, `maxDate` | Between min and max (inclusive) |
| `MIN` | `minDate` | Greater than or equal to minDate |
| `MAX` | `maxDate` | Less than or equal to maxDate |
| `ONLY_NULL` | — | Only null values |
| `ONLY_NON_NULL` | — | Only non-null values |

> _Note_: Dates must use the RFC 3339 standard (e.g., `2025-03-14`).


### DATE Filter (Relative Date)

Filter relative date periods:

**REQUEST PAYLOAD:**

```json
{
  "field": { "fieldCaption": "Order Date" },
  "filterType": "DATE",
  "periodType": "MONTHS",
  "dateRangeType": "LAST"
}
```

| `dateRangeType` | Required Properties | Description |
|-----------------|---------------------|-------------|
| `CURRENT` | `periodType` | Current period |
| `LAST` | `periodType` | Last completed period |
| `NEXT` | `periodType` | Next period |
| `TODATE` | `periodType`, `anchorDate` | From start of period to anchor date |
| `LASTN` | `periodType`, `rangeN` | Last N periods |
| `NEXTN` | `periodType`, `rangeN` | Next N periods |

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `periodType` | `"MINUTES"` \| `"HOURS"` \| `"DAYS"` \| `"WEEKS"` \| `"MONTHS"` \| `"QUARTERS"` \| `"YEARS"` | Yes | Time period granularity |
| `anchorDate` | string (RFC 3339) | No* | Anchor date for `TODATE` |
| `rangeN` | integer | No* | Number of periods for `LASTN` / `NEXTN` |
| `includeNulls` | boolean | No | Include null values |

> _Note_: `anchorDate` is required when `dateRangeType` is `TODATE`. `rangeN` is required when `dateRangeType` is `LASTN` or `NEXTN`.


## Date Formats

VDS accepts dates in **RFC 3339** format only.

- **Valid**: `2025-03-14`
- **Invalid**: `2025-03-14T00:00:00Z` (datetime), `03/14/2025` (locale-dependent)

> _Note_: When providing dates in custom calculations or filters, always use the `#YYYY-MM-DD#` literal format for Tableau calculation syntax (e.g., `#2021-05-05#`).


### Filter Support

- **Unsupported in filters**: `IN` operator, wildcard patterns in `SET` filters.


---

### Related Documentation

- [FIELDS.md](./FIELDS.md) — field definitions and the `function` enum values
- [PARAMETERS.md](./PARAMETERS.md) — overriding parameter values (often used alongside filters)
- [LIMITATIONS.md](./LIMITATIONS.md) — filter version-gating and restrictions
- [CALCULATIONS.md](./calculations/CALCULATIONS.md) — syntax for the `calculation` property in calculated filter fields
