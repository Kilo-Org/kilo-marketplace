# Kilo Marketplace Review Guidance

Review the cumulative PR diff against its base, not only the latest commit. Use
`AGENTS.md` and `CONTRIBUTING.md` as policy. Review every added package file,
including scripts, hooks, references, assets, templates, notebooks, archives,
binaries, licenses, and local controls.

Reviews are read-only. Never edit, create worktrees, install dependencies,
regenerate, refresh, patch, package, or run commands that write locally or
remotely. Use repository content and existing CI/PR evidence. If evidence is
missing, state what is unverified and give the exact targeted maintainer command
or CI check.

## Coverage and sub-agents

Use no sub-agents for trivial docs, formatting, or generated-only changes; use
1-2 for a focused risk. Use all 6 for multi-package imports or changes combining
external sources, executable code, and assets. Shard them across:

1. provenance, licensing, metadata, generated entries, and update behavior;
2. scripts, hooks, templates, notebooks, archives, and binaries;
3. packaging, missing resources, links, and installation portability;
4. domain correctness of formulas, SQL, APIs, versions, and examples;
5. injection, secrets, subprocesses, network actions, cost, and consent;
6. activation quality, overlap, progressive disclosure, and token efficiency.

Sub-agents remain read-only and return path, line, severity, trigger, impact,
minimal fix, and confidence. The main reviewer verifies and deduplicates them.

## New or imported packages

Verify:

- A distinct real use case and precise activation description.
- Directory name, definition ID/name, marketplace ID, and archive name agree.
- `metadata.source.repository`, source path, attribution, and authorship match
  the actual canonical public source.
- Contributed third-party skills have `metadata.source.license_path` as required
  by `CONTRIBUTING.md`. Elsewhere accept the top-level `license` alternative from
  `AGENTS.md`; never require both. Verify the license exists upstream and covers
  every copied file.
- Categories are intentional, never importer placeholders such as `unknown`.
  `metadata.suggest_for.extension` contains only distinctive patterns.
- Every local and sibling-package reference resolves from the installed package
  with correct case; no promised dependency or resource is absent.
- Examples are independently correct: imports, syntax, schemas, units, edge
  cases, current APIs/versions, and semantics of claimed optimizations.
- Commands do not assume Claude/Codex/plugin layouts, `/mnt/user-data`, an
  upstream repository root, or an undeclared working directory.
- Destructive, production-changing, or paid actions require confirmation and
  safe defaults. Secrets use placeholders/environment variables and never enter
  commands, tracked files, generated output, or logs.
- Generated HTML, SQL, shell, and subprocess examples safely handle untrusted
  input. Archives and binaries are inspected rather than treated as opaque.

Use existing tests/CI to assess helpers beyond syntax: meaningful modes, artifact
schemas, output location, and overwrite behavior. Report missing behavioral
coverage; do not execute helpers that write.

## Skill quality

Keep `SKILL.md` focused on activation, decisions, workflow, safety, and
navigation. Flag always-loaded catalogs or code, generic background, duplication,
dead or low-value references, broad activation, and overlapping skills without a
composition rule. Prefer tested scripts/templates for deterministic work, but do
not reward brevity that omits safety or verification. For batch imports, include
a concise per-skill quality verdict.

## Updates and generated output

Treat `local.patch` and `local.remove` as maintained security/correctness
controls. Never run updater or patch generation in review. Inspect normalization
and compare intentional local differences with these controls.

For affected skills, require maintainer/CI evidence of two stable focused runs:

- `npx tsx bin/update-skills.ts <skill-name ...>`
- when patches change, `npx tsx bin/generate-patches.ts <skill-name ...>`

Without evidence, mark refresh/patch idempotence unverified and request the
check. Report edits the next refresh will overwrite. Statically inspect failure
handling, missing source/license, partial replacement, removal paths, symlinks,
shell interpolation, cleanup, and upstream additions/deletions/renames.

Marketplace YAML is derived: review source definitions and generators, not
unchanged generated churn. Verify deterministic output, unique IDs, valid
categories, URLs, archive names, and required definition files. For agents check
permissions/prompt/mode; for MCPs check installation JSON, parameters,
placeholders, secrets, and category; for release workflows inspect packaged
files.

Use read-only evidence from the repository's Validate Skills and Generate
Marketplace workflows, updater/patch idempotence checks, executable-resource
tests, schema validation, and local/source/license link resolution. CI passing
alone does not prove examples, formulas, security, licenses, updater behavior,
or bundled resources correct.

## Findings

Prioritize concrete defects over style. **Critical** includes credential
exposure, code execution, data loss/corruption, materially wrong results, or
unusable primary functionality. **Warning** includes broken workflows/examples,
unsafe defaults, missing required metadata, portability failures, incomplete
packaging, or lost local changes.

Each finding needs a changed path/line, trigger, impact, and minimal fix. Group
cross-cutting instances in the summary and comment on one representative line.
Deduplicate existing comments. If no issues remain, say so and list the evidence
reviewed.
