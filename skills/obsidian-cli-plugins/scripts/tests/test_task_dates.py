import datetime as dt
import pathlib
import sys
import unittest


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins.task_dates import infer_task_date_from_clue, resolve_new_task_dates, task_line


class TaskDateTests(unittest.TestCase):
    def test_infers_chinese_relative_weekday(self) -> None:
        base = dt.date(2026, 6, 30)

        self.assertEqual(infer_task_date_from_clue("下周一开会", base), dt.date(2026, 7, 6))

    def test_invalid_explicit_date_clues_are_ignored(self) -> None:
        base = dt.date(2026, 6, 30)

        self.assertIsNone(infer_task_date_from_clue("误写为 2026-13-01", base))
        self.assertIsNone(infer_task_date_from_clue("误写为 2/31", base))

    def test_month_period_defaults_to_month_end(self) -> None:
        base = dt.date(2026, 6, 30)

        dates = resolve_new_task_dates("月度总结", base, "month", None)

        self.assertIsNotNone(dates)
        self.assertEqual(dates["start"], dt.date(2026, 6, 1))
        self.assertEqual(dates["due"], dt.date(2026, 6, 30))

    def test_task_line_adds_task_tag_kind_and_dates(self) -> None:
        base = dt.date(2026, 6, 30)

        line = task_line("处理缺陷", "work", {"start": base, "due": base})

        self.assertTrue(line.startswith("- [ ] #task #work 处理缺陷"))
        self.assertIn("🛫 2026-06-30", line)
        self.assertIn("📅 2026-06-30", line)


if __name__ == "__main__":
    unittest.main()
