# SDK Reference — `query_tableau_data_py`

This document is the **reference guide** for agents using the `query_tableau_data_py` Python package. It covers the module map, usage patterns, and troubleshooting.

**New to this skill? Start with [REPL.md](../REPL.md)** — it demonstrates a complete REPL exploration session before you need this reference.

## Contents

| File | When to Use | Description |
| --- | --- | --- |
| [SDK.md](./SDK.md) (this file) | writing scripts, understanding the module map and `Session` API | Primary SDK reference — quick start, workflow decision tree, module reference table, common patterns, and troubleshooting |
| [ADVANCED.md](./ADVANCED.md) | Fine-grained control over auth lifecycle, custom HTTP transport, or raw payload construction outside of `Session` | Advanced patterns — raw functional API, manual token management, custom retry logic, and long-lived process integration |
| [TEMP_DATA.md](./TEMP_DATA.md) | Persisting results to disk for CSV export, multi-session continuity, or handing data to external tools | File-based persistence conventions — naming, formats (JSON/CSV/Markdown), cleanup, and `jq` exploration commands |
| [INTEGRATION.md](./INTEGRATION.md) | Integrating VDS queries into async applications (Streamlit, FastAPI) | Patterns for wrapping sync Session in async code, correct test mocking, thread safety guidance |

---

## Setup

See [REPL.md — Prerequisites](../REPL.md#prerequisites) for credentials and dependency installation.

---

## Understanding the Workflow

The skill implements a multi-phase pipeline with two parallel paths depending on the user's question:

### Datasource Path (Custom Queries)

| Phase | Module | Purpose |
|-------|--------|---------|
| 1. Authentication | `modules/auth.py` | Sign in, get token, manage session lifecycle |
| 2. Discovery | `modules/catalog.py` | List available datasources via Metadata API (GraphQL) or REST fallback |
| 3. Introspection | `modules/introspect_datasource.py` | Retrieve field metadata, parameters, logical table relationships |
| 4. Query Execution | `modules/query.py` | Execute VDS queries, handle streaming, process results |

### Workbook / View Path (Pre-configured Data)

| Phase | Module | Purpose |
|-------|--------|---------|
| 1. Authentication | `modules/auth.py` | Sign in, get token, manage session lifecycle |
| 2. Discovery | `modules/catalog.py` | List workbooks or views via Metadata API or REST fallback |
| 2a. (Optional) | `modules/introspect_workbook.py` | Deep-dive a workbook's sheets, field instances, embedded datasources |
| 3. View Query | `modules/query_view.py` | Retrieve view data via REST, parse CSV |

**Persistence** is handled by `data.py`, which writes outputs to `temp/` in JSON, CSV, and Markdown formats. See [TEMP_DATA.md](./TEMP_DATA.md).

### Choosing the Right Path

```
Agent is assigned a task that requires data
    │
    ├─ This an ad-hoc question and a view already answers it? (pre-configured data)
    │   ├─ YES → list_views() → query_view_data(view_luid) → view data
    │   └─ NO ↓
    │
    ├─ Need custom aggregation, filtering, or field selection?
    │   ├─ YES → list_datasources() → introspect() → query() → VDS data
    │   └─ UNSURE → try query_view_data first, fall back to VDS
    │
    ├─ The query must be a reusable script or incorporated into an app?
    │   ├─ YES → list_datasources() → introspect() → query() → VDS data (not views)
    │   └─ No → query the view or datasource in the REPL without writing to disk
    │
    └─ Need to understand workbook structure?
        ├─ YES → list_workbooks() → introspect_workbook(wb_luid)
        └─ Then → navigate to published datasource via embedded_datasources[].upstream_datasources
```

### Data Flow

```
.env credentials
      │
      ▼
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐     ┌─────────────┐
│    Auth     │ ──▶ │       Catalog        │ ──▶ │     Introspect      │ ──▶ │    Query    │
│  (sign_in)  │     │ list_datasources()   │     │ introspect_ds()     │     │  query()    │
│             │     │ list_workbooks()     │     │ introspect_wb()     │     │  query_vd() │
└─────────────┘     │ list_views()        │     └─────────────────────┘     └─────────────┘
                    └──────────────────────┘              │                        │
                           │                              ▼                        ▼
                           ▼                   temp/datasource_*.json    temp/query_*.csv
                  temp/data_catalog_*.json     temp/inspect_*.md         temp/query_*.json
                  temp/workbook_catalog_*.json temp/workbook_*.json      temp/view_query_*.csv
                  temp/view_catalog_*.json     temp/workbook_inspect_*.md
```

---

## REPL Exploration (default)

The recommended exploration workflow holds catalog, schema, and query results as Python variables and surfaces only printed summaries to the LLM context. This keeps information-dense payloads out of the context window, where they degrade reasoning on linear-complexity tasks.

**Rule:** `print()` only counts, filtered lists, and small row samples. Never print full catalogs or full result sets.

See **[REPL.md](../REPL.md)** for a complete runnable session demonstrating auth → catalog discovery → view exploration → workbook introspection → datasource introspection → VDS query.

---

## Alternative: File-Based Exploration (opt-in)

Use this path when persistence is explicitly needed — not as the default exploration workflow. See [TEMP_DATA.md](./TEMP_DATA.md) for full documentation on file formats, naming conventions, and `jq` exploration commands.

**When to use file-based persistence:**

| Scenario | Use `data.py`? |
|----------|---------------|
| Exploring catalog to answer a question | No — keep in REPL variables |
| Building a query strategy interactively | No — intermediate state in memory |
| User requests a CSV export | **Yes** |
| Multi-session work (resume later) | **Yes** |
| Handing data to another tool | **Yes** |
| Demo / connectivity verification (`main.py`) | **Yes** — the demo is designed for this |

To verify credentials and populate `temp/` with sample data:

```bash
uv run python -m query_tableau_data_py.main
```

> **WARNING**: Always clean up `temp/` when you finish your work. These files may contain sensitive business data.
> ```bash
> rm -f temp/*.json temp/*.csv temp/*.md
> ```

---

## Default Workflow

When users need to query their specific datasources, **write your own script in `scripts/`** using `Session` as the foundation. `main.py` is the demo — read it as a structural reference for the discover → introspect → query pattern, but write a new file rather than modifying it.

> **See [REPL.md](../REPL.md) for a complete REPL exploration session demonstrating this workflow.**

### Required Imports

```python
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.session import Session
from query_tableau_data_py.models import (
    QueryField, QueryFilter, QueryOptions, QueryRequest
)
```

### Write Your Own Orchestrator

```python
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.session import Session
from query_tableau_data_py.models import (
    QueryField, QueryFilter, QueryOptions, QueryRequest
)

config = SdkConfig()

with Session(config) as session:
    # 1. Discover
    sources = session.list_datasources(filter_name="Regional")
    target = next(ds for ds in sources if "Regional" in ds.name)

    # 2. Introspect
    schema = session.introspect(target.luid)

    # 3. Query
    request = QueryRequest(
        datasource_luid=target.luid,
        fields=[
            QueryField(field_caption="Region"),
            QueryField(field_caption="Sales", function="SUM"),
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
        options=QueryOptions(return_format="OBJECTS", row_limit=1000),
    )
    result = session.query(request)
    print(f"Rows: {result.metadata.row_count}")
```

### Workflow Steps

1. Use the REPL exploration pattern above to discover catalog, introspect schema, and test queries — holding all results as Python variables
2. Filter programmatically (`[ds for ds in catalog if ...]`); print only counts and small slices
3. Once you have validated the right datasource and field names interactively, write a clean standalone script **in `scripts/`** using those confirmed values
4. Import `Session` from `query_tableau_data_py.session` in your script
5. Use `session.list_datasources()`, `session.introspect()`, and `session.query()` for custom VDS queries
6. Or use `session.list_views()` and `session.query_view_data()` for quick pre-configured view data
7. Use `session.list_workbooks()` and `session.introspect_workbook()` to understand workbook structure

> **NOTE**: The `Session` class handles authentication lifecycle automatically — transparent 401 retry and sign-out on exit. Import it from `session.py` directly.

---

## Advanced Scenarios

For fine-grained control beyond the default `Session` workflow, see [ADVANCED.md](ADVANCED.md):

| Scenario | What to Use |
|----------|-------------|
| Customize a single call (custom headers, pagination) | Session escape hatches (access `session.config`, `session.token`, `session.conn`) |
| Raw VDS payload for fields not yet in the typed model | `session.query_raw()` with `build_query_payload()` |
| Custom retry logic or long-lived processes | Raw functional API (manual `sign_in`/`sign_out`) |
| Stream large result sets via SSE | [STREAMING.md — http.client escape hatch](../vds/STREAMING.md#implementing-sse-with-httpclient-advanced) |
| Pre-flight validation against schema | `validate_query()` |
| Integrate into async apps (Streamlit, FastAPI) | [INTEGRATION.md](INTEGRATION.md) — `asyncio.to_thread()` wrapping, correct test mocking |

---

## Module Reference

| Module | Purpose | Key Functions/Classes |
|--------|---------|----------------------|
| `session.py` | Auth lifecycle & API delegate | `Session` (context manager), `query_raw()` |
| `main.py` | Demo orchestrator & entry point | `demo()`, `main()` |
| `config.py` | Environment-based configuration | `SdkConfig` (loads `.env` from cwd or skill root) |
| `models.py` | Pydantic data models | `QueryRequest`, `QueryField`, `QueryFilter`, `DatasourceSchema`, `FieldMeta`, `WorkbookSummary`, `ViewSummary`, `WorkbookSchema`, `ViewQueryResult` |
| `errors.py` | Exception hierarchy | `AuthenticationError`, `QueryExecutionError`, `RateLimitError`, `CatalogUnavailableError`, `ViewQueryError` |
| `data.py` | Persistence to `temp/` | `write_catalog()`, `write_schema()`, `write_query_result()`, `write_workbook_catalog()`, `write_view_catalog()`, `write_workbook_schema()`, `write_view_query_result()` |
| `modules/auth.py` | Authentication | `sign_in()`, `sign_out()`, `AuthToken` |
| `modules/catalog.py` | Datasource, workbook, and view discovery | `list_datasources()`, `list_workbooks()`, `list_views()` |
| `modules/introspect_datasource.py` | Datasource schema introspection | `introspect()` |
| `modules/introspect_workbook.py` | Workbook deep-dive introspection | `introspect_workbook()` |
| `modules/query.py` | VDS query execution | `query()`, `query_raw()`, `health_check()`, `build_query_payload()` |
| `modules/query_view.py` | REST-based view data retrieval | `query_view_data()` |
| `modules/validate.py` | Pre-flight validation | Validate queries against schema |

---

## Troubleshooting

### Authentication Fails
- Verify `.env` has correct `TABLEAU_SERVER_URL`, `PAT_NAME`, `PAT_VALUE`
- For Tableau Cloud, include the pod name: `https://prod-useast-b.online.tableau.com`
- Check that the PAT hasn't expired

### No Datasources Found
- Verify the user has permissions to view published datasources
- Check that datasources have "API Access" permission enabled
- Try running without a filter to see all available datasources

### Query Returns Error 404934 (Unknown Field)
- Field captions are case-sensitive; verify exact spelling from introspection
- In a REPL: open a session and run `schema = session.introspect(luid)` then `[f.name for fg in schema.field_groups for f in fg.fields]`

### Rate Limited (429)
- The `Session` class automatically waits and retries once
- For heavy workloads, add delays between requests

See [vds/ERRORS.md](../vds/ERRORS.md) for a full error code reference.
