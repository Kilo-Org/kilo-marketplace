# Backend OAuth and AI Pass login

Use backend OAuth only when the AI action must run server-side, browser token custody is disallowed, or the host deliberately needs durable AI Pass identity. Do not choose it merely because a backend exists.

## Protocol

- Authorization metadata: `GET https://aipass.one/.well-known/oauth-authorization-server`
- Authorization endpoint: `https://aipass.one/oauth2/authorize`
- Token endpoint: `https://aipass.one/oauth2/token`
- User info: `GET https://aipass.one/oauth2/userinfo`
- Model API base: `https://aipass.one/v1`
- Model catalog: `GET https://aipass.one/v1/models`
- Flow: authorization code with PKCE (`S256`)
- Public client: no client secret
- Runtime scope: `api:access`; add `profile:read` only for host-login identity

Before requesting setup approval, determine the real callback route and include it in `proposedRedirectUris`. AI Pass creates the public client with exactly the destinations the user approves and rejects every other callback. There is no callback-less authorization compatibility state.

AI Pass also binds each newly issued authorization code to the exact callback used for that flow, so the token request must send that same callback byte-for-byte after trimming outer whitespace. Path, query, case, encoding, port, and trailing slash are significant. The authorization server accepts PKCE `S256` only; never fall back to `plain`.

For a localhost proof, use the actual `http://localhost` or `http://127.0.0.1` callback implemented by the project. Public deployments require exact HTTPS callbacks. If another deployment origin or route is needed later, start a new setup approval or have the owner update the client deliberately in **Developer console → OAuth2 Clients**, then re-test every callback. Never substitute a callback that the user did not approve.

## Server-side broker

1. Generate high-entropy `state`, `code_verifier`, and its `S256` challenge. Reject any response or configuration that tries to downgrade to `plain`.
2. Bind `state` and verifier to the current host session with a short expiry.
3. Redirect the user to `/oauth2/authorize` with the public client ID, exact callback, scopes, state, and challenge.
4. On callback, validate state once and exchange the code server-to-server.
5. Encrypt access and refresh tokens at rest and bind them to the correct host user.
6. Refresh once when authorization expires. Never retry an ambiguous paid model call automatically.
7. Provide disconnect and reauthorization behavior.

Do not improvise token storage. Reuse the host's established encrypted credential store and secret manager when one exists. Otherwise pause for the user's approval before adding security infrastructure, then require at minimum:

- authenticated encryption such as AES-256-GCM with a fresh nonce per record;
- an encryption key supplied by the deployment secret manager or environment, never committed or stored beside ciphertext;
- a stored key version so rotation is possible;
- access control by the existing host user ID;
- an atomic token-pair update and a database lock or distributed single-flight guard around refresh;
- deletion on account deletion and disconnect;
- backups that contain ciphertext only and an operational key-rotation plan.

If those controls cannot be provided, do not store runtime tokens and do not claim the backend path is complete.

Never log authorization codes, PKCE verifiers, tokens, or token-bearing responses.

The authorization redirect uses:

```text
GET /oauth2/authorize
  ?response_type=code
  &client_id=AI_PASS_CLIENT_ID
  &redirect_uri=EXACT_CALLBACK
  &scope=api:access
  &state=RANDOM_STATE
  &code_challenge=S256_CHALLENGE
  &code_challenge_method=S256
```

Exchange the code with JSON camel-case request fields:

```http
POST /oauth2/token
Content-Type: application/json

{
  "grantType": "authorization_code",
  "clientId": "AI_PASS_CLIENT_ID",
  "code": "AUTHORIZATION_CODE",
  "codeVerifier": "ORIGINAL_VERIFIER",
  "redirectUri": "EXACT_CALLBACK"
}
```

The response uses `access_token`, `token_type`, `expires_in`, `refresh_token`, and `scope`. Compute expiry when the response arrives.

Refresh with the current rotated token pair:

```http
POST /oauth2/token
Content-Type: application/json

{
  "grantType": "refresh_token",
  "refreshToken": "CURRENT_REFRESH_TOKEN",
  "clientId": "AI_PASS_CLIENT_ID"
}
```

Persist the returned access and refresh tokens atomically, coalesce concurrent refreshes, and require authorization again after an invalid grant. Do not retry an ambiguous paid model call.

Disconnect by revoking the refresh token and current access token when present, then deleting the encrypted local record:

```http
POST /oauth2/revoke
Content-Type: application/x-www-form-urlencoded

token=TOKEN_TO_REVOKE&client_id=AI_PASS_CLIENT_ID
```

Treat revocation as idempotent. Clear local ciphertext even when the remote token is already invalid, but surface an unexpected network failure instead of claiming remote revocation succeeded.

Discover a current model ID, then call the OpenAI-compatible model API. Declare the public client binding on every request:

```http
POST /v1/chat/completions
Authorization: Bearer ACCESS_TOKEN
X-AIPass-OAuth-Client-Id: AI_PASS_CLIENT_ID
Content-Type: application/json

{
  "model": "MODEL_FROM_DISCOVERY",
  "messages": [{"role":"user","content":"Approved verification prompt"}],
  "max_tokens": 64,
  "stream": false
}
```

For the one paid verification call, choose a current low-cost non-reasoning text model and a short prompt. Use a small explicit output cap only when that model supports it; reasoning models may spend the cap internally and return no visible output. State the model and its variable input/output pricing basis before asking for spend approval.

## AI Pass as host login

Choose this only when the host lacks authentication and needs durable local users or sessions:

1. Complete the same authorization-code-with-PKCE flow.
2. Call `/oauth2/userinfo` with the AI Pass access token.
3. Map the stable `sub` to a local user record.
4. Mint or resume a normal opaque host session with the host's own cookie protections.

Never use the AI Pass access token itself as the host application's session. AI Pass authorization scopes and host roles remain separate.

## Existing login

When the host already has authentication, attach the encrypted AI Pass grant to the current user. Do not create a parallel login model. Keep account linking explicit and reversible.

Use `"path": "backend-oauth"` in `.aipass/config.json` for this path.
