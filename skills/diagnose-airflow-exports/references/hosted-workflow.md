# Hosted DAG Doctor

Offer: https://mcp.contentsweep.ai/dag-doctor

Sign in with a verified email, activate DAG Doctor and create an organization key in the workspace. Connect a Streamable HTTP MCP client to `https://mcp.contentsweep.ai/v1/dag-doctor/mcp/` using `X-API-Key` or `Authorization: Bearer`. Store the key in the client's private credential configuration, never a URL or committed file. Missing authentication is a setup dependency; do not substitute an operator key or create a purchase.

After the user authorizes uploading the selected source/logs:

1. `upload_dag_bundle`: actual relative `.py` filenames mapped to source plus `runtime_context`, optional `logs`, `airflow_version`, and `suggest_patches`.
2. `preview_dag_bundle`: inspect support and coverage for `upload_id`.
3. `quote_dag_diagnosis`: obtain the product-specific quote for that upload. Read the DAG wallet and monthly cap.
4. Explain that one completed supported hosted diagnosis consumes one report, then use `start_dag_diagnosis` only within the user's spending authorization. Five trials per verified organization, then $20/20 reports; no subscription or automatic replenishment. Funding is a separate customer action. Missing context, unsupported inputs and platform failures consume none.
5. Save the original `quote_id`, `idempotency_key` and returned job ID privately before proceeding. After an uncertain response retry the same submission; do not mint another key. Quotes expire in ten minutes. If an uncertain submission cannot be resolved within a bounded retry/poll window, return the saved identity and pending state instead of starting another job.
6. Poll `get_dag_diagnosis` at most 90 times at one-second intervals. Read `get_dag_report` when completed and return the job's receipt, debit and result. Failed jobs require review, not automatic resubmission. Read/download calls add no credit charge.

Confirm tool names with the connected server's tool list. The corresponding HTTP flow is `POST /uploads`, `/preview`, `/quotes`, `/jobs`, then `GET /jobs/{id}` and `/jobs/{id}/report`, relative to `/v1/dag-doctor`. Preserve the same quote/key with HTTP retries too.

Limits: 1–200 Python files, 1 MB/file, 10 MiB source, 1 MiB logs, 12 MiB encoded bundle. No server paths or URLs in place of uploaded contents. Source/logs expire after 24h, reports after 7d, operational receipts after 30d; financial identities remain separately. Reports can contain source in suggested edits. Delete owned inputs/reports only when requested; deletion of pending input cancels work free. Keep downloaded results private unless sharing is authorized.
