# WABA Onboarding Runbook — Dashboard Flow

Operator-facing companion to `waba-embedded-signup`. Walks the **Sent dashboard** WhatsApp connection flow in time order and tells you, for each step, what success looks like, the failure modes you should expect, and how to recover **without** restarting the whole signup.

The v3 snapshot confirms there is **no public Sent Embedded Signup API endpoint** — the Channels page in the dashboard is the surface, and it initiates Meta's Facebook Login for Business flow internally. This runbook reflects that reality; for the broader skill workflow and integration-path decision, see `waba-embedded-signup` SKILL.md.

## 0. Pre-flight (per-tenant gates)

Before the "Continue Channel Setup" button is meaningful for a tenant, two account-level gates must be true:

- [ ] **KYC approved.** Per the verified onboarding state machine, the account must have reached `KYC_COMPLETED` (state 5+). Before that, the v3 API returns `AUTH_006` and the dashboard blocks the Channels page. Compliance form fields (business identity, use cases, opt-in evidence) come from the dashboard's KYC + compliance pages.
- [ ] **Meta Business Portfolio ready.** The tenant must already have (or create during the flow) a Meta Business Portfolio under which a WABA will be selected or created. Sent does not provision this on the tenant's behalf.

If KYC is still in `KYC_STARTED`, `WHITELISTED`, `ONBOARDING_STARTED`, or `KYC_RESUBMISSION_REQUESTED`, finish that first. The dashboard's onboarding checklist surfaces the next required step.

## 1. Click "Continue Channel Setup" in the dashboard

After KYC, the dashboard surfaces a **Continue Channel Setup** entry that lands on the **Channels** page.

**Success looks like:** The Channels page loads and shows a **WhatsApp** tab with a **Connect** action.

**Common failure modes:**
- Button is missing / disabled → account state hasn't reached `KYC_COMPLETED`. Finish KYC first.
- API returns `AUTH_007` against `/v3/messages` for a tenant who thinks they're set up → they're at `KYC_COMPLETED` or `MESSAGE_COMPLIANCE_COMPLETED` but haven't completed channel setup. They need to land on this page.

**Recovery without restarting:** Re-check `GET /v3/me` or the dashboard's onboarding indicator. Channel setup itself has no API; route the tenant back to the dashboard.

## 2. Select the phone number

In the Channels → WhatsApp flow, the tenant selects the phone number that will be used for the WABA's first sender. Sent docs note that **this selection is not easy to change later** — once a phone number is bound to a Sender Profile, swapping it requires Meta-side migration plus a dashboard re-bind.

**Success looks like:** The phone number is captured and the flow advances to Meta login. The number should be an E.164 line the tenant controls, not currently registered to another WABA they care about.

**Common failure modes:**
- Tenant picks a number that's already on a WABA they intend to keep separate → after Meta consent they'll discover the number is "in use elsewhere" and have to detach in WhatsApp Manager.
- Tenant picks a personal line they later want back for WhatsApp Consumer → that's a one-way door; warn upfront.

**Recovery without restarting:** Within the same flow you can usually back out and pick a different number. After completion, switching numbers requires Meta-side migration and a fresh dashboard binding.

## 3. Log in with Facebook/Meta and grant Sent permission

The dashboard launches Meta's Embedded Signup popup (Facebook Login for Business). The tenant:

- Logs in with their Meta account that admins the Business Portfolio.
- Selects (or creates) the **WABA** to bind.
- Grants Sent permission to **manage messages and templates** on that WABA.

**Success looks like:** The popup closes with success; the dashboard reflects the connected WABA name.

**Common failure modes:**
- Popup closes immediately → ad-blocker or popup-blocker. Disable for the Sent dashboard origin.
- Tenant chose "Create a new WhatsApp Business Account" inside the dialog and got stuck on business verification → not a Sent issue; tenant must finish verification in Meta Business Suite, then return.
- Tenant unchecked WhatsApp permissions in the consent screen → the binding will fail or be unusable. Re-launch Connect and accept all required permissions.

**Recovery without restarting:** Re-launch Connect from the dashboard. The tenant only re-confirms permissions; previously-captured fields (like the chosen phone number) typically persist.

## 4. Add Meta payment method

Meta charges per-conversation for WhatsApp Business messaging, separately from Sent's billing. The tenant must add a payment method to the WABA in WhatsApp Manager / Meta Business Suite.

**Success looks like:** Payment method status is "Active" in WhatsApp Manager. Sent's dashboard may surface a "Meta payment required" warning until this is true.

**Common failure modes:**
- Card declines → tenant retries with a different card in Meta Business Suite.
- Tenant conflates this with Sent billing → clarify: Sent bills Sent fees; Meta bills WhatsApp conversation fees directly to the WABA.

**Recovery without restarting:** Meta payment is set on the WABA, independent of the Sent flow — the tenant can complete this without re-doing steps 1–3.

## 5. Confirm channel setup completion in dashboard

After the WABA binding and Meta payment are in place, the dashboard reflects channel setup as complete. Internally, the account state should advance to `MESSAGE_COMPLIANCE_COMPLETED` and then to activated. The API surface that signals "I am done" is `POST /v3/profiles/{id}/complete` (idempotent, sensitive — 10/min, burst 5). Inspect `GET /v3/profiles/{id}` and look for `status` ∈ `pending_review` → `approved`.

**Success looks like:** Profile `status` reaches `approved`; the dashboard shows the WhatsApp channel as connected.

**Common failure modes:**
- Profile stays `pending_review` → Sent-side review is still running. Surface the status to the tenant; do not retry `complete` in a loop (rate-limited).
- Profile lands at `rejected` → KYC or compliance evidence was insufficient; the dashboard explains the reason. Fix in KYC + re-run.
- API returns `AUTH_005` against sends → the account state is at step 6 waiting for final Sent-side activation. No tenant action needed; wait.

**Recovery without restarting:** `POST /v3/profiles/{id}/complete` is idempotent — calling again with the same input is safe. Do not delete and re-create the profile to "reset" status.

## 6. Copy API credentials

Once `status = approved`, API credentials are available:

- On the post-setup screen, or
- Anytime from the dashboard's **API Keys** page (the snapshot lists this as `(dashboard-only; not in v3 API spec)` — there is no API to mint or list keys).

Auth in v3 is a single header: `x-api-key: <UUID>`. There is no `x-sender-id` in v3 — that's v2 legacy. The key is account-scoped.

**Success looks like:** A test request to `GET /v3/me` with the key returns 200.

**Common failure modes:**
- `AUTH_001` (401, missing header) → header name wrong; must be `x-api-key`.
- `AUTH_002` (401, invalid key) → key was rotated or copied with whitespace.
- `AUTH_007` (403, no channel configured) → key is valid but the account is at `KYC_COMPLETED` / `MESSAGE_COMPLIANCE_COMPLETED` without a finished channel. Re-check step 5.
- `AUTH_005` (403, pending final activation) → wait for Sent activation; not a credential problem.

**Recovery without restarting:** Re-copy the key from the dashboard. Treat the key as a secret — never log it. Use the sandbox mode (`"sandbox": true` in mutation request bodies) for integration tests so you don't burn budget.

## Stuck-state triage cheat-sheet

| Symptom in production | Step | First thing to check |
|---|---|---|
| "Continue Channel Setup" missing | 0–1 | Account state — finish KYC first |
| Channels page rejects the chosen number | 2 | Number already on another WABA |
| Meta popup closes immediately | 3 | Popup/ad-blocker on dashboard origin |
| Popup completes but dashboard shows "not connected" | 3 | Tenant unchecked permissions; re-launch Connect |
| Dashboard shows "Meta payment required" | 4 | Add payment in WhatsApp Manager |
| Profile stuck `pending_review` | 5 | Sent-side review; do not re-POST `complete` in a loop |
| API send returns `AUTH_007` | 5 | Channel setup not actually complete |
| API send returns `AUTH_005` | 5 | Final Sent activation pending; no action |
| `x-api-key` returns `AUTH_002` | 6 | Re-copy from dashboard; check whitespace |

## What this runbook deliberately does not cover

- Customer apps that own their **own** Meta App and run Embedded Signup themselves (rather than using the Sent-managed dashboard flow). That path is owned by Meta — see `references/waba-embedded-signup-spec.md` and Meta's [Embedded Signup docs](https://developers.facebook.com/docs/whatsapp/embedded-signup).
- Template authoring and submission — see `waba-template-author`.
- Multi-tenant Sender Profile design — see `sender-profile-architect`.
- Post-connection delivery debugging — see `messaging-performance-analyzer`.
