---
name: "aidp-object-storage"
description: "Read and write OCI Object Storage natively from an AIDP notebook using the `oci://` URI scheme. Use when the user mentions OCI Object Storage, \"oci://\", external volumes, external tables backed by Object Storage, CSV/Parquet/JSON/Delta files in a bucket, or wants to land data in OCI buckets. Auth is implicit via the workspace's IAM identity — no keys in the notebook."
metadata:
  category: data
  source:
    repository: "https://github.com/oracle-samples/oracle-aidp-samples"
    path: "ai/claude-code-plugins/oracle-ai-data-platform-workbench-spark-connectors/skills/aidp-object-storage"
    license_path: "LICENSE.txt"
---

# `aidp-object-storage` — OCI Object Storage native (`oci://`)

Read and write Object Storage data directly from Spark. The AIDP cluster's IAM identity is used automatically — no `OCI_CONFIG`, no API keys, no inline PEM.

## When to use
- Land or read CSV / Parquet / JSON / Avro / Delta files in an OCI bucket from Spark.
- Register an **External Volume** (`/Volumes/...`) backed by an OCI bucket.
- Define an **External Table** (`USING CSV/PARQUET/...`) over an `oci://` path.
- Mentioned: "oci://", "Object Storage bucket", "external volume", "external table".

## When NOT to use
- For **Iceberg** architecture and table design, defer to a licensed Iceberg specialist or the official Iceberg documentation; this skill only covers native OCI object paths.
- For **AWS S3** security and bucket configuration, use [`securing-s3-buckets`](../securing-s3-buckets/SKILL.md).
- For **Azure ADLS Gen2**, use [`azure-storage`](../azure-storage/SKILL.md).

## URI form
```
oci://<bucket>@<namespace>/<path>
```
The namespace is the tenancy's Object Storage namespace (OCI Console > Object Storage > Bucket Details).

## Direct read/write
```python
oci_path = "oci://my-bucket@mynamespace/folder/file"

# Write
df.write.mode("overwrite").option("header", True).format("csv").save(oci_path)

# Read
df_read = spark.read.option("header", True).format("csv").load(oci_path)
df_read.show()
```

Same pattern with `format("parquet")`, `format("json")`, `format("delta")`.

## External Volume (DDL)
Mount a bucket once, reference by Volume path forever:

```sql
CREATE EXTERNAL VOLUME IF NOT EXISTS default.default.ext_volume
LOCATION 'oci://my-bucket@mynamespace/';
```
Then:
```python
volume_path = "/Volumes/default/default/ext_volume/folder/file"
df.write.format("csv").option("header", True).save(volume_path)
spark.read.option("header", True).format("csv").load(volume_path).show()
```
Drop with `DROP VOLUME default.default.ext_volume`.

## External Table (DDL)
Register a table whose data lives in `oci://`:

```sql
CREATE TABLE IF NOT EXISTS default.default.ext_table (name STRING, age INT)
USING CSV
OPTIONS (path='oci://my-bucket@mynamespace/folder/file', delimiter=',', header='true');
```
Query like any Spark table:
```python
spark.sql("SELECT * FROM default.default.ext_table").show()
```
Drop with `DROP TABLE default.default.ext_table`.

## Gotchas
- **Auth is implicit** — the AIDP cluster's IAM identity is used. The user never types OCI keys. If reads fail with 404/403, the workspace identity lacks bucket privileges; fix in OCI IAM.
- **Namespace ≠ tenancy name.** The Object Storage namespace is a separate, immutable string. Find it in `OCI Console > Profile > Tenancy: <tenancy_name>` — the `object_storage_namespace` field.
- **External volume path is `/Volumes/<catalog>/<schema>/<volume>/...`**, NOT `oci://...`. Once a volume is registered, address files via the Volume path.
- **External table `path` option uses `oci://` directly**, not the Volume path. Both work; choose based on whether you want a re-mountable abstraction (Volume) or a simple direct reference (Table).
- **`/Workspace/...` is NOT for data.** It's a FUSE-mounted file system intended for notebooks/configs. For data files use `oci://` or `/Volumes/...`.

## References
- Official sample: [oracle-samples/oracle-aidp-samples → `getting-started/Access_Object_Storage_Data.ipynb`](https://github.com/oracle-samples/oracle-aidp-samples/blob/main/getting-started/Access_Object_Storage_Data.ipynb)
