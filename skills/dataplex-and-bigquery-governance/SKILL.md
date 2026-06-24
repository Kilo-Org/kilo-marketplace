---
name: "dataplex-and-bigquery-governance"
description: "Guides agents through GCP-native data governance workflows with Dataplex and BigQuery. Use when designing lakes, zones, policy tags, metadata quality, lineage, discovery, and governed publishing across Cloud Storage, BigQuery, Dataflow, Dataproc, and Google Cloud analytics platforms."
metadata:
  category: data
  source:
    repository: "https://github.com/vaquarkhan/data-engineering-agent-skills"
    path: "skills/dataplex-and-bigquery-governance"
    license_path: "LICENSE"
---

# Dataplex And BigQuery Governance

## Overview

Use this skill when governance on `GCP` is centered on `Dataplex`, `BigQuery`, and related Google Cloud metadata controls. It helps agents define governance zones, policy-tag boundaries, lineage expectations, and trusted publishing patterns for warehouse and lake platforms.

## When to Use

- designing `Dataplex` lakes, zones, or governance domains
- defining `BigQuery` policy tags and governed publish boundaries
- improving metadata quality, lineage, and discovery on `GCP`
- aligning warehouse and lake governance across `Cloud Storage`, `BigQuery`, `Dataflow`, and `Dataproc`
- making governed analytics delivery work with regional or regulated-data controls

Do not treat `BigQuery` governance as only a permissions problem. Trusted publishing also needs metadata, ownership, and policy boundaries.

## Workflow

1. Define the governance boundary.
   Decide:
   - lakes and zones
   - datasets and domains
   - producer versus consumer boundaries
   - ownership expectations

2. Define metadata and policy controls.
   Include:
   - policy tags
   - classifications
   - lineage coverage
   - discovery metadata
   - trusted versus exploratory asset signaling

3. Align lake and warehouse governance.
   Make explicit how `Cloud Storage`, `BigQuery`, and processing services fit the same control model.

4. Design governed publish behavior.
   Require:
   - clear serving boundaries
   - ownership visibility
   - release or validation evidence where needed
   - rules for schema and policy change

5. Validate day-2 operations.
   Review whether onboarding, schema evolution, and new domains remain manageable under the governance model.

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "Policy tags are the whole governance design." | Tags help, but they do not replace ownership, zone design, trusted publishing, or metadata quality. |
| "Dataplex is only for lake governance." | Many teams need a joined governance model across storage, warehouse, and processing surfaces. |
| "Discovery will happen automatically once assets are scanned." | Useful discovery requires curated metadata and trust signals. |

## Red Flags

- lake, dataset, and domain boundaries are inconsistent
- policy tags exist without ownership or publish context
- warehouse and lake governance behave differently with no clear rule
- certification or trusted-asset behavior is missing
- schema and policy changes are operationally unclear

## Verification

- [ ] Governance boundaries are explicit across lake and warehouse surfaces
- [ ] Policy tags, metadata, and lineage expectations are defined
- [ ] Publish behavior is governed and reviewable
- [ ] Ownership and discovery expectations are visible
- [ ] Day-2 operations fit the governance design
