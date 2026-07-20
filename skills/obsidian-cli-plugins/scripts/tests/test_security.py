import pathlib
import sys
import tempfile
import unittest


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins.obsidian import command_risk
from obsidian_cli_plugins.tasks import all_vault_tasks
from obsidian_cli_plugins.vault_content import safe_read, safe_search


class SecurityTests(unittest.TestCase):
    def test_command_risk_blocks_unknown_sensitive_and_destructive_commands(self) -> None:
        commands = [
            {"id": "workspace:open", "name": "Open workspace"},
            {"id": "dev:console", "name": "Show console"},
            {"id": "plugin:uninstall", "name": "Uninstall plugin"},
        ]

        self.assertEqual(command_risk("missing", commands)["risk"], "unknown")
        self.assertEqual(command_risk("dev:console", commands)["risk"], "sensitive")
        self.assertEqual(command_risk("plugin:uninstall", commands)["risk"], "destructive")
        self.assertEqual(command_risk("workspace:open", commands)["risk"], "normal")

    def test_safe_read_and_search_redact_and_skip_sensitive_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            (vault / ".obsidian").mkdir()
            (vault / "notes").mkdir()
            (vault / "notes/health.md").write_text(
                "联系 13812345678 token=abc12345\n下一行\n",
                encoding="utf-8",
            )
            (vault / "notes/secret-token.md").write_text("token=should-not-read\n", encoding="utf-8")

            read = safe_read(vault, "notes/health.md")
            search = safe_search(vault, "联系")
            skipped = safe_read(vault, "notes/secret-token.md")

            self.assertTrue(read["ok"])
            self.assertIn("138****5678", read["content"])
            self.assertNotIn("abc12345", read["content"])
            self.assertEqual(search["total"], 1)
            self.assertEqual(skipped["reason"], "sensitive-path-skipped")

    def test_safe_search_and_task_scan_skip_symlinked_files_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            outside = root / "outside.md"
            outside.write_text("outside token=abc12345\n- [ ] #task #work outside 📅 2026-06-30\n", encoding="utf-8")
            (vault / "linked.md").symlink_to(outside)

            search = safe_search(vault, "outside")
            tasks = all_vault_tasks(vault)

            self.assertTrue(search["ok"])
            self.assertEqual(search["total"], 0)
            self.assertEqual(tasks, [])


if __name__ == "__main__":
    unittest.main()
