---
name: checkpoint-best-practices
description: Configure and manage checkpoint locations for reliable Spark Structured Streaming. Use when setting up new streaming jobs, troubleshooting checkpoint issues, migrating checkpoints, or ensuring exactly-once semantics with proper checkpoint storage and organization.
---

# Checkpoint Best Practices

Configure checkpoint locations for reliable streaming with exactly-once semantics. Checkpoints track progress and enable fault tolerance.

## Quick Start

```python
def get_checkpoint_location(table_name):
    """Checkpoint tied to target table"""
    return f"/Volumes/catalog/checkpoints/{table_name}"

# Example:
# Table: prod.analytics.orders
# Checkpoint: /Volumes/prod/checkpoints/orders

query = (df
    .writeStream
    .format("delta")
    .option("checkpointLocation", get_checkpoint_location("orders"))
    .start("/delta/orders")
)
```

## Checkpoint Storage

### Use Persistent Storage

```python
# DO: Use Unity Catalog volumes (S3/ADLS-backed)
checkpoint_path = "/Volumes/catalog/checkpoints/stream_name"

# DON'T: Use DBFS (ephemeral, workspace-local)
checkpoint_path = "/dbfs/checkpoints/stream_name"  # Avoid
```

### Target-Tied Organization

```python
def get_checkpoint_location(table_name):
    """Checkpoint should be tied to TARGET, not source"""
    return f"/Volumes/catalog/checkpoints/{table_name}"

# Why target-tied?
# - Checkpoint already contains source information
# - Systematic organization
# - Easy backup and restore
# - Clear ownership
```

### Unique Checkpoint Per Stream

```python
# CORRECT: Each stream has its own checkpoint
stream1.writeStream \
    .option("checkpointLocation", "/checkpoints/stream1") \
    .start()

stream2.writeStream \
    .option("checkpointLocation", "/checkpoints/stream2") \
    .start()

# WRONG: Never share checkpoints between streams
# This causes data loss and corruption
```

## Checkpoint Structure

### Folder Contents

```
checkpoint_location/
├── metadata/      # Query ID
├── offsets/       # What to process (intent)
├── commits/       # What completed (confirmation)
├── sources/       # Source metadata
└── state/         # Stateful operations (if any)
```

### Stateless vs Stateful

```python
# Stateless (read from Kafka, write to Delta)
# Checkpoint: metadata, offsets, commits, sources
# No state folder

df = (spark.readStream
    .format("kafka")
    .option("subscribe", "topic")
    .load())

# Stateful (with watermark and deduplication)
# Checkpoint: + state folder
df_stateful = (df
    .withWatermark("timestamp", "10 minutes")
    .dropDuplicates(["partition", "offset"])
)
```

## Reading Checkpoint Contents

### Read Offset Files

```python
import json

# Read offset file
offset_file = "/checkpoints/stream/offsets/223"
content = dbutils.fs.head(offset_file)
offset_data = json.loads(content)

# Pretty print
print(json.dumps(offset_data, indent=2))

# Key fields:
# - batchWatermarkMs: Watermark timestamp
# - batchTimestampMs: When batch started
# - source[0].startOffset: Beginning of batch (inclusive)
# - source[0].endOffset: End of batch (exclusive)
# - source[0].latestOffset: Current position in source
```

### Read State Store

```python
# Query state store directly
state_df = (spark
    .read
    .format("statestore")
    .load("/checkpoints/stream/state")
)

state_df.show()
# Shows: key, value, partitionId, expiration timestamp

# Read state metadata
state_metadata = (spark
    .read
    .format("state-metadata")
    .load("/checkpoints/stream")
)
state_metadata.show()
# Shows: operatorName, numPartitions, minBatchId, maxBatchId
```

## Recovery Scenarios

### Lost Checkpoint

Stop the query and determine whether a complete, consistent checkpoint backup exists. Do not delete or overwrite the original path during diagnosis.

```python
# Preferred recovery: restore the entire checkpoint (metadata, offsets, commits,
# sources, and state) from a backup captured while the query was stopped.
restored_checkpoint = "/checkpoints/stream-restored-20260101"
dbutils.fs.cp(
    "/checkpoints/backups/stream-20260101",
    restored_checkpoint,
    recurse=True,
)

# Restart the unchanged query with restored_checkpoint as checkpointLocation.
# Validate source continuity and target counts before returning it to service.
```

If no valid backup exists, this is a new query, not a continuation. Select replay boundaries based on source retention and the last reconciled target key/offset. `startingOffsets` is a source option on `readStream` and is used only when the new checkpoint has no saved offsets.

```python
replay_source = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
    .option("subscribe", "events")
    .option("startingOffsets", "earliest")  # Or explicit reviewed offsets.
    .load())

replayed = transform_events(replay_source)

query = (replayed.writeStream
    .foreachBatch(upsert_idempotently)  # MERGE/deduplicate by stable event key.
    .option("checkpointLocation", "/checkpoints/stream-replay-20260101")
    .start())
```

Replay into an idempotent sink or a shadow target. A new checkpoint gives the stream a new query identity, so a Delta append sink does not automatically deduplicate data already written by the old query. Reconcile counts, keys, and offsets before an explicitly approved cutover.

### Corrupted Checkpoint

Stop the stream and preserve the complete checkpoint path for forensic analysis. Never delete only `state/`, `offsets/`, or `commits/`; those components form one recovery unit and partial removal can cause incorrect state or duplicate output.

1. Restore a known-good, complete checkpoint to a new path and restart the unchanged query there.
2. If no backup is usable, retain the corrupt path, start with a new unique checkpoint, and replay from reviewed source offsets into an idempotent or shadow sink as shown above.
3. Confirm the source still retains the required range, validate stateful results and target reconciliation, and document data gaps that cannot be replayed.
4. Remove the old/corrupt checkpoint only after recovery is complete and its exact path and retention requirement have been explicitly confirmed.

### Crash During Batch

```python
# Scenario: Crash during batch processing
# - Latest offset = 223 (written at start)
# - Commit 223 missing (crash before finish)
# - On restart: Spark reprocesses offset 223
# - Delta deduplication prevents duplicates (if txnVersion configured)
```

## Monitoring

### Checkpoint Size

```python
# Track checkpoint folder size
checkpoint_size = dbutils.fs.ls("/checkpoints/stream")
total_size = sum([f.size for f in checkpoint_size if f.isFile()])
print(f"Checkpoint size: {total_size / (1024*1024):.2f} MB")

# Alert on checkpoint access failures
try:
    dbutils.fs.ls("/checkpoints/stream")
except Exception as e:
    print(f"Checkpoint access failed: {e}")
    # Send alert
```

### State Store Growth

```python
# Monitor state store size (stateful jobs)
state_df = spark.read.format("statestore").load("/checkpoints/stream/state")

# Check partition balance
state_df.groupBy("partitionId").count().orderBy(desc("count")).show()

# Look for skew - one partition with 10x others = problem
# State size = f(watermark duration, key cardinality)
```

### Offset vs Commit Sync

```python
# Check if offsets have matching commits
import json

# Read latest offset
latest_offset_file = sorted(dbutils.fs.ls("/checkpoints/stream/offsets"))[-1].path
offset_data = json.loads(dbutils.fs.head(latest_offset_file))
batch_id = latest_offset_file.split("/")[-1]

# Check if commit exists
commit_file = f"/checkpoints/stream/commits/{batch_id}"
if dbutils.fs.exists(commit_file):
    print(f"Batch {batch_id}: Committed")
else:
    print(f"Batch {batch_id}: Not committed (will reprocess)")
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **State growing too large** | Long watermark duration or high cardinality keys | Reduce watermark duration; reduce key cardinality |
| **Checkpoint corruption** | File system issues or manual deletion | Stop and preserve it; restore the complete checkpoint, or use a new checkpoint with reviewed, idempotent replay |
| **Slow state operations** | Partition imbalance | Check partition balance; ensure keys are evenly distributed |
| **Can't find commit file** | Normal if job crashed | Spark will reprocess on restart |
| **Offsets out of sync** | Offsets without matching commits | Indicates unprocessed batch; will reprocess |

## Production Best Practices

### Checkpoint Location Pattern

```python
def get_checkpoint_path(table_name, environment="prod"):
    """
    Checkpoint should be:
    1. Tied to TARGET table (not source)
    2. In persistent storage (UC Volume, S3, ADLS)
    3. Organized systematically
    """
    return f"/Volumes/{environment}/checkpoints/{table_name}"

# Usage
checkpoint = get_checkpoint_path("orders", "prod")
```

### Backup Strategy

```python
# Stop the stream and await termination before a filesystem-level checkpoint copy.
# Alternatively use a storage snapshot mechanism that guarantees a consistent view.
def backup_stopped_checkpoint(checkpoint_path, backup_suffix):
    backup_path = f"{checkpoint_path}_backup_{backup_suffix}"
    dbutils.fs.cp(checkpoint_path, backup_path, recurse=True)
    return backup_path

query.stop()
query.awaitTermination()
backup_stopped_checkpoint("/checkpoints/stream", "20260101")
# Restart only after verifying the backup contains metadata, offsets, commits,
# sources, and state (for a stateful query).
```

### Migration

```python
# Migrate only while the query is stopped, or from a consistent storage snapshot.
def migrate_stopped_checkpoint(old_path, new_path):
    dbutils.fs.cp(old_path, new_path, recurse=True)

    # Verify the complete directory structure and permissions before restart.
    # Keep old_path unchanged for rollback; never merge two checkpoint trees.
    return new_path
```

## Production Checklist

- [ ] Checkpoint location is persistent (S3/ADLS, not DBFS)
- [ ] Unique checkpoint per stream
- [ ] Target-tied checkpoint organization
- [ ] Backup strategy defined
- [ ] Monitoring configured (checkpoint size, access failures)
- [ ] State store growth monitored (if stateful)
- [ ] Recovery procedure documented
- [ ] Migration procedure documented

## Related Skills

- `kafka-to-delta` - Kafka ingestion with checkpoint management
- `stream-stream-joins` - Stateful operations and state stores
- `state-store-management` - Deep dive on state store optimization
