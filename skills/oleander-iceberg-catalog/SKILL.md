---
name: oleander-iceberg-catalog
description: >-
  Patterns for reading and writing oleander Iceberg catalog tables in Spark
  jobs, including naming conventions, write modes, and catalog hierarchy.
metadata:
  category: data
  source:
    repository: 'https://github.com/oleanderhq/skills'
    path: skills/oleander-iceberg-catalog
    license_path: LICENSE
    commit: e67bc57b5bdb98f68c29d034a0cc1bb71c973e61
---

# oleander Iceberg Catalog

Use this skill when reading from or writing to the oleander Iceberg catalog in a Spark job.

## Catalog hierarchy

Tables are addressed as `catalog.namespace.table`:

- **catalog**: always `oleander` for the managed Lakekeeper-backed catalog
- **namespace**: a logical grouping (e.g., `default`, `san_francisco`, `my_org`)
- **table**: the table name

By default, `default` and `telemetry` namespaces are available out of the box. The `telemetry` namespace contains oleander-managed data you can query directly (for example `oleander.telemetry.run_events`, `oleander.telemetry.traces`, and `oleander.telemetry.logs`).

Examples:

```bash
oleander.default.sf_311
oleander.san_francisco.district_stats
oleander.my_namespace.results
```

## Reading tables

Use `spark.table()` with the fully qualified name:

```python
df = spark.table("oleander.default.sf_311")
```

Never construct table paths as raw S3 URIs. Always use the catalog name so Iceberg metadata and lineage are tracked correctly.

## Writing tables

**Append** (add rows to an existing or new table):

```python
df.writeTo("oleander.my_namespace.my_table").append()
```

**Overwrite** (replace table contents):

```python
df.write.mode("overwrite").saveAsTable("oleander.my_namespace.my_table")
```

Use `writeTo(...).append()` for incremental pipelines. Use `write.mode("overwrite").saveAsTable(...)` when replacing full result sets each run.

## Prefer Spark writes over driver writes

Avoid collecting data to the driver and then writing from Python memory. Keep writes as Spark DataFrame operations so Iceberg handles the transaction, partitioning, and metadata correctly.

Bad:

```python
rows = df.collect()
# write rows from Python memory
```

Good:

```python
df.write.mode("overwrite").saveAsTable("oleander.my_namespace.my_table")
```

## Parameterize table names

Accept table names as arguments or environment variables so scripts are reusable:

```python
import os, argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input-table", default="oleander.default.sf_311")
parser.add_argument("--output-catalog", default="oleander.my_namespace")
args = parser.parse_args()

df = spark.table(args.input_table)
df.write.mode("overwrite").saveAsTable(f"{args.output_catalog}.results")
```

## Namespace conventions

- Use lowercase, underscore-separated names for namespaces and tables.
- Keep the namespace tied to the domain or data source, not the job name.
- Avoid deeply nested namespaces; one level is usually sufficient.

## Cache reused tables, then unpersist

If a table is read and used in multiple downstream transforms, cache it once and unpersist when done:

```python
df = spark.table("oleander.default.sf_311")
df.cache()
# ... multiple transforms ...
df.unpersist()
```

Do not cache tables that are only used once.
