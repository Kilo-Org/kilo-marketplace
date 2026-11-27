# Repository context

Generated from `tools/templates/repo-context.md`. Read only when repository context is
relevant and available for the requested workflow.

Read the existing `.rootly/config.json` service mapping. Prefer explicit service
IDs and path mapping; the legacy `.claude/rootly-config.json` is a fallback.
If mappings conflict or are absent, propose candidates and ask for confirmation
before claiming that a repository corresponds to a production service.

Read diffs, relevant history, ownership files, CI, and deployment records within
scope. A commit or merge time is not a deployment time. Config and feature flag
changes may be outside git. Do not infer approval, test results, deployment,
rollback readiness, or AI authorship from a diff alone. A clean working tree
does not exclude a committed branch, PR, or release awaiting deployment.

Without a repository, continue applicable Rootly analysis and identify the
missing code context. Never clone an unrelated repository, change files, check
out branches, or execute a runbook's remediation merely to enrich a brief.
