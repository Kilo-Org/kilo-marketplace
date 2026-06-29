# organizations use

Persist a default organization ID to `~/.airbyte-agent/settings.json`. After running this, every API call the CLI makes scopes to this organization (via the `X-Organization-Id` header).

> [!NOTE]
> The command verifies the UUID belongs to the authenticated account before writing. Match is case-insensitive, but the ID is saved as it appears in the API response (typically lowercase).

## Usage

```bash
airbyte-agent organizations use --json '{"id": "11111111-1111-1111-1111-111111111111"}'
```

`id` is required and must be a UUID that appears in `airbyte-agent organizations list`.

## When to use

- **When you belong to multiple organizations** and want to switch the CLI's default without re-running `airbyte-agent login --org-id <uuid>`.
- **After `airbyte-agent login`** if the login flow auto-picked the wrong org (e.g. you had a single-org account that just gained a second org).
- **In CI / agent harnesses** where the settings file has been seeded but the org needs to change between runs.

## Output

```jsonc
{
  "status": "saved",
  "organization_id": "11111111-1111-1111-1111-111111111111",
  "message": "default organization set to \"11111111-1111-1111-1111-111111111111\" in ~/.airbyte-agent/settings.json"
}
```

## Errors

| Error | Cause | Fix |
|---|---|---|
| `validation_error` (exit 4) | `id` parameter missing | Pass `--json '{"id": "<uuid>"}'` |
| `not_found` (exit 3) on organization | UUID does not belong to the authenticated account | Run `airbyte-agent organizations list --json '{}'` to see the real UUIDs |
| `not_found` (exit 3) on settings file | `~/.airbyte-agent/settings.json` missing | Run `airbyte-agent login` first |
| `auth_error` (exit 2) | Credentials invalid | Run `airbyte-agent login` to refresh credentials |

## Hints

- This command writes to disk. If you're configured via `AIRBYTE_ORGANIZATION_ID` instead of `settings.json`, the env var still wins at runtime — the saved value won't take effect until you unset the env override.
- Use `airbyte-agent organizations list --fields id,organization_name --json '{}'` to find the UUID you need.
