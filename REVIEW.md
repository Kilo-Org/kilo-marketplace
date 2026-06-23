# Kilo Marketplace Review Guidance

Review the complete pull request diff against its base branch. Do not limit a new
review to files changed by the latest commit. Independently verify existing bot
findings and inspect every newly added or modified file, including bundled
resources that are not directly referenced by the diff summary.

Use `AGENTS.md` and `CONTRIBUTING.md` as repository policy. Prefer actionable
correctness, security, licensing, portability, packaging, and user-impact
findings over style preferences.

## Severity

- **Critical**: likely credential exposure, arbitrary code execution, data loss,
  silent corruption, materially wrong business results, or unusable primary
  functionality.
- **Warning**: broken documented workflows, invalid examples, missing required
  metadata, unsafe defaults, portability failures, incomplete packaging, or
  refresh behavior that discards marketplace changes.
- **Suggestion**: material maintainability, discoverability, or token-efficiency
  improvements that do not currently break behavior.

Do not report speculative concerns without a concrete triggering condition and
user impact. Do not downgrade a defect merely because it originates upstream;
the marketplace distributes and recommends the imported content.

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

Sub-agents stay read-only and do not post comments. Each returns path, line,
severity, triggering condition, impact, remediation, and confidence. The main
reviewer verifies every finding, removes duplicates, and ensures comments target
valid changed lines.

Apply every relevant section below. Review source changes together with their
generated, updated, and packaged consequences.

## New and imported skills

Review the entire skill directory, not only `SKILL.md`. Include `scripts/`,
`hooks/`, `references/`, `resources/`, `assets/`, `examples/`, templates,
notebooks, archives, binaries, nested skills, and license files.

Verify all of the following:

- The skill solves a distinct real use case and its description says when it
  should activate without matching unrelated work.
- Directory name, frontmatter `name`, marketplace ID, and archive name agree.
- `metadata.source.repository` and `metadata.source.path` identify the actual
  public canonical source. Attribution and author claims match that source.
- For contributed skills, require `metadata.source.license_path` as specified by
  `CONTRIBUTING.md`. Verify that it is repository-root-relative, exists upstream,
  and covers every copied text, code, image, font, template, and example. Do not
  require a separate top-level `license` when `license_path` supplies it.
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

Smoke-test primary bundled helpers when safe. Syntax-only checks are not enough:
exercise meaningful modes, parse generated artifacts with their real schema
validator, and verify output location and overwrite behavior.

## Skill quality and token efficiency

Judge whether the skill is useful to a model, not merely comprehensive.

- Keep the main `SKILL.md` focused on activation, decisions, workflow, safety,
  and navigation. Move large catalogs and detailed examples to references.
- Flag large always-loaded CSS, JavaScript, API catalogs, or generic background
  knowledge when progressive disclosure would preserve behavior.
- Identify duplicated guidance, tiny references that add lookup cost without
  detail, broad activation descriptions, dead resources, and overlapping skills
  without a clear composition rule.
- Check that deterministic repeated work is implemented by a tested script or
  template where that is safer and cheaper than regenerating it in context.
- Do not reward brevity when it omits necessary safety, correctness, or
  verification instructions.

Include a concise per-skill quality verdict in the review summary for batch
imports, even when no individual line comment is warranted.

## Updater and local controls

Treat `local.patch` and `local.remove` as maintained correctness and security
controls, not generated noise.

For every affected skill, perform the following in a disposable worktree. If
network or tooling prevents a step, identify the unverified behavior in the
review summary:

1. Refresh the selected skills with `bin/update-skills.ts`.
2. Confirm intentional marketplace differences survive through `local.patch`
   and `local.remove`.
3. Confirm the refresh leaves no unexpected diff.
4. Run the same refresh again and require an identical clean result.
5. If patches are regenerated, run patch generation twice and require stable
   output.

Report manual edits that the next refresh will overwrite. A patch failure,
missing source path, missing license, or partial replacement must fail clearly;
it must not silently publish unpatched upstream content. Check removal paths,
symlinks, shell interpolation, temporary cleanup, and behavior when upstream
adds, deletes, renames, or changes binary files.

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

Run the smallest relevant checks and report anything that could not run:

- Skill changes: `skills-ref validate` for every affected skill.
- Marketplace source or generator changes: regenerate all affected marketplace
  files and require a clean second run.
- Imported or refreshed skills: focused updater idempotence in a disposable
  worktree.
- Executable resources: language syntax checks plus focused behavior tests.
- Structured assets: parse and validate JSON, YAML, notebooks, manifests, and
  templates against the format version they declare.
- Links and resource maps: verify local targets exist; verify critical external
  source and license URLs.

Passing CI is supporting evidence, not proof that examples, formulas, security,
licenses, updater behavior, and bundled resources are correct.

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
