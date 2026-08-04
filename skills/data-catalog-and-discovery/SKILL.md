---
name: data-catalog-and-discovery
description: >-
  Guides agents through data catalog, discovery, and metadata quality workflows.
  Use when publishing datasets, improving discoverability, curating lineage
  metadata, or making data products easier for other teams to find and trust.
metadata:
  category: data
  source:
    repository: 'https://github.com/vaquarkhan/data-engineering-agent-skills'
    path: skills/data-catalog-and-discovery
    license_path: LICENSE
    commit: 421ef57e8d42c464b29339193c18dd5bd2946bc2
---

# Data Catalog And Discovery

## Overview

Use this skill when the challenge is not only building data, but making it understandable and discoverable. It helps agents treat metadata, ownership, lineage, and usage context as delivery artifacts instead of afterthoughts.

## When to Use

- publishing a new shared dataset
- improving catalog metadata quality
- curating lineage, tags, or ownership information
- reducing duplicate datasets created because teams cannot find trusted ones

Do not stop at filling in a title and description. Discovery quality requires operational context too.

## Workflow

1. Define the discovery contract.
   Include:
   - owner
   - business description
   - technical description
   - grain
   - freshness expectation
   - intended consumers

2. Link the asset to its lineage.
   Show upstream sources, transformation layers, and major downstream uses where possible.

3. Add trust signals.
   Typical signals:
   - quality status
   - SLA or freshness status
   - certification or review state
   - deprecation state

4. Tag for real discovery, not taxonomy theater.

5. Revisit metadata when the contract changes.

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "The table name is descriptive enough." | Names alone do not explain grain, trust, or ownership. |
| "We can catalog it after people start using it." | Poor discovery usually leads to duplicate local copies first. |
| "Lineage is a platform problem, not a delivery problem." | Producers know the business meaning and must help make lineage useful. |

## Red Flags

- shared datasets have no owner or description
- certified and experimental assets are indistinguishable
- metadata is copied from schema names without business meaning
- deprecation state is absent for old assets

## Verification

- [ ] Ownership, description, grain, and freshness are documented
- [ ] Lineage or source context is attached
- [ ] Trust signals exist for consumers
- [ ] Discovery metadata is updated when the contract changes
