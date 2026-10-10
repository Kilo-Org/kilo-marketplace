# Template Status Handling

The lifecycle states a Sent template moves through, which fields are editable in each, how the UI gets notified of upstream changes, and how to handle resubmission. The builder UI tracks every template against the state machine below.

## Status enum

Sent's template status enum is exactly four states the UI renders, regardless of underlying channel: `Draft`, `Pending`, `Approved`, `Rejected`. There is **no `PAUSED` state in Sent.** Meta's upstream `PAUSED` flag exists Meta-side only and is not surfaced into the Sent template-status enum.

| State | Meaning | Source |
|---|---|---|
| `Draft` | Authored locally, not yet submitted | Sent-internal |
| `Pending` | Submitted, awaiting review (WhatsApp = Meta review, typically 24–48 hours per Sent docs; RCS = Google review; SMS does not gate on review) | Set by Sent on submit, cleared by upstream callback |
| `Approved` | Live and sendable | Set by Sent on upstream approval |
| `Rejected` | Upstream rejected the submission | Set by Sent on upstream rejection, carries a `rejection_reason` payload |

Other upstream states (Meta `PAUSED`, `DISABLED`, `IN_APPEAL`, etc.) do not appear as Sent statuses. If your UI needs to surface a Meta-only signal (e.g. a deliverability pause), treat it as a secondary annotation on an `Approved` row — never bucket those rows as `Rejected`.

**During `Pending`, SMS sends still work.** Per Sent docs, a template can be sent over SMS while it is still awaiting WhatsApp approval — the `Pending` status gates only the channels that require upstream review. Reflect this in the UI: don't grey out the entire row, only the WhatsApp/RCS send actions.

## Editable fields by state

| Field | Draft | Pending | Approved | Rejected |
|---|:-:|:-:|:-:|:-:|
| Name | edit | locked | locked | locked |
| Language | edit | locked | locked | locked |
| Category | edit | locked | locked (Meta may silently change it — see below) | locked |
| Channel | edit | locked | locked | locked |
| Body | edit | locked | edit (creates v2) | edit |
| Header type | edit | locked | locked | edit |
| Header text/media | edit | locked | edit | edit |
| Footer | edit | locked | edit | edit |
| Button types (radio) | edit | locked | locked | edit |
| Button labels | edit | locked | edit | edit |
| Variable samples | edit | locked | edit | edit |

Editing an **Approved** template's editable fields does not mutate the live template — it creates a new version on submit, while the prior version continues to send until the new one is approved. Make this obvious in the editor footer ("Submitting creates v2; v1 keeps sending until v2 is approved").

In **Pending**, surface a "Withdraw and edit" affordance — it calls the Sent withdraw endpoint and moves the template back to Draft.

> The locks above are a **product-governance** choice. The Sent v3 `PUT /v3/templates/{id}` endpoint accepts name/language/category in its request body; whether those fields are truly immutable server-side after first save is not documented in the snapshot and should be verified against the live OpenAPI before relying on it.

## Webhook vs polling

Sent webhook events follow a top-level `field` + `sub_type` envelope, with `sub_type` formatted as `<field>.<event>` (e.g., `message.delivered`, `message.failed`). Template status changes are inferred to follow the same pattern (e.g., `template.approved`, `template.rejected`, or a single `template.status_changed`) — the snapshot confirms the envelope but does not enumerate template-specific events. **Discover the exact event names via `GET /v3/webhooks/event-types` for your account** and subscribe via `POST /v3/webhooks` with the relevant `event_types` / `event_filters` shape.

Two reasonable UI approaches:

- **Webhook + realtime fanout** (preferred). The backend receives the Sent webhook, fans out to the relevant tenant's realtime channel (Pusher / Ably / Supabase Realtime / WebSocket), and the list row updates in place. Lowest latency, no client polling load. Use when you already have a realtime layer for other reasons.
- **Short polling** (acceptable fallback). The list view polls `GET /v3/templates?status=pending` every 5–10s while any row is in Pending; stops polling when none remain. Simpler to ship; more network load. Use when you don't yet have realtime infrastructure.

Do *not* poll per-row — always poll the list filter — and do not poll forever. Cap at e.g. 30 min after submit; beyond that, the tenant must refresh.

## Rejection reason display: Meta vs Sent

Two distinct rejection sources, and the UI should render them differently:

- **Meta-surfaced rejection.** The `rejection_reason` Sent forwards from Meta's template-status update. Render this as a sticky banner with the human-readable reason on top, the raw Meta enum (e.g. `INVALID_FORMAT`, `ABUSIVE_CONTENT`, `INCORRECT_CATEGORY`) collapsed by default, and a Sent-maintained remediation hint mapped from the enum.
- **Sent-surfaced rejection.** When Sent's own pre-submission validation (the server-side mirror of the matrix) rejects the payload before forwarding to Meta. Render with a different icon and label ("Caught by Sent before submission") so tenants don't think Meta reviewed the template.

Never show the raw Meta JSON — it's noisy and changes shape. Always go through the Sent-normalized rejection-reason API.

## Resubmission flow

After editing a Rejected template:

1. The Submit button triggers a *new submission attempt* against the existing template record. The template ID stays stable; only the `attempt_id` increments.
2. The list row transitions Rejected → Pending in place; do not create a duplicate row.
3. The rejection-reason banner is dismissed automatically when the new attempt enters Pending.
4. On Approval, the row turns green and the banner stays gone. On a fresh Rejection, render the new reason — and add a "previous reasons" disclosure showing the prior failures so tenants can see they're not regressing.

For Approved templates, "resubmit" is really "submit a new version" — covered above in Editable fields.

## Silent re-categorization

Meta may re-categorize an Approved template (most commonly `UTILITY` → `MARKETING`) without changing its status. If Sent surfaces this (event name not enumerated in the snapshot — verify against `GET /v3/webhooks/event-types`), the list-row UI should render a one-time dismissible banner ("Meta moved this template to Marketing — it will now bill at marketing rates"). Tenants who miss this end up surprised by billing. See the `template-builder-ui` SKILL.md for the editor-side treatment.
