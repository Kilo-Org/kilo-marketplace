# Example: brief -> outline -> spec -> deck

A worked walkthrough of the presentation-creator workflow, using the accompanying
`example-deck.json`.

## 1. The brief

> We need a short internal deck explaining the new "Presentation Creator" skill: what it
> does, the problem it solves, how the QA gate works, and a closing call to action. About
> seven slides, clean and light, 16:9, for an engineering audience.

## 2. Clarify

Only what changes the output. Here: audience (engineering), length (~7 slides), tone
(clean/light), aspect (16:9). Nothing about brand fonts or a logo was given, so the
`clean-light` preset is assumed and stated in the delivery summary.

## 3. Outline (assertion-style headlines)

1. *Title* - Presentation Creator / Polished decks from a brief, in one pass
2. *Problem* - Decks fail on the same three things
3. *Approach* - Outline first, then generate
4. *Detail* - What the QA gate catches
5. *Evidence* - Review time drops once QA is automated
6. *Principle* - A deck is a decision aid, not a document dump
7. *Close* - Build your next deck with the skill

Each content slide gets <=5 bullets and one paragraph of speaker notes.

## 4. Theme

`clean-light`: white background, `1F6FEB` accent, Segoe UI. 16:9 canvas. See
`../references/design-system.md` for the full preset.

## 5. Spec

The outline maps directly onto `example-deck.json`:

| Slide | `layout` | Fields |
|---|---|---|
| 1 | `title` | `title`, `subtitle` (inherited from the deck) |
| 2 | `bullets` | `title`, `subtitle`, `bullets`, `notes` |
| 3 | `two_column` | `title`, `columns`, `notes` |
| 4 | `table` | `title`, `table.headers`, `table.rows`, `notes` |
| 5 | `chart` | `title`, `chart.type`, `chart.categories`, `chart.series`, `notes` |
| 6 | `quote` | `quote`, `attribution`, `notes` |
| 7 | `closing` | `title`, `subtitle`, `notes` |

For an `image` slide, add `"layout": "image", "image": "/abs/path/shot.png"` (the path must
exist locally; the skill never downloads remote images).

## 6. Build

```sh
python3 ../scripts/build_deck.py example-deck.json -o /tmp/kilo/sample.pptx
# Wrote 7 slides to /tmp/kilo/sample.pptx (theme: clean-light, 16:9)
```

## 7. QA gate

```sh
python3 ../scripts/validate_deck.py /tmp/kilo/sample.pptx
# PASSED: 0 errors, 0 warning(s)
```

Fix every error and re-run until the exit code is 0. To see the gate reject a deck, take a
copy of the spec, put a few hundred words into a single `bullets` entry, rebuild, and
validate again - it exits 1 with an `estimated text overflow` error.

## 8. Deliver

Report the output path, slide count, theme, the `clean-light` assumption, and that the QA
gate passed. A LibreOffice PDF preview is optional and skipped when `soffice` is absent.
