# Measurement and improvement

Start with a business outcome and an observable definition. A button click, submit
attempt, accepted request, qualified lead, and purchase are different events.

## Define trustworthy events

Document name, trigger, acceptance predicate, opaque identifier, deduplication
scope, property allowlist, permission category, and test sink. Do not send form
values, email addresses, names, free text, full query strings, or credentials as
analytics properties. Sanitize permitted campaign values before storing them.

Acceptance events follow the server's application-level acknowledgement. Emit at
most once per logical accepted request. Known failures and direct/repeated success
page visits must not count as leads. A retry should preserve identity where safe.

Test the actual configured permission states, including refusal and withdrawal
where required. Do not assume every analytics configuration is exempt or that all
collection universally requires the same mechanism. Load the privacy reference.

Use `scripts/validate-events.mjs --help` on an exported test trace. This checks
semantics within that trace, not whether the production collector received data.
Record how the trace was captured and whether it is synthetic or browser-observed.

## Read data before acting

Check time window, timezone, denominator, bot/internal traffic handling, duplicate
events, permission coverage, and implementation changes. Show absolute counts
alongside rates. Segment only when there is enough relevant data to learn from it.
A bounce or scroll pattern suggests an investigation; it does not prove motivation.

For each proposal separate observation, interpretation, hypothesis, and action.
Prioritize known breakage and missing promises before cosmetic hypotheses. Tie
changes to the visitor's decision and business goal, with cost and risk considered.

## Pick an appropriate evaluation

| Situation | Useful next step |
| --- | --- |
| No endpoint or broken event | Repair and verify instrumentation/journey |
| Very little traffic | Observe usability, interview prospects, inspect support/sales feedback |
| Qualitative evidence points to confusion | Change the explanation and test comprehension |
| Enough stable traffic and assignment capability | Plan a randomized experiment |
| Only before/after data exists | Describe change and uncertainty; do not claim causation |

Before an experiment, define unit of assignment, primary metric, denominator,
baseline, smallest worthwhile effect, feasible sample/time, stopping rule,
exclusions, and guardrails. Do not generate a sample-size result without a method
and its assumptions. Avoid repeated peeking or chasing arbitrary “significance.”

Keep concurrent marketing/price/traffic changes visible. Report negative and mixed
results. An expert score, screenshot preference, or accessibility improvement is
valuable in its own dimension; none independently establishes conversion lift.
