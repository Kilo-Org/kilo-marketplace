# Configuration Baseline

Every generated app starts with this baseline. Pattern-specific configs are layered on top (see `topology-patterns.md`).

**Reference docs:** [Streams config reference](https://docs.confluent.io/platform/current/streams/developer-guide/config-streams.md)

## Core Properties

```properties
# Application identity
application.id=<user-provided-or-generated>
client.id=<application.id>

# Cluster connection
bootstrap.servers=<from-user>

# Schema Registry
schema.registry.url=<from-user>
auto.register.schemas=true  # Set to false in production

# Default serdes — required for internal topics (repartition, changelog)
# Even when using explicit serdes in Consumed.with()/Produced.with(),
# some internal operations need defaults (e.g., selectKey triggers repartition)
default.key.serde=org.apache.kafka.common.serialization.Serdes$StringSerde
# Default value serde — use the Confluent Schema Registry serde matching the user's schema format:
#   Avro:        default.value.serde=io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde
#   Protobuf:    default.value.serde=io.confluent.kafka.streams.serdes.protobuf.KafkaProtobufSerde
#   JSON Schema: default.value.serde=io.confluent.kafka.streams.serdes.json.KafkaJsonSchemaSerde
default.value.serde=<set-based-on-schema-format>

# Rebalance protocol (KIP-1071) — requires AK 4.2+/CP 8.2+
# CC rollback: if you hit UnsupportedVersionException after a CC version
# downgrade, comment this line out to fall back to the classic protocol.
# Standby/warm-up replicas and static membership require classic protocol.
group.protocol=streams

# Explicit naming (prevents state loss on topology changes)
ensure.explicit.internal.resource.naming=true

# Error handling
default.deserialization.exception.handler=org.apache.kafka.streams.errors.LogAndContinueExceptionHandler
production.exception.handler=org.apache.kafka.streams.errors.DefaultProductionExceptionHandler
task.timeout.ms=300000

# Producer best practices
# acks=all is the default since KS 3.0 — no need to set explicitly
compression.type=lz4

# Monitoring
metrics.recording.level=INFO

# Recommended defaults
num.stream.threads=1  # Start with 1, scale based on throughput needs
commit.interval.ms=30000  # 30s default for at-least-once
# IMPORTANT: Do NOT set commit.interval.ms for exactly_once_v2 apps.
# EOS defaults to 100ms and relies on this for correctness. Omit this line entirely for EOS.
```

## Security Patterns {#security-patterns}

### SASL_SSL with PLAIN {#sasl-ssl}
```properties
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
  username='<KEY>' password='<SECRET>';
```

### SASL_SSL with SCRAM-SHA-256 {#scram}
```properties
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-256
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required \
  username='<USER>' password='<PASSWORD>';
```

### mTLS {#mtls}
```properties
security.protocol=SSL
ssl.keystore.location=/path/to/client.keystore.jks
ssl.keystore.password=<password>
ssl.key.password=<password>
ssl.truststore.location=/path/to/client.truststore.jks
ssl.truststore.password=<password>
```

### OAUTHBEARER (CP RBAC/MDS) {#oauth}
```properties
security.protocol=SASL_SSL
sasl.mechanism=OAUTHBEARER
sasl.login.callback.handler.class=io.confluent.kafka.clients.plugins.auth.token.TokenUserLoginCallbackHandler
sasl.jaas.config=org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \
  username='<USER>' password='<PASSWORD>' metadataServerUrls='<MDS_URL>';
```

### SR Basic Auth {#sr-basic-auth}
```properties
basic.auth.credentials.source=USER_INFO
basic.auth.user.info=<SR_KEY>:<SR_SECRET>
```

**Manual serde configuration:** When instantiating serdes in topology code, pass SR auth to `.configure()`:
```java
Map<String, String> srConfig = Map.of(
    "schema.registry.url", srUrl,
    "basic.auth.credentials.source", "USER_INFO",
    "basic.auth.user.info", srKey + ":" + srSecret);
serde.configure(srConfig, false);
```

## Environment-Specific Configuration

### Apache Kafka (Open Source)
**Connection:** PLAINTEXT (default) or [SASL_SSL](#sasl-ssl) / [mTLS](#mtls) if configured.
**Schema Registry:** `http://localhost:8081` (no auth by default).
**CLI:** `kafka-topics.sh`, `kafka-console-consumer.sh` from AK download. Schema-aware producers ship separately.

### Confluent Platform (Self-Managed)
**Connection:** PLAINTEXT (dev) or [SASL_SSL](#sasl-ssl) / [SCRAM](#scram) / [mTLS](#mtls) / [OAUTHBEARER](#oauth) (prod).
**Schema Registry:** `http://localhost:8081`. Auth: [basic](#sr-basic-auth) or RBAC token.
**CLI:** `$CONFLUENT_HOME/bin/` — includes `kafka-topics`, `kafka-avro-console-producer`.

### Confluent Cloud (Fully Managed)
**Connection:** [SASL_SSL with PLAIN](#sasl-ssl) (always required).
**Schema Registry:** [Basic auth](#sr-basic-auth) (always required).
**CLI:** `confluent` CLI.

```properties
bootstrap.servers=<pkc-xxxxx.region.provider.confluent.cloud:9092>
# + SASL_SSL pattern
schema.registry.url=<https://psrc-xxxxx.region.provider.confluent.cloud>
# + SR basic auth pattern
```

### WarpStream
**Connection:** [SASL_SSL with PLAIN](#sasl-ssl) or PLAINTEXT, depending on the WarpStream deployment.
**Schema Registry:** Separate service — same SR config as the user's chosen SR provider (Confluent Cloud SR, WarpStream BYOC SR, self-hosted, Amazon Glue, etc.).
**CLI:** Standard Kafka CLI tools work. WarpStream has its own `warpstream` CLI for Agent management.
**UI:** User interfaces that are commonly used with Kafka can be used with WarpStream.

**Full WarpStream config reference:** `warpstream-optimization.md` — read this for complete overrides.

```properties
bootstrap.servers=<warpstream-agent-endpoint:9092>
# + auth pattern matching your WarpStream setup

# --- WarpStream-specific overrides (layer on top of core properties) ---

# Disable idempotence for better throughput on WarpStream.
# EOS (exactly_once_v2) enables idempotence internally — see warpstream-optimization.md for tradeoffs.
producer.enable.idempotence=false
producer.max.in.flight.requests.per.connection=1000

# Larger batches amortize object-storage write latency
producer.batch.size=100000
producer.linger.ms=100
producer.buffer.memory=128000000
producer.max.request.size=64000000
producer.request.timeout.ms=30000

# Large fetch sizes — WarpStream appears as a single broker
consumer.fetch.max.bytes=50242880
consumer.max.partition.fetch.bytes=50242880
consumer.fetch.max.wait.ms=10000
# Do NOT set consumer.fetch.min.bytes — unsupported by WarpStream

# Reduce metadata refresh frequency
metadata.max.age.ms=60000

# Zone-aware routing to avoid cross-AZ costs
client.id=<application.id>,ws_az=<availability-zone>
```

## Default Serde Selection

| Schema Format | Default Value Serde | Dependency |
|--------------|-------------------|------------|
| Avro | `io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde` | `kafka-streams-avro-serde` |
| Protobuf | `io.confluent.kafka.streams.serdes.protobuf.KafkaProtobufSerde` | `kafka-streams-protobuf-serde` |
| JSON Schema | `io.confluent.kafka.streams.serdes.json.KafkaJsonSchemaSerde` | `kafka-streams-json-schema-serde` |

Default key serde is always `Serdes.StringSerde` unless the user has non-String keys.

## Topic Management Rules

Include these as comments in generated code or config:

- **Source topics:** User-managed. Must exist before the app starts.
- **Changelog topics:** Auto-created by Kafka Streams. `compact` for non-windowed, `compact,delete` for windowed (so expired window segments are cleaned up).
- **Repartition topics:** Auto-created with infinite retention. Don't set retention — causes data loss.
- **Output topics:** Pre-create before deploying to production.
- **DLQ topics** (if using KIP-1034): Pre-create. Named `<application.id>-<source-topic>-dlq`. See `production-hardening.md`.

**Production clusters typically have `auto.create.topics.enable=false`** (and Confluent Cloud always does). Source, output, and DLQ topics must be created manually. Changelog and repartition topics are still auto-created by Kafka Streams via the admin client.

## Monitoring Metrics

Include as comments in generated config:

```properties
# Key metrics to monitor:
# - kafka.streams:type=stream-metrics,client-id=*
#   alive-stream-threads: should equal num.stream.threads
#   failed-stream-threads: should be 0
# - kafka.streams:type=stream-thread-metrics,thread-id=*
#   process-rate: records/sec processed
#   commit-rate: commits/sec
# - kafka.streams:type=stream-task-metrics,thread-id=*,task-id=*
#   active-process-ratio: time spent processing vs polling (target: >0.5)
# - Stateful apps also monitor:
#   kafka.streams:type=stream-state-metrics: store operation latency
#   org.rocksdb:type=statistics: SST file sizes, compaction stats
```

Or expose via JMX for Prometheus/Grafana.

---

## EOS Configuration

Dedicated configuration reference for Exactly-Once Semantics. See `topology-patterns.md` for the decision framework on whether EOS is appropriate.

> **WarpStream:** EOS (`exactly_once_v2`) has a significant throughput cost on WarpStream. It enables idempotent producers internally, limiting concurrency to 5 in-flight requests — combined with WarpStream's higher produce latency, this reduces throughput and may produce `KAFKA_STORAGE_ERROR` retries. Prefer `at_least_once` with downstream deduplication when possible. If EOS is required, it will work — plan for additional capacity. See `warpstream-optimization.md`.

### Required Properties

```properties
# Enable EOS — always use v2, never v1
processing.guarantee=exactly_once_v2
```

### Properties to NOT Set

```properties
# Do NOT set commit.interval.ms for EOS apps.
# EOS overrides this to 100ms internally for correctness.
# OMIT this line entirely when using exactly_once_v2.
```

### Transaction Timeout

```properties
# Default: 10000ms (10s). Increase for slow processing.
# If processing takes longer, the transaction coordinator aborts and fences the producer.
# This triggers rebalance + state restoration, which can cascade.
#
# Common values:
#   60000   (60s)  — good starting point for most stateful apps
#   300000  (5min) — apps with slow external lookups or large state
#   900000  (15min) — extreme cases with slow processing or large state
transaction.timeout.ms=60000
```

### Producer Properties Enforced by EOS

Set automatically when `processing.guarantee=exactly_once_v2`. Do NOT override.

| Property | Enforced Value | Why |
|----------|---------------|-----|
| `acks` | `all` | All ISR replicas must acknowledge |
| `enable.idempotence` | `true` | Required for transactional producers |
| `retries` | `2147483647` | Transactional producers retry indefinitely |
| `max.in.flight.requests.per.connection` | `5` | Max allowed for idempotent producers |

### EOS + Resilience Properties

```properties
# Standby replicas — critical for EOS resilience.
num.standby.replicas=1

# Internal topic replication
replication.factor=3

# Align poll timeout with transaction timeout.
consumer.max.poll.interval.ms=600000
consumer.session.timeout.ms=45000
```

### EOS Checklist

1. `processing.guarantee=exactly_once_v2` (not `exactly_once`)
2. `commit.interval.ms` is NOT set
3. `transaction.timeout.ms` high enough for your processing time
4. `num.standby.replicas=1` for resilience
5. `replication.factor=3` for internal topics
6. Downstream consumers have `isolation.level=read_committed`
7. Broker has `transaction.state.log.replication.factor=3` and `min.isr=2`
8. On CC: app runs at least once per 7 days (transactional ID expiry)
9. `consumer.max.poll.interval.ms` >= `transaction.timeout.ms`

---

## Performance Tuning

Configuration parameters with the strongest impact on throughput.

> **WarpStream:** The defaults in this table are for standard Kafka. WarpStream requires significantly larger batch sizes, higher linger, and larger fetch sizes. See the WarpStream section under [Environment-Specific Configuration](#warpstream) and `warpstream-optimization.md` for exact values.

### High-Impact Parameters

| Parameter | Default | Tuning Guidance |
|-----------|---------|-----------------|
| `producer.batch.size` | 16384 | Very strong positive correlation with throughput. Increase for high-volume apps. |
| `producer.linger.ms` | 0 | Moderate positive correlation. Set 5-50ms to allow batching. |
| `consumer.fetch.min.bytes` | 1 | Moderate positive correlation. Increase for throughput at cost of latency. |
| `consumer.max.poll.records` | 500 | Tune to control processing time per poll. Reduce if hitting `max.poll.interval.ms`. |
| `commit.interval.ms` | 30000 | At-least-once only. Larger = better throughput but more reprocessing on failure. |
| `cache.max.bytes.buffering` | 10485760 | Increasing reduces write frequency to state stores and changelog topics. |
| `num.stream.threads` | 1 | Set <= available CPU cores. Max useful threads = input partitions / instances. |
| `producer.compression.type` | none | Set to `lz4` or `snappy` to reduce network bandwidth. |

### RocksDB Tuning for Stateful Apps

```java
public class TunedRocksDBConfig implements RocksDBConfigSetter {
    @Override
    public void setConfig(String storeName, Options options, Map<String, Object> configs) {
        // UNIVERSAL compaction — optimized for write-heavy workloads
        options.setCompactionStyle(CompactionStyle.UNIVERSAL);
        options.setWriteBufferSize(64 * 1024 * 1024L);  // 64MB (default 16MB)
        options.setMaxWriteBufferNumber(4);               // default 3
        options.setMaxBackgroundJobs(4);                  // default 2
        options.setCompressionType(CompressionType.LZ4_COMPRESSION);
    }

    @Override
    public void close(String storeName, Options options) {}
}
```

**BoundedMemoryRocksDBConfig:** When you have many stores, the default per-store allocation (98MB each: 50MB block cache + 16MB × 3 write buffers) adds up fast. Use `BoundedMemoryRocksDBConfig` to share a single block cache across all stores, capping total off-heap:

```properties
rocksdb.config.setter=org.apache.kafka.streams.state.internals.BoundedMemoryRocksDBConfig
# Total shared block cache for ALL RocksDB instances (replaces the 50MB-per-store default)
rocksdb.block.cache.size=536870912      # 512MB total (shared, not per-store)
rocksdb.write.buffer.size=16777216      # 16MB per write buffer (same as default)
rocksdb.max.write.buffers=2             # 2 buffers per store (default is 3; lower = less memory)
```

### State Restoration Tuning

```properties
# Speed up state restoration by increasing fetch size
restore.consumer.fetch.max.bytes=52428800   # 50MB
restore.consumer.max.partition.fetch.bytes=10485760  # 10MB
```
