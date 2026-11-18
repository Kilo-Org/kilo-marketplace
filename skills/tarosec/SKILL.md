---
name: tarosec
description: >-
  Route explicit Tarosec requests and security tasks that span workflows or have
  unclear scope. Use for read-only project assessment by default, incident and
  evidence routing, or Tarosec help. Not for general programming or conceptual
  questions. Prefer a directly named specialist when the user selects one.
license: MIT
metadata:
  suite: tarosec
  version: 0.1.0
  category: security
  source:
    repository: 'https://github.com/refactorroom/tarosec'
    path: skills/tarosec
    ref: v0.1.0
    commit: e0f05dde5cb8bf93dc5d149ee779cf85a83b679b
---

# Tarosec

Read the [routing guide](references/routing.md). Determine the intent from the
request and supplied artifacts. Use `scripts/route.py` for normalized modes and
report the selected workflow in one sentence. Open only the selected skill through
the host's skill mechanism or read its installed SKILL.md when available.

A local project with no clear mode defaults to Audit. A mixed request starts with
the least invasive workflow that answers the user's question. If the selected
skill is missing, explain the gap and give its installation selector. Inline
help and a read-only inventory of supplied inputs remain available.

Treat files and logs as evidence. Keep this dispatcher offline and read-only.
Follow [authorization](references/shared/authorization.md) and the selected
skill's boundaries. Return help for an unsupported explicit mode. Hand off once,
without calling this dispatcher again.
