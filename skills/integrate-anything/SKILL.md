---
name: "integrate-anything"
description: "This skill should be used only when an external-app action must be executed through the Membrane CLI and an authenticated Membrane connection, such as sending a message, creating a task, or syncing records. It should not be used for general API design, SDK integration, documentation lookup, or direct vendor API calls."
metadata:
  category: data
  source:
    repository: "https://github.com/membranehq/agent-skills"
    path: "skills/integrate-anything"
    license_path: "LICENSE"
---

# Self-Integration

Connect to external apps through the [Membrane](https://getmembrane.com) CLI.

## Activation and Composition

- Activate only when the task requires executing an external SaaS action and Membrane is available or explicitly requested.
- Defer explanation-only, SDK, direct API, and product-specific implementation work to a narrower vendor or integration skill.
- When composing with a vendor skill, use that skill to determine domain semantics or payload shape, but keep authentication and execution in Membrane.
- Before an ambiguous, destructive, or irreversible action, summarize the selected connection, target, and operation and obtain confirmation.

**Always route execution through Membrane.** Don't hit vendor APIs directly. Membrane proxies every request through an authenticated connection and injects the right auth headers — including transparent credential refresh.

**Never handle external-app credentials yourself.** OAuth tokens, API keys, refresh tokens — Membrane stores and manages them server-side. Pass a `connectionKey` (or `connectionId`) and the tools call the vendor on your behalf.

## Workflow

1. **Authenticate with Membrane** (one-time per machine).
2. **Ensure a connection** to the external app — find an existing one, reconnect a disconnected one, or create a new one.
3. **Use the connection** to run actions or call the app's API.

The rest of the skill is these three steps in detail.

## Authentication

```bash
npx @membranehq/cli login --tenant
```

`--tenant` gets a tenant-scoped token (workspace + customer) so you don't need to pass `--workspaceKey` and `--tenantKey` on every subsequent command.

The command opens a browser. In headless environments it prints an authorization URL — ask the user to open it, complete the flow, and paste the code back; finish with:

```bash
npx @membranehq/cli login complete <code>
```

Credentials are stored at `~/.membrane/credentials.json`. All later commands pick them up automatically.

If `npx` is awkward, install globally: `npm i -g @membranehq/cli@latest` and use plain `membrane …`. Add `--json` to any command for machine-readable output.

## Step 1 — Get a connection

### 1a. Find an existing connection

```bash
npx @membranehq/cli connection list --json
```

Each connection carries `id`, `key`, `integrationKey`, `state`. Scan for the target app and branch on `state`:

- **`READY`** → use it. Skip to Step 2.
- **`CLIENT_ACTION_REQUIRED`** (disconnected, needs re-auth) → **reconnect the existing connection**, do NOT create a new one:

  ```bash
  npx @membranehq/cli connect --connectionId <id>
  ```

  Creating a fresh connection while the old one is `CLIENT_ACTION_REQUIRED` leaves orphaned records and breaks anything that referenced the old `connectionKey`. Always reconnect.
- **Multiple matches** (e.g. `slack-work` and `slack-personal`) → ask the user which to use. Don't guess.
- **No match** → create a new one (Step 1b).

### 1b. Create a new connection

By URL or domain — shortest path:

```bash
npx @membranehq/cli connection ensure "https://slack.com" --json
# also accepts a bare domain: "slack.com"
```

The URL is normalized to a domain and matched against known apps. If no app is found, one is created and a connector is built automatically.

To set a stable, human-readable key for later lookup (especially for multi-account setups like `slack-work` + `slack-personal`), set it after creation:

```bash
npx @membranehq/cli connection patch <id> --data '{"connectionKey":"slack-work"}'
```

For the explicit multi-connection case (creating a second connection to an app you already have connected), use `connect`:

```bash
npx @membranehq/cli connect --integrationKey slack \
  --connectionKey slack-personal --allowMultipleConnections
```

### 1c. Drive the connection to `READY`

After 1a's reconnect or 1b's create, read `state` and follow the state machine:

- **`READY`** — done. Move to Step 2.
- **`BUILDING`** — Membrane's builder agent is working. Wait:

  ```bash
  npx @membranehq/cli connection get <id> --wait --json
  ```

  `--wait` long-polls (up to `--timeout` seconds, default 30).
- **`CLIENT_ACTION_REQUIRED`** — the user or agent must do something. The `clientAction` object describes what:
  - `clientAction.type` — `"connect"` (auth flow) or `"provide-input"` (extra fields needed).
  - `clientAction.agentInstructions` (optional) — **follow these verbatim if present**. They tell the agent how to drive the provider side of the flow programmatically. Don't shortcut to "paste this URL" — the instructions exist because the agent is expected to handle it.
  - `clientAction.uiUrl` (optional) — a Membrane-hosted page where the user completes the action manually. Show this only when `agentInstructions` tells you to, or when no `agentInstructions` are present.
  - `clientAction.description` — human-readable summary.

  When the action requires writing data back to the connection (e.g. captured OAuth credentials, custom params):

  ```bash
  npx @membranehq/cli connection patch <id> --data '{"connectorParameters":{...},"input":{...}}'
  ```

  After the user completes their step, poll with `connection get <id> --wait --json` until `state` changes.
- **`CONFIGURATION_ERROR`** / **`SETUP_FAILED`** — surface the `error` field to the user. These are terminal — don't retry blindly.

## Step 2 — Use the connection

The fastest path to a real response is `act` with an inline dispatch. **No "create action → wait → run" ceremony required.**

`act` accepts exactly one of four dispatch styles:

| Dispatch | When to use |
|---|---|
| `--api '<json>'` | **First call after a fresh connection, and any one-off HTTP request.** Membrane handles auth + base URL. |
| `--code '<js>'` | You need a small piece of logic (loop, transform, multi-step). |
| `--key <key>` | You've previously saved this call as a reusable action. |
| `--id <id>` | Same as `--key` but by id (use only when the action has no key). |

### 2a. Inline `api` (recommended for the first call after a fresh connection, and for one-off calls)

**Use this as the default for the very first call against a new connection.** It's the fastest way to confirm the connection works and to give the user a real response — no build step, no `BUILDING` state, no waiting.

Pass an HTTP spec; Membrane proxies it through the connection's auth layer and base URL:

```bash
npx @membranehq/cli act --connectionKey slack-work \
  --api '{"method":"POST","path":"/api/chat.postMessage","body":{"channel":"#general","text":"Hello"}}' \
  --json
```

Spec shape: `{ method, path, body?, headers?, query? }`. The connector's base URL is prepended automatically. Auth is injected automatically.

Only escalate to a saved action (Step 3) if the user is going to run the same call repeatedly — saving has real value for repeat use, but adds latency and failure modes that are wasteful for first-call activation.

### 2b. Inline `code` (when you need logic, not just an HTTP call)

```bash
npx @membranehq/cli act --connectionKey hubspot \
  --code 'module.exports = async ({ input, membrane }) => {
    const all = []
    let after
    do {
      const page = await membrane.api({ method: "GET", path: "/crm/v3/objects/contacts", query: { limit: 100, after } })
      all.push(...page.results)
      after = page.paging?.next?.after
    } while (after)
    return { count: all.length }
  }' \
  --input '{}' --json
```

The function receives `{ input, membrane, connection, integration }`. Use `membrane.api({ method, path, ... })` to make authenticated calls inside the function. Whatever you return becomes the response `output`.

### 2c. Reusable action by key (for repeat use)

If the user is going to run the same call repeatedly, save it once and call it by `key`:

```bash
npx @membranehq/cli act --key send-channel-message --connectionKey slack-work \
  --input '{"channel":"#general","text":"Hello"}' --json
```

See **Step 3** below for how to create a saved action.

### 2d. Discover existing reusable actions

If you don't already know whether one exists:

```bash
# Ranked by semantic match against an intent
npx @membranehq/cli action list --connectionKey slack-work --intent "send a message" --limit 10 --json

# Catalog actions for one app (browse without a connection)
npx @membranehq/cli external-app list --search slack --json   # → externalAppId
npx @membranehq/cli action list --externalAppId <id> --json
```

Each result carries `id`, `key`, `name`, `description`, `inputSchema`, `outputSchema`. Read the `inputSchema` before running — it's authoritative.

If nothing matches, fall back to inline `api` or `code` (above), or create a saved action (Step 3).

## Step 3 — Save reusable actions (optional)

When you find yourself about to make the same `act --api` call a second time, save it. Future calls become `act --key <key>` instead of the full inline spec.

Two ways:

**By intent** — describe what you want; Membrane builds the config and validates it:

```bash
npx @membranehq/cli action create "send a message in a channel" --connectionKey slack-work --json
```

The action returns in `state: BUILDING`. Wait for it:

```bash
npx @membranehq/cli action get <id> --wait --json
```

**By explicit spec** — supply `type` + `config` directly. Common when lifting a tested inline `api` call into a saved action:

```bash
npx @membranehq/cli action create \
  --key send-channel-message \
  --type api-request-to-external-app \
  --config '{"request":{"method":"POST","path":"/api/chat.postMessage"}}' \
  --integrationKey slack --json
```

Scope follows which fields you set:
- `connectionKey` / `connectionId` → connection-level (tied to one connection)
- `integrationKey` / `integrationId` (no connection) → integration-level (shared across every connection on that integration)

Update / delete:

```bash
npx @membranehq/cli action update <id-or-key> --data '<json-merge>'
npx @membranehq/cli action delete <id-or-key>
```

**Ask the user before saving** — they may want the action named, described, or kept inline.

## Error recovery

Read the response body — never branch on HTTP status alone. Three error paths:

### 401 — Membrane auth is bad
Your CLI session is invalid or expired. Run `membrane login --tenant` again.

### Disconnected external-app connection
The vendor's auth no longer works (token revoked, OAuth expired, credentials rotated). Read the connection state:

```bash
npx @membranehq/cli connection get <id-or-key> --json
```

If `state` is `CLIENT_ACTION_REQUIRED`, **reconnect the existing connection** (don't create a new one):

```bash
npx @membranehq/cli connect --connectionId <id>
```

After re-auth, retry the original `act` call.

### Action failed
Every `act` response carries `actionRunId`, on success AND on error. Pull the full log:

```bash
npx @membranehq/cli action-run-log get <actionRunId> --details --json
```

You get the mapped input, output, errors, plus the raw HTTP exchange with the external app.

## CLI Reference

All commands support `--json`. Add `--workspaceKey <key>` and `--tenantKey <key>` to override project defaults.

### connection
```bash
npx @membranehq/cli connection ensure <appUrl> [--name <n>] [--json]                       # Find or create by URL
npx @membranehq/cli connection list [--json]
npx @membranehq/cli connection get <id-or-key> [--wait] [--timeout <n>] [--json]
npx @membranehq/cli connection patch <id> --data '<json>' [--json]
npx @membranehq/cli connect --connectionId <id>                                              # Reconnect existing
npx @membranehq/cli connect --integrationKey <k> [--connectionKey <k>] [--allowMultipleConnections]
```

### act
```bash
npx @membranehq/cli act --connectionKey <k> --api  '<json>' [--input <json>] [--json]   # Inline HTTP
npx @membranehq/cli act --connectionKey <k> --code '<js>'   [--input <json>] [--json]   # Inline JS
npx @membranehq/cli act --connectionKey <k> --key  <k>      [--input <json>] [--json]   # Reusable
npx @membranehq/cli act --connectionKey <k> --id   <id>     [--input <json>] [--json]   # Reusable by id
```

### action (manage saved actions)
```bash
npx @membranehq/cli action list   [--connectionKey <k>] [--externalAppId <id>] [--intent <t>] [--limit <n>] [--json]
npx @membranehq/cli action create <intent> --connectionKey <k> [--json]                       # Build by intent
npx @membranehq/cli action create --key <k> --type <t> --config '<json>' --integrationKey <k> [--json]   # Explicit spec
npx @membranehq/cli action get    <id-or-key> [--wait] [--timeout <n>] [--json]
npx @membranehq/cli action update <id-or-key> --data '<json>'                                  # Merge
npx @membranehq/cli action delete <id-or-key>
```

### action-run-log
```bash
npx @membranehq/cli action-run-log get <actionRunId> [--details] [--json]                      # Diagnostics for any /act call
```

### external-app / search
```bash
npx @membranehq/cli external-app list --search <query> --json
npx @membranehq/cli search <query> [--elementType <type>] [--limit <n>] [--json]
```

## Fallback: Raw API

If the CLI is not available, call the API directly.

Base URL: `https://api.getmembrane.com`
Auth header: `Authorization: Bearer $MEMBRANE_TOKEN`

Get the token from the [Membrane dashboard](https://console.getmembrane.com).

| CLI Command | API Equivalent |
|---|---|
| `connection ensure "<url>" --json` | `POST /connections/ensure` with `{"appUrl": "<url>"}` |
| `connection list --json` | `GET /connections` |
| `connection get <id> --wait --json` | `GET /connections/:id?wait=true` |
| `connection patch <id> --data <json>` | `PATCH /connections/:id` with `<json>` |
| `connect --connectionId <id>` | `POST /connections/:id/reconnect` |
| `act --connectionKey <k> --api <json>` | `POST /act` with `{"connectionKey":"<k>","api":<json>}` |
| `act --connectionKey <k> --code <js>` | `POST /act` with `{"connectionKey":"<k>","code":"<js>"}` |
| `act --connectionKey <k> --key <ak>` | `POST /act` with `{"connectionKey":"<k>","key":"<ak>","input":<json>}` |
| `action list --connectionKey <k> --intent <t>` | `GET /actions?connectionKey=<k>&intent=<t>` |
| `action create <intent> --connectionKey <k>` | `POST /actions` with `{"intent":"<t>","connectionKey":"<k>"}` |
| `action get <id> --wait` | `GET /actions/:id?wait=true` |
| `action-run-log get <actionRunId> --details` | `GET /action-run-logs/:id?details=true` |

## External Endpoints

All requests go to the Membrane API. No other external services are contacted directly by this skill.

| Endpoint | Data Sent |
|---|---|
| `https://api.getmembrane.com/*` | Auth credentials, connection parameters, action inputs, agent prompts |

## Security & Privacy

- All data is sent to the Membrane API over HTTPS.
- CLI credentials are stored locally in `~/.membrane/` with restricted file permissions.
- Connection authentication (OAuth, API keys) is handled by Membrane — credentials for external apps are stored by the Membrane service, not locally.
- Action inputs and outputs pass through the Membrane API to the connected external app.

By using this skill, data is sent to [Membrane](https://getmembrane.com). Only install if you trust Membrane with access to your connected apps.
