---
name: changelog-generator
description: "Generates user-facing changelogs and release notes from git commit history by categorizing changes, filtering internal commits, and rewriting technical messages into customer-friendly language. Use when preparing release notes, version summaries, or product update announcements."
metadata:
  category: development
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: changelog-generator
---

## When to Use

- Preparing release notes for a new version or tag
- Writing weekly/monthly product update summaries
- Generating app store update descriptions
- Creating a public changelog or product-updates page
- Drafting email or social media release announcements

## Workflow

1. **Scan** — Analyze git commits for a date range, tag range, or since last release.
2. **Categorize** — Group commits into: Features, Improvements, Bug Fixes, Breaking Changes, Security.
3. **Filter** — Exclude internal-only commits (refactors, CI, tests, docs).
4. **Rewrite** — Transform developer commit messages into clear, customer-facing language.
5. **Format** — Output a structured, publish-ready changelog in Markdown.

## Usage

```
# Basic — since last release
Create a changelog from commits since the last release

# Date range
Create a changelog for commits between March 1 and March 15

# Tag range
Create release notes for commits since v2.4.0

# Custom style
Generate changelog since v2.4.0 using guidelines from CHANGELOG_STYLE.md
```

## Example Output

**Prompt:** "Create a changelog for the past 7 days"

```markdown
# Updates — Week of March 10, 2024

## New Features
- **Team Workspaces** — Create separate workspaces per project with member invitations.
- **Keyboard Shortcuts** — Press `?` to view all shortcuts; navigate without a mouse.

## Improvements
- **Faster Sync** — File sync is now 2x faster across devices.
- **Better Search** — Search now includes file contents, not just titles.

## Fixes
- Fixed large-image upload failures.
- Resolved timezone issues in scheduled posts.
- Corrected notification badge counts.
```

## Tips

- Run from the git repository root so commit history is accessible.
- Provide a `CHANGELOG_STYLE.md` for consistent voice and formatting.
- Review generated output before publishing — adjust tone as needed.
- Pipe output directly to `CHANGELOG.md` for quick updates.
