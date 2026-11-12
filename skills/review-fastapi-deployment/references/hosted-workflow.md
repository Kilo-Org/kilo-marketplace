# Hosted Deployment Fixer

Offer: https://mcp.contentsweep.ai/deployment-fixer

Verify email, activate this product and create an organization key in the workspace. Connect a Streamable HTTP MCP client to `https://mcp.contentsweep.ai/v1/deployment-fixer/mcp/` with `X-API-Key` or `Authorization: Bearer`. Keep keys in private client configuration. Missing access or credit is a dependency; do not use an operator key or buy credits automatically.

After permission to upload the selected source/configuration:

1. `upload_deployment_bundle` with `files` mapping relative names to text and optional `region`, `image_uri`, `service_name`.
2. `preview_deployment_bundle` with `upload_id`; inspect scope and explain limitations.
3. `quote_deployment_plan` for the upload, plus `deployment_fixer_wallet` to check product credit/cap.
4. Use `start_deployment_plan` with the quote and a stable `idempotency_key` only within the user's spending authorization. Five trials per verified organization, then $20/10 plans. A supported completed assessment costs one plan even when blocked. Unsupported, incomplete and failed evaluations are free. There is no subscription or automatic replenishment; funding stays a separate customer action.
5. Save quote/key/job privately. Uncertain responses must reuse that submission. Poll `get_deployment_plan` at most 90 times at one-second intervals. If unresolved, return the identity and pending state. Do not create replacement jobs to evade uncertainty or quote expiry (ten minutes).
6. `read_deployment_report` after completion; return the report, receipt and actual units consumed. Read/download/retry adds no additional debit. A failed job requires review before any new evaluation.

Confirm available tools from the connected server. HTTP equivalents are `POST /uploads`, `/preview`, `/quotes`, `/jobs`, then `GET /jobs/{id}`, `/jobs/{id}/report`, and `/jobs/{id}/download?format=json`, relative to `/v1/deployment-fixer`.

Accept 1–200 relative Python/Dockerfile/text configuration files; 1 MiB/file, 10 MiB source, 12 MiB encoded. Never upload private environment files or credentials. Inputs expire after 24h, reports after 7d, operational receipts after 30d; financial identities remain separately. Delete owned inputs/reports only on request; pending-input deletion cancels work free. Plans remain advisory: no AWS mutation, cost quote or runtime verification is supplied.
