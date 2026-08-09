---
name: rcs-agent-onboarding
description: >-
  Guides RCS/RBM onboarding for Sent customers by preparing agent identity,
  launch evidence, carrier-approval handoff, SMS fallback, and post-launch
  verification. Use when a user says RCS agent, RBM, rich business messaging,
  carrier launch, RCS approval, RCS fallback, branded messages, agent
  verification, capability check, or wants to send RCS through Sent.
metadata:
  category: business
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/rcs-agent-onboarding
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

<!--
Verified against Sent sources:
- https://docs.sent.dm/start/quickstart/channel-setup
- https://docs.sent.dm/start/quickstart/first-message
- https://docs.sent.dm/start/quickstart/dashboard-walkthrough
- Sent v3 OpenAPI: POST /v3/messages, GET /v3/messages/{id}, GET /v3/messages/{id}/activities, /v3/profiles, /v3/profiles/{profileId}/complete

Review notes:
- Sent docs say RCS setup is not self-service, requires one-time carrier approval, and should be initiated by contacting Sent.
- Sent docs verify automatic SMS fallback when RCS is unavailable and explicit fallback/broadcast using channel arrays such as ["rcs", "sms"].
- Treat Google RBM launch states, capability endpoints, and per-carrier rollout fields as external platform context unless Sent exposes them in the customer’s account or docs.
-->

# RCS agent onboarding

## Overview

Use this skill to prepare a Sent customer for RCS launch without inventing a self-service provisioning flow. Sent’s public channel setup guidance says RCS setup is initiated through Sent, requires one-time carrier approval, and is not self-service. The agent’s job is to collect clean launch evidence, design fallback behavior, confirm profile/channel readiness, and create a verification plan for the first production sends.

RCS onboarding touches three separate layers. Sent owns the unified messaging API and fallback behavior. Google RBM and carriers own brand/agent review and launch approval. The customer owns brand assets, use-case clarity, consent, and support readiness. Keep those boundaries explicit.

## When to use

Use this skill when the request mentions RCS, RBM, RCS agent, carrier launch, branded messaging, rich card, carousel, SMS fallback from RCS, or RCS approval. Use it for launch preparation, evidence gathering, fallback decisions, and post-launch smoke tests.

Do not use this skill for live delivery-rate analysis after launch; use `messaging-performance-analyzer`. Do not use it to register US SMS compliance; use `sms-10dlc-registration`. Do not promise direct Graph/RBM API provisioning unless the user confirms they operate the external RBM account outside Sent.

## Source-of-truth boundaries

| Topic | Treat as | Action |
|---|---|---|
| Sent API sending | Sent API fact | Use `POST /v3/messages` with templates and channel arrays. |
| RCS setup path | Sent documentation fact | Tell the user RCS setup is initiated by contacting Sent and requires approval. |
| SMS fallback | Sent documentation fact | Use Sent’s fallback behavior and explicit `channel: ["rcs", "sms"]` where appropriate. |
| Google RBM agent fields | External platform context | Collect assets and evidence, but do not claim Sent exposes those fields. |
| Per-carrier launch states | External platform context | Track approval evidence from Sent/Google/carriers; do not invent Sent status fields. |
| Rich-card rendering | Runtime evidence | Verify with test sends and message activities after setup is active. |

## Process

### 1. Classify the requested launch

Start by asking what the RCS agent will do, who receives the messages, and whether SMS fallback is required. The use case should be concrete enough for carrier review and template design.

A good launch statement names the brand, audience, consent source, message types, support contact, and fallback behavior. A weak launch statement says only “we want RCS for marketing” or “we need branded SMS.”

**Example.** “Acme Logistics wants RCS order updates for US consumers who opted in at checkout. Messages include shipment confirmation, delivery window changes, and support links. If RCS is unavailable, send the SMS version through the same Sent profile.”

### 2. Build the RCS evidence packet

Collect review-ready evidence before involving Sent. This reduces approval loops and prevents the agent from submitting vague brand claims.

| Evidence | What to collect | Why it matters |
|---|---|---|
| Brand identity | Legal name, public brand name, website, logo, brand color, description | Reviewers compare the agent identity to the live business. |
| Contact and support | Support email, support phone, help URL, privacy policy | RCS users need visible ways to identify and contact the sender. |
| Use case | Transactional, OTP, marketing, customer care, or mixed use | Approval and fallback design depend on intent and consent. |
| Consent | Opt-in path, screenshot/URL, privacy policy, opt-out wording | Carriers need proof that recipients expect the messages. |
| Message examples | Representative plain-text and rich examples | Rich content must match the declared use case and brand. |
| SMS fallback | Equivalent SMS copy and approved SMS sender/compliance status | Fallback fails if SMS compliance is not ready. |

### 3. Check Sent profile and SMS fallback readiness

Confirm that the customer has a Sender Profile in the Sent dashboard or through `/v3/profiles`. The dashboard walkthrough shows Sender Profiles with a display name, brand description, `x-sender-id`, and SMS/WhatsApp configuration status. The OpenAPI confirms profile creation, retrieval, update, and completion endpoints.

If the launch requires US SMS fallback, verify that the SMS side is compliant before RCS goes live. Sent’s channel setup guide recommends using the same phone number across SMS, WhatsApp, and RCS where possible, but fallback must still have a valid SMS route and compliance posture.

**Example fallback request.** After Sent confirms RCS is configured, a customer can request an RCS-first send with SMS fallback/broadcast semantics using a channel array such as:

```json
{
  "to": ["+15551234567"],
  "channel": ["rcs", "sms"],
  "template": { "id": "template_uuid" }
}
```

Explain that Sent may create separate messages for each recipient/channel pair when multiple channels are specified. Analyze RCS and SMS attempts separately after sending.

### 4. Route the launch through Sent

Because Sent states that production RCS setup is not self-service, prepare a handoff note for Sent rather than pretending to click through an RBM console. Include the evidence packet, the Sender Profile identifier, the target countries/carriers if known, fallback requirements, and the requested go-live timeline.

A clean handoff reads like this:

> “Please initiate RCS setup for Sender Profile `support-us` / `x-sender-id` `...`. Brand is Acme Logistics, website `https://acme.example`, use case shipment notifications and customer-care replies. Opt-in occurs at checkout. SMS fallback is required through the existing US SMS route. Attached are logo, brand color, support contacts, privacy policy, and five message examples.”

### 5. Define the test plan before launch

Write the first-send test plan before approval arrives. Include a small set of internal numbers, target devices/carriers when available, template IDs, expected channel behavior, and rollback criteria.

| Test | Expected result | Evidence to collect |
|---|---|---|
| RCS-capable internal device | RCS message reaches `DELIVERED`; `READ` may appear if opened. | Sent message status and activities. |
| Non-RCS-capable recipient | SMS fallback path succeeds where fallback is requested. | Separate RCS and SMS message IDs/statuses. |
| Rich content render | Cards/buttons render as designed on target devices. | Screenshots and message activities. |
| Webhook callback | Customer endpoint receives delivery/read events. | Sent webhook event history and customer logs. |

### 6. Verify launch with Sent message evidence

After Sent confirms the RCS setup is active, send a controlled batch using `POST /v3/messages`. For every Sent `message_id`, retrieve `GET /v3/messages/{id}` and `GET /v3/messages/{id}/activities`. Confirm that RCS messages progress through the documented lifecycle and that SMS fallback behaves as expected.

If the first batch fails, do not guess. Separate setup failures from fallback failures, template/payload failures, and webhook ingestion failures. Use `messaging-performance-analyzer` for deeper funnel analysis once the launch is producing enough evidence.

## Common rationalizations to avoid

Do not tell the user RCS is self-service in Sent. Sent’s channel setup guide says to contact Sent and wait for carrier approval.

Do not create a fake `fallback_policy` field in Sent requests. Use documented channel arrays and account-level fallback behavior unless a verified account-specific API field exists.

Do not assume SMS fallback is safe because RCS is approved. SMS fallback needs a compliant sender, especially for US A2P traffic.

Do not conflate brand approval with template quality. An approved RCS agent can still fail if the message payload, media, or fallback copy is wrong.

## Verification checklist

- [ ] The user’s RCS use case is specific enough for review and not just “send rich messages.”
- [ ] Brand identity, support contact, privacy policy, opt-in evidence, and sample messages are collected.
- [ ] The Sent Sender Profile or `x-sender-id` is identified.
- [ ] SMS fallback requirements are documented and routed to SMS compliance checks where needed.
- [ ] The handoff explicitly says Sent must initiate RCS setup and carrier approval.
- [ ] The first-send test plan includes RCS-capable, non-RCS-capable, rich-rendering, and webhook checks.
- [ ] Post-launch verification uses Sent `message_id`, status, and activities.
- [ ] External RBM facts are labeled as external context, not Sent API guarantees.

## Related skills

Use `sms-10dlc-registration` before launch when SMS fallback touches US A2P traffic, opt-in evidence, 10DLC campaigns, or brand vetting.

Use `sender-profile-architect` when the customer has multiple brands, tenants, departments, or profiles and needs a durable sender architecture.

Use `template-builder-ui` when the RCS launch needs reusable templates, rich component validation, or a template-creation workflow.

Use `messaging-performance-analyzer` after launch when the user has message IDs, webhook events, failed sends, or delivery-rate symptoms.

Use the `sent` skill for shared Sent terminology and routing.

## Suggested bundled references and scripts

| File | Type | Purpose |
|---|---|---|
| `references/rbm-agent-spec.md` | Payload/schema reference | Keep Google RBM identity fields, asset requirements, and review vocabulary outside the skill body. |
| `references/rcs-launch-evidence-packet.md` | Worked example | Provide a complete filled-in launch packet for a realistic transactional RCS launch. |
| `references/rcs-fallback-patterns.md` | Decision matrix | Compare RCS-only, RCS-first with SMS fallback, and multi-channel broadcast patterns. |

## Unverified claims to confirm or remove

- Google RBM lifecycle states such as `pending_verification`, `launch_review`, or per-carrier launched states were not verified in Sent docs (these are Google-side, not exposed by Sent v3).
- Sent does not expose RCS rollout-status or capability-check endpoints in v3; use Activities + webhook events to observe behavior.
- Exact rich-card capability differences by carrier/device require external RBM evidence or live testing, not Sent docs alone.
