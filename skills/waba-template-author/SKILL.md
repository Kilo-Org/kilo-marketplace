---
name: waba-template-author
description: >-
  Writes, classifies, and revises WhatsApp templates for Sent, including
  utility, marketing, and authentication category decisions, variable samples,
  component structure, rejection-risk review, and Sent template submission. Use
  when a user says WhatsApp template, WABA template, template category, utility
  vs marketing, authentication template, Meta rejection, template samples,
  buttons, or wants approved WhatsApp copy in Sent.
metadata:
  category: business
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/waba-template-author
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

<!--
Verified against Sent sources:
- https://docs.sent.dm/docs/docs/03-quickstart/first-template
- https://docs.sent.dm/start/quickstart/first-message
- https://docs.sent.dm/reference/api
- Sent v3 OpenAPI: POST /v3/templates, GET /v3/templates, GET /v3/templates/{id}, PUT /v3/templates/{id}, DELETE /v3/templates/{id}, POST /v3/messages

Review notes:
- Sent docs define templates across SMS, WhatsApp, and RCS, and state that WhatsApp templates require Meta approval.
- Sent's surfaced template statuses are `APPROVED`, `PENDING`, `REJECTED` (snapshot Template Models section).
- Sent's three template categories are `UTILITY`, `MARKETING`, `AUTHENTICATION` — no others.
- Treat WhatsApp category rules, rejection reasons, the Meta-only `PAUSED` state, and Cloud API payloads as Meta-side policy/context. Sent does not surface `PAUSED`.
-->

# WABA template author

## Overview

Use this skill to write WhatsApp template content that can be represented as a Sent template, submitted for WhatsApp review where required, and later sent through `POST /v3/messages` with `template.id`. The skill’s job is not just to produce polished copy; it must choose the right category, structure components correctly, provide realistic sample values, and flag review risks before submission.

Sent stores templates as reusable message blueprints across SMS, WhatsApp, and RCS. WhatsApp review and category enforcement come from Meta, but the Sent-facing workflow uses Sent’s `/v3/templates` endpoints and Sent template statuses.

## When to use

Use this skill when the user asks for WhatsApp template copy, WABA template creation, utility/marketing/authentication classification, template rejection fixes, variable samples, buttons, headers, template categories, Meta approval risk, or a Sent template payload for WhatsApp.

Do not use this skill to design the whole template-management UI; use `template-builder-ui`. Do not use it to connect a WABA or phone number; use `waba-embedded-signup`. Do not use it to register SMS compliance; use `sms-10dlc-registration`.

## Category decision

Pick the narrowest truthful WhatsApp category. Do not force promotional content into utility. The category should match the recipient’s expectation, the opt-in context, and the actual copy.

| Category | Use when | Avoid when |
|---|---|---|
| Utility | The message is tied to an existing transaction, account, order, appointment, or service request. | The copy includes upsell, acquisition, abandoned cart, discount, or broad engagement language. |
| Marketing | The message promotes, re-engages, cross-sells, announces offers, or encourages optional action not tied to an existing transaction. | The message is purely required service/account information. |
| Authentication | The message delivers one-time passcodes or verification flows. | The message includes non-authentication content or marketing. |

**Example.** “Your order 1234 shipped and arrives tomorrow” is utility. “Your order shipped — add accessories for 20% off” is marketing risk because it adds promotional content.

## Process

### 1. Capture the business intent

Ask what event triggers the template, who receives it, what action the recipient should take, and whether the message contains any promotion. Write those answers before drafting copy.

A strong intent statement is specific: “Send a delivery reschedule link after a courier misses the first attempt.” A weak one says: “Notify users about updates.”

### 2. Choose the category before writing copy

Drafting before category selection often creates copy that fails review. Choose utility, marketing, or authentication first, then write within that boundary.

If the user wants utility but includes promotional language, explain the conflict and offer two options: remove promotion and keep utility, or keep promotion and classify as marketing.

### 3. Draft the component structure

Represent the template in Sent-compatible component language: header, body, footer, buttons, variables, and samples. Keep the component set as simple as the use case allows.

| Component | Guidance |
|---|---|
| Header | Use only when it clarifies identity or context. Avoid promotional headers for utility templates. |
| Body | Put the required message and variables here. Keep the first sentence clear without needing the button. |
| Footer | Use for low-emphasis context such as opt-out or support where appropriate. |
| Buttons | Use quick replies or call-to-action buttons only when they directly support the message intent. |
| Variables | Use stable names and provide realistic samples for every variable. |

### 4. Write with review risk in mind

Use concise, literal copy. Avoid vague urgency, misleading scarcity, or mixed intents. Do not include sensitive data unless the use case requires it and the customer confirms it is acceptable.

**Utility example.**

```text
Name: order_shipped_update
Category: Utility
Language: en_US
Body: Hi {{first_name}}, your {{brand_name}} order {{order_id}} has shipped and is expected on {{delivery_date}}. Track it here: {{tracking_url}}.
Samples:
  first_name: Alex
  brand_name: Acme
  order_id: A12345
  delivery_date: May 22
  tracking_url: https://acme.example/t/A12345
Button: Track order -> {{tracking_url}}
```

**Marketing example.**

```text
Name: spring_sale_announcement
Category: Marketing
Language: en_US
Body: Hi {{first_name}}, {{brand_name}} spring deals are live. Use code {{promo_code}} by {{end_date}} to save on selected items.
Samples:
  first_name: Alex
  brand_name: Acme
  promo_code: SPRING20
  end_date: May 31
Button: Shop now -> https://acme.example/sale
```

### 5. Convert the draft into a Sent template operation

Use Sent’s template API for creation and lifecycle management. The verified operations are:

| Operation | Endpoint | Use |
|---|---|---|
| Create template | `POST /v3/templates` | Save a draft or submit a new template. |
| List templates | `GET /v3/templates` | Find templates by search, status, or category. |
| Retrieve template | `GET /v3/templates/{id}` | Inspect status and definition. |
| Update template | `PUT /v3/templates/{id}` | Revise name, category, language, definition, or submit for review. |
| Delete template | `DELETE /v3/templates/{id}` | Delete the Sent template, optionally deleting from Meta where supported. |

Use Sent’s documented template statuses in user-facing instructions: `PENDING`, `APPROVED`, `REJECTED` (per the Sent docs snapshot, Template Models section). Sent does **not** surface `PAUSED` — that is Meta-side only. If Meta returns additional statuses for a WhatsApp account, quote them as Meta-side evidence rather than Sent-surfaced statuses.

### 6. Add variable samples before submission

Every placeholder needs a realistic sample. Samples should look like production data and should not add claims that the body does not support.

**Bad sample pattern.** Body says “Your appointment is confirmed,” but sample data includes “50% off visit.” This can create category confusion.

**Good sample pattern.** Body and sample values all support the same transactional use case.

### 7. Revise rejected templates from the reason, not from guesses

If a template is rejected, retrieve the Sent template detail/status and any available rejection reason. Then change only what the reason justifies. Category mismatch, missing samples, unsupported components, and promotional language in utility templates require different fixes.

| Rejection symptom | Likely correction |
|---|---|
| Category mismatch | Change category or remove conflicting copy. |
| Missing/weak samples | Add realistic variable samples. |
| Unsupported component | Simplify header/buttons or split channel variants. |
| Policy concern | Remove misleading, sensitive, or prohibited content. |
| Language mismatch | Correct language code and localized text. |

### 8. Confirm sendability after approval

After approval, confirm the template can be used with the intended Sender Profile/channel and sent through `POST /v3/messages` with `template.id`. If delivery later fails, hand off to `messaging-performance-analyzer` rather than rewriting approved copy blindly.

## Common rationalizations to avoid

Do not call a template utility if it includes discounts, upsells, abandoned-cart messaging, or broad engagement language.

Do not omit sample values because the placeholders are obvious. Review and test flows need rendered examples.

Do not treat Meta Cloud API payload examples as the Sent API contract. Use Sent `/v3/templates` for Sent integrations.

Do not introduce `PAUSED` as a Sent template status. Sent surfaces only `APPROVED`, `PENDING`, and `REJECTED` — PAUSED is Meta-side and is not reflected in the Sent template status. When Meta pauses, the Sent status stays as it was, and individual sends start failing instead — diagnose via `messaging-performance-analyzer`.

Do not rewrite a rejected template without reading the actual rejection reason when available.

## Verification checklist

- [ ] The trigger event, audience, recipient action, and promotional content are documented.
- [ ] Category is chosen before copy is drafted.
- [ ] The body is clear without relying on a button.
- [ ] Every variable has a realistic sample value.
- [ ] Component choices match the selected channel and use case.
- [ ] Sent template API endpoints are used for create/list/get/update/delete.
- [ ] Status handling uses only Sent's surfaced set — `APPROVED`, `PENDING`, `REJECTED` (no `PAUSED`).
- [ ] Rejection fixes map to observed reasons, not generic rewrites.
- [ ] Approved templates are tested through Sent sending with `template.id` before broad rollout.

## Related skills

Use `template-builder-ui` when the task is UI design, component validation, JSON editor behavior, or template-management product specs.

Use `waba-embedded-signup` when the WhatsApp sender/WABA/phone number is not connected to Sent yet.

Use `sender-profile-architect` when the template belongs to a specific tenant, brand, department, or profile boundary.

Use `sms-10dlc-registration` when WhatsApp copy will be mirrored to SMS and must align with US A2P use-case registration.

Use `messaging-performance-analyzer` when approved WhatsApp templates have poor delivery, read, or webhook outcomes.

Use the `sent` skill for shared Sent terminology and routing.

## Bundled references and scripts

| File | Type | Purpose |
|---|---|---|
| `references/waba-template-categories.md` | Policy lookup table | Meta category boundaries, component rules, and Cloud API submission shape. |
| `references/waba-template-examples.md` | Worked examples | Copy-pasteable payloads for utility, marketing, and authentication templates. |
| `references/template-rejection-playbook.md` | Decision matrix | Map rejection reasons to precise edits and resubmission etiquette. |
| `scripts/lint_waba_template.py` | Validation script | Stdlib lint for a template JSON payload (placeholder numbering, samples, category-risk phrases, button structure, language code). Run from the skill root: `python scripts/lint_waba_template.py template.json`. |
| `scripts/fixtures/utility_good.json` | Fixture | Passing fixture for the linter. |
| `scripts/fixtures/utility_bad.json` | Fixture | Failing fixture (wrong placeholder order, promo phrasing in utility). |

## Unverified claims to confirm or remove

- Exact category-pricing behavior and Meta rejection-code semantics are external Meta policy context, not Sent API facts.
- Cross-check the Sent template schema against the live OpenAPI at `https://docs.sent.dm` before promoting code to production.
