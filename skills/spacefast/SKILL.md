---
name: spacefast
description: >-
  Publish an existing website, app, report, or other artifact to Spacefast and
  verify its live link. Also use to read or manage team Memories and inspect
  team Skills. For changes to an existing Space's content or design, use
  edit-space.
metadata:
  category: development
  source:
    repository: 'https://github.com/spacefast/plugins'
    path: skills/spacefast
    ref: main
    commit: ae351469bf4ce5d72cd8e3de36bd2947ca0924aa
---

# Publish your work

Use the connected Spacefast tools. When working in a checkout, preserve unrelated files and changes.

If a task requires an existing Space and its identity is unclear, call `choose_space`. Use the selected Space as the target. A selection does not approve publishing or other changes.

Read the MCP calls, approval, and work mode rules in [references.md](references.md) before a management operation.

1. For a team Memories or Skills request, resolve the team and optional Space. Read Team Memories and Skills in references.md and perform only the requested context work. Publish only when the user also requests it.
2. Use the artifact the user wants to publish. Keep its intended destination and access settings.
3. Before creating or editing, read **Team Memories and Skills** in [references.md](references.md). Read the full context before preparing changes and apply relevant saved practices within the task.
4. Before publishing or deploying new or changed source, run the verify-design-system skill against current saved standards and the exact source/build being deployed. Inspect affected pages and states at desktop and mobile widths, and report gaps. Reuse verification only while the source/build and design revision are unchanged. Report missing standards as unavailable, not a pass. Verify before a source-workspace commit when autoDeploy is enabled. Follow the user's existing publication intent and approval rules.
5. Read **Publish** in [references.md](references.md). It covers this host's publish route, receipt, and verification.
6. Do not rebuild an existing Space from its served files. For a file or design change, follow the source workflow instead.
7. Return the live link and version link from the result. State whether the version is live or only ready.
8. For a requested preview, redirect, or GitHub workflow, read the matching section in [references.md](references.md).
