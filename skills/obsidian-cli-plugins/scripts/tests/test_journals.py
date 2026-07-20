import datetime as dt
import pathlib
import sys
import unittest


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins.journals import DateParseError, target_date


class JournalDateTests(unittest.TestCase):
    def test_target_date_accepts_relative_aliases(self) -> None:
        today = dt.date.today()

        self.assertEqual(target_date("today"), today)
        self.assertEqual(target_date("yesterday"), today - dt.timedelta(days=1))
        self.assertEqual(target_date("tomorrow"), today + dt.timedelta(days=1))
        self.assertEqual(target_date("昨天"), today - dt.timedelta(days=1))
        self.assertEqual(target_date("明天"), today + dt.timedelta(days=1))

    def test_target_date_accepts_iso_dates(self) -> None:
        self.assertEqual(target_date("2026-07-06"), dt.date(2026, 7, 6))

    def test_target_date_reports_supported_formats(self) -> None:
        with self.assertRaisesRegex(DateParseError, "YYYY-MM-DD"):
            target_date("last week")


if __name__ == "__main__":
    unittest.main()
