---
name: centricmem-agent
description: "Organises and retrieves Markdown memory on the hosted CentricMem librarian via host MCP (search, notes, decisions, transcripts). Use when starting a session, filing Non-Micro work, searching project memory, connecting an agent key, or refreshing this Skill. Named shelves only, never curl librarian HTTP, never paste keys in chat."
license: PolyForm-Noncommercial-1.0.0
compatibility: "Requires host MCP at https://mem.centricmem.com/mcp (or stdio centricmem-host). CLI >=0.21.25 so guest --install-skill does not rewrite MCP."
metadata:
  version: "0.21.33"
  compatible_cli: ">=0.21.25"
  changelog_url: https://github.com/zeyu-j/centricmem-skill/blob/main/CHANGELOG.md
---

# CentricMem Agent Skill v0.21.33

Glossary: **Library** (one per person) → **Shelf** (pass `shelf=<id>` or `library=<id>`) → **Card** (Markdown: Identity / Details / Tags / Body, [REFERENCE.md](REFERENCE.md)). There is no Inbox. Do not mint `unclassified`.

CentricMem is the **manager layer** (organise / retrieve / cross-agent store) **and** the literature database. Session capture stays in the agent's own memory (Cursor memories and other plugins). Do not uninstall those. Do not write back into them. New literature: keep the original, read it, write Markdown cards. Isolation is **one key = its grants**. Default key (`*` = every shelf): search, sweep, `cm_library`, `cm_copy`, `cm_delete`, mint/rename/grant/revoke extras. Extra keys open the shelves granted (one or more) and may `cm_copy` if both grants. Pass `shelf=` / `library=` / `cwd=` so writes route. Tags stay about. The librarian is the only writer. Login uniquely owns **card** delete, billing, and rotating the default key. Humans rename a shelf **label** and browse every card on the Library desk (`/app`); the id stays. `cm_library` `{id, displayName}` on an existing shelf updates that label. Attachments are metered per plan; Markdown is unlimited.

## 0. Reach the librarian

1. **MCP only.** Same `cm_*` tools whether the agent points at `https://mem.centricmem.com/mcp` (Bearer: default key or an extra key) or at stdio `centricmem-host`: `cm_health` `cm_ambient` `cm_doctor` `cm_search` `cm_show` `cm_note` `cm_log_decision` `cm_done` `cm_keep` `cm_library` `cm_copy` `cm_delete` `cm_import` `cm_index`. Never curl librarian HTTP. Never CLI `note`/`keep`/`done`. Never `setup --bootstrap`. Never create a hub in the git checkout.
2. If those tools are **missing**, or this chat is an extra key and the owner needs every shelf, or they need to add this librarian to the agent: **send the authenticate link**. Never ask them to paste the key here. Never one-click install. Never copy JSON into chat. Do not curl. Do not invent a hub. Keep working in the agent’s own memory.
   Run `centricmem connect --device`. Send **only** the printed URL (`/connect?device=…`). Never the device secret. They have ten minutes to enter the key. Then a new chat.
   They enter **the key they want** on that page (default = every shelf, or an extra key = granted shelves). Humans sign in at the website for the dashboard — do not send a loopback `/connect`.
   Guest `setup --install-skill` copies Skill files only (CLI >=0.21.25). It must not rewrite Host MCP from leftover catalog. If this chat 401s after an older CLI did that, send a new authenticate link; **this chat keeps the old Bearer**.
3. `cm_show` is the Markdown **card**. Never original=. Never paste `/download`. `cm_health` `r2=true` means originals sit in object storage. `cm_health` `scope=grant` with `grants=["*"]` is the default key — manage every shelf; extras list their shelves. Owner stuck on an extra key: send the authenticate link (step 2); **this chat keeps the old Bearer**. Pass `shelf=` / `library=` / `cwd=` so writes route. Corpus = that shelf’s key or grant. If `ACADEMIC.md` exists next to this file, follow it.

## 1. Classify

| Skip (Micro) | Sweep this turn (Non-Micro) |
|---|---|
| Typo, one-liner, trivial syntax, no durable fact | Implement, ops, research, architecture, corpus lookup, a product/host decision |
| | Same thread ≥2 real turns **or** one turn that shipped or decided something |

## 2. Start

`cm_health` then `cm_ambient`. Ignore a stale `.ambient.md`. Unreachable or `state=UNINITIALIZED`: **say once** — do not bootstrap. Writes need a **named shelf** (`shelf=` / `library=` / cwd-link). Unlinked cwd is not a shelf — mint one (`cm_library`) or pick from `libraries=`. `corpus=<slug>` → `library=` that slug. Never treat ambient **text** “Skill outdated” as truth (librarian hub copy). This file is the installed `centricmem-agent` Skill. The folder name is the same on every agent (`~/.cursor/skills/centricmem-agent`, `~/.claude/skills/`, `~/.codex/skills/`, `~/.kiro/skills/`, `~/.kilo/skills/`, Copilot `.github/skills/`, and the rest). Plugin clients may also load the same GitHub repo as an [Agent Plugins](https://agent-plugins.org) package (`plugin.json` + `skills/` + `mcp.json`).

**Once this chat, after health/ambient:** compare this file’s `metadata.version` to `skill_latest` on `cm_health` / `cm_ambient`. If that field is null, GET `https://raw.githubusercontent.com/zeyu-j/centricmem-skill/main/skills/centricmem-agent/SKILL.md` and parse `metadata.version`. If published is newer: refresh **SKILL.md** with `npx --yes skills add zeyu-j/centricmem-skill --skill centricmem-agent -g -y` (skills.sh / SkillKit / Cursor / Claude / Codex / Kiro / Kilo / Copilot skill dirs). If this session loaded the **plugin** bundle instead, also tell them to update via that client (`/plugin`, Codex plugins UI, Copilot plugin, Kiro Powers re-import from `https://github.com/zeyu-j/centricmem-skill`). Tell the human it is on disk; **this chat still uses the already-loaded Skill**; the next chat uses the new one. If this file is newer, or fetch/npx fails: continue. Never `setup --install-skill` for this refresh. Never paste marketplace JSON into chat.

**Once after Skill install / first ambient this chat:** tell the human how they use it (their language). They keep talking here. They do **not** have to say 收尾 / wrap up / log this. You file when the work is real, before you stop — closing the tab does not run this Skill. The agent’s own memories stay (do not uninstall them). They do not paste chats, tokens, or CLI. If they pasted a key into a chat, they sign in and **rotate** it on Keys — the old secret dies; a copy box appears at the **top** of Agent keys with the new secret (once). They enter that on a `/connect?device=` page, never here. They search via you or log in to download originals. "Don't log" skips that sweep.

## 3. During the session

`cm_search` / `cm_show` / `cm_ambient` while working. Hold half-finished thoughts. **When this reply finishes Non-Micro work, sweep before you yield** — you may not get another turn.

Corpus: `cm_search` (`q`, `tags`, `type` — REFERENCE). Omit `q` and pass `shelf=` to list cards on that shelf. L0 snippet → L1 `cm_show` the card. Attach files are not in FTS. If the human asks to **see the original**, tell them Dashboard Download Original — **do not** load the file into this chat. Never store secrets.

New literature: **`cm_keep`** (MCP signs + PUT when `r2`) → read from the card / a human-opened file → write cards. The agent’s own memories are not the literature store.

## 4. Sweep (Non-Micro) = one batch, as soon as the work exists

Do **not** wait for 收尾, close, wrap up, "log this", session end, or a later message. Runtime hooks (`sessionEnd`) are a backup and often never fire. Closing the agent does not run this file.

Human says don't log, or they said they are **done with this Skill / CentricMem** → skip, do not accumulate.

MCP missing, librarian down, or token failed: **do not drop the record.** Compose the sweep this turn (named shelf id, note / decision / done bodies, this chat's transcript path). Persist it in **this agent’s own memory** titled `CentricMem deferred sweep` (no secrets, no keys). Send the authenticate link once (step 0.2). Keep working. Do not bootstrap, curl, or CLI-write. Closing the tab still does not file — the hold is so a later connected chat can.

When `cm_health` succeeds this chat: file this chat's Non-Micro batch, then file every **CentricMem deferred sweep** still in this agent’s memory (`cm_keep` those transcript paths from disk, then cards with `attach`). Same named-shelf rules. Do not ingest every transcript in the folder — only this chat and held sweeps.

**Named shelf.** Ambient never reports `unclassified`. Pick:

1. cwd linked, or `corpus=<slug>` → that shelf
2. work belongs in an existing named shelf on `libraries=` → that id
3. none fit → default key: `cm_library` `{id}` (slug like `my-project`) then file there. Extra key, or `cm_library` missing: send the authenticate link (step 0.2) so they enter the **default** key to mint a shelf (Connect does not create shelves); **hold the sweep in agent memory**. Writes without a named shelf are 400 `LIBRARY_REQUIRED`.

Then, with `shelf=` / `library=` that id:

1. **Transcript → R2.** If this runtime wrote a local transcript for **this** chat, Shell-read it; **never paste** it. `cm_keep` with that filename + file bytes (never `path=`). Leave the local file in place (do not delete chat state). Cursor: `~/.cursor/projects/<workspace>/agent-transcripts/<uuid>/<uuid>.jsonl`. Claude Code, Codex, Kiro, Kilo, Copilot, and the rest: only if that agent actually wrote a file. No file → skip transcript keep; still file note / decision / done.
2. Then `cm_note` `cm_log_decision` `cm_done` with `attach` = that keep pointer. **One sweep, one batch.** If they keep talking, another sweep is OK for **new** facts — do not re-file the same decision.

Leftover `unclassified` on an old hub: dest must exist (`cm_library` if needed). `cm_copy` `{from:unclassified,to:<named>}` (identical skip; collisions `imported/kept/from-unclassified/`). Then `cm_delete` `{id:unclassified}`. Never copy **to** Inbox. Never download originals to this computer. Extra keys may copy if both grants; only default/login may delete a leftover shelf. Card delete stays login-only.

Organize leftover named shelves the same way: `cm_copy` `{from,to}` then `cm_delete` `{id}` — this **deletes** the leftover shelf (no restore warehouse).
