import pathlib
import subprocess
import sys
import unittest


SKILL_DIR = pathlib.Path(__file__).resolve().parents[2]


class ScriptLauncherTests(unittest.TestCase):
    def test_obsidian_workflows_script_launcher(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "obsidian_workflows.py"), "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Obsidian CLI and plugin workflows", result.stdout)

    def test_obs_record_sync_script_launcher_preserves_record_sync_alias(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "obs_record_sync.py"), "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("record-sync", result.stdout)


if __name__ == "__main__":
    unittest.main()
