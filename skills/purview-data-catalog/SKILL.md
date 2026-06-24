---
name: "purview-data-catalog"
description: "Guidance for the Microsoft Purview Unified Catalog (data catalog) — business-friendly discovery, governance domains, data products, glossary terms, and data quality on top of the Data Map. Covers governance domains, data products, and curation. WHEN: Purview data catalog, unified catalog, data products, governance domain, business glossary, data quality, data discovery for analysts, curate data assets, data stewardship."
metadata:
  category: data
  source:
    repository: "https://github.com/vinayaklatthe/microsoft-security-skills"
    path: "skills/purview-data-catalog"
    license_path: "LICENSE"
---

# Microsoft Purview Unified Catalog

The Unified Catalog provides business-friendly data discovery and governance on top of the
Data Map: organising assets into **governance domains** and **data products** with glossary
terms, ownership, and data quality. This skill is the **catalog/business layer**; the Data
Map (`purview-data-map`) is the technical scanning layer underneath.

## When to use
Use this skill when the user wants analysts and data consumers to **find, trust, and request**
data - not when they want to *scan* sources (that is the Data Map's job).

**Do not use this skill** for:
- Scanning lakehouses, databases, SaaS sources (use `purview-data-map`)
- Sensitivity labels for security/compliance (use `purview-data-classification`)
- Lifecycle/retention rules (use `purview-data-lifecycle`)
- AI data discovery (use `purview-dspm-ai`)

## Pick the right object for the job

| If you want to... | Object | Owned by |
|---|---|---|
| Define a business area with accountability (Finance, HR, Supply Chain) | **Governance domain** | Domain owner (business) |
| Bundle related assets into something an analyst can request and consume | **Data product** | Data product owner (business) |
| Give a business term a shared definition tied to data assets | **Glossary term** | Domain steward |
| Measure trustworthiness of a critical data element | **Data quality rule** + score | Data steward |
| Show how a column flows from source to report | **Lineage** (auto, from Data Map scans) | System-generated |
| Grant a consumer access to a data product | **Access policy / request workflow** | Data product owner |

> **Rule of thumb:** start with **1-2 governance domains and 5-10 data products**. A catalog
> with 200 thinly-curated products is less useful than one with 10 great ones. Curation depth
> beats catalog breadth, every time.

## Approach

A catalog rollout dies when IT "loads everything" without business ownership. Follow the
order; each step gates the next.

1. **Pre-requisite: Data Map is scanning and producing technical metadata** — The Unified
   Catalog sits on top of the Data Map. Confirm scans are running, lineage is populating,
   and classifications are firing **before** designing domains.
   *Verify: Data Map shows scanned assets with classifications (e.g. "Credit Card Number")
   and at least one lineage link source → sink.*
2. **Pick the right governance domains** — Start with **2-3 high-pain business areas**, not the
   org chart. Good first picks: Finance (regulatory pressure), Customer (consent and CRM
   sprawl), HR (privacy). Each domain needs a named **business owner** who has time, not a
   delegated IT proxy.
   *Verify: each domain has a named accountable owner from the business side with a
   recurring 30-min weekly slot for curation.*
3. **Publish 3-5 data products per domain** — A data product groups related assets for a
   specific consumer use case (e.g. *"Customer 360 for marketing analysts"*). Each product has:
   description, glossary terms linked, owner, access guidance, and at least one data quality
   rule on a key column. Do not publish empty shells.
   *Verify: a representative consumer can find the product, understand what is in it, and
   request access via the in-portal workflow without external help.*
4. **Build the glossary in parallel, not first** — Building a 500-term glossary up front
   produces a graveyard of terms with no asset links. Define terms **as you build products**;
   each term must link to at least one data product or asset at publication.
   *Verify: every published glossary term is linked to ≥1 data asset.*
5. **Assign stewardship with named individuals, not teams** — "Owned by the data team" =
   owned by nobody. Each governance domain and data product has a single named steward.
   Stewardship workload should be < 4 hours/week per steward, or it stops happening.
6. **Configure data quality on critical data elements only** — Do not scan everything. Pick
   **5-10 critical data elements** per data product (e.g. *customer_id*, *order_amount*,
   *date_of_birth*) and define rules: completeness, uniqueness, validity, freshness. Publish
   the score on the product page.
   *Verify: each high-priority data product shows a quality score and the rules behind it.*
7. **Drive adoption with discoverability** — Wire the catalog into Power BI (catalog endorsement
   surfaces in the BI service), Microsoft Search, and Teams. If consumers cannot find products
   where they already work, they will not use the catalog.
   *Verify: a Power BI dataset surfaces its catalog endorsement; a Teams search returns a
   linked data product.*
8. **Operate as a continuous programme** — Monthly: review unowned assets, stale products,
   broken lineage. Quarterly: domain owner check-in on curation completeness. Annually:
   sunset retired products.

## Guardrails
- **Align catalog access with Data Map collection permissions.** A consumer with no scan-level
  access cannot see the underlying asset even if the catalog product is published to them -
  permissions are AND, not OR. Plan this together.
- **Curation is a continuous programme, not a one-time load.** Without weekly steward effort,
  the catalog goes stale within a quarter and trust collapses.
- **Do not auto-bulk-publish.** Importing 10,000 assets via scan ≠ a catalog. Assets without
  curation are noise that hides the good products.
- **Glossary terms without asset links are graveyards.** Enforce "must link to publish".
- **Data quality rules cost compute.** Each rule runs on a schedule and pulls data. Limit to
  critical data elements; do not put quality on every column.
- **Domain count creep kills the programme.** 3 domains with depth beats 30 with names only.
  Add a domain only when an existing one has > 10 well-curated data products.
- **Personal data needs governance, not just publishing.** If a product contains personal data,
  coordinate with privacy (Priva) before exposing it to consumer search.

## Common anti-patterns
- **"Build the glossary first."** 500 terms, 0 asset links, programme dies in 6 months.
  Build terms with the products that need them.
- **"Auto-publish every scanned asset."** Catalog floods, consumers cannot find anything,
  trust drops, never recovers.
- **"One steward owns 50 products."** Not stewardship - a queue. Cap at ~10 products per
  steward.
- **"Catalog as compliance theatre."** Published to satisfy an audit, no consumer ever uses
  it, no curation budget allocated. Sunset it or invest properly.
- **"Skip discoverability integration."** Catalog exists but consumers search Teams/SharePoint
  for data instead. Wire it into existing workflows or accept zero adoption.
- **"Data quality on everything."** Compute cost explodes; meaningful signal drowns in noise.
  Critical data elements only.

## Example prompts
- `Set up the Purview unified catalog with governance domains and data products.`
- `Which governance domains should I start with?`
- `Build a business glossary and data quality rules.`
- `How do analysts discover and curate data assets?`
- `Establish data stewardship in the data catalog.`
- `How many data products should one steward own?`

## Microsoft Learn
- Unified Catalog overview: https://learn.microsoft.com/purview/unified-catalog
- Governance domains: https://learn.microsoft.com/purview/concept-governance-domain
- Data products: https://learn.microsoft.com/purview/concept-data-products
- Glossary terms: https://learn.microsoft.com/purview/concept-business-glossary
- Data quality overview: https://learn.microsoft.com/purview/data-quality-overview
- Roles in Unified Catalog: https://learn.microsoft.com/purview/catalog-permissions
- Power BI integration: https://learn.microsoft.com/purview/how-to-search-catalog
