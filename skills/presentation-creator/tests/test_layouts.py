"""Edge-case tests for the presentation-creator builder layouts."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_deck  # noqa: E402


def _build(spec):
    builder = build_deck.DeckBuilder(spec)
    builder.build(spec)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "deck.pptx"
        builder.prs.save(str(out))
        assert out.is_file() and out.stat().st_size > 0
    return builder


class LayoutEdgeCases(unittest.TestCase):
    def _base(self, slides):
        return {"title": "T", "theme": "clean-light", "aspect": "16:9", "slides": slides}

    def test_empty_stats_renders(self):
        spec = self._base([{"layout": "stats", "title": "S", "stats": [], "notes": "n"}])
        _build(spec)

    def test_stats_strings_and_tuples(self):
        spec = self._base([{"layout": "stats", "title": "S", "stats": ["a", ("b", "B", "+1")], "notes": "n"}])
        _build(spec)

    def test_stats_single(self):
        spec = self._base([{"layout": "stats", "title": "S", "stats": [{"value": "1", "label": "L"}], "notes": "n"}])
        _build(spec)

    def test_timeline_empty(self):
        spec = self._base([{"layout": "timeline", "title": "T", "steps": [], "notes": "n"}])
        _build(spec)

    def test_timeline_strings(self):
        spec = self._base([{"layout": "timeline", "title": "T", "steps": ["a", "b"], "notes": "n"}])
        _build(spec)

    def test_timeline_tuples(self):
        spec = self._base([{"layout": "timeline", "title": "T", "steps": [("a", "b")], "notes": "n"}])
        _build(spec)

    def test_comparison_empty(self):
        spec = self._base([{"layout": "comparison", "title": "C", "headers": [], "columns": [], "notes": "n"}])
        _build(spec)

    def test_comparison_headers_from_columns(self):
        spec = self._base([{"layout": "comparison", "title": "C", "columns": [{"header": "H", "items": ["a"]}], "notes": "n"}])
        _build(spec)

    def test_comparison_single_column(self):
        spec = self._base([{"layout": "comparison", "title": "C", "headers": ["H"], "columns": [["a"]], "notes": "n"}])
        _build(spec)

    def test_cards_empty(self):
        spec = self._base([{"layout": "cards", "title": "C", "cards": [], "notes": "n"}])
        _build(spec)

    def test_cards_strings_tuples(self):
        spec = self._base([{"layout": "cards", "title": "C", "cards": ["a", ("b", "body", ["x"])], "notes": "n"}])
        _build(spec)

    def test_cards_single(self):
        spec = self._base([{"layout": "cards", "title": "C", "cards": [{"title": "T", "body": "B", "bullets": ["x"]}], "notes": "n"}])
        _build(spec)

    def test_chart_pie_requires_one_series(self):
        with self.assertRaises(ValueError):
            spec = self._base([{"layout": "chart", "title": "C", "chart": {"type": "pie", "categories": ["a"], "series": [{"name": "s1", "values": [1]}, {"name": "s2", "values": [2]}]}, "notes": "n"}])
            _build(spec)

    def test_unknown_layout_raises(self):
        with self.assertRaises(ValueError):
            spec = self._base([{"layout": "nope", "title": "C", "notes": "n"}])
            _build(spec)

    def test_alias_layouts(self):
        for alias in ("kpi", "process", "process_steps", "card"):
            spec = self._base([{"layout": alias, "title": "C", "notes": "n"}])
            # may need items; empty is fine
            _build(spec)

    def test_accent_bar_disabled(self):
        spec = self._base([{"layout": "bullets", "title": "B", "bullets": ["x"], "notes": "n"}])
        spec["accent_bar"] = False
        _build(spec)

    def test_palette_override(self):
        spec = self._base([{"layout": "title", "title": "T", "notes": "n"}])
        spec["palette"] = {"accent": "#FF0000"}
        _build(spec)

    def test_4_3_aspect(self):
        spec = self._base([{"layout": "bullets", "title": "B", "bullets": ["x"], "notes": "n"}])
        spec["aspect"] = "4:3"
        _build(spec)


if __name__ == "__main__":
    unittest.main()
