# Worked example: quiet traffic versus missing evidence

Synthetic fixture at 03:30 UTC for a batch-processing service.

## Available evidence

- M1: Traffic is zero during 03:00–03:30 UTC. The comparable prior-week baseline
  is also zero; the scheduled batch normally starts at 04:00 UTC.
- M2: The latency panel has no samples in this window.
- M3: The error-rate panel has no denominator because no requests occurred.
- R1: Current Rootly query returns no active incident for this service.
- O1: Rootly lists Batch Team as owner and responder A on call.
- D1: Deployment feed supplies only three releases, each with PR/author identifiers.

## Example summary

Traffic is zero in the observed window, consistent with the supplied baseline
and schedule (M1). That alone does not indicate an outage. Latency and error
rate cannot be assessed without requests (M2, M3); do not render them as zero
or conclude the next batch will succeed.

The record lists Batch Team and responder A (O1); the query found no active
incident in its covered scope (R1). Show the three verified deploys from D1,
stating that five were requested but only three were available.

Assessment: partial. Recheck execution/traffic when the batch is expected,
following the team's threshold. No universal zero-traffic alert interval applies.

## Counterexample

For a continuously used checkout service with an established nonzero baseline,
the same zero-traffic observation merits urgent investigation. Do not reuse the
batch-service interpretation without checking the workload.
