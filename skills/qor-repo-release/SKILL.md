---
name: qor-repo-release
description: >-
  Delivery Gate Orchestration - orchestrates release workflow after /ql-substantiate seals a session. Version bump, metadata sync, git tag, release pipeline trigger.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-repo-release
---

# /ql-repo-release - Delivery Gate Orchestration

<skill>
  <trigger>/ql-repo-release</trigger>
  <phase>DELIVER</phase>
  <persona>Governor</persona>
  <output>Version bump, metadata sync, git tag, release pipeline trigger</output>
</skill>

## Purpose

Orchestrate the full local release workflow after `/ql-substantiate` seals a session. Transitions substantiated deliverables to production-ready releases with confirmation gates at every irreversible step.

## Execution Protocol

### Step 1: Verify Branch and Seal

#### Branch Gate

```bash
git branch --show-current
```

The release branch must follow the naming convention `hotfix/vX.Y.Z` or `release/vX.Y.Z`.

If on a feature branch (e.g., `feat/*`, `plan/*`):

```
ABORT
Report: "Cannot release from a feature branch. Create a release or hotfix branch first:
  git checkout -b hotfix/vX.Y.Z   (from the branch with all changes)
  git checkout -b release/vX.Y.Z  (from main after merging)"
```

If on `main`:

```
WARN: "Direct push to main is blocked by pre-push policy. Switching to release branch."
git checkout -b release/vX.Y.Z
```

#### Pull Latest

```bash
git pull --rebase
```

**Note**: After release, create a PR to merge the release/hotfix branch into `main`.

#### Seal Check

```
Read: docs/SYSTEM_STATE.md
Read: docs/META_LEDGER.md (last entry)
```

Confirm the latest ledger entry is a SUBSTANTIATE seal. If not:

```
ABORT
Report: "No seal found. Run /ql-substantiate before releasing."
```

### Step 2: Run Pre-Flight
 
Execute `release-gate.cjs --preflight` from `./`:
 
```bash
node ./release-gate.cjs --preflight
```
 
Additionally verify: uncommitted skill files (`git diff --name-only -- .claude/commands/ql-*.md`), help doc version markers (COMPONENT_HELP.md, PROCESS_GUIDE.md), and backlog coherence (no duplicate B-items, version table current). STOP if any check fails.

### Step 3: Confirm Version Bump

Read current version from `./package.json`.

Ask the user:

> Current version is **vX.Y.Z**. What bump level? (patch / minor / major)

Wait for response before proceeding.

### Step 4: Apply Version Bump

Execute:

```bash
node scripts/release-gate.cjs --bump <level>
```

Report: `vX.Y.Z -> vA.B.C (<level> bump)`

### Step 5: Author Release Metadata

Invoke `/ql-document` in RELEASE_METADATA mode with the target version:

1. Read recent META_LEDGER entries (from last DELIVER or SUBSTANTIATE to current)
2. Read SYSTEM_STATE.md for implementation summary
3. Author the 3 required files:
   - `./CHANGELOG.md` — `## [A.B.C] - YYYY-MM-DD`
   - `./README.md` — Current Release + What's New
   - Root `CHANGELOG.md` — `## [A.B.C]`
4. Present authored content to user for review before writing

**Confirmation gate** — Show authored content. User approves or edits before files are written.

### Step 6: Documentation Gate (HARD STOP)

**INTERDICTION**: Documentation versioning MUST be verified complete before any commit or tag. This gate cannot be bypassed.

Execute `release-gate.cjs --preflight`:

```bash
node scripts/release-gate.cjs --preflight
```

**INTERDICTION**: If ANY check shows [FAIL], ABORT. List failing checks and return to Step 5. All version markers (CHANGELOG, README, COMPONENT_HELP, PROCESS_GUIDE, BACKLOG) must show vA.B.C before proceeding.

### Step 7: Stage and Commit

**Confirmation gate** — Show the user the diff:

```bash
git diff --stat
```

Ask: "Stage and commit these changes as `[RELEASE] vA.B.C`? (y/n)"

If confirmed:

```bash
git add -f ./package.json ./CHANGELOG.md ./README.md ./docs/COMPONENT_HELP.md ./docs/PROCESS_GUIDE.md CHANGELOG.md README.md docs/BACKLOG.md
git commit -m "[RELEASE] vA.B.C"
```

Note: `-f` is required because `./docs/` is in `.gitignore` but tracked.

### Step 8: Create Tag

Execute:

```bash
node scripts/release-gate.cjs --tag
```

This runs preflight internally and creates an annotated git tag.

### Step 9: Confirm Push

**Confirmation gate** — Present:

> Tag **vA.B.C** created locally. Push to origin to trigger the release pipeline?
>
> Remote: origin
> Branch: current branch
> Tag: vA.B.C
>
> Proceed? (y/n)

If confirmed:

```bash
git push && git push --tags
```

### Step 10: Record Ledger

Add META_LEDGER entry:

```markdown
### Entry #[N]: DELIVER — vA.B.C

**Timestamp**: [ISO 8601]
**Phase**: DELIVER
**Author**: Governor

**Version**: A.B.C
**Tag**: vA.B.C
**Commit**: [short hash]

**Decision**: Release vA.B.C delivered. Tag pushed to trigger release pipeline.
```

Calculate and record content hash and chain hash per standard Merkle chain protocol.

## Constraints

- **NEVER** push without user confirmation
- **NEVER** write metadata without user review of authored content
- **NEVER** release without a preceding SUBSTANTIATE seal
- **NEVER** skip the pre-flight validation
- **NEVER** proceed past Step 6 if preflight has ANY [FAIL] — Step 6 is a hard ABORT gate
- **NEVER** commit `[RELEASE] vX.Y.Z` without confirmed preflight PASS (the commit-msg hook enforces this at the git layer)
- **NEVER** release from a feature branch — must be on `main`
- **NEVER** tag without pulling latest `main` first
- **ALWAYS** use `/ql-document` for release metadata authoring
- **ALWAYS** run pre-flight twice (before and after metadata authoring)
- **ALWAYS** use `[RELEASE] vX.Y.Z` commit message format
- **ALWAYS** record the delivery in META_LEDGER
- **ALWAYS** update version markers in `docs/COMPONENT_HELP.md` and `docs/PROCESS_GUIDE.md`
- **ALWAYS** update `README.md` (root) Current Release marker and Socket badge version
- **ALWAYS** update `docs/BACKLOG.md` version summary table: mark previous version RELEASED, add new version row
- **ALWAYS** use `git add -f` for gitignored-but-tracked paths (e.g., `./docs/`)

## Success Criteria

Release succeeds when:

- [ ] Branch is release/* or hotfix/* (not feature branch)
- [ ] SUBSTANTIATE seal exists in META_LEDGER
- [ ] Pre-flight checks pass (both before and after metadata)
- [ ] Version bump applied
- [ ] /ql-document authored and user-approved release metadata
- [ ] User confirmed commit and push
- [ ] Tag created and pushed
- [ ] META_LEDGER updated with DELIVER entry

## Integration with S.H.I.E.L.D.

This skill implements:

- **Delivery Gate**: Final phase of S.H.I.E.L.D. lifecycle
- **Confirmation Gates**: User approval at every irreversible step (commit, push)
- **Documentation Gate**: Hard stop if version markers incomplete
- **Hash Chain Continuation**: Records delivery in META_LEDGER with Merkle linkage

