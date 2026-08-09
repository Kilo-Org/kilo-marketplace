---
name: waba-embedded-signup
description: >-
  Guides WhatsApp Business Account connection for Sent Sender Profiles,
  including Embedded Signup planning, WABA and phone-number mapping,
  token/security handling, webhook readiness, and profile completion. Use when a
  user says Embedded Signup, WABA, connect WhatsApp, WhatsApp sender, phone
  number ID, Facebook Login for Business, Meta Business, sender profile WhatsApp
  setup, or webhooks not firing after WhatsApp signup.
metadata:
  category: development
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/waba-embedded-signup
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

<!--
Verified against Sent sources:
- https://docs.sent.dm/start/quickstart/dashboard-walkthrough
- https://docs.sent.dm/start/quickstart/channel-setup
- https://docs.sent.dm/reference/api
- Sent v3 OpenAPI: /v3/profiles, /v3/profiles/{profileId}, /v3/profiles/{profileId}/complete, /v3/webhooks, /v3/webhooks/{id}/test, /v3/webhooks/{id}/rotate-secret

Review notes:
- Sent docs verify Sender Profiles and WhatsApp configuration status in the dashboard, but the extracted Sent docs/API did not expose a public Sent-specific Embedded Signup endpoint.
- Treat Meta Graph API calls, Facebook Login for Business configuration, system-user tokens, WABA subscription, and phone-number registration as external Meta implementation details unless Sent confirms they are required for the integration path.
- Anchor Sent-side completion to Sender Profile configuration and /v3/profiles/{profileId}/complete.
-->

# WABA Embedded Signup

## Overview

Use this skill to connect a WhatsApp Business Account (WABA) and phone number to a Sent Sender Profile without confusing Sent-side setup with Meta-side implementation details. Sent’s dashboard exposes Sender Profiles and WhatsApp configuration status. Sent’s profile API exposes profile CRUD and a profile-completion workflow. The public Sent sources reviewed for this rewrite did not expose a dedicated Embedded Signup endpoint, so direct Meta Graph flows should be treated as external integration context unless the user confirms that their application owns that flow.

The safest workflow is to decide the integration path first: Sent-managed WhatsApp setup, customer-managed Meta Embedded Signup connected back to Sent, or a hybrid implementation coordinated with Sent.

## When to use

Use this skill when the user mentions Embedded Signup, WABA, WhatsApp Business Account, WhatsApp phone number, phone number ID, Facebook Login for Business, Meta Business Manager, connecting WhatsApp to Sent, WhatsApp sender setup, Sender Profile WhatsApp status, or webhook delivery after WhatsApp onboarding.

Do not use this skill to author WhatsApp templates; use `waba-template-author`. Do not use it to build a generic Meta app unless the user explicitly asks for a Meta-side implementation. Do not claim Sent exposes Embedded Signup endpoints unless the account/docs confirm them.

## Process

### 1. Decide the integration path first

Start every session by asking which path applies. The answer changes what the agent should do next.

| Path | Use when | Agent role |
|---|---|---|
| Sent-managed setup | The customer wants Sent to guide or operate WhatsApp connection. | Prepare Sender Profile, business evidence, phone-number details, and handoff notes. |
| Customer-managed Embedded Signup | The customer’s app launches Meta Embedded Signup and passes results to Sent. | Review Meta-side security and mapping, then align results to Sent profile completion. |
| Migration/import | The customer already has a WABA/phone number and needs it represented in Sent. | Collect WABA/phone identifiers, ownership evidence, and profile mapping. |

If the user cannot answer, default to Sent-managed setup and avoid prescribing Graph API calls.

### 2. Identify the Sender Profile

Locate or create the Sender Profile that will own the WhatsApp sender identity. Use the Sent dashboard or `/v3/profiles`. Record the Sent profile ID, `x-sender-id` if visible, display name, brand description, and intended WhatsApp phone number.

A WhatsApp number should map to the same recipient-visible brand represented by the profile. If the number belongs to a different brand, department, or tenant, use `sender-profile-architect` before proceeding.

### 3. Collect WhatsApp onboarding evidence

Collect the minimum evidence needed for Sent or Meta review.

| Evidence | Why it matters |
|---|---|
| Business legal name and Meta Business identity | Confirms the WABA belongs to the intended sender. |
| Public website and privacy policy | Supports business verification and template review. |
| Phone number and ownership/control evidence | Prevents connecting the wrong sender. |
| Display name | Must match the business identity recipients expect. |
| Use cases and example messages | Drives template authoring and policy review. |
| Webhook endpoint and owner | Needed to verify event delivery after connection. |

### 4. Map external identifiers without making them the Sent contract

If the user provides WABA ID, phone-number ID, Meta Business ID, or System User details, store them as external provider identifiers mapped to the Sent profile. Do not make those IDs the primary application sender key. Use Sent profile ID and Sent message IDs for Sent operations.

**Example mapping.**

```text
sent_profile_id: 2b1b...
x_sender_id: support_us
channel: whatsapp
provider: meta
provider_business_id: external value, if available
provider_waba_id: external value, if available
provider_phone_number_id: external value, if available
status_source: Sent dashboard/API or Meta integration logs
```

### 5. Complete or re-check the Sent profile

Use `/v3/profiles/{profileId}/complete` when prerequisites are ready and API completion is in scope. The OpenAPI describes profile completion as a background process that validates prerequisites and connects profile configuration. If completion returns missing prerequisites, fix those inputs rather than creating duplicate profiles.

### 6. Verify webhook readiness

Use Sent webhook endpoints to confirm event delivery. Verify the webhook exists, the relevant event types are available, and a test event reaches the customer endpoint via `POST /v3/webhooks/{id}/test`.

Rotate webhook secrets only when needed and coordinate deployment, because secret rotation invalidates the old secret immediately.

## Meta-side implementation review

Use this section only when the user confirms that their application owns Embedded Signup. Label the work as Meta-side. Validate security, mapping, and callback handling before connecting results to Sent.

| Area | Check |
|---|---|
| Launch context | Embedded Signup is launched from the right app, business, and allowed origin. |
| Callback handling | The app captures the signup result, not just a UI success state. |
| Token exchange | Authorization codes/tokens are exchanged server-side, never in public frontend storage. |
| Scope verification | Returned permissions/granular scopes match the required WABA and phone-number access. |
| Identifier lookup | WABA ID and phone-number ID are read back and mapped to the Sent profile. |
| Phone registration | Registration is completed only if the integration path requires the customer app to do it. |
| App subscription | Webhook subscription is completed only if the integration path requires direct Meta callbacks. |
| Secret handling | Tokens and webhook secrets are encrypted, rotated, and not logged. |

Do not assume the customer app must call every Meta endpoint. Sent may abstract parts of onboarding depending on the customer’s setup.

## Troubleshooting patterns

| Symptom | First check | Likely next step |
|---|---|---|
| Sender Profile still shows WhatsApp not configured | Sent profile prerequisites and completion status | Confirm whether Sent-managed setup or external Embedded Signup results were expected. |
| User completed Meta flow but Sent cannot send | Mapping between external phone/WABA and Sent profile | Provide identifiers/evidence to Sent or update integration mapping. |
| Templates remain unavailable | Template status and WhatsApp business review | Use `waba-template-author` and Sent template status. |
| Webhooks not firing | Sent webhook test and event history | Fix endpoint/subscription before blaming WhatsApp delivery. |
| Wrong tenant receives events | Profile/message ID mapping | Use `sender-profile-architect` to redesign routing. |

## Common rationalizations to avoid

Do not treat a Meta UI success screen as proof that Sent can send WhatsApp messages. Verify Sent profile/channel status and test sends.

Do not store access tokens in browser storage or logs. Treat Meta tokens and Sent webhook secrets as production credentials.

Do not assume a WABA can be reused across unrelated brands or tenants. Recipient-visible identity and operational ownership matter.

Do not hardcode Graph API version, scope names, or endpoint sequences in this skill body. Keep those in a reference file and re-check Meta docs or Sent implementation guidance before use.

Do not rotate Sent webhook secrets without coordinating the receiving endpoint.

## Verification checklist

- [ ] The integration path is identified as Sent-managed, customer-managed Embedded Signup, or migration/import.
- [ ] The correct Sent Sender Profile is identified before external identifiers are mapped.
- [ ] WhatsApp business identity, phone-number evidence, display name, and use cases are collected.
- [ ] WABA/phone-number IDs are stored as external identifiers, not as the primary Sent sender key.
- [ ] Profile completion is run or checked after prerequisites are ready.
- [ ] Sent webhook existence, event types, event history, and test delivery are verified.
- [ ] Meta Graph steps are only prescribed when the user confirms direct ownership of Embedded Signup.
- [ ] Tokens, webhook secrets, and callback data are handled server-side and securely.

## Related skills

Use `sender-profile-architect` when deciding whether a WABA or phone number belongs in a separate Sender Profile.

Use `waba-template-author` when the WhatsApp sender needs templates written, categorized, submitted, or revised.

Use `template-builder-ui` when building the UI that imports or manages WhatsApp templates inside Sent.

Use `messaging-performance-analyzer` when WhatsApp sends are connected but delivery/read/webhook outcomes are poor.

Use the `sent` skill for shared Sent terminology and routing.

## Suggested bundled references and scripts

| File | Type | Purpose |
|---|---|---|
| `references/waba-embedded-signup-spec.md` | External platform reference | Keep Meta launch, token exchange, WABA lookup, phone registration, and subscription details out of the skill body. |
| `references/whatsapp-sender-profile-mapping.md` | Schema reference | Define how Sent profile IDs map to WABA IDs, phone-number IDs, display names, and status evidence. |
| `references/waba-onboarding-runbook.md` | Worked example | Show Sent-managed and customer-managed onboarding examples end-to-end. |

## Unverified claims to confirm or remove

- Sent does not expose a public Embedded Signup endpoint; WhatsApp connection is dashboard-only via Channels → WhatsApp (confirmed against Sent v3 docs snapshot, 2026-05-19; the Channels page is explicitly listed as "dashboard config; not directly in v3 API").
- Required Meta app type, Tech Provider/Solution Partner status, granular scopes, and Graph endpoint sequence are external Meta claims, not Sent API facts.
- Mandatory direct phone-number registration or WABA subscription by the customer app depends on integration path and was not verified as a universal Sent requirement.
- Sent's webhook envelope is confirmed as `{field, sub_type, timestamp, payload}` with sub-types of the form `<field>.<event>` (e.g., `message.delivered`). WhatsApp-specific sub-types are not enumerated in the snapshot — discover them empirically against your account.
