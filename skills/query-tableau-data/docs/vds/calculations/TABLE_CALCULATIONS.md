# Transform Values with Table Calculations

This article explains the basics of table calculations, their object schema, and how to use them in VDS queries.

> **Requires Tableau >= 2025.3**. Table calculations are not available on earlier versions.

## What is a table calculation?

A table calculation is a transformation you apply to the values in a query. Table calculations are a special type of calculated field that computes on **local data** — the result set returned by your query. They are calculated based on what is currently in the query, not at the database level.

You can use table calculations for a variety of purposes, including:

* Transforming values to rankings
* Transforming values to show running totals
* Transforming values to show percent of total
* Computing differences or percent changes between rows
* Applying moving averages/windows over rows

> **Important**: Table calculation functions (`RUNNING_SUM`, `WINDOW_AVG`, `RANK`, `LOOKUP`, `FIRST`, `LAST`, `INDEX`, `SIZE`, `TOTAL`, `PREVIOUS_VALUE`, etc.) **cannot** be placed directly in a `calculation` string. You **must** use the `tableCalculation` object wrapper. See the [Table Calculation Functions reference](./functions/TABLE_CALCS.md) for all available functions and their descriptions.

---

## The `tableCalculation` Object Schema

Every table calculation field requires a `tableCalculation` property on the field object. This property controls which operation is applied and how the result set is partitioned.

### Base Properties (all `tableCalcType` values)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `tableCalcType` | string (enum) | Yes | The type of table calculation. See [Supported Types](#supported-tablecalctype-values). |
| `dimensions` | array of [`TableCalcFieldReference`](#tablecalcfieldreference) | Yes | The partition dimensions. Rows sharing the same values for these dimensions form one partition. The table calculation operates independently within each partition. |

### `TableCalcFieldReference`

Used in `dimensions`, `levelAddress`, `restartEvery`, and `customSort` to reference a field.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `fieldCaption` | string | Yes | The name of the field in the datasource |
| `function` | `Function` enum | No | Aggregation/date function applied to the field (e.g., `YEAR`, `MONTH`, `SUM`) |

### `TableCalcCustomSort`

Controls the sort order within a partition for addressing.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `fieldCaption` | string | Yes | Field to sort by |
| `function` | `Function` enum | Yes | Aggregation function on the sort field |
| `direction` | `ASC` \| `DESC` | Yes | Sort direction |

---

## Partitioning and Addressing

Table calculations operate within **partitions** — groups of rows that share the same dimension values. The `dimensions` array defines the partition:

- **Partitioning** (`dimensions`): which dimensions define the groups. Rows with identical values for all listed dimensions are in the same partition.
- **Addressing**: the order in which rows within a partition are processed (top-to-bottom). Control this via `customSort` or the natural sort of remaining fields.

Think of `dimensions` as the equivalent of "Compute Using: Table (across)" in Tableau Desktop — they define the scope within which the calculation restarts.

**Example**: If your query has `Region`, `YEAR(Order Date)`, and `SUM(Sales)`, and your table calculation sets `dimensions: [{"fieldCaption": "Region"}]`, then the calculation restarts for each Region. Within each Region, it processes rows across years.

---

## Supported `tableCalcType` Values

| `tableCalcType` | Description | Extra Properties |
|-----------------|-------------|-----------------|
| `CUSTOM` | Raw table calc function syntax (e.g., `RUNNING_SUM(SUM([Sales]))`) | `levelAddress`, `restartEvery`, `customSort` |
| `DIFFERENCE_FROM` | Absolute difference from a reference row | `relativeTo`, `levelAddress`, `customSort` |
| `PERCENT_DIFFERENCE_FROM` | Percent difference from a reference row | `relativeTo`, `levelAddress`, `customSort` |
| `PERCENT_FROM` | Value as percent of a reference row | `relativeTo`, `levelAddress`, `customSort` |
| `PERCENT_OF_TOTAL` | Value as percent of partition total | `levelAddress`, `customSort` |
| `RANK` | Rank within the partition | `rankType`, `direction` |
| `PERCENTILE` | Percentile rank within the partition | `direction` |
| `RUNNING_TOTAL` | Cumulative aggregation across the partition | `aggregation`, `restartEvery`, `customSort`, `secondaryTableCalculation` |
| `MOVING_CALCULATION` | Sliding window aggregation | `aggregation`, `previous`, `next`, `includeCurrent`, `fillInNull`, `customSort`, `secondaryTableCalculation` |

---

## Type-Specific Properties

### `RANK`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `rankType` | `COMPETITION` \| `MODIFIED COMPETITION` \| `DENSE` \| `UNIQUE` | `COMPETITION` | Ranking strategy for ties |
| `direction` | `ASC` \| `DESC` | `DESC` | Sort direction for ranking |

**Example** — Rank profit within each region-year:

```json
{
  "fields": [
    { "fieldCaption": "Region" },
    { "fieldCaption": "Order Date", "function": "YEAR" },
    { "fieldCaption": "Sales", "function": "SUM" },
    { "fieldCaption": "Profit", "function": "SUM" },
    {
      "fieldCaption": "Profit",
      "fieldAlias": "Profit Rank",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "RANK",
        "dimensions": [
          { "fieldCaption": "Region" },
          { "fieldCaption": "Order Date", "function": "YEAR" }
        ],
        "rankType": "COMPETITION",
        "direction": "DESC"
      }
    }
  ]
}
```

### `PERCENTILE`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `direction` | `ASC` \| `DESC` | `ASC` | Sort direction for percentile ranking |

**Example** — Percentile rank of sales across sub-categories:

```json
{
  "fields": [
    { "fieldCaption": "Sub-Category" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Sales",
      "fieldAlias": "Sales Percentile",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "PERCENTILE",
        "dimensions": [],
        "direction": "ASC"
      }
    }
  ]
}
```

### `DIFFERENCE_FROM` / `PERCENT_DIFFERENCE_FROM` / `PERCENT_FROM`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `relativeTo` | `PREVIOUS` \| `NEXT` \| `FIRST` \| `LAST` | `PREVIOUS` | Which row to compare against |
| `levelAddress` | `TableCalcFieldReference` | — | Optional field to address across |
| `customSort` | `TableCalcCustomSort` | — | Custom sort order within partition |

**Example** — Month-over-month sales change (`DIFFERENCE_FROM`):

```json
{
  "fields": [
    { "fieldCaption": "Order Date", "function": "TRUNC_MONTH" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Sales",
      "fieldAlias": "MoM Sales Change",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "DIFFERENCE_FROM",
        "dimensions": [],
        "relativeTo": "PREVIOUS"
      }
    }
  ]
}
```

**Example** — Percent change from previous quarter (`PERCENT_DIFFERENCE_FROM`):

```json
{
  "fields": [
    { "fieldCaption": "Order Date", "function": "QUARTER" },
    { "fieldCaption": "Profit", "function": "SUM" },
    {
      "fieldCaption": "Profit",
      "fieldAlias": "QoQ % Change",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "PERCENT_DIFFERENCE_FROM",
        "dimensions": [],
        "relativeTo": "PREVIOUS"
      }
    }
  ]
}
```

**Example** — Each row as percent of first row (`PERCENT_FROM`):

```json
{
  "fields": [
    { "fieldCaption": "Order Date", "function": "TRUNC_MONTH" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Sales",
      "fieldAlias": "% of First Month",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "PERCENT_FROM",
        "dimensions": [],
        "relativeTo": "FIRST"
      }
    }
  ]
}
```

### `PERCENT_OF_TOTAL`

| Property | Type | Description |
|----------|------|-------------|
| `levelAddress` | `TableCalcFieldReference` | Optional field to address across |
| `customSort` | `TableCalcCustomSort` | Custom sort order within partition |

**Example** — Sales as percent of category total:

```json
{
  "fields": [
    { "fieldCaption": "Category" },
    { "fieldCaption": "Sub-Category" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Sales",
      "fieldAlias": "% of Category Total",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "PERCENT_OF_TOTAL",
        "dimensions": [
          { "fieldCaption": "Category" }
        ]
      }
    }
  ]
}
```

### `RUNNING_TOTAL`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `aggregation` | `SUM` \| `AVG` \| `MIN` \| `MAX` | `SUM` | Running aggregation function |
| `restartEvery` | `TableCalcFieldReference` | — | Restart the running total when this field's value changes |
| `customSort` | `TableCalcCustomSort` | — | Custom sort order within partition |
| `secondaryTableCalculation` | `TableCalcSpecification` | — | Nested secondary table calculation |

**Example** — Cumulative sales over months:

```json
{
  "fields": [
    { "fieldCaption": "Order Date", "function": "TRUNC_MONTH" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Sales",
      "fieldAlias": "Running Total Sales",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "RUNNING_TOTAL",
        "dimensions": [],
        "aggregation": "SUM"
      }
    }
  ]
}
```

> _Note_: An empty `dimensions: []` means the entire result set is one partition — the running total spans all rows.

### `MOVING_CALCULATION`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `aggregation` | `SUM` \| `AVG` \| `MIN` \| `MAX` | `SUM` | Window aggregation function |
| `previous` | integer | `2` | Number of previous rows to include |
| `next` | integer | `0` | Number of next rows to include |
| `includeCurrent` | boolean | `true` | Include the current row in the window |
| `fillInNull` | boolean | `false` | Fill null values with zero in the window |
| `customSort` | `TableCalcCustomSort` | — | Custom sort order within partition |
| `secondaryTableCalculation` | `TableCalcSpecification` | — | Nested secondary table calculation |

**Example** — 3-month moving average:

```json
{
  "fields": [
    { "fieldCaption": "Order Date", "function": "TRUNC_MONTH" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Sales",
      "fieldAlias": "3-Month Moving Avg",
      "function": "SUM",
      "tableCalculation": {
        "tableCalcType": "MOVING_CALCULATION",
        "dimensions": [],
        "aggregation": "AVG",
        "previous": 2,
        "next": 0,
        "includeCurrent": true,
        "fillInNull": false
      }
    }
  ]
}
```

### `CUSTOM`

| Property | Type | Description |
|----------|------|-------------|
| `levelAddress` | `TableCalcFieldReference` | Optional field to address across |
| `restartEvery` | `TableCalcFieldReference` | Restart the calculation when this field's value changes |
| `customSort` | `TableCalcCustomSort` | Custom sort order within partition |

> _Note_: `CUSTOM` requires a `calculation` string on the field (the raw table calc formula, e.g. `RUNNING_SUM(SUM([Sales]))`). The `tableCalculation` wrapper tells VDS to treat it as a table calculation rather than a regular calculation.

**Example** — Raw table calc formula (running sum with restart):

```json
{
  "fields": [
    { "fieldCaption": "Region" },
    { "fieldCaption": "Order Date", "function": "TRUNC_MONTH" },
    { "fieldCaption": "Sales", "function": "SUM" },
    {
      "fieldCaption": "Cumulative Regional Sales",
      "calculation": "RUNNING_SUM(SUM([Sales]))",
      "tableCalculation": {
        "tableCalcType": "CUSTOM",
        "dimensions": [
          { "fieldCaption": "Region" }
        ],
        "restartEvery": {
          "fieldCaption": "Region"
        }
      }
    }
  ]
}
```

> _Note_: `CUSTOM` is the only `tableCalcType` that uses the `calculation` string on the field. All other types derive the formula from the `function` property on the parent field.

---

## Key Constraints

- Table calculations **cannot** be used inside LOD aggregate expressions.
- Table calculations **cannot** be referenced in filters.
- Custom calculations created as ad-hoc fields **cannot** reference a table calculation field.
- The `dimensions` array must reference fields that are present in the query's `fields` array (with matching `function` if applicable).
- See [LIMITATIONS.md — Table Calculation Constraints](../LIMITATIONS.md#table-calculation-constraints) for the full list.

---

## Related Documentation

- [FIELDS.md](../FIELDS.md) — field properties including `tableCalculation`
- [Table Calculation Functions](./functions/TABLE_CALCS.md) — all table calc functions available in VDS
- [LIMITATIONS.md](../LIMITATIONS.md) — version gating and unsupported features
- [LEVEL_OF_DETAIL.md](./LEVEL_OF_DETAIL.md) — LOD expressions (complementary but cannot contain table calcs)
