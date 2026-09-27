# Delegated setup control plane

Use this flow to provision AI Pass without receiving a user's session credential. Base URL: `https://aipass.one`.

## Scope selection

Request the standard project setup set once: `setup:read`, `oauth-clients:read`, `oauth-clients:create`, `space:read`, `space-apps:write`, `space-apps:publish`, and `nova:query`. The OAuth callbacks remain exact, and Space writes remain bound to one inferred project app slug. Request runtime `profile:read` only when ensuring a public client that intentionally uses AI Pass as host login.

These grants do not authorize billing, payments, wallet access, account security, model spending, generic API keys, or administrator operations.

Always send `requestedScopes`. Omitting it grants only `setup:read`; it does not infer broad setup access.

## Stable public project identity

Before the first request, read `.aipass/config.json`. Reuse its `projectFingerprint` when present. Otherwise generate a random UUID v4, write it there, and reuse it exactly for every later setup grant for this project. The fingerprint is a public correlation identifier, not a credential. Do not derive it from the repository path, Git remote, account, hostname, or other machine identity.

For example:

```json
{
  "schemaVersion": 1,
  "projectFingerprint": "4f23c8c2-75ee-4c7f-8762-cdb8225d7a31"
}
```

## Determine callbacks before approval

When requesting `oauth-clients:create`, inspect the application and determine one to eight exact callback destinations before starting the device flow:

- Browser SDK: propose a stable URL on each exact browser origin where the SDK proof will run, for example `http://localhost:3000/` and later `https://app.example/`. The SDK uses AI Pass's signed central handoff, but the target origin must still be represented by an approved callback. The app does not need to implement that URL as an OAuth handler for the SDK path.
- Backend OAuth or AI Pass host login: propose the real callback route the host will implement, for example `https://app.example/auth/aipass/callback`.
- Mobile/deep-link clients: propose the exact private custom-scheme callback.

Public web callbacks must use HTTPS. Plain HTTP is allowed only on `localhost` or `127.0.0.1`. Userinfo, fragments, wildcards, dangerous schemes, and values longer than 2048 characters are rejected. Path, query, case, encoding, port, and trailing slash are significant for direct OAuth callbacks.

Do not invent a production hostname. Ask the user only when the repository and deployment configuration do not establish the destination. The user sees these exact destinations on the approval screen. The resulting client is bound to them; a later change requires a new setup request and approval.

## 1. Start device authorization

No authentication is required for this request:

```http
POST /api/v1/agent-auth/device
Content-Type: application/json

{
  "agentName": "Actual executing agent name",
  "projectName": "Inferred app name",
  "projectFingerprint": "4f23c8c2-75ee-4c7f-8762-cdb8225d7a31",
  "setupVersion": 5,
  "requestedScopes": [
    "setup:read",
    "oauth-clients:read",
    "oauth-clients:create",
    "space:read",
    "space-apps:write",
    "space-apps:publish",
    "nova:query"
  ],
  "proposedRedirectUris": [
    "http://localhost:3000/"
  ],
  "proposedSpaceAppSlug": "example-app"
}
```

Always send `setupVersion: 5` when following this version of the skill. It fails closed when `oauth-clients:create` lacks exact proposed callbacks, binds an existing Space from the approved account when available, and otherwise reserves the one app slug until that same account claims a Space. Omitting the field is reserved for compatibility with older published instructions.

Use the true executing tool name; do not copy an example agent identity. The HTTP 201 response uses the standard AI Pass envelope. Its `data` contains `deviceCode`, `userCode`, `verificationUri`, `verificationUriComplete`, `expiresIn`, and `interval`.

Show the user the app name, requested capability, and `verificationUriComplete`. When the environment has a browser or open-URL capability, open that user-facing URL once, then say that the approval page is open and ask the user to review it. Use the native capability instead of fetching the URL:

- Local macOS terminal: `open "$verificationUriComplete"`
- Local Linux desktop: `xdg-open "$verificationUriComplete"`
- Local Windows PowerShell: `Start-Process $verificationUriComplete`
- Replit, Lovable, or another browser IDE: use its native external-link or preview-opening affordance when available.

Do not run a local desktop opener from a remote or headless shell where it would open on the server rather than the user's device. In that case, or when opening fails, present `verificationUriComplete` as a clickable link. Attempt the automatic open only once; do not reopen it on every pending poll.

Opening the page is only a convenience handoff. Never use `curl`, an HTTP client, browser automation, or computer-use tools to inspect, sign in, click Continue, approve, or otherwise interact with the authorization page on the user's behalf. Never ask them to paste a session token or setup grant, and never call the approval endpoint yourself.

## 2. Poll for approval

Wait at least the returned interval between requests:

```http
POST /api/v1/agent-auth/token
Content-Type: application/json

{"deviceCode":"returned device code"}
```

While approval is pending, the API returns HTTP 400 with a standard envelope whose `.error` is `authorization_pending`. Poll no faster than `interval`. On `slow_down`, increase the wait before the next poll. Stop on `access_denied` or `expired_token`. Continue only when the standard response envelope has this `data`:

```json
{
  "status": "approved",
  "accessToken": "asg_...",
  "tokenType": "Bearer",
  "expiresIn": 2592000,
  "scopes": ["setup:read", "oauth-clients:read", "oauth-clients:create", "space:read", "space-apps:write", "space-apps:publish", "nova:query"]
}
```

Honor the returned polling interval and all pending, denied, and expired outcomes. Do not restart automatically after denial. Keep the `accessToken` in process memory only. Record its computed expiry deadline in agent memory from `expiresIn` so the final report can say when the retained project grant expires. Redact both values from logs and output.

### Resuming across turns

Not every runtime can hold a process open while the user approves in a browser. A server-side or turn-based agent ends execution when it hands control back to the user, so a polling loop started before the approval never survives to see it. Hosts in this category include Replit, Lovable, v0, and Bolt.

When the runtime cannot poll continuously, store the request and resume instead of looping:

1. Add `.aipass/pending-device.json` to the project's ignore file, then write the raw `deviceCode`, the `userCode`, and the absolute `expiresIn` deadline to it.
2. Open `verificationUriComplete` once with a native user-facing browser capability when available. Otherwise show it as a clickable link. End the turn asking the user to review, approve, and return.
3. On a later turn, read that file and call the token endpoint once. On `authorization_pending`, ask the user to finish approving and end the turn again. Do not busy-loop and do not start a new device request.
4. Delete the file as soon as the exchange succeeds, the request is denied, or the deadline passes.

Never start a second device request while a stored one is still unexpired and unexchanged. A user who approved one code and is then handed another cannot tell which is live, and the approved one is silently abandoned.

The stored `deviceCode` is scoped to this project. A retry can recover the same issued token while the grant remains valid, so delete the file immediately after a successful exchange as instructed. Treat it as a secret until deletion: never commit it, print it, or place it in application code.

If the executing agent supports ephemeral authenticated remote MCP, continue with [remote-mcp.md](remote-mcp.md). If its MCP configuration would persist the bearer value, use the REST calls below instead. Never trade away the setup grant's in-memory-only boundary merely to use MCP. The device-code resume file above is the only value this flow may write to disk, and it never holds an `asg_` grant.

## 3. Read before mutating

All REST control-plane calls use:

```http
Authorization: Bearer asg_REDACTED
```

Read owned resources first:

```http
GET /api/v1/agent-control/context
```

Unwrap the standard response envelope's `data`. It is intentionally minimal: owned public OAuth clients with client type, runtime scopes, and exact redirect URIs; read-only Space context; and grant bounds. It contains no client secret, wallet balance, session token, or private profile.

Reuse only an exact public client ID already stored in this project's configuration and confirmed by context as active, `PUBLIC`, correctly scoped, and bound to the same ordered callback list the user approved. Never reuse by display-name similarity.

## 4. Ensure a public OAuth client

For the SDK, backend OAuth, or login path:

```http
POST /api/v1/agent-control/oauth-clients/ensure
Content-Type: application/json
Authorization: Bearer asg_REDACTED

{
  "name": "Inferred app name",
  "idempotencyKey": "oauth-client:v1",
  "runtimeScopes": ["api:access"]
}
```

Use runtime scope `api:access` for SDK and model calls. Add `profile:read` only when AI Pass is intentionally serving as host login. Reuse the returned public `clientId`. This endpoint creates a public, secretless PKCE client only.

The ensure request intentionally does not accept redirect URIs. It reads the immutable `proposedRedirectUris` from the approved setup grant, creates the client with exactly those values, and returns them as `redirectUris`. If the callbacks differ from a prior idempotent client, setup fails and requires a new approval and versioned idempotency key; never work around this by choosing another unapproved callback.

The idempotency key is scoped by signed-in user, project fingerprint, and operation. Use the stable literal `oauth-client:v1` for the first client for this project and persist it as `oauthClientIdempotencyKey` in `.aipass/config.json`. If a response is lost or a grant expires, read context and retry with the same project fingerprint, approved project name, runtime scopes, and key; the control plane returns the original usable client rather than creating a duplicate.

If AI Pass explicitly reports that the prior client for that key was deleted, deactivated, or no longer matches a secretless public PKCE client, never reactivate or modify it. Ask for a fresh setup approval, advance the persisted key once to the next version such as `oauth-client:v2`, and ensure a replacement. Do not rotate the key for transient network failures or to bypass a scope/name mismatch.

## 5. Reuse this grant for the project's Space app

The standard project grant already includes the publishing scopes displayed on the approval page and one exact `proposedSpaceAppSlug`. If the user asks for Spaces after the SDK or OAuth setup, read [spaces-path.md](spaces-path.md) and continue with this same bearer value. Do not start another device request. If the account had no Space during approval, the first preflight after the user claims one binds that same-account Space to the existing grant.

## 6. Optional read-only A2A support

Discover Nova at `/.well-known/agent-card.json`. Calls use the same project grant with `nova:query`:

```http
POST /a2a/v1/message:send
Content-Type: application/a2a+json
A2A-Version: 1.0
Authorization: Bearer asg_REDACTED

{
  "message": {
    "messageId": "new-uuid",
    "role": "ROLE_USER",
    "parts": [{"text":"Which documented path should I read for a localhost React app?"}]
  }
}
```

The first release supports synchronous read-only messages that route questions to documentation, path guidance, and error checklists. It does not inspect the project, analyze a supplied plan or error, stream, manage tasks, provision, publish, or mutate anything.

## 7. Keep one grant across project setup work

Keep one grant in process memory through integration, correction, retry, Nova guidance, and optional publication of the approved Space app. Do not revoke after provisioning the OAuth client or after the first Space call. Never persist it or use it outside the project resources shown on the approval page. Device approval does not authorize paid model calls.

Revoke when the user asks to disconnect or the agent must abandon a credential it can no longer protect:

```http
DELETE /api/v1/agent-control/session
Authorization: Bearer asg_REDACTED
```

The response is HTTP 200 and the grant becomes unusable immediately. Normal task completion, client provisioning, a passing build, or the first model call is not itself a reason to revoke while the same agent context may continue; server-side expiry ends it after one month. Report a healthy grant as "retained in agent memory; expires at [time] or the user can revoke it." If the user requests a different project, callback destination, or Space app slug, start a fresh user-approved device flow rather than reusing this project grant.
