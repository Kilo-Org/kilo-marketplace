---
name: skill-share
description: "Scaffolds new agent skills with SKILL.md, validates structure, packages as zip, and posts announcements to Slack via Rube. Use when creating, packaging, or sharing agent skills with a team."
license: Complete terms in LICENSE.txt
metadata:
  category: development
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: skill-share
---

## Workflow

### 1. Scaffold

Create the skill directory and SKILL.md from a name and description:

```bash
SKILL_NAME="pdf-analyzer"
SKILL_DIR="skill-${SKILL_NAME}"

mkdir -p "${SKILL_DIR}"/{scripts,references,assets}

cat > "${SKILL_DIR}/SKILL.md" << 'TEMPLATE'
---
name: pdf-analyzer
description: "Analyzes PDF documents and extracts structured content. Use when parsing, summarizing, or extracting data from PDF files."
metadata:
  category: development
---

# PDF Analyzer

[Skill instructions here]
TEMPLATE
```

Required frontmatter fields for a valid SKILL.md:
- `name` — kebab-case identifier (must match directory name)
- `description` — quoted string with "Use when..." clause
- `metadata.category` — one of: development, business-marketing, communication-writing, creative-media

### 2. Validate

Check the skill passes structural validation before packaging:

```bash
# Verify required files exist
test -f "${SKILL_DIR}/SKILL.md" || echo "ERROR: Missing SKILL.md"

# Verify frontmatter has required fields
head -20 "${SKILL_DIR}/SKILL.md" | grep -q "^name:" || echo "ERROR: Missing name field"
head -20 "${SKILL_DIR}/SKILL.md" | grep -q "^description:" || echo "ERROR: Missing description field"

# Verify name is kebab-case
echo "${SKILL_NAME}" | grep -qE '^[a-z][a-z0-9]*(-[a-z0-9]+)*$' || echo "ERROR: Name must be kebab-case"
```

**Common validation failures:**
- Name contains uppercase or underscores — convert to kebab-case
- Description uses `>` (chevron) instead of quoted string — wrap in double quotes
- Missing `metadata` block — add category at minimum

### 3. Package

Bundle the validated skill into a distributable zip:

```bash
# Run validation first, then package
cd "${SKILL_DIR}" && zip -r "../${SKILL_NAME}.zip" . -x "*.DS_Store" "*.git*"
echo "Packaged: ${SKILL_NAME}.zip ($(du -h "../${SKILL_NAME}.zip" | cut -f1))"
```

### 4. Share on Slack (via Rube)

Post an announcement to the team channel:

| Rube Action | Purpose | When to Use |
|---|---|---|
| `SLACK_SEND_MESSAGE` | Post skill name + description to a channel | Simple announcements |
| `SLACK_POST_MESSAGE_WITH_BLOCKS` | Share rich-formatted metadata with sections | Detailed skill launches |
| `SLACK_FIND_CHANNELS` | Discover available channels by name | Finding the right target channel |

## Example

**Prompt:** "Create and share a new skill called pdf-analyzer"

```
1. Scaffolded skill-pdf-analyzer/
   ├── SKILL.md (frontmatter + body template)
   ├── scripts/
   ├── references/
   └── assets/
2. Validation passed (name ✓, description ✓, metadata ✓)
3. Packaged as pdf-analyzer.zip (2.1 KB)
4. Posted to #skills via SLACK_SEND_MESSAGE:
   "New Skill: pdf-analyzer — Analyzes PDF documents and extracts structured content"
```

## Requirements

- Slack workspace connected via Rube
- Write access to the skill creation directory
- Python 3.7+
