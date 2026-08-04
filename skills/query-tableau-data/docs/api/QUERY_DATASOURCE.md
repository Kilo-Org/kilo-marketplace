# Querying the VizQL Data Service

The **VizQL Data Service (VDS)** is the execution layer for querying published Tableau data sources. It is an HTTP API available on Tableau Cloud and Tableau Server 2025.1+. This document covers **Phase 3: Query Execution** in the agent's three-phase pipeline.

1. **Discovery** — Find data sources via the Data Catalog. See [CATALOG.md](./CATALOG.md).
2. **Introspection** — Retrieve field metadata and datasource model. See [INTROSPECT_DATASOURCE.md](./INTROSPECT_DATASOURCE.md).
3. **Execution** — Construct and submit VDS queries. Covered in this document.

> **Prerequisites:** You must authenticate via the Tableau REST API as described in [AUTH.md](./AUTH.md) before calling any VDS endpoint.

> _NOTE_: VDS only works with published datasources, not those embedded inside workbooks.

---

## Health Check

Before executing queries, confirm that VDS is reachable.

**METHOD**: `GET /api/v1/vizql-data-service/simple-request`

**HEADERS**:

```
X-Tableau-Auth: <token>
```

**REQUEST PAYLOAD**: None

**RESPONSE PAYLOAD**:

```json
{
  "message": "ahoy"
}
```

_Example Request_:
```bash
curl "https://{my-server}/api/v1/vizql-data-service/simple-request" \
  -H "X-Tableau-Auth: <token>"
```

---

## Query a Data Source

**METHOD**: `POST /api/v1/vizql-data-service/query-datasource`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```json
{
  "datasource": {
    "datasourceLuid": "<luid>",
    "connections": [
      {
        "connectionLuid": "optional-connection-luid",
        "connectionUsername": "db-user",
        "connectionPassword": "db-password"
      }
    ]
  },
  "query": {
    "fields": [
      { "fieldCaption": "Category" },
      { "fieldCaption": "Sales", "function": "SUM" }
    ],
    "filters": [
      {
        "field": { "fieldCaption": "Category" },
        "filterType": "SET",
        "values": ["Technology", "Furniture"]
      }
    ],
    "parameters": [
      {
        "parameterCaption": "Date Range",
        "value": "2024-01-01"
      }
    ]
  },
  "options": {
    "returnFormat": "OBJECTS",
    "debug": false,
    "disaggregate": false,
    "rowLimit": 1000
  }
}
```

### The `datasource` Object

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `datasourceLuid` | string | Yes | Locally unique identifier of the published data source |
| `connections` | array | No | Array of database credential objects for data sources requiring authentication |

**Connection object**:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `connectionLuid` | string | No | LUID of the specific connection (required when a data source has multiple connections) |
| `connectionUsername` | string | Yes | Database username |
| `connectionPassword` | string | Yes | Database password |

> _Note_: Multiple connections are supported for data sources with multiple database connections. If a data source has only one connection, the `connectionLuid` is optional.

---

## Query Options

Control how VDS processes and returns data.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `returnFormat` | `"OBJECTS"` \| `"ARRAYS"` | `"OBJECTS"` | Format of the response data |
| `debug` | boolean | `false` | Include debug information in the response |
| `disaggregate` | boolean | `false` | Return row-level data without aggregation |
| `rowLimit` | integer (>=1) | — | Maximum rows to return (2026.1+) |
| `bypassMetadataCache` | boolean | `false` | Bypass the metadata cache for fresh data |
| `interpretFieldCaptionsAsFieldNames` | boolean | `false` | Use `fieldName` instead of `fieldCaption` in queries |
| `includeHiddenFields` | boolean | `false` | Include hidden fields in `readMetadata` response |
| `includeGroupFormulas` | boolean | `false` | Include group formulas in `readMetadata` response |
| `returnServerSentEvents` | boolean | `false` | Stream results using SSE protocol (2026.1+) |

### Response Formats

**`OBJECTS`** (default): Each row is a JSON object with field names as keys.

```json
{
  "data": [
    { "Category": "Technology", "SUM(Sales)": 12345.67 },
    { "Category": "Furniture", "SUM(Sales)": 8901.23 }
  ]
}
```

> **Response key naming:** Dimensions (fields without a `function`) use their bare `fieldCaption` as the key (e.g., `"Category"`). Aggregated fields use the pattern `FUNCTION(fieldCaption)` (e.g., `"SUM(Sales)"`). To override this behavior and get a clean key like `"Sales"`, set `fieldAlias` on the field in the request. See [INTROSPECT_DATASOURCE.md § Response Key Naming](./INTROSPECT_DATASOURCE.md#response-key-naming).

**`ARRAYS`**: Each row is an array of values in the same order as the requested fields.

```json
{
  "data": [
    ["Technology", 12345.67],
    ["Furniture", 8901.23]
  ]
}
```

A short summary should be printed to `stdout`:
```bash
Queried datasource <luid> (<name>).
- 2 fields, 1 filter
- 42 rows returned
Saved: temp/query_<luid>_<timestamp>.json
       temp/query_<luid>_<timestamp>.csv
```

> **IMPORTANT**: Query results are saved to `temp/`, see [TEMP_DATA.md](../sdk/TEMP_DATA.md) for best practices when handling response data.

---

### Error Handling

VDS distinguishes between **pre-streaming** and **during-streaming** errors.

**Pre-streaming errors** (HTTP non-200):

```json
{
  "errorCode": "400000",
  "message": "Bad request",
  "datetime": "2025-03-14T12:00:00Z",
  "debug": {},
  "tab-error-code": "400000"
}
```

**During-streaming errors** (HTTP 200 with error object in the stream):

```json
{
  "errorCode": "400804",
  "message": "Response too large",
  "datetime": "2025-03-14T12:00:00Z",
  "debug": {},
  "tab-error-code": "400804"
}
```

> **IMPORTANT**: See [vds/ERRORS.md](../vds/ERRORS.md) for a full catalog of error codes.

> _Note_: You must still handle the HTTP status code. A 200 response does not guarantee success if an error object appears in the stream.

---

## List Supported Functions

Returns the Tableau functions supported for a specific data source. These are the functions that can be used when creating calculated fields.

**METHOD**: `POST /api/v1/vizql-data-service/list-supported-functions`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD:**

```json
{
  "datasource": {
    "datasourceLuid": "<luid>"
  }
}
```

**RESPONSE PAYLOAD:**

```json
{
  "data": [
    {
      "name": "SUM",
      "argumentTypes": ["REAL"],
      "returnType": "REAL"
    },
    {
      "name": "DATEDIFF",
      "argumentTypes": ["STRING", "DATETIME", "DATETIME"],
      "returnType": "INTEGER"
    }
  ]
}
```

---

## Troubleshooting

### Health Check Fails
Use `simple-request` to verify VDS is enabled and reachable:
```bash
curl "https://{my-server}/api/v1/vizql-data-service/simple-request" \
  -H "X-Tableau-Auth: <token>"
```
If this returns `403157` or a non-200 status, VDS is disabled or the user lacks API Access on the data source.

### Debug Information
Set `debug: true` in the request `options` to receive additional diagnostic information in the response.

### Common JSON Errors
- **Missing or incomplete JSON**: Returns `400000`. Validate the request body with a JSON linter.
- **Invalid formula**: Returns `400800`. Verify Tableau calculation syntax at
- **Unknown field**: Returns `404934`. Ensure the `fieldCaption` matches the datasource metadata exactly (case-sensitive).

### Getting Help
For the latest OpenAPI schema and reference documentation, see the [VizQL Data Service OpenAPI Schema](../../src/schemas/vds.20261.0.openapi.json).
