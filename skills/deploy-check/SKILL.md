---
name: deploy-check
description: >-
  Assess a proposed deploy using its diff, review and test evidence, rollout
  safeguards, and Rootly incident context. Recommend GO, CAUTION, or NO-GO with
  reasons; use before deploying a branch, PR, release, or configuration change,
  without executing it.
metadata:
  author: Rootly
  version: 3.0.0
  category: development
  access: read
  short-description: Assess deployment risk and explain the recommendation
  source:
    repository: 'https://github.com/rootlyhq/agent-skills'
    path: skills/deploy-check
    ref: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    commit: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    license_path: LICENSE
---

# Deploy check

## Purpose

Help an engineer decide whether a proposed change has adequate evidence to ship.
Keep operational staffing warnings separate from the technical recommendation.

First read [common rules](references/common.md), including for assessments based
entirely on supplied facts. Then follow the workflow below.
Before drafting the assessment, read the
[evidence guidance](references/evidence.md) and apply its final evidence check
to the table, reasoning, questions, and recommendations.

## Use when / not when

- Use for a proposed deploy, PR, branch diff, release, or config/flag change.
- Use incident-response for mitigation during an active outage.
- This is a recommendation, not release approval or a deployment executor.

## Inputs

Identify the proposed artifact, base/target, target environment, mapped services,
and customer release policy from the supplied or retrieved evidence. An
unspecified environment stays unknown; scope the assessment to the supplied
checks without assuming a target. Clarify it before a real environment-specific
decision needs that identity.
Use [tools](references/tools.md) to check incidents. Clarify an ambiguous target
or service mapping before issuing a service-specific verdict.

## Jobs

1. Inspect scope across services/dependencies, diff size, major upgrades, review
   comments, human approvals, CI failures, pre-production results, rollout
   breadth, and feature flag/canary/rollback safeguards. Report AI-authored scope
   only when provenance is supplied; never guess it from code style.
2. Check active and monitoring incidents on affected services, recent incidents
   involving the same feature/dependencies/vendor, concurrent major upgrades to
   shared infrastructure, and an active change freeze. Include upgrades outside
   the proposed diff when they affect the same service or its dependencies.
3. Apply the customer's release policy. In its absence, state these defaults:
   known failing required tests, no human review, an open incident on the same
   service, or a freeze support NO-GO. A relevant major upgrade (in the change or
   concurrent shared infrastructure), a broad diff, no pre-prod
   run, related recent failures, or all-environment rollout support CAUTION.
   Clean pre-prod, human review, and a canary/flag with verified rollback support GO
   only when required checks are complete and no blocking factor remains.
4. Unknown test/review/freeze/incident state is not a passed check. Use
   "assessment incomplete" with missing evidence rather than manufacture GO.
   A known blocker still supports NO-GO even when optional context is missing.
   Favorable factors do not cancel a blocker. Customer-approved emergency fixes
   may follow a documented exception path; do not authorize the exception.
5. Add a separate staffing warning for relevant pages in the last 60 minutes or
   a handoff in the next 60 minutes. Cite counts, priorities, window, handoff time,
   and next responder when known. These signals do not change GO/CAUTION/NO-GO.
   Use [responder judgment](references/responder-judgment.md): duplicate,
   low-priority pages do not establish overload or fatigue; say so when relevant.
   Deduplicate warnings already acknowledged for this deploy; repeat only when
   materially changed. Avoid generic warnings or old page counts. Respect
   customer-defined windows and explain any departure from this default.

## Repo leg

Inspect the requested branch/PR/release diff, including committed changes when
the working tree is clean. Do not stop merely because there are no uncommitted
files. Use deployment and CI evidence to distinguish commits from releases.
If the artifact cannot be inspected, report an incomplete assessment rather than
assessing an unrelated diff. Never run the deployment or modify the checkout.

## Data honesty

Missing Rootly access is not a clean incident history. A timeout in optional
on-call enrichment does not become a
technical blocker; report the missing staffing information separately.
Diff size is context, not a universal line-count rule or evidence of poor quality.

## Output

Read [the deploy assessment](references/output.md) and return exactly this shape:
Start the final answer with the verdict and end with the exact non-action
sentence below. The lead names only the deciding evidence and applicable rule;
do not add a safety assessment of the patch. Do not add a preamble, recap,
closing offer, or text after it.

```
**Verdict: GO | CAUTION | NO-GO | INCOMPLETE.** One sentence with the deciding evidence ID.

| Check | Finding | Source |
|---|---|---|
| Artifact / Base and target / Environment / Mapped services / Review and CI /
  Pre-production / Rollout safeguards / Incidents / Release policy /
  Concurrent changes / Staffing (one row each, in this order) | ... | ID or — |

**Inferences, not evidence**
**Unresolved checks**
**What would change the verdict**
I did not deploy, approve, roll back, or notify anyone.
```

Each finding restates its cited source. Unstated identities are `unknown`;
missing evidence is `not supplied` with source `—`. Reasoning beyond the
evidence, including why a factor matters, goes only under **Inferences, not
evidence**, using "If ... could/would ..." for each bullet. Before handing it over, check each row
against its source and remove any window, environment, number or capability the
source does not state. See [the worked example](references/example.md).
For a gap, recommend what to confirm. Do not write that a source "only says",
"does not show", or "gives no" detail unless the supplied evidence establishes
that absence in the full record. A source ID does not make a summary complete.

## Writes

Do not deploy, roll back, toggle flags, approve a PR, bypass a freeze, change
incident state, or contact a responder. A recommendation is not authorization.

## Routes

Use incident-response for an incident found during the check, or on-call for
coverage planning, when installed and relevant to the user's request.
