# RCS Fallback Patterns — Reference

Supporting reference for `rcs-agent-onboarding`. Covers how Sent expresses RCS-to-SMS fallback (the `channel` array on the send request), what the documented webhook events tell you, and where the boundary sits between Sent-verified behavior and Google RBM-side semantics.

External error semantics live at [Google's RBM error reference](https://developers.google.com/business-communications/rcs-business-messaging/reference/rest) — this doc only covers Sent's wrapping.

## How fallback is expressed (verified)

Sent does **not** expose a separate `fallback_policy` field in v3. Fallback intent is expressed entirely by the ordered `channel` array on `POST /v3/messages`:

```json
{
  "to": ["+15551234567"],
  "channel": ["rcs", "sms"],
  "template": { "id": "template_uuid" }
}
```

| Array | Behavior |
|---|---|
| `["rcs"]` | RCS-only. If RCS can't deliver, the message fails. No SMS attempt. |
| `["rcs", "sms"]` | Documented fallback pattern. SMS is the explicit fallback target. |
| `["sms", "whatsapp", "rcs"]` | Per the v3 docs, an array with multiple channels creates **one message per channel** — all dispatch. This is a multi-channel broadcast, not a waterfall. |
| `["sms"]` | SMS-only. Used during agent provisioning before RCS is live. |
| (omitted) | Sent picks the optimal channel automatically based on the recipient's `available_channels`. |

Two things worth surfacing to a customer:

1. **Multi-channel arrays are broadcast, not waterfall.** The v3 docs describe `["sms", "whatsapp", "rcs"]` as producing one message per channel that all dispatch. If you want a strict RCS-first-with-SMS-fallback waterfall, the documented shape is `["rcs", "sms"]`. Anything longer needs explicit confirmation with Sent.
2. **No `fallback_policy` field exists in v3.** Documentation, dashboards, or examples that reference one are inferring a v2 concept. Use the channel array.

## When fallback fires (inferred — confirm before promising)

Sent's docs verify that RCS "falls back to SMS automatically for non-RCS-capable recipients" and that `["rcs", "sms"]` makes that explicit. The docs do **not** enumerate every trigger condition (capability mismatch vs. carrier-pending vs. RBM outage). Treat the following as inferred and confirm with Sent if a customer needs exact semantics:

- Recipient device not RCS-capable
- Recipient on a carrier where the RCS Agent is not yet rolled out
- RBM transient unreachability

For day-to-day customer guidance, "if RCS can't deliver, SMS is attempted" is the documented promise. The why-it-fell-back detail surfaces in the message's failure description (see below).

## Content trimming on fallback (external)

The v3 docs don't specify what happens to rich content (Rich Cards, Carousel Cards, Suggestion Chips) when a message authored for RCS falls back to SMS. SMS has no equivalent for any of those components.

The safe default is to **author SMS-side content explicitly** rather than rely on automatic trimming. The `template-builder-ui` skill covers the dual-authoring workflow.

If a customer needs an exact answer about Sent's trimming behavior, escalate to `support@sent.dm` — it's not in v3 docs.

## Verified webhook events for message lifecycle

Sent's quickstart docs verify this lifecycle. Sub-types follow `message.<event>`:

| Event | Meaning |
|---|---|
| `message.queued` | Send accepted, waiting to dispatch |
| `message.routed` | Assigned to a carrier/provider |
| `message.sent` | Dispatched to the carrier/RCS/WhatsApp provider |
| `message.delivered` | Confirmed delivery to device |
| `message.read` | Recipient opened. RCS and WhatsApp only. |
| `message.failed` | Delivery failed at any stage. `payload.message_status = FAILED`. Fetch `GET /v3/messages/{id}` for the reason. |

Webhook payload shape (top-level):

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

The `payload.channel` field is what tells you which channel actually delivered. To distinguish "RCS delivered" from "SMS fallback delivered" for the same logical send, inspect `payload.channel` on the `message.delivered` event.

### Events that are NOT verified — do not assume they exist

Earlier drafts of this skill referenced events like `message.channel_selected` and `message.fallback_triggered`. **Those names are not in the v3 docs.** The only verified `message.*` sub-types are `queued`, `routed`, `sent`, `delivered`, `read`, `failed`.

If a customer's integration depends on a dedicated "fallback fired" event, reconstruct it from what's documented:

- For an `["rcs", "sms"]` send, observe `message.delivered` events and check `payload.channel` — `"sms"` on what was meant to be an RCS-first send is the fallback signal.
- For a failed RCS attempt that succeeded via SMS, the v3 docs don't promise an explicit pairing. Reconstruct by correlating `message.failed` (RCS) with a separate `message.delivered` (SMS) sharing the same logical send.
- If you genuinely need a dedicated fallback event, ask Sent — don't invent the name.

### Send-time failure codes (verified)

On `message.failed`, fetch the message and read `description`. Verified codes that may appear:

| Code | Meaning |
|---|---|
| `ERR_CONSENT_BLOCKED` | Recipient is opted out or on suppression list. No provider call. |
| `ERR_ROUTE_DENIED` | No active route could deliver to the requested channel/country. |
| `ERR_TEMPLATE_PARAMS_INVALID` | Required template variables missing or failed regex validation. |

Per-carrier RBM rejection codes are external (Google) and not surfaced as a structured field in v3.

## Testing fallback in lower environments

Sent's v3 docs document **sandbox mode** as the testing affordance: add `"sandbox": true` to the request body and the API returns a realistic fake response without a provider call. Response includes `X-Sandbox: true` header.

Sandbox mode is documented for `POST /v3/messages` and most other mutation endpoints.

The v3 docs do **not** document a `force_fallback` flag, a test-recipient registry, or per-carrier launch-state overrides. Earlier drafts referenced these — treat as inferred / unverified. If a customer needs to exercise the SMS-fallback path specifically in a lower environment, the documented approach is:

1. Send with `sandbox: true` to validate request shape without side effects.
2. To exercise the real fallback path against the real provider chain, send with a small recipient list including known-non-RCS-capable numbers.
3. For pre-launch testing, send with `["sms"]` first to confirm SMS compliance and webhook plumbing, then introduce `["rcs", "sms"]` once RCS is approved.

## What's NOT in v3 (gap notes)

- A dedicated `message.fallback_triggered` webhook event.
- A `message.channel_selected` event.
- A `fallback_policy` field on the Sender Profile or on the send request.
- A `force_fallback` flag for non-prod testing.
- An MDR export schema documenting `attempted_channels` / `delivered_channel` fields.
- Per-carrier rollout-status fields.

Anything above that appears in customer-facing guidance should be flagged as inferred and confirmed with Sent before relying on it.

## Anti-patterns

- Inventing a `fallback_policy` field — it doesn't exist in v3; use the `channel` array.
- Inventing `message.fallback_triggered` or `message.channel_selected` webhook events — they're not in the documented lifecycle.
- Sending with `["rcs"]` and expecting SMS to back it up. RCS-only means RCS-or-fail.
- Treating a long channel array like `["rcs", "whatsapp", "sms"]` as a waterfall. Per v3 docs, multiple channels create one message per channel (broadcast). Use `["rcs", "sms"]` for the documented fallback shape.
- Assuming Sent auto-trims rich RCS content gracefully into SMS. Trimming behavior isn't in v3 docs — author SMS variants explicitly.
- Using `sandbox: true` in production traffic — sandbox is for tests, not real sends.
