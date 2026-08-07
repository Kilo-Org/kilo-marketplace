---
name: cat-game-architecture
description: Applies the GDC 2026 "AI-Driven 3D Game Prototyping" C.A.T framework (Code Reuse, Adapter Design, Token-Friendly) to game codebases. Audits a project against the standard, refactors a game-engine monolith into a platform-agnostic core plus platform adapters, and adds a tokenized text representation of the 3D world so AI agents can edit game rules safely. Use when the user asks to test/apply that GDC 2026 paper's workflow on a codebase, make a game AI-editable or token-friendly, split a game into core/adapters, or audit a game engine for AI-driven development readiness.
---

# C.A.T Game Architecture — AI-Driven 3D Game Refactoring

Distilled from Hao Yang (Tencent Photon Studio Group), *AI-Driven 3D Game Prototyping*, GDC 2026. The framework lets a language model build/edit playable 3D games by making the codebase AI-safe: pure game rules decoupled from platform code, and the 3D world exposed as text.

## The C.A.T Standard

| Letter | Principle | Acceptance criterion |
|--------|-----------|----------------------|
| **C** | Code Reuse | Game logic ships as runtime-agnostic TypeScript. No logic file imports three/react/zustand/DOM/WebAudio. |
| **A** | Adapter Design | Hard core/adapters split: `core/` = rules/state/AI (zero platform deps); `engine/` = rendering/input/audio/UI binding. Side effects leave the core only as typed events. |
| **T** | Token-Friendly (most critical) | The 3D world is serialized to text: domain rules, arena bounds, collider table, named markers, entity state. "Game tools were built for humans. Stop expecting AI to see pixels." |

## Workflow

### Phase 0 — Audit (produce a verdict table before touching code)

Audit the three letters against concrete evidence. Do not skip this; the report drives the refactor and becomes the doc trail.

1. **C**: Find the largest engine/god-class file (`wc -l` / line count). Grep the candidate logic files for platform imports: `rg "from '(three|react|zustand)'|window\.|document\.|HTMLCanvasElement"`.
2. **A**: Check whether simulation paths call rendering/audio/store directly (`scene.createXMesh`, `audio.playX`, `store.setGame` inside update loops). Identify already-pure modules (types, constants, data tables).
3. **T**: Grep for scattered world literals (collider radii, arena bounds, spawn coordinates, boss positions). Check for any textual world description or dev introspection hook.

Record the verdict as a C/A/T table with `file:line` evidence, e.g. the table in `references/worked-example.md`.

### Phase 1 — C: extract the pure core

1. Move platform-agnostic modules into `src/core/` (or equivalent): `types.ts`, `constants.ts`, `math.ts`, `data/` tables (weapons/enemies/bosses/skills).
2. Update all importers, delete the old directories.
3. Verify with `tsc` before proceeding.

### Phase 2 — A: extract the simulation, make adapters event-driven

1. **Define the event union** (`core/simulation/events.ts`): `SimEvent = sound | explosion | fx` — the only way the core signals the outside world.
2. **Port logic verbatim** into a `Simulation` class (rules, movement, AI, spawning, boss patterns, collisions). Replace every side effect with an event emission:
   - `audioManager.playX(...)` → `{ type: 'sound', sound: 'x' }`
   - `scene.createExplosion(...)` → `{ type: 'explosion', pos, color, size }`
   - `store.triggerX(...)` / camera shake → `{ type: 'fx', fx: '...', value }`
3. **Push camera/canvas-dependent computations out of the sim**. Anything requiring projection becomes adapter-computed input data passed in each tick (`TickInput`):
   - `crosshairDir` (world aim direction from camera+mouse)
   - `aimOrigin` (camera world position, for ray tests)
   - `smartTargetId` (screen-space smart-circle pick)
   - `lockStickPoint` (normalized screen pos of the lock target, for aim stick)
   - `rawAim` (raw normalized mouse)
   The sim stays pure math; the adapter owns all matrices.
4. **Rewrite the orchestrator** (`GameEngine`) as a thin adapter:
   - fixed-step loop (accumulator pattern)
   - assemble `TickInput` per step, run `sim.update(dt, tick)`
   - dispatch returned events (audio/scene/store side effects)
   - **mesh reconciliation**: each frame create meshes for entity ids not yet in the scene maps, remove meshes whose ids vanished — never create/remove meshes inside the sim
   - **store sync**: patch only changed fields (wave, lockOn, bossFight, bossName, score, time) to avoid re-render churn; advance `time` by the fixed step
5. Keep render-only visuals in the adapter: camera/FOV breathing, screen shake, lock indicators/outlines, thruster flames, hover bob, brake pitch.

### Phase 3 — T: tokenize the world

1. **World manifest** (`core/world/world.ts`): single source of truth for arena bounds, collider table (per entity radius), named markers (player start, boss arena, camera home, spawn band), spawn bands, caps, pacing, lock parameters. The sim imports helpers from it (e.g. `hitRadiusFor(type)`).
2. **Tokenizers** (`core/world/worldText.ts`): pure functions producing prompt-ready text:
   - `describeWorld()` — manifest as text
   - `describeRules()` — controls, win/lose, economy, weapon/enemy/boss tables
   - `describeEntities(sim)` — live state: player HP/EN/weapon/combo, per-enemy pos/hp/state/dist, projectile counts
   - `buildPromptContext(sim)` — combined full context
3. **DEV hook**: expose `window.__gameManifest = () => buildPromptContext(sim)` and `window.__sim` guarded by `import.meta.env.DEV` (production builds tree-shake the hook).

### Phase 4 — Verify (do not skip)

1. `tsc` + full build green.
2. Browser gameplay smoke (Playwright): menu → start → intro completes → enemies spawn → shoot → kill → score/combo register → wave clears and advances → lock-on toggles ↔ store ↔ HUD. Zero console errors.
3. Token output: `__gameManifest()` contains world manifest + rules + live state.
4. **Behavioral equivalence**: extraction must be verbatim. If gameplay changed, it is an extraction bug — fix the port, not the tuning. The only accepted deviation is 1-frame staleness on projection-fed input (imperceptible at 60fps).
5. Sync docs (TDD file tree, verification report). Never touch docs with concurrent user edits.

## Hard rules

- `core/` imports nothing platform-specific. Grep-verify after every batch.
- Side effects leave the core **only** as events.
- During extraction, change behavior **never** — only move code.
- The sim never touches meshes; the adapter reconciles entity/mesh maps by id each frame.
- Caps (`MAX_ENEMIES`, `MAX_PROJECTILES`) stay in the sim — they are gameplay, not rendering.
- Keep per-batch verification: each batch type-checks green before the next.

## Known gotchas (full detail in `references/worked-example.md`)

- Aim-stick feedback is projection-dependent: the adapter computes it from the previous tick's lock target — one frame stale, imperceptible.
- Mesh reconciliation must handle boss minions (their mesh color/size must match the def table or the reconcile lookup diverges).
- Boss attack bullets/meshes must not bypass the entity cap checks that player/enemy fire uses.
- After refactor, verify the HUD clock/score still advance — store-sync drops (e.g. `time`) are the classic silent regression.
- Store `setPlayers` with the same array reference does not re-render React (zustand `Object.is`); do not rely on it for change detection.

## References

- `references/cat-framework.md` — the GDC 2026 talk summary (principles, Tencent stack, proof points).
- `references/audit-checklist.md` — concrete PASS/FAIL criteria with grep commands per letter.
- `references/worked-example.md` — full before/after of the Pure White Lancer refactor (audit findings, target structure, TickInput design, verification results).
