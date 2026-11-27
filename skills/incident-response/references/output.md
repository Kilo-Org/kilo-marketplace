# Responder brief

Lead with mitigation-relevant information in this order. Use the same structure
for a refresh, showing what changed instead of repeating the entire history.

1. Current impact: customer experience, affected services/environment/regions,
   measured scope, status/severity as recorded, and observation window. Separate
   confirmed observations from unconfirmed impact. Cite metrics/logs and charts.
2. Recent changes: deployed change/PR/config/flag, time, author, relevance to
   symptoms, and gaps. A suspected change remains a hypothesis. Do not notify authors.
3. Next actions: recommended mitigation/check, why, proposed owner or owner
   needed, and the evidence that would change the recommendation. Name the
   expertise or authority needed before suggesting another responder.

Then add only decision-relevant detail:

- Hypotheses with qualitative confidence, support, contradictions, and next checks.
- Historical matches with important differences and applicability of earlier fixes.
- For concurrent failures: dependency overlap, symptom comparison, separate vs.
  shared investigation recommendation, and explicit revisit conditions.
- Source coverage, stale data, unavailable enrichment, and checks not performed.

Do not fill unknown fields with defaults. Your recommended actions are proposals;
report responders' actions separately, using only their recorded execution state.
Use the smallest useful comparison for concurrent failures; no generic wall of data.

## Focused decision

Use this shape for an evidence-rule or action-state question: what a rule
requires, or what a record establishes about approval, execution or outcome.
Responder, concurrent-failure, vendor and impact questions use the brief above
even when they supply their own facts. Return exactly these sections and
nothing else.
Begin the final answer with the answer line and end at the exact non-action
sentence. Use only the prescribed headings. Put every requested explanation
under **Rule** instead of creating a new section. Do not add an introduction,
recap, closing offer, or sample update.

```
**Answer: Yes | No | Conditional.** One sentence answering the question asked.

| Fact | State | Source |
|---|---|---|
| Signal | ... | ... |
| Corroboration | ... | ... |
| Approval | ... | ... |
| Execution | ... | ... |
| Outcome | ... | ... |
| Cause | ... | ... |
| Action risks | ... | ... |

**Rule**
The applicable general rule and requested explanation. Incident states and
source contents belong in the table, not this paragraph.

**Inferences, not evidence**
None.

**Next check**
- Only the neutral evidence questions needed to resolve the remaining gaps,
  using the forms below. Do not add a story about an operator or prior work.

I did not call Rootly, change any record, or execute anything.
```

For **Next check**, select only unresolved checks relevant to the question.
Use these question forms, substituting only actions or record IDs supplied in
the evidence. They request information without assuming a person, event, record
or prerequisite exists. Add no factual rationale to a question.

- Unknown execution: "Has the action started, and is an execution record available?"
- Reported start: "Is completion evidence available? What independent evidence could establish the outcome?"
- Missing approval or assessment: "Is an approval record or decision assessment available, and what does it cover?"
- Unread policy or runbook: "Is the applicable policy or runbook available? Does it define prerequisites and verification criteria?"
- Unconfirmed operational claim: "What second independent operational source could corroborate the reported signal or proposed cause?"

Keep supplied approval and assessments in the table; do not ask as though they
were missing. Do not infer an operator's identity or an ongoing state from
"started" alone. Avoid phrases such as "the responder running the runbook"
unless the source actually establishes that actor and ongoing state.

Table rules:

- Keep the seven rows when the question involves an action. Drop rows only when
  the question involves no signal or no action.
- Copy the state values below literally. In particular, use
  `unassessed in supplied evidence`, not a paraphrase such as "not assessed".
  The Execution state cell contains only its state; put any unknown completion
  or recovery in Outcome or Next check, not in an Execution qualifier.
- **Execution** is `unknown`, `not started`, `reported started`, or
  `reported complete`. Every state except `unknown` needs a record that states it.
  An approval alone gives `unknown`. A start record never gives completion.
  "Completion unknown from the supplied material" is not a finding that the
  full operator log contains no completion entry.
- **Corroboration** is `not supplied` unless the evidence contains a second
  independent source. Do not state that no other source exists or can be found.
- **Outcome** is `unknown` unless independent evidence shows recovery.
- **Action risks** is `unassessed in supplied evidence` only when no assessment
  is supplied; this does not mean responders never assessed the risks. When one
  is supplied, replace that default with the attributed judgment, its author,
  source and scope.
  An attributed assessment need not be independently verified to be reported;
  do not call it missing just because safety or effectiveness remains unverified.
  Do not independently call the action safe, bounded, low-risk, cheaper than
  waiting, justified, or sufficient. Approval, reversibility and a practiced
  runbook alone do not establish any of these.
- **Source** names the actual supplied source. Use "user-supplied approval" when
  the user states an approval; name an approval record only when one was supplied.
  Use `—` for an unknown state or risks unassessed in supplied evidence.

For a focused question, the table, Rule and Next check carry the answer. Default
**Inferences, not evidence** to `None.`; do not add speculative scenarios just
to fill it. Only when the user explicitly asks for hypothetical scenarios,
use up to two short "If ... could/would ..." bullets instead. Keep every clause
conditional and do not presuppose the contents of an unread source.

For evidence-rule questions, copy this paragraph under **Rule** unchanged.
Do not append incident states or descriptions of what a log records:

```
Corroboration from two independent sources, including metrics or logs, is required before impact, cause or recovery is called confirmed. It is not a waiting period for an authorized human choosing mitigation under uncertainty. It does not establish that this action is safe, sufficient, or preferable to waiting; that is the decision-maker's assessment of prerequisites and risks.
```

When asked to distinguish acting under uncertainty from claiming a confirmed
cause, append only this explanation, unchanged, under **Rule**:

```
Choosing a mitigation is a decision about what to try while evidence is incomplete. Calling a cause confirmed is an evidence claim about what produced the incident. Authority or approval to choose an action does not establish its safety, comparative harm, or fulfillment of applicable customer prerequisites. Approval, execution, completion and verified recovery are separate claims; report each only at the strength its source supports.
```

This explains the distinction without supplying a rationale for this incident's
decision. Do not extend it with a story about why the commander chose to act,
a claim that acting is reasonable or less harmful than waiting, or an invented
list of the only prerequisites. A supplied decision assessment may be attributed
in the table; it is not independently verified safety or causal confirmation.

Do not add sample record text or first-person action narration, including under
**Inferences, not evidence**. Use the sourced table state for handoff guidance:
approval alone cannot become a recommendation to record execution; a reported
start cannot become a recommendation to record completion or recovery.
