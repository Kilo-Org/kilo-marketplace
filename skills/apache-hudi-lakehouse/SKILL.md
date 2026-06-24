---
name: "apache-hudi-lakehouse"
description: "Guides agents through Apache Hudi lakehouse design. Use when managing incremental upserts, record-level mutations, timeline behavior, compaction, and Hudi-based lakehouse tables."
metadata:
  category: data
  source:
    repository: "https://github.com/vaquarkhan/data-engineering-agent-skills"
    path: "skills/apache-hudi-lakehouse"
    license_path: "LICENSE"
---

# Apache Hudi Lakehouse

## Overview

Use this skill when `Apache Hudi` is the primary table layer for incremental lakehouse workloads. It helps agents reason about mutation-heavy patterns, table type selection, compaction behavior, timeline safety, and consumer expectations across read-optimized and real-time query paths.

## When to Use

- choosing or operating `Apache Hudi` for lakehouse tables
- building record-level upsert or delete pipelines
- managing compaction, clustering, and incremental consumption
- supporting lakehouse tables with heavy mutations (CDC sinks, slowly changing dimensions)
- planning multi-engine access (Spark, Presto, Trino, Athena, Hive)

Do not use this when the workload is append-only with no mutation requirements and simpler formats like Parquet or Iceberg would suffice.

## Workflow

1. Define mutation patterns and read access expectations.
   Include:
   - primary record key and partition path
   - expected operations: inserts, upserts, deletes, or bulk replaces
   - read latency expectations: are readers okay with merge-on-read or do they need read-optimized snapshots?
   - query engines that must access the table
   - expected write throughput and record mutation rate

2. Choose the right table type and indexing strategy.
   - `Copy-on-Write (COW)`: best for read-heavy workloads, produces columnar snapshots on write
   - `Merge-on-Read (MOR)`: best for write-heavy workloads, defers merge to read time or compaction
   - choose record index type: `BLOOM`, `GLOBAL_BLOOM`, `SIMPLE`, `BUCKET`, or `RECORD_INDEX`
   - index choice affects upsert performance and scaling behavior
   - document why the table type was chosen — revisiting later is expensive

3. Plan compaction and clustering explicitly.
   - for MOR tables: compaction converts log files to columnar — it is not optional
   - define compaction strategy: synchronous (inline) or asynchronous (scheduled)
   - set compaction triggers: by number of commits, time, or log file size
   - clustering reorganizes data layout for query performance — plan separately from compaction
   - budget compute for compaction and clustering in cost planning

4. Design incremental consumption and downstream contracts.
   - Hudi supports incremental queries by commit timeline
   - define the consumer contract: which commit instant do consumers start from?
   - plan for consumer resets and bootstrap reads
   - document how schema changes affect incremental consumers
   - test that consumers handle compaction and rollback instants correctly

5. Handle schema evolution and timeline safety.
   - Hudi supports schema evolution but not all changes are safe across readers
   - column adds are generally safe; renames and type changes require care
   - define compatibility expectations per reader engine
   - rollback instants can confuse consumers — document rollback behavior
   - archive policy affects timeline visibility for late consumers

6. Plan operations, monitoring, and recovery.
   - monitor timeline growth, pending compactions, and inflight commits
   - alert on compaction backlog and write failures
   - plan for rollback: Hudi supports instant-level rollback, but consumers must handle gaps
   - define retention and archival for the Hudi timeline
   - document backup and restore procedures for critical tables

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "Hudi handles upserts so we don't need to think about keys." | Record key and partition path design determines correctness, performance, and scaling. Wrong keys cause silent data loss or duplication. |
| "MOR is always better because writes are faster." | MOR defers work to compaction and read time. Without compaction planning, read performance degrades unboundedly. |
| "Compaction will just happen in the background." | Compaction requires explicit scheduling, compute budget, and monitoring. Unmanaged compaction leads to reader degradation and timeline bloat. |
| "All query engines see the same data." | COW and MOR tables expose different snapshots to different query types. Read-optimized queries on MOR tables see only compacted data. |

## Red Flags

- record key chosen without understanding uniqueness guarantees
- MOR table with no compaction schedule or monitoring
- incremental consumers have no documented starting instant or reset procedure
- schema changes deployed without testing across all reader engines
- no monitoring of timeline growth, pending compactions, or inflight commits
- clustering is never run despite increasing query scan ranges
- rollback behavior is undocumented and consumers assume a linear timeline
- index type is default without analysis of key cardinality and write patterns

## Verification

- [ ] Record key, partition path, and mutation semantics are explicitly documented
- [ ] Table type choice (COW vs MOR) is justified with read/write trade-off analysis
- [ ] Compaction is scheduled, monitored, and budgeted for compute cost
- [ ] Incremental consumer contracts define starting instants and reset behavior
- [ ] Schema evolution paths are tested across all target query engines
- [ ] Timeline monitoring covers pending compactions, inflight commits, and archival
- [ ] Rollback behavior is documented and consumers handle timeline gaps safely
