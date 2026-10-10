# C.A.T Audit Checklist

Run the audit before any refactor. Produce a verdict table with `file:line` evidence, e.g.:

| Letter | Standard | Verdict | Evidence |
|--------|----------|---------|----------|
| C | logic is runtime-agnostic TS | ❌ / ⚠️ / ✅ | `engine/GameEngine.ts` 1656 lines imports `three`, touches `THREE.Mesh` |
| A | clean core/adapter boundary | ❌ / ⚠️ / ✅ | `updateEnemies` calls `scene.createExplosion` + `audioManager.playX` inline |
| T | world serialized to text | ❌ / ⚠️ / ✅ | collider radii/arena bounds hardcoded; no manifest, no dev hook |

## C — Code Reuse

**FAIL** signs:
- The main logic class imports platform libs: `rg "from '(three|react|zustand)'|window\.|document\.|HTMLCanvasElement|requestAnimationFrame" src/engine`
- Game rules call rendering objects (`THREE.Mesh`, `THREE.Vector3`) or construct them in update paths
- The sim class is 1000+ lines mixing physics, AI, and mesh/audio/UI calls

**PASS** when: `src/core/**` contains zero platform imports (grep-verify), and the sim class can in principle run headless (feed inputs, read state/events).

## A — Adapter Design

**FAIL** signs:
- `scene.createXMesh(...)` / `audioManager.playX()` / `store.setGame(...)` inside movement/AI/collision update paths
- The engine class both simulates and renders
- Adapter-owned data (camera matrices, canvas size, mouse pixels) flows INTO sim logic mid-step

**PASS** when:
- Side effects leave the sim only as a typed event union (`sound | explosion | fx`)
- All projection-dependent values arrive as plain-data inputs each tick (`crosshairDir`, `aimOrigin`, `smartTargetId`, `lockStickPoint`, `rawAim`)
- Mesh lifecycle is reconciled by the adapter (entity id diff per frame), never created inside the sim
- Store/UI sync is a separate adapter concern that patches only changed fields

## T — Token-Friendly

**FAIL** signs:
- Collider radii, arena bounds, spawn coordinates, boss positions are literals scattered in engine code
- No textual description of the world exists anywhere
- No way to introspect live entity state from a console/devtools

**PASS** when:
- A `WorldManifest` declares: arena bounds, collider table (per entity), named markers (player start / boss arena / camera home / spawn band), spawn bands, caps, pacing, lock params
- The sim imports manifest helpers (`hitRadiusFor`, `enemyTypesForWave`) so manifest and behavior cannot drift
- Tokenizers produce prompt-ready text: `describeWorld()` / `describeRules()` / `describeEntities(sim)` / `buildPromptContext(sim)`
- DEV hook exposes the token text (`window.__gameManifest()`) and sim (`window.__sim`), guarded by `import.meta.env.DEV`

## Grep cheat sheet

```bash
# platform deps inside core (must be empty)
rg "from '(three|react|zustand)'|window\.|document\.|HTMLCanvasElement|requestAnimationFrame" src/core

# side effects inside sim update paths (must be events only)
rg "createExplosion|play[A-Z]|setGame|setPlayers" src/core/simulation

# scattered world literals (should be centralized in world manifest)
rg "=== (EnemyType\.)?Boss \? 4|randRange\(-30, 30\)|z: -50|WORLD_SIZE" src

# engine size (god-class smell)
(Get-Content src/engine/GameEngine.ts).Count
```
