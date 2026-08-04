# connectors update

Open the user's browser to the credentials page so they can edit an existing connector's configuration. The CLI never accepts credentials directly — entry happens in the browser-based widget.

## When to use

- A connector's OAuth token expired and `connectors execute` started returning `auth_error`.
- The user rotated their API key for a SaaS source.
- The user explicitly wants to change a connector's configuration (auth, entity selection, etc.).

Do NOT use this command for renaming a connector or other metadata-only edits — those would need a real PUT call, which this command does not make.

## Usage

```bash
airbyte-agent connectors update --json '{"workspace": "my-workspace", "name": "my-source"}'

# By connector ID instead of name
airbyte-agent connectors update --json '{"id": "<connector-id>"}'
```

`workspace` is optional when used with `name` — it falls back to the configured default workspace (then to `default`) and a JSON notice is printed to stderr.

## What happens

1. The CLI looks up the connector by name in the workspace (or accepts the `id` directly).
2. It builds the URL `<webapp>/organizations/<org_id>/credentials`, prints the action message + a confirmation prompt to stderr: `Open <URL> in your browser? Type 'yes' to confirm (skips after 10s): `.
3. **If** the user types `yes` (case-insensitive, whitespace-trimmed) within 10 seconds, the CLI opens the URL in the user's default browser.
4. **Otherwise** (`no`, any other input, EOF, or timeout — typical for MCP/CI/piped invocations where stdin is empty), the browser is NOT opened. Exit code is still 0; the URL is still returned.
5. The CLI prints a JSON object on stdout with `url`, `connector_id`, `browser_opened: bool`, and `message` (leading with **"Connectors cannot be edited through the CLI. Visit the link below to update the connector config"** then the pencil-icon hint).
6. The user follows the link, finds the named connector in the credentials list, and clicks the pencil icon — that launches the embedded edit dialog where credentials are re-entered.

**Agent guidance**: when driving the CLI from an MCP/automation context, expect `browser_opened: false` (stdin is closed → instant EOF → no open). Relay the `url` to the human and let them open it themselves.

`AIRBYTE_WEBAPP_URL` overrides the base URL for staging/preview environments.

## Workflows

**Credential rotation after `auth_error`**

```bash
# 1. Identify the failing connector
airbyte-agent connectors list --json '{"workspace": "my-workspace"}'

# 2. Launch the edit flow
airbyte-agent connectors update --json '{"workspace": "my-workspace", "name": "my-source"}'

# 3. Wait for the user to confirm they completed the browser flow, then re-run the failing call
airbyte-agent connectors execute --json '{"workspace": "my-workspace", "name": "my-source", "entity": "...", "action": "..."}'
```

## Error recovery

- **`auth_error`** (exit 2) — your CLI session token expired. Run `airbyte-agent login` and retry.
- **`not_found`** (exit 3) — the name doesn't exist in that workspace. Run `connectors list --json '{"workspace": "..."}'` to see what's actually there.
- **`validation_error: provide either 'id' or 'name', not both`** (exit 4) — pick one.
- **`validation_error: either 'name' + 'workspace' or 'id' is required`** (exit 4) — pass at least one form of identification.
- **`validation_error: ambiguous: N connectors named "X" in workspace "Y"`** (exit 4) — use `"id": "<uuid>"` instead.
- **`validation_error: no organization_id configured`** (exit 4) — run `airbyte-agent login` (the login flow records the org id in settings.json).

## Do NOT

- Do NOT ask the user to paste credentials into the chat or the CLI. The CLI does not take credentials as parameters — entry happens exclusively in the browser-based widget.
- Do NOT manually construct a PUT request to `/api/v1/integrations/connectors/{id}` as a "shortcut". The widget owns secret handling and a direct PUT bypasses it.
- Do NOT use this command for irreversible operations like deleting/replacing a connector — for that, use `connectors delete` and `connectors create`.
