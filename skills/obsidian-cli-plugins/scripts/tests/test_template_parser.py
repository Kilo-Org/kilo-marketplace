import pathlib
import sys
import tempfile
import unittest

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import obsidian_cli_plugins.template_parser as template_parser
from obsidian_cli_plugins.template_parser import field_names, parse_fragment_template, parse_markdown_structure


class TemplateParserTests(unittest.TestCase):
    def test_parse_heading_tree_strips_icons_and_numbers(self) -> None:
        markdown = "\n".join(
            [
                "# 🚀 项目记录",
                "## 1. 项目概览",
                "### ✅ 功能需求",
                "### 🧭 非功能需求",
                "## 二、附录",
                "### 📝 任务(Task)",
            ]
        )

        structure = parse_markdown_structure(markdown, source="template.md")

        self.assertIn("项目记录/项目概览/功能需求", structure["by_id"])
        self.assertIn("项目记录/项目概览/非功能需求", structure["by_id"])
        self.assertIn("项目记录/附录/任务(Task)", structure["by_id"])
        self.assertEqual(structure["by_id"]["项目记录/项目概览/功能需求"]["title"], "功能需求")

    def test_target_id_escapes_slashes_inside_titles(self) -> None:
        structure = parse_markdown_structure("# 项目\n## 子项目/任务1\n", source="template.md")

        self.assertIn("项目/子项目~1任务1", structure["by_id"])

    def test_markdown_it_parser_ignores_fenced_code_headings(self) -> None:
        markdown = "\n".join(
            [
                "# 项目",
                "```md",
                "## 不应解析",
                "```",
                "## 应解析",
            ]
        )

        structure = parse_markdown_structure(markdown, source="template.md")

        self.assertIn("项目/应解析", structure["by_id"])
        self.assertNotIn("项目/不应解析", structure["by_id"])

    def test_fallback_parser_is_used_when_markdown_it_is_missing(self) -> None:
        original = template_parser.MarkdownIt
        template_parser.MarkdownIt = None
        try:
            structure = parse_markdown_structure("# 项目\n## 功能需求\n", source="template.md")
        finally:
            template_parser.MarkdownIt = original

        self.assertIn("项目/功能需求", structure["by_id"])
        self.assertEqual(structure["by_id"]["项目/功能需求"]["parser"], "fallback")

    def test_fragment_template_fields(self) -> None:
        self.assertEqual(
            field_names("- 需求：\n  来源：\n  使用场景：\n"),
            ["需求", "来源", "使用场景"],
        )

    def test_parse_fragment_template(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = pathlib.Path(td)
            fragment = vault / "90_asset/templates/card-project-fr.md"
            fragment.parent.mkdir(parents=True)
            fragment.write_text("- 需求：\n  状态：\n", encoding="utf-8")

            schema = parse_fragment_template(vault, fragment, kind="functional")

            self.assertEqual(schema["path"], "90_asset/templates/card-project-fr.md")
            self.assertEqual(schema["kind"], "functional")
            self.assertEqual(schema["fields"], ["需求", "状态"])


if __name__ == "__main__":
    unittest.main()
