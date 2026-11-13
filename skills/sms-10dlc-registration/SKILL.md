---
name: sms-10dlc-registration
description: >-
  Prepares Sent US A2P SMS 10DLC compliance by collecting business, opt-in,
  brand, campaign, sample-message, and profile-completion evidence. Use when a
  user says 10DLC, A2P, TCR, campaign registry, brand vetting, SMS compliance,
  US texting, long code registration, opt-in proof, opt-out language, carrier
  filtering, or needs to register SMS through Sent.
metadata:
  category: business
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/sms-10dlc-registration
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

<!--
Verified against Sent sources:
- https://docs.sent.dm/troubleshooting/compliance
- https://docs.sent.dm/start/quickstart/channel-setup
- https://docs.sent.dm/start/quickstart/dashboard-walkthrough
- Sent v3 OpenAPI: /v3/brands, /v3/brands/{brandId}, /v3/brands/{brandId}/campaigns, /v3/brands/{brandId}/campaigns/{campaignId}, /v3/profiles/{profileId}/complete

Review notes:
- Sent docs verify that US SMS A2P messaging requires 10DLC registration and that Sent handles TCR registration as part of the compliance process.
- Sent docs list required compliance-form inputs: legal business name, business address, EIN/tax ID, live website, privacy policy, opt-in mechanism URL, use-case description, sample messages, and opt-out instructions.
- Treat exact carrier throughput, vetting-score impact, and TCR taxonomy details as external/compliance reference material unless Sent compliance data confirms them for the account.
-->

# SMS 10DLC registration

## Overview

Use this skill to prepare US A2P SMS compliance for Sent. Sent’s compliance documentation states that compliance is a prerequisite for sending messages and that 10DLC registration is mandatory for A2P messaging to US numbers. Sent handles TCR registration as part of the compliance process, while the customer must provide accurate business identity, consent, use-case, sample-message, and opt-out evidence.

The Sent v3 API exposes Sent-facing brand and campaign resources through `/v3/brands` and `/v3/brands/{brandId}/campaigns`. Profile completion through `/v3/profiles/{profileId}/complete` validates profile, brand, and campaign prerequisites before the profile is ready.

## When to use

Use this skill when the request mentions 10DLC, A2P, TCR, brand registration, campaign registration, SMS compliance, US long code, EIN, opt-in proof, sample messages, opt-out, HELP/STOP language, vetting, rejected campaign, or carrier filtering caused by compliance. Use it before enabling US SMS sending or SMS fallback for RCS.

Do not use this skill for non-US country compliance unless the user supplies a Sent compliance source for that country. Do not use it to analyze live delivery failures except to identify whether compliance status is the likely next check.

## Required evidence

Collect evidence before creating or updating Sent brand/campaign resources. Bad evidence creates review loops and downstream filtering risk.

| Evidence | What to capture | Sent-grounded reason |
|---|---|---|
| Legal business identity | Legal business name, address, EIN/tax ID, entity type | Sent’s compliance guide lists these as required inputs. |
| Public web presence | Live website URL and privacy policy URL | Sent requires a live website and privacy policy for compliance review. |
| Opt-in mechanism | URL, screenshot, form text, checkbox language, or checkout flow | Sent requires an opt-in mechanism URL. |
| Use-case description | Clear description of what messages are sent and why | Sent requires use-case description. |
| Sample messages | Realistic messages matching the declared use case | Sent requires sample messages. |
| Opt-out instructions | STOP/HELP or equivalent instructions where applicable | Sent requires opt-out instructions. |
| Sender Profile | Sent profile ID or dashboard profile being completed | Profile completion validates compliance prerequisites. |

## Process

### 1. Decide whether this is US A2P SMS

Confirm destination country, traffic type, and sender type. This skill applies to US A2P SMS over 10DLC. If the user is sending only WhatsApp, RCS without SMS fallback, short code, toll-free, or non-US traffic, document the difference and route to the appropriate compliance workflow.

**Example.** “We send appointment reminders from a SaaS platform to US patients using local long-code numbers” is US A2P SMS and needs 10DLC. “We send only WhatsApp utility templates” is not a 10DLC workflow, though WhatsApp has its own template and business requirements.

### 2. Normalize the business identity

Use the exact legal business name and tax ID records. Do not “clean up” the name to a marketing brand if the tax record uses another legal entity. Mismatches between legal identity, website, and opt-in flow are common rejection causes.

If the customer is an ISV registering many customers, decide whether each customer needs its own profile/brand/campaign boundary with `sender-profile-architect`. Do not put unrelated customers under one brand because it is faster.

### 3. Classify the campaign by use case

Pick the narrowest truthful campaign use case. Mixed-use campaigns can be valid, but they invite broader review and more filtering risk if the sample messages do not match the declared intent.

| Declared intent | Better sample | Bad sample |
|---|---|---|
| Account notification | “Acme: Your password was changed. If this was not you, visit https://acme.example/security. Reply STOP to opt out.” | “Huge sale today. Click now.” |
| Delivery notification | “Acme: Order 1234 is out for delivery today. Track: https://acme.example/t/1234. Reply STOP to opt out.” | “Your package is coming. Also buy these add-ons.” |
| Customer care | “Acme Support: We received your request and will respond shortly. Reply STOP to opt out.” | “Thanks for contacting us. Get 20% off now.” |
| Marketing | “Acme: Spring sale starts today. Use code SPRING. Reply STOP to opt out.” | Transactional description with promotional samples. |

Keep detailed TCR taxonomy and carrier-specific advice in a reference file. In the skill body, use only enough taxonomy to keep the submission honest.

### 4. Create or update Sent brand resources

Use Sent’s brand endpoints when API work is in scope. The verified v3 API includes:

| Operation | Endpoint | Notes |
|---|---|---|
| Create brand | `POST /v3/brands` | Creates a new brand and associated information. |
| List brands | `GET /v3/brands` | Retrieves brands for the authenticated customer, including inherited brands where applicable. |
| Update brand | `PUT /v3/brands/{brandId}` | Cannot update brands already submitted to TCR or inherited brands. |
| Delete brand | `DELETE /v3/brands/{brandId}` | Deletes a brand that belongs to the authenticated customer. |

Use optional `Idempotency-Key` headers on create/update calls when retrying. Store the Sent brand ID returned by the API. Store any returned TCR identifiers separately only if the API response exposes them.

### 5. Create or update Sent campaign resources

Create campaigns under the relevant Sent brand. The verified v3 API says each campaign must include at least one use case with sample messages.

| Operation | Endpoint | Notes |
|---|---|---|
| Create campaign | `POST /v3/brands/{brandId}/campaigns` | Links the campaign to the brand and requires use-case/sample-message data. |
| List campaigns | `GET /v3/brands/{brandId}/campaigns` | Retrieves campaigns and their use cases/sample messages. |
| Update campaign | `PUT /v3/brands/{brandId}/campaigns/{campaignId}` | Cannot update campaigns already submitted to TCR. |
| Delete campaign | `DELETE /v3/brands/{brandId}/campaigns/{campaignId}` | Deletes a campaign within the brand. |

Do not claim a public `tcr_campaign_id` field unless the actual response includes it. Refer to the Sent campaign ID for Sent API operations.

### 6. Complete the Sender Profile setup

After profile data, brand, and campaign prerequisites are ready, call or trigger profile completion through `POST /v3/profiles/{profileId}/complete`. The OpenAPI describes this as the final step in the profile compliance workflow, validating prerequisites and connecting profile configuration in the background.

If completion fails, fix the missing prerequisite rather than creating duplicate brands or campaigns. Duplicate compliance objects increase confusion and can lead to sending from the wrong profile.

### 7. Prepare the review-ready submission summary

End the workflow with a compact summary the user can paste into Sent support, a dashboard form, or an internal ticket. Include legal identity, website, privacy policy, opt-in URL/evidence, use-case description, sample messages, opt-out instructions, Sent profile ID, Sent brand ID, Sent campaign ID, and any unresolved questions.

**Example summary.**

> “Acme Logistics LLC, EIN ending 1234, sends US SMS delivery notifications to customers who opt in at checkout. Website and privacy policy are live. Opt-in screenshot and URL are attached. Campaign use case is delivery notification. Sample messages match shipment status only and include opt-out instructions. Sent profile `...`, Sent brand `...`, Sent campaign `...` are ready for completion.”

## Common rationalizations to avoid

Do not register a marketing campaign as a utility or account-notification campaign because it may be cheaper or easier. The samples, opt-in flow, and actual traffic must match.

Do not submit placeholder websites, private staging URLs, or missing privacy policies. Sent’s compliance guide calls for live URLs.

Do not reuse one brand/campaign for unrelated customers. Compliance belongs to the sender and use case, not just the platform sending the API call.

Do not edit a submitted brand or campaign in place if the API says submitted objects cannot be updated. Create the right correction path with Sent.

Do not promise exact approval times beyond Sent’s guidance. Sent says TCR registration typically completes within 3 to 7 business days after the Sent compliance form is approved, with additional propagation time possible.

## Verification checklist

- [ ] The traffic is confirmed as US A2P SMS over a long-code route.
- [ ] Legal business identity matches tax and website evidence.
- [ ] Website and privacy policy URLs are live.
- [ ] Opt-in evidence is concrete and matches the declared use case.
- [ ] Sample messages are realistic and match the use case.
- [ ] Opt-out instructions are included where applicable and consistent with the user experience.
- [ ] Sent brand and campaign IDs are stored separately from any provider/TCR identifiers.
- [ ] Profile completion is run only after profile, brand, and campaign prerequisites are ready.
- [ ] Unverified throughput, carrier, or pricing claims are not presented as Sent facts.

## Related skills

Use `sender-profile-architect` when deciding whether brands, tenants, departments, or use cases need separate Sender Profiles.

Use `rcs-agent-onboarding` when 10DLC work is needed for SMS fallback from RCS.

Use `messaging-performance-analyzer` when registered traffic still shows delivery failures or filtering symptoms.

Use `template-builder-ui` when the customer needs reusable SMS template copy that matches the registered use case.

Use the `sent` skill for shared Sent terminology and routing.

## Bundled references and scripts

| File | Type | Purpose |
|---|---|---|
| `references/tcr-use-cases.md` | Lookup table | TCR use-case taxonomy, sample-message patterns, and rejection reasons. |
| `references/10dlc-evidence-checklist.md` | Worked example | Field-by-field checklist for Sent's 10DLC compliance form. |
| `references/10dlc-rejection-remediation.md` | Decision matrix | Common TCR / carrier rejection codes mapped to fix steps and re-submission etiquette. |
| `scripts/validate_10dlc_packet.py` | Validation script | Pre-flight validator for a packet JSON. Run from the skill root: `python scripts/validate_10dlc_packet.py packet.json`. |
| `scripts/fixtures/good.json` | Fixture | Complete valid packet (passes validator). |
| `scripts/fixtures/bad.json` | Fixture | Packet with missing fields / invalid EIN / short sample (validator exits non-zero). |

## Unverified claims to confirm or remove

- Sent's `/v3/brands` and `/v3/brands/{id}/campaigns` endpoints exist; their internal mapping to TCR identifiers is opaque to the customer. Store the Sent brand and campaign IDs returned by the API — don't claim a public `tcr_brand_id` or `tcr_campaign_id` field unless an API response surfaces it.
- Exact throughput limits, per-carrier caps, and vetting-score-to-throughput mapping are not in Sent's docs. The snapshot only confirms account-wide tier limits (Starter 60 msg/min, Growth 300 msg/min, Enterprise custom) — these are not TCR / carrier per-campaign throughput numbers.
- Country-specific compliance, routing, and pricing claims beyond Sent's listed country-specific document requirements (AU, BE, PL, ZA, SE, TH, UK) require a current Sent source.
