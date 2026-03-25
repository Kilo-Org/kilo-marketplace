---
name: theme-factory
description: "Applies professional color-palette and font-pairing themes to slides, docs, reports, and HTML pages from 10 built-in presets or a custom-generated theme. Use when styling an artifact with a consistent visual identity or generating a new theme on the fly."
license: Complete terms in LICENSE.txt
metadata:
  category: creative-media
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: theme-factory
    license_path: theme-factory/LICENSE.txt
---

## When to Use

- Applying a cohesive color palette and fonts to a slide deck, document, report, or HTML page
- Browsing available themes to pick a visual direction
- Generating a brand-new custom theme when presets do not fit
- Re-theming an existing artifact with a different look

## Workflow

1. **Present options** — Display `theme-showcase.pdf` so the user can see all 10 themes visually. Do not modify this file.
2. **Confirm selection** — Ask which theme to apply; wait for explicit confirmation.
3. **Load theme spec** — Read the chosen theme file from the `themes/` directory (hex palette + font pairings).
4. **Apply** — Set colors and fonts consistently across the entire artifact, ensuring contrast and readability.

### Custom Theme Path

If no preset fits:
1. Gather a brief description of the desired mood or brand.
2. Generate a new theme (palette + fonts) following the same format as built-in themes.
3. Show the generated theme for review before applying.

## Available Themes

| # | Theme | Mood |
|---|---|---|
| 1 | Ocean Depths | Professional, calming maritime |
| 2 | Sunset Boulevard | Warm, vibrant sunset |
| 3 | Forest Canopy | Natural, grounded earth tones |
| 4 | Modern Minimalist | Clean, contemporary grayscale |
| 5 | Golden Hour | Rich, warm autumnal |
| 6 | Arctic Frost | Cool, crisp winter |
| 7 | Desert Rose | Soft, sophisticated dusty tones |
| 8 | Tech Innovation | Bold, modern tech |
| 9 | Botanical Garden | Fresh, organic garden |
| 10 | Midnight Galaxy | Dramatic, cosmic deep tones |

Each theme includes hex color codes, header/body font pairings, and a distinct visual identity. Full specs live in the `themes/` directory.

## Example

**Prompt:** "Apply the Arctic Frost theme to my quarterly report deck"

**Steps taken:**
1. Showed `theme-showcase.pdf` — user confirmed Arctic Frost.
2. Loaded `themes/arctic-frost` spec (palette: #E8F1F8, #1B3A4B, #5BA4CF; fonts: Inter / Source Serif Pro).
3. Applied colors and fonts across all slides, verified contrast ratios.

## Tips

- Mention the artifact type (slides, HTML, doc) so theme application targets the right format.
- For branded work, provide brand hex codes and the skill generates a matching custom theme.
- Themes maintain proper contrast — accessibility is checked during application.
