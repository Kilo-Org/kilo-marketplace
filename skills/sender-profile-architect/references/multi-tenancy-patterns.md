# Multi-Tenancy Patterns for Messaging Apps on Sent — Reference

Supporting reference for `sender-profile-architect`. Patterns that are *specific to messaging workloads* on Sent — high write volume, webhook fan-in across SMS/WhatsApp/RCS, and the compliance constraints carriers, Meta, and Google impose. Generic multi-tenant SaaS theory is covered exhaustively elsewhere; this doc only captures what changes when SMS, WhatsApp, and RCS run through Sent.

## What a Sender Profile owns

A Sender Profile is *one tenant's sending identity* across the channels that profile uses. It carries `name`, `description`, `short_name`, `status` (`incomplete | pending_review | approved | rejected`), and a `settings` block of `{default_channel, webhook_url, timezone, language}`. Each channel attaches separately:

- **SMS** — TCR Brand (`/v3/brands`) + at least one Campaign (`/v3/brands/{brandId}/campaigns`), plus one or more phone numbers / short codes.
- **WhatsApp** — Meta WABA + WABA phone numbers (configured via the Sent dashboard / Channels page).
- **RCS** — Google RBM agent (not self-service; via Sent support).

A tenant may have multiple profiles (one per brand, region, or use case). Auth is a single account-level `x-api-key`; that key can operate on any profile the account owns.

## Webhook Routing (the hot path)

Sent fans channel events into a unified payload shape:

```json
{
  "field": "message",
  "sub_type": "message.delivered",
  "timestamp": "2026-01-15T10:35:00+00:00",
  "payload": {
    "account_id": "<UUID>",
    "message_id": "<UUID>",
    "message_status": "DELIVERED",
    "channel": "sms",
    "inbound_number": "+1...",
    "outbound_number": "+1...",
    "template_id": "<UUID>"
  }
}
```

Top-level fields: `field`, `sub_type`, `timestamp`, `payload`. `sub_type` follows `<field>.<event>` (e.g., `message.delivered`, `message.failed`, `message.read`).

Routing back to a Sender Profile uses what your application persisted at send time, joined on stable IDs in the payload:

| Channel | Verified payload fields | Used to find |
|---|---|---|
| All | `payload.message_id` | the profile that owns this outbound message |
| All | `payload.account_id` | the customer account |
| All | `payload.channel` + `payload.outbound_number` | the configured sender |
| All | `payload.template_id` | the template / its owning profile |

Narrow webhook subscriptions with `event_filters`:

```json
"event_filters": { "message": ["delivered", "failed"] }
```

Shape: `{<parent>: [<sub_type_suffix>, ...]}`. Combine with `event_types: ["message"]` to subscribe to the `message` parent and only fire on the listed sub-types.

ACK fast (≤ webhook `timeout_seconds`, default 30s, max 120s; Sent retries up to `retry_count`, default 3, max 5). Synchronous business logic in the webhook handler kills throughput because three platforms upstream all retry on slow / 5xx responses.

Two failure modes to design out:

- **Cold routing key.** A webhook arrives for an `outbound_number` or `template_id` you haven't mapped (the tenant added a number out-of-band, or a template was created in another environment). Log, return 200, alert ops — don't drop the event.
- **Slow routing-key lookup.** Cache the `message_id` → profile mapping aggressively, but back it with durable storage so cold pods resolve correctly.

## Per-Channel Rate-Limit Accounting

You account for limits at four layers. Track per-channel; bill at the profile.

| Source | Limit | Where it comes from |
|---|---|---|
| **Sent — standard endpoints** | 200 req/min, burst 50 | Sent API gateway |
| **Sent — sensitive endpoints** | 10 req/min, burst 5 (e.g., `POST /v3/webhooks/{id}/rotate-secret`, `POST /v3/users`, `POST /v3/profiles/{id}/complete`) | Sent API gateway |
| **Sent — message sending tier** | Starter 60/min · Growth 300/min · Enterprise custom | Sent plan tier |
| **Sent — webhook test** | 60/min | Sent API gateway |
| **SMS — TCR campaign TPS** | Per-campaign throughput, assigned after vetting | TCR + carrier reconciliation |
| **WhatsApp — phone-number tier** | 1K / 10K / 100K / unlimited business-initiated conversations per 24h, plus Cloud API CPS | Meta — readable from the phone-number record |
| **RCS — agent QPS** | Google RBM | Google |
| **Your per-profile quota** | Whatever you actually sell | Your billing layer |

Rate-limit responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and (on 429) `Retry-After`. The error code on 429 is `BUSINESS_002`.

Bill against the Sender Profile, not the customer account — an account with three brands gets three meters.

## Idempotency

Header: `Idempotency-Key: <key>` where the key matches `^[a-zA-Z0-9_-]{1,255}$`. Cached for **24 hours**, scoped **per customer account**.

Concurrent requests with the same key → second returns `409 CONFLICT_001`. Replays carry `Idempotent-Replayed: true` and `X-Original-Request-Id: <original>` headers.

**Same key + different payload → returns the cached response for the *first* payload, not a new one.** Use a unique key per distinct operation. A safe pattern: hash `(profile_id, operation, client_intent_id)` into the key so a re-send of the same business intent is idempotent but a different intent on the same profile is not.

Supported on all profile mutations:
- `POST /v3/profiles`, `PATCH /v3/profiles/{id}`, `DELETE /v3/profiles/{id}`
- `POST /v3/profiles/{id}/complete`

And on every other mutation endpoint listed in the snapshot (`/v3/messages`, `/v3/contacts`, `/v3/templates`, `/v3/brands`, `/v3/brands/{id}/campaigns`, `/v3/webhooks`, `/v3/users`).

Sandbox mode (`"sandbox": true` in the body) stacks with idempotency — validates the request, returns a realistic fake response, and caches it for 24 hours. Useful for CI per-tenant smoke tests.

## Outbound Message Idempotency

Outbound message sends should also be idempotent on the tuple `(profile_id, channel, client_message_id)` at the application layer. Persist the intent to send *before* the upstream `POST /v3/messages` — if the call succeeds but your write fails, a retry would otherwise duplicate. Pair this with a stable `Idempotency-Key` on the Sent request itself so Sent collapses the duplicate even if your row write reaches Sent first.

## State Reconciliation (per channel)

The Profile resource exposes a coarse `status` (`incomplete | pending_review | approved | rejected`). Per-channel readiness (TCR vetting score, WhatsApp messaging tier, RBM launch state) is not in this snapshot — re-fetch from the dashboard or upstream APIs on a schedule:

- **TCR / SMS** — campaign vetting score updates and carrier-level filtering changes don't always fire webhooks. Reconcile daily for healthy campaigns, hourly when state was recently changing.
- **WhatsApp** — phone-number quality rating and messaging tier change without webhooks. Re-fetch every few hours; alert on transitions.
- **RCS** — agent launch state and carrier rollout status update silently. Re-fetch daily for launched agents and more often during initial verification.

Track when each channel was last reconciled so dashboards can show how stale each profile is. Don't conflate this internal staleness with Sent's `status` field.

## Channel-Specific Anti-Patterns

- **WhatsApp** — Sharing one Meta System User token across multiple Sender Profiles. Token revocation now disables every profile.
- **SMS** — Reusing a TCR campaign across tenants. The campaign vetting score follows whoever the brand says it is — share at your peril.
- **RCS** — Hardcoding the RBM agent into the application instead of attaching it to a Sender Profile. Multi-region or multi-brand tenants will need multiple agents and the code path forks.
- **All** — Synchronous webhook processing. Throughput dies and the platforms retry aggressively.
- **All** — Claiming "data residency" by application-level filtering when the legal commitment is storage-level isolation.

## Tenant Offboarding

When a tenant churns, run the per-channel teardown — not just a state flag:

- **SMS** — deactivate the TCR campaign(s), release the phone number(s) per Sent's release flow.
- **WhatsApp** — unsubscribe your app from the WABA, revoke the System User token.
- **RCS** — unlaunch / suspend the RBM agent (via Sent support).

Then `DELETE /v3/profiles/{id}` to soft-delete the profile (use an `Idempotency-Key`). Disable or delete webhook subscriptions that fan into this profile. Schedule message-content deletion per your retention policy.
