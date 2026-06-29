# Performance, Monitoring, Maintenance, and RHEL Configuration

Reference file for the `db2-rhel` skill. Covers performance tuning (db2advis, db2pd, MON functions), monitoring, maintenance, RHEL-specific configuration, and DB2 pureScale.

## 6. Performance Tuning

### AUTOCONFIGURE

```bash
su - db2inst1
db2 connect to myappdb

# Auto-tune based on workload hints
db2 "AUTOCONFIGURE USING
     MEM_PERCENT 75
     WORKLOAD_TYPE MIXED
     NUM_STMTS 500
     TPM 1000
     ADMIN_PRIORITY BOTH
     IS_POPULATED YES
     NUM_LOCAL_APPS 5
     NUM_REMOTE_APPS 100
     ISOLATION RR
     APPLY DB AND DBM"

db2 connect reset
```

### Self-Tuning Memory Manager (STMM)

```bash
# Enable STMM
db2 update db cfg for myappdb using SELF_TUNING_MEM ON

# Enable self-tuning on individual heaps
db2 update db cfg for myappdb using SORTHEAP AUTOMATIC
db2 update db cfg for myappdb using SHEAPTHRES_SHR AUTOMATIC
db2 update db cfg for myappdb using LOCKLIST AUTOMATIC
db2 update db cfg for myappdb using PCKCACHESZ AUTOMATIC
db2 update db cfg for myappdb using DATABASE_MEMORY AUTOMATIC

# Buffer pools participate in STMM when set to AUTOMATIC
db2 "ALTER BUFFERPOOL BP_DATA SIZE AUTOMATIC"
```

### db2advis (Index Advisor)

```bash
su - db2inst1
db2 connect to myappdb

# Advise indexes for a specific query
db2advis -d myappdb -s "SELECT c.name, o.total FROM app.customers c JOIN app.orders o ON c.id = o.customer_id WHERE c.email LIKE '%@example.com'" -m I

# Advise from a workload file (SQL statements, one per line)
db2advis -d myappdb -i /tmp/workload.sql -m I -l 500

# Advise indexes and MQTs (Materialized Query Tables)
db2advis -d myappdb -i /tmp/workload.sql -m IMP -l 1000

db2 connect reset
```

Flags: `-m I` = indexes only, `-m M` = MQTs, `-m P` = partitioning, `-l` = disk limit in MB.

### db2expln (Explain Plans)

```bash
su - db2inst1

# Explain a single statement
db2expln -d myappdb -q "SELECT * FROM app.customers WHERE email = 'foo@bar.com'" -g -t

# Explain from package cache (already-optimized SQL)
db2 connect to myappdb
db2 "EXPLAIN PLAN FOR SELECT * FROM app.customers WHERE email = 'foo@bar.com'"
db2 "SELECT * FROM SYSTOOLS.EXPLAIN_STATEMENT ORDER BY EXPLAIN_TIME DESC FETCH FIRST 5 ROWS ONLY"
db2 connect reset

# Visual explain (requires db2exfmt)
db2exfmt -d myappdb -1 -o explain_output.txt
```

### db2pd (Problem Determination)

```bash
su - db2inst1

# Instance overview
db2pd -

# Database overview
db2pd -db myappdb -

# Active applications
db2pd -db myappdb -applications

# Lock waits and deadlocks
db2pd -db myappdb -locks showlocks
db2pd -db myappdb -wlocks

# Buffer pool stats
db2pd -db myappdb -bufferpools

# Tablespace utilization
db2pd -db myappdb -tablespaces

# Transaction logs
db2pd -db myappdb -logs

# Dynamic SQL (top consumers)
db2pd -db myappdb -dynamic

# HADR status
db2pd -db myappdb -hadr

# Memory usage
db2pd -db myappdb -dbmcfg
db2pd -db myappdb -mem
```

### MON_GET Functions (Monitoring Table Functions)

```sql
CONNECT TO myappdb;

-- Top SQL by execution time
SELECT EXECUTABLE_ID, NUM_EXECUTIONS, TOTAL_ACT_TIME / 1000 AS TOTAL_MS,
       ROWS_READ, ROWS_RETURNED, SUBSTR(STMT_TEXT, 1, 200) AS SQL_TEXT
FROM TABLE(MON_GET_PKG_CACHE_STMT(NULL, NULL, NULL, -2)) AS T
ORDER BY TOTAL_ACT_TIME DESC
FETCH FIRST 20 ROWS ONLY;

-- Buffer pool hit ratios per database
SELECT BP_NAME,
       POOL_DATA_L_READS, POOL_DATA_P_READS, POOL_INDEX_L_READS, POOL_INDEX_P_READS,
       CASE WHEN (POOL_DATA_L_READS + POOL_INDEX_L_READS) > 0
            THEN DECIMAL((1.0 - FLOAT(POOL_DATA_P_READS + POOL_INDEX_P_READS)
                 / (POOL_DATA_L_READS + POOL_INDEX_L_READS)) * 100, 5, 2)
            ELSE 100.00 END AS OVERALL_HIT_PCT
FROM TABLE(MON_GET_BUFFERPOOL(NULL, -2)) AS BP;

-- Active connections
SELECT APPLICATION_HANDLE, APPLICATION_NAME, CLIENT_HOSTNAME,
       ACTIVITY_STATE, UOW_START_TIME
FROM TABLE(MON_GET_CONNECTION(NULL, -2)) AS C
WHERE ACTIVITY_STATE != 'IDLE';

-- Lock waits
SELECT REQ_APPLICATION_HANDLE, REQ_AGENT_TID,
       HLD_APPLICATION_HANDLE, LOCK_OBJECT_TYPE, LOCK_MODE, LOCK_WAIT_START_TIME
FROM TABLE(MON_GET_APPL_LOCKWAIT(NULL, -2)) AS LW;

-- Log utilization
SELECT LOG_UTILIZATION_PERCENT, TOTAL_LOG_USED_KB, TOTAL_LOG_AVAILABLE_KB
FROM SYSIBMADM.LOG_UTILIZATION;

-- Tablespace I/O
SELECT TBSP_NAME, POOL_DATA_P_READS, POOL_DATA_WRITES,
       DIRECT_READS, DIRECT_WRITES
FROM TABLE(MON_GET_TABLESPACE(NULL, -2)) AS TS
ORDER BY POOL_DATA_P_READS DESC;

CONNECT RESET;
```

### Lock Tuning

```bash
# Lock timeout (seconds; -1 = wait forever, 0 = no wait)
db2 update db cfg for myappdb using LOCKTIMEOUT 30

# Deadlock check interval (milliseconds)
db2 update db cfg for myappdb using DLCHKTIME 10000

# Lock list size (pages)
db2 update db cfg for myappdb using LOCKLIST AUTOMATIC
db2 update db cfg for myappdb using MAXLOCKS AUTOMATIC

# Current lock escalation
db2 "SELECT LOCK_ESCALS FROM TABLE(MON_GET_DATABASE(-2)) AS D"
```

---

## 7. Monitoring

### db2top (Real-Time Dashboard)

```bash
su - db2inst1

# Interactive dashboard
db2top -d myappdb

# Non-interactive snapshot
db2top -d myappdb -b -n -C     # bufferpools
db2top -d myappdb -b -n -l     # sessions/locks
db2top -d myappdb -b -n -D     # dynamic SQL
db2top -d myappdb -b -n -T     # tablespaces
```

Inside db2top: press `d` (dynamic SQL), `b` (bufferpools), `l` (locks), `T` (tablespaces), `U` (utilities), `s` (statements).

### Snapshot Monitor (Legacy but Useful)

```bash
su - db2inst1
db2 connect to myappdb

# Enable monitors
db2 update monitor switches using BUFFERPOOL ON LOCK ON SORT ON STATEMENT ON TABLE ON UOW ON

# Database snapshot
db2 get snapshot for database on myappdb

# Application snapshots
db2 get snapshot for applications on myappdb

# Bufferpool snapshot
db2 get snapshot for bufferpools on myappdb

# Tablespace snapshot
db2 get snapshot for tablespaces on myappdb

# Dynamic SQL snapshot
db2 get snapshot for dynamic sql on myappdb

# Reset counters
db2 reset monitor all

db2 connect reset
```

### Event Monitors

```sql
CONNECT TO myappdb;

-- Create event monitor for deadlocks
CREATE EVENT MONITOR deadlock_mon
  FOR DEADLOCKS WITH DETAILS HISTORY
  WRITE TO UNFORMATTED EVENT TABLE (TABLE dl_events IN ts_data);

SET EVENT MONITOR deadlock_mon STATE 1;

-- Create event monitor for statements (expensive — use selectively)
CREATE EVENT MONITOR stmt_mon
  FOR STATEMENTS
  WRITE TO UNFORMATTED EVENT TABLE (TABLE stmt_events IN ts_data)
  AUTOSTART;

-- Query deadlock events
SELECT * FROM dl_events ORDER BY EVENT_TIMESTAMP DESC FETCH FIRST 10 ROWS ONLY;

CONNECT RESET;
```

### Diagnostic Logs

```bash
su - db2inst1

# db2diag.log — primary diagnostic log
# Location: ~/sqllib/db2dump/db2diag.log (or as configured)
db2 get dbm cfg | grep DIAGPATH

# View recent errors
tail -100 /home/db2inst1/sqllib/db2dump/db2diag.log

# Filter diagnostics with db2diag tool
db2diag -level Error -lastdays 1
db2diag -level Warning -gi "db=MYAPPDB" -lastdays 1

# Admin notification log (human-readable summary of critical events)
cat /home/db2inst1/sqllib/db2dump/instance_db2inst1/notifylevel/db2inst1.nfy

# First failure data capture (FFDC)
ls /home/db2inst1/sqllib/db2dump/
```

### SQL Analysis from Package Cache

```sql
CONNECT TO myappdb;

-- Worst performers by total time
SELECT EXECUTABLE_ID, NUM_EXECUTIONS,
       TOTAL_ACT_TIME, TOTAL_ACT_WAIT_TIME,
       ROWS_READ, ROWS_RETURNED,
       TOTAL_SORTS, SORT_OVERFLOWS,
       SUBSTR(STMT_TEXT, 1, 300) AS SQL_TEXT
FROM TABLE(MON_GET_PKG_CACHE_STMT(NULL, NULL, NULL, -2)) AS T
WHERE NUM_EXECUTIONS > 0
ORDER BY TOTAL_ACT_TIME DESC
FETCH FIRST 20 ROWS ONLY;

-- Statements with high rows-read-to-rows-returned ratio (table scans)
SELECT EXECUTABLE_ID, NUM_EXECUTIONS,
       ROWS_READ, ROWS_RETURNED,
       CASE WHEN ROWS_RETURNED > 0
            THEN ROWS_READ / ROWS_RETURNED
            ELSE ROWS_READ END AS READ_EFFICIENCY,
       SUBSTR(STMT_TEXT, 1, 200) AS SQL_TEXT
FROM TABLE(MON_GET_PKG_CACHE_STMT(NULL, NULL, NULL, -2)) AS T
WHERE NUM_EXECUTIONS > 10 AND ROWS_READ > 10000
ORDER BY READ_EFFICIENCY DESC
FETCH FIRST 20 ROWS ONLY;

-- Statements causing sort overflows
SELECT NUM_EXECUTIONS, TOTAL_SORTS, SORT_OVERFLOWS,
       SUBSTR(STMT_TEXT, 1, 200) AS SQL_TEXT
FROM TABLE(MON_GET_PKG_CACHE_STMT(NULL, NULL, NULL, -2)) AS T
WHERE SORT_OVERFLOWS > 0
ORDER BY SORT_OVERFLOWS DESC
FETCH FIRST 10 ROWS ONLY;

CONNECT RESET;
```

---

## 8. Maintenance

### RUNSTATS

```bash
su - db2inst1
db2 connect to myappdb

# Basic RUNSTATS on a table
db2 "RUNSTATS ON TABLE app.customers"

# RUNSTATS with distribution and detailed index stats
db2 "RUNSTATS ON TABLE app.customers WITH DISTRIBUTION AND DETAILED INDEXES ALL"

# RUNSTATS allowing read access during collection
db2 "RUNSTATS ON TABLE app.customers WITH DISTRIBUTION AND DETAILED INDEXES ALL ALLOW READ ACCESS"

# RUNSTATS on specific columns (for frequently filtered columns)
db2 "RUNSTATS ON TABLE app.customers ON COLUMNS (email, created_at) WITH DISTRIBUTION AND DETAILED INDEXES ALL"

# Check when stats were last collected
db2 "SELECT TABSCHEMA, TABNAME, STATS_TIME FROM SYSCAT.TABLES WHERE TABSCHEMA = 'APP'"

db2 connect reset
```

### REORG TABLE

```bash
su - db2inst1
db2 connect to myappdb

# Check if reorg is needed
db2 "REORGCHK UPDATE STATISTICS ON TABLE app.customers"

# Offline REORG (exclusive access)
db2 "REORG TABLE app.customers"

# Online REORG (allows concurrent access — requires a temp tablespace)
db2 "REORG TABLE app.customers INPLACE ALLOW WRITE ACCESS"

# Online REORG with start/pause/resume
db2 "REORG TABLE app.customers INPLACE ALLOW WRITE ACCESS START"
db2 "REORG TABLE app.customers INPLACE PAUSE"
db2 "REORG TABLE app.customers INPLACE RESUME"

# REORG INDEX
db2 "REORG INDEXES ALL FOR TABLE app.customers ALLOW WRITE ACCESS"

# Monitor reorg progress
db2 "SELECT REORG_STATUS, REORG_PHASE, REORG_TYPE, REORG_START, REORG_END
     FROM SYSIBMADM.SNAPTAB_REORG WHERE TABSCHEMA = 'APP' AND TABNAME = 'CUSTOMERS'"

db2 connect reset
```

### Automatic Maintenance

```bash
su - db2inst1

# Enable automatic maintenance
db2 update db cfg for myappdb using AUTO_MAINT ON
db2 update db cfg for myappdb using AUTO_TBL_MAINT ON
db2 update db cfg for myappdb using AUTO_RUNSTATS ON
db2 update db cfg for myappdb using AUTO_STMT_STATS ON
db2 update db cfg for myappdb using AUTO_REORG ON
db2 update db cfg for myappdb using AUTO_DB_BACKUP ON

# Set maintenance window
db2 "CALL SYSPROC.AUTOMAINT_SET_SCHEDULE('RUNSTATS',
     NULL, NULL, NULL, 22, 0, NULL, 6, 0)"
# Parameters: object, startdate, enddate, startday, starthour, startmin, endday, endhour, endmin

# View current auto-maintenance config
db2 "CALL SYSPROC.AUTOMAINT_GET_SCHEDULE('RUNSTATS', ?, ?)"
```

### db2look (DDL Extraction)

```bash
su - db2inst1

# Extract all DDL for a database
db2look -d myappdb -e -o /tmp/myappdb_ddl.sql

# Extract DDL for specific schema
db2look -d myappdb -e -z APP -o /tmp/app_schema_ddl.sql

# Extract DDL with statistics (for cloning optimizer behavior)
db2look -d myappdb -e -m -o /tmp/myappdb_ddl_with_stats.sql

# Extract only table DDL for specific table
db2look -d myappdb -e -t app.customers -o /tmp/customers_ddl.sql

# Extract authorization DDL
db2look -d myappdb -x -o /tmp/myappdb_auth.sql

# Extract database configuration
db2look -d myappdb -f -o /tmp/myappdb_cfg.sql
```

---

## 9. RHEL-Specific Configuration

### SELinux Contexts for DB2

```bash
# DB2 installation directory
sudo semanage fcontext -a -t usr_t "/opt/ibm/db2(/.*)?"
sudo restorecon -Rv /opt/ibm/db2

# DB2 instance home directory
sudo semanage fcontext -a -t user_home_t "/home/db2inst1(/.*)?"
sudo restorecon -Rv /home/db2inst1

# DB2 data directories
sudo semanage fcontext -a -t db2_data_t "/db2data(/.*)?"
sudo restorecon -Rv /db2data

# If db2_data_t is not available (no DB2 SELinux policy module), use a generic type
# and create a custom module
sudo semanage fcontext -a -t var_t "/db2data(/.*)?"
sudo restorecon -Rv /db2data

# DB2 archive log directory
sudo semanage fcontext -a -t var_log_t "/db2archlog(/.*)?"
sudo restorecon -Rv /db2archlog

# DB2 backup directory
sudo semanage fcontext -a -t var_t "/db2backup(/.*)?"
sudo restorecon -Rv /db2backup

# Verify contexts
ls -lZ /opt/ibm/db2 /db2data /db2archlog /db2backup

# Troubleshoot SELinux denials for DB2
sudo ausearch -m AVC -c db2sysc --start recent
sudo ausearch -m AVC -c db2fm --start recent
sudo sealert -a /var/log/audit/audit.log

# Generate and apply custom policy module if needed
sudo ausearch -m AVC --start recent | audit2allow -M db2custom
sudo semodule -i db2custom.pp
```

### Firewalld Rules

```bash
# DB2 client connections (restrict to app subnet)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.1.0/24" port port="50000" protocol="tcp" accept'

# DB2 SSL port
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.1.0/24" port port="50001" protocol="tcp" accept'

# HADR replication port
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.2.10/32" port port="50002" protocol="tcp" accept'

# DB2 FCM (Fast Communication Manager) for pureScale/partitioned
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.2.0/24" port port="60000-60005" protocol="tcp" accept'

# Apply and verify
sudo firewall-cmd --reload
sudo firewall-cmd --list-rich-rules
```

### Systemd Service for DB2 Instance

Create `/etc/systemd/system/db2inst1.service`:

```ini
[Unit]
Description=IBM DB2 Instance db2inst1
After=network.target

[Service]
Type=forking
User=db2inst1
Group=db2iadm1
ExecStartPre=/bin/bash -c '. /home/db2inst1/sqllib/db2profile'
ExecStart=/bin/bash -lc '. /home/db2inst1/sqllib/db2profile && db2start'
ExecStop=/bin/bash -lc '. /home/db2inst1/sqllib/db2profile && db2stop force'
TimeoutStartSec=120
TimeoutStopSec=120
Restart=on-failure
RestartSec=30
LimitNOFILE=65536
LimitNPROC=16384

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable db2inst1
sudo systemctl start db2inst1
sudo systemctl status db2inst1
```

### Kernel Tuning (sysctl)

Full `/etc/sysctl.d/99-db2.conf` for production:

```
# Shared memory
kernel.shmmax = 68719476736
kernel.shmall = 16777216
kernel.shmmni = 4096

# Message queues
kernel.msgmni = 16384
kernel.msgmax = 65536
kernel.msgmnb = 65536

# Semaphores: SEMMSL SEMMNS SEMOPM SEMMNI
kernel.sem = 250 256000 32 1024

# Virtual memory
vm.swappiness = 5
vm.overcommit_memory = 0
vm.dirty_ratio = 15
vm.dirty_background_ratio = 3

# Network (for HADR and client connections)
net.core.somaxconn = 4096
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_max_syn_backlog = 8096
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 5
```

### Large Pages (Huge Pages)

```bash
# Calculate huge pages needed (example: 16GB for DB2 shared memory, 2MB page size)
# 16GB / 2MB = 8192 pages
echo 8192 | sudo tee /proc/sys/vm/nr_hugepages

# Persist in sysctl
echo "vm.nr_hugepages = 8192" | sudo tee -a /etc/sysctl.d/99-db2.conf
sudo sysctl --system

# Verify
grep -i huge /proc/meminfo

# Grant db2inst1 group permission to use huge pages
echo "@db2iadm1 - memlock unlimited" | sudo tee -a /etc/security/limits.d/99-db2.conf

# Enable in DB2
su - db2inst1
db2set DB2_LARGE_PAGE_MEM=*
db2stop force
db2start
```

### File Descriptor and Process Limits

`/etc/security/limits.d/99-db2.conf`:

```
db2inst1  soft  nofile  65536
db2inst1  hard  nofile  65536
db2inst1  soft  nproc   16384
db2inst1  hard  nproc   16384
db2inst1  soft  memlock unlimited
db2inst1  hard  memlock unlimited
db2fenc1  soft  nofile  65536
db2fenc1  hard  nofile  65536
db2fenc1  soft  nproc   16384
db2fenc1  hard  nproc   16384
```

---

## 10. DB2 pureScale

### Overview

DB2 pureScale provides shared-data, active-active clustering for DB2 LUW. All members read and write the same data simultaneously — no data partitioning required. It delivers continuous availability and transparent horizontal scaling.

### Architecture Components

- **Members** — DB2 database engine instances that process SQL. All members are active and can handle read/write workloads.
- **Cluster Caching Facility (CF)** — Centralized shared memory facility that manages global buffer pool, lock management, and group buffer pool. Typically runs on dedicated hosts. Configure a primary and secondary CF for redundancy.
- **GPFS / IBM Spectrum Scale** — Required shared filesystem. All members and CFs access the same storage through GPFS.
- **Cluster interconnect** — Low-latency network (InfiniBand or 10GbE+) between members and CFs for lock and page transfer.

### Requirements

```bash
# GPFS / IBM Spectrum Scale must be installed and mounted on all nodes
mmlscluster
mmlsfs all
mmgetstate -a

# Verify RDMA / high-speed interconnect
ibstat               # InfiniBand
ip link show         # 10GbE bonded interfaces

# All nodes must have identical DB2 versions, OS levels, and user IDs
/opt/ibm/db2/V11.5/instance/db2ilist
```

### Creating a pureScale Instance

```bash
# Run on the first member — creates the instance across all nodes
sudo /opt/ibm/db2/V11.5/instance/db2icrt -d \
  -cf cf1.example.com -cfnet cf1-ib.example.com \
  -cf cf2.example.com -cfnet cf2-ib.example.com \
  -m member1.example.com -mnet member1-ib.example.com \
  -m member2.example.com -mnet member2-ib.example.com \
  -instance_shared_dev /dev/hdisk1 \
  -tbdev /dev/hdisk2 \
  -u db2fenc1 db2inst1
```

### Member Management

```bash
su - db2inst1

# Add a member
db2iupdt db2inst1 -add -m member3.example.com -mnet member3-ib.example.com

# Remove a member
db2iupdt db2inst1 -drop -m member3.example.com

# Start/stop specific member
db2start member 0
db2stop member 0 force

# View cluster status
db2instance -list
db2pd -db myappdb -members
```

### When to Use pureScale vs HADR

| Criterion | pureScale | HADR |
|---|---|---|
| **Goal** | Scale-out active-active + HA | Disaster recovery + HA |
| **Data access** | All members read/write simultaneously | Primary only; standby is read-only (or no access) |
| **Infrastructure** | Shared storage (GPFS), dedicated CFs, low-latency interconnect | Independent storage per server, any network |
| **Cost** | Higher (hardware, GPFS, pureScale license) | Lower (standard DB2 ESE license + OS) |
| **RPO** | Zero (shared data) | Zero (SYNC) to minutes (ASYNC) |
| **RTO** | Seconds (member restart) | Seconds to minutes (takeover) |
| **Scaling** | Horizontal read/write scaling | No read scaling (standby can handle reads with HADR_SPOOL_LIMIT) |
| **Recommendation** | High-throughput OLTP needing linear scale-out | Most environments needing HA/DR without shared storage |

For most RHEL deployments, HADR with automatic client reroute is the standard HA pattern. pureScale is reserved for workloads requiring active-active read/write scaling or sub-second failover without application awareness.

---

## Related Skills

| Workload | Skill |
|---|---|
| Core RHEL admin (dnf, SELinux, firewalld, LVM) | `rhel-server-admin` |
| PostgreSQL, MySQL, Redis on RHEL | `rhel-databases` |
| Python DB2/Oracle/SQL Server connectors | `python-enterprise-connectors` |
| Web servers (Nginx, Apache, Caddy) | `rhel-web-servers` |
| Docker / Podman containers | `rhel-docker-host` |
| Monitoring (Prometheus, Grafana, PCP) | `rhel-monitoring` |
