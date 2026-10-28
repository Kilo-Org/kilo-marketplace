# REPL Exploration — Query Tableau Data

A complete REPL session demonstrating the recommended three-tier workflow: authenticate, take inventory of the full site, trace lineage on selected assets, introspect field schemas, and execute VDS queries — all holding data as Python variables.

> **Formalizing a workflow?** Once you've explored in the REPL, see [SDK.md](sdk/SDK.md) to write a reusable script.
> **Advanced usage:** See [ADVANCED.md](sdk/ADVANCED.md) for raw payloads and the functional API.

---

## Choosing the Right Path

```
Agent is assigned a task that requires Tableau data
  │
  ├─ Always start: scope_site() to gauge scale and project taxonomy
  │    4 fast REST requests, safe on any site size
  │
  ├─ Small/medium site (datasources < 500, workbooks < 1000)?
  │    YES → inventory_datasources() + inventory_views() (full pull, fast)
  │    NO  → inventory_datasources(limit=1000) + filter_project + is_certified
  │
  ├─ Need to understand how views relate to datasources?
  │    YES → workbook_lineage(luid) for top-viewed workbooks
  │           datasource_lineage(luid) for candidate datasources
  │
  ├─ Need an asset's full field structure, calculations & semantics?
  │    YES → introspect_workbook(wb_luid) for workbooks
  │          introspect(ds_luid) for datasources
  │
  ├─ Ready to query a specific datasource via VDS?
  │    YES → introspect(luid) → build QueryRequest → query()
  │
  ├─ An ad-hoc question is already answered by a pre-configured view?
  │    YES → inventory_views() → query_view_data(view_luid)
  │
  ├─ Writing a reusable script?
  │    YES → explore in REPL → write new script to the scripts/ folder
  │
  └─ Adding Tableau VDS queries to an application?
       YES → explore in REPL → write VDS query with conventions of the local repo
```

## Data Flow

```
.env credentials
      │
      ▼
┌─────────────┐   ┌─────────────┐   ┌──────────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐   ┌─────────────┐
│ Server Info │   │    Auth     │   │   Tier 0 — Scope             │   │     Tier 1 — Inventory       │   │  Tier 2 — Lineage    │   │  Tier 3 — Introspect │   │  Tier 4 —   │
│ (no auth)   │──▶│  (sign_in)  │──▶│ scope_site()                 │──▶│ inventory_datasources()      │──▶│ datasource_lineage() │──▶│  introspect(luid)    │──▶│   Query        │
│             │   │             │   │   4 REST requests            │   │ inventory_views()            │   │ workbook_lineage()   │   │  introspect_workbook │   │  query()       │
└─────────────┘   └─────────────┘   │   counts + project list      │   │ inventory_workbooks()        │   │                      │   │                      │   │  query_view_   │
  REST — instant     REST — instant  └──────────────────────────────┘   └──────────────────────────────┘   └──────────────────────┘   └──────────────────────┘   │  data(luid)    │
                                           REST — instant                       REST — fast                    GraphQL per asset           VDS + GraphQL          └────────────────┘
```

---

## Session Primitives

All methods are available on the `Session` object. Mix and match based on your task — you do not need to call every tier.

| Method | Tier | Transport | Returns | Use When |
|--------|------|-----------|---------|----------|
| `server_info` (auto) | Pre-auth | REST | `ServerInfo` | Populated automatically on `Session.__enter__()`; determines VDS availability, feature tier, and auto-negotiates API version |
| `scope_site()` | 0 — Scope | REST | `SiteScope` | First step on any task — 4 fast requests for asset counts + project taxonomy, safe on any site size |
| `inventory_datasources(**kw)` | 1 — Inventory | REST | `list[DatasourceInventoryItem]` | Full list of all published datasources with certification/tag signals |
| `inventory_views(**kw)` | 1 — Inventory | REST | `list[ViewInventoryItem]` | Fast view listing with `total_view_count` built in — canonical popularity signal |
| `inventory_workbooks(**kw)` | 1 — Inventory | REST | `list[WorkbookInventoryItem]` | Flat workbook list for initial orientation; no sheets/datasource links |
| `datasource_lineage(luid)` | 2 — Lineage | GraphQL | `DatasourceLineage` | Per-asset: downstream workbooks/sheets/dashboards + upstream tables/databases + 30-field preview |
| `workbook_lineage(luid)` | 2 — Lineage | GraphQL | `WorkbookLineage` | Per-asset: sheets, dashboards, embedded and upstream published datasources |
| `introspect(luid)` | 3 — Introspect | VDS + GraphQL | `DatasourceSchema` | Full field schema for VDS query building — run on a datasource you've already chosen |
| `introspect_workbook(luid)` | 3 — Introspect | GraphQL | `WorkbookSchema` | Workbook field-level structure, calculations, and upstream datasource links |
| `query(request)` | 4 — Query | VDS | `QueryResult` | Custom aggregation, filtering, and field selection from a published datasource |
| `query_view_data(luid)` | 4 — Query | REST | `ViewQueryResult` | Pre-configured view data — no field selection needed |
| `list_supported_functions(luid)` | Utility | VDS | `list[SupportedFunction]` | Check which aggregation functions are available for a specific datasource |
| `health_check()` | Utility | REST | `bool` | Verify VDS connectivity after auth |
| `query_raw(payload)` | Utility | VDS | `QueryResult` | Send a raw dict payload, bypassing the typed `QueryRequest` model |

**Key filters** (`**kw` on inventory functions): `filter_name="..."`, `filter_project="..."`, `page_size=1000`, `limit=N`

> **Note:** The REST `id` field and the GraphQL Metadata API `luid` field are the same value for any given asset. Use LUIDs from `scope_site()`, `inventory_*()`, or catalog methods directly in lineage and introspect calls without any translation.

---

## Prerequisites

**1. Credentials & Configuration** — Copy the environment template and ask the user to fill in their Tableau credentials (or get their explicit permission to do so):

```bash
cp .env.template .env
# Edit .env — see variable reference below
```

| Variable | Required | Description |
|----------|----------|-------------|
| `TABLEAU_SERVER_URL` | **Yes** | Full URL to Tableau Cloud or Server (e.g., `https://site.online.tableau.com`) |
| `TABLEAU_SITE_NAME` | **Yes** | Site content URL name (empty string for Default site on Server) |
| `PAT_NAME` | **Yes*** | Personal Access Token name |
| `PAT_VALUE` | **Yes*** | Personal Access Token secret value |
| `TABLEAU_USERNAME` | Alt | Username for username/password auth (alternative to PAT) |
| `TABLEAU_PASSWORD` | Alt | Password for username/password auth |
| `TABLEAU_API_VERSION` | No | **Deprecated** — auto-negotiated from the server on session entry. Do not set manually. |
| `TABLEAU_VDS_VERSION` | No | VDS API version path segment (default: `v1`). Only version available today. |
| `TABLEAU_USE_HTTP` | No | Allow plain HTTP instead of HTTPS (default: `false` = HTTPS enforced). Dev-only escape hatch; a warning is logged when active. |
| `TABLEAU_TIMEOUT` | No | HTTP request timeout in seconds for all API calls (default: `30.0`). Increase for large queries or slow networks. |

\* At least one credential pair is required: PAT (recommended) or username/password.

> **WARNING**: Do NOT read the `.env` file directly — user secrets must never be exposed to your context window. `SdkConfig` loads and validates the file automatically. If credentials are missing or invalid it raises immediately with a clear error. Ask the user to create/edit `.env` themselves, or get their explicit permission before touching it. Never commit `.env` to version control.

See [AUTH.md](api/AUTH.md) for credential types (PAT, username/password) and how to obtain them.

**2. Dependencies**

```bash
uv sync
```

**3. Start the REPL**

```bash
uv run python
```

---

## Full REPL Session

> **RULE: Do not write files for exploration.** Run `uv run python -c "..."` directly.
> Only write to `scripts/` when formalizing a reusable workflow after REPL exploration is complete.

Run this as a single script or paste sections into a REPL. The `Session` context manager handles sign-in, transparent 401 retry, and sign-out automatically. Print only counts, filtered lists, and small samples — never full catalogs or result sets.

If auth fails, check [AUTH.md](api/AUTH.md) and [Troubleshooting in SDK.md](sdk/SDK.md#troubleshooting).

```python
from collections import defaultdict
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.session import Session
from query_tableau_data_py.models import (
    QueryField, QueryFilter, QueryOptions, QueryRequest
)

with Session(SdkConfig()) as session:

    # =====================================================================
    # STEP 0 — AUTH CHECK (run this first, every time)
    # If we reach here, credentials from .env were accepted.
    # Do not manually check for .env — SdkConfig raises immediately:
    #   ValidationError       → .env is missing required fields
    #   AuthenticationError   → credentials are wrong or PAT is expired
    #   OSError/ConnectError  → server URL is wrong or network is down
    # =====================================================================
    si = session.server_info
    print(f"Server {si.product_version} (API {si.rest_api_version} — auto-negotiated), VDS tier: {si.vds_feature_tier}")
    print("AUTH OK\n")

    # =====================================================================
    # STEP 1 — SCOPE  (Tier 0: 4 fast REST requests, safe on any site)
    # Always run scope_site() before any inventory call.
    # Returns asset counts and the full project list in ~300 ms.
    # Use counts to branch strategy — full inventory vs. filtered/limited.
    # =====================================================================
    scope = session.scope_site()
    print(f"{scope.datasource_count} datasources, {scope.workbook_count} workbooks, {scope.view_count} views")
    print(f"{len(scope.projects)} projects")
    for p in scope.projects[:20]:
        print(f"  {p.name}")

    # =====================================================================
    # STEP 2 — INVENTORY  (Tier 1: REST, full site picture)
    # Adapt strategy based on scope counts.
    # inventory_views() always includes total_view_count (usage statistics).
    # Hold all three as variables. Print only counts and filtered slices.
    # =====================================================================
    if scope.datasource_count < 500 and scope.workbook_count < 1000:
        # Small/medium site: full inventory is fast in the REPL (default page_size=1000)
        datasources = session.inventory_datasources()
        views       = session.inventory_views()          # includes total_view_count
        workbooks   = session.inventory_workbooks()
    else:
        # Large site: use project filtering + limits in the REPL
        datasources = session.inventory_datasources(limit=1000)
        views       = session.inventory_views(limit=5000)
        workbooks   = session.inventory_workbooks(limit=1000)

    print(f"{len(datasources)} datasources, {len(views)} views, {len(workbooks)} workbooks\n")

    # Filter datasources by keyword and certification status
    sales_ds   = [ds for ds in datasources if "Sales" in ds.name]
    certified  = [ds for ds in datasources if ds.is_certified]
    print(f"{len(sales_ds)} Sales datasources, {len(certified)} certified")
    print([(ds.name, ds.luid) for ds in certified[:5]])

    # Rank views by popularity — total_view_count is always populated here
    top_views = sorted(views, key=lambda v: v.total_view_count or 0, reverse=True)
    print(f"\nTop 5 views by usage:")
    print([(v.name, v.total_view_count) for v in top_views[:5]])

    # Narrow candidates: certified datasources or keyword matches
    candidates = [ds for ds in datasources if ds.is_certified or "Sales" in ds.name]
    print(f"\n{len(candidates)} candidate datasources for deeper inspection")

    # =====================================================================
    # STEP 3 — LINEAGE  (Tier 2: targeted GraphQL, one request per asset)
    # For each selected candidate, fetch lineage to understand:
    #   - Which workbooks and sheets consume this datasource (downstream)
    #   - Which physical tables and databases it reads from (upstream)
    #   - A 30-field preview to gauge schema relevance without a full introspect
    #
    # For top-viewed workbooks, fetch workbook lineage to discover which
    # published datasources power them — this is your bridge from a view
    # that answers a question to the datasource you can query via VDS.
    #
    # Each call is one HTTP request — no pagination, no timeout risk.
    # =====================================================================

    # Trace the top-viewed workbooks → find which datasources power them
    wb_luids = {v.workbook_luid for v in top_views[:5] if v.workbook_luid}
    print(f"\nTracing lineage for {len(wb_luids)} top-viewed workbooks:")
    for luid in list(wb_luids)[:3]:
        wb_lin = session.workbook_lineage(luid)
        upstream_names = [d.name for d in wb_lin.upstream_datasources]
        print(f"  {wb_lin.name}")
        print(f"    sheets:              {[s.name for s in wb_lin.sheets]}")
        print(f"    upstream datasources: {upstream_names}")

    # Trace certified datasources → understand downstream impact and upstream sources
    print(f"\nLineage for certified datasources:")
    for ds in certified[:2]:
        ds_lin = session.datasource_lineage(ds.luid)
        print(f"  {ds_lin.name} (certified={ds_lin.is_certified})")
        print(f"    downstream workbooks: {[w.name for w in ds_lin.downstream_workbooks]}")
        print(f"    upstream tables:      {[t.name for t in ds_lin.upstream_tables]}")
        print(f"    upstream databases:   {[db.name for db in ds_lin.upstream_databases]}")
        # Field preview from lineage — 30 fields without a full introspect call
        dims_preview = [f for f in ds_lin.field_preview if f.role == "DIMENSION"]
        meas_preview = [f for f in ds_lin.field_preview if f.role == "MEASURE"]
        print(f"    field preview:        {len(dims_preview)} dims, {len(meas_preview)} measures (first 30 total)")

    # Pick the best target for VDS querying — prefer certified, use lineage field
    # preview to confirm it has the dimensions and measures you need
    target_ds = certified[0] if certified else candidates[0]
    print(f"\nSelected target: {target_ds.name}  (luid={target_ds.luid})")

    # =====================================================================
    # STEP 4 — INTROSPECT  (Tier 3: full field schema for the chosen target)
    # Only run introspect() on an asset you've already selected via inventory
    # and lineage. This is the most expensive call — VDS readMetadata plus
    # optional GraphQL enrichment.
    #
    # Field names are CASE-SENSITIVE — use the exact names from introspection
    # in your QueryRequest below.
    #
    # Fields are grouped by logical table in schema.field_groups. Each
    # FieldGroup has a logical_table_caption attribute (NOT .name) and
    # a .fields list. Use the iteration pattern below.
    #
    # Some datasources have "API Access" disabled — catch IntrospectionError
    # 401 when looping over candidates:
    #
    #   from query_tableau_data_py.errors import IntrospectionError
    #   for ds in candidates:
    #       try:
    #           schema = session.introspect(ds.luid)
    #       except IntrospectionError as e:
    #           if "401" in str(e):
    #               print(f"SKIP {ds.name!r} — API Access not enabled")
    #           else:
    #               raise
    # =====================================================================
    schema = session.introspect(target_ds.luid)

    # Dimensions (for grouping / row-level detail)
    dims = [f for fg in schema.field_groups for f in fg.fields
            if f.column_class == "DIMENSION"]
    print(f"\n{len(dims)} dimensions (first 10):")
    for f in dims[:10]:
        print(f"  {f.name:30s}  {f.data_type}")

    # Measures (for aggregation: SUM, AVG, COUNT, MIN, MAX)
    measures = [f for fg in schema.field_groups for f in fg.fields
                if f.role == "MEASURE"]
    print(f"\n{len(measures)} measures:")
    for f in measures[:10]:
        print(f"  {f.name:30s}  {f.data_type}")

    # Inspect logical table groupings
    print(f"\nLogical tables ({len(schema.field_groups)}):")
    for fg in schema.field_groups:
        print(f"  {fg.logical_table_caption}: {len(fg.fields)} fields")

    # =====================================================================
    # PRE-FLIGHT — Read these references BEFORE constructing a query.
    #
    # | Doc                              | Why                                                        |
    # |----------------------------------|------------------------------------------------------------|
    # | vds/FIELDS.md                    | Field types, fieldAlias, calculation vs function, rules    |
    # | vds/LIMITATIONS.md               | Version-gated features (rowLimit needs >= 2026.1),         |
    # |                                  | unsupported functions, calculation constraints             |
    # | vds/FILTERS.md                   | Filter types and restrictions (if using filters)           |
    # | vds/calculations/CALCULATIONS.md | Calculation formula syntax (if using custom calculations)  |
    # | models.py — QueryResult          | Response shape: result.rows (NOT .data),                   |
    # |                                  | result.metadata.row_count                                  |
    # | models.py — QueryField, Options  | Available parameters and their camelCase aliases           |
    #
    # Response key convention:
    #   Dimensions keep bare captions:       "Region", "Category"
    #   Aggregated fields get FUNCTION(cap): "SUM(Sales)", "AVG(Profit)"
    #   Use fieldAlias on QueryField to override response keys.
    # =====================================================================

    # =====================================================================
    # STEP 5 — QUERY VDS  (Tier 4)
    # Build a query using exact field names from introspection above.
    # - Dimensions without a function become GROUP BY columns
    # - Measures require an aggregation function (SUM, AVG, COUNT, etc.)
    # - Filters narrow the result set server-side
    # - row_limit caps returned rows (Tableau >= 2026.1 only)
    # =====================================================================
    request = QueryRequest(
        datasource_luid=target_ds.luid,
        fields=[
            QueryField(field_caption="Region"),
            QueryField(field_caption="Category"),
            QueryField(field_caption="Sales",  function="SUM"),
            QueryField(field_caption="Profit", function="SUM"),
        ],
        filters=[
            QueryFilter(
                field_caption="Order Date",
                filter_type="QUANTITATIVE_DATE",
                anchor_date="2024-01-01",
                period_type="YEARS",
                period_count=1,
            ),
        ],
        # NOTE: row_limit requires Tableau >= 2026.1; omit on older servers
        options=QueryOptions(return_format="OBJECTS", row_limit=500),
    )

    result = session.query(request)
    print(f"\nRows returned: {result.metadata.row_count}")
    print(result.rows[:5])  # Always slice — never print full result sets

    # =====================================================================
    # STEP 6 — PROCESS RESULTS
    # The result is a Python object (QueryResult). Filter, aggregate, or
    # transform in memory. Always slice or aggregate before printing —
    # large payloads in the context window degrade reasoning quality.
    #
    # IMPORTANT — Response key naming:
    #   Dimensions (no function) keep their bare caption: "Region", "Category"
    #   Aggregated fields use FUNCTION(caption): "SUM(Sales)", "SUM(Profit)"
    # =====================================================================
    high_sales = [r for r in result.rows if r["SUM(Sales)"] > 50000]
    print(f"\n{len(high_sales)} high-sales rows")

    by_region = defaultdict(float)
    for r in result.rows:
        by_region[r["Region"]] += r["SUM(Sales)"]
    print(dict(by_region))
```

---

## Multi-step pattern (reuse variables across REPL cells)

For interactive exploration where you build up context across multiple cells, call `__enter__()` once and keep the session open:

```python
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.session import Session

# Cell 1 — setup (runs once)
session = Session(SdkConfig()).__enter__()

# Cell 2 — scope (always first, 4 fast requests)
scope = session.scope_site()
print(f"{scope.datasource_count} datasources, {scope.workbook_count} workbooks, {scope.view_count} views")

# Cell 3 — inventory (variables survive in REPL)
datasources = session.inventory_datasources()
views       = session.inventory_views()
print(f"{len(datasources)} datasources, {len(views)} views")

# Cell 4 — lineage on a candidate (reuses datasources from cell 3)
certified = [ds for ds in datasources if ds.is_certified]
ds_lin = session.datasource_lineage(certified[0].luid)
print(f"Downstream workbooks: {[w.name for w in ds_lin.downstream_workbooks]}")

# Cell 5 — introspect the target (reuses certified from cell 4)
schema = session.introspect(certified[0].luid)
measures = [f for fg in schema.field_groups for f in fg.fields if f.role == "MEASURE"]
print(f"{len(measures)} measures: {[f.name for f in measures]}")

# Cell N — teardown when done
session.__exit__(None, None, None)
```

> _Note_: Holding thousands of rows in `result.rows` is fine for programmatic processing. But always slice or aggregate before printing: `print(result.rows[:5])` not `print(result.rows)`.

---

## Getting View Usage Statistics

`inventory_views()` is the canonical path for view popularity signals. It always sets `includeUsageStatistics=true` — `total_view_count` is always populated.

```python
with Session(SdkConfig()) as session:
    views = session.inventory_views()
    top = sorted(views, key=lambda v: v.total_view_count or 0, reverse=True)
    print([(v.name, v.total_view_count) for v in top[:10]])
```

To resolve workbook names (not included in the REST `/views` response), join with `inventory_workbooks()`:

```python
with Session(SdkConfig()) as session:
    views     = session.inventory_views()
    workbooks = session.inventory_workbooks()
    wb_map    = {wb.luid: wb.name for wb in workbooks}
    top = sorted(views, key=lambda v: v.total_view_count or 0, reverse=True)
    for v in top[:10]:
        print(v.name, v.total_view_count, wb_map.get(v.workbook_luid, "unknown"))
```

---

## Persisting Results (opt-in)

If you need to export data to disk (CSV, JSON), use `data.py`:

```python
from query_tableau_data_py.data import write_query_result
files = write_query_result(result, datasource_name=target_ds.name, datasource_luid=target_ds.luid)
print("Written to:", files)
```

See [TEMP_DATA.md](sdk/TEMP_DATA.md) for file naming conventions, formats, and `jq` exploration commands.

> **WARNING**: Always clean up `temp/` when you finish — these files may contain sensitive business data.
> ```bash
> rm -f temp/*.json temp/*.csv temp/*.md
> ```

---

## What's Next

| Goal | Resource |
|------|----------|
| Write a reusable script from your REPL findings | [SDK.md](sdk/SDK.md) |
| Understand all available filter types | [vds/FILTERS.md](vds/FILTERS.md) |
| Use aggregation functions (SUM, AVG, COUNT…) | [vds/FIELDS.md](vds/FIELDS.md) |
| Check version-gated features and known constraints | [vds/LIMITATIONS.md](vds/LIMITATIONS.md) |
| Work with Tableau parameters | [vds/PARAMETERS.md](vds/PARAMETERS.md) |
| Write calculations (LOD, table calcs) | [vds/CALCULATIONS.md](vds/calculations/CALCULATIONS.md) |
| Handle errors by code | [vds/ERRORS.md](vds/ERRORS.md) |
| Stream large result sets (advanced) | [STREAMING.md — http.client escape hatch](vds/STREAMING.md#implementing-sse-with-httpclient-advanced) |
| File-based persistence & exploration | [TEMP_DATA.md](sdk/TEMP_DATA.md) |
| Full catalog API reference | [CATALOG.md](api/CATALOG.md) |
