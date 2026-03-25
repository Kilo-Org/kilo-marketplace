---
name: langsmith-fetch
description: "Debugs LangChain and LangGraph agents by fetching and analyzing execution traces from LangSmith Studio via the langsmith-fetch CLI. Surfaces errors, tool-call sequences, token usage, and latency bottlenecks. Use when debugging agent behavior, investigating failures, analyzing memory operations, reviewing performance, or exporting trace sessions. Requires langsmith-fetch CLI and LANGSMITH_API_KEY."
metadata:
  category: development
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: langsmith-fetch
---

# LangSmith Fetch — Agent Debugging

Fetches and analyzes LangChain/LangGraph execution traces from LangSmith Studio to diagnose agent failures, performance issues, and behavioral problems.

## Prerequisites

```bash
pip install langsmith-fetch
export LANGSMITH_API_KEY="your_key"
export LANGSMITH_PROJECT="your_project"
```

Verify: `echo $LANGSMITH_API_KEY && echo $LANGSMITH_PROJECT`

## Core Workflows

### Quick Debug (Recent Activity)

**Trigger**: "What just happened?", "Debug my agent", "Show recent traces"

```bash
langsmith-fetch traces --last-n-minutes 5 --limit 5 --format pretty
```

Analyze and report: trace count, errors/failures, tools called, execution times, token usage. Highlight the root cause if failures are present.

### Deep Dive (Specific Trace)

**Trigger**: User provides a trace ID or says "investigate that error"

```bash
langsmith-fetch trace <trace-id> --format json
```

Report: agent goal, ordered tool-call sequence with pass/fail status, error messages, root-cause analysis, and suggested fix.

### Error Detection

**Trigger**: "Show me errors", "What's failing?"

```bash
langsmith-fetch traces --last-n-minutes 30 --limit 50 --format json > recent-traces.json
```

Search for errors/failures. Report: total vs. failed traces, error types with frequency, affected agents/tools, patterns, and remediation steps.

### Export Session

**Trigger**: "Save this session", "Export traces"

```bash
SESSION_DIR="langsmith-debug/session-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SESSION_DIR"
langsmith-fetch traces "$SESSION_DIR/traces" --last-n-minutes 30 --limit 50 --include-metadata
langsmith-fetch threads "$SESSION_DIR/threads" --limit 20
```

## Common Diagnostic Scenarios

| Symptom | Diagnostic steps |
|---------|-----------------|
| Agent not responding | Check if traces exist (tracing may be disabled); verify `LANGCHAIN_TRACING_V2=true` |
| Wrong tool called | Fetch trace, review tool selection reasoning, check tool descriptions |
| Memory not working | Search for memory/recall/store operations; verify tools are called and results used |
| Agent too slow | Export with `--include-metadata`; identify slowest tool calls and token-heavy iterations |

## CLI Reference

| Command | Use case |
|---------|----------|
| `--format pretty` | Human-readable output |
| `--format json` | Detailed analysis and parsing |
| `--format raw` | Piping to other commands |
| `--last-n-minutes N` | Time-based filtering |
| `--include-metadata` | Agent type, model, tags, environment |
| `--concurrent N` | Speed up large exports |

## Troubleshooting

- **No traces found**: Try longer timeframe (`--last-n-minutes 1440`), verify API key and project name, check `LANGCHAIN_TRACING_V2=true`
- **Project not found**: Run `langsmith-fetch config show`, then `export LANGSMITH_PROJECT="correct-name"`
- **Env vars not persisting**: Add exports to `~/.bashrc` or `~/.zshrc` and `source` the file
