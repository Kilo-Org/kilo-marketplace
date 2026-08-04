---
name: kimi3-game-research
description: >-
  Research and analysis of Kimi K3 model's game generation capabilities (K399 /
  K3 Game Arcade). Documents the DDD (Document-Driven Development) + multi-agent
  swarm architecture, tech stack, and workflow used to generate complete games
  from single-sentence prompts. Use when the user asks about AI game generation,
  replicating Kimi K3's game creation approach, or understanding DDD-based
  multi-agent game development workflows.
license: MIT
metadata:
  category: development
  author: xindong
---

# Kimi K3 Game Generation Research

This skill documents the analysis of Kimi K3 (released 2024-07-16) and its K399 / K3 Game Arcade platform, which generates complete web games from single-sentence prompts using a DDD (Document-Driven Development) + multi-agent swarm architecture.

## Background

Kimi K3 generates full, playable web games (logic, art, audio) from minimal user prompts. The reference case is a "Blood Moon Survivor" (类吸血鬼幸存者) game generated from just two user prompts: one to create the game and one to fix a bug. The resulting game has ~5,000 lines of code across 42+ files.

## Tech Stack

| Layer | Choice | Detail |
|-------|--------|--------|
| Language | TypeScript (strict) | `npx tsc -b --noEmit` for type checking |
| Framework | React 19 | Design doc mandates + `init-webapp.sh` scaffold |
| Styling | Tailwind CSS | `init-webapp.sh` produces tailwind.config + global theme vars |
| Build | Vite | `npm run build` → vite build, ~468 modules |
| Rendering | Canvas 2D (main) + WebGL2 (effects) | Programmatic silhouette drawing, bloom + shockwave |
| Audio | Web Audio API (zero audio files) | OscillatorNode/GainNode/BiquadFilter/Convolver/WaveShaper |
| State | Zustand | Global state, settings persisted to localStorage |
| Deployment | Static HTML/JS/CSS | `website_version_manager` build_version action |

## Architecture: DDD + Multi-Agent Swarm

The workflow follows a **Document-Driven Development** process on a remote sandbox VM with git branch isolation.

### Stage 1: Design
- Read `plan.md` template
- Dispatch designer Agent → produces N design documents
- Design docs stored in `/mnt/agents/output/design/`

### Stage 2: Scaffold
- Run `init-webapp.sh` to initialize project
- Dispatch scaffold Agent to establish:
  - `types.ts` — all type definitions
  - `store.ts` — zustand global state
  - `engine.ts` — game engine skeleton, fixed timestep
  - `systems/*.ts` — placeholders (signatures as contracts)
  - Data tables: `weapons.ts`, `passives.ts`, `enemies.ts`
  - Pages/components — placeholders or full implementations
- Merge to master, create parallel branches

### Stage 3: Parallel Development
- Dispatch N coder Agents, each on their own git branch
- Each agent:
  - Runs `setup-local.sh` for independent environment
  - Reads their assigned design document section
  - Can only modify their assigned files
  - Self-validates with `tsc` + git commit
- Main agent merges and build-validates

### Stage 4: Delivery
- `npx tsc -b --noEmit` — full type check
- `npm run build` — Vite production build
- `website_version_manager build_version` — deploy

### Key Contract Mechanisms
- **File ownership isolation**: Each agent can only modify assigned files (~20+ files on blacklist)
- **Interface signature freeze**: Types/store/engine/systems signatures cannot change after scaffold
- **Git branch isolation**: Each agent works on independent branch, main agent merges
- **Self-validation loop**: Each agent must pass `npx tsc -b --noEmit` before commit
- **No dev server**: Agents commit only; main agent handles build verification

## Bundled Skills

### Image Generation Skill
- Source: `image_generation` skill (Python-based)
- Generates images from text descriptions
- Supports multiple ratios (1:1, 3:2, 2:3, 16:9, 9:16) and resolutions (1K, 2K, 4K)
- Opaque or transparent background
- Uses `scripts/image_generation_tool.py` with agent-gw Python SDK

### Vibecoding WebApp Swarm Skill
- Orchestration skill for multi-agent parallel web app development
- Sub-components:
  - `design-guide.md` — design document format, output spec, asset strategy
  - `react-dev.md` — React + TypeScript + Tailwind coding conventions
- Multi-agent workflow template (Stages 1-4 above)

## Game File Structure (Reference)

```
React App
└── GameScreen.tsx
    └── GameEngine (class, rAF loop)
        ├── engine.ts — fixed timestep 1/60
        ├── player.ts
        ├── enemies.ts — 12 enemy AI + 3 Boss (sub-state WeakMap)
        ├── spawner.ts — wave timeline + difficulty multiplier
        ├── combat.ts — spatial hash O(n) collision
        ├── pickups.ts — XP gems/chests/magnetism
        ├── weapons.ts — 12 weapons + 8 super weapons + projectile pool
        ├── upgrades.ts — card pool weighting / evolution check
        ├── fx.ts — particles/screen shake/hit freeze/damage numbers
        ├── audio.ts — Web Audio programmatic
        ├── input.ts — virtual joystick + keyboard fallback
        └── store.ts — zustand global state (settings persisted to localStorage)
```

## Comparison: Astrocade vs Kimi K3

| Dimension | Astrocade | Kimi K3 |
|-----------|-----------|---------|
| Entry | Single file `run(mode)` | Full React + Vite project |
| Rendering | Platform Canvas 2D (implicit) | Self-built dual-layer Canvas + WebGL2 |
| Assets | Platform asset library (`lib.getAsset`) | Self-managed (2 AI images + full procedural) |
| Audio | Platform hosted (`type: "audio"`) | Self-built Web Audio programmatic synthesis |
| Save/Leaderboard | `lib.saveUserGameState` / `lib.addPlayerScoreToLeaderboard` | None (pure single-player) |
| LLM | `lib.llm()` built-in | None |
| Deploy | Upload to Astrocade platform | Vite build → static files → website_version_manager |
| Edit Mode | Platform `mode='edit'` + undo/redo | None |

## When to Apply This Skill

- User asks about generating games from AI prompts
- User wants to understand or replicate Kimi K3's game generation approach
- User is researching DDD + multi-agent workflows for game development
- User asks about React + Canvas 2D + Web Audio game architecture
- User asks about programmatic asset generation vs AI-generated assets
- User needs to compare game generation platforms/approaches (Astrocade vs Kimi K3)