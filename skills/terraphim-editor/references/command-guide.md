# Editor-to-search command guide

The editor is a separately installed extension or the online editor. There is no
`terraphim-editor` command to run. Use the actual editor's save/export controls.
The [workflow](workflows.md) contains portable setup and both CLI examples.

| Action | Actual output to inspect |
|---|---|
| Save and reopen | Annotated Markdown retains the applied word and alternative. |
| Export clean Markdown | Text contains the chosen words without hidden annotation metadata. |
| Export Document Knowledge Graph | JSON maps Risk and Concern to the same concept ID. |
| `terraphim-grep Concern --search-only --haystack all --paths ./corpus --json -n 3` | Literal baseline has no Concern passages in the supplied clean corpus. |
| Same query with `--thesaurus ./risk-concern.knowledge-graph.json` | Actual Risk passages, source filenames and line numbers; `answer: null`. |
| Same query with `--answer` | Explicit provider synthesis, with source passages distinct from generated wording. |
| `terraphim-agent --format json memory capture --content ... --provenance-tag public-project-brief` | Actual new memory ID; writes the OS-user store. |
| `terraphim-agent memory show <id> --json` | That saved ID, content and supplied source tag. |

The examples target released Clients 1.21.20. The editor walkthrough targets the
online deployment identified by the public tutorial and Microsoft preview 0.1.3.
Kilo installation does not install these binaries or configure an AI provider.
The `synonyms::` concept note is Logseq-compatible Markdown, but the grep flag
expects exported JSON. Keep notes and graph outside the clean search corpus.

For a successful demonstration retain actual files, versions and checksums.
A process exit, input echo, prepared graph or source-level test is insufficient
to prove a new editor registration or native Kilo installation. Do not claim the
agent accepts this JSON as its memory store; it has separate configuration.
