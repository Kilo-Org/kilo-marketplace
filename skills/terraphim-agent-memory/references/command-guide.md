# Command guide

Checked with released Clients 1.21.20. Inspect each subcommand's `--help` before use.

| Operation | Actual effect |
|---|---|
| `memory list` / `memory show <ID> --json` | Read items in the current user's OS-local store |
| `memory retrieve <QUERY> --role <ROLE>` | Read configured KG-ranked memory; no lexical fallback |
| `memory capture --content <TEXT> --provenance-tag <TAG>` | Save explicit text and a source label; verify the returned ID using show |
| `memory apply --prompt <TEXT>` | Preview hook context; does not install or execute a hook |
| `memory validate` | Run `heuristic-v1` diagnostics; not an LLM judge |
| `memory rubric` | Run a heuristic project diagnostic |
| `memory retire --lesson-id <ID> --reason <TEXT>` | Write a pending proposal `retired-<ID>.md`; not immediate deletion |
| `memory export --output <PATH>` | Write an external artifact; verify the saved bytes |

Capture is independent of cwd and is not scoped by `--config` or `--role`.
`memory scope --check` is not a security-boundary verification. In this release,
`memory provenance` does not perform a session lookup and `memory distill` does
not compile/export learned rules. Do not report either status as completed work.

[Run explicit capture and readback](workflows.md).
