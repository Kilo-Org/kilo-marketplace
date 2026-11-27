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
| Incident and recorded resolution | `get_incident` | read | incident_id |
| Existing human-authored review | `get_incident_retrospective` | read | incident_id; optional and may not be available on older servers |
| Recorded responder accounts | `get_incident_meeting_transcripts` | read | incident_id; optional max_recordings |
| Existing action items | `list_incident_action_items` | read | Use actual parent incident ID and live pagination arguments |
| Historical comparisons | `find_related_incidents` | read | incident_id or incident_description; max_results; optional evidence, not causal proof |

Metrics/logs, CI/review/deploy evidence, calendars, and policy are separate
sources. Use them only if connected and authorized; Rootly records are not
substitutes for unavailable telemetry or a missing deployment feed.
