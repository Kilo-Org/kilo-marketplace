#!/usr/bin/env python3
"""Render and lint SPL2 pipeline starters for IP and EP profiles."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "splunk-spl2-pipeline-kit-rendered"
PROFILES = ("ingestProcessor", "edgeProcessor")

BASE_COMMANDS = {
    "branch",
    "eval",
    "expand",
    "fields",
    "flatten",
    "from",
    "into",
    "lookup",
    "mvexpand",
    "ocsf",
    "rename",
    "replace",
    "rex",
    "route",
    "stats",
    "thru",
    "where",
}
INGEST_ONLY_COMMANDS = {"decrypt", "logs_to_metrics"}
EDGE_ONLY_COMMANDS: set[str] = set()
PROFILE_COMMANDS = {
    "ingestProcessor": BASE_COMMANDS | INGEST_ONLY_COMMANDS,
    "edgeProcessor": BASE_COMMANDS,
}
PIPELINE_STAT_FUNCTIONS = {"count", "max", "min", "sum", "span"}
SPL1_COMMAND_PATTERNS = {
    "table": re.compile(r"\|\s*table\b", re.IGNORECASE),
    "search": re.compile(r"\|\s*search\b", re.IGNORECASE),
    "regex": re.compile(r"\|\s*regex\b", re.IGNORECASE),
    "makeresults": re.compile(r"\|\s*makeresults\b", re.IGNORECASE),
    "collect": re.compile(r"\|\s*collect\b", re.IGNORECASE),
    "sendemail": re.compile(r"\|\s*sendemail\b", re.IGNORECASE),
}


TEMPLATES: dict[str, dict[str, str]] = {
    "ingestProcessor": {
        "filter.spl2": """// Keep non-noisy events.
$pipeline = | from $source
            | where sourcetype != "noisy:type"
            | into $destination;
""",
        "route.spl2": """// Route security data to one destination and everything else to default.
$pipeline = | from $source
            | branch
                [ where sourcetype LIKE "sec:%" | into $destination_security ]
                [ where true() | into $destination_default ];
""",
        "copy-thru.spl2": """// Send one copy to metrics and one copy to the normal event destination.
import logs_to_metrics from /splunk.ingest.commands;
$pipeline = | from $source
            | thru [
                | logs_to_metrics metric_name="events.count" metric_value=1 metric_type="counter" round_timestamp=true
                | into $destination_metrics
              ]
            | into $destination_events;
""",
        "redact.spl2": """// Redact password-like material in _raw using PCRE2.
$pipeline = | from $source
            | eval _raw = replace(_raw, "(?i)password=\\\\S+", "password=REDACTED")
            | into $destination;
""",
        "hash.spl2": """// Hash a field; hashing is not complete anonymization.
$pipeline = | from $source
            | eval user_hash = sha256(coalesce(user, ""))
            | fields - user
            | into $destination;
""",
        "sample.spl2": """// Keep about 10 percent of events.
$pipeline = | from $source
            | where random_int < 10
            | into $destination;
""",
        "lookup.spl2": """// Lookup enrichment placeholder; keep lookup content outside rendered output.
import asset_lookup from /splunk.ingest.lookups;
$pipeline = | from $source
            | lookup asset_lookup host OUTPUT owner, criticality
            | into $destination;
""",
        "extract-json.spl2": """// Extract selected fields from JSON payloads.
$pipeline = | from $source
            | eval payload = json_extract(_raw)
            | eval user = payload.user, action = payload.action
            | into $destination;
""",
        "timestamp.spl2": """// Normalize a timestamp field before routing.
$pipeline = | from $source
            | eval _time = strptime(event_time, "%Y-%m-%dT%H:%M:%S.%QZ")
            | into $destination;
""",
        "xml-object.spl2": """// Convert XML into an object, then emit the normalized event.
$pipeline = | from $source
            | eval xml_object = xml_to_object(_raw)
            | eval normalized_xml = object_to_xml(xml_object)
            | into $destination;
""",
        "metrics.spl2": """// Generate a metric stream from events.
import logs_to_metrics from /splunk.ingest.commands;
$pipeline = | from $source
            | thru [
                | logs_to_metrics metric_name="http.requests" metric_value=1 metric_type="counter" round_timestamp=true
                | into $destination_metrics
              ]
            | into $destination_events;
""",
        "ocsf.spl2": """// OCSF conversion starter. Validate unsupported classes after preview.
$pipeline = | from $source
            | ocsf
            | into $destination;
""",
        "decrypt.spl2": """// Decrypt with a private-key lookup placeholder. Do not render key material.
import private_keys from /splunk.ingest.lookups;
$pipeline = | from $source
            | eval private_key = private_keys.key
            | decrypt encrypted_field AS cleartext WITH private_key
            | into $destination;
""",
        "stats.spl2": """// Batch aggregation. Use sum/count instead of avg().
$pipeline = | from $source
            | stats count() as event_count, sum(bytes) as bytes_sum by sourcetype
            | into $destination;
""",
        "s3-archive.spl2": """// Archive selected events to an S3 destination.
$pipeline = | from $source
            | where sourcetype LIKE "archive:%"
            | into $destination_s3;
""",
        "compatibility-lint.spl2": """// Compatibility review starter for SPL-to-SPL2 migration.
$pipeline = | from $source
            | rex field=_raw "(?P<user>user=[^ ]+)"
            | into $destination;
""",
    },
    "edgeProcessor": {
        "filter.spl2": """// Keep non-noisy events.
$pipeline = | from $source
            | where sourcetype != "noisy:type"
            | into $destination;
""",
        "route.spl2": """// Route security data to one destination and everything else to default.
$pipeline = | from $source
            | branch
                [ where sourcetype LIKE "sec:%" | into $destination_security ]
                [ where true() | into $destination_default ];
""",
        "redact.spl2": """// Redact password-like material in _raw using PCRE2.
$pipeline = | from $source
            | eval _raw = replace(_raw, "(?i)password=\\\\S+", "password=REDACTED")
            | into $destination;
""",
        "hash.spl2": """// Hash a field; hashing is not complete anonymization.
$pipeline = | from $source
            | eval user_hash = sha256(coalesce(user, ""))
            | fields - user
            | into $destination;
""",
        "sample.spl2": """// Keep about 10 percent of events.
$pipeline = | from $source
            | where random_int < 10
            | into $destination;
""",
        "lookup.spl2": """// Lookup enrichment placeholder; keep lookup content outside rendered output.
import asset_lookup from /splunk.edge.lookups;
$pipeline = | from $source
            | lookup asset_lookup host OUTPUT owner, criticality
            | into $destination;
""",
        "extract-json.spl2": """// Extract selected fields from JSON payloads.
$pipeline = | from $source
            | eval payload = json_extract(_raw)
            | eval user = payload.user, action = payload.action
            | into $destination;
""",
        "timestamp.spl2": """// Normalize a timestamp field before routing.
$pipeline = | from $source
            | eval _time = strptime(event_time, "%Y-%m-%dT%H:%M:%S.%QZ")
            | into $destination;
""",
        "ocsf.spl2": """// OCSF conversion starter. Validate unsupported classes after preview.
$pipeline = | from $source
            | ocsf
            | into $destination;
""",
        "stats.spl2": """// Edge Processor aggregation starter. Review state-window behavior on EP 1.10.0+.
$pipeline = | from $source
            | stats count() as event_count, sum(bytes) as bytes_sum by sourcetype
            | into $destination;
""",
        "s3-archive.spl2": """// Archive selected events to an S3 destination.
$pipeline = | from $source
            | where sourcetype LIKE "archive:%"
            | into $destination_s3;
""",
        "compatibility-lint.spl2": """// Compatibility review starter for SPL-to-SPL2 migration.
$pipeline = | from $source
            | rex field=_raw "(?P<user>user=[^ ]+)"
            | into $destination;
""",
    },
}


@dataclass
class LintFinding:
    severity: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "message": self.message}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("render", "lint", "validate", "smoke", "all"), default="render")
    parser.add_argument("--profile", choices=(*PROFILES, "both"), default="ingestProcessor")
    parser.add_argument("--pipeline-file", action="append", default=[])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def profiles_for(value: str) -> list[str]:
    return list(PROFILES) if value == "both" else [value]


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def strip_comments(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        cleaned_lines.append(re.sub(r"//.*$", "", line))
    return "\n".join(cleaned_lines)


def command_names(text: str) -> list[str]:
    cleaned = strip_comments(text)
    return [match.group(1) for match in re.finditer(r"\|\s*([A-Za-z_][A-Za-z0-9_]*)", cleaned)]


def import_names(text: str) -> set[str]:
    return set(
        match.group(1)
        for match in re.finditer(r"^\s*import\s+([A-Za-z_][A-Za-z0-9_]*)\s+from\s+", text, re.MULTILINE)
    )


def lint_text(text: str, profile: str, *, strict: bool = False) -> list[LintFinding]:
    findings: list[LintFinding] = []
    cleaned = strip_comments(text)
    commands = command_names(text)
    imports = import_names(text)
    allowed = PROFILE_COMMANDS[profile]

    if "$pipeline" not in cleaned:
        findings.append(LintFinding("error", "SPL2-MISSING-PIPELINE", "Pipeline is missing `$pipeline`."))
    if "from $source" not in cleaned:
        findings.append(LintFinding("error", "SPL2-MISSING-SOURCE", "Pipeline is missing `from $source`."))
    if "into $destination" not in cleaned and "into $destination_" not in cleaned:
        findings.append(LintFinding("error", "SPL2-MISSING-DESTINATION", "Pipeline is missing an `into $destination` target."))

    for command in commands:
        if profile == "edgeProcessor" and command in INGEST_ONLY_COMMANDS:
            findings.append(
                LintFinding(
                    "error",
                    "SPL2-PROFILE-INCOMPATIBLE",
                    f"`{command}` is Ingest Processor-only in this kit and is not valid for edgeProcessor.",
                )
            )
            continue
        if command in imports:
            continue
        if profile == "ingestProcessor" and command in EDGE_ONLY_COMMANDS:
            findings.append(
                LintFinding(
                    "error",
                    "SPL2-PROFILE-INCOMPATIBLE",
                    f"`{command}` is Edge Processor-only and is not valid for ingestProcessor.",
                )
            )
            continue
        if command not in allowed:
            severity = "error" if strict else "warning"
            findings.append(
                LintFinding(
                    severity,
                    "SPL2-UNKNOWN-COMMAND",
                    f"`{command}` is not in the built-in {profile} command catalog; import it or review in Splunk preview.",
                )
            )

    if "logs_to_metrics" in commands and "logs_to_metrics" not in imports:
        findings.append(
            LintFinding(
                "error",
                "SPL2-METRICS-IMPORT",
                "`logs_to_metrics` requires an import from /splunk.ingest.commands.",
            )
        )

    for fn in re.findall(r"\bstats\b[^;\n]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", cleaned, re.IGNORECASE):
        lower = fn.lower()
        if lower == "avg":
            findings.append(
                LintFinding(
                    "error",
                    "SPL2-STATS-AVG",
                    "Ingest Processor and Edge Processor pipeline stats do not document avg(); use sum()/count() instead.",
                )
            )
        elif lower not in PIPELINE_STAT_FUNCTIONS:
            findings.append(
                LintFinding(
                    "warning",
                    "SPL2-STATS-FUNCTION",
                    f"`stats {fn}()` is not in the documented pipeline stats function set.",
                )
            )

    if re.search(r"\bobject_to_array\s*\(", cleaned):
        findings.append(
            LintFinding(
                "warning",
                "SPL2-DEPRECATED-FUNCTION",
                "`object_to_array()` was replaced by `json_entries()` in SPL2 release notes; update the pipeline before preview/apply.",
            )
        )

    if re.search(r"\(\?<[^=!]", text):
        findings.append(
            LintFinding(
                "warning",
                "SPL2-PCRE2-NAMED-CAPTURE",
                "Review named capture syntax; Splunk documents `(?P<fieldName>...)` for PCRE2 captures.",
            )
        )
    if re.search(r"\\[1-9]", text):
        findings.append(
            LintFinding(
                "warning",
                "SPL2-PCRE2-BACKREFERENCE",
                "Review numeric backreferences during PCRE2 migration.",
            )
        )

    if re.search(r"(^|\s)index\s*=", cleaned):
        findings.append(
            LintFinding(
                "warning",
                "SPL2-SPL1-INDEX-PREDICATE",
                "`index=` looks like SPL1 search syntax; review conversion to SPL2 source/partition/index routing.",
            )
        )
    for name, pattern in SPL1_COMMAND_PATTERNS.items():
        if pattern.search(cleaned):
            findings.append(
                LintFinding(
                    "warning",
                    "SPL2-SPL1-COMMAND",
                    f"`| {name}` is SPL1-shaped and should be reviewed with the SPL to SPL2 conversion tool.",
                )
            )

    return findings


def lint_file(path: Path, profile: str, *, strict: bool = False) -> dict:
    text = path.read_text(encoding="utf-8")
    findings = lint_text(text, profile, strict=strict)
    errors = [finding for finding in findings if finding.severity == "error"]
    return {
        "path": str(path),
        "profile": profile,
        "status": "FAIL" if errors else ("PASS_WITH_WARNINGS" if findings else "PASS"),
        "commands": command_names(text),
        "imports": sorted(import_names(text)),
        "findings": [finding.as_dict() for finding in findings],
    }


def render_custom_template_app(output_dir: Path) -> None:
    template = """// Example custom pipeline template module.
@template(
  name="ip_route_redact_template",
  description="Route and redact starter for Ingest Processor or Edge Processor",
  runtimes=["ingestProcessor", "edgeProcessor"],
  sourcetype="example:json"
)
$pipeline = | from $source
            | eval _raw = replace(_raw, "(?i)token=\\\\S+", "token=REDACTED")
            | into $destination;
"""
    write_file(output_dir / "custom-template-app/default/data/spl2/ip_route_redact_template.spl2", template)


def render_templates(output_dir: Path, profiles: list[str]) -> list[Path]:
    rendered: list[Path] = []
    for profile in profiles:
        for name, content in TEMPLATES[profile].items():
            path = output_dir / "templates" / profile / name
            write_file(path, content)
            rendered.append(path)
    render_custom_template_app(output_dir)
    return rendered


def render_coverage(output_dir: Path, profiles: list[str]) -> None:
    rows = []
    for feature in (
        "filter",
        "route",
        "branch_thru_copy",
        "redact",
        "hash",
        "sample",
        "lookup",
        "extract_json",
        "timestamp",
        "xml_object",
        "metrics",
        "ocsf",
        "decrypt",
        "stats",
        "s3_archive",
        "custom_pipeline_template",
        "spl_to_spl2_lint",
        "pcre2_lint",
    ):
        rows.append(
            {
                "feature": feature,
                "profiles": profiles,
                "coverage_status": "rendered" if feature not in {"spl_to_spl2_lint", "pcre2_lint"} else "lint",
            }
        )
    write_file(output_dir / "coverage-report.json", json.dumps(rows, indent=2) + "\n")


def render_lint_reports(output_dir: Path, reports: list[dict]) -> None:
    write_file(output_dir / "lint-report.json", json.dumps(reports, indent=2) + "\n")
    lines = ["# SPL2 Lint Report", ""]
    for report in reports:
        lines.append(f"## {report['path']}")
        lines.append("")
        lines.append(f"- Profile: `{report['profile']}`")
        lines.append(f"- Status: `{report['status']}`")
        lines.append(f"- Commands: {', '.join(report['commands']) or '(none)'}")
        lines.append(f"- Imports: {', '.join(report['imports']) or '(none)'}")
        if report["findings"]:
            lines.append("")
            for finding in report["findings"]:
                lines.append(f"- {finding['severity'].upper()} {finding['code']}: {finding['message']}")
        lines.append("")
    write_file(output_dir / "lint-report.md", "\n".join(lines).rstrip() + "\n")


def render_readme(output_dir: Path, profiles: list[str]) -> None:
    lines = [
        "# Rendered SPL2 Pipeline Kit",
        "",
        f"Profiles: {', '.join(profiles)}",
        "",
        "Use `templates/<profile>/*.spl2` as starters, then run `setup.sh --phase lint`",
        "against edited copies before previewing in Splunk.",
        "",
        "Secret policy: rendered files contain placeholders only. Keep lookup content,",
        "private keys, and tokens in local chmod 600 files or Splunk-managed objects.",
    ]
    write_file(output_dir / "README.md", "\n".join(lines) + "\n")


def collect_lint_targets(args: argparse.Namespace, rendered: list[Path]) -> list[Path]:
    targets = [Path(value).expanduser().resolve() for value in args.pipeline_file]
    if targets:
        return targets
    if rendered:
        return rendered
    out = Path(args.output_dir).expanduser().resolve()
    return sorted(out.glob("templates/**/*.spl2"))


def run_lint(args: argparse.Namespace, targets: list[Path]) -> list[dict]:
    profiles = profiles_for(args.profile)
    reports: list[dict] = []
    for target in targets:
        if not target.is_file():
            reports.append(
                {
                    "path": str(target),
                    "profile": args.profile,
                    "status": "FAIL",
                    "commands": [],
                    "imports": [],
                    "findings": [
                        {
                            "severity": "error",
                            "code": "SPL2-FILE-MISSING",
                            "message": "Pipeline file does not exist.",
                        }
                    ],
                }
            )
            continue
        target_profiles = profiles
        for profile in PROFILES:
            if f"/templates/{profile}/" in target.as_posix():
                target_profiles = [profile]
                break
        for profile in target_profiles:
            reports.append(lint_file(target, profile, strict=args.strict))
    return reports


def status_from_reports(reports: list[dict]) -> str:
    if any(report["status"] == "FAIL" for report in reports):
        return "FAIL"
    if any(report["status"] == "PASS_WITH_WARNINGS" for report in reports):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def run_smoke() -> int:
    with tempfile.TemporaryDirectory(prefix="spl2-kit-smoke-") as tmp:
        tmp_dir = Path(tmp)
        args = parse_args(["--phase", "all", "--profile", "both", "--output-dir", str(tmp_dir)])
        exit_code = main(args)
        required = [
            tmp_dir / "README.md",
            tmp_dir / "coverage-report.json",
            tmp_dir / "lint-report.json",
            tmp_dir / "templates/ingestProcessor/metrics.spl2",
            tmp_dir / "templates/edgeProcessor/route.spl2",
            tmp_dir / "custom-template-app/default/data/spl2/ip_route_redact_template.spl2",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if exit_code != 0 or missing:
            print(f"smoke_offline: FAIL missing={missing}", file=sys.stderr)
            return 1
    print("smoke_offline: OK")
    return 0


def main(args: argparse.Namespace | None = None) -> int:
    if args is None:
        args = parse_args()
    if args.phase == "smoke":
        return run_smoke()

    output_dir = Path(args.output_dir).expanduser().resolve()
    if args.phase in {"render", "all"}:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[Path] = []
    if args.phase in {"render", "all"}:
        rendered = render_templates(output_dir, profiles_for(args.profile))
        render_coverage(output_dir, profiles_for(args.profile))
        render_readme(output_dir, profiles_for(args.profile))

    reports: list[dict] = []
    if args.phase in {"lint", "validate", "all"}:
        targets = collect_lint_targets(args, rendered)
        reports = run_lint(args, targets)
        render_lint_reports(output_dir, reports)
    elif args.phase == "render":
        reports = run_lint(args, rendered)
        render_lint_reports(output_dir, reports)

    status = status_from_reports(reports) if reports else "PASS"
    if args.json:
        print(json.dumps({"status": status, "output_dir": str(output_dir)}, sort_keys=True))
    elif args.phase in {"render", "all", "lint", "validate"}:
        print(f"{status}: rendered/linted SPL2 assets in {output_dir}")
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
