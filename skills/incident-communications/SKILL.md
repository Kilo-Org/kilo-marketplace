---
name: incident-communications
description: >-
  Draft responder, executive, customer, or incident commander handoff updates
  from Rootly incident evidence. Use for stakeholder briefs and status-update
  drafts; distinguish confirmed impact from internal hypotheses and never
  publish messages.
metadata:
  author: Rootly
  version: 3.0.0
  category: productivity
  access: read
  short-description: Draft clear incident updates for the right audience
  source:
    repository: 'https://github.com/rootlyhq/agent-skills'
    path: skills/incident-communications
    ref: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    commit: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    license_path: LICENSE
---

# Incident communications

## Purpose

Draft an update that remains accurate if the leading hypothesis proves wrong.
Tailor detail to the audience while preserving uncertainty and useful next steps.

## Use when / not when

- Use for responder, executive, customer, or incident commander handoff drafts.
- Use incident-response to investigate; on-call owns shift handoffs.
- Do not interpret a draft request as permission to publish or send it.

## Inputs

Read [common rules](references/common.md). Resolve incident, audience, intended
channel, observation time, approved template, and update cadence. If the audience
is unclear, ask before preparing external wording. Use [tools](references/tools.md).

## Jobs

1. First show a short reviewer fact list from audience-authorized evidence:
   impact, exact recorded action wording and phase, conditional recovery estimate,
   and approved next update, each with its source or explicit unknown. Then draft
   from that list. Reuse the recorded action wording or an approved audience-safe
   paraphrase; if neither is suitable, request wording instead of inventing it.
   "Rollback validation is underway" stays that way: it establishes neither
   "we are rolling back" nor "a rollback has already been applied."
   Approval or a status of "investigating" is not evidence of execution. Keep
   hypotheses internal; do not combine an observation with an inferred cause.
2. Responders need current state, checked/ruled-out hypotheses, metric values
   and trends, impact, and ordered next actions with owners or owner-needed.
   Commander handoff also needs current decisions, pending checks and command
   transfer/acknowledgment still required; do not silently appoint a commander.
3. Executives need affected customers/features, severity of experience, external
   communications already sent, a plain-language summary, and next steps.
   Prefer a direct briefing through the agreed company channel; do not invite
   them onto the bridge by default or send a message yourself.
4. Customers need the degraded features, experienced symptoms, confirmed scope,
   work underway, and next update. Follow approved external templates; omit
   internal hypotheses and speculative vendor attribution. Adjust technical
   detail to the customer's audience rather than expose internal diagnostics;
   keep the sourced action wording, estimate conditions and commitments intact.
5. Use an incident-commander-approved or evidence-supported recovery estimate
   as a buffered range, with its source, conditions, and uncertainty. Do not
   invent the range or its buffer. If no defensible estimate exists, explicitly
   say recovery time is unknown, request an estimate from the commander, and
   include a confirmed next-update time or mark it pending approval in the draft.
   Preserve that commitment: do not add "or sooner," extra updates, or a faster
   cadence unless the incident commander or applicable policy approves it.
6. Avoid "soon/shortly," minimization, unsupported all-clears or data-safety
   assurances, blame, defensive "unexpected/unprecedented" framing, and generic
   apologies for inconvenience. Use concrete impact language without exaggeration.
7. Revise when impact, evidence, actions, or estimates change. Do not create
   timer-driven channel noise. If policy requires a scheduled human update with
   no new facts, say what is unchanged and still unknown in the requested draft.
8. Before handing off, compare the recipient draft with the fact list and remove
   any added claim or promise. If a reviewer note says a sentence is unsupported
   or needs new approval, correct or omit that sentence now; a caveat in notes
   does not make it suitable for the draft. Ask for missing facts separately.

## Repo leg

Use code context already supported by incident evidence to explain changes in
plain language. Keep suspect commits and unconfirmed cause attribution out of
customer drafts. Repository access is optional for communications.

## Data honesty

Apply [common rules](references/common.md). A resolved record is not a verified
all-clear. When confirmation is uncertain, label it unconfirmed internally and
ask the commander. No evidence-backed estimate is better than invented precision.
Missing required incident data stops a substantive incident-specific update;
offer only a clearly labeled template until facts are supplied.

## Output

Use [the audience templates](references/output.md). Put the reviewer fact list
before the separate recipient draft. Label the output as a draft,
name audience/destination, and include state, unknowns, actions, recovery estimate
or unknown, next-update time or pending, and internal verification notes kept
outside customer-facing text. See [the worked example](references/example.md).

## Writes

Do not publish to a status page, post in chat, DM executives, send email, or
modify an incident. Identify the human reviewer and intended destination only.

## Routes

Use incident-response for missing investigative evidence and on-call for shift
coverage, when available. Do not let a draft turn into an investigation without
respecting the user's scope and urgency.
