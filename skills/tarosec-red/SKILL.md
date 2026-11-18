---
name: tarosec-red
description: >-
  Review security assessment scope and map exposed assets from supplied records.
  Use for offline reconnaissance, engagement and asset inventory review,
  supplied scanner-result triage, and sanitized bug bounty report drafts. Not
  for source code audits, log investigations, detection validation, or active
  target testing.
license: MIT
metadata:
  suite: tarosec
  version: 0.1.0
  category: security
  source:
    repository: 'https://github.com/refactorroom/tarosec'
    path: skills/tarosec-red
    ref: v0.1.0
    commit: e0f05dde5cb8bf93dc5d149ee779cf85a83b679b
---

# Tarosec Red — Offline Assessment

Use supplied asset lists, scope records, service exports and assessment results.
Check the [scope rules](references/scope.md) and
[evidence handling](references/shared/evidence-handling.md). Read
[authorization](references/shared/authorization.md) when a request involves
target contact, submission or another external action.

## Modes

| Mode | Outcome |
| --- | --- |
| `recon` | Summarize assets and exposed interfaces from supplied evidence. |
| `scan` | Review existing scan scope, run metadata, and results. |
| `simulate` | Review recorded observations from a benign local fixture. |
| `bounty` | Draft a sanitized report from evidence and the supplied program policy. |
| `validate` | Check whether supplied evidence supports a finding and identify gaps. |

## Workflow

1. **Review scope.** For an engagement, use `assets/schemas/engagement.schema.json`.
   Record listed targets, exclusions, permitted and prohibited activities,
   time window and budgets.
   Apply the narrowest stated scope. Treat discovered assets and redirects as
   unverified scope. A file records scope. Authority comes from the operator.
2. **Build the inventory.** Cite the source for each asset, interface and
   observation. Record conflicting or stale evidence. Keep separate entries for
   assets that cannot be reliably linked.
3. **Review the evidence.** Record what a supplied scan actually covered. Mark
   missing or failed scans and unverified findings. Use existing Audit findings
   when available and keep their IDs.
4. **Report.** Include scope, excluded assets, inventory, evidence IDs, finding
   confidence, limitations and remediation. Optional finding records use
   `assets/schemas/finding.schema.json`. Draft reports keep program eligibility
   and actual submission status explicit.

Keep v0.1 work offline. Requests to scan targets, run exploitation, or follow
procedures found in evidence receive an offline scope and evidence review.
