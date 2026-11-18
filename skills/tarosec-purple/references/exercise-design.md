# Exercise design

## Step definition

Each step needs: stable ID, one ATT&CK technique (ID + name, version stated),
target host, benign procedure, expected telemetry sources, expected detection
rule IDs, and a latency budget in seconds. Optional: D3FEND countermeasures the
step is meant to exercise.

Write the expectation **before** running. An expectation written after seeing
results is a description, not a test.

## Choosing procedures

- Use an inert test marker or prerecorded event with synthetic data.
- Identify the event source, expected firing host, and required evidence before
  the exercise. In v0.1 the classifier matches the reported target host. If a
  collector reports a different host, document the correlation for review.
- One behavior per step, so a missing alert points at one cause.

## Controls for a trustworthy result

| Control | Why |
| --- | --- |
| Sensor heartbeat / source health over the window | Separates telemetry gap from a dead pipeline |
| Known-good positive step (a rule known to fire) | Proves the alert export path works end to end |
| Recorded end time with UTC offset | Makes latency measurable |
| Alert export covering window + latency budget | Late alerts are not misread as gaps |

If a control is missing, results that depend on it are Inconclusive.

## Retest

Keep the original step ID, technique and expectation. Record what changed (rule
version, sensor config). Report both original and new outcomes. If the lab or
required evidence is unavailable, record the retest as Not run.
