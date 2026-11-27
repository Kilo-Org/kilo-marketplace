# Worked example: disputed cause, human-owned learning

Synthetic fixture. Rootly records INC-9 as resolved; this is review preparation.

## Available evidence

- M1: Latency rose during 09:00–09:30 and later returned to its baseline.
- L1: Request logs corroborate elevated latency and later recovery.
- D1: A config change was deployed at 08:58.
- V1: Vendor degradation was reported at 09:00, without endpoint-level detail.
- T1: Two responders disagree: one suspects config, the other the vendor.
- R1: No human review conclusion or accepted action item has been recorded.
- P1: Company policy calls for a facilitated review at the incident's recorded severity.

## Example packet

Confirmed observation: elevated latency and subsequent recovery (M1, L1).
The timeline includes D1's deployment and V1's vendor report with separate
source attribution. Their timing does not establish either as the cause.

Unconfirmed explanations: configuration interaction (D1, T1) and vendor effect
(V1, T1). Endpoint-level vendor evidence and a reproduction test are missing.
Ask participants what they knew at each decision point and which evidence would
distinguish these explanations. Preserve their disagreement rather than choose
a winner. Human learning/conclusions remain pending (R1).

Proposed follow-up: ask the roadmap owner to consider a reproduction test and
better dependency telemetry. Success would mean distinguishing local config
failure from upstream latency. No engineer, due date, or commitment is assigned.
Recommend naming a review owner and gathering raw notes for the P1 review.

## Counterexample

If an approved human review later establishes contributing factors, summarize
them with attribution. Do not continue to label an already-adjudicated human
decision as an agent-generated hypothesis, or silently replace its conclusion.
