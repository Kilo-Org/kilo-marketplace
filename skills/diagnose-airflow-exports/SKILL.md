---
name: diagnose-airflow-exports
description: >-
  Review Airflow 3.2/3.3 DAG source and diagnose exported task incidents with
  DAG Doctor. Use for exported logs, pool waits, upstream failures or executor
  mismatch; live Airflow access and automatic fixes are outside this workflow.
metadata:
  category: development
  author: founder-sweep
  source:
    repository: 'https://github.com/founder-sweep/contentsweep-dag-doctor'
    path: skills/diagnose-airflow-exports
    license_path: LICENSE
    ref: main
    commit: 830e358b7568ae513a64ffe8100abe9aa7823be9
---

# Diagnose exported Airflow evidence

Use the free local engine when source and logs should stay on the machine. Use the hosted workflow when the user wants a saved hosted diagnosis and authorizes the upload. Installing this skill does not install the engine or connect an MCP server.

Compose with the existing `airflow` skill when available: use `diagnose-airflow-exports` for supplied exports without a live connection, and `airflow` for separately authorized live `af` CLI troubleshooting. This skill does not require `airflow` or grant live access.

Local setup: [official guide](https://mcp.contentsweep.ai/dag-doctor/docs), [wheel](https://mcp.contentsweep.ai/dag-doctor/download), [SHA256 manifest](https://mcp.contentsweep.ai/dag-doctor/downloads/manifest.json). This reviewed skill pins version `1.0.0`, filename `contentsweep_dag_doctor-1.0.0-py3-none-any.whl`, SHA256 `4c70e010790e9e1b18f285f8348ca2e6333c02428673d75bdc8f57b45372da4a`. Verify the downloaded bytes against that literal digest and require the manifest's version, filename and SHA256 to agree before installing in a dedicated Python 3.12+ environment. Stop on any mismatch; do not adopt a replacement digest from the download origin without reviewing an updated skill revision. Configure the client with the installed executable's absolute path. CLI: `dagdoctor`; local stdio MCP: `dagdoctor-mcp`, tool `diagnose_airflow_dag`.

```sh
dagdoctor review dags/ --airflow-version 3.3.1 --format json
dagdoctor diagnose dags/ --runtime-context incident.json --format json
```

The context needs schema version `1.0`, Airflow version, DAG/run/task IDs, state, executor and task logs. Review exports for secrets before upload. Qualified fixtures cover 3.2.0 and 3.3.1; provider versions remain supplied context. Customer code is parsed without importing or executing it.

Read [the hosted workflow](references/hosted-workflow.md) before using the hosted MCP/API. It covers upload permission, the quote and credit boundary, retry identity, delivery and retention.

Deliver the verdict, evidence-linked cause or missing fields, coverage gaps, and a reviewable next step. A signature is evidence for investigation, not proof of root cause. An upstream-failure state does not prove a branch rule caused it. Confidence is a heuristic, not measured accuracy. Unsupported versions, unfamiliar failures and incomplete context must remain unresolved. Do not apply a suggested patch or connect to production without the user's separate instruction; syntax-checked suggestions have no runtime verification.
