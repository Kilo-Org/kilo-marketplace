#!/usr/bin/env python3
"""Classify each step of a Tarosec purple exercise into a detection outcome.

Offline and deterministic: reads a tarosec.exercise/v1 JSON file with recorded
results and prints per-step outcomes. It never executes emulation, contacts a
SIEM/EDR, or decides authorization.

Usage: classify_exercise.py EXERCISE.json [--json]
Exit: 0 classified, 1 invalid exercise, 2 usage/IO error.

Outcomes are documented in the skill's SKILL.md.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from validate_record import load_json, validate  # noqa: E402  (synced sibling)

SCHEMA = os.path.join(HERE, "..", "assets", "schemas", "exercise.schema.json")


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else None  # naive timestamps cannot be ordered safely


def classify_step(step: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    res = step.get("results")
    if not res:
        return "Not run", ["no results recorded"]
    status = res["execution"]["status"]
    if status in ("not_run", "blocked"):
        return "Not run", [f"execution status {status}"]
    if status in ("failed", "unknown"):
        return "Inconclusive", [f"execution {status}: no evidence the behavior occurred"]

    expected = step["expected"]
    host = step["targetHost"]
    alerts = res.get("alerts", [])
    started = _ts(res["execution"].get("startedAt"))
    ended = _ts(res["execution"].get("endedAt"))
    if started is not None and ended is not None and started > ended:
        return "Inconclusive", ["execution start is after its reported end"]
    expected_rules = dict.fromkeys(expected["detections"])
    for alert in alerts:
        if alert["ruleId"] not in expected_rules and alert["status"] == "fired":
            reasons.append(f"unexpected rule {alert['ruleId']} fired (not counted)")

    matched = []
    unresolved = []
    for rule in expected_rules:
        rows = [alert for alert in alerts if alert["ruleId"] == rule]
        fired = [alert for alert in rows if alert["status"] == "fired"]
        correlated = []
        for alert in fired:
            timestamp = _ts(alert.get("firedAt"))
            if started is not None and timestamp is not None and timestamp < started:
                reasons.append(f"{rule}: observed firing predates the execution window")
            elif alert.get("host") == host:
                correlated.append(alert)
        negatives = [alert for alert in rows if alert["status"] == "not_fired"
                     and alert.get("host", host) == host]
        if correlated and not negatives:
            matched.append((rule, correlated))
        elif fired or not negatives or any(alert["status"] == "unknown" for alert in rows):
            unresolved.append(rule)
            observed_hosts = ", ".join(sorted({alert.get("host") or "unknown" for alert in fired}))
            detail = f"; reported firing host(s): {observed_hosts}, expected {host}" if fired else ""
            reasons.append(f"{rule}: alert evidence missing, conflicting or unattributed{detail}")
        else:
            reasons.append(f"{rule}: export records no firing")

    if res["execution"].get("prevented"):
        state = "with a correlated alert" if matched else "with no confirmed matching alert"
        return "Prevented", reasons + [f"control blocked execution ({state})"]

    if matched:
        budget = expected["maxLatencySeconds"]
        any_late = False
        for rule, rows in matched:
            timestamps = [_ts(alert.get("firedAt")) for alert in rows]
            # An alert can fire during the step. Use the first ordered alert
            # and measure post-execution delay, with zero for in-step firing.
            if ended is None or any(ts is None for ts in timestamps):
                reasons.append(f"{rule}: latency unmeasurable (missing, invalid or naive timestamp)")
                continue
            first = min(timestamps)
            if first < ended and started is None:
                reasons.append(f"{rule}: latency unmeasurable (alert predates end and start is unknown)")
                continue
            delay = max(0.0, (first - ended).total_seconds())
            any_late |= delay > budget
            reasons.append(f"{rule}: {delay:g}s post-execution delay (budget {budget}s)")
        if expected.get("requireTelemetryForDetection"):
            missing = [source for source in expected["telemetrySources"] if
                       {row["status"] for row in res.get("telemetry", []) if row["source"] == source} != {"observed"}]
            if missing:
                return "Partially detected", reasons + ["Unconfirmed expected telemetry: " + ", ".join(missing)]
        if len(matched) != len(expected_rules):
            return "Partially detected", reasons
        return ("Detected (late)" if any_late else "Detected"), reasons

    if unresolved:
        return "Inconclusive", reasons

    missing_healthy, missing_unknown = [], []
    for src in expected["telemetrySources"]:
        observations = [item for item in res.get("telemetry", []) if item["source"] == src]
        states = {item["status"] for item in observations}
        if states == {"observed"}:
            continue
        if states == {"absent"} and all(item.get("sourceHealthy") is True for item in observations):
            missing_healthy.append(src)
        else:
            missing_unknown.append(src)
    if missing_unknown:
        return "Inconclusive", reasons + [
            f"unresolved telemetry from {', '.join(missing_unknown)} (missing, unhealthy or conflicting)"]
    if missing_healthy:
        return "Telemetry gap", reasons + [f"healthy source(s) recorded nothing: {', '.join(missing_healthy)}"]
    return "Detection gap", reasons + ["expected telemetry observed; expected rule(s) did not fire"]


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--json"]
    if len(args) != 1:
        print("usage: classify_exercise.py EXERCISE.json [--json]", file=sys.stderr)
        return 2
    try:
        with open(args[0], encoding="utf-8") as f:
            exercise = load_json(f)
        with open(SCHEMA, encoding="utf-8") as f:
            schema = load_json(f)
        errors = validate(exercise, schema)
    except (OSError, ValueError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("INVALID exercise:\n" + "\n".join(errors))
        return 1
    rows = []
    for step in exercise["steps"]:
        outcome, reasons = classify_step(step)
        results = step.get("results", {})
        observations = [results.get("execution", {}), *results.get("telemetry", []),
                        *results.get("alerts", [])]
        evidence_refs = list(dict.fromkeys(ref for row in observations for ref in row.get("evidenceRefs", [])))
        rows.append({"step": step["id"], "technique": step.get("technique", {}).get("id"),
                     "outcome": outcome, "reasons": reasons, "evidenceRefs": evidence_refs})
    if "--json" in argv:
        print(json.dumps({"exercise": exercise["id"], "steps": rows}, indent=2))
    else:
        for r in rows:
            print(f"{r['step']}\t{r['technique'] or 'unmapped'}\t{r['outcome']}\t{'; '.join(r['reasons'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
