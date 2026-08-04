# workspaces list

List workspaces in the organization. Workspace names are the identifier passed to almost every connector command, so this is typically the first command in a session.

> [!IMPORTANT]
> If only one workspace exists, use it directly without prompting the user. Most accounts have a single workspace.

> [!NOTE]
> Pagination is automatic — all workspaces are returned in a single response regardless of server-side page size.

## Usage

```bash
airbyte-agent workspaces list --json '{}'
airbyte-agent workspaces list --json '{"name_contains": "production"}'
airbyte-agent workspaces list --json '{"status": "active"}'
```

Run `airbyte-agent schema workspaces list` to see the full parameter schema.

## Filtering output

```bash
airbyte-agent workspaces list --fields name,status --json '{}'              # short form
airbyte-agent workspaces list --fields data.name,data.status --json '{}'    # long form

# Mixed top-level and row-level paths — use the long form for the row paths
airbyte-agent workspaces list --fields data.name,next --json '{}'
```

## Discovery flow

1. `airbyte-agent workspaces list --json '{}'` — see all workspaces.
2. Note the exact `name` value.
3. Either:
   - Pass that name into each command: `--json '{"workspace": "<name>"}'`, or
   - Persist it as the default once: `airbyte-agent workspaces use --json '{"name": "<name>"}'`. Subsequent commands will fall back to this when `workspace` is omitted.

## Do NOT

- Do NOT prompt the user to pick a workspace if only one exists.
- Do NOT assume workspace names — always discover them first.
- Do NOT pass workspace UUIDs to commands that accept `workspace` — the CLI expects the human-readable name.

## Hints

- Use `name_contains` for partial matching when the exact name is unknown.
- The `limit` parameter controls server-side page size; results are still returned in full.
