# Sender Profile Data Model — Reference

Supporting reference for `sender-profile-architect`. Captures the conceptual model Sent exposes for a Sender Profile and the resources that attach to it, as verified against the Sent v3 docs snapshot.

This doc is **conceptual**, not a schema dump. Resource shapes evolve; the relationships below are what stabilize them.

## Authentication context

In v3, authentication is header-only with a single key per account:

```http
x-api-key: <UUID>
```

The dashboard exposes a per-profile `x-sender-id` value for inspection and v2 legacy routing, but v3 API auth needs only `x-api-key`. API keys are issued at the **customer account** level, not per profile — a single API key can list, retrieve, create, update, complete, or delete any profile the account owns via `/v3/profiles*` endpoints.

## Sender Profile resource (verified)

The verified Profile model in Sent v3:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Stable, Sent-issued |
| `name` | string | Display name |
| `icon` | string \| null | URL |
| `description` | string \| null | Human-readable description |
| `short_name` | string \| null | Compact label |
| `role` | `admin` \| `billing` \| `developer` \| null | The calling user's role within this profile |
| `status` | `incomplete` \| `pending_review` \| `approved` \| `rejected` \| null | Setup status — these are the **only** Sent-side enum values |
| `created_at` | ISO8601 | |
| `settings` | object | `{default_channel, webhook_url, timezone, language}` |

Note: `role` is the *calling user's* role in this profile, not a property of the profile itself. The org-level role enum (Owner / Admin / Billing / Developer) is the full set; the field omits `Owner` because that's billing-owner-only.

## Sender Profile -> Channels -> Webhooks

```
Customer account (one x-api-key)
   │
   ├── SenderProfile (1..N)
   │     ├── id, name, short_name, description, icon
   │     ├── status: incomplete | pending_review | approved | rejected
   │     ├── role (caller's role: admin | billing | developer)
   │     ├── settings.default_channel    ── routes if /v3/messages omits "channel"
   │     ├── settings.webhook_url        ── per-profile webhook destination
   │     ├── settings.timezone, .language
   │     │
   │     └── Channels (attached via dashboard / compliance flow)
   │            ├── SMS      → Brand (TCR) → Campaign(s)
   │            ├── WhatsApp → WABA + phone number(s)
   │            └── RCS      → RBM agent (via Sent support)
   │
   └── Webhooks (configured separately; can be per-profile or shared)
         ├── id, display_name, endpoint_url, is_active
         ├── event_types: ["message", "templates", ...]
         ├── event_filters: {<parent>: [<sub_type_suffix>, ...]}
         ├── signing_secret, retry_count (1-5, default 3),
         │   timeout_seconds (5-120, default 30)
         └── last_delivery_attempt_at, last_successful_delivery_at,
             consecutive_failures
```

Webhook payloads have the shape:

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

`payload.account_id` is the customer-account-level UUID. The payload does not currently include a top-level `profile_id`; routing back to a profile relies on the channel/numbers/template recorded at send time.

## How channels attach to a profile

Channels are configured per-profile through the Sent dashboard and compliance flow. Each channel attachment carries the regulator-facing identity for that channel:

| Channel | Attached identity | Sent endpoints |
|---|---|---|
| SMS | A TCR-registered brand + at least one campaign, plus phone numbers / short codes | `/v3/brands`, `/v3/brands/{brandId}/campaigns` |
| WhatsApp | A Meta WABA + one or more WABA phone numbers (linked through Sent's Channels / WABA Embedded Signup flow) | Dashboard-only configuration in v3 |
| RCS | A Google RBM agent (not self-service; initiated via `support@sent.dm`) | Dashboard-only configuration in v3 |

Two consequences fall out of this model:

1. **Provisioning is per-channel and largely dashboard-driven.** A profile's `status` (`incomplete | pending_review | approved | rejected`) is the rollup; per-channel readiness is tracked alongside it but not in the verified Profile resource. If your application tracks finer-grained channel readiness it should label those as internal app states, not Sent enum values.
2. **Channel identifiers are the inbound routing keys.** The data model is what makes "look up the Sender Profile from an inbound phone number / WABA / RBM agent" possible — but in v3 those joins are made on data you persist at send time, not on a `profile_id` carried in the inbound webhook payload.

## Brands and Campaigns (SMS / 10DLC)

The word *brand* shows up at two layers — keep them distinct:

- **Profile metadata** — the `name`, `description`, and `short_name` on the Sender Profile, used for display and as default sender identity.
- **TCR Brand** — the legal-entity record registered with The Campaign Registry, mandatory for US 10DLC SMS. Sent exposes these as first-class resources:
  - `GET /v3/brands`, `POST /v3/brands`, `PUT /v3/brands/{brandId}`, `DELETE /v3/brands/{brandId}`
  - `POST /v3/brands/{brandId}/campaigns`, `PUT /v3/brands/{brandId}/campaigns/{id}`, `DELETE /v3/brands/{brandId}/campaigns/{id}`

```
SenderProfile (Sent)
  └── SMS channel
       └── TCR Brand (1)
            └── TCR Campaign (1..N) ─── carrier filtering happens here
```

For 10DLC details and use-case selection, see `sms-10dlc-registration`.

WhatsApp has no direct analogue of TCR Campaigns — per-template approval (via `/v3/templates`) plays a similar role. RCS uses one RBM agent per profile per region.

## Webhooks

Webhooks are configured at the account level and can be scoped to a profile via `settings.webhook_url`, or you can configure a single webhook URL and route on the payload (`payload.account_id`, `payload.channel`, `payload.outbound_number`, `payload.template_id`).

Key webhook config fields:

- `event_types` — list of parent event types subscribed (e.g., `["message"]`, `["message", "templates"]`).
- `event_filters` — narrow within a parent type: `{"message": ["delivered", "failed"]}` only fires for `message.delivered` and `message.failed`.
- `signing_secret` — rotate via `POST /v3/webhooks/{id}/rotate-secret` (sensitive endpoint: 10 req/min limit). Rotation invalidates the old secret immediately.
- `retry_count` 1-5 (default 3), `timeout_seconds` 5-120 (default 30) — Sent will retry up to `retry_count` times if your endpoint times out or 5xxs.
- `consecutive_failures` — surfaced so you can monitor a failing webhook before it's auto-disabled.

## Idempotency

`POST /v3/profiles`, `PATCH /v3/profiles/{id}`, `DELETE /v3/profiles/{id}`, and `POST /v3/profiles/{id}/complete` all support `Idempotency-Key: <key>` where the key matches `^[a-zA-Z0-9_-]{1,255}$`. Keys are cached **per customer account for 24 hours**. See `references/multi-tenancy-patterns.md` for the full idempotency/sandbox behavior across endpoints.

## ER summary

```
Customer account ── x-api-key (one per account)
  │  1..N
  ▼
SenderProfile { id, name, status, role, settings }
  │
  ├── Brand (TCR) ── Campaign(s) ── carrier-filtered SMS senders
  ├── WABA ── PhoneNumber(s)   (configured via dashboard)
  └── RBM Agent                 (configured via Sent support)

Webhooks (separate resource; can be many-to-one with profiles)
  └── event_types[], event_filters{}, signing_secret, retry/timeout config
```

The single architectural rule that follows: every channel-specific record your application stores should reference the Sent **profile `id`**, not the customer `account_id` directly. Account is a foreign key on profile.

## What to confirm against the live OpenAPI

Before writing application code, confirm the endpoint and schema details against the live Sent v3 OpenAPI at https://docs.sent.dm:

- Exact channel-attachment fields on the Profile resource (the snapshot doesn't enumerate per-channel sub-objects).
- Whether `payload.profile_id` is added to webhooks in future API revisions.
- API-key creation + scope semantics (API Keys is dashboard-only in this snapshot).
