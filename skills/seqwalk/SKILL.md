---
name: seqwalk
description: >-
  Create or update self-contained interactive HTML sequence diagrams that help
  humans understand and review code execution flows, especially AI-written or
  AI-modified code. Use when asked to inspect code flow, explain what calls
  what, visualize data movement, review AI-generated code, create architecture
  walkthroughs, or generate browser-validated HTML sequence diagrams with sticky
  participants and aligned message lines.
license: MIT
metadata:
  category: development
  author: reason211
  version: 0.1.2
  source:
    repository: 'https://github.com/reason211/seqwalk'
    path: skills/seqwalk
    ref: main
    commit: 191ea17698156c263d707986d7435c275c1e54f5
---

# SeqWalk

SeqWalk creates browser-validated interactive HTML sequence diagrams that help humans understand code execution flow. The output should behave like a real sequence diagram: participants stay sticky, lifelines align to participant centers, message lines connect exact lifeline centers, and interaction highlights remain first-degree and understandable.

Use the bundled scaffold at `assets/strict-sequence-viewer-template.html` when starting from scratch. For an existing artifact, update it in place while preserving its data model and visual system unless the user asks for a redesign.

## Core Requirements

1. Define an ordered `actors` list with stable `id`, `label`, `sub`, `kind`, and `color`.
2. Render the sticky participant rail from that actor list.
3. Render the lifeline layer from the same actor list and inside the same measured container width.
4. Mark every message line with explicit `data-from="<actor-id>"` and `data-to="<actor-id>"`.
5. Give every event card a stable `data-card-id` and explicit `data-actors`.
6. Use compact sequence prefixes such as `A1`, `A2`, `B1`, or `C1` when the diagram has multiple phases.
7. Compute message `left` and `width` from real DOM lifeline centers after layout, resize, filtering, or data changes.
8. Track the current visible step while scrolling and highlight related participants, lifelines, message lines, and cards.
9. Keep hover, focus, and click relationships first-degree only.
10. Validate the rendered page in a browser before claiming completion.

## Highlighting Model

Direct highlighting is first-degree only.

- A card highlights its own `data-actors`, exact flows in the same step whose endpoints touch those actors, and those endpoint actors. It must not highlight other cards just because they share an actor.
- A participant highlights itself, flows whose `data-from` or `data-to` is that actor, endpoint actors for those exact flows, and cards whose own `data-actors` include that actor. It must not recursively expand through those cards' other actors.
- A clicked card or participant uses the same visual scope as hover/focus, then holds it until toggled off.
- Avoid broad selectors such as `.step.locked .flow` or `.step.related .flow`; they light unrelated same-row lines. Apply `.flow.related` and `.flow.locked` only to exact direct flows.
- Locked flows should preserve the colored related-line treatment. Do not turn them into white card-like objects.

Highlight layer priority, low to high:

1. Scroll-window highlight
2. Clicked card
3. Clicked participant
4. Store/cache highlight

## Alignment Rules

Never rely on CSS grid spans alone for message-line endpoints. CSS grid may place cards and rails, but message line endpoints must come from measured lifeline centers.

Validation targets:

```js
maxActorToLifelineDelta <= 1
maxMessageEndpointDelta <= 1
```

For strict alignment requests, treat `0px` as the target and investigate any non-zero delta.

## Store And Cache Emphasis

Store/cache highlighting is semantic, not just dimming.

When a user asks to highlight stores, caches, databases, queues, files, persistence layers, audit logs, or result stores:

- mark store-like actors with `kind: "store"` or a domain-specific equivalent;
- add `store-related` to steps whose actors or messages touch a store actor;
- highlight store participant cards;
- highlight store lifelines;
- highlight store-related message lines;
- highlight store-related event cards;
- keep non-store content readable but secondary;
- keep store/cache emphasis as the highest-priority layer.

Useful store examples: `Parquet cache`, `Redis`, `Postgres`, `S3`, `JSON job queue`, `results store`, `audit log`, `browser cache`, `in-memory store`.

## Labels And Cards

Flow labels must be complete and readable.

- Do not use ellipsis or truncation on message labels.
- Prefer `min-width: max-content`, `white-space: nowrap`, `overflow: visible`, and `text-overflow: clip`.
- Position labels separately from line endpoints. Label placement may change `--label-left` and `--label-top`, but must not change measured message `left` or `width`.
- Test label collisions against cards, endpoint dots, and sibling labels in the same step.
- Use alternate vertical slots such as above, below, higher above, and lower below.
- Use placement variables such as `--at`, `--span`, `--card-y`, `--card-x`, and `--card-width` for card nudges.
- Avoid negative card offsets unless the user explicitly wants rows to overlap.

## Visible Copy

Write visible text like a product walkthrough, not an implementation memo.

- Prefer "user action + data source + visible result" for cards and message labels.
- Avoid exposing internal terms such as `payload`, `surface`, `miss`, `switching`, `AbortController`, `DataSource`, `resultId`, or `candidateHash` unless required for code lookup.
- If a technical name must remain, pair it with plain language.
- Match the user's language for controls and side panels.
- Remove filters or controls that do not materially improve comprehension.

## Workflow

### Create A New Diagram

1. Copy `assets/strict-sequence-viewer-template.html` to the requested output path.
2. Replace sample actors with the user's real actors.
3. Replace sample steps, cards, and message flows with verified system behavior.
4. Keep all flows explicit with `data-from` and `data-to`.
5. Keep card `data-actors` accurate and first-degree.
6. Run browser validation.
7. Save screenshots only when the user asks for visual artifacts or when visual QA evidence is useful.

### Update An Existing Diagram

1. Read the HTML and identify actor list, steps, filters, and validation helpers.
2. Read the source code or docs that define current system behavior. Do not invent architecture.
3. Update actors first, then messages, then cards and labels.
4. Preserve or add group sequence numbers when multiple chains exist.
5. Recompute lifelines and explicit message lines.
6. Recheck first-degree hover/click semantics.
7. Recheck store/cache semantics when relevant.
8. Audit rendered visible copy in the browser with `document.body.innerText`.
9. Run browser validation.

## Browser Validation

Use a local static server when direct `file://` access is blocked:

```bash
python -m http.server 8765 --bind 127.0.0.1 -d <directory-containing-html>
```

Check at least:

- one desktop viewport such as `1440x900`;
- one narrower viewport such as `1280x800`;
- no console errors;
- sticky participant rail position after scrolling;
- actor center to lifeline center max delta;
- message endpoint to lifeline center max delta;
- label readability and collision checks;
- card hover/focus first-degree related actors, lifelines, and flows;
- card click lock and unrelated-content dimming;
- participant hover/click first-degree highlighting;
- locked flow lines keep their colored related state;
- store/cache highlight mode when stores exist;
- filter or navigation interaction when present;
- visible text contains no implementation-first terms inappropriate for the target reader.

Useful validation snippets:

```js
[...document.querySelectorAll(".actor")].map(actor => {
  const id = actor.dataset.actor;
  const a = actor.getBoundingClientRect();
  const line = document.querySelector(`.lifeline[data-actor="${id}"] .lifeline-line`).getBoundingClientRect();
  return Math.abs((line.left + line.width / 2) - (a.left + a.width / 2));
});
```

```js
[...document.querySelectorAll(".flow")].map(flow => {
  const center = id => {
    const line = document.querySelector(`.lifeline[data-actor="${id}"] .lifeline-line`).getBoundingClientRect();
    return line.left + line.width / 2;
  };
  const rect = flow.getBoundingClientRect();
  const a = center(flow.dataset.from);
  const b = center(flow.dataset.to);
  return {
    step: flow.closest(".step")?.id,
    deltaLeft: Math.abs(Math.min(a, b) - rect.left),
    deltaRight: Math.abs(Math.max(a, b) - rect.right)
  };
});
```

Report checked viewport sizes and maximum deltas in the final response.
