# Performance diagnosis playbook

Supporting reference for `messaging-performance-analyzer`. The SKILL.md tells you *what* a clean funnel analysis looks like; this doc tells you *which signal to pull next* for a specific symptom, keyed on the Sent error codes that actually surface in v3.

For the full catalog of codes referenced below, see `references/mdr-status-codes.md`.

## Symptom-driven diagnosis

Every entry follows the same pattern: **observable symptom -> where the failure code lives -> what to check first -> handoff if rooted elsewhere.**

### Symptom: messages stuck in QUEUED -> ROUTED, never reach SENT

The lifecycle gate between `ROUTED` and `SENT` is where Sent dispatches to the upstream provider. Stuck cohorts at this gate point at a Sent-side rate or capacity issue, not provider delivery.

Check, in order:

1. **`BUSINESS_002` (429, rate limit exceeded)** — inspect the response envelope of recent `POST /v3/messages` calls and the `X-RateLimit-Remaining` / `Retry-After` headers. Message-sending limits are tiered: Starter 60/min, Growth 300/min, Enterprise custom. If the caller bursts above the tier, new sends 429 and queued ones back up.
2. **`BUSINESS_003` (422, insufficient account balance)** — a stalled queue with zero forward progress and a `BUSINESS_003` in the response is a billing block, not a delivery block. Escalate via account / billing, not delivery.
3. **`BUSINESS_008` (422, operation exceeds account quota)** — quota gate hit; fix is at the account-tier level.
4. **`INTERNAL_003` (502, external provider error) / `INTERNAL_005` (503)** — Sent's upstream provider is degraded. Backoff and retry; no tenant-side fix.

If none of the above codes appear and messages are sitting in `QUEUED`/`ROUTED` for unusually long, capture sample `message_id` values and escalate to Sent support with the timestamps and the request IDs.

### Symptom: every send in a batch fails synchronously with the same error

The whole-batch rejection is in the HTTP response envelope — `error.code` is the lead. Common synchronous codes:

| Code | What it means | Where to fix |
|---|---|---|
| `AUTH_001` / `AUTH_002` | Missing or bad `x-api-key` | Caller integration. |
| `AUTH_005` / `AUTH_006` / `AUTH_007` | Account isn't fully activated / KYC incomplete / no channel configured | `sender-profile-architect` -> onboarding path. |
| `BUSINESS_002` | Rate limit | Slow down or upgrade tier. |
| `BUSINESS_003` | Insufficient balance | Top up account. |
| `BUSINESS_004` | Every recipient has `opt_out=true` | Contact-list hygiene — the batch is correct but the audience is exhausted. |
| `BUSINESS_005` | WhatsApp template not approved (`PENDING` / `REJECTED`) | `waba-template-author` to fix and re-submit. |
| `BUSINESS_007` | Channel not available for these contacts | Check each contact's `available_channels`; route via a different channel or update the contact. |
| `VALIDATION_002` | Phone number not E.164 | Caller bug — fix formatting. |
| `VALIDATION_006` | Invalid enum (case-sensitive) | Caller bug — enums are case-sensitive. |

Rule: a synchronous error never produces FAILED message rows. If the user is asking "why is `message_id=X` failed?" and you can't find the row, look at the request envelope — the batch was rejected before any message was created.

### Symptom: some recipients in a batch succeed, others end up FAILED

This is the per-recipient async failure case. The batch returned 202; some messages later transitioned to FAILED. The diagnosis lives in the `description` field, accessible via:

- `GET /v3/messages/{id}` -> `description`
- `GET /v3/messages/{id}/activities` -> the FAILED activity row's `description`
- The `message.failed` webhook payload tells you which message — **you still must fetch the message** to see the code

Look for these `ERR_*` codes in `description`:

| Code | Triage |
|---|---|
| `ERR_CONSENT_BLOCKED` | Per-recipient opt-out or suppression-list hit. Surface count, dedupe by contact, fix the contact list upstream. This is the per-recipient cousin of `BUSINESS_004` — same root cause, different surface. |
| `ERR_ROUTE_DENIED` | No active route for this channel/country combo. If concentrated in one country: route configuration. If across many countries: sender-profile setup. Hand off to `sender-profile-architect`. |
| `ERR_TEMPLATE_PARAMS_INVALID` | Caller bug — template variables missing or failed regex/type validation. Pull the failing payload, compare against template `variables[]`. Hand off to `waba-template-author` or `template-builder-ui` for the caller-side fix. |

Heuristic: if one `ERR_*` code dominates (>50% of failures), the root cause is at the source of those failures (contact list, route table, caller integration). If failures are evenly distributed, look at infrastructure (provider, network, account state).

### Symptom: webhooks are not firing / customer endpoint sees nothing

Before blaming delivery, prove the webhook itself is working. The webhook config object exposes diagnostic fields directly:

| Check | Field | What "broken" looks like |
|---|---|---|
| Is the webhook active? | `is_active` | `false` -> nothing fans out. |
| Is the endpoint receiving? | `last_delivery_attempt_at` | If recent attempts exist but `last_successful_delivery_at` is much older, the endpoint is returning non-2xx. |
| Is the endpoint healthy? | `consecutive_failures` | Non-zero and growing -> Sent has been hitting the endpoint and getting errors. The fix is on the customer side. |
| Are the right events subscribed? | `event_types`, `event_filters` | A filter like `{"message": ["delivered"]}` will never deliver `message.failed`. If a customer says "I never see failures," check this first. |
| Is the secret current? | `signing_secret` | If recently rotated and the customer is still verifying with the old secret, requests look like signature failures. |

Use `POST /v3/webhooks/{id}/test` (60/min limit) to inject a synthetic event and confirm reachability end-to-end. Use `GET /v3/webhooks/{id}/events` to compare what Sent attempted to fan out against what the customer database actually persisted.

If Sent's webhook event history shows successful deliveries but the customer database is missing rows, the gap is in customer-side ingestion, not in Sent delivery — close the ticket and direct to the customer's webhook handler.

### Symptom: WhatsApp / RCS `READ` rate is suspiciously low

`READ` only exists for WhatsApp and RCS — SMS has no equivalent. Even where supported:

- WhatsApp recipients can disable read receipts; treat read rate as advisory, not authoritative.
- RCS read receipts depend on the handset implementation.
- Compare like-for-like cohorts (same template, same country, same week) before concluding "reads dropped."

If `DELIVERED` is healthy and `READ` is low across all cohorts, the cause is almost always recipient setting / handset variance, not a Sent or template issue.

### Symptom: RCS funnel "looks broken"

RCS is two funnels stitched together. Capability check happens before delivery; most "RCS broken" reports are actually "the audience isn't RCS-capable."

- If the Sender Profile uses fallback (`"channel": ["rcs", "sms"]`), the SMS fallback leg has its own `message_id` and its own lifecycle. Count separately. Never roll fallback SMS into RCS delivery.
- Per-carrier RCS approval is real — an agent can be launched on one carrier and not on another. Symptoms scoped to one carrier point at agent state; hand off to `rcs-agent-onboarding`.

## Cross-skill handoff matrix

| Symptom (with the code that exposes it) | Likely root cause | Hand off to |
|---|---|---|
| `AUTH_005` / `AUTH_006` / `AUTH_007` | Account not fully activated | `sender-profile-architect` |
| `BUSINESS_005` (template not approved) | Template lifecycle issue | `waba-template-author` |
| `ERR_CONSENT_BLOCKED` dominant | Contact-list hygiene | Caller-side (contact ingestion) |
| `ERR_ROUTE_DENIED` dominant | Sender-profile / route config | `sender-profile-architect` |
| `ERR_TEMPLATE_PARAMS_INVALID` dominant | Caller payload bug | `waba-template-author` or `template-builder-ui` |
| WhatsApp `131005` / `133006` (in `description`) | WABA registration / auth drift | `waba-embedded-signup` (re-auth / re-register) |
| WhatsApp `133016` (in `description`) | Tier exhausted | `sender-profile-architect` (capacity planning) |
| SMS carrier-filter spike on new content | Content / use-case mismatch | `sms-10dlc-registration` |
| RCS scoped to one carrier (`description` mentions agent state) | Per-carrier approval | `rcs-agent-onboarding` |
| Webhook `consecutive_failures` growing | Customer endpoint failing | Customer-side (endpoint handler) |

## When to escalate to Sent support

Investigate yourself first when:

- The symptom is scoped to one tenant, template, campaign, or country.
- A specific Sent code (`AUTH_*`, `BUSINESS_*`, `ERR_*`) explains the symptom.
- The webhook health fields (`is_active`, `consecutive_failures`, `last_successful_delivery_at`) prove ingestion is fine.

Escalate to Sent support when:

- Messages sit in `QUEUED`/`ROUTED` for an extended window with no rate-limit / balance / quota codes in the recent request envelopes.
- `INTERNAL_001` / `INTERNAL_002` / `INTERNAL_004` show up at non-trivial rates (Sent infrastructure).
- The `description` on FAILED messages is empty — normalization is broken on Sent's side.
- A delivery anomaly correlates with a Sent platform deploy window.

When escalating, include: account / profile ID, channel, cohort definition (template, country, time window), broken lifecycle stage with absolute counts, distribution of error codes (synchronous and `ERR_*`), `X-Request-Id` values, and a sample of `message_id` values to inspect.

## Diagnostic loop

Repeat until the symptom is explained or scoped:

1. Pin the cohort (channel × template × country × profile × window).
2. Compute the funnel; identify the broken lifecycle stage (`QUEUED`/`ROUTED`/`SENT`/`DELIVERED`/`READ`).
3. If the gate is between `QUEUED` and `SENT`: check synchronous codes on recent request envelopes.
4. If the gate is at `FAILED` after `SENT`: fetch a sample of failed message IDs, read `description` for `ERR_*` codes.
5. If the symptom is missing customer-side data: prove webhook health via `is_active`, `consecutive_failures`, and `/v3/webhooks/{id}/events` before blaming delivery.
6. Hand off via the matrix above, or escalate to Sent support with the required evidence.
7. Quantify the diagnosis — never "looks better now" without a recomputed funnel.
