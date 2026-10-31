#!/usr/bin/env python3
"""Lightweight regression suite for the presentation-creator builder.

Builds the bundled example decks and runs the validator, asserting zero errors
and the expected slide counts.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_deck.py"
VALIDATOR = ROOT / "scripts" / "validate_deck.py"

CASES = [
    (ROOT / "examples" / "example-deck.json", 7),
    (ROOT / "examples" / "layouts-deck.json", 6),
    (ROOT / "examples" / "edge-cases-deck.json", 9),
]


def run(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def main() -> int:
    failures = []
    for spec_path, expected_slides in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "deck.pptx"
            r = run(str(BUILDER), str(spec_path), "-o", str(out), "--force")
            if r.returncode != 0:
                failures.append(f"{spec_path.name}: build failed: {r.stderr.strip()}")
                continue
            r = run(str(VALIDATOR), str(out), "--json")
            if r.returncode != 0 and r.returncode != 1:
                failures.append(f"{spec_path.name}: validator crashed: {r.stderr.strip()}")
                continue
            try:
                data = json.loads(r.stdout)
            except json.JSONDecodeError as exc:
                failures.append(f"{spec_path.name}: bad validator JSON: {exc}")
                continue
            if data.get("errors"):
                failures.append(f"{spec_path.name}: {len(data['errors'])} error(s): {data['errors'][:3]}")
            if len(data.get("slides", [])) != expected_slides:
                failures.append(
                    f"{spec_path.name}: slide count {len(data.get('slides', []))} != {expected_slides}"
                )
    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print(f"PASSED: {len(CASES)} deck(s) built and validated clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
