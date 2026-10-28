# YARN Operations — Hadoop

## Architecture Basics

```
ResourceManager (1-2)
├── Schedules resources across cluster
├── Manages application lifecycle
└── Handles node heartbeats

NodeManager (per node)
├── Launches/monitors containers
├── Reports resource usage
└── Manages local resources

ApplicationMaster (per app)
├── Negotiates resources from RM
├── Works with NM to execute tasks
└── Handles task failures
```

## Application Management

### List Applications
```bash
# Running applications
yarn application -list

# All states
yarn application -list -appStates ALL

# Specific state
yarn application -list -appStates FAILED
yarn application -list -appStates KILLED
yarn application -list -appStates FINISHED

# Filter by type
yarn application -list -appTypes SPARK
yarn application -list -appTypes MAPREDUCE
```

### Application Details
```bash
# Full status
yarn application -status application_1234567890123_0001

# Kill application
yarn application -kill application_1234567890123_0001

# Move to different queue
yarn application -movetoqueue application_1234567890123_0001 -queue high_priority
```

### Application Logs
```bash
# All logs (after completion)
yarn logs -applicationId application_1234567890123_0001

# Specific container
yarn logs -applicationId <app_id> -containerId <container_id>

# Specific log type
yarn logs -applicationId <app_id> -log_files stdout
yarn logs -applicationId <app_id> -log_files stderr

# Save to file
yarn logs -applicationId <app_id> > app_logs.txt
```

## Queue Management

### View Queues
```bash
# List all queues
yarn queue -list

# Queue details
yarn queue -status default
yarn queue -status root.production
```

### Capacity Scheduler Config
Key parameters in `capacity-scheduler.xml`:
```xml
<!-- Queue capacity (% of cluster) -->
yarn.scheduler.capacity.root.default.capacity=40
yarn.scheduler.capacity.root.production.capacity=60

<!-- Max capacity (elastic growth) -->
yarn.scheduler.capacity.root.default.maximum-capacity=60

<!-- User limits -->
yarn.scheduler.capacity.root.default.user-limit-factor=1
yarn.scheduler.capacity.root.default.minimum-user-limit-percent=25
```

### Fair Scheduler Config
Key parameters in `fair-scheduler.xml`:
```xml
<queue name="production">
  <weight>2.0</weight>
  <schedulingPolicy>fair</schedulingPolicy>
  <minResources>10000 mb, 10 vcores</minResources>
</queue>
```

## Resource Configuration

### Node-Level Settings
```xml
<!-- yarn-site.xml -->

<!-- Total memory available to YARN -->
<property>
  <name>yarn.nodemanager.resource.memory-mb</name>
  <value>32768</value>
</property>

<!-- Total vCores available -->
<property>
  <name>yarn.nodemanager.resource.cpu-vcores</name>
  <value>16</value>
</property>

<!-- Minimum container allocation -->
<property>
  <name>yarn.scheduler.minimum-allocation-mb</name>
  <value>1024</value>
</property>

<!-- Maximum container allocation -->
<property>
  <name>yarn.scheduler.maximum-allocation-mb</name>
  <value>16384</value>
</property>
```

### MapReduce Memory Settings
```xml
<!-- mapred-site.xml -->

<!-- Map task memory -->
<property>
  <name>mapreduce.map.memory.mb</name>
  <value>2048</value>
</property>

<!-- Reduce task memory -->
<property>
  <name>mapreduce.reduce.memory.mb</name>
  <value>4096</value>
</property>

<!-- Map JVM heap (should be ~80% of container) -->
<property>
  <name>mapreduce.map.java.opts</name>
  <value>-Xmx1638m</value>
</property>

<!-- Reduce JVM heap -->
<property>
  <name>mapreduce.reduce.java.opts</name>
  <value>-Xmx3276m</value>
</property>
```

### Memory Formula
```
Container memory = JVM heap + overhead
JVM heap ≈ 0.8 × Container memory
Overhead = max(384MB, 0.1 × Container memory)
```

## Node Management

### List Nodes
```bash
# All nodes
yarn node -list

# Only healthy
yarn node -list -states RUNNING

# Node details
yarn node -status <node_id>
```

### Decommission Node
```bash
# 1. Add node to exclude file
echo "node-to-remove.example.com" >> /etc/hadoop/conf/yarn.exclude

# 2. Refresh nodes
yarn rmadmin -refreshNodes

# 3. Wait for containers to migrate, then remove from cluster
```

### Recommission Node
```bash
# 1. Remove from exclude file
# 2. Refresh
yarn rmadmin -refreshNodes
```

## ResourceManager Admin

### HA Operations
```bash
# Check RM state
yarn rmadmin -getServiceState rm1
yarn rmadmin -getServiceState rm2

# Manual failover
yarn rmadmin -transitionToActive rm2 --forcemanual
yarn rmadmin -transitionToStandby rm1 --forcemanual
```

### Refresh Operations
```bash
# Refresh queues (after config change)
yarn rmadmin -refreshQueues

# Refresh nodes
yarn rmadmin -refreshNodes

# Refresh admin ACLs
yarn rmadmin -refreshAdminAcls

# Refresh user-to-group mappings
yarn rmadmin -refreshUserToGroupsMappings
```

## Container Debugging

### Container Status
```bash
# List containers for application
yarn container -list <application_id>

# Container status
yarn container -status <container_id>
```

### Common Container Failures

| Exit Code | Meaning | Common Cause |
|-----------|---------|--------------|
| -100 | Container killed by RM | Exceeded memory/time |
| -103 | Container killed externally | Manual kill, node failure |
| -104 | Container launch failed | Configuration error |
| 137 | SIGKILL | OOM killer (memory) |
| 143 | SIGTERM | Preemption or shutdown |

### Debugging OOM
```bash
# Check container memory usage
yarn logs -applicationId <app_id> -containerId <container_id> | grep -i "memory\|heap\|oom"

# Common fixes:
# 1. Increase container memory
# 2. Increase JVM heap (but keep < container memory)
# 3. Check for memory leaks in code
```

## Tuning Tips

### Speculative Execution
Reruns slow tasks on other nodes. Good for stragglers, bad for expensive tasks:
```xml
<!-- Disable for predictable tasks -->
<property>
  <name>mapreduce.map.speculative</name>
  <value>false</value>
</property>
<property>
  <name>mapreduce.reduce.speculative</name>
  <value>false</value>
</property>
```

### Preemption
Allow high-priority queues to take resources:
```xml
<property>
  <name>yarn.scheduler.capacity.preemption</name>
  <value>true</value>
</property>
```

### Locality Delay
Wait for data-local slots before accepting rack-local:
```xml
<property>
  <name>yarn.scheduler.capacity.node-locality-delay</name>
  <value>40</value>
</property>
```
