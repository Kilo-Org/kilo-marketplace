"""Unit tests for the shared office converter registry."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import office_convert  # noqa: E402

SCRIPT = ROOT / "scripts" / "office_convert.py"
VALID_PDF = b"%PDF-1.4\n% fake\n"


def write_cli(directory: Path, name: str, mode: str = "ok") -> Path:
    """Create a fake soffice-compatible executable."""
    path = Path(directory) / name
    body = [
        "#!/usr/bin/env python3",
        "import pathlib, sys",
        "args = sys.argv[1:]",
        "outdir = None",
        "for i, a in enumerate(args):",
        "    if a == '--outdir':",
        "        outdir = args[i + 1]",
        "deck = pathlib.Path(args[-1])",
        "if outdir is None:",
        "    sys.exit(9)",
        "if %r == 'fail':" % mode,
        "    sys.exit(1)",
        "if %r == 'notpdf':" % mode,
        "    out = pathlib.Path(outdir) / (deck.stem + '.pdf')",
        "    out.write_bytes(b'NOTAPDF')",
        "    sys.exit(0)",
        "if %r == 'silent':" % mode,
        "    sys.exit(0)",
        "if %r == 'needs_profile' and not any(a.startswith('-env:UserInstallation') for a in args):" % mode,
        "    sys.exit(1)",
        "out = pathlib.Path(outdir) / (deck.stem + '.pdf')",
        "out.parent.mkdir(parents=True, exist_ok=True)",
        "out.write_bytes(b'%PDF-1.4\\n% fake\\n')",
    ]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def which_map(mapping):
    def _which(name, *args, **kwargs):
        return mapping.get(name)

    return _which


class FakeConverterTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.deck = self.root / "deck.pptx"
        self.deck.write_bytes(b"pptx")
        patcher = mock.patch.object(office_convert, "SOFFICE_GLOBS", ())
        patcher.start()
        self.addCleanup(patcher.stop)

    def convert(self, converters, out_name="out.pdf", timeout=30.0):
        out = self.root / out_name
        with mock.patch.object(office_convert, "find_converters", return_value=converters):
            return office_convert.convert_to_pdf(self.deck, out, timeout=timeout)


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        patcher = mock.patch.object(office_convert, "SOFFICE_GLOBS", ())
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(office_convert.platform, "system", return_value="Linux")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_prefers_soffice_then_openoffice(self):
        soffice = write_cli(self.root, "soffice")
        openoffice = write_cli(self.root, "openoffice")
        with mock.patch.object(office_convert.shutil, "which", which_map({
            "soffice": str(soffice), "openoffice": str(openoffice),
        })):
            found = office_convert.find_converters()
        self.assertEqual([c.name for c in found], ["soffice", "openoffice"])
        self.assertEqual(found[0].label, "LibreOffice")
        self.assertEqual(found[1].label, "OpenOffice")

    def test_falls_back_to_openoffice(self):
        openoffice = write_cli(self.root, "openoffice")
        with mock.patch.object(office_convert.shutil, "which", which_map({
            "openoffice": str(openoffice),
        })):
            found = office_convert.find_converters()
        self.assertEqual([c.name for c in found], ["openoffice"])

    def test_dedupes_same_resolved_binary(self):
        binary = write_cli(self.root, "real")
        with mock.patch.object(office_convert.shutil, "which", which_map({
            "soffice": str(binary), "libreoffice": str(binary),
        })):
            found = office_convert.find_converters()
        self.assertEqual(len(found), 1)

    def test_reports_unsupported_apps(self):
        with mock.patch.object(office_convert.shutil, "which", which_map({
            "onlyoffice-desktopeditors": "/opt/onlyoffice/desktopeditors/DesktopEditors",
        })):
            apps = office_convert.unsupported_apps()
        self.assertEqual([a["name"] for a in apps], ["onlyoffice"])

    def test_describe_environment_shape(self):
        with mock.patch.object(office_convert.shutil, "which", which_map({})):
            info = office_convert.describe_environment()
        self.assertEqual(set(info), {"converters", "unsupported"})
        self.assertIsInstance(info["converters"], list)
        self.assertIsInstance(info["unsupported"], list)

    def test_list_json_cli(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--list", "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), {"converters", "unsupported"})


class ConversionTests(FakeConverterTestBase):
    def test_writes_pdf_to_requested_path(self):
        conv = office_convert.Converter(
            name="soffice", kind="cli", path=str(write_cli(self.bin, "soffice")), label="LibreOffice"
        )
        result = self.convert([conv])
        self.assertEqual(result.pdf, self.root / "out.pdf")
        self.assertTrue(result.pdf.is_file())
        self.assertTrue(result.pdf.read_bytes().startswith(b"%PDF-"))
        self.assertEqual(result.converter, "soffice")

    def test_retries_with_private_profile(self):
        conv = office_convert.Converter(
            name="soffice", kind="cli",
            path=str(write_cli(self.bin, "soffice", mode="needs_profile")), label="LibreOffice",
        )
        result = self.convert([conv])
        self.assertTrue(result.pdf.is_file())
        self.assertEqual(result.pdf.read_bytes(), VALID_PDF)

    def test_rejects_non_pdf_output(self):
        bad = office_convert.Converter(
            name="soffice", kind="cli", path=str(write_cli(self.bin, "soffice", mode="notpdf")),
            label="LibreOffice",
        )
        good = office_convert.Converter(
            name="openoffice", kind="cli", path=str(write_cli(self.bin, "openoffice")),
            label="OpenOffice",
        )
        result = self.convert([bad, good])
        self.assertEqual(result.converter, "openoffice")

    def test_zero_exit_without_output_is_an_attempt(self):
        conv = office_convert.Converter(
            name="soffice", kind="cli", path=str(write_cli(self.bin, "soffice", mode="silent")),
            label="LibreOffice",
        )
        with self.assertRaises(office_convert.ConversionError) as ctx:
            self.convert([conv])
        self.assertTrue(any("soffice" in name for name, _ in ctx.exception.attempts))

    def test_all_converters_fail_lists_attempts(self):
        first = office_convert.Converter(
            name="soffice", kind="cli", path=str(write_cli(self.bin, "soffice", mode="fail")),
            label="LibreOffice",
        )
        second = office_convert.Converter(
            name="openoffice", kind="cli", path=str(write_cli(self.bin, "openoffice", mode="fail")),
            label="OpenOffice",
        )
        with self.assertRaises(office_convert.ConversionError) as ctx:
            self.convert([first, second])
        names = [name for name, _ in ctx.exception.attempts]
        self.assertEqual(names, ["soffice", "openoffice"])
        message = str(ctx.exception)
        self.assertIn("soffice", message)
        self.assertIn("openoffice", message)

    def test_no_converter_raises_with_guidance(self):
        with mock.patch.object(office_convert, "find_converters", return_value=[]), \
                mock.patch.object(office_convert, "unsupported_apps", return_value=[]):
            with self.assertRaises(office_convert.ConversionError) as ctx:
                office_convert.convert_to_pdf(self.deck, self.root / "x.pdf")
        self.assertIn("no PDF converter available", str(ctx.exception))
        self.assertEqual(ctx.exception.attempts, [])

    def test_failed_conversion_leaves_target_untouched(self):
        existing = self.root / "keep.pdf"
        existing.write_bytes(b"%PDF-1.7\nold\n")
        conv = office_convert.Converter(
            name="soffice", kind="cli", path=str(write_cli(self.bin, "soffice", mode="fail")),
            label="LibreOffice",
        )
        with mock.patch.object(office_convert, "find_converters", return_value=[conv]):
            with self.assertRaises(office_convert.ConversionError):
                office_convert.convert_to_pdf(self.deck, existing)
        self.assertEqual(existing.read_bytes(), b"%PDF-1.7\nold\n")

    def test_timeout_kills_child_processes(self):
        script = self.bin / "soffice"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
            "time.sleep(120)\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
        conv = office_convert.Converter(name="soffice", kind="cli", path=str(script), label="LibreOffice")
        import time

        started = time.monotonic()
        with self.assertRaises(office_convert.ConversionError) as ctx:
            self.convert([conv], timeout=1.0)
        self.assertLess(time.monotonic() - started, 30)
        self.assertTrue(any("timed out" in why for _, why in ctx.exception.attempts))


class PowerPointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.deck = self.root / "deck.pptx"
        self.deck.write_bytes(b"pptx")

    def test_windows_builds_powershell_command(self):
        conv = office_convert.Converter(
            name="powerpoint-com", kind="powerpoint",
            path=r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            label="Microsoft PowerPoint (COM)",
        )
        captured = {}

        def fake_run(cmd, timeout):
            captured["cmd"] = cmd
            out = Path(cmd[cmd.index("-OutputPath") + 1])
            out.write_bytes(VALID_PDF)
            return 0, b"", b""

        with mock.patch.object(office_convert.platform, "system", return_value="Windows"), \
                mock.patch.object(office_convert.shutil, "which",
                                  which_map({"powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"})), \
                mock.patch.object(office_convert, "_run", fake_run):
            result = office_convert._convert_powerpoint(conv, self.deck, self.root, 30.0)

        self.assertTrue(result.is_file())
        self.assertEqual(result.read_bytes(), VALID_PDF)
        cmd = captured["cmd"]
        self.assertIn("-NoProfile", cmd)
        self.assertIn("-File", cmd)
        self.assertTrue(cmd[cmd.index("-File") + 1].endswith(".ps1"))
        script = Path(cmd[cmd.index("-File") + 1]).read_text(encoding="utf-8")
        self.assertIn("GetActiveObject('PowerPoint.Application')", script)
        self.assertIn("SaveAs($OutputPath, 32)", script)
        # Quit must only run for an instance we created.
        self.assertGreater(script.index("$ppt.Quit()"), script.index("if ($created)"))

    def test_macos_builds_applescript_command(self):
        conv = office_convert.Converter(
            name="powerpoint-applescript", kind="powerpoint",
            path="/Applications/Microsoft PowerPoint.app",
            label="Microsoft PowerPoint (AppleScript)",
        )
        captured = {}

        def fake_run(cmd, timeout):
            captured["cmd"] = cmd
            Path(cmd[-1]).write_bytes(VALID_PDF)
            return 0, b"", b""

        with mock.patch.object(office_convert.platform, "system", return_value="Darwin"), \
                mock.patch.object(office_convert.shutil, "which", which_map({"osascript": "/usr/bin/osascript"})), \
                mock.patch.object(office_convert, "_run", fake_run):
            result = office_convert._convert_powerpoint(conv, self.deck, self.root, 30.0)

        self.assertEqual(result.read_bytes(), VALID_PDF)
        script = Path(captured["cmd"][1]).read_text(encoding="utf-8")
        self.assertIn("POSIX file outPath", script)
        self.assertIn("as save as PDF", script)
        self.assertNotIn("quit", script.lower())

    def test_other_platform_rejected(self):
        conv = office_convert.Converter(
            name="powerpoint-com", kind="powerpoint", path="POWERPNT.EXE", label="Microsoft PowerPoint (COM)"
        )
        with mock.patch.object(office_convert.platform, "system", return_value="Linux"):
            with self.assertRaises(RuntimeError):
                office_convert._convert_powerpoint(conv, self.deck, self.root, 1.0)


if __name__ == "__main__":
    unittest.main()