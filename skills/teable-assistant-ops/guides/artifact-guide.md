# Artifact Guide

Use artifacts for durable HTML pages, charts, or Markdown reports that should remain available in Teable. For an ephemeral answer shown only in the conversation, use an inline HTML block instead.

## Workflow

1. Build and inspect the content in a local file.
2. Run `artifact list` first, scoped by project and/or name search when useful. If the same deliverable already exists, update it instead of creating a duplicate.
3. If no match exists, `artifact create` once and retain the returned artifact ID.
4. For later revisions, restore the current source with `artifact get` if the local working file is unavailable; edit that file rather than recreating the artifact from memory.
5. `artifact update` the same artifact. Each update appends an immutable version, so earlier versions remain restorable.

## Content Rules

- HTML must be self-contained: inline CSS/JS and inline SVG are safe defaults.
- Do not reference external CDN URLs. If a library is needed, load an exact version from `/api/artifact-vendor/<pkg>@<version>/<file>`.
- Choose Markdown for text-first reports; use HTML for charts or interactive presentation.
- `artifact create` uses project context; `artifact update` and `artifact get` target the artifact ID directly.
- Use `artifact get --version <n>` when restoring a specific historical version rather than the current one.
