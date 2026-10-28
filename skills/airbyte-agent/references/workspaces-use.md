# workspaces use

Persist a default workspace name to `~/.airbyte-agent/settings.json`. After running this, any command that takes a `workspace` parameter and doesn't receive one will fall back to this value (in place of the literal `"default"`).

> [!NOTE]
> The command verifies the workspace exists via the API before writing. The canonical-cased name from the API is what gets persisted (so typing `production` will save `Production` if that's how it's stored).

## Usage

```bash
airbyte-agent workspaces use --json '{"name": "Production"}'
```

`name` is required. Match is case-insensitive against the workspace's actual `name` field.

## When to use

- **Right after `airbyte-agent login`** — typically the second step in onboarding once you know which workspace you'll be working in.
- **When switching projects** — instead of typing `--json '{"workspace": "..."}'` on every command, set it once.
- **After creating a new workspace** that should become the default.

## Output

```jsonc
{
  "status": "saved",
  "workspace": "Production",
  "message": "default workspace set to \"Production\" in ~/.airbyte-agent/settings.json"
}
```

## Errors

| Error | Cause | Fix |
|---|---|---|
| `validation_error` (exit 4) | `name` parameter missing | Pass `--json '{"name": "<workspace>"}'` |
| `not_found` (exit 3) on workspace | Workspace doesn't exist in this account | Run `airbyte-agent workspaces list --json '{}'` to see real names |
| `not_found` (exit 3) on settings file | `~/.airbyte-agent/settings.json` missing | Run `airbyte-agent login` first |
| `auth_error` (exit 2) | Credentials invalid | Run `airbyte-agent login` to refresh credentials |

## Hints

- This command writes to disk. If you're configured via `AIRBYTE_*` env vars instead of `settings.json`, the env vars still win at runtime — the saved value won't take effect until you unset the env override.
- To clear the default and revert to the literal `"default"` fallback, edit the file and remove the `workspace` field, or set it to `"default"`.
