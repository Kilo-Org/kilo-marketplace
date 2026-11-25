# Investigate and act on a finding

**Evidence.** Read the selected repository and finding with
`get_security_finding`. Compare the described path and recommendation with the
source and controls the host can actually inspect. For “has this been verified
at runtime?”, use `get_security_runtime_validation_capability`. If available,
pass its `findingIdentityId` as `finding_identity_id` to
`list_security_runtime_validations`. Inspect the relevant attempt with
`get_security_runtime_validation` and summarize the recorded outcome and
environment. An unavailable capability, absent attempt or null evidence
manifest leaves a gap. These tools read existing attempts.

**Tickets.** Check the finding's existing ticket status and links first.
`preview_security_finding_ticket` takes the repository, finding and requested
Jira or Linear destination. Show the draft title, destination, suggested
priority and actionable description. If the preview omits part of the draft,
compose that part from the finding and distinguish it from the returned fields.
A preview creates no ticket. If the user wants to file it, use the selected
tracker and team or project. Ask for the destination if neither the preview
nor the user supplies it. For a direct tracker write, include the finding ID
and check for an existing ticket there when possible. Report the returned
ticket ID or link; a tracker receipt alone does not establish a link back
from CodeRabbit. Without an authorized tracker, leave a ready-to-copy draft. For ticket
preview, fix and dismiss operations, the current tool schema requires
`finding_kind: "vulnerability"` even for a Deep Scan secret. The listing
filter for secrets is `finding_kind: "secret"`.

**Fixes.** For a request to *explain* a fix, give the recommendation.
For an authorized CodeRabbit fix, read the current fix status first and reuse
an existing task or PR. Request `fix_security_finding` once. Pending or running
means the service accepted work. Follow `get_security_finding` for the
result. If a response is lost, read the finding again before considering
another request.

**Disposition.** Use `set_security_finding_severity`,
`dismiss_security_finding` or `reopen_security_finding` when the user selects
that change. A lower triage priority alone does not justify dismissal. When
the user asks to record a dismissal reason, check for `dismiss_reason` in
the connected tool's schema before changing state. If the field is missing,
explain where the user can record the reason in the app.

**After a merge.** Use these actions only if the host actually advertises
them. For `resolve_security_finding`, identify the open finding and supply
the requested supporting context, such as the merged fix. For
`recheck_security_finding`, follow the selected finding's recorded attempt
to its outcome. If either tool is absent, report the existing state and
direct the user to that action in the app. Runtime validation history and
a new repository scan answer different questions.

**Security learnings.** If the user asks to teach future scans, `create_security_finding_learning` saves
suppression or severity feedback. Explain its future scope and use the
requested finding or repository scope. Editing the current finding and
saving a learning are independent actions. To inspect existing feedback, use
`list_security_learnings`. For a requested edit or deletion, use the selected
learning ID from the 100 most recent results. Use `update_security_learning`
to replace its text or `delete_security_learning` to remove it. Severity
calibration requires different previous and new severities and applies to the
finding. Report which future scans it applies to when the service supplies
that scope.

**Export.** For a CSV request, use `export_security_findings_csv`. Save the
first page's content, then append each continuation verbatim with identical
filters and limit. Only the first page supplies headers. Mark an interrupted
export as partial and give the final path only after the requested pages are
written. In a chat-only host, report the available delivery options.
