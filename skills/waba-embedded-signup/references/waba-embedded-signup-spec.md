# WABA Embedded Signup — Implementation Reference

Supporting reference for `waba-embedded-signup`. The Sent v3 docs snapshot (2026-05-19) confirms that **Sent does not expose a public Embedded Signup API endpoint**. The customer-facing surface for connecting WhatsApp to Sent is the **dashboard's Channels → WhatsApp tab**, which is explicitly listed in Sent's "Dashboard pages → API endpoints map" as `(dashboard config; not directly in v3 API)`. The dashboard internally initiates Meta's Facebook Login for Business / Embedded Signup flow on the tenant's behalf.

What this means for an integrator:

- **You do not call a Sent endpoint to start Embedded Signup.** You direct the tenant to their Sent dashboard.
- The Meta-side authentication, token exchange, WABA discovery, phone-number registration, app subscription, and app review state are owned by **Meta** and abstracted by the Sent dashboard. They are not surfaced as Sent API operations.
- After dashboard completion, the WhatsApp wiring is bound to the tenant's Sender Profile and routable via Sent's normal v3 API (`POST /v3/messages`, etc.).

Anything below this line is **external Meta documentation context** — included only so an operator debugging a stuck dashboard flow knows what is happening behind the scenes. Authoritative source: Meta — [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup), [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api), [Facebook Login for Business](https://developers.facebook.com/docs/facebook-login/facebook-login-for-business). Meta bumps the Graph API version regularly — always check the live Meta docs for the current version, scope names, and field names.

## Sent-side surface (what the API does and doesn't expose)

| Concern | Where it lives |
|---|---|
| Start Embedded Signup | Dashboard → Channels → WhatsApp → "Connect" (no public Sent API) |
| WABA / phone-number binding | Dashboard (not in v3 API) |
| Mark profile setup complete | `POST /v3/profiles/{id}/complete` (idempotent, sensitive endpoint — 10/min, burst 5) |
| Profile status after binding | `GET /v3/profiles/{id}` → `status` ∈ `incomplete` \| `pending_review` \| `approved` \| `rejected` |
| Webhook config | `POST /v3/webhooks`, `PUT /v3/webhooks/{id}`, `POST /v3/webhooks/{id}/test`, `POST /v3/webhooks/{id}/rotate-secret` (sensitive — 10/min, burst 5) |
| Auth header | `x-api-key: <UUID>` — single header, account-scoped. No `x-sender-id` in v3. |

## Customer-facing dashboard flow (what the tenant sees)

This mirrors the live flow on the dashboard's Channels page; it is what a tenant should be guided through, not an API sequence:

1. Dashboard → **Channels** → **WhatsApp** tab → click **Connect**.
2. Meta consent popup opens (Facebook Login for Business surface, initiated by Sent).
3. Tenant selects (or creates) a **WABA** under their Meta Business Portfolio.
4. Tenant grants Sent permission to **manage WhatsApp messages and templates** on that WABA.
5. Tenant adds a **Meta payment method** (separate from Sent billing — Meta charges per-conversation independently).
6. Dashboard reflects channel setup completion; the WhatsApp wiring is bound to the tenant's Sender Profile.
7. API credentials (the `x-api-key`) can be copied from the post-setup screen or retrieved later from the dashboard's API Keys page.

The runbook (`references/waba-onboarding-runbook.md`) walks through this end-to-end with failure modes and recovery steps.

## Webhook envelope (Sent-confirmed)

After WhatsApp is connected, Sent emits webhooks for that profile's messages using the universal envelope:

```json
{
  "field": "message",
  "sub_type": "message.delivered",
  "timestamp": "2026-01-15T10:35:00+00:00",
  "payload": {
    "account_id": "<UUID>",
    "message_id": "<UUID>",
    "message_status": "DELIVERED",
    "channel": "whatsapp",
    "inbound_number": "+1...",
    "outbound_number": "+1...",
    "template_id": "<UUID>"
  }
}
```

Sub-types follow `<field>.<event>` (`message.queued`, `message.routed`, `message.sent`, `message.delivered`, `message.failed`, and on WhatsApp/RCS only, `message.read`).

WhatsApp-specific sub-types beyond the universal `message.*` family (e.g., template approval/rejection notifications) are not enumerated in the v3 snapshot. To discover what your account currently subscribes to:

1. List configured webhooks: `GET /v3/webhooks`.
2. Inspect a single webhook's `event_types` and `event_filters` fields.
3. Subscribe broadly to the `message` parent type and observe what arrives in production — fold the observed sub-types into your routing.

## Webhook signature verification

The webhook model (verified) exposes `signing_secret` as a per-webhook field; the exact HMAC algorithm and header name are not specified in the snapshot. Rotate via `POST /v3/webhooks/{id}/rotate-secret` — the old secret is invalidated immediately, so coordinate with the receiver before rotating.

## Meta-side context (for operators only — link, do not reimplement)

When a dashboard tenant is stuck and you need to know what the dashboard is doing on their behalf, the underlying Meta flow looks like this — read Meta's docs for current details:

- Meta app type, Tech Provider / Solution Partner status, granular scopes, Graph version, redirect URI allowlisting → [Embedded Signup docs](https://developers.facebook.com/docs/whatsapp/embedded-signup).
- OAuth code → System User token exchange → [Facebook Login for Business](https://developers.facebook.com/docs/facebook-login/facebook-login-for-business).
- WABA / phone-number lookup, phone-number registration with PIN, app subscription to WABA → [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api).
- App review state, business verification, payment method, quality rating → Meta Business Suite UI.

If a tenant is genuinely operating their own Meta app (not using the Sent-managed dashboard flow), they own all of the above and should be referred to Meta's docs directly. Sent's API does not replace that.

## What is not in the v3 docs snapshot

- The exact shape of the request body for `POST /v3/profiles/{id}/complete` for WhatsApp wiring (the snapshot confirms the endpoint exists and is sensitive; the per-channel payload is not published).
- The webhook signature algorithm / header used to verify Sent → receiver deliveries.
- The mapping shape between Sender Profile and the WABA / phone-number IDs the dashboard binds to it.
- WhatsApp-specific webhook sub-types (e.g., template lifecycle events).

Treat each of these as "discover via your account" rather than "code to a spec".
