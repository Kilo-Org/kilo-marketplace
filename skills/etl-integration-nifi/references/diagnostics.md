# NiFi Diagnostics

## Back Pressure Issues

### Symptoms

- Connection queues fill up (yellow/red indicators in the UI)
- Upstream processors stop being scheduled
- Data flow stalls or slows dramatically
- FlowFiles age in queues (increasing latency)

### Diagnostic Steps

1. **Identify the bottleneck processor**: Check processor stats -- compare in vs. out FlowFile counts. The processor with growing input and low output is the bottleneck.
2. **Check downstream processor bulletins**: Look for error bulletins on the processor that is not draining its input.
3. **Check external system health**: Database connections, API availability, file system capacity.
4. **Review connection queue details**: Right-click connection in UI for object count, data size, and percentage full.

### Resolutions

| Cause | Fix |
|---|---|
| Downstream processor slower than upstream | Increase concurrent tasks on bottleneck processor if I/O-bound |
| Downstream processor in error state | Fix the error (check bulletins, logs, external system health) |
| External system unresponsive or slow | Verify connectivity, check external system load |
| Thresholds too low for workload | Increase back pressure thresholds (default: 10,000 objects / 1 GB) |
| CPU/memory-bound processor | Scale the cluster or reduce concurrent tasks on other processors |

**Additional mitigations**:
- Add MergeRecord before bottleneck to batch records for higher throughput
- Add ControlRate to throttle upstream production rate
- Use load-balanced connections in clusters to distribute across nodes

### Monitoring

- Connection queue status visible in UI (object count, data size, percentage full, color coding)
- REST API: `GET /nifi-api/connections/{id}/status` returns queuedCount, queuedSize, percentUseCount, percentUseBytes
- PrometheusReportingTask exports connection queue metrics for Grafana dashboards and alerting

## Memory Pressure

### Symptoms

- Slow, unresponsive NiFi UI
- JVM garbage collection pauses (visible in GC logs)
- `OutOfMemoryError` in nifi-app.log
- Node disconnections in clustered environments
- High CPU caused by excessive GC

### Diagnostic Steps

1. Check System Diagnostics (Global Menu -> System Diagnostics or `GET /nifi-api/system-diagnostics`): Heap Usage, Non-Heap Usage, GC count and time
2. Review GC logs for long pauses (>500ms):
   ```
   java.arg.13=-Xlog:gc*:file=./logs/nifi-gc.log
   ```
3. Check total FlowFiles in flight across all connections (large queues consume FlowFile Repository memory)
4. Identify processors that buffer entire FlowFile content in memory (some processors load content into heap)

### Resolutions

1. **Increase JVM heap** (allocate 50-75% of available RAM):
   ```
   # bootstrap.conf
   java.arg.2=-Xms4g
   java.arg.3=-Xmx4g
   ```
2. **Reduce in-flight FlowFiles**: Lower back pressure thresholds to limit total queue sizes
3. **Avoid content buffering**: Use streaming processors where possible. Avoid loading entire FlowFile content into memory for large files.
4. **Tune garbage collection**: G1GC is default in Java 21. Monitor for long pauses.
5. **Reduce concurrent tasks**: Lower total thread count if memory pressure is from thread overhead
6. **Configure Content Repository cleanup**: Set appropriate `nifi.content.claim.max.appendable.size` and ensure garbage collection runs regularly
7. **Configure Provenance Repository limits**:
   ```
   nifi.provenance.repository.max.storage.size=10 GB
   nifi.provenance.repository.max.storage.time=30 days
   nifi.provenance.repository.rollover.time=30 secs
   ```

## Processor Errors

### Symptoms

- Red error indicator on processor in UI
- Bulletins appearing on processor (icon overlay)
- FlowFiles routing to `failure` relationship
- Processor in STOPPED or INVALID state

### Common Error Types

| Error | Typical Cause | Resolution |
|---|---|---|
| Connection refused / timeout | External system down or unreachable | Verify network connectivity, firewall rules, service health |
| Authentication failure | Invalid credentials or expired tokens | Update credentials in controller services or parameter contexts |
| Schema mismatch | Input data does not match expected schema | Validate input data; use ValidateRecord to filter non-conforming records |
| Permission denied | File system or service permissions | Fix permissions; check NiFi user identity |
| SQL exception | Bad query, constraint violation, pool exhaustion | Review SQL, check constraints, increase pool size in DBCPConnectionPool |
| NullPointerException | Missing required FlowFile attributes or content | Add attribute validation before the failing processor |
| Invalid configuration | Missing required properties or invalid values | Review processor config; check for deprecated properties after 2.x upgrade |

### Resolution Steps

1. Check the processor's bulletin (hover over processor or check Bulletin Board)
2. Review `nifi-app.log` for detailed stack traces
3. Inspect the FlowFile in the incoming connection queue (right-click connection -> List queue -> View attributes and content)
4. Test with a simple FlowFile to isolate the issue
5. Check controller service status (ensure referenced services are enabled)

## Clustering Issues

### Symptoms

- Nodes showing as DISCONNECTED in cluster summary
- Flows not propagating to all nodes
- Inconsistent processing (some nodes working, others not)
- ZooKeeper connection errors in logs
- "Unable to communicate with cluster" errors

### Common Causes and Resolutions

| Issue | Cause | Resolution |
|---|---|---|
| Node disconnection | Network partition, ZK timeout, node overload | Check network, ZK health, node resources |
| Flow out of sync | Manual edits, version conflicts | Use Git-based Flow Registry; re-sync from coordinator |
| Primary node failover | Primary node crashed | Automatic via ZK election; verify new primary is operational |
| ZooKeeper quorum loss | Majority of ZK nodes down | Restore ZK nodes; requires majority for quorum |
| Split brain | Network partition isolating node groups | Resolve network partition; may require manual intervention |
| K8s lease expiry | Pod rescheduling, resource pressure | Check pod health; review lease TTL configuration |

### Clustering Health Checks

1. Verify all nodes connected: NiFi UI -> Cluster Summary (hamburger menu)
2. Check ZooKeeper status: `echo ruok | nc zookeeper-host 2181` (returns `imok`)
3. Review `nifi-app.log` on disconnected nodes for root cause
4. Verify network connectivity between all nodes (NiFi ports + ZK ports)
5. Check time synchronization across nodes (NTP)

## Performance Monitoring

### Bulletin Board

Real-time alerting mechanism:
- Access: Global Menu -> Bulletin Board, or status bar at top of UI
- Severity levels: DEBUG, INFO, WARNING, ERROR
- Filter by component, severity, message content, time range
- Retention: configurable (default 5 minutes)
- Key bulletins to watch: ERROR on any processor, WARNING on controller services, system-level memory/disk/cluster alerts

### System Diagnostics

Access via Global Menu -> System Diagnostics or `GET /nifi-api/system-diagnostics`:

| Metric | Warning Threshold |
|---|---|
| **Heap Usage** | >80% sustained |
| **Non-Heap Usage** | Unusual growth |
| **Processor Load** | >80% sustained |
| **Thread Count** | Unusual growth |
| **Uptime** | Frequent restarts |
| **FlowFile Repository Usage** | >80% |
| **Content Repository Usage** | >80% |
| **Provenance Repository Usage** | >80% |
| **Garbage Collection** | Long pauses (>500ms) |

### Provenance Analysis

Data provenance provides deep insight into flow behavior:
- **Lineage view**: Visual DAG showing the complete path of a FlowFile
- **Event search**: Query by processor, FlowFile UUID, time range, event type
- **Replay**: Re-submit a FlowFile from any point in its lineage for debugging
- Performance impact: provenance indexing generates significant I/O. High-volume flows may need reduced provenance detail or a separate provenance disk.

### Reporting Tasks

| Task | Purpose |
|---|---|
| **MonitorDiskUsage** | Alert when repository disk usage exceeds threshold |
| **MonitorMemory** | Alert when JVM memory pool usage exceeds threshold |
| **ControllerStatusReportingTask** | Report overall controller status metrics |
| **SiteToSiteProvenanceReportingTask** | Forward provenance events to remote NiFi or external system |
| **PrometheusReportingTask** | Export metrics in Prometheus format |

## Troubleshooting Procedures

### Flow Debugging

1. **Identify the problem area**: Look for processors with error bulletins, connections with growing queues, or processors with zero output
2. **Check the Bulletin Board**: Global Menu -> Bulletin Board. Filter by ERROR severity.
3. **Inspect connection queues**: Right-click connection -> "List queue". Examine FlowFiles:
   - View attributes: verify expected attributes are present and correctly formatted
   - View content: download or view in-browser to verify data format
4. **Review provenance**: Right-click processor -> "View data provenance". Find the problematic FlowFile and trace its lineage backward.
5. **Use DebugFlow processor**: Insert DebugFlow to simulate specific failure modes (exception, yield, penalize) for testing error handling.
6. **Check processor stats**: Right-click processor -> "View status history". Review Tasks/Time, FlowFiles In/Out, Bytes Read/Written. Identify trends.
7. **Review logs**: `nifi-app.log` for errors and stack traces. `nifi-user.log` for access issues.

### FlowFile Inspection

1. Right-click connection -> "List queue"
2. Select a FlowFile, click "eye" icon for details:
   - **Attributes tab**: All key-value pairs
   - **Content tab**: View or download (renders text, JSON, XML, hex)
3. Queue listing shows: position, UUID, filename, file size, queue duration, lineage duration

### Common Diagnostic Commands

```bash
# Check NiFi status
./bin/nifi.sh status

# System diagnostics via REST API
curl -k https://localhost:8443/nifi-api/system-diagnostics

# Cluster status
curl -k https://localhost:8443/nifi-api/controller/cluster

# All connections with queue sizes (recursive)
curl -k https://localhost:8443/nifi-api/flow/process-groups/root/status?recursive=true

# ZooKeeper health (1.x clusters)
echo ruok | nc zookeeper-host 2181
echo stat | nc zookeeper-host 2181
```

### Log Files

| Log File | Contents |
|---|---|
| `nifi-app.log` | Main application log: processor errors, framework events, stack traces |
| `nifi-user.log` | User actions: login, flow changes, access denials |
| `nifi-bootstrap.log` | NiFi startup/shutdown, JVM launch parameters |
| `nifi-deprecation.log` | Deprecated feature usage (important for 2.x migration planning) |
| `nifi-gc.log` | JVM garbage collection events (if configured) |

## Performance Tuning Checklist

- [ ] JVM heap sized to 50-75% of available RAM
- [ ] Repositories on separate fast disks (SSD/NVMe)
- [ ] Content Repository spread across multiple partitions
- [ ] Provenance Repository with appropriate retention limits
- [ ] Concurrent tasks tuned per processor based on workload type
- [ ] Back pressure thresholds set appropriately for each connection
- [ ] MergeRecord/MergeContent used before data egress
- [ ] Record-oriented processors used instead of per-FlowFile processing
- [ ] Monitoring configured (Prometheus, disk alerts, memory alerts)
- [ ] GC logging enabled for diagnosing memory issues
- [ ] Load-balanced connections configured in clusters
- [ ] Run schedule appropriate (not polling too frequently when idle)
