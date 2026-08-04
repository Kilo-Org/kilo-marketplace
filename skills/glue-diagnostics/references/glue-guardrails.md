# Glue Anti-Misdiagnosis Guardrails

Read these guardrails BEFORE concluding on any AWS Glue issue.

## Guardrail 1: DPU Sizing Is Not One-Size-Fits-All
G.1X (16 GB) is sufficient for standard ETL. G.2X (32 GB) is needed for memory-intensive joins and aggregations. G.4X (64 GB) and G.8X (128 GB) are for ML transforms and massive datasets. Under-provisioning causes OOM errors; over-provisioning wastes cost. Always check the worker type and number of workers before diagnosing performance issues.

## Guardrail 2: Executor OOM and Driver OOM Have Different Root Causes
Executor OOM means individual data partitions are too large for the worker memory. Fix by repartitioning data or increasing worker type. Driver OOM means too much data is being collected to the driver node. Fix by avoiding collect(), reducing broadcast join thresholds, or removing groupBy operations that aggregate to the driver. Never apply the same fix to both.

## Guardrail 3: Job Bookmarks Require Explicit Code Integration
Job bookmarks only work with S3 and JDBC sources. The job script must call job.init() at the start and job.commit() at the end. Without these calls, bookmarks do not track progress. Resetting a bookmark causes full reprocessing of all data. Never claim bookmarks work automatically without code changes.

## Guardrail 4: Crawler Schema Changes Depend on Policy
Crawlers have a SchemaChangePolicy with UpdateBehavior (UPDATE_IN_DATABASE or LOG) and DeleteBehavior (DELETE_FROM_DATABASE, LOG, DEPRECATE_IN_DATABASE). UPDATE_IN_DATABASE overwrites existing schema. LOG only logs changes without modifying the table. Never assume crawlers automatically handle schema evolution correctly.

## Guardrail 5: Glue Connections Require Full VPC Networking
JDBC connections require a VPC, subnet, and security group. The subnet must have a route to the target database. For Glue service access, the subnet needs either a NAT gateway to the internet or VPC endpoints for Glue and S3. Security groups must allow self-referencing inbound rules for Glue ENIs. Never suggest JDBC connections work without VPC configuration.

## Guardrail 6: Job Timeout Defaults to 48 Hours
The default job timeout is 2880 minutes (48 hours). Jobs that hang or run inefficiently can silently consume DPUs for two full days. Always recommend setting an explicit timeout based on expected job duration. A stuck job at 10 DPUs for 48 hours costs significantly more than expected.

## Guardrail 7: Glue Version Determines Available Features
Glue 2.0 uses Spark 2.4 and Python 3.7. Glue 3.0 uses Spark 3.1 with optimized shuffle and auto-scaling. Glue 4.0 uses Spark 3.3 with Python 3.10 and Ray support. Libraries, APIs, and behaviors differ across versions. Never suggest features from one version when the job uses a different version.

## Guardrail 8: Data Catalog Is Not a Real-Time View of S3
The Glue Data Catalog stores metadata about tables and partitions. It is not automatically synchronized with S3. New partitions in S3 are not visible until a crawler runs or MSCK REPAIR TABLE / batch-create-partition is called. Never assume the Catalog reflects the current state of S3.

## Guardrail 9: Spark UI Is Only Available for Glue 2.0+
The Spark UI for debugging job performance is available for Glue version 2.0 and later. It must be enabled by setting --enable-spark-ui to true and providing an S3 path for Spark event logs. It is not available for Glue 0.9 or 1.0 jobs. Never reference Spark UI for legacy Glue versions.

## Guardrail 10: Partition Count Directly Impacts Performance
Too many small partitions (< 1 MB each) cause excessive S3 LIST API calls and task scheduling overhead. Too few large partitions (> 1 GB each) cause executor OOM and poor parallelism. Aim for 128 MB–512 MB per partition. Use coalesce() to reduce partitions or repartition() to increase them.

## Guardrail 11: Glue Studio Visual Editor Has Transform Limitations
Glue Studio's visual editor supports common transforms (ApplyMapping, Filter, Join, SelectFields) but does not support all PySpark/Scala operations. Complex logic like window functions, UDFs, or multi-step aggregations require custom code nodes or script-only jobs. Never claim all transformations are available in the visual editor.

## Guardrail 12: S3 Strong Consistency Does Not Eliminate All Race Conditions
S3 provides strong read-after-write consistency since December 2020. However, Glue Data Catalog metadata updates, crawler runs, and job bookmark state changes are separate operations that may not be immediately consistent with S3 object changes. Race conditions can still occur between concurrent jobs writing to the same S3 prefix and catalog updates.
