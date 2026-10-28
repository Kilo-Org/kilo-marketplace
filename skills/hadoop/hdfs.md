# HDFS Operations — Hadoop

## Architecture Basics

```
NameNode (1-2)
├── Manages metadata (file → block mapping)
├── Handles namespace operations
└── Coordinates replication

DataNode (many)
├── Stores actual blocks
├── Sends heartbeats to NameNode
└── Handles read/write requests
```

## File Operations

### Reading Data
```bash
# List contents
hdfs dfs -ls /path
hdfs dfs -ls -R /path              # Recursive
hdfs dfs -ls -h /path              # Human-readable sizes

# View file content
hdfs dfs -cat /path/file.txt
hdfs dfs -head /path/file.txt      # First 1KB
hdfs dfs -tail /path/file.txt      # Last 1KB

# Download
hdfs dfs -get /hdfs/path local/path
hdfs dfs -getmerge /hdfs/dir local/file.txt  # Merge directory into one file
```

### Writing Data
```bash
# Upload
hdfs dfs -put local/file.txt /hdfs/path
hdfs dfs -put -f local/file.txt /hdfs/path   # Overwrite

# Create directory
hdfs dfs -mkdir -p /path/to/dir

# Move/Copy within HDFS
hdfs dfs -mv /source /destination
hdfs dfs -cp /source /destination

# Append (if supported)
hdfs dfs -appendToFile local.txt /hdfs/existing.txt
```

### Deleting Data
```bash
# Move to trash (recoverable)
hdfs dfs -rm /path/file
hdfs dfs -rm -r /path/dir

# Permanent delete (skip trash)
hdfs dfs -rm -skipTrash /path/file
hdfs dfs -rm -r -skipTrash /path/dir

# Empty trash
hdfs dfs -expunge
```

## Space Management

### Check Usage
```bash
# Cluster capacity
hdfs dfs -df -h

# Directory size
hdfs dfs -du -h /path
hdfs dfs -du -s -h /path           # Summary only

# Count files/directories
hdfs dfs -count /path
hdfs dfs -count -q /path           # Include quota
```

### Quotas
```bash
# Set space quota (bytes)
hdfs dfsadmin -setSpaceQuota 100G /path

# Set name quota (file/dir count)
hdfs dfsadmin -setQuota 10000 /path

# Clear quota
hdfs dfsadmin -clrSpaceQuota /path
hdfs dfsadmin -clrQuota /path

# Check quota
hdfs dfs -count -q /path
```

## Block Operations

### Check Block Health
```bash
# Full filesystem check
hdfs fsck /

# Specific path
hdfs fsck /path -files -blocks

# Show replica locations
hdfs fsck /path -files -blocks -locations

# Find corrupt blocks
hdfs fsck / -list-corruptfileblocks

# Find under-replicated blocks
hdfs fsck / -under-replicated-blocks
```

### Replication Management
```bash
# Change replication factor
hdfs dfs -setrep 2 /path/file
hdfs dfs -setrep -R 2 /path/dir    # Recursive
hdfs dfs -setrep -w 3 /path        # Wait for replication

# Check current replication
hdfs dfs -stat %r /path/file
```

## Snapshots

### Enable/Disable
```bash
# Enable snapshots for directory
hdfs dfsadmin -allowSnapshot /path

# Disable
hdfs dfsadmin -disallowSnapshot /path
```

### Create/Manage
```bash
# Create snapshot
hdfs dfs -createSnapshot /path snapshot_name

# List snapshots
hdfs dfs -ls /path/.snapshot

# Delete snapshot
hdfs dfs -deleteSnapshot /path snapshot_name

# Rename snapshot
hdfs dfs -renameSnapshot /path old_name new_name
```

### Restore from Snapshot
```bash
# Copy from snapshot
hdfs dfs -cp /path/.snapshot/snapshot_name/file /path/restored_file
```

## Permissions

### Basic Operations
```bash
# Change owner
hdfs dfs -chown user:group /path
hdfs dfs -chown -R user:group /path

# Change permissions
hdfs dfs -chmod 755 /path
hdfs dfs -chmod -R 755 /path

# Check ACLs
hdfs dfs -getfacl /path

# Set ACLs
hdfs dfs -setfacl -m user:alice:rwx /path
hdfs dfs -setfacl -m group:analysts:r-x /path
```

## Admin Operations

### Safe Mode
```bash
# Check status
hdfs dfsadmin -safemode get

# Enter/leave
hdfs dfsadmin -safemode enter
hdfs dfsadmin -safemode leave

# Wait for exit
hdfs dfsadmin -safemode wait
```

### Cluster Reports
```bash
# DataNode report
hdfs dfsadmin -report

# Print topology
hdfs dfsadmin -printTopology

# Refresh nodes
hdfs dfsadmin -refreshNodes
```

### Balancer
```bash
# Run balancer (default 10% threshold)
hdfs balancer

# Custom threshold
hdfs balancer -threshold 5

# Limit bandwidth (bytes/sec per DataNode)
hdfs balancer -Ddfs.datanode.balance.bandwidthPerSec=104857600
```

## Performance Tips

### Small Files Problem
Many small files = NameNode memory pressure.
Solutions:
- HAR (Hadoop Archive): `hadoop archive -archiveName files.har -p /input /output`
- Sequence files: combine into single file with keys
- CombineFileInputFormat for MapReduce

### Optimal Block Size
Default 128MB (or 256MB). Match to typical file size:
- Files < 128MB: consider combining
- Files >> 128MB: default is fine

### Read Locality
HDFS tries to read from local DataNode. For best performance:
- Process data where it lives
- Use rack awareness configuration
