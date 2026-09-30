# SEO delivery gates

Use this reference when SEO work includes implementation, review, release, or regression repair.

## 1. Intake

Define the user problem, target audience, affected URLs or templates, intended indexability, languages, evidence, scope, and authorization boundary.

## 2. Impact design

Consider status codes, title, description, primary heading, canonical, robots, sitemap, hreflang, structured data, main content, internal links, images, performance, accessibility, analytics, advertising, privacy, and URL retirement. Record applicable and non-applicable areas.

Plan both expected and failure paths before implementation. As applicable, cover normal, boundary, empty, malformed, malicious, oversized, unauthorized, dependency-failure, partial-success, retry, concurrency, compatibility, and rollback cases. For every material branch record the precondition, input or action, expected result, and validation layer. Map each branch to source, unit, integration, artifact, browser, candidate, production, or external verification.

## 3. Implementation

Make the smallest coherent change in the project's canonical source. Do not create keyword variants, doorway pages, fake freshness, fabricated entities, or unsupported claims. Repair the affected class when evidence shows a systemic defect.

## 4. Automated verification

Run the project's relevant checks. A failed applicable gate returns to root-cause repair and a complete relevant rerun. Do not pass by deleting tests, lowering thresholds, fixed failure allowlists, or historical-score exemptions.

## 5. Independent review

Review the actual content and rendered result for user value, facts, sources, language quality, privacy, accessibility, policy conflicts, and unexpected data flows. Automated scores do not replace this review.

## 6. Candidate and release

Enter this stage only when candidate creation or release is separately authorized. Freeze a versioned candidate, record its identity, and identify the rollback point. Verify the same SEO contract on the candidate that will reach production. Implementation authorization alone stops before this stage.

## 7. Production verification

Use read-only checks unless production writes are explicitly authorized. Verify the public status, preferred URL, rendered content, indexability, metadata, language relationships, structured data, internal discovery, performance risk, and allowed network behavior. Roll back only when rollback is separately authorized and the project defines it as the safe response.

## 8. Monitoring

Separate immediate engineering success from delayed crawler, indexing, ranking, traffic, rich-result, advertising, or AI-system outcomes. Record those as pending until verified by the appropriate source.

## 9. Knowledge and evidence

Synchronize the project's real rule, task, capability, environment, third-party, and release evidence owners when the change affects them. Do not leave the only reusable rule in a temporary report or task note. Before deleting temporary work, confirm that future maintainers can continue from the authoritative project sources without it.
