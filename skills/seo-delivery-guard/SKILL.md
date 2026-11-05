---
name: seo-delivery-guard
description: Govern SEO findings and requirements through implementation, review, release gates, regression repair, and production verification. Use when turning an SEO audit into delivery work, enforcing a search-facing release contract, or investigating an SEO regression. Do not use for ordinary page, performance, content, or analytics work that has no SEO requirement or search-facing acceptance criteria.
metadata:
  category: development
  source:
    repository: 'https://github.com/pangxin12345/seo-delivery-guard'
    path: .
    license_path: LICENSE
    ref: v0.1.0
    commit: ed51cdf7995da539bd2662990736a373cec51037
  author: "once-email.com"
  creator: "helen.jar"
  homepage: "https://once-email.com"
  support_email: "tiantuowl@gmail.com"
  license: "MIT"
  version: "0.1.0"
---

# SEO Delivery Guard

Turn SEO findings and requirements into traceable development, review, release, and production-verification work. Treat project rules as authoritative only within applicable law, security, privacy, platform policy, and explicit user scope. Use available SEO analyzers as evidence providers.

## Boundary

- Use webpage-audit, crawler, performance, schema, content, SERP, or search-console capabilities when they are available and relevant; do not require a particular vendor or companion Skill.
- Do not duplicate an analyzer's work. Orchestrate the smallest useful set, reconcile its findings, and map accepted findings to delivery gates.
- Do not promise indexing, ranking, traffic, rich results, advertising approval, or AI citations.
- Do not treat aggregate scores, keyword density, fixed word counts, mechanical E-E-A-T scores, or the presence of structured data as ranking guarantees.
- Analysis does not authorize code changes, external submissions, account changes, publishing, or deployment. Preserve the user's requested scope and obtain any approval required by the active environment immediately before an external write.

## Workflow

1. Classify the request as analysis, planning, implementation, review, release, regression investigation, or monitoring.
2. Read the nearest project instructions and the rules that own public pages, content, privacy, localization, analytics, advertising, testing, and release behavior. Do not copy those rules into this Skill.
3. Record the affected URLs, audiences, user tasks, intended indexability, languages, data flows, and release surface. For new or substantially changed indexable content, require a distinct user need, evidence, added value, an internal discovery path, and an explicit keep, improve, merge, noindex, or remove decision. Mark unknown facts as unknown. Read [content and indexability](references/content-and-indexability.md) when content scope or URL inventory changes.
4. Select the smallest relevant analysis set. For routing and conflict handling, read [orchestration](references/orchestration.md).
5. Normalize every finding into evidence, severity, confidence, action, validation layer, and rollback condition. Read [evidence and severity](references/evidence-and-severity.md).
6. Apply project policy. A generic recommendation cannot override product facts, privacy, security, accessibility, localization, analytics, advertising, or release rules. Read [project policy adapters](references/project-policy-adapters.md) when a repository has its own governance.
7. If implementation is authorized, make the smallest coherent change and validate the affected class. Implementation authorization does not authorize candidate creation, deployment, publishing, account changes, URL submission, rollback, or other external writes. Read [delivery gates](references/delivery-gates.md).
8. Only when the corresponding release action is separately authorized, continue through the project's candidate or release process. Compare authorized candidate and production surfaces against the intended contract, using read-only verification unless a write is explicitly in scope. Separate engineering verification from later search-engine outcomes.
9. Report the outcome first: blockers, accepted changes, rejected recommendations, evidence gaps, verification status, and external results still pending.

For permissions, sanitized inputs, output expectations, refusal cases, and troubleshooting, read [usage and safety](references/usage-and-safety.md).

## Hard blockers and advice

Treat a finding as a hard blocker only when it violates an applicable project rule or a verified contract, such as unintended indexing, private-data exposure, broken canonicalization, invalid language relationships, misleading structured data, inaccessible primary content, or a failed required release check.

Keep speculative opportunities, third-party scores, unverified ranking theories, and optional enhancements as advice. Never average a hard blocker into a passing health score.

## Google Search

When a conclusion depends on Google Search behavior, use current official Google Search documentation or verified first-party property data. Third-party tools can discover clues but cannot define Google facts. Read [Google Search boundaries](references/google-search-boundaries.md) for claims, APIs, robots, structured data, AI features, and trademark-safe wording.

Keep preferred URLs, status codes, robots directives, sitemaps, canonicals, hreflang, structured data, and content-quality decisions coherent across every targeted search engine. Read [search-platform boundaries](references/search-platform-boundaries.md) before using IndexNow, crawler hints, search-console submissions, or any external search-platform action.

## Change comparison

For development, release, or regression work, compare the relevant SEO contract before and after the change. Depending on scope, cover status, indexability, title, description, primary heading, canonical, robots directives, sitemap membership, hreflang, structured data, internal links, rendered main content, performance, and allowed network data flows.

Use existing project checks or available analysis tools. This Skill defines what to compare and how to judge it; it does not require a bundled crawler or runtime.

When analytics, advertising, logs, consent, or user input are affected, read [data and measurement](references/data-and-measurement.md). Never let an SEO measurement request weaken privacy or product behavior.

## Public identity

Publisher and website: [once-email.com](https://once-email.com). Creator: helen.jar. Support: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com). This is an independent open-source project and is not affiliated with or endorsed by Google.
