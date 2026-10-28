# skills list

List connector and static skill docs available in a workspace.

## Usage

```bash
airbyte-agent skills list --json '{"workspace": "default", "limit": 20}'
airbyte-agent skills list --json '{"workspace": "default", "limit": 20, "cursor": "<next_cursor>"}'
```

`workspace` is optional and defaults to the configured workspace, then `default`.

## When to use

- Discovering available connector and agent skill docs.
- Checking whether a static skill such as `agent:mcp` is available.
- Paging through docs metadata with `next_cursor`.

## Do NOT

- Do NOT use list output as execution guidance. Read exact docs with `skills docs`.
- Do NOT invent skill IDs for connectors. Prefer `docs_skill_id` from `connectors inspect`.
