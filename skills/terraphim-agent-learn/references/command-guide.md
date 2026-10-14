# Command guide

Checked with released Clients 1.21.20. Inspect subcommand help before use.

| Operation | Actual effect |
|---|---|
| `learn list --recent <N>` / `learn query <PATTERN>` | Read selected learnings; inspect reported scope |
| `learn query <PATTERN> --global` | Deliberately read global learnings |
| `learn capture --error <ERROR> --exit-code <CODE> <COMMAND>` | Save a real observed failure |
| `learn correct <ID> --correction <TEXT>` | Annotate the actual failure learning; does not populate the separate compiled-rule store |
| `learn correction add --original <TEXT> --corrected <TEXT> --correction-type tool-preference` | Save an explicitly reviewed rewrite for separate compile/export |
| `learn compile` | Write compiled correction rules after review |
| `learn procedure ...` | Manage/replay procedures; replay executes commands |
| `learn install-hook ...` | Write a script and manual setup instructions; does not activate the host hook |
| `learn export-kg ...` | Write graph files for separate review and consumption |

Without an existing project `.terraphim` directory, commands can fall back to the
global store even inside a Git repository. Never infer project isolation from cwd.
Redact sensitive input before writes and read actual output files afterward.

[Use both Terraphim CLIs](workflows.md).
