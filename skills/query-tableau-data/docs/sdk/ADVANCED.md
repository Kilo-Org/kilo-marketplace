# Advanced Usage — `query_tableau_data_py`

This document covers advanced usage patterns for agents who need fine-grained control over the auth lifecycle, HTTP transport, or query payload construction. Most agents should use `Session` (see [SDK.md — Default Workflow](SDK.md#default-workflow)).

> **Start with [REPL.md](../REPL.md) if you are new to this skill.**

---

## When to Use Advanced Patterns

| Situation | What to Use |
|-----------|-------------|
| Multi-step workflow (discover → introspect → query) | `Session` context manager ([Default Workflow](SDK.md#default-workflow)) |
| Workbook-aware workflow (discover workbooks → view data) | `Session` context manager ([Default Workflow](SDK.md#default-workflow)) |
| Customize a single call (custom headers, logging) | [Session escape hatches](#session-escape-hatches) below |
| Custom retry logic, long-lived process, testing | [Raw functional API](#raw-functional-api-no-session) below |
| VDS field not yet in the typed model | [`session.query_raw()`](#raw-vds-payload-query_raw) below |

---

## Raw Functional API (No Session)

For full control over the auth lifecycle. You are responsible for sign-out — always use `try/finally`.

```python
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.modules import auth, catalog, introspect_datasource, query
from query_tableau_data_py.models import QueryField, QueryRequest

config = SdkConfig()
token = auth.sign_in(config)
try:
    sources = catalog.list_datasources(config, token)
    schema = introspect_datasource.introspect(config, token, sources[0].luid)
    request = QueryRequest(
        datasource_luid=sources[0].luid,
        fields=[QueryField(field_caption="Region")],
    )
    result = query.query(config, token, request)
    print(result.rows[:5])
finally:
    auth.sign_out(token, config)
```

### Workbook-Aware Raw API

The same raw functional API works for workbook and view workflows:

```python
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.modules import auth, catalog, introspect_workbook, query_view

config = SdkConfig()
token = auth.sign_in(config)
try:
    # Discover workbooks
    workbooks = catalog.list_workbooks(config, token, filter_name="Sales Overview")
    if workbooks:
        # Deep-dive workbook introspection
        wb_schema = introspect_workbook.introspect_workbook(config, token, workbooks[0].luid)
        print(f"Workbook: {wb_schema.name}")
        for sheet in wb_schema.sheets:
            print(f"  Sheet: {sheet.name} — {len(sheet.field_instances)} fields")

    # Discover views and query one directly
    views = catalog.list_views(config, token, filter_name="Revenue")
    if views:
        result = query_view.query_view_data(config, token, views[0].luid)
        print(f"View rows: {result.row_count}")
finally:
    auth.sign_out(token, config)
```

### Passing a Shared Connection

When you need a custom SSL context, proxy, or explicit connection reuse, create the `http.client.HTTPSConnection` yourself and pass it as `conn`:

```python
import http.client
import ssl
from urllib.parse import urlparse
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.modules import auth, catalog

config = SdkConfig()
parsed = urlparse(config.base_url)
ssl_ctx = ssl._create_unverified_context()  # e.g. self-signed cert
conn = http.client.HTTPSConnection(
    parsed.hostname, parsed.port or 443, context=ssl_ctx, timeout=config.timeout
)

token = auth.sign_in(config, conn=conn)
try:
    sources = catalog.list_datasources(config, token, conn=conn)
    print(f"{len(sources)} datasources")
finally:
    auth.sign_out(token, config, conn=conn)
    conn.close()
```

**Use the raw functional API when:**
- You need a custom `http.client.HTTPSConnection` (e.g., custom SSL context, proxy settings)
- You are writing tests and want to inject a mock connection directly
- You need to implement custom retry logic beyond the Session's single-retry behaviour

**Do not use it** for normal agent workflows — `Session` ([Default Workflow](SDK.md#default-workflow)) is cleaner and safer.

---

## Raw VDS Payload: `query_raw()`

If the typed `QueryRequest` model does not yet expose a VDS field, construct the payload manually and call `session.query_raw()`:

```python
from query_tableau_data_py.modules.query import build_query_payload
from query_tableau_data_py.models import QueryField, QueryRequest
from query_tableau_data_py.session import Session
from query_tableau_data_py.config import SdkConfig

with Session(SdkConfig()) as session:
    # Build the typed model first
    request = QueryRequest(
        datasource_luid=target.luid,
        fields=[QueryField(field_caption="Sales", function="SUM")],
    )
    # Serialise to dict and mutate
    payload = build_query_payload(request)
    payload["query"]["fields"][0]["someNewVdsField"] = "value"

    result = session.query_raw(payload)
```

`build_query_payload` is an internal function. Treat the resulting dict as opaque — its shape matches the VDS OpenAPI schema at `schemas/vds.20261.0.openapi.json`.

---

## Session Escape Hatches

Access `Session` internals to call functional APIs directly while still benefiting from Session-managed auth and sign-out:

```python
from query_tableau_data_py.modules import catalog
from query_tableau_data_py.session import Session
from query_tableau_data_py.config import SdkConfig

with Session(SdkConfig()) as session:
    # Bypass the session delegate for full control over a single call
    sources = catalog.list_datasources(
        session.config,
        session.token,
        conn=session.conn,
        filter_name="Sales",
        page_size=50,   # custom pagination
    )

    # Same escape hatch works for workbook and view catalog calls
    workbooks = catalog.list_workbooks(
        session.config,
        session.token,
        conn=session.conn,
        filter_project="Finance",
    )
    views = catalog.list_views(
        session.config,
        session.token,
        conn=session.conn,
        filter_name="Revenue",
    )
```

**Available escape hatches on `Session`:**

| Property | Type | Purpose |
|----------|------|---------|
| `session.config` | `SdkConfig` | The loaded configuration |
| `session.token` | `AuthToken` | The active auth token (raises if not authenticated) |
| `session.conn` | `http.client.HTTPSConnection` | The shared HTTP connection |

**Session delegate methods (workbook/view):**

| Method | Delegates to | Returns |
|--------|-------------|---------|
| `session.list_workbooks(**kw)` | `catalog.list_workbooks()` | `list[WorkbookSummary]` |
| `session.list_views(**kw)` | `catalog.list_views()` | `list[ViewSummary]` |
| `session.introspect_workbook(luid)` | `introspect_workbook.introspect_workbook()` | `WorkbookSchema` |
| `session.query_view_data(luid, **kw)` | `query_view.query_view_data()` | `ViewQueryResult` |

---

## Streaming Queries

`query_stream()` is not part of the SDK's public API. The buffered `session.query()` covers all standard REPL exploration and script use cases.

For agents that specifically need row-by-row SSE streaming of very large result sets, see the self-contained escape hatch in [STREAMING.md — Implementing SSE with http.client](../vds/STREAMING.md#implementing-sse-with-httpclient-advanced).

---

## Pre-flight Validation

Run validation against the datasource schema before sending a query to catch errors client-side:

```python
from query_tableau_data_py.modules.validate import validate_query

warnings = validate_query(request, schema)
if warnings:
    print("Warnings:", warnings)
# validate_query raises ValidationError on rule violations before returning
```

---

## Token Lifecycle

Tokens are valid for approximately 240 minutes. The `Session` context manager handles token expiry transparently:

- On `AuthenticationError` (401), `Session` re-signs-in and retries the call **once**
- On `RateLimitError` (429), `Session` waits `retry_after` seconds and retries **once**
- 5xx errors and timeouts are **not** retried — they surface to the caller

For long-running processes that outlive a token, create a new `Session`:

```python
# Each Session gets a fresh token
for batch in batches:
    with Session(config) as session:
        result = session.query(build_request(batch))
        process(result)
```

See [AUTH.md](../api/AUTH.md) for full token lifecycle documentation.
