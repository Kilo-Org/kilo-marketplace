---
name: varalign
description: >-
  Track every variable an AI agent writes across sessions and flag duplicate or
  drifted variables (e.g. MAX_RETRIES vs RETRY_LIMIT, a connection string
  re-typed under a new name) before they pile up in a codebase.
metadata:
  category: development
  source:
    repository: 'https://github.com/greenyogainc/varalign'
    path: skills/varalign
    license_path: LICENSE
    ref: main
    commit: dc9dc3fef41cb27dd82663c8adc708bf672990e6
---

# VarAlign

AI coding agents forget. Across sessions they re-introduce a variable that
already exists under another name, let a value drift from the one they wrote
last week, or strand a definition when a file moves. VarAlign tracks every
assignment an agent writes, reconciles it against what the repo actually
holds, and scores duplicate/misaligned variables so they get consolidated
instead of multiplying.

## When to Use This Skill

- Setting up a new project (or onboarding an existing one) so variable writes
  get tracked across sessions.
- The user asks to find duplicate/misaligned constants, reduce config drift,
  or "make sure I'm not inventing a new name for something that already
  exists."
- A repo already has a `.varmem/` directory — tracking is already live; use
  this skill to run scans, read the report, or fix flagged pairs.

## What This Skill Does

1. **Capture** — installs a Kilo plugin (`.kilo/plugins/varmem.ts`) that
   records every variable assignment Kilo writes, attributed with a session
   id, so drift and duplication are visible across sessions, not just within
   one.
2. **Detect** — scans the repo for duplicate/misaligned variables (same
   concept, two names) and drifted values (same name, changed value),
   producing a scored, color-coded report. Detection is file-based and
   language-aware (Python via `ast`, honest heuristics for JS/TS, PowerShell,
   Bash, C#, Go, `.env`) — it also catches drift in code written by other
   tools or by hand, not just Kilo.
3. **Fix** — generates a ready-to-paste remediation prompt scoped to exactly
   the findings above a chosen confidence level.

## How to Use

### Basic Usage

```
Set up variable drift tracking for this repo with varalign.
```

This runs `python varmem.py --project . init --kilo` (writes the capture
plugin) and `python varmem.py scan` (baselines everything already in the
repo).

### Advanced Usage

```
Run varalign's duplicate scan at high confidence only, and write a fix prompt.
```

```bash
python varmem.py duplicates --level high
python varmem.py prompt --min-level high --out fix.md
```

## Example

**User**: "Set up variable drift tracking for this repo."

**Output**:

```
$ python varmem.py --project . init --kilo
Kilo plugin written to .kilo/plugins/varmem.ts
Restart Kilo (or start a new session) to load it.

$ python varmem.py scan
scanned 214 files, tracked 1,406 assignments (origin=scan)

$ python varmem.py duplicates --level high
  [high]   MAX_RETRIES <-> RETRY_LIMIT   (src/client.py:12 / src/worker.py:40)
           same-value, near-name match
```

## Tips

- Zero dependencies — pure Python 3.11+ stdlib, nothing to install beyond the
  interpreter.
- `.varmem/` is meant to be **committed** — state travels with the repo and
  is readable by Kilo, Claude Code, CI, and the VS Code extension alike, with
  no database drivers.
- Dismissing a suspect with `varmem dup-note "<pair>" --verdict not_duplicate`
  learns the family, so the rest of it quiets automatically.
- Add `python varmem.py ci --fail-on high` to CI once a repo's baseline is
  clean, to block new drift instead of just reporting it.

## Common Use Cases

- Long AI-assisted sessions where the agent tends to reinvent constant names
  across files instead of reusing an existing one.
- Cleaning up a legacy codebase with scattered near-duplicate config values
  (retry limits, timeouts, connection strings) before a refactor.
- Enforcing a variable-naming baseline in CI so drift doesn't creep back in.
