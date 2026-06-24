---
name: "data-distributed-storage"
description: "Use this skill when designing distributed storage for HDFS, S3, ADLS, GCS, MinIO, NFS, or any distributed file system for data workloads. This skill enforces: storage backend selection, data durability and replication, file format selection, partitioning and compression, lifecycle policies, storage tiering, and cost optimization. Do NOT use for: database storage engines, local filesystem tuning, or content delivery networks."
metadata:
  category: data
  source:
    repository: "https://github.com/j4flmao/agent-skills"
    path: "skills/data/distributed-storage"
    license_path: "LICENSE"
---

# Distributed Storage

## Purpose
Design distributed storage systems for data workloads. Select the right storage backend (HDFS, S3, ADLS, GCS, MinIO), configure durability and replication, optimize file formats and compression, and implement lifecycle policies.

## Agent Protocol

### Trigger
Exact user phrases: "HDFS", "S3", "ADLS", "GCS", "MinIO", "distributed storage", "object storage", "file system", "data lake storage", "storage tier", "lifecycle policy", "replication factor", "erasure coding", "storage cost".

### Input Context
- Storage backend preference (S3, ADLS, GCS, HDFS, MinIO)
- Data volume (current TB, annual growth)
- Access patterns (frequent, infrequent, archive)
- Durability and availability requirements
- Budget and cost constraints
- Compliance requirements (data residency, encryption)
- Network bandwidth and latency constraints

### Output Artifact
Distributed storage architecture with backend selection, tiering strategy, lifecycle policy, and cost model.

### Response Format
```yaml
# Storage backend
# Tier configuration
# Lifecycle rules
# Cost projection
```

### Completion Criteria
- [ ] Storage backend selected with rationale
- [ ] Storage tiers defined (hot/warm/cold/archive)
- [ ] Lifecycle policies configured for data movement
- [ ] Data durability and replication strategy documented
- [ ] Encryption (at rest, in transit) configured
- [ ] Cost projection for current and 3-year growth
- [ ] Backup and disaster recovery plan defined

## Workflow

### Step 1: Backend Selection

#### Object Store Comparison

| Feature | AWS S3 | ADLS Gen2 | GCS | MinIO |
|---|---|---|---|---|
| Consistency | Read-after-write | Strong | Strong | Strong |
| Auth | IAM roles, bucket policies | RBAC, SAS tokens | IAM, service accounts | JWT, OIDC, LDAP |
| Encryption | SSE-S3/KMS/CSE | SSE-AES/KMS/CMK | Google-managed/CMEK/CSE | KMS, auto-encryption |
| Lifecycle | Transition, expiry, versioning | Tiering, soft-delete | Nearline/Coldline/Archive | Bucket lifecycle |
| Max object size | 5 TB | 4.75 TB | 5 TB | 100 TB (configurable) |
| S3 Compatible | Native | Yes (via gateway) | Yes (XML API) | Native |
| Cost (per TB/mo) | ~$23 (standard) | ~$20 (hot) | ~$20 (standard) | Hardware + ops |
| Durability | 99.999999999% (11 9s) | 99.999999999% (11 9s) | 99.999999999% (11 9s) | Configurable |
| Availability SLA | 99.99% | 99.9% | 99.95% | Depends on setup |

#### Backend Selection Decision Tree
```
Cloud provider?
├── AWS → S3 (best integration with AWS ecosystem)
├── Azure → ADLS Gen2 (best with Azure AD, Active Directory)
├── GCP → GCS (strong consistency, best for Google ecosystem)
├── Multi-cloud → MinIO (S3-compatible layer across clouds)
└── On-premise / air-gapped → MinIO or HDFS

Primary workload?
├── Data lake with compute engines → Object store (S3/ADLS/GCS)
├── Legacy Hadoop/Spark without cloud → HDFS
├── Private cloud, edge, or air-gapped → MinIO
└── High-performance computing → Parallel file system (Lustre, GPFS)
```

### Step 2: Storage Tiering

#### Tier Characteristics

| Tier | Storage Class | Latency | Cost/TB/mo | Use Case |
|---|---|---|---|---|
| Hot | S3 Standard, ADLS Hot | Millisecond | ~$23 | Active data, daily pipelines, ML training |
| Warm | S3 Infrequent Access | Millisecond | ~$12.50 | Monthly queries, staging data |
| Cold | S3 Glacier Instant | Millisecond (instant) | ~$4 | Quarterly access, compliance retention |
| Archive | S3 Glacier Deep Archive | 12 hours | ~$1 | Annual access, legal holds |

#### Tiering Strategy
Hot: last 30-90 days of data. Warm: 90 days to 1 year. Cold: 1-3 years. Archive: 3-7+ years (retention-based). Intelligent tiering (S3) auto-moves objects between hot and warm based on access patterns.

### Step 3: Lifecycle Policies

```json
{
  "Rules": [
    {
      "Id": "TierAndExpire",
      "Status": "Enabled",
      "Filter": { "Prefix": "logs/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER" },
        { "Days": 365, "StorageClass": "DEEP_ARCHIVE" }
      ],
      "Expiration": { "Days": 2555 }
    },
    {
      "Id": "ExpireTempFiles",
      "Status": "Enabled",
      "Filter": { "Prefix": "tmp/" },
      "Expiration": { "Days": 7 }
    }
  ]
}
```

### Step 4: Durability and Replication

#### Object Store Durability
S3/ADLS/GCS provide 11 9s of durability via erasure coding across multiple devices/facilities. Replication is handled by the cloud provider. For additional protection: cross-region replication (CRR) for disaster recovery, same-region replication (SRR) for compliance.

#### HDFS Replication
Default replication factor: 3 (1 primary, 2 replicas on different racks). Storage overhead: 3x. Erasure coding reduces overhead: RS-6-3 (1.33x overhead), RS-10-4 (1.5x overhead). EC recommended for cold data on HDFS (> 100TB).

#### Backup and DR
Cross-region backup for critical data. Versioning enabled on all buckets. Replication Rules: replicate Tier 1 data to DR region synchronously or asynchronously. Test restore quarterly.

### Step 5: Compression and Encoding

| Codec | Speed | Compression Ratio | Use Case |
|---|---|---|---|
| ZSTD (level 3) | Very fast | Good (2-4x) | Default for Parquet/ORC |
| GZIP (level 6) | Moderate | Best (3-6x) | Archive, cold data |
| Snappy | Fastest | Fair (1.5-3x) | Streaming, hot data |
| LZ4 | Fastest | Fair (1.5-2x) | Logs, real-time |
| BZIP2 | Slow | Best (4-8x) | Archive only |

Compress data at the file format level (Parquet/ORC) rather than at the transport level. Avoid double compression. Test: compress a representative dataset with each codec, measure speed and ratio.

### Step 6: Data Layout

#### Partitioning by File Structure
Organize storage by: source/system, data domain, date partition, file. Example: `s3://data-lake/raw/salesforce/orders/year=2026/month=05/day=01/load_id=abc123/orders_001.parquet`. This layout enables: partition pruning, easy lifecycle management, clear ownership boundaries.

#### File Size Targets
Small files cause performance problems for query engines. Target file size: 128MB-1GB. Use compaction jobs to merge small files. Monitor average file size per dataset.

### Step 7: HDFS Architecture

#### NameNode and DataNode
Active NameNode manages filesystem metadata (namespace, blocks, locations). Standby NameNode for HA via QJM (Quorum Journal Manager). DataNodes store block data and report to NameNode. Block size: 128MB or 256MB default. Rack awareness for replica placement.

#### HDFS Key Config
```yaml
# hdfs-site.xml
dfs.replication: 3
dfs.block.size: 268435456  # 256MB
dfs.namenode.handler.count: 100
dfs.datanode.handler.count: 50
dfs.namenode.gc.time.threshold: 60s
dfs.namenode.checkpoint.period: 3600  # 1 hour
dfs.permissions.enabled: true
```

### Step 8: Security

#### Encryption at Rest
Server-side encryption: SSE-S3 (AES-256, S3-managed keys), SSE-KMS (AWS KMS-managed keys), SSE-C (customer-provided keys). Client-side encryption: encrypt before upload, decrypt after download. For compliance: SSE-KMS with audit logging.

#### Encryption in Transit
TLS 1.2+ for all S3/ADLS/GCS API calls. Enforce HTTPS-only bucket policies. HDFS: enable SSL for RPC and data transfer.

```json
{
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::data-lake/*",
      "Condition": {
        "Bool": { "aws:SecureTransport": "false" }
      }
    }
  ]
}
```

### Step 9: Cost Optimization

#### Strategies
Use intelligent tiering for automatic cost savings on variable-access data. Request (S3) Reduced Redundancy for non-critical data (lower durability = lower cost). Reserved capacity for predictable usage. Monitor and alert on cost anomalies.

#### Cost Monitoring
Track: storage cost per bucket/container, data transfer costs (egress), request costs (PUT/GET/LIST), lifecycle transition costs. Allocate costs to teams/domains via tag-based cost allocation.

### Decision Trees

#### Storage Backend
```
Cloud adoption strategy?
├── Single cloud → Native object store (S3/ADLS/GCS)
├── Multi-cloud → MinIO (abstraction layer)
├── On-premise
│   ├── Hadoop ecosystem → HDFS
│   └── Kubernetes-native → MinIO (S3-compatible)
└── Edge / IoT → MinIO (lightweight, S3 API)
```

#### Lifecycle Policy
```
Data access pattern?
├── Accessed frequently → Hot tier (delete when no longer needed)
├── Accessed occasionally → Intelligent tiering or manual tiering
├── Compliance retention → Write once, tier to cold → delete after retention
└── Temporary data → Hot tier → delete in 7-30 days
```

### MinIO Deployment Architecture

#### Multi-Node Setup
MinIO runs as a distributed system across multiple nodes. Minimum 4 nodes for erasure coding protection. Each node: 4+ drives, SSD/NVMe preferred for performance. Deployed via: Docker Compose (dev/tiny), Kubernetes Operator (production), bare metal (HPC).

```yaml
# MinIO Kubernetes Operator
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: data-lake-storage
spec:
  image: quay.io/minio/minio:latest
  credsSecret:
    name: minio-creds
  pools:
    - servers: 4
      volumesPerServer: 4
      volumeClaimTemplate:
        spec:
          storageClassName: ssd
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 4Ti
  mountPath: /export
  requestAutoCert: true
  buckets:
    - name: raw
    - name: staging
    - name: analytics
```

#### Erasure Coding
MinIO uses Reed-Solomon erasure coding. Default parity: N/2 drives (max protection). Configurable: standard (EC:4) for 8-drive setup, reduced (EC:2) for performance. Read tolerance: lose up to N/2 drives. Write tolerance: lose up to N/2 drives. Storage overhead: 2x for N/2 parity, 1.33x for N/4 parity.

```yaml
# Erasure coding parity by deployment size
# 4 nodes × 4 drives = 16 drives
#   EC:8 → tolerate 8 drive failures, 2x overhead
#   EC:4 → tolerate 4 drive failures, 1.33x overhead
#   EC:2 → tolerate 2 drive failures, 1.14x overhead

# Set via environment variable
MINIO_STORAGE_CLASS_STANDARD: "EC:4"
MINIO_STORAGE_CLASS_RRS: "EC:2"     # Reduced redundancy for temp data
```

#### Performance Tuning
```yaml
# Drive-level
# Use XFS filesystem with noatime,nodiratime mount options
# Separate write-intensive (metadata, WAL) from read-intensive drives

# Network-level
# MinIO uses S3-compatible HTTP/REST
# Enable HTTP/2 for multiplexing
# Use load balancer (nginx, HAProxy) for multi-node distribution

# Kernel tuning
# net.core.rmem_max: 134217728    # 128MB receive buffer
# net.core.wmem_max: 134217728    # 128MB send buffer
# net.ipv4.tcp_congestion_control: bbr  # BBR for better throughput
# vm.dirty_ratio: 30              # Page cache dirty ratio
# vm.dirty_background_ratio: 10
```

### Step 10: Data Transfer and Migration

#### Transfer Acceleration
```yaml
# AWS S3 Transfer Acceleration
# Uses CloudFront edge locations, TCP optimization
# Enable: s3.put_bucket_accelerate_configuration
# Best for: cross-region uploads, large objects > 1GB
# Cost: premium per GB transferred
# Test: s3-accelerate-speedtest.s3-accelerate.amazonaws.com

# Azure Data Box / Import-Export
# Physical transfer: Data Box (80TB), Data Box Disk (8TB)
# For: > 10TB initial loads, slow networks, air-gapped
# Timeline: order → receive → load → return → ingest (2-4 weeks)

# GCS Storage Transfer Service
# Online: from S3, HTTP, or GS URLs
# Schedule: one-time or recurring
# Best for: ongoing sync from S3 to GCS
```

#### Migration Strategy
```yaml
migration_phases:
  phase_1_assessment:
    - inventory current storage (total TB, object count, avg size)
    - identify access patterns (hot vs cold, frequency)
    - document retention and compliance requirements
    - estimate egress costs and transfer time

  phase_2_pilot:
    - migrate 1-2 TB of non-critical data first
    - validate performance, cost, and access patterns
    - document issues and adjust strategy

  phase_3_bulk:
    - parallel multi-threaded copy (aws s3 sync, rclone, distcp)
    - validate data integrity checksums post-transfer
    - monitor for failures (rate limits, timeouts)

  phase_4_cutover:
    - final sync of delta changes
    - update application configs to point to new storage
    - redirect DNS / endpoint to new location
    - decommission old storage after 30-day validation window
```

### Step 11: Compliance Features

#### Object Lock / WORM
```yaml
# S3 Object Lock (compliance mode)
# Prevents object deletion or overwrite for retention period
# Governance mode: users with special permissions can override
# Compliance mode: no one (including root) can override
# Legal hold: prevents deletion regardless of retention

object_lock_examples:
  - name: "Financial records (SOX)"
    mode: COMPLIANCE
    retention_days: 2555  # 7 years
    bucket: "data-lake/finance/"

  - name: "Logs (internal policy)"
    mode: GOVERNANCE
    retention_days: 365  # 1 year
    bucket: "data-lake/logs/"

# ADLS Gen2: immutability policy
# Set at container level
# Time-based retention or legal hold
```

#### Data Residency
```yaml
# Data residency requirements
# GDPR: data must stay in EU region
# Financial services: data within country borders
# Healthcare: HIPAA requires US-only storage (for US patients)

# Implementation:
# - Per-region buckets with IAM restrictions
# - S3 bucket policies denying cross-region replication for sensitive data
# - MinIO multi-tenant deployment per region
# - Regular audit to verify no data leaves allowed regions
```

### Step 12: Cost Modeling

#### Cost Components
```yaml
cost_components:
  storage:
    - per-GB-month by tier (hot, warm, cold, archive)
    - minimum storage duration charges (Glazer: 90 days min)
    - early deletion fees (cold/archive tiers)

  operations:
    - PUT/COPY/POST/LIST requests (per 1000)
    - GET/SELECT requests (per 1000)
    - lifecycle transition requests (per 1000)

  data_transfer:
    - upload (usually free)
    - download / egress (per GB, tiered pricing)
    - cross-region replication (per GB)
    - transfer acceleration (premium per GB)

  additional:
    - encryption (KMS: per key, per API call)
    - monitoring (CloudWatch, metrics per custom metric)
    - backup / replication (CRR storage in destination region)
```

#### Estimation Tool
```yaml
# Monthly storage cost estimate
cost_estimate:
  hot_data:
    volume: 50 TB
    unit_cost: $23/TB/mo
    subtotal: $1,150/mo

  warm_data:
    volume: 150 TB
    unit_cost: $12.50/TB/mo
    subtotal: $1,875/mo

  cold_data:
    volume: 300 TB
    unit_cost: $4/TB/mo
    subtotal: $1,200/mo

  archive_data:
    volume: 500 TB
    unit_cost: $1/TB/mo
    subtotal: $500/mo

  operations:
    requests: $200/mo  # Based on 10M PUT + 100M GET

  data_transfer:
    egress: $300/mo    # Based on 10TB egress

  monitoring_backup:
    cross_region_replication: $500/mo  # 50TB replicated
    monitoring: $100/mo

  total_monthly: $5,825/mo
  total_annual: $69,900/yr
```

### Step 13: Monitoring and Observability

#### Storage Metrics
```yaml
# Object store monitoring (CloudWatch, Azure Monitor, GCS Ops)
metrics:
  storage:
    - BucketSizeBytes (by storage tier)
    - NumberOfObjects
    - AverageObjectSize

  requests:
    - AllRequests (count)
    - GetRequests / PutRequests / ListRequests
    - 4xxErrors / 5xxErrors
    - FirstByteLatency / TotalRequestLatency

  throughput:
    - BytesDownloaded / BytesUploaded
    - GetBandwidth / PutBandwidth (MB/s)

  cost:
    - StorageCost (by bucket/tag)
    - RequestCost
    - DataTransferCost
    - TotalCost
```

#### Alerting Thresholds
```yaml
alerts:
  - name: "Storage growth anomaly"
    metric: BucketSizeBytes
    threshold: "> 20% week-over-week increase"
    severity: warning

  - name: "Error rate spike"
    metric: 5xxErrors
    threshold: "> 1% of total requests"
    severity: critical

  - name: "Latency degradation"
    metric: FirstByteLatency
    threshold: "p99 > 500ms"
    severity: warning

  - name: "Budget threshold"
    metric: TotalCost
    threshold: "> 80% of monthly budget"
    severity: warning

  - name: "Lifecycle failure"
    metric: LifecycleTransitions
    threshold: "transitions failed > 10 per hour"
    severity: warning
```

### Decision Trees (continued)

#### Compression Codec Selection
```
Workload type?
├── Hot data, frequent queries → ZSTD (level 3) — fast decompression
├── Cold data, archive → GZIP (level 6) — best compression ratio
├── Streaming, low-latency → Snappy or LZ4 — minimal CPU overhead
├── Columnar formats (Parquet/ORC)
│   ├── Default → ZSTD (best balance)
│   └── Legacy compatibility → Snappy
└── JSON/CSV files
    ├── Compressed → GZIP (most tools support it)
    └── Splittable → BZIP2 or LZ4
```

#### Replication Strategy
```
Compliance requirement?
├── Disaster recovery (region outage)
│   ├── RTO < 1 hour → Synchronous CRR
│   └── RTO < 4 hours → Asynchronous CRR
├── Data sovereignty (must stay in region)
│   └── Same-region replication (SRR) + backup to another AZ
├── GDPR right to erasure
│   ├── Replicate selectively (no unnecessary copies)
│   └── Document replication topology for audit
└── No compliance requirement
    └── No replication — rely on cloud provider durability
```

## Rules
- Separate storage from compute for elasticity
- Use lifecycle policies to automatically tier data
- Compress all data at rest — storage is not free
- Encrypt data at rest and in transit
- Monitor storage growth and set budget alerts
- Document retention policies for compliance requirements
- Prefer object storage over HDFS for new deployments
- Use versioning for data protection against accidental deletion
- Target 128MB-1GB file sizes for query engine performance
- Monitor and alert on storage cost anomalies by team/project
- Test disaster recovery procedures annually
- Allocate storage costs to teams for cost accountability
- Run MinIO with at least 4 nodes and N/2 erasure coding parity for production
- Benchmark storage performance before committing to architecture
- Use Object Lock (WORM) for compliance-bound data
- Plan data migration with pilot phase before bulk transfer
- Model total cost of ownership including operations, transfer, and egress
- Alert on storage growth anomalies and budget thresholds

## References

- [Distributed storage fundamentals](references/distributed-storage-fundamentals.md)
- [Advanced distributed storage](references/distributed-storage-advanced.md)
- [HDFS architecture](references/hdfs-architecture.md)
- [S3-compatible storage](references/s3-compatible.md)
- [S3-compatible configurations](references/s3-compatible-configs.md)
- [Storage deployment guide](references/storage-deployment-guide.md)
