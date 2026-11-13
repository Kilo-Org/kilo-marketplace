# WhatsApp ↔ Sent Sender Profile Mapping

How Meta-side entities created during Embedded Signup map onto Sent's Sender Profile model. Read this before deciding how many profiles to create per tenant, or when debugging why a webhook landed on the wrong profile.

For the broader multi-channel architecture (one profile owns SMS + WhatsApp + RCS halves; how to split tenants across profiles), see `sender-profile-architect`.

## The entities

**Meta side:**
- **Business Manager / Business Portfolio** — the tenant's legal/operational umbrella in Meta Business Suite.
- **WABA (WhatsApp Business Account)** — owns templates and phone numbers; the unit Meta bills.
- **Phone Number** — a single E.164 number registered for Cloud API on a WABA.
- **System User** — long-lived identity holding the access token used to call Graph API on behalf of the tenant.

**Sent side (v3 — schema verified against snapshot):**

A Sender Profile is:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | The Sent-side primary key. |
| `name` | string | Display name. |
| `icon` | string \| null | URL. |
| `description` | string \| null | |
| `short_name` | string \| null | |
| `role` | `admin` \| `billing` \| `developer` \| null | Caller's role on this profile. |
| `status` | `incomplete` \| `pending_review` \| `approved` \| `rejected` \| null | Setup status. |
| `created_at` | ISO8601 | |
| `settings` | object | `{default_channel, webhook_url, timezone, language}` |

There is **no public `channels.whatsapp` sub-resource** on the Profile in the v3 docs snapshot. Per-channel WhatsApp wiring (WABA ID, phone-number ID) is performed via the dashboard Channels page, which is explicitly listed as "dashboard config; not directly in v3 API". Treat WABA and phone-number IDs as external provider identifiers that the dashboard binds to the profile; do not invent v3 endpoints to mutate that binding.

Auth in v3 is a single header — `x-api-key: <UUID>` — at the account level. `x-sender-id` is **v2 legacy** and is exposed per profile in the dashboard for routing, not as a v3 API auth requirement.

## ASCII map

```
Tenant
  │
  ├── Business Manager (1)
  │     │
  │     ├── WABA #A ────────────────────────► Sender Profile P1 (id, status=approved)
  │     │     ├── Phone +1 555 0100  ◄────────┤  (dashboard-bound)
  │     │     ├── Phone +1 555 0101  ◄──┐     │
  │     │     └── Templates              │    │
  │     │                                │    │
  │     │                                └────► Sender Profile P2
  │     │                                     │  (different phone, same WABA)
  │     │
  │     └── WABA #B ────────────────────────► Sender Profile P3
  │           └── Phone +44 20 7946 0000 ◄────┤
  │
  └── System User (1) ──► token held in vault, referenced by all of P1/P2/P3
```

## Cardinality rules (operational, not enforced by v3 API)

| Relationship | Cardinality | Notes |
|---|---|---|
| Business Manager → WABA | 1 : N | A tenant may operate multiple WABAs (per region or brand). |
| WABA → Phone Number | 1 : N | Up to 25 per WABA per Meta's current limits. |
| Phone Number → Sender Profile | 1 : 1 | **Hard rule.** Each phone number routes to exactly one profile; sharing breaks inbound routing. |
| WABA → Sender Profile | 1 : N | Multiple profiles may bind to the same WABA, each pinning a different phone number. |
| System User → WABA | 1 : N | One System User token can hold scopes for many WABAs. |
| Sender Profile → WhatsApp wiring | 0 : 1 | A profile has at most one WhatsApp binding. SMS / RCS bindings are independent. |

## What `POST /v3/profiles/{id}/complete` actually does

`POST /v3/profiles/{id}/complete` is confirmed in the v3 snapshot as the profile-completion endpoint. It supports `Idempotency-Key` and is classified as a sensitive endpoint (10 req/min, burst 5). It transitions the profile out of `incomplete` once prerequisites are met.

The exact request/response shape for the completion call (which fields must be present, what gets persisted) is **not enumerated in the v3 snapshot**. Treat the completion call as a commit: prerequisites (KYC + channel config done via the dashboard) must already be true; the endpoint signals "I am ready". Check the live OpenAPI at [docs.sent.dm](https://docs.sent.dm) before wiring a tenant-facing integration.

## Routing inbound events back to a profile

Sent's webhook envelope (verified) is:

```json
{
  "field": "message",
  "sub_type": "message.delivered",
  "timestamp": "2026-01-15T10:35:00+00:00",
  "payload": { "account_id": "...", "message_id": "...", "channel": "whatsapp", "inbound_number": "+1...", "outbound_number": "+1...", "template_id": "..." }
}
```

For WhatsApp inbound, the payload carries `account_id`, `message_id`, and the inbound/outbound E.164 numbers. WhatsApp-specific sub-types beyond the generic `message.*` family (e.g., template-status events) are not enumerated in the snapshot — discover them empirically against your account by subscribing broadly and observing what arrives.

## Detaching a WABA without losing message history

There is no v3 API endpoint documented for detaching a WhatsApp binding from a profile. The Channels page in the dashboard is the surface. Operationally:

1. Stop sending on the profile.
2. Wait for in-flight deliveries to settle (delivery webhooks drain within ~24h for normal traffic, longer for slower carriers).
3. Use the dashboard Channels page to remove the WhatsApp binding.
4. On the Meta side, unsubscribe your Tech Provider app from the WABA via Graph API if you held the subscription directly.

Historical MDRs remain queryable by `message_id` — message history is not deleted when the binding is removed.

## Migrating a phone number between WABAs

Meta supports moving a phone number between WABAs and the phone-number ID is stable across the move. On Sent's side, the dashboard Channels page is the supported surface to re-bind. Since the v3 docs do not publish the channel-config mutation endpoint, do not encode a `PATCH /v3/profiles/{id}/channels/whatsapp` call in client integrations — operate via the dashboard until the API is published.

Templates are WABA-scoped and do **not** transfer with the phone number — re-author or re-import on the new WABA.
