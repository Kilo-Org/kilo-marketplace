---
name: meeting-insights-analyzer
description: "Analyzes meeting transcripts to extract behavioral patterns, speaking ratios, filler-word frequency, conflict-avoidance instances, and facilitation quality scores. Produces timestamped examples with improvement suggestions. Use when reviewing meeting recordings, preparing performance reviews, coaching communication skills, or tracking speaking habits over time."
metadata:
  category: communication-writing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: meeting-insights-analyzer
---

# Meeting Insights Analyzer

Parses meeting transcript files (.txt, .md, .vtt, .srt, .docx) from a local folder to surface communication patterns, speaking statistics, and actionable improvement recommendations with timestamped evidence.

## Workflow

### 1. Discover Data

- Scan the target folder for transcript files (.txt, .md, .vtt, .srt, .docx)
- Verify files contain speaker labels and timestamps
- Identify the user's name/identifier and confirm the date range

### 2. Clarify Analysis Goals

If not specified, ask which areas to analyze:

| Area | What to look for |
|------|-----------------|
| Conflict avoidance | Hedging ("maybe", "kind of"), subject changes under tension, indirect requests |
| Speaking ratios | % of meeting speaking, interruptions given/received, turn length |
| Filler words | "um", "uh", "like", "you know" — frequency per minute |
| Active listening | References to others' points, paraphrasing, clarifying questions |
| Facilitation | Decision-making style, inclusion of quiet participants, agenda control |

### 3. Analyze Patterns

For each requested area, scan all transcripts and quantify occurrences. For every pattern found, produce output in this format:

```
### [Pattern Name]
**Finding**: One-sentence summary
**Frequency**: X times across Y meetings

**Example** — [Meeting Name/Date] at [Timestamp]
> [Actual quote from transcript]

**Why it matters**: [Impact explanation]
**Better approach**: [Specific alternative phrasing]
```

Include 2-3 strongest examples per pattern.

### 4. Synthesize Summary

Produce a final report containing:
- **Analysis period** and number of meetings analyzed
- **Key patterns** with observed behavior, impact, and recommendation
- **Communication strengths** (with examples)
- **Growth opportunities** (specific, actionable)
- **Speaking statistics**: average speaking %, questions per meeting, filler words per minute, interruptions given/received
- **Next steps**: 3-5 concrete actions

### 5. Offer Follow-Up

- Track the same metrics in future meetings for trend comparison
- Deep-dive into specific meetings or patterns
- Generate performance-review-ready summaries

## Example

**User**: "Tell me all the times I've subtly avoided conflict."

**Output** (abbreviated):
```
# Conflict Avoidance Patterns
Found 23 instances across 15 meetings.

## Hedging on Critical Feedback (8 times, 7 meetings)

**1:1 with Sarah** — 00:14:32
> "So, I was thinking... maybe we could, like, potentially
> consider looking at the timeline again?"

**Why it matters**: Hedging language made it easy to miss the urgency.
**Better approach**: "Sarah, the project is two weeks behind schedule.
We need to discuss what's blocking progress and create a new timeline today."
```

## Setup Tips

| Source | How to export |
|--------|--------------|
| Zoom | Enable cloud recording with transcription; download VTT/SRT files |
| Google Meet | Use auto-transcription; save as .txt |
| Granola | Export transcripts to a local folder |
| Otter.ai / Fireflies.ai | Bulk-export transcripts to a local folder |

**Best practices**: Name files `YYYY-MM-DD - Meeting Name.txt`. Analyze monthly or quarterly for trends. Keep sensitive data local.
