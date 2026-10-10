---
name: gdd-markdown-template
description: >-
  Create or scaffold a Game Design Document (GDD) in Markdown using a structured
  13-section template (Overview, Gameplay, Story, Levels, Interface, AI,
  Technical, Art, etc.). This skill should be used when the user asks for a
  game design document, GDD, game design spec, wants to draft a new game
  concept, or needs the standard section structure for documenting a game.
license: Complete terms in LICENSE.txt (upstream: TheLazyHatGuy/GDDMarkdownTemplate)
metadata:
  category: game-design
  source:
    repository: 'https://github.com/TheLazyHatGuy/GDDMarkdownTemplate'
    path: GDDMarkdownTemplate
---

# GDD Markdown Template

Provides the canonical 13-section Game Design Document markdown template (originally by Artjom Kurapov, packaged by TheLazyHatGuy) as a ready-to-fill scaffold for new game projects.

## When to use

- The user asks to create, scaffold, or draft a **Game Design Document** (GDD).
- The user wants a structured game design spec in Markdown.
- The user asks "set up a GDD for X game" / "make a game design doc" / "document my game idea".
- The user references "GDD template", "game design template", or asks to clone/scaffold the GDD structure.
- A new game project needs an initial design document before development starts.

Do NOT use for: technical design docs (TDD), postmortems, or non-game software specs.

## Template structure (13 sections)

The template defines these numbered files. Use the file naming convention exactly as shown.

| #  | File                                  | Purpose                                                        |
|----|---------------------------------------|----------------------------------------------------------------|
| 1  | `1_Copyright Information.md`          | Copyright / legal info                                         |
| 2  | `2_Version History.md`                | Revision log                                                   |
| 3  | `3_Game Overview.md`                  | Concept, feature set, genre, audience, flow, look/feel, scope  |
| 4  | `4_Gameplay and Mechanics.md`         | Gameplay, mechanics, screen flow, options, saving, cheats      |
| 5  | `5_Story, Setting and Character.md`   | Narrative, game world, characters                              |
| 6  | `6_Levels.md`                         | Per-level design (synopsis, objectives, map, walkthrough)       |
| 7  | `7_Interface.md`                      | Visual / control / audio systems                               |
| 8  | `8_Artificial Intelligence.md`        | Opponent, enemy, NPC, friendly, support AI                     |
| 9  | `9_Technical.md`                      | Target hardware, engine, network, scripting                    |
| 10 | `10_Game Art.md`                      | Concept art, style guides, characters, environments, equipment  |
| 11 | `11_Secondary Software.md`            | Editor, installer, updater                                     |
| 12 | `12_Management.md`                    | Schedule, budget, risk, localization, test plan                |
| 13 | `13_Appendices.md`                    | Asset lists (art, sound, music, voice)                         |

Two pre-built navigation files are also included:
- `_Sidebar.md` — short top-level TOC for GitHub wikis / Obsidian sidebars.
- `SmallerTableOfContents.md` — flat one-level TOC.
- `LargerHeadings/` — same 13 section files but with shallower heading nesting for projects that prefer flatter structure.

## How to scaffold a new GDD

1. **Ask clarifying questions** if the user hasn't specified a game concept: name, genre, platform, target audience, scope.
2. **Copy the template** from `assets/` into the target directory (e.g. `docs/GDD/` or `<project>/GDD/`). Keep the numbered filenames.
3. **Fill in section 3 first** (Game Overview) — Concept, Feature Set, Genre, Target Audience, Look and Feel, Project Scope (number of locations / levels / NPCs / weapons). This anchors the rest.
4. **Work outward in waves**:
   - Wave 1: Sections 1, 2, 3 (meta + concept).
   - Wave 2: Section 4 (gameplay/mechanics) and Section 5 (story/world/characters).
   - Wave 3: Sections 6, 7, 8, 9 (content + interface + AI + tech).
   - Wave 4: Sections 10, 11, 12, 13 (art pipeline, tools, management, appendices).
5. **Leave sections as `TBD` placeholders** when the user has not yet decided — do not invent details silently.
6. **Replace inline guidance comments** (lines starting with `>` in the template) with actual content, or keep them as inline prompts.
7. **Add a top-level README.md** linking to all 13 files and embedding `_Sidebar.md`.

## Customization rules

- Preserve the numbered file naming — many tools and scripts rely on it.
- Preserve the existing heading hierarchy within each file unless the user explicitly asks to restructure.
- You may add new files (e.g. `14_Postmortem.md`) but never renumber or remove the original 13.
- For wiki-style rendering, keep the GitHub-flavored anchor links (no spaces in headings).
- For non-wiki readers (PDF, web), strip the `github.com/...` URLs from `_Sidebar.md` and replace with relative paths: `[Copyright Information](1_Copyright Information.md)`.

## Bundled assets

All template files live under `assets/`:

```
assets/
├── README.md                        # Upstream notes + full deep TOC
├── _Sidebar.md                      # Compact TOC for wikis
├── SmallerTableOfContents.md        # Flat 2-level TOC
├── LargerHeadings/                  # Flatter-heading variants of all 13 files
├── 1_Copyright Information.md
├── 2_Version History.md
├── 3_Game Overview.md
├── 4_Gameplay and Mechanics.md
├── 5_Story, Setting and Character.md
├── 6_Levels.md
├── 7_Interface.md
├── 8_Artificial Intelligence.md
├── 9_Technical.md
├── 10_Game Art.md
├── 11_Secondary Software.md
├── 12_Management.md
└── 13_Appendices.md
```

When the user asks for a GDD, copy from `assets/` (not `assets/LargerHeadings/` unless they ask for the flatter version).

## Attribution

Template based on Artjom Kurapov's GDD template, packaged in Markdown by TheLazyHatGuy:
https://github.com/TheLazyHatGuy/GDDMarkdownTemplate

When shipping a GDD built from this template, retain the upstream attribution in `README.md`.