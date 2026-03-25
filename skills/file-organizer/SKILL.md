---
name: file-organizer
description: "Analyzes directory structures, finds duplicate files by content hash, proposes logical folder hierarchies, and automates file cleanup with confirmation-based safety. Use when organizing messy downloads folders, finding and removing duplicates, restructuring project directories, reclaiming disk space, or establishing consistent file naming conventions."
metadata:
  category: productivity-organization
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: file-organizer
---

# File Organizer

Analyzes directory structures, identifies duplicates by content hash, proposes better folder hierarchies, and automates cleanup with confirmation-based safety guards.

## Workflow

### Step 1: Understand the Scope

Gather context before making changes:

- Which directory needs organization (Downloads, Documents, entire home folder)
- Main problem: can't find things, duplicates, no structure, general mess
- Files or folders to avoid (active projects, sensitive data)
- Aggressiveness level: conservative tidy-up vs. comprehensive restructure

### Step 2: Analyze Current State

Review the target directory:

```bash
# Overview of current structure
ls -la [target_directory]

# File type breakdown
find [target_directory] -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# Largest files and folders
du -sh [target_directory]/* | sort -rh | head -20
```

Summarize: total files/folders, file type distribution, size breakdown, date ranges, and obvious issues.

### Step 3: Identify Organization Patterns

Determine logical groupings based on the content:

**By type**: Documents (PDF, DOCX), Images (JPG, PNG), Videos (MP4, MOV), Archives (ZIP, DMG), Code/Projects, Spreadsheets, Presentations

**By purpose**: Work vs. Personal, Active vs. Archive, Project-specific, Reference materials, Temporary/scratch

**By date**: Current year/month, previous years, very old (archive candidates)

### Step 4: Find Duplicates

When requested, search for exact and near-duplicates:

```bash
# Find exact duplicates by content hash
find [directory] -type f -exec md5 {} \; | sort | uniq -d

# Find files with identical names
find [directory] -type f -printf '%f\n' | sort | uniq -d
```

For each duplicate set: show all file paths, sizes, and modification dates. Recommend which to keep (usually newest or best-named). **Always ask for confirmation before deleting.**

### Step 5: Propose an Organization Plan

Present a clear plan before making any changes:

```markdown
# Organization Plan for [Directory]

## Current State
- X files across Y folders, [Size] total

## Proposed Structure
[Directory]/
├── Work/
│   ├── Projects/
│   ├── Documents/
│   └── Archive/
├── Personal/
│   ├── Photos/
│   └── Documents/
└── Downloads/
    └── To-Sort/

## Changes
1. Create new folders: [list]
2. Move files: X PDFs → Work/Documents/, Y images → Personal/Photos/
3. Rename: [patterns]
4. Delete: [duplicates or trash]

## Files Needing Your Decision
- [ambiguous files listed here]
```

### Step 6: Execute Organization

After approval, organize systematically:

```bash
mkdir -p "path/to/new/folders"
mv "old/path/file.pdf" "new/path/file.pdf"
```

**Rules**: Always confirm before deleting. Log all moves for potential undo. Preserve original modification dates. Handle filename conflicts gracefully. Stop and ask on unexpected situations.

### Step 7: Summarize and Provide Maintenance Tips

After organizing, report what changed (folders created, files moved, space freed) and suggest a maintenance cadence:

- **Weekly**: Sort new downloads
- **Monthly**: Review and archive completed projects
- **Quarterly**: Check for new duplicates
- **Yearly**: Archive old files

## Examples

### Example 1: Organizing Downloads

**Prompt**: "My Downloads folder is a mess with 500+ files. Help me organize it."

**Process**: Analyzes Downloads, identifies patterns (work docs, personal photos, installers, random PDFs), proposes structure (Work/, Personal/, Installers/, Archive/, ToSort/), gets confirmation, moves files intelligently. Result: 500 files → 5 organized folders.

### Example 2: Finding and Removing Duplicates

**Prompt**: "Find duplicate files in my Documents and help me decide which to keep."

**Output**: Finds 23 sets of duplicates (156 MB total). For each set, shows all paths, sizes, and dates. Recommends which to keep based on recency and location. Asks confirmation before each deletion.

### Example 3: Restructuring a Projects Folder

**Prompt**: "Review my ~/Projects directory and suggest improvements."

**Output**: Identifies issues (mix of active and archived, inconsistent naming, duplicate folders). Proposes Active/Archive/Templates structure. Moves 12 untouched projects to Archive, consolidates 4 duplicates, applies consistent naming convention.

**Inspired by:** Justin Dielmann's workflow

## Tips

1. **Start small**: Begin with one messy folder to build trust
2. **Consistent naming**: Use "YYYY-MM-DD - Description" for important files
3. **Archive over delete**: Move old projects to Archive instead of removing
4. **Avoid spaces in names**: Use hyphens or underscores
5. **Be descriptive**: "client-proposals" not "docs"
