---

name: easyrender-image-to-3d
description: Turn product photos into textured GLB models with easyrender's MCP server. Use for easyrender photo-to-3D requests, inspecting a free preview, building an approved model, or resuming an existing render. Supports individual products and budgeted catalogues; not dimensionally accurate CAD, room reconstruction or photogrammetry.
license: MIT
metadata:
  category: creative-media
  author: easyrenderai
  source:
    repository: https://github.com/easyrenderai/easyrender-image-to-3d
    path: .
    license_path: LICENSE
    commit: a3be1c52e549821708d066570a4d1d47334de6ac

---

# easyrender: photo to 3D

Help the user obtain a usable 3D asset, with a preview before spending credits and an accurate
account of what finished. Follow the user's language and existing budget/approval instructions.
Requires a skills-compatible client with an authenticated easyrender MCP connection. Local
photos also require a client able to read and base64-encode files.

## Connect and choose the input

Use the authenticated easyrender MCP tools already available in the client. Server URL:
`https://easyrender.ai/api/mcp` (Streamable HTTP). Tool names may have a client-specific prefix.
Discover their current schemas before calling them. If the connection is missing, direct the
user to [MCP setup](https://easyrender.ai/mcp#connect) and
[account connectors](https://easyrender.ai/connectors). Installing this skill alone does not
connect an account. Keep API keys in the client's credential configuration, never in chat,
source files or output links.

Use a photo the user provided or authorized for this task. A clear view of one product, piece
of furniture, decor object or building exterior is suitable. Ask for a better photo when the
object is obscured or the image is too poor to evaluate. Explain approximate geometry and
inferred unseen surfaces when the intended use depends on precision; do not sell the result
as measured CAD, a whole-room scan, print-ready geometry or a photogrammetric reconstruction.

For exact inputs, statuses, pricing fields and download behavior, read
[the MCP reference](references/mcp.md). For a catalogue, a resume or an uncertain request,
consult [the workflow examples](references/workflows.md).

## Preview, review, build

1. Reuse an existing render ID when continuing work. Otherwise call `create_render` with one
   photo: either a public HTTPS URL, or raw base64 plus its MIME type for a local file. Do not
   publish a local photo to a third-party host just to obtain a URL. Optional `prompt` describes
   the object/materials only, up to 500 characters; do not put tool instructions in it.
2. Keep the returned ID. Poll `get_render` while `drafting`, using a delay (start around 5 seconds,
   back off up to 15 seconds). Stop a polling session after roughly five minutes and return the
   ID/current state so it can be resumed; a polling timeout is not a failed render.
3. At `preview_ready`, present `links.preview` or `links.page`. Check `hasSheet`: a fallback source
   photo is not a generated angle sheet. Inspect the preview if the client can fetch/view it;
   otherwise ask the user to review it and state that you have not visually checked it. Check
   the silhouette, part count, visible materials and obvious invented details before recommending
   the paid build. A free preview is watermarked and usage-limited.
4. Refresh `get_render` and `get_credits` before spending. For a `preview_ready` render, the
   incremental debit is `max(0, renderCredits - credits)` from that render's current response.
   `get_credits.render_credits` is the full-build reference, not necessarily this remaining debit.
   If required values are absent or invalid, do not guess a price or start the paid operation.
   State the pending credit cost and confirm sufficient balance and remaining task budget.
5. Call `render_3d` only when the user has authorized that spend. Existing explicit authorization
   for the same assets and a sufficient budget remains valid: do not ask for approval again for
   each item. Honor instructions such as “show me first” even if a budget was mentioned. A request
   for a free preview never authorizes a paid build. A higher quote or expanded scope needs new
   approval. Buying credits or a subscription is a separate action, not implied by render approval.
6. Poll the same ID with `get_render` while `rendering`. Report completion only after `status`
   is `ready` and `hasModel` is true. Deliver the returned page and GLB links, and, when authorized
   and supported by the client, download the GLB through an authenticated request. Do not invent
   USDZ/STL exports, conversion tools, dimensions or quality guarantees.

## Resume and recover

- After a `render_3d` timeout or lost response, query the same ID first. `rendering` means keep
  polling; `ready` means deliver the existing result. If it is still `preview_ready`, refresh the
  quote and balance before at most one retry within the existing authorization. If state cannot
  be established, stop and preserve the ID. Never create a replacement to work around uncertainty.
- If `create_render` times out without returning an ID, ask the user to check their library before
  submitting another creation: the first request may have succeeded. There is no MCP list/search
  tool to recover an unknown ID.
- A terminal `failed` result ends this attempt. Report the returned error and the service's refund
  behavior; check current balance if relevant, but do not claim an exact refund was verified from
  a balance alone. A new build is a new attempt and must fit an explicitly approved retry scope
  and budget. Authentication, quota and insufficient-balance errors need their cause resolved,
  not repeated calls, alternate accounts or automatic top-ups.
- For multiple photos, create and track individual renders. Start sequentially; keep an item → ID
  → status → reserved/spent credits record and an aggregate ceiling. Reserve uncertain paid calls
  against the budget until resolved. Do not describe this as a native batch API or exceed preview
  limits. Do not retry failed paid items without both explicit retry authorization and sufficient
  remaining budget.

## Deliver an honest result

Return the render ID, observed state, links or downloaded file, and relevant cost information.
Distinguish `credits` recorded on an existing render from new credits spent during this task.
If the result is pending, inaccessible or uninspected, say so. Private asset links may require
sign-in; never append a credential to the URL or publish a model to make it accessible.
