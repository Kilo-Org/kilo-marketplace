# WarpStream Client Optimization

WarpStream is Kafka-protocol-compatible but architecturally different from Apache Kafka: stateless Agents write directly to object storage (e.g., S3) instead of broker-local disks. This eliminates replication, disk management, and inter-broker traffic — but changes the performance profile. **A few small client configuration changes can result in 10-20x higher throughput.**

Read this reference whenever the user's target environment is WarpStream. Apply these overrides on top of the standard config baseline for the relevant skill.

**Reference docs:** [WarpStream configuration recommendations](https://docs.warpstream.com/warpstream/kafka/configure-kafka-client/tuning-for-performance.md)

---

## Why Defaults Must Change

| Kafka assumption | WarpStream reality |
|---|---|
| Produce latency is single-digit ms | Produce latency is ~250ms p50 / ~500ms p99 (data must flush to object storage) |
| Each broker owns specific partitions | Any Agent can serve any partition — Agents are stateless and interchangeable |
| `fetch.min.bytes` controls batching | `fetch.min.bytes` is **not supported** by WarpStream |
| Replication factor controls durability | Durability comes from object storage (11 nines); `replication.factor` is cosmetic (hard-coded to 3) |
| Idempotent producers have minimal overhead | Idempotent producers reduce throughput (see [Idempotent Producers and EOS](#idempotent-producers-and-eos)) |

---

## Java Client Overrides (Kafka Streams, Kafka Clients)

Apply these on top of the standard config baseline. Properties not listed here remain unchanged.

### Producer

```properties
# Disable idempotence for throughput (see warning above)
enable.idempotence=false

# With idempotence disabled, increase in-flight requests dramatically
max.in.flight.requests.per.connection=1000

# Larger batches amortize object-storage write latency
batch.size=100000
linger.ms=100

# Larger buffer to sustain high in-flight request count
buffer.memory=128000000

# Allow large requests
max.request.size=64000000

# LZ4 compression (WarpStream decompresses and recompresses for storage)
compression.type=lz4

# Higher request timeout for object-storage flush
request.timeout.ms=30000

# Reduce unnecessary metadata refreshes
metadata.max.age.ms=60000

# Rebootstrap on metadata errors (useful when Agents scale)
metadata.recovery.strategy=rebootstrap
```

### Consumer

```properties
# Large fetch sizes — WarpStream appears as a single broker,
# so per-partition limits are the effective bottleneck
fetch.max.bytes=50242880
max.partition.fetch.bytes=50242880

# Long wait — fetch.min.bytes is NOT supported by WarpStream,
# so fetch.max.wait.ms controls how long the Agent waits before responding
fetch.max.wait.ms=10000
```

### Kafka Streams Specific

```properties
# Override the producer/consumer defaults within Streams
producer.batch.size=100000
producer.linger.ms=100
producer.enable.idempotence=false
producer.max.in.flight.requests.per.connection=1000
producer.buffer.memory=128000000
producer.max.request.size=64000000
producer.request.timeout.ms=30000

consumer.fetch.max.bytes=50242880
consumer.max.partition.fetch.bytes=50242880
consumer.fetch.max.wait.ms=10000

# Do NOT set consumer.fetch.min.bytes — unsupported by WarpStream

# Metadata
metadata.max.age.ms=60000
metadata.recovery.strategy=rebootstrap
```

**EOS note for Kafka Streams:** If the user's existing app uses `processing.guarantee=exactly_once_v2`, inform them of the tradeoff:

> EOS enables idempotent producers internally (max 5 in-flight requests). On WarpStream, this reduces throughput and may produce `KAFKA_STORAGE_ERROR` retries. Consider whether `at_least_once` with downstream deduplication would work for your use case. If EOS is required, it will work — plan for additional capacity.

---

## librdkafka / confluent-kafka-python Overrides

These apply to any client built on librdkafka, including `confluent-kafka-python`, `confluent-kafka-go`, and `node-rdkafka`.

### Producer

```properties
queue.buffering.max.kbytes=1048576
queue.buffering.max.messages=1000000
message.max.bytes=64000000
batch.size=16000000
batch.num.messages=100000
linger.ms=100
sticky.partitioning.linger.ms=25
enable.idempotence=false
max.in.flight.requests.per.connection=1000000
partitioner=consistent_random
request.timeout.ms=30000
```

### Consumer

```properties
fetch.max.bytes=50242880
max.partition.fetch.bytes=50242880
fetch.wait.max.ms=10000
```

### librdkafka Version Notes

- **librdkafka < 2.8:** Leader epoch mismatch errors. WarpStream returns epoch 0; librdkafka 2.4+ expects monotonically increasing epochs. Workaround: append `ws_sle=true` to `client.id` (e.g., `client.id=my-app,ws_sle=true`). Best fix: upgrade to librdkafka 2.8+.
- **librdkafka < 2.10:** Retains stale Agent IP addresses during rolling restarts. Upgrade to 2.10.0+.

---

## Kafka Connect Overrides (CDC / Connectors)

When running Kafka Connect against WarpStream, set these worker-level overrides via environment variables:

```bash
# Consumer overrides
CONNECT_CONSUMER_FETCH_MAX_BYTES=50242880
CONNECT_CONSUMER_MAX_PARTITION_FETCH_BYTES=50242880
CONNECT_CONSUMER_FETCH_MAX_WAIT_MS=10000

# Producer overrides
CONNECT_PRODUCER_ENABLE_IDEMPOTENCE=false
CONNECT_PRODUCER_MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION=1000
CONNECT_PRODUCER_LINGER_MS=100
CONNECT_PRODUCER_BATCH_SIZE=100000
CONNECT_PRODUCER_BUFFER_MEMORY=128000000
CONNECT_PRODUCER_MAX_REQUEST_SIZE=64000000
CONNECT_PRODUCER_COMPRESSION_TYPE=lz4
CONNECT_PRODUCER_METADATA_MAX_AGE_MS=60000
CONNECT_PRODUCER_METADATA_RECOVERY_STRATEGY=rebootstrap
```

**Note:** CDC pipelines targeting WarpStream will have ~250-500ms additional latency per hop compared to standard Kafka, which may matter for near-real-time use cases.

---

## Idempotent Producers and EOS

Enabling idempotent producers (`enable.idempotence=true`) or Exactly-Once Semantics (`processing.guarantee=exactly_once_v2`) reduces throughput on WarpStream. This is because idempotence limits `max.in.flight.requests.per.connection` to 5, and WarpStream's higher produce latency means those slots are occupied longer. The Java client may also see retriable `KAFKA_STORAGE_ERROR` errors due to frequent partition ownership shifts between Agents.

The client config overrides above already set `enable.idempotence=false` — this is the recommended default. If EOS is required, it will work — plan for additional capacity to compensate for the reduced concurrency.

For Kafka Streams specifically: prefer `processing.guarantee=at_least_once` (the default) with downstream deduplication when possible.

---

## Zone-Aware Routing

WarpStream charges for cross-AZ network transfer. To eliminate this cost, append `ws_az=<availability-zone>` to the Kafka `client.id`:

```properties
client.id=my-app,ws_az=us-east-1a
```

This tells WarpStream's service discovery to route the client to an Agent in the same availability zone. Without it, clients may be routed cross-AZ, incurring ~$0.05/GB on AWS.

**Do NOT enable Kafka's `client.rack` or rack-aware consumer assignment** — these cause unnecessary rebalances with WarpStream since Agents are stateless and interchangeable.

For Kafka Streams, set `client.id` in the Streams config (not `application.id`) — Streams uses `client.id` as the base for producer/consumer client IDs.

---

## Sticky Partitioning

WarpStream Agents batch records across topics and partitions into combined object-storage files. Larger batches = fewer S3 PUTs = lower cost and higher throughput.

To maximize batch sizes:
- **Use null message keys** whenever ordering between records is not required. This enables sticky partitioning, where the client accumulates records for a single partition before rotating.
- **Avoid explicit partition assignment** (`partition=N` in produce calls).
- Only use message keys when entity-based ordering is genuinely needed (e.g., all events for the same `order_id` must be on the same partition).

---

## Latency Expectations and Tuning

WarpStream defaults to maximum throughput and minimal cost at the expense of higher latency compared to standard Kafka.

| Configuration | p50 Produce | p99 Produce |
|---|---|---|
| Default (S3 Standard) | ~250ms | ~500ms |
| Reduced linger + batch timeout | ~150ms | ~300ms |
| S3 Express One Zone | <80ms | <150ms |
| S3 Express + Lightning Topics | <35ms | <50ms |

**To reduce latency** (cumulative strategies):
1. Reduce client `linger.ms` from 100 to 10-25ms (no cost increase).
2. Reduce Agent `WARPSTREAM_BATCH_TIMEOUT` from 250ms to 25ms (increases S3 API costs).
3. Use a higher WarpStream virtual cluster tier (Pro and Enterprise tiers batch fewer metadata operations).
4. Enable **Lightning Topics** — skips synchronous control plane commit on produce (relaxed consistency).
5. Use **S3 Express One Zone** storage class (~20% cost increase).

Present these options when the user expresses latency concerns. Most users should start with the throughput-optimized defaults.

---

## Things That Don't Apply on WarpStream

These standard Kafka configurations are irrelevant or cosmetic on WarpStream — do not set or tune them:

| Config | Why irrelevant |
|---|---|
| `replication.factor` | Always returns 3 (cosmetic). Durability is from object storage. |
| `min.insync.replicas` | Always returns 1. |
| `num.io.threads` / `num.network.threads` | Java broker tunables. WarpStream Agents are written in Go. |
| `log.dirs` / `broker.id` | No local disks, no static broker identities. |
| `log.retention.bytes` | Not supported (hard-coded to -1). Use `log.retention.ms` instead. |
| `fetch.min.bytes` | Not supported. Use `fetch.max.wait.ms` instead. |
| Replica management APIs | `AlterReplicaLogDirs`, `ElectLeaders`, etc. are unsupported. |

---

## Known Client-Specific Issues

### Sarama (Go)
- **Not recommended.** Sarama has liveness and correctness issues with WarpStream, including message ordering failures and data loss risks.
- Use **franz-go** instead.

### Java Client
- With idempotent producers enabled, expect retriable `KAFKA_STORAGE_ERROR` errors due to frequent partition ownership shifts between Agents.
- `metadata.recovery.strategy=rebootstrap` helps recover from stale metadata after Agent scaling events.

### librdkafka
- See version notes above (epoch mismatch < 2.8, stale IPs < 2.10).
- WarpStream's fetch size auto-tuning (`WARPSTREAM_AUTO_TUNE_FETCH_LIMITS=true`, on by default) interprets fetch limits as **uncompressed** bytes, not compressed. If this causes excessive memory usage, disable per-client with `ws_dfat=true` in the client ID.

---

## Compacted Topics

WarpStream supports `cleanup.policy=compact` with these limitations:
- Cannot switch between `delete` and `compact` after topic creation.
- Deduplication buffer is 128 MB per partition (~3.27M distinct keys max). Beyond this, duplicates may persist.
- Partitions exceeding 128 GiB uncompressed data may retain duplicates.
- Compaction scheduling is automatic and not configurable (unlike Kafka's `log.cleaner.min.cleanable.ratio`).

---

## Quick Checklist

When generating code or configs for a WarpStream target, verify:

- [ ] `enable.idempotence=false` (unless user requires EOS — inform them of the throughput tradeoff)
- [ ] `max.in.flight.requests.per.connection` raised (1000 Java, 1000000 librdkafka)
- [ ] `linger.ms=100` (or 10-25 for low-latency)
- [ ] `batch.size` increased (100KB+ Java, 16MB librdkafka)
- [ ] `fetch.max.bytes` and `max.partition.fetch.bytes` set to ~50MB
- [ ] `fetch.max.wait.ms=10000`
- [ ] `fetch.min.bytes` NOT set (unsupported)
- [ ] `metadata.max.age.ms=60000`
- [ ] `client.id` includes `ws_az=<az>` for zone-aware routing
- [ ] `compression.type=lz4`
- [ ] No `replication.factor` tuning (cosmetic on WarpStream)
- [ ] Kafka Streams: `processing.guarantee=at_least_once` preferred (if user needs `exactly_once_v2`, inform them of throughput tradeoff)
