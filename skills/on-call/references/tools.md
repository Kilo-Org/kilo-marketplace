# Rootly tool mapping

These are read operations verified against the public Rootly MCP source at
[commit `7140ccb10ce5f231d7f6d62ecc4716e976db72d1`](https://github.com/rootlyhq/rootly-mcp-server/tree/7140ccb10ce5f231d7f6d62ecc4716e976db72d1),
reviewed 2026-11-11.
This is source verification, not a capture of your connected server's tool list.
Discover the current schema and read-only annotations before calling a tool.
If a capability is absent, say so; do not guess aliases or bypass its permissions.

Generated OpenAPI tools can expose different parameter spelling from the HTTP
API. Copy the MCP schema's spelling; do not send bracketed HTTP filters unless
that schema accepts them. Stop on a real auth failure rather than retrying with
broader credentials. Scope and page list operations before expanding them.

| Need | Tool | Access | Inputs and constraints |
|---|---|---|---|
| Resolve current user | `get_current_user` | read | No assumed user identity; inspect live schema |
| Discover schedules | `list_schedules` | read | Use supported filters and pagination; keep returned schedule IDs |
| Schedule coverage | `get_oncall_schedule_summary` | read | start_date, end_date; schedule_ids/team_ids; include_user_ids when needed |
| Handoff context | `get_oncall_handoff_summary` | read | schedule_ids/team_ids, timezone, include_incidents when needed |
| Individual shift records | `get_schedule_shifts` | read | Use exact schedule ID and time argument names from the connected schema; no unfilled path placeholders |
| Cross-schedule shifts | `list_shifts` | read | Use supported user/schedule IDs and time bounds from the connected schema |
| Shift incidents | `get_shift_incidents` | read | start_time, end_time; optional severity/status. schedule_ids and tags are ignored and do not scope results; returned incidents do not by themselves establish schedule or person-level involvement |
| Shift alert records | `list_alerts` | read | Bound to the shift and relevant services/sources using supported filters and pagination; verify person-level involvement rather than assume all routed alerts were touched |
| Alert handling history | `list_alert_events` | read | Use actual alert ID and connected schema; verify outcomes and handling actors when exposed, otherwise disclose attribution gaps |
| Workload | `get_oncall_shift_metrics` | read | start_date, end_date; user_ids/schedule_ids, group_by |
| Scheduled obligations in Rootly | `check_responder_availability` | read | start_date, end_date, user_ids; returns scheduled duties, not external calendar/PTO/access |
| Escalation duties | `list_escalation_policies` | read | Use supported filters/pagination; verify all relevant schedules and roles |
| Resolve escalation policy | `get_escalation_policy` | read | Use the actual policy ID and exact argument name from live schema |
| Follow-ups for known incidents | `list_incident_action_items` | read | Use parent incident ID and exact pagination arguments from the connected schema |

Metrics/logs, CI/review/deploy evidence, calendars, and policy are separate
sources. Use them only if connected and authorized; Rootly records are not
substitutes for unavailable telemetry or a missing deployment feed.
