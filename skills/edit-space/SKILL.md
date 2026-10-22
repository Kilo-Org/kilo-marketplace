---
name: edit-space
description: >-
  Change the content, design, or source files of an existing Spacefast Space and
  apply visual review notes. Use for page text, styles, layout, or file edits.
  Do not use for unrelated local editing.
metadata:
  category: development
  source:
    repository: 'https://github.com/spacefast/plugins'
    path: skills/edit-space
    license_path: LICENSE
    ref: main
    commit: ae351469bf4ce5d72cd8e3de36bd2947ca0924aa
---

# Update your site

Use the connected Spacefast tools. When working in a checkout, preserve unrelated files and changes.

If a task requires an existing Space and its identity is unclear, call `choose_space`. Use the selected Space as the target. A selection does not approve publishing or other changes.

Read the MCP calls, approval, and work mode rules in [references.md](references.md) before a management operation.

1. Resolve the intended Space. A request to update the visible site includes deployment intent; a source-only edit does not.
2. Before creating or editing, read **Team Memories and Skills** in [references.md](references.md). Read the full context before preparing changes and apply relevant saved practices within the task.
3. Before publishing or deploying new or changed source, run the verify-design-system skill against current saved standards and the exact source/build being deployed. Inspect affected pages and states at desktop and mobile widths, and report gaps. Reuse verification only while the source/build and design revision are unchanged. Report missing standards as unavailable, not a pass. Verify before a source-workspace commit when autoDeploy is enabled. Follow the user's existing publication intent and approval rules.
4. Read **Source edits** in [references.md](references.md) before changing files. Read the work mode and exact source revision.
5. Read complete source files. Preserve unrelated changes. Do not use served deployment files as editable source.
6. When design standards are present, read **Design system** in [references.md](references.md) and verify affected components before deployment.
7. For visual notes, read **Visual review** in [references.md](references.md). Keep each note tied to its reviewed version.
8. For saved comment threads and screenshots, read **Comments** in [references.md](references.md).
9. For a requested CMS or admin panel, read **Content dashboard** in [references.md](references.md) before building anything.
10. Save the intended source changes, then follow the Space's build and promotion flow. Report saved source and live deployment separately.
