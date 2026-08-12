# Browser SDK path

Use this path by default when the product has a browser surface and the selected AI action can safely execute there. It works on localhost and on normal deployments such as Vercel, Replit, Lovable, or a private web host; no Space migration is needed. Begin from the existing user action. If the action depends on a private system prompt, server-only data, privileged authorization logic, or a policy that forbids browser token custody or third-party scripts, choose [backend-oauth.md](backend-oauth.md) instead.

## Public configuration

Use the public client ID returned by `/api/v1/agent-control/oauth-clients/ensure`. Store it in the framework's public environment/configuration system and in `.aipass/config.json`. It is an identifier, not a secret.

Before setup approval, propose a stable URL on every exact browser origin where this integration will run. AI Pass binds the resulting client to those approved origins. The SDK requests a signed, server-bound handoff from `POST https://aipass.one/oauth2/handoff`; it does not use the app as the popup document. Never construct `/oauth2/callback?origin=...` yourself, omit the signed handoff parameters, or add an unapproved origin. A forged or unregistered target fails closed.

Never initialize with a placeholder or include the project setup grant in runtime code.

The official SDK is loaded from the AI Pass origin and is updated by AI Pass. Respect the host's existing CSP and dependency policy. Do not add a broad script exception, disable CSP, copy the SDK into the repository, or invent an integrity hash. When the existing policy disallows this runtime dependency, use backend OAuth.

## Lazy-load from the user action

Use the project's framework conventions. The core browser pattern is:

```js
let sdkPromise;
let paidRequest;

function loadAiPass() {
  if (window.AiPass) return Promise.resolve(window.AiPass);
  if (sdkPromise) return sdkPromise;

  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://aipass.one/aipass-sdk.js';
    script.async = true;
    script.onload = () => {
      if (!window.AiPass) {
        reject(new Error('AI Pass loaded without exposing its SDK'));
        return;
      }
      resolve(window.AiPass);
    };
    script.onerror = () => reject(new Error('AI Pass failed to load'));
    document.head.appendChild(script);
  }).catch((error) => {
    sdkPromise = undefined;
    throw error;
  });

  return sdkPromise;
}

async function generateWithAiPass(prompt) {
  if (paidRequest) throw new Error('An AI Pass request is already running');
  paidRequest = (async () => {
    const AiPass = await loadAiPass();
    if (!AiPass.initialized) {
      AiPass.initialize({
        clientId: PUBLIC_AI_PASS_CLIENT_ID,
        scopes: ['api:access'],
      });
    }
    return AiPass.generateCompletion({ prompt });
  })();

  try {
    return await paidRequest;
  } finally {
    paidRequest = undefined;
  }
}
```

Call `generateWithAiPass` from the app's actual generation button or form submission. Disable duplicate submission while the promise is active. Render `result.choices?.[0]?.message?.content` as text or through the product's existing sanitized result component.

## Preserve the real wallet experience

- Let the first generation action open the SDK connection dialog when needed.
- Let the SDK obtain and use its signed central callback. Direct OAuth callbacks and token exchange still require byte-for-byte exact redirect URIs, and PKCE is S256-only.
- Do not add a separate AI Pass connect button unless the product already has an account-connections surface.
- Do not pre-connect invisibly, fabricate success, suppress cancellation, or retry a paid request after an ambiguous failure.
- Reuse existing loading, error, and result UI.
- When current funding paths exist, keep the existing provider or subscription selected by default. Make AI Pass a deliberate pay-per-use choice for each call rather than replacing them.
- The SDK stores runtime tokens in a client-ID-scoped browser slot. If host logout or account switching must prevent a later host user on the same browser from inheriting that wallet connection, call `await AiPass.logout()` as part of the host's logout or account-switch flow and test it. Do not expose the token to perform this cleanup.

## Add persistence only when the product needs it

The SDK authenticates generation and storage methods at call time. Do not block an action because
`AiPass.isAuthenticated()` is false or wait for `aipass:login`; that prevents the SDK from opening
its automatic login modal and resuming the operation. Catch `AUTH_REQUIRED` only when the user
dismisses the modal.

Use `AiPass.data` for the app's private 1 MB JSON document and `AiPass.files` for its private files.
Use `AiPass.shared` only when the same user deliberately moves data between apps. Shared vaults
contain keyed, revisioned JSON records and private files; grants are `READ`, `CONTRIBUTE`, or
`READ_WRITE` and the SDK displays a user confirmation before granting access. Read
[sdk-storage.md](sdk-storage.md) for the exact API, quotas, and verification rules.

## First proof

Route one representative AI feature. After separate approval for that specific paid action, including the selected model or variable usage basis when the UI can show it, confirm the call connects and charges the user's wallet. Observe one model request for the one action and never retry after an ambiguous paid response. Confirm reuse through authenticated SDK state or the absence of another connection prompt; do not make a second paid call without separate approval.

After implementation, distinguish safe local proof from paid verification. A successful build or lint run means "implemented and built; live wallet-funded verification pending" until the user approves and performs a real call. Then read [feature-opportunities.md](feature-opportunities.md) and offer only the most relevant optional next step. For a new self-contained localhost prototype without an existing deployment target, [spaces-path.md](spaces-path.md) permits one optional offer to publish the same app for online testing; do not steer an existing hosted product to Spaces.
