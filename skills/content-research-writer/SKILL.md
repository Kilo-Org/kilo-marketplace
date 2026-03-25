---
name: content-research-writer
description: "Researches topics, builds structured outlines, adds inline citations, strengthens hooks and introductions, and provides section-by-section editorial feedback to produce polished articles, blog posts, newsletters, and tutorials. Use when writing long-form content that needs research backing, iterative outlining, citation management, voice-preserving editorial feedback, or collaborative drafting workflows."
metadata:
  category: communication-writing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: content-research-writer
---

## Workflow

### Step 1: Understand the Writing Project

Ask the author for: topic/thesis, target audience, format (blog post, newsletter, tutorial, case study), and any existing research or prior drafts. If source files are available, read them directly:

```bash
# Read existing drafts and research in the working directory
ls *.md drafts/ research/ 2>/dev/null
# Read style samples to learn the author's voice
cat previous-post.md | head -50
```

### Step 2: Build a Collaborative Outline

Structure the article in a separate outline file for iterative refinement:

```bash
cat > outline.md << 'EOF'
# [Title]

## Hook
- [Opening: statistic, story, or question] — [Research needed: Y/N]

## Introduction
- Context: [1-2 sentences]
- Problem: [What gap this article fills]
- Promise: [What the reader will learn]

## Section 1: [Title]
- Key point + evidence: [source needed]
- Key point + evidence: [source needed]

## Section 2: [Title]
- Key point + data: [source needed]
- Counter-argument + resolution

## Conclusion
- Summary + call to action
EOF
```

Iterate on the outline with the author before drafting. Flag `[Research needed]` items for Step 3.

### Step 3: Research and Add Citations

For each research gap, use web search with targeted queries and store findings in a companion file:

```bash
cat > research.md << 'EOF'
## Research: [Topic]

### Finding 1: [Claim]
- Source: [Author]. ([Year]). "[Title]". [Publication]. [URL]
- Key data: [specific statistic or quote]

### Finding 2: [Claim]
- Source: [Author]. ([Year]). "[Title]". [Publication]. [URL]
- Key data: [specific statistic or quote]
EOF
```

Insert citations inline using the author's preferred format — `(Author, Year)`, `[1]`, or `^1`. Keep the `research.md` as a reference alongside the draft.

### Step 4: Strengthen Hooks and Introductions

When the author shares an introduction, offer three alternative openings:

1. **Data-driven**: Lead with a surprising statistic from research
2. **Story-driven**: Open with a relatable scenario
3. **Question-driven**: Pose the question the article answers

Evaluate each: Does it create curiosity? Does it promise value? Does it match the audience?

### Step 5: Section-by-Section Editorial Feedback

Review each section as it is drafted. Provide specific before/after edits:

```markdown
**Line 23** (Clarity):
- Before: "The implementation of this methodology facilitates enhanced outcomes"
- After: "This approach gets better results"
- Why: Active voice, fewer words, same meaning

**Line 31** (Evidence):
- "AI adoption grew 3x" — needs citation. Check research.md or search for source.

**Line 45** (Flow):
- Missing transition from Section 2 to Section 3. Suggest: "Beyond [topic A], [topic B] adds another dimension..."
```

### Step 6: Final Polish

Run a pre-publish checklist on the completed draft:

- All claims have citations (grep for unsourced assertions)
- Tone is consistent throughout (compare first and last sections)
- Transitions connect every section pair
- No orphaned `[Research needed]` or `[TODO]` markers remain
- Word count matches target format (blog: 1000-2000, newsletter: 500-800, tutorial: 1500-3000)

Preserve the author's voice throughout: learn style from existing samples, suggest options rather than rewrite, match their tone.

## Format-Specific Workflows

| Format | Sequence |
|--------|----------|
| **Blog post** | Outline > Research > Intro (feedback) > Body sections (feedback each) > Conclusion > Polish |
| **Newsletter** | Hook ideas > Quick outline > Single-session draft > Clarity review > Polish |
| **Tutorial** | Outline steps > Write code examples > Add explanations > Test instructions > Add troubleshooting |
| **Thought leadership** | Unique angle > Research existing takes > Develop thesis > Write with strong POV > Add evidence |

**Inspired by:** Teresa Torres's content research process
