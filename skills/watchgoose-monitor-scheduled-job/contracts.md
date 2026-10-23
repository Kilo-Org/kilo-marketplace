# Tool contracts and evidence

Verify against the connected tool's actual schema. These examples describe the Watchgoose MCP
contracts, not proof a call ran. Every call is scoped to the selected project.

| Operation                      | Contract                                                                                                                                                                                                                           |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `list_checks`                  | Only `slug`, `tags`, `limit` (1–100). Without a known slug/tag, use `{"limit":100}`. No name filter or pagination. Meta counts this response, not the whole account/project.                                                       |
| `get_check` / `update_check`   | Use the stable lowercase 40-character `unique_key` returned by tools, never a slug, UUID or ping URL.                                                                                                                              |
| `create_check` with `unique`   | Matching check is updated in place. Supplied settings change; a timeout-only payload also selects interval monitoring. Creation authorization is not authorization for this update.                                                |
| `channels: []`                 | Removes all integration assignments. Omit it to preserve assignments on update. On plain NEW creation, omitted `channels` means no integrations, not all. Exact integration names require confirmation; do not invent them.        |
| `schedule`, `timeout`, `grace` | `schedule` is a string expression, **never an object**. `timeout` and `grace` are top-level integer seconds (minimum 60). Schedule takes precedence over timeout. No `schedule_type`, `interval_unit`, or `interval_value` fields. |

## Valid creation input examples

An interval monitor:

```json
{ "name": "Export", "slug": "export-hourly", "timeout": 3600, "grace": 600 }
```

A scheduled monitor, once the user confirms schedule/timezone:

```json
{ "name": "Nightly backup", "schedule": "0 2 * * *", "tz": "Europe/Riga", "grace": 600 }
```

Both examples omit integration assignment; disclose pending routing. Do not send either unless the
exact creation was authorized. Do not add `unique` merely to avoid duplicates. Names alone are not
proof of an existing check's identity.

FreeBSD cron supports `@every_second`; that does not make it a supported Watchgoose schedule. Do not
declare the original scheduler syntax invalid or silently turn it into seconds-cron. Clarify an
appropriate monitoring strategy and the missing timezone/grace instead.

## What the evidence does NOT prove

- A timed-out write plus a missing read-only match **does not establish failure**. It remains
  uncertain; report that and seek the user's decision before any subsequent write.
- An omitted `channels` response field does not reveal which fields the original request sent. With
  only a creation response, report **routing unknown**; do not claim no integrations.
- `timeout` without `schedule` switches an existing scheduled check to interval monitoring. The
  stored schedule string stays, but no longer governs cadence. To retain cron/OnCalendar monitoring,
  include the confirmed `schedule` in the authorized update; do not infer or silently change it. A
  grace-only update does not select a new kind. Explain these derived effects in the proposed diff.
- Successful creation is not instrumentation, a real job run, successful heartbeat reception, or
  notification delivery. Stored `new` awaits completion cadence; a processed start can trigger down
  at start-plus-grace before completion. A first failure heartbeat may also mark down.
