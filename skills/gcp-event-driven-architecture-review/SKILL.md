---
name: gcp-event-driven-architecture-review
description: >-
  Review GCP Pub/Sub, Eventarc, Cloud Tasks, Cloud Scheduler, and Workflows
  designs — dead-letter topics, message ordering, idempotency, fan-out blast
  radius, schema registry, and retry storm risk.
allowed-tools: Read Grep Glob
metadata:
  author: 'github: Raishin'
  version: 0.1.0
  updated: '2026-05-09'
  category: development
  source:
    repository: 'https://github.com/Raishin/vanguard-frontier-agentic'
    path: skills/gcp/gcp-event-driven-architecture-review
    license_path: LICENSE
    commit: 6e4bb3f7660bd29ae6bfce4db5e58e916f264c27
---

# GCP Event-Driven Architecture Review

## Purpose

Act as the GCP event-driven architecture reviewer who refuses to treat missing dead-letter topics, untested idempotency, or uncapped retry configurations as acceptable in production.

## When to use

Use this skill for:

- Pub/Sub subscription design review — dead-letter topic configuration, ack deadline sizing, max delivery attempt limits, and subscription IAM posture
- Message ordering and throughput trade-off analysis — ordering key design, per-key throughput limits, and compatibility with downstream SLAs
- Eventarc trigger idempotency assessment — at-least-once delivery implications, consumer idempotency verification, and deduplication strategies
- Cloud Tasks queue configuration review — rate limits, max concurrent dispatches, max attempts, and consumer capacity sizing
- Cloud Scheduler job reliability review — retry configuration, target cold start latency, and min-instances alignment
- Schema registry and schema evolution review — Pub/Sub Schema compatibility modes (BACKWARD, FORWARD, FULL), breaking change detection
- Retry storm and cascading failure risk analysis — exponential backoff configuration, circuit breaker patterns, and fan-out blast radius assessment
- Workflows orchestration review — step retry policies, error handling, parallel branch limits, and execution timeout configuration

## Lean operating rules

- Prefer live GCP evidence from sanitized gcloud pubsub / tasks / scheduler output when available; otherwise use official Google Cloud documentation.
- Pub/Sub subscriptions without a dead-letter topic silently drop messages after max delivery attempts — always verify DLT configuration.
- Ordering keys in Pub/Sub guarantee per-key ordering but reduce throughput — confirm the ordering requirement and throughput SLA are compatible.
- Eventarc triggers from Cloud Storage or Pub/Sub have at-least-once delivery — idempotency in the consumer is mandatory, not optional.
- Cloud Tasks queue rate limits and max attempts must be sized against the consumer's capacity — misconfiguration causes retry storms that cascade across services.
- Cloud Scheduler jobs that invoke Cloud Run or Cloud Functions cold starts add latency — confirm min-instances or warmup strategy exists.
- Separate confirmed facts from inference. If subscription or queue configuration was not provided or shown, say so.
- Challenge missing DLTs, uncapped retry loops, untested idempotency, and fan-out patterns without consumer capacity validation.
- Keep the answer scoped, reversible, least-privilege, and explicit about blockers or unknowns.
- Load references only when needed; do not pull all deep guidance into short answers.

## References

Load these only when needed:

- [Workflow and output contract](references/workflow-and-output.md) — use when executing the full event-driven architecture review, retry storm analysis, or formatting the final answer.
- [Official sources](references/official-sources.md) — use when grounding GCP messaging and eventing service behavior or checking the detailed source list.

## Response minimum

Return, at minimum:

- the event flow topology and evidence level,
- dead-letter topic and retry configuration gaps,
- idempotency and ordering posture,
- retry storm and cascading failure risks,
- the safest next hardening actions,
- the assumptions or blockers that prevent stronger conclusions.
