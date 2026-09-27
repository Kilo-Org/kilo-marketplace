# Remote MCP setup tools

Use AI Pass remote MCP only after the user approves the device flow in [setup-control-plane.md](setup-control-plane.md). The endpoint is `POST https://aipass.one/mcp` and accepts only the one-month `asg_` project setup grant. It does not accept an AI Pass session, runtime OAuth token, generic API key, client secret, provider key, or wallet credential.

## Choose MCP only when the grant stays ephemeral

Prefer MCP when the executing agent can attach an HTTP authorization header in memory for this run. If the client requires writing the bearer value into a persistent MCP configuration file, shell profile, project file, command history, or log, do not configure it. Use the equivalent REST control-plane calls instead. Never put the grant in a URL or query parameter.

MCP and REST enforce the same scopes, ownership, idempotency, mutation budget, audit trail, expiry, and revocation. MCP is a typed transport, not broader authority.

## Transport

Send one JSON-RPC object per request:

```http
POST /mcp
Authorization: Bearer asg_REDACTED
Content-Type: application/json
Accept: application/json, text/event-stream
```

Prefer the current stateless protocol revision `2026-07-28`. Send `MCP-Protocol-Version: 2026-07-28` and an exact `Mcp-Method` header on every request; send `Mcp-Name` for `tools/call`. You may call `server/discover` first, but no initialize handshake or transport session is required. Clients pinned to `2025-11-25` remain supported: initialize with that version, send `notifications/initialized`, then include `MCP-Protocol-Version: 2025-11-25` on later requests. The server returns JSON and does not expose SSE streams, resources, prompts, tasks, batches, or server push.

Call `tools/list` and use only tools returned for the current grant. Legacy initialized clients send `notifications/initialized` first. Do not guess or probe hidden tool names.

## Available tools

| Tool | Required setup scope | Purpose |
| --- | --- | --- |
| `read_context` | `setup:read`; add `oauth-clients:read` to include owned public client metadata | Read grant bounds and the categories explicitly authorized for inspection. |
| `ensure_public_oauth_client` | `oauth-clients:create` | Idempotently create or recover the approved project's public, secretless PKCE client. |
| `get_integration_guidance` | `nova:query` | Get deterministic, read-only links and path guidance. |
| `revoke_setup_session` | Any valid setup grant | Immediately revoke the calling grant. |

There are no tools for model calls, wallet access, payments, billing, generic API keys, account security, administration, Space claiming, Space editing, or Space publication.

For `ensure_public_oauth_client`, use the exact project name the user approved, the stable versioned idempotency key from `.aipass/config.json`, and runtime scope `api:access`. Add `profile:read` only when AI Pass is intentionally the host login. Read context before ensuring anything. Callback destinations are not tool arguments: the server reads the exact `proposedRedirectUris` shown during device approval and returns those immutable values in `redirectUris`.

## Optional disconnect

Do not call `revoke_setup_session` after the first provisioning step or merely because the user asks for a follow-up Space deployment. Keep using the same in-memory grant for the approved project. Call it when the user asks to disconnect, the project identity changes, or the agent must abandon a value it can no longer protect. A successful response ends the grant immediately; do not send another authenticated request with it. If MCP revocation cannot be called, use `DELETE /api/v1/agent-control/session` once and discard the grant from memory.
