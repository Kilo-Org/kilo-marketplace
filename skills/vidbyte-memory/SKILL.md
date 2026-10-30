---
name: vidbyte-memory
description: Install correction-driven memory into a repository so every correction the user gives becomes a slim fact, a pytest test that fails if the mistake comes back, and a git commit. Use when the agent keeps repeating mistakes the user already corrected, or when the user asks to install vidbyte-memory.
license: MIT
---

# vidbyte-memory

Installs [vidbyte-memory](https://github.com/cerredz/vidbyte-memory) (MIT) into the repository you are working in. After the install, the memory lives in the repo's own files: `AGENTS.md`, typed memory under `memory/`, slim facts under `facts/`, skills under `.agents/skills/` and tests under `tests/`.

From then on, every correction the user gives is logged word for word and becomes three things:
- a fact or rule the agent loads next time;
- a test or verifier that fails if the mistake returns;
- a footprint commit that shows how memory changed.

No API key, database or service is involved. In Kilo, the installer also writes `.kilo/plugins/vidbyte-memory.js`. When a session goes idle, that plugin re-prompts it while tests fail, feedback is pending or changes are uncommitted, so the request is actually finished before the agent stops.

## When to Use This Skill

- The user corrects the agent ("no, we never do X here") and wants the correction to stick for future sessions.
- The user asks for memory that is enforced by tests, not just written down.
- The user asks to install, repair or remove vidbyte-memory.

## What This Skill Does

1. **Previews the install.** It clones the template to a temporary folder and shows a dry-run plan: files to create, agents detected, and existing files it keeps.
2. **Installs without overwriting.** An existing `AGENTS.md` is folded into the new `## Task` section, every edited file gets a `.vidbyte-memory-backup` copy, and every write is recorded in `.vidbyte-memory/install.json`.
3. **Sets up enforcement.** It writes the Kilo plugin and the hooks for the other coding agents found in the repo or on the machine.
4. **Finishes the setup with the user.** It fills the `## Task` section, runs the tests and commits.

## How to Use

### Basic Usage

```
Install vidbyte-memory in this repo
```

### Advanced Usage

```
Install vidbyte-memory here, wire only Kilo and Codex, and show me the plan first
```

## Steps

1. Clone the template outside the repository and show the user `scripts/install.py` before running it:
   ```bash
   git clone --depth 1 https://github.com/cerredz/vidbyte-memory /tmp/vidbyte-memory
   ```
2. Show the plan: `python /tmp/vidbyte-memory/scripts/install.py --target . --dry-run`. When the user names their agents, pass them with `--agents`, for example `--agents kilo,codex`. `AGENTS.md`, the `.agents/skills` mirror and the Claude Code hook are always written.
3. If the plan reports a conflict on `tests/helpers.py`, `tests/test_memory_integrity.py`, `scripts/guard.py` or `scripts/footprint.py`, stop and ask the user how to resolve it.
4. Confirm with the user, then run the same command without `--dry-run`.
5. Ask the user for the recurring task this repository serves, and replace the placeholder under `## Task` in `AGENTS.md` with it.
6. Run `python -m pytest -q tests` (install pytest first if needed) and fix anything the install caused.
7. Commit with `python scripts/footprint.py --commit --title "install vidbyte-memory"`.

To remove it, run `python scripts/install.py uninstall --dry-run`, show the plan, then run it without `--dry-run`. Memory the agent wrote is kept unless the user asks for `--force`.

## Example

**User**: "You keep writing prices without the currency. Make that stick, and install whatever you need."

**Output**:
```
vidbyte-memory would write 77 files in /work/shop
  + kilo (repo has .kilo)
Proceed? -> yes
vidbyte-memory wrote 77 files in /work/shop
36 passed, 3 skipped
[main 1a2b3c4] install vidbyte-memory
```
Then the correction goes through the `handle-feedback` skill. It becomes `R-001: every price shows its currency`, a test `tests/test_fb001_price_currency.py` that fails on a price without one, and a footprint commit.

## Requirements

- Python 3.9 or later. The installer and scripts use only the standard library; the tests need pytest.
- git.
