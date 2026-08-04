---
name: cortex-code
description: >-
  Routes Snowflake-related operations to Cortex Code CLI for specialized
  Snowflake expertise. Use when user asks about Snowflake databases, data
  warehouses, SQL queries on Snowflake, Cortex AI features, Snowpark, dynamic
  tables, data governance in Snowflake, Snowflake security, or mentions "Cortex"
  explicitly. Do NOT use for general programming, local file operations,
  non-Snowflake databases, web development, or infrastructure tasks unrelated to
  Snowflake.
metadata:
  author: Snowflake Integration Team
  version: 1.0.0
  compatibility: Requires Cortex Code CLI installed and configured
  category: data
  source:
    repository: 'https://github.com/snowflake-labs/subagent-cortex-code'
    path: skills/cortex-code
    license_path: LICENSE
    commit: f3557faf20581ece1c46ab1a10b8041a4bb88532
---

# Cortex Code Integration Skill

## Prerequisite

This marketplace skill is already installed; do not install or replace skill instructions dynamically. Cortex Code CLI must be installed and configured from the official Snowflake documentation. Verify the reviewed installation with:

```bash
which cortex
```

This skill enables your coding agent to leverage Cortex Code's specialized Snowflake expertise by intelligently routing Snowflake-related operations to Cortex Code CLI in headless mode.

## Architecture Overview

**Routing Principle**: ONLY Snowflake operations → Cortex Code. Everything else → your coding agent.

**Key Components**:
- Dynamic skill discovery at session initialization
- LLM-based semantic routing (not keyword matching)
- Security wrapper with approval modes (prompt/auto/envelope_only)
- Stateless Cortex execution with context enrichment
- Hybrid memory management
- Audit logging for compliance

## Security

The skill includes a security wrapper around Cortex execution with three approval modes:

### Approval Modes

1. **prompt** (default): High security
   - User shown approval prompt with predicted tools and confidence
   - User must approve before execution
   - No audit logging required
   - Best for: Interactive sessions, untrusted prompts, production

2. **auto**: Medium security
   - All operations auto-approved
   - Mandatory audit logging
   - Envelopes still enforced
   - Best for: Automated workflows, trusted environments

3. **envelope_only**: Medium security
   - No tool prediction (faster)
   - Auto-approved with audit logging
   - Relies on envelope blocklist only
   - Best for: Trusted environments, low latency needs

**Configuration**: Set in `config.yaml` in the skill's install directory, or via organization policy.

> **IMPORTANT — `config.yaml` is optional.** The skill ships only `config.yaml.example` as a template. If no `config.yaml` exists, the Python scripts apply safe defaults (`approval_mode: prompt`, `default_envelope: RO`). **Do not search, glob, or `ls` for `config.yaml` before executing** — `ConfigManager` handles this internally. Only read/create `config.yaml` if the user explicitly asks to change settings.

### Built-in Protections

- **Prompt Sanitization**: Automatic PII removal and injection detection
- **Credential Blocking**: Prevents routing when credential paths detected
- **Secure Caching**: SHA256-validated cache in `~/.cache/cortex-skill/`
- **Audit Logging**: Structured JSONL logs (mandatory for auto/envelope_only)
- **Organization Policy**: Enterprise override via `~/.snowflake/cortex/agent-skill-policy.yaml`

## Fast Path for Repeat Queries

**Session state is cached — do not re-run initialization steps on every query.**

Skip the following steps if they've already run in the current session:
- `discover_cortex.py` — output cached to `~/.cache/cortex-skill/cortex-capabilities.json`
- `route_request.py` — for obvious Snowflake queries (user says "Snowflake", "Cortex", "databases", "warehouse", etc.), you can skip routing and go straight to execution
- `cortex connections list` — the active connection doesn't change within a session; reuse it
- Any `config.yaml` / org-policy inspection — `ConfigManager` handles this (see note above)

**Minimal flow for a follow-up Snowflake query** (after the first query in a session):
1. (If `approval_mode: prompt`) ask user for approval
2. Call `execute_cortex.py` with the enriched prompt and envelope
3. Return results

That's it. Three steps — no re-discovery, no re-routing, no config inspection.

## Session Initialization

When this skill is first loaded:

### Step 1: Discover Cortex Capabilities
```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
$PYTHON scripts/discover_cortex.py
```

This script:
1. Runs `cortex skill list` to enumerate all available Cortex skills
2. Reads each skill's SKILL.md frontmatter and trigger patterns
3. Caches capabilities with `CacheManager` in the configured cache directory
4. Returns structured data about what Cortex can handle

Expected output: JSON mapping of skill names to their trigger patterns and capabilities.

### Step 2: Load Routing Context
The discovered capabilities are loaded into memory to inform routing decisions throughout the session.

## Workflow: Handling User Requests

### Step 1: Analyze Request with LLM-Based Routing

Before taking any action, analyze the user's request:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
$PYTHON scripts/route_request.py --prompt "USER_PROMPT_HERE"
```

This script:
1. Loads Cortex capabilities from cache
2. Uses LLM reasoning to classify the request
3. Returns routing decision with confidence score

**Routing Logic**:
- **Route to Cortex** if request involves:
  - Snowflake databases, warehouses, schemas, tables
  - SQL queries specifically for Snowflake
  - Cortex AI features (Cortex Search, Cortex Analyst, ML functions)
  - Snowpark, dynamic tables, streams, tasks
  - Data governance, data quality, or security in Snowflake context
  - User explicitly mentions "Cortex" or "Snowflake"

- **Route to your coding agent** if request involves:
  - Local file operations (reading, writing, editing local files)
  - General programming (Python, JavaScript, etc. not Snowflake-specific)
  - Non-Snowflake databases (PostgreSQL, MySQL, MongoDB, etc.)
  - Web development, frontend work
  - Infrastructure/DevOps unrelated to Snowflake
  - Git operations, GitHub, version control

### Step 2: Execute Based on Routing Decision

#### If routing is `coding_agent` (handle locally):
Handle the request directly using your agent's built-in capabilities. No Cortex involvement.

#### If routed to Cortex Code:
Proceed to Step 3.

### Step 3: Choose Security Envelope and Handle Approval

Before executing Cortex, the security wrapper handles approval based on configured mode.

#### Step 3a: Check Approval Mode

`security_wrapper.py` reads `approval_mode` from `config.yaml` internally — **do not inspect the config file yourself.** If `config.yaml` doesn't exist, the default is `prompt` mode.

- **prompt mode** (default): Requires user approval
- **auto mode**: Auto-approve with audit logging
- **envelope_only mode**: Auto-approve, no tool prediction

#### Step 3b: Handle Approval (if prompt mode)

If using prompt mode:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
$PYTHON scripts/security_wrapper.py \
  --prompt "ENRICHED_PROMPT" \
  --envelope "RW"
```

This will:
1. Predict required tools using LLM
2. Display approval prompt to user:
   ```
   Cortex Code needs to execute the following tools:

     • snowflake_sql_execute
     • Read
     • Write

   Envelope: RW
   Confidence: 85%

   Approve execution? [yes/no]
   ```
3. If approved, proceed to Step 3c
4. If denied, abort execution

#### Step 3c: Determine Security Envelope

Determine the appropriate security envelope based on the operation:
- **RO** (Read-Only): For queries and read operations - blocks Edit, Write, destructive Bash
- **RW** (Read-Write): For data modifications - allows most operations, blocks destructive Bash
- **RESEARCH**: For exploratory work - read access plus web tools
- **DEPLOY**: For deployment operations - blocks destructive Bash commands
- **NONE**: Custom blocklist via --disallowed-tools

### Step 4: Enrich Context for Cortex

Build an enriched prompt that includes:

**Current Agent Conversation Context**:
- Last 2-3 relevant exchanges from the current agent session
- Any Snowflake-specific details already discussed

**Recent Cortex Session Context**:
```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
$PYTHON scripts/read_cortex_sessions.py --limit 3
```

This reads the most recent Cortex session files from `~/.local/share/cortex/sessions/` to understand what Cortex recently worked on.

**Enriched Prompt Format**:
```
# Context from Current Session
[Recent relevant conversation history]

# Recent Cortex Work
[Summary from recent Cortex sessions]

# User Request
[Original user prompt]
```

### Step 5: Execute Cortex Code Headlessly

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
$PYTHON scripts/execute_cortex.py \
  --prompt "ENRICHED_PROMPT" \
  --connection "connection_name" \
  --envelope "RW" \
  --disallowed-tools "tool1" "tool2"
```

This script:
1. Invokes `cortex -p "prompt" --output-format stream-json`
2. Uses print mode for prompt delivery and stream JSON output for non-TTY parsing
3. Applies envelope-based security via `--disallowed-tools` blocklist for safety
4. Parses NDJSON event stream in real-time
5. Detects tool use events and execution results

**Key Insight**: The wrapper intentionally does not combine `-p` with `--input-format stream-json`. Cortex reserves `--input-format` for JSON stdin input; with closed stdin, that combination can emit only an init event and exit before processing the prompt.

**Security Envelopes**:
- **RO** (Read-Only): Blocks Edit, Write, destructive Bash commands
- **RW** (Read-Write): Blocks destructive operations like rm -rf, sudo
- **RESEARCH**: Read access plus web tools, blocks write operations
- **DEPLOY**: Deployment operations, blocks destructive Bash commands
- **NONE**: Custom blocklist via --disallowed-tools parameter

**Event Stream Handling**:
- `type: assistant` → Cortex's responses, display to user
- `type: tool_use` → Cortex is calling a tool
- `type: result` → Final outcome

### Step 6: Handle Permission Requests

With the security wrapper:
- **prompt mode**: User approves BEFORE execution (no mid-execution prompts)
- **auto/envelope_only modes**: Non-blocked tools are auto-approved in stream JSON mode

The security wrapper handles permission management through:
1. **Upfront approval** (prompt mode): User approves predicted tools before execution
2. **Audit logging** (auto/envelope_only): All operations logged to `audit.log` in the skill's install directory
3. **Envelope enforcement**: Tool blocklist still enforced via `--disallowed-tools`

### Step 7: Return Results to User

Format Cortex's output for the current session:
- Show SQL query results in readable format
- Display any generated artifacts
- Report success/failure status
- Provide relevant excerpts from Cortex's analysis

## Examples

### Example 1: Snowflake Query
**User says**: "Show me the top 10 customers by revenue in Snowflake"

**Routing**: → Cortex Code (Snowflake SQL query)

**Security Envelope**: RW (allows SQL execution)

**Cortex Action**:
1. Uses snowflake_sql_execute to run: `SELECT customer_name, SUM(revenue) as total FROM sales GROUP BY customer_name ORDER BY total DESC LIMIT 10`
2. Returns formatted results

**Result**: Table displayed to user with top 10 customers.

### Example 2: Local File Operation
**User says**: "Read the config.json file in this directory"

**Routing**: → your coding agent (local file operation)

**Agent Action**: Uses Read tool directly, no Cortex involvement.

**Result**: File contents displayed.

### Example 3: Data Quality Check
**User says**: "Check data quality for the SALES_DATA table"

**Routing**: → Cortex Code (Snowflake data quality - matches Cortex's data-quality skill)

**Security Envelope**: RW (allows SQL execution for analysis)

**Cortex Action**:
1. Runs data quality checks using its data-quality skill
2. Analyzes schema, null rates, duplicates, etc.
3. Generates quality report

**Result**: Comprehensive data quality report with recommendations.

## Important Notes

### Security Wrapper

The skill uses a security wrapper that provides:
- **Approval modes**: prompt (default), auto, envelope_only
- **Prompt sanitization**: Automatic PII removal and injection detection
- **Credential blocking**: Prevents routing when credential paths detected
- **Audit logging**: Mandatory for auto/envelope_only modes
- **Tool prediction**: LLM predicts required tools for approval prompt

**Configuration**: `config.yaml` in the skill's install directory, or via organization policy

### Headless Execution with Auto-Approval

When using auto or envelope_only modes:
- All tool calls are automatically approved without interactive prompts
- Works for built-in tools (Read, Write, Edit, Bash, Grep, Glob) and non-builtin tools (snowflake_sql_execute, data_diff, MCP tools)
- Uses print mode for prompt delivery and stream JSON mode for non-TTY output parsing
- Security is controlled via `--disallowed-tools` blocklist instead of interactive approval; use these modes only in trusted contexts

### Stateless Execution
Each Cortex invocation is stateless. Context must be explicitly provided via enriched prompts.

### Memory Boundaries
- **Your coding agent maintains**: Full conversation history, user preferences, project context
- **Cortex Code receives**: Only task-specific context for current operation
- **Cortex sessions are read**: For historical context enrichment only

### Security Envelope Strategy
Choose envelopes based on operation risk:
1. **Start with RO or RW**: Most operations fit here
2. **Use RESEARCH**: When web access is needed for exploratory work
3. **Use DEPLOY**: Only for deployment-style operations that require broader non-destructive tool access
4. **Use NONE with custom blocklist**: When fine-grained control is needed

### Performance Considerations
- Cortex skill discovery runs once per session (cached)
- Each Cortex execution adds ~2-5 seconds latency
- Use routing wisely to minimize unnecessary Cortex calls

## Troubleshooting

### Error: "Cortex CLI not found"
**Cause**: Cortex Code is not installed or not in PATH

**Solution**:
```bash
which cortex
# If not found, check installation: ~/.snowflake/cortex/
```

### Error: Approval prompt not appearing (or appearing unexpectedly)
**Cause**: Approval mode misconfiguration or organization policy override

**Solution**:
```bash
# Check approval mode in the agent-specific skill directory.
cat "$(dirname $(which cortex))/../skills/cortex-code/config.yaml" | grep approval_mode 2>/dev/null \
  || cat ~/skills/cortex-code/config.yaml | grep approval_mode

# Check organization policy (overrides user config)
cat ~/.snowflake/cortex/agent-skill-policy.yaml 2>/dev/null

# Expected:
#   prompt = shows approval prompts (default)
#   auto = auto-approves all operations
#   envelope_only = auto-approves, no tool prediction
```

### Error: "Prompt contains credential file path"
**Cause**: Prompt mentions paths matching credential allowlist (e.g., ~/.ssh/, .env)

**Solution**:
1. Remove credential references from prompt
2. Or customize allowlist in config.yaml if false positive

### Error: PII removed from prompts
**Symptom**: Emails, phone numbers replaced with placeholders

**Cause**: Automatic sanitization enabled by default

**Solution**: Disable if needed (not recommended):
```yaml
security:
  sanitize_conversation_history: false
```

### Error: "Permission denied" despite auto mode
**Cause**: Tool is in the --disallowed-tools blocklist for current envelope

**Solution**:
1. Check which envelope is being used (RO/RW/RESEARCH/DEPLOY)
2. If operation is safe, switch to a less restrictive envelope
3. Avoid `NONE` in auto/envelope_only modes; use a named envelope plus explicit custom blocklist if needed

### Error: Audit log not created
**Symptom**: No audit.log despite auto/envelope_only mode

**Solution**:
```bash
# Create the skill's install directory if missing and set permissions
# Path is agent-specific; use the configured cortex-code skill directory.
chmod 700 "$(cd "$(dirname "$0")/.." && pwd)"

# Verify audit_log_path in config.yaml within the skill directory
grep audit_log_path config.yaml
```

### Error: Tools still requiring approval
**Cause**: Approval mode, envelope blocklist, or stream JSON invocation is misconfigured

**Solution**: Ensure the wrapper invokes `cortex -p "..." --output-format stream-json` without `--input-format`, and that the configured envelope does not block the intended tool.

### Issue: Routing sends Snowflake query to your coding agent
**Cause**: Routing logic didn't detect Snowflake keywords

**Solution**:
1. Check if user mentioned "Snowflake" explicitly
2. Review routing script logic in `scripts/route_request.py`
3. Add more trigger patterns to routing context

### Issue: Cortex returns "Connection refused"
**Cause**: Snowflake connection not configured in Cortex

**Solution**:
```bash
cortex connections list
# Verify connection is active
# Check ~/.snowflake/cortex/settings.json for cortexAgentConnectionName
```

### Issue: Context enrichment too large
**Cause**: Including too much conversation history

**Solution**: Limit to last 2-3 relevant exchanges, summarize older context.

## Advanced: Custom Routing Rules

To customize routing beyond default logic, edit `scripts/route_request.py`:

```python
# Add custom patterns
FORCE_CORTEX_PATTERNS = [
    "snowflake",
    "cortex",
    "warehouse",
    "snowpark"
]

FORCE_CODING_AGENT_PATTERNS = [
    "local file",
    "git commit",
    "python script" # unless Snowpark
]
```

## References

See `references/` directory for:
- `cortex-cli-reference.md` - Full Cortex CLI documentation
- `routing-examples.md` - More routing decision examples
- `session-file-format.md` - Cortex session file structure
- `troubleshooting-guide.md` - Extended troubleshooting
