---
name: aipass-spaces
description: Build and publish a self-contained hosted app to the signed-in user's AI Pass Space through one reusable browser-approved project authorization. Use when the user asks to publish on AI Pass Spaces or a hosted Space is the fastest deployment path. Discover or later bind the user's handle automatically; never ask them to look it up or paste it into chat.
---

# Publish to AI Pass Spaces

Use this path when a self-contained hosted app reaches a real result faster than deploying or changing the user's existing project. A Space lives at `https://aipass.one/spaces/{handle}`.

## Security boundary

Publishing uses a browser-approved `asg_` setup grant. Never ask the user to paste a Space handle, API key, OAuth token, browser cookie, password, device code, or setup grant. Never call generic API-key create, rotate, regenerate, or delete endpoints.

The grant:

- gives reusable project setup access for up to one month so integration, correction, and publication do not require repeated approval;
- is bound to the signed-in account, one app slug, and the stable project fingerprint, and binds that account's Space during approval or first later use;
- can read the owner's Space, create or update one draft, and publish that draft;
- cannot call models, spend wallet funds, access payments, read account secrets, or act as a normal user credential.

Keep the `asg_` value only in process memory. Never print, persist, commit, or include credentials in tool output. Send credentials only to `https://aipass.one` over HTTPS. The raw `deviceCode` may be stored temporarily in a gitignored `.aipass/pending-device.json` only when a turn-based runtime cannot stay alive while the user approves; delete it at the first terminal outcome.

## 1. Prepare the exact app before authorization

Choose a stable lowercase slug using letters, numbers, and hyphens. Build one complete HTML document with inline app CSS and JavaScript. Include the SDK and keep `PLACEHOLDER_CLIENT_ID` exactly as written; AI Pass replaces it during the draft write.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>My AI app</title>
  <link rel="stylesheet" href="https://aipass.one/aipass-ui.css">
</head>
<body>
  <div data-aipass-button></div>
  <button id="generate" type="button">Generate</button>
  <output id="result"></output>
  <script src="https://aipass.one/aipass-sdk.js"></script>
  <script>
    AiPass.initialize({ clientId: 'PLACEHOLDER_CLIENT_ID', requireLogin: false });
  </script>
</body>
</html>
```

Use `AiPass.streamText`, `generateCompletion`, image/audio/video helpers, `AiPass.data`, `AiPass.files`, and user-approved `AiPass.shared` only as documented by the browser SDK. The publishing grant must never appear in app HTML.

Before the first request, reuse `.aipass/config.json`'s public `projectFingerprint`, or generate and persist a random UUID v4. It is a public project identifier, not a credential. Never derive it from a path, user, hostname, or Git remote. If the agent already holds a usable `asg_` project grant whose scopes include Space read/write/publish and whose project fingerprint and approved app slug match, skip device authorization and reuse it.

## 2. Start device authorization

No authentication is required:

```http
POST /api/v1/agent-auth/device
Content-Type: application/json

{
  "agentName": "Actual executing agent name",
  "projectName": "My AI app",
  "projectFingerprint": "4f23c8c2-75ee-4c7f-8762-cdb8225d7a31",
  "setupVersion": 5,
  "requestedScopes": [
    "setup:read",
    "space:read",
    "space-apps:write",
    "space-apps:publish"
  ],
  "proposedSpaceAppSlug": "my-ai-app"
}
```

Use the real executing tool name. Do not send `proposedSpaceHandle` and do not ask the user for it. Do not send `proposedContentSha256`; setup version 5 lets the agent fix and republish this one approved app without another authorization. The page shows the exact `@handle` when one exists, app slug, editing permission, and other scopes before approval. If the account has no Space yet, the user can still approve; after they claim a handle, the first preflight binds the Space owned by that same account to the existing grant.

Open `verificationUriComplete` once when the environment has a native browser or open-URL capability. Use `open "$verificationUriComplete"` on a local macOS terminal, `xdg-open "$verificationUriComplete"` on a local Linux desktop, `Start-Process $verificationUriComplete` in local Windows PowerShell, or the host's external-link affordance in Replit, Lovable, or another browser IDE. Do not run a desktop opener from a remote or headless server. When opening is unavailable, show the clickable URL.

Opening is only a convenience handoff. Never fetch the page with `curl`, inspect it with browser automation, sign in, click Continue, approve, or otherwise interact with it on the user's behalf. Attempt the automatic open once, not after every pending poll.

Poll no faster than the returned `interval`:

```http
POST /api/v1/agent-auth/token
Content-Type: application/json

{"deviceCode":"in-memory device code"}
```

Continue on `authorization_pending`, slow down on `slow_down`, and stop on denial or expiry. On success, keep the returned `asg_` access token in memory only.

If the runtime ends its turn after handing control to the browser, add `.aipass/pending-device.json` to the project's ignore file and store only the raw `deviceCode`, `userCode`, and absolute expiry there. On the next turn, exchange that same device code once. Never start a second request while it remains unexpired. Delete the file after approval, denial, or expiry. Never write the `asg_` grant to disk.

## 3. Mandatory preflight

Before every draft write, call:

```http
GET /api/v1/agent-control/space/preflight
Authorization: Bearer asg_REDACTED
```

The returned `handle` is the exact signed-in Space bound during approval or this first preflight. Save it as public metadata in `.aipass/config.json`; do not ask the user to copy it. Inspect `apps` and update the approved matching slug instead of creating a duplicate. The grant may revise content for this slug, but it cannot switch slugs or take over an app that is not already managed by the same project fingerprint.

Machine-readable failures:

- `MISSING_CREDENTIAL`: no bearer value was sent;
- `INVALID_CREDENTIAL`: malformed, unknown, or wrong credential family;
- `CREDENTIAL_REVOKED`: the owner ended the grant;
- `CREDENTIAL_EXPIRED`: the grant timed out;
- `SPACE_NOT_CLAIMED`: the authenticated owner has no Space; open `/spaces` for them to claim one, then retry with the same grant;
- `SPACE_HANDLE_MISMATCH`: the approved handle is not the owner's current handle.

Keep the same approved grant through SDK/OAuth integration, draft creation, correction, retry, and publication for this exact project app for up to one month. Do not revoke after the first successful call or start a replacement merely because another already-approved operation remains. For an expired, revoked, missing, or invalid grant, start one fresh device authorization for the same target and ask for browser approval. Never rotate or create a generic API key. Do not retry automatically after denial. `404` is not an authentication signal.

## 4. Create or update the draft first

```http
PUT /api/v1/agent-control/space/apps/{approved-slug}
Authorization: Bearer asg_REDACTED
Content-Type: application/json

{
  "name": "My AI app",
  "shortDescription": "A clear description of what the app does.",
  "htmlContent": "<!doctype html>...PLACEHOLDER_CLIENT_ID...</html>",
  "idempotencyKey": "space-draft:v1"
}
```

The server verifies the approved Space, app slug, project fingerprint, and session scope, then writes `DRAFT`; it never publishes in the same call. A fresh project may create the approved slug. A returning project may update only an agent-managed app previously created with the same stable project fingerprint. It cannot take over another app.

If the response is lost, run preflight again before retrying. Reuse the same slug, fingerprint, content, and idempotency key. Never invent a second slug to bypass an ambiguous response.

## 5. Publish that exact draft

```http
POST /api/v1/agent-control/space/apps/{approved-slug}/publish
Authorization: Bearer asg_REDACTED
```

Only the draft bound to this grant can be promoted. Confirm the response status is `PUBLISHED`, then open the preflight handle at `/spaces/{handle}/{slug}`. The public Spaces index lists only Spaces with published apps; the owner can still see empty Spaces, drafts, and failed builder records on their own Space page.

## 6. Verify and keep the project grant available

Open the real app, exercise its normal AI Pass connection, and make a wallet-funded AI call only with contemporaneous user approval. Confirm one user action makes one model request and renders the real result. Exercise loading, cancellation, one error state, and storage isolation when used.

Do not revoke merely because publication completed; the same agent conversation may need to correct or republish the app. Revoke only when the user asks to disconnect, the project identity changes, or the agent must abandon a credential it can no longer protect:

```http
DELETE /api/v1/agent-control/session
Authorization: Bearer asg_REDACTED
```

When revocation is requested, confirm a later control-plane request returns `CREDENTIAL_REVOKED`. Otherwise report that the in-memory project grant remains available until its one-month expiry or user revocation. Report the public Space URL, slug, and verification performed. Never include credential-bearing responses in the report.
