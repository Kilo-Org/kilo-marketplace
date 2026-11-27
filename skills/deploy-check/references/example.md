# Worked example: staffing warning stays separate

Synthetic fixture at 14:00 UTC.

## Available evidence

- R0: Release request for PR-42 to checkout production.
- P1: The team's policy requires passing CI, a human approval, pre-prod validation,
  and no open incident/freeze. A second approval and canary are favorable signals.
- C1: PR-42 is a narrow reviewed change; two human approvals cover the current revision.
- T1: Required CI checks passed on that revision.
- D1: That artifact passed pre-prod. Canary with automated rollback was verified.
- I1: Complete authorized query shows no active/monitoring checkout incident at 13:59.
- F1: Current release policy/calendar shows no change freeze.
- S1: The outgoing responder hands off to the incoming responder at 14:20.
- W1: Twelve low-priority duplicate alerts fired in the last hour; no active incident
  is assigned to the outgoing responder. They have not stated they are overloaded.

## Example assessment

**Verdict: GO.** Every gate in P1 is met by C1, T1, D1, I1 and F1.

| Check | Finding | Source |
|---|---|---|
| Artifact | PR-42, a narrow reviewed change | R0, C1 |
| Base and target | unknown | — |
| Environment | production | R0 |
| Mapped services | checkout | R0 |
| Review and CI | Two human approvals and passing required CI on the current revision | C1, T1 |
| Pre-production | Passed | D1 |
| Rollout safeguards | Canary with automated rollback, verified | D1 |
| Incidents | No active or monitoring checkout incident at 13:59 | I1 |
| Release policy | No change freeze; P1 gates apply | F1, P1 |
| Concurrent changes | not supplied | — |
| Staffing | Handoff at 14:20; twelve low-priority duplicate alerts in the last hour, none assigned as an active incident | S1, W1 |

**Inferences, not evidence**
- Page count alone does not establish that the outgoing responder is overloaded.
- If the rollout overlaps the 14:20 handoff, the observer could change mid-rollout.

**Unresolved checks**
- Base and target revisions.
- Concurrent shared-infrastructure changes for the deploy window.
- Who observes the rollout; confirm through the team's usual process.

**What would change the verdict**
- A failing required check in T1 would make this NO-GO, even with the canary.
- Unavailable CI or incident evidence would make this INCOMPLETE.
- A concurrent major upgrade of a checkout dependency would make this CAUTION.

I did not deploy, approve, roll back, or notify anyone.

The staffing warning stays in its row. It does not change GO to CAUTION.

## Counterexamples

- If T1 instead shows a failing required test, recommend NO-GO even with the canary.
- If CI or incident evidence is unavailable, label the assessment incomplete;
  do not preserve GO by treating an unavailable check as passed.
