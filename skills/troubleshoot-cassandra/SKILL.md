---
name: troubleshoot-cassandra
description: >-
  Use when diagnosing issues with Apache Cassandra: gc death spiral, compaction
  death spiral, tombstone storm, disk space exhaustion, or hint overflow.
  Queries Netdata via MCP for node liveness (failure detector), native transport
  active, client request rate (read/write), client request latency
  (coordinator), applies the diagnostic tree from the Netdata operator playbook,
  and recommends remediation.
metadata:
  upstream:
    version: 0.1.0
    author: Netdata
    tags:
      - netdata
      - troubleshoot
      - mcp
      - cassandra
  category: observability
  source:
    repository: 'https://github.com/netdata/skills'
    path: skills/troubleshoot-cassandra
    license_path: LICENSE
    commit: ae650fc3766642f14e29892ab4fed607ac29d263
---

# Troubleshoot Apache Cassandra

## When to use this skill

- **GC Death Spiral**: Heap pressure then long GC pauses then gossip failures then node marked DOWN
                       then client retries flood then more heap pressure. Self-reinforcing.
- **Compaction Death Spiral**: Write rate exceeds compaction throughput then SSTables accumulate
                               then read amplification increases then latency spikes then more
                               compaction needed then disk I/O saturated.
- **Tombstone Storm**: Accumulated tombstones (deletes/expired TTLs) force reads to scan massive
                       amounts of dead data then read latency spikes, possible query abortion at
                       100K tombstones.
- **Disk Space Exhaustion**: Compaction backlog + snapshots + hints consume space then compaction
                             cannot run (needs temporary space) then writes blocked.
- **Hint Overflow**: Long node outage then hints accumulate on coordinators then hints expire
                     (`max_hint_window`, default 3h) then data permanently inconsistent unless
                     repaired.
- Any time the user reports a Apache Cassandra service behaving outside its expected envelope
  (elevated errors, latency, saturation, resource exhaustion, or unexpected restarts).
- An on-call engineer is paging on a Netdata alert tied to a Apache Cassandra instance and wants a
  structured triage path.

## Key facts

- This skill wraps the Netdata operator playbook for Apache Cassandra. It does not replace the
  playbook; it routes a coding agent through MCP queries against the same signals the playbook
  relies on.
- The playbook decomposes Apache Cassandra health into 8 signal domains: Availability, Throughput,
  Latency, Errors, Saturation / Internal State, Replication / Consistency. Each domain maps to one
  rule file in this skill.
- Dominant failure archetypes the playbook calls out: GC Death Spiral; Compaction Death Spiral;
  Tombstone Storm; Disk Space Exhaustion; Hint Overflow.
- Netdata observes the signals listed in the rule files via its native collectors, plus any
  OpenTelemetry-shipped metrics that your Apache Cassandra instrumentation adds. Both paths end at
  the same MCP query surface.
- Netdata's cassandra collector emits 28 context(s) under `cassandra.*`. The rule files enumerate
  which contexts surface which domain; the Verification section below names the load-bearing ones
  explicitly.

## Step-by-step

1. Confirm the Apache Cassandra service is up. Query Netdata via MCP with `list_nodes` and filter by
   the host running the target. A missing node means the symptom is at the network or orchestrator
   layer, not inside the service.
2. Pull the last 15 minutes of signals for the target. Use `query_metrics` against the contexts
   listed in the domain rule files. Run `find_anomalous_metrics` in parallel over the same window;
   anomalies frame which rule file to read first.
3. Check for **GC Death Spiral**. Heap pressure then long GC pauses then gossip failures then node
   marked DOWN then client retries flood then more heap pressure. Self-reinforcing. Inspect the rule
   file whose signals move first for this mode.
4. Check for **Compaction Death Spiral**. Write rate exceeds compaction throughput then SSTables
   accumulate then read amplification increases then latency spikes then more compaction needed then
   disk I/O saturated. Inspect the rule file whose signals move first for this mode.
5. Check for **Tombstone Storm**. Accumulated tombstones (deletes/expired TTLs) force reads to scan
   massive amounts of dead data then read latency spikes, possible query abortion at 100K
   tombstones. Inspect the rule file whose signals move first for this mode.
6. Check for **Disk Space Exhaustion**. Compaction backlog + snapshots + hints consume space then
   compaction cannot run (needs temporary space) then writes blocked. Inspect the rule file whose
   signals move first for this mode.
7. Check for **Hint Overflow**. Long node outage then hints accumulate on coordinators then hints
   expire (`max_hint_window`, default 3h) then data permanently inconsistent unless repaired.
   Inspect the rule file whose signals move first for this mode.
8. Correlate with host-level signals (`system.cpu.utilization`, `system.memory.usage`,
   `system.disk.io_time`). Many service-level failures have a host-resource precursor.
9. Apply the remediation hinted at in the matching rule file or the operator playbook. Re-run the
   MCP queries from the Verification section to confirm the signals returned to expected ranges. A
   fix that does not move the signal back is not a fix.

### Handy MCP call templates

```text
# Discover metrics from Apache Cassandra
list_metrics with q="cassandra"

# Pull a specific context over the last window
query_metrics with context="cassandra.dropped_messages_rate", relative_window=-15m

# Rank anomalies for the service or host
find_anomalous_metrics with node=<host> and context_pattern="cassandra.*"

# Correlate a known problem context with others
find_correlated_metrics around the incident window

# Show current alert state
list_raised_alerts scoped to the node
```

## Common mistakes

- Treating Apache Cassandra as a generic HTTP or process health check. Apache Cassandra has specific
  failure archetypes (see Key facts) that generic checks miss.
- Stopping at the first anomalous metric. Several archetypes produce correlated spikes; use
  `find_correlated_metrics` to widen the search before concluding a root cause.
- Quoting percentile latency without the sample count. Low traffic plus a single slow request moves
  p99 by seconds.
- Reading dashboards for a window shorter than the failure's fingerprint. Slow-brew failures (queue
  growth, bloat, memory fragmentation) need 30+ minutes of data to see the trend.
- Skipping the host-level correlation. A process-level fix for a noisy-neighbour problem does not
  hold.
- Assuming alert thresholds are tuned for your workload. Tune against observed Apache Cassandra
  traffic before escalating an alert configuration issue.

## Verification

Run these MCP queries against the Netdata instance that sees the Apache Cassandra service. Every
context listed below is a real Netdata chart name; the agent does not need to guess.

```text
1. list_metrics filtered by q="cassandra" (returns every cassandra.* context Netdata sees)
2. query_metrics with contexts=[cassandra.dropped_messages_rate, cassandra.client_requests_timeouts_rate, cassandra.client_requests_failures_rate, cassandra.client_requests_rate, cassandra.client_requests_latency, cassandra.row_cache_hit_rate] and relative_window=-30m
3. find_anomalous_metrics filtered by node=<host> and context_pattern="cassandra.*"
```

Load-bearing contexts for this service:

- `cassandra.dropped_messages_rate`: Dropped messages rate (messages/s). Dimensions: dropped.
- `cassandra.client_requests_timeouts_rate`: Client requests timeouts rate (timeout/s). Dimensions:
                                             read, write.
- `cassandra.client_requests_failures_rate`: Client requests failures rate (failures/s). Dimensions:
                                             read, write.
- `cassandra.client_requests_rate`: Client requests rate (requests/s). Dimensions: read, write.
- `cassandra.client_requests_latency`: Client requests total latency (seconds). Dimensions: read,
                                       write.
- `cassandra.row_cache_hit_rate`: Key cache hit rate (events/s). Dimensions: hits, misses.

A clean result means every context is within its expected band and the `find_anomalous_metrics` list
is empty or contains only already-acknowledged items. If the fix was real, re-running the same
queries 10 minutes after applying it will show a clean result. If it does not, revert and look
deeper.

### When the fix does not hold

If signals drift back into the anomalous range within 30 minutes of a remediation, the cause was
deeper than the applied change. Typical misdiagnoses for Apache Cassandra:

- Host-resource pressure masquerading as application bug.
- Dependent service (DB, cache, upstream) causing a secondary symptom in the instrumented service.
- Configuration change that was never reloaded (some subsystems only pick up config on full
  restart).

Escalate by widening the query window: 2-6 hours instead of 15 minutes. Slow-moving causes are
invisible at triage window sizes.

## References

- [`rules/availability.md`](./rules/availability.md)
- [`rules/throughput.md`](./rules/throughput.md)
- [`rules/latency.md`](./rules/latency.md)
- [`rules/errors.md`](./rules/errors.md)
- [`rules/saturation-internal-state.md`](./rules/saturation-internal-state.md)
- [`rules/replication-consistency.md`](./rules/replication-consistency.md)
- [`rules/cache-performance.md`](./rules/cache-performance.md)
- [`rules/security-integrity.md`](./rules/security-integrity.md)
- Netdata operator playbook: the authoritative source material this skill summarizes.
- `skills/netdata-mcp-integration/` for the transport setup.
- `skills/netdata-otel-setup/` if additional application signals are needed beyond what Netdata
  collects natively.
