# Example workflows

These examples describe decisions, not completed renders or fixed prices.

## Preview only

User: “Show me what this chair would look like in 3D. Don't spend anything yet.”

Create a preview and poll its ID. Present the preview/page and current build quote. Stop before
`render_3d`, even if the account has enough credits. If the preview cannot be inspected in the
client, say so and ask the user to review it in their account.

## Approved single build

User: “Use this photo to make a GLB. You may spend up to 100 credits; proceed if the preview is OK.”

Generate and inspect the preview. If the live pending debit and balance permit the build,
proceed under that authorization without another approval question. If inspection is impossible,
the user's quality condition is not verified: share the preview for their review. If the quote
exceeds 100, pause the paid step. Finish only on `ready` with `hasModel: true`.

## Catalogue with a shared budget

User: “Make models for these ten product photos, with a total cap of 600 credits. Preview each first.”

Preview and record each photo's render ID and quote; preview quotas still apply. “Preview each
first” establishes order, whereas “show me each preview for approval” would require user review.
Build sequentially within the aggregate limit. Do not spend up to 600 on each item. Track paid
attempts whose outcome is uncertain as reserved spend; a timeout does not free the budget.
If every item will not fit, explain the estimate and obtain a priority order unless the user has
already authorized partial completion. Do not silently choose which products to omit.

## Resume without duplicate spend

User: “The request for render `r_example` timed out. Finish it.”

Query that exact ID. If it is `rendering`, keep polling. If `ready` with a model, return the
existing output. If `preview_ready`, show the current pending debit and use a previous applicable
spending authorization or obtain one before building. If no ID was returned by creation, direct
the user to their library to recover it; don't invent a lookup tool or submit another photo blindly.

## Approximate geometry is unsuitable

User: “Use this photo to make a dimensionally accurate replacement part for manufacturing.”

Explain that easyrender infers unseen surfaces and does not recover measured CAD geometry.
Do not submit a paid render as though it meets that requirement. If the user chooses an approximate
visualization instead, proceed with that revised scope and its budget.
