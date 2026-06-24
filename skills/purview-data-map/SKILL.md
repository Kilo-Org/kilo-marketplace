---
name: "purview-data-map"
description: "Guidance for the Microsoft Purview Data Map - the foundation that scans and maps data sources across multicloud and on-premises estates to power cataloging and governance. Covers source registration, integration runtimes (managed vs self-hosted), scan rule sets, classifications, collections, and cost control. WHEN: Purview Data Map, scan data sources, register data source, data discovery, integration runtime, map enterprise data, multicloud data scanning, classification scan, collections, glossary."
metadata:
  category: data
  source:
    repository: "https://github.com/vinayaklatthe/microsoft-security-skills"
    path: "skills/purview-data-map"
    license_path: "LICENSE"
---

# Microsoft Purview Data Map

The Data Map is the foundational layer of Microsoft Purview data governance: it discovers, scans,
and maps metadata and classifications from data sources across Azure, multicloud, SaaS, and
on-premises - powering the Unified Catalog, lineage, and downstream protection decisions.

## When to use
Building an enterprise-wide inventory of data assets and their classifications as the basis for
governance, security, and data product publishing.

Do not use this skill for in-tenant Microsoft 365 classification (use `purview-data-classification`)
or for AI prompt visibility (use `purview-dspm-ai`).

## Pick the right integration runtime
| Source location | Use this runtime |
|---|---|
| Azure (Storage, SQL, Synapse, Fabric, Cosmos) | **Managed** (Azure-hosted) runtime |
| AWS S3 / RDS, GCP BigQuery, public SaaS | Managed runtime, with credentials in Key Vault |
| On-premises SQL, Oracle, file shares | **Self-hosted integration runtime (SHIR)** on a domain-joined Windows host |
| Private-endpoint-only Azure sources | SHIR or VNet-integrated managed runtime |
| Power BI tenant | Native connector, no runtime config |

Rule of thumb: managed runtime first; deploy SHIR only when network or private-endpoint reach
requires it - and treat the SHIR host as Tier-0 infrastructure.

## Approach
1. **Plan collections** - Design the collection hierarchy (by business domain or geography)
   before registering sources; collections drive RBAC and asset organisation.
   *Verify: a draft collection tree exists and maps to data-owner accountability.*
2. **Register sources** - Connect data sources (Azure Storage, SQL, Synapse, Fabric, AWS S3,
   databases, Power BI, etc.) into the right collection with appropriate credentials.
   *Verify: each registered source shows correct subscription/account and target collection.*
3. **Choose an integration runtime** - Use the **managed** runtime for cloud sources; deploy a
   **self-hosted integration runtime** to reach on-premises or private-network sources securely.
   *Verify: SHIR status is Running and self-update is enabled.*
4. **Configure scans and rule sets** - Schedule scans with scan rule sets; apply
   **classifications** (built-in SITs and custom) and lineage extraction where supported. Start
   incremental, not full.
   *Verify: scan history shows successful runs with classified assets counted.*
5. **Curate** - Review discovered assets, apply glossary terms, and assign data owners/stewards;
   tune custom classifications based on real matches.
   *Verify: top assets have owners and at least one glossary term.*
6. **Govern access** - Use collections to organise assets and scope permissions by domain;
   prefer collection-level role assignment over root.
   *Verify: collection-admin roles assigned to domain owners, not platform team only.*
7. **Operate** - Monitor scan failures, classification drift, and cost; right-size scan frequency
   per source criticality.
   *Verify: a weekly scan-health report exists.*

## Guardrails
- Scope and schedule scans to manage cost and source load; avoid scanning everything at full
  depth on day one - sampling first, full second.
- Secure the self-hosted integration runtime host as sensitive infrastructure - it holds
  credentials and reaches into production data sources; patch, restrict logon, monitor.
- Validate classification accuracy before relying on it for downstream protection - sample matches
  per SIT and tune confidence levels.
- Use Key Vault for credentials; never embed secrets in scan configuration.
- Plan capacity - Data Map is metered by capacity units; oversized scans inflate cost without
  governance value.

## Common anti-patterns
- Registering every source into the root collection and assigning everyone Data Reader.
- Scheduling weekly full scans on petabyte data lakes - blows out capacity and budget.
- Running SHIR on a workstation or shared jump host.
- Skipping the glossary and ownership step - assets get classified but nobody acts on them.
- Treating Data Map as a one-off load instead of a continuously curated catalogue.

## Example prompts
- `Register and scan data sources in the Purview Data Map.`
- `Configure an integration runtime for multicloud data scanning.`
- `How do I map enterprise data and run classification scans?`
- `Plan data discovery across cloud and on-prem sources.`
- `Design a Purview collection hierarchy aligned to business domains.`

## Microsoft Learn
- Data Map overview: https://learn.microsoft.com/purview/concept-elastic-data-map
- Register & scan sources: https://learn.microsoft.com/purview/scan-data-sources
- Manage integration runtimes: https://learn.microsoft.com/purview/manage-integration-runtimes
- Classifications: https://learn.microsoft.com/purview/concept-classification
- Collections & access control: https://learn.microsoft.com/purview/how-to-create-and-manage-collections
- Pricing & capacity: https://learn.microsoft.com/purview/concept-elastic-data-map
