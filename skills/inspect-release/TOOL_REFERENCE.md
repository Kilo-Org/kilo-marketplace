# Task-to-tool reference

Generated from the unchanged product MCP declarations. Parameter types and source hash are in TOOLS.json.

## inspect_repository

Inspect local Python/FastAPI, Docker and Actions evidence under the configured root.

Paths are relative. No target code runs; no network, uploads or remote
repositories. A ready result covers only shipped static rules. Check
complete, issues, coverage and findings before declaring a release ready.

- Task: Inspect local release evidence
- Prerequisites: Explicit configured root, relative contained path, compatible baseline if used
- Outputs: Bounded static findings, complete flag, issues and coverage
- Approval: Authorized read-only scan; no upload or target-code execution
- Credits: No credits consumed
- Retry: Safe unchanged read; timestamps can differ; ready is not runtime certification

