# Apache Cassandra: Throughput signals

## Scope

Signals in the Throughput domain for Apache Cassandra, as defined in the Netdata operator playbook.
Each signal includes a short description, the collection source, and a hint for the MCP query
pattern that surfaces it. Use this file during a triage pass to decide which signal to pull first.

## Severity legend

- **HIGH**: first-class paging target. Short time to impact.
- **MEDIUM**: ticket-worthy. Usually a precursor, not a cause.
- **LOW**: context only. Useful for RCA, not for alerting.

## Signals

### Client Request Rate (Read/Write) [MED]

Rate of client read and write requests processed by this node as coordinator. The baseline workload
measurement.

Collection source: JMX: `org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Latency`;
attribute `Count` (cumulative) and `OneMinuteRate` JMX:
`org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Latency`; same attributes
Additional scopes: `CASRead`, `CASWrite`, `RangeSlice`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

## Triage order within this domain

Investigate HIGH-severity signals first, then MEDIUM, then LOW. HIGH-severity signals have the
shortest time to impact; a confirmed HIGH anomaly usually justifies paging. When two HIGH signals
move together, treat them as one incident until `find_correlated_metrics` rules out shared cause.

## Common false positives

- A single stale data point from a collector restart triggers many signals briefly. Re-query after
  30 seconds before escalating.
- Short bursts under 60 seconds rarely warrant action unless paired with a confirmed business
  impact.
- Comparing against yesterday's baseline on a post-deploy day produces false anomalies. Compare
  against the pre-deploy baseline.
- Collector-visible percentile latency with < 100 samples per minute is noise. Require a minimum
  sample count before acting.

## Remediation pointers

Remediation for signals in this domain is tech-specific and typically covered in the operator
playbook's SECTION 3 (Failure Patterns) or SECTION 4 (Runbooks). Before applying a change:

1. Run the MCP verification queries to record the current state.
2. Apply the smallest remediation that addresses the confirmed cause. Config changes before
   restarts; restarts before rollbacks.
3. Re-run the same MCP queries after the remediation settles. Recording before/after numbers is how
   a runbook entry gets sharpened over time.

## Netdata contexts that surface Throughput

These are the real Netdata chart contexts the native collector emits for Apache Cassandra. Use these
names verbatim in `query_metrics` calls.

- `cassandra.client_requests_rate`: Client requests rate (requests/s). Dimensions: read, write.
- `cassandra.client_requests_latency`: Client requests total latency (seconds). Dimensions: read,
                                       write.
- `cassandra.row_cache_hit_rate`: Key cache hit rate (events/s). Dimensions: hits, misses.
- `cassandra.key_cache_hit_rate`: Row cache hit rate (events/s). Dimensions: hits, misses.
- `cassandra.compaction_completed_tasks_rate`: Completed compactions rate (tasks/s). Dimensions:
                                               completed.
- `cassandra.compaction_compacted_rate`: Compaction data rate (bytes/s). Dimensions: compacted.
- `cassandra.jvm_gc_rate`: Garbage collections rate (gc/s). Dimensions: parnew, cms.
- `cassandra.dropped_messages_rate`: Dropped messages rate (messages/s). Dimensions: dropped.
- `cassandra.client_requests_timeouts_rate`: Client requests timeouts rate (timeout/s). Dimensions:
                                             read, write.
- `cassandra.client_requests_unavailables_rate`: Client requests unavailable exceptions rate
                                                 (exceptions/s). Dimensions: read, write.
- `cassandra.client_requests_failures_rate`: Client requests failures rate (failures/s). Dimensions:
                                             read, write.
- `cassandra.storage_exceptions_rate`: Storage exceptions rate (exceptions/s). Dimensions: storage.

## MCP query examples for this domain

```text
# Pull every context in this domain at once
query_metrics with contexts=[cassandra.client_requests_rate, cassandra.client_requests_latency, cassandra.row_cache_hit_rate, cassandra.key_cache_hit_rate, cassandra.compaction_completed_tasks_rate, cassandra.compaction_compacted_rate] and relative_window=-30m

# Rank anomalies that match this domain
find_anomalous_metrics with node=<host> and context_pattern="cassandra.*"

# Correlate a problem context with others outside the domain
find_correlated_metrics around the incident window, anchor_context="cassandra.client_requests_rate"
```

## When to escalate out of this skill

If none of the signals in this domain move during the incident, the root cause is elsewhere. Typical
re-routing:

- Host-resource domain: load, CPU, memory, disk, network saturation
- Dependency domain: the service's upstream or downstream (database, cache, queue) is the actual
  source
- Orchestrator domain: Kubernetes or systemd lifecycle events rather than application misbehavior
- Alert engine domain: a misconfigured alert threshold triggered a false-positive incident
