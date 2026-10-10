# RBM Agent Spec — Reference

Supporting reference for `rcs-agent-onboarding`. This doc separates **what Sent exposes** about an RCS Agent from **what lives in Google RBM** (the underlying carrier platform). Keep that line bright: anything not in the Sent v3 docs snapshot is external context and should be linked, not mirrored.

Canonical Google source: [RCS Business Messaging docs](https://developers.google.com/business-communications/rcs-business-messaging).

## Sent's RCS setup model (verified)

- **Not self-service.** Per Sent's channel-setup docs, RCS setup requires a one-time carrier approval that has to be initiated by contacting Sent (`support@sent.dm`). There is no dashboard button or v3 API endpoint that provisions an RCS Agent end-to-end on its own.
- **Post-approval visibility.** Once Sent (with Google + the carriers) has finished the approval cycle, the RCS Agent — Sent calls it a **Branded Sender** for RCS — appears in the dashboard alongside the customer's other channels.
- **No rollout-status or capability-check endpoint.** The v3 API does not surface a per-carrier launch state, an agent-ID field, or a recipient capability probe. To observe RCS behavior after launch, use `GET /v3/messages/{id}`, `GET /v3/messages/{id}/activities`, and webhook events (see `references/rcs-fallback-patterns.md`).

If a request implies "click here to create my RCS agent", correct it. The handoff is human-initiated by emailing `support@sent.dm` with the launch evidence packet.

## Sent-side terminology (verified)

These are the terms Sent uses in its public docs and dashboard. Use them when talking to a Sent customer instead of Google's RBM API names.

| Sent term | What it is |
|---|---|
| **RCS Agent** | The branded RCS sender identity that recipients see. Created on Sent's side after carrier approval. |
| **Branded Sender** | Sent's umbrella term for the per-channel sender identity (the RCS Agent for RCS, the WABA-attached phone number for WhatsApp, the 10DLC long code for SMS). |
| **Rich Card** | A single card with media, title, description, and suggestion chips. |
| **Carousel Card** | A horizontally-swiped collection of up to **10** Rich Cards. |
| **Suggestion Chip** | A tap-to-act chip below or inside a message. Three documented kinds: quick reply, open URL, dial number. |

## Google RBM-side concepts (external — link, do not mirror)

The following live entirely in Google's RBM platform and are **not** exposed in the Sent v3 API. Don't pretend Sent surfaces them; treat them as platform context the customer hears about during review.

- Agent identity fields (`displayName`, `logoUri`, `heroUri`, `color`, `verifiedDomains`, contact info) — set during Sent's onboarding handoff, not via Sent v3 API. See [Google's agent reference](https://developers.google.com/business-communications/rcs-business-messaging/reference/business-communications/rest/v1/brands.agents).
- RBM capabilities the agent must declare (suggested replies, suggested actions, standalone rich card, rich card carousel, file/image/video/audio attachments). See [Google's capabilities guide](https://developers.google.com/business-communications/rcs-business-messaging/guides/build/capabilities).
- RBM use case taxonomy (`TRANSACTIONAL`, `OTP`, `PROMOTIONAL`, `CUSTOMER_CARE`, `MULTI_USE`).
- Verification and launch-review lifecycle (Google review → per-carrier review → carrier-specific `ENABLED` / `PENDING` rollout). Typical turnaround: 1-7 business days for verification; longer for launch.
- Per-carrier rejection codes and rejection reasons. See [Google's launch guidance](https://developers.google.com/business-communications/rcs-business-messaging/guides/learn/launch).
- Capability-check endpoint (`https://rcsbusinessmessaging.googleapis.com/v1/users/{phoneNumber}:capabilities`) — Google-side, requires direct RBM API access, not part of Sent v3.

## What Sent does NOT expose (gap notes)

These would be useful for an agent but are not in the v3 docs snapshot:

- A field on the message resource indicating per-carrier launch state for the originating RCS Agent.
- A capability-check endpoint on Sent's side.
- A public `fallback_policy` field — channel selection is done via the `channel` array on the send request (see `references/rcs-fallback-patterns.md`).
- A structured RBM rejection code on failed messages. The `message.failed` webhook carries `payload.message_status = FAILED`; the human-readable reason lives in the `description` of the message detail fetched via `GET /v3/messages/{id}`.

## Anti-patterns

- Claiming Sent surfaces an `agentId` or per-carrier rollout state in v3 — it doesn't.
- Promising the customer they can self-serve an RCS Agent through the dashboard — the docs explicitly say to contact `support@sent.dm`.
- Restating Google's agent JSON schema in this file — link to Google's docs instead so this skill stays small and current.
- Using Google-side names (`displayName`, `verifiedDomains`) when talking to a Sent customer about their dashboard. Use Sent's terms (RCS Agent, Branded Sender, Rich Card, Carousel Card, Suggestion Chip).
- Treating a Carousel Card as unbounded — Sent's docs cap it at 10 Rich Cards.
