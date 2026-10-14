# Command guide

Checked with released Clients 1.21.20. Inspect installed `--help` when versions differ.

| Need | Flag |
|---|---|
| Offline retrieval | `--search-only` (alias `--no-rlm`) |
| Bound roots | `--paths <PATHS>...` |
| Local code | `--haystack code` |
| Local Markdown | `--haystack all`; `docs` did not return these matches in the checked releases |
| Context and result limit | `-C <COUNT>` and `-n <COUNT>` |
| Actual structured output | `--json` |
| Exported synonym graph | `--thesaurus <JSON_PATH>` |
| Existing configured role | `--role <NAME>` |

`--answer` and `--force-rlm` can invoke configured model synthesis; neither belongs
to the default offline workflow. [Run the paired CLI examples](workflows.md).
