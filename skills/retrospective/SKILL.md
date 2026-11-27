---
name: retrospective
description: >-
  Prepare a Rootly post-incident review with sourced metadata, timeline, impact
  evidence, facilitation questions, and action proposals. Use for retrospectives
  and incident action-item reviews; preserve human ownership of conclusions,
  disputed causes, and roadmap commitments.
metadata:
  author: Rootly
  version: 3.0.0
  category: productivity
  access: read
  short-description: Prepare incident reviews while humans own the learning
  source:
    repository: 'https://github.com/rootlyhq/agent-skills'
    path: skills/retrospective
    ref: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    commit: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    license_path: LICENSE
---

# Retrospective

## Purpose

Prepare evidence and questions that help humans learn from an incident.
Do not invent the team's conclusions or convert suggestions into commitments.

## Use when / not when

- Use for review preparation, timeline reconstruction, and action-item review.
- Use incident-response for mitigation of an active incident.
- If still active, ask whether a preliminary evidence draft is wanted; do not
  imply that the response or review is finished.

## Inputs

Read [common rules](references/common.md). Resolve incident, state, customer
severity policy, intended audience, and available human-authored conclusions.
Use [tools](references/tools.md) for incident, transcript, review, and action records.

## Jobs

1. As soon as resolution is recorded, recommend naming a review owner, scheduling
   the review, and capturing raw responder notes while memory is fresh. These
   are proposals; do not assign people or schedule a meeting.
2. Match depth to the customer's severity thresholds. A lower-severity review
   can be an async factual summary plus learning questions. A higher-severity
   review also examines response quality, impact charts, alert gaps, and whether
   facilitated individual interviews would help. No universal severity cutoff.
3. Assemble metadata, a sourced timeline, impact dashboards, and factual summary.
   Identify missing/conflicting timestamps. Ask questions that connect technical
   evidence to response decisions; distinguish retrospective knowledge from
   what responders could know at the time.
4. Examine technical conditions (test/review gates, alerting, runbooks, pre-prod,
   single points of failure) and organizational conditions (roadmap pressure,
   documented overnight load, rotation capacity, concentrated knowledge,
   unclear ownership). For each incident-specific question, name the authorized
   source and the unresolved fact it would clarify. Keep generic agenda prompts
   separate and label them as generic, not incident findings; their selection
   must not be driven by excluded accounts.
   Protect confidential interview sources and do not expose identifiable private
   statements or infer personal health from messages. Without permission, do not
   reveal a private statement's topic or gist in reviewer notes, anonymous
   summaries, or targeted questions. Use only approved interview synthesis;
   if needed, say only that restricted material was excluded.
5. Humans decide what mattered, what was learned, and what to change. Quote or
   summarize their existing conclusions with attribution, or leave explicit
   human-review questions. Do not fill the gaps with a polished root-cause story.
6. Keep confirmed contributing factors separate from competing explanations.
   Show evidence for and against disputed causes without picking a winner.
   Propose the logging, test, or investigation that could resolve the dispute.
7. Present action candidates to the roadmap owner (PM/engineering manager or
   customer-defined role). Each includes evidence, intended outcome, and a way
   to verify improvement. The owner schedules and then assigns it, or records
   why it is declined. Do not assign an engineer or due date by default, and do
   not erase a declined action from the record.

## Repo leg

Link verified deploy/PR/commit events to the timeline; distinguish their times.
Include relevant paths when drafting an action proposal, without implying the
change author caused the incident. Lack of repo access is a recorded evidence gap.

## Data honesty

Apply [common rules](references/common.md). A root cause can remain unknown.
Transcript statements are attributed accounts, not automatic operational proof.
An empty action list with incomplete permissions is not proof there are no actions.
Never claim interviews, review approval, or roadmap acceptance occurred when absent.

## Output

Use [the review packet](references/output.md): facts/timeline, impact, review
questions, human-authored learning or unresolved questions, disputed explanations,
and action proposals awaiting roadmap decisions. See [the worked example](references/example.md).

## Writes

Do not create review records, publish retrospectives, create/assign action items,
change progress status, or schedule interviews. Explicitly requested local drafts
are allowed; substantive conclusions remain with the human review participants.

## Routes

Use incident-communications for an approved external summary and incident-response
for renewed impact, if available. Public summaries must respect company policy.
