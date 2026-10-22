---
name: verify-design-system
description: >-
  Check a Spacefast source build or preview against its saved team design
  system, including visual and editorial results. Report deviations and fix them
  when the task includes corrections.
metadata:
  category: development
  source:
    repository: 'https://github.com/spacefast/plugins'
    path: skills/verify-design-system
    license_path: LICENSE
    ref: main
    commit: ae351469bf4ce5d72cd8e3de36bd2947ca0924aa
---

# Verify design application

Use the connected Spacefast tools. When working in a checkout, preserve unrelated files and changes.

If a task requires an existing Space and its identity is unclear, call `choose_space`. Use the selected Space as the target. A selection does not approve publishing or other changes.

Read the MCP calls, approval, and work mode rules in [references.md](references.md) before a management operation.

1. Resolve the team and Space, then identify the exact complete source revision and matching built preview or version. Read Design system and Source edits in references.md.
2. Read Team Memories and Skills in references.md. Retrieve current standards, applicable memories, enabled team skills, and assets. Identify a stale `design.md` or preview before judging compliance; do not treat a missing standard as a pass.
3. Inspect affected pages, components, states, assets, and copy at representative desktop and mobile widths. Tie each finding to the saved rule, implementation location, and rendered evidence.
4. For a request that includes corrections, change authorized source, rebuild, and repeat affected visual checks. For review-only work, report findings without editing.
5. Report versions, areas checked, fixes and retests, unresolved gaps, and decisions. Verification does not authorize publication.
