# Worked example: simultaneous failures

Synthetic fixture, observed at 10:10 UTC. Evidence identifiers below are local
fixture labels, not live links.

## Available evidence

- I1: Rootly incident INC-101 is investigating checkout; recorded severity SEV2.
- I2: Rootly incident INC-102 is investigating search; recorded severity SEV2.
- M1: Checkout error rate rises from 0.2% to 9% at 10:00, region A.
- L1: Checkout logs show payment request timeouts in region A at 10:00–10:09.
- M2: Search error rate rises from 0.1% to 6% at 10:00, region B.
- L2: Search logs show index schema errors in region B at 10:00–10:09.
- D1: Current dependency map shows distinct payment and search-index dependencies;
  completeness of lower-level infrastructure dependencies is unknown.
- C1: Checkout dependency bump was deployed at 09:50, authored by an automation bot.
- C2: Search index configuration changed at 09:57; no shared deployment is recorded.
- O1: Schedule records list separate service on-call rotations. Calendar data is absent.

## Example brief

Confirmed: checkout requests are failing in region A (M1, L1), while search
queries fail with a different signature in region B (M2, L2). Both began around
10:00. Rootly records both incidents as investigating/SEV2 (I1, I2).

Unconfirmed causes: the checkout dependency bump (C1) and search configuration
change (C2) are relevant candidates. Neither is proven causal. The available
dependency map shows little overlap but does not cover all infrastructure (D1).

Recommendation: keep separate investigations and propose cross-links. Ask the
checkout and search responders to compare their deployed changes with the logs.
Consider a shared investigation if a common dependency shows errors, failure
signatures converge, or a single change is shown to affect both paths. Do not
merge merely because the start times match.

Ask the commander to confirm who owns each check. O1 establishes scheduled
roles, not availability or permission to page. No records or responders were changed.

## Counterexample

If new independent evidence identifies an auth dependency failing along both
request paths with matching errors, reassess the split. The lesson is to test
causal overlap, not always create separate incidents.
