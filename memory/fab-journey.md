---
name: fab-journey
description: the staged sand→chip journey front-end — phase 1 (purification stage) BUILT; the cost-side decision + difficulty + live UI deferred
metadata:
  type: project
---

The staged sand→chip **journey** — a new player-facing front-end (sibling to the roguelike
`game.py` and the `dashboard`): build ONE wafer's recipe **stage by stage**, a decision per
fab stage with the downstream consequence shown. Plan `docs/plans/fab-journey.md` (the full
vision + phased order + the four-beat pattern: **decide → advance/observe → forecast →
commit**). Zero new physics — composes `run_line` + `score_wafer` (ADR 0005). The scaffold is
deliberately THIN (an accumulating `Recipe` + the current stage's decision), NOT a 9-stage
state machine — a stage gets built when it has a consumer (anti-over-build).

**Phase 1 (purification stage) BUILT 2026-06-14** — `fab_game/journey.py` (headless,
GameSession discipline: frozen/immutable, action→new state, append-only log, deterministic):
- `JourneyState` accumulator (`current_recipe` overlay + `commit` fold); `choose_grade` /
  `refine(step)` (multi-step "watch it develop") / `commit`; `refining_trajectory`.
- `forecast(state)` → `StageForecast`: runs the line (variation ON) → a **band**
  (`consequence_band`: clean/ring/dead = ok→rework→fail, margined) AND the **channel**
  (`_dominant_channel`: mobile-ion `V_t` ring vs deep-level-metal **leakage** — a metal feed
  reads fine on V_t but dies on leakage → reconnects the metal-grade finding).
- `finish(state)` → run + `score_wafer`, REUSING `game.GameConfig` economics (don't fork).
- Showcase: a **solar** feed walks dead → **ring (66%)** → clean as refining effort rises; the
  continuous lever (`zone_passes` relaxed to float, `front_purity`'s k^n smooth) places the
  residual in the ring band whole passes leap over. Rides the [[gradual-failure-preferred]]
  edge-loaded Na ring.
- Surfaces: `demo_journey.py` (watch-a-playthrough) + the **J1** gallery card +
  `docs/figures/fab-game-journey.png`; tests `test_journey.py` (16) + `test_demo_journey.py` (4).

**THE #1 open item (advisor — deferred but NAMED, not silently shipped):** the purification
*decision is currently ONE-SIDED.* The consequence spectrum is built (under-refining →
ring/dead) but refining is **free** and grades are all one price → the optimal play is
trivially "refine until clean" (a cleanup slider, not a decision). The **cost side** — a grade
price (cheap-dirty MGS vs expensive-clean EGS) + a per-pass refining cost — is what makes *how
much to refine* a real two-sided Goldilocks decision (ring penalizes under-refining, cost
penalizes over-refining; the shape the G7 oxide lever has). **The natural next increment.**

**Deferred:** the other 8 stages' interactive logic (run at recipe defaults today — see the
plan's stage table), all difficulty mechanics ("start easy, difficulty later"), the live UI
(notebook `interact` / Textual journey screen — the scripted playthrough is phase-1's artifact).
Default grade `solar` is an *intermediate* (already partly-refined) feed, chosen for the clean
ring at 0.25 steps; the raw-"sand" MGS narrative is noted in the demo. [[fab-game]]
[[gradual-failure-preferred]] [[scope-edge-backlog]]
