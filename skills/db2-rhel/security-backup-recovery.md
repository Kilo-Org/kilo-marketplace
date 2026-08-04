# Security, Backup, and Recovery

Reference file for the `db2-rhel` skill. Covers DB2 security (authentication, authorization, roles, audit), backup strategies, and HADR recovery.

## 4. Security

### Authentication Modes

Set in DBM CFG; determines how credentials are validated.

```bash
# SERVER — OS authenticates on the server
db2 update dbm cfg using AUTHENTICATION SERVER

# SERVER_ENCRYPT — same as SERVER but password encrypted over the wire
db2 update dbm cfg using AUTHENTICATION SERVER_ENCRYPT

# GSSPLUGIN — GSS-API plugin (Kerberos, custom)
db2 update dbm cfg using AUTHENTICATION GSSPLUGIN
db2 update dbm cfg using SRVCON_GSSPLUGIN_LIST IBMkrb5

# KERBEROS — native Kerberos
db2 update dbm cfg using AUTHENTICATION KERBEROS
```

### GRANT / REVOKE

```sql
CONNECT TO myappdb;

-- Database-level privileges
GRANT CONNECT ON DATABASE TO USER appuser;
GRANT DBADM ON DATABASE TO USER dba_user;
GRANT CREATETAB, BINDADD, CONNECT ON DATABASE TO USER devuser;

-- Schema privileges
GRANT CREATEIN, ALTERIN, DROPIN ON SCHEMA app TO USER appuser;

-- Table privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE app.customers TO USER appuser;
GRANT SELECT ON TABLE app.customers TO USER readonly;

-- Revoke
REVOKE DELETE ON TABLE app.customers FROM USER readonly;

-- Role-based access
CREATE ROLE app_reader;
GRANT SELECT ON TABLE app.customers TO ROLE app_reader;
GRANT ROLE app_reader TO USER reporting_user;

-- View effective privileges
SELECT * FROM SYSCAT.TABAUTH WHERE GRANTEE = 'APPUSER';
SELECT * FROM SYSCAT.DBAUTH WHERE GRANTEE = 'APPUSER';

CONNECT RESET;
```

### Label-Based Access Control (LBAC)

```sql
CONNECT TO myappdb;

-- Create security label component
CREATE SECURITY LABEL COMPONENT classification
  ARRAY ['TOP_SECRET', 'SECRET', 'CONFIDENTIAL', 'UNCLASSIFIED'];

-- Create security policy
CREATE SECURITY POLICY data_policy
  COMPONENTS classification
  WITH DB2LBACRULES
  RESTRICT NOT AUTHORIZED WRITE SECURITY LABEL;

-- Apply to table
ALTER TABLE app.customers ADD SECURITY POLICY data_policy;
ALTER TABLE app.customers ADD COLUMN sec_label DB2SECURITYLABEL;

-- Create labels
CREATE SECURITY LABEL data_policy.confidential
  COMPONENT classification 'CONFIDENTIAL';

CREATE SECURITY LABEL data_policy.secret
  COMPONENT classification 'SECRET';

-- Grant label to user
GRANT SECURITY LABEL data_policy.confidential TO USER appuser FOR READ ACCESS;
GRANT SECURITY LABEL data_policy.secret TO USER dba_user FOR ALL ACCESS;

CONNECT RESET;
```

### Audit Policies

```sql
CONNECT TO myappdb;

-- Create audit policy
CREATE AUDIT POLICY sensitive_audit
  CATEGORIES EXECUTE STATUS BOTH,
             OBJMAINT STATUS BOTH,
             SYSADMIN STATUS BOTH
  ERROR TYPE AUDIT;

-- Apply to specific table
AUDIT TABLE app.customers USING POLICY sensitive_audit;

-- Apply to database
AUDIT DATABASE USING POLICY sensitive_audit;

-- Extract and view audit log
-- (run as instance owner from OS)
-- db2audit flush
-- db2audit extract file audit_out.del

CONNECT RESET;
```

```bash
# Flush and extract audit records
su - db2inst1
db2audit flush
db2audit extract delasc to /home/db2inst1/audit_output
```

### Data at Rest Encryption (Native Encryption)

```bash
su - db2inst1

# Create keystore
gsk8capicmd_64 -keydb -create -db /home/db2inst1/keystore/db2keystore.p12 \
  -pw "Keystore_P@ss!2024" -type pkcs12 -stash

# Configure instance for encryption
db2 update dbm cfg using KEYSTORE_TYPE PKCS12
db2 update dbm cfg using KEYSTORE_LOCATION /home/db2inst1/keystore/db2keystore.p12
db2 update dbm cfg using KEYSTORE_PASSWORD /home/db2inst1/keystore/db2keystore.sth

# Create encrypted database
db2 "CREATE DATABASE securedb ENCRYPT"

# Or encrypt existing database during restore
db2 "RESTORE DATABASE myappdb FROM /db2backup ENCRYPT"
```

### SSL/TLS Connections

```bash
su - db2inst1

# Create keystore for SSL
gsk8capicmd_64 -keydb -create -db /home/db2inst1/ssl/db2server.kdb \
  -pw "SSL_P@ss!2024" -type cms -stash

# Create self-signed certificate (or import CA-signed cert)
gsk8capicmd_64 -cert -create -db /home/db2inst1/ssl/db2server.kdb \
  -stashed -label "db2server" -dn "CN=db2server.example.com,O=MyOrg" \
  -size 2048 -sigalg SHA256WithRSA -expire 1095

# Extract public cert for clients
gsk8capicmd_64 -cert -extract -db /home/db2inst1/ssl/db2server.kdb \
  -stashed -label "db2server" -target /home/db2inst1/ssl/db2server.arm -format ascii

# Configure DB2 for SSL
db2 update dbm cfg using SSL_SVR_KEYDB /home/db2inst1/ssl/db2server.kdb
db2 update dbm cfg using SSL_SVR_STASH /home/db2inst1/ssl/db2server.sth
db2 update dbm cfg using SSL_SVR_LABEL db2server
db2 update dbm cfg using SSL_SVCENAME db2s_db2inst1
db2set DB2COMM=TCPIP,SSL

# Add SSL service port to /etc/services
echo "db2s_db2inst1   50001/tcp" | sudo tee -a /etc/services

db2stop force
db2start
```

---

## 5. Backup & Recovery

### Offline Backup

```bash
su - db2inst1

# Full offline backup (compressed)
db2 "BACKUP DATABASE myappdb TO /db2backup COMPRESS"

# Full offline backup with multiple sessions (parallelism)
db2 "BACKUP DATABASE myappdb TO /db2backup WITH 4 BUFFERS BUFFER 4096 PARALLELISM 4 COMPRESS"
```

### Online Backup

Requires archive logging (`LOGARCHMETH1` set to a path or `TSM`).

```bash
# Full online backup
db2 "BACKUP DATABASE myappdb ONLINE TO /db2backup COMPRESS INCLUDE LOGS"

# Incremental online backup (requires TRACKMOD ON)
db2 "BACKUP DATABASE myappdb ONLINE INCREMENTAL TO /db2backup COMPRESS INCLUDE LOGS"

# Delta online backup (changes since last backup of any type)
db2 "BACKUP DATABASE myappdb ONLINE INCREMENTAL DELTA TO /db2backup COMPRESS INCLUDE LOGS"
```

### Restore

```bash
# List backup images
db2 "LIST HISTORY BACKUP ALL FOR myappdb"

# Restore from latest backup (offline)
db2stop force
db2 "RESTORE DATABASE myappdb FROM /db2backup TAKEN AT 20260331120000 REPLACE EXISTING"
db2 "ROLLFORWARD DATABASE myappdb TO END OF LOGS AND STOP"
db2start

# Restore to a point in time
db2 "RESTORE DATABASE myappdb FROM /db2backup TAKEN AT 20260331120000 REPLACE EXISTING"
db2 "ROLLFORWARD DATABASE myappdb TO 2026-03-31-14.30.00.000000 USING LOCAL TIME AND STOP"

# Incremental restore (automatic — DB2 figures out chain)
db2 "RESTORE DATABASE myappdb INCREMENTAL AUTOMATIC FROM /db2backup TAKEN AT 20260331180000"
db2 "ROLLFORWARD DATABASE myappdb TO END OF LOGS AND STOP"

# Redirect restore (move to different paths)
db2 "RESTORE DATABASE myappdb FROM /db2backup INTO newdb REDIRECT"
db2 "SET TABLESPACE CONTAINERS FOR 0 USING (PATH '/db2data/newdb/ts_syscatspace')"
db2 "SET TABLESPACE CONTAINERS FOR 1 USING (PATH '/db2data/newdb/ts_temp')"
db2 "SET TABLESPACE CONTAINERS FOR 2 USING (PATH '/db2data/newdb/ts_data')"
db2 "RESTORE DATABASE newdb CONTINUE"
db2 "ROLLFORWARD DATABASE newdb TO END OF LOGS AND STOP"
```

### HADR (High Availability Disaster Recovery)

**Primary setup:**

```bash
su - db2inst1

# Configure primary database
db2 update db cfg for myappdb using HADR_LOCAL_HOST primary.example.com
db2 update db cfg for myappdb using HADR_LOCAL_SVC 50002
db2 update db cfg for myappdb using HADR_REMOTE_HOST standby.example.com
db2 update db cfg for myappdb using HADR_REMOTE_SVC 50002
db2 update db cfg for myappdb using HADR_REMOTE_INST db2inst1
db2 update db cfg for myappdb using HADR_SYNCMODE NEARSYNC
db2 update db cfg for myappdb using HADR_PEER_WINDOW 120
db2 update db cfg for myappdb using LOGINDEXBUILD ON

# Ensure archive logging is on
db2 update db cfg for myappdb using LOGARCHMETH1 DISK:/db2archlog/myappdb

# Take a backup and ship to standby
db2 "BACKUP DATABASE myappdb ONLINE TO /db2backup COMPRESS INCLUDE LOGS"
scp /db2backup/MYAPPDB.0.db2inst1.* standby.example.com:/db2backup/
```

**Standby setup:**

```bash
su - db2inst1

# Restore on standby
db2 "RESTORE DATABASE myappdb FROM /db2backup REPLACE EXISTING"

# Configure standby (mirror of primary, swapping local/remote)
db2 update db cfg for myappdb using HADR_LOCAL_HOST standby.example.com
db2 update db cfg for myappdb using HADR_LOCAL_SVC 50002
db2 update db cfg for myappdb using HADR_REMOTE_HOST primary.example.com
db2 update db cfg for myappdb using HADR_REMOTE_SVC 50002
db2 update db cfg for myappdb using HADR_REMOTE_INST db2inst1
db2 update db cfg for myappdb using HADR_SYNCMODE NEARSYNC
db2 update db cfg for myappdb using HADR_PEER_WINDOW 120
db2 update db cfg for myappdb using LOGINDEXBUILD ON

# Start HADR on standby FIRST
db2 "START HADR ON DATABASE myappdb AS STANDBY"
```

**Then on primary:**

```bash
db2 "START HADR ON DATABASE myappdb AS PRIMARY"
```

**HADR sync modes:**

| Mode | Data Loss Risk | Performance Impact | Use Case |
|---|---|---|---|
| SYNC | Zero | Highest latency | Same data center, zero RPO required |
| NEARSYNC | Near-zero | Moderate | Same site or low-latency link (recommended) |
| ASYNC | Possible | Lowest | Cross-region DR |
| SUPERASYNC | Higher | Minimal | Long-distance, high-latency links |

**Monitor HADR:**

```bash
db2pd -db myappdb -hadr

# Or SQL
db2 "SELECT HADR_ROLE, HADR_STATE, HADR_SYNCMODE, HADR_CONNECT_STATUS,
            PRIMARY_LOG_FILE, STANDBY_LOG_FILE, HADR_LOG_GAP
     FROM TABLE(MON_GET_HADR(NULL)) AS H"
```

**Takeover (planned):**

```bash
# On standby — graceful takeover
db2 "TAKEOVER HADR ON DATABASE myappdb"

# Forced takeover (if primary is down)
db2 "TAKEOVER HADR ON DATABASE myappdb BY FORCE PEER WINDOW ONLY"
```

### Automatic Client Reroute (ACR)

```bash
# On primary — configure alternate server
db2 update alternate server for database myappdb \
  using hostname standby.example.com port 50000

# Client-side catalog with ACR
db2 "CATALOG TCPIP NODE nd_primary REMOTE primary.example.com SERVER 50000"
db2 "CATALOG DATABASE myappdb AT NODE nd_primary"
db2 "UPDATE ALTERNATE SERVER FOR DATABASE myappdb \
     USING HOSTNAME standby.example.com PORT 50000"
```

### TSA (Tivoli System Automation) for Failover

```bash
# Install TSA (ships with DB2)
sudo /opt/ibm/db2/V11.5/bin/db2haicu

# This interactive wizard configures:
# - Cluster domain between primary and standby
# - Quorum device
# - Automated HADR takeover on failure
# - Virtual IP (VIP) that follows the primary role
```

### Automated Backup (systemd timer)

`/etc/systemd/system/db2-backup.service`:
```ini
[Unit]
Description=DB2 myappdb online backup
After=network.target

[Service]
Type=oneshot
User=db2inst1
ExecStart=/usr/local/bin/db2-backup.sh
```

`/etc/systemd/system/db2-backup.timer`:
```ini
[Unit]
Description=DB2 backup daily 02:00

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

`/usr/local/bin/db2-backup.sh`:
```bash
#!/bin/bash
set -euo pipefail
. /home/db2inst1/sqllib/db2profile
BACKUP_DIR="/db2backup"
RETENTION=14
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

db2 connect to myappdb
db2 "BACKUP DATABASE myappdb ONLINE TO $BACKUP_DIR COMPRESS INCLUDE LOGS"
db2 connect reset

# Prune old backup images
db2 "PRUNE HISTORY $TS AND DELETE"
find "$BACKUP_DIR" -name "*.001" -mtime +$RETENTION -delete
```

Enable:
```bash
sudo chmod +x /usr/local/bin/db2-backup.sh
sudo systemctl daemon-reload
sudo systemctl enable --now db2-backup.timer
systemctl list-timers | grep db2-backup
```
---
