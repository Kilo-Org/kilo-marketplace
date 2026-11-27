# Worked example: handoff and provisional cover

Synthetic fixture for the 08:00–16:00 UTC shift.

## Available evidence

- A1: Complete shift activity identifies AL-1 (resolved), AL-2 (duplicate/noisy),
  and INC-7 (monitoring, awaiting an error-rate check).
- F1: Follow-up proposes tuning AL-2. It has not been accepted or assigned.
- E1: Maintenance is scheduled at 17:00; a database deploy is planned at 16:30.
- S1: The primary schedule hands off from responder A to responder B at 16:00.
- S2: Responder B also covers another schedule until 17:30.
- W1: Two priority-1 pages this shift; overnight paging history is unavailable.
- C1: External calendar, PTO, and service-access information are unavailable.

## Example handoff

The primary schedule lists A → B at 16:00 UTC (S1). AL-1 resolved; AL-2 was
noise; INC-7 remains in monitoring with its next check outstanding (A1). The
AL-2 tuning proposal needs roadmap-owner review (F1).

Upcoming work: database deploy at 16:30 and maintenance at 17:00 (E1). Ask the
incoming responder to acknowledge INC-7 and confirm coverage for these events.

Coverage is provisional: B has another schedule until 17:30 (S2). W1 records
two priority-1 pages but does not establish fatigue or overnight load. Calendar,
PTO, and required service access have not been checked (C1). No swap was applied.

## Counterexample

A candidate with no overlapping shifts but missing service access is not a
verified replacement. Availability and qualification are separate checks.
