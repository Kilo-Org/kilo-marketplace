# CentricMem Agent — how to use

The session loop lives in [SKILL.md](SKILL.md). Agents talk to the hosted librarian **only through host MCP**. Prefer the cloud URL `https://mem.centricmem.com/mcp` (Bearer: the default key, or an extra key with shelf grants). stdio `centricmem-host` is the sandbox fallback when `/health` has no `mcp` field. You do not curl librarian HTTP.

## What you are filing

```text
Library  (one per person — login, billing, delete)
  └── Shelf  (pass shelf=<id> or library=<id>)
        └── Card  (.md or one ##)
              Identity / Details / Tags / Body
              Original (optional) — pointer in Details; bytes in object storage
```

Inbox is gone. Do not mint `unclassified`. Leftover Inbox on an old hub: `cm_copy` `{from:unclassified,to:<named>}` then `cm_delete` `{id:unclassified}`. Never copy **to** Inbox. Tags are about the work. `project:` / `type:` / `#id` in search are index shortcuts, not extra types. Corpus YAML is that shelf’s Details.

## Reach

MCP tools must be present: `cm_health` `cm_ambient` `cm_doctor` `cm_search` `cm_show` `cm_note` `cm_log_decision` `cm_done` `cm_keep` `cm_library` `cm_copy` `cm_delete` `cm_import` `cm_index`.

If they are missing, send the authenticate link. Run `centricmem connect --device` and send **only** the printed `/connect?device=` URL — never the secret, never the key. They have ten minutes. They enter **any** agent key on that page (default = every shelf, extra key = granted shelves) — never in chat. Humans sign in at the website for the dashboard. Do not send a loopback `/connect`. Do not curl. Do not CLI-write. Do not bootstrap.

Config (agent key stays off git):

```json
{
  "mcpServers": {
    "centricmem": {
      "type": "http",
      "url": "https://mem.centricmem.com/mcp",
      "headers": {
        "Authorization": "Bearer <default key or extra key>"
      }
    }
  }
}
```

Sandbox fallback (only if `cm_health` has no `mcp` field, or the origin is not upgraded yet):

```json
{
  "mcpServers": {
    "centricmem": {
      "command": "centricmem-host",
      "env": {
        "CENTRICMEM_URL": "https://mem.centricmem.com",
        "CENTRICMEM_TOKEN": "<default key or extra key>"
      }
    }
  }
}
```

`setup --install-skill` on a guest copies Skill files only (CLI >=0.21.25). It must not merge leftover catalog pairing tokens into Cursor `mcp.json`. Host MCP on a guest is `centricmem connect --device` (cloud `/mcp` Bearer). Local librarian hosts may still merge loopback MCP when `/health` advertises `mcp`. When a key is needed, the agent runs `centricmem connect --device` and sends **only** the printed `/connect?device=` URL (ten minutes; secret stays on the agent). The human enters **any** agent key on that page: default (`*` = every shelf) or an extra key (granted shelves). Never ask them to paste a token in chat. Never one-click install. Never a dashboard “connect this computer”. Token failure: say once; send a new device link; **hold the sweep** (this agent’s memory `CentricMem deferred sweep` + transcript path) until `cm_health` works. Only drop the hold if they said don't log or they stopped using this Skill.

Do **not** call `/download`, HTTP `/delete` (cards), billing, or `/register` `/login`. Humans download originals and **delete cards** on the dashboard. Login uniquely owns **card** delete and billing. The **default** key (`*`) may mint, rename, grant, and revoke extras — that stays HTTP/dashboard/CLI, not these `cm_*` tools, so a new token never lands in chat. Default (and owner login) may `cm_copy` / `cm_delete` leftover shelves (`cm_delete` is delete, not archive — no restore). Extra keys cannot manage keys or delete a leftover shelf; they may `cm_copy` if both grants. Attachments are metered per plan (Lite 100MB, Education 200MB, Pro 1GB, Ultra 10GB; operator uncapped). Over quota, `cm_keep` fails — say so; do not drop bytes silently.

## Search and show

Progressive disclosure:

| Layer | Call | What you get |
|-------|------|----------------|
| L0 | `cm_search` | snippet from the Markdown **card** |
| L1 | `cm_show` | the card — agent context |
| Original | human Dashboard **Download Original** | attach bytes. Not FTS. Not agent context |

Never ask `cm_show` for originals. Never paste download URLs into the chat.

Useful query bits (in `q` / `tags` / `type`): `filter`, `tag`, `type:decision`, `#0016` / `id:0016`. Bare word `decision` is full-text, not a type filter. `all` does not leak other shelves. An extra key’s `all` is only the shelves on that key’s grants. Pass `shelf=` / `library=` / `cwd=` when the Bearer can open more than one shelf. Isolation: **one key = its grants**. The owner's agent Bearer is the **default** key (`*` = every shelf).

| Situation | Do |
|-----------|-----|
| Session start | `cm_health` + `cm_ambient` (never a stale `.ambient.md`). Then refresh Skill if published `version` is newer |
| Why we chose X | `cm_search` (decision) |
| What we know | `cm_search` + lessons / `tags` |
| Human wants the file | tell them Dashboard Download Original |
| Durable work just finished | pick a **named** shelf (or `cm_library`), then one MCP sweep **this turn** |
| Librarian down / token failed | compose the sweep anyway; this agent’s memory `CentricMem deferred sweep`; connect link once; file the hold when health succeeds |
| Leftover named shelf or leftover Inbox | dest must exist; `cm_copy` `{from,to}` on the librarian, then `cm_delete` `{id}`. Never download originals here. Never `to=unclassified` |
| Structured corpus (`corpus=slug`) | `library=` that slug; `cm_search` then `cm_show` the **card**, not a dump page |

Empty ambient + Work/Ops → do not deep-search; execute, then sweep this turn.

## Skill refresh (once per chat)

Guests install from GitHub, not from the librarian disk. `cm_health` `min_skill` is the HTTP floor. `skill_latest` is the published Skill (env `CENTRICMEM_SKILL_LATEST` on the librarian) — it is **never** the hub’s `skills/centricmem-agent/SKILL.md`.

1. Read `version` from this Skill’s frontmatter (`metadata.version`).
2. `latest` = JSON `skill_latest` if present, else `metadata.version` at `https://raw.githubusercontent.com/zeyu-j/centricmem-skill/main/skills/centricmem-agent/SKILL.md`.
3. If `latest` is newer: `npx --yes skills add zeyu-j/centricmem-skill --skill centricmem-agent -g -y` (portable SKILL.md for Cursor, Claude, Codex, Kiro, Kilo, Copilot, skills.sh, SkillKit). If this session is a **plugin** install, also update via that client (`/plugin`, Codex plugins UI, Copilot plugin, Kiro Powers re-import). Say once: on disk now; this chat still uses the loaded copy.
4. If this file is newer, or the fetch/npx fails: continue. Do not `setup --install-skill`.

## Writes (one sweep as soon as Non-Micro work exists)

Hold half-finished thoughts. When the chunk is done, file **before you stop talking**. Closing the agent does not run this Skill. Do not wait for session end or for the human to say wrap up.

| Type | When | MCP |
|------|------|------|
| Transcript | Each Non-Micro sweep | Shell-read jsonl → `cm_keep` filename + bytes (MCP does sign+PUT) |
| Session | Same sweep | `cm_done` with `attach` |
| Knowledge | durable model / fact | `cm_note` |
| Decision | architecture or durable host fact | `cm_log_decision` |
| Original | a file worth keeping | `cm_keep` as above. Never `path=` |
| Shelf | none of the named shelves fit | `cm_library` `{id}` (default key). Extra: authenticate so they enter the **default** key. Connect does not mint a shelf |
| Shelf label | human wants a different display name | they rename on the Library desk; or default key `cm_library` `{id, displayName}` (id stays) |
| Copy shelf | leftover named shelf (or leftover Inbox) should live on another | `cm_copy` `{from,to}`. Dest must exist. Extra keys need both grants. Never download originals here. Never `to=unclassified` |
| Delete leftover shelf | leftover is empty or already copied | `cm_delete` `{id}` (default key or login). Extra keys cannot. Leftover Inbox may be the source. This is delete, not archive |
| Bundle | capture import | `cm_import` with `library=` a named shelf |
| Index | after bulk import | `cm_index` |

Later sweeps in the same chat are OK for **new** facts. Do not re-file the same decision.

Do not send `path=` for the librarian to open a server file. Mention `#NNNN` in a decision body when linking units.

Cursor already writes `~/.cursor/projects/<workspace>/agent-transcripts/<uuid>/<uuid>.jsonl`. Shell-read it; never paste jsonl; never delete that local file.

Claude Code, Codex, Kiro, Kilo, Copilot, and other Agent Skills clients: only keep a transcript if that runtime actually wrote a local file for **this** chat. If there is no file, say so; do not invent a dump. Never paste the bytes into chat.

## Do not

- Curl librarian HTTP (or CLI `note` / `keep` / `done`) when MCP is the Skill path
- Wait for 收尾 / close / wrap up / "log this" before filing finished Non-Micro work
- `setup --bootstrap` on a guest machine
- Uninstall the agent’s own memories or write back into them
- Put secrets in cards
- Ask the human to paste a key, token, or transcript jsonl. If they leaked a key, they sign in and rotate it on Keys.
- Load attach originals into the chat
- Treat this git checkout as the memory disk
- Write `unclassified` — pick or create a named shelf. Writes without one are 400 `LIBRARY_REQUIRED`.
