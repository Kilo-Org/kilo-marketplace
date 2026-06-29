---
name: flink-best-practices
description: >-
  Apache Flink development best practices for DataStream API, state management,
  checkpointing, event time processing, and deployment
metadata:
  category: data
  source:
    repository: 'https://github.com/BigDataBoutique/skills'
    path: flink-best-practices
    license_path: LICENSE
    commit: 1831ce77355a610d52b3545a96f9779476ed0681
---

# Apache Flink Best Practices

## Core Principles

- Assign stable UIDs to every operator — mandatory for savepoint compatibility
- Use keyed state with TTL — unbounded state is the #1 cause of production failures
- Use event time with watermarks — processing time is non-deterministic on replay
- Use RocksDB state backend with incremental checkpoints for production
- Never do blocking I/O in operators — use `AsyncDataStream`
- Name every operator for debuggability in the Flink Web UI
- Deploy in Application Mode for production workloads

## Application Structure (HIGH)

### app-operator-uids

**Assign `.uid("stable-id")` to every operator. This is mandatory.**

Without UIDs, Flink cannot map state across job restarts or upgrades from savepoints. Missing UIDs will cause state loss on any job modification.

```java
DataStream<Event> events = env
    .addSource(kafkaSource)
    .name("kafka-source")
    .uid("kafka-source-uid")
    .map(new EventParser())
    .name("event-parser")
    .uid("event-parser-uid")
    .keyBy(Event::getUserId)
    .process(new UserSessionProcessor())
    .name("session-processor")
    .uid("session-processor-uid");
```

### app-job-design

**One job per pipeline. Keep `main()` clean.**

Build the `StreamExecutionEnvironment`, define the DAG, call `execute()`. Extract business logic into separate `ProcessFunction` or `MapFunction` classes — avoid inline lambdas for complex logic.

Externalize all configuration (Kafka brokers, parallelism, checkpoint intervals) via `ParameterTool` or Flink's `Configuration` object. Never hardcode.

### app-max-parallelism

**Set `env.setMaxParallelism()` explicitly (power of 2, e.g., 128, 256).**

The default max parallelism cannot be changed after the first savepoint without losing state. Set it upfront to allow future scaling.

---

## DataStream API (HIGH)

### datastream-operator-selection

**Choose the right operator abstraction.**

| Need | Use |
|------|-----|
| 1:1 transformation | `map` |
| 1:N transformation | `flatMap` |
| Predicate filtering | `filter` |
| Keyed state + timers | `KeyedProcessFunction` |
| Lifecycle hooks (`open`/`close`) | `RichMapFunction`, `RichFlatMapFunction` |

### datastream-type-system

**Use POJOs for best serialization performance.**

Flink's POJO serializer is significantly faster than Kryo. A POJO must have: public fields or getters/setters, and a no-arg constructor.

- Avoid `GenericTypeInfo` (Kryo fallback) — it is slow and prevents optimizations
- If you see "is being handled as a GenericType" in logs, fix the type
- Register custom types with `env.getConfig().registerTypeWithKryoSerializer()` only as a last resort
- Use `TypeInformation.of(new TypeHint<Tuple2<String, Long>>(){})` for generic types

### datastream-operator-chaining

**Do not disable operator chaining globally.**

Chaining eliminates serialization overhead between operators in the same task. Only break chains with `.disableChaining()` on a specific operator when needed for debugging or resource isolation.

Use `.slotSharingGroup("name")` to isolate resource-heavy operators into dedicated slots.

### datastream-parallelism

**Set source parallelism to match input partition count.**

For Kafka sources, match the number of topic partitions. Downstream operators can have different parallelism. Use `keyBy()` for logical partitioning — key selection determines data distribution and state locality.

Avoid hot keys (keys with disproportionate traffic). Consider pre-aggregation or key salting for skewed distributions.

---

## Table API and Flink SQL (HIGH)

### sql-prefer-for-etl

**Prefer Flink SQL for ETL, aggregations, and joins — it benefits from the query optimizer.**

Use `CREATE TABLE` DDL with connector properties. Define watermarks in DDL:

```sql
CREATE TABLE orders (
    order_id STRING,
    user_id STRING,
    amount DECIMAL(10, 2),
    order_time TIMESTAMP(3),
    WATERMARK FOR order_time AS order_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'orders',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);
```

### sql-state-ttl

**Always set `table.exec.state.ttl` for streaming SQL — state grows forever without it.**

```sql
SET 'table.exec.state.ttl' = '24 h';

SELECT user_id, COUNT(*) as order_count, SUM(amount) as total
FROM orders
GROUP BY user_id;
```

Without TTL, streaming joins and group-by aggregations accumulate state indefinitely.

### sql-temporal-joins

**Use temporal joins for versioned lookups instead of regular stream-stream joins.**

```sql
SELECT o.order_id, o.amount, c.currency_rate
FROM orders AS o
JOIN currency_rates FOR SYSTEM_TIME AS OF o.order_time AS c
ON o.currency = c.currency;
```

Regular stream-stream joins hold state for both sides indefinitely unless TTL is set. Prefer `INTERVAL` joins or temporal joins for streaming.

---

## State Management (CRITICAL)

### state-keyed-state-types

**Choose the right state primitive.**

| Type | Use When |
|------|----------|
| `ValueState<T>` | Single value per key |
| `ListState<T>` | List of values per key |
| `MapState<K,V>` | Key-value lookups per key |
| `ReducingState<T>` | Incrementally reduced aggregate |
| `AggregatingState<IN,OUT>` | Incrementally aggregated with different output type |

### state-mapstate-over-valuemap

**Use `MapState<K,V>` instead of `ValueState<Map<K,V>>`.**

With RocksDB, `MapState` stores each entry as a separate RocksDB key, enabling lazy deserialization. `ValueState<Map>` serializes/deserializes the entire map on every access — catastrophic for large maps.

### state-ttl

**Configure state TTL on all keyed state to prevent unbounded growth.**

```java
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Duration.ofHours(24))
    .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
    .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
    .cleanupInRocksdbCompactFilter(1000)
    .build();

ValueStateDescriptor<MyState> descriptor =
    new ValueStateDescriptor<>("my-state", MyState.class);
descriptor.enableTimeToLive(ttlConfig);
```

Unbounded state is the #1 cause of production failures — eventual OOM or disk exhaustion.

### state-backend-rocksdb

**Use EmbeddedRocksDBStateBackend with incremental checkpoints for production.**

```java
env.setStateBackend(new EmbeddedRocksDBStateBackend(true)); // true = incremental
```

Use HashMapStateBackend only when state is guaranteed small and you need absolute minimum latency (development, small jobs).

| Backend | State Location | Incremental Checkpoints | Best For |
|---------|---------------|------------------------|----------|
| HashMapStateBackend | JVM heap | No | Small state, dev/test |
| EmbeddedRocksDBStateBackend | Local disk (off-heap) | Yes | Production, large state |

### state-rocksdb-tuning

**Tune RocksDB for production workloads.**

```yaml
state.backend.rocksdb.block.cache-size: 128m      # increase for read-heavy state access
state.backend.rocksdb.writebuffer.size: 64m
state.backend.rocksdb.writebuffer.count: 4
state.backend.rocksdb.bloom-filter.bits-per-key: 10
state.backend.rocksdb.predefined-options: FLASH_SSD_OPTIMIZED  # or SPINNING_DISK_OPTIMIZED_HIGH_MEM
```

Note: Flink allocates a portion of managed memory for RocksDB block cache and write buffers by default. Explicit settings here override the managed memory allocation.

---

## Checkpointing (CRITICAL)

### checkpoint-configuration

**Configure checkpointing for production.**

```java
CheckpointConfig config = env.getCheckpointConfig();
config.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
config.setCheckpointInterval(60_000);              // 1 minute
config.setCheckpointTimeout(600_000);              // 10 minutes
config.setMinPauseBetweenCheckpoints(30_000);      // prevent checkpoint storms
config.setMaxConcurrentCheckpoints(1);
config.setTolerableCheckpointFailureNumber(3);
config.setExternalizedCheckpointRetention(
    ExternalizedCheckpointRetention.RETAIN_ON_CANCELLATION
);
```

**Checkpoint interval guidance:**
- Short (10–30s): faster recovery, higher I/O overhead
- Long (5–10min): less overhead, longer recovery
- Start with 1–3 minutes, tune based on recovery requirements and checkpoint duration

### checkpoint-storage

**Use distributed filesystem for checkpoint storage. Never use JobManager storage in production.**

```yaml
state.checkpoints.dir: s3://bucket/flink/checkpoints
state.savepoints.dir: s3://bucket/flink/savepoints
```

JobManager checkpoint storage stores on the JM heap and is lost on JM failure.

### checkpoint-unaligned

**Enable unaligned checkpoints when backpressure causes checkpoint barriers to stall.**

```java
config.enableUnalignedCheckpoints();
```

Unaligned checkpoints snapshot in-flight data along with state, decoupling checkpoint duration from backpressure. Trade-off: larger checkpoint size.

### checkpoint-savepoints

**Always trigger a savepoint before stopping a job for upgrades.**

```bash
flink savepoint <jobId> [targetDir]
```

Savepoints require stable operator UIDs. Use savepoints (not checkpoints) for Flink version upgrades. Without UIDs, state cannot be restored.

---

## Watermarks and Event Time (CRITICAL)

### watermark-strategy

**Assign watermarks as close to the source as possible.**

```java
WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
    .withTimestampAssigner((event, timestamp) -> event.getEventTime())
    .withIdleness(Duration.ofMinutes(1));
```

### watermark-idleness

**Always set `withIdleness()` when source partitions may go idle.**

Without it, an idle partition prevents the watermark from advancing across the entire job, stalling all downstream windows. This is one of the most common production issues.

### watermark-late-data

**Handle late data explicitly.**

Late events (arriving after the watermark has passed the window end) are dropped by default. Options:
- Use `allowedLateness()` on windows to accept late data
- Route late data to a side output for separate processing
- Monitor watermark lag via `currentInputWatermark` metric

### watermark-alignment

**Use watermark alignment when fast sources advance watermarks too far ahead of slow sources.**

```java
WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
    .withWatermarkAlignment("alignment-group", Duration.ofSeconds(20), Duration.ofSeconds(2));
```

---

## Window Operations (HIGH)

### window-types

**Choose the right window type.**

| Type | Use When | Caution |
|------|----------|---------|
| Tumbling | Fixed-size, non-overlapping (per-minute counts) | None |
| Sliding | Moving averages | Creates N instances per element (size/slide ratio) — state explosion if ratio > 10 |
| Session | User session analysis (gap-based) | Expensive due to window merging |
| Global | Custom triggers (count-based) | Requires explicit trigger |

### window-reduce-over-process

**Prefer `reduce()` / `aggregate()` over `ProcessWindowFunction`.**

- `ReduceFunction`: most efficient, incrementally reduces (no buffering)
- `AggregateFunction`: incrementally aggregates with an accumulator
- `ProcessWindowFunction`: buffers all elements — use only when you need all elements or window metadata

Combine for the best of both: `reduce(myReducer, myProcessWindowFunction)`.

```java
stream
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Duration.ofMinutes(5)))
    .allowedLateness(Duration.ofMinutes(1))
    .sideOutputLateData(lateOutputTag)
    .reduce(new MyReduceFunction())
    .name("5min-tumble")
    .uid("5min-tumble-uid");
```

---

## Connectors (HIGH)

### connector-kafka

**Configure Kafka source and sink correctly.**

```java
KafkaSource<Event> source = KafkaSource.<Event>builder()
    .setBootstrapServers("kafka:9092")
    .setTopics("events")
    .setGroupId("flink-consumer-group")
    .setStartingOffsets(OffsetsInitializer.committedOffsets(OffsetResetStrategy.LATEST))
    .setValueOnlyDeserializer(new EventDeserializationSchema())
    .build();

KafkaSink<Event> sink = KafkaSink.<Event>builder()
    .setBootstrapServers("kafka:9092")
    .setRecordSerializer(...)
    .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)
    .setTransactionalIdPrefix("flink-kafka-sink")
    .build();
```

- Set source parallelism equal to the number of Kafka partitions
- For exactly-once sinks, Kafka `transaction.timeout.ms` must exceed Flink's checkpoint interval + max checkpoint duration (set to at least 15 minutes)
- Downstream consumers must set `isolation.level=read_committed`

### connector-serialization

**Use schema-based serialization — avoid Kryo for connector records.**

- **Avro**: schema evolution support, native Flink support via `flink-avro`
- **Protobuf**: best throughput via `flink-protobuf`
- **JSON**: human-readable but slower than binary formats
- For Flink SQL: `'format' = 'json'`, `'format' = 'avro'`, `'format' = 'protobuf'`

### connector-filesystem

**Configure rolling policy for filesystem sinks.**

```sql
CREATE TABLE output (
    user_id STRING,
    event_count BIGINT
) WITH (
    'connector' = 'filesystem',
    'path' = 's3://bucket/output/',
    'format' = 'parquet',
    'sink.rolling-policy.file-size' = '128MB',
    'sink.rolling-policy.rollover-interval' = '10 min',
    'sink.partition-commit.policy.kind' = 'success-file'
);
```

---

## Memory Management (HIGH)

### memory-configuration

**Configure total process memory, not individual components.**

```yaml
taskmanager.memory.process.size: 4096m
taskmanager.memory.managed.fraction: 0.5    # increase for RocksDB-heavy jobs (0.5-0.7)
taskmanager.memory.network.fraction: 0.1    # increase if network buffer backpressure
taskmanager.numberOfTaskSlots: 2            # 2-4 slots per TM
taskmanager.memory.task.heap.size: 1024m    # for user code objects
```

- Prefer fewer slots with more memory per slot over many slots with little memory
- For RocksDB, managed memory is used for block cache and write buffers — more managed memory = better performance
- Monitor GC pauses; if GC is a bottleneck, reduce heap and move state to RocksDB (off-heap)

---

## Backpressure (HIGH)

### backpressure-diagnosis

**Use Flink Web UI to identify backpressure bottlenecks.**

Check `busyTimeMsPerSecond` metric per operator — values near 1000 indicate saturation. The bottleneck is the first operator that is busy with low output rate. Backpressure propagates upstream from there.

### backpressure-solutions

**Solutions in order of preference:**

1. **Optimize the slow operator** — reduce computation per record
2. **Increase parallelism** of the bottleneck operator only
3. **Use async I/O** for external lookups (database, API calls)
4. **Buffer and batch** external writes with `ProcessFunction` + timers

```java
AsyncDataStream.unorderedWait(
    stream,
    new AsyncDatabaseLookup(),
    30, TimeUnit.SECONDS,
    100  // max concurrent requests
).name("async-db-lookup").uid("async-db-lookup-uid");
```

**Never** do blocking I/O in `map()`/`flatMap()`/`processElement()`. Never use `Thread.sleep()` in operators.

---

## Exactly-Once Semantics (HIGH)

### exactly-once-requirements

**End-to-end exactly-once requires all three components.**

1. **Source**: must be replayable (e.g., Kafka with offset tracking)
2. **Flink**: exactly-once checkpointing enabled
3. **Sink**: transactional (two-phase commit) or idempotent (upsert by key)

For Kafka end-to-end exactly-once: source tracks offsets in checkpoint state, sink uses Kafka transactions, downstream consumers set `isolation.level=read_committed`.

---

## Deployment (HIGH)

### deployment-application-mode

**Use Application Mode for production deployments.**

Each job gets its own dedicated JobManager. Best isolation, no resource contention between jobs. Use Session Mode only for development or many small short-lived jobs.

### deployment-kubernetes

**Use the Flink Kubernetes Operator for declarative job management.**

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: my-flink-job
spec:
  image: ${FLINK_IMAGE_REF:?Set FLINK_IMAGE_REF to my-registry/my-flink-job@sha256:<reviewed-digest>}
  flinkVersion: v1_19
  flinkConfiguration:
    state.backend.type: rocksdb
    state.backend.incremental: "true"
    state.checkpoints.dir: s3://bucket/checkpoints
    state.savepoints.dir: s3://bucket/savepoints
    execution.checkpointing.interval: "60000"
    execution.checkpointing.min-pause: "30000"
    high-availability.type: kubernetes
    high-availability.storageDir: s3://bucket/ha
  jobManager:
    resource:
      memory: "2048m"
      cpu: 1
  taskManager:
    resource:
      memory: "4096m"
      cpu: 2
    taskSlots: 2
  job:
    jarURI: local:///opt/flink/usrlib/my-job.jar
    parallelism: 4
    upgradeMode: savepoint
    state: running
```

Set `upgradeMode: savepoint` for stateful upgrades (takes savepoint, stops, redeploys, restores).

---

## Testing (MEDIUM)

### testing-unit

**Test functions as plain Java objects. Test stateful operators with test harnesses.**

```java
// Unit test: plain function
@Test
public void testEventParser() {
    EventParser parser = new EventParser();
    Event result = parser.map(rawInput);
    assertEquals("click", result.getType());
}

// Stateful operator test with harness
OneInputStreamOperatorTestHarness<Event, Result> harness =
    ProcessFunctionTestHarnesses.forKeyedProcessFunction(
        new MyKeyedProcessFunction(),
        Event::getKey,
        Types.STRING);

harness.processElement(new StreamRecord<>(event, timestamp));
harness.processWatermark(new Watermark(timestamp));
// Assert on harness.extractOutputStreamRecords()
harness.close();
```

### testing-integration

**Use MiniCluster for integration tests. Use Testcontainers for Kafka tests.**

```java
// JUnit 5 (recommended)
@RegisterExtension
static final MiniClusterExtension MINI_CLUSTER = new MiniClusterExtension(
    new MiniClusterResourceConfiguration.Builder()
        .setNumberSlotsPerTaskManager(2)
        .setNumberTaskManagers(1)
        .build());
```

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|---|---|---|
| Missing operator UIDs | State lost on savepoint restore | Always set `.uid("stable-id")` |
| `ValueState<HashMap<K,V>>` with RocksDB | Full map serialized on every access | Use `MapState<K,V>` |
| Blocking I/O in operators | Backpressure, underutilization | Use `AsyncDataStream` |
| Unbounded state without TTL | OOM / disk exhaustion | Configure state TTL |
| Large sliding windows (size/slide > 10) | State explosion | Use smaller ratios or session windows |
| Processing time when event time is needed | Non-deterministic, incorrect on replay | Use event time with watermarks |
| Ignoring idle sources | Watermarks stall, windows never fire | Set `.withIdleness()` |
| Kryo fallback for state | Slow, no schema evolution | Use POJOs or Avro |
| No `minPauseBetweenCheckpoints` | Checkpoint storms under load | Set to 50%+ of checkpoint interval |
| Default max parallelism | Cannot scale up without losing state | Set explicitly (power of 2) |
| `print()` sink in production | Log I/O bottleneck | Replace with metrics |
| Catching/swallowing exceptions | Silent data loss | Fail fast or route to dead-letter side output |
