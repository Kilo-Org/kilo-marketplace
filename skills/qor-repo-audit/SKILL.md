---
name: qor-repo-audit
description: >-
  /ql-repo-audit - Repository Governance Audit
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-repo-audit
---

# /ql-repo-audit - Repository Governance Audit

<skill>
  <trigger>/ql-repo-audit</trigger>
  <phase>AUDIT</phase>
  <persona>Judge</persona>
  <output>Gap report with compliance score and GitHub API metrics</output>
</skill>

## Purpose

Audit repository against GitHub Gold Standard. Integrates with GitHub API for community profile score when available.

## Execution Protocol

### Step 1: Local File Inventory

Check for presence and placement:

**Community Files** (7 required):
```
Glob: README.md          -> has_readme
Glob: LICENSE            -> has_license
Glob: CODE_OF_CONDUCT.md -> has_coc
Glob: CONTRIBUTING.md    -> has_contributing
Glob: SECURITY.md        -> has_security
Glob: GOVERNANCE.md      -> has_governance
Glob: CHANGELOG.md       -> has_changelog
```

**GitHub Templates** (5 required):
```
Glob: .github/ISSUE_TEMPLATE/bug_report.yml    -> has_bug_template
Glob: .github/ISSUE_TEMPLATE/feature_request.yml -> has_feature_template
Glob: .github/ISSUE_TEMPLATE/documentation.yml -> has_docs_template
Glob: .github/ISSUE_TEMPLATE/config.yml        -> has_template_config
Glob: .github/PULL_REQUEST_TEMPLATE.md         -> has_pr_template
```

**README Contract** (if README exists):
```
Read: README.md (limit: 100)
Check: Contains link to CONTRIBUTING.md
Check: Contains link to SECURITY.md
Check: Contains link to Roadmap or CHANGELOG.md
```

### Step 2: GitHub API Check (Optional)

```bash
gh api repos/{owner}/{repo}/community/profile --jq '.'
```

IF command succeeds:
- Extract `health_percentage` (target: 100%)
- Extract `files` object (what GitHub detects)

IF command fails:
- REPORT: "GitHub API unavailable - using local checks only"
- CONTINUE with local results

### Step 3: Calculate Scores

```
local_score = (present_files / 12) * 100
github_score = health_percentage (if available)
```

### Step 4: Generate Gap Report

```markdown
## Repository Gold Standard Audit

**Repository**: [detected from git remote or folder name]
**Audit Date**: [timestamp]

### Scores

| Source | Score | Target |
|--------|-------|--------|
| Local Files | [X]/12 ([Y]%) | 100% |
| GitHub API | [Z]% | 100% |

### Community Files

| File | Required | Present | Status |
|------|----------|---------|--------|
| README.md | Yes | [check] | [PASS/FAIL] |
...

### Missing Items (Priority Order)

1. [HIGH] [file] - [reason]
2. [MEDIUM] [file] - [reason]

### Remediation

Run `/ql-repo-scaffold` to auto-generate missing files.
```

## Constraints

- **NEVER** modify any repository files during audit
- **NEVER** fail if GitHub API is unavailable (use local fallback)
- **ALWAYS** report specific missing files with remediation path
- **ALWAYS** calculate both local and API scores when available

## Success Criteria

Repo audit succeeds when:

- [ ] All 12 community/template files checked for presence
- [ ] README contract verified (links to CONTRIBUTING, SECURITY)
- [ ] Scores calculated (local + GitHub API if available)
- [ ] Gap report generated with priority-ordered missing items
- [ ] Remediation path provided (points to /ql-repo-scaffold)

## Integration with S.H.I.E.L.D.

This skill implements:

- **Gold Standard Enforcement**: Verifies repository meets community governance baseline
- **Pre-Scaffold Gate**: Identifies what /ql-repo-scaffold needs to generate
- **Audit Pass 7**: Referenced by /ql-audit for repository-level compliance
- **GitHub API Integration**: Optional remote health check via `gh` CLI
