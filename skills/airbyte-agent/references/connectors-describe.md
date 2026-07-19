# connectors describe

Legacy compatibility command that shows a connector's available entities and actions by calling the older rich describe flow.

> [!IMPORTANT]
> Prefer `connectors inspect` plus `skills docs` for new workflows. Use `connectors describe` only when the new inspect/docs endpoints are unavailable or a legacy script depends on the old merged schema shape.

## Usage

```bash
airbyte-agent connectors describe --json '{"workspace": "my-workspace", "name": "my-source"}'

# workspace defaults to "default" when omitted
airbyte-agent connectors describe --json '{"name": "my-source"}'

# By connector ID instead of name
airbyte-agent connectors describe --json '{"id": "<connector-id>"}'
```

`workspace` is optional; if omitted while using `name`, the command falls back to the workspace named `default` and prints a JSON notice on stderr.

## When to use

- Maintaining an existing script that consumes the old `schema` field.
- Working against an environment where `connectors inspect` or `skills docs` is unavailable.
- Comparing legacy schema output during migration.

## Workflow

```bash
# 1. Find the connector
airbyte-agent connectors list --json '{"workspace": "my-workspace"}'

# 2. Preferred: inspect and read docs
airbyte-agent connectors inspect --json '{"workspace": "my-workspace", "name": "my-source"}'
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>"}' --fields data.markdown

# Legacy fallback: describe it
airbyte-agent connectors describe --json '{"workspace": "my-workspace", "name": "my-source"}'

# 3. Execute the discovered entity + action
airbyte-agent connectors execute --json '{
  "workspace": "my-workspace",
  "name": "my-source",
  "entity": "users",
  "action": "context_store_search",
  "select_fields": ["id", "email"]
}'
```

For new executions, open [`connectors-inspect.md`](connectors-inspect.md), [`skills-docs.md`](skills-docs.md), and [`connectors-execute.md`](connectors-execute.md) before composing the `execute` call.

## Do NOT

- Do NOT use this as the default discovery path for new workflows — use `connectors inspect` plus `skills docs`.
- Do NOT cache describe output across CLI versions — the schema can change when connectors update.
