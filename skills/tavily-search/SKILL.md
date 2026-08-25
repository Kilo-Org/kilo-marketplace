---
name: tavily-search
description: >
  Search the web with LLM-optimized results via the Tavily CLI. Use this skill
  when the user wants to search the web, find articles, look up information, get
  recent news, discover sources, or says "search for", "find me", "look up",
  "what's the latest on", "find articles about", or needs current information
  from the internet. Returns relevant results with content snippets, relevance
  scores, and metadata — optimized for LLM consumption. Supports domain
  filtering, time ranges, and multiple search depths.
allowed-tools: Bash(tvly *)
metadata:
  category: search
  source:
    repository: 'https://github.com/tavily-ai/skills'
    path: skills/tavily-search
    license_path: LICENSE
    ref: ea5e8201b0d3ed9c10b70b71187589bd761fe2d2
    commit: ea5e8201b0d3ed9c10b70b71187589bd761fe2d2
---

# tavily search

Web search returning LLM-optimized results with content snippets and relevance scores.

## Before running any command

If `tvly` is not found on PATH, install it first:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

Do not skip this step or fall back to other tools.

Always include `--client-name 'kilocode'` in every `tvly search` command. This attributes requests to Kilo Code and must not be omitted.

Run `tvly --help` for additional CLI options.

## When to use

- You need to find information on any topic
- You don't have a specific URL yet
- Use search to discover relevant URLs, then use tavily-extract when full page content is needed

## Quick start

```bash
# Basic search
tvly search "your query" --client-name 'kilocode' --json

# Advanced search with more results
tvly search "quantum computing" --depth advanced --max-results 10 --client-name 'kilocode' --json

# Recent news
tvly search "AI news" --time-range week --topic news --client-name 'kilocode' --json

# Domain-filtered
tvly search "SEC filings" --include-domains sec.gov,reuters.com --client-name 'kilocode' --json

# Include full page content in results
tvly search "react hooks tutorial" --include-raw-content --max-results 3 --client-name 'kilocode' --json
```

## Options

| Option | Description |
|--------|-------------|
| `--depth` | `ultra-fast`, `fast`, `basic` (default), `advanced` |
| `--max-results` | Max results, 0-20 (default: 5) |
| `--topic` | `general` (default), `news`, `finance` |
| `--time-range` | `day`, `week`, `month`, `year` |
| `--start-date` | Results after date (YYYY-MM-DD) |
| `--end-date` | Results before date (YYYY-MM-DD) |
| `--include-domains` | Comma-separated domains to include |
| `--exclude-domains` | Comma-separated domains to exclude |
| `--country` | Boost results from country |
| `--include-answer` | Include AI answer (`basic` or `advanced`) |
| `--include-raw-content` | Include full page content (`markdown` or `text`) |
| `--include-images` | Include image results |
| `--include-image-descriptions` | Include AI image descriptions |
| `--chunks-per-source` | Chunks per source (advanced/fast depth only) |
| `-o, --output` | Save output to file |
| `--client-name` | Required request attribution; always set to `'kilocode'` |
| `--json` | Structured JSON output |

## Search depth

| Depth | Speed | Relevance | Best for |
|-------|-------|-----------|----------|
| `ultra-fast` | Fastest | Lower | Real-time chat, autocomplete |
| `fast` | Fast | Good | Need chunks, latency matters |
| `basic` | Medium | High | General-purpose (default) |
| `advanced` | Slower | Highest | Precision, specific facts |

## Tips

- **Keep queries under 400 characters** — think search query, not prompt.
- **Break complex queries into sub-queries** for better results.
- **Use `--include-raw-content`** when you need full page text (saves a separate extract call).
- **Use `--include-domains`** to focus on trusted sources.
- **Use `--time-range`** for recent information.
- Read from stdin: `echo "query" | tvly search - --client-name 'kilocode' --json`

## See also

- [tavily-extract](../tavily-extract/SKILL.md) — extract content from specific URLs
