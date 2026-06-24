# PR 149 skill update verification

## Verdict

**Fail.** The supported updater completed 14 invocations with exit code 0, but 4 of the 147 top-level skills added by PR 149 were not updated because their configured source paths do not contain `SKILL.md`. The other 143 skills updated and produced substantial drift from the PR head. Regenerating `skills/marketplace.yaml` also produced a non-empty diff and exposed identity/category changes. PR 149 is neither fully updateable nor synchronized with current upstream content.

## Scope and environment

- PR: `https://github.com/Kilo-Org/kilo-marketplace/pull/149`
- Base: `c7d249097589c6c94808688969097a5048ff5890`
- Tested head: `9c60c4951a0cec941a63d0e6bcaaad0c808aa33e`
- Mutation worktree: `/tmp/kilo/pr-149-update-check`
- Report worktree: `/tmp/kilo/pr-149-review`
- Test date: 2026-06-24 UTC
- Environment: Linux; Node `v22.22.3`; npm/npx `10.9.8`; pnpm `11.8.0`; Python `3.10.12`; Git `2.54.0`; GNU `patch` absent.
- The update worktree was clean and at the PR head before dependency installation and updates. Its merge base with the requested base was exactly the requested base.
- The review worktree contains unrelated untracked `AGENT_WORDING.md`, `BINARIES.md`, `CATEGORIES.md`, and `SOURCE.md`; this report did not modify them.

## Supported workflow identified

- `bin/update-skills.ts` is the supported source updater. It accepts skill directory names, groups them by `metadata.source.repository`, sparse-checks out each configured source path, replaces each local skill, preserves marketplace-owned category/suggestions only when absent upstream, reinjects `metadata.source`, and copies `license_path` to local `LICENSE`.
- `bin/generate-skill-marketplace.ts` regenerates `skills/marketplace.yaml` from every top-level `skills/*/SKILL.md`.
- `.github/workflows/validate-skills.yml` installs `skills-ref` from `agentskills/agentskills` and validates every skill directory.
- Dependencies are declared under `bin/package.json`; there is no root `package.json`.

## Exact commands

All updater/generator commands and mutations ran only against `/tmp/kilo/pr-149-update-check`. Each command had a 120-second limit.

```bash
npm --prefix /tmp/kilo/pr-149-update-check/bin ci

/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts adbc adf-master aidp-object-storage airbyte-agent airflow authoring-dags deploying-airflow aoti-debug apache-arrow cassandra dagster prefect
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts apache-hudi-lakehouse data-catalog-and-discovery dataplex-and-bigquery-governance apollo-graphql cheerio-parsing graphql aws-cognito-admin aws-messaging-and-streaming aws-sdk-python-usage connecting-to-data-source creating-data-lake-table creating-secrets-using-best-practices exploring-data-catalog ingesting-into-data-lake securing-s3-buckets
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts azure-compliance azure-rbac azure-storage entra-agent-id entra-app-registration azure-data-factory azure-data-share azure-databricks azure-event-hubs azure-machine-learning azure-synapse-analytics
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts azure-eventhub-py azure-key-vault purview-data-catalog purview-data-map azureml-scaffolding beam-concepts io-connectors bigquery-ai-ml bigquery-basics gcloud gemini-api
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts bootstrapping-agent build-connector cdc-streaming-pipeline chdb-datastore cognito collibra-chip cortex-code csv-query csv-wrangling dagster-expert
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts dashboarding database-observability data-distributed-storage data-quality-frameworks-sickn33 database-redshift etl-integration-nifi databricks-core databricks-jobs databricks-model-serving databricks-pipelines databricks-spark-structured-streaming
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts databricks-dbsql databricks-unity-catalog datarobot-data-preparation datarobot-feature-engineering dataset-evaluation dataset-transformation db2-rhel dbt-analytics-engineering dbt-testing dd-logs dd-pup
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts delta-sharing dynamic-tables-tutorial elasticsearch-esql elasticsearch-file-ingest fastapi-itechmeat fastapi-martinholovsky flink-best-practices flink gcp-event-driven-architecture-review gcp-iam
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts gcp-secret-manager gcs-lifecycle-policy oraclecloud-data-handling glue-diagnostics hadoop hbase integrate-anything jq-json-processing kafka-schema-registry kafka-streams-programming
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts knowledge-catalog-discovery lookml-model lookml-tests microsoft-code-reference microsoft-docs mlflow-onboarding searching-mlflow-docs mongodb-query-optimizer mongodb-schema-design mysql-patterns pytorch-patterns
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts mysql neon-postgres newrelic-cli-skills nifi-flow-layout okta-identity-integration-patterns oleander-iceberg-catalog oracle-database oracledb powerbi-documentation powerbi-mcp
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts prometheus-addxai qlik-load-script query-tableau-data redis-core redis-observability redshift scikit-learn-best-practices scikit-learn secrets-vault-manager senior-data-engineer
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts snowflake-expert snowpipe-bcdr soda-cli spark-engineer splunk-ingest-processor-setup splunk-spl2-pipeline-kit sql-server-table-reconciliation supabase-postgres-best-practices tableau-dashboard-creator tensorflow-data-pipelines tensorflow-model-deployment
/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/update-skills.ts troubleshoot-cassandra udf-benchmark validating-json-data vault-api

/tmp/kilo/pr-149-update-check/bin/node_modules/.bin/tsx /tmp/kilo/pr-149-update-check/bin/generate-skill-marketplace.ts
```

CI-equivalent validator installation was attempted with:

```bash
python3 -m venv /tmp/kilo/pr-149-update-check/.validation-venv && /tmp/kilo/pr-149-update-check/.validation-venv/bin/pip install 'git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref'
```

It failed before installing `skills-ref` because this image lacks `ensurepip`/`python3.10-venv`. The `skills-ref validate` loop therefore could not run. The attempt left an incomplete untracked `.validation-venv/` in the update worktree; this is environment debris, not updater output.

## Per-skill results

### Source-path failures (4)

All four containing updater invocations returned overall exit code 0 despite logging per-skill errors. None of these four skill directories changed.

| Skill | Configured source | Result and root cause |
|---|---|---|
| `collibra-chip` | `https://github.com/collibra/chip`, path `SKILLS.md` | `no SKILL.md at upstream path, skipping`: path points to a file named `SKILLS.md`; updater requires a directory containing `SKILL.md`. |
| `newrelic-cli-skills` | `https://github.com/vince-winkintel/newrelic-cli-skills`, path `.` | `no SKILL.md at upstream path, skipping`: fetched repository root has no required `SKILL.md`. |
| `powerbi-mcp` | `https://github.com/devsaikan/powerbi-mcp-skill`, path `.` | `no SKILL.md at upstream path, skipping`: fetched repository root has no required `SKILL.md`. |
| `redshift` | `https://github.com/onsen-ai/redshift-skill`, path `.` | `no SKILL.md at upstream path, skipping`: fetched repository root has no required `SKILL.md`. |

The updater's final `Done. Updated N skill(s).` count is the number selected, not the number actually updated, and missing source paths do not make it exit nonzero.

### Updater-reported success (143)

Each skill below was fetched, replaced locally, had source metadata reinjected, and became dirty relative to the PR head:

`adbc`, `adf-master`, `aidp-object-storage`, `airbyte-agent`, `airflow`, `aoti-debug`, `apache-arrow`, `apache-hudi-lakehouse`, `apollo-graphql`, `authoring-dags`, `aws-cognito-admin`, `aws-messaging-and-streaming`, `aws-sdk-python-usage`, `azure-compliance`, `azure-data-factory`, `azure-data-share`, `azure-databricks`, `azure-event-hubs`, `azure-eventhub-py`, `azure-key-vault`, `azure-machine-learning`, `azure-rbac`, `azure-storage`, `azure-synapse-analytics`, `azureml-scaffolding`, `beam-concepts`, `bigquery-ai-ml`, `bigquery-basics`, `bootstrapping-agent`, `build-connector`, `cassandra`, `cdc-streaming-pipeline`, `chdb-datastore`, `cheerio-parsing`, `cognito`, `connecting-to-data-source`, `cortex-code`, `creating-data-lake-table`, `creating-secrets-using-best-practices`, `csv-query`, `csv-wrangling`, `dagster`, `dagster-expert`, `dashboarding`, `data-catalog-and-discovery`, `data-distributed-storage`, `data-quality-frameworks-sickn33`, `database-observability`, `database-redshift`, `databricks-core`, `databricks-dbsql`, `databricks-jobs`, `databricks-model-serving`, `databricks-pipelines`, `databricks-spark-structured-streaming`, `databricks-unity-catalog`, `dataplex-and-bigquery-governance`, `datarobot-data-preparation`, `datarobot-feature-engineering`, `dataset-evaluation`, `dataset-transformation`, `db2-rhel`, `dbt-analytics-engineering`, `dbt-testing`, `dd-logs`, `dd-pup`, `delta-sharing`, `deploying-airflow`, `dynamic-tables-tutorial`, `elasticsearch-esql`, `elasticsearch-file-ingest`, `entra-agent-id`, `entra-app-registration`, `etl-integration-nifi`, `exploring-data-catalog`, `fastapi-itechmeat`, `fastapi-martinholovsky`, `flink`, `flink-best-practices`, `gcloud`, `gcp-event-driven-architecture-review`, `gcp-iam`, `gcp-secret-manager`, `gcs-lifecycle-policy`, `gemini-api`, `glue-diagnostics`, `graphql`, `hadoop`, `hbase`, `ingesting-into-data-lake`, `integrate-anything`, `io-connectors`, `jq-json-processing`, `kafka-schema-registry`, `kafka-streams-programming`, `knowledge-catalog-discovery`, `lookml-model`, `lookml-tests`, `microsoft-code-reference`, `microsoft-docs`, `mlflow-onboarding`, `mongodb-query-optimizer`, `mongodb-schema-design`, `mysql`, `mysql-patterns`, `neon-postgres`, `nifi-flow-layout`, `okta-identity-integration-patterns`, `oleander-iceberg-catalog`, `oracle-database`, `oraclecloud-data-handling`, `oracledb`, `powerbi-documentation`, `prefect`, `prometheus-addxai`, `purview-data-catalog`, `purview-data-map`, `pytorch-patterns`, `qlik-load-script`, `query-tableau-data`, `redis-core`, `redis-observability`, `scikit-learn`, `scikit-learn-best-practices`, `searching-mlflow-docs`, `secrets-vault-manager`, `securing-s3-buckets`, `senior-data-engineer`, `snowflake-expert`, `snowpipe-bcdr`, `soda-cli`, `spark-engineer`, `splunk-ingest-processor-setup`, `splunk-spl2-pipeline-kit`, `sql-server-table-reconciliation`, `supabase-postgres-best-practices`, `tableau-dashboard-creator`, `tensorflow-data-pipelines`, `tensorflow-model-deployment`, `troubleshoot-cassandra`, `udf-benchmark`, `validating-json-data`, `vault-api`.

“Success” means updater execution success, not semantic acceptance; identity and marketplace problems below affect several successful updates.

## Source metadata and identity

Before updating, all 147 added top-level skills parsed and had non-empty `metadata.source.repository`, `metadata.source.path`, and `metadata.source.license_path`. Presence checks did not detect the four unusable paths.

After updating, source metadata remained populated, but current upstream frontmatter caused eight directory/name failures:

| Directory | Updated `name` | Impact |
|---|---|---|
| `aidp-object-storage` | missing | Generator logs `Added: undefined`; invalid/ambiguous identity. |
| `data-quality-frameworks-sickn33` | `data-quality-frameworks` | Directory ID and declared name diverge. |
| `dbt-analytics-engineering` | `using-dbt-for-analytics-engineering` | Directory ID and declared name diverge. |
| `fastapi-itechmeat` | `fastapi` | Directory ID diverges and collides with the next skill. |
| `fastapi-martinholovsky` | `fastapi` | Directory ID diverges and duplicates `fastapi-itechmeat`. |
| `hadoop` | `Hadoop` | Case-sensitive directory/name mismatch. |
| `oracle-database` | `db` | Directory ID and declared name diverge. |
| `prometheus-addxai` | `prometheus` | Directory ID and declared name diverge. |

The updater reinjects source metadata and conditionally preserves marketplace category/suggestions, but does not preserve the marketplace-local `name`. Imported aliases silently lose their local identity on update. The generator uses directory names as IDs, so it masks these mismatches rather than rejecting them.

Local license-file presence was confirmed for 145/147 added skills after updates. The two without local `LICENSE`, `LICENSE.txt`, or `COPYING` were unchanged failures `collibra-chip` and `redshift`. `newrelic-cli-skills` and `powerbi-mcp` already had local licenses despite being unupdateable.

## Dirty files and unexpected diffs

Final update-worktree state after updater, generator, and failed validator setup:

- 410 dirty entries: 248 tracked and 162 untracked files.
- Tracked: 245 modified and 3 deleted files.
- Tracked diff: 248 files, 7,091 insertions, 5,835 deletions.
- 143/147 added top-level skill directories changed; only the four source-path failures stayed unchanged.
- Most successful skills gained an untracked local `LICENSE`; other fetched files include references/scripts and Redis `.cursor-plugin/plugin.json` files.
- Five untracked `.validation-venv` entries are solely from failed validator setup.

Notable unexpected/destructive upstream drift:

- Deleted `skills/azure-machine-learning/references/documentation-catalog.md`.
- Deleted `skills/powerbi-documentation/references/documentation-specification.md` while content moved/expanded into `SKILL.md`.
- Deleted `skills/scikit-learn/references/workflows-and-examples.md`, replaced by multiple references/scripts.
- Large rewrites in `cortex-code`, `database-redshift`, `oracle-database`, `powerbi-documentation`, `scikit-learn`, `snowflake-expert`, and several scripts/references.
- Upstream categories moved `apache-arrow`, `cassandra`, `dagster`, and `prefect` from `data` to `data-ai`, and `gcp-event-driven-architecture-review` from `data` to `platform`. Upstream-supplied categories override marketplace-local categories.

The drift includes real current-upstream changes plus deterministic frontmatter reserialization by `gray-matter`; it is not formatting-only.

## Marketplace consistency

`generate-skill-marketplace.ts` exited 0 and reported 187 top-level skills, but changed `skills/marketplace.yaml` by 196 insertions and 130 deletions. The committed marketplace is not consistent after running the supported updater.

The generated diff contains current upstream description changes, category/order movement for the five skills listed above, `Added: undefined` for `aidp-object-storage`, and duplicate `Added: fastapi` logs for the two FastAPI directories. Stable directory-based IDs mask declared-name problems.

## Root causes and remediation

1. Correct/replace source locations for `collibra-chip`, `newrelic-cli-skills`, `powerbi-mcp`, and `redshift`; each path must be a directory containing `SKILL.md` at source HEAD.
2. Decide whether marketplace directory names or upstream `name` values are authoritative. If aliases are intentional, updater tooling must preserve/override local `name`; otherwise rename directories and resolve duplicate `fastapi` identity.
3. Re-import or update before merge, review the 143-skill upstream drift, and commit accepted skill/license changes with a freshly generated `skills/marketplace.yaml`.
4. Make `update-skills.ts` return nonzero for missing selected paths/`SKILL.md` and report successful versus skipped counts accurately.
5. Validate source reachability/path shape and directory-to-frontmatter name consistency; current metadata-presence checks and generation allow these failures.
6. Run `skills-ref validate` in an environment with `python3-venv`/`ensurepip`; this container could not complete that check.

No commits were created. All update and generation mutations remain isolated in `/tmp/kilo/pr-149-update-check`.
