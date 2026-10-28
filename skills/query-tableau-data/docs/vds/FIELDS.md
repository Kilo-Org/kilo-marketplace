## Fields

Every query must contain at least one field in the `fields` array. Fields define the columns returned in the result set.


### Field Types

| Type | Properties | Description |
|------|------------|-------------|
| **Dimension** | `fieldCaption` | Returns raw dimension values |
| **Measure** | `fieldCaption`, `function` | Aggregates the field using a function |
| **Custom Calculation** | `fieldCaption`, `calculation` | Ad-hoc calculated field using Tableau formula syntax |
| **Table Calculation** | `fieldCaption`, `function`, `tableCalculation` | Applies a table calculation to the aggregated field (see [TABLE_CALCULATIONS.md](./calculations/TABLE_CALCULATIONS.md)) |
| **Bin** | `fieldCaption`, `binSize` | Creates a new binned measure on the fly |


### Available Functions

| Function | Description |
|----------|-------------|
| `SUM` | Sum of values |
| `AVG` | Average |
| `MEDIAN` | Median |
| `COUNT` | Count of rows |
| `COUNTD` | Count distinct |
| `MIN` | Minimum value |
| `MAX` | Maximum value |
| `STDEV` | Standard deviation |
| `VAR` | Variance |
| `COLLECT` | Collect values (spatial) |
| `YEAR` | Extract year |
| `QUARTER` | Extract quarter |
| `MONTH` | Extract month |
| `WEEK` | Extract week |
| `DAY` | Extract day |
| `TRUNC_YEAR` | Truncate to year |
| `TRUNC_QUARTER` | Truncate to quarter |
| `TRUNC_MONTH` | Truncate to month |
| `TRUNC_WEEK` | Truncate to week |
| `TRUNC_DAY` | Truncate to day |
| `AGG` | Generic aggregation |
| `NONE` | No aggregation |
| `UNSPECIFIED` | Unspecified |


### Field Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `fieldCaption` | string | Yes | Human-readable field name (must match VDS metadata) |
| `fieldAlias` | string | No | Alias for the field in the response |
| `function` | string | No | Aggregation or date function to apply |
| `calculation` | string | No | Tableau calculation formula |
| `tableCalculation` | object | No | Table calculation specification (see [TABLE_CALCULATIONS.md](./calculations/TABLE_CALCULATIONS.md)) |
| `binSize` | number (>0) | No | Bin size for creating a new bin field |
| `maxDecimalPlaces` | integer (>=0) | No | Maximum decimal places in the output |
| `sortDirection` | `ASC` \| `DESC` | No | Sort direction for this field |
| `sortPriority` | integer (>0) | No | Sort priority (1 = highest) |


### Field Validation Rules

- The `fields` array must not be empty.
- `fieldCaption` must be a non-empty string.
- A field cannot contain both `function` and `calculation` (unless it also has `tableCalculation` — see below).
- A field with `tableCalculation` must also have a `function` (or a `calculation` when `tableCalcType` is `CUSTOM`).
- `sortPriority` values must be unique across fields.
- `maxDecimalPlaces` must be >= 0.
- A custom calculation must use a unique `fieldCaption` that does not match an existing field in the datasource.
- Custom calculations created as part of a query **cannot** be referenced in other calculations or filters.
- Table calculation fields **cannot** be referenced in filters or other calculations.


### Creating Bins

To create a new bin on the fly, provide a `binSize` and use the `fieldCaption` of the measure field you want to group:

```json
{
  "fieldCaption": "Sales Bin",
  "binSize": 1000
}
```

The query must also include the corresponding measure field:

```json
{
  "fieldCaption": "Sales",
  "function": "SUM"
}
```

> _Note_: You cannot override the bin size of a preexisting bin field in the datasource. To use an existing bin, omit `binSize` and reference it by `fieldCaption`.


### Field Support

- **Unsupported field types**: Sets, Combined Sets, Hierarchies, Geographic roles, Image roles (when not assigned as URL).


---

### Related Documentation

- [TABLE_CALCULATIONS.md](./calculations/TABLE_CALCULATIONS.md) — full schema and examples for the `tableCalculation` object
- [CALCULATIONS.md](./calculations/CALCULATIONS.md) — how to write `calculation` formulas
- [FILTERS.md](./FILTERS.md) — filtering on fields
- [LIMITATIONS.md](./LIMITATIONS.md) — unsupported field types and version constraints
