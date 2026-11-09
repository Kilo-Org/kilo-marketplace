# Use the graph with grep; save a lesson with the agent

Terraphim's skills call two separately installed tools:

- **`terraphim-grep`** retrieves passages from files you choose, using an optional shared synonym graph.
- **`terraphim-agent`** saves authored lessons and reads them back from the current user's local memory store.

The commands below were exercised with the released **Terraphim Clients 1.21.20** binaries on macOS arm64. Obtain the correct archive and `SHA256SUMS` from the [1.21.20 release](https://github.com/terraphim/terraphim-clients/releases/tag/v1.21.20), verify the checksum, and check both `--version` outputs. Homebrew may supply a different version; inspect the installed help before following its command examples. The plugin does not bundle or install either binary.

```sh
terraphim-grep --version
terraphim-agent --version
terraphim-agent memory capture --help
```

## Search by a synonym created in the editor

A Markdown concept note can express the same vocabulary as a Logseq PKM note:

```markdown
# Risk
synonyms:: concern
```

In the [editor walkthrough](https://terraphim.ai/how-tos/synonym-search/), create **Concern** as an alternative for **Risk**, swap the word, save the document, then export its knowledge graph. `terraphim-grep --thesaurus` consumes that exported **JSON** graph; do not pass the Markdown concept note to that flag.

This repository includes a [small graph already exported by the editor](risk-concern.knowledge-graph.json): both terms have concept ID `1` and canonical term `risk`. Its SHA256 is `f8648b16470e764bdff5c95064078419d71e8d41d2ca30d4b1508017c166a45d`.

From the directory containing this workflow, create a disposable public corpus and copy that graph:

```sh
example_dir="$(mktemp -d)"
cp risk-concern.knowledge-graph.json "$example_dir/"
cd "$example_dir"
mkdir corpus
printf 'Risk: supplier delays require a backup plan.\n' > corpus/brief.md
printf 'Risk: approve a second supplier for delivery continuity.\n' > corpus/decision.md
printf 'Risk: review supplier lead times on Friday.\n' > corpus/review.md
```

First search without the shared graph, then with it:

```sh
terraphim-grep Concern --search-only --haystack all \
  --paths ./corpus --json -n 3 > before-sharing.json

terraphim-grep Concern --search-only --haystack all \
  --paths ./corpus --thesaurus ./risk-concern.knowledge-graph.json \
  --json -n 3 > with-shared-graph.json
```

The literal baseline has no passages. The shared graph returns the three **Risk** passages even though none contains **Concern**. Both outputs have `answer: null`; these are actual search results, not generated prose. Open the JSON files and inspect their `chunks`, source filenames and line numbers.

Use `--haystack all` for this example. In the checked releases, `--haystack docs` does not return these local Markdown matches. To compare explicit synthesis, use the [published synthesis walkthrough](https://terraphim.ai/how-tos/synonym-search/) after configuring a provider and deciding which context it may receive. `--answer` is a separate, opt-in model operation.

## Save an authored lesson and read the exact output

These commands write a new item to the current user's OS-local memory store, independent of the current working directory. The exported search graph and this memory store are separate: copying the JSON graph does not import it into agent memory, select a role, or make the memory store project-scoped.

Run this in the example directory. The lesson text is supplied explicitly; a provenance tag alone is not lesson content.

```sh
terraphim-agent --format json memory capture \
  --content 'Risk requires a Decision: approve a second supplier as the mitigation.' \
  --provenance-tag 'public-project-brief' > captured-memory.json

memory_id="$(python3 -c 'import json; print(json.load(open("captured-memory.json"))["memory_id"])')"
terraphim-agent memory show "$memory_id" --json > saved-memory.json
```

`captured-memory.json` contains the actual new `memory_id`. `saved-memory.json` must contain the same ID, the exact authored lesson, and the `provenance:public-project-brief` tag. The tag labels the source of the lesson.

For role-ranked retrieval and its distinct configuration, follow the [agent memory walkthrough](https://terraphim.ai/posts/cold-start-tax-agentic-memory/). For actual failed-command learning and the difference between a proposed command, a hook rewrite and executed output, see [the hooks walkthrough](https://terraphim.ai/posts/native-hook-support/).
