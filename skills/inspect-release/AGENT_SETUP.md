# Inspector agent setup

Reviewed documentation: 2026-11-01. Examples contain placeholders, never live credentials.

## Install and authenticate

Use Python 3.12+ in a dedicated environment. On macOS, install the reviewed Inspector source checkout; the immutable 0.3.0 wheel is Linux-qualified. Trusted product repository: https://github.com/founder-sweep/production-readiness-inspector. From that reviewed checkout, choose your installed Python 3.12+ executable explicitly to create .venv (the Mac system Python may be older), then .venv/bin/python -m pip install '.[mcp]'. Enable the server in the client and review tool-permission prompts. Set the example's command to that environment's absolute Python path and replace every absolute-path placeholder deliberately. Never execute source or requirements from the target repository. No hosted key is needed for local MCP. Launch from a trusted workspace; a working directory is not a filesystem sandbox. Owned examples and installation source: https://github.com/founder-sweep/production-readiness-inspector.

Copy this reviewed skill bundle into .agents/skills/inspect-release/ for Codex or .claude/skills/inspect-release/ for Claude Code in the intended project. Copy the supporting AGENT_SETUP.md, TOOL_REFERENCE.md, TOOLS.json and client examples with it. Codex user-wide skills can instead live in ~/.agents/skills; Claude Code user-wide skills in ~/.claude/skills. Merge the Codex entry into the chosen isolated profile config.toml or reviewed ~/.codex/config.toml; merge Claude entries into project .mcp.json. Never overwrite unrelated settings. Review existing settings before merging a server entry; do not replace an entire configuration file. Restart or create a fresh client session and confirm tool discovery.

## Codex configuration

```toml
[mcp_servers."inspect-release"]
command = "/ABSOLUTE/TO/REVIEWED/ENV/bin/python"
args = ["-m", "mcp_products.inspector.mcp", "--root", "/ABSOLUTE/TO/AUTHORIZED/REPOSITORY"]
cwd = "/ABSOLUTE/TO/TRUSTED/WORKSPACE"
```

## Claude Code configuration

```json
{
  "mcpServers": {
    "inspect-release": {
      "type": "stdio",
      "command": "/ABSOLUTE/TO/REVIEWED/ENV/bin/python",
      "args": [
        "-m",
        "mcp_products.inspector.mcp",
        "--root",
        "/ABSOLUTE/TO/AUTHORIZED/REPOSITORY"
      ]
    }
  }
}
```

## Synthetic first task

Inspect examples/inspector/defective and examples/inspector/corrected in a trusted copy of the public examples. Compare actual findings and coverage. These are owned synthetic fixtures, not customer outcomes.

## Workflow

Install a reviewed Inspector release into a dedicated Python 3.12+ environment with its MCP dependencies. Choose the local repository root explicitly. Call inspect_repository with a relative path. Review complete, issues, coverage and findings before reporting the result. Compare a compatible baseline when requested. Keep the source local. Hosted history is optional and separate: preview its bounded metadata before any authorized submission.

## Recovery and credit effects

Stop on incomplete/error coverage, unsupported syntax, invalid baselines or a rejected path. A declared health route does not prove runtime health. Findings require review; never turn ready into production certification. An exact hosted retry is free; a new complete hosted report consumes one credit. Do not create a workspace, upload metadata or purchase credits without authorization.

## Price and bounds

Local scanning and stdio MCP are free. Three hosted trial reports; $19 USD per 100 optional hosted reports. No subscription.

Bounded static rules only. No target-code execution, repository upload, remote repository fetch, vulnerability certification or runtime-readiness guarantee.

Official client references: https://learn.chatgpt.com/docs/extend/mcp?surface=cli and https://code.claude.com/docs/en/mcp. Skill installation references: https://learn.chatgpt.com/docs/build-skills and https://code.claude.com/docs/en/skills.

Configuration, actual MCP execution and paid customer adoption are different outcomes. Qualification fixtures and internal accounts are not customers.

## Optional account and funding workflow

Create a workspace at https://inspector.contentsweep.ai/inspector?campaign=agent-skill#workspace and save its key privately as PRIVATE_NEW_KEY_FILE before using the commands below. The published 0.3.0 wheel supports submit/history; campaign attribution is captured by browser workspace creation.

Three hosted reports are free; $19 buys 100 reports. No subscription or automatic top-up. One new complete summary costs one report; exact retries reuse the original receipt. Raw source and evidence prose stay local. Preview relative paths, fingerprints and supported summary fields before submission.

```bash
.venv/bin/python -m mcp_products.inspector.cloud submit report.json --project client-api --key-file PRIVATE_NEW_KEY_FILE
.venv/bin/python -m mcp_products.inspector.cloud history --key-file PRIVATE_NEW_KEY_FILE
```

The workspace API key is the only credential; save it privately. There is no password/email recovery. Use an existing saved key on later runs. Never recreate a workspace to evade limits or print its key. Keep the same project only for matching scope/ruleset; changed coverage needs a new project.

Read GET https://inspector.contentsweep.ai/inspector/api/balance with Authorization: Bearer WORKSPACE_KEY. If funding is needed, open https://inspector.contentsweep.ai/inspector?campaign=agent-skill#workspace, restore the same key, and let the operator approve the $19 Checkout. No automatic purchases. Subsequent authorized submissions use its balance. Do not upload source repositories.

GET /inspector/api/reports/{id}/html with that same Bearer key exports the handoff. Hosted summaries expire after 30 days; financial and retry identities remain. An export reports caller-submitted evidence; the service does not independently rescan source. On 401 recover the saved credential; on 402 request funding; on failed/incomplete scans fix the input before submitting. Retrying an unchanged report must not create a second debit.
