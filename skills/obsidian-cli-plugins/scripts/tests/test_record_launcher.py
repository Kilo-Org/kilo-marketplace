import pathlib
import sys
import unittest


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obs_record_sync import record_sync_argv, split_global_args


class RecordLauncherTests(unittest.TestCase):
    def test_inserts_record_sync_after_global_vault_args(self) -> None:
        argv = [
            "--vault-path",
            "/vault/path",
            "--period",
            "day",
            "--text",
            "一天之计在于晨",
        ]

        self.assertEqual(
            record_sync_argv(argv),
            [
                sys.argv[0],
                "--vault-path",
                "/vault/path",
                "record-sync",
                "--period",
                "day",
                "--text",
                "一天之计在于晨",
            ],
        )

    def test_allows_idempotent_record_sync_subcommand(self) -> None:
        self.assertEqual(
            record_sync_argv(["record-sync", "--text", "记录"]),
            [sys.argv[0], "record-sync", "--text", "记录"],
        )

    def test_supports_equals_form_global_args(self) -> None:
        self.assertEqual(
            split_global_args(["--vault=current", "--text", "记录"]),
            (["--vault=current"], ["--text", "记录"]),
        )


if __name__ == "__main__":
    unittest.main()
