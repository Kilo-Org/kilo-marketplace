#!/usr/bin/env python3
"""Build a reproducible exercise from inert event fixtures or sanitized replay."""
import argparse
import hashlib
import io
import json
import os
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from classify_exercise import classify_step
from validate_record import load_json, validate

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ENGINE_VERSION = "1.0.0"
EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)
MAX_BYTES = 256 * 1024
MAX_RECORDS = 1000
MAX_OFFSET = 86400
HOST = "fixture-host"
LIMITATIONS = [
    "Events and rule observations are fixture data. Results apply to this evaluation pipeline.",
    "A digest binds the observation export to the event bytes. Source authenticity is unverified.",
]
OUTCOMES = {
    "Detected": "detected", "Detected (late)": "detected",
    "Detection gap": "not_detected", "Partially detected": "partially_detected",
    "Inconclusive": "inconclusive", "Telemetry gap": "inconclusive",
}


def canonical(record):
    return (json.dumps(record, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def timestamp(offset):
    return (EPOCH + timedelta(seconds=offset)).isoformat()


def checked(record, schema_name):
    with (ASSETS / "schemas" / f"{schema_name}.schema.json").open() as stream:
        errors = validate(record, load_json(stream))
    if errors:
        raise ValueError(f"{schema_name}: {errors[0]}")
    return record


def read_fixture(directory, name):
    # Resolve only fixed fixture basenames relative to an open directory.
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except OSError as exc:
        raise ValueError(f"{name}: {exc.strerror}") from None
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f"{name}: expected a regular file")
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"{name}: exceeds the input byte limit")
    return data


def decode(data):
    return load_json(io.StringIO(data.decode("utf-8")))


def read_events(directory, mode, ndjson):
    data = read_fixture(directory, "events.ndjson" if ndjson else "events.json")
    if ndjson:
        lines = data.splitlines()
        if len(lines) > MAX_RECORDS:
            raise ValueError("too many event records")
        events = [decode(line) for line in lines]
    else:
        events = decode(data)
    if isinstance(events, list) and len(events) > MAX_RECORDS:
        raise ValueError("too many event records")
    checked(events, "simulation-events")
    if any(event["offsetSeconds"] > MAX_OFFSET for event in events):
        raise ValueError("event offset exceeds the logical clock limit")
    if mode == "synthetic":
        events = [dict(event, synthetic=True) for event in events]
    return sorted(events, key=lambda event: (event["offsetSeconds"], event["type"], event.get("synthetic", False)))


def read_alerts(directory, event_bytes, expected, first_offset):
    raw = decode(read_fixture(directory, "alerts.json"))
    if isinstance(raw, dict) and isinstance(raw.get("alerts"), list) and len(raw["alerts"]) > MAX_RECORDS:
        raise ValueError("too many rule observations")
    export = checked(raw, "simulation-alerts")
    if export["eventsSha256"] != digest(event_bytes):
        raise ValueError("alerts.json: event digest mismatch")
    seen = set()
    for alert in export["alerts"]:
        rule = alert["rule"]
        if rule in seen or rule not in expected:
            raise ValueError("alerts.json: duplicate or unexpected rule")
        seen.add(rule)
        has_time = "offsetSeconds" in alert
        if has_time != (alert["status"] == "fired"):
            raise ValueError("alerts.json: offset is required only for a fired alert")
        if has_time and not first_offset <= alert["offsetSeconds"] <= MAX_OFFSET:
            raise ValueError("alerts.json: firing outside the logical exercise window")
    export["alerts"].sort(key=lambda alert: alert["rule"])
    return export


def assess(scenario, events, export, run_id):
    expected = scenario["expected"]
    observed = sorted({event["type"] for event in events})
    start = timestamp(events[0]["offsetSeconds"])
    end = timestamp(events[-1]["offsetSeconds"])
    alerts = []
    if export:
        for alert in export["alerts"]:
            status = alert["status"]
            if status == "not_fired" and not export["windowComplete"]:
                status = "unknown"
            observation = dict(ruleId=alert["rule"], status=status, host=HOST, evidenceRefs=["alerts"])
            if status == "fired":
                observation["firedAt"] = timestamp(alert["offsetSeconds"])
            alerts.append(observation)
    step = {
        "id": "fixture", "description": "Evaluate the recorded fixture", "targetHost": HOST,
        "expected": {"telemetrySources": expected["events"], "detections": expected["rules"],
                     "requireTelemetryForDetection": True, "maxLatencySeconds": MAX_OFFSET},
        "results": {
            "execution": {"status": "executed", "startedAt": start, "endedAt": end,
                          "evidenceRefs": ["events"]},
            "telemetry": [{"source": kind, "status": "observed", "evidenceRefs": ["events"]}
                          for kind in observed],
            "alerts": alerts,
        },
    }
    status, reasons = classify_step(step)
    outcome = OUTCOMES[status]
    if not export:
        reasons.append("No independent defensive rule observations were supplied.")
    elif not export["windowComplete"]:
        reasons.append("The defensive report does not establish full window coverage.")
    exercise = {
        "schemaVersion": "tarosec.exercise/v1", "id": "sim-" + run_id,
        "name": scenario["id"], "environment": "offline", "attackVersion": "unmapped",
        "window": {"start": start, "end": timestamp(max(
            [events[-1]["offsetSeconds"]] + [a.get("offsetSeconds", 0) for a in (export or {}).get("alerts", [])]))},
        "limitations": LIMITATIONS,
        "steps": [step],
    }
    return outcome, reasons, observed, exercise, start, end


def run(args):
    if args.mode == "synthetic":
        if args.ndjson or args.alerts:
            raise ValueError("synthetic mode accepts only a catalog ID and output directory")
        matches = {p.name: p for p in (ASSETS / "scenarios").iterdir() if p.is_dir()}
        source = matches.get(args.input)
        if source is None:
            source = matches.get("auth." + args.input)
        if source is None:
            raise ValueError("unknown built-in scenario")
    else:
        source = Path(args.input)
        if ":" in args.input or ".." in source.parts:
            raise ValueError("replay requires a local directory path without parent traversal")
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ValueError("this host cannot enforce fixture directory restrictions")
    directory = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        scenario = checked(decode(read_fixture(directory, "scenario.json")), "scenario")
        if len(scenario["expected"]["rules"]) > MAX_RECORDS:
            raise ValueError("too many expected rules")
        events = read_events(directory, args.mode, args.ndjson)
        event_bytes = canonical(events)
        export = read_alerts(directory, event_bytes, scenario["expected"]["rules"],
                             events[0]["offsetSeconds"]) if args.alerts else None
    finally:
        os.close(directory)
    records = {"scenario.json": canonical(scenario), "events.json": event_bytes}
    if export:
        records["alerts.json"] = canonical(export)
    run_id = digest(canonical([ENGINE_VERSION, args.mode, {name: digest(data) for name, data in records.items()}]))
    outcome, reasons, observed, exercise, start, end = assess(scenario, events, export, run_id)
    records["exercise.json"] = canonical(checked(exercise, "exercise"))
    result = {
        "schemaVersion": "tarosec.simulation-result/v1", "engineVersion": ENGINE_VERSION,
        "scenario": scenario["id"], "scenarioVersion": scenario["version"], "runId": run_id,
        "mode": args.mode, "execution": "completed", "outcome": outcome,
        "startedAt": start, "endedAt": end, "eventCount": len(events),
        "expectedEvents": scenario["expected"]["events"], "expectedRules": scenario["expected"]["rules"],
        "observedEvents": observed, "limitations": LIMITATIONS, "reasons": reasons,
        "evidence": [{"id": Path(name).stem, "path": name, "sha256": digest(data)} for name, data in records.items()],
    }
    output = Path(args.output)
    if ":" in args.output or ".." in output.parts or output.resolve().is_relative_to(source.resolve()):
        raise ValueError("output must be a new directory outside the input directory")
    report = (
        f"# Simulation report\n\nScenario **{result['scenario']}** ran in {args.mode} mode.\n\n"
        f"Execution **completed** with {len(events)} events. Detection outcome **{outcome}**.\n\n"
        "## Evidence\n\n" + "".join(f"- {item['path']} SHA-256 `{item['sha256']}`\n" for item in result["evidence"])
        + "\n## Assessment and limits\n\n" + "".join(f"- {line}\n" for line in reasons + LIMITATIONS)
    )
    result_bytes = canonical(checked(result, "simulation-result"))
    output.mkdir(mode=0o700)
    directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        artifacts = {**records, "report.md": report.encode("utf-8"), "result.tmp": result_bytes}
        for name, data in artifacts.items():
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600,
                         dir_fd=directory)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        os.replace("result.tmp", "result.json", src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        os.close(directory)
    print(f"{outcome} — {len(events)} events — {output / 'report.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("list")
    for mode in ("synthetic", "replay"):
        command = modes.add_parser(mode)
        command.add_argument("input", help="catalog ID" if mode == "synthetic" else "local fixture directory")
        command.add_argument("--output", required=True, help="new output directory with an existing parent")
        if mode == "replay":
            command.add_argument("--ndjson", action="store_true")
            command.add_argument("--alerts", action="store_true")
        command.set_defaults(ndjson=False, alerts=False)
    args = parser.parse_args()
    if args.mode == "list":
        for path in sorted((ASSETS / "scenarios").glob("*/scenario.json")):
            print(path.parent.name)
        return 0
    try:
        run(args)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        reason = exc.strerror if isinstance(exc, OSError) else str(exc)
        failure = {"schemaVersion": "tarosec.simulation-result/v1", "execution": "failed",
                   "outcome": "not_executed", "reasons": [reason]}
        print(canonical(failure).decode(), end="", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
