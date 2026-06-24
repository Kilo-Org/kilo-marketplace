# PR 149 Category Placement Review

**Review scope:** PR head `9c60c4951a0cec941a63d0e6bcaaad0c808aa33e` against base `c7d249097589c6c94808688969097a5048ff5890` in the clean worktree `/tmp/kilo/pr-149-review`.

## Executive assessment

- Reviewed every added or materially modified marketplace unit: **88 MCPs** (86 added, 2 materially modified existing entries) and **153 skills** (all added), for **241 total entries**.
- Found **58 questionable placements**: **10 MCPs** and **48 skills**. Consistent with the requested conservative standard, borderline cases are included rather than silently accepted.
- Assessed **183 placements as correct**: **78 MCPs** and **105 skills**.
- The dominant issue is that every added skill declares `data`. Many are genuinely data engineering, database, analytics, or ML/data-science skills, but API development, identity/security, documentation retrieval, and observability skills should not inherit `data` merely because this PR is data-heavy.
- Applied the repository MCP convention from `CONTRIBUTING.md`: `data` covers databases, storage, data engineering, and persistent knowledge; `development` covers code, developer platforms, and software tooling; `observability` covers application/system performance, logs, metrics, and incidents; `productivity` covers workflows and office/SaaS actions; `search` covers documentation and information retrieval. The same broad discovery semantics are the most coherent convention for skills.

## Questionable MCP placements

### `mcps/jupyter-mcp/MCP.yaml`
- **Current category:** `productivity`
- **Suggested category:** `data`
- **Rationale:** Its primary work is reading, editing, and executing Jupyter notebooks and kernels. Jupyter is a core data-science environment, and the base already places the existing `mcps/jupyter/MCP.yaml` entry in `data`; `productivity` hides it from the users most likely to seek it.

### `mcps/okta-mcp-server/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `development`
- **Rationale:** Okta administration is identity/security platform tooling, not a specialized business operation such as finance or contracts. Repository conventions put developer platforms and software tooling in `development`.

### `mcps/power-bi-modeling/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `data`
- **Rationale:** The tools inspect semantic-model metadata, validate DAX, and analyze BI models. This is analytics/data-modeling work used by analysts and data scientists, squarely within the repository definition of `data`.

### `mcps/power-bi-remote/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `data`
- **Rationale:** The server discovers semantic-model schemas and executes DAX over Power BI data. Its primary discovery audience is analytics and data practitioners, so `data` is more precise than generic business operations.

### `mcps/privilege-cloud-mcp/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `development`
- **Rationale:** Privileged-access account, safe, platform, and session administration is security/developer-platform tooling. It does not primarily implement a business-domain workflow.

### `mcps/pytorch-mcp-server/MCP.yaml`
- **Current category:** `development`
- **Suggested category:** `data`
- **Rationale:** Tensor operations, neural-network layers, losses, and autograd are machine-learning/data-science capabilities. The PR consistently places PyTorch, scikit-learn, TensorFlow, DataRobot, and MLflow skills in `data`; this MCP should follow that convention.

### `mcps/qlik-mcp/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `data`
- **Rationale:** Applications, datasets, data products, lineage, and Qlik analytics are data discovery and BI workloads. Analysts and data scientists are the primary users, making `data` the better navigation group.

### `mcps/qlik-sense-mcp/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `data`
- **Rationale:** Inspecting load scripts, fields, hypercubes, and app data plus reloads is BI/data-platform work. It should be discoverable with other analytics entries under `data`.

### `mcps/redis-cloud-mcp/MCP.yaml`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** The description explicitly says it does not access database data and instead manages cloud accounts, subscriptions, plans, payment methods, and provisioning. This is platform administration, best matched by `development`; retaining `data` is defensible only if all database-vendor control planes are intentionally grouped there.

### `mcps/tableau-mcp/MCP.yaml`
- **Current category:** `business`
- **Suggested category:** `data`
- **Rationale:** The server queries Tableau data and explores workbooks and published data sources. This directly serves analysts/data scientists and parallels other BI and semantic-model tools that belong in `data`.

## Questionable skill placements

### `skills/aoti-debug/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/apollo-graphql/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/aws-cognito-admin/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/aws-messaging-and-streaming/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It selects and configures application messaging/event services and delivery semantics. Although Kinesis/MSK can support data engineering, the skill spans SQS, SNS, EventBridge, and MQ and is primarily software architecture/tooling; in doubt, classify it as `development`.

### `skills/aws-sdk-python-usage/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/azure-compliance/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It performs cloud security/compliance audits and remediation guidance. No security category exists, and this is cloud engineering tooling rather than database/storage/data-science work.

### `skills/azure-key-vault/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/azure-rbac/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/bootstrapping-agent/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It generates SDK agent integration and tool-function code. Airbyte is data-oriented, but the skill’s direct output and user task are software development, so `development` is the stronger primary category.

### `skills/cheerio-parsing/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It guides Node.js DOM parsing and scraping implementation. This is software tooling; `data` is too broad even though parsed output is data.

### `skills/cognito/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/creating-secrets-using-best-practices/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/dashboarding/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/database-observability/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/dd-logs/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/dd-pup/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/elasticsearch-esql/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/entra-agent-id/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/entra-app-registration/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/fastapi-itechmeat/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/fastapi-martinholovsky/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/gcloud/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/gcp-event-driven-architecture-review/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It reviews application architecture across Pub/Sub, Eventarc, Tasks, Scheduler, and Workflows. Its primary purpose is software/system design, not persistent data or data science.

### `skills/gcp-iam/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/gcp-secret-manager/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/gemini-api/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It teaches developers to integrate an API/SDK and build multimodal applications. Model inputs and outputs do not make the integration itself a data-platform skill.

### `skills/graphql/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/integrate-anything/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `productivity`
- **Rationale:** It executes actions across connected SaaS applications (messages, tasks, record sync), which is workflow/productivity automation rather than a data-platform skill.

### `skills/microsoft-code-reference/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `search`
- **Rationale:** Its primary capability is retrieving documentation or code references, matching `search`; it does not primarily create, store, or transform data.

### `skills/microsoft-docs/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `search`
- **Rationale:** Its primary capability is retrieving documentation or code references, matching `search`; it does not primarily create, store, or transform data.

### `skills/newrelic-cli-skills/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/newrelic-cli-skills/alerts/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/newrelic-cli-skills/apm/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/newrelic-cli-skills/deployments/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/newrelic-cli-skills/diagnostics/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/newrelic-cli-skills/infrastructure/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/newrelic-cli-skills/nrql/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/okta-identity-integration-patterns/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/prometheus-addxai/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/redis-observability/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/searching-mlflow-docs/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `search`
- **Rationale:** Its primary capability is retrieving documentation or code references, matching `search`; it does not primarily create, store, or transform data.

### `skills/secrets-vault-manager/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/securing-s3-buckets/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

### `skills/splunk-ingest-processor-setup/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/splunk-spl2-pipeline-kit/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/troubleshoot-cassandra/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `observability`
- **Rationale:** Its primary workflow is monitoring, telemetry, diagnostics, logs/metrics, incident triage, or operational health, matching the repository definition of `observability` rather than generic data work.

### `skills/validating-json-data/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** It implements JSON Schema validation with a JavaScript library, TypeScript types, and project integration. This is developer tooling, not database/storage/data-science work.

### `skills/vault-api/SKILL.md`
- **Current category:** `data`
- **Suggested category:** `development`
- **Rationale:** Its primary purpose is API/application development, cloud or identity/security platform administration, SDK/CLI usage, or developer tooling. Under repository conventions that belongs in `development`, not the broad `data` bucket.

## Correct placements

The following entries fit their declared category under the repository’s broad, primary-purpose discovery convention. They were still individually checked; grouping them here avoids repeating identical “keep as-is” findings.

### MCPs assessed as correct

- **`data` (49):** `mcps/adls2-mcp/MCP.yaml`, `mcps/airbyte-agent-mcp/MCP.yaml`, `mcps/airflow-us-all/MCP.yaml`, `mcps/amazon-keyspaces-mcp/MCP.yaml`, `mcps/aws-data-processing/MCP.yaml`, `mcps/aws-redshift-mcp/MCP.yaml`, `mcps/awslabs-kinesis-mcp-server/MCP.yaml`, `mcps/azure-data-factory-consultant/MCP.yaml`, `mcps/bigquery-mcp/MCP.yaml`, `mcps/confluent/MCP.yaml`, `mcps/csv-tools-mcp/MCP.yaml`, `mcps/dagster-mcp/MCP.yaml`, `mcps/data-lineage-mcp/MCP.yaml`, `mcps/databricks-sql/MCP.yaml`, `mcps/datahub-mcp/MCP.yaml`, `mcps/datarobot-global-mcp/MCP.yaml`, `mcps/dbhub/MCP.yaml`, `mcps/dbt-us-all/MCP.yaml`, `mcps/dremio-mcp-lite/MCP.yaml`, `mcps/fivetran-mcp-server/MCP.yaml`, `mcps/gcp-pubsub/MCP.yaml`, `mcps/infoinlet-mongodb/MCP.yaml`, `mcps/knowledge-catalog-mcp/MCP.yaml`, `mcps/looker-toolbox/MCP.yaml`, `mcps/matillion/MCP.yaml`, `mcps/mcp-json-tools/MCP.yaml`, `mcps/mcp-snowflake-server/MCP.yaml`, `mcps/microsoft-data-api-builder/MCP.yaml`, `mcps/mlflow-mcp/MCP.yaml`, `mcps/mlflow-us-all/MCP.yaml`, `mcps/mongodb-mcp-server/MCP.yaml`, `mcps/neon/MCP.yaml`, `mcps/nifi-mcp-server/MCP.yaml`, `mcps/oci-database-tools-mcp/MCP.yaml`, `mcps/openmetadata-mcp/MCP.yaml`, `mcps/openmetadata-us-all/MCP.yaml`, `mcps/oracle-sqlcl-mcp/MCP.yaml`, `mcps/postgres-mcp-pro/MCP.yaml`, `mcps/prefect-mcp-server/MCP.yaml`, `mcps/purview-unified-catalog-mcp/MCP.yaml`, `mcps/redis-mcp/MCP.yaml`, `mcps/s3-tables-mcp/MCP.yaml`, `mcps/sap-bdc-mcp-server/MCP.yaml`, `mcps/snowflake-managed/MCP.yaml`, `mcps/snowflake-mcp-server/MCP.yaml`, `mcps/spark-sql-mcp/MCP.yaml`, `mcps/tokenlite-mysql-mcp/MCP.yaml`, `mcps/trino-mcp/MCP.yaml`, `mcps/unity-catalog-functions/MCP.yaml`
- **`development` (12):** `mcps/agent-platform-mcp/MCP.yaml`, `mcps/aws/MCP.yaml`, `mcps/aws-api-mcp/MCP.yaml`, `mcps/aws-serverless-mcp/MCP.yaml`, `mcps/azure/MCP.yaml`, `mcps/github/MCP.yaml`, `mcps/graphql-to-mcp/MCP.yaml`, `mcps/oci-api-mcp/MCP.yaml`, `mcps/oci-cloud-mcp/MCP.yaml`, `mcps/openapi-mcp/MCP.yaml`, `mcps/sylphlab-xml/MCP.yaml`, `mcps/vault-mcp/MCP.yaml`
- **`observability` (12):** `mcps/datadog-mcp-datadoghq/MCP.yaml`, `mcps/elastic-agent-builder-mcp/MCP.yaml`, `mcps/grafana-cloud-mcp/MCP.yaml`, `mcps/mcp-grafana/MCP.yaml`, `mcps/new-relic-ai-mcp/MCP.yaml`, `mcps/newrelic-mcp/MCP.yaml`, `mcps/prometheus-pab1it0/MCP.yaml`, `mcps/prometheus-tjhop/MCP.yaml`, `mcps/sagemaker-spark-troubleshooting-mcp/MCP.yaml`, `mcps/spark-history/MCP.yaml`, `mcps/splunk-mcp-server/MCP.yaml`, `mcps/vault-radar-mcp/MCP.yaml`
- **`search` (4):** `mcps/airbyte-knowledge-mcp/MCP.yaml`, `mcps/astronomer-docs-mcp/MCP.yaml`, `mcps/gitmcp-apache-atlas/MCP.yaml`, `mcps/spark-documentation/MCP.yaml`
- **`productivity` (1):** `mcps/membrane-cloud-mcp/MCP.yaml`

### Skills assessed as correct

All 105 skills below correctly use `data`: they primarily cover databases/storage, data engineering and orchestration, analytics/BI, data governance and quality, or ML/data-science workflows.

- `skills/adbc/SKILL.md`, `skills/adf-master/SKILL.md`, `skills/aidp-object-storage/SKILL.md`, `skills/airbyte-agent/SKILL.md`, `skills/airflow/SKILL.md`, `skills/apache-arrow/SKILL.md`, `skills/apache-hudi-lakehouse/SKILL.md`, `skills/authoring-dags/SKILL.md`, `skills/azure-data-factory/SKILL.md`, `skills/azure-data-share/SKILL.md`, `skills/azure-databricks/SKILL.md`, `skills/azure-event-hubs/SKILL.md`, `skills/azure-eventhub-py/SKILL.md`, `skills/azure-machine-learning/SKILL.md`, `skills/azure-storage/SKILL.md`
- `skills/azure-synapse-analytics/SKILL.md`, `skills/azureml-scaffolding/SKILL.md`, `skills/beam-concepts/SKILL.md`, `skills/bigquery-ai-ml/SKILL.md`, `skills/bigquery-basics/SKILL.md`, `skills/build-connector/SKILL.md`, `skills/cassandra/SKILL.md`, `skills/cdc-streaming-pipeline/SKILL.md`, `skills/chdb-datastore/SKILL.md`, `skills/collibra-chip/SKILL.md`, `skills/connecting-to-data-source/SKILL.md`, `skills/cortex-code/SKILL.md`, `skills/creating-data-lake-table/SKILL.md`, `skills/csv-query/SKILL.md`, `skills/csv-wrangling/SKILL.md`
- `skills/dagster-expert/SKILL.md`, `skills/dagster/SKILL.md`, `skills/data-catalog-and-discovery/SKILL.md`, `skills/data-distributed-storage/SKILL.md`, `skills/data-quality-frameworks-sickn33/SKILL.md`, `skills/database-redshift/SKILL.md`, `skills/databricks-core/SKILL.md`, `skills/databricks-dbsql/SKILL.md`, `skills/databricks-jobs/SKILL.md`, `skills/databricks-model-serving/SKILL.md`, `skills/databricks-pipelines/SKILL.md`, `skills/databricks-spark-structured-streaming/SKILL.md`, `skills/databricks-unity-catalog/SKILL.md`, `skills/dataplex-and-bigquery-governance/SKILL.md`, `skills/datarobot-data-preparation/SKILL.md`
- `skills/datarobot-feature-engineering/SKILL.md`, `skills/dataset-evaluation/SKILL.md`, `skills/dataset-transformation/SKILL.md`, `skills/db2-rhel/SKILL.md`, `skills/dbt-analytics-engineering/SKILL.md`, `skills/dbt-testing/SKILL.md`, `skills/delta-sharing/SKILL.md`, `skills/deploying-airflow/SKILL.md`, `skills/dynamic-tables-tutorial/SKILL.md`, `skills/elasticsearch-file-ingest/SKILL.md`, `skills/etl-integration-nifi/SKILL.md`, `skills/exploring-data-catalog/SKILL.md`, `skills/flink-best-practices/SKILL.md`, `skills/flink/SKILL.md`, `skills/gcs-lifecycle-policy/SKILL.md`
- `skills/glue-diagnostics/SKILL.md`, `skills/hadoop/SKILL.md`, `skills/hbase/SKILL.md`, `skills/ingesting-into-data-lake/SKILL.md`, `skills/io-connectors/SKILL.md`, `skills/jq-json-processing/SKILL.md`, `skills/kafka-schema-registry/SKILL.md`, `skills/kafka-streams-programming/SKILL.md`, `skills/knowledge-catalog-discovery/SKILL.md`, `skills/lookml-model/SKILL.md`, `skills/lookml-tests/SKILL.md`, `skills/mlflow-onboarding/SKILL.md`, `skills/mongodb-query-optimizer/SKILL.md`, `skills/mongodb-schema-design/SKILL.md`, `skills/mysql-patterns/SKILL.md`
- `skills/mysql/SKILL.md`, `skills/neon-postgres/SKILL.md`, `skills/nifi-flow-layout/SKILL.md`, `skills/oleander-iceberg-catalog/SKILL.md`, `skills/oracle-database/SKILL.md`, `skills/oraclecloud-data-handling/SKILL.md`, `skills/oracledb/SKILL.md`, `skills/powerbi-documentation/SKILL.md`, `skills/powerbi-mcp/SKILL.md`, `skills/prefect/SKILL.md`, `skills/purview-data-catalog/SKILL.md`, `skills/purview-data-map/SKILL.md`, `skills/pytorch-patterns/SKILL.md`, `skills/qlik-load-script/SKILL.md`, `skills/query-tableau-data/SKILL.md`
- `skills/redis-core/SKILL.md`, `skills/redshift/SKILL.md`, `skills/scikit-learn-best-practices/SKILL.md`, `skills/scikit-learn/SKILL.md`, `skills/senior-data-engineer/SKILL.md`, `skills/snowflake-expert/SKILL.md`, `skills/snowpipe-bcdr/SKILL.md`, `skills/soda-cli/SKILL.md`, `skills/spark-engineer/SKILL.md`, `skills/sql-server-table-reconciliation/SKILL.md`, `skills/supabase-postgres-best-practices/SKILL.md`, `skills/tableau-dashboard-creator/SKILL.md`, `skills/tensorflow-data-pipelines/SKILL.md`, `skills/tensorflow-model-deployment/SKILL.md`, `skills/udf-benchmark/SKILL.md`

## Coverage accounting

| Unit type | Added | Materially modified existing | Reviewed | Questionable | Correct |
|---|---:|---:|---:|---:|---:|
| MCP | 86 | 2 | 88 | 10 | 78 |
| Skill | 153 | 0 | 153 | 48 | 105 |
| **Total** | **239** | **2** | **241** | **58** | **183** |

For MCPs, “materially modified existing” refers to `github` and `neon`; both retain appropriate categories (`development` and `data`, respectively). Registry-only generated/aggregate changes were reconciled against the per-entry `MCP.yaml` and `SKILL.md` definitions, so entries are counted once.
