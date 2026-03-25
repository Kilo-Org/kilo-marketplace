---
name: lead-research-assistant
description: "Identifies and qualifies sales leads by analyzing a product's value proposition, defining ideal customer profiles (ICP), researching matching companies via job postings and GitHub signals, scoring prospects by fit on a 1-10 scale, and delivering personalized outreach strategies with conversation starters. Use when building prospect lists, preparing for business development outreach, researching target accounts, qualifying leads for a product or service, or generating personalized sales messaging."
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: lead-research-assistant
---

## Workflow

### Step 1: Understand the Product

Gather context about what is being sold. If run from a code directory, analyze README, landing page copy, and package metadata to extract the value proposition automatically. Otherwise, ask for:

- Core value proposition and key differentiators
- Problems solved and target buyer persona
- Pricing model and competitive positioning

### Step 2: Define the ICP

Confirm targeting criteria: industry, company size, geography, tech stack signals, budget indicators (funding stage, revenue range).

### Step 3: Research and Identify Leads

Use web search with targeted queries for each signal type:

```
# Job postings signaling need
site:linkedin.com/jobs "[target technology]" OR "[pain point keyword]"
site:lever.co "[company type]" "[relevant role]"
site:greenhouse.io "[target technology]"

# GitHub signals for tech stack fit
site:github.com "[technology]" org:[company]
# Search GitHub orgs for repos using specific dependencies
https://github.com/orgs/[company]/repositories?q=[technology]

# Funding and growth signals
site:crunchbase.com "[company name]" "Series"
site:techcrunch.com "[company name]" "raises" OR "funding"
```

Cross-reference signals: a company hiring for a relevant role AND using the relevant tech stack AND recently funded scores higher than one signal alone.

**Validation**: Require at least 2 independent signals per lead before advancing to scoring. If searches return fewer than 5 candidates, broaden ICP criteria or add new signal sources.

### Step 4: Score and Prioritize

Rate each lead 1-10 based on weighted criteria:

| Factor | Weight | Scoring |
|--------|--------|---------|
| ICP alignment | 30% | Industry + size + geography match |
| Active need signals | 25% | Job postings, pain-point mentions |
| Budget availability | 20% | Funding stage, company revenue |
| Timing indicators | 15% | Contract renewals, fiscal year, recent changes |
| Competitive landscape | 10% | No incumbent vs. displacing competitor |

### Step 5: Deliver Lead Profiles

**Validation**: Verify LinkedIn URLs resolve and company websites are active before including in output. Drop leads scoring below 5/10.

For each qualifying lead, output a structured profile:

```markdown
## Lead: [Company Name]

**Website**: [URL] | **Score**: [X/10] | **Industry**: [Industry] | **Size**: [N employees]

**Fit signals**:
- [Specific evidence from research — job posting URL, GitHub repo, funding round]
- [Second signal with source link]

**Decision Maker**: [Role/Title] — [LinkedIn URL]

**Personalized Outreach**:
- Hook: [Reference their specific pain point or recent news]
- Value prop: [How the product solves their specific problem]
- Ask: [Specific CTA — demo, call, pilot]
```

### Step 6: Export and Next Steps

```python
import csv

leads = [
    {"company": "Acme Corp", "score": 9, "contact": "VP Eng", "linkedin": "https://...", "hook": "..."},
    # ... additional leads
]

with open("leads.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=leads[0].keys())
    writer.writeheader()
    writer.writerows(leads)
```

After delivery, offer to: draft personalized outreach emails for top-3 leads, do deeper research on highest-scoring prospects, or refine ICP criteria based on which leads feel strongest.

## Example

**Prompt:** "I'm building a tool that masks sensitive data in AI coding assistant queries. Find potential leads."

**Research approach**: Search GitHub for orgs with Copilot/Cursor repos (`site:github.com copilot configuration`), job boards for "AI coding assistant" or "code security" roles (`site:lever.co "AI security" OR "code privacy"`), and Crunchbase for funded fintech/healthcare companies with SOC 2 or HIPAA requirements.

**Output**: Prioritized list of 10 companies using AI coding assistants that handle sensitive data, each with fit score, evidence links, decision-maker LinkedIn URLs (VP Engineering, CISO), and a personalized outreach hook referencing their specific compliance needs.

**Inspired by:** Use case from Lenny's Newsletter
