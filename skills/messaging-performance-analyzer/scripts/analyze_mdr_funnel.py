#!/usr/bin/env python3
"""Analyze a Sent MDR export and report funnel drop-off by lifecycle stage.

Lifecycle stages (in order): QUEUED, ROUTED, SENT, DELIVERED, READ.

The script counts distinct messages that reached at least each stage,
computes the drop-off percentage between adjacent stages, and flags any
stage where drop-off exceeds the configured threshold.

Exit codes:
    0 - healthy funnel (no stage drops more than --threshold)
    2 - bad arguments / malformed input
    3 - unhealthy funnel (one or more stages exceed the threshold)

Examples:
    python analyze_mdr_funnel.py path/to/mdr.json
    python analyze_mdr_funnel.py path/to/mdr.csv --threshold 15
    python analyze_mdr_funnel.py path/to/mdr.json --show-errors
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

# Ordered lifecycle stages. A message that reached stage N is counted as
# having reached every earlier stage as well.
STAGES: tuple[str, ...] = ("QUEUED", "ROUTED", "SENT", "DELIVERED", "READ")
STAGE_RANK: dict[str, int] = {s: i for i, s in enumerate(STAGES)}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="analyze_mdr_funnel.py",
        description=(
            "Analyze a Sent MDR export and report funnel drop-off by "
            "lifecycle stage (QUEUED -> ROUTED -> SENT -> DELIVERED -> READ)."
        ),
    )
    parser.add_argument(
        "path",
        help="Path to the MDR export (CSV or JSON; format auto-detected by extension).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help=(
            "Drop-off percentage threshold per stage. Any stage with a "
            "drop-off greater than this value triggers a non-zero exit. "
            "Default: 20."
        ),
    )
    parser.add_argument(
        "--show-errors",
        action="store_true",
        help=(
            "When set, also summarise the count of each Sent send-time error "
            "code (ERR_*) parsed from the 'description' field of FAILED "
            "messages. Non-FAILED rows and rows without a description are "
            "ignored. Does not change exit codes."
        ),
    )
    return parser.parse_args(argv)


class InputError(Exception):
    """Raised for malformed or missing input. Mapped to exit code 2."""


def _load_messages(path: Path) -> list[dict]:
    if not path.is_file():
        raise InputError(f"file not found: {path}")
    ext = path.suffix.lower()
    if ext == ".json":
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "messages" in data:
            data = data["messages"]
        if not isinstance(data, list):
            raise InputError("JSON must be a list of message records or {\"messages\": [...]}")
        return data
    if ext == ".csv":
        with path.open("r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    raise InputError(f"unsupported file extension '{ext}'; expected .json or .csv")


def _latest_stage(record: dict) -> str | None:
    """Return the furthest stage a message reached, or None if unknown.

    Accepts either a single `status`/`stage` field, or a `statuses` list of
    {stage, ...} entries (treated as the lifecycle history; the max-rank stage
    is the latest in funnel-progression sense).
    """
    if "statuses" in record and isinstance(record["statuses"], list):
        ranks = [
            STAGE_RANK[s["stage"].upper()]
            for s in record["statuses"]
            if isinstance(s, dict) and isinstance(s.get("stage"), str) and s["stage"].upper() in STAGE_RANK
        ]
        if not ranks:
            return None
        return STAGES[max(ranks)]
    for key in ("status", "stage", "latest_status"):
        val = record.get(key)
        if isinstance(val, str) and val.upper() in STAGE_RANK:
            return val.upper()
    return None


def compute_funnel(messages: Iterable[dict]) -> dict[str, int]:
    """Return {stage: count_of_messages_that_reached_at_least_this_stage}."""
    counts = {s: 0 for s in STAGES}
    for record in messages:
        latest = _latest_stage(record)
        if latest is None:
            continue
        for stage in STAGES[: STAGE_RANK[latest] + 1]:
            counts[stage] += 1
    return counts


def stage_dropoffs(counts: dict[str, int]) -> list[tuple[str, str, float]]:
    """Return [(from_stage, to_stage, dropoff_pct)] for adjacent stages."""
    out: list[tuple[str, str, float]] = []
    for i in range(len(STAGES) - 1):
        a, b = STAGES[i], STAGES[i + 1]
        if counts[a] == 0:
            pct = 0.0
        else:
            pct = (counts[a] - counts[b]) / counts[a] * 100.0
        out.append((a, b, pct))
    return out


def _print_report(counts: dict[str, int], drops: list[tuple[str, str, float]]) -> None:
    print("Funnel:")
    for stage in STAGES:
        print(f"  {stage:<10} {counts[stage]}")
    print("\nStage drop-off:")
    for a, b, pct in drops:
        print(f"  {a} -> {b}: {pct:.1f}%")


# Sent's documented send-time per-message error codes appear in the message
# `description` field on FAILED rows. See references/mdr-status-codes.md.
_ERR_CODE_RE = re.compile(r"\bERR_[A-Z0-9_]+\b")
_STATUS_KEYS = ("status", "stage", "latest_status")


def _is_failed(record: dict) -> bool:
    # FAILED isn't in STAGES, so _latest_stage() returns None for it. Check
    # the explicit status keys and the statuses history directly.
    for key in _STATUS_KEYS:
        val = record.get(key)
        if isinstance(val, str) and val.upper() == "FAILED":
            return True
    history = record.get("statuses")
    if isinstance(history, list):
        for entry in history:
            if isinstance(entry, dict) and isinstance(entry.get("stage"), str) \
                    and entry["stage"].upper() == "FAILED":
                return True
    return False


def summarise_errors(messages: Iterable[dict]) -> Counter:
    """Return a Counter of ERR_* codes parsed from FAILED messages' descriptions."""
    counter: Counter = Counter()
    for record in messages:
        if not isinstance(record, dict) or not _is_failed(record):
            continue
        description = record.get("description")
        if not isinstance(description, str):
            continue
        # Dedupe within a row so one message with the same code mentioned
        # twice doesn't double-count.
        counter.update(set(_ERR_CODE_RE.findall(description)))
    return counter


def _print_error_summary(counter: Counter) -> None:
    print("\nERR_* codes (from FAILED descriptions):")
    if not counter:
        print("  (none found)")
        return
    for code, count in counter.most_common():
        print(f"  {code:<32} {count}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        messages = _load_messages(Path(args.path))
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not messages:
        print("error: no messages found in input", file=sys.stderr)
        return 2

    counts = compute_funnel(messages)
    drops = stage_dropoffs(counts)
    _print_report(counts, drops)

    if args.show_errors:
        _print_error_summary(summarise_errors(messages))

    anomalies = [(a, b, pct) for a, b, pct in drops if pct > args.threshold]
    if anomalies:
        print(
            f"\nFAIL: {len(anomalies)} stage(s) exceeded the {args.threshold}% drop-off threshold:",
            file=sys.stderr,
        )
        for a, b, pct in anomalies:
            print(f"  {a} -> {b}: {pct:.1f}%", file=sys.stderr)
        return 3
    print(f"\nOK: no stage exceeded the {args.threshold}% drop-off threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
