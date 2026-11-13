import json
import pathlib
import sys
import tempfile
import unittest
import datetime as dt


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins.reports import format_today_report, format_week_report
from obsidian_cli_plugins.records import (
    append_record_to_note,
    create_fleeting_record,
    filename_from_title,
    inline_record_line,
    normalize_heading_title,
    record_index_line,
)
from obsidian_cli_plugins.tasks import append_task_to_note, query_today_tasks, query_week_tasks
from obsidian_cli_plugins.journals import apply_auto_template, note_has_target_section, target_date


DEFAULT_FLEETING_TEMPLATE = """---
title: <% tp.file.title %>
category: <% tp.file.path(true).split("/").slice(0, -1).join("/") %>
tags:


<%*
let fullPath = tp.file.path(true).split("/").slice(0, -1);
fullPath.forEach((folder, index) => {
if (folder) {
  tR += `  - "${folder}"\\n`;
}
});
%>
status:
card:
  - fleeting
created: <% tp.date.now("YYYY-MM-DD HH:mm:ss") %>
updated: <% tp.file.last_modified_date("YYYY-MM-DD HH:mm:ss") %>
deadline: <% tp.date.now("YYYY-MM-DD", +7) %>
uid: <% tp.file.title + "-" + tp.date.now("YYYYMMDDHHmmss") %>
author:
  - dxshelley
topic:
issue:
project:
area:
resource: <% tp.file.path(true).split("/").slice(0, -1).join("/") %>
archive:
source:
scenarios:
aliases:
  - <% tp.file.title %>

---
# <% tp.file.title %>

<% tp.file.cursor(1) %>

## 时间

## 场景
- 触发场景：【如：会议讨论/阅读第X页/与某人交流】

## 人物


## 灵感
- 核心内容：【简洁记录灵感要点，不超过5行】

## 思考

- **联想**：这个想法像什么？有哪些隐喻？
- **组合**：如果把A和B看似不相关的东西结合起来会怎样？
- **逆向**：如果反过来呢？如果不考虑限制呢？

## 后续行动

- 后续行动：【如：转化为文献笔记/永久笔记/放弃】

## 参考


<% tp.file.include("[[2-meth-note-tail]]") %>
"""


DEFAULT_TAIL_TEMPLATE = """
***

## 附录

### 来源(Source)


### 关联(Reference)


### 术语(Term)
### 应用(Target)
### 任务(Task)
### 问题(Question)
"""


def setup_quickadd_fleeting(vault: pathlib.Path, template: str = DEFAULT_FLEETING_TEMPLATE) -> None:
    (vault / ".obsidian/plugins/quickadd").mkdir(parents=True)
    (vault / "90_asset/templates").mkdir(parents=True)
    (vault / "90_asset/templates/card-fleeting-note.md").write_text(template, encoding="utf-8")
    (vault / "90_asset/templates/2-meth-note-tail.md").write_text(DEFAULT_TAIL_TEMPLATE, encoding="utf-8")
    (vault / ".obsidian/plugins/quickadd/data.json").write_text(
        '{"choices":[{"name":"fleeting","type":"Template","templatePath":"90_asset/templates/card-fleeting-note.md","folder":{"folders":["00_inbox/fleeting"]}}]}',
        encoding="utf-8",
    )


class TaskReportTests(unittest.TestCase):
    def test_filename_from_title_replaces_windows_reserved_characters(self) -> None:
        self.assertEqual(filename_from_title('How does this work? A <note>|draft*'), "How does this work- A -note-draft-")

    def test_today_and_week_queries_with_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            (vault / ".obsidian/plugins/obsidian-tasks-plugin").mkdir(parents=True)
            (vault / ".obsidian/plugins/obsidian-tasks-plugin/data.json").write_text(
                '{"statusSettings":{"coreStatuses":[],"customStatuses":[]}}',
                encoding="utf-8",
            )
            (vault / "20_plan/21_daily").mkdir(parents=True)
            (vault / "20_plan/22_weekly").mkdir(parents=True)
            (vault / "20_plan/21_daily/2026-06-30.md").write_text(
                "# Daily\n\n"
                "- [ ] #task #work 今天处理拆分 📅 2026-06-30\n"
                "- [x] #task #life 已完成 ✅ 2026-06-30\n",
                encoding="utf-8",
            )
            (vault / "20_plan/22_weekly/2026-W27.md").write_text(
                "# Weekly\n\n"
                "## 本周焦点\n\n"
                "- [ ] #task #work 周任务 🛫 2026-06-29 📅 2026-07-05\n"
                "- [ ] 普通焦点\n",
                encoding="utf-8",
            )

            date = target_date("2026-06-30")
            today = query_today_tasks(vault, date)
            week = query_week_tasks(vault, date)

            self.assertEqual(today["total"], 2)
            self.assertEqual(today["summary"]["status_counts"]["TODO"], 1)
            self.assertEqual(week["summary"]["plain_focus_count"], 1)
            self.assertIn("# 今日待办列表 2026-06-30", format_today_report(today))
            self.assertIn("# 本周待办列表 2026-W27", format_week_report(week))

    def test_auto_template_repairs_interactive_daily_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            note = vault / "20_plan/21_daily/2026-06-30.md"
            template = vault / "90_asset/templates/journal-daily-auto.md"
            note.parent.mkdir(parents=True)
            template.parent.mkdir(parents=True)
            note.write_text("---\njournal: daily\njournal-date: 2026-06-30\n---\n", encoding="utf-8")
            template.write_text(
                "---\ntitle: {{title}}\ncategory: {{category}}\njournal-date: {{date}}\n---\n"
                "# {{title}}_日志\n\n"
                "## 🎯 今日待办\n\n"
                "### 新增任务\n\n"
                "- [ ]\n",
                encoding="utf-8",
            )

            result = apply_auto_template(vault, note, "day", target_date("2026-06-30"))

            self.assertTrue(result["ok"])
            self.assertTrue(note_has_target_section(note, "day"))
            text = note.read_text(encoding="utf-8")
            self.assertIn("title: 2026-06-30", text)
            self.assertIn("category: 20_plan/21_daily", text)
            self.assertIn("### 新增任务", text)

    def test_append_task_fails_when_target_section_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = pathlib.Path(tmp) / "2026-06-30.md"
            original = "---\njournal: daily\njournal-date: 2026-06-30\n---\n"
            note.write_text(original, encoding="utf-8")

            result = append_task_to_note(note, "- [ ] #task #work 测试 📅 2026-06-30", "day")

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "target-section-missing")
            self.assertEqual(note.read_text(encoding="utf-8"), original)

    def test_append_record_index_targets_new_record_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            note = vault / "20_plan/21_daily/2026-06-30.md"
            record_note = vault / "00_inbox/fleeting/中药对身体有害吗.md"
            note.parent.mkdir(parents=True)
            record_note.parent.mkdir(parents=True)
            note.write_text(
                "# 2026-06-30_日志\n\n"
                "## 🎯 今日待办\n\n"
                "### 新增任务\n\n"
                "- [ ]\n\n"
                "## 📝 记录\n\n"
                "## 💭 思考\n\n"
                "## 🔄 今日复盘\n",
                encoding="utf-8",
            )
            record_note.write_text("# 中药对身体有害吗\n", encoding="utf-8")

            index_line = record_index_line(note, record_note, "中药对身体有害吗？")
            result = append_record_to_note(note, index_line, "day")

            self.assertTrue(result["ok"])
            self.assertEqual(normalize_heading_title(result["section"]), "记录")
            text = note.read_text(encoding="utf-8")
            self.assertIn("## 📝 记录\n\n- [中药对身体有害吗？](../../00_inbox/fleeting/中药对身体有害吗.md)\n\n## 💭 思考", text)
            self.assertIn("### 新增任务\n\n- [ ]", text)

    def test_append_inline_record_targets_new_record_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = pathlib.Path(tmp) / "2026-07-01.md"
            note.write_text(
                "# 2026-07-01_日志\n\n"
                "## 📝 记录\n\n"
                "## 💭 思考\n",
                encoding="utf-8",
            )

            line = inline_record_line("王老师 13800000000", dt.datetime(2026, 7, 1, 14, 32))
            result = append_record_to_note(note, line, "day")

            self.assertTrue(result["ok"])
            self.assertEqual(normalize_heading_title(result["section"]), "记录")
            self.assertIn("## 📝 记录\n\n- 14:32 王老师 13800000000\n\n## 💭 思考", note.read_text(encoding="utf-8"))

    def test_append_record_index_keeps_legacy_combined_heading_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            note = vault / "20_plan/21_daily/2026-06-30.md"
            record_note = vault / "00_inbox/fleeting/中药对身体有害吗.md"
            note.parent.mkdir(parents=True)
            record_note.parent.mkdir(parents=True)
            note.write_text(
                "# 2026-06-30_日志\n\n"
                "## 📝 记录与思考\n\n"
                "- 今天最重要的一件事:\n\n"
                "### 专注力\n",
                encoding="utf-8",
            )
            record_note.write_text("# 中药对身体有害吗\n", encoding="utf-8")

            index_line = record_index_line(note, record_note, "中药对身体有害吗？")
            result = append_record_to_note(note, index_line, "day")

            self.assertTrue(result["ok"])
            self.assertEqual(normalize_heading_title(result["section"]), "记录与思考")
            text = note.read_text(encoding="utf-8")
            self.assertIn("## 📝 记录与思考\n\n- [中药对身体有害吗？](../../00_inbox/fleeting/中药对身体有害吗.md)\n- 今天最重要的一件事:", text)

    def test_append_record_fails_when_record_section_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = pathlib.Path(tmp) / "2026-W27.md"
            original = "# Weekly\n\n## 本周焦点\n\n- [ ]\n"
            note.write_text(original, encoding="utf-8")

            result = append_record_to_note(note, "本周记录", "week")

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "record-section-missing")
            self.assertEqual(note.read_text(encoding="utf-8"), original)

    def test_create_fleeting_record_uses_quickadd_template_location_and_existing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)

            result = create_fleeting_record(
                vault_path=vault,
                text="中药对身体有害吗？",
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="medical",
                issue=None,
                scenarios=["晚上喝中药时突然想到的问题"],
                attachments=[],
                related=[],
                external_sources=["NCCIH=https://www.nccih.nih.gov/health/herbsataglance"],
                now=dt.datetime(2026, 6, 30, 20, 31, 0),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["quickadd"]["folder"], "00_inbox/fleeting")
            note = pathlib.Path(result["note"])
            text = note.read_text(encoding="utf-8")
            self.assertIn("status: \"ai_pending\"", text)
            self.assertIn("type: \"text\"", text)
            self.assertIn("source: \"agent/codex\"", text)
            self.assertIn("kind: \"medical\"", text)
            self.assertNotIn("topic:", text)
            self.assertNotIn("issue:", text)
            self.assertNotIn("scenarios:", text)
            self.assertIn("## 灵感\n\n- 核心内容：中药对身体有害吗？", text)
            self.assertIn("## 参考", text)
            self.assertIn("## 附录", text)
            self.assertIn("- [NCCIH](https://www.nccih.nih.gov/health/herbsataglance)", text)
            self.assertNotIn("<%", text)
            self.assertNotIn("[[", text)

    def test_create_fleeting_record_uses_agent_analysis_json_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)

            raw = "今天又下雨了 突然灵光乍现 蚂蚁从飞机上掉下来会摔死吗 记录一下"
            analysis_json = json.dumps(
                {
                    "kind": "灵感",
                    "time_hints": ["今天"],
                    "occurred_on": "2026-07-01",
                    "actors": ["我"],
                    "scenes": ["下雨"],
                    "insight": "蚂蚁从飞机上掉下来会摔死吗",
                    "intent": "记录",
                    "headline": "蚂蚁从飞机上掉下来会摔死吗",
                    "question": "蚂蚁从飞机上掉下来会摔死吗",
                },
                ensure_ascii=False,
            )
            result = create_fleeting_record(
                vault_path=vault,
                text=raw,
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                analysis_json=analysis_json,
                now=dt.datetime(2026, 7, 1, 9, 30, 0),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["headline"], "蚂蚁从飞机上掉下来会摔死吗")
            self.assertEqual(result["question"], "蚂蚁从飞机上掉下来会摔死吗")
            self.assertEqual(result["kind"], "灵感")
            self.assertEqual(result["scenes"], ["下雨"])
            self.assertEqual(result["analysis"]["time_hints"], ["今天"])
            self.assertEqual(result["analysis"]["occurred_on"], "2026-07-01")
            self.assertEqual(result["analysis"]["actors"], ["我"])
            self.assertEqual(result["time_hints"], ["今天"])
            self.assertEqual(result["occurred_on"], "2026-07-01")
            self.assertEqual(result["actors"], ["我"])
            self.assertEqual(result["analysis"]["intent"], "记录")
            self.assertEqual(result["analysis"]["kind"], "灵感")

            text = pathlib.Path(result["note"]).read_text(encoding="utf-8")
            self.assertIn("kind: \"灵感\"", text)
            self.assertIn('time_hints:\n  - "今天"', text)
            self.assertIn('occurred_on: "2026-07-01"', text)
            self.assertIn('actors:\n  - "我"', text)
            self.assertIn("## 时间\n\n- 发生时间：2026-07-01", text)
            self.assertIn("- 时间线索：今天", text)
            self.assertIn("## 场景\n\n- 触发场景：下雨", text)
            self.assertIn("## 人物\n\n- 相关人物：我", text)
            self.assertIn(f"## 灵感\n\n- 核心内容：{raw}", text)
            self.assertIn("- 待分析问题：蚂蚁从飞机上掉下来会摔死吗", text)
            self.assertIn("## 思考\n\n## 后续行动\n\n## 参考", text)
            self.assertNotIn("等待 AI 分析", text)

    def test_create_fleeting_record_uses_insight_as_headline_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)

            raw = "今天又下雨了 突然灵光乍现 蚂蚁从飞机上掉下来会摔死吗 记录一下"
            analysis_json = json.dumps(
                {
                    "kind": "灵感",
                    "occurred_on": "2026-07-01",
                    "scenes": ["下雨"],
                    "insight": "蚂蚁从飞机上掉下来会摔死吗",
                    "intent": "记录",
                },
                ensure_ascii=False,
            )
            result = create_fleeting_record(
                vault_path=vault,
                text=raw,
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/openclaw",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                analysis_json=analysis_json,
                now=dt.datetime(2026, 7, 1, 9, 32, 0),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["headline"], "蚂蚁从飞机上掉下来会摔死吗")
            self.assertEqual(result["question"], "")
            self.assertEqual(pathlib.Path(result["note"]).name, "蚂蚁从飞机上掉下来会摔死吗.md")
            text = pathlib.Path(result["note"]).read_text(encoding="utf-8")
            self.assertIn(f"## 灵感\n\n- 核心内容：{raw}", text)
            self.assertNotIn("- 待分析问题：", text)

    def test_create_fleeting_record_uses_configured_body_sections_and_canonical_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)
            config = {
                "sections": [
                    {"heading": "时间", "fields": ["occurred_on", "time_hints"], "formatter": "time"},
                    {"heading": "场景", "fields": ["scenes"], "formatter": "scenes", "required": True},
                    {"heading": "人物", "fields": ["actors"], "formatter": "actors"},
                    {"heading": "灵感", "fields": ["original_text", "question"], "formatter": "insight", "required": True},
                    {"heading": "思考", "fields": ["reflection"], "formatter": "bullets", "label": "思考"},
                    {"heading": "后续行动", "fields": ["next_actions"], "formatter": "blank", "fill": "never", "required": True},
                ]
            }
            config_path = vault / "90_asset/templates/record-body.json"
            config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
            raw = "今天午后在书房想到雨水循环 记录一下"
            analysis_json = json.dumps(
                {
                    "kind": "灵感",
                    "occurred_on": "2026-07-01",
                    "time_hints": ["今天午后"],
                    "actors": ["我"],
                    "scenes": ["书房", "雨天联想"],
                    "insight": "雨水循环",
                    "headline": "雨水循环",
                    "question": "雨水从哪里来",
                    "reflection": "可以关联水循环和日常观察",
                    "next_actions": ["转成永久笔记"],
                },
                ensure_ascii=False,
            )

            result = create_fleeting_record(
                vault_path=vault,
                text=raw,
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                analysis_json=analysis_json,
                body_config="90_asset/templates/record-body.json",
                now=dt.datetime(2026, 7, 1, 15, 0, 0),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["headline"], "雨水循环")
            self.assertEqual(result["kind"], "灵感")
            self.assertEqual(result["occurred_on"], "2026-07-01")
            self.assertEqual(result["time_hints"], ["今天午后"])
            self.assertEqual(result["actors"], ["我"])
            text = pathlib.Path(result["note"]).read_text(encoding="utf-8")
            self.assertIn("## 时间\n\n- 发生时间：2026-07-01\n- 时间线索：今天午后", text)
            self.assertIn("## 场景\n\n- 触发场景：书房\n- 触发场景：雨天联想", text)
            self.assertIn("## 人物\n\n- 相关人物：我", text)
            self.assertIn(f"## 灵感\n\n- 核心内容：{raw}\n- 待分析问题：雨水从哪里来", text)
            self.assertIn("## 思考\n\n- 思考：可以关联水循环和日常观察", text)
            self.assertIn("## 后续行动\n\n## 参考", text)
            self.assertNotIn("转成永久笔记", text)

    def test_create_fleeting_record_rejects_body_config_using_appendix_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)
            config_path = vault / "90_asset/templates/record-body.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sections": [
                            {"heading": "灵感", "fields": ["source_links"], "formatter": "bullets", "required": True}
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = create_fleeting_record(
                vault_path=vault,
                text="测试",
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                body_config="90_asset/templates/record-body.json",
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "record-body-config-invalid")
            self.assertIn("appendix-reserved", result["detail"])

    def test_create_fleeting_record_normalizes_legacy_analysis_field_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)

            raw = "今天又下雨了 突然灵光乍现 天上的雨是从哪里来的？"
            analysis_json = json.dumps(
                {
                    "classification": "灵感",
                    "time_clues": ["今天"],
                    "event_date": "2026-07-01",
                    "people": ["我"],
                    "scene": "下雨",
                    "inspiration": "天上的雨是从哪里来的？",
                    "title": "天上的雨是从哪里来的",
                    "issue": "天上的雨是从哪里来的？",
                    "action": "记录",
                },
                ensure_ascii=False,
            )
            result = create_fleeting_record(
                vault_path=vault,
                text=raw,
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/openclaw",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                analysis_json=analysis_json,
                now=dt.datetime(2026, 7, 1, 16, 0, 0),
            )

            self.assertTrue(result["ok"])
            self.assertTrue(result["analysis"]["ok"])
            self.assertEqual(result["analysis"]["diagnostics"]["legacy_fields"]["title"], "headline")
            self.assertEqual(result["headline"], "天上的雨是从哪里来的")
            self.assertEqual(result["kind"], "灵感")
            self.assertEqual(result["time_hints"], ["今天"])
            self.assertEqual(result["occurred_on"], "2026-07-01")
            self.assertEqual(result["actors"], ["我"])
            self.assertEqual(result["scenes"], ["下雨"])
            text = pathlib.Path(result["note"]).read_text(encoding="utf-8")
            self.assertIn(f"## 灵感\n\n- 核心内容：{raw}", text)
            self.assertIn("天上的雨是从哪里来的.md", result["relative_note"])

    def test_create_fleeting_record_skips_semantic_analysis_when_json_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)

            raw = "今天又下雨了 突然灵光乍现 蚂蚁从飞机上掉下来会摔死吗 记录一下"
            result = create_fleeting_record(
                vault_path=vault,
                text=raw,
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                now=dt.datetime(2026, 7, 1, 9, 35, 0),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["headline"], raw)
            self.assertEqual(result["kind"], "")
            self.assertEqual(result["scenes"], [])
            self.assertFalse(result["analysis"]["ok"])
            self.assertEqual(result["analysis"]["reason"], "analysis-missing")
            self.assertEqual(result["question"], "")
            text = pathlib.Path(result["note"]).read_text(encoding="utf-8")
            self.assertIn(f"## 灵感\n\n- 核心内容：{raw}", text)
            self.assertIn("## 场景\n\n## 人物", text)

    def test_create_fleeting_record_skips_semantic_analysis_when_json_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault)

            raw = "上班路上看到猫狗打闹 记录一下"
            result = create_fleeting_record(
                vault_path=vault,
                text=raw,
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
                analysis_json="{not json",
                now=dt.datetime(2026, 7, 1, 9, 40, 0),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["headline"], raw)
            self.assertFalse(result["analysis"]["ok"])
            self.assertEqual(result["analysis"]["reason"], "analysis-json-invalid")
            self.assertIn(f"核心内容：{raw}", pathlib.Path(result["note"]).read_text(encoding="utf-8"))

    def test_create_fleeting_record_returns_copied_attachment_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            vault = root / "vault"
            source = root / "source-video.mp4"
            vault.mkdir()
            source.write_bytes(b"video")
            setup_quickadd_fleeting(vault)

            blocked = create_fleeting_record(
                vault_path=vault,
                text="上班路上看到猫狗打闹",
                title=None,
                record_type="video",
                status="ai_pending",
                source="agent/openclaw",
                topic="cat dog",
                issue=None,
                scenarios=[],
                attachments=[str(source)],
                related=[],
                external_sources=[],
                now=dt.datetime(2026, 6, 30, 21, 0, 0),
            )
            self.assertFalse(blocked["ok"])
            self.assertEqual(blocked["reason"], "external-attachment-requires-confirmation")
            self.assertNotIn(str(source), str(blocked))

            result = create_fleeting_record(
                vault_path=vault,
                text="上班路上看到猫狗打闹",
                title=None,
                record_type="video",
                status="ai_pending",
                source="agent/openclaw",
                topic="cat dog",
                issue=None,
                scenarios=[],
                attachments=[str(source)],
                related=[],
                external_sources=[],
                allow_external_attachments=True,
                now=dt.datetime(2026, 6, 30, 21, 0, 0),
            )

            self.assertTrue(result["ok"])
            copied = result["copied_attachments"]
            self.assertEqual(len(copied), 1)
            self.assertEqual(copied[0]["relative_path"], "00_inbox/fleeting/assets/上班路上看到猫狗打闹/source-video.mp4")
            self.assertEqual(copied[0]["source"], "<external-file>")
            self.assertTrue(pathlib.Path(copied[0]["path"]).exists())
            self.assertIn("assets/上班路上看到猫狗打闹/source-video.mp4", pathlib.Path(result["note"]).read_text(encoding="utf-8"))

    def test_create_fleeting_record_requires_real_attachment_for_media(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            setup_quickadd_fleeting(vault)

            result = create_fleeting_record(
                vault_path=vault,
                text="听到一首好听的歌",
                title=None,
                record_type="audio",
                status="ai_pending",
                source="agent/openclaw",
                topic="music",
                issue=None,
                scenarios=[],
                attachments=[str(root / "missing.m4a")],
                related=[],
                external_sources=[],
                allow_external_attachments=True,
                require_attachment=True,
                now=dt.datetime(2026, 7, 2, 9, 0, 0),
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "attachment-path-unavailable")
            self.assertFalse((vault / "00_inbox/fleeting/听到一首好听的歌.md").exists())

    def test_copied_attachment_links_embed_media_and_keep_files_plain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            vault = root / "vault"
            first_source = root / "first" / "clip (1)#tag.mp4"
            second_source = root / "second" / "clip (1)#tag.mp4"
            doc_source = root / "doc (1)#tag.pdf"
            vault.mkdir()
            first_source.parent.mkdir()
            second_source.parent.mkdir()
            first_source.write_bytes(b"first")
            second_source.write_bytes(b"second")
            doc_source.write_bytes(b"doc")
            setup_quickadd_fleeting(vault)

            result = create_fleeting_record(
                vault_path=vault,
                text="重复附件",
                title=None,
                record_type="video",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[str(first_source), str(second_source), str(doc_source)],
                related=[],
                external_sources=[],
                allow_external_attachments=True,
                now=dt.datetime(2026, 6, 30, 21, 30, 0),
            )

            self.assertTrue(result["ok"])
            copied = result["copied_attachments"]
            self.assertEqual(
                [item["relative_path"] for item in copied],
                [
                    "00_inbox/fleeting/assets/重复附件/clip (1)#tag.mp4",
                    "00_inbox/fleeting/assets/重复附件/clip (1)#tag-1.mp4",
                    "00_inbox/fleeting/assets/重复附件/doc (1)#tag.pdf",
                ],
            )
            note_text = pathlib.Path(result["note"]).read_text(encoding="utf-8")
            self.assertIn("![clip (1)#tag](assets/重复附件/clip%20%281%29%23tag.mp4)", note_text)
            self.assertIn("![clip (1)#tag](assets/重复附件/clip%20%281%29%23tag-1.mp4)", note_text)
            self.assertIn("[doc (1)#tag](assets/重复附件/doc%20%281%29%23tag.pdf)", note_text)

    def test_create_fleeting_record_rejects_non_default_template_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            setup_quickadd_fleeting(vault, template="# custom\n")

            result = create_fleeting_record(
                vault_path=vault,
                text="测试",
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/openclaw",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "quickadd-template-required-headings-missing")
            self.assertEqual(result["template"], "90_asset/templates/card-fleeting-note.md")

    def test_quickadd_incomplete_config_does_not_return_raw_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            (vault / ".obsidian/plugins/quickadd").mkdir(parents=True)
            (vault / ".obsidian/plugins/quickadd/data.json").write_text(
                '{"choices":[{"name":"fleeting","secret":"should-not-return"}]}',
                encoding="utf-8",
            )

            result = create_fleeting_record(
                vault_path=vault,
                text="测试",
                title=None,
                record_type="text",
                status="ai_pending",
                source="agent/codex",
                topic="",
                issue=None,
                scenarios=[],
                attachments=[],
                related=[],
                external_sources=[],
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "quickadd-fleeting-incomplete")
            self.assertNotIn("secret", result)
            self.assertNotIn("should-not-return", str(result))


if __name__ == "__main__":
    unittest.main()
