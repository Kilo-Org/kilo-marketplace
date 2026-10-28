---
name: hadoop
description: >-
  Manage Hadoop clusters with HDFS operations, YARN job tuning, and distributed
  processing diagnostics.
metadata:
  clawdbot:
    emoji: "\U0001F418"
    requires:
      bins:
        - hdfs
        - yarn
        - hadoop
    os:
      - linux
      - darwin
  upstream:
    slug: hadoop
    version: 1.0.0
    homepage: 'https://clawic.com/skills/hadoop'
  category: data
  source:
    repository: 'https://github.com/clawic/skills'
    path: skills/hadoop
    license_path: LICENSE
    commit: ff40511e7588b7b91d4427b65931f420a7412bb0
---

## Setup

If `~/hadoop/` doesn't exist or is empty, read `setup.md` and start the conversation naturally.

## When to Use

User works with Hadoop ecosystem (HDFS, YARN, MapReduce, Hive). Agent handles cluster diagnostics, job optimization, storage management, and troubleshooting distributed processing failures.

## Architecture

Memory lives in `~/hadoop/`. See `memory-template.md` for structure.

```
~/hadoop/
├── memory.md        # Cluster configs, common issues, preferences
├── clusters/        # Per-cluster notes and configs
│   └── {name}.md    # Specific cluster context
└── scripts/         # Custom diagnostic scripts
```

## Quick Reference

| Topic | File |
|-------|------|
| Setup process | `setup.md` |
| Memory template | `memory-template.md` |
| HDFS operations | `hdfs.md` |
| YARN tuning | `yarn.md` |
| Troubleshooting | `troubleshooting.md` |

## Core Rules

### 1. Verify Cluster State First
Before any operation, check cluster health:
```bash
hdfs dfsadmin -report
yarn node -list
```
Never assume cluster is healthy. A single dead DataNode changes everything.

### 2. Storage Before Compute
HDFS issues cascade into job failures. Always check:
```bash
hdfs dfs -df -h                    # Capacity
hdfs fsck / -files -blocks         # Block health
```
A job failing with "No space left" is storage, not code.

### 3. Resource Calculator Awareness
YARN allocates based on configured scheduler. Know which is active:
```bash
yarn rmadmin -getServiceState rm1
cat /etc/hadoop/conf/yarn-site.xml | grep scheduler
```
Default (Capacity) vs Fair scheduler behave very differently.

### 4. Replication Factor Context
Default replication=3. For temp data, suggest 1-2 to save space:
```bash
hdfs dfs -setrep -w 1 /tmp/scratch/
```
For critical data, verify replication is honored:
```bash
hdfs fsck /data/critical -files -blocks -replicaDetails
```

### 5. Log Location Awareness
Hadoop logs scatter across machines. Key locations:
| Component | Log Path |
|-----------|----------|
| NameNode | /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*.log |
| DataNode | /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log |
| ResourceManager | /var/log/hadoop-yarn/yarn-yarn-resourcemanager-*.log |
| NodeManager | /var/log/hadoop-yarn/yarn-yarn-nodemanager-*.log |
| Application | yarn logs -applicationId <app_id> |

### 6. Safe Mode Handling
NameNode enters safe mode on startup or low block count:
```bash
hdfs dfsadmin -safemode get        # Check status
hdfs dfsadmin -safemode leave      # Exit (if blocks OK)
```
Never force-leave if blocks are actually missing.

### 7. Memory Settings Matter
90% of "job killed" issues are memory:
```bash
# Container settings
yarn.nodemanager.resource.memory-mb     # Total per node
yarn.scheduler.minimum-allocation-mb    # Min container
mapreduce.map.memory.mb                 # Map task
mapreduce.reduce.memory.mb              # Reduce task
```
Check these before assuming code is wrong.

## HDFS Operations

### Essential Commands
```bash
# Navigation
hdfs dfs -ls /path
hdfs dfs -du -h /path              # Size with human units
hdfs dfs -count -q /path           # Quota info

# Data movement
hdfs dfs -put local.txt /hdfs/     # Upload
hdfs dfs -get /hdfs/file.txt .     # Download
hdfs dfs -cp /src /dst             # Copy within HDFS
hdfs dfs -mv /src /dst             # Move within HDFS

# Maintenance
hdfs dfs -rm -r /path              # Delete (trash)
hdfs dfs -rm -r -skipTrash /path   # Delete (permanent)
hdfs dfs -expunge                  # Empty trash
```

### Block Management
```bash
# Find corrupt blocks
hdfs fsck / -list-corruptfileblocks

# Delete corrupt file (after confirming unrecoverable)
hdfs fsck /path/file -delete

# Force replication
hdfs dfs -setrep -w 3 /important/data/
```

## YARN Job Management

### Application Lifecycle
```bash
# List applications
yarn application -list                    # Running
yarn application -list -appStates ALL     # All states

# Application details
yarn application -status <app_id>

# Kill stuck application
yarn application -kill <app_id>

# Get logs (after completion)
yarn logs -applicationId <app_id>
yarn logs -applicationId <app_id> -containerId <container_id>
```

### Queue Management
```bash
# List queues
yarn queue -list

# Queue status
yarn queue -status <queue_name>

# Move application between queues
yarn application -movetoqueue <app_id> -queue <target_queue>
```

## Common Traps

- **Deleting without -skipTrash on full cluster** → Trash still uses space, cluster stays full
- **Setting container memory below JVM heap** → Instant container kill, confusing errors
- **Ignoring speculative execution on slow jobs** → Wastes resources on duplicated tasks
- **Running fsck on busy cluster** → Performance impact, run during maintenance
- **Assuming HDFS = POSIX semantics** → No append-in-place, no random writes
- **Forgetting timezone in scheduling** → Oozie/Airflow jobs fire at wrong times

## Security & Privacy

**Data that stays local:**
- Cluster notes saved in ~/hadoop/clusters/
- Preferences and environment context

**What commands access:**
- hdfs/yarn commands connect to your Hadoop cluster
- Some commands read system paths (/var/log, /etc/hadoop/conf)
- Destructive commands require explicit user confirmation

**This skill does NOT:**
- Store credentials (use kinit/keytab separately)
- Make external API calls beyond your cluster
- Run destructive commands without asking first

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `linux` — system administration
- `docker` — containerized deployments
- `bash` — shell scripting

## Feedback

- If useful: `clawhub star hadoop`
- Stay updated: `clawhub sync`
