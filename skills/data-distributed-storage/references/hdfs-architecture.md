# HDFS Architecture Reference

## NameNode HA with Quorum Journal Manager

```
           ZK Failover Controller
            Monitor NN health
               /        \
              v          v
        +---------+  +---------+
        | NN Act  |  | NN Std  |
        | namenode|  | namenode|
        +----+----+  +----+----+
             |            |
    edits -->+-----+------+<-- edits
                  |
           +------+------+
           | QJM         |
           | JN1 JN2 JN3 |  (3 or 5 nodes)
           +------+------+
```

- QJM writes to majority of JournalNodes (2/3 or 3/5)
- Active NN writes edits to all JNs, commits when majority acknowledges
- Standby NN reads edits from JNs and applies to namespace
- Failover: ZKFC detects NN failure via ZK ephemeral node, fence active, promote standby

## Block Management

- Default block size: 128MB (configurable: `dfs.blocksize`)
- Replication factor: 3 (configurable per directory/file: `dfs.replication`)
- Block reports: DataNode sends block list to NN every 6h (`dfs.blockreport.intervalMsec`)
- Heartbeat: DataNode sends heartbeat every 3s to NN (`dfs.heartbeat.interval`)
- Re-replication: NN detects under-replicated blocks via heartbeat, schedules replication

```
Block locations in NN memory:
  inode -> block list -> block_id -> [DN1, DN2, DN3]

Block state machine:
  UNDER_REPLICATED -> replicas assigned -> UNDER_CONSTRUCTION -> COMPLETED
  CORRUPT -> replication to new DN -> UNDER_REPLICATED -> ...
```

## Rack Awareness

- Script: returns network topology for node IP (`/rack/rack1`, `/rack/rack2`)
- Configure: `net.topology.node.switch.mapping.impl`
- Default: `DefaultRackTopology` (all in /default-rack) — always configure for multi-rack!

```
Replica placement (default 3):
  1st replica: same node as writer, or same rack
  2nd replica: different rack (cross-rack redundancy)
  3rd replica: same rack as 2nd (but different node)

Network cost:
  same node:      0
  same rack:      1
  different rack: 2
  different DC:   3+ (additional cost)
```

## HDFS Federation

- Multiple NNs manage independent namespace volumes
- Each NN owns a block pool (subset of DataNode storage)
- DataNodes register with all NNs, block pools are isolated
- Client uses ViewFs or mount table for transparent access

```
Federation architecture:
  NN-1 (sales):    /data/sales     -> block pool BP-1
  NN-2 (analytics): /data/analytics -> block pool BP-2
  NN-3 (users):    /user           -> block pool BP-3

  DataNode pool: DNs store blocks for BP-1, BP-2, BP-3
  Client mount:  /sales  -> hdfs://nn1:8020/data/sales
                  /analytics -> hdfs://nn2:8020/data/analytics
```

## Erasure Coding

- RS-6-3: 6 data + 3 parity = 12 blocks, tolerates 3 failures
- RS-3-2: 3 data + 2 parity = 5 blocks, tolerates 2 failures
- XOR-2-1: 2 data + 1 parity = 3 blocks, tolerates 1 failure

```
Space efficiency comparison (3x replication vs EC):
  RF3:  100TB raw -> 33TB usable (67% overhead)
  RS-6-3: 100TB raw -> 66TB usable (50% overhead)
  RS-3-2: 100TB raw -> 60TB usable (40% overhead)

Configuration:
  hdfs ec -enablePolicy -policy RS-6-3-1024k
  hdfs ec -setPolicy -path /cold_data -policy RS-6-3-1024k
```

## Fsimage and Edits Log

- Fsimage: checkpoint of filesystem metadata (directories, files, permissions, block lists)
- Edits log: incremental journal of transactions since last checkpoint
- Checkpoint: Standby NN merges fsimage + edits -> new fsimage
- Recovery: replay edits log into fsimage on startup

```
Checkpoint cycle:
  Every 3600s (dfs.namenode.checkpoint.period)
  OR every 1M transactions (dfs.namenode.checkpoint.txns)

Edits segment:
  edits_0000000001-0000001000
  edits_0000001001-0000002000
  Current edits: edits_inprogress_0000002001

Recovery on NN restart:
  1. Load fsimage into memory
  2. Replay all edits segments in order
  3. Start serving client requests
  4. Memory usage: ~1KB per file + ~200 bytes per block
```

## Key Configuration

```xml
<!-- hdfs-site.xml -->
<property><name>dfs.nameservices</name><value>mycluster</value></property>
<property><name>dfs.ha.namenodes.mycluster</name><value>nn1,nn2</value></property>
<property><name>dfs.namenode.rpc-address.mycluster.nn1</name><value>nn1-host:8020</value></property>
<property><name>dfs.namenode.rpc-address.mycluster.nn2</name><value>nn2-host:8020</value></property>
<property><name>dfs.namenode.shared.edits.dir</name>
  <value>qjournal://jn1:8485;jn2:8485;jn3:8485/mycluster</value></property>
<property><name>dfs.blocksize</name><value>134217728</value></property>
<property><name>dfs.replication</name><value>3</value></property>
<property><name>dfs.namenode.handler.count</name><value>128</value></property>
<property><name>dfs.heartbeat.interval</name><value>3</value></property>
</configuration>
```
