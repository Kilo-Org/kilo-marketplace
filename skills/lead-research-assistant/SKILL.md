---
name: lead-research-assistant
description: "Identify and qualify potential leads by analyzing a product's value proposition, defining ideal customer profiles, researching matching companies, scoring them by fit, and providing personalized outreach strategies. Use when building sales prospect lists, preparing for business development outreach, researching target accounts, or qualifying leads for a specific product or service."
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: lead-research-assistant
---

# Lead Research Assistant

Identifies and qualifies potential leads by analyzing a product or service, defining the ideal customer profile, researching matching companies, and delivering prioritized prospect lists with personalized outreach strategies.

## Workflow

### Step 1: Understand the Product or Service

Gather context about what is being sold:

- If run from a code directory, analyze the codebase to understand the product automatically
- Identify the core value proposition and key differentiators
- Understand what problems the product solves and for whom
- Note pricing model and competitive positioning

### Step 2: Define the Ideal Customer Profile (ICP)

Work with the user to establish targeting criteria:

- **Industry and sector**: Which verticals are the best fit
- **Company size**: Employee count or revenue range
- **Geography**: Location preferences or restrictions
- **Technology stack**: Tools or platforms that signal fit (e.g., companies using Kubernetes)
- **Pain points**: Specific problems that map to the product's value proposition
- **Budget indicators**: Funding stage, revenue signals, or technology spend patterns

### Step 3: Research and Identify Leads

Search for companies matching the ICP using available signals:

- Job postings that mention relevant technologies or pain points
- GitHub activity showing relevant tech stack usage
- Recent funding rounds or growth indicators
- News about expansion, hiring, or relevant initiatives
- Complementary product usage that suggests need

### Step 4: Score and Prioritize

Rate each lead on a 1–10 fit score based on:

- Alignment with ICP criteria
- Signals of immediate need (active job postings, recent pain-point mentions)
- Budget availability (funding stage, company size)
- Competitive landscape (are they already using a competitor?)
- Timing indicators (contract renewal cycles, fiscal year planning)

### Step 5: Deliver Actionable Lead Profiles

For each lead, provide a structured profile:

```markdown
## Lead: [Company Name]

**Website**: [URL]
**Priority Score**: [X/10]
**Industry**: [Industry] | **Size**: [Employee count]

**Why They're a Good Fit**:
- [Specific reason based on their business]
- [Signal that indicates need]

**Target Decision Maker**: [Role/Title]
**LinkedIn**: [URL if available]

**Value Proposition for Them**:
[How the product solves their specific problem]

**Outreach Strategy**:
[Personalized approach — mention specific pain points, recent news, or relevant context]

**Conversation Starters**:
- [Specific talking point 1]
- [Specific talking point 2]
```

### Step 6: Suggest Next Steps

After delivering the lead list:

- Offer to draft personalized outreach messages for top leads
- Suggest saving results to CSV for CRM import
- Recommend prioritization based on timing and urgency signals
- Offer deeper research on the highest-scoring prospects

## Examples

### Example 1: Developer Tool Leads

**Prompt**: "I'm building a tool that masks sensitive data in AI coding assistant queries. Find potential leads."

**Research process**: Search for companies with GitHub repos referencing Copilot or Cursor in their workflows. Check job postings for "AI coding assistant" or "code security" roles. Look for fintech/healthcare companies with recent SOC 2 or HIPAA compliance mentions. Cross-reference with companies that have public incidents involving exposed secrets in code.

**Output**: Identifies companies that use AI coding assistants (Copilot, Cursor), handle sensitive data (fintech, healthcare, legal), have evidence in GitHub repos of coding agent usage, and may have compliance requirements around data exposure. Includes LinkedIn URLs of relevant decision-makers (VP Engineering, CISO).

### Example 2: Consulting Practice

**Prompt**: "I run a consulting practice for remote team productivity. Find me 10 companies in the Bay Area that recently went remote."

**Output**: Identifies companies that recently posted remote job listings, announced remote-first policies, are hiring distributed teams, and show signs of remote work challenges. Provides personalized outreach strategies for each.

**Inspired by:** Use case from Lenny's Newsletter

## Tips

1. **Be specific about your product**: The more detail about unique value, the better the lead matching
2. **Run from your codebase**: Automatic product understanding leads to better targeting
3. **Provide ICP context**: Industry, size, and location constraints sharpen results
4. **Request follow-up research**: Ask for deeper dives on the most promising leads
5. **Iterate on criteria**: Refine the ICP based on which leads feel strongest
