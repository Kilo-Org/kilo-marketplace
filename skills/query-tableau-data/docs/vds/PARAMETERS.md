# Parameters

Override datasource parameter values at query time. Parameters must already exist in the published data source.

**REQUEST PAYLOAD:**

```json
{
  "parameters": [
    {
      "parameterCaption": "Date Range",
      "value": "2024-01-01"
    }
  ]
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `parameterCaption` | string | Yes | Name of the parameter as shown in the datasource |
| `value` | string \| number \| boolean \| null | Yes | New value for the parameter |


## Parameter Types from Metadata

| `parameterType` | Value Constraints | Description |
|---------------|-------------------|-------------|
| `ANY_VALUE` | Must match parameter `dataType` | Free-form value |
| `LIST` | Must be one of `members` | Value from a predefined list |
| `QUANTITATIVE_DATE` | RFC 3339 date string within `minDate`/`maxDate` | Date within a range |
| `QUANTITATIVE_RANGE` | Number within `min`/`max` | Numeric value within a range |

> _Note_: For ad-hoc calculations that use parameters, create a custom `calculation` field that references the parameter and include the parameter override in the `parameters` array.


## Date Formats

VDS accepts dates in **RFC 3339** format only.

- **Valid**: `2025-03-14`
- **Invalid**: `2025-03-14T00:00:00Z` (datetime), `03/14/2025` (locale-dependent)

> _Note_: When providing dates in custom calculations or filters, always use the `#YYYY-MM-DD#` literal format for Tableau calculation syntax (e.g., `#2021-05-05#`).


---

### Related Documentation

- [FIELDS.md](./FIELDS.md) — field definitions and how parameters interact with calculated fields
- [FILTERS.md](./FILTERS.md) — filtering (often used alongside parameter overrides)
- [CALCULATIONS.md](./calculations/CALCULATIONS.md) — using parameters in calculation formulas
- [LIMITATIONS.md](./LIMITATIONS.md) — constraints on parameter types
