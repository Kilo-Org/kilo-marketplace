# Vault Safety and Content Semantics

Use this file before reading, searching, summarizing, or returning arbitrary Obsidian vault content. These rules were distilled from the older OpenClaw `obsidian-management` skill, but updated for the active `obsidian-cli-plugins` workflow and current vault path discovery.

## Active vault rule

- Do not use the old hard-coded path `~/syncthing/obsidian-2026`.
- Resolve the vault with `doctor`, `OBSIDIAN_VAULT_PATH`, Obsidian config discovery, `--vault current`, an exact `--vault` name, or `--vault-path`.
- On hosts with multiple vaults, inspect `doctor.configured_vaults` and `doctor.resolved_vault` before reading or writing. Do not guess from folder names alone.
- Treat `doctor` output as redacted by default. Use `doctor --verbose` only for local debugging when full absolute paths are necessary.
- Write, Git-mutating, and task-query commands must target a directory containing `.obsidian`; `--allow-non-vault` is only for explicit controlled tests.
- For the current host, the expected fallback is `~/git/obsidian-2026`.
- Keep the Git preflight/edit/push rules from `runtime-sync.md`; do not revive the older "modify first, then ask whether to commit" flow.

## Scope

This skill may:

- Read and write Markdown files inside the resolved vault when the requested workflow requires it.
- Read Obsidian config files only to resolve vault names, paths, and open-vault state.
- Read `.obsidian/community-plugins.json` and plugin manifests/settings only for command discovery and workflow support.
- Run configured local CLIs such as `obsidian`, `git`, and the bundled Python scripts.
- Use official Obsidian or installed plugin commands only after resolving the target vault.
- Persist task query JSON/report outputs to the user's private cache directory with private permissions unless the user explicitly provides another output path.
- Copy external local attachment files into a record only when the exact path was explicitly provided by the user or by current-message Agent runtime attachment metadata, and the command uses `--allow-external-attachments`; redact the original external source path in returned JSON. For arbitrary external paths not tied to the current user message, ask for explicit confirmation first.

This skill must not:

- Read arbitrary files outside the resolved vault except Obsidian config files and explicitly provided paths.
- Follow symlinks that resolve outside the vault during safe reads, searches, task scans, or summaries.
- Read credential files such as API keys, tokens, cookies, password stores, or app login databases.
- Send vault content to external services unless the user explicitly asks for that integration and the target service is named.
- Install, enable, disable, or remove Obsidian plugins/themes without explicit confirmation.
- Modify system settings, Obsidian app settings, or unrelated application data unless the user explicitly requests it.
- Persist copied vault content into another memory/wiki/index store unless the user asks for that durable export.

## Credential handling

- Do not open credential files just to check whether a token exists. Ask the user to provide required credentials through the normal platform mechanism or environment variables.
- If a command needs a credential, report the missing variable or config key name without inspecting secret-bearing files.
- Never echo full credentials, cookies, bearer tokens, API keys, session IDs, or private keys in command output summaries.
- Treat `.obsidian/plugins/*/data.json` as potentially sensitive. Read only the minimal keys required for the current workflow.
- Redact Git and Obsidian command outputs before returning JSON or summaries, especially remotes, URLs, tokens, usernames, cookies, and plugin error details.

## Script-enforced safety gates

The bundled `obsidian_workflows.py` script enforces these rules in code. Do not document or call alternate workflows that bypass them:

- `doctor` redacts local paths and environment-derived paths by default. Use `doctor --verbose` only for local troubleshooting when full absolute paths are necessary.
- `run <command-id>` blocks unknown, sensitive, and destructive command IDs. Sensitive commands include developer/eval/debug/history/sync/publish surfaces; destructive commands include delete, remove, install, enable, uninstall, reset, discard, clear, cleanup, purge, wipe, trash, unlink, disable, restrict, and restore. Execute only after explicit user confirmation, then pass `--risk sensitive --yes` or `--risk destructive --yes`.
- Sync, Git-mutating, note-writing, and task-query commands require the resolved path to contain `.obsidian`. Use `--allow-non-vault` only for a controlled local test, never as a normal workaround.
- Git and Obsidian command outputs are redacted before they are returned in JSON records. Still avoid pasting raw command output manually if it may include remotes, credentials, cookies, server URLs, account IDs, or local absolute paths.
- `today-tasks` and `week-tasks` write report/query artifacts to `~/.cache/obsidian-cli-plugins` by default with private file permissions. Do not restore public `/tmp/obsidian-*.json` defaults.
- Validation commands such as `py_compile` must not leave `__pycache__` or `.pyc` files inside the skill package. Use `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPYCACHEPREFIX`, or remove generated caches before syncing.

## Content areas

Use these directory meanings when routing user requests:

- `20_plan/21_daily/`: daily journals, daily task query blocks, habit fields, daily review.
- `20_plan/22_weekly/`: weekly planning and weekly focus.
- `20_plan/23_monthly/`: monthly goals and monthly tasks.
- `20_plan/24_quarterly/`: quarterly goals and tasks.
- `20_plan/25_annual/`: annual goals and tasks.
- `90_asset/data/pomodoro-data.md`: pomodoro or behavior-tracking data; summarize carefully and avoid over-sharing raw logs.
- `02_area/`: domain knowledge.
- `03_resource/`: collected resources.
- `01_project/`: project notes.

If a request is specifically about daily/weekly/monthly/quarterly/yearly todos, prefer the deterministic task workflows in `obsidian_workflows.py` over ad hoc search.

## Sensitive path skip rules

Do not read or return content from paths that match any of these rules unless the user explicitly requests that exact file and confirms the risk:

- `90_asset/keepassxc/`
- `.env`
- `.gitcredentials`
- Any path segment or filename containing `password`, `passwd`, `secret`, `token`, `apikey`, `api-key`, `private-key`, `credential`, `credentials`, or `keepass`.
- Any file clearly named as a key, certificate, wallet, private backup, or credential store.

When skipped, say the file was skipped because it appears sensitive. Do not quote surrounding lines.

## Redaction rules

Before returning content from arbitrary vault files, scan for sensitive values and redact:

- Usernames/passwords: replace values with `***`.
- API keys, tokens, cookies, sessions, OAuth secrets, SSH keys: hide completely, for example `sk-***` or `***`.
- Mainland China phone numbers: keep first 3 and last 4 digits, for example `138****5678`.
- ID card numbers: keep short prefix/suffix only, for example `310***********1234`.
- Bank cards: keep only last 4 digits where possible.
- Server IPs, ports, internal hosts: generalize when not required, for example `192.168.1.x:xx`.
- Real names, birthdays, ages, addresses, medical details, family details, or other identity clues: summarize or generalize unless the user explicitly asks for their own exact data.
- Business-confidential or explicitly marked confidential content: summarize at a high level or skip if safe redaction is not possible.

If accurate redaction is uncertain, provide a short summary and tell the user that detailed content was withheld due to possible sensitive information.

## Search and summary behavior

- Prefer `safe-search` for locating notes and `safe-read` for returning note snippets. If manual inspection is required, use `rg` for locating notes, then read only the minimal relevant line ranges.
- Avoid dumping entire personal notes, journals, or behavior logs.
- For knowledge notes in `01_project/`, `02_area/`, and `03_resource/`, return titles, paths, headings, and short redacted snippets unless the user asks for more detail.
- For habit, pomodoro, and daily review data, summarize trends and counts instead of exposing raw diary text.
- For tasks, returning task lines is allowed after sensitive path filtering because tasks are the expected user-facing unit.

## Compatibility decision

`obsidian-management` is treated as a historical reference only. Retain its useful privacy and directory semantics, but do not inherit:

- Its obsolete vault path.
- Its manual Tasks query workflow when deterministic script commands exist.
- Its old Git policy of editing first and asking later whether to commit.
