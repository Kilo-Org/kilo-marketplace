---
name: terraphim-grep
description: >-
  Search local source code and documentation with the installed terraphim-grep
  CLI. Use for bounded text or knowledge-graph-assisted retrieval inside a
  project; do not use it for internet search or file-name-only lookup.
metadata:
  category: search
  source:
    repository: 'https://github.com/terraphim/terraphim-cursor-plugin'
    path: skills/terraphim-grep
    license_path: LICENSE
    ref: 391c7e4ebc103f1770b9dca589fcce7ccd211d5f
    commit: 391c7e4ebc103f1770b9dca589fcce7ccd211d5f
---

# Terraphim Grep

Locate evidence in local code and Markdown. Default to bounded, offline search;
use synthesis only for an explicitly requested model operation.

## Install and check the dependency

On macOS or Linux with Homebrew:

```sh
brew tap terraphim/terraphim
brew install terraphim-grep
terraphim-grep --version
terraphim-grep --help
```

The examples target released **Clients 1.21.20**. Homebrew may install a different
version; inspect the installed help before using a command. For checksummed release archives, follow the
[installation guide](https://terraphim-skills.md/docs/non-technical/).
The skill does not install software automatically.

## Search workflow

1. Choose the narrowest useful existing path.
2. Pass `--search-only` so ambient provider credentials do not enable synthesis.
3. Use `--haystack code` for code or `--haystack all` for local Markdown.
   In the checked releases, `--haystack docs` does not return these local
   Markdown matches; do not interpret that empty result as absence of content.
4. Bound the result count and context; inspect actual chunks and source paths.
5. Use `--json` when another tool will consume the result.

```sh
terraphim-grep "fn main" --search-only --haystack code --paths src -C 2 -n 20
terraphim-grep "validation report" --search-only --haystack all --paths docs --json -n 20
```

Use a compiled JSON thesaurus that the project supplies or the editor exports:

```sh
terraphim-grep Concern --search-only --haystack all --paths ./corpus \
  --thesaurus ./risk-concern.knowledge-graph.json --json -n 3
```

A concept note can contain `synonyms:: concern`, compatible with Logseq PKM
syntax. The `--thesaurus` flag takes its exported JSON graph, not the Markdown
note. The [packaged examples](references/workflows.md) include that graph and a
clean corpus. Do not create or overwrite a project's graph without authorization.

## Synthesis and completion

`--answer` and `--force-rlm` can use a configured model. Before a requested
synthesis run, establish the model, data boundary and possible cost. Keep secrets
and private data out of unapproved providers. Search-only outputs have
`answer: null`; report retrieved passages separately from generated prose.

Report the paths, mode, relevant chunks and limitations. An empty result applies
only to the query and scope actually searched.

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
