# Apache Cassandra: Replication / Consistency signals

## Scope

Signals in the Replication / Consistency domain for Apache Cassandra, as defined in the Netdata
operator playbook. Each signal includes a short description, the collection source, and a hint for
the MCP query pattern that surfaces it. Use this file during a triage pass to decide which signal to
pull first.

## Severity legend

- **HIGH**: first-class paging target. Short time to impact.
- **MEDIUM**: ticket-worthy. Usually a precursor, not a cause.
- **LOW**: context only. Useful for RCA, not for alerting.

## Signals

### Hinted Handoff Status [MED]

State of hint storage and delivery on this node. Hints are stored when a write's target replica is
unavailable, and delivered when the replica returns.

Collection source: JMX: `org.apache.cassandra.metrics:type=Storage,name=TotalHintsInProgress`; hints
currently being delivered (active delivery threads) JMX:
`org.apache.cassandra.metrics:type=Storage,name=TotalHints`; total hints written since restart
(cumulative counter) JMX: `org.apache.cassandra.metrics:type=Hi...

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Repair Status / Last Repair Time [MED]

Whether anti-entropy repair has run successfully within `gc_grace_seconds` (default 10 days) for
each table. Repair ensures replica consistency and enables tombstone garbage collection.

Collection source: `system_distributed.repair_history` table (3.x+) `nodetool repair_admin list`
(4.0+) Log files: grep for repair session completion

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Read Repair and Speculative Retry Activity [MED]

Rate of read repairs (triggered when replicas return inconsistent data during a read) and
speculative retries (when the coordinator sends an extra read to another replica because the first
is too slow).

Collection source: JMX:
`org.apache.cassandra.metrics:type=Table,keyspace=X,scope=Y,name=ReadRepairRequests` (Meter) JMX:
`org.apache.cassandra.metrics:type=Table,keyspace=X,scope=Y,name=SpeculativeRetries` (Counter)

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Streaming Progress and Failures [MED]

Status and error rate of streaming sessions; bulk data transfers during bootstrap, decommission,
rebuild, or repair.

Collection source: JMX: `org.apache.cassandra.metrics:type=Streaming,name=TotalIncomingBytes` /
`TotalOutgoingBytes` Virtual table (4.0+): `system_views.sstable_tasks` (shows streaming tasks)

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

## Netdata contexts that surface Replication / Consistency

No Netdata-native contexts were classified into the Replication / Consistency domain for Apache
Cassandra. Use discovery-style MCP calls below, or consult the full context list in SKILL.md.

## MCP query examples for this domain

```text
# Discover contexts for this service
list_metrics with q="apache-cassandra"

# Rank anomalies on the host running this service
find_anomalous_metrics with node=<host>
```

## When to escalate out of this skill

If none of the signals in this domain move during the incident, the root cause is elsewhere. Typical
re-routing:

- Host-resource domain: load, CPU, memory, disk, network saturation
- Dependency domain: the service's upstream or downstream (database, cache, queue) is the actual
  source
- Orchestrator domain: Kubernetes or systemd lifecycle events rather than application misbehavior
- Alert engine domain: a misconfigured alert threshold triggered a false-positive incident
