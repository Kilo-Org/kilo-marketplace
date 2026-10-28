#!/usr/bin/env python3
"""Render Splunk Ingest Processor setup, SPL2, and handoff assets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "splunk-ingest-processor-rendered"
KIT_SCRIPT = REPO_ROOT / "skills/splunk-spl2-pipeline-kit/scripts/spl2_pipeline_kit.py"
VALID_DESTINATION_TYPES = {"splunk_cloud", "observability", "metrics_index", "s3"}
REFUSED_DESTINATION_TYPES = {"splunk_enterprise", "enterprise", "indexer_cluster", "hec"}
AFE_SUPPORTED_REGIONS = [
    "us-east-1",
    "eu-west-1",
    "eu-west-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "eu-central-1",
    "us-west-2",
    "eu-west-3",
]
KNOWN_ISSUE_GUARDRAILS = [
    {
        "code": "IP-NO-DELIVERY-GUARANTEE",
        "message": "Ingest Processors provide no data delivery guarantees during high back pressure or prolonged destination outages.",
    },
    {
        "code": "IP-TENANT-ADMIN-ONLY",
        "message": "Only Splunk Cloud tenant administrators can create and view Ingest Processor pipelines.",
    },
    {
        "code": "IP-BROWSER-SESSION-CAVEAT",
        "message": "Multiple browser sessions are not supported for concurrent pipeline editing.",
    },
    {
        "code": "IP-FORWARDER-USEACK-OFF",
        "message": "Forwarders sending data to Ingest Processor pipelines must set outputs.conf useACK=false.",
    },
    {
        "code": "IP-HEC-ACK-OFF",
        "message": "HEC tokens used to receive data through Ingest Processor must have indexer acknowledgement disabled.",
    },
    {
        "code": "IP-CIDR-LOOKUP-UNSUPPORTED",
        "message": "CIDR matching is not supported for Ingest Processor lookups.",
    },
]
DEFAULT_SOURCE_TYPES = ["aws:cloudtrail", "crowdstrike:fdr", "json_app"]
DEFAULT_DESTINATIONS = (
    "splunk_indexer=type=splunk_cloud;default=true,"
    "metrics=type=metrics_index;index=metrics,"
    "s3_archive=type=s3;format=parquet;bucket=example-bucket"
)
DEFAULT_PIPELINES = (
    "redact_auth=template=redact;sourcetype=json_app;destination=splunk_indexer,"
    "http_metrics=template=metrics;destination=metrics,"
    "cloudtrail_ocsf=template=ocsf;sourcetype=aws:cloudtrail;destination=splunk_indexer"
)
SECRET_KEY_RE = re.compile(r"(password|secret|token|private[_-]?key|access[_-]?key)", re.IGNORECASE)


FEATURE_COVERAGE = [
    ("Provisioning and entitlement", "ui_handoff"),
    ("Role and service account readiness", "rendered"),
    ("Source types and sample data", "rendered"),
    ("Forwarder HEC syslog Data Manager SC4S UF ingress handoffs", "delegated_handoff"),
    ("Splunk Cloud destination", "rendered"),
    ("Observability destination", "rendered"),
    ("Metrics index destination", "rendered"),
    ("Amazon S3 JSON Parquet destination", "rendered"),
    ("Default destination verification", "ui_handoff"),
    ("Route branch thru copy templates", "rendered"),
    ("Redact hash sample lookup extract timestamp JSON XML templates", "rendered"),
    ("Logs to metrics", "rendered"),
    ("OCSF conversion", "rendered"),
    ("Decrypt private-key lookup", "rendered"),
    ("Stats aggregation", "rendered"),
    ("Custom pipeline templates", "rendered"),
    ("AI-powered data management readiness", "ui_handoff"),
    ("Automated Field Extraction", "ui_handoff"),
    ("Automated Field Extraction region allowlist", "rendered"),
    ("SPL to SPL2 conversion review", "lint"),
    ("PCRE2 compatibility lint", "lint"),
    ("Lifecycle apply edit remove refresh delete", "ui_handoff"),
    ("Queue DLQ Usage Summary monitoring", "rendered"),
    ("Known issue guardrails", "rendered"),
    ("Data-source readiness downstream validation", "delegated_handoff"),
    ("Splunk Enterprise destination", "refused_handoff"),
]


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("render", "doctor", "status", "validate", "all"), default="render")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--tenant-name", default="example-prod")
    parser.add_argument("--stack-url", default="https://example-prod.scs.splunk.com")
    parser.add_argument("--subscription-tier", choices=("unknown", "essentials", "premier"), default="unknown")
    parser.add_argument("--source-types", default=",".join(DEFAULT_SOURCE_TYPES))
    parser.add_argument("--destinations", default=DEFAULT_DESTINATIONS)
    parser.add_argument("--pipelines", default=DEFAULT_PIPELINES)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def write_file(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


def csv_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def split_specs(value: str) -> list[str]:
    return csv_list(value)


def parse_spec_list(value: str) -> list[dict[str, str]]:
    specs = []
    for item in split_specs(value):
        fields: dict[str, str] = {}
        chunks = [chunk.strip() for chunk in item.split(";") if chunk.strip()]
        if not chunks:
            continue
        first = chunks.pop(0)
        if "=" in first and not first.startswith(("type=", "template=", "destination=")):
            name, rest = first.split("=", 1)
            fields["name"] = name.strip()
            if rest:
                chunks.insert(0, rest)
        else:
            fields["name"] = first.strip()
        for chunk in chunks:
            if "=" not in chunk:
                fields[chunk] = "true"
                continue
            key, val = chunk.split("=", 1)
            fields[key.strip()] = val.strip()
        validate_secret_fields(fields)
        specs.append(fields)
    return specs


def validate_secret_fields(spec: dict[str, str]) -> None:
    for key, value in spec.items():
        if SECRET_KEY_RE.search(key) and not key.endswith("_file"):
            raise ValueError(f"Raw secret-like field `{key}` is not allowed; use `{key}_file` or a Splunk-managed object.")
        if SECRET_KEY_RE.search(value) and "/" not in value and value.lower() not in {"true", "false"}:
            raise ValueError("Raw secret-like values are not allowed in Ingest Processor specs.")


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value.strip())
    return cleaned or "unnamed"


def render_source_type(name: str) -> str:
    payload = {
        "name": name,
        "event_breaking": {
            "mode": "ui_handoff",
            "review": [
                "Confirm line breaking and event merging in Ingest Processor preview.",
                "Use raw or parsed CSV sample data before applying a pipeline.",
                "Confirm _time extraction and timezone handling.",
            ],
        },
        "sample_data": {
            "raw_file": f"samples/{safe_name(name)}.raw",
            "parsed_csv": f"samples/{safe_name(name)}.csv",
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def render_destination(dest: dict[str, str]) -> str:
    dest_type = dest.get("type", "splunk_cloud")
    payload = {
        "name": dest["name"],
        "type": dest_type,
        "status": "rendered" if dest_type in VALID_DESTINATION_TYPES else "refused_handoff",
        "settings": {key: value for key, value in sorted(dest.items()) if key not in {"name", "type"}},
    }
    if dest_type == "s3" and payload["settings"].get("object_lock", "").lower() == "true":
        payload["status"] = "refused_handoff"
        payload["finding"] = "S3 Object Lock requires manual review and is not rendered by this skill."
    if dest_type in REFUSED_DESTINATION_TYPES:
        payload["finding"] = "Use splunk-edge-processor-setup for Splunk Enterprise or HEC-style destinations."
    return json.dumps(payload, indent=2) + "\n"


def run_kit(output_dir: Path) -> Path:
    kit_out = output_dir / "spl2-pipeline-kit"
    subprocess.run(
        [
            sys.executable,
            str(KIT_SCRIPT),
            "--phase",
            "all",
            "--profile",
            "ingestProcessor",
            "--output-dir",
            str(kit_out),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return kit_out


def template_from_kit(kit_out: Path, template_name: str) -> str:
    normalized = template_name if template_name.endswith(".spl2") else f"{template_name}.spl2"
    path = kit_out / "templates/ingestProcessor" / normalized
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return (
        f"// Generated fallback for template {template_name}.\n"
        "$pipeline = | from $source\n"
        "            | into $destination;\n"
    )


def render_pipeline(pipe: dict[str, str], kit_out: Path) -> str:
    content = template_from_kit(kit_out, pipe.get("template", "filter"))
    header = [
        f"// Ingest Processor pipeline: {pipe['name']}",
        f"// Template: {pipe.get('template', 'filter')}",
        f"// Destination: {pipe.get('destination', '$destination')}",
    ]
    if "sourcetype" in pipe:
        header.append(f"// Source type: {pipe['sourcetype']}")
    return "\n".join(header) + "\n" + content


def collect_findings(destinations: list[dict[str, str]], pipelines: list[dict[str, str]], tier: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if tier == "unknown":
        findings.append(
            {
                "severity": "warning",
                "code": "IP-TIER-UNKNOWN",
                "message": "Subscription tier is unknown; verify Essentials/Premier entitlement, ingest volume, and persistent queue retention.",
            }
        )
    if not any(dest.get("default", "").lower() == "true" for dest in destinations):
        findings.append(
            {
                "severity": "warning",
                "code": "IP-DEFAULT-DESTINATION",
                "message": "No destination is marked default in the worksheet; confirm default destination behavior in the UI before applying.",
            }
        )
    for dest in destinations:
        dest_type = dest.get("type", "splunk_cloud")
        if dest_type in REFUSED_DESTINATION_TYPES:
            findings.append(
                {
                    "severity": "error",
                    "code": "IP-DESTINATION-REFUSED",
                    "message": f"Destination `{dest['name']}` uses `{dest_type}`; route this workflow to splunk-edge-processor-setup.",
                }
            )
        if dest_type == "s3" and dest.get("object_lock", "").lower() == "true":
            findings.append(
                {
                    "severity": "error",
                    "code": "IP-S3-OBJECT-LOCK",
                    "message": "S3 Object Lock destination settings require manual review and are refused by this renderer.",
                }
            )
    if any(pipe.get("template") == "metrics" for pipe in pipelines):
        findings.append(
            {
                "severity": "info",
                "code": "IP-METRICS-ROLLUP",
                "message": "Review logs_to_metrics metric types and Observability rollups before apply.",
            }
        )
    if any(pipe.get("template") == "decrypt" for pipe in pipelines):
        findings.append(
            {
                "severity": "warning",
                "code": "IP-DECRYPT-THROUGHPUT",
                "message": "Decrypt is resource-intensive; validate RSA/PKCS#1 v1.5 private-key lookup and throughput in preview.",
            }
        )
    return findings


def render_readiness(args: argparse.Namespace, findings: list[dict[str, str]]) -> str:
    lines = [
        "# Ingest Processor Readiness Report",
        "",
        f"- Tenant: `{args.tenant_name}`",
        f"- Stack URL: `{args.stack_url}`",
        f"- Subscription tier: `{args.subscription_tier}`",
        "- Experience: verify Splunk Cloud Platform Victoria Experience.",
        "- Provisioning: verify Ingest Processor is enabled or open a Splunk Support case.",
        "- Roles: verify `sc_admin`, `admin_all_objects`, and service account/index access.",
        "- Connection refresh: refresh after index, lookup, or role changes.",
        "- Limits: verify pipeline count, lookup size, ingest volume, and persistent queue retention against service details.",
        "- Automated Field Extraction: UI handoff only; supported regions are "
        + ", ".join(f"`{region}`" for region in AFE_SUPPORTED_REGIONS)
        + ".",
        "- AI-powered data management: review assistant-generated onboarding, schema, and pipeline recommendations in the UI; this renderer keeps them as handoffs until Splunk publishes a stable public API.",
        "",
        "## Known Issue Guardrails",
        "",
    ]
    lines.extend(f"- {item['code']}: {item['message']}" for item in KNOWN_ISSUE_GUARDRAILS)
    lines.extend(
        [
        "",
        "## Findings",
        "",
        ]
    )
    if not findings:
        lines.append("- No blocking findings in the rendered worksheet.")
    for finding in findings:
        lines.append(f"- {finding['severity'].upper()} {finding['code']}: {finding['message']}")
    return "\n".join(lines) + "\n"


def render_apply_plan(args: argparse.Namespace, source_types: list[str], destinations: list[dict[str, str]], pipelines: list[dict[str, str]], findings: list[dict[str, str]]) -> str:
    plan = {
        "workflow": "splunk-ingest-processor-setup",
        "tenant": args.tenant_name,
        "api_crud": "not_claimed",
        "actions": [
            {"order": 1, "type": "ui_handoff", "object": "provisioning", "description": "Confirm Ingest Processor is provisioned for the tenant."},
            {"order": 2, "type": "ui_handoff", "object": "source_types", "items": source_types},
            {"order": 3, "type": "ui_handoff", "object": "destinations", "items": [dest["name"] for dest in destinations]},
            {"order": 4, "type": "ui_handoff", "object": "pipelines", "items": [pipe["name"] for pipe in pipelines]},
            {"order": 5, "type": "ui_handoff", "object": "preview_apply", "description": "Preview with sample data, verify default destination, then apply in UI."},
            {"order": 6, "type": "delegated_handoff", "object": "post_ingest_readiness", "skill": "splunk-data-source-readiness-doctor"},
        ],
        "findings": findings,
    }
    return json.dumps(plan, indent=2) + "\n"


def render_coverage() -> str:
    rows = [
        {"feature": feature, "coverage_status": status}
        for feature, status in FEATURE_COVERAGE
    ]
    return json.dumps(rows, indent=2) + "\n"


def render_ui_handoff(source_types: list[str], destinations: list[dict[str, str]], pipelines: list[dict[str, str]]) -> str:
    lines = [
        "# Ingest Processor UI Handoff",
        "",
        "1. Open Splunk Cloud Platform Data Management -> Ingest Processor.",
        "2. Confirm provisioning, roles, service account access, indexes, and lookups.",
        "3. Create or review source types with the rendered JSON notes.",
        "4. Create destinations in this order: Splunk Cloud, metrics, Observability, S3.",
        "5. Create pipelines from `pipelines/*.spl2` or the custom template app.",
        "6. Preview every pipeline with representative sample data.",
        "7. Confirm index routing and default destination behavior.",
        "8. Review any AI-powered data management or Automated Field Extraction recommendations before accepting generated schema or pipeline changes.",
        "9. Confirm only one browser session is editing each pipeline.",
        "10. Apply pipelines and immediately run the rendered monitoring searches.",
        "",
        "## Source Types",
        "",
    ]
    lines.extend(f"- `{source_type}`" for source_type in source_types)
    lines.extend(["", "## Destinations", ""])
    lines.extend(f"- `{dest['name']}` (`{dest.get('type', 'splunk_cloud')}`)" for dest in destinations)
    lines.extend(["", "## Pipelines", ""])
    lines.extend(f"- `{pipe['name']}` -> `{pipe.get('destination', 'review')}`" for pipe in pipelines)
    return "\n".join(lines) + "\n"


def render_lifecycle(name: str) -> str:
    steps = {
        "apply": "Preview, confirm destination, apply, then monitor queues and destination indexes.",
        "edit": "Clone or edit pipeline, preview with sample data, and compare output before reapply.",
        "remove": "Remove only after confirming alternate routing for matching data.",
        "refresh": "Refresh connections after index, lookup, role, or destination changes.",
        "delete": "Delete only after pipeline is removed and no data source depends on it.",
        "rollback": "Reapply the last known good pipeline text and validate destination counts.",
    }
    return f"# Ingest Processor {name.title()} Runbook\n\n{steps[name]}\n"


def render_monitoring_searches(source_types: list[str], destinations: list[dict[str, str]]) -> str:
    sourcetype_clause = " OR ".join(f'sourcetype="{source_type}"' for source_type in source_types)
    index_names = [dest.get("index") for dest in destinations if dest.get("index")]
    index_clause = " OR ".join(f"index={index}" for index in index_names) or "index=*"
    return f"""# Ingest Processor validation searches. Review and run in Splunk Search.

({sourcetype_clause}) earliest=-24h latest=now
| stats count max(_time) as latest min(_time) as earliest by index sourcetype host source

{index_clause} earliest=-24h latest=now
| stats count by index sourcetype

index=_internal earliest=-24h ("Ingest Processor" OR ingest_processor OR scpbridge)
| stats count by sourcetype source host

index=_audit earliest=-24h ("Ingest Processor" OR "pipeline")
| table _time user action info

| mstats sum(*) as value where index=* earliest=-24h by metric_name
| search metric_name="*ingest*" OR metric_name="*queue*"
"""


def render_usage_handoff() -> str:
    return """# Usage Summary And Queue Handoff

- Open the Ingest Processor Usage Summary dashboard after applying pipelines.
- Check persistent queue and DLQ indicators before and after fan-out changes.
- Compare source-event count with every destination count when using `branch`,
  `route`, or `thru`.
- Treat blocked destinations as urgent because route/fan-out can duplicate
  queue pressure.
"""


def render_known_issues() -> str:
    lines = [
        "# Ingest Processor Known Issue Guardrails",
        "",
        "Render and review these before any pipeline apply.",
        "",
    ]
    lines.extend(f"- {item['code']}: {item['message']}" for item in KNOWN_ISSUE_GUARDRAILS)
    lines.extend(
        [
            "",
            "## Automated Field Extraction Regions",
            "",
            "AFE is a UI handoff only and is documented for these regions:",
            "",
        ]
    )
    lines.extend(f"- `{region}`" for region in AFE_SUPPORTED_REGIONS)
    return "\n".join(lines) + "\n"


def render_handoffs() -> dict[str, str]:
    return {
        "splunk-hec-service-setup.md": "# HEC Handoff\n\nUse `splunk-hec-service-setup` for HEC token/index readiness. Keep `useACK=false` for Ingest Processor source paths that do not support indexer acknowledgement.\n",
        "splunk-edge-processor-setup.md": "# Edge Processor Handoff\n\nUse `splunk-edge-processor-setup` for Splunk Enterprise destinations, customer-managed runtime routing, syslog/HEC/S2S edge collection, or EP-specific destination catalogs.\n",
        "splunk-federated-search-s3.md": "# S3 Federated Search Handoff\n\nWhen IP writes archive data to S3 and operators need search access, hand off to `splunk-federated-search-setup` for Federated Search for Amazon S3 readiness.\n",
        "splunk-data-source-readiness-doctor.md": "# Data Source Readiness Handoff\n\nAfter applying IP pipelines, run `splunk-data-source-readiness-doctor` with expected indexes, sourcetypes, macros, CIM/OCSF expectations, and sample-event evidence.\n",
    }


def render_assets(args: argparse.Namespace) -> Path:
    output_dir = Path(args.output_dir).expanduser().resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_types = csv_list(args.source_types) or DEFAULT_SOURCE_TYPES
    destinations = parse_spec_list(args.destinations)
    pipelines = parse_spec_list(args.pipelines)
    kit_out = run_kit(output_dir)
    findings = collect_findings(destinations, pipelines, args.subscription_tier)

    write_file(output_dir / "README.md", "# Rendered Splunk Ingest Processor Assets\n\nReview `readiness-report.md`, then follow `control-plane-handoffs/ingest-processor-ui.md`.\n")
    write_file(output_dir / "readiness-report.md", render_readiness(args, findings))
    write_file(output_dir / "coverage-report.json", render_coverage())
    write_file(output_dir / "findings.json", json.dumps(findings, indent=2) + "\n")
    write_file(output_dir / "apply-plan.json", render_apply_plan(args, source_types, destinations, pipelines, findings))
    write_file(output_dir / "control-plane-handoffs/ingest-processor-ui.md", render_ui_handoff(source_types, destinations, pipelines))
    write_file(output_dir / "control-plane-handoffs/known-issues.md", render_known_issues())
    for source_type in source_types:
        write_file(output_dir / f"source-types/{safe_name(source_type)}.json", render_source_type(source_type))
    for dest in destinations:
        write_file(output_dir / f"destinations/{safe_name(dest['name'])}.json", render_destination(dest))
    for pipe in pipelines:
        write_file(output_dir / f"pipelines/{safe_name(pipe['name'])}.spl2", render_pipeline(pipe, kit_out))
    for lifecycle in ("apply", "edit", "remove", "refresh", "delete", "rollback"):
        write_file(output_dir / f"lifecycle/{lifecycle}.md", render_lifecycle(lifecycle))
    write_file(output_dir / "monitoring/searches.spl", render_monitoring_searches(source_types, destinations))
    write_file(output_dir / "monitoring/usage-summary-handoff.md", render_usage_handoff())
    for name, content in render_handoffs().items():
        write_file(output_dir / f"handoffs/{name}", content)
    return output_dir


def validate_output(output_dir: Path) -> list[str]:
    required = [
        "README.md",
        "readiness-report.md",
        "coverage-report.json",
        "apply-plan.json",
        "control-plane-handoffs/ingest-processor-ui.md",
        "control-plane-handoffs/known-issues.md",
        "monitoring/searches.spl",
        "monitoring/usage-summary-handoff.md",
        "spl2-pipeline-kit/lint-report.json",
    ]
    missing = [rel for rel in required if not (output_dir / rel).is_file()]
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in output_dir.rglob("*")
        if path.is_file() and path.suffix in {".md", ".json", ".spl", ".spl2", ".sh"}
    )
    forbidden = [
        "POST /services/data-manager/input",
        "PUT /services/data-manager/input",
        "terraform resource splunk_cloud_data_manager_input",
        "global HEC ACK",
        "BEGIN PRIVATE KEY",
    ]
    missing.extend(f"forbidden phrase present: {phrase}" for phrase in forbidden if phrase in combined)
    return missing


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = render_assets(args)
    problems: list[str] = []
    if args.phase in {"validate", "all", "doctor", "status"}:
        problems = validate_output(output_dir)
        write_file(
            output_dir / "validation-report.json",
            json.dumps({"status": "FAIL" if problems else "PASS", "problems": problems}, indent=2) + "\n",
        )
    status = "FAIL" if problems else "PASS"
    if args.json:
        print(json.dumps({"status": status, "output_dir": str(output_dir), "problems": problems}, sort_keys=True))
    else:
        print(f"{status}: rendered Ingest Processor assets in {output_dir}")
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
