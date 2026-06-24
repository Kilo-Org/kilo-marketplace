# Kafka Streams Architecture

How Kafka Streams works internally. Read this when explaining KS to users, sizing applications, or diagnosing issues.

**Docs:** [Architecture guide](https://docs.confluent.io/platform/current/streams/architecture.md)

## Core Concepts

Kafka Streams is a **client library** — it runs inside your JVM process, not on a separate cluster. Each instance connects to Kafka as a consumer, processes records, and produces results back to Kafka.

### Threading Model

```
KafkaStreams instance
├── StreamThread-1 (a Java thread)
│   ├── Consumer (polls from assigned partitions)
│   ├── Task 0_0 (partition 0 of subtopology 0)
│   │   ├── Processor topology
│   │   └── State stores (RocksDB)
│   ├── Task 0_1 (partition 1 of subtopology 0)
│   └── Producer (writes to output/changelog topics)
├── StreamThread-2
│   └── ...
├── GlobalStreamThread (if GlobalKTable is used)
│   └── Reads ALL partitions of global topics
└── StateRestoreThread
    └── Replays changelogs to rebuild state stores
```

- **StreamThread:** Each thread runs an event loop: poll → process → commit. One thread handles multiple tasks.
- **Task:** The unit of parallelism. One task per input partition per subtopology. A task owns its state stores.
- **Subtopology:** An independent processing graph with no shared state. KS creates separate subtopologies for disconnected parts of the topology.
- **GlobalStreamThread:** Separate thread for GlobalKTable — reads every partition, builds a local copy of the entire table.

### How Partitions Map to Tasks

```
Input topic: orders (6 partitions)
Topology: orders → groupByKey → aggregate → output

Tasks created: 6 (one per partition)
If 2 instances with 1 thread each: 3 tasks per instance
If 1 instance with 3 threads: 2 tasks per thread
```

**Max parallelism = number of input partitions.** More instances/threads than partitions means idle capacity.

### State Stores

Each stateful task has its own state store instance, backed by RocksDB (default). State is:
- **Partitioned:** Task 0_0 only has state for partition 0's keys
- **Persistent:** Survives restarts via local RocksDB files
- **Recoverable:** Backed by changelog topics in Kafka — can be rebuilt from scratch
- **Off-heap:** RocksDB memory (block cache, write buffers) is NOT controlled by JVM heap settings

### Lifecycle States

CREATED → REBALANCING → RUNNING → PENDING_SHUTDOWN → NOT_RUNNING (normal path)
RUNNING → PENDING_ERROR → ERROR (error path)

States: CREATED (not started), REBALANCING (task assignment), RUNNING (processing), PENDING_SHUTDOWN (draining), NOT_RUNNING (clean exit), ERROR (unrecoverable).

### Commit and Flush

Commit cycle (`commit.interval.ms`): (1) flush state stores, (2) flush producer, (3) commit offsets.
- At-least-once: async, 30s default
- Exactly-once: transactional (atomic), 100ms default

**Cache** (`statestore.cache.max.bytes`): In front of RocksDB. Deduplicates updates per key within commit interval. 50MB + 30s commits = downstream sees only latest value per key per cycle.

### Changelog Topics

Every state store has a changelog: `<application.id>-<store-name>-changelog`
- Non-windowed: `cleanup.policy=compact`
- Windowed: `cleanup.policy=compact,delete`

Enable recovery by replaying. Standby replicas stay warm by continuously replaying.

### Repartition Topics

Created by `selectKey()`, `groupBy()`, `map()` when key changes. Naming: `<application.id>-<operator-name>-repartition`. **Retention: infinite** — DO NOT set retention (causes data loss).

### GlobalKTable vs KTable

| Aspect | KTable | GlobalKTable |
|--------|--------|-------------|
| Distribution | Partitioned | Replicated to all |
| Co-partitioning for joins | Required | Not required |
| Join key | Must match table key | Any field |
| Memory | Per partition | Full table per instance |
| Changelog | Yes | No (reads source) |

Use GlobalKTable when: lookup is small (< few GB), join key ≠ record key, or co-partitioning impractical.

## Sizing Guidelines

### Parallelism

`total_threads = instances × num.stream.threads ≤ input_partitions`

More threads than partitions = idle (hot standbys). Multi-sub-topology: use `topology.describe()` for actual task count.

**Sizing:**
- Stateless: more threads/instance (match CPU), fewer instances
- Stateful: fewer threads/instance, size for RocksDB. Prefer fewer large instances over many small (restoration is expensive).

### Memory (stateful apps) — canonical reference

Other files cross-reference this section for the RocksDB memory formula.

```
JVM heap: application objects + serde buffers + cache
  - statestore.cache.max.bytes is on-heap (divided among threads)
  - Typical: 512MB - 2GB heap

RocksDB off-heap: per state store instance
  - block_cache(50MB) + write_buffers(16MB × 3) = 98MB per instance
  - Non-windowed: store_instances = partitions_per_instance × stores
  - Windowed: store_instances = partitions_per_instance × stores × 3 (segments)
  - Typical: 1-10 GB off-heap

Container total = heap + off-heap + OS overhead (~256MB)
Set MaxRAMPercentage=75 to leave room for RocksDB
```

**Worked example (windowed aggregation):**
- 40 partitions, 1 windowed store, 4 instances → 10 partitions/instance
- Windowed segments: 10 × 1 × 3 = 30 store instances per app
- RocksDB memory: 30 × 98MB = ~2.9 GB off-heap
- Container: 2GB heap + 2.9GB RocksDB + 256MB OS = ~5.2 GB minimum

**BoundedMemoryRocksDBConfig:** For apps with many stores, share a single block cache across all RocksDB instances to limit total off-heap. See `config-baseline.md` § Performance Tuning.

### Disk (stateful apps)

```
RocksDB disk = state_size × 3 (SST files + WAL + compaction overhead)
Standby replicas double the disk requirement
Use fast local storage (SSD), never NFS/EBS
Monitor disk usage with alerts at 70%
```

The 3x factor accounts for: active SST files, write-ahead log, and temporary files created during compaction. Windowed stores create multiple segments per partition, further increasing disk needs.

**Always use persistent volumes (PVCs) in Kubernetes for stateful apps.** Ephemeral storage forces full state restoration on every restart, which can take hours for large state stores.

### Network and Broker Sizing

```
Stateless broker overhead:  ~1x input volume (read + write output)
Stateful broker overhead:   ~1.5-2x input volume (+ changelog writes)
EOS broker overhead:        ~2x input volume (+ transaction markers)
```

Changelog topics are replicated by `replication.factor` (default 3). Each state store creates one changelog topic. Repartition topics add additional broker load approximately matching the original topic being remapped.

### Scaling

**Scale out** (add instances): Network/memory-bound apps. Tasks reassign after rebalance.
**Scale up** (add threads/resources): CPU-bound. Must increase `num.stream.threads` + adjust heap/RocksDB caps.
