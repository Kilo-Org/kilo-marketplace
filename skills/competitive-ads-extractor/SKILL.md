---
name: competitive-ads-extractor
description: "Extracts competitor ads from Facebook Ad Library, LinkedIn, TikTok, and Google Ads Transparency Center, then analyzes messaging patterns, creative formats, audience targeting, and copy formulas to produce actionable campaign insights. Use when researching competitor ad strategies, planning paid media campaigns, auditing creative approaches, benchmarking ad copy, or mapping competitive positioning through paid channels."
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: competitive-ads-extractor
---

# Competitive Ads Extractor

Extracts competitor ads from public ad transparency libraries and analyzes what's working — the problems they highlight, use cases they target, and copy/creative patterns that resonate — to produce actionable campaign insights.

## Workflow

### Step 1: Gather Requirements

Collect targeting parameters before extraction:

- **Competitors**: Specific companies or a competitive set to analyze
- **Platforms**: Facebook Ad Library, LinkedIn Ad Library, TikTok Creative Center, Google Ads Transparency
- **Focus**: Messaging, creative formats, audience targeting, or full audit
- **Time window**: Current ads only, or quarterly trend analysis

### Step 2: Extract Ads

Navigate to the relevant ad library (e.g., `https://www.facebook.com/ads/library/`) and search by company name or page. For each active ad, capture:

- Screenshot of the ad creative (save to `competitor-ads/[company-name]/`)
- Headline, body copy, and CTA button text
- Format: static image, video, or carousel
- Visible targeting or placement info

If no ads are found, verify spelling and check alternative platforms — some companies concentrate spend on a single channel.

### Step 3: Analyze Patterns

Categorize extracted ads across four dimensions:

| Dimension | What to look for |
|-----------|-----------------|
| **Pain points** | Which problems appear most frequently across ads |
| **Use cases** | Jobs-to-be-done the ads address |
| **Value props** | How benefits are framed (cost savings, speed, quality) |
| **Audiences** | Different messages for different personas (founders vs. enterprise) |

### Step 4: Evaluate Creative and Copy

**Creative patterns**: Before/after splits, feature GIFs, social proof (user counts, logos, testimonials), data-driven hooks (specific numbers or percentages). Frequency of a format often correlates with performance.

**Copy formulas**: Sentence structure, emotional triggers (fear, aspiration, curiosity), CTA patterns ("Try for free", "Get started", "See how"), benefit-focused vs. feature-focused framing.

### Step 5: Deliver Insights

Present findings with clear, prioritized recommendations:

```markdown
# [Competitor] Ad Analysis

## Overview
- Total Ads: [X] active
- Primary Themes: [breakdown by percentage]
- Ad Formats: Static [X%], Video [X%]
- Top CTAs: [list]

## Key Problems They Highlight
1. **[Pain point]** ([X] ads) — Copy: "[example]" — Why it works: [explanation]
2. **[Pain point]** ([X] ads) — Copy: "[example]" — Why it works: [explanation]

## Successful Creative Patterns
- [Pattern]: Used in [X] ads, [description of approach]

## Recommendations for Your Ads
1. Test [specific angle] — strong resonance based on competitor frequency
2. Use [format] — proven pattern in their creative
3. Lead with [approach] — their best-performing copy structure
```

## Example

**Prompt**: "Extract ads from Notion on Facebook Ad Library and tell me what messaging is working."

**Output**: Finds 23 active ads. Identifies primary themes: Productivity (35%), Collaboration (30%), Templates (20%), AI Features (15%). Top pain points: scattered information (8 ads), meeting overload (5 ads), lost documentation (4 ads). Successful patterns: before/after splits, feature GIFs, social proof ("Join 20M users"). Recommends testing the "tool sprawl" pain point, using product screenshots over abstract visuals, and leading with problems over solutions.

**Inspired by:** Sumant Subrahmanya's use case from Lenny's Newsletter

## Common Workflows

- **Campaign planning**: Extract ads --> identify patterns --> find messaging gaps --> brainstorm angles --> draft test variations
- **Positioning research**: Analyze 5+ competitors --> map positioning landscape --> find underserved angles --> develop differentiated messaging
- **Trend tracking**: Compare a competitor's ads across quarters to spot messaging shifts

## Tips

1. **Track over time**: Save ads monthly to spot evolving strategies
2. **Frequency = signal**: Ads that run longest are likely performing well
3. **Segment by audience**: Same competitor often runs different messages for different personas
4. **Cross-platform**: LinkedIn vs. Facebook messaging often differs significantly — compare both
5. **Adapt, don't copy**: Use patterns for inspiration; all ad libraries are public transparency tools
