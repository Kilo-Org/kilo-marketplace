---
name: diagnose-airflow-exports
description: Review Airflow 3.2/3.3 DAG source and diagnose exported task incidents
  with DAG Doctor. Use for exported logs, pool waits, upstream failures or executor
  mismatch; live Airflow access and automatic fixes are outside this workflow.
metadata:
  category: development
  source:
    repository: https://github.com/founder-sweep/contentsweep-dag-doctor
    path: skills/diagnose-airflow-exports
    ref: main
    commit: 57c8bf20d8dab343293e67be17f5a46c69eac822
    license_path: LICENSE
  author: founder-sweep
---

# Diagnose exported Airflow evidence

Use the free local engine when source and logs should stay on the machine. Use the hosted workflow when the user wants a saved hosted diagnosis and authorizes the upload. Installing this skill does not install the engine or connect an MCP server.

Local setup: [official guide](https://mcp.contentsweep.ai/dag-doctor/docs), [wheel](https://mcp.contentsweep.ai/dag-doctor/download), [SHA256 manifest](https://mcp.contentsweep.ai/dag-doctor/downloads/manifest.json). Verify the wheel against the manifest and install it in a Python 3.12+ environment. CLI: `dagdoctor`; local stdio MCP: `dagdoctor-mcp`, tool `diagnose_airflow_dag`.

```sh
dagdoctor review dags/ --airflow-version 3.3.1 --format json
dagdoctor diagnose dags/ --runtime-context incident.json --format json
```

The context needs schema version `1.0`, Airflow version, DAG/run/task IDs, state, executor and task logs. Review exports for secrets before upload. Qualified fixtures cover 3.2.0 and 3.3.1; provider versions remain supplied context. Customer code is parsed without importing or executing it.

Read [the hosted workflow](references/hosted-workflow.md) before using the hosted MCP/API. It covers upload permission, the quote and credit boundary, retry identity, delivery and retention.

Deliver the verdict, evidence-linked cause or missing fields, coverage gaps, and a reviewable next step. A signature is evidence for investigation, not proof of root cause. An upstream-failure state does not prove a branch rule caused it. Confidence is a heuristic, not measured accuracy. Unsupported versions, unfamiliar failures and incomplete context must remain unresolved. Do not apply a suggested patch or connect to production without the user's separate instruction; syntax-checked suggestions have no runtime verification.
