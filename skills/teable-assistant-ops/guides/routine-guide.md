# Routine Guide

Use routines for headless agent work that can be expressed as a self-contained prompt, triggered by either a schedule or a connected-app event. Use an automation instead when the work needs a deterministic trigger/action graph.

## Safe workflow

1. Write a prompt containing all context each run needs; routines do not see the current conversation.
2. Preview creation with `routine create --dry-run`. For schedules, confirm timezone, bounds, and upcoming occurrences. For connector events, confirm the toolkit, event type, and event parameters.
3. Create as a draft. For a connector event, create without an account, request the connection for the returned routine ID, then update the routine with the returned alias.
4. Use `routine run-now` to preview real behavior, retain its run ID, and poll `routine get-run` until terminal. An inactive connector-event routine waits up to 30 minutes for the next real event, so ask the user to trigger it in the connected app.
5. Read the agent's closing text from the run; inspect the full conversation only when more detail or per-message credit use matters. Fix the prompt or trigger config with `routine update --dry-run`, then save and preview again.
6. Activate only after the user approves both trigger and behavior. Connector-event subscription starts on activation.

## Trigger decisions

- Use `schedule` for RRULE-driven work and `connectorEvent` for one run per event from a connected app.
- For a connector event, discover the toolkit and event type before creating the routine. Bind the account through the credential flow; do not invent or expose an account alias.
- If `routine get` reports a disconnected subscription, reconnect or bind another connection and update the alias before activation.

## Scheduling decisions

- RRULE times are wall-clock values in the specified IANA timezone. Keep timezone separate; do not put `TZID`, `DTSTART`, or `UNTIL` in the RRULE.
- Use `starting` to anchor intervals and one-shot dates; use `ending` for a time boundary and `COUNT` for a bounded number of occurrences.
- Prefer fresh chats for independent runs. Continue the previous chat only when later runs intentionally depend on accumulated conversational state.
- Set the run limit to match expected work. A run exceeding it fails with a timeout rather than continuing indefinitely.

## Lifecycle and recovery

- `routine get` distinguishes saved draft configuration from the published schedule: when `hasDraft` is true, the next run still follows the published configuration.
- Deactivation pauses future scheduling; missed occurrences are not replayed wholesale on reactivation.
- Activation fails when a schedule has no future occurrence, such as an exhausted `COUNT`; update and preview the schedule first.
- `routine run-now` also works for drafts but rejects overlapping in-flight runs. For inactive connector-event routines it listens for one new event instead of synthesizing one.
- Use `routine get-runs` for newest-first history and cursor pagination. A failed run may have executed (`runFail`, `timeout`) or never started (`creditExceed`, `overlap`, `queueTimeout`); distinguish these before retrying.
- Deletion stops scheduling and moves the routine to project trash. Runs and chats remain readable, and restoration returns the routine paused.
