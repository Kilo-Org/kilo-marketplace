---
name: incident-response
description: >-
  Investigate outages and active incidents with Rootly context. Use when asked
  to investigate a failure, assess impact, compare simultaneous incidents,
  choose mitigation or responders, or decide whether to wait for a vendor,
  including when the user supplies the evidence. Use alert-triage for unassigned
  alerts and incident-communications for audience-specific updates.
metadata:
  author: Rootly
  version: 3.0.0
  category: observability
  access: read
  short-description: Investigate incidents and recommend mitigation
  source:
    repository: 'https://github.com/rootlyhq/agent-skills'
    path: skills/incident-response
    ref: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    commit: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    license_path: LICENSE
---

# Incident response

## Purpose

Give the incident commander an evidence-backed path toward mitigation.
Do not delay useful mitigation options to finish a root-cause narrative.

Before either answer path, open [common rules](references/common.md) for this
invocation. Invoking the skill does not load its linked references; do not rely
on an earlier read. Then read the relevant output guidance below.

## Use when / not when

- Use for incident investigation, impact assessment, and a responder brief.
- Use alert-triage for deciding what to do with an alert without an incident.
- Route audience-specific drafts to incident-communications and reviews to retrospective.

## Inputs

Route on the question's subject, not on whether it supplied its own facts.
Use **Focused decisions** below for an evidence-rule or action-state question:
what a rule requires, or what a record establishes about approval, execution or
outcome. Responder, concurrent-failure, vendor and impact questions use the
investigation jobs and the brief even when every fact is supplied. No incident
lookup is needed unless a particular record would change the answer.
Resolve the incident from the supplied ID, URL, or description using
[tools](references/tools.md). Confirm ambiguous matches; never choose by title alone.
Get the affected services, incident window, and relevant customer policy.

## Jobs

An evidence-rule or action-state question does not run the investigation jobs.

### Focused decisions

For an evidence-rule or action-state question, read **Focused decision** in
[the output contract](references/output.md). Put requested explanations under
**Rule** and return only:

```
**Answer: Yes | No | Conditional.** One sentence.
| Fact | State | Source |  rows: Signal, Corroboration, Approval, Execution,
                            Outcome, Cause, Action risks
**Rule**  **Inferences, not evidence**  **Next check**
I did not call Rootly, change any record, or execute anything.
```

Stop there; this is not an incident update. Execution is `unknown` unless a
record states it: approval alone gives "approved; execution unknown", and an
operator log may give `reported started`, never completion or recovery.
Corroboration is `not supplied` when no second source is given. Use Action risks
`unassessed in supplied evidence` only when no assessment is supplied; otherwise
attribute the reported assessment and its scope. Copy applicable states literally rather
than paraphrasing them. Copy the applicable rule and requested decision/claim
explanation from the output contract unchanged. Do not invent the commander's
rationale or an exhaustive prerequisite list. Attribute supplied assessments in
the table; approval or a practiced runbook alone does not establish one.
Handoff guidance and next checks must preserve execution and actor evidence.
Put requested hypotheticals under **Inferences, not evidence**, using "If ... could/would ...".
Use `None.` for **Inferences, not evidence** unless the user explicitly asks
for hypothetical scenarios. Do not add sample updates or illustrative action
narration; keep the action status at the strength supplied by its source.

### Incident investigations

1. Establish current impact first: the reported symptom, customer experience,
   blast radius, and relevant metrics or logs. Include retrieved charts when
   available. Rank observations by confidence with their evidence and timestamps.
2. Check recent deploys, PRs, dependencies, config, and feature flags on the
   affected service and its dependencies. Identify authors for consultation,
   without tagging or paging anyone. Recency alone does not establish causation.
3. Present mitigation options, the next check, and any need for another responder.
   Anchor each action to its recorded state: proposed, approved, executing, or
   outcome verified. Approval establishes permission, not execution; an unreported
   execution is unknown, not known not to have happened. Separately
   state the known prerequisites, possible harm and verification criteria; if
   these are unassessed, say so. Reversible describes a recovery option, not a
   bound on harm or cost. An unread runbook does not establish its contents.
   Explain the missing expertise, service owner, decision authority, or capacity;
   name the evidence behind the suggestion. Do not judge a person's performance.
4. For concurrent failures, compare dependency overlap, error signatures, and
   changes. Different symptoms with little shared dependency evidence favor
   separate investigations and proposed cross-links. Shared timing alone does
   not justify a merge. Revisit if a common failing dependency, matching errors,
   or one deployed change provides a stronger explanation. Do not split blindly
   when shared-cause evidence or scarce response capacity points elsewhere.
5. Compare up to three to five useful historical matches, fewer if that is all
   the evidence supports. Explain similarities, differences, confidence, and
   whether the old fix fits today's symptoms. Keyword or service-name matches
   alone are weak. Do not invent a track record for the assistant.
6. Treat a coincident vendor outage as a hypothesis. Compare affected endpoints,
   codes, regions, and timing; recommend vendor confirmation while continuing
   internal checks, including automated dependency updates. Do not advise waiting
   for the vendor solely because its status page is red.
   Respect a complete, scoped change audit; reopen it only for a specific gap or
   new evidence. One failed alternative does not exhaust mitigation options.
   Leave recheck and communication cadence to the commander or customer policy.

## Repo leg

Read mapped paths and history around symptom onset; use 48 hours before onset as
an initial search window only when no better deployment window is known.
Check real deployment timing, major upgrades, review and CI gaps, skipped
pre-production, bot merges, bypassed config review, and change breadth. Fifty
changed lines or five files are prompts to inspect scope, not universal risk
thresholds. Include config changes outside git when an authorized source exists.
Without repo access, continue incident analysis and identify that gap.

## Data honesty

Apply the evidence rules in [common rules](references/common.md). Unknown impact
is not zero impact. Keep competing supported hypotheses visible and revise them
when evidence changes. Similarity or solution-tool failures are optional gaps;
an unresolved incident identity stops incident-specific conclusions.

## Output

Before returning either format, apply the [final evidence check](references/evidence.md#final-evidence-check)
to the whole answer, including next steps and review questions.
For focused decisions, use the focused format above.
For investigations, use [the responder brief](references/output.md): impact and evidence, recent
changes, then next actions and proposed responders. Always include the recorded
status/severity, affected services or unknown, and the next recommended action.
See [the worked example](references/example.md) for concurrent failures.

## Writes

Read-only: do not change severity/status, merge/split incidents, cross-link records,
page responders, publish updates, or roll back production. Describe proposals
as proposals and preserve the commander's decision authority.

## Routes

If installed, use incident-communications for stakeholder drafts, on-call for
coverage/handoffs, and retrospective for post-incident learning. Otherwise state
the next workflow without pretending the other skill ran.
