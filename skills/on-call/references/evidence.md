# Evidence assessment

Generated from `tools/templates/evidence.md`. Read when assessing operational claims,
trends, or disputed evidence, not for a simple record or schedule lookup.

A copied dashboard screenshot and its underlying query count as one source.
A Slack statement, vendor status page, similarity score, or generated summary
alone does not establish cause or impact scope. Check whether sources are
independent rather than counting two renderings of the same assertion.
A before/after reading from the same monitor is still one source; improvement
after an action alone proves neither independent corroboration nor causation.

Administrative facts can be attributed directly: "The Rootly record lists
severity X" or "The schedule lists Y on call." This does not verify appropriate
severity or actual availability. Separate those assessments from record retrieval.

When evidence is insufficient, mark the claim unconfirmed and identify the next
useful check without withholding useful mitigation options. Use qualitative
confidence with reasons. Show evidence for and against supported alternatives,
and visibly revise recommendations when observations change. Do not invent
extra hypotheses to meet a quota.

Record source freshness and the covered service, region, environment, window,
and pagination. Recheck stale ownership/routing before relying on it. Complete
a handoff's scoped pages when available; disclose any remaining gaps rather than
describe one page as every record.

Prefer retrieved charts or screenshots. Charts drawn from numeric samples must
cite those samples; missing samples or baselines cannot be replaced with an
illustration presented as measured telemetry.

## Final evidence check

Distinguish a supplied summary from the full record it describes. A missing
detail in an excerpt supports "not supplied in this excerpt", not a claim that
the full record lacks it. An identifier or citation does not establish that the
whole record was inspected. The same distinction applies to a missing report
of an event versus evidence that the event did not happen. When complete,
scoped evidence establishes absence, report that absence rather than leave it
unknown.
For missing details, make the gap about the supplied material: "rollback scope
not supplied", not "the rollout record gives no rollback scope". A policy
summary omitting a requirement does not establish that the requirement does
not apply. Likewise, say a property does not establish risk or cost, rather
than claim that an unread runbook says nothing about them.

Before returning an assessment, check factual premises throughout the answer,
including recommendations, questions, headings, and sample wording. Keep each
claim at the strength and scope its source supports; an earlier uncertainty
label does not qualify a later factual assertion. Missing verification describes
our evidence, not whether responders performed a check: say "no verification
was supplied", not "no check was done". When an absence is inferred only from a
missing record, the same wording applies to approval, agreement, execution,
paging, detection and warning: write that the record is not supplied, not that
nobody approved, agreed, started or acted.
Apply the same check to example wording: approval alone cannot become a sample
update saying an action was taken. Do not state comparative safety or call an
option the lowest-risk path without evidence comparing the alternatives. A
recommendation can be stated as a recommendation without that factual claim.
A passing check establishes its reported result, not which failure modes it can
detect. A scoped finding in a calendar does not establish that the calendar
covers only that kind of event. Check each clause, including factual premises
inside otherwise conditional or labeled reasoning.
Repair the wording in place, without adding a review section to the response.

| Supplied evidence | Unsupported wording | Evidence-preserving wording |
|---|---|---|
| Error signatures were not supplied | "There is no shared error signature." | "We cannot compare signatures from the supplied evidence." |
| Certificate expiry is a suspected cause; detection history is unknown | "Why wasn't expiry caught before it caused the outage?" | "Did expiry contribute, and what warning or detection evidence exists?" |
| Mitigation is stalled by missing database expertise; a candidate has database access | "The candidate fills the expertise and access gaps blocking mitigation." | "Consider the candidate for the expertise gap; their access is relevant, but an access blocker was not established." |

When a scoped check actually establishes absence, or new evidence establishes a
cause or blocker, report that finding with its source. Do not preserve uncertainty
after the evidence resolves it, or expand a scoped absence into a broader one.
