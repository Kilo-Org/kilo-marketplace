---
name: qor-repo-scaffold
description: >-
  /ql-repo-scaffold - Generate Governance Scaffold
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-repo-scaffold
---

# /ql-repo-scaffold - Generate Governance Scaffold

<skill>
  <trigger>/ql-repo-scaffold</trigger>
  <phase>IMPLEMENT</phase>
  <persona>Specialist</persona>
  <output>Created community files from templates</output>
</skill>

## Purpose

Generate missing repository governance files using the bundled templates in this package, with variable substitution for project-specific values.

## Execution Protocol

### Step 1: Detect Project Context

```bash
# Project name
cat package.json | jq -r '.name' 2>/dev/null || basename $(pwd)

# License type
head -1 LICENSE 2>/dev/null | grep -oE '(MIT|Apache|GPL|BSD|ISC)' || echo "MIT"

# Maintainer email
git config user.email || cat package.json | jq -r '.author.email' 2>/dev/null

# Current year
date +%Y
```

Store as:
- `{{PROJECT_NAME}}`
- `{{LICENSE_TYPE}}`
- `{{MAINTAINER_EMAIL}}`
- `{{YEAR}}`

### Step 2: Run Audit First

```
Execute: /ql-repo-audit (internal)
Capture: List of MISSING files
```

IF no missing files:
- REPORT: "Repository already meets Gold Standard"
- DONE

### Step 3: Generate Missing Files

For each file marked MISSING, load a bundled template when one exists in this package and substitute variables. If no bundled template exists for a missing file, report it as a follow-up item instead of claiming it was generated:

| Missing File | Template |
|--------------|----------|
| CODE_OF_CONDUCT.md | Contributor Covenant |
| CONTRIBUTING.md | Standard guide |
| SECURITY.md | Security policy |
| GOVERNANCE.md | Project governance |
| .github/ISSUE_TEMPLATE/bug_report.yml | `references/Issue templates/bug_report.yml` |

### Step 4: Stage Files

```bash
git add [created files]
```

### Step 5: Report

```markdown
## Scaffold Complete

**Project**: {{PROJECT_NAME}}
**License**: {{LICENSE_TYPE}}

### Files Created

| File | Path | Status |
|------|------|--------|
| [name] | [path] | Created & Staged |

### Next Steps

1. Review staged files: `git status`
2. Customize content as needed
3. Commit: `git commit -m "docs: add community governance files"`
4. Verify: `/ql-repo-audit`
```

## Constraints

- **NEVER** overwrite existing files
- **NEVER** auto-commit (stage only, user owns final review)
- **ALWAYS** run /ql-repo-audit first to identify gaps
- **ALWAYS** use template substitution only for bundled templates that actually exist in this package
- **ALWAYS** make template substitution idempotent

## Success Criteria

Scaffold succeeds when:

- [ ] Project context detected (name, license, email, year)
- [ ] /ql-repo-audit run to identify missing files
- [ ] All missing files with bundled templates generated from templates
- [ ] Template variables substituted correctly
- [ ] Files staged (not committed)
- [ ] Report generated listing created files

## Integration with S.H.I.E.L.D.

This skill implements:

- **Gold Standard Remediation**: Generates files identified by /ql-repo-audit
- **Template-Driven Generation**: Consistent community files across projects
- **Bootstrap Support**: Called silently by /ql-bootstrap for new repositories
- **Specialist Persona**: Precision file generation with variable substitution
