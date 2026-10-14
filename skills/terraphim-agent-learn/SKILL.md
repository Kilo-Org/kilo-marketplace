---
name: terraphim-agent-learn
description: >-
  Inspect and capture command failures or user corrections with terraphim-agent
  learn. Use when a user asks to preserve a concrete operational lesson, search
  earlier failures, or attach a correction; use terraphim-agent-memory for
  authored memory capture and retrieval.
metadata:
  category: development
  source:
    repository: 'https://github.com/terraphim/terraphim-cursor-plugin'
    path: skills/terraphim-agent-learn
    license_path: LICENSE
    ref: 391c7e4ebc103f1770b9dca589fcce7ccd211d5f
    commit: 391c7e4ebc103f1770b9dca589fcce7ccd211d5f
---

# Terraphim Agent Learn

Use real failed commands, observed errors and verified corrections. Start with
read-only inspection and establish the actual learning store before writing.

## Install and check the dependency

On macOS or Linux with Homebrew:

```sh
brew tap terraphim/terraphim
brew install terraphim-agent
terraphim-agent --version
terraphim-agent learn --help
```

The examples target released **Clients 1.21.20**. Homebrew may install a different
version; inspect the installed help before using a command. For checksummed release archives, follow the
[installation guide](https://terraphim-skills.md/docs/non-technical/).
The skill does not install software automatically.

## Establish the actual scope

A Git repository alone does not select project storage. In Clients 1.21.20, an
existing project `.terraphim` directory selects project learning; without it the
command can fall back to the global store. Inspect the returned scope/path.
Use `--global` only for deliberately global work. If project storage is wanted,
create its `.terraphim` directory only within the user-authorized project setup.
Do not overwrite an existing directory or configuration.

```sh
terraphim-agent learn list --recent 10
terraphim-agent learn query "cargo build"
```

Use `--exact` for a literal identifier. Use `--semantic` only with a suitable
configured knowledge graph. Bound results and inspect returned IDs and paths.

## Capture and correct a real failure

Capture only a command that actually failed. Redact credentials, personal data,
customer data and sensitive paths before persistent storage.

```sh
terraphim-agent learn capture --error "<observed redacted error>" \
  --exit-code 1 "<actual redacted failed command>"
terraphim-agent learn query "<failure pattern>" --exact
terraphim-agent learn correct "<actual-learning-id>" \
  --correction "<verified corrected command>"
```

`learn correct` annotates that failure; it does not add a rule to the separate
correction store consumed by compilation. To record an explicitly reviewed
rewrite, inspect the help and use the distinct correction command:

```sh
terraphim-agent learn correction add --original "<observed command>" \
  --corrected "<verified command>" --correction-type tool-preference
terraphim-agent learn compile --output ./compiled-corrections.json
terraphim-agent learn export-kg --output ./reviewed-corrections
```

Read the compiled mapping and exported Markdown. A stored rule alone does not
activate a rewrite; separately configure the intended host adapter and verify
what actually executes.

## Procedures, hooks and exports

- `learn procedure replay` executes stored commands. Inspect their effects and
  run only within the user's authorized scope.
- `learn install-hook` writes a hook script and gives manual configuration
  instructions. It does not itself activate the host hook. Verify the adapter's
  configuration and actual execution separately.
- `learn compile` writes the compiled correction artifact. Read that artifact
  and verify the intended reviewed rule is present before using it.
- `learn export-kg` writes graph files to the selected output directory. Read
  them back and keep unreviewed or sensitive learnings out of a public graph.

For each write, report the actual ID, scope/path and saved file. For hook demos,
keep attempted input, the applied rewrite, actual execution result and output
file distinct. See the [verified hooks workflow](https://terraphim.ai/posts/native-hook-support/).

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
