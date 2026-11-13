# 10DLC Evidence Checklist — Sent Compliance Form

Supporting reference for `sms-10dlc-registration`. This is the definitive list of fields a tenant must supply on Sent's compliance form before Sent files the TCR brand + campaign on their behalf. Field names below match the verified compliance form in the Sent dashboard. The deeper TCR payload (`Brand.entityName`, `Campaign.privacyPolicyLink`, etc.) is filed by Sent internally — keep that taxonomy in `references/tcr-use-cases.md`.

Use this alongside `references/tcr-use-cases.md` when authoring the form, validating an incoming packet, or debugging why a customer's submission failed pre-flight checks. Run `scripts/validate_10dlc_packet.py` against a JSON dump of the packet for the mechanical checks.

## Required fields — business identity

These appear on the KYC + compliance pages and are required for every tenant regardless of country.

### 1. Legal business name

- **Format:** Exact name as registered with the state or national business registry. Include the suffix (`LLC`, `Inc.`, `Corp.`, `LLP`).
- **Common mistakes:**
  - Submitting a DBA, marketing brand, or trade name instead of the legal entity. Sent will reject if the EIN/tax-ID-to-name match fails at the issuer lookup step.
  - Trailing punctuation (`Acme, Inc.,`) — strip the trailing comma.
  - Mismatched capitalization vs registry records.
- **Sent tip:** If the customer uses a different consumer-facing brand, that goes in campaign sample messages, not here.

### 2. Business registration number

- **Format:** The jurisdiction's company / corporate registration number (e.g. state filing number in the US, Companies House number in the UK).
- **Common mistakes:**
  - Confusing this with the EIN / tax ID — they're separate fields.
  - Submitting the partner / member number instead of the entity's filing number.

### 3. Business type / structure

- **Format:** One of the dashboard's entity-type options (Private Profit, Public Profit, Non-Profit, Government, Sole Proprietor, etc.).
- **Common mistakes:**
  - Sole proprietors marking themselves as Private Profit. Sole-prop senders are subject to additional restrictions and Sent must know.
  - Non-profits marking themselves as Private Profit to avoid extra documentation.

### 4. Industry category

- **Format:** Pick the closest match from the dropdown. Drives review path and downstream carrier filtering posture.
- **Common mistakes:**
  - Picking "Other" when a specific match exists.
  - Misclassifying regulated industries (health, finance, gambling) as general retail.

### 5. EIN / tax ID

- **Format:** Federal tax ID for the country. US EIN is nine digits, optionally hyphenated after the first two: `12-3456789` or `123456789`. Regex: `^\d{2}-?\d{7}$`.
- **Common mistakes:**
  - Confusing EIN with SSN (sole proprietors). Sole props with no EIN should pick the sole-proprietor entity type — see `references/tcr-use-cases.md`.
  - Submitting a state tax ID instead of the federal EIN.
  - Typos in the first two digits (the IRS prefix). These fail the IRS match every time.
- **Non-US tenants:** Use the equivalent national tax ID (e.g. VAT number, ABN, GST registration).

### 6. Business address

- **Format:** Street, city, state / region, postal code, country (ISO 3166-1 alpha-2). PO boxes are not accepted for primary brand address.
- **Common mistakes:**
  - Using a mail-forwarding or virtual-office address that doesn't match the address on file with the tax authority for the EIN.
  - Country code mismatches (`USA` vs `US`).

### 7. Business phone number

- **Format:** Full E.164 phone number reachable for compliance contact.
- **Common mistakes:**
  - Submitting a number that goes to a marketing IVR with no path to a human.
  - Submitting a personal mobile when the tenant is a registered entity.

### 8. Contact email

- **Format:** Monitored inbox for compliance correspondence.
- **Common mistakes:**
  - Submitting `noreply@…`. Sent's compliance team replies to this address and reviewers test it.
  - Submitting the founder's personal email when the company has compliance ownership in a separate team.

## Required fields — messaging / use case

These appear in the messaging-compliance section of the form and are filed against the TCR campaign.

### 9. Use-case selection

- **Format:** One of: **Authentication**, **Notifications**, **Marketing**, **Customer Service**, **High Volume**.
- **Common mistakes:**
  - Picking **Marketing** for a transactional flow because it sounds friendlier. Use-case affects review bar and carrier filtering posture — pick the narrowest accurate option.
  - Picking **High Volume** for genuinely low-volume traffic to "future-proof" — Sent maps this to the TCR `MIXED` flow which has a higher review bar.
- **Sent tip:** The dashboard's **Suggest** button auto-fills `Campaign description` based on the use case. Edit it to match the tenant's actual flow before submitting.

### 10. Campaign description

- **Format:** 1-3 sentences explaining what messages the tenant sends, to whom, and when. The dashboard's **Suggest** button drafts this; edit before submitting.
- **Common mistakes:**
  - Generic descriptions ("transactional messages"). Reviewers want specifics: "Shipping and delivery updates for orders placed on acme.example.com."
  - Description doesn't match the use-case option (e.g. describing promotional content under **Notifications**).

### 11. Sample messages (per use case)

- **Format:** Plain-text examples of actual production messages, with `{Variable}` placeholders. Should include the brand name.
- **Common mistakes:**
  - Under 20 characters. Reviewers flag these as too generic.
  - Including a URL shortener that isn't on the brand's verified-domains list.
  - Sample doesn't match the declared use case (promo content in an Authentication sample).
- **Note on opt-out language in samples:** Including `Reply STOP to opt out.` in samples is good carrier hygiene and most reviewers expect to see it, but Sent's compliance form treats opt-out **keywords** as a separate field (see #13). Putting STOP in samples does not satisfy field #13 and vice versa.

### 12. Opt-in mechanism (URL or description)

- **Format:** Public URL showing the exact form, checkbox, or flow where end users consent to receive SMS — or a written description of the opt-in flow if no public URL exists.
- **Common mistakes:**
  - Linking to a checkout flow without showing the SMS-consent checkbox.
  - Consent language that bundles SMS with marketing email — reviewers want SMS-specific consent.
  - Pre-checked consent boxes (forbidden under most state laws).

### 13. Opt-out instructions (Opt Keywords tab)

- **Format:** Managed in the Sent dashboard under **Compliance → Opt Keywords**, not as free-text on the compliance form. At minimum: `STOP` to opt out, `START` to resume. Help keyword (`HELP`) is configured here too.
- **Common mistakes:**
  - Assuming the keywords are inferred from sample messages — they're configured separately and must be set explicitly.
  - Customizing the auto-reply text without a brand-name reference.
  - Forgetting `START` — required for re-opt-in after a `STOP`.

## US-specific extras (required for 10DLC)

| Field | Format | Common mistakes |
|---|---|---|
| **Live website URL** | Full URL with scheme that resolves at submission time. | Staging or preview URLs; coming-soon pages; non-HTTPS. |
| **Privacy policy URL** | Direct URL to a public privacy policy that mentions SMS data handling. | Pointing at the homepage; policy doesn't mention SMS / frequency / data sharing; 404 or auth-walled URL. |
| **Opt-in mechanism URL or screenshot** | Same as field #12 but a publicly hosted URL is strongly preferred for US 10DLC review. | Auth-walled flows; staging-only flows. |
| **Opt-out instructions (STOP / START)** | Configured via the **Opt Keywords** dashboard tab. | Configured per profile, not per brand — make sure the right profile is selected. |

## Country-specific extras

Selected countries require additional uploaded documents in the KYC stage. These are gated by the country selected during KYC, not by use case:

| Country | Extra docs |
|---|---|
| Australia (AU) | Utility Bill |
| Belgium (BE) | Proof of Local Address, Passport, Business Registration Certificate |
| Poland (PL) | Proof of Local Address |
| South Africa (ZA) | Proof of Local Address |
| Sweden (SE) | Proof of Local Address |
| Thailand (TH) | Proof of Worldwide Address, Business Registration Certificate |
| United Kingdom (UK) | Proof of Local Address |

## After the form is submitted

Sent's pre-flight runs `scripts/validate_10dlc_packet.py` against a JSON dump of these answers. Issues at this stage are cheap to fix — once filed with TCR a rejection costs days of round-trip. See `references/10dlc-rejection-remediation.md` for what to do when an account error code, TCR, or a carrier bounces a submission that passed pre-flight.
