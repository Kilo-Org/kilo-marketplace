---
name: domain-name-brainstormer
description: "Generate creative domain name ideas based on a project description and check availability across multiple TLDs (.com, .io, .dev, .ai, .app). Use when launching a new project or company, rebranding, registering a side project domain, or finding available alternatives when a preferred name is taken."
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: domain-name-brainstormer
---

# Domain Name Brainstormer

Generates creative, brandable domain name options for a project and checks availability across multiple TLDs — saving hours of manual brainstorming and availability checking.

## Workflow

### Step 1: Understand the Project

Gather context to generate relevant names:

- What the project does and who it serves
- Target audience and industry
- Preferred keywords or word roots (e.g., "pixel", "studio")
- TLD preferences (.com, .io, .dev, .ai, .app)
- Name style: descriptive, abstract, compound word, or invented
- Length preference: short (under 8 chars) or flexible

### Step 2: Generate Domain Name Candidates

Create 10–15 candidates using strategies:

- **Compound words**: Combine two relevant terms (e.g., "SnippetBox", "CodeClip")
- **Portmanteaus**: Blend words together (e.g., "Netlify" from "internet" + "simplify")
- **Descriptive**: Clearly state the function (e.g., "ShareCode")
- **Abstract/Invented**: Unique coined words (e.g., "Vercel", "Figma")
- **Keyword + TLD hacks**: Use the TLD as part of the name (e.g., "del.icio.us")

### Step 3: Check Availability

For each candidate, check availability across requested TLDs:

```
🎯 Domain Name Suggestions

## Available (.com)
1. ✓ snippetbox.com — Clear, memorable
2. ✓ codeclip.com — Short, only 8 characters

## Available (Alternative TLDs)
3. ✓ snippet.dev — Perfect .dev extension for developer audience
4. ✓ codebox.io — Tech-forward, popular with startups

## Taken / Premium
- codeshare.com (Taken, est. $2,500)
- snippets.com (Taken, premium domain)
```

### Step 4: Provide Recommendations

Rank the top picks with reasoning:

- **Top pick**: Best combination of availability, memorability, and brand fit
- **Runner-up**: Strong alternative with different trade-offs
- **Budget option**: Available at standard registration price

Include pricing context: standard domains (~$10–15/year), premium TLDs like .io/.ai (~$30–50/year), and aftermarket domains (variable).

### Step 5: Suggest Next Steps

- Register the chosen domain before it's taken
- Check matching social media handle availability (@username)
- Consider registering key TLD variants to protect the brand
- Verify no trademark conflicts

## Example

**Prompt**: "I'm building a tool for developers to share code snippets. Suggest creative domain names."

**Output**: Analyzes project (target: developers, features: code sharing, snippets). Generates candidates: snippetbox.com (available, descriptive), codeclip.com (short, available), snippet.dev (perfect .dev extension), codebox.io (tech-forward). Top pick: snippet.dev — short, memorable, .dev signals developer tool. Runner-up: snippetbox.com — .com universally recognized, great brandability.

**Inspired by:** Ben Aiad's use case from Lenny's Newsletter

## What Makes a Good Domain Name

- **Short**: Under 15 characters, ideally under 10
- **Memorable**: Easy to recall after hearing once
- **Pronounceable**: Can be spoken in conversation without spelling it out
- **No hyphens**: Easier to share verbally
- **Brandable**: Unique enough to stand out in the market

## TLD Guide

| TLD | Best For | Price Range |
|-----|----------|-------------|
| .com | Universal, trusted, any business | $10–15/yr |
| .io | Tech startups, developer tools | $30–50/yr |
| .dev | Developer-focused products | $12–20/yr |
| .ai | AI/ML products | $30–80/yr |
| .app | Mobile or web applications | $14–20/yr |
| .co | Alternative to .com | $10–25/yr |
| .design | Creative and design agencies | $30–40/yr |

## Tips

1. **Act fast**: Good domains get registered quickly
2. **Register variations**: Get .com and your primary TLD to protect the brand
3. **Avoid numbers**: Hard to communicate verbally
4. **Say it out loud**: Test pronunciation before committing
5. **Check trademarks**: Ensure no legal conflicts exist
6. **Think long-term**: Will the name still fit if the project evolves?
