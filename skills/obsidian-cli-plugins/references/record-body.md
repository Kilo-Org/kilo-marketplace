# Record Body Configuration

Use this reference when changing how `record-sync --mode file` fills the middle body sections of a QuickAdd fleeting record.

The record writer keeps these parts outside body configuration:

- Frontmatter shell and stable metadata updates.
- File name and journal index link.
- Attachment copying.
- Appendix sections such as `### 来源(Source)` and `### 关联(Reference)`.

## Unified analysis fields

LLM `--analysis-json` must use only these record fields:

- `kind`: record type or classification, such as `灵感`, `摘录`, `事件`, `反思`.
- `headline`: concise file headline.
- `occurred_on`: concrete date or datetime, such as `2026-07-01`.
- `time_hints`: natural-language time clues, such as `今天`, `昨晚`, `午后`.
- `scenes`: trigger scenes or contexts.
- `actors`: people or entities involved.
- `insight`: distilled core idea. Metadata only; the body still records original `--text`.
- `question`: key question or issue.
- `reflection`: optional reflection.
- `next_actions`: optional follow-up actions.
- `intent`: requested operation, such as `记录`.

Do not use legacy names such as `classification`, `title`, `event_date`, `time_clues`, `people`, `scene`, `scenarios`, `inspiration`, `issue`, or `action`.

Before file-mode record writes, use the shared contract command so every Agent works from the same prompt, schema, current-date context, and golden examples:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today
python3 <skill-dir>/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today --prompt-only
python3 <skill-dir>/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today --analysis-json '<model json>' --normalized-only
```

The script normalizes known legacy aliases for resilience and returns diagnostics, but Agent prompts must still produce the unified field names above.

The script also provides body-only fields:

- `original_text`: the original `--text` body.
- `attachment_links`: links to copied or referenced attachments. Image/audio/video attachments use Markdown image/embed syntax such as `![clip](assets/record/clip.mp4)`; non-media attachments use ordinary links.

## Body config schema

Default body config:

```json
{
  "sections": [
    {"heading": "时间", "fields": ["occurred_on", "time_hints"], "formatter": "time"},
    {"heading": "场景", "fields": ["scenes"], "formatter": "scenes", "required": true},
    {"heading": "人物", "fields": ["actors"], "formatter": "actors"},
    {"heading": "灵感", "fields": ["original_text", "question", "attachment_links"], "formatter": "insight", "required": true},
    {"heading": "思考", "fields": ["reflection"], "formatter": "blank", "fill": "never"},
    {"heading": "后续行动", "fields": ["next_actions"], "formatter": "blank", "fill": "never", "required": true}
  ]
}
```

Use `--body-config <path>` to load a JSON config. Relative paths resolve from the vault root.

Supported formatter values preserve the existing record wording:

- `time`: writes `- 发生时间：...` and `- 时间线索：...`.
- `scenes`: writes `- 触发场景：...`.
- `actors`: writes `- 相关人物：...`.
- `insight`: writes `- 核心内容：<original_text>`, `- 待分析问题：...`, and attachment lines. Media attachment lines keep the `![label](path)` embed form.
- `bullets`: writes generic bullet lines, optionally with `label`.
- `blank`: leaves the section empty.

Use `fill: "never"` for sections that must stay empty even when analysis has data, such as `思考` or `后续行动`.

Use `on_missing: "blank"` to clear a section when fields are empty, or `on_missing: "preserve"` to keep the template text.

## Appendix keywords

Do not use appendix-reserved fields in body config: `source`, `sources`, `source_links`, `reference`, `references`, `reference_links`, `term`, `terms`, `term_links`, `target`, `targets`, `target_links`, `task`, `tasks`, `task_links`, `appendix`, `appendix_sources`, `appendix_references`.

External sources still go to `### 来源(Source)` through `--external-source`. Related note links still go to `### 关联(Reference)` through `--related`.
