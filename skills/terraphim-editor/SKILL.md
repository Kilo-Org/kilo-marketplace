---
name: terraphim-editor
description: >-
  Create and swap wording alternatives in the existing Terraphim editor, save
  the annotated document, export its synonym graph, and search related decisions
  with terraphim-grep. Use for a writing-to-search workflow, not for installing
  an editor runtime or automatically activating agent hooks.
metadata:
  category: productivity
  suggest_for:
    vscode_extension:
      - name: Terraphim
        id: applied-knowledge-systems.terraphim-it
  source:
    repository: 'https://github.com/terraphim/terraphim-cursor-plugin'
    path: skills/terraphim-editor
    license_path: LICENSE
    ref: 11311294ce0d1afb3f1abf491028ffadea3861cd
    commit: 11311294ce0d1afb3f1abf491028ffadea3861cd
---

# Terraphim Editor

Help the user turn a useful wording choice into reusable search vocabulary.
Start with a public project brief: **Risk** becomes **Concern**, while the graph
keeps both terms connected. The skill supplies instructions and example files;
it does not bundle an editor, CLI, MCP server or automatic hook.

## Open the editor and check the tools

Use the [online editor](https://terraphim.ai/editor/) or the separately installed
Terraphim It extension (`applied-knowledge-systems.terraphim-it`). The extension
workflow targets Microsoft preview **0.1.3**. Check the installed version and
follow the [editor walkthrough](https://terraphim.ai/how-tos/synonym-search/).
Kilo catalog installation and native host qualification are separate gates;
this companion does not claim that all editor features work in every host.

The search and separate memory examples target **Terraphim Clients 1.21.20**.
On macOS or Linux with Homebrew:

```sh
brew tap terraphim/terraphim
brew install terraphim-grep terraphim-agent
terraphim-grep --version
terraphim-grep --help
terraphim-agent --version
terraphim-agent memory capture --help
```

Homebrew may install a different version. Check its help, or use the checksummed
release archives in the [installation guide](https://terraphim-skills.md/docs/non-technical/).
Dependencies are installed separately and only when requested.

## Author and verify an alternative

1. Open a public Markdown brief in the editor's **Alternative Control** view.
2. Select **Risk**, open **Alternatives**, and add **Concern** as an authored
   alternative. Apply or swap the alternative so the visible text changes.
3. Save the annotated document, close it, and reopen it. Check the actual saved
   text and retained alternative; a typed input alone is not a successful save.
4. Export clean Markdown for the corpus and use **Export Document Knowledge Graph** for the JSON thesaurus. Keep the exported files separate from the
   annotated source. Verify that `risk` and `concern` share a concept ID.
5. Preserve the actual export when demonstrating registration. The packaged
   fixture is a separate, already exported example, not proof of a new action.

Use the user's selected role and inspect the actual suggestions. Local KG
suggestions and authored alternatives need no remote model. If the user chooses
AI suggestions, establish the configured provider and what text it receives
before sending context. This skill does not silently enable providers.

## Search with the shared vocabulary

A concept note can express the vocabulary using Logseq PKM-compatible Markdown:

```markdown
# Risk
synonyms:: Concern
```

Keep that note outside the clean corpus. `--thesaurus` takes the **exported JSON**,
not the Markdown note. The [runnable workflow](references/workflows.md) creates a
clean three-file Risk corpus and compares the actual saved outputs:

```sh
terraphim-grep Concern --search-only --haystack all \
  --paths ./corpus --thesaurus ./risk-concern.knowledge-graph.json --json -n 3
```

First run the same query without the graph. It has no literal Concern passages;
with the graph, inspect the returned Risk passages and source filenames.
Use `--answer` only after the user explicitly chooses provider synthesis and
reviews the context disclosure. Keep the query, corpus and graph unchanged,
and display retrieved passages separately from the generated answer.

## Separate agent-memory example

The same [packaged workflow](references/workflows.md) also shows
`terraphim-agent --format json memory capture --content ...` and
`terraphim-agent memory show <returned-id> --json`. Read back the exact ID,
authored content and supplied provenance tag. This writes the current user's
OS-local memory store; the working directory does not isolate it. Exporting a
graph does not import agent memory or activate a correction hook.

Keep this memory example separate from the short editor → graph → grep demo.
For command learning and explicit correction compilation, use
[the existing learning guide](https://terraphim.ai/posts/native-hook-support/).

## Output and recovery

Report the saved annotated file, clean Markdown, exported graph and actual search
JSON paths. If save, export or retrieval fails, preserve the inputs and report
the error; do not replace the output with a prepared fixture. Do not overwrite
user files or delete their alternatives, graphs or memory to recover an install.
The [command guide](references/command-guide.md) explains the checks and boundaries.

Inspired by Jason Fried's Write_On video: it prompted Alex Mikhalev to return to
his Rust/WebAssembly editor and connect alternatives to reusable knowledge.
The [public tutorial](https://terraphim.ai/how-tos/synonym-search/) links to Jason's
original post and shows the complete example.

Browse the [Community, Core, and Premium skill catalogue](https://terraphim-skills.md/skills/).
Discovering a related skill never starts checkout or changes an entitlement.

## Kilo distribution provenance

This Kilo copy preserves the original skill instructions and resources. Its
frontmatter and packaging were transformed by the pinned Kilo importer. The
original Terraphim signature applies to the immutable source, not this copy.
See [source provenance](references/kilo-provenance.json), [LICENSE](LICENSE) and
[NOTICE](NOTICE).
