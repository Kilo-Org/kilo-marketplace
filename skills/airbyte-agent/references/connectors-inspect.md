# connectors inspect

Inspect connector metadata and readiness, and get the `docs_skill_id` used by `skills docs`.

## Usage

```bash
airbyte-agent connectors inspect --json '{"workspace": "my-workspace", "name": "my-source"}'

# workspace defaults to "default" when omitted
airbyte-agent connectors inspect --json '{"name": "my-source"}'

# By connector ID instead of name
airbyte-agent connectors inspect --json '{"id": "<connector-id>"}'
```

## When to use

- Before the first `connectors execute` on an unfamiliar connector.
- When you need the authoritative `docs_skill_id` for connector usage docs.
- When checking context-store readiness and warnings before choosing `context_store_search` vs `list`.

## Workflow

```bash
airbyte-agent connectors inspect --json '{"workspace": "default", "name": "hubspot"}'
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>"}' --fields data.markdown
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>", "section": "<exact-section-id>"}' --fields data.markdown
```

Use the `docs_skill_id` exactly as returned. Do not construct `connector-source:<id>` yourself unless you are debugging the current backend convention.

## Do NOT

- Do NOT call `execute` on an unfamiliar connector before reading the relevant docs section.
- Do NOT treat `inspect` as usage documentation by itself — it points you to docs via `docs_skill_id`.
