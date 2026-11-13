# Extending Obsidian Plugin Workflows

Use this file when adding support for newly installed Obsidian plugins.

## Discovery process

1. List enabled plugins:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py plugins
```

2. List a plugin's command IDs:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py commands --plugin <plugin-id>
```

3. Inspect the plugin manifest and only the needed settings keys:

```bash
jq . ~/git/obsidian-2026/.obsidian/plugins/<plugin-id>/manifest.json
jq 'keys' ~/git/obsidian-2026/.obsidian/plugins/<plugin-id>/data.json
jq '.safeKeyNeededForThisWorkflow' ~/git/obsidian-2026/.obsidian/plugins/<plugin-id>/data.json
```

Treat `.obsidian/plugins/*/data.json` as potentially sensitive. Do not dump the whole file; read the minimal key required for the current workflow and redact credentials, tokens, account IDs, server URLs, cookies, and local absolute paths before returning output.

4. Add only stable, user-facing command IDs to `references/runtime-sync.md`.
5. If a workflow requires repeated parsing or file edits, extend `scripts/obsidian_workflows.py` with a subcommand instead of rewriting shell snippets in SKILL.md.

## Best-practice guardrails

- Prefer Obsidian plugin commands for UI-visible actions.
- Prefer direct file parsing for read-only summaries when plugin commands do not return useful output.
- Check Git conflicts before sync, commit, push, or file-writing workflows.
- Ask before sensitive or destructive commands: developer/eval/debug commands, `delete`, `discard`, `reset`, `install`, `enable`, `uninstall`, `rm`, restore, publish, vault-wide cleanup, or permanent file deletion.
- Use `run <command-id> --risk sensitive --yes` or `run <command-id> --risk destructive --yes` only after the user explicitly confirms that exact command. Normal `run <command-id>` calls are blocked when the command ID or name looks sensitive or destructive.
- For write, sync, commit, push, and task-query workflows, require a target directory containing `.obsidian`; use `--allow-non-vault` only for controlled tests.
- Verify after execution. `Executed: <id>` only means Obsidian accepted the command; it does not prove the plugin completed successfully.
- For Git push failures, inspect the host `git` command output from the script result. Do not route host Git failures through the Obsidian Git plugin; the plugin is fallback-only when host `git` is not found.

## Non-goals and isolated extensions

- Do not merge `obsidian-management` directly into this skill's main workflow. It contains obsolete vault paths and an older Git policy. Keep only its privacy guardrails and high-level vault directory semantics, now captured in `references/vault-safety.md`.
- Do not merge `obsidian-manager` directly into this skill's main workflow. It is a compatibility layer for a specific research-note directory layout and is not a general Obsidian plugin command workflow.
- If research-note templates are needed later, add a separate extension with explicit vault path, directory mapping, and template rules. Keep it independent from journal, Tasks, and Git-sync commands.
- Prefer native Obsidian official CLI lookup through `official-commands` for generic vault operations, and prefer runtime plugin discovery through `commands --plugin <plugin-id>` for community plugin behavior.
