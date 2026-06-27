# Debugging Kafka Streams Applications

Diagnostic guide organized by symptom. Start from what the user sees, then work backward to the root cause.

**Docs:** [Monitoring](https://docs.confluent.io/platform/current/streams/monitoring.md) | [Troubleshooting](https://docs.confluent.io/platform/current/streams/developer-guide/running-app.md)

## Table of Contents
- [Startup Failures](#startup-failures)
- [Processing Stalls](#processing-stalls)
- [Rebalancing Issues](#rebalancing-issues)
- [Performance](#performance)
- [Deserialization Errors](#deserialization-errors)
- [State Store Issues](#state-store-issues)
- [Thread Failures](#thread-failures)
- [Memory Issues](#memory-issues)
- [Key Metrics to Monitor](#key-metrics)
- [Confluent Cloud Gotchas](#confluent-cloud-gotchas)
- [Security / ACL Issues](#security--acl-issues)
- [EOS / Transaction Issues](#eos--transaction-issues)
- [Additional Failure Patterns](#additional-failure-patterns)
- [Common Error Messages](#common-error-messages)

---

## Startup Failures

### UnsupportedVersionException on startup
**Cause:** `group.protocol=streams` (KIP-1071) requires AK 4.2+ / CP 8.2+. Broker is too old.
**Fix:** Remove `group.protocol=streams` from config. Upgrade broker when possible.

### TopologyException: Invalid topology
**Cause:** Topology is invalid — often due to missing source topics, duplicate store names, or circular dependencies.
**Fix:** Check `TopologyBuilder.build()` — verify all source topics exist and all store names are unique.

### StreamsException: Could not find state directory
**Cause:** `state.dir` points to a non-existent or non-writable directory.
**Fix:** Create the directory or change `state.dir`. In containers, ensure the directory is mounted and writable.

### Schema Registry connection timeout / serde hang
**Cause:** Confluent SR serdes call the Schema Registry during `configure()`. If SR is unreachable, the app hangs.
**Diagnosis:**
1. Verify SR URL is reachable: `curl <SR_URL>/subjects`
2. Ask user: SR API key/secret correct? NEVER read the actual credentials whether in a .env file or a properties file
3. Enable DEBUG logging: `io.confluent.kafka.serializers=DEBUG`
4. Check version compatibility: Confluent serde version should match SR version
**Fix:** Fix SR URL, auth, or network connectivity. The serde will initialize once SR is reachable.

### ConfigException: Missing required config
**Common missing configs:**
- `application.id` — always required
- `bootstrap.servers` — always required
- `default.key.serde` / `default.value.serde` — required when any internal topic is created (groupBy, selectKey, join)

---

## Processing Stalls

### App runs but produces no output

**Diagnostic steps:**
1. **Check consumer lag:** Are input topics getting new records?
   ```bash
   # CC
   confluent kafka consumer-group describe <application.id>
   # Local
   kafka-consumer-groups --bootstrap-server localhost:9092 --group <application.id> --describe
   ```
2. **Check state:** Is the app in RUNNING state? Check `/health/ready` or logs for state transitions.
3. **Check for exceptions:** Look for `LogAndContinueExceptionHandler` messages — the app may be dropping all records due to deserialization errors.
4. **Check filter predicates:** If you have `.filter()`, is the predicate excluding all records?
5. **Check join windows:** For stream-stream joins, records outside the join window are silently dropped.

### App processes slowly then stops

**Likely cause:** `max.poll.interval.ms` exceeded → consumer evicted → rebalance → state restoration → evicted again (loop).
**Fix:** Increase `consumer.max.poll.interval.ms` or reduce `consumer.max.poll.records`.

### Stream-table join produces nulls

**Causes:**
1. **Table not populated yet:** The KTable reads from a compacted topic. If the stream arrives before the table is populated, joins return null.
   - Fix: Pre-populate the table topic before starting the stream, or use `leftJoin()` and handle nulls.
2. **Co-partitioning violation:** Stream and table must have the same number of partitions and the same partitioning strategy.
   - Fix: Ensure both topics have the same partition count and are keyed the same way.
3. **Key mismatch:** The stream key must match the table key exactly (same type, same serialization).

---

## Rebalancing Issues

### Constant rebalancing / rebalance storm

The most common P1 pattern in production Kafka Streams deployments. The cascade: processing exceeds `max.poll.interval.ms` → consumer evicted → rebalance → state restoration → restoration exceeds `max.poll.interval.ms` → evicted again → loop.

**Diagnostic runbook:**
1. **Check `max.poll.interval.ms` violation:**
   - Look for: `Member consumer-<id> has exceeded max.poll.interval.ms`
   - Fix: Increase `consumer.max.poll.interval.ms` (default: 300000 = 5 min)
2. **Check if state restoration is the bottleneck:**
   - Look for: `Restoration in progress for N partitions`
   - If so, restoration itself exceeds poll timeout. See "State Restoration Cascade" below.
3. **Check processing time:**
   - Monitor `process-latency-max` and `punctuate-latency-max`
   - Common culprits: blocking external calls (REST, DB), full state store scans in punctuators, slow RocksDB operations
4. **Check instance stability:** Are instances crashing and restarting? (K8s OOM kills, health check failures). For stateful apps, **also compute expected RocksDB off-heap memory** using `architecture.md` § Memory — container OOMs from undersized memory requests are a frequent rebalance root cause.
5. **Check for CPU throttling:** K8s CPU limits cause poll delays → rebalances. Never set CPU limits on KS containers.

**Config relationship rules (must all hold):**
- `session.timeout.ms` <= `max.poll.interval.ms` (with cooperative protocol)
- `request.timeout.ms` >= `max.poll.interval.ms`
- For EOS: `transaction.timeout.ms` <= `max.poll.interval.ms`

### 10-Minute Rebalance Loop (Probing Rebalance)

**Symptom:** App stabilizes, runs for exactly 10 minutes, then rebalances again. Repeats indefinitely.

**Root cause:** `probing.rebalance.interval.ms` defaults to 600000 (10 min). When standby replicas never fully catch up, the probing rebalance fires to redistribute tasks, but nothing changes — the same pattern repeats.

**Diagnosis:**
1. Check if rebalances occur on a regular interval (~10 min)
2. Check standby replica lag — are they keeping up?
3. Check changelog topic compaction — is there too much data to replay?

**Fix:**
- Increase `acceptable.recovery.lag` to allow standbys more time
- Increase `probing.rebalance.interval.ms` (e.g., to 86400000 = 24h) if probing isn't needed
- Ensure changelog topic compaction is configured correctly

### Broker Failover Causing Streams Disconnect

**Symptom:** All streams disconnect simultaneously after a broker goes down. `COORDINATOR_NOT_AVAILABLE` or `DisconnectException`.

**Root cause:** The consumer group coordinator was on the failed broker. Reconnection takes longer than `session.timeout.ms`, causing all consumers to be evicted.

**Fix:**
- Set `session.timeout.ms` >= 60000ms for production
- Increase `reconnect.backoff.max.ms` for transient reconnections
- Use `num.standby.replicas=1` for faster task failover

### Stuck After Partial Shutdown

**Symptom:** After partial restart (some pods still in group while others restart), new instances see "group is already rebalancing" repeatedly and cannot join.

**Root cause:** Zombie members hold the group generation, preventing clean rejoin.

**Fix:**
1. Stop ALL instances of the application
2. Wait for `session.timeout.ms` to expire
3. Restart incrementally
4. Implement proper shutdown hooks: `streams.close(Duration.ofSeconds(30))` with `Runtime.getRuntime().addShutdownHook()`
5. In K8s, set `terminationGracePeriodSeconds` >= `close()` timeout

### Rebalance takes a long time

**With KIP-1071 (`group.protocol=streams`):** Rebalances should be fast (seconds). If slow, check broker logs.
**Without KIP-1071:** Use cooperative-sticky rebalancing (default since KS 2.4). Long rebalances usually mean state restoration.

---

## Performance

### High consumer lag

1. **Not enough parallelism:** Threads × instances < input partitions means some partitions are unprocessed.
   - Fix: Add instances or increase `num.stream.threads`
2. **Slow processing:** Topology operations taking too long.
   - Check `active-process-ratio` metric — should be > 0.5. Below 0.5 means the app spends more time polling than processing.
   - Check for blocking calls in topology (REST APIs, DB writes)
3. **Producer backpressure:** Output topic is slow to accept writes.
   - Check `producer.batch.size`, `producer.linger.ms`, `producer.compression.type`
4. **State store bottleneck:** RocksDB writes are slow.
   - Check RocksDB metrics, consider increasing `statestore.cache.max.bytes`

### High latency (records take a long time from input to output)

1. **Commit interval too high:** `commit.interval.ms=30000` means up to 30s before records are committed and visible downstream.
   - Fix: Reduce `commit.interval.ms` (tradeoff: more frequent commits = more overhead)
2. **Cache deduplication:** `statestore.cache.max.bytes` deduplicates updates. Larger cache = fewer downstream updates but higher latency.
   - Fix: Reduce cache size or set to 0 for lowest latency (tradeoff: more downstream traffic)
3. **Suppression:** If using `Suppressed.untilWindowCloses()`, output is delayed until the window closes + grace period.
4. **Producer batching:** `producer.linger.ms` adds intentional delay for batching.

---

## Deserialization Errors

### "Unknown magic byte!"
**Cause:** Record was produced without Schema Registry (plain `kafka-console-producer`). SR serdes expect a 5-byte header (magic byte + schema ID).
**Fix:** Re-produce data using schema-aware producers (`kafka-avro-console-producer`, etc.).

### ClassCastException: LinkedHashMap cannot be cast to MyPojo
**Cause:** JSON Schema serde missing `json.value.type` config. Without it, Jackson deserializes to `LinkedHashMap`.
**Fix:** Set `json.value.type=com.example.MyPojo` on the serde.

### "Cannot construct instance of MyPojo (no Creators)"
**Cause:** JSON Schema POJO missing no-arg constructor (Jackson requirement).
**Fix:** Add `public MyPojo() {}` to the class.

### DynamicMessage instead of typed Protobuf message
**Cause:** Protobuf serde missing `specific.protobuf.value.type` config.
**Fix:** Set `specific.protobuf.value.type=com.example.proto.MyMessage` on the serde.

### Schema incompatibility errors
**Cause:** Schema evolution broke compatibility. New schema can't read old data (or vice versa).
**Fix:** Check SR compatibility settings. Reset if needed — see `references/verification.md` § Resetting Application State.

---

## State Store Issues

### State store growing without bound
**Cause:** KTable or state store accumulates all unique keys without expiration.
**Fix:** Set TTL via `Materialized.withRetention(Duration.ofDays(30))` or produce tombstones (null values) for expired keys.

### State Restoration Cascade

After pod/instance restart, state stores rebuild from changelog topics. For large stores (tens to hundreds of GB), this takes minutes to hours. During restoration, the consumer cannot process records, exceeds `max.poll.interval.ms`, gets evicted, triggering another rebalance, which cancels and restarts restoration — a death spiral.

**Diagnosis:**
1. Look for `Restoration in progress for N partitions` in logs
2. Check `max.poll.interval.ms` vs estimated restoration time
3. Check if persistent volumes (PVCs) are used — ephemeral storage forces full restoration on every restart
4. **Compute expected RocksDB memory for the user's topology** using the per-store formula in `architecture.md` § Memory (block_cache 50MB + write_buffers 16MB × 3 ≈ 98MB per store-partition; multiply by partitions/instance × stores × segments for windowed). Container OOMs and oversized JVM heap that starves RocksDB are common rebalance triggers.

**Fix:**
1. **Use persistent volumes (PVCs) in K8s** — avoids full restoration on pod restart (critical for stateful apps)
2. Increase `consumer.max.poll.interval.ms` to at least 2x expected restoration time
3. Increase `restore.consumer.fetch.max.bytes` to 50MB+ to speed up restoration
4. Add `num.standby.replicas=1` for warm standby
5. Use `acceptable.recovery.lag` to control when tasks are considered caught up

### Large State Store Pathology

Applications with very large state stores (100GB+ per partition) experience increasing latency for state store operations. This is one of the most common causes of prolonged production outages.

**Root cause:** Full-scan operations (`store.all()`, `seekToFirst()`) in punctuators on large RocksDB stores. The stream thread spends minutes in RocksDB, blocking commits and heartbeats. This causes `DisconnectException`, rebalances, and cascading failures.

**Key factors:**
- **Tombstone accumulation:** Delete-heavy workloads (queue-like patterns) create tombstones that `all()` scans must traverse. Tombstones accumulate at the head of the keyspace until compaction.
- **Iterator lifecycle:** Long-lived or leaked iterators pin RocksDB resources. Monitor `num-open-iterators` and `oldest-iterator-open-since-ms`.

**Diagnosis:**
1. Thread dumps show streams thread stuck in RocksDB `seekToFirst()` (RUNNABLE state)
2. Punctuator callbacks taking minutes (e.g., 30s commit interval taking ~10 minutes)
3. `live-sst-files-size` growing unexpectedly
4. `compaction-pending` staying high

**Fix:**
1. **Replace `store.all()` with `store.range(lastProcessedKey, null)`** — process in batches, avoid full scans
2. Tune RocksDB compaction for delete-heavy workloads (`CompactionStyle.UNIVERSAL`)
3. Increase background compaction threads
4. Add instrumentation to punctuators (log time per operation, records processed)

**RocksDB metrics to monitor:**
- `compaction-pending`, `num-running-compactions`
- `mem-table-flush-pending`, `num-running-flushes`
- `block-cache-usage` / `block-cache-capacity` / `block-cache-pinned-usage`
- `live-sst-files-size`, `total-sst-files-size`
- `cur-size-all-mem-tables`
- `num-open-iterators`, `oldest-iterator-open-since-ms`

### State restoration takes too long
**Causes and fixes:**
1. **Large state:** Reduce state size with TTL or tombstones
2. **Slow network:** Increase `restore.consumer.fetch.max.bytes` (default 1MB → 50MB)
3. **No standbys:** Add `num.standby.replicas=1` — standbys stay warm and take over without full restoration
4. **Compaction lag:** Changelog topic hasn't been compacted — more data to replay than needed. Run compaction on the broker.

### "Error restoring store from changelog" / corruption
**Fix:** Full reset procedure:
1. Stop the app
2. Delete local state: `rm -rf <state.dir>/<application.id>`
3. Run `kafka-streams-application-reset`
4. Restart

See `references/verification.md` § Resetting Application State for the full procedure.

---

## Thread Failures

### StreamThread dies and isn't replaced
**Cause:** No `UncaughtExceptionHandler` set — default behavior is to shut down the entire app on any thread failure.
**Fix:** Add `MaxFailuresUncaughtExceptionHandler` (see SKILL.md § Invariant 4).

### Thread replaced but same error repeats
**Cause:** The failing record is retried after thread replacement, causing the same exception.
**Fix:**
1. Add defensive null/validation checks in topology lambdas
2. Use `ProcessingExceptionHandler` (KIP-1034) to route bad records to DLQ
3. If the error is in the deserialization layer, use `LogAndContinueExceptionHandler`

### "ProducerFencedException"
**Causes:**
1. **EOS with slow operations:** Transaction timeout (10s default) exceeded.
   - Fix: Increase `transaction.timeout.ms`
2. **Zombie instance:** An old instance is still running with the same `application.id`.
   - Fix: Stop the old instance. Only one instance per task should be active with EOS.
3. **Transactional.id expired:** App was idle > 7 days on CC.
   - Fix: Restart with a new `application.id`, or handle `InvalidPidMappingException` in UncaughtExceptionHandler

---

## Memory Issues

### OutOfMemoryError (JVM heap)
1. **Reduce `statestore.cache.max.bytes`** — this is on-heap (default 10MB per thread)
2. **Reduce `num.stream.threads`** — each thread has its own cache allocation
3. **Increase JVM heap** — but leave room for RocksDB off-heap

### Container OOM killed (but JVM heap is fine)
**Cause:** RocksDB off-heap memory exceeds container limit.
**Fix:**
1. Calculate RocksDB memory: `(block_cache + write_buffers) × instances` — see architecture.md
2. Set `MaxRAMPercentage=75` to leave 25% for RocksDB
3. Reduce RocksDB memory with custom `RocksDBConfigSetter` (smaller block cache, fewer write buffers)

### Memory keeps growing
1. **Unbounded state store:** KTable accumulating data without TTL. Fix: add `.withRetention()`.
2. **Unbounded suppression buffer:** Using `Suppressed.BufferConfig.unbounded()` in production. Fix: use `maxRecords(N).shutDownWhenFull()`.
3. **Memory leak in topology lambda:** Custom objects retained across calls. Fix: avoid stateful lambdas.

---

## Confluent Cloud Gotchas

### Topics must be pre-created
CC always has `auto.create.topics.enable=false`. Source, output, and DLQ topics must be created before the app starts. KS internal topics (changelog, repartition) are auto-created if the service account has `CREATE` with prefix ACL matching `application.id`.

### ACLs required for Kafka Streams on CC
KS apps need more permissions than a simple consumer/producer:

| Resource | Operation | Pattern |
|----------|-----------|---------|
| Consumer Group | `READ` | `application.id` |
| Source topics | `READ` | Exact topic name |
| Output topics | `WRITE` | Exact topic name |
| Internal topics | `READ`, `WRITE`, `CREATE` | Prefixed with `application.id` |
| Transactional ID (EOS) | `WRITE` | Prefixed with `application.id` |
| Cluster (EOS) | `IDEMPOTENT_WRITE` | Cluster resource |

Missing any of these causes `TopicAuthorizationException`, `GroupAuthorizationException`, or silent failures.

### CKU throughput limits
When a KS app exceeds CKU produce/consume byte limits, requests are throttled, causing `TimeoutException` and potential rebalances. Monitor `received_bytes` and `sent_bytes` in the CC Console. Fix: increase CKU allocation or distribute writes across more partitions.

### Broker logs not available
On CC, broker logs are not available to customers. All troubleshooting must rely on client-side logs. Enable DEBUG for `org.apache.kafka.streams` and `org.apache.kafka.clients.consumer`.

### Audit log growth from KS
KS apps perform frequent `DeleteRecords` on repartition topics, generating audit log events. At scale, this can cause `confluent-audit-log-events` to grow at hundreds of records/sec. Fix: configure audit log routing to exclude `kafka.DeleteRecords` on internal topics.

---

## Security / ACL Issues

### TopicAuthorizationException on internal topics
**Error:** `TopicAuthorizationException` on changelog or repartition topics.
**Cause:** ACLs set for source/output topics but not for KS internal topics. Internal topics follow `<application.id>-<operator-name>-<suffix>`.
**Fix:** Grant `READ`, `WRITE`, `CREATE` with a prefix ACL matching `application.id`:
```bash
kafka-acls --bootstrap-server <broker> --add \
  --allow-principal User:<service-account> \
  --operation READ --operation WRITE --operation CREATE \
  --topic <application.id> --resource-pattern-type prefixed
```

### mTLS certificate rotation
After certificate rotation, all KS instances must be restarted with updated keystores/truststores. Symptoms: `SSL handshake failed`, consumers missing from group, inconsistent connectivity across instances.
**Fix:** Update certs → rolling restart brokers → rolling restart KS instances. Verify: `openssl s_client -connect <broker>:<port>`.

---

## Key Metrics

### Thread-level
| Metric | What it means | Healthy range |
|--------|--------------|---------------|
| `alive-stream-threads` | Active threads | Should equal `num.stream.threads` |
| `failed-stream-threads` | Threads that died | Should be 0 |
| `process-rate` | Records/sec processed | Depends on workload |
| `commit-rate` | Commits/sec | ~1/commit.interval.ms |
| `active-process-ratio` | Time processing vs polling | > 0.5 |

### Task-level
| Metric | What it means | Healthy range |
|--------|--------------|---------------|
| `process-latency-avg` | Avg time to process one record | Depends on topology |
| `enforced-processing` | Whether KS forces processing | Should be rare |

### State store
| Metric | What it means | Healthy range |
|--------|--------------|---------------|
| `put-latency-avg` | Avg state store write latency | < 1ms for local SSD |
| `get-latency-avg` | Avg state store read latency | < 1ms for local SSD |
| `suppression-buffer-size-avg` | Suppression buffer size | Within configured bounds |

### How to access metrics
```java
for (Metric metric : streams.metrics().values()) {
    if (metric.metricName().group().equals("stream-thread-metrics")) {
        System.out.printf("%s = %s%n", metric.metricName().name(), metric.metricValue());
    }
}
```

Or expose via JMX for Prometheus/Grafana.

---

## EOS / Transaction Issues

### Transaction timeout cascade

**Symptoms:** Growing consumer lag on specific partitions, `ProducerFencedException` or `InvalidProducerEpochException` in client logs, broker logs showing `Completed rollback of ongoing transaction for transactionalId ... due to timeout`.

**Root cause:** Processing or state restoration takes longer than `transaction.timeout.ms` (default 10s). The transaction coordinator aborts the transaction, the producer is fenced, a rebalance is triggered, state must be restored, and the cycle repeats.

**Diagnosis:**
1. Check broker logs: `Completed rollback of ongoing transaction for transactionalId <app-id>-<uuid>-<thread> due to timeout`
2. Check client logs: `InvalidProducerEpochException: Producer attempted to produce with an old epoch`
3. Check client logs: `Detected that the thread is being fenced`
4. Check if the issue is partition-specific — data skew causes some partitions to process slower
5. Check if state restoration is in progress

**Fix:**
1. Increase `transaction.timeout.ms` — start with 60s, go higher if needed (some production apps use 900s)
2. Reduce `consumer.max.poll.records` to process fewer records per transaction
3. Set `consumer.max.poll.interval.ms` >= `transaction.timeout.ms`
4. Use `num.standby.replicas=1` to reduce restoration time

### EOS error amplification (state wipe on unhandled exceptions)

**Symptoms:** With EOS, an application bug (NPE, ClassCastException) causes multi-hour outage due to repeated state wipe and restoration.

**Root cause:** EOS requires transactional atomicity. When an unhandled exception occurs, KS aborts the transaction, wipes local state, and rebuilds from changelog. For large state stores, each error triggers 40+ minutes of restoration.

**Emergency procedure:**
1. **Immediately** switch to `processing.guarantee=at_least_once` to stop the state-wipe loop
2. Fix the application error that triggers the crash
3. Add `ProcessingExceptionHandler` (KIP-1034) to route bad records to DLQ
4. After fixing, re-enable EOS if needed

### InvalidPidMappingException (CC-specific)

**Symptoms:** `InvalidPidMappingException: The producer attempted to use a producer id which is not currently assigned to its transactional id`, growing consumer lag.

**Root cause:** On Confluent Cloud, transactional ID-to-PID mappings expire after 7 days of inactivity (non-configurable). App restart after 7+ days idle triggers this error.

**Fix:**
1. Restart the application (re-registers the transactional ID)
2. If error persists, use a new `application.id`
3. Preventive: ensure the app runs at least once per week on CC

### TxnOffsetCommitResponse disconnect (KIP-890 bug)

**Symptoms:** `Unexpected error in TxnOffsetCommitResponse: The server disconnected`, followed by `Transiting to fatal error state`. App shuts down.

**Root cause:** KIP-890 transaction verification bug. During broker rolls, the verification request receives a `DisconnectException` treated as fatal. Fixed by Apache Kafka PR #15559.

**Fix:**
1. Upgrade Kafka client libraries to a version containing the fix
2. Contact support to disable `transaction.partition.verification.enable` as temporary mitigation

### COORDINATOR_NOT_AVAILABLE after broker failure

**Symptoms:** App stops processing but does not shut down. After broker recovery, some apps auto-reconnect but others remain stuck with `IllegalStateException: Cannot attempt operation sendOffsetsToTransaction because the previous call to commitTransaction timed out`.

**Root cause:** Transaction coordinator broker unavailable. `__transaction_state` partition leaders on the failed broker. After recovery, some apps enter unrecoverable state.

**Fix:**
1. Ensure `transaction.state.log.replication.factor=3` and at least 3 healthy brokers
2. Set `replication.factor=3` for all internal topics
3. If the app is stuck after broker recovery, restart it manually
4. Monitor `alive-stream-threads` and `failed-stream-threads` metrics

---

## Additional Failure Patterns

### Cloud Load Balancer Idle Connection Drop

**Symptoms:** `DisconnectException` during long RocksDB operations on Azure/AWS/GCP. Connections dropped by load balancer after idle timeout (4-30 minutes).

**Root cause:** Stream thread busy in RocksDB does not send network traffic, load balancer drops the idle connection.

**Fix:**
- Set OS-level TCP keepalive < cloud LB idle timeout
- Tune `connections.max.idle.ms` < cloud LB idle timeout
- Fix root cause of long-running operations (see Large State Store Pathology)

### Topology Change Breaking State Stores

**Symptoms:** After deploying a new version with modified topology, the app cannot start or enters restart/restore loops.

**Root cause:** KS auto-generates internal topic and store names based on topology structure. Changing the topology changes these names, breaking compatibility.

**Fix:**
1. Use `kafka-streams-application-reset` to reset state
2. Deploy with a new `application.id` for breaking topology changes
3. Roll back to previous topology version if possible

**Prevention:**
- Use `Named.as()` on all operators to pin internal topic names
- Set `ensure.explicit.internal.resource.naming=true`
- Test topology changes in non-production with state compatibility checks

### Schema Registry Throttling (429 Errors)

**Symptoms:** Schema Registry returns HTTP 429 during startup, causing `SerializationException` or app hangs.

**Root cause:** All instances register and look up schemas simultaneously during startup. CC environments have rate limits.

**Fix:**
- Enable schema caching on the client side (default cache is usually sufficient)
- Stagger application startup to reduce concurrent SR requests
- Pre-register schemas in CI/CD pipeline
- Set `auto.register.schemas=false` in production

### SSL/TLS Certificate Rotation Breaking Streams

**Symptoms:** After SSL certificate rotation, socket timeouts and disconnections cause consumer group instability and increasing lag.

**Fix:**
- Rolling restart all KS instances after certificate rotation
- Verify new certificates are in trust store before rotation
- Increase `reconnect.backoff.max.ms` for transient reconnection issues

### Post-Upgrade / Migration Issues

**Symptoms:** After upgrading client libraries or migrating clusters, unexpected behavior: topology incompatibilities, different defaults, protocol mismatches.

**Common breaking changes to check:**
- Cooperative rebalancing becoming default (from eager)
- `exactly_once` deprecated in favor of `exactly_once_v2`
- Internal topic naming changes
- `group.protocol=streams` (KIP-1071) requiring AK 4.2+ / CP 8.2+

**Fix:**
- Test upgrades in non-production first
- Review release notes for breaking changes
- Use `ensure.explicit.internal.resource.naming=true` to pin internal topic names
- Plan for cooperative rebalancing migration if coming from older versions

---

## Quick Error Lookup

- `UnsupportedVersionException` → [§ Startup Failures](#startup-failures)
- `Unknown magic byte!` → [§ Deserialization Errors](#deserialization-errors)
- `ClassCastException: LinkedHashMap` → [§ Deserialization Errors](#deserialization-errors)
- `InvalidPidMappingException` → [§ EOS / Transaction Issues](#eos--transaction-issues)
- `ProducerFencedException` → [§ Thread Failures](#thread-failures) or [§ EOS](#eos--transaction-issues)
- `Member has exceeded max.poll.interval.ms` → [§ Rebalancing Issues](#rebalancing-issues)
- `TopicAuthorizationException` → [§ Security / ACL Issues](#security--acl-issues)
- `NO-SOURCE` in Avro build → `schema-patterns.md` (wrong directory)
- Transaction rollback due to timeout → [§ EOS / Transaction Issues](#eos--transaction-issues)
