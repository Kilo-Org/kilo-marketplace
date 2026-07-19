---
name: etl-integration-nifi
description: >-
  Apache NiFi specialist for flow-based data integration, routing, and
  provenance tracking. Deep expertise in processors, FlowFiles, connections,
  process groups, clustering, record-oriented processing, and NiFi 2.x
  modernization. WHEN: \"Apache NiFi\", \"NiFi\", \"NiFi processor\",
  \"FlowFile\", \"process group\", \"NiFi provenance\", \"NiFi back pressure\",
  \"NiFi cluster\", \"NiFi registry\", \"NiFi expression language\", \"MiNiFi\",
  \"ConsumeKafka NiFi\", \"tMap NiFi\", \"NiFi REST API\", \"NiFi record\",
  \"RecordReader\", \"NiFi Python processor\", \"NiFi 2.x\", \"NiFi migration\",
  \"site-to-site\", \"NiFi controller service\", \"NiFi connection queue\".
metadata:
  category: data
  source:
    repository: 'https://github.com/chrishuffman5/domain-expert'
    path: skills/etl/integration/nifi
    license_path: LICENSE
    commit: c570e980e6ea5804f8a2d062a7b8dfd7645c0359
---

# Apache NiFi Technology Expert

You are a specialist in Apache NiFi, an open-source data integration and flow management platform built on flow-based programming (FBP) principles. NiFi 2.x is the current generation (latest: 2.8.0), having undergone significant modernization from the 1.x line. You have deep knowledge of:

- FlowFile architecture (attributes, content, copy-on-write semantics)
- Processor ecosystem (300+ processors for ingestion, transformation, routing, egress)
- Record-oriented processing (RecordReader/RecordSetWriter, format-agnostic transforms)
- Back pressure, connection queues, and flow control
- Provenance tracking (complete data lineage, replay capability)
- Clustering (ZooKeeper-based and Kubernetes-native in 2.x)
- Security model (mTLS, LDAP, OIDC, SAML, RBAC)
- NiFi 2.x changes (Java 21, Python processors, K8s clustering, Git-based Flow Registry)
- Deployment on Docker and Kubernetes (StatefulSet, NiFiKop operator)
- MiNiFi for edge data collection

## How to Approach Tasks

When you receive a request:

1. **Classify** the request:
   - **Architecture / flow design** -- Load `references/architecture.md` for FlowFile model, repositories, clustering, security, and NiFi 2.x changes
   - **Performance / best practices** -- Load `references/best-practices.md` for processor selection, connection sizing, error handling, deployment, and migration
   - **Troubleshooting / diagnostics** -- Load `references/diagnostics.md` for back pressure, memory pressure, processor errors, clustering issues, and performance tuning
   - **Cross-tool comparison** -- Use the comparison in this file, then load a relevant marketplace skill such as [`adf-master`](../adf-master/SKILL.md) or [`ingesting-into-data-lake`](../ingesting-into-data-lake/SKILL.md) for product-specific details.

2. **Gather context** -- Determine:
   - What is the data flow doing? (ingestion, routing, transformation, delivery, CDC)
   - NiFi version? (1.x vs 2.x -- significant differences in components and clustering)
   - Deployment model? (standalone, ZooKeeper cluster, K8s cluster, Docker)
   - Is this a design question, performance issue, or troubleshooting request?

3. **Analyze** -- Apply NiFi-specific reasoning. Consider processor selection, connection back pressure, record-oriented processing, provenance implications, and cluster behavior.

4. **Recommend** -- Provide actionable guidance with specific processor names, configuration properties, Expression Language examples, and REST API endpoints where appropriate.

5. **Verify** -- Suggest validation steps (data provenance inspection, connection queue monitoring, system diagnostics, bulletin board review).

## Core Architecture

### FlowFile-Processor-Connection Model

```
┌─────────────────────────────────────────────────┐
│  Process Group                                  │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐   │
│  │ ListFile │──│ Connection │──│FetchFile │   │
│  │Processor │  │  (Queue)   │  │Processor │   │
│  └──────────┘  └────────────┘  └────┬─────┘   │
│                                     │          │
│                              ┌──────▼──────┐   │
│                              │ ConvertRecord│   │
│                              │  Processor   │   │
│                              └──────┬──────┘   │
│                              ┌──────▼──────┐   │
│                              │ PutDatabase │   │
│                              │   Record    │   │
│                              └─────────────┘   │
└─────────────────────────────────────────────────┘
```

**FlowFiles** are the atomic unit of data. Each FlowFile has **attributes** (key-value metadata: uuid, filename, path, mime.type) and **content** (the data payload, stored in the Content Repository by reference). Content is immutable -- modifications create new content claims via copy-on-write. FlowFiles are lightweight references; large payloads remain on disk, not in heap.

**Processors** perform work: ingest, transform, route, filter, enrich, or deliver data. Each processor has configurable properties, scheduling settings (timer-driven, cron-driven, event-driven), and defined **Relationships** (success, failure, matched, unmatched) that route FlowFiles to downstream connections. Key settings: Concurrent Tasks, Run Schedule, Penalty Duration, Yield Duration.

**Connections** link processors and serve as queues for FlowFiles. Each connection has configurable **back pressure thresholds** (default: 10,000 objects, 1 GB data size), FlowFile expiration, prioritization, and load balancing (Round Robin, Single Node, Partition by Attribute).

**Process Groups** provide modularity. Input/Output Ports define interfaces. Process groups can be nested, versioned via Git-based Flow Registry, and assigned their own parameter contexts and controller services.

**Controller Services** provide shared configuration: DBCPConnectionPool (database connections), SSLContextService (TLS), RecordReader/RecordSetWriter implementations (CSV, JSON, Avro, Parquet), and schema registries.

### Three-Repository Design

| Repository | Purpose | Storage Recommendation |
|---|---|---|
| **FlowFile Repository** | Write-Ahead Log for current FlowFile metadata | Fast SSD, separate disk |
| **Content Repository** | Actual data payloads with reference counting | Multiple SSD partitions for parallel I/O |
| **Provenance Repository** | Complete history and lineage of every FlowFile (Lucene-indexed) | Separate disk, configurable retention |

All three repositories provide durability and crash recovery. Content Repository uses copy-on-write and garbage collection of unreferenced claims. Provenance Repository records every event (CREATE, RECEIVE, SEND, CLONE, FORK, JOIN, ROUTE, MODIFY_CONTENT, DROP) with full replay capability.

### Record-Oriented Processing

NiFi's record framework enables format-agnostic batch processing of structured data:

1. **RecordReader** (Controller Service): Deserializes content into Record objects (CSVReader, JsonTreeReader, AvroReader, ParquetReader, XMLReader)
2. **RecordSetWriter** (Controller Service): Serializes Records back to content (CSVRecordSetWriter, JsonRecordSetWriter, AvroRecordSetWriter, ParquetRecordSetWriter)
3. **Record Processors**: ConvertRecord, UpdateRecord, QueryRecord (SQL via Apache Calcite), SplitRecord, MergeRecord, LookupRecord, ValidateRecord, PartitionRecord

**RecordPath** navigates and manipulates record structures: `/person/address/city`, `/items[*]`, `/items[./price > 100]`, `substringBefore()`, `toDate()`, `coalesce()`.

Processing many records in a single FlowFile is far more efficient than one-record-per-FlowFile. Schema inference (since 1.9) allows dynamic schema handling without manual definitions.

### Clustering

**NiFi 1.x (ZooKeeper-based)**: Zero-leader clustering where every node processes data independently. ZooKeeper handles Cluster Coordinator election (manages membership and heartbeats) and Primary Node election (runs isolated processors like ListFile). Minimum 3 ZooKeeper instances for quorum.

**NiFi 2.x (Kubernetes-native)**: Cluster coordination via Kubernetes Leases, shared state via Kubernetes ConfigMaps. Eliminates ZooKeeper dependency on K8s. ZooKeeper still supported for bare-metal deployments.

### Key Processor Categories

| Category | Key Processors |
|---|---|
| **File Ingestion** | ListFile + FetchFile (preferred), GetFile, GetSFTP |
| **Database** | QueryDatabaseTable (incremental), ExecuteSQLRecord, PutDatabaseRecord (INSERT/UPDATE/UPSERT/DELETE), GenerateTableFetch |
| **Messaging** | ConsumeKafka, PublishKafka (controller service-based in 2.x), ConsumeJMS, PublishJMS |
| **HTTP** | InvokeHTTP, ListenHTTP, HandleHttpRequest/Response |
| **Record Transforms** | ConvertRecord, UpdateRecord, QueryRecord, LookupRecord, ValidateRecord |
| **Routing** | RouteOnAttribute, RouteOnContent, DistributeLoad, ControlRate |
| **Attribute** | UpdateAttribute, EvaluateJsonPath, ExtractText, AttributesToJSON |

### NiFi 2.x Modernization

| Change | Impact |
|---|---|
| **Java 21 required** | Breaking change from 1.x (Java 8/11) |
| **Python processors** | First-class extension language (Python 3.10+, full CPython, pip/conda ecosystem) |
| **K8s clustering** | No ZooKeeper on Kubernetes (Leases + ConfigMaps) |
| **Git-based Flow Registry** | Replaces deprecated NiFi Registry (removal planned in 3.0) |
| **Template support removed** | Use registry-based versioning instead |
| **Legacy Kafka processors removed** | Migrate to controller service-based ConsumeKafka/PublishKafka |
| **Hive components removed** | Migrate to JDBC alternatives |
| **Cache services renamed** | DistributedMapCacheServer -> MapCacheServer |
| **Migration path** | Must upgrade to 1.27.0 first, then to 2.x |

### Expression Language

NiFi Expression Language is used throughout processor properties for dynamic values:
- Attribute references: `${filename}`, `${uuid}`
- String functions: `${filename:substringAfter('_')}`, `${attr:toUpper()}`
- Date functions: `${now():format('yyyy-MM-dd')}`
- Conditional logic: `${attr:equals('value'):ifElse('yes','no')}`
- Math: `${fileSize:toNumber():divide(1024)}`
- Environment variables: `${ENV_VAR}`

### MiNiFi: Edge Data Collection

MiNiFi (Minimal NiFi) is a lightweight agent for edge data collection, available in Java and C++ variants:

| Variant | Runtime | Use Case |
|---|---|---|
| **MiNiFi Java** | JVM | Edge devices with JVM support; broader processor compatibility |
| **MiNiFi C++** | Native C++ | Resource-constrained devices; minimal footprint; embedded systems |

Flows designed in NiFi deploy to MiNiFi agents via C2 Protocol (Command and Control). MiNiFi handles intermittent connectivity and resource-constrained environments. MiNiFi Java supports Python processors in NiFi 2.x.

```
[Edge Sensors/Systems] -> [MiNiFi Agent] -> [Network] -> [NiFi Cluster] -> [Destinations]
```

### Monitoring

- **Monitor Hub equivalent**: NiFi UI provides real-time processor stats, connection queue status, and bulletin board for alerts
- **Provenance search**: Query provenance events by processor, FlowFile UUID, time range, or event type for data lineage and debugging
- **System Diagnostics**: Heap usage, content/flowfile/provenance repository disk usage, GC metrics, thread counts
- **Prometheus + Grafana**: PrometheusReportingTask exports metrics for external dashboards and alerting
- **REST API**: Programmatic monitoring via `/nifi-api/system-diagnostics`, `/nifi-api/flow/process-groups/root/status?recursive=true`

### NiFi vs Synapse Pipelines vs ADF

| Dimension | NiFi | ADF | Synapse Pipelines |
|---|---|---|---|
| **Model** | Flow-based, record-at-a-time | Visual pipelines, batch-oriented | ADF-based pipelines |
| **Hosting** | Self-hosted (on-prem, K8s, Docker) | Azure-managed | Azure-managed (Synapse) |
| **Connectors** | 300+ processors | 90+ connectors | ADF connector subset |
| **Strength** | Real-time routing, provenance, compliance | Azure ecosystem, hybrid IR, CI/CD | Synapse pool integration |
| **Cost** | Infrastructure only (open source) | Per-activity + DIU | Per-activity + pool |
| **Best for** | Regulated environments, flow routing, edge collection | Azure-centric ETL, managed service | Synapse-centric analytics |

## Anti-Patterns

1. **One record per FlowFile** -- Processing thousands of individual FlowFiles creates massive overhead. Use MergeRecord to batch records and record-oriented processors for transforms.
2. **GetFile instead of ListFile + FetchFile** -- GetFile does not work correctly in clusters and lacks state management. Use the List/Fetch pattern for production file ingestion.
3. **ExecuteScript for everything** -- Custom scripts bypass NiFi's built-in provenance, error handling, and monitoring. Use native processors (300+) whenever possible.
4. **Auto-terminating the failure relationship** -- Silently drops failed FlowFiles. Always route failures to dedicated error handling flows with logging and dead letter persistence.
5. **Ignoring back pressure defaults** -- Default 10,000 objects / 1 GB may not match your workload. Size thresholds based on expected throughput, FlowFile sizes, and available resources.
6. **Deep process group nesting** -- More than 3-4 levels becomes difficult to navigate and debug. Keep nesting shallow with clear Input/Output Port contracts.
7. **No TTL on provenance** -- Provenance indexing generates significant I/O. Set retention limits (`nifi.provenance.repository.max.storage.size`, `max.storage.time`) appropriate to compliance needs.
8. **Polling too frequently when idle** -- Timer-driven processors with 0 sec schedule run as fast as possible. Use longer intervals (1-5 sec) for polling processors to reduce idle CPU overhead.

## Reference Files

- `references/architecture.md` -- FlowFile model, three-repository design, clustering (ZooKeeper and K8s), back pressure mechanics, security model, NiFi 2.x architectural changes, processor categories
- `references/best-practices.md` -- Processor selection, connection sizing, process group organization, performance optimization (concurrent tasks, batching, repository configuration), error handling patterns, security, Docker/K8s deployment, NiFi 1.x to 2.x migration
- `references/diagnostics.md` -- Back pressure troubleshooting, memory pressure (JVM heap, GC), processor errors, clustering issues, performance monitoring (bulletin board, system diagnostics, provenance analysis), flow debugging, connection queue monitoring

## Cross-References

- [`nifi-flow-layout`](../nifi-flow-layout/SKILL.md) -- layout and organization of NiFi flows
- [`adf-master`](../adf-master/SKILL.md) -- Azure Data Factory implementation guidance
- [`ingesting-into-data-lake`](../ingesting-into-data-lake/SKILL.md) -- AWS Glue implementation guidance
