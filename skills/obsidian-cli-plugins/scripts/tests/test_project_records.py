import datetime as dt
import json
import pathlib
import tempfile
import unittest

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"

import sys

sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins.project_records import append_project_entry, create_project_note


def target_id(*parts: str) -> str:
    return "/".join(parts)


class ProjectRecordsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.vault = pathlib.Path(self.temp.name)
        (self.vault / ".obsidian").mkdir()
        templates = self.vault / "90_asset/templates"
        templates.mkdir(parents=True)
        (templates / "2-meth-note-tail.md").write_text(
            "\n***\n\n## 附录\n\n### 来源(Source)\n\n\n### 关联(Reference)\n\n\n### 术语(Term)\n### 应用(Target)\n### 任务(Task)\n### 问题(Question)\n",
            encoding="utf-8",
        )
        (templates / "card-project-incubating-note.md").write_text(
            "\n".join(
                [
                    "---",
                    "title: <% tp.file.title %>",
                    "aliases:",
                    "  - <% tp.file.title %>",
                    'category: <% tp.file.path(true).split("/").slice(0, -1).join("/") %>',
                    "tags:",
                    "  - project",
                    "author:",
                    "  - dxshelley",
                    'created: <% tp.date.now("YYYY-MM-DD HH:mm:ss") %>',
                    'updated: <% tp.date.now("YYYY-MM-DD HH:mm:ss") %>',
                    "type: project",
                    "status: idea",
                    "priority: medium",
                    "project_stage: idea",
                    "last_capture:",
                    "capture_count: 0",
                    "landing_threshold:",
                    "---",
                    "***",
                    "",
                    "# <% tp.file.title %>",
                    "",
                    "## 1. 项目概览",
                    "",
                    "### 一句话定位",
                    "",
                    "### 使用场景",
                    "",
                    "### 落地判断",
                    "",
                    "## 2. 原始灵感",
                    "",
                    "- HH:mm 原始想法：",
                    "",
                    "## 3. 需求与约束",
                    "",
                    "### 功能需求",
                    "",
                    "### 非功能需求",
                    "",
                    "### 边界约束",
                    "",
                    "## 4. 设计方案",
                    "",
                    "### 信息结构",
                    "",
                    "### 交互流程",
                    "",
                    "### 实现入口",
                    "",
                    "## 5. 决策与风险",
                    "",
                    "### 决策",
                    "",
                    "### 风险",
                    "",
                    "### 取舍",
                    "",
                    "## 6. 推进状态",
                    "",
                    "### 当前状态",
                    "",
                    "### 阶段回顾",
                    "",
                    "### 下一步摘要",
                    "",
                    '<% tp.file.include("[[2-meth-note-tail]]") %>',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (templates / "card-project-fr.md").write_text(
            "- 需求：\n  来源：\n  使用场景：\n  价值：\n  优先级：\n  状态：\n",
            encoding="utf-8",
        )
        (templates / "card-project-nfr.md").write_text(
            "- 约束：\n  类型：\n  影响：\n  判断标准：\n  状态：\n",
            encoding="utf-8",
        )
        (templates / "card-project-decision.md").write_text(
            "- 时间：\n  背景：\n  决策：\n  原因：\n  影响：\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_project_note_uses_incubating_structure(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)

        result = create_project_note(
            self.vault,
            title="项目灵感记录功能",
            folder="01_project/obsidian",
            landing_threshold="核心需求清晰后落地",
            now=now,
        )

        self.assertTrue(result["ok"], result)
        note = self.vault / "01_project/obsidian/项目灵感记录功能.md"
        content = note.read_text(encoding="utf-8")
        self.assertIn('project_stage: "idea"', content)
        self.assertIn('landing_threshold: "核心需求清晰后落地"', content)
        self.assertIn("## 2. 原始灵感", content)
        self.assertIn("## 6. 推进状态", content)
        self.assertIn("### 任务(Task)", content)
        self.assertIn("### 问题(Question)", content)
        self.assertIn("## 附录", content)

    def test_create_project_note_quotes_yaml_scalars_from_template(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)

        result = create_project_note(
            self.vault,
            title="API: 项目记录",
            folder="01_project/obsidian",
            landing_threshold="需求: 清晰后落地",
            now=now,
        )

        self.assertTrue(result["ok"], result)
        content = (self.vault / "01_project/obsidian/API- 项目记录.md").read_text(encoding="utf-8")
        self.assertIn('title: "API: 项目记录"', content)
        self.assertIn('  - "API: 项目记录"', content)
        self.assertIn('uid: "API: 项目记录-20260702093000"', content)
        self.assertIn('landing_threshold: "需求: 清晰后落地"', content)

    def test_append_default_entry_goes_to_original_ideas(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)
        create_project_note(self.vault, title="项目灵感记录功能", folder="01_project/obsidian", now=now)

        result = append_project_entry(
            self.vault,
            project="项目灵感记录功能",
            text="想到的项目细节应该随时追加到项目文件",
            analysis_json=json.dumps({"target_id": target_id("项目灵感记录功能", "原始灵感"), "text": "想到的项目细节应该随时追加到项目文件", "fields": {}}, ensure_ascii=False),
            now=dt.datetime(2026, 7, 2, 10, 5),
        )

        self.assertTrue(result["ok"], result)
        content = (self.vault / "01_project/obsidian/项目灵感记录功能.md").read_text(encoding="utf-8")
        self.assertIn("- 10:05 原始想法：想到的项目细节应该随时追加到项目文件", content)
        self.assertIn("capture_count: 1", content)

    def test_append_task_and_question_use_tail_sections(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)
        create_project_note(self.vault, title="项目灵感记录功能", folder="01_project/obsidian", now=now)

        task = append_project_entry(
            self.vault,
            project="01_project/obsidian/项目灵感记录功能.md",
            section="task",
            text="实现 project-record-sync 命令",
            analysis_json=json.dumps({"target_id": target_id("项目灵感记录功能", "附录", "任务(Task)"), "text": "实现 project-record-sync 命令", "fields": {"任务": "实现 project-record-sync 命令"}}, ensure_ascii=False),
            now=dt.datetime(2026, 7, 2, 10, 10),
        )
        question = append_project_entry(
            self.vault,
            project="01_project/obsidian/项目灵感记录功能.md",
            section="question",
            text="自动归类是否需要默认关闭？",
            analysis_json=json.dumps({"target_id": target_id("项目灵感记录功能", "附录", "问题(Question)"), "text": "自动归类是否需要默认关闭？", "fields": {"问题": "自动归类是否需要默认关闭？"}}, ensure_ascii=False),
            now=dt.datetime(2026, 7, 2, 10, 20),
        )

        self.assertTrue(task["ok"], task)
        self.assertTrue(question["ok"], question)
        content = (self.vault / "01_project/obsidian/项目灵感记录功能.md").read_text(encoding="utf-8")
        task_index = content.index("### 任务(Task)")
        question_index = content.index("### 问题(Question)")
        self.assertGreater(content.index("- [ ] 实现 project-record-sync 命令"), task_index)
        self.assertGreater(content.index("- 问题：自动归类是否需要默认关闭？"), question_index)

    def test_append_functional_requirement_uses_block_template(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)
        create_project_note(self.vault, title="项目灵感记录功能", folder="01_project/obsidian", now=now)

        result = append_project_entry(
            self.vault,
            project="项目灵感记录功能",
            section="functional",
            text="支持指定 section 追加项目内容",
            analysis_json=json.dumps({"target_id": target_id("项目灵感记录功能", "需求与约束", "功能需求"), "text": "支持指定 section 追加项目内容", "fields": {"需求": "支持指定 section 追加项目内容"}}, ensure_ascii=False),
            now=dt.datetime(2026, 7, 2, 10, 30),
        )

        self.assertTrue(result["ok"], result)
        content = (self.vault / "01_project/obsidian/项目灵感记录功能.md").read_text(encoding="utf-8")
        self.assertIn("- 需求：支持指定 section 追加项目内容", content)
        self.assertNotIn("  使用场景：", content)

    def test_append_functional_requirement_prefers_fragment_template(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)
        create_project_note(self.vault, title="项目灵感记录功能", folder="01_project/obsidian", now=now)
        templates = self.vault / "90_asset/templates"
        (templates / "card-project-fr.md").write_text("- 需求：{{text}}\n  状态：待整理\n", encoding="utf-8")

        result = append_project_entry(
            self.vault,
            project="项目灵感记录功能",
            section="functional",
            text="使用手动小模板格式化功能需求",
            analysis_json=json.dumps({"target_id": target_id("项目灵感记录功能", "需求与约束", "功能需求"), "text": "使用手动小模板格式化功能需求", "fields": {"需求": "使用手动小模板格式化功能需求"}}, ensure_ascii=False),
            now=dt.datetime(2026, 7, 2, 10, 40),
        )

        self.assertTrue(result["ok"], result)
        content = (self.vault / "01_project/obsidian/项目灵感记录功能.md").read_text(encoding="utf-8")
        self.assertIn("- 需求：使用手动小模板格式化功能需求", content)
        self.assertIn("  状态：待整理", content)

    def test_append_decision_template_fills_bullet_time(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)
        create_project_note(self.vault, title="项目灵感记录功能", folder="01_project/obsidian", now=now)
        (self.vault / "90_asset/templates/card-project-decision.md").write_text(
            "- 时间：\n  背景：\n  决策：\n  原因：\n  影响：\n",
            encoding="utf-8",
        )

        result = append_project_entry(
            self.vault,
            project="项目灵感记录功能",
            section="decision",
            text="采用项目记录命令",
            analysis_json=json.dumps({"target_id": target_id("项目灵感记录功能", "决策与风险", "决策"), "text": "采用项目记录命令", "fields": {"决策": "采用项目记录命令"}}, ensure_ascii=False),
            now=dt.datetime(2026, 7, 2, 10, 50),
        )

        self.assertTrue(result["ok"], result)
        content = (self.vault / "01_project/obsidian/项目灵感记录功能.md").read_text(encoding="utf-8")
        self.assertIn("- 时间：2026-07-02 10:50", content)
        self.assertIn("  决策：采用项目记录命令", content)

    def test_append_requires_analysis_json(self) -> None:
        now = dt.datetime(2026, 7, 2, 9, 30)
        create_project_note(self.vault, title="项目灵感记录功能", folder="01_project/obsidian", now=now)

        result = append_project_entry(
            self.vault,
            project="项目灵感记录功能",
            text="没有分析 JSON 不允许写入",
            now=dt.datetime(2026, 7, 2, 10, 55),
        )

        self.assertFalse(result["ok"], result)
        self.assertEqual(result["reason"], "project-analysis-required")


if __name__ == "__main__":
    unittest.main()
