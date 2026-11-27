---
name: on-call
description: >-
  Look up Rootly on-call coverage and personal shifts, prepare shift handoffs,
  and recommend coverage changes using schedule, workload, expertise, and
  explicit availability. Use for shifts, handoffs, swaps, or coverage planning
  without modifying schedules.
metadata:
  author: Rootly
  version: 3.0.0
  category: productivity
  access: read
  short-description: Prepare on-call handoffs and evidence-based coverage
  source:
    repository: 'https://github.com/rootlyhq/agent-skills'
    path: skills/on-call
    ref: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    commit: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    license_path: LICENSE
---

# On-call

## Purpose

Help responders understand their obligations and transfer useful context.
Coverage recommendations support human agreement and do not assign work.

## Use when / not when

- Use for who is on, personal shifts, shift handoff, coverage or swap advice.
- Use incident-communications for an incident commander handoff.
- Use incident-response to decide which expertise an active investigation needs.

## Inputs

Read [common rules](references/common.md). Resolve the person for personal
requests, affected services, schedules, exact interval, and display time zone.
Ask rather than infer time zone or identity. See [tools](references/tools.md).

## Jobs

1. For a lookup, show the recorded responder and shift boundaries in the chosen
   time zone. Include overlapping responsibilities when relevant. Do not run an
   unnecessary personal workload investigation for a simple schedule question.
2. For a handoff, cover every alert and incident the outgoing responder touched
   within the shift, each outcome, alert actionability/tuning needs, loose ends,
   follow-ups, and active incidents needing transfer. Include upcoming deploys,
   events, and maintenance. Summarize compactly and link the scoped item list;
   disclose incomplete attribution or pagination instead of claiming completeness.
3. Contextualize current load using page priority and actionability, ongoing
   versus resolved incidents, and documented consecutive nights of paging.
   Do not equate noisy page volume with severe-incident workload or diagnose
   fatigue from a score. Use the person's stated need for help or availability.
4. For a swap/coverage proposal, check every relevant schedule and escalation
   policy for both people, overlap, time zones, authorized calendar availability
   and PTO, service context, and required access. If any source is unavailable,
   label the candidate provisional and list the checks a human must complete.
5. Explain each proposed responder using operational need, relevant expertise
   and authority, duties, and explicit availability. Never use Slack presence,
   response speed, inferred health, or assumed working hours to rank people.
   A candidate suggested by a tool still needs these checks and human agreement.

## Repo leg

When asked whether the user is on call for code they are editing, map the repo
and relevant paths to services, then resolve schedules. Ask about conflicting
or absent mappings. Other on-call jobs do not require repository access.

## Data honesty

Apply [common rules](references/common.md). An empty schedule query with limited
scope is not proof someone has no duties. Missing calendar data is not free time.
Record coverage windows and source freshness. Stop personal conclusions if the
user cannot be identified; continue non-personal schedule information if useful.

## Output

Use the relevant mode in [output guidance](references/output.md). Include
current coverage, the next handoff in the chosen time zone, known workload
context or its absence, and pending checks. For handoffs, upcoming work is a
required section. See [the worked example](references/example.md).

## Writes

Do not create overrides, request/accept coverage, alter schedules, assign work,
or page anyone. State the proposal and whose agreement remains necessary.

## Routes

Use incident-response for an active investigation and incident-communications
for commander handoff drafts when installed. Preserve the distinction between
shift coverage and command of a particular incident.
