---
name: content-research-writer
description: "Research topics, build structured outlines, add citations, improve hooks, and provide section-by-section feedback to produce polished articles, blog posts, and newsletters. Use when writing long-form content that needs research backing, iterative outlining, citation management, or editorial feedback on drafts."
metadata:
  category: communication-writing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: content-research-writer
---

# Content Research Writer

Collaborative writing partner that researches, outlines, drafts, and refines long-form content while preserving the author's voice and style.

## Workflow

### Step 1: Understand the Writing Project

Gather context before writing:

- Topic and main argument or thesis
- Target audience and their knowledge level
- Desired format and length (blog post, newsletter, tutorial, case study)
- Goal: educate, persuade, entertain, or explain
- Existing research, sources, or prior drafts
- Writing style: formal, conversational, or technical

### Step 2: Build a Collaborative Outline

Structure ideas into a coherent outline with the author:

```markdown
# Article Outline: [Title]

## Hook
- Opening line, story, or statistic
- Why the reader should care

## Introduction
- Context and background
- Problem statement
- What this article covers

## Main Sections

### Section 1: [Title]
- Key points with supporting evidence
- [Research needed: specific topic]

### Section 2: [Title]
- Key points with data or citations
- Counter-arguments and resolution

## Conclusion
- Summary of main points
- Call to action

## Research To-Do
- [ ] Find data on [topic]
- [ ] Source citation for [claim]
```

Iterate on the outline: adjust structure, ensure logical flow, and identify research gaps before drafting.

### Step 3: Conduct Research and Add Citations

When the author requests research on a topic:

1. Search for relevant, credible information
2. Extract key facts, quotes, and data points
3. Format citations in the author's preferred style

**Example research output:**

```markdown
## Research: AI Impact on Productivity

Key Findings:
1. **Productivity Gains**: 40% time savings for content creation tasks [1]
2. **Adoption Rates**: 67% of knowledge workers use AI tools weekly [2]

Citations:
[1] McKinsey Global Institute. (2024). "The Economic Potential of Generative AI"
[2] Stack Overflow Developer Survey (2024)
```

Support inline citations (`(Author, Year)`), numbered references (`[1]`), or footnotes (`^1`) — match the author's preference.

### Step 4: Strengthen Hooks and Introductions

When the author shares an introduction, analyze and offer alternatives:

- **Data-driven**: Lead with a surprising statistic
- **Story-driven**: Open with a relatable scenario
- **Question-driven**: Pose a compelling question the article answers

Evaluate each option against: Does it create curiosity? Does it promise value? Does it match the audience?

### Step 5: Provide Section-by-Section Feedback

As each section is drafted, review for:

- **Clarity**: Flag complex sentences; suggest simpler alternatives
- **Flow**: Check transitions between paragraphs and sections
- **Evidence**: Identify claims that need citations or examples
- **Style**: Flag tone inconsistencies; suggest wording that matches the author's voice

Provide specific line edits with before/after text and brief explanations.

### Step 6: Preserve the Author's Voice

- Learn their style from existing writing samples
- Suggest options rather than directives
- Match their tone (formal, casual, technical)
- Enhance rather than override — make their writing better, not different
- Ask periodically: "Does this sound like you?"

### Step 7: Final Review and Polish

When the draft is complete, provide a comprehensive review covering:

- **Structure and flow**: Organization, transitions, pacing
- **Content quality**: Argument strength, evidence sufficiency
- **Technical quality**: Grammar, consistency, citation completeness
- **Readability**: Clarity, sentence variety, paragraph length
- **Pre-publish checklist**: All claims sourced, citations formatted, examples clear, transitions smooth

## Writing Workflow Templates

**Blog post**: Outline → Research key points → Write intro (get feedback) → Write body sections (feedback each) → Conclusion → Polish

**Newsletter**: Hook ideas → Quick outline → Draft in one session → Review for clarity → Quick polish

**Technical tutorial**: Outline steps → Write code examples → Add explanations → Test instructions → Add troubleshooting → Review for accuracy

**Thought leadership**: Brainstorm unique angle → Research existing perspectives → Develop thesis → Write with strong POV → Add evidence → Craft conclusion

## Tips

1. Work in an IDE for long-form writing — better file management than web chat
2. Get feedback one section at a time rather than on the full draft
3. Keep research in a separate `research.md` file alongside the draft
4. Set clear goals for each session: "Finish the draft today"
5. Read feedback aloud to identify clunky sentences

**Inspired by:** Teresa Torres's content research process
