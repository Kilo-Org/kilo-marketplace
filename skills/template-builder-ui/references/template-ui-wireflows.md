# Template UI Wireflows

The user journeys a Sent template builder must support. Each flow is a UX spec — entry point, screen sequence, state at each step, validation gates, exit conditions — written so a frontend engineer can implement against it without re-deriving the requirements.

The dashboard surface lives at `app.sent.dm/dashboard/templates`. The list view supports search/filter by **name**, **category** (Marketing / Utility), **description**, and **status** (Draft / Approved / Pending / Rejected). Each row exposes per-template actions: **edit**, **delete**, **view analytics**.

There are four template creation flows, exposed in the dashboard exactly as: **Create from Scratch**, **Import from Meta**, **Create From Definition**, **Create from Sample**.

## Flow 1: Create from Scratch

**Entry:** Templates list (`app.sent.dm/dashboard/templates`) → "Create from Scratch" action.

1. **Channel select** (if the tenant has more than one channel provisioned). One-step picker: SMS / WhatsApp / RCS. Locks the validator set (see `references/template-validation-matrix.md`).
2. **Category picker** (WhatsApp only). `UTILITY` / `MARKETING` / `AUTHENTICATION`, each with one-line definition + example.
3. **Name + language** form. Name validated against `^[a-z][a-z0-9_]{0,511}$`; show `_v1` suffix nudge. Language is a typed-search picker over BCP-47 codes.
4. **Editor + preview split**. Component editor left, live preview right, sticky sample editor bottom-right.
5. **Submit gate.** Submit button disabled until all blocking validations pass. On click: confirm modal that shows the final payload diff ("here's what we're sending to Meta").
6. **Optimistic insert.** Template row appears in the list with `Pending` status before the network round-trips.
7. **Status polling / webhook subscription.** See `references/template-status-handling.md`.

## Flow 2: Create from Sample (clone)

**Entry:** Templates list → "Create from Sample" action, or existing template row → "Duplicate".

1. Open the editor pre-filled with the source template's full state (curated sample, or an existing template).
2. **Name field is empty and focused** — the user must pick a new name; the original `(name, language)` pair is treated as permanent by the builder.
3. The category and channel are pre-selected and locked to match the source (changing channel is "create new", not "duplicate").
4. From here: identical to Flow 1 from step 4 onward.

Clone is the most-used "create" path in practice — make it 1-click from any approved template, including across languages (duplicate + change language).

## Flow 3: Import from Meta

**Entry:** Templates list → "Import from Meta" action (WhatsApp only).

1. Modal: paste the raw template JSON from the Meta dashboard's "View JSON" panel.
2. Parser maps Meta's shape into Sent's internal template model.
3. **Diff preview**: show fields that didn't round-trip cleanly (e.g. Meta has a property Sent doesn't model yet). Tenant can proceed or cancel.
4. Land in the editor (Flow 1 from step 4) with all parsed fields filled. Validation runs immediately so any Meta-side state that violates current rules surfaces as inline errors.
5. Sent treats the import as a *draft* — the imported template is not auto-submitted; the tenant must click Submit.

## Flow 4: Create From Definition (advanced)

**Entry:** Templates list → "Create From Definition" action, or Editor → "Edit as JSON" toggle (available on Draft only).

1. Editor swaps to (or opens directly into) a monaco-style JSON pane showing Sent's internal template schema.
2. **Schema-guided autocomplete** (using the same JSON schema that drives the matrix).
3. Live validation + preview continue to run against the JSON.
4. "Back to form" toggle round-trips if the JSON is currently valid; greyed out if not (don't silently discard).
5. Submit gate is identical to Flow 1.

This is the escape hatch for power users and for tenants whose IDE-driven workflows generate templates programmatically.

## Flow 5: Edit

**Entry:** Existing template row → "edit" action.

State of the editor depends on the template's lifecycle state (see `references/template-status-handling.md`):

- **Draft** → all fields editable.
- **Pending** → editor is read-only with a "Pending review — edit blocked" banner. Offer "Withdraw and edit" which moves the template back to Draft via the Sent API.
- **Approved** → name, language, and category are locked. Body, header (text only, not media swap), footer, button labels (not button types) are editable. Editing an Approved template creates a *new version* on submit — surface this prominently ("Submitting will create v2; v1 keeps sending until v2 is approved").
- **Rejected** → all fields editable; the rejection-reason banner is sticky at the top of the editor (see Flow 8).

## Flow 6: Status transitions visible in UI

Every list row shows a status pill. Sent's status enum is exactly `Draft` / `Pending` / `Approved` / `Rejected` — there is no `PAUSED` state surfaced in Sent. Allowed transitions:

```
Draft  ─submit→  Pending  ─approved upstream→  Approved
                          └─rejected upstream→  Rejected ─edit→ Draft
```

Pills use Sent's design-system tokens — not raw Meta colors — so the same component renders for SMS templates and RCS templates.

Transitions animate (fade pill color), and the row's last-updated timestamp updates on each transition so tenants can correlate with WhatsApp review SLA (per Sent docs, typically 24–48 hours).

## Flow 7: Submit

The submit click is the *only* destructive step in the builder. Treat it carefully:

1. **Pre-submit checks** (client-side):
   - Run the full validation matrix; any blocking failure aborts.
   - Open a confirmation modal showing: final preview render, the JSON that will hit Meta, and a "What happens next?" explainer (review SLA, billing implication for marketing, etc.).
2. **POST to Sent's template-submit endpoint** (`POST /v3/templates`, optionally with `Idempotency-Key`). Show a button spinner.
3. **On 2xx**: dismiss the modal; insert an optimistic `Pending` row into the list; clear the draft state.
4. **On 4xx**: surface the Sent error message inline in the modal — do not dismiss; do not lose the user's work.
5. **Subscribe to status** — see `references/template-status-handling.md` for the webhook-vs-polling tradeoff.

## Flow 8: Reject-recover

When a template lands in `Rejected`:

1. The list row's status pill is red and clickable.
2. Clicking opens the editor with a sticky banner at the top: human-readable rejection reason, the raw Meta `reason` collapsed by default, and a "Remediation" callout that maps the rejection code to a concrete fix ("Variable samples contained promotional language — rewrite samples as neutral data and resubmit").
3. The editor pre-focuses the field most likely to be wrong (e.g. the offending sample input).
4. The tenant edits and clicks Submit — the resubmission creates a new attempt with a new `attempt_id` server-side; the list row updates in place rather than duplicating.

## Cross-cutting notes

- Every flow that lands in the editor reuses the same editor component — channel + category state determine which sub-forms render. There is *not* a separate editor per channel.
- Every flow respects the validation matrix at every keystroke; submit is the only network call.
- Optimistic UI is acceptable for insertions (Draft creation, submit) but not for status transitions — those must come from the server.
- All confirmation modals are dismissable with Escape; the Submit modal additionally requires explicit confirm (no Enter-key auto-submit).
