---
name: flink
description: >-
  Apache Flink stream processing expertise for stateful computations over
  bounded and unbounded streams. Use when the user mentions Flink, Flink SQL,
  Table API, DataStream API, CDC, Kafka-to-Flink pipelines, checkpoints,
  savepoints, watermarks, windows, Flink Kubernetes Operator, or Flink
  integrations with Iceberg, Paimon, or Fluss.
metadata:
  category: data
  source:
    repository: 'https://github.com/gordonmurray/data-engineering-skills'
    path: flink
    license_path: LICENSE
    commit: 226973561ae6881d21b6567171195e8211863d75
---

# Apache Flink Data Streaming Expert

Use this skill for production Flink architecture, operations, SQL/DataStream implementation, upgrade planning, and lakehouse streaming integrations.

## Current Facts

- **Current Flink line:** 2.2.x. Downloads include Apache Flink 2.2.1, while the site still labels 2.2.0 as the latest stable line.
- **Maintained 2.x patch lines:** 2.2.1, 2.1.2, 2.0.2.
- **1.x maintenance line:** 1.20.4. Use this as the 1.x migration baseline unless the project is pinned elsewhere.
- **Kubernetes Operator:** 1.15.0, compatible with Flink 2.2.x, 2.1.x, 2.0.x, 1.20.x, and 1.19.x.
- **Flink CDC:** 3.6.0, with artifacts for Flink 1.20.x and 2.2.x.
- **Java:** Flink 2.x requires Java 11+; Java 17 is the practical default for new deployments.

## Critical 2.x Notes

- DataSet API removed; use DataStream, Table API, or SQL.
- Scala DataStream/DataSet APIs removed from the core distribution.
- SourceFunction/SinkFunction and Sink V1 patterns are obsolete; prefer Source/Sink V2 connectors.
- `flink-conf.yaml` was replaced by standard YAML `config.yaml` in Flink 2.x.
- Per-job deployment mode was removed; use Application mode or Kubernetes Operator patterns.
- Validate savepoint compatibility carefully before 1.x to 2.x migrations.

## How To Use

1. Classify the request: SQL/Table API, DataStream, deployment, operations, upgrade, CDC, or lakehouse sink/source.
2. For new greenfield work, prefer Flink 2.2.x plus current connector artifacts.
3. For migration work, identify the exact source version, connector versions, state backend, and savepoint strategy before recommending commands.

## Production Defaults

- Enable checkpointing for streaming jobs and set explicit checkpoint storage.
- Use savepoints for planned upgrades and topology changes.
- Use watermarks and allowed lateness deliberately; make event-time assumptions visible.
- Monitor checkpoint duration, alignment time, backpressure, restart count, and state size.
- Prefer the Kubernetes Operator for long-running production jobs on Kubernetes.
- Use Iceberg/Paimon/Fluss connectors only at versions compatible with the selected Flink line.

## Update Checklist

- Recheck Flink downloads for core, CDC, connector, and Kubernetes Operator versions.
- Update Helm/doc URLs when operator versions change.
