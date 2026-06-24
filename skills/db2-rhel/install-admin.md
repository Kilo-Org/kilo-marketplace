# Installation, Instance, and Database Administration

Reference file for the `db2-rhel` skill. Covers DB2 installation on RHEL, instance management, and database administration (tablespaces, buffer pools, schemas, tables).

## 1. Installation

### RHEL Prerequisites

```bash
# Required packages
sudo dnf install -y pam pam-devel libstdc++ libstdc++-devel libaio libaio-devel \
  numactl numactl-libs cpp gcc gcc-c++ ksh binutils file

# Check 64-bit libraries present
rpm -qa | grep -E 'libstdc\+\+|libaio|pam' | grep x86_64
```

### Kernel Parameters

Edit `/etc/sysctl.d/99-db2.conf`:

```
kernel.shmmax = 68719476736
kernel.shmall = 16777216
kernel.shmmni = 4096
kernel.msgmni = 16384
kernel.msgmax = 65536
kernel.msgmnb = 65536
kernel.sem = 250 256000 32 1024
vm.swappiness = 5
vm.overcommit_memory = 0
```

Apply:
```bash
sudo sysctl --system
sysctl kernel.shmmax kernel.msgmni kernel.sem
```

### Create DB2 Users

```bash
# Instance owner
sudo groupadd -g 1100 db2iadm1
sudo useradd -u 1100 -g db2iadm1 -m -d /home/db2inst1 -s /bin/bash db2inst1

# Fenced user (runs fenced UDFs/stored procs)
sudo groupadd -g 1101 db2fadm1
sudo useradd -u 1101 -g db2fadm1 -m -d /home/db2fenc1 -s /bin/bash db2fenc1

# DAS admin (optional, for DB2 Administration Server)
sudo groupadd -g 1102 dasadm1
sudo useradd -u 1102 -g dasadm1 -m -d /home/dasusr1 -s /bin/bash dasusr1

# Set passwords through masked interactive prompts. Do not place passwords in
# shell arguments, scripts, history, or process-substitution commands.
sudo passwd db2inst1
sudo passwd db2fenc1
```

### Installation Methods

**Method 1 — db2_install (command line, universal):**

```bash
# Mount or extract DB2 server package
tar xzf v11.5.9_linuxx64_server_dec.tar.gz
cd server_dec

# Check prerequisites
sudo ./db2prereqcheck

# Install DB2 Enterprise Server Edition
sudo ./db2_install -b /opt/ibm/db2/V11.5 -p SERVER -f NOTSAMP
```

**Method 2 — db2setup (interactive or response file):**

```bash
# Interactive GUI (requires X11)
sudo ./db2setup

# Response file install (unattended)
sudo ./db2setup -r /tmp/db2server.rsp
```

**Sample response file** `/tmp/db2server.rsp`:

```
PROD                 = DB2_SERVER_EDITION
LIC_AGREEMENT        = ACCEPT
FILE                 = /opt/ibm/db2/V11.5
INSTALL_TYPE         = TYPICAL
INSTANCE             = DB2_INST
DB2_INST.NAME        = db2inst1
DB2_INST.GROUP_NAME  = db2iadm1
DB2_INST.HOME_DIRECTORY = /home/db2inst1
DB2_INST.FENCED_USER = db2fenc1
DB2_INST.FENCED_GROUP = db2fadm1
DB2_INST.TYPE        = ESE
DB2_INST.AUTOSTART   = YES
DB2_INST.START_DURING_INSTALL = YES
DB2_INST.SVCENAME    = db2c_db2inst1
DB2_INST.PORT_NUMBER = 50000
```

### Post-Install Verification

```bash
# Check installation
/opt/ibm/db2/V11.5/bin/db2ls

# Validate license
su - db2inst1 -c "db2licm -l"

# Apply license file
su - db2inst1 -c "db2licm -a /path/to/db2ese_u.lic"
```

---

## 2. Instance Management

### Instance Lifecycle

```bash
# Create a new instance
sudo /opt/ibm/db2/V11.5/instance/db2icrt -u db2fenc1 -p 50000 db2inst1

# Update instance after fix pack
sudo /opt/ibm/db2/V11.5/instance/db2iupdt db2inst1

# Drop instance (removes config, not data)
sudo /opt/ibm/db2/V11.5/instance/db2idrop db2inst1

# List instances
/opt/ibm/db2/V11.5/instance/db2ilist
```

### Start / Stop

```bash
su - db2inst1

# Start instance
db2start

# Stop instance (force disconnects after timeout)
db2stop
db2stop force

# Check instance status
db2pd -

# Attach to instance (for remote admin); omit USING so DB2 prompts securely.
db2 attach to db2inst1 user db2inst1
# Enter the credential only at the masked prompt.
```

### Instance Profile and Environment

The instance profile is sourced at login: `~db2inst1/sqllib/db2profile`

```bash
# Source DB2 environment (in scripts)
. /home/db2inst1/sqllib/db2profile

# Or add to .bash_profile
if [ -f /home/db2inst1/sqllib/db2profile ]; then
    . /home/db2inst1/sqllib/db2profile
fi
```

### Registry Variables (db2set)

```bash
su - db2inst1

# List all set variables
db2set -all

# List all supported variables
db2set -lr

# Common tuning variables
db2set DB2_WORKLOAD=SAP              # or ANALYTICS for warehouse
db2set DB2_PARALLEL_IO=*             # enable parallel I/O on all containers
db2set DB2_SKIPDELETED=ON            # skip deleted rows during index scan
db2set DB2_SKIPINSERTED=ON           # skip uncommitted inserts during scan
db2set DB2_USE_ALTERNATE_PAGE_CLEANING=ON   # page cleaner efficiency
db2set DB2COMM=TCPIP                 # enable TCP/IP listener

# Remove a variable
db2set DB2_SKIPDELETED=

# Show effective value
db2set DB2COMM
```

Most registry variable changes require `db2stop` / `db2start` to take effect.

### Database Manager Configuration (DBM CFG)

```bash
su - db2inst1

# View all DBM CFG parameters
db2 get dbm cfg

# Key parameters
db2 update dbm cfg using SVCENAME db2c_db2inst1 immediate
db2 update dbm cfg using AUTHENTICATION SERVER_ENCRYPT immediate
db2 update dbm cfg using DIAGLEVEL 3 immediate
db2 update dbm cfg using NOTIFYLEVEL 3 immediate
db2 update dbm cfg using INSTANCE_MEMORY AUTOMATIC immediate
db2 update dbm cfg using MON_HEAP_SZ AUTOMATIC immediate
db2 update dbm cfg using HEALTH_MON ON immediate
db2 update dbm cfg using INTRA_PARALLEL YES immediate
db2 update dbm cfg using NUMDB 8 immediate
db2 update dbm cfg using KEEPFENCED NO immediate

# View specific parameter
db2 get dbm cfg | grep -i svcename
```

---

## 3. Database Administration

### Create Database

```bash
su - db2inst1

# Basic creation with UTF-8 and automatic storage
db2 "CREATE DATABASE myappdb
     AUTOMATIC STORAGE YES
     ON /db2data/myappdb
     DBPATH ON /db2data/myappdb
     USING CODESET UTF-8
     TERRITORY US
     COLLATE USING IDENTITY
     PAGESIZE 32768"

# Verify
db2 list db directory
db2 connect to myappdb
db2 "SELECT * FROM SYSIBMADM.DBCFG WHERE NAME IN ('logfilsiz','logprimary','logsecfil')"
db2 connect reset
```

### Database Configuration (DB CFG)

```bash
db2 connect to myappdb

# View all DB CFG
db2 get db cfg for myappdb

# Transaction logging — critical for recovery
db2 update db cfg for myappdb using LOGFILSIZ 16384        # 16K pages = 64MB per log file (32K pagesize)
db2 update db cfg for myappdb using LOGPRIMARY 20           # pre-allocated log files
db2 update db cfg for myappdb using LOGSECFIL 15            # secondary log files (on demand)
db2 update db cfg for myappdb using LOGARCHMETH1 DISK:/db2archlog/myappdb
db2 update db cfg for myappdb using LOGARCHCOMPR1 ON        # compress archive logs
db2 update db cfg for myappdb using SOFTMAX 600             # soft checkpoint interval

# Recovery
db2 update db cfg for myappdb using TRACKMOD ON             # needed for incremental backup
db2 update db cfg for myappdb using AUTO_DEL_REC_OBJ ON     # auto-delete pruned logs/backups

# Performance
db2 update db cfg for myappdb using LOCKLIST AUTOMATIC
db2 update db cfg for myappdb using MAXLOCKS AUTOMATIC
db2 update db cfg for myappdb using CATALOGCACHE_SZ 300
db2 update db cfg for myappdb using PCKCACHESZ AUTOMATIC
db2 update db cfg for myappdb using STMTHEAP AUTOMATIC
db2 update db cfg for myappdb using SORTHEAP AUTOMATIC
db2 update db cfg for myappdb using SHEAPTHRES_SHR AUTOMATIC
db2 update db cfg for myappdb using NUM_IOCLEANERS AUTOMATIC
db2 update db cfg for myappdb using NUM_IOSERVERS AUTOMATIC
db2 update db cfg for myappdb using DFT_QUERYOPT 5          # optimizer effort (1-9, 5 = default)

# Self-tuning memory
db2 update db cfg for myappdb using SELF_TUNING_MEM ON

db2 connect reset
```

### Tablespaces

DB2 supports three types: SMS (System Managed Space), DMS (Database Managed Space), and Automatic Storage (recommended).

```sql
-- Connect
CONNECT TO myappdb;

-- Automatic storage tablespace (recommended — DB2 manages containers)
CREATE TABLESPACE ts_data
  PAGESIZE 32768
  MANAGED BY AUTOMATIC STORAGE
  AUTORESIZE YES
  INCREASESIZE 500 M
  MAXSIZE 50 G;

-- DMS tablespace with explicit containers
CREATE TABLESPACE ts_large_data
  PAGESIZE 32768
  MANAGED BY DATABASE
  USING (FILE '/db2data/myappdb/ts_large_01.dbf' 10G,
         FILE '/db2data/myappdb/ts_large_02.dbf' 10G)
  AUTORESIZE YES
  INCREASESIZE 2 G
  MAXSIZE NONE;

-- Temporary tablespace (system temp for sorts/joins)
CREATE SYSTEM TEMPORARY TABLESPACE ts_temp
  PAGESIZE 32768
  MANAGED BY AUTOMATIC STORAGE
  BUFFERPOOL BP_TEMP;

-- User temporary tablespace (DGTT, CTEs)
CREATE USER TEMPORARY TABLESPACE ts_usertemp
  PAGESIZE 32768
  MANAGED BY AUTOMATIC STORAGE
  BUFFERPOOL BP_TEMP;

-- Monitor tablespace usage
SELECT TBSP_NAME, TBSP_TYPE, TBSP_STATE, TBSP_USED_SIZE_KB, TBSP_FREE_SIZE_KB,
       TBSP_UTILIZATION_PERCENT
FROM SYSIBMADM.TBSP_UTILIZATION;

-- Add container to existing tablespace
ALTER TABLESPACE ts_large_data ADD (FILE '/db2data/myappdb/ts_large_03.dbf' 10G);

-- Rebalance after adding container
ALTER TABLESPACE ts_large_data REBALANCE;

CONNECT RESET;
```

### Buffer Pools

```sql
CONNECT TO myappdb;

-- Create buffer pools (size in pages; 32K pagesize x 131072 pages = 4GB)
CREATE BUFFERPOOL BP_DATA SIZE 131072 PAGESIZE 32768;
CREATE BUFFERPOOL BP_INDEX SIZE 65536 PAGESIZE 32768;
CREATE BUFFERPOOL BP_TEMP SIZE 32768 PAGESIZE 32768;

-- Enable self-tuning for buffer pools
ALTER BUFFERPOOL BP_DATA SIZE AUTOMATIC;
ALTER BUFFERPOOL BP_INDEX SIZE AUTOMATIC;

-- Assign tablespace to buffer pool
ALTER TABLESPACE ts_data BUFFERPOOL BP_DATA;

-- Monitor buffer pool hit ratio (target > 95%)
SELECT BP_NAME, POOL_DATA_L_READS, POOL_DATA_P_READS,
       CASE WHEN POOL_DATA_L_READS > 0
            THEN DECIMAL((1.0 - (FLOAT(POOL_DATA_P_READS) / POOL_DATA_L_READS)) * 100, 5, 2)
            ELSE 100.00 END AS HIT_RATIO_PCT
FROM TABLE(MON_GET_BUFFERPOOL(NULL, -2)) AS BP;

CONNECT RESET;
```

### Schema Management

```sql
CONNECT TO myappdb;

-- Create schema
CREATE SCHEMA app AUTHORIZATION db2inst1;

-- Set default schema for session
SET CURRENT SCHEMA = 'APP';

-- Create table in schema
CREATE TABLE app.customers (
    id          INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY,
    name        VARCHAR(200) NOT NULL,
    email       VARCHAR(254),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) IN ts_data INDEX IN ts_data COMPRESS YES;

-- Create index
CREATE INDEX app.idx_cust_email ON app.customers(email);

-- List schemas
SELECT SCHEMANAME, OWNER FROM SYSCAT.SCHEMATA WHERE SCHEMANAME NOT LIKE 'SYS%';

CONNECT RESET;
```

---
