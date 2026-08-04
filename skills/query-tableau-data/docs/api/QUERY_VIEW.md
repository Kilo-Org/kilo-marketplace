# View Data Query

When a user's question is perfectly answered by an existing Tableau view, `query_view_data()` retrieves that view's data directly via the REST API. This is the "quick answer" path — faster and simpler than introspecting a datasource and building a VDS query.

This document covers **Phase 3: Query Execution** in the agent's three-phase pipeline.

1. **Discovery** — Find views via the Data Catalog. See [CATALOG.md](./CATALOG.md).
2. **Introspection** — Retrieve field metadata and datasource model. See [INTROSPECT_WORKBOOK.md](./INTROSPECT_WORKBOOK.md).
3. **Execution** — Construct and submit view queries. Covered in this document.

> **Prerequisites:** Authenticate via the Tableau REST API as described in [AUTH.md](./AUTH.md) before calling any endpoints.

> **When to use this:** When the data the user wants is already pre-configured in a Tableau view. Use [INTROSPECT_DATASOURCE.md](./INTROSPECT_DATASOURCE.md) and [QUERY_DATASOURCE.md](./QUERY_DATASOURCE.md) instead when you need custom fields, filters, or aggregations.

> **IMPORTANT**: Read the [Known Limitations](#known-limitations) section before using this module. View data retrieval has significant constraints compared to VDS.


## Agent Decision Guide

Before calling `query_view_data()`, consider:

```
Does a view already answer the user's question?
    ├─ YES → query_view_data(view_luid) → return ViewQueryResult
    └─ NO  → introspect_datasource(ds_luid) → query_vds(request)

Does the user need custom aggregation, filtering, or field selection?
    ├─ YES → Use VDS (introspect + query)
    └─ NO  → Try query_view_data first

Does the user's question map to a named view in the catalog?
    ├─ YES → catalog.list_views(filter_name="...") → query_view_data(view_luid)
    └─ NO  → Use VDS
```

---

## REST Endpoint

**METHOD**: `GET /api/{api-version}/sites/{site-id}/views/{view-id}/data`

**HEADERS**:

```
X-Tableau-Auth: <token>
```

**QUERY PARAMETERS**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `maxAge` | integer | Maximum age of cached data in minutes. `None` uses Tableau's default (60 minutes). |

**RESPONSE**:

The response body is `text/csv`. The first row is the header (column names). Each subsequent row is a data row.

---

## Known Limitations

These limitations are inherent to the REST API endpoint and cannot be worked around without switching to VDS.

### 1. First Sheet Only

`query_view_data` renders the **first (default) sheet** in a workbook. If the workbook author reordered sheets, "first" may not be the most prominent sheet. You cannot specify which sheet to render.

**Workaround:** Identify the exact view LUID from `catalog.list_views()`. Each view (sheet) in a workbook has its own LUID. Use the specific view's LUID, not the workbook's LUID.

### 2. Hidden Sheets

Sheets hidden by the workbook author are **not queryable**. The endpoint returns an empty result (no data, no error) for hidden sheets. The agent receives `ViewQueryResult` with empty `rows` and `column_names` — there is no signal that the sheet is hidden.

**Detection:** If `row_count == 0` and you expected data, the view may be hidden. Cross-reference with `catalog.list_views()` — hidden sheets typically have blank or missing LUIDs in the catalog.

### 3. Published Views Only

The endpoint targets **published views** — views accessible on the Tableau site. Views that have not been published independently (e.g., a sheet inside a workbook that was not shared) may not be queryable by LUID.

### 4. No Filter or Aggregation Control

Unlike VDS, you cannot specify custom fields, filters, or aggregations. The view returns its **pre-configured data** exactly as the workbook author designed it.

If you need:
- Custom filters → Use VDS `query-datasource` with `QueryFilter`
- Custom aggregations → Use VDS with `QueryField(function="SUM")`
- Specific field selection → Use VDS with the fields you need

View-level URL filter parameters (`vf_<fieldname>`) exist in the Tableau REST API but are **out of scope** for this module.

### 5. CSV Only

The response is always `text/csv`. `ViewQueryResult` exposes both the parsed structure (`column_names`, `rows`) and the raw text (`raw_csv`) for agents that prefer to process it themselves.

## Cache Behaviour

The `max_age` parameter (mapped to `?maxAge=`) controls how Tableau caches the rendered view data:

| `max_age` value | Behaviour |
|-----------------|-----------|
| `None` (default) | Tableau uses its default cache TTL (typically 60 minutes) |
| `0` | Forces a cache bypass — always re-renders the view |
| `n` (minutes) | Returns cached data if it is at most `n` minutes old |

For real-time data, use `max_age=0`. Be aware this increases load on the Tableau server.
