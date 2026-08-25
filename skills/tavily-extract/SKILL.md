---
name: tavily-extract
description: >
  Extract clean markdown or text content from specific URLs via the Tavily CLI.
  Use this skill when the user has one or more URLs and wants their content,
  says "extract", "grab the content from", "pull the text from", "get the page
  at", "read this webpage", or needs clean text from web pages. Handles
  JavaScript-rendered pages, returns LLM-optimized markdown, and supports
  query-focused chunking for targeted extraction. Can process up to 20 URLs in a
  single call.
allowed-tools: Bash(tvly *)
metadata:
  category: search
  source:
    repository: 'https://github.com/tavily-ai/skills'
    path: skills/tavily-extract
    license_path: LICENSE
    ref: ea5e8201b0d3ed9c10b70b71187589bd761fe2d2
    commit: ea5e8201b0d3ed9c10b70b71187589bd761fe2d2
---

# tavily extract

Extract clean markdown or text content from one or more URLs.

## Before running any command

If `tvly` is not found on PATH, install it first:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

Do not skip this step or fall back to other tools.

Always include `--client-name 'kilocode'` in every `tvly extract` command. This attributes requests to Kilo Code and must not be omitted.

Run `tvly --help` for additional CLI options.

## When to use

- You have a specific URL and want its content
- You need text from JavaScript-rendered pages
- Use extract after tavily-search when you have specific URLs and need full page content

## Quick start

```bash
# Single URL
tvly extract "https://example.com/article" --client-name 'kilocode' --json

# Multiple URLs
tvly extract "https://example.com/page1" "https://example.com/page2" --client-name 'kilocode' --json

# Query-focused extraction (returns relevant chunks only)
tvly extract "https://example.com/docs" --query "authentication API" --chunks-per-source 3 --client-name 'kilocode' --json

# JS-heavy pages
tvly extract "https://app.example.com" --extract-depth advanced --client-name 'kilocode' --json

# Save to file
tvly extract "https://example.com/article" -o article.md --client-name 'kilocode'
```

## Options

| Option | Description |
|--------|-------------|
| `--query` | Rerank chunks by relevance to this query |
| `--chunks-per-source` | Chunks per URL (1-5, requires `--query`) |
| `--extract-depth` | `basic` (default) or `advanced` (for JS pages) |
| `--format` | `markdown` (default) or `text` |
| `--include-images` | Include image URLs |
| `--timeout` | Max wait time (1-60 seconds) |
| `-o, --output` | Save output to file |
| `--client-name` | Required request attribution; always set to `'kilocode'` |
| `--json` | Structured JSON output |

## Extract depth

| Depth | When to use |
|-------|-------------|
| `basic` | Simple pages, fast — try this first |
| `advanced` | JS-rendered SPAs, dynamic content, tables |

## Tips

- **Max 20 URLs per request** — batch larger lists into multiple calls.
- **Use `--query` + `--chunks-per-source`** to get only relevant content instead of full pages.
- **Try `basic` first**, fall back to `advanced` if content is missing.
- **Set `--timeout`** for slow pages (up to 60s).
- If search results already contain the content you need (via `--include-raw-content`), skip the extract step.

## See also

- [tavily-search](../tavily-search/SKILL.md) — find pages when you don't have a URL
