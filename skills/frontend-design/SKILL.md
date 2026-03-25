---
name: frontend-design
description: "Creates distinctive, production-grade frontend interfaces with high design quality that avoids generic AI aesthetics. Generates working HTML/CSS/JS, React, or Vue code with bold typography, intentional color palettes, motion, and spatial composition. Use when building web components, landing pages, dashboards, posters, or styling any web UI."
license: Complete terms in LICENSE.txt
metadata:
  category: development
  source:
    repository: 'https://github.com/anthropics/skills'
    path: skills/frontend-design
    license_path: skills/frontend-design/LICENSE.txt
---

# Frontend Design

Generates distinctive, production-grade frontend interfaces with working code (HTML/CSS/JS, React, Vue, etc.) and exceptional visual design. Every output must avoid generic "AI slop" aesthetics and commit to a clear, intentional creative direction.

## Design Thinking (Before Coding)

Before writing any code, establish:

1. **Purpose**: What problem does this interface solve? Who uses it?
2. **Aesthetic direction**: Commit to a bold direction — brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, industrial/utilitarian, etc.
3. **Constraints**: Framework, performance, accessibility requirements.
4. **Differentiator**: What single element makes this unforgettable?

**Key principle**: Bold maximalism and refined minimalism both work. The key is intentionality, not intensity. Match implementation complexity to the vision.

## Aesthetics Checklist

| Element | Do | Avoid |
|---------|-----|-------|
| **Typography** | Distinctive display + refined body font pairing | Arial, Inter, Roboto, system fonts |
| **Color** | Dominant colors with sharp accents via CSS variables | Purple gradients on white, timid evenly-distributed palettes |
| **Motion** | High-impact moments: staggered page-load reveals, scroll-triggered animations, surprising hover states. Prefer CSS-only for HTML; use Motion library for React | Scattered micro-interactions with no cohesion |
| **Layout** | Asymmetry, overlap, diagonal flow, grid-breaking elements, generous negative space OR controlled density | Predictable centered layouts, cookie-cutter patterns |
| **Backgrounds** | Gradient meshes, noise textures, geometric patterns, layered transparencies, grain overlays, dramatic shadows | Flat solid colors with no atmosphere |

## Implementation Rules

- Output must be production-grade and functional
- Visually striking and cohesive with a clear aesthetic point-of-view
- Never converge on the same font (e.g., Space Grotesk) across generations — vary choices
- Vary between light and dark themes across different outputs
- Maximalist designs need elaborate animations and effects; minimalist designs need precise spacing and subtle details
