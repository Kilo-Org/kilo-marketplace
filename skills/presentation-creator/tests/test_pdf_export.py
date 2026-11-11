"""End-to-end PDF export tests driven by a fake soffice on PATH."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
BUILDER = SCRIPTS / "build_deck.py"
RENDER = SCRIPTS / "render_preview.py"
SPEC = ROOT / "examples" / "example-deck.json"

try:
    import pptx  # noqa: F401

    HAVE_PPTX = True
except ModuleNotFoundError:  # pragma: no cover - environment guard
    HAVE_PPTX = False

FAKE_SOFFICE = """#!/usr/bin/env python3
import pathlib
import sys

args = sys.argv[1:]
outdir = None
for i, a in enumerate(args):
    if a == "--outdir":
        outdir = args[i + 1]
deck = pathlib.Path(args[-1])
if outdir is None:
    sys.exit(9)
out = pathlib.Path(outdir) / (deck.stem + ".pdf")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(b"%PDF-1.4\\n% fake export\\n")
"""


class Tool:
    """Runs a skill script with an isolated PATH and no absolute-app fallbacks."""

    def __init__(self, root: Path, converter: str | None = "soffice"):
        self.root = root
        self.pybin = root / "pybin"
        self.pybin.mkdir(parents=True, exist_ok=True)
        python = self.pybin / "python3"
        if not python.exists():
            os.symlink(sys.executable, python)
        self.bindir = root / "bin"
        self.bindir.mkdir(parents=True, exist_ok=True)
        if converter:
            script = self.bindir / converter
            script.write_text(FAKE_SOFFICE, encoding="utf-8")
            script.chmod(0o755)
        self.runner = root / "runner.py"
        self.runner.write_text(
            "import runpy, sys\n"
            f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
            "import office_convert\n"
            "office_convert.SOFFICE_GLOBS = ()\n"
            "office_convert.WINDOWS_SOFFICE_GLOBS = ()\n"
            "sys.argv = sys.argv[1:]\n"
            "runpy.run_path(sys.argv[0], run_name='__main__')\n",
            encoding="utf-8",
        )

    def __call__(self, script: Path, args) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PATH"] = os.pathsep.join([str(self.pybin), str(self.bindir)])
        return subprocess.run(
            [str(self.pybin / "python3"), str(self.runner), str(script), *args],
            capture_output=True, text=True, env=env,
        )


@unittest.skipIf(os.name == "nt", "fake converters are POSIX scripts")
@unittest.skipUnless(HAVE_PPTX, "python-pptx is not installed")
class PdfExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_build_writes_pptx_and_pdf(self):
        tool = Tool(self.root)
        out = self.root / "deck.pptx"
        r = tool(BUILDER, [str(SPEC), "-o", str(out), "--pdf"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.is_file())
        pdf = self.root / "deck.pdf"
        self.assertTrue(pdf.is_file(), r.stdout + r.stderr)
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
        self.assertIn("Rendered PDF", r.stdout)
        self.assertIn(str(pdf), r.stdout)

    def test_build_writes_explicit_pdf_path(self):
        tool = Tool(self.root)
        out = self.root / "deck.pptx"
        pdf = self.root / "exports" / "custom.pdf"
        r = tool(BUILDER, [str(SPEC), "-o", str(out), "--pdf", str(pdf)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(pdf.is_file(), r.stdout + r.stderr)

    def test_build_requires_force_for_existing_pdf(self):
        tool = Tool(self.root)
        out = self.root / "deck.pptx"
        pdf = self.root / "deck.pdf"
        pdf.write_bytes(b"%PDF-1.7\nold\n")
        r = tool(BUILDER, [str(SPEC), "-o", str(out), "--pdf"])
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--force", r.stderr)
        self.assertEqual(pdf.read_bytes(), b"%PDF-1.7\nold\n")

    def test_build_requires_force_for_existing_pptx(self):
        tool = Tool(self.root)
        out = self.root / "deck.pptx"
        out.write_bytes(b"old")
        r = tool(BUILDER, [str(SPEC), "-o", str(out), "--pdf"])
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertFalse((self.root / "deck.pdf").exists())

    def test_build_without_converter_exits_3_and_keeps_pptx(self):
        tool = Tool(self.root, converter=None)
        out = self.root / "deck.pptx"
        r = tool(BUILDER, [str(SPEC), "-o", str(out), "--pdf"])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertTrue(out.is_file())
        self.assertFalse((self.root / "deck.pdf").exists())
        self.assertIn("no PDF converter available", r.stderr)
        self.assertIn(f"The .pptx was written to {out}.", r.stderr)

    def test_build_without_pdf_flag_is_unchanged(self):
        tool = Tool(self.root, converter=None)
        out = self.root / "deck.pptx"
        r = tool(BUILDER, [str(SPEC), "-o", str(out)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.is_file())
        self.assertFalse((self.root / "deck.pdf").exists())

    def test_preview_pdf_out_without_pngs(self):
        tool = Tool(self.root)
        deck = self.root / "deck.pptx"
        deck.write_bytes(b"pptx")
        pdf = self.root / "out" / "deck.pdf"
        r = tool(RENDER, [str(deck), "--pdf-out", str(pdf), "--no-png"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(pdf.is_file(), r.stdout + r.stderr)
        self.assertEqual(list(pdf.parent.glob("*.png")), [])

    def test_preview_default_outdir_writes_pdf(self):
        tool = Tool(self.root)
        deck = self.root / "deck.pptx"
        deck.write_bytes(b"pptx")
        outdir = self.root / "preview"
        r = tool(RENDER, [str(deck), "-o", str(outdir)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((outdir / "deck.pdf").is_file(), r.stdout + r.stderr)
        self.assertIn("pdftoppm not available", r.stdout)

    def test_preview_pdf_out_requires_force(self):
        tool = Tool(self.root)
        deck = self.root / "deck.pptx"
        deck.write_bytes(b"pptx")
        pdf = self.root / "deck.pdf"
        pdf.write_bytes(b"%PDF-1.7\nold\n")
        r = tool(RENDER, [str(deck), "--pdf-out", str(pdf)])
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--force", r.stderr)
        self.assertEqual(pdf.read_bytes(), b"%PDF-1.7\nold\n")

    def test_preview_without_converter_skips(self):
        tool = Tool(self.root, converter=None)
        deck = self.root / "deck.pptx"
        deck.write_bytes(b"pptx")
        outdir = self.root / "preview"
        r = tool(RENDER, [str(deck), "-o", str(outdir)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("skipped", r.stdout)

    def test_preview_explicit_pdf_without_converter_exits_3(self):
        tool = Tool(self.root, converter=None)
        deck = self.root / "deck.pptx"
        deck.write_bytes(b"pptx")
        r = tool(RENDER, [str(deck), "--pdf-out", str(self.root / "deck.pdf")])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertFalse((self.root / "deck.pdf").exists())


@unittest.skipIf(os.name == "nt", "POSIX-only paths")
class RenderPreviewArgumentTests(unittest.TestCase):
    def test_requires_outdir_or_pdf_out(self):
        proc = subprocess.run(
            [sys.executable, str(RENDER), __file__], capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--pdf-out", proc.stderr)


if __name__ == "__main__":
    unittest.main()