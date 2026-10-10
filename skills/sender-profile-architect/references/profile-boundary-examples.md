# Profile Boundary Examples — Reference

Supporting reference for `sender-profile-architect`. Worked examples for "where should the Sender Profile boundary go?" — the question that determines blast radius, billing granularity, and onboarding pain. Each example covers when the boundary makes sense, when it doesn't, ops considerations, and how the choice ripples into 10DLC registration and WABA setup.

The default rule of thumb: **one Sender Profile per legal entity per distinct sending identity**. The examples below are when to break that rule.

## What's confirmed in v3 (read before using the examples)

- **Auth.** A single account-level `x-api-key` operates on every profile the account owns. There is no per-profile API key in v3.
- **`x-sender-id`.** Visible per-profile in the dashboard (Profiles page maps to `/v3/profiles` endpoints), but is v2 legacy for routing; v3 needs only `x-api-key`. Treat it as a per-profile identifier you can read, not as the auth header.
- **Profile `status`.** The Sent-side enum is `incomplete | pending_review | approved | rejected`. Anything finer-grained ("partially_active", "restricted", "restoring") is an application-level label.
- **Org-level user roles.** Owner / Admin / Billing / Developer. Owner is the only role with billing-ownership transfer rights; the Profile resource's per-call `role` field surfaces `admin | billing | developer` (not Owner) for the authenticated user's role in that profile.
- **10DLC.** Brand and Campaign are first-class Sent resources at `/v3/brands` and `/v3/brands/{brandId}/campaigns` — register them before completing the SMS portion of a profile.

## 1. One profile per legal entity (single-brand SaaS)

A small SaaS with one corporate identity sending password resets, billing reminders, and product nudges from a single sender name.

**Picks this when:** all messages legitimately come from the same business, same brand voice, same vetting story.

**Doesn't pick this when:** the company runs multiple consumer brands under one corporate parent (those want separate profiles even if the same lawyer signs both TCR forms).

**Ops:**
- One webhook, one secret to rotate, one set of API keys. Lowest operational overhead.
- Single TCR Brand registration; multiple TCR Campaigns under it for distinct use cases (transactional vs marketing).
- Single WABA, one System User token. WABA quality rating reflects all sending behavior.
- Billing is a single line item — easy for finance, hard to attribute internally if multiple product teams share the profile.

**10DLC:** one Brand, multiple Campaigns. If transactional and marketing share one Campaign, carrier filtering will be harsher than necessary — split them.

**WABA:** one WABA, one phone number to start; tier upgrades benefit everything sent through this profile.

## 2. One profile per channel (WhatsApp-only vs SMS-fallback chains)

A tenant explicitly wants channel isolation — e.g. a WhatsApp-only consumer brand whose ops team should never accidentally send SMS, or a region where RCS is the primary channel with SMS strictly as fallback.

**Picks this when:** legal, compliance, or product policy requires that channel-by-channel sending be controllable independently and visible independently in billing.

**Doesn't pick this when:** the channels are genuinely interchangeable for the same user journey. Sent's whole point is unifying sending — splitting profiles by channel often duplicates work without adding isolation.

**Ops:**
- Multiple webhook subscriptions, multiple secrets. Secret-rotation blast radius is smaller per channel, larger in aggregate.
- The "fallback" pattern (try WhatsApp, fall back to SMS) becomes an application-level orchestration across two profiles instead of one. Manageable, but inbound replies on the SMS profile won't carry the original WhatsApp `wamid` context — your app has to stitch threads.
- Cost tracking is cleanly per-channel.

**10DLC:** the SMS-only profile carries the TCR registration; the WhatsApp-only profile has none. Don't register TCR for a profile that won't send SMS.

**WABA:** the WhatsApp profile carries the WABA. Quality scoring is isolated — a bad SMS campaign won't pull WhatsApp tier down.

## 3. Per-department profiles (sales, support, marketing) on the same brand

A mid-sized company wants Sales, Support, and Marketing to send under the same overall brand but with different sender names, different vetting stories, and different billing meters.

**Picks this when:** internal billing attribution matters (Marketing's budget is separate from Support's), or each department's send volume / patterns are different enough that mixing them would hurt vetting (Marketing's bulk sends would tank Support's quality rating).

**Doesn't pick this when:** the departments truly send identical-looking traffic under one external brand. Splitting buys complexity without changing what carriers see.

**Ops:**
- Three webhooks (or one webhook routing on `payload` fields), three sets of templates — but one shared account-level `x-api-key`. Reusable copy (e.g. WhatsApp templates) has to be authored per profile or copied between them.
- Quota / rate-limit accounting is per profile — Marketing can be throttled without affecting Support.
- Suspension blast radius is per profile — a Meta quality drop on Marketing doesn't pause Support.

**10DLC:** typically one TCR Brand (same legal entity) but separate Campaigns per department's use case. Some tenants register multiple Brands if Marketing operates as a distinct legal entity.

**WABA:** can be one WABA with multiple phone numbers split across profiles, or one WABA per profile. One-WABA-multiple-profiles complicates Sent-side modeling (each profile attaches to the same WABA); separate WABAs are cleaner if the departments genuinely want isolation.

## 4. Per-tenant profile in a B2B2C platform (one Sent customer hosting many merchants)

A platform — appointment-booking SaaS, e-commerce host, marketing platform — has one Sent contract but serves hundreds of downstream merchants who each need their own sender identity.

**Picks this when:** each merchant is a distinct end-business that needs to appear as themselves to recipients, comply with TCR / Meta independently, and have their own billing meter.

**Doesn't pick this when:** all merchants legitimately send "from" the platform brand. Then one profile is correct and merchant attribution is an internal concern.

**Ops:**
- Profile provisioning is part of the merchant onboarding flow — this is where the WABA Embedded Signup (`waba-embedded-signup`) and 10DLC registration (`sms-10dlc-registration`) skills get invoked hundreds of times.
- Webhook fan-in: one Sent webhook per profile is unmanageable at hundreds of profiles. Either configure all profiles to one webhook URL and route on payload fields (`payload.account_id`, `payload.outbound_number`, `payload.template_id`, plus a `message_id`-to-profile map you keep at send time), or run per-profile webhooks behind a routing layer. The single-URL pattern has one secret to rotate and a larger blast radius.
- API-key blast radius: v3 issues a single account-level `x-api-key`, so a compromised key affects every merchant under that account. If per-merchant key isolation is a requirement, give each merchant its own Sent customer account (not just its own profile) — that's the only boundary that produces a distinct API key today.
- Billing: per-merchant meters fall out of per-profile accounting cleanly.

**10DLC:** each merchant is its own TCR Brand and Campaign. The platform does not register *its own* Brand on behalf of merchants — the merchant signs. Plan for per-merchant TCR vetting time (days, not seconds).

**WABA:** each merchant goes through Embedded Signup to attach their own WABA. The platform is the Tech Provider on Meta's side. Plan for the support burden — Meta's "phone number already in use" errors land on the platform.

## 5. Per-region / per-geo profiles

A business serving multiple regions wants to honor local regulations, language defaults, and regulator-specific sender identities (e.g. EU brand vs US brand vs LATAM brand).

**Picks this when:** regions have genuinely different regulators (US 10DLC + Brazil's regs + EU's WhatsApp rules), different timezones for send-window enforcement, or different localized sender display names.

**Doesn't pick this when:** the regional split is only a marketing convenience and all sending is from one legal entity with one global compliance posture.

**Ops:**
- Per-region webhooks make per-region failover and on-call rotation straightforward.
- Per-region rate limits avoid one region's burst exhausting another's budget.
- Per-region secret rotation contains blast radius geographically.
- Cross-region analytics need a join layer — the per-profile billing/usage data has to be aggregated for the global view.

**10DLC:** US-only concept. The US-region profile is the one with TCR; non-US profiles ignore TCR entirely. Don't try to register a non-US brand with TCR "for completeness".

**WABA:** WABAs can serve global recipients, but pricing tiers and template approval workflows differ by recipient country, not by WABA region. Per-region WABAs typically map to per-region Meta Business Manager assets and per-region System User tokens — that's the operational reason to split, not regulatory.

## Decision heuristic

When you're not sure whether to split, ask in order:

1. **Are these messages legally from the same entity?** No → split.
2. **Will one identity's bad behavior unfairly impact another's quality rating / TCR vetting?** Yes → split.
3. **Does anyone need to see per-X billing or rate limiting (X = brand, department, merchant, region)?** Yes → split.
4. **Do these channels actually share a user journey or are they being kept apart for ops reasons?** Kept apart → split.
5. **Otherwise:** one profile. Splits are cheap to add later; merges are not.
