---
name: template-builder-ui
description: >-
  Designs and audits a Sent template builder UI for cross-channel SMS, WhatsApp,
  and RCS templates, including component editing, variable samples, status
  handling, channel-specific validation, and submission workflows. Use when a
  user says template builder, template editor, Sent templates, WhatsApp template
  UI, RCS template, SMS template, Meta import, JSON template, approval status,
  or wants a product spec for template creation. Do not use for generic
  templating engines (Jinja, Handlebars, Mustache, email/HTML templates) or
  non-Sent template systems.
metadata:
  category: development
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/template-builder-ui
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

<!--
Verified against Sent sources:
- https://docs.sent.dm/docs/docs/03-quickstart/first-template
- https://docs.sent.dm/start/quickstart/first-message
- https://docs.sent.dm/start/quickstart/dashboard-walkthrough
- Sent v3 OpenAPI: POST /v3/templates, GET /v3/templates, GET /v3/templates/{id}, PUT /v3/templates/{id}, DELETE /v3/templates/{id}, POST /v3/messages, /v3/webhooks/event-types

Review notes:
- Sent docs define templates as reusable message blueprints across SMS, WhatsApp, and RCS.
- Sent docs verify dashboard creation paths: sample, scratch, Meta import, and JSON definition.
- Sent docs verify template statuses Draft, Pending, Approved, and Rejected. Treat Meta-only statuses such as PAUSED as external unless Sent webhook event types expose them.
-->

# Template builder UI

## Overview

Use this skill to design or improve a Sent template builder UI. Sent templates are reusable message blueprints across SMS, WhatsApp, and RCS. The UI must let users create valid templates, preview channel-specific rendering, supply variable samples, submit for review where required, and understand status without exposing irrelevant provider internals.

The Sent v3 template API supports create, list, retrieve, update, and delete operations. The first-message workflow sends templates through `POST /v3/messages` using a `template.id`. A good UI therefore optimizes both authoring and later sendability.

## When to use

Use this skill when the user asks for a template builder, template editor, template management UI, template validation, Meta import flow, JSON template builder, WhatsApp approval UI, RCS rich template editor, SMS template preview, template status page, or a product/engineering spec for Sent templates.

Do not use this skill to write final WhatsApp template copy; use `waba-template-author`. Do not use it to decide Sender Profile boundaries; use `sender-profile-architect`. Do not use it to diagnose delivery failures after sends; use `messaging-performance-analyzer`.

## Product principles

A Sent template UI should make the valid path obvious and the invalid path hard. Users should understand three things at all times: what channels the template targets, what variables need examples, and whether the template is editable, pending, approved, or rejected.

| Principle | UI behavior | Why it matters |
|---|---|---|
| Channel-first editing | User chooses SMS, WhatsApp, RCS, or combinations before components. | Component support differs by channel. |
| Variable-first validation | Every variable has a sample value before review/submission. | Reviewers and test sends need concrete rendered examples. |
| Status-aware actions | Drafts can be edited; pending/approved/rejected states guide next action. | Users should not unknowingly break reviewed content. |
| Provider-specific details are scoped | WhatsApp category and Meta import appear only where WhatsApp applies. | Keeps cross-channel UI from becoming WhatsApp-only. |
| JSON escape hatch | Advanced users can paste/edit JSON with schema validation. | Sent docs include JSON definition as a creation path. |

## Process

### 1. Start with the template intent and channels

Ask what the template is for before showing component controls. Intent drives category, variables, and review risk. Then ask which channels the user wants to support.

**Example.** “Order shipped” targeting SMS, WhatsApp, and RCS should start from one intent but render differently: SMS may be plain text, WhatsApp may need a utility category and sample variables, and RCS may use richer actions if configured.

### 2. Model the Sent template lifecycle

Use Sent’s documented statuses in the UI: Draft, Pending, Approved, and Rejected. Do not introduce provider-only states as global Sent states unless Sent event types or API responses expose them for the account.

| Status | UI meaning | Allowed primary action |
|---|---|---|
| Draft | Saved but not submitted. | Edit, preview, validate, submit. |
| Pending | Submitted for review/approval where required. | View, cancel if supported, duplicate. |
| Approved | Available for production sends where channel setup allows. | Use in send flow, duplicate for revision. |
| Rejected | Review failed or validation blocked approval. | View reason, revise, resubmit or duplicate. |

Although the OpenAPI says `PUT /v3/templates/{id}` can update name, category, language, definition, or submit for review, the UI should still protect approved templates with a “duplicate and revise” path when auditability matters. Present immutability as a product-safety choice, not a Sent API fact.

### 3. Back the UI with Sent template endpoints

Keep the UI contract aligned to the verified v3 template operations.

| UI action | Endpoint | Notes |
|---|---|---|
| Create template | `POST /v3/templates` | Create with header, body, footer, buttons, and review/draft intent. |
| List/search templates | `GET /v3/templates?page=&pageSize=&search=&status=&category=` | Support filtering by status, category, and search. |
| Open template detail | `GET /v3/templates/{id}` | Show name, category, language, status, and definition. |
| Save/update | `PUT /v3/templates/{id}` | Update editable fields or submit for review. |
| Delete | `DELETE /v3/templates/{id}` | Optionally delete from Meta where supported by the API request. |
| Send test after approval | `POST /v3/messages` | Use `template.id` and channel selection. |

Use optional `Idempotency-Key` headers when create/update requests may be retried by the frontend or backend.

### 4. Design the editor around components

Represent the template as a structured definition rather than one text blob. Sent’s docs describe template components such as header, body, footer, and buttons, with practical support differences across SMS, RCS, and WhatsApp.

| Component | UI guidance | Channel notes |
|---|---|---|
| Header | Optional title/media area with clear preview. | Most relevant to WhatsApp/RCS; validate per selected channel. |
| Body | Required main content with variable insertion. | Needed across channels; SMS preview should show plain-text length behavior. |
| Footer | Optional low-emphasis text. | Useful for compliance or context where supported. |
| Buttons/actions | Explicit button type and target. | Validate per channel; do not allow unsupported combinations. |
| Variables | Named or positional placeholders with sample values. | Samples are required for review and testing. |

### 5. Make validation staged and explainable

Run validation in layers so users know whether a problem is a Sent schema issue, a channel support issue, or a policy/review issue.

| Layer | Example error | Fix |
|---|---|---|
| Required fields | “Body is required.” | Add body content. |
| Variable samples | “`{{order_id}}` has no sample value.” | Add a realistic sample. |
| Channel support | “SMS cannot render this rich button.” | Remove button for SMS or split channel variants. |
| WhatsApp review risk | “Marketing language in a utility template may be rejected or reclassified.” | Change category or remove promotional content. |
| JSON schema | “Definition does not match Sent template shape.” | Correct JSON before save. |

**Example validation.** If a utility WhatsApp template says “Your order shipped. Add 20% off accessories today,” the UI should warn that promotional content conflicts with utility intent. For SMS, the same content may be syntactically valid but still must align with 10DLC use-case registration.

### 6. Support Sent’s creation paths

Sent's dashboard exposes four template creation flows at `app.sent.dm/dashboard/templates`. Mirror them by name and intent.

| Path | Best for | UI requirement |
|---|---|---|
| Create from Sample | New users and common templates | Curated examples with editable variables. |
| Create from Scratch | Product teams building custom flows | Guided component editor. |
| Import from Meta | Existing WhatsApp template libraries | Import review, mapping, and status reconciliation. |
| Create From Definition | Developers and migrations | Schema validation, diff view, and clear errors. |

### 7. Preview the send path, not only the design

An approved template is only useful if it can be sent. Add a test-send preview that asks for Sender Profile/channel context, recipient test number, variable values, and sandbox/production mode where applicable. Show that production sending uses `POST /v3/messages` with the selected `template.id`.

## Common rationalizations to avoid

Do not build a WhatsApp-only UI and call it a Sent template builder. Sent templates span SMS, WhatsApp, and RCS.

Do not mark name/language/category immutable as a Sent API fact. The verified update endpoint can update those fields; immutability is a product governance decision.

Do not show provider policy warnings globally. Only show WhatsApp-specific category/review warnings when WhatsApp is selected.

Do not hide sample values in an advanced panel. Missing or unrealistic samples are a common review and testing failure.

Do not rely on frontend validation alone. The backend should validate the Sent request shape and preserve API error messages for users.

## Verification checklist

- [ ] The UI starts with template intent and target channels.
- [ ] Statuses match Sent’s documented Draft, Pending, Approved, and Rejected states.
- [ ] Template CRUD maps to verified `/v3/templates` endpoints.
- [ ] Variables cannot be submitted without sample values.
- [ ] Component validation is channel-aware for SMS, WhatsApp, and RCS.
- [ ] WhatsApp-specific category/review warnings are scoped to WhatsApp templates.
- [ ] JSON definition mode validates schema before save.
- [ ] Test-send preview uses `POST /v3/messages` with `template.id` after approval/readiness checks.

## Related skills

Use `waba-template-author` when the task is to write or classify WhatsApp template content.

Use `sms-10dlc-registration` when SMS template copy must match a US A2P campaign use case or opt-out evidence.

Use `rcs-agent-onboarding` when RCS templates depend on agent approval, fallback behavior, or rich-rendering tests.

Use `sender-profile-architect` when template ownership, profile scoping, or tenant boundaries are unclear.

Use `messaging-performance-analyzer` when an approved template sends poorly or webhook evidence shows failures.

Use the `sent` skill for shared Sent terminology and routing.

## Suggested bundled references and scripts

| File | Type | Purpose |
|---|---|---|
| `references/template-validation-matrix.md` | Lookup table | List component support, variable rules, and channel-specific restrictions without bloating the skill body. |
| `references/template-ui-wireflows.md` | Worked examples | Show sample, scratch, Meta import, and JSON creation flows. |
| `references/template-status-handling.md` | Decision matrix | Map Sent status and provider review outcomes to UI actions. |

## Unverified claims to confirm or remove

- Whether template name/language/category are immutable after first save is not documented in the snapshot; the `PUT /v3/templates/{id}` endpoint accepts these fields, so behavior should be verified against the live OpenAPI before assuming. Treat product-side locking as a governance choice, not an API fact.
- Mixed-button rules (quick-reply XOR CTA, ordering, per-category constraints) remain external Meta concerns — link to Meta's WhatsApp template docs, do not mirror.
- Template-status webhook event names follow the `<field>.<event>` pattern (the snapshot confirms the envelope) but the snapshot does not enumerate template-specific events. Discover the exact names via `GET /v3/webhooks/event-types` for the account.
