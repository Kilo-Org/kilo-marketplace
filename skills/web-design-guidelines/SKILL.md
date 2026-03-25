---
name: web-design-guidelines
description: "Reviews UI code against the Web Interface Guidelines specification, fetching the latest rules and reporting violations in a terse file:line format. Use when asked to review UI code, check accessibility compliance, audit web design patterns, review UX implementation, or validate a site against interface best practices."
metadata:
  author: vercel
  version: 1.0.0
  argument-hint: <file-or-pattern>
  category: development
  source:
    repository: 'https://github.com/vercel-labs/agent-skills'
    path: skills/web-design-guidelines
---

# Web Interface Guidelines

Reviews UI code for compliance with the Web Interface Guidelines specification and reports violations in a terse `file:line` format.

## Workflow

### Step 1: Fetch Latest Guidelines

Fetch fresh guidelines before each review using WebFetch:

```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

The fetched content contains all rules and the required output format.

### Step 2: Identify Target Files

When the user provides a file or glob pattern argument (e.g., `src/**/*.tsx`), read those files. If no files are specified, ask the user which files or pattern to review.

### Step 3: Audit and Report

Apply every rule from the fetched guidelines against the target files. Output each finding in the terse `file:line` format specified in the guidelines document.

## Example

**Prompt**: "Review my UI" with argument `src/components/Button.tsx`

**Process**: Fetches latest guidelines from the source URL, reads the specified component file, checks against all rules (accessibility, semantic HTML, interaction patterns, visual consistency), and outputs findings as `src/components/Button.tsx:42 — missing aria-label on icon-only button`.

## Tips

1. **Run on components individually** for focused, actionable feedback rather than auditing an entire codebase at once
2. **Re-fetch guidelines each session** to pick up any upstream rule changes
3. **Combine with linting** — this skill catches design and UX issues that ESLint/Stylelint miss
