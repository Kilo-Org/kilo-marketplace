# connectors list

List the connectors that already exist in a given workspace.

## Usage

```bash
airbyte-agent connectors list --json '{"workspace": "my-workspace"}'

# workspace defaults to "default" when omitted
airbyte-agent connectors list --json '{}'
```

`workspace` is optional. If omitted, the command falls back to the workspace named `default` and prints a JSON notice on stderr — the API call still proceeds. To target a different workspace, set `"workspace": "<name>"` in the JSON payload.

## When to use

- Confirming a connector exists before calling `inspect`, `skills docs`, or `execute`.
- Discovering exact connector names to pass to other commands.
- Checking the status of existing connectors.
- Checking the context-store status of a connector (e.g. `loading`, `building`, `preview`, `ready`).

## Response fields

Each item under `data[]` carries the standard connector fields (`id`, `name`, `summarized_source_template`, `created_at`, `updated_at`) plus two enrichment fields merged in from the org credentials endpoint:

- `context_store_status` (string|null) — current state of the connector's context store. Typical values include `loading`, `building`, `preview`, and `ready`. The field is `null` when no matching credential exists for the connector or when the enrichment lookup failed (see stderr notice below).
- `context_store_entity_count` (int) — number of entities currently materialized in the context store. Defaults to `0` when no credential is found or on enrichment failure.

If the org credentials lookup fails, the command still returns the connector list but emits a JSON notice on stderr similar to the workspace-fallback notice. Every item in that response carries `context_store_status: null` and `context_store_entity_count: 0`.

## Filtering output

```bash
airbyte-agent connectors list --fields id,name --json '{}'              # short form
airbyte-agent connectors list --fields data.id,data.name --json '{}'    # long form

# Mixed top-level and row-level paths — use the long form for the row paths
airbyte-agent connectors list --fields data.id,next --json '{}'

# Just the context-store status per connector
airbyte-agent connectors list --fields data.id,data.context_store_status --json '{}'
```

## Related commands

- `connectors list-available` — list templates available to install (different command, different purpose).
- `connectors inspect` — inspect metadata and get `docs_skill_id` for `skills docs`.
- `skills docs` — read connector usage docs before `execute`.
- `connectors describe` — legacy compatibility command for older workflows.
- `connectors create` — install a new connector from a template.

## Hints

- Names returned here can be matched in subsequent commands by connector instance name, template display name, OR template slug — all case-insensitive.
- If two connectors share a name, `inspect`/`execute`/`describe`/`delete` will return a validation error — pass `"id": "<uuid>"` in the JSON payload instead.
