# Apache Cassandra: Saturation / Internal State signals

## Scope

Signals in the Saturation / Internal State domain for Apache Cassandra, as defined in the Netdata
operator playbook. Each signal includes a short description, the collection source, and a hint for
the MCP query pattern that surfaces it. Use this file during a triage pass to decide which signal to
pull first.

## Severity legend

- **HIGH**: first-class paging target. Short time to impact.
- **MEDIUM**: ticket-worthy. Usually a precursor, not a cause.
- **LOW**: context only. Useful for RCA, not for alerting.

## Signals

### Pending Compactions [MED]

Number of compaction tasks queued and waiting to execute. The "technical debt" of the storage
engine.

Collection source: JMX: `org.apache.cassandra.metrics:type=Compaction,name=PendingTasks`
(Gauge<Integer>) Per-table:
`org.apache.cassandra.metrics:type=Table,keyspace=X,scope=Y,name=PendingCompactions`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Thread Pool Pending Tasks [MED]

Count of tasks queued in Cassandra's internal thread pools. Cassandra uses a staged event-driven
architecture (SEDA) where different operations have dedicated thread pools.

Collection source: JMX:
`org.apache.cassandra.metrics:type=ThreadPools,path=request,scope=MUTATION,name=PendingTasks` JMX:
`org.apache.cassandra.metrics:type=ThreadPools,path=request,scope=READ,name=PendingTasks` Additional
request scopes: `COUNTER_MUTATION`, `VIEW_MUTATION`, `REQUEST_RESPONSE` Internal scopes (pat...

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Commitlog Pending Tasks [MED]

Number of commitlog operations waiting to be written/synced to disk.

Collection source: JMX: `org.apache.cassandra.metrics:type=CommitLog,name=PendingTasks` (Gauge)
Also: `TotalCommitLogSize`, `WaitingOnSegmentAllocation`, `WaitingOnCommit`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### JVM Heap Usage [MED]

JVM heap memory utilization; the primary memory pressure indicator for Cassandra. Cassandra runs as
a single JVM process per node.

Collection source: JMX: `java.lang:type=Memory`; attribute `HeapMemoryUsage` (used, committed, max)
JMX: `java.lang:type=MemoryPool,name=G1 Old Gen`; `Usage` (for generational breakdown with G1GC)

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### GC Pause Duration [MED]

Duration of stop-the-world JVM garbage collection pauses. During a pause, all application threads
are frozen; no gossip, no client responses, no compaction.

Collection source: JMX: `java.lang:type=GarbageCollector,name=G1 Young Generation`;
`CollectionCount`, `CollectionTime` JMX: `java.lang:type=GarbageCollector,name=G1 Old Generation`;
`CollectionCount`, `CollectionTime` Note: GC names depend on collector. G1GC (default in 4.x with
Java 11+) uses `G1 Young Generation...

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Disk Space Usage [MED]

Disk space consumed by Cassandra data directories, commitlog, hints, and snapshots relative to
available space.

Collection source: OS-level: `df` on data/commitlog directories JMX:
`org.apache.cassandra.metrics:type=Storage,name=Load`; total data file size on this node (does not
include commitlog, hints, or snapshots) Virtual table (4.0+): `system_views.disk_usage`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### SSTable Count Per Table [MED]

Number of SSTables per table on this node. Directly determines read amplification.

Collection source: JMX:
`org.apache.cassandra.metrics:type=Table,keyspace=X,scope=Y,name=LiveSSTableCount` (Gauge)

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Disk I/O Utilization and Latency [MED]

I/O utilization, throughput, and latency on the disks used by Cassandra (data directories, commitlog
volume).

Collection source: OS-level: `iostat -x`, `/proc/diskstats`, or system metrics (per-device) Key
metrics: `%util` (saturation), `r/s + w/s` (IOPS), `await` (average I/O latency),
`r_await`/`w_await`

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### File Descriptor Usage [MED]

Number of open file descriptors in the Cassandra JVM process relative to the configured ulimit.

Collection source: JMX: `java.lang:type=OperatingSystem`; attributes `OpenFileDescriptorCount`,
`MaxFileDescriptorCount` OS: `/proc/<pid>/fd/` (count) and `/proc/<pid>/limits` (configured limit)

MCP query: pull this signal with `query_metrics` and check the last 15 to 30 minutes against
expected bands. Cross-reference with `find_anomalous_metrics` scoped to the same context. Use
`find_correlated_metrics` if the signal has moved but the obvious cause is not visible.

### Off-Heap Memory Usage [MED]

Memory used outside the JVM heap; direct ByteBuffers, memory-mapped files, bloom filters (off-heap
since 3.x), compression metadata, and off-heap memtables (if configured).

Collection source: JMX: `java.lang:type=MemoryPool,name=direct`; `Usage` (for direct ByteBuffers)
JMX: `org.apache.cassandra.metrics:type=BufferPool,name=Size` (Cassandra internal buffer pool) OS:
RSS from `/proc/<pid>/status` minus JVM heap max

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

## Netdata contexts that surface Saturation / Internal State

No Netdata-native contexts were classified into the Saturation / Internal State domain for Apache
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
