# C.A.T Framework — Source Talk Summary

**Talk:** *AI-Driven 3D Game Prototyping* — Hao Yang, Senior Engineer, Tencent Photon Studio Group
**Venue:** GDC 2026 (40th), AI Summit, Moscone Center
**Impact:** One of the most oversubscribed AI talks at GDC 2026; queue started an hour before doors opened.

## Core idea

Existing AI tools can ship small **Web 2D** games end-to-end but cannot cross into a **3D game engine** — where the money is. C.A.T is a three-principle framework that lets a language model build playable 3D prototypes inside Unreal.

## The three principles

| Letter | Principle | What it does |
|--------|-----------|--------------|
| **C** | Code Reuse | Share the same TypeScript source between Web and engine runtimes. Logic ships once, runs everywhere. |
| **A** | Adapter Design | Split the codebase into a platform-agnostic **core** (game rules, state) and platform-specific **adapters** (Web DOM, Unreal ECS). AI only touches the core. |
| **T** | Token-Friendly *(most critical)* | Tokenize the 3D world before the AI touches it: feed domain rules, expose asset bounding boxes / colliders as text, let designers place named markers. AI manipulates a textual representation of the 3D scene. |

## Tencent's stack

`Prompt (TypeScript)` → **Puerts** (open-source TS-to-engine bridge, no C++) → **ECS** (data-driven core) → **Unreal Web Browser widget** (pixel-perfect Web UI in-engine) → playable prototype.

## Proof points (all built by AI)

1. **8-Ball Pool** — physics-heavy, simple rules, deterministic. 100% functional.
2. **Top-down RPG** — single prompt, ~40 minutes, ~70% of the final game.
3. **Action Combat** — multi-character, multi-boss, varied mechanics; most ambitious case.

## Why it matters

- **Internal R&D:** designers validate mechanics in hours instead of weeks.
- **External:** amateurs build playable 3D prototypes from a sentence.
- **Strategic:** game tooling must shift from GUI-first (for humans) to token-first (for AI); the two will converge.

## Headline quote

> *"Game tools were built for humans. Stop expecting AI to see pixels."* — Hao Yang

## Note

The reference implementation in this skill targets a Web (Three.js) platform instead of Unreal/Puerts — same principles, adapters swapped. For an engine-agnostic core, keep the sim free of THREE types (use plain `Vector3`-style data objects), exactly as the worked example does.
