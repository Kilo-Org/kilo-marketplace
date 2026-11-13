import importlib.util
import pathlib
import tempfile
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "sync_openclaw.py"
SPEC = importlib.util.spec_from_file_location("sync_openclaw", SCRIPT_PATH)
assert SPEC and SPEC.loader
sync_openclaw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_openclaw)


class SyncOpenClawTests(unittest.TestCase):
    def test_force_replaces_existing_skill_without_backup_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "obsidian-cli-plugins"
            dest_root = root / "openclaw-skills"
            dest = dest_root / "obsidian-cli-plugins"
            source.mkdir()
            dest.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (dest / "SKILL.md").write_text("old", encoding="utf-8")

            result = sync_openclaw.sync_skill(source, dest_root, force=True, link=False, dry_run=False)

            self.assertTrue(result["ok"])
            self.assertIsNone(result["backup"])
            self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "new")
            self.assertEqual(list(dest_root.glob("obsidian-cli-plugins.bak.*")), [])

    def test_force_backup_keeps_timestamped_backup_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "obsidian-cli-plugins"
            dest_root = root / "openclaw-skills"
            dest = dest_root / "obsidian-cli-plugins"
            source.mkdir()
            dest.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (dest / "SKILL.md").write_text("old", encoding="utf-8")

            result = sync_openclaw.sync_skill(
                source,
                dest_root,
                force=True,
                link=False,
                dry_run=False,
                backup_existing=True,
            )

            backups = list(dest_root.glob("obsidian-cli-plugins.bak.*"))
            self.assertTrue(result["ok"])
            self.assertEqual(len(backups), 1)
            self.assertEqual(pathlib.Path(result["backup"]), backups[0])
            self.assertEqual((backups[0] / "SKILL.md").read_text(encoding="utf-8"), "old")
            self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "new")


if __name__ == "__main__":
    unittest.main()
