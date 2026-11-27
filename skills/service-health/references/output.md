# Service-health summary

For a health assessment include:

1. Service/environment/region, explicit time window, freshness, and baseline period.
2. Error rate, latency, and traffic: actual values/trends, comparable baseline,
   source chart or samples, and gaps. Call out persistent drift, repeated blips,
   and unexpected zero traffic with the service's normal pattern.
3. Active/monitoring incidents with recorded severity; catalog coverage limits.
4. Team owner and on-call responder as recorded; stale or missing data.
5. Five recent verified deploys with PRs/authors, or fewer with a stated gap.
6. Assessment, confidence and reason, and the next useful check.

If telemetry is absent, label this a partial service-context summary. Do not
replace the three signals with incident counts or fabricate missing charts.
For an owner-only lookup, give the requested ownership result and source only.
