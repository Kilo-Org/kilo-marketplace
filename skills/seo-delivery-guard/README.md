# SEO Delivery Guard

**Google Search–aligned SEO development and release governance for AI coding agents.**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](SKILL.md)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](LICENSE)
[![Documentation languages: 10](https://img.shields.io/badge/docs-10%20languages-7c3aed)](#documentation)
[![GitHub source](https://img.shields.io/badge/GitHub-pangxin12345%2Fseo--delivery--guard-181717?logo=github&logoColor=white)](https://github.com/pangxin12345/seo-delivery-guard)
[![Official website](https://img.shields.io/badge/website-once--email.com-0f766e?logo=googlechrome&logoColor=white)](https://once-email.com)
[![skills.sh](https://skills.sh/b/pangxin12345/seo-delivery-guard)](https://skills.sh/pangxin12345/seo-delivery-guard)

[English](README.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md) · [Português do Brasil](docs/README.pt-BR.md) · [Deutsch](docs/README.de.md) · [Français](docs/README.fr.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Bahasa Indonesia](docs/README.id.md) · [Tiếng Việt](docs/README.vi.md)

SEO audits find problems. **SEO Delivery Guard helps an AI coding agent carry accepted findings through implementation, review, release, and production verification.**

It does not replace crawlers, performance tools, content analyzers, schema validators, SERP research, or search-console data. It orchestrates the capabilities already available, applies the project's own rules, separates release blockers from optional advice, and keeps delayed search-engine outcomes distinct from engineering proof.

## Why this Skill exists

A technically correct recommendation can still fail during delivery:

- a canonical is fixed in source but wrong in the generated site;
- a translated page enters a sitemap before professional review;
- structured data describes facts users cannot see;
- a crawler directive is mistaken for access control;
- a passing health score hides an indexing or privacy blocker;
- a candidate passes, but production serves different metadata;
- a release is declared successful before a search engine recrawls it.

SEO Delivery Guard closes that gap. It gives AI agents a portable governance workflow for **SEO development, SEO CI/CD, SEO regression review, release gates, and production verification**.

## What it does

- Routes each change to the smallest relevant SEO analysis set.
- Reads project-specific development, privacy, localization, analytics, advertising, testing, and release rules.
- Reconciles conflicting recommendations using an explicit authority order.
- Records evidence source, collection time, confidence, severity, action, validation layer, and rollback consequence.
- Keeps hard blockers binary instead of averaging them into an SEO score.
- Compares the relevant search-facing contract before and after a change.
- Separates source, generated artifact, browser, public HTTP, laboratory, first-party search data, and third-party estimates.
- Turns accepted findings into implementation and verification work without expanding the user's authorization.
- Preserves external outcomes—indexing, ranking, traffic, rich results, advertising review, and AI visibility—as pending until verified.
- Requires an explicit keep, improve, merge, noindex, or remove decision when content or URL inventory changes.
- Uses a permanent redirect only for a real equivalent; otherwise preserves honest `404` or `410` semantics instead of soft redirects.

## What it does not do

- It is not another website crawler or all-in-one SEO audit.
- It does not require a specific SEO vendor, API, MCP server, or companion Skill.
- It does not submit URLs, change search-console properties, publish code, or deploy without task authority.
- It does not promise rankings, indexing, traffic, rich results, advertising approval, or AI citations.
- It does not use keyword density, fixed word counts, mechanical E-E-A-T scores, or schema quantity as ranking guarantees.

## How it works

```text
Change request or SEO finding
            ↓
Discover project rules and intended indexability
            ↓
Select available page, technical, content, schema,
performance, international, SERP, or search-data analysis
            ↓
Normalize and reconcile evidence
            ↓
Apply project policy and separate blockers from advice
            ↓
Map accepted findings to implementation and validation
            ↓
Verify candidate and production behavior
            ↓
Monitor delayed search outcomes without inventing success
```

## Example requests

```text
Use SEO Delivery Guard to review this landing-page change before implementation.

Turn this technical SEO audit into a traceable development and release plan.

Check whether this multilingual release can ship, including canonical,
sitemap, hreflang, structured data, privacy, and production verification.

Investigate the SEO regression after this deployment and distinguish
engineering defects from search-engine refresh delays.
```

## Inputs and outputs

Provide only the minimum useful combination of a public URL, repository path, intended change, target audience, intended indexability, locales, audit findings, and sanitized evidence. Do not provide credentials, cookies, private keys, complete analytics exports, private messages, or sensitive user data.

The Skill returns applicable rules, blockers, advice, unknowns, rejected recommendations, evidence dates and limitations, accepted actions, validation layers, release consequences, production status, and delayed external outcomes. It does not expose complete secrets or sensitive source material in its report.

## Content and URL lifecycle

Every new indexable page should serve a distinct user task that the strongest existing page cannot satisfy. Search volume, keyword coverage, advertising inventory, page count, and AI-generation speed are not independent value.

When pages overlap or quality signals deteriorate, choose deliberately among improving the strongest URL, merging equivalent value, keeping a useful page `noindex`, or removing it. Redirect a retired URL only to a real equivalent; otherwise preserve honest `404/410` semantics. Never use wildcard homepage redirects or restore doorway pages merely to preserve keywords.

An indexable locale requires factual and professional language review. Automated checks can confirm structure and shared facts, but cannot prove translation quality. Unreviewed translations should not enter sitemaps or hreflang sets.

## Install

Install the `seo-delivery-guard` folder through a supported Skill marketplace or copy the complete folder into the Skill directory recognized by your AI agent. Start a new session or reload Skills, then invoke:

```text
$seo-delivery-guard
```

The portable public package contains only text instructions and metadata. It has no runtime dependency, API key, crawler, executable, or operating-system-specific component.

Marketplace submission, local installation, compatibility verification, review, and public publication are different states. Consult your host product's current Skill documentation for its exact installation path and reload command.

## Portable across Skill platforms

`SKILL.md` is the single behavioral source. Platform-specific metadata and archive layouts must be derived from the same frozen version without changing behavior, license, identity, or safety boundaries.

The distribution plan covers public source hosts, discovery directories, Skill marketplaces, and compatible AI-agent clients. A platform is described as published only after its public entry can be read back and the frozen package can be installed and invoked. Platforms without a verified public submission path remain candidates rather than fictional listings.

## Project policy comes first

Every repository has different product facts, privacy boundaries, localization requirements, analytics rules, and release processes. SEO Delivery Guard discovers and applies those owners instead of replacing them with a generic checklist.

When no formal project governance exists, it uses conservative defaults: coherent preferred URLs, truthful structured data, accessible primary content, protected private resources, minimal sensitive-data exposure, change-level verification, public-result checks, and a reversible release path proportional to risk.

## Refusal and troubleshooting

The Skill refuses ranking manipulation, fabricated evidence or experience, doorway pages, value-free mass content, access-control bypass, confidential-data exposure, and false search-engine certification or guarantees.

If a page or analyzer is unavailable, the missing evidence remains unknown—not passed. If candidate and production differ, production is the current user-facing fact. If search results have not refreshed, verify the engineering contract and record recrawl or reevaluation as pending instead of repeatedly rewriting the page.

## Google Search boundaries

Google-specific conclusions use current official Google Search documentation or verified first-party property data. Third-party SEO tools can provide clues, but they cannot define Google's API scope, indexing decisions, ranking factors, title links, rich results, AI features, or advertising outcomes.

SEO Delivery Guard is an independent open-source project. It is not affiliated with, certified by, sponsored by, or endorsed by Google.

## Documentation

- [Capability orchestration](references/orchestration.md)
- [Evidence and severity](references/evidence-and-severity.md)
- [Project policy adapters](references/project-policy-adapters.md)
- [SEO delivery gates](references/delivery-gates.md)
- [Google Search boundaries](references/google-search-boundaries.md)
- [Content and indexability](references/content-and-indexability.md)
- [Data and measurement](references/data-and-measurement.md)
- [Search-platform boundaries](references/search-platform-boundaries.md)
- [Usage and safety](references/usage-and-safety.md)
- [Distribution model](DISTRIBUTION.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Support](SUPPORT.md)

## Publisher

- Publisher and official website: [once-email.com](https://once-email.com)
- Creator: helen.jar
- GitHub profile: [pangxin12345](https://github.com/pangxin12345)
- Public support: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

MIT License · Version 0.1.0
