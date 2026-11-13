# RCS Launch Evidence Packet — Reference

Supporting reference for `rcs-agent-onboarding`. Describes the evidence Sent needs from a customer before initiating the RCS handoff to Google + the carriers. Sent's docs say RCS setup is not self-service and must be requested through `support@sent.dm`; the packet is what makes that email actionable.

The carrier-side launch review is external — authoritative source is [Google's RBM launch documentation](https://developers.google.com/business-communications/rcs-business-messaging/guides/learn/launch). This doc only covers what Sent itself collects, and how that overlaps with the broader KYC/compliance form the customer already fills in.

## Why a packet

The dashboard handoff to `support@sent.dm` is the single biggest lever a customer has on launch latency. A complete packet means Sent's team can take it to the carriers without round-tripping the customer for missing material. A vague packet means the agent sits idle for weeks.

## Overlap with the existing compliance form (verified)

The Sent dashboard already collects most of the brand-identity and use-case evidence as part of KYC and the compliance form. Reuse those answers — don't ask the customer to write everything from scratch.

Fields the dashboard's compliance form already captures (per Sent's docs):

**Business identity**
- Legal business name
- Business registration number
- Business type / structure
- Industry category
- EIN / tax ID (US)
- Business address
- Business phone number
- Contact email

**Messaging / use-case**
- Use-case selection (Authentication, Notifications, Marketing, Customer Service, High Volume)
- Campaign description
- Sample messages per use case
- Opt-in mechanism (URL or description)
- Opt-out language

For an RCS launch, these answers map directly into what the carriers want to see. If they're already complete and current, the RCS packet is mostly assembly, not authoring.

## RCS-specific evidence (additive to compliance form)

The bits below are required for RCS review but are **not** part of Sent's general compliance form — the customer has to supply them specifically for the RCS handoff.

### 1. Brand authorization

- Letter of authorization (LOA) signed by an officer of the brand confirming the customer is authorized to operate this RCS Agent
- For franchises / resellers: documentation of the licensing arrangement

### 2. Sample message gallery for RCS

For every Sent-side RCS component the agent will use, include at least one realistic sample showing it in use:

- Plain text body
- Suggestion Chip — quick reply
- Suggestion Chip — open URL
- Suggestion Chip — dial number
- Rich Card (with media, title, description, chip)
- Carousel Card (up to 10 Rich Cards)
- Any attachment type the agent will send (image, video, file)

Samples must use real brand assets (logo, color, copy voice). Placeholders are a common rejection reason.

### 3. Brand assets

- Square logo (RBM has minimum dimensions; check [Google's agent docs](https://developers.google.com/business-communications/rcs-business-messaging/reference/business-communications/rest/v1/brands.agents))
- Brand color (hex)
- Optional hero/banner image
- Public website URL (must match the brand the agent represents)

### 4. SMS fallback plan

A one-paragraph statement of what happens when the recipient isn't RCS-capable. Sent's documented fallback mechanism is the `channel` array on the send request — see `references/rcs-fallback-patterns.md` for the option set. If the customer needs US SMS as fallback, confirm 10DLC compliance is already in place (see `sms-10dlc-registration`).

### 5. End-user support contact

A phone number, email, or in-product support URL recipients can reach with questions. Google and carriers both probe this contact during review, so it has to actually answer.

## Pre-handoff checklist

Before emailing `support@sent.dm`, confirm:

- [ ] Compliance form is complete and current in the Sent dashboard
- [ ] Use-case selection on the form matches the RCS Agent's intended use
- [ ] Sample messages on the form cover the RCS use case (not just SMS)
- [ ] Opt-in mechanism (URL or description) is filled in and accurate
- [ ] Opt-out language is documented
- [ ] LOA signed and dated within last 12 months
- [ ] At least one sample per RCS component the agent will use, with real brand assets
- [ ] Brand logo, color, website URL ready to attach
- [ ] SMS fallback plan written down, with channel-array shape (e.g. `["rcs", "sms"]`)
- [ ] If US SMS is the fallback, 10DLC registration already complete
- [ ] Support contact is live and answers within stated SLA
- [ ] Every URL that will appear in a sample message resolves on the brand's public domain

## Per-carrier nuance (external)

Each carrier reviews independently after Google approves. The specifics shift over time and are not documented in Sent's v3 docs — treat carrier-specific copy requirements, opt-in language minimums, and throttling windows as external. Always check [Google's per-carrier guidance](https://developers.google.com/business-communications/rcs-business-messaging/guides/learn/launch) for the current rules.

Patterns that broadly hold:
- Marketing use cases get scrutinized harder than transactional / OTP.
- Carriers may require additional opt-in disclosure language beyond Google's.
- Even after `ENABLED`, carriers may stage rollout by recipient volume in the first weeks.

## Common rejection reasons (Google-side, external)

These come from Google and the carriers, not Sent. Listed here as a checklist, not a substitute for the [official guidance](https://developers.google.com/business-communications/rcs-business-messaging/guides/learn/launch).

| Reason | Remediation |
|---|---|
| Brand assets in sample don't match the agent identity | Re-render samples with the actual logo, color, brand name |
| Use case description and declared use case disagree | Either change the declared use case or rewrite the description; resubmit |
| Opt-in disclosure missing channel name | Update the opt-in surface to name RCS (or "text messages including RCS") and re-screenshot |
| Sample exercises a capability not declared on the agent | Either declare the capability or remove the sample |
| Support contact unreachable | Wire up the contact and confirm before resubmitting |
| Same packet recycled across multiple agents with different brands | Each agent needs its own packet — Google catches this |

## After submission

- Sent does not expose a per-carrier rollout-status endpoint in v3. To observe RCS behavior after launch, use `GET /v3/messages/{id}`, `GET /v3/messages/{id}/activities`, and the webhook events listed in `references/rcs-fallback-patterns.md`.
- A carrier coming back with changes requested will produce a short reason — feed that back to the customer and update the relevant packet artifact before resubmitting.
- Some carriers stay pending for weeks even after Google approves; that's an external timeline, not a Sent issue.
