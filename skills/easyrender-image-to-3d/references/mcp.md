# MCP contract and operational details

Checked against the production application's `packages/mcp/src/index.ts` and
`packages/core/src/renders.ts` on 2026-11-15. Discover the connected server's current tool schemas;
if they differ, use them and report any material workflow/cost difference before spending.

## Connection

- Endpoint: `https://easyrender.ai/api/mcp`.
- Transport: Streamable HTTP.
- Authentication: the client's supported easyrender sign-in flow or an easyrender API key passed
  in `Authorization: Bearer …`. Manage credentials through the client, not this skill's files.
- [Account connectors](https://easyrender.ai/connectors) and
  [setup instructions](https://easyrender.ai/mcp#connect).
- Logical tool names below may be namespaced by the host. There are no `list_renders`,
  `batch_render`, `cancel_render`, `refund`, `publish` or export-conversion tools in this contract.

## Tools

| Tool            | Input                                                                       | Important response                                                |
| --------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `create_render` | `image_url` OR `image_base64`; `content_type` for base64; optional `prompt` | Render view and `links`; creation starts the preview              |
| `get_render`    | `{ "id": "<returned-id>" }`                                                 | Current render view and `links`                                   |
| `get_credits`   | `{}`                                                                        | `balance`, `render_credits`, account pricing/plans and `buy` link |
| `render_3d`     | `{ "id": "<returned-id>" }`                                                 | Render view and `links`; starts the paid build                    |

The tools return a text content block containing JSON on success. A result marked `isError`
is an error message, not a successful render or a guaranteed JSON object.

### Photo input

Supported photo MIME types are `image/jpeg`, `image/png`, `image/webp`; maximum decoded file size
is 4 MiB (4 × 1024 × 1024 bytes). Prefer a well-lit, sharp image around 800 px or larger on its
short side. Current bundled validation rejects sides below 400 px; live guardrails may be tuned.
Do not silently crop away parts, materially alter the photo or enlarge it to bypass validation.

For a URL, pass a fetchable **public HTTPS** image URL. For a private/local photo, use
`image_base64` with the **raw base64 payload, without a data-URL prefix**, and its matching
`content_type`. Do not include both input forms: the server prefers `image_url`. If the client
cannot access/encode the image, explain the missing capability rather than inventing a URL.
`prompt` is optional, maximum 500 characters, and must describe the object rather than instruct
an agent or override the rendering system.

### Render view

Useful fields are `id`, `status`, `error`, `hasPreview`, `hasSheet`, `hasModel`, `credits`,
`renderCredits`, `sheetCredits`, `isPublic`, plus:

- `links.page`: account-facing result page.
- `links.preview`: watermarked preview until paid.
- `links.model_glb`: model endpoint; usable only after the model is ready.

The presence of a link is not proof an asset exists. Links are returned before completion.

| Observed state                                   | What to do                                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| `drafting`                                       | Poll the same ID with bounded backoff; no paid call                      |
| `preview_ready`                                  | Review preview, check cost/balance, then build only within authorization |
| `rendering`                                      | A build is running; poll the same ID, do not create another              |
| `ready` and `hasModel: true`                     | Deliver the returned GLB/page; do not rebuild                            |
| `failed`                                         | Report error; no automatic new paid attempt                              |
| Unknown state or inconsistent `ready`/`hasModel` | Do not assert success; re-read once, then report the inconsistency       |

### Quote and budget

For `preview_ready`, validate that `renderCredits`, `credits` and `balance` are finite,
non-negative numeric values. Pending debit = `max(0, renderCredits - credits)`. `renderCredits`
already reflects whether the render can reuse a final sheet. `credits` accounts for money already
spent on this render; don't subtract a sheet cost again or count prior spend as a new debit.

Consult live values; do not hard-code a credit amount or currency conversion in this skill.
Plans may vary by account, and an AI client can charge separately. If the user sets a ceiling
in money, use an explicitly agreed current conversion in that currency or ask for a credit
ceiling; do not infer it from a default advertised rate or an unrelated subscription price. The `buy` URL is a destination
for the user to review, not authorization to purchase. The server bills/refunds; the skill cannot
prevent all concurrent account spend, cancel a job or grant a refund. Recheck the budget before
each paid call and count unresolved attempts against the cap.

### Downloads and errors

Private `links.preview`/`links.model_glb` requests require the owner's authenticated session or
API-key header. When fetching from a tool, use only the trusted easyrender origin and the client's
secure credential facility. Never send the API key to another host or attach it as a query
parameter. If the host cannot fetch with authentication, give the signed-in page link instead.
Do not change `isPublic` or expose the model as a workaround.

A `failed` render is reported with zero recorded credits because failed builds are refunded by
the service. State what the response says; without a ledger or isolated before/after evidence,
a current balance alone cannot prove the exact refund. Preserve the ID for support/resume.
