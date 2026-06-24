---
name: "db2-rhel"
description: "Use when installing, configuring, or managing IBM DB2 LUW on RHEL 9 (and AlmaLinux/Rocky 9) — instance creation, database administration, buffer pool and tablespace management, backup/restore with HADR, performance tuning (db2advis, db2pd, MON functions), runstats/reorg, SELinux contexts, firewalld rules, and DB2 pureScale. Part of the db2-* skill family."
metadata:
  category: data
  source:
    repository: "https://github.com/joogy06/agent-foundry"
    path: "skills/db2-rhel"
    license_path: "LICENSE"
---

# IBM DB2 LUW — Administration on RHEL 9

Companion skill to `rhel-server-admin` and `rhel-databases`. For Python DB2 connectivity see `python-enterprise-connectors`.

<HARD-RULE>
Always RUNSTATS after bulk loads and before production queries — stale stats produce bad access plans. The optimizer relies on distribution statistics to choose join methods, index paths, and sort strategies. Stale or missing stats silently degrade performance by orders of magnitude.
</HARD-RULE>

<HARD-RULE>
Never modify DB2 registry variables on a running production instance without scheduling a maintenance window — most require db2stop/db2start to take effect, and some (DB2_WORKLOAD, DB2_PARALLEL_IO) change optimizer behavior globally. Always db2set -lr to list variables, test in non-prod first.
</HARD-RULE>

<HARD-RULE>
Always test HADR takeover procedures regularly — untested failover is not HA. Run TAKEOVER HADR on the standby at least quarterly in a maintenance window. Verify automatic client reroute (ACR) reconnects applications. Document RTO/RPO and validate them.
</HARD-RULE>

<HARD-RULE>
Never disable SELinux for DB2 — use correct contexts and fcontext rules. DB2 directories (/opt/ibm/db2, instance home, database paths) need proper SELinux labels. See the RHEL-Specific section for exact fcontext commands.
</HARD-RULE>

---

## Reference Files

Detailed code examples, patterns, and configuration are in the reference files below. Read the relevant file when working on that area.

| File | Covers |
|---|---|
| [install-admin.md](install-admin.md) | DB2 installation on RHEL, instance management, and database administration (tablespaces, buffer pools, schemas, tables) |
| [performance-monitoring-rhel.md](performance-monitoring-rhel.md) | performance tuning (db2advis, db2pd, MON functions), monitoring, maintenance, RHEL-specific configuration, and DB2 pureScale |
| [security-backup-recovery.md](security-backup-recovery.md) | DB2 security (authentication, authorization, roles, audit), backup strategies, and HADR recovery |

---

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| Running DB2 with default buffer pool sizes | Default 1000 pages is far too small for production; excessive disk I/O, poor query performance | Size buffer pools based on workload: OLTP needs 60-80% of data in memory; run db2pd -bufferpools to monitor hit ratio |
| Skipping RUNSTATS after bulk data loads | Optimizer uses stale cardinality estimates; queries that were fast become full table scans | Run RUNSTATS WITH DISTRIBUTION on tables and indexes after every significant data change |
| Using HADR without automatic client reroute | Failover happens but applications cannot find the new primary; manual intervention required | Configure ALTERNATE SERVER in database directory and enable ACR in application connection strings |
| Not setting LOGFILSIZ and LOGPRIMARY appropriately | Default log sizes cause log-full conditions during batch loads; transactions roll back and retry endlessly | Size transaction logs based on largest expected transaction; monitor with db2pd -logs; set LOGSECOND as overflow |
| Running backup without testing restore | Backup jobs succeed but restore fails due to missing log files, wrong paths, or version mismatch | Test restore to a different instance quarterly; validate with RESTORE DB ... WITHOUT ROLLING FORWARD |

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
