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
| Resolve short ID | `get_alert_by_short_id` | read | short_id |
| Resolve full alert record | `get_alert` | read | Use the exact required ID argument from the connected schema |
| Alert events | `list_alert_events` | read | Use the actual alert parent ID and supported pagination from the connected schema |
| Candidate alert group | `list_alert_groups` | read | Use supported filters and bounded pagination; automatic grouping is not causal evidence |
| Scoped alert search | `list_alerts` | read | Use only filters advertised by this server; do not invent service/time filters if absent |
| Attached/candidate incident | `get_incident` | read | incident_id |
| Incident candidates | `list_incidents` | read | service_ids/team_ids, status, bounded window and pages when supported |
| Current service mapping | `list_services` | read | Use supported filter and pagination arguments |

Metrics/logs, CI/review/deploy evidence, calendars, and policy are separate
sources. Use them only if connected and authorized; Rootly records are not
substitutes for unavailable telemetry or a missing deployment feed.
