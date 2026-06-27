# NiFi Best Practices

## Flow Design

### Processor Selection

- **Prefer native processors over scripts**: Use built-in processors (300+) whenever possible. Custom scripts (ExecuteScript, ExecuteStreamCommand) bypass NiFi's built-in provenance, error handling, and monitoring. They are harder to maintain and debug.
- **Use record-oriented processors for structured data**: ConvertRecord, UpdateRecord, QueryRecord, LookupRecord, and ValidateRecord handle many records per FlowFile efficiently. Avoid splitting into one-record-per-FlowFile unless downstream processing truly requires it.
- **Use the List/Fetch pattern for file ingestion**: Prefer ListFile + FetchFile over GetFile. ListFile runs on the Primary Node (avoids duplicate processing in clusters), tracks state, and FetchFile distributes retrieval across all nodes.
- **Use controller service-based Kafka processors (NiFi 2.x)**: The new ConsumeKafka/PublishKafka use shared controller services for connection configuration, replacing the older embedded-config approach. All legacy Kafka processors were removed in 2.0.

### Connection Sizing

- **Set back pressure thresholds intentionally**: Defaults are 10,000 objects and 1 GB. Adjust based on expected throughput, FlowFile sizes, available memory, and acceptable latency tolerance.
- **Size connections for expected burst**: If upstream produces faster than downstream consumes, size the queue to absorb bursts without triggering back pressure prematurely.
- **Set FlowFile expiration on non-critical connections**: Prevent stale data from accumulating indefinitely. Useful for monitoring and alerting side flows.
- **Use load-balanced connections in clusters**: Configure Round Robin, Single Node, or Partition by Attribute to distribute work effectively across cluster nodes.

### Process Group Organization

- **Organize by function**: Create process groups for logical stages -- Ingestion, Validation, Transformation, Routing, Delivery, Error Handling.
- **Use Input/Output Ports for clear interfaces**: Define the data contract between process groups via named ports.
- **Name descriptively**: Include source/destination and purpose (e.g., "Ingest: Customer Orders from Kafka", "Transform: Normalize Address Records").
- **Keep nesting to 3-4 levels maximum**: Deeply nested process groups are difficult to navigate and debug.
- **Use Parameter Contexts per environment**: Define parameters (database URLs, credentials, file paths) in parameter contexts. Swap contexts when promoting flows across environments.
- **Version process groups via Git-based Flow Registry**: NiFi 2.x Git-based Flow Registry Clients are the recommended versioning mechanism. NiFi Registry is deprecated.

## Performance Optimization

### Concurrent Tasks

- **Start conservative, scale up**: Begin with default concurrent tasks (1) and increase based on observed throughput.
- **Multi-thread I/O-bound processors**: InvokeHTTP, PutDatabaseRecord, PutS3Object benefit from higher concurrent tasks (4-16+) since they wait on external systems.
- **Limit CPU-bound processors**: Transformation processors (JoltTransformJSON, ConvertRecord) may cause contention with too many threads. Monitor CPU utilization.
- **Account for cluster multiplication**: In clusters, total concurrent tasks = (configured value) x (number of nodes).

### Batch Size and FlowFile Management

- **Batch records into larger FlowFiles**: Processing 1,000 records in one FlowFile is far more efficient than 1,000 individual FlowFiles. Use MergeRecord or MergeContent to batch small FlowFiles.
- **Use MergeContent before egress**: Merge small FlowFiles before writing to destinations (S3, HDFS, databases) to reduce overhead and small-file problems.
- **Avoid unnecessary splits**: SplitRecord and SplitText create many FlowFiles. Only split when downstream processing requires individual records.
- **Set appropriate Run Schedule**: Timer-driven with 0 sec runs as fast as possible. Use longer intervals (1 sec, 5 sec) for polling processors to reduce CPU overhead when idle.

### Repository Configuration

- **Place repositories on separate fast disks**: FlowFile, Content, and Provenance Repositories should each be on separate physical disks (SSDs recommended). This prevents I/O contention.
- **Use multiple Content Repository partitions**: Spread across multiple disks for parallel I/O throughput.
- **Size Provenance Repository appropriately**: Provenance generates significant I/O. Set retention limits based on compliance needs vs performance:
  ```
  nifi.provenance.repository.max.storage.time=30 days
  nifi.provenance.repository.max.storage.size=10 GB
  ```
- **Tune JVM heap size**: Allocate 50-75% of available RAM to NiFi's JVM heap. Remaining RAM is used by the OS for disk caching (critical for repository performance):
  ```
  # bootstrap.conf
  java.arg.2=-Xms4g
  java.arg.3=-Xmx4g
  ```

### Content Repository Sizing

- Provision 2-3x the expected in-flight data size
- Monitor disk usage with MonitorDiskUsage reporting task
- Use NVMe SSDs for high-throughput deployments; test network storage (NFS, EBS) carefully for latency impact

## Error Handling

### Retry Patterns

- **Configure penalty and yield**: Penalty duration controls how long a FlowFile waits before retry. Yield duration controls how long the processor pauses after errors.
- **Use RetryFlowFile processor**: Tracks retry count and routes to `retries_exceeded` after a configurable maximum. Prevents infinite retry loops.
- **Implement exponential backoff**: Use UpdateAttribute to track retry count and ControlRate or Wait processor for increasing delays between retries.

### Failure Routing

- **Always connect the failure relationship**: Never auto-terminate `failure` on production processors. Route failures to dedicated error handling flows.
- **Log failures with context**: Route failed FlowFiles through LogAttribute or LogMessage to capture error details, FlowFile attributes, and relevant context.
- **Separate transient from permanent failures**: Transient errors (network timeouts, temporary unavailability) should retry. Permanent errors (malformed data, schema violations) should route to dead letter flows.

### Dead Letter Pattern

```
[Processor] --failure--> [UpdateAttribute: add error metadata]
                              |
                              v
                         [RouteOnAttribute: transient vs permanent?]
                              |                    |
                         (transient)          (permanent)
                              |                    |
                              v                    v
                    [RetryFlowFile]     [PutFile: dead_letter/]
                         |        |
                    (retry)  (retries_exceeded)
                         |        |
                         v        v
                   [Original]  [PutFile: dead_letter/]
```

- Persist failed FlowFiles to a dead letter destination (file, S3, database)
- Include error metadata (error message, timestamp, source processor, retry count)
- Design for reprocessing so failed FlowFiles can be resubmitted after root cause fix
- Monitor dead letter queues with alerting

## Security Best Practices

### Least Privilege

- Restrict user access to specific process groups via NiFi's policy-based authorization
- Use dedicated service accounts for each NiFi node and integration
- Limit controller service access -- database connection pools and SSL contexts contain sensitive credentials

### Sensitive Properties

- Use Parameter Contexts for credentials -- never hardcode passwords, API keys, or connection strings in processor properties
- Integrate with external secret stores via Parameter Providers (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)
- NiFi encrypts sensitive property values in flow.json.gz using the configured sensitive properties key

### Network Security

- Always use HTTPS for web UI and REST API access (default port 8443)
- Enable inter-node mutual TLS in clusters
- Use `tls-toolkit` to automate keystore and truststore generation
- Restrict network access via firewalls/security groups

## Deployment

### Docker

- Use official images: `apache/nifi:2.x.x`
- Mount volumes for all three repositories (never use container-local storage):
  ```yaml
  volumes:
    - nifi-content:/opt/nifi/content_repository
    - nifi-flowfile:/opt/nifi/flowfile_repository
    - nifi-provenance:/opt/nifi/provenance_repository
    - nifi-conf:/opt/nifi/conf
  ```
- Build custom images for extensions using multi-stage Dockerfiles
- Externalize configuration via environment variables or mounted config files

### Kubernetes

- **Deploy as StatefulSet**: NiFi requires stable network identifiers and persistent storage
- **Use performant storage classes**: SSDs (gp3/io1 on AWS, premium-lv on Azure) for repository PVCs. Avoid network-attached HDD.
- **Consider single-node deployments**: Multiple independent single-node NiFi instances (one per pipeline or team) are often simpler and more reliable than clusters on K8s.
- **Use NiFi 2.x K8s clustering**: Eliminates ZooKeeper dependency (Leases + ConfigMaps)
- **Consider NiFiKop operator**: Konpyutaika NiFiKop automates cluster provisioning, scaling, and management on Kubernetes
- **Resource requests/limits**: NiFi typically needs 4-8 GB RAM minimum for production workloads

### Monitoring Integration

- **Prometheus + Grafana**: Use PrometheusReportingTask to export metrics. Push to Prometheus PushGateway or pull via metrics endpoint.
- **REST API polling**: `/nifi-api/system-diagnostics` and `/nifi-api/flow/cluster/summary` for programmatic monitoring
- **Reporting Tasks**: MonitorDiskUsage, MonitorMemory, ControllerStatusReportingTask, SiteToSiteProvenanceReportingTask
- **Log aggregation**: Ship nifi-app.log, nifi-user.log, nifi-bootstrap.log to ELK/Splunk/CloudWatch
- **Alert on back pressure**: Monitor connection queue sizes and alert when queues approach thresholds

## Migration: NiFi 1.x to 2.x

### Pre-Migration Checklist

1. **Upgrade to NiFi 1.27.0 first**: Migration to 2.0 requires being on 1.27.0. Direct jumps from older 1.x are not supported.
2. **Review nifi-deprecation.log**: Available in recent 1.x versions. Identifies deprecated features and components in active use.
3. **Inventory deprecated components**: Check all processors, controller services, and reporting tasks against the 2.0 removal list.
4. **Test Java 21 compatibility**: Ensure all custom NARs and extensions compile and run on Java 21.
5. **Plan for Kafka migration**: All legacy Kafka processors are removed. Migrate to controller service-based ConsumeKafka/PublishKafka.
6. **Plan for Hive component removal**: All Hive components removed. Migrate to JDBC-based alternatives.

### Breaking Changes

| Area | Change | Action |
|---|---|---|
| Java | Java 21 required | Update JDK on all nodes |
| Kafka | All legacy Kafka processors removed | Migrate to controller service-based processors |
| Hive | All Hive components removed | Migrate to JDBC alternatives |
| Cache | Distributed*Cache* services renamed | Update bundle coordinates in flow.json.gz |
| Kerberos | Only KerberosUserService retained | Consolidate Kerberos configuration |
| Templates | Support removed | Convert templates to versioned process groups |
| UI | Advanced UI path changed to `/` | Update automation/bookmarks |
| NARs | Some components relocated | Update bundle coordinates |

### Migration Steps

1. Upgrade to NiFi 1.27.0 and resolve all deprecation warnings
2. Back up all flow configurations, repositories, and NiFi properties
3. Replace deprecated components with recommended alternatives
4. Update Java to 21, install NiFi 2.x binaries
5. Update flow.json.gz with new bundle coordinates (renamed/relocated components)
6. Migrate Kafka flows to controller service-based processors
7. Test thoroughly in a non-production environment
8. Update monitoring and automation scripts for API or path changes
