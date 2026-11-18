# Simulation contract

Replay reads `scenario.json` and `events.json` in a caller-selected directory.
With `--ndjson`, provide `events.ndjson` with one event object per line.
Normalize raw evidence before replay. Events have a catalog type and a
nonnegative `offsetSeconds` relative to 2026-01-01 UTC. The runner sorts records,
rejects unknown fields and limits each input to 256 KiB, 1,000 records and a
24-hour logical window.

Use `--alerts` to explicitly supply `alerts.json` in the same directory.
Provide `schemaVersion: tarosec.simulation-alerts/v1`, the canonical event
digest in `eventsSha256`, the flag `windowComplete`, and the `alerts` array.
Each row specifies `rule`, `status` (`fired` or `not_fired`), and an
`offsetSeconds` for firing only. Run a replay without alerts to get the
canonical event digest. Obtain observations independently of the expectations.

| Outcome | Evidence needed |
| --- | --- |
| detected | Every expected event type and a bound firing for each expected rule |
| partially_detected | A bound firing with another rule or event type unresolved |
| not_detected | All expected telemetry plus explicit non-firings for every expected rule in a complete window |
| inconclusive | Missing or insufficient observations |
| not_executed | Input, execution, or output failure |

Reports contain normalized events, optional observations, an exercise for
Purple, a Markdown report and a machine-readable result with evidence hashes.
Equivalent inputs in the same mode produce the same result and run ID.
Choose a new output directory for each run. Fixture findings describe
the evaluation pipeline.
