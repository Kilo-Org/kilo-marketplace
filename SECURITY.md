# Security Review: PR 149

## Executive summary

**Target:** `HEAD` (`9c60c49`) versus base `c7d249097589c6c94808688969097a5048ff5890` using the three-dot diff.

**Disposition: Changes requested.** The PR changes 1,352 files (1,347 added, 5 modified), adding 153 skills, 89 MCP definitions, 101 executable/source files, 21 dependency manifests/locks, 69 examples/evals/templates, and one workflow change. Primary risks are mandatory ingestion of mutable remote content into agent context, unpinned executable/skill installation, broad mutable MCP trust boundaries, and unsafe privileged/TLS/supply-chain examples.

No live private keys, AWS/GitHub/Google token patterns, or JWTs were detected. Credential-looking eval values appear synthetic. No Kilo commands or repository-level Kilo permission configuration were added. Severity totals: **3 High, 6 Medium, 2 Low, 5 informational/human-review concerns**.

## Findings

### HIGH-01: Mutable remote text is loaded as authoritative agent context without prompt-injection controls

**Evidence:** `skills/searching-mlflow-docs/SKILL.md:16-38` mandates fetching `https://mlflow.org/docs/latest/llms.txt` and mutable `.md` pages, verbatim, and `:48` rejects versioned paths. `skills/dynamic-tables-tutorial/SKILL.md:90-97` says to fetch Snowflake docs first and use them as source of truth. `skills/neon-postgres/SKILL.md:20-39` mandates current docs/`llms.txt`; `:294-301` fetches or installs another remote skill. `skills/adf-master/SKILL.md:116`, `skills/dataset-transformation/SKILL.md:49`, and Azure skills including `skills/azure-data-factory/SKILL.md:22` direct live documentation retrieval. `skills/airbyte-agent/SKILL.md:36,75-76` and `skills/airbyte-agent/references/connectors-execute.md:6` require remotely returned connector docs before execution.

**Impact:** Compromised first-party docs/CDN, connector content, or SaaS accounts can inject instructions after marketplace review. "Source of truth," mandatory-first, and verbatim directives encourage agents to obey remote prose, potentially exposing data/secrets or invoking tools and write-capable cloud operations.

**Remediation:** Treat fetched/MCP text strictly as untrusted data; explicitly ignore embedded instructions; delimit and summarize it before use; prevent it from selecting tools/URLs; allowlist host/path and redirects; cap size; prefer bundled reviewed references or immutable versions/digests; require explicit user intent for live retrieval and independent validation before executing copied commands.

### HIGH-02: Skills execute mutable packages, skills, archives, and images

**Evidence:** `skills/neon-postgres/SKILL.md:65,75-76,301` runs `neonctl@latest`, unpinned `add-mcp`, and `npx skills add`. `skills/microsoft-code-reference/SKILL.md:91`, `skills/microsoft-docs/SKILL.md:76`, `skills/query-tableau-data/README.md:30`, and `skills/chdb-datastore/README.md:8` use unpinned package/skill installs. `skills/oracle-database/devops/database-testing.md:17,700` clones a mutable branch/downloads `latest`; `skills/oracle-database/ords/ords-metadata-catalog.md:286` pipes mutable archive content into `tar`; multiple `skills/oracle-database/sqlcl/*.md` files download `sqlcl-latest.zip` without verification. `skills/oracle-database/containers/*.md`, `skills/oracle-database/ords/ords-architecture.md:226`, `skills/deploying-airflow/SKILL.md:134`, and `skills/flink-best-practices/SKILL.md:497` use mutable image tags. `skills/kafka-schema-registry/references/code-migration.md:307-309` specifies `latest` dependencies.

**Impact:** Upstream compromise, retagging, dependency confusion, or malicious install hooks can execute code with agent filesystem/environment/cloud credentials. Dynamic skill installation also mutates the instruction set without review.

**Remediation:** Pin exact versions plus integrity hashes, Git full SHAs, images by digest, and skills by reviewed commit. Use signed/versioned artifacts and separately authenticated SHA-256 verification. Inspect archive paths before extraction; never stream remote archives into extractors. Add CI policy rejecting `latest`, unversioned installers, and mutable branches in executable guidance.

### HIGH-03: MCP catalog contains unpinned launchers and broad mutable remote capabilities

**Evidence:** `mcps/neon/MCP.yaml:32,40,48,56,64` has five unpinned NPX paths and passes `NEON_API_KEY` as argv. `mcps/github/MCP.yaml:18-28` uses mutable image tag `:1.4.0`; `:41-44` retains unpinned legacy `@modelcontextprotocol/server-github` without read-only mode. Hosted MCPs can change independently. `mcps/databricks-sql/MCP.yaml:3` explicitly supports writes; `mcps/bigquery-mcp/MCP.yaml:3` and `mcps/gcp-pubsub/MCP.yaml:3` manage resources. `mcps/oci-api-mcp/MCP.yaml:3`, `oci-cloud-mcp`, `privilege-cloud-mcp`, `redis-mcp`, `vault-mcp`, and `qlik-sense-mcp` expose administrative/mutating capability governed mainly by backend IAM. `mcps/openapi-mcp/MCP.yaml:3` dynamically creates tools from mutable local/remote specifications.

**Impact:** MCPs are executable dependencies and sources of model-visible tool descriptions/results. A compromised package/host can prompt-inject, exfiltrate prompts/tool arguments, or exercise broad credentials. Secrets in argv can appear in process listings/diagnostics. Read-only labels are not boundaries unless server and backend IAM both enforce them.

**Remediation:** Remove unpinned/legacy options; use package versions or image digests; never pass secrets in argv; default to backend-enforced read-only credentials; separate write-capable definitions with per-operation approval; document hosted-server operator, retention, scopes, and mutation surface; treat MCP output as untrusted. Permit dynamic OpenAPI only from reviewed local/immutable digest-validated specs and reject redirects/private addresses.

### MEDIUM-01: Delta Sharing activation secrets are printed

**Evidence:** `skills/delta-sharing/SKILL.md:87-88,223` and `skills/delta-sharing/examples/external_data_sharing.py:47` print/serialize `recipient.activation_url`.

**Impact:** Bearer-like bootstrap URLs leak through terminal/chat/CI logs or telemetry, enabling unauthorized activation/data access.

**Remediation:** Store in mode-0600 file or secret manager, show only fingerprint, transmit out-of-band, use short expiry, and revoke on exposure.

### MEDIUM-02: TLS bypasses are normalized

**Evidence:** `skills/etl-integration-nifi/references/diagnostics.md:212,215,218` uses `curl -k`; `skills/data-distributed-storage/references/s3-compatible-configs.md:13` uses `verify=False`; Elastic skills/scripts expose `ELASTICSEARCH_INSECURE=true` (`skills/elasticsearch-esql/scripts/esql.js:25`, `skills/elasticsearch-file-ingest/scripts/ingest.js:63`).

**Impact:** MITM can steal credentials and alter data-platform responses/operations.

**Remediation:** Use private CA bundles and explicit CA-file options. If emergency bypass remains, require warning/confirmation, loopback restriction, and refuse credentials while verification is disabled.

### MEDIUM-03: Tutorial falls back to `ACCOUNTADMIN`

**Evidence:** `skills/dynamic-tables-tutorial/SKILL.md:126` and `references/LESSONS.md:15` select Snowflake `ACCOUNTADMIN` before creating/loading resources.

**Impact:** Highest-role execution magnifies mistakes and prompt injection.

**Remediation:** Require a dedicated least-privilege tutorial role/database/warehouse; provide separately reviewed administrator setup rather than fallback.

### MEDIUM-04: Destructive operations lack uniform confirmation boundaries

**Evidence:** Added content includes DROP/TRUNCATE/DELETE, migrations, secret deletion, and cloud administration. `skills/kafka-streams-programming/scripts/teardown.sh:89` recursively deletes state. `skills/vault-api/SKILL.md:127` has good typed-confirmation controls, but they are not consistently applied elsewhere.

**Impact:** Ambiguous requests or injected instructions can destroy local, database, or cloud state.

**Remediation:** Marketplace-wide policy: inspect/show exact target, verify backup/recovery, dry-run by default, require typed confirmation for irreversible actions, canonicalize deletion paths, and reject empty/root/home targets.

### MEDIUM-05: Write-privileged workflow uses mutable action tags (pre-existing)

**Evidence:** `.github/workflows/package-skills.yml:15` grants `contents: write`; `:21,45` use `actions/checkout@v4` and `softprops/action-gh-release@v2`. The PR itself only changes packaging at `:32` to exclude evals.

**Impact:** Moved/compromised action tags could use the token to alter releases.

**Remediation:** Pin full action SHAs and narrow write permission. Excluding evals is security-positive.

### MEDIUM-06: Realistic example credentials may become unsafe defaults

**Evidence:** `skills/kafka-streams-programming/evals/evals.json:44`, `skills/query-tableau-data/docs/api/AUTH.md:103`, `skills/cognito/SKILL.md:124`, `skills/oracle-database/devops/database-testing.md:633-654`, and `skills/oracle-database/devops/schema-migrations.md:677` contain synthetic token/password-like values.

**Impact:** Copy/paste into reachable systems and scanner noise; realistic values can hide future leaks.

**Remediation:** Use unmistakable `<REQUIRED_SECRET>` placeholders/reserved `.invalid` domains and fail if placeholders remain.

### LOW-01: Parent-directory `.env` discovery can load unintended credentials

**Evidence:** `skills/query-tableau-data/src/query_tableau_data_py/config.py:64-84` and `skills/tableau-dashboard-creator/scripts/query_postgresql.py:10-11` walk for `.env`. Generated Oracle/Dataplex Node wrappers load repository `.env` and pass inherited environment to child NPX.

**Impact:** Wrong/more privileged credentials can be selected and exposed to dependencies.

**Remediation:** Require explicit or skill-local env files and pass allowlisted child variables only.

### LOW-02: Read-only claims depend on unverified upstream flags

**Evidence:** Numerous MCP configs set `READ_ONLY_MODE`, `*_ALLOW_WRITE=false`, `--read-only`, or tool allowlists, but upstream implementations are not in this PR.

**Impact:** Ignored/changed flags can expose writes.

**Remediation:** Integration-test tool enumeration and representative denied writes with disposable accounts; enforce read-only backend roles independently.

## Uncertain concerns requiring human review

1. Confirm `skills/cortex-code/scripts/execute_cortex.py:20-41` wildcard/blocklist semantics against the exact Cortex CLI; test aliases, shell indirection, case variants, and unknown future tools. Default CLI envelope is `RW`, though default prompt mode normally blocks tools pending approval.
2. Review privacy, retention, training use, tenancy, and incident response for every hosted MCP; prompts, schemas, queries, metadata, and rows may leave the local trust boundary.
3. Verify ownership/release signing/license/maintainer identity for community MCPs and third-party citations.
4. Sandbox-open/OCR Tableau `.twb`/PNG assets. No secret signature matched, but base64-like workbook blobs and image metadata were not deeply decoded.
5. Run OSV/Dependabot/Snyk and container scans. Exact pinning was checked statically; online CVE status was not.

## External URLs and prompt-injection assessment

The scan found **6,645 URL occurrences / 5,941 distinct URL strings** in added skill files. Most are passive citations. The following are **active** remote trust boundaries because instructions cause retrieval, loading, installation, or execution of mutable content:

| URL/pattern | Evidence | Assessment |
| --- | --- | --- |
| `https://mlflow.org/docs/latest/llms.txt` and `https://mlflow.org/docs/latest/[path].md` | `skills/searching-mlflow-docs/SKILL.md:16-38` | Mandatory mutable context; prompt-injection risk. |
| `https://docs.snowflake.com/en/user-guide/dynamic-tables-about` | `skills/dynamic-tables-tutorial/SKILL.md:90-97` | Mandatory source-of-truth fetch; prompt-injection risk. |
| `https://neon.com/docs/llms.txt`, `https://neon.com/docs/**/*.md`, and `.../SKILL.md` | `skills/neon-postgres/SKILL.md:20-39,294-301` | Mutable docs/skill instructions; prompt injection and supply chain. |
| AWS SageMaker live docs | `skills/dataset-transformation/SKILL.md:49` | Fixed first-party path but mutable context. |
| Airbyte `skills docs` | `skills/airbyte-agent/SKILL.md:36,75-76` | Remote Markdown/schema precedes connector execution; confused-deputy risk. |
| Context7 latest docs | `skills/adf-master/SKILL.md:116` | Third-party retrieval/provenance and injection risk. |
| Microsoft docs fetch/CLI | `skills/microsoft-code-reference/SKILL.md:52,80,91`; `skills/microsoft-docs/SKILL.md:56,76` | Mutable context plus unpinned CLI. |
| Azure ADF raw PowerShell on `main` | `skills/adf-master/references/cicd-deployment.md:156` | Mutable executable download. |
| Airflow stable Docker Compose | `skills/deploying-airflow/SKILL.md:113` | Mutable deployment config. |
| utPLSQL `latest`, Swagger `v5.x.x`, Oracle `sqlcl-latest.zip` | paths in HIGH-02 | Unverified mutable executable/archive content. |
| `npx skills add ...`, `neonctl@latest`, `add-mcp` | paths in HIGH-02 | Remote code and agent-instruction installation. |

All other extracted links are **passive citations or runtime/example endpoints** unless execution is separately requested: they do not instruct the agent merely by appearing in Markdown. Passive citations are not prompt injection by themselves, though browsing them later creates a remote-content boundary.

### Exhaustive added-skill URL host inventory

The table explicitly enumerates every lexically extracted hostname/template. Template/malformed labels are retained for reproducibility. Active hosts are marked; others are passive citations, schemas/namespaces, runtime endpoints, or examples.

| Host/template | URLs | Occ. | Files | Classification |
| --- | ---: | ---: | ---: | --- |
| `$(account).blob.core.windows.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `$auth0_domain` | 9 | 9 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${accountname}.blob.core.windows.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${accountname}.file.core.windows.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${accountname}.queue.core.windows.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${account}.blob.core.windows.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${auth0_domain}` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${process.env.databricks_workspace_id}.ai-gateway.cloud.databricks.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `${vaultname}.vault.azure.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `*` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `+:5000` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `.*\.example\.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `.*\.myapp\.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `0.0.0.0:8081` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `127.0.0.1:5000` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `127.0.0.1:8000` | 2 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `127.0.0.1:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `<malformed>` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `account.blob.core.windows.net` | 1 | 6 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `acme-prod.scs.splunk.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `action.co` | 5 | 5 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `action.co)**` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `adb-1111111111111111.10.azuredatabricks.net` | 1 | 6 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `adb-1234567890123456.7.azuredatabricks.net` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `ai.google.dev` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `airflow.apache.org` | 2 | 2 | 1 | **Mixed/active; see active table** |
| `airflow.example.com` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `aka.ms` | 2 | 3 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `api.dev.internal` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `api.example.com` | 8 | 15 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `api.external.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `api.getmembrane.com` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `api.github.com` | 3 | 3 | 3 | **Mixed/active; see active table** |
| `api.pagerduty.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `api.payment-gateway.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `api.production.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `app.datarobot.com` | 1 | 3 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `app.example.com` | 1 | 4 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `app.example.com,https:` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `app.snowflake.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `arrow.apache.org` | 9 | 9 | 9 | Passive citation, schema/namespace, runtime, template, or example |
| `arxiv.org` | 2 | 7 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `auth0.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `azure.github.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `azuremlschemas.azureedge.net` | 3 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `blogs.oracle.com` | 5 | 5 | 4 | Passive citation, schema/namespace, runtime, template, or example |
| `cdn.example.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `cdn.jsdelivr.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `central.sonatype.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `charts.minio.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `clickhouse.com` | 1 | 3 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `cloud.getdbt.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `cloud.google.com` | 24 | 31 | 9 | Passive citation, schema/namespace, runtime, template, or example |
| `cognito-idp.us-east-1.amazonaws.com` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `cognito-idp.{region}.amazonaws.com` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `community.qlik.com` | 2 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `community.snowflake.com` | 2 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `company-workspace.cloud.databricks.com` | 1 | 7 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `concert.sample.app` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `console.getmembrane.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `container-registry.oracle.com` | 20 | 39 | 20 | Passive citation, schema/namespace, runtime, template, or example |
| `containers.dev` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `custom-workspace.cloud.databricks.com` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `databricks-sdk-py.readthedocs.io` | 2 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `datacontract.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `dataframes.bigquery.dev` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `datarobot-public-api-client.readthedocs-hosted.com` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `dbc-2222222222222222.cloud.databricks.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `dev-workspace.databricks.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `dev12345.service-now.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `developer.microsoft.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.adbc-drivers.org` | 3 | 4 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.astral.sh` | 5 | 7 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.aws.amazon.com` | 19 | 26 | 16 | **Mixed/active; see active table** |
| `docs.cloud.google.com` | 17 | 18 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.columnar.tech` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.confluent.io` | 9 | 11 | 9 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.dagster.io` | 62 | 62 | 62 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.databricks.com` | 16 | 16 | 9 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.datadoghq.com` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.datarobot.com` | 4 | 6 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.djangoproject.com` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.docker.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.getdbt.com` | 6 | 9 | 4 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.github.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.gitlab.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.greatexpectations.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.jboss.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.liquibase.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.microsoft.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.nestjs.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.oracle.com` | 421 | 581 | 142 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.snowflake.com` | 28 | 30 | 7 | **Mixed/active; see active table** |
| `docs.soda.io` | 2 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.spring.io` | 2 | 3 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.sqlalchemy.org` | 2 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `docs.warpstream.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `documentation.red-gate.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `download.oracle.com` | 1 | 7 | 3 | **Mixed/active; see active table** |
| `duckdb.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `elasticsearch:9200` | 1 | 4 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `example-prod.scs.splunk.com` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `example.com` | 10 | 10 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `example2.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `fastapi.tiangolo.com` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `files.pythonhosted.org` | 104 | 104 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `fivetran.com` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `getmembrane.com` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `github.com` | 159 | 245 | 183 | Passive citation, schema/namespace, runtime, template, or example |
| `googleapis.dev` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `gorm.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `grafana.com` | 7 | 7 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `graph.microsoft.com` | 10 | 31 | 10 | Passive citation, schema/namespace, runtime, template, or example |
| `hbase.apache.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `help.qlik.com` | 14 | 19 | 5 | Passive citation, schema/namespace, runtime, template, or example |
| `help.splunk.com` | 11 | 13 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `hooks.slack.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `host:8443` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `host:port` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `hrportal.example.com` | 3 | 5 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `hub.getdbt.com` | 4 | 5 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `identity.oraclecloud.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `img.shields.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `insomnia.rest` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `jeffallan.github.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `jqplay.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `json-schema.org` | 1 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `jwt.ms` | 1 | 4 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `kafka.apache.org` | 1 | 4 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `learn.microsoft.com` | 4385 | 4444 | 37 | Passive citation, schema/namespace, runtime, template, or example |
| `learn.snowflake.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `linusdata.blog` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost` | 2 | 10 | 6 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:3000` | 2 | 18 | 8 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:4200` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:4566` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:5000` | 1 | 4 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:5001` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:5601` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:8000` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:8080` | 8 | 16 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:8081` | 3 | 21 | 12 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:8400` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:8443` | 3 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:8501` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:9000` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `localhost:9200` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `login.microsoftonline.com` | 12 | 28 | 9 | Passive citation, schema/namespace, runtime, template, or example |
| `management.azure.com` | 2 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `marczak.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `marquez:5000` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `maven.apache.org` | 2 | 9 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `mcp-toolbox.dev` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mcp.neon.tech` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mdformat.readthedocs.io` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `medium.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `microsoft.com` | 1 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `minio.datalake.internal:9000` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `minio{1...4}` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mlflow.org` | 14 | 15 | 2 | **Mixed/active; see active table** |
| `modelcontextprotocol.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mongodb.com` | 24 | 26 | 17 | Passive citation, schema/namespace, runtime, template, or example |
| `my-domain.auth.us-east-1.amazoncognito.com` | 2 | 6 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `myapp.azurewebsites.net` | 3 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `myapp.com` | 12 | 23 | 6 | Passive citation, schema/namespace, runtime, template, or example |
| `myapp.example.com` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mybatis.org` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mydatalake.dfs.core.windows.net` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `mykeyvault.vault.azure.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `myorg.grafana.net` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `myserver.example.com` | 16 | 20 | 4 | Passive citation, schema/namespace, runtime, template, or example |
| `mystorageaccount.blob.core.windows.net` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `neon.com` | 25 | 32 | 1 | **Mixed/active; see active table** |
| `nifi.example.com` | 1 | 4 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `node-oracledb.readthedocs.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `oauth.pstmn.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `oracle-base.com` | 17 | 18 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `oracle-samples.github.io` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `order-service` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `order-service:8080` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `orders.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `orders.example.com` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `oss.oracle.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `packages.confluent.io` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `packages.microsoft.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `packaging.python.org` | 3 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `pandas.pydata.org` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `pkg.go.dev` | 3 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `planetscale.com` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `portal.azure.com` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `pre-commit.com` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `prod-ca-a.online.tableau.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `prod-useast-b.online.tableau.com` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `prod-workspace.databricks.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `prometheus.internal:9090` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `prometheus.io` | 2 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `proxy:8080` | 1 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `psrc-xxxxx.region.provider.confluent.cloud` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `psrc-xyz.us-east-2.aws.confluent.cloud` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `pypi.org` | 2 | 8 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `python-oracledb.readthedocs.io` | 5 | 8 | 7 | Passive citation, schema/namespace, runtime, template, or example |
| `raw.githubusercontent.com` | 24 | 27 | 4 | **Mixed/active; see active table** |
| `redis.io` | 4 | 9 | 6 | Passive citation, schema/namespace, runtime, template, or example |
| `registry.terraform.io` | 4 | 4 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `s3tables` | 1 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `schemas.xmlsoap.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `scikit-learn.org` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `sequelize.org` | 3 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `server` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `sidecar:5000` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `site.online.tableau.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `skills.sh` | 2 | 2 | 2 | **Mixed/active; see active table** |
| `slack.com` | 1 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `smoke-prod.scs.splunk.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `sonar.mycompany.com` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `staging.example.com` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `status.azure.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `stedolan.github.io` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `sts.windows.net` | 2 | 3 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `supabase.com` | 15 | 16 | 14 | Passive citation, schema/namespace, runtime, template, or example |
| `support.oracle.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `surviving-node:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `tableau.example.invalid` | 4 | 4 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `tableau.yourcompany.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `techcommunity.microsoft.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `test` | 1 | 7 | 4 | Passive citation, schema/namespace, runtime, template, or example |
| `towardsdatascience.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `trivadis.github.io` | 1 | 3 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `typeorm.io` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `user-service` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `user-service:8080` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `utplsql.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-0.vault-internal:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-1.internal:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-1.internal:8201` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-2.internal:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-3.internal:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-leader:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-standby-1:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault-standby-2:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault.example.com` | 3 | 4 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `vault.example.invalid` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault.internal:8200` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `vault.vault:8200` | 1 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `wiki.example.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `wiki.postgresql.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.apache.org` | 3 | 14 | 13 | Passive citation, schema/namespace, runtime, template, or example |
| `www.astronomer.io` | 2 | 2 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `www.directionsonmicrosoft.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.elastic.co` | 21 | 25 | 6 | Passive citation, schema/namespace, runtime, template, or example |
| `www.example.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.learndapper.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.liquibase.org` | 3 | 13 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `www.mongodb.com` | 4 | 5 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `www.myapp.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.npmjs.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.nuget.org` | 2 | 2 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.oracle.com` | 18 | 28 | 22 | Passive citation, schema/namespace, runtime, template, or example |
| `www.orafaq.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.postgresql.org` | 21 | 22 | 22 | Passive citation, schema/namespace, runtime, template, or example |
| `www.rfc-editor.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.snowflake.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.sqlite.org` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.tableau.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.tableausoftware.com` | 1 | 33 | 32 | Passive citation, schema/namespace, runtime, template, or example |
| `www.tensorflow.org` | 16 | 16 | 2 | Passive citation, schema/namespace, runtime, template, or example |
| `www.thatjeffsmith.com` | 3 | 3 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `www.verylongurlkey.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `www.w3.org` | 5 | 17 | 12 | Passive citation, schema/namespace, runtime, template, or example |
| `www.youtube.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `x-force.example.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `your-app.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `your-workspace.cloud.databricks.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `{location}-aiplatform.googleapis.com` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `{my-server}` | 4 | 5 | 3 | Passive citation, schema/namespace, runtime, template, or example |
| `{storage_account}.blob.core.windows.net` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |
| `\|https:` | 1 | 1 | 1 | Passive citation, schema/namespace, runtime, template, or example |


## MCP, credentials, dependency, and workflow assessment

- **MCPs:** All 89 changed definitions were reviewed for commands, args, endpoints, headers, secrets, pins, mounts, and write controls. Many local MCPs are exactly pinned and explicitly read-only (for example `mcps/aws-api-mcp/MCP.yaml:17-24`, `mcps/azure/MCP.yaml:17`, `mcps/tokenlite-mysql-mcp/MCP.yaml:17-34`, and digest-pinned Vault images). Hosted endpoints avoid local package execution but remain mutable remote trust boundaries. Community servers require stronger provenance review.
- **Credentials:** No live key/token signatures were found. Templates use placeholders. Neon argv and Delta activation output are exceptions documented above. Binary assets were inventoried but not metadata/OCR-decoded.
- **Dependencies/images:** MCP launchers are mostly exact-version/commit/digest pinned; `skills/query-tableau-data/uv.lock` contains hashes. Remaining floating paths are concentrated in Neon/legacy GitHub MCP, skill installers, Oracle downloads/images, and generic examples. Exact pins do not replace transitive/CVE review.
- **Workflow:** The only change is `tar --exclude="${skill}/evals" ...`, reducing release contents. No PR-trigger or fork execution was added; quoting is adequate. Existing mutable actions/write token are MEDIUM-05.
- **Commands/permissions:** No new `.kilo` commands, agents, `kilo.json`, or repository-level permission rules were added. Eight skill-local `agents/openai.yaml` files were inspected as content metadata, not privileged Kilo configuration.

## Methodology

1. Verified worktree/commit and compared `c7d249097589c6c94808688969097a5048ff5890...HEAD`.
2. Enumerated all changed paths, status/modes/extensions and sensitive classes.
3. Reviewed the workflow diff and all five modified files.
4. Scanned all 89 MCP definitions and 1,261 added skill files; inspected all 153 added `SKILL.md` frontmatters (all had source repository/path and license metadata).
5. Statically reviewed 101 executable/source files for network/process/filesystem/secret/deserialization/path risks.
6. Scanned additions for private keys, common cloud/token/JWT patterns, generic secrets, destructive commands, privilege, TLS bypass, mutable installs/images, remote fetching, and prompt-injection boundaries.
7. Enumerated all textual added-skill URLs and distinguished active retrieval from passive citation.
8. Ran `git diff --check` successfully. No package, installer, MCP, code, image, or URL was executed.

## Coverage and limitations

**Covered:** all 1,352 changed files; all MCP configs; workflow; marketplace indexes; all added skill content/resources/scripts/examples/evals/templates; dependency manifests/locks; credentials, permissions, endpoints, defaults, and supply-chain patterns.

**Limitations:** Static review cannot prove upstream/hosted behavior. No dependencies were installed, no CVE/reputation lookup was performed, and no cloud/MCP permission tests were possible. Large reference corpora were covered by automated scans plus targeted manual review rather than semantic line-by-line validation of 294,290 additions. PNGs and embedded workbook blobs were not deeply decoded. URL extraction is lexical and includes template/parser artifacts.

## Merge gates

1. Resolve HIGH-01 through HIGH-03.
2. Add policy checks for immutable package/image/action refs, remote-fetch trust boundaries, secret-in-argv, TLS bypass, and write-capable MCP metadata.
3. Require human approval for hosted/community MCPs and skills that install packages/skills.
4. Run secret, OSV/dependency, container, and isolated read-only integration tests.
5. Re-review the remediated final diff.
