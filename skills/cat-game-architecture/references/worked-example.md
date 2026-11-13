# Worked Example — Pure White Lancer (Three.js + React + zustand)

Full before/after of applying C.A.T to `VibeGames/4_chunbai/new_game` (Vite 6 + React 19 + Three.js + Tailwind + zustand, strict TS, no test suite — tsc is the gate).

## Audit findings (start state)

| Letter | Verdict | Evidence |
|--------|---------|----------|
| C | ❌ | `engine/GameEngine.ts` 1656 lines: imported `three`, constructed `THREE.Color/Vector3`, called `scene.createXMesh` in update paths; sim could not run headless |
| A | ⚠️ | `data/`, `utils/`, `types.ts` were pure, but `updateEnemies` called `scene.createExplosion` + `audioManager.playExplosion` + `store` inline; no boundary |
| T | ❌ | hit radii `1.5 / 4 / 0.3`, arena ±200/±60, boss arena `randRange(-30,30), y=5, z=-50`, spawn band 30–80 were literals; zero text representation |

## Target structure

```
src/
├── core/                      # platform-agnostic, zero THREE/DOM/store
│   ├── types.ts               # all contracts (moved from src/)
│   ├── constants.ts           # all tuning constants (moved)
│   ├── math.ts                # vec3 pure functions (moved)
│   ├── data/                  # weapons/enemies/bosses/skills tables (moved)
│   ├── simulation/
│   │   ├── Simulation.ts      # 881 lines: rules/AI/spawn/boss; update(dt, tick) -> SimEvent[]
│   │   ├── enemyAI.ts         # 6+1 behaviors, pure functions + ctx callbacks
│   │   ├── bossAttacks.ts     # 8 attack patterns, pure + ctx callbacks
│   │   └── events.ts          # SimEvent = sound | explosion | fx
│   └── world/
│       ├── world.ts           # WorldManifest + hitRadiusFor/enemyTypesForWave (fact source)
│       └── worldText.ts       # describeWorld/describeRules/describeEntities/buildPromptContext
├── engine/                    # platform adapters
│   ├── GameEngine.ts          # 534 lines: loop + tick assembly + event dispatch + mesh reconcile + store sync + render visuals
│   ├── SceneManager.ts        # three scene/meshes/camera (adapter)
│   ├── InputManager.ts        # DOM -> InputState (adapter)
│   ├── AudioManager.ts        # WebAudio (adapter)
│   └── postfx.ts              # postprocessing (adapter)
├── store.ts                   # zustand (UI state)
└── components/                # React UI
```

## Key design decisions

### TickInput (adapter projections feed the pure sim)

```ts
interface TickInput {
  input: InputState;
  rawAim: { x: number; y: number };                 // raw normalized mouse
  crosshairDir: Vector3;                             // world aim dir (camera+mouse, player height)
  aimOrigin: Vector3;                                // camera world pos (ray tests)
  smartTargetId: number | null;                      // adapter screen-space smart-circle pick
  lockStickPoint: { x: number; y: number } | null;   // normalized screen pos of lock target
}
```

Aim-stick feedback is projection-dependent, so the adapter computes `lockStickPoint` from the **previous** tick's lock target; the sim pulls the aim toward it. One-frame staleness — imperceptible at 60fps. Sim exposes `aimNormX/Y`; the orchestrator writes them back into the InputManager so the next tick's crosshair uses the stuck aim.

### SimEvent (the only side-effect channel)

```ts
type SimEvent =
  | { type: 'sound'; sound: SoundKind; param?: string; freq?: number }
  | { type: 'explosion'; pos: Vector3; color: string; size: number }
  | { type: 'fx'; fx: 'edgePulse' | 'timeDilation' | 'shake'; value?: number };
```

Orchestrator dispatch: sound → AudioManager switch; explosion → `scene.createExplosion`; fx → store triggers (`triggerEdgePulse`, `triggerTimeDilation`) and camera-shake accumulation.

### Mesh reconciliation (never create meshes inside the sim)

Each fixed step, the orchestrator diffs sim entity ids against the scene maps:
- enemy id missing → `createEnemyMesh(def.color, def.size, type)` (boss → `createBossMesh(getBoss(currentBossIndex+1))`); orphaned map ids → remove.
- same for projectiles (geometry variant from type; `Laser` gets `scale(1,1,3)`).
- Boss minions spawn as scout enemies — def-table lookup happens to match their hardcoded mesh color/size; verify this assumption when reusing the pattern.

### Store sync (patch-only + time trap)

`syncStore` patches only changed fields: wave, lockOn, bossFight, bossName, score — plus `time += FIXED_TIMESTEP` **every step**. Dropping `time` is a silent regression (result screen stuck at 00:00; caught in verification). `setPlayers(sim.players)` with the same array reference does not re-trigger zustand subscribers (Object.is) — do not rely on it for change detection.

### Verification protocol used

- `npx tsc -b --noEmit` + `npm run build` green.
- Playwright gameplay smoke: intro completes → L1 spawns 7 enemies → hold LMB → kills/score/combo register (4 kills/80 pts in 3s; 6 kills/150 pts) → wave clears to L2 with 2.5s intermission → Tab lock-on toggles sim/store/HUD in sync → HUD clock advances.
- Token output: `window.__gameManifest()` → 83-line text = World Manifest (arena/colliders/5 named markers/spawn bands/caps/pacing/lock params) + Domain Rules (controls/win-lose/economy/weapon+enemy+boss tables) + Live state (player HP-EN-weapon-combo, per-enemy pos-hp-state-dist, projectile count).
- Zero game console errors; the only browser errors were Playwright synthetic-event artifacts (`pointer lock` on non-user-gesture mousedown) — not app bugs.

## Gotchas observed

1. **Ray-snap aim ported into sim** needs `aimOrigin` as data — the ray-vs-enemy-sphere test is pure math once the origin and direction arrive as inputs.
2. **Boss attack bullets** skip the entity cap checks player/enemy fire uses — keep that asymmetry explicit; the reconcile path must handle it.
3. **Enemy AI side effects** (bomber contact, commander buff, firing) become `ctx` callbacks (`fire`, `onBomberContact`, `enemies` list) — the sim wires them to events.
4. **Render-only state** (brake pitch, camera stiffness, FOV ratio, thrusters, hover bob, lock outline pulse) stays in the adapter; the sim only touches gameplay-relevant state.
5. **introActive freeze** lives in the orchestrator (skip sim update, still drain input edges) — do not put it in the sim.
