---
name: sent
description: >-
  Routes broad or ambiguous Sent requests to the correct MCP-backed operation or
  specialist skill. Use when the user asks what Sent can do, says "help me with
  Sent" or "set up messaging," needs several Sent workflows, or has not made the
  channel, task, or desired operation clear enough to select a more specific
  skill.
metadata:
  category: development
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/sent
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

# Sent Meta Dispatcher

## Overview

This skill is a router, not a worker. When a request does not identify one clear Sent workflow, inspect the intent, ask only the clarification needed to select a route, and invoke the matching skill.

Sent spans direct account operations through its MCP server and specialist guidance for SMS, WhatsApp, RCS, Sender Profiles, templates, and delivery analysis. Prefer a direct-operation skill for live Sent data or mutations and a specialist skill for planning, compliance, diagnosis, or product design.

## When to Use

Use when:
- The user mentions "Sent" broadly without naming a channel ("help me with Sent", "I want to use Sent for messaging")
- The user asks an open-ended question like "what can you help with on Sent?" or "where do I start?"
- The request could plausibly span multiple target skills (e.g., "messaging isn't working" — could be account readiness, 10DLC vetting, WABA template rejection, RBM capability, or an MDR funnel)
- The channel is ambiguous (SMS vs WhatsApp vs RCS not stated; geography matters because 10DLC is US-only)
- The surface is ambiguous (API integration vs dashboard UX vs compliance paperwork)
- The user pastes a Sent dashboard URL or API path without further context

Do **not** use when:
- The user has already named one supported operation or specialist workflow; invoke that skill directly.
- The question is purely about pricing, contracts, or unsupported product policy; point the user to `https://docs.sent.dm` or Sent support.

## Routing rules

### MCP-backed operations

| User intent | Target skill |
|---|---|
| Preview or send a templated message; inspect one message and its activity | `sent-messaging` |
| List, inspect, create, summarize, or delete Sent contacts | `sent-contacts` |
| Find, inspect, or delete existing Sent templates | `sent-templates` |
| Query dashboard messaging metrics or look up number capabilities | `sent-analytics` |
| Check the selected account, balance, onboarding state, or readiness to send | `sent-account-readiness` |

### Specialist guidance

| User intent | Target skill |
|---|---|
| SMS compliance, 10DLC, brand or campaign registration, TCR vetting, or carrier rejects | `sms-10dlc-registration` |
| Authoring WhatsApp template content, choosing a category, or fixing a Meta rejection | `waba-template-author` |
| Connecting a WABA through Embedded Signup, callbacks, token exchange, or phone-number mapping | `waba-embedded-signup` |
| Launching RCS, preparing an RBM agent, or deciding capabilities and fallback | `rcs-agent-onboarding` |
| Designing multi-tenant Sender Profile boundaries, routing, or rate-limit ownership | `sender-profile-architect` |
| Diagnosing delivery from MDR exports, funnels, cohorts, or cross-channel failure codes | `messaging-performance-analyzer` |
| Designing or auditing a tenant-facing template-builder UI | `template-builder-ui` |

If the request matches one row cleanly, invoke that skill and stop. If it spans several rows, state the proposed order and begin with the prerequisite. For example, check `sent-account-readiness` before a live send, use `sent-templates` to locate an existing template before `sent-messaging`, and use `messaging-performance-analyzer` when the user provides an export rather than asking for live dashboard metrics.

## Clarifying questions to ask before routing

Ask only what's needed to pick a lane. Stop as soon as the channel + workflow are unambiguous.

1. **Channel** — SMS, WhatsApp, RCS, or unsure?
2. **Workflow stage** — fresh setup, in the middle of integration, or debugging something that was working?
3. **Geography** — US only, international, or both? (Matters for SMS — 10DLC / TCR is US-only.)
4. **Surface** — live account operation, API/backend integration, dashboard UX, or compliance paperwork?
5. **Audience** — are you an end-tenant of Sent, or are you building the multi-tenant Sent platform itself? (Sender Profile vs single-tenant onboarding.)
6. **Symptom** (if debugging) — error code, rejection reason, low vetting score, or pure delivery-rate drop?
7. **Artifact in hand** — do you have a contact, template or message ID, template draft, MDR export, RBM agent ID, or `config_id`?

One question per turn is fine; never fire all seven at once.

## When to handle without routing

This skill is not a fallback for general questions. If the user asks about:
- **Balance, onboarding state, or whether the selected account can send** — use `sent-account-readiness`.
- **Contracts, plan pricing, invoices, or account access that the available operations cannot answer** — direct them to Sent support or `https://docs.sent.dm`.
- **Generic engineering** such as retries, queueing, or observability with no Sent-specific work — answer normally.
- **Meta, Google, TCR, or carrier policy outside a specialist skill's scope** — use current upstream documentation.

If after the clarifying questions the request still doesn't fit any target skill, say so plainly. Don't force a route.

## Shared terminology

Read `references/sent-glossary.md` when a routing decision depends on Sent, SMS, WhatsApp, RCS, or MCP terminology. Keep operational details in the target skill rather than duplicating them here.
