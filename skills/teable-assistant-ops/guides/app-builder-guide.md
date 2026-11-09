# App Builder Guide

## When to Use

- Dashboards with live data, custom web interfaces, interactive tools, monitoring panels
- **Do NOT use for**: simple one-time charts — use inline HTML code blocks instead
- **Do NOT duplicate**: basic CRUD / admin interfaces — the database already has built-in UI

## Workflow

1. `app list` — check existing apps (update existing instead of creating duplicate)
2. `app create` / `app update` — create or update app
3. Include `--table-ids` to give the app data access
4. The app runtime includes an AI API for text and image generation — pass AI-related features in `--prompt` and the builder handles integration

**Optional capabilities** (applied to an app independently, in any order):
- **AI access** — `app ai-enable` + `app ai-docs` (see [AI in apps](#ai-in-apps))
- **End-user login** — `app login-config` (see [App login / authentication](#app-login--authentication))
- **Publishing** — `app publish` / `app status` / `app unpublish` (see [Publishing](#publishing))

```bash
# Create new app
teable app create \
  --name "Sales Dashboard" \
  --prompt "build a sales dashboard showing monthly revenue trends" \
  --table-ids '["tblXXX","tblYYY"]'

# Update existing app
teable app update \
  --app-id appXXX \
  --prompt "add a filter by date range"

# Redirect work that is currently generating (otherwise updates queue by default)
teable app update \
  --app-id appXXX \
  --prompt "keep the current layout; change the chart to weekly totals" \
  --send-mode steer

# Read an existing app's source code (to answer questions or ground an update)
teable app get-code --app-id appXXX
```

`app get-code` writes a **read-only snapshot** to `~/.teable/refs/<appId>/` (`.env*` files excluded; requires app update permission). `app list --search <keyword>` filters by name.

## Key Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--prompt` | Yes | User's request — pass exactly as stated |
| `--name` | Create only | App name |
| `--app-id` | Update only | Target app ID |
| `--table-ids` | No | JSON array of table IDs for data access |
| `--attachment-tokens` | No | Screenshots or design reference images |
| `--folder-id` | No | Place the new app in a folder (`folderId` from the active tab meta); omit for project root |

## Updates While the Builder Is Busy

The default delivery mode is `queue`: use it for a new or independent request that should run as a separate generation after current work finishes. Use `--send-mode steer` only when the prompt corrects, refines, or adds to the generation in progress; if nothing is running, it falls back to queue. The option applies only to `app update`.

## Key Rules

- **Pass user requirements verbatim** to `--prompt` — do not interpret, expand, or add features
- Do not use markdown formatting in the prompt text
- Do not specify tech stack unless the user explicitly requests it
- Before `app delete`, verify the app ID. Deletion moves the app to the project trash rather than permanently erasing it, so restore it there if deletion was accidental.

## Publishing

A generated app runs in preview until published:

```bash
teable app publish --app-id appXXX     # deploy the app; returns success / failed / deploying
teable app status --app-id appXXX      # check publish status
teable app unpublish --app-id appXXX   # take the published app offline
```

If `app publish` returns `deploying`, poll `teable app status --app-id appXXX` until it reports `success` or `failed`.

## AI in apps

When an app needs to call AI (text/image generation) from its own server-side code, enable the proxy:

```bash
teable app ai-enable --app-id appXXX
```

- **Idempotent** — safe to run when already enabled. `--app-id` falls back to `TEABLE_APP_ID` when omitted (`app login-config` has no such fallback — always pass it there).
- Injects `TEABLE_AI_API_BASE_URL` and `TEABLE_AI_API_KEY` into the app on its **next preview restart**.
- The proxy is **Anthropic-compatible** and **server-side only** — never expose `TEABLE_AI_API_KEY` to the browser. The key value is never printed.
- System-model usage consumes credits; BYOK models run on the space's own key.

For usage patterns and the **available model keys for the current project** (resolved dynamically), read the docs — do not hardcode model names:

```bash
teable app ai-docs            # equivalent to: teable get-doc --topic app.ai
```

## App login / authentication

By default a generated app is open. To require end-users to authenticate before accessing it, set a login config:

```bash
teable app login-config --app-id appXXX --login-config '{
  "enabled": true,
  "userTableId": "tblXXX",
  "emailFieldId": "fldXXX",
  "providers": [{ "type": "email-otp" }]
}'
```

**`loginConfig` shape:**

| Field | Description |
|-------|-------------|
| `enabled` | `true` to require login, `false` to disable |
| `userTableId` | Table ID that stores user records |
| `emailFieldId` | Field ID of the email column in the user table |
| `providers` | Array of `{ "type": ... }`: `"email-otp"`, `"google"`, or `"teable"` |
| `access` (optional) | `{ "mode": "open" \| "domain" \| "existing-only", "domains": [...] }` — `domains` only used in `domain` mode |

Pass `--login-config null` to disable login entirely.
