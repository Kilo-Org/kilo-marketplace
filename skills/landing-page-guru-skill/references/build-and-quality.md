# Build and quality

Inspect the repository's scripts, components, routes, CSS, and conventions first.
Preserve the existing framework and package manager. A new simple static landing
page can be plain HTML/CSS/JS; interactivity does not automatically require a new
application framework.

## Implementation

Use semantic landmarks, a coherent heading structure, links for navigation,
buttons for actions, visible labels, and stable IDs. Provide complete responsive
states, not just a hero screenshot. Use native controls where they serve the task.
Avoid unnecessary dependencies, client-side rendering, or third-party scripts.

Keep content and behavior usable if a decorative asset or optional script fails.
If a form requires JavaScript, make that dependency honest and prevent fallback
navigation from exposing fields in a URL. Follow the forms reference for requests.

## Verify in layers

| Layer | Evidence to collect |
| --- | --- |
| Build | Existing lint/type/build tests where relevant; no missing imports/assets |
| Structure | Valid links, labels, unique IDs, heading order, meaningful metadata |
| Browser | Actual primary journey, errors, focus movement, back/reload behavior |
| Responsive | Desktop/mobile screenshots, no unintended horizontal overflow |
| Accessibility | Automated findings plus keyboard, focus, zoom, and feedback checks |
| Performance | Reproducible lab conditions, payloads, layout movement, image loading |
| Operations | Distinguish intercepted frontend checks from real backend/delivery tests |

Run the smallest meaningful set for the change. A headline edit needs no browser
automation suite unless its size or placement threatens layout. A changed form
needs its failure and success states exercised. Do not list checks you did not run.

## Performance and search

Use LCP, INP, and CLS as relevant field measures; current good thresholds are
LCP ≤ 2.5s, INP ≤ 200ms, and CLS ≤ 0.1 at the 75th percentile. Lab results help
diagnose but do not substitute for real visitor distributions. Record conditions
and use current [Web Vitals guidance](https://web.dev/articles/vitals).

Decide whether the page should be indexed. Public information pages generally
need descriptive title/description, crawlable content and links, correct canonical
URL when known, and a useful sharing preview. Private previews and fictional demos
can be noindex. Do not invent a canonical production URL before deployment.

Use structured data only for supported, visible, accurate content and current
eligibility. Do not promise a rich result, an AI citation, or a ranking increase.
For translated variants, verify actual language URLs and alternates; don't create
bulk near-duplicate location pages as a default growth tactic. Consult current
[Google guidance](https://developers.google.com/search/docs/fundamentals/seo-starter-guide).

## Handoff

Report changed files/URL, checks and their evidence, connected/unconnected status,
known limitations, and the next required configuration. Keep deployment within
the user's authorization and follow the selected platform's current publish flow.
