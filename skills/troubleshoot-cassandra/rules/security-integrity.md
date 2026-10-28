# Apache Cassandra: Security & Integrity signals

## Scope

Signals in the Security & Integrity domain for Apache Cassandra, as defined in the Netdata operator
playbook. Each signal includes a short description, the collection source, and a hint for the MCP
query pattern that surfaces it. Use this file during a triage pass to decide which signal to pull
first.

## Severity legend

- **HIGH**: first-class paging target. Short time to impact.
- **MEDIUM**: ticket-worthy. Usually a precursor, not a cause.
- **LOW**: context only. Useful for RCA, not for alerting.

## Signals

### Authentication / Authorization Failures [MED]

- Source: System logs (`grep "Authentication error"`) or audit log (4.0+) - Significance: Brute
force detection, misconfigured clients - Action: TICKET if high sustained rate from single source

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Authorization Failures [MED]

- Source: System logs (`grep "Unauthorized"`) or audit log - Significance: Compromised accounts,
application misconfiguration - Action: TICKET if sustained from known users

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### DDL Changes to System Keyspaces [MED]

- Source: Audit log (4.0+) - Significance: Unauthorized modifications to `system_auth`,
`system_traces` - Action: TICKET; investigate whether the change was authorized. PAGE only with
external change-control context confirming the change is unexpected.

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Unexpected Client Connections [MED]

- Source: Virtual table (4.0+): `system_views.clients` - Significance: Unknown clients connecting to
the cluster - Action: TICKET for investigation

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Data Integrity / Corruption Detection [MED]

- Source: System logs (grep for `FSError`, `CorruptSSTableException`, `IOError`), `nodetool verify`
output - Significance: Detects on-disk SSTable corruption, filesystem errors, bad sectors - Action:
PAGE for `CorruptSSTableException` or `FSError` detected in logs (these are real hardware/data fa...

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Tombstone Scan Warnings [MED]

Log warnings when a read query scans more tombstones than `tombstone_warn_threshold` (default 1000).
At `tombstone_failure_threshold` (default 100000), the query is **aborted**.

Collection source: System logs: `grep "Scanned over .* tombstones" /var/log/cassandra/system.log`
Virtual table (4.1+): `system_views.tombstones_per_read`

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

## Netdata contexts that surface Security & Integrity

No Netdata-native contexts were classified into the Security & Integrity domain for Apache
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
