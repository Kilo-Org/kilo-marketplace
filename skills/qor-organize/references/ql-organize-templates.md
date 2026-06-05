# QL Organize Templates and Archetype Definitions

## Workspace Isolation Rules

### Forbidden Paths (NEVER reorganize)

```
FORBIDDEN_PATHS = ['.agent/', '.claude/', '.qorelogic/', '.failsafe/']
```

### FailSafe Dev Repo Detection

If ALL present: `src/Genesis/workflows/*.yml`, `build/transform.ps1`, `targets/`
Then also exclude: `src/`, `qorelogic/`, `build/`, `targets/`, `PROD-Extension/`

### Path Validation

```python
def is_path_safe_to_reorganize(path):
    FORBIDDEN = ['.agent/', '.claude/', '.qorelogic/', '.failsafe/']
    for f in FORBIDDEN:
        if path.startswith(f):
            return False
    if is_failsafe_dev_repo():
        for f in ['src/', 'qorelogic/', 'build/', 'targets/', 'PROD-Extension/']:
            if path.startswith(f):
                return False
    return True
```

## Archetype Classification Table

| Archetype | Indicators | Canonical Structure |
|-----------|-----------|---------------------|
| node-app | Single package.json at root | `src/`, `lib/`, `test/`, `dist/` |
| node-monorepo | Multiple package.json, workspaces | `packages/`, `apps/`, `libs/` |
| python-package | pyproject.toml or setup.py | `src/[pkg]/`, `tests/`, `docs/` |
| python-scripts | .py files, requirements.txt | `scripts/`, `data/`, `output/` |
| rust-crate | Cargo.toml | `src/`, `tests/`, `benches/` |
| rust-workspace | Cargo.toml with [workspace] | `crates/`, `bins/` |
| go-module | go.mod | `cmd/`, `pkg/`, `internal/` |
| dotnet | .sln or .csproj | `src/`, `tests/`, `docs/` |
| data-science | .ipynb files | `notebooks/`, `data/`, `models/` |
| documentation | mkdocs.yml, docusaurus | `docs/`, `static/`, `src/` |
| ai-workspace | .claude/, .cursor/ | `docs/`, `.agent/`, governance dirs |
| mixed | Multiple indicators | Hybrid approach |
| personal | No clear indicators | `Projects/`, `Documents/`, `Archive/` |

## Archetype Detection Indicators

```
Glob: **/package.json    Glob: **/Cargo.toml
Glob: **/go.mod          Glob: **/pyproject.toml
Glob: **/requirements.txt  Glob: **/*.sln
Glob: **/pom.xml         Glob: **/*.ipynb
Glob: **/mkdocs.yml      Glob: **/docusaurus.config.js
```

## Archetype Directory Templates

### node-app
```
project/
├── src/          # Source code
├── test/         # Test files
├── dist/         # Build output (gitignored)
├── docs/         # Documentation
├── package.json
└── README.md
```

### node-monorepo
```
project/
├── packages/     # Shared packages
├── apps/         # Applications
├── docs/         # Documentation
├── package.json  # Root workspace config
└── README.md
```

### python-package
```
project/
├── src/package_name/
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

### data-science
```
project/
├── notebooks/    # Jupyter notebooks
├── data/raw/     # Immutable original data
├── data/processed/
├── models/       # Trained models
├── src/          # Reusable code
├── reports/      # Generated reports
└── requirements.txt
```

### ai-workspace
```
project/
├── docs/         # CONCEPT.md, ARCHITECTURE_PLAN.md, META_LEDGER.md
├── .agent/staging/
├── .claude/      # Claude Code config
├── .qorelogic/   # QoreLogic config
├── src/          # Implementation
└── README.md
```

## Convention Analysis Checks

### node-app
- src/ exists and contains source files
- test/ or __tests__/ or *.test.ts pattern
- dist/ or build/ for output
- No source files in root (except config)

### python-package
- src/[package_name]/ structure
- tests/ directory
- __init__.py files present
- No loose .py files in root

### data-science
- notebooks/ for .ipynb files
- data/ for datasets
- models/ for trained models
- src/ for reusable code

## Organization Proposal Template

```markdown
## Organization Proposal

**Archetype**: [detected]
**Strategy**: [incremental/restructure/minimal]

### Proposed Changes

#### High Priority (Convention Violations)
1. Move `[file]` → `[destination]` — Reason: [convention]

#### Medium Priority (Improvement)
2. Create `[directory]` — Reason: [missing standard]

### Preserved (No Changes)
- `[directory]` - Already well-organized

### Estimated Impact
- Files to move: [count]
- Directories to create: [count]
- Risk level: [low/medium/high]
```

## FILE_INDEX.md Template

```markdown
# File Organization Index

**Generated**: [ISO 8601]
**Archetype**: [detected]

## Summary
| Metric | Count |
|--------|-------|
| Files moved | [n] |
| Directories created | [n] |
| Items preserved | [n] |

## Movement Log
| # | Source | Destination | Reason | Status |
|---|--------|-------------|--------|--------|
| 1 | [path] | [path] | [reason] | ✓ |

## Rollback Instructions
```bash
# Reverse movements
mv "[dest]" "[source]"
```
```

## Privacy Configuration

### Required Patterns (Public Repos)

```gitignore
# AI GOVERNANCE
.agent/
.claude/
.failsafe/
.qorelogic/
CLAUDE.md
GEMINI.md

# Planning documents
plan-*.md
docs/

# IDE local settings
.vscode/
```

### workspace.json Schema

```json
{
  "archetype": "[detected]",
  "detectedAt": "[ISO 8601]",
  "confidence": "[high/medium/low]",
  "lockedBy": "user-approval",
  "privacy": {
    "visibility": "public|private",
    "configuredAt": "[ISO 8601]"
  }
}
```
