---
name: canvas-design
description: "Creates original visual art as .png or .pdf by first generating a design philosophy manifesto, then expressing it on canvas with museum-quality craftsmanship. Use when the user asks to create a poster, piece of art, visual design, or other static visual piece."
license: Complete terms in LICENSE.txt
metadata:
  category: creative-media
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: canvas-design
    license_path: canvas-design/LICENSE.txt
---

## When to Use

- Creating a poster, art print, visual composition, or static design piece
- Generating an original design philosophy and then expressing it visually
- Producing museum/magazine-quality single-page or multi-page visual artifacts
- Styling visual work with custom fonts from the `./canvas-fonts` directory

**Outputs:** `.md` (philosophy), `.pdf` or `.png` (canvas). Never copy existing artists' work.

## Workflow

### Step 1 — Design Philosophy (.md)

Create a visual philosophy (an aesthetic manifesto), not a layout or template. The user's input is a foundation, not a constraint — it should not limit creative freedom.

1. **Name the movement** (1-2 words): e.g. "Brutalist Joy", "Chromatic Silence", "Metabolist Dreams"
2. **Articulate the philosophy** (4-6 paragraphs) covering how the aesthetic manifests through:
   - Space and form
   - Color and material
   - Scale, rhythm, composition, and balance
   - Visual hierarchy
3. **Guidelines:**
   - Each design aspect mentioned once — no redundancy.
   - Repeatedly emphasize master-level craftsmanship: "meticulously crafted," "painstaking attention," "the product of deep expertise."
   - Leave creative room for the canvas phase.
   - Keep the philosophy generic (reusable) — no mention of the specific art's intent.
   - Text in the final work is always sparse, essential-only, integrated as a visual element.

Output the philosophy as a `.md` file.

<details>
<summary>Philosophy examples (condensed)</summary>

**"Concrete Poetry"** — Communication through monumental form and bold geometry. Massive color blocks, sculptural typography, Brutalist spatial divisions. Text as rare, powerful gesture.

**"Chromatic Language"** — Color as the primary information system. Geometric precision, minimal sans-serif labels, Josef Albers meets data visualization.

**"Analog Meditation"** — Quiet contemplation through texture and breathing room. Paper grain, ink bleeds, vast negative space, Japanese photobook aesthetic.

**"Organic Systems"** — Natural clustering and modular growth. Rounded forms, organic arrangements, nature-through-architecture color.

**"Geometric Silence"** — Pure order and restraint. Grid-based precision, dramatic negative space, Swiss formalism meets Brutalist material honesty.

*Actual philosophies should be 4-6 substantial paragraphs.*
</details>

### Step 2 — Deduce the Subtle Reference

Before creating the canvas, identify the subtle conceptual thread from the original request. The topic is a niche reference embedded within the art — not literal, always sophisticated. Those familiar with the subject feel it intuitively; others simply experience a masterful composition. Think of a jazz musician quoting another song: only insiders catch it, but everyone appreciates the music.

### Step 3 — Canvas Creation (.pdf / .png)

With philosophy and conceptual framework established, create the visual artifact:

- **Quality bar:** Museum or magazine quality. Every element — composition, spacing, color, typography — must demonstrate expert-level craftsmanship. The work should look like it took countless hours by someone at the top of their field.
- **Visual language:** Repeating patterns, perfect shapes, dense accumulation of marks, layered patterns that reward sustained viewing. Sparse clinical typography and systematic reference markers. Limited, intentional color palette.
- **Text treatment:** Minimal and visual-first. Context guides scale — a punk poster uses bolder type than a ceramics identity. Search `./canvas-fonts` for fonts. Make typography part of the art itself. All elements must stay within canvas boundaries with proper margins; nothing overlaps. Breathing room and clear separation are non-negotiable.
- **Sophistication is non-negotiable** regardless of subject matter (movie, game, book — always art, never cartoony).
- **Output:** Single-page .pdf or .png (unless more pages requested), plus the .md philosophy file.

### Step 4 — Refinement Pass

Automatically take a second pass. Do not add more graphics — instead refine what exists. Ask: "How can I make what is already here more cohesive and pristine?" Polish spacing, alignment, color consistency, and typographic precision until museum-ready.

### Multi-Page Option

When additional pages are requested, create distinct variations on the same philosophy. Bundle in one .pdf or multiple .pngs. Treat each page as part of a coffee table book — unique twists that tell a story. Exercise full creative freedom.
