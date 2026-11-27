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
| Open/monitoring incidents | `list_incidents` | read | service_ids, status, page_size, page_number; recent history may use started_after/started_before; do not exclude an older still-open incident |
| Inspect relevant incident | `get_incident` | read | incident_id |
| Historical symptoms | `search_incidents` | read | query, page_size, page_number, max_results; optional enrichment |
| Resolve affected service | `list_services` | read | Use supported filter and pagination arguments |
| Upcoming handoff | `get_oncall_handoff_summary` | read | schedule_ids or team_ids, timezone; include_incidents only when necessary |
| Recent workload warning | `get_oncall_shift_metrics` | read | start_date, end_date for last 60 minutes by default; user_ids/schedule_ids; do not change the deploy verdict from this result |

Metrics/logs, CI/review/deploy evidence, calendars, and policy are separate
sources. Use them only if connected and authorized; Rootly records are not
substitutes for unavailable telemetry or a missing deployment feed.
