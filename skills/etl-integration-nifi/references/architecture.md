# NiFi Architecture Deep Dive

## Flow-Based Programming Model

NiFi implements the Flow-Based Programming (FBP) paradigm where data flows as independent packets (FlowFiles) through a network of black-box processors connected by explicitly defined, configurable connections. Processors run asynchronously on their own schedules with built-in back pressure for flow control. Originally developed by the NSA as "Niagarafiles" and donated to Apache in 2014.

### FlowFile Internals

A FlowFile consists of two parts:

**Attributes** (key-value metadata):
- Standard: `uuid`, `filename`, `path`, `entryDate`, `lineageStartDate`
- MIME type: `mime.type` (set by IdentifyMimeType processor)
- Custom: any key-value pair added by processors (UpdateAttribute, EvaluateJsonPath, ExtractText)
- Attributes travel with the FlowFile and are lightweight (in-memory)

**Content** (data payload):
- Stored in the Content Repository on disk, referenced by pointer from the FlowFile
- Immutable -- when a processor modifies content, NiFi creates a new content claim (copy-on-write)
- Reference counting enables deduplication: cloned FlowFiles share the same content claim until modified
- FlowFiles can handle very large data objects (multi-GB files) without holding content in memory

### Processor Execution Model

Each processor has configurable execution parameters:

- **Concurrent Tasks**: Number of threads allocated (default: 1). Increase for I/O-bound processors (InvokeHTTP, PutDatabaseRecord). Limit for CPU-bound processors.
- **Run Schedule**: Timer-driven (interval), cron-driven (cron expression), or event-driven (triggered by upstream FlowFile arrival)
- **Penalty Duration**: How long a FlowFile is penalized before retry (default: 30 sec)
- **Yield Duration**: How long a processor pauses after yielding on error (default: 1 sec)
- **Bulletin Level**: Minimum severity for bulletin messages (DEBUG, INFO, WARNING, ERROR)

Processors define **Relationships** (success, failure, matched, unmatched, etc.) that determine routing. Every relationship must be either connected to a downstream processor or auto-terminated. Auto-terminating `failure` relationships silently drops errors -- avoid in production.

### Connection and Back Pressure Mechanics

Connections serve as bounded queues between processors with two configurable back pressure thresholds:

1. **Object Threshold** (default: 10,000 FlowFiles): Maximum FlowFile count
2. **Data Size Threshold** (default: 1 GB): Maximum total content size

When either threshold is reached:
- The upstream processor is **no longer scheduled to run**
- The connection shows yellow/red in the UI
- Downstream processing continues to drain the queue
- Once the queue drops below thresholds, the upstream processor resumes

These are **soft limits** -- a processor producing multiple FlowFiles in a single execution may temporarily exceed the threshold before back pressure takes effect.

Additional flow control mechanisms:
- **FlowFile expiration**: Auto-drop aged FlowFiles after a configurable TTL
- **Prioritization**: FirstInFirstOut (default), NewestFlowFileFirst, OldestFlowFileFirst, PriorityAttribute
- **Load balancing** (clusters): Round Robin, Single Node, Partition by Attribute across cluster nodes

## Core Repositories

### FlowFile Repository

- Write-Ahead Log (WAL) for current FlowFile metadata
- Contains FlowFile attributes and pointers to content claims
- Provides crash recovery -- on restart, NiFi rebuilds state from the WAL
- Must be on fast storage (SSD recommended) for optimal performance
- Size is proportional to the number of FlowFiles in flight (not content size)

### Content Repository

- Stores actual data payloads via content claims
- Uses reference counting for deduplication (cloned FlowFiles share claims)
- Copy-on-write semantics for content modification
- Content claims are garbage collected when no longer referenced by any FlowFile
- Can span multiple disk partitions for parallel I/O:
  ```
  nifi.content.repository.directory.default=./content_repository
  nifi.content.repository.directory.disk2=/data2/content_repository
  nifi.content.repository.directory.disk3=/data3/content_repository
  ```
- Provision 2-3x the expected in-flight data size

### Provenance Repository

- Complete history and lineage of every FlowFile
- Indexed via Apache Lucene for fast querying (default 500 MB per shard)
- Journals merged and compressed every 30 seconds
- Configurable retention:
  ```
  nifi.provenance.repository.max.storage.time=30 days
  nifi.provenance.repository.max.storage.size=10 GB
  nifi.provenance.repository.rollover.time=30 secs
  ```
- Event types: CREATE, RECEIVE, SEND, CLONE, FORK, JOIN, ROUTE, MODIFY_CONTENT, MODIFY_ATTRIBUTES, DROP, EXPIRE, DOWNLOAD, FETCH, ADDINFO
- Enables: lineage visualization (DAG), replay from any point, compliance auditing
- Performance impact: provenance indexing generates significant I/O on high-volume flows. Consider separate disk and tuning `nifi.provenance.repository.indexed.fields` to only needed fields.

## Clustering Architecture

### ZooKeeper-Based Clustering (1.x and 2.x Non-K8s)

NiFi uses **zero-leader clustering**: every node performs the same work on different data. No node distributes work to others.

Key roles:
- **Cluster Coordinator** (elected by ZooKeeper): Manages cluster membership, node heartbeats, disconnection/reconnection
- **Primary Node** (elected by ZooKeeper): Runs "isolated" processors (processors configured to run on only one node, e.g., ListFile, to avoid duplicate processing)

Data flow changes on any node are replicated to all nodes via the Cluster Coordinator. Each node processes its own data independently.

ZooKeeper requirements:
- Minimum 3 instances (odd number for quorum)
- Can be embedded within NiFi or external
- Manages leader election via ephemeral znodes

### Kubernetes-Native Clustering (2.x)

NiFi 2.0 introduced Kubernetes-native clustering:
- **Kubernetes Leases**: Replace ZooKeeper for Cluster Coordinator and Primary Node election
- **Kubernetes ConfigMaps**: Replace ZooKeeper znodes for shared state tracking
- Eliminates ZooKeeper deployment and management on Kubernetes
- Decoupled leader election interface promoted to `nifi-framework-api` library

### Connection Load Balancing

In clusters, connections can distribute FlowFiles across nodes:
- **Round Robin**: Even distribution across all nodes
- **Single Node**: All FlowFiles go to one node
- **Partition by Attribute**: FlowFiles with the same attribute value go to the same node (useful for ordered processing)

## Security Model

### Authentication

- **Mutual TLS (mTLS)**: Always the first method attempted when HTTPS is configured. Cannot be disabled.
- **LDAP/LDAPS**: Integration with LDAP directories (Active Directory, OpenLDAP)
- **Kerberos**: SPNEGO-based authentication. In NiFi 2.x, only Kerberos User Service is retained (keytab, password, ticket cache).
- **OpenID Connect (OIDC)**: Integration with identity providers (Keycloak, Okta). Supports RP-Initiated Logout, refresh tokens, automatic bearer token renewal.
- **SAML**: SAML 2.0 single sign-on

### Authorization

- Policy-based RBAC at the level of individual processors, process groups, controller services, and UI components
- Read, write, and component-specific policies
- Multi-tenant: different users/groups can access different parts of the flow
- File-based and LDAP-based user/group providers

### Data Protection

- SSL/TLS for all inter-node and client communication
- Sensitive properties encrypted at rest in flow configuration (flow.json.gz)
- Encrypted provenance for sensitive data flows
- `tls-toolkit` command-line utility for generating keystores, truststores, and configuration
- Parameter Contexts with sensitive values encrypted at rest
- Parameter Providers for external secret stores (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)

## NiFi 2.x Architectural Changes

### Runtime and Framework

| Component | NiFi 1.x | NiFi 2.x |
|---|---|---|
| Java | 8 or 11 | 21 (required) |
| Web framework | Spring 5 / Jetty 9 | Spring 6 / Jetty 12 / Servlet 6 |
| UI framework | AngularJS | Angular 18 |
| REST API spec | Swagger | OpenAPI 3 |

### Python Processor Support

NiFi 2.x introduced Python 3.10+ as a first-class extension language:
- Processors can be written entirely in Python using the NiFi Python API
- Full CPython support with access to pip/conda ecosystem
- Python processors support state management (added in 2.1.0)
- Can be packaged in NARs with included dependencies
- Works with NiFi's stateless mode for on-demand processing, data enrichment, and inline ML inference
- MiNiFi Java also supports Python processors

### Component Changes

- **Removed**: All legacy Kafka processors (replaced with controller service-based ConsumeKafka/PublishKafka), all Hive components, many deprecated processors
- **Renamed**: DistributedMapCacheServer -> MapCacheServer, DistributedMapCacheClient -> MapCacheClientService
- **Added**: Git-based Flow Registry Clients (primary versioning mechanism)
- **Deprecated**: NiFi Registry (community vote Feb 2026; removal planned in 3.0)
- **Removed**: Template support (use registry-based versioning)

### Version History

| Version | Date | Key Changes |
|---|---|---|
| 2.0.0 | Nov 2024 | GA: Java 21, Python support, K8s clustering, component removals |
| 2.1.0 | Jan 2025 | State management in Python processors; Python NAR packaging |
| 2.5.0 | 2025 | 150+ issues resolved |
| 2.6.0 | 2025 | 175+ issues resolved |
| 2.8.0 | 2026 | 170+ issues resolved; Record Gauge method in Process Session |

## NiFi REST API

NiFi exposes a comprehensive REST API for programmatic control:

- **Flow management**: Create, configure, start, stop processors and connections
- **Provenance queries**: Search and retrieve data lineage events
- **System diagnostics**: `GET /nifi-api/system-diagnostics` (heap, disk, threads)
- **Cluster management**: `GET /nifi-api/controller/cluster` (node status)
- **Flow status**: `GET /nifi-api/flow/process-groups/root/status?recursive=true`
- **Connection queues**: `GET /nifi-api/connections/{id}/status` (queue size, back pressure)
- **Counters and metrics**: Flow-level counters and reporting task data

All API endpoints use HTTPS when security is configured. Authentication follows the same mechanisms as the UI.
