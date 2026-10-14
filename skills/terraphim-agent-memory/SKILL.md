---
name: terraphim-agent-memory
description: >-
  Save explicit authored lessons, read saved memory by ID, and retrieve
  configured KG-ranked memory with terraphim-agent memory. Use for local memory
  capture/readback, heuristic checks, or explicitly requested exports; use
  terraphim-agent-learn for command failures and corrections.
metadata:
  category: productivity
  source:
    repository: 'https://github.com/terraphim/terraphim-cursor-plugin'
    path: skills/terraphim-agent-memory
    license_path: LICENSE
    ref: 391c7e4ebc103f1770b9dca589fcce7ccd211d5f
    commit: 391c7e4ebc103f1770b9dca589fcce7ccd211d5f
---

# Terraphim Agent Memory

Read stored items before writing. Capture only the lesson the user actually
provides or explicitly approves, and verify the saved output.

## Install and check the dependency

On macOS or Linux with Homebrew:

```sh
brew tap terraphim/terraphim
brew install terraphim-agent
terraphim-agent --version
terraphim-agent memory --help
```

The examples target released **Clients 1.21.20**. Homebrew may install a different
version; inspect the installed help before using a command. For checksummed release archives, follow the
[installation guide](https://terraphim-skills.md/docs/non-technical/).
The skill does not install software automatically.

## Storage and reads

In Clients 1.21.20, capture/list/show use the current user's OS-local evolution
store, independent of the working directory. `--config`, `--role`, or an exported
search graph does not create a project-scoped capture store. Do not assume a new
project means an empty or isolated memory store.

```sh
terraphim-agent memory list --limit 20
terraphim-agent memory show "<actual-memory-id>" --json
```

For KG-ranked retrieval, use an exact role already defined in the active
configuration:

```sh
terraphim-agent memory retrieve "<query>" --role "<exact configured role>"
```

Retrieval requires matching graph concepts and has no lexical fallback. An empty
result does not establish that no related stored item exists. Inspect the
configured role and actual saved items; do not infer a security boundary from
`memory scope --check`. The released scope diagnostic is not an access-control
test and can ignore an explicitly supplied configuration.

## Capture explicit content and verify it

Only perform the write when authorized. A provenance tag labels the source; it
is not lesson content or proof of an external session lookup.

```sh
terraphim-agent --format json memory capture \
  --content 'Risk requires a Decision: approve a second supplier as the mitigation.' \
  --provenance-tag 'public-project-brief' > captured-memory.json
memory_id="$(python3 -c 'import json; print(json.load(open("captured-memory.json"))["memory_id"])')"
terraphim-agent memory show "$memory_id" --json > saved-memory.json
```

Read both files. Require the returned ID, exact content and source tag to match.
Use `--file` only after reviewing that file's contents and the installed help.
Never capture private data merely to demonstrate the command.

## Evaluation, previews and explicit lifecycle writes

- `memory validate` and `memory rubric` provide heuristic diagnostics. The
  checked validator reports `heuristic-v1`; do not describe it as an LLM judge
  or a proof of correctness.
- `memory apply --prompt <TEXT>` previews available hook context. A preview is
  not evidence of an installed or executed hook.
- `memory export --output <PATH>` writes an artifact. Confirm the destination
  and read the saved file after execution.
- `memory retire --lesson-id <ID> --reason <TEXT>` writes a pending-approval
  retirement proposal named `retired-<ID>.md`; it does not immediately remove
  the stored item. Review the actual path returned by the command.

In Clients 1.21.20, `memory provenance` and `memory distill` return status output
without performing the session lookup or compile/export their names suggest.
Do not use either as completion evidence. Use the saved content/tag for capture
readback, or the separate reviewed `learn compile`/`learn export-kg` workflow.

## Completion evidence

Report actual IDs, saved content only as needed, storage behavior, configured
retrieval role, and the files created. Distinguish author-provided source tags,
heuristics, previews and actual execution.

## Related workflows

The packaged [CLI examples](references/workflows.md) show both
`terraphim-grep` synonym search and `terraphim-agent` authored-memory
capture/readback. The graph and memory store are separate.

Browse the [Community, Core, and Premium skill catalogue](https://terraphim-skills.md/skills/).
Discovering a related skill never starts checkout or changes an entitlement.

## Kilo distribution provenance

This Kilo copy preserves the original skill instructions and resources. Its
frontmatter and packaging were transformed by the pinned Kilo importer. The
original Terraphim signature applies to the immutable source, not this copy.
See [source provenance](references/kilo-provenance.json), [LICENSE](LICENSE) and
[NOTICE](NOTICE).
