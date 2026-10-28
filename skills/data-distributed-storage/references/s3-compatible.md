# S3-Compatible Object Store Reference

## MinIO Deployment

### Distributed Mode
```
MinIO distributed: N servers x M drives per server
Erasure coding: data + parity = N*M drives
EC tolerance: up to N*M/2 drives can fail (with N/2 parity)

Example: 4 servers x 4 drives = 16 drives
  EC:8 = 8 data + 8 parity -> 50% usable, tolerate 8 drive failures
  EC:4 = 12 data + 4 parity -> 75% usable, tolerate 4 drive failures
  EC:2 = 14 data + 2 parity -> 87.5% usable, tolerate 2 drive failures
```

```yaml
# docker-compose.yml - 4-node distributed MinIO
version: '3.8'
services:
  minio1: &minio
    image: quay.io/minio/minio
    command: server --console-address ":9001" http://minio{1...4}/data{1...4}
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 10s
      retries: 5
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
      MINIO_SITE_REGION: us-east-1
      MINIO_STORAGE_CLASS_STANDARD: EC:4
      MINIO_STORAGE_CLASS_RRS: EC:2
    volumes:
      - d1:/data1; d2:/data2; d3:/data3; d4:/data4

  minio2: *minio
  minio3: *minio
  minio4: *minio

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    ports:
      - "9000:9000"
```

### K8s Helm Deployment
```bash
helm repo add minio https://charts.minio.io
helm upgrade --install minio minio/minio \
  --set mode=distributed \
  --set replicas=4 \
  --set persistence.size=1Ti \
  --set resources.requests.memory=4Gi \
  --set buckets[0].name=data-lake \
  --set buckets[0].policy=none \
  --set accessKey=$ACCESS_KEY \
  --set secretKey=$SECRET_KEY \
  --set ingress.enabled=true
```

## Ceph RADOS

### Architecture
```
Ceph cluster components:
  MONs (ceph-mon): maintain cluster map (3 or 5 for quorum)
  OSDs (ceph-osd): store data, 1 per disk
  MGR (ceph-mgr): cluster metrics, dashboard, balancer
  MDS (ceph-mds): metadata server for CephFS (optional for object only)

RADOS gateway (RGW):
  S3-compatible REST API
  Multi-tenancy via buckets/containers
  Supports S3 API (GET/PUT/DELETE, multipart, versioning)
  Standalone or HA with load balancer
```

```bash
# Bootstrap Ceph cluster
cephadm bootstrap --mon-ip 10.0.0.10
ceph osd pool create data-lake replicated 128
ceph osd pool application enable data-lake rgw
radosgw-admin user create --uid=data-user --display-name="Data Lake User"

# Erasure coded pool
ceph osd erasure-code-profile set ec-6-3 \
  k=6 m=3 ruleset-failure-domain=host
ceph osd pool create ec-data-pool 256 erasure ec-6-3
```

## Bucket Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["arn:aws:iam::account:user/etl-user"]},
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::data-lake/*", "arn:aws:s3:::data-lake"]
    }
  ]
}
```

## Versioning and Lifecycle

```bash
# Enable versioning (MinIO + Ceph RGW)
mc version enable myminio/data-lake

# Lifecycle rules: tier to cold storage
mc ilm rule add myminio/data-lake \
  --expire-days "365" \
  --transition-days "90" \
  --storage-class "MINIO_TIER_COLD"
```

```json
{
  "Rules": [
    {"Id": "tier-to-cold", "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "Transitions": [{"Days": 90, "StorageClass": "GLACIER"}],
      "NoncurrentVersionExpiration": {"NoncurrentDays": 30}
    }
  ]
}
```

## S3 Gateway (MinIO as gateway)

MinIO gateway mode is deprecated. Use sidecar pattern instead:

```yaml
# Sidecar pattern: MinIO as caching proxy
apiVersion: v1
kind: Pod
metadata: {name: spark-etl}
spec:
  containers:
  - name: spark
    image: spark:3.5
    env:
    - name: AWS_S3_ENDPOINT
      value: http://localhost:9000
  - name: minio-cache
    image: quay.io/minio/minio
    args: ["server", "/cache", "--address", ":9000"]
    env:
    - name: MINIO_ROOT_USER
      value: cacheuser
    - name: MINIO_ROOT_PASSWORD
      value: cachepass
```

## Key Configuration

```properties
# MinIO environment variables
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=minio-secret-key-change
MINIO_STORAGE_CLASS_STANDARD=EC:4
MINIO_SITE_REGION=us-east-1
MINIO_BROWSER=off
MINIO_PROMETHEUS_AUTH_TYPE=public

# Ceph RGW config (ceph.conf)
[client.rgw.rgw1]
rgw_frontends = beast port=7480
rgw_enable_usage_log = true
rgw_enable_ops_log = false
rgw_bucket_default_quota_max_size = 10T
rgw_multipart_min_part_size = 5242880
rgw_compression_type = zstd
```
