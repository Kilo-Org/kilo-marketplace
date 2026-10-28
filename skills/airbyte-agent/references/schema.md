# schema

Return the full machine-readable schema for an operation: the CLI-level parameter shape **and** the underlying OpenAPI route's parameters, request body, and response.

> [!IMPORTANT]
> Run `airbyte-agent schema <resource> <operation>` **before** writing code or scripts that consume an operation's output. The `api.response` schema tells you exactly what fields will come back so you can pass `--fields` correctly the first time.

> [!NOTE]
> `schema` takes positional arguments, not a `--json` payload — it is an introspection command, not an API call.

## Usage

```
airbyte-agent schema <resource> <operation>

# Examples
airbyte-agent schema workspaces list
airbyte-agent schema connectors execute
airbyte-agent schema organizations list
```

## Output shape

```jsonc
{
  "description": "...",        // CLI-level operation description
  "params": { ... },           // CLI flag/JSON parameters (what you pass)
  "api": {                     // OpenAPI route info (omitted if no mapping)
    "path": "/api/v1/...",
    "method": "GET",
    "summary": "...",
    "description": "...",
    "parameters": [ ... ],     // query/path/header parameters
    "request_body": { ... },   // present on POST/PATCH/PUT routes
    "response": { ... }        // 200/2xx response schema, $refs inlined
  }
}
```

The two surfaces are intentionally separate:

- **`params`** — what you, as a CLI caller, pass inside the `--json` payload. Includes CLI conveniences (workspace fallback, name/id alternation, etc.).
- **`api`** — what bytes go on the wire to the Airbyte API. Use this to know what fields the response will contain and pick `--fields` accordingly.

## When to use

- **Before building any automation** that depends on an operation's response shape — read `api.response` so you can shape your filtering/parsing precisely.
- **When `--fields` returns something unexpected** — `api.response` shows the exact field names and structure.
- **When discovering the API surface** as an agent — `airbyte-agent schema <r> <op>` is the canonical way to learn what an operation does without making a request.

## Hints

- `airbyte-agent schema` never makes API calls — safe to run without auth, against unfamiliar accounts, etc.
- Errors from `airbyte-agent schema` (unknown resource or operation) are JSON on stderr with exit code 3.
- Operations that don't map to an OpenAPI route omit the `api` block. (`airbyte-agent login` is also purely local but isn't a registered operation — it's a top-level command.)
