# Design system

Presets consumed by `scripts/build_deck.py` and usable by hand-written slides. Each preset
defines a palette, fonts, a type scale, and grid metrics. Keep to one preset per deck.

## Canvas and grid

- **16:9** (default): 13.333in × 7.5in (12192000 × 6858000 EMU).
- **4:3**: 10in × 7.5in.
- Margin: 0.6in on all sides. Content width = canvas width − 2 × margin.
- Title baseline: top 0.5in; body starts 1.6in from top.
- Footer (page number / deck title): 0.35in from bottom. Rendered on every slide with the
caption font and the muted (or band) color.

## Type scale (points)

| Role | 16:9 | 4:3 | Weight |
|---|---|---|---|
| Deck title | 40 | 36 | Bold |
| Slide title | 30 | 28 | Bold |
| Section header | 34 | 30 | Bold |
| Body / bullets | 18 | 16 | Regular |
| Caption / footer | 12 | 12 | Regular |
| Quote | 26 | 24 | Italic |

Hard floors enforced by the validator: titles ≥ 28pt, body ≥ 14pt.

## Presets

### `clean-light`

- Background: `FFFFFF`; surface/card: `F2F4F7`.
- Text: `1A1A1A`; muted: `5A6472`.
- Accent: `1F6FEB` (primary), `0E9F6E` (positive), `D9381E` (negative).
- Fonts: title **Segoe UI Semibold**, body **Segoe UI** (fallbacks: Calibri, Arial).
- Use for: general business, docs, teaching.

### `corporate-blue`

- Background: `FFFFFF`; surface/card: `E8EEF7`.
- Text: `0B1F33`; muted: `4A5A6A`.
- Accent: `0B3D91` (primary), `2E7DD1` (secondary), `C9A227` (highlight).
- Fonts: title **Calibri** bold, body **Calibri** (fallbacks: Arial, Helvetica).
- Use for: corporate decks, board updates, proposals.

### `dark-tech`

- Background: `0D1117`; surface/card: `161B22`.
- Text: `E6EDF3`; muted: `8B949E`.
- Accent: `58A6FF` (primary), `3FB950` (positive), `F85149` (negative).
- Fonts: title **Segoe UI Semibold**, body **Segoe UI** (fallbacks: Calibri, Arial).
- Use for: engineering, product, demos.

## Contrast rules

- Body text must clear WCAG AA: **4.5:1** on the background; large/title text **3:1**.
- Never place body text directly on an accent fill unless contrast is verified; use the surface
  color for text cards instead.
- The validator computes the ratio between a solid-fill background shape and its text and
  fails below the floor. If a slide fails, darken/lighten the text or the fill.

## Chart rules

- Max ~7 categories; group or drop the rest.
- One message per chart; put it in the slide title, not a legend.
- Reuse accent colors as the series palette; greys for de-emphasized series.
- Label axes and units; prefer direct value labels over a legend when ≤4 series.
- Secondary series are muted (grey) unless they carry the message.

## Tables

- Header row filled with the primary accent, text in white (verify contrast).
- Zebra-stripe Body rows with the surface color.
- ≤6 columns, ≤8 rows; anything larger becomes a separate appendix slide.


## Cards and containers

- Card corner radius: 0.05 (rounded-rectangle adjustment) for all card/container shapes.
- Card padding: 0.25in inside the shape; keep text 0.2in from edges.
- Surface color from the preset; never place body text directly on an accent fill.

## Footer

- Every slide carries a subtle footer: deck title (left) and slide number (right).
- Footer uses the caption size (12pt) and the muted color on light backgrounds, or the
  band text color on full-bleed band slides.

## Logo placement

- Default: top-right, 0.7in height, 0.35in margin from edges.
- Keep the logo on a solid or quiet area; avoid overlapping the title.
- Use `logo.position` (`top-left`, `top-right`, `bottom-left`, `bottom-right`) and `logo.size`.
- On title slides the logo may be larger; on content slides keep it subtle.

## Footer, page numbers, and markings

- Every slide carries deck title (left) and slide number (right) by default.
- `footer.enabled`, `footer.page_numbers`, `footer.title`, `footer.confidential`, and
  `footer.mark` control the footer. `confidential: true` (top-level or footer) prints
  "CONFIDENTIAL".
- On full-bleed band slides the footer switches to the band text color.

## Fonts and fallbacks

- `fonts.title` / `fonts.body` set the primary font names.
- `fonts.title_fallbacks` / `fonts.body_fallbacks` (or a list value for `title_font`) define
  the fallback chain used when the primary font is unavailable.
- `font_files` validates that custom font files exist; python-pptx cannot embed fonts, so the
  font must be installed on the rendering machine. Document this requirement in delivery.
