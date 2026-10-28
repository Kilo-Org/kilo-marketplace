## Limitations

### Data Source Support

| Feature | Status |
|---------|--------|
| Published data sources | Supported |
| Extract data sources | Supported |
| Live connections | Supported |
| Embedded data sources in workbooks | Not supported |
| Custom SQL data sources | Not supported |
| Cube data sources (Microsoft Analysis Services, Oracle OLAP, etc.) | Not supported |

### Performance and Scale

| Limit | Value |
|-------|-------|
| Query timeout | 30 minutes |
| Maximum response size (pre-2026.1) | 1 GB |
| Maximum response size (2026.1+) | Unlimited (streaming) |
| Query cap per site | 100 queries/hour per Creator license on the site |

### Licensing

VDS is available for all license models. Each **Creator license** assigned to a site raises the site-wide query cap by 100 queries per hour.

> _Note_: If you exceed the query cap, the server returns HTTP `429` with error code `429000`.

---

### Calculation Support

VDS supports the following calculation types in custom `calculation` fields:

- Basic row-level calculations
- Aggregate calculations
- LOD expressions (FIXED, INCLUDE, EXCLUDE)
- Logical calculations (IF/THEN/ELSE, CASE/WHEN, IIF)
- String, date, number, and type conversion functions
- Parameter-based calculations
- User functions

#### Supported Aggregation Functions (via `function` property)

`SUM`, `AVG`, `MEDIAN`, `COUNT`, `COUNTD`, `MIN`, `MAX`, `STDEV`, `VAR`, `COLLECT`, `YEAR`, `QUARTER`, `MONTH`, `WEEK`, `DAY`, `TRUNC_YEAR`, `TRUNC_QUARTER`, `TRUNC_MONTH`, `TRUNC_WEEK`, `TRUNC_DAY`

#### Unsupported Function Categories

The following entire categories of Tableau functions **cannot** be used in VDS queries:

| Category | Functions | Reason |
|----------|-----------|--------|
| **Spatial** | `AREA`, `BUFFER`, `DIFFERENCE`, `DISTANCE`, `INTERSECTION`, `INTERSECTS`, `MAKELINE`, `MAKEPOINT`, `LENGTH` (spatial), `OUTLINE`, `SHAPETYPE`, `SYMDIFFERENCE`, `VALIDATE`, `COLLECT` (spatial agg) | Spatial calculations not supported |
| **Pass-through (RAWSQL)** | All `RAWSQL_*` and `RAWSQLAGG_*` variants (`RAWSQL_BOOL`, `RAWSQL_INT`, `RAWSQL_REAL`, `RAWSQL_STR`, `RAWSQL_DATE`, `RAWSQL_DATETIME`, `RAWSQL_SPATIAL`, and their `RAWSQLAGG_*` counterparts) | Pass-through calculations not supported |
| **Analytics Extensions (Script)** | `SCRIPT_BOOL`, `SCRIPT_INT`, `SCRIPT_REAL`, `SCRIPT_STR` | Python/R calculations not supported |
| **Model Extensions** | `MODEL_EXTENSION_BOOL`, `MODEL_EXTENSION_INT`, `MODEL_EXTENSION_REAL`, `MODEL_EXTENSION_STRING` | Analytics extensions not supported |
| **Hadoop Hive-specific** | `GET_JSON_OBJECT`, `PARSE_URL`, `PARSE_URL_QUERY`, `XPATH_BOOLEAN`, `XPATH_DOUBLE`, `XPATH_FLOAT`, `XPATH_INT`, `XPATH_LONG`, `XPATH_SHORT`, `XPATH_STRING` | Data-source-specific functions not available |
| **Google BigQuery-specific** | `DOMAIN`, `GROUP_CONCAT`, `HOST`, `LOG2`, `LTRIM_THIS`, `RTRIM_THIS`, `TIMESTAMP_TO_USEC`, `USEC_TO_TIMESTAMP`, `TLD` | Data-source-specific functions not available |

#### Unsupported Individual Functions

| Function | Status |
|----------|--------|
| `ATTR` | Not available as a VDS aggregation function |
| `STDEVP` | Not in VDS supported aggregation list (use `STDEV` instead) |
| `VARP` | Not in VDS supported aggregation list (use `VAR` instead) |
| `CORR` | Not in VDS supported aggregation list |
| `COVAR` | Not in VDS supported aggregation list |
| `COVARP` | Not in VDS supported aggregation list |
| `PERCENTILE` (aggregate) | Not in VDS supported aggregation list |
| `COUNT(table)` | Explicitly unsupported |
| `DATEPARSE` | Heavy data source restrictions; may fail in VDS context |
| `MAKEDATETIME` | MySQL-only connector; unlikely to work via VDS |

#### Unsupported Calculation Features

| Feature | Detail |
|---------|--------|
| **Sets** | Cannot query sets; cannot reference sets in calculations |
| **Combined fields** | Cannot query or reference combined fields |
| **Groups** | Cannot reference a group in a calculation |
| **Fiscal date calculations** | Explicitly unsupported |

---

### Table Calculation Constraints

VDS supports table calculations via the dedicated `tableCalculation` object, NOT by placing table calc functions directly in a `calculation` string. For the full schema, partitioning semantics, and worked examples, see [TABLE_CALCULATIONS.md](./calculations/TABLE_CALCULATIONS.md).

**Supported `tableCalcType` values:**
`CUSTOM`, `DIFFERENCE_FROM`, `PERCENT_DIFFERENCE_FROM`, `PERCENT_FROM`, `PERCENT_OF_TOTAL`, `RANK`, `PERCENTILE`, `RUNNING_TOTAL`, `MOVING_CALCULATION`

**Key gotchas:**

- **Do not** use table calculation functions (`RUNNING_SUM`, `WINDOW_AVG`, `RANK`, `LOOKUP`, `FIRST`, `LAST`, `INDEX`, `SIZE`, `TOTAL`, `PREVIOUS_VALUE`, etc.) inside a regular `calculation` field. This will fail. You **must** use the `tableCalculation` object wrapper.
- The only way to use raw table calc function syntax (e.g., `RUNNING_SUM(SUM([Sales]))`) is via `tableCalcType: "CUSTOM"` with both a `calculation` string AND a `tableCalculation` wrapper.
- Table calculations **cannot** be used inside LOD aggregate expressions.
- Table calculations require **Tableau >= 2025.3**.

---

### Date Limitations

| Limitation | Detail |
|------------|--------|
| **No datetime support** | VDS does not support datetimes -- only dates. Use date fields only. |
| **No time zones** | VDS does not support time zones in dates |
| **RFC 3339 format required** | Dates must be in RFC 3339 format (e.g., `2020-01-15`), not Tableau `#date#` literal syntax |
| **No date-time aggregations** | `HOUR`, `MINUTE`, `SECOND` aggregations are not supported |

---

### Filter Limitations

| Limitation | Detail |
|------------|--------|
| **No functions in set/match/date filters** | Set filters, match filters, and relative date filters cannot have functions or calculations |
| **One filter per field** | Cannot have multiple filters for the same field in a single query (e.g., you can't have two filters both on `SUM(Sales)`) |
| **No bins or groups in filters** | Bins and groups cannot be used in filters |
| **Pre-2026.1 restrictions** | `restrictFunctionsAndCalculationsInFilters` is more restrictive before Tableau 2026.1 |

---

## Version Gating Reference

The following features affect VDS query workflows:

| Feature | Tableau >= 2026.1 | < 2026.1 (2025.3) | < 2025.3 |
|---------|-------------------|-------------------|----------|
| `rowLimit` in options | Supported | Not supported | Not supported |
| `returnServerSentEvents` (SSE streaming) | Supported | Not supported | Not supported |
| JSON streaming | Supported | Not supported | Not supported |
| `restrictFunctionsAndCalculationsInFilters` | Relaxed (functions allowed in more filters) | Restricted | Restricted |
| Table calculations | Supported | Supported | Not supported |
| `getDatasourceModel` | Supported | Supported | Not supported |

---

### Related Documentation

- [TABLE_CALCULATIONS.md](./calculations/TABLE_CALCULATIONS.md) — full table calculation schema, partitioning, and examples
- [FIELDS.md](./FIELDS.md) — field types including table calculation fields
- [FILTERS.md](./FILTERS.md) — filter restrictions and version gating
- [STREAMING.md](./STREAMING.md) — streaming features (2026.1+)
- [ERRORS.md](./ERRORS.md) — error codes for constraint violations
