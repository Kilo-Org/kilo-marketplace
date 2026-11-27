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
| Resolve incident | `get_incident` | read | incident_id; current source accepts UUID, number, #number, or INC-number |
| Bounded discovery | `list_incidents` | read | query, service_ids/team_ids, started_after/started_before, status, page_size, page_number; use supported filters only |
| Historical text search | `search_incidents` | read | query, page_size, page_number, max_results |
| Compare historical matches | `find_related_incidents` | read | incident_id or incident_description; max_results 3–5; score is similarity, not causal confidence |
| Prior mitigations | `suggest_solutions` | read | incident_id or incident_title/incident_description; max_solutions; treat as unverified options |
| Recorded accounts | `get_incident_meeting_transcripts` | read | incident_id; optional max_recordings; speaker accounts are not telemetry |
| Service/owner lookup | `list_services` | read | Discover exact filter and pagination arguments from the connected schema |
| Team lookup | `list_teams` | read | Discover exact filter and pagination arguments from the connected schema |
| Service on-call | `get_oncall_handoff_summary` | read | team_ids or schedule_ids, timezone; do not enable business-hour region filtering to infer availability |
| Workload context | `get_oncall_shift_metrics` | read | start_date, end_date; scope user_ids/schedule_ids; group_by when supported |
| Schedule obligations | `check_responder_availability` | read | start_date, end_date, user_ids (numeric IDs as a comma-separated string); schedule coverage only |

Metrics/logs, CI/review/deploy evidence, calendars, and policy are separate
sources. Use them only if connected and authorized; Rootly records are not
substitutes for unavailable telemetry or a missing deployment feed.
