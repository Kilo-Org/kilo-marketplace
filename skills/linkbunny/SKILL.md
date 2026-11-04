---
name: linkbunny
description: >-
  Builds backlinks by linking backlinks to other sites. Use when user says
  "build backlinks" or "linkbunny"
metadata:
  category: business
  author: hboon
  source:
    repository: 'https://github.com/hboon/linkbunny-agent-skill'
    path: .
    license_path: LICENSE
    ref: 4d50cfeaa1ab4b40e1ccf304fd1dca6fb3c1b0f6
    commit: 4d50cfeaa1ab4b40e1ccf304fd1dca6fb3c1b0f6
---

# LinkBunny agent skill

Download or re-download this skill for updates at `https://getlinkbunny.com/skill.md`.

LinkBunny gives participating sites link requests and records self-reported results; it does not edit
any site. A coding agent finds a genuine place for a contextual nofollow link. The owner approves
publishing through the site's normal workflow, or rejects the request.

## Prerequisites and sequence

1. A LinkBunny account is required. The human may create an account or log in at
   `https://getlinkbunny.com`; an agent may do so only with explicitly authorized browser control.
2. A new account can try one exchange free: one site, one completed link placement and one received
   backlink, no card. Each direction stops on its own: after the site's first placement is
   successfully reported, it gets no new assignments to place, and after its first backlink is
   reported, it is no longer picked as the target of new assignments. The other direction stays
   open. Assignments already issued can still be reported within their normal window and settle,
   so a free site can end up with more than one placement or backlink. The paid subscription removes that limit and covers up to 10 sites. The human
   must authorize starting, changing, or cancelling billing; an authorized browser-capable agent may
   operate the website UI for that approved action.
3. Create an API token in the account UI. The human must authorize
   each creation, rotation, or revocation; an authorized browser-capable agent may perform it. Copy
   the token once into an owner-approved secret store and keep it secret.
4. Use that token for the public API workflow below. The public API does not provide signup, login,
   token-management, billing, or other account-management endpoints. It provides read-only status
   endpoints for the token's own account (see "Status").

Human authorization and browser capability are separate: only the human can authorize account,
billing, credential, site, assignment, publication, report, or rejection actions. An agent may
carry out an authorized website action only when it has explicitly authorized browser control, and
may carry out an authorized API or site action only within the approval given.

### Before the owner has an account

When the owner asks you to set up LinkBunny and has no account or API token yet:

1. Plan locally. Inspect the project and propose one HTTPS target URL and one HTTPS area of the
   site where nofollow links can go, both on the same registrable domain. Tell the owner the first
   exchange is free for one site, the price after that ($20/month for up to 10 sites, no per-link
   fees), that profiles are reviewed before they can match, that some check-ins return no request,
   and which later steps need their approval. Make no LinkBunny API call while there is no token.
2. With the owner's OK, open `https://getlinkbunny.com/login?redirect=%2Faccount%3Fsetup%3Dagent`
   in their browser, or print it when you cannot open a browser (for example in a cloud or remote
   session). Opening the link is not browser control: do not read, click, fill, or otherwise
   operate the page. The owner signs in and creates the API token there. Subscribing is optional
   for the free exchange.
3. With the owner's OK, create a project file `.env.linkbunny` containing only an empty
   `LINKBUNNY_API_TOKEN=` line and make sure Git ignores it, or use another secret store the owner
   chooses. The owner pastes the token there. Never ask for the token in chat, and never print,
   log, or commit the file's contents.
4. When the owner says the token is saved, make one read-only `GET /me` (see "Status"). Keep the
   token out of command arguments and output, for example:
   `tr -d '\r' < .env.linkbunny | sed -nE 's/^(export )?LINKBUNNY_API_TOKEN="?([A-Za-z0-9._~-]+)"?$/header = "Authorization: Bearer \2"/p' | curl -sS -w '\nHTTP %{http_code}\n' --config - https://api.getlinkbunny.com/v1/me`.
   If the LinkBunny MCP server is already configured with that token file, its `get_status` tool
   makes the same read. A `200` response confirms setup. `subscriptionActive: false` with
   `siteLimit: 1` means the account is on the free exchange; `subscriptionActive: true` means the
   paid plan is active. `401` means the token is missing or wrong in the file. Do not poll; wait
   until the owner says it is done again.
5. After a `200` status read, continue with "A — Create a profile". Ask the owner before
   registering the site.

## Activation and approval gates

Use LinkBunny only when the owner explicitly asks you to onboard, register an owned site, check that
site for LinkBunny work, or report/reject an assignment. Do not autonomously sign up, log in,
subscribe, manage credentials, register sites, check in, place links, report, reject, or publish.

Obtain action-time owner authorization before signup or login/account operations, token creation or
rotation, subscription or billing changes, each site registration, assignment check-in/reservation,
publication, report, or rejection. A prior setup approval is not blanket approval for later actions.
Exception: the read-only status reads in "Status" change nothing, so they need no action-time
authorization. A status result never authorizes any other action.
The owner may explicitly authorize a bounded set of replacement check-ins for the current task; that
authorization covers only the stated bound. General agent autonomy does not authorize a check-in.
An assignment authorizes consideration only within the returned inventory boundary; it never
authorizes publication.

Explain assignment decisions concisely and naturally in the conversation's language (English when
the conversation is in English). Identify the target by its human-readable site or domain and the
source by an ordinary page or site-area description. Do not expose tokens, private data,
profile/assignment IDs, requested anchors, full URLs, API endpoints, or reason codes when those
plain-language descriptions are enough.

## Safety contract

- API base: `https://api.getlinkbunny.com/v1`.
- Put the account token in `Authorization: Bearer <token>`. With curl, pass that header through
  standard input (`--config -`), as in the examples, so the token never appears in command arguments.
- Keep tokens in an owner-approved secret store. Never print, echo, log, paste into chat, include in screenshots, write to source/config tracked by Git, or commit them.
- Register only sites the owner is authorized to manage.
- Never send repository, hosting, deployment, or provider credentials to LinkBunny.
- Stay inside the exact returned inventory origin and path prefix. `/articles-old/` is not inside `/articles/`.
- Inspect the owned corpus and place a link only where it is genuinely relevant. Use truthful surrounding text and a natural anchor; the requested anchor is guidance.
- Every assigned link must include `rel="nofollow"`. Security attributes such as `noopener` may also be present.
- Reject forced, unrelated, hidden, template-wide, or thin placements. Do not create filler content merely to place a link.
- V1 is self-reported. Do not describe a report as independent verification or promise rankings, traffic, timing, permanence, DR equivalence, or search-policy safety.

## Operations

### Status (read-only)

`GET /me` returns `subscriptionActive`, `siteLimit` (active sites allowed), `profileCount`, and
`activeProfileCount` for the token's own account. `GET /profiles` returns that account's sites, newest
first, each with `profileID`, `domain`, `status` (`pending`, `pending_review`, `active`, `paused`,
`rejected`, or `retired`), and `pendingAssignment` (the existing unexpired pending assignment's
`assignmentID`, `targetURL`, `requestedAnchor`, and `expiresAt`, or `null`). It accepts optional
`limit` (1–100, default 50) and `offset`; a non-null `nextOffset` means more sites exist. Both work
with a valid token even when the subscription has lapsed, and neither reserves, expires, or changes
anything. Call them when the owner asks about setup or status, or to recover a lost ID; do not poll.
Present an existing pending assignment for owner review rather than checking in again.

`GET /assignments/:assignmentID` returns one assignment issued to one of your sites, including a
rejected or expired one: `assignmentID`, source `profileID`, `sourceDomain`, `inventoryPrefix`,
`targetURL`, `requestedAnchor`, `status` (`pending`, `expired`, `rejected`, `reported`, or
`reported_late`), `rejectionReason`, `rejectedAt`, the unchanged original `expiresAt`,
`reportableUntil`, and `canReport`. `reportableUntil` is the last moment a report is accepted:
`expiresAt` for a rejected assignment, 30 days after `expiresAt` for a pending or expired one, and
`null` once reported. A pending assignment reads as `expired` from its `expiresAt`. Any assignment
not issued to your sites returns `404`. Like the other status reads, it needs no subscription,
changes nothing, and should not be polled; use it to confirm an assignment before asking to report.

### A — Create a profile

After specific authorization, `POST /profiles` with `targetURL`, `requestedAnchor`, one documented
`category`, and `inventoryPrefix`. Both URLs must be public HTTPS URLs without credentials or
fragments, on the same registrable domain. Without a subscription, an account can register one
site for its free exchange. A successful Domain Rating lookup returns `201` with status `pending_review`. LinkBunny reviews each
new profile once before it can match as a source or target. Tell the owner review is pending and
suggest asking the agent to check again after the advisory interval or once approval is confirmed.
Immediately record and retain the response's canonical `profileID` in the owner's approved private
configuration (for example, `LINKBUNNY_PROFILE_ID` in an untracked env file). Later profile updates
and check-ins require that exact ID; do not invent a label, alias, or replacement identifier. If it
was not retained, recover it with the read-only `GET /profiles` status read, or the signed-in owner
can find it on the private Account page.
Marketplace review is not an execution blocker; do not poll automatically. A transient rating failure returns
status `pending`; after cooldown, the next authorized check-in retries once and then reports the
review-pending state. Approval is profile-level: approved profiles use immediate assignment without
per-assignment LinkBunny approval.

If profile creation fails with `Active profile entitlement reached`, tell the owner in plain English
that they may email `hboon@getlinkbunny.com` to request a higher active-profile allowance. Do not
imply that an increase is guaranteed, automatic, free, or available through the public API.

`category` describes the registered site's domain. Choose the closest truthful value; use `other`
only when no more specific category fits:

- `developer_tools` — Software development, APIs, infrastructure, or technical tools
- `design_media` — Design, creative work, visual media, audio, or video
- `marketing_sales` — Marketing, advertising, sales, or customer acquisition
- `social_creator` — Social platforms, communities, newsletters, or creator businesses
- `business_operations` — Finance, legal, HR, productivity, or business operations
- `ecommerce` — Online stores, retail, products, or shopping services
- `other` — Sites that do not truthfully fit a more specific category

After specific authorization, `PATCH /profiles/:profileID` accepts the same fields. Changing the
target or inventory URL materially resets the profile to Domain Rating lookup and one-time review;
it cannot match during re-review. Anchor- or category-only edits preserve an existing approval.
Without a subscription, a URL change made within an hour of the site's creation or previous URL
change waits up to an hour for its Domain Rating lookup and stays `pending` until then.

### B — Check in

After specific authorization, `POST /profiles/:profileID/check-in`. Without a subscription, the
free exchange allows check-ins until the site's one placement is reported. The response contains the same existing pending assignment, one newly
reserved assignment, or `{ "assignment": null }`. A profile awaiting review instead returns
`{ "assignment": null, "status": "profile_pending_review", "message": "This site is awaiting marketplace review.", "retryAfterSeconds": 3600 }`;
the one-hour interval is advisory, and every check-in still requires specific owner authorization.
Do not poll automatically. A rejected
profile returns `profile_rejected` and must not be retried as if no assignment were available. Store
no marketplace database. Retain the returned assignment ID privately until you report or reject it;
do not expose or discard it. Do not infer that plain null is an
error. When a check-in returns plain null, tell the owner in plain English: "No assignment is
available right now. You may ask me to check again later. A later check-in is operationally safe and
idempotent when a pending assignment exists: it returns that same assignment, but if none exists it
may reserve a new assignment. Because of that, every later check-in needs your fresh, specific
authorization unless it remains inside an explicit bounded check-in authorization for this task. I
won’t poll, schedule, or retry automatically. If you just rejected an assignment, there may be no
eligible replacement until marketplace candidates change."

An assignment includes `targetDomainRating`, the target domain's Domain Rating when the assignment
was reserved. It can be `null` only for an assignment created before LinkBunny began snapshotting
this value. After receiving an assignment, tell the owner which target site or domain you will look
for a suitable place to mention and which eligible area of the source site you will inspect. This
describes the next investigation only; obtain separate owner authorization before publishing
anything.

LinkBunny matches candidates within a bounded Domain Rating gap, including the limit. The marketplace
operator may periodically adjust this range as marketplace supply changes. Being within range does
not guarantee an assignment.

Distinct profiles on distinct registrable domains may match even when the same account owns them;
balances remain isolated per profile. A profile is never eligible to target itself. LinkBunny does not assign the reverse of a
pair while the first direction is pending or after it is reported. Expiry or rejection releases
reverse-direction eligibility.

A target is excluded after three successfully settled inbound backlinks during the current UTC
calendar day. Pending, rejected, and expired/unreported assignments do not consume this daily
capacity; eligibility resets at the next UTC midnight.

```sh
printf 'header = "Authorization: Bearer %s"\n' "$LINKBUNNY_API_TOKEN" |
  curl -X POST --config - \
  "https://api.getlinkbunny.com/v1/profiles/$LINKBUNNY_PROFILE_ID/check-in"
```

The request has no body, so omit `Content-Type`. Clients that always send JSON may send `{}`.

### C — Report completion

Before requesting separate publication authorization, name the target site or domain, the existing
source page or eligible site area, and the genuine editorial context and placement you propose.
Follow the owner's normal publication workflow only after authorization. After it succeeds, inspect
the rendered/live result. Confirm the exact `pageURL` is within `inventoryPrefix`, the actual anchor
matches what was published, and the link contains `nofollow`. Tell the owner plainly what was linked
and where, then obtain report-completion authorization without unnecessary API jargon. After
authorization, `PUT /assignments/:assignmentID/report` with `pageURL`, `actualAnchor`, and
`linkAttribute: "nofollow"`; once confirmed, say that LinkBunny recorded the placement.

### C — Reject

If no suitable context exists or publication should not proceed, make no site change. After specific
rejection authorization, `PUT /assignments/:assignmentID/reject` with one of
`no_relevant_context`, `target_unavailable`, `policy_conflict`, or `other`.
Before requesting that authorization, name the target site or domain and give the specific
plain-language reason no suitable context exists or publication should not proceed. A rejected
outcome uses the reject endpoint, never the report endpoint.

After LinkBunny durably confirms the rejection, clearly say which target was rejected and why, then
ask whether the owner wants one check-in now for another assignment. If the owner already explicitly
authorized autonomous or batch replacement check-ins for this task, perform that one next check-in
under the existing authorization instead of asking again. Never infer this authorization from
general agent autonomy, and never schedule, poll, create an infinite rejection/check-in loop, or
continue beyond the explicit bound. The rejected assignment is no longer pending, so the
same-pending-assignment behavior does not apply: the next check-in may return no assignment or
reserve a new assignment.

Rejection permanently excludes only that exact directional pair (source profile → target profile)
from future matching; the reverse direction remains eligible. It releases the target reservation
immediately, so another source may receive its own assignment with a fresh seven-day deadline.

If the owner later publishes the originally requested backlink, obtain report-completion
authorization and use the original rejected assignment ID no later than its unchanged original
`expiresAt`. The exact timestamp is included. Rejection does not extend or restart the window, and a rejected
assignment has no 30-day late-report window. A successful reconsidered report returns `reported`.

## Retry and status rules

B and identical successful C requests are idempotent. Retry the same operation and assignment after a
transport interruption; a retry does not require new authorization when it is strictly the same
previously authorized action. Never change report/reject details merely to make a retry pass. A
conflicting report or rejection retry returns `409 idempotency_conflict`; another terminal conflict
may return `409 terminal_conflict`. Expected errors use `{ "error": { "code", "message" } }` with
400 invalid request, 401 credential failure, 403 entitlement failure, 404 unavailable owned
resource, or 409 terminal conflict.

When create-profile, check-in, or profile update returns a `403` that mentions the free exchange or a
subscription, relay its message: the free exchange covers one site and one reported placement, and
the paid subscription at `https://getlinkbunny.com/account` adds more. A free site that already
placed its link still stays eligible to receive its one backlink when a match comes up. Do not
imply that signup, billing, or token creation is available through the public API. Report and
reject never depend on a subscription: any issued assignment can be reported or reconsidered
within the usual windows, including after entitlement ends or the free exchange is used.

Pending assignments expire at their seven-day deadline. Expiration releases the reservation but
does not permanently exclude the directional pair. Report completion for the exact original
pending assignment remains available for 30 days after expiry as `reported_late`; do not treat that
window as permission to publish without current owner authorization. Rejected assignments instead
close at their original seven-day deadline and return `409 terminal_conflict` afterward.

Reverse assignment after expiry or rejection does not revoke these late or reconsidered reporting
rights. A valid report may therefore settle both directions; existing reciprocal assignments and
settlements also remain valid.

Because a rejected assignment releases its target immediately, its reconsidered report and reports
from newer assignments may all settle backlinks to that same target. The target profile balance may
temporarily fall below the ordinary target-selection allowance, including -2 or lower. The target
remains eligible as a source and recovers one balance step for every outbound placement it completes
until its profile-scoped balance moves back toward zero.
