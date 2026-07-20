# Obsidian Record Workflows

Use this file when adding records, cards, file-mode records, or attachment-backed records. Use `task-add.md` for todo/task additions.

## Inline record default

Use this when the user says `记录 <content>`, `记一条`, `添加记录`, `加到今日记录`, or equivalent and does not request a separate file/card/analysis/attachment workflow.

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py record-sync --mode inline --period <day|week|month|quarter|year> --date today --text "<original record content>"
```

Default period mapping:

- unspecified, 今日, 今天, 日: `--period day`
- 本周, 周: `--period week`
- 本月, 月: `--period month`
- 本季度, 季度: `--period quarter`
- 本年, 今年, 年: `--period year`

Rules:

- Put the user's original record content in `--text`; do not expand, polish, summarize, translate, or rewrite it.
- Remove only the explicit command wrapper when isolating the content.
- Default inline records render as `- HH:mm <original record content>` under `记录`, with legacy `记录与思考` journals still supported.
- Inline records do not create independent record files, wiki links, or tags in the journal index.
- Use local-only `record` only when explicitly requested.

For cross-agent inline record calls, prefer:

```bash
python3 <skill-dir>/scripts/obs_record_sync.py --mode inline --period <period> --date today --text "<original record content>"
```

## File-mode records

Use `--mode file` only when the user explicitly asks for a separate record file, card, note, link, analysis, long-term capture, attachment handling, or knowledge processing.

Before writing, obtain the shared analysis contract, analyze with the Agent application's own model, optionally normalize, then write:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today --prompt-only
python3 <skill-dir>/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today --analysis-json '<model json>' --normalized-only
python3 <skill-dir>/scripts/obs_record_sync.py --mode file --period day --date today --text "<original record content>" --analysis-json '<normalized model json>'
```

Accuracy rules:

- Treat `--analysis-json` as metadata only. It may affect headline, kind, question, time, actors, and scenes, but must not replace the `--text` body.
- Do not treat hand-written field extraction, fixed local rules, or manually assembled JSON as semantic analysis.
- If model-side analysis is unavailable, fails, or produces no useful fields, do not block the record write; pass original `--text` and omit unsupported analysis fields. Do not claim semantic analysis succeeded.
- Use only unified fields from `record-body.md`: `kind`, `headline`, `occurred_on`, `time_hints`, `scenes`, `actors`, `insight`, `question`, `reflection`, `next_actions`, and `intent`.
- The script normalizes known legacy aliases for resilience, but prompts should ask for unified field names.

File-mode behavior:

1. Run the same preflight cleanup as `add-task-sync` unless `--no-pull` is explicitly used for a controlled test.
2. Ensure the target period journal exists using the same journal creation rules as task additions.
3. Read QuickAdd choice `fleeting` from `.obsidian/plugins/quickadd/data.json`; render its configured template, normally `90_asset/templates/card-fleeting-note.md`, and write to its configured folder, normally `00_inbox/fleeting`.
4. Stop if QuickAdd choice, template, folder config, frontmatter, or required template sections are missing.
5. Required sections include `## 场景`, `## 灵感`, `## 后续行动`, `### 来源(Source)`, and `### 关联(Reference)`.
6. Fill body sections using `record-body.md`; default content maps time to `## 时间`, scenes to `## 场景`, actors to `## 人物`, and original `--text` plus question/attachments to `## 灵感`.
7. Insert only a standard Markdown relative-path link under the journal note's `记录` section. Do not use wiki links or add tags in the journal index.
8. Put weak internal Obsidian references under `### 关联(Reference)` and external source links under `### 来源(Source)`.

## Attachments and media

When the user request includes, uploads, records, or otherwise supplies media/file attachments, create a file-mode record and copy attachments in the same command. Images, videos, audio, and ordinary files use the same attachment workflow:

```bash
python3 <skill-dir>/scripts/obs_record_sync.py --mode file --period day --date today --text "<original record content>" --type mixed --analysis-json '<normalized model json>' --attach "<path>" --require-attachment --allow-external-attachments
```

Rules:

- Pass every readable attachment path with `--attach`.
- Pass `--require-attachment` whenever the request includes an attachment, even if `--type` remains `text`.
- Pass `--allow-external-attachments` only when the user message or Agent runtime supplied that exact external local path.
- Required/media records must copy at least one real local attachment into the record assets folder. Missing paths, stale staged ids, URL-only attachments, and plain Markdown links do not satisfy `--require-attachment`.
- Image/audio/video attachments in the record body use Markdown image/embed syntax such as `![clip](assets/record/clip.mp4)`. Non-media attachments remain ordinary links.
- Do not create the record first and then ask whether to attach already supplied media.
- External source paths are redacted as `<external-file>` in JSON; do not echo raw local paths unless the user asks for local debugging.

For media-only messages followed by a later text command, first stage readable local files, then list pending media with the TTL-aware command:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py attachment-stage --path "<path>" --type <image|audio|video|file> --batch-key "<conversation-or-message-group>"
python3 <skill-dir>/scripts/obsidian_workflows.py attachment-pending --batch-key "<conversation-or-message-group>" --ttl-hours 48
python3 <skill-dir>/scripts/obs_record_sync.py --mode file --period day --date today --text "<later text>" --type mixed --analysis-json '<normalized model json>' --staged-attachment "batch:<conversation-or-message-group>" --require-attachment
```

Staged attachments are private cache items, not Obsidian records. `attachment-pending` is the only listing command for record consumption; do not use `attachment-list --batch-key default`, stale staged ids from model memory, or direct reads under `~/.cache/obsidian-cli-plugins/staged-attachments`. Load `openclaw.md` for the full cross-agent state machine, success criteria, and unsupported-channel failure rules.

For OpenClaw phone channels, also load `openclaw.md` before claiming same-turn media support. Current guidance: WeCom `mixed` is preferred for mobile media + text when readable paths are exposed; QQBot can work when every referenced media item has a readable local path; Feishu and current `openclaw-weixin` are not supported for attachment-backed records unless another layer exposes readable local paths.

## Success criteria

For sync-backed records, success requires returned JSON with `ok=true`, no conflict state, the expected journal update, and clean/synced Git status after push. In file mode, verify `record_file.copied_attachments` matches the requested/uploaded attachment count before claiming success.
