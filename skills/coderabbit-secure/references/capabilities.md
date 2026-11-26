# What can I do with CodeRabbit Secure over MCP?

Check the connected server's catalog, schema and permissions for the requested action.

## Repositories and scans

| Request | In chat | In the dashboard |
| --- | --- | --- |
| Find a repository | `list_repositories` by owner/name or `get_repository` by provider ID. | Compare coverage and finding totals across repositories. |
| Price a scan | `get_security_scan_quote` returns the full-scan estimate, freshness and known credits. It can generate a missing estimate. Estimate the gap after credits and confirm spending before a paid start. | Force-refresh an existing quote, preview delta cost and baseline eligibility, or check, redeem and retry a first-scan offer. |
| Start and track | `start_security_scans` requests full or delta scans. Follow each accepted `codeScanId` with `get_security_scan` for status, coverage, findings and billed cost when available. `list_security_scans` searches run history. | View scan activity charts. |
| Recover a scan | `recover_security_scan` retries an eligible failed run or resumes a partial run. Follow the returned run ID. | |
| Manage schedules | `get_security_scan_schedule`, `save_security_scan_schedule` and `delete_security_scan_schedule` read, create, edit and remove schedules. Full scans use cron and timezone. Delta triggers include cron, coverage, commits or elapsed days. | Edit legacy multi-target schedules. |

See [scan operations](scans.md) for spending limits, delta fallback and schedule revisions.

## Findings and follow-up

| Request | In chat | In the dashboard |
| --- | --- | --- |
| Rank findings or secrets | `list_security_findings` pages by repository, scan, severity, state, kind and text, including saved secret validation status. `get_security_finding` reads location, evidence, recommendation, disposition and linked tasks, PRs or tickets. | Advanced filters, timeline, grouped views and source viewer. |
| Change a finding | `set_security_finding_severity`, `dismiss_security_finding` with an optional `dismiss_reason`, or `reopen_security_finding`. Where advertised, `resolve_security_finding` marks fixed with supporting context and `recheck_security_finding` requests a recheck. Check the connected schemas and permissions before acting. | Record a dismissal reason, mark fixed with supporting context, request a recheck or manage grouped findings. Use these dashboard actions when the connected tool or field is unavailable. |
| Request a fix | `fix_security_finding` starts an AI fix. Follow its task and PR through the finding detail. | |
| Draft a ticket | `preview_security_finding_ticket` drafts for Jira or Linear. A connected tracker can file the draft on request. | File through CodeRabbit's integrated workflow or configure ticket automation. |
| Read runtime evidence | `get_security_runtime_validation_capability` supplies the finding identity. `list_security_runtime_validations` lists attempts and `get_security_runtime_validation` reads an outcome and evidence manifest. | Start or cancel a validation and download evidence files. |
| Export findings | `export_security_findings_csv` exports filtered, paginated CSV. | JSON, SARIF or PDF where offered. |
| Maintain Security learnings | `create_security_finding_learning` saves suppression or severity feedback. `list_security_learnings` returns the 100 most recent. `update_security_learning` edits text and `delete_security_learning` removes a selected learning. | |

See [finding follow-up](findings.md) for ticket delivery, fix status, saved evidence and export handling.

## Other dashboard workflows

- Explore attack paths, posture maps and coverage trends in the dashboard. An individual scan or finding can supply narrower coverage or reachability evidence in chat.
- Inspect the PR Security inventory and remediation analytics in the dashboard. For a known GitHub Cloud PR, chat can read its feedback with `get_pull_request` including threads and its review state with `get_pull_request_review`.
- Configure Security checks, linked scan context, runtime verification, reachability zones and fix automation in repository Security settings. Change email delivery in Security notification preferences.
