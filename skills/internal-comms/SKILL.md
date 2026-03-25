---
name: internal-comms
description: "Drafts internal communications — 3P updates, company newsletters, FAQs, status reports, leadership updates, project updates, and incident reports — using company-specific formats and tone guidelines loaded from bundled example files. Use when writing any internal communication, composing a weekly status update, drafting a company newsletter, preparing leadership or 3P updates, or answering internal FAQs."
license: Complete terms in LICENSE.txt
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: internal-comms
    license_path: internal-comms/LICENSE.txt
---

# Internal Comms

Drafts internal communications using company-specific formats, tone, and structure guidelines loaded from bundled example files.

## Workflow

### Step 1: Identify Communication Type

Determine which type of internal communication is needed from the request.

### Step 2: Load the Appropriate Guideline

Load the matching guideline file from the `examples/` directory:

| Communication Type | Guideline File |
|-------------------|----------------|
| Progress/Plans/Problems (3P) updates | `examples/3p-updates.md` |
| Company-wide newsletters | `examples/company-newsletter.md` |
| FAQ responses | `examples/faq-answers.md` |
| Status reports, leadership updates, project updates, incident reports, or other | `examples/general-comms.md` |

### Step 3: Draft Using Guidelines

Follow the specific instructions in the loaded guideline file for formatting, tone, and content structure. Gather any missing context from the user before drafting.

If the communication type does not match any existing guideline, ask for clarification or more context about the desired format.

## Example

**Prompt**: "Write a 3P update for my team this week. We shipped the new dashboard, plan to start the API migration, and are blocked on the auth provider outage."

**Process**: Loads `examples/3p-updates.md`, follows the 3P format (Progress, Plans, Problems), and drafts a concise update with the three sections populated from the user's input.

## Tips

1. **Provide raw bullet points** rather than full prose — the skill formats them into the correct structure
2. **Mention the audience** (team, leadership, company-wide) so tone is calibrated correctly
3. **Include dates and metrics** where possible for status reports and project updates
