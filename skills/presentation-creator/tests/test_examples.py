"""Build + validate every bundled example deck."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_deck.py"
VALIDATOR = ROOT / "scripts" / "validate_deck.py"
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))


class ExampleDecks(unittest.TestCase):
    def test_examples_build_and_validate(self):
        self.assertTrue(EXAMPLES, "no example decks found")
        for spec_path in EXAMPLES:
            with self.subTest(deck=spec_path.name), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "deck.pptx"
                r = subprocess.run(
                    [sys.executable, str(BUILDER), str(spec_path), "-o", str(out), "--force"],
                    capture_output=True, text=True,
                )
                self.assertEqual(r.returncode, 0, f"build failed: {r.stderr}")
                r2 = subprocess.run(
                    [sys.executable, str(VALIDATOR), str(out), "--json"],
                    capture_output=True, text=True,
                )
                try:
                    data = json.loads(r2.stdout)
                except json.JSONDecodeError as exc:
                    self.fail(f"bad validator JSON: {exc}\n{r2.stdout}\n{r2.stderr}")
                self.assertFalse(data.get("errors"), f"{spec_path.name}: {data.get('errors')}")


if __name__ == "__main__":
    unittest.main()
