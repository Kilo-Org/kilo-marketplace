# Kilo Marketplace Review Guidance

Review the complete pull request diff against its base branch. Do not limit a new
review to files changed by the latest commit. Independently verify existing bot
findings and inspect every newly added or modified file, including bundled
resources that are not directly referenced by the diff summary.

Use `AGENTS.md` and `CONTRIBUTING.md` as repository policy. Prefer actionable
correctness, security, licensing, portability, packaging, and user-impact
findings over style preferences.

Reviews are read-only. Never edit files, create worktrees, install dependencies,
regenerate artifacts, refresh imports, apply patches, package, or run commands
that write locally or remotely. Use repository content and existing CI. For a
mutating or unavailable validation, name the missing evidence and exact targeted
maintainer check.

## Severity

- **Critical**: credential exposure, code execution, data loss/corruption,
  materially wrong business results, or unusable primary functionality.
- **Warning**: broken workflows/examples, missing required metadata, unsafe
  defaults, portability failures, incomplete packaging, or lost local changes.
- **Suggestion**: material maintainability, discoverability, or token-efficiency
  improvement without current breakage.

Report only defects with a concrete trigger and impact. Upstream origin does not
reduce severity because the marketplace distributes the content.

## Sub-agent usage

Use 0 sub-agents for formatting-only, generated-output-only, or trivial
single-file documentation changes, regardless of diff size.

Use 1-2 focused sub-agents when one or two risky areas need independent
verification, such as an executable script, licensing, an MCP configuration, or
marketplace generation.

Use up to 6 sub-agents for PRs spanning several review domains. Use all 6 when
a PR imports or refreshes multiple packages, or combines executable code,
external sources, and packaged assets. File or line count alone is not a reason
to add sub-agents.

For a large skill PR, shard the review as follows:

1. Provenance and repository integration: source paths, licenses, frontmatter,
   categories, IDs, generated marketplace entries, and update behavior.
2. Bundled code and assets: scripts, hooks, templates, notebooks, archives,
   binaries, dependencies, and end-to-end helper behavior.
3. Packaging and portability: missing files, broken links, installation-layout
   assumptions, environment-specific paths, and cross-platform commands.
4. Domain correctness: independently validate formulas, SQL, API usage, code
   examples, version claims, and whether "better" examples preserve semantics.
5. Security and destructive behavior: injection, secret persistence, unsafe
   subprocesses, downloads, uploads, overwrites, deletion, cost, and consent.
6. Skill quality: activation scope, overlap, progressive disclosure, token use,
   duplicated guidance, and whether the skill provides enough value to ship.

Sub-agents remain read-only and do not comment. They return path, line, severity,
trigger, impact, remediation, and confidence. The main reviewer verifies and
deduplicates findings and targets only valid changed lines.

## New and imported skills

Review the whole skill directory, not only `SKILL.md`: scripts, hooks,
references, resources, assets, examples, templates, notebooks, archives,
binaries, nested skills, and licenses.

Verify all of the following:

- The skill solves a distinct real use case and its description says when it
  should activate without matching unrelated work.
- Directory name, frontmatter `name`, marketplace ID, and archive name agree.
- `metadata.source.repository` and `metadata.source.path` identify the actual
  public canonical source. Attribution and author claims match that source.
- Require either top-level `license` or `metadata.source.license_path`, not both,
  as specified by `AGENTS.md`. Verify the declared license against upstream and
  ensure it covers every copied text, code, image, font, template, and example.
  When used, `license_path` must be repository-root-relative and exist upstream.
- Category is intentional and is not the importer placeholder `unknown`.
- Every referenced sibling skill or file is shipped and resolves with correct
  case from the installed skill directory.
- Examples are executable and current. Check imports, syntax, schemas, API and
  database versions, units, edge cases, and semantic equivalence. Do not assume
  upstream examples are correct.
- Commands work in Kilo's installation layout and do not assume Claude, Codex,
  a plugin repository root, `/mnt/user-data`, or an undeclared working directory.
- Destructive, production-changing, or paid actions require explicit
  confirmation and safe defaults. Credentials use placeholders or environment
  variables and are never committed, embedded in commands, persisted to tracked
  files, or written to logs.
- Generated HTML, SQL, shell, and subprocess examples handle untrusted input
  safely.
- Bundled files are necessary, non-placeholder, inspectable, and covered by the
  stated license. Treat archives and binaries as content to inspect, not opaque
  attachments.

Use test or CI evidence to verify helpers beyond syntax: meaningful modes,
artifact schemas, output locations, and overwrite behavior. Do not execute
helpers that write; report missing behavioral coverage.

## Skill quality and token efficiency

Judge usefulness to a model, not mere comprehensiveness.

- Keep `SKILL.md` focused on activation, decisions, workflow, safety, and
  navigation; move catalogs and detailed examples to references.
- Flag always-loaded CSS, JavaScript, API catalogs, or generic background where
  progressive disclosure preserves behavior.
- Identify duplication, low-value references, broad activation, dead resources,
  and overlapping skills without a composition rule.
- Prefer tested scripts/templates for safer deterministic repeated work.
- Do not reward brevity that omits safety, correctness, or verification.

Include a concise per-skill quality verdict in the review summary for batch
imports, even when no individual line comment is warranted.

## Updater and local controls

Treat `local.patch` and `local.remove` as maintained correctness and security
controls, not generated noise.

Never run updater or patch-generation commands in review. Inspect normalization
and compare local differences with the control files. Look for evidence that a
maintainer ran `npx tsx bin/update-skills.ts <skill-name ...>` twice in a
disposable worktree with a clean idempotence result. For patch changes, require
two stable runs of `npx tsx bin/generate-patches.ts <skill-name ...>`. Otherwise
mark this unverified and request the targeted check.

Report local edits the next refresh will overwrite. Patch failure, missing source
or license, and partial replacement must fail clearly. Statically check removal
paths, symlinks, shell interpolation, cleanup, and upstream additions, deletions,
renames, or binary changes.

## Marketplace, agents, MCPs, and packaging

Treat `skills/marketplace.yaml`, `agents/marketplace.yaml`, and
`mcps/marketplace.yaml` as derived files. Fix source definitions or generators,
not generated YAML. Inspect the item-level semantic delta rather than spending
review tokens on unchanged generated sections.

Verify deterministic regeneration, unique IDs, valid categories, accurate
URLs, matching release archive names, and no missing definition files. Keep
`metadata.suggest_for.extension` limited to distinctive high-confidence
patterns rather than broad file types.

For agents, verify permissions, prompt behavior, and mode. For MCPs, verify
installation JSON, parameters, placeholders, secrets handling, and category.
For release workflows, inspect the actual packaged file set: control files,
unrelated upstream files, secrets, caches, and opaque assets must not be shipped
accidentally.

## Validation expectations

Use read-only checks and existing CI/PR evidence. Do not install tools or run
commands that write. Applicable evidence includes:

- `skills-ref validate` results for every affected skill.
- Clean, repeatable marketplace regeneration for source or generator changes.
- Focused updater and patch idempotence for imported or refreshed skills.
- Syntax and focused behavior tests for executable resources.
- Schema validation for JSON, YAML, notebooks, manifests, and templates against
  the format version they declare.
- Resolution of local resource links and critical external source/license URLs.

For missing evidence, state what is unverified and provide the exact maintainer
command or CI check. Passing CI does not prove examples, formulas, security,
licenses, updater behavior, or bundled resources are correct.

## Review output

Order findings by severity. Each finding must state:

- Exact path and changed line
- Concrete triggering condition
- User or repository impact
- Minimal practical correction

Group cross-cutting instances in the summary, but place an inline comment on a
representative changed line. Avoid duplicate comments, generic best-practice
advice, speculative redesigns, typo-only findings, and findings that apply only
to unchanged code. If no actionable findings remain, say so explicitly and list
the validation performed.
