# Obsidian Official CLI Reference

Use this file when a user asks for native Obsidian CLI commands, non-plugin note operations, or a broad command lookup beyond installed community plugin command IDs.

## When to use

- Use official CLI commands for generic vault operations: create, read, append, search, tags, properties, links, tabs, workspaces, templates, themes, plugins, sync, publish, and developer inspection.
- Use `commands --plugin <plugin-id>` for installed community plugin command IDs such as `obsidian-tasks-plugin`, `obsidian-linter`, and `journals`.
- Git workflows prefer the host `git` executable for status, pull, push, commit, and sync. `obsidian-git:*` command IDs are fallback-only when host `git` is not found.
- Use the task/Git/Journals workflow commands in this skill for journal todos and vault edits; they contain sync, conflict, placement, and verification guardrails that the official CLI reference does not provide.
- Treat sensitive or destructive official commands such as developer/eval/debug commands, `delete`, `theme:install`, `theme:uninstall`, `plugin:enable`, `plugin:install`, `plugin:uninstall`, `workspace:delete`, `history:restore`, `sync:restore`, and `publish:remove` as confirmation-required.

## Runtime assumptions

- Obsidian 1.12+.
- Obsidian is running.
- Obsidian CLI is enabled in Settings > General.
- `obsidian` is available in PATH or configured with `OBSIDIAN_BIN`.

## Platform notes

- macOS and Windows installers usually expose the `obsidian` binary directly; still verify with `doctor` or `obsidian version`.
- Linux packaged launchers may inject Electron flags that break CLI argument parsing. Prefer a clean wrapper script in PATH before the desktop launcher when CLI calls fail unexpectedly.
- For Linux services or agent runtimes that call the official CLI through IPC, ensure the runtime can access Obsidian's IPC socket. In systemd service contexts, `PrivateTmp=false` may be required.
- If Obsidian is installed via Flatpak, use a wrapper such as `flatpak run md.obsidian.Obsidian "$@"` and point `OBSIDIAN_BIN` at it.
- Do not enable developer commands (`eval`, `dev:cdp`, `dev:dom`, `dev:console`, `dev:debug`, screenshots) in unattended flows unless the user explicitly asks and the vault/app context is trusted.

## Stable lookup command

Prefer the bundled script so agents can query this index without loading this reference:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py official-commands
python3 <skill-dir>/scripts/obsidian_workflows.py official-commands --category files
python3 <skill-dir>/scripts/obsidian_workflows.py official-commands --search property --json
```

## Syntax

```bash
obsidian vault="Vault Name" <command> name=value flag
obsidian read file="Note"
obsidian read path="folder/Note.md"
obsidian append path="folder/Note.md" content="- [ ] #task #work Example"
```

- Put `vault="..."` before the command when targeting a specific vault.
- Use `file=Name` for wikilink-style lookup.
- Use `path=folder/file.md` for exact path lookup.
- Use `name=value` or `name="value with spaces"` for parameters.
- Flags are bare words.
- Use `\n` inside content strings for newlines when invoking from a shell.

## Imported command categories

The index was imported from `obsidian-cli-official@4.0.2` as a reference layer:

- `general`: `help`, `version`, `reload`, `restart`.
- `daily`: `daily`, `daily:path`, `daily:read`, `daily:append`, `daily:prepend`.
- `files`: `file`, `files`, `folder`, `folders`, `open`, `create`, `read`, `append`, `prepend`, `move`, `rename`, `delete`.
- `search`: `search`, `search:context`, `search:open`.
- `tasks`: `tasks`, `task`.
- `tags`: `tags`, `tag`.
- `properties`: `properties`, `property:set`, `property:remove`, `property:read`.
- `links`: `backlinks`, `links`, `unresolved`, `orphans`, `deadends`.
- `commands-hotkeys`: `commands`, `command`, `hotkeys`, `hotkey`.
- `tabs-workspaces`: `tabs`, `tab:open`, `workspace`, `workspaces`, `workspace:load`, `workspace:save`, `workspace:delete`.
- `history-diff`: `diff`, `history`, `history:list`, `history:read`, `history:restore`, `history:open`.
- `sync`: `sync`, `sync:status`, `sync:history`, `sync:read`, `sync:restore`, `sync:open`, `sync:deleted`.
- `publish`: `publish:site`, `publish:list`, `publish:status`, `publish:add`, `publish:remove`, `publish:open`.
- `themes-snippets`: `themes`, `theme`, `theme:set`, `theme:install`, `theme:uninstall`, `snippets`, `snippets:enabled`, `snippet:enable`, `snippet:disable`.
- `plugins`: `plugins`, `plugins:enabled`, `plugins:restrict`, `plugin`, `plugin:enable`, `plugin:disable`, `plugin:install`, `plugin:uninstall`, `plugin:reload`.
- `developer`: `devtools`, `eval`, `dev:screenshot`, `dev:console`, `dev:errors`, `dev:css`, `dev:dom`, `dev:cdp`, `dev:debug`, `dev:mobile`.
- Other categories: `aliases`, `outline`, `bookmarks`, `bases`, `templates`, `vault`, `random`, `unique`, `web`, `wordcount`, `recents`.

## Obsidian Manager comparison decision

Do not merge `obsidian-manager` into the main workflow. It is a backward-compatibility layer for a specific research-note directory layout and points users to `knowledge obsidian`. If research-note templates are needed later, add a separate optional extension under `references/extensions.md` and keep it isolated from vault-wide journal, Git, and Tasks workflows.
