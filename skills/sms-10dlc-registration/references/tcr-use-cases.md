# TCR Use Cases & Vetting — Reference

Supporting reference for `sms-10dlc-registration`. The Campaign Registry's use-case taxonomy and the practical effect of each choice on throughput and carrier filtering. The canonical list is on the [TCR website](https://www.campaignregistry.com/) — use this doc for the *interpretation* in a multi-tenant Sent deployment.

## Sent's compliance-form taxonomy (verified)

Sent's compliance form exposes a **five-option** use-case selector to the tenant, not the full TCR taxonomy. Pick one of these on the form:

| Sent compliance-form option | Typical underlying TCR use case(s) |
|---|---|
| **Authentication** | `2FA` |
| **Notifications** | `ACCOUNT_NOTIFICATION`, `DELIVERY_NOTIFICATION`, `FRAUD_ALERT`, `SECURITY_ALERT`, `PUBLIC_SERVICE_ANNOUNCEMENT` |
| **Marketing** | `MARKETING` |
| **Customer Service** | `CUSTOMER_CARE` |
| **High Volume** | `MIXED` / high-throughput senders (Sent maps internally) |

Sent files the TCR-side payload on the tenant's behalf — the deeper TCR taxonomy below is for interpreting that mapping and reasoning about why a use-case selection might trigger more or less filtering. The tenant only sees and chooses one of the five form values.

## TCR use cases sorted by throughput & filtering risk (external interpretation)

| Use case | Typical TPS (post-vetting) | Filtering risk | When to pick |
|---|---|---|---|
| `2FA` | Highest | Lowest | Codes only. No promotional content. |
| `ACCOUNT_NOTIFICATION` | High | Low | Order, shipping, appointment, payment, security notifications. Triggered by the recipient's action. |
| `CUSTOMER_CARE` | Medium-high | Low | Two-way support replies. Mostly inbound-driven. |
| `DELIVERY_NOTIFICATION` | High | Low | Specialized variant of ACCOUNT_NOTIFICATION for couriers. |
| `FRAUD_ALERT` | High | Low | Account-security alerts and fraud confirmations. |
| `HIGHER_EDUCATION` | Medium | Medium | School-affiliated communications. Required for many edu senders. |
| `LOW_VOLUME` | Low | Low | Pilots, internal tools, < 6,000 messages/day. |
| `MARKETING` | Medium | High | Promo, discount, win-back. Highest review bar; opt-in must be airtight. |
| `MIXED` | Medium | High | Last resort. Raises the bar without raising throughput. |
| `POLITICAL` | Medium | High | Political campaigns (US). Regulated category. |
| `POLLING_VOTING` | Medium | Medium | Surveys, polls, non-political voting. |
| `PUBLIC_SERVICE_ANNOUNCEMENT` | Medium | Low | Non-profit / government PSAs. |
| `SECURITY_ALERT` | High | Low | Specialized variant of FRAUD_ALERT for non-financial security. |
| `SOCIAL` | Medium | Medium | Person-to-person-feeling but business-sent (matchmaking, social apps). |

Specific TPS numbers and vetting-score-to-throughput thresholds are **external** — Sent's docs only confirm the tier-level account-wide rate caps (Starter 60 msg/min, Growth 300 msg/min, Enterprise custom), not TCR / carrier per-campaign throughput.

## Brand external vetting (external context)

Brands can submit for **External Vetting** via TCR-approved vetting providers. This produces a `vettingScore` that:

- Unlocks higher per-campaign TPS caps from each carrier.
- Reduces the filtering aggressiveness applied to the campaign's traffic.
- Cannot be inherited from another brand — every brand vets independently.

The exact vetting-score-to-throughput mapping is set by each carrier and not exposed in Sent's docs. Treat as external (TCR + carrier docs).

## Required campaign attributes (TCR-side, external)

Every TCR campaign declares these. They're not directly user-visible on Sent's compliance form, but Sent files them from the form data plus dashboard configuration:

- **Subscriber opt-in** — How recipients agreed to receive these messages. Captured on Sent's compliance form as the **opt-in mechanism URL or description**.
- **Opt-out keywords** — Minimum `STOP`. Managed on Sent in the **Compliance → Opt Keywords** tab; not embedded per sample message.
- **Help keywords** — Minimum `HELP`. Reply should describe what the campaign is and how to opt out.
- **Embedded link** — Whether your messages include URLs (`yes` / `no`).
- **Embedded phone** — Whether your messages include phone numbers (`yes` / `no`).
- **Affiliate marketing** — Whether the campaign promotes affiliate offers (`yes` / `no`). `yes` is heavily scrutinized.
- **Age-gated content** — Alcohol, gambling, firearms, tobacco. `yes` requires age verification at opt-in.
- **Direct lending** — Whether the campaign is for direct loans. Subject to additional review.

## Sample messages

TCR requires 2-5 sample messages per campaign. Carrier filters use these to validate live traffic. Mismatches between samples and production are the most common reason for downgrade.

Good sample:
> {Brand Name}: Your order #1029 has shipped. Track: https://example.com/track/1029.

Bad sample (don't do):
> Your order has shipped!

Bad because: no brand name, no link/tracking specifics that mirror production.

Note: Opt-out language (`Reply STOP to opt out.`) is conventional in samples and many carriers expect to see it, but the **rule** that every Sent-filed sample must literally embed `STOP` is not confirmed in Sent's docs — Sent treats opt-out as a separate field on the compliance form (Opt Keywords tab) rather than embedded in each sample. Sample-level opt-out is good carrier hygiene; the Sent-required field lives elsewhere.

## Per-carrier filtering notes (external)

TCR-approved doesn't mean delivered. Each major US carrier filters independently:

- **T-Mobile** — Most aggressive. Strict on URL shorteners (use a branded short-link domain on your verified domains, not generic `bit.ly`).
- **AT&T** — Stricter on message-volume spikes than on content. Pace sends.
- **Verizon** — More content-sensitive on `MARKETING` and `MIXED`. Promotional content in an `ACCOUNT_NOTIFICATION` campaign gets caught here first.

Track per-carrier delivery in the MDR funnel and reconcile per-carrier approval state on the campaign daily. Specific carrier rejection codes are external (Twilio / Bandwidth / Sinch / direct-aggregator docs).

## Common rejection reasons (external taxonomy)

| Reason | What it means | Fix |
|---|---|---|
| `Use case mismatch` | Sample messages don't fit the declared use case | Re-classify campaign or rewrite samples |
| `Missing opt-out language` | Samples don't include STOP / HELP language | Add it everywhere |
| `Brand name not in sender ID` | Recipient can't see who's texting | Add `{Brand Name}:` prefix to messages |
| `Affiliate disclosed = no, content suggests affiliate` | Lied on the attribute | Declare honestly |
| `Embedded link not declared` | Samples have links, attribute says no | Update the attribute |
| `Insufficient vetting score for requested TPS` | Vetting too low for the throughput tier | Re-vet at a higher tier, or accept lower TPS |
