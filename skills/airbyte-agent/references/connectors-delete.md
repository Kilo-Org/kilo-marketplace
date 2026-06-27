# connectors delete

Permanently delete a connector from a workspace.

> [!IMPORTANT]
> Deletion is irreversible. Confirm with the user before running this command unless they have explicitly authorized it.

## Usage

```bash
airbyte-agent connectors delete --json '{"workspace": "my-workspace", "name": "my-source"}'

# By connector ID instead of name
airbyte-agent connectors delete --json '{"id": "<connector-id>"}'
```

`workspace` is optional. If omitted while using `name`, the command falls back to the workspace named `default` and prints a JSON notice on stderr. **Confirm with the user before relying on the fallback for a delete** — operating on the wrong workspace's connector is hard to recover from.

## Confirmation prompt

By default, delete asks `Type 'yes' to confirm:` on stderr and reads from stdin. Anything other than an exact `yes` aborts.

Agents driving the CLI typically can't answer the prompt. There are two ways to allow non-interactive deletes:

1. **Per-machine permission (recommended)**: set `"allow_destructive": true` in `~/.airbyte-agent/settings.json`. The user should explicitly grant this — do not silently flip it on.
2. **Per-invocation env var**: `AIRBYTE_ALLOW_DESTRUCTIVE=true airbyte-agent connectors delete ...`.

If neither is set and stdin isn't a TTY, the command refuses with a `validation_error` and a hint pointing at the setting (exit 4).

## Error recovery

- **Not found** (exit 3): run `connectors list` to confirm the name exists in the workspace.
- **Ambiguous name** (exit 4): two connectors share a name — pass `"id": "<uuid>"` in the JSON payload instead.
- **`destructive action requires confirmation but no TTY is available`** (exit 4): stdin isn't a terminal and `allow_destructive` isn't enabled. Ask the user to grant the permission in settings.json (or re-run interactively).
- **`destructive action cancelled by user`** (exit 4): the user typed something other than `yes`. Don't retry without checking with them.

## Do NOT

- Do NOT delete a connector without explicit user confirmation.
- Do NOT use this command to "reset" a connector's credentials — instead, delete and recreate, or update credentials directly via the connector configuration flow.
