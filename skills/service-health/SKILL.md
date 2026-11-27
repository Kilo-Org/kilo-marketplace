---
name: service-health
description: >-
  Assess whether a service is down, healthy, or deteriorating from errors,
  latency, traffic, and their baselines. Use for zero-traffic questions,
  recurring spikes, health checks and trends, service or owner lookup, and
  recent deploy context, including when evidence is already supplied. Include
  available Rootly incident, ownership, and on-call records; incident counts
  alone cannot establish health.
metadata:
  author: Rootly
  version: 3.0.0
  category: observability
  access: read
  short-description: Summarize service signals against meaningful baselines
  source:
    repository: 'https://github.com/rootlyhq/agent-skills'
    path: skills/service-health
    ref: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    commit: 2cb000d774887a5761d7953bfd6a3947cdc91baa
    license_path: LICENSE
---

# Service health

## Purpose

Explain whether a service needs attention using its behavior against a baseline.
Distinguish production health from what the incident catalog happens to contain.

## Use when / not when

- Use for an overview, service/owner lookup, or health trend over a named window.
- Use incident-response for a specific outage investigation, deploy-check for a release.
- Match the depth to the request; an owner lookup does not require every metric.

## Inputs

Read [common rules](references/common.md). Resolve service, environment, region,
time zone, and window. Default to the latest 30 minutes for current health,
making the window explicit and configurable. For trends, use the requested
period and a comparable baseline. See [tools](references/tools.md) for sources.

## Jobs

1. Obtain error rate, latency, and traffic with source charts or actual samples.
   Compare against the service's normal pattern for a comparable period, workload,
   and region; identify a missing or non-comparable baseline.
2. Prioritize persistent increases, repeated below-threshold blips, unexpected
   traffic deviations, and flatlined zero traffic. Check whether quiet traffic
   is expected. There is no universal zero-traffic duration or incident threshold.
3. Put a self-recovered spike in context. It may be transient noise but is not
   proof that there was no impact. Raw values without a baseline do not establish
   a trend or justify a healthy/unhealthy verdict.
4. Include current owner, on-call coverage, active/monitoring incidents with
   recorded severities, and the five most recent verified deploys with PRs and
   authors. If fewer are available, report the coverage. Commits are not deploys.
5. Separate incident-history statistics from live telemetry. Bound every trend
   by its actual window and list coverage; do not extrapolate from a partial page.

## Repo leg

Use mappings and ownership files for service context. A difference between
CODEOWNERS and service ownership is not inherently a defect. During an incident,
if evidence implicates a change by someone outside the owning team, recommend
consulting the change author and service owner for routing, without blame.
Do not turn routine ownership differences into health warnings.

## Data honesty

Apply [common rules](references/common.md). Missing metrics produce a partial
catalog/incident summary, not an all-clear. Report unavailable charts, baseline,
deploy feed, or stale ownership explicitly. Rootly alone may not supply the
metrics, logs, deployment history, or observability access this workflow needs.

## Output

Use [the health summary](references/output.md): scope/window, three signals
against baseline, incidents, owner/on-call, recent deploys, limitations, and the
next useful check. Label the assessment incomplete when health cannot be judged.
See [the worked example](references/example.md).

## Writes

Do not change monitors, ownership, severity, service catalog entries, or incident
state. Return proposed follow-ups only.

## Routes

Use alert-triage for a specific alert or incident-response for active impact,
if installed. Pass the chart window and evidence instead of only a health label.
