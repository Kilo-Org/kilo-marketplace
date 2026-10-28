# Apache Cassandra: Errors signals

## Scope

Signals in the Errors domain for Apache Cassandra, as defined in the Netdata operator playbook. Each
signal includes a short description, the collection source, and a hint for the MCP query pattern
that surfaces it. Use this file during a triage pass to decide which signal to pull first.

## Severity legend

- **HIGH**: first-class paging target. Short time to impact.
- **MEDIUM**: ticket-worthy. Usually a precursor, not a cause.
- **LOW**: context only. Useful for RCA, not for alerting.

## Signals

### Dropped Messages [MED]

Messages (mutations, reads, etc.) that were discarded because they sat in an internal queue past
their timeout. The node is shedding load; it cannot keep up.

Collection source: JMX:
`org.apache.cassandra.metrics:type=DroppedMessage,scope=MUTATION,name=Dropped` (Meter: count, rates)
Additional scopes: `READ`, `COUNTER_MUTATION`, `RANGE_SLICE`, `HINT`, `BATCH_STORE`, `BATCH_REMOVE`,
`READ_REPAIR`, `REQUEST_RESPONSE` Note: In Cassandra 4.x, primary scopes are `MUTATION_REQ...

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Client Request Timeouts [MED]

Count of read or write requests where the coordinator timed out waiting for enough replica
responses. The client receives a timeout error.

Collection source: JMX: `org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Timeouts`
(Meter) JMX: `org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Timeouts`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Client Request Unavailables [MED]

Count of requests where the coordinator could not find enough live replicas to satisfy the
consistency level. Unlike timeouts, these fail immediately; no waiting.

Collection source: JMX:
`org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Unavailables` (Meter) JMX:
`org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Unavailables`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Storage Exceptions [MED]

Count of uncaught exceptions in the storage subsystem; typically indicates disk I/O errors,
filesystem failures, or corruption events.

Collection source: JMX: `org.apache.cassandra.metrics:type=Storage,name=Exceptions` (Counter)

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

## Netdata contexts that surface Errors

These are the real Netdata chart contexts the native collector emits for Apache Cassandra. Use these
names verbatim in `query_metrics` calls.

- `cassandra.dropped_messages_rate`: Dropped messages rate (messages/s). Dimensions: dropped.
- `cassandra.client_requests_timeouts_rate`: Client requests timeouts rate (timeout/s). Dimensions:
                                             read, write.
- `cassandra.client_requests_failures_rate`: Client requests failures rate (failures/s). Dimensions:
                                             read, write.

## MCP query examples for this domain

```text
# Pull every context in this domain at once
query_metrics with contexts=[cassandra.dropped_messages_rate, cassandra.client_requests_timeouts_rate, cassandra.client_requests_failures_rate] and relative_window=-30m

# Rank anomalies that match this domain
find_anomalous_metrics with node=<host> and context_pattern="cassandra.*"

# Correlate a problem context with others outside the domain
find_correlated_metrics around the incident window, anchor_context="cassandra.dropped_messages_rate"
```

## When to escalate out of this skill

If none of the signals in this domain move during the incident, the root cause is elsewhere. Typical
re-routing:

- Host-resource domain: load, CPU, memory, disk, network saturation
- Dependency domain: the service's upstream or downstream (database, cache, queue) is the actual
  source
- Orchestrator domain: Kubernetes or systemd lifecycle events rather than application misbehavior
- Alert engine domain: a misconfigured alert threshold triggered a false-positive incident
