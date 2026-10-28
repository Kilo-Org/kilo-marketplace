# skills docs

Read usage documentation for a skill. For connector docs, pass the `docs_skill_id` returned by `connectors inspect`.

## Usage

```bash
# Outline plus default guidance
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>"}' --fields data.markdown

# Exact section from the outline
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>", "section": "<exact-section-id>"}' --fields data.markdown

# Static docs are workspace-scoped by default
airbyte-agent skills docs --json '{"workspace": "default", "id": "agent:mcp"}' --fields data.markdown

# Raw backend envelope for scripts
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>", "format": "json"}'
```

Default output is JSON with rendered markdown at `data.markdown`. `format: "json"` returns the backend docs envelope unchanged.

## Workspace scoping

- For `connector-source:*` IDs, omit `workspace` unless the user explicitly asks for a workspace-scoped read.
- If `workspace` is supplied, the CLI resolves it and sends `workspace_id`.
- For static/non-connector skill IDs such as `agent:mcp`, the CLI resolves and sends the supplied or default workspace.

## Workflow

```bash
airbyte-agent connectors inspect --json '{"workspace": "default", "name": "slack"}'
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>"}' --fields data.markdown
airbyte-agent skills docs --json '{"id": "<docs_skill_id from inspect>", "section": "actions.messages.create"}' --fields data.markdown
```

Use exact section IDs from the outline. They are stable IDs, not display titles.

## Do NOT

- Do NOT construct connector docs IDs manually when `connectors inspect` can return `docs_skill_id`.
- Do NOT pass a section title as `section`; pass the exact section ID.
- Do NOT call `connectors execute` until you have read the section for the entity/action you plan to use.
