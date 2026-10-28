# Troubleshooting — Hadoop

## Quick Diagnosis Flow

```
Job Failed?
├── Check YARN app status: yarn application -status <app_id>
├── Get logs: yarn logs -applicationId <app_id>
├── Look for:
│   ├── "Container killed" → Memory issue
│   ├── "No space left" → HDFS full
│   ├── "Connection refused" → Service down
│   └── "Permission denied" → ACL/Kerberos
└── Fix based on error category below
```

## HDFS Issues

### NameNode Won't Start

**Symptoms:** NameNode fails to start, logs show formatting errors

**Check:**
```bash
# Review NameNode logs
tail -500 /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*.log

# Common causes:
# 1. Corrupted fsimage/edits
# 2. Disk full on NameNode
# 3. Port already in use
```

**Fix - Port conflict:**
```bash
netstat -tlnp | grep 8020
# Kill conflicting process or change port
```

**Fix - Disk full:**
```bash
df -h /var/lib/hadoop-hdfs
# Clean up old checkpoints if safe
```

### Stuck in Safe Mode

**Symptoms:** "Cannot create file. Name node is in safe mode"

**Check:**
```bash
hdfs dfsadmin -safemode get
hdfs fsck / -list-corruptfileblocks
```

**Fix - If blocks are healthy:**
```bash
hdfs dfsadmin -safemode leave
```

**Fix - If blocks are corrupt:**
```bash
# Option 1: Wait for replication
hdfs dfsadmin -safemode wait

# Option 2: Delete corrupt files (data loss!)
hdfs fsck / -delete
```

### DataNode Not Registering

**Symptoms:** DataNode running but not in cluster

**Check:**
```bash
# On DataNode
tail -200 /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log

# Look for:
# - "Incompatible clusterIDs"
# - "NameNode still not started"
# - Network connectivity issues
```

**Fix - Incompatible cluster ID:**
```bash
# ⚠️ DATA LOSS WARNING - only for fresh nodes with no data
# 1. Confirm node has no valuable data
# 2. Back up if uncertain: cp -r /data/hdfs/datanode/current /backup/
# 3. Only then remove: rm -rf /data/hdfs/datanode/current
# 4. Restart: service hadoop-hdfs-datanode restart
```

**Fix - Network:**
```bash
# From DataNode
telnet namenode-host 8020
# If fails: check firewall, DNS
```

### HDFS Full

**Symptoms:** "No space left on device" in job logs

**Check:**
```bash
hdfs dfs -df -h
hdfs dfs -du -h / | sort -h | tail -20
```

**Fix:**
```bash
# 1. Empty trash
hdfs dfs -expunge

# 2. Find large temp files
hdfs dfs -du -h /tmp /user/*/.staging | sort -h | tail -20

# 3. Reduce replication on non-critical data
hdfs dfs -setrep 1 /tmp/

# 4. Run balancer if uneven
hdfs balancer -threshold 10
```

## YARN Issues

### Application Stuck in ACCEPTED

**Symptoms:** Job shows ACCEPTED but never RUNNING

**Check:**
```bash
yarn application -status <app_id>
yarn queue -status <queue_name>
```

**Common causes:**
1. No available resources
2. Queue at capacity
3. AM container can't launch

**Fix - Resource shortage:**
```bash
# Check cluster capacity
yarn node -list
# Kill low-priority jobs if urgent
yarn application -kill <other_app_id>
```

**Fix - Queue full:**
```bash
# Move to different queue
yarn application -movetoqueue <app_id> -queue another_queue
```

### Container Killed by YARN

**Symptoms:** Exit code -100, "Container killed by the ApplicationMaster"

**Check logs:**
```bash
yarn logs -applicationId <app_id> | grep -i "memory\|killed\|exceeded"
```

**Fix - Memory exceeded:**
```bash
# Increase container memory
# For MapReduce:
-Dmapreduce.map.memory.mb=4096
-Dmapreduce.reduce.memory.mb=8192

# For Spark:
--executor-memory 4g
--driver-memory 2g
```

### ResourceManager Failover Issues

**Check HA state:**
```bash
yarn rmadmin -getServiceState rm1
yarn rmadmin -getServiceState rm2
```

**Force failover:**
```bash
yarn rmadmin -transitionToStandby rm1 --forcemanual
yarn rmadmin -transitionToActive rm2 --forcemanual
```

## MapReduce Issues

### Map Tasks Failing

**Check:**
```bash
yarn logs -applicationId <app_id> -log_files syslog | grep -A5 "Error\|Exception"
```

**Common causes:**

| Error | Cause | Fix |
|-------|-------|-----|
| OutOfMemoryError | Heap too small | Increase mapreduce.map.java.opts |
| InputSplit too large | Bad input format | Check file format, compression |
| Task timeout | Slow processing | Increase mapreduce.task.timeout |

### Reduce Tasks Slow/Stuck

**Check shuffle phase:**
```bash
# In job tracker UI, check shuffle progress
# Or in logs:
yarn logs -applicationId <app_id> | grep -i "shuffle\|fetch"
```

**Common causes:**
1. Too few reducers (increase mapreduce.job.reduces)
2. Data skew (one key has most data)
3. Network bottleneck

**Fix - Data skew:**
```bash
# Use combiner to reduce mapper output
# Or custom partitioner to spread hot keys
```

### Job Counter Analysis

Key counters to check:
```
Map input records vs Map output records → Filtering ratio
Reduce shuffle bytes → Network transfer
Spilled Records → Memory pressure (increase io.sort.mb)
GC time → JVM tuning needed
```

## Performance Issues

### Slow Job Diagnosis

**Step 1: Check for data locality**
```bash
# In job history, check "Data-local maps" %
# Target: >90% data local
```

**Step 2: Check for stragglers**
```bash
# Enable speculative execution
-Dmapreduce.map.speculative=true
-Dmapreduce.reduce.speculative=true
```

**Step 3: Check for skew**
```bash
# Look at task duration variance
# If one task takes 10x longer: data skew
```

### Balancer Running Slow

**Increase bandwidth:**
```bash
hdfs balancer -Ddfs.datanode.balance.bandwidthPerSec=209715200  # 200MB/s
```

**Run with higher threshold (less precise but faster):**
```bash
hdfs balancer -threshold 15
```

## Security Issues

### Kerberos Authentication Failures

**Check:**
```bash
klist  # Current tickets
kinit -kt /path/to/keytab principal  # Refresh
```

**Common errors:**

| Error | Fix |
|-------|-----|
| Clock skew | Sync NTP across cluster |
| Ticket expired | kinit again |
| Keytab not found | Check path, permissions (600) |

### Permission Denied on HDFS

**Check:**
```bash
hdfs dfs -ls /path
hdfs dfs -getfacl /path
```

**Fix:**
```bash
# As superuser
hdfs dfs -chmod 755 /path
hdfs dfs -chown user:group /path
```

## Log Locations Quick Reference

| Component | Default Log Path |
|-----------|------------------|
| NameNode | /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*.log |
| DataNode | /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log |
| ResourceManager | /var/log/hadoop-yarn/yarn-yarn-resourcemanager-*.log |
| NodeManager | /var/log/hadoop-yarn/yarn-yarn-nodemanager-*.log |
| JobHistory | /var/log/hadoop-mapreduce/mapred-mapred-historyserver-*.log |
| Application | yarn logs -applicationId <app_id> |

## Emergency Commands

⚠️ **These commands are destructive. Always confirm with the user before running.**

```bash
# Kill all applications in queue (confirm first!)
yarn application -list -appStates RUNNING -queue bad_queue
# Then kill individually: yarn application -kill <app_id>

# Force leave safe mode (DANGEROUS if blocks missing - confirm!)
hdfs dfsadmin -safemode get  # Check first
hdfs dfsadmin -safemode leave  # Only if blocks are OK

# Restart services via Cloudera Manager UI or Ambari UI
# Prefer UI over CLI for audit trail
```
