---
name: "hbase"
description: "Apache HBase wide-column store on Hadoop. Use for big data."
metadata:
  category: data
  source:
    repository: "https://github.com/G1Joshi/Agent-Skills"
    path: "skills/databases/hbase"
    license_path: "LICENSE"
---

# Apache HBase

HBase is the Hadoop database. It is a distributed, scalable, big data store. It provides random, real-time read/write access to your Big Data.

## When to Use

- **Hadoop Ecosystem**: Deep integration with HDFS, Hive, Spark.
- **Petabyte Scale**: Serving billions of rows with low latency.
- **Random Access**: When you need random R/W on HDFS data (which is usually WORM - Write Once Read Many).

## Quick Start

Uses Java API or Shell.

```bash
create 'users', 'info', 'data'
put 'users', 'row1', 'info:name', 'Alice'
get 'users', 'row1'
```

## Core Concepts

### Column Families

Data is grouped into column families (`info:name`, `info:email`). Families are stored physically together.

### Region Servers

HBase scales by splitting tables into "Regions" and hosting them on Region Servers.

### WAL & MemStore

Writes go to Write-Ahead-Log (Disk) and MemStore (RAM). When MemStore fills, it flushes to HFile (HDFS).

## Best Practices (2025)

**Do**:

- **Design Row Keys carefully**: Row keys determine sorting and sharding. "Hotspotting" (sequential keys) is the enemy. Use salt or hashing.
- **Pre-split Regions**: Don't start with 1 region. Pre-split based on your known key distribution.
- **Use Phoenix**: Apache Phoenix provides a SQL skin over HBase, making it usable like a Relational DB.

**Don't**:

- **Don't use for small data**: The overhead of HDFS/ZimeKeeper/HBase is huge. Only for >TB scale.
- **Don't scan excessively**: Full table scans are MapReduce jobs.

## References

- [Apache HBase Reference Guide](https://hbase.apache.org/book.html)
