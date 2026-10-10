# 10DLC Rejection Remediation — Reference

Supporting reference for `sms-10dlc-registration`. When a tenant says "my SMS isn't going through", the failure can be in three layers: **Sent account state** (the customer isn't fully onboarded), **TCR-side** (the brand or campaign was rejected before reaching carriers), or **carrier-side** (T-Mobile / AT&T / Verizon / MVNO declined a TCR-approved campaign). Each layer has a different fix path — always identify the layer first.

Pair with `references/10dlc-evidence-checklist.md` (what should be in the packet) and `references/tcr-use-cases.md` (taxonomy). Run `scripts/validate_10dlc_packet.py` against the corrected packet before re-submitting.

## Layer 0 — Sent account-state errors (verified)

Before assuming TCR or carrier rejection, check whether the API call itself is returning a Sent account-state error. These are returned synchronously from the v3 API and indicate the tenant isn't fully activated yet.

| Sent error code | HTTP | Account states that produce it | What to do |
|---|---|---|---|
| `AUTH_006` | 403 | `SIGNED_UP`, `KYC_STARTED`, `WHITELISTED`, `ONBOARDING_STARTED`, `KYC_RESUBMISSION_REQUESTED` | KYC isn't complete. Finish KYC in the dashboard. If `KYC_RESUBMISSION_REQUESTED`, the compliance team is waiting on revised docs. |
| `AUTH_007` | 403 | `KYC_COMPLETED`, `MESSAGE_COMPLIANCE_COMPLETED` | KYC is done but no messaging channel is configured. Complete the channel + brand/campaign step in the dashboard. |
| `AUTH_005` | 403 | (post-`MESSAGE_COMPLIANCE_COMPLETED`, pre-activation) | Everything is filed; Sent is finishing internal activation. Wait and re-poll. |
| `BUSINESS_003` | 422 | (any active account) | Insufficient account balance. Not a compliance issue — top up billing. Common source of post-registration sending failures once a tenant goes live. |
| `BUSINESS_005` | 422 | (any active account) | A referenced template is still `PENDING` or `REJECTED` (Sent template lifecycle, not TCR). Confirm the SMS template at `/v3/templates/{id}` is `APPROVED` before sending. |

If you're seeing any of the above, it is **not** a TCR or carrier rejection. Resolve the account-state issue first, then verify whether downstream layers are clean.

## Layer 1 — TCR-side rejections (external)

TCR rejected the brand or campaign before it reached carriers. Faster turnaround. Most often: missing data, EIN-name mismatch, content that violates TCR policy. Sent surfaces these on the Sender Profile / Compliance status surfaces; the specific rejection strings come from TCR and are not part of Sent's public error catalog.

## Layer 2 — Carrier-side rejections (external)

TCR approved the campaign, but one or more of T-Mobile, AT&T, Verizon, or an MVNO declined. The campaign's per-carrier state will show `DECLINED` or `SUSPENDED`. Carrier decisions are slower to reverse and require evidence updates before re-submission. Per-carrier rejection codes are owned by each carrier — track them externally.

## 1. Brand verification failure (`UNVERIFIED`, `VETTING_FAILED`)

- **Detect:** TCR brand status moves to `UNVERIFIED` or external vetting returns `FAILED`. Sent surfaces this on the Compliance status of the brand.
- **Root causes:**
  - EIN doesn't match the IRS record for the supplied legal name.
  - Brand address doesn't match the IRS or state filing.
  - Submitted entity type (`PRIVATE_PROFIT` vs `NON_PROFIT`) contradicts the IRS record.
- **Fix steps:**
  1. Re-pull the tenant's IRS EIN confirmation letter (Form CP-575) and reconcile name, address, and entity type field-by-field.
  2. Correct the brand record in Sent. Resubmit for vetting (costs another vet fee).
  3. If the legal name has genuinely changed, the tenant needs an IRS Form 147C confirming the current name before re-vetting.
- **Re-submission etiquette:** Don't re-submit the same data hoping for a different reviewer. Re-vetting with unchanged data is logged as a duplicate and may slow the next legitimate re-vet.

## 2. EIN-to-legal-name mismatch

- **Detect:** Pre-flight (`scripts/validate_10dlc_packet.py`) catches format issues; TCR catches semantic mismatch.
- **Root causes:**
  - Tenant submitted a DBA instead of legal entity name.
  - Recent legal name change not yet reflected with the IRS.
  - Typo in EIN.
- **Fix steps:**
  1. Confirm the EIN against the IRS confirmation letter — not the tenant's accounting system.
  2. Update legal name to match exactly (including suffix).
  3. If a legitimate name change has occurred, request Form 147C from IRS before re-filing.
- **Re-submission etiquette:** Note the changed fields in the resubmission cover letter. Reviewers approve corrections faster when the delta is explicit.

## 3. Campaign content does not match declared use case

- **Detect:** TCR returns a use-case-mismatch verdict or carriers return a content-violation verdict. Often surfaces as an Authentication / 2FA campaign getting downgraded after a sample promo message slips in.
- **Root causes:**
  - Promotional language in samples for **Notifications**, **Authentication**, or **Customer Service**.
  - Samples mention a discount, sale, or call-to-buy.
  - Sample uses a transactional voice but the declared use case is **Marketing**.
- **Fix steps:**
  1. Re-classify: if any sample is genuinely promotional, split into two campaigns rather than reclassifying everything as **High Volume** (see `references/tcr-use-cases.md`).
  2. Rewrite samples to mirror only the traffic that belongs in the declared use case.
  3. For ambiguous samples, lead with the trigger event (`Your order #1029 has shipped`) — reviewers parse the first sentence hardest.
- **Re-submission etiquette:** Resubmit with the trimmed samples. If splitting into two campaigns, file them sequentially, not in parallel, so the first one's vetting score informs the second.

## 4. Opt-in evidence insufficient

- **Detect:** TCR flags the opt-in URL or it gets flagged in manual review.
- **Root causes:**
  - URL points at a homepage rather than the specific consent form.
  - Consent language bundles SMS with email or push.
  - Pre-checked consent box.
  - Consent is buried in terms of service rather than at the point of phone-number capture.
- **Fix steps:**
  1. Update the live opt-in surface so the SMS checkbox is unchecked by default and the consent text is SMS-specific.
  2. Take a fresh screenshot with timestamp and host it publicly.
  3. Re-file with the new URL or screenshot as the opt-in evidence.
- **Re-submission etiquette:** Don't paste a URL that requires login. If the consent flow is behind auth, host a public mock that mirrors the production UX.

## 5. Sample messages too generic

- **Detect:** TCR flags samples as too generic, or carriers downgrade vetting after launch.
- **Root causes:**
  - Samples under 20 characters or under 3 sentences.
  - Missing brand name, recipient context, or opt-out language.
  - Samples are paraphrases instead of literal production sends.
- **Fix steps:**
  1. Pull 5 real sends (with PII redacted) from staging.
  2. Replace generic samples with the redacted real sends, keeping brand name intact.
  3. Make sure samples cover the variety the campaign will actually send.
- **Re-submission etiquette:** Number the samples in the cover note so a reviewer can confirm each one passes their content scan.

## 6. Opt-out configuration missing or inconsistent

- **Detect:** Sample messages don't reference opt-out, or the **Compliance → Opt Keywords** tab has STOP / START / HELP unconfigured for the active profile.
- **Root causes:**
  - Opt Keywords tab not configured for the profile sending the traffic.
  - Brand name missing from the opt-out confirmation auto-reply.
  - Samples don't mention the opt-out instruction (even though the rule is in Opt Keywords, carriers still expect to see hints in samples).
- **Fix steps:**
  1. Configure **STOP** and **START** at minimum in **Compliance → Opt Keywords** for the active profile.
  2. Verify the auto-reply text references the brand and the word `STOP`.
  3. Add a hint like `Reply STOP to unsubscribe.` to samples — it's not the Sent-required field but most carriers expect it.
- **Re-submission etiquette:** Note in the cover that both the Opt Keywords config and the samples were updated together.

## 7. Prohibited content category

- **Detect:** TCR flags `SHAFT` (sex, hate, alcohol, firearms, tobacco) or a similar prohibited-content verdict. Some carriers extend this list (cannabis, payday loans, debt collection).
- **Root causes:**
  - Campaign content falls into an outright prohibited category for US carriers.
  - Age-gated category declared but no age-verification at opt-in.
  - Affiliate marketing without disclosure.
- **Fix steps:**
  1. If outright prohibited (e.g. cannabis on Verizon), 10DLC is not the right channel. Surface this back to the tenant; the registration cannot succeed.
  2. If age-gated, add age verification at opt-in and update samples to reference the gate.
  3. If affiliate marketing, declare it honestly and add disclosure in the message body.
- **Re-submission etiquette:** Don't shop the same prohibited campaign to different reviewers. Address the category restriction or recommend an alternative channel (e.g. WhatsApp, RCS, email).

## General re-submission etiquette

- Fix one class of issue at a time. Bundling unrelated changes into a single re-submission makes it hard for reviewers to confirm each fix.
- Include a short cover note listing what changed since the last submission.
- Re-run `scripts/validate_10dlc_packet.py` before every re-submission. Mechanical failures are free to catch and expensive to re-file for.
- Track rejection codes on the Sender Profile so repeat rejections trigger a manual review before another re-file.
