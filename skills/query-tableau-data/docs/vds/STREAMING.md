## Streaming and Error Checking (2026.1+)

Starting in Tableau 2026.1, VDS supports streaming results to improve performance and remove the previous 1 GB response size limit.

> **Requires Tableau >= 2026.1**. On earlier versions, results are returned as a single JSON response body.

### JSON Streaming

When `returnServerSentEvents` is `false` (or omitted), VDS streams newline-delimited JSON objects:

```json
{"Category":"Technology","Sales":12345.67}
{"Category":"Furniture","Sales":8901.23}
```

### Server-Sent Events (SSE)

Set `returnServerSentEvents: true` to receive results via the SSE protocol (`Content-Type: text/event-stream`).

**SSE Event Types:**

| Event Type | Description |
|------------|-------------|
| `METADATA` | Column metadata (first event) — describes columns and their data types |
| `DATA` | Result row data — one event per row |
| `ERROR` | Error during streaming — indicates a failure after the response started |

**Example SSE Response:**

```text
event: METADATA
data: {"columns":[{"name":"Category","dataType":"STRING"},{"name":"Sales","dataType":"REAL"}]}

event: DATA
data: {"Category":"Technology","Sales":12345.67}

event: DATA
data: {"Category":"Furniture","Sales":8901.23}
```

---

### METADATA Event Schema

The `METADATA` event is always the first event in an SSE stream. It describes the shape of the result set.

| Property | Type | Description |
|----------|------|-------------|
| `columns` | array | Array of column descriptors |
| `columns[].name` | string | Column name (matches `fieldCaption` or `fieldAlias`) |
| `columns[].dataType` | string | One of: `STRING`, `INTEGER`, `REAL`, `BOOLEAN`, `DATE` |

---

### ERROR Event Handling

An `ERROR` event can arrive at any point during streaming — even after some `DATA` events have already been received. This is distinct from pre-streaming HTTP errors (which return non-200 status codes).

**Example ERROR event:**

```text
event: ERROR
data: {"errorCode":"400804","message":"Response too large","datetime":"2025-03-14T12:00:00Z"}
```

**Handling strategy:**

1. Always check for `ERROR` events while consuming the stream.
2. If an `ERROR` event is received, discard any partially received data — the result set is incomplete.
3. The error payload uses the same schema as pre-streaming errors (see [ERRORS.md](./ERRORS.md)).

---

### Interaction with Query Options

| Option | Streaming Behavior |
|--------|-------------------|
| `returnFormat: "OBJECTS"` | Each `DATA` event contains a JSON object with field names as keys |
| `returnFormat: "ARRAYS"` | Each `DATA` event contains a JSON array of values (column order matches `METADATA`) |
| `rowLimit` | The stream terminates after the specified number of `DATA` events |
| `debug: true` | Debug information is included in `ERROR` events if they occur |

> _Note_: `rowLimit` is also a 2026.1+ feature. On earlier versions, you must filter the data source to control result size.

---

### When to Use Streaming

| Scenario | Recommended Mode |
|----------|-----------------|
| Small result sets (< 10k rows) | Standard (non-streaming) is fine |
| Large result sets (> 100k rows) | Enable streaming to avoid memory issues |
| Real-time consumption (e.g., piping to a file) | SSE (`returnServerSentEvents: true`) |
| Programmatic row-by-row processing | JSON streaming (default when 2026.1+) |

---

### Related Documentation

- [QUERY_DATASOURCE.md](../api/QUERY_DATASOURCE.md) — full query request/response structure
- [ERRORS.md](./ERRORS.md) — complete error code reference
- [LIMITATIONS.md](./LIMITATIONS.md) — version gating for streaming features

---

## Implementing SSE with http.client (Advanced)

> **Most agents do not need this section.** The SDK's buffered `session.query()` handles all standard REPL exploration and script use cases. Use this escape hatch only when you specifically need row-by-row streaming of very large result sets without introducing external HTTP dependencies.

The SDK's `query()` method reads the full response body into memory before returning. For very large result sets (hundreds of thousands of rows), you may want to consume the SSE stream line-by-line to avoid buffering the entire payload. This section shows how to do that directly with Python's `http.client` stdlib — no additional packages required.

### How SSE Works Over http.client

The VDS SSE response is a `text/event-stream` body delivered over a standard HTTP/1.1 connection. Each event is a pair of lines:

```
event: <TYPE>\r\n
data: <JSON>\r\n
\r\n
```

Because `http.client.HTTPResponse` exposes the socket as a file-like object, you can read it line-by-line using `makefile()`.

### Self-Contained SSE Example

```python
import http.client
import json
import ssl
from urllib.parse import urlparse

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.modules.auth import sign_in, sign_out
from query_tableau_data_py.models import QueryField, QueryOptions, QueryRequest

config = SdkConfig()

# --- Build SSL context ---
ssl_ctx = ssl.create_default_context() if config.ssl_verify else ssl._create_unverified_context()

# --- Parse host from base URL ---
parsed = urlparse(config.base_url)
host = parsed.hostname
port = parsed.port or 443
base_path = parsed.path.rstrip("/")

conn = http.client.HTTPSConnection(host, port, context=ssl_ctx, timeout=config.timeout)

token = sign_in(config, conn=conn)
try:
    # Build a VDS query payload with SSE enabled
    request = QueryRequest(
        datasource_luid="<your-datasource-luid>",
        fields=[
            QueryField(field_caption="Region"),
            QueryField(field_caption="Sales", function="SUM"),
        ],
        options=QueryOptions(return_server_sent_events=True),
    )
    payload = json.dumps({
        "query": {
            "fields": [
                {"fieldCaption": f.field_caption, **({"function": f.function} if f.function else {})}
                for f in request.fields
            ],
            "returnFormat": "OBJECTS",
            "returnServerSentEvents": True,
        }
    }).encode("utf-8")

    path = f"{base_path}/api/v1/sites/{token.site_id}/datasources/{request.datasource_luid}/query"
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
        "x-tableau-auth": token.token,
    }

    conn.request("POST", path, body=payload, headers=headers)
    resp = conn.getresponse()

    if resp.status >= 400:
        raise RuntimeError(f"VDS error {resp.status}: {resp.read().decode()}")

    # --- Consume SSE stream line-by-line ---
    columns = None
    row_count = 0

    reader = resp.makefile("r", encoding="utf-8")
    event_type = None

    for raw_line in reader:
        line = raw_line.rstrip("\r\n")

        if line.startswith("event:"):
            event_type = line[len("event:"):].strip()

        elif line.startswith("data:"):
            data = json.loads(line[len("data:"):].strip())

            if event_type == "METADATA":
                columns = [col["name"] for col in data["columns"]]
                print(f"Columns: {columns}")

            elif event_type == "DATA":
                row_count += 1
                # Process the row here — never accumulate all rows in memory
                if row_count <= 3:
                    print(data)  # Sample only; remove for production

            elif event_type == "ERROR":
                raise RuntimeError(
                    f"Stream error {data.get('errorCode')}: {data.get('message')}"
                )

        elif line == "":
            # Blank line = end of event; reset type
            event_type = None

    print(f"\nTotal rows streamed: {row_count}")

finally:
    sign_out(token, config, conn=conn)
    conn.close()
```

### Key Points

| Concern | Detail |
|---------|--------|
| **`resp.makefile("r")`** | Wraps the socket as a text iterator — yields one line per `\r\n`. Do not call `resp.read()` first; that would consume the body. |
| **Event boundary** | A blank line (`""`) separates events. Reset `event_type` on blank lines. |
| **`METADATA` event** | Always arrives first. Parse column names before processing `DATA` events. |
| **`ERROR` event** | Can arrive mid-stream after `DATA` events have been received. The partial result is incomplete — discard it and raise. |
| **Memory** | Process each row in-place. Do not accumulate `result.rows` — that defeats the purpose of streaming. |
| **Connection reuse** | This example creates a dedicated connection. If you already have a `Session` open, you can pass `session._conn` as `conn` to `sign_in()`, but be aware that consuming the SSE stream will block the connection until the stream ends. |
