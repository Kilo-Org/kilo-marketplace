# Preserve existing authentication and billing

Treat AI Pass as an additional user-funded model-access path unless repository evidence and an explicit user request say otherwise.

## Existing authentication

- Keep the current user model, session cookie, roles, and account lifecycle.
- With the browser SDK, wallet connection is an app authorization, not a replacement host login.
- For shared-browser safety, decide whether host logout or account switching must also call `AiPass.logout()` so a different host user cannot inherit the prior wallet connection. Preserve independent wallet persistence only when that is an intentional product decision.
- With backend OAuth, attach encrypted AI Pass tokens to the current local user.
- Offer AI Pass login only when no host authentication exists and durable local identity is needed.

## Existing subscriptions or credits

- Keep active plans, trials, credit balances, and entitlements working.
- AI Pass changes who funds an allowed model call; it does not bypass the host's feature entitlements, subscription paywall, age gate, role check, moderation rule, or usage policy unless the user explicitly requests and approves that product change.
- Add an explicit funding choice such as "Pay per use with AI Pass" where users choose how to run the AI action.
- Keep the existing provider or funding source selected by default. AI Pass is an explicit per-call opt-in unless the user requests a broader migration.
- Preserve the existing provider adapter. Route only the selected proof feature first.
- Do not double-charge, decrement app credits on an AI Pass-funded call, or send both provider and AI Pass requests.
- Do not retry a paid call when the first request may have succeeded.

## Existing provider keys

Do not delete or expose provider credentials. Preserve the host's established secure key-storage and handling design; in particular, do not move server-secured provider keys into browser or local storage. Never default provider keys to `localStorage`, browser storage, or device storage. If no design or repository evidence is available, do not recommend a storage location; resolve the required trust boundary before choosing one. Keep server-side providers as a fallback or subscription path. The browser SDK public client ID is not a provider key and should not enter the server secret store.

## Report the boundary

State which path funds each call, which existing behavior remains unchanged, and what user choice was added. If migration is desired later, propose it separately after the first real AI Pass call works.
