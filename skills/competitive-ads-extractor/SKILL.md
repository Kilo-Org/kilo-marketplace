---
name: competitive-ads-extractor
description: "Extract competitor ads from ad libraries (Facebook Ad Library, LinkedIn, TikTok), capture screenshots, and analyze messaging patterns, creative approaches, audience targeting, and copy formulas. Use when researching competitor ad strategies, planning ad campaigns, finding inspiration for creative, or analyzing market positioning through paid media."
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: competitive-ads-extractor
---

# Competitive Ads Extractor

Extracts competitor ads from ad libraries and analyzes what's working — the problems they highlight, use cases they target, and copy/creative that resonates — to inform and inspire ad campaigns.

## Workflow

### Step 1: Identify Target Competitors and Platforms

Gather context:

- Which competitors to analyze (specific companies or a competitive set)
- Which platforms to check (Facebook Ad Library, LinkedIn, TikTok, Google Ads Transparency)
- Focus area: messaging, creative, audience targeting, or all
- Time period: current ads only, or trend analysis over quarters

### Step 2: Extract Ads from Ad Libraries

Navigate to the relevant ad library (e.g., `https://www.facebook.com/ads/library/` for Meta ads) and search for the competitor by company name or page. Browse active ads and for each one, capture:

- Screenshot of the ad creative
- Headline and body copy text
- Call-to-action button text
- Format: static image, video, or carousel
- Any visible targeting or placement info

Save screenshots to a local directory (e.g., `competitor-ads/[company-name]/`) organized by competitor. If no ads are found, verify the company name spelling and check whether they run ads on that platform — some companies concentrate spend on a single channel.

### Step 3: Analyze Messaging Patterns

Categorize extracted ads and identify patterns:

- **Problems highlighted**: Which pain points appear most frequently
- **Use cases targeted**: What jobs-to-be-done the ads address
- **Value propositions**: How they frame their product's benefits
- **Audience segments**: Different messages for different personas (e.g., founders vs. enterprise)

### Step 4: Evaluate Creative Approaches

Identify successful creative patterns:

- **Before/After splits**: Showing chaos → organized solution
- **Feature showcases**: GIF or video of product in action
- **Social proof**: User counts, customer logos, testimonials
- **Data-driven**: Leading with specific numbers or percentages

Note which formats appear most frequently — frequency often correlates with performance.

### Step 5: Analyze Copy Formulas

Extract headline and body copy patterns:

- Sentence length and structure
- Emotional triggers (fear, aspiration, curiosity)
- CTA patterns ("Try for free", "Get started", "See how")
- Benefit-focused vs. feature-focused framing

### Step 6: Deliver Actionable Insights

Present findings with clear recommendations:

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

**Ad campaign planning**: Extract competitor ads → Identify successful patterns → Note messaging gaps → Brainstorm unique angles → Draft test variations

**Positioning research**: Analyze 5 competitors → Map positioning landscape → Find underserved angles → Develop differentiated messaging

**Trend tracking**: Compare a competitor's ads across quarters — what messaging shifted and why

## Tips

1. **Track over time**: Save ads monthly to spot evolving strategies
2. **Look for frequency**: Ads that run longest are likely performing well
3. **Segment by audience**: Same competitor often runs different messages for different personas
4. **Compare platforms**: LinkedIn vs. Facebook messaging often differs significantly
5. **Use for inspiration, not copying**: Adapt successful patterns to your own brand voice

### Legal and Ethical Guidelines

- Use extracted ads for research and inspiration only
- Do not copy ad creative or messaging directly
- Respect intellectual property — adapt patterns, don't plagiarize
- All ad libraries used are public transparency tools
