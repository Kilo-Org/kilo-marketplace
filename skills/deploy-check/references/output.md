# Deploy assessment

Return exactly the sections below, in this order, and nothing else. The table
holds what the evidence says. Everything you reason beyond the evidence goes in
**Inferences, not evidence**. These are recommendations, not permission to deploy.
The final answer begins with the verdict line and ends at the exact non-action
sentence. Include the contract once, with no introductory prose, recap, or
closing offer. Keep any explanation inside the named sections.

```
**Verdict: GO | CAUTION | NO-GO | INCOMPLETE.** One sentence naming the deciding factor and its evidence ID.

| Check | Finding | Source |
|---|---|---|
| Artifact | ... | ... |
| Base and target | ... | ... |
| Environment | ... | ... |
| Mapped services | ... | ... |
| Review and CI | ... | ... |
| Pre-production | ... | ... |
| Rollout safeguards | ... | ... |
| Incidents | ... | ... |
| Release policy | ... | ... |
| Concurrent changes | ... | ... |
| Staffing | ... | ... |

**Inferences, not evidence**
- If [unverified condition], [possible operational consequence or recommendation].
  Use this conditional form for each useful inference, or write "None."
  Do not repeat evidence, inventory missing details, or speculate to fill this section.

**Unresolved checks**
- Recommended checks to resolve missing evidence or identities. Or "None."
  Write each as an action or question, such as "Confirm the target environment."
  Do not add a narrative about what an unseen record contains or omits.

**What would change the verdict**
- Specific evidence and the verdict it would produce.

I did not deploy, approve, roll back, or notify anyone.
```

## Table rules

- Keep all eleven rows, in this order, even when the evidence is silent.
- **Source** holds the evidence identifier as supplied (R1, P2), or the tool and
  record it came from. Use `—` only when the finding is `unknown` or
  `not supplied`.
- **Finding** restates its source. Do not add an environment, window, duration,
  time, count, owner or capability the source does not state. Any number in a
  finding must appear in its cited source.
- An unspecified environment, base or target is `unknown`. Never fill it from
  convention or from the rollout style.
- Missing incident data does not establish no incident; write `not supplied`.
- Preserve the scope of negative evidence everywhere, including the verdict:
  no concurrent shared-infrastructure upgrade does not mean no concurrent change
  or no dependency risk. Unknown identities must stay unknown in recommendations
  too; do not presuppose production when asking what remains to be confirmed.
- **Staffing** is reported separately and never changes the technical verdict.
  Restate the supplied staffing evidence. If that material includes no window,
  add the literal phrase "window not stated" in that row without paraphrasing it;
  this describes the supplied material,
  not the contents of an unseen full record. Never supply the window yourself
  or infer that the responder's full record is unscoped.

## Verdict rules

The lead names only the deciding observed factor, its source and the applicable
policy or stated default. Do not add a summary calling the patch low-risk, safe,
isolated or harmless. Small size, label-only scope, approvals and passing checks
are observations, not risk assessments. Attribute a risk judgment only when the
supplied evidence explicitly records it.

- A failing required check, missing human review, active incident on the
  service, or freeze supports NO-GO. A green canary does not cancel failing tests.
- A relevant major upgrade (in the change or concurrent shared infrastructure),
  broad diff, no pre-prod, related recent failures, or all-environment rollout
  supports CAUTION.
- A required check that is unavailable makes the verdict INCOMPLETE; do not
  preserve GO by treating it as passed.
- Apply the customer's release policy, or say which stated defaults you used.
  An emergency exception needs the customer's authorized decision-maker.

## Inferences, not evidence

Use up to three short bullets for useful operational inferences. Each begins
"If" with an unverified condition, followed by what "could" or "would" follow,
or a conditional recommendation. Keep every clause conditional; do not append
factual assertions, risk rankings, or source summaries. For example: "If the
shared dependency degrades during rollout, it could affect the mapped service
even when the patch checks pass." The heading alone does not qualify a claim. Never describe the customer's safeguards, monitors or
teams as able or unable to do something the evidence does not state.
Move missing details to **Unresolved checks** as recommendations to confirm
information. Do not narrate that a source "only says", "does not show", or
"gives no" detail when only its summary was supplied. Use source IDs to cite
supplied contents, not to imply that a whole record was inspected.
Recommendations do not establish that an option is safest or lowest-risk.
A passing CI result does not establish what the checks detect. A scoped calendar
finding does not establish that the calendar covers only that kind of change.
Use "None." when no useful additional inference is needed; do not invent
possibilities just to fill this section.

The final line covers only your own non-actions. Do not extend it to the release team.
