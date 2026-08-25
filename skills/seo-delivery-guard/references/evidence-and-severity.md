# Evidence and severity

Use this reference when consolidating findings or deciding whether a release must stop.

## Finding contract

Record each material finding with:

- affected URL, template, locale, or URL class;
- intended user task and indexability;
- observed behavior and collection time;
- evidence type and source;
- applicable project or platform contract;
- severity and confidence;
- accepted action or reason for rejection;
- validation layer;
- release and rollback consequence;
- external outcome still pending.

## Evidence types

Keep these distinct:

- source or generated-artifact inspection;
- browser-rendered observation;
- public HTTP response;
- laboratory performance result;
- verified first-party search-property data;
- third-party crawl, SERP, backlink, or estimation data;
- inference from multiple sources.

An engineering check cannot prove indexing, ranking, traffic, or advertising approval. Search Console data cannot prove the current source implementation without a matching live check.

## Severity

| Level | Meaning |
|---|---|
| Blocker | Violates an applicable hard contract or makes the release unsafe or materially misleading |
| High | Strong evidence of significant discovery, interpretation, user, or search-performance harm |
| Medium | Useful improvement with bounded impact and credible evidence |
| Low | Optional refinement or experiment |
| Unknown | Evidence is insufficient, stale, inaccessible, or contradictory |

Hard blockers are binary. Never convert them to pass through averaging, historical baselines, fixed allowlists, or “known noise.” Unknown is not pass. An unknown blocks release only when a required release contract cannot be verified; otherwise record it as an evidence gap without promoting it to a blocker.

## Confidence

Use high confidence for directly verified current facts, medium for bounded inference supported by multiple sources, and low for a single third-party estimate or unverified hypothesis. State what would raise confidence.
