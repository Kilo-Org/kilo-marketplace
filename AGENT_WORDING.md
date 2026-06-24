# PR 149 agent/product wording audit

## Scope and method

Compared `HEAD` (`9c60c49`) with base `c7d249097589c6c94808688969097a5048ff5890`. PR 149 adds 147 top-level skill directories and 1,261 files under `skills/`: 1,256 UTF-8/text files and 5 binary image files. The text review covered all 153 added `SKILL.md` files (some directories contain nested skills) and all 1,103 other added text resources/scripts/examples/manifests; the 5 PNG files were checked only as binary assets. `skills/marketplace.yaml` is modified but is marketplace indexing rather than bundled skill content, so it is outside the requested wording corpus.

The broad lexical scan found 1,023 lines in 189 files matching at least one deliberately over-inclusive token (`Codex`, `Claude`, `Anthropic`, `Cursor`, `Copilot`, `Gemini`, `OpenCode`, `OpenAI`, `AGENTS.md`, or related runtime variables). Most are false positives or technically required product references: database/API cursors; model/provider/API names; source-repository metadata; generated benchmark model IDs; vendor CLI modes; and documentation about integrations. The actionable set below is 38 lines in 8 files. A further 98 lines in 17 files are recorded as doubts/portability items rather than direct wording defects.

## Actionable agent-self/runtime wording

These references describe the agent currently executing the skill, its shell behavior, its project guidance, or its identity. They should use `Kilo` when the statement is specifically about this runtime, or `the agent` when runtime-neutral.

### `skills/databricks-core/SKILL.md`

- `skills/databricks-core/SKILL.md:45`: `## Claude Code - IMPORTANT` identifies the current runtime as Claude Code. Replace with `## Kilo - IMPORTANT` (or the more portable `## Agent shell behavior`). The following statement at line 47 is already product-neutral.
- `skills/databricks-core/SKILL.md:30`: `In sandboxed environments (Cursor IDE, containers)` unnecessarily uses Cursor as the exemplar for the executing environment. Replace with `In sandboxed environments (including Kilo cloud sessions and containers)` or simply `In sandboxed environments and containers`.

### `skills/databricks-core/data-exploration.md`

- `skills/databricks-core/data-exploration.md:264`: `## Claude Code-Specific Tips` -> `## Kilo-Specific Tips` or `## Agent Shell Tips`.
- `skills/databricks-core/data-exploration.md:266`: `Remember that each Bash command in Claude Code runs in a separate shell:` -> `Remember that each Bash command run by the agent may use a separate shell:`. This retains the operational reason for chaining/export guidance without asserting another product runtime.
- `skills/databricks-core/data-exploration.md:376`: `Always specify --profile in Claude Code` -> `Always specify --profile when commands run in separate shells` (preferred, because the recommendation follows from shell isolation rather than branding).

### `skills/databricks-core/databricks-cli-auth.md`

Eighteen lines encode Claude Code as the executing shell. Replace the product name consistently while preserving the command examples:

- `skills/databricks-core/databricks-cli-auth.md:16`: `## Claude Code Specific Behavior` -> `## Agent Shell Behavior`.
- `skills/databricks-core/databricks-cli-auth.md:18`: `When working in Claude Code` -> `When the agent runs commands in isolated shells`.
- `skills/databricks-core/databricks-cli-auth.md:37`: `Quick Reference for Claude Code` -> `Quick Reference for Isolated Agent Shells`.
- `skills/databricks-core/databricks-cli-auth.md:71`: `In Claude Code` -> `In isolated agent shells`.
- `skills/databricks-core/databricks-cli-auth.md:180`: replace the full lead-in `IMPORTANT FOR CLAUDE CODE USERS: In Claude Code ... See the Claude Code-specific guidance below.` with `IMPORTANT FOR AGENT RUNS: Commands may execute in separate shell sessions, so an export in one command may not persist to the next. See the agent-shell guidance below.`
- `skills/databricks-core/databricks-cli-auth.md:184`: `RECOMMENDED FOR CLAUDE CODE` -> `RECOMMENDED FOR AGENT RUNS`.
- `skills/databricks-core/databricks-cli-auth.md:194`: `In Claude Code` -> `For agent-run commands`.
- `skills/databricks-core/databricks-cli-auth.md:212`: `CRITICAL - Claude Code Users` -> `CRITICAL - Isolated Agent Shells`.
- `skills/databricks-core/databricks-cli-auth.md:214`: `Since each Bash command in Claude Code runs in a separate shell` -> `When each Bash command runs in a separate shell`.
- `skills/databricks-core/databricks-cli-auth.md:217`, `:226`, `:233`, `:241`: replace `in Claude Code` with `across isolated agent shells` or `for isolated agent shells`, matching each comment's grammar.
- `skills/databricks-core/databricks-cli-auth.md:321`: `In Claude Code, use --profile ...` -> `For agent-run commands, use --profile ...`.
- `skills/databricks-core/databricks-cli-auth.md:329`: `Alternatively in Claude Code` -> `Alternatively, in an agent-run command`.
- `skills/databricks-core/databricks-cli-auth.md:339`: `NOT for Claude Code` -> `NOT for isolated agent shells`.
- `skills/databricks-core/databricks-cli-auth.md:341`: `NOT in Claude Code` -> `NOT across separate agent commands`.
- `skills/databricks-core/databricks-cli-auth.md:376`: `Claude Code version` -> `Agent-shell version`.

Using `the agent`/`agent shell` is safer than a blind `Claude Code` -> `Kilo` replacement: Kilo command persistence can vary by tool and command composition, while the actual constraint being taught is process isolation.

### `skills/databricks-core/databricks-cli-install.md`

- `skills/databricks-core/databricks-cli-install.md:5`: `Sandboxed / IDE environments (Cursor, containers)` -> `Sandboxed agent / container environments`.
- `skills/databricks-core/databricks-cli-install.md:11`: `For Linux/macOS containers or Cursor` -> `For Linux/macOS containers or sandboxed agent environments`.
- `skills/databricks-core/databricks-cli-install.md:81`: `sandboxed IDEs (e.g. Cursor)` -> `sandboxed agent environments`.

These are generic installation constraints, not Cursor-specific behavior.

### `skills/databricks-jobs/SKILL.md`

- `skills/databricks-jobs/SKILL.md:37`: `create CLAUDE.md and AGENTS.md` imports Claude Code's project-instruction convention. Replace with `create AGENTS.md` and write the supplied content once. `AGENTS.md` is agent-neutral and is already described as guidance for agents; duplicating it into `CLAUDE.md` is unnecessary for Kilo.

### `skills/datarobot-data-preparation/SKILL.md`

- `skills/datarobot-data-preparation/SKILL.md:120`: `helper scripts that Claude can run directly` -> `helper scripts that the agent can run directly`.
- `skills/datarobot-data-preparation/SKILL.md:130`: `Claude can run this script directly` -> `The agent can run this script directly`.

### `skills/redshift/SKILL.md`

- `skills/redshift/SKILL.md:16`: `${CLAUDE_SKILL_DIR}/scripts/` is a Claude runtime variable and no such scripts are bundled in this imported skill. Replace the sentence with `Any scripts in the canonical skill are expected under the skill's scripts directory and require Python 3 plus the AWS CLI.` If an executable path is actually needed, derive it from the loaded skill directory rather than inventing `${KILO_SKILL_DIR}`; no Kilo variable with that name is established here.

### `skills/oracle-database/agent/client-identification.md`

The examples label the current agent as `claude-agent`, although the mechanism is generic Oracle client identification. Use `kilo-agent` for the concrete executing-agent examples, or `<agent-name>` where a generic placeholder is clearer:

- `skills/oracle-database/agent/client-identification.md:15`, `:99`, `:115`, `:132`, `:198`: replace `'claude-agent'` with `'kilo-agent'`.
- `skills/oracle-database/agent/client-identification.md:164`: example `e.g. 'claude-agent', 'my-chatbot'` -> `e.g. 'kilo-agent', 'my-chatbot'`.
- `skills/oracle-database/agent/client-identification.md:167`: example `'claude-agent:klrice:session-42'` -> `'kilo-agent:klrice:session-42'`.
- `skills/oracle-database/agent/client-identification.md:231`: example ``claude-agent:ra-ingest:task-042:step-3`` -> ``kilo-agent:rag-ingest:task-042:step-3``. This also fixes the apparent `ra-ingest`/`rag-ingest` typo.

## Technically required references to retain

These references name a real provider, model, API, integration, source, file format, CLI option, or compatibility target. They should not be rewritten to Kilo/the agent.

- **Source provenance:** repository/path values containing `claude`, `.claude`, `.codex`, `awesome-copilot`, or `gemini-cli-extensions` are historical source locations required by marketplace metadata. Examples: `skills/adf-master/SKILL.md:7`, `skills/aoti-debug/SKILL.md:8`, `skills/bootstrapping-agent/SKILL.md:8`, `skills/oracledb/SKILL.md:7`, and `skills/sql-server-table-reconciliation/SKILL.md:7`.
- **Models/providers/APIs:** Claude, Anthropic, Gemini, OpenAI, and Azure OpenAI names in product instructions are domain facts. Examples: `skills/databricks-model-serving/SKILL.md:22`, `skills/mlflow-onboarding/SKILL.md:30`, `skills/oracle-database/features/ai-profiles.md:30`, and `skills/dataset-transformation/references/sagemaker_dataset_formats.md:17`.
- **Vendor integration documentation:** client setup or integration catalogs correctly name supported products. Examples: `skills/bigquery-basics/references/mcp-usage.md:45`, `skills/oracle-database/sqlcl/sqlcl-mcp-server.md:115`, `skills/azure-databricks/integrations.md:452`, and `skills/neon-postgres/SKILL.md:68`.
- **Vendor feature/CLI literals:** Redis Copilot and Soda `copilot` are product/command names, not GitHub Copilot self-references. Retain `skills/redis-observability/SKILL.md:74`, `skills/soda-cli/SKILL.md:125`, and related Soda command-reference lines. Likewise database/programming `cursor` occurrences are technical terms, not Cursor IDE references.
- **Evaluation artifacts:** model IDs and providers in `skills/prefect/_scores.json:6`, `skills/redis-core/evals/core/baselines/aggregate-benchmark.json:10`, and related benchmark/matrix files are recorded data and should remain unchanged.
- **OpenAI interface manifests:** the 8 files named `agents/openai.yaml` are upstream interface metadata. Their paths are product-specific but do not claim the running agent is OpenAI. Retain unless the marketplace separately decides not to ship foreign harness manifests.
- **Agent SDK target:** `skills/bootstrapping-agent/SKILL.md:3`, `:87`, and `skills/bootstrapping-agent/agents/openai.yaml:3` explicitly generate PydanticAI/Claude SDK application code. Claude is the target being authored, not the current agent, so retain it.
- **Databricks model selection:** `skills/databricks-model-serving/SKILL.md:242` names Claude Sonnet and `-codex-max` endpoint/model families. Retain if those names are returned by the Databricks live endpoint list; they are model defaults, not runtime identity.

## Doubts and portability follow-ups

These are not clear `Claude` -> `Kilo` wording substitutions, but they deserve owner confirmation.

- **Runtime scripts (87 lines, 11 files):** `skills/knowledge-catalog-discovery/scripts/lookup_context.js:27-64` and its three sibling scripts, plus `skills/oracledb/scripts/execute_sql.js:32-69` and its six sibling scripts, branch on `GEMINI_CLI`, `CLAUDECODE`, and `CODEX_CI`, map Claude plugin options, and emit product-specific user-agent strings. The references are technically required for those compatibility branches, so they should not simply be renamed. Doubt: there is no explicit Kilo branch/user-agent and no documented Kilo option mapping. Confirm whether generic fallback `skills` is intentional; otherwise add a Kilo detection path using an actually supported Kilo environment signal. Repeated sibling files: `lookup_entry.js`, `search_aspect_types.js`, `search_entries.js`, `get_query_plan.js`, `list_active_sessions.js`, `list_invalid_objects.js`, `list_tables.js`, `list_tablespace_usage.js`, `list_top_sql_by_resource.js` at the same respective line blocks.
- **Harness metadata (4 lines, 1 file):** `skills/gcp-event-driven-architecture-review/metadata.json:7-10` lists Codex, Claude Code, Cursor, and Gemini but not Kilo. These are compatibility declarations, not self-references. Doubt: because `other` is present at line 12, Kilo may already be covered; add `kilo` only if this metadata is consumed for explicit harness discovery.
- **BigQuery wording (2 lines, 2 files):** `skills/bigquery-basics/SKILL.md:79` advertises a Gemini CLI extension, and `skills/bigquery-basics/references/mcp-usage.md:45` documents Gemini CLI/Claude Code/Codex packaging. This appears technically accurate. Doubt: the skill tells Kilo users about remote MCP and product-specific packaging but gives no Kilo setup path; add Kilo instructions only if the referenced server can be configured in Kilo.
- **Cursor installation examples (3 lines, 2 files):** the Databricks Cursor references listed as actionable above could be defended as concrete IDE compatibility notes. They are marked actionable because the same sandbox constraints apply to Kilo and the text currently frames the guidance around another agent product. If preserving tested compatibility matrices is more important, retain Cursor and add Kilo rather than replacing it.
- **`CLAUDE.md` interoperability (1 line, 1 file):** some tools may intentionally generate both `CLAUDE.md` and `AGENTS.md` for cross-agent repositories. If that is the goal at `skills/databricks-jobs/SKILL.md:37`, rewrite it explicitly: `For cross-agent compatibility, create AGENTS.md and optionally mirror it to CLAUDE.md for Claude Code users.` Do not call both files essential for all agents.
- **Kilo shell semantics:** the Claude-specific Databricks advice assumes separate command shells. Kilo's Bash tool executes each tool call as a new process, but commands chained in one call share a shell. The proposed runtime-neutral wording describes that behavior without promising that every Kilo integration behaves identically.

## Coverage summary

- Added top-level skills reviewed: **147/147**.
- Added `SKILL.md` files reviewed: **153/153**.
- Added bundled text resources/scripts/examples/manifests reviewed: **1,103/1,103**.
- Added binary assets accounted for: **5/5** (not text-searchable).
- Broad candidate matches triaged: **1,023 lines across 189 files**.
- Recommended wording changes: **38 lines across 8 files**.
- Doubts/portability items: **98 lines across 17 files** (87 runtime-script lines in 11 files, plus 11 documentation/metadata lines in 6 files; two files overlap the actionable set).
- Confirmed OpenCode occurrences: **1**, at `skills/neon-postgres/SKILL.md:68`, a literal supported `--agent` value; no replacement recommended.
