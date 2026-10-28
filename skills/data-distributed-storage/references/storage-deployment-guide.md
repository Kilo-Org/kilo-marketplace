# Storage Deployment Guide

## HDFS Configuration

```xml
<!-- hdfs-site.xml — production NameNode HA -->
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>3</value>
  </property>
  <property>
    <name>dfs.blocksize</name>
    <value>268435456</value>
    <description>256MB block size for analytics</description>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>/data/hdfs/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/data/hdfs/datanode1,/data/hdfs/datanode2</value>
  </property>
  <property>
    <name>dfs.namenode.handler.count</name>
    <value>64</value>
  </property>
  <property>
    <name>dfs.datanode.handler.count</name>
    <value>16</value>
  </property>
  <property>
    <name>dfs.heartbeat.interval</name>
    <value>3</value>
  </property>
</configuration>
```

## MinIO Kubernetes Deployment

```yaml
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: datalake
spec:
  image: ${MINIO_IMAGE_REF:?Set MINIO_IMAGE_REF to quay.io/minio/minio@sha256:<reviewed-digest>}
  pools:
    - servers: 4
      volumesPerServer: 4
      volumeClaimTemplate:
        metadata:
          name: data
        spec:
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 4Ti
          storageClassName: fast-ssd
  mountPath: /export
  requestAutoCert: true
  s3:
    bucketDNS: false
  configuration:
    name: minio-config
  credsSecret:
    name: minio-creds
  podManagementPolicy: Parallel
  serviceMetadata:
    minioService: data-minio-hl
  console:
    image: quay.io/minio/console:v0.28.0
    replicas: 2
```

## Ceph Cluster Config

```yaml
[global]
  fsid = 7a4a3c2b-1d2e-3f4a-5b6c-7d8e9f0a1b2c
  mon_host = 192.168.1.10, 192.168.1.11, 192.168.1.12
  auth_cluster_required = cephx
  auth_service_required = cephx
  auth_client_required = cephx
  osd_pool_default_size = 3
  osd_pool_default_min_size = 2
  osd_pool_default_pg_num = 128
  osd_pool_default_pgp_num = 128
  osd_crush_chooseleaf_type = 1
  public_network = 192.168.1.0/24
  cluster_network = 192.168.2.0/24

[mon.a]
  host = mon-node1
  mon_addr = 192.168.1.10:6789

[mon.b]
  host = mon-node2
  mon_addr = 192.168.1.11:6789

[mon.c]
  host = mon-node3
  mon_addr = 192.168.1.12:6789

[osd]
  osd_journal_size = 10240
  osd_class_update_on_start = false
```

## Erasure Coding Profiles

```bash
# Ceph EC profile: tolerate 2 OSD failures with 6+2 encoding
ceph osd erasure-code-profile set ec-6-2 \
  k=6 m=2 \
  crush-failure-domain=host \
  directory=/usr/lib/ceph/erasure-code

ceph osd pool create ec-data-pool 128 erasure ec-6-2

# MinIO EC: environment variable
export MINIO_STORAGE_CLASS_STANDARD=EC:4
export MINIO_STORAGE_CLASS_RRS=EC:2
```
