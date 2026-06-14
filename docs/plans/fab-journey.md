# Plan — the staged sand→chip journey

A player-facing front-end that the roguelike (`fab_game/game.py`, one boule, wafers as turns) and the
dashboard (`fab_game/dashboard.py`, four live sliders) never gave: build **one wafer's recipe stage by
stage**, making a real decision at each fab stage and watching it land downstream — from no-effect,
through a graded yield ring, to an outright scrap.

This is a **phased** build. It is also, deliberately, almost entirely a *sequencing/exposure* problem over
already-validated physics: the `Recipe` (`fab_game/recipe.py`) is already grouped by fab stage, and
`run_line` already chains them. The journey adds **zero new physics** — it composes `run_line` +
`score_wafer` and surfaces a decision + a consequence at each stage (ADR 0005).

## The decision (what the user asked for)

- **Every stage is a decision point** with a full downstream-consequence spectrum: *ok → doesn't-matter →
  problems/rework → outright failure.* (Decided 2026-06-14.)
- **Stages can be multi-step** — advance the process and watch state develop, recalibrate mid-way
  (especially growth/refining), not always one atomic step.
- **Start easy; difficulty comes later.** Build the stages broadly first; the difficulty mechanics
  (the Scheil slice-position curve, adversity/events, run-to-run progression) are **deferred** until the
  steps are broadly done.
- **Gradual failure is preferred when realistic** (memory `gradual-failure-preferred`): when a
  consequence can honestly be a graded slope rather than a cliff, build the slope.
- **First stage built = silicon purification** (physically the front of the line: sand → metallurgical
  silicon → purify → melt → grow).

## The pattern (every stage reuses this four-beat loop)

1. **Decide** — set this stage's knobs (they already exist on `Recipe`, grouped by stage).
2. **Advance & observe** *(multi-step where natural)* — step the process, watch state evolve.
3. **Forecast the consequence** — run the line with the recipe-so-far (defaults downstream) and read the
   device outcome: a **band** (`clean`/`ring`/`dead` = ok→rework→fail) **and the channel it fails on**.
   This reuses the validated line — no new physics, no duplicated device math.
4. **Commit** — fold the stage's knobs into the accumulating recipe; the next stage builds on it.

Once one stage is built this way, the others are fill-in-the-blanks — so the scaffold stays **thin** (an
accumulating `Recipe` + the current stage's decision), **not** a nine-stage state machine. A stage gets
built when it has a consumer (the repo's anti-over-build rule, `scope-edge-backlog`).

## Phased order

| Phase | Stage | Status | One-line intent |
|------|-------|--------|-----------------|
| **1** | **Purification** | **BUILT** | refine a dirty feed; the edge-loaded Na ring is the graded consequence |
| **2** | **Crystal growth (Czochralski)** | **BUILT** | set the boule pull rate at a radial hot zone — the two-sided Voronkov window (slow → dislocation leakage rim, fast → void core, clean OSF ring between), graded both ways; the axial Scheil drift flattens with a faster pull (CG-1) |
| 3 | Wafer prep (slice/polish) | stub | kerf/waste, count, TTV/bow → flatness scrap + the killer-defect map |
| 4 | Diffusion | stub | dose/temperature/time → junction depth + sheet resistance |
| 5 | Oxidation | stub | ambient/T/time → gate oxide; the thin-oxide V_t lever |
| 6 | Lithography | stub | focus/dose → the CD/NILS edge ring (the G1 dramatic knob) |
| 7 | Etch & deposition | stub | over/under-etch, conformality → bridges/voids (functional shorts/opens) |
| 8 | Device / packaging | stub | gate geometry, assembly funnel → the binned, scored chip |

Difficulty mechanics (slice-position camping, adversity/events, run-to-run progression) are deferred
across **all** phases until the stages are broadly built.

## Phase 1 — the purification stage (BUILT 2026-06-14)

`fab_game/journey.py` (headless, import-pure; mirrors the `GameSession` discipline — frozen/immutable,
action→new state, append-only log, deterministic):

- `JourneyState` — the accumulating `Recipe` + the in-progress purification decision (`grade`, continuous
  `effort`); `current_recipe` overlays it, `commit()` folds it in.
- The interaction: `choose_grade`, `refine(step)` (the multi-step "watch it develop" — each call advances
  the zone-refining effort and logs the new impurity vector), `commit`.
- `refining_trajectory(grade)` — the impurity vector at each effort (Na/Fe/Cu fall by `k^n`, boron flat —
  the cited segregation contrast).
- `forecast(state)` → a `StageForecast`: runs the line (variation on, so the ring shows) → the band
  (`consequence_band`) **and the channel** (`_dominant_channel`: mobile-ion `V_t` vs deep-level-metal
  leakage — so a feed clean on threshold can still die on leakage).
- `finish(state)` → run the committed recipe + `score_wafer`, reusing the `game.GameConfig` economics
  (market bins/prices) — playable start-to-finish even with only purification interactive.

The graded consequence rides the **edge-loaded Na ring** (memory `gradual-failure-preferred`): a marginal
feed kills an outboard rim, not the whole wafer, and the **continuous refining effort** (`front_purity`'s
`k^n` is smooth in `n`) lets the player place the residual in that band — a fractional pass lands the ring
that whole passes leap over. On a solar feed the forecast walks **dead → ring (66%) → clean**; a metal
feed (Na-free, iron-laden) reads fine on `V_t` yet dies on **leakage** — the channel the forecast names.

Surfaces: `fab_game/demo_journey.py` (a *watch-a-playthrough* artifact + the `J1` gallery card / figure)
and `tests/test_journey.py` + `tests/test_demo_journey.py`.

## Phase 2 — the crystal growth stage (BUILT 2026-06-14)

On the committed-clean feed, the decision is the boule **pull rate** (`JourneyState.grow(pull_rate)`),
riding a *fixed radial hot zone* (`GROWTH_G_CENTER_K_PER_MM`, `GROWTH_RADIAL_BOOST`). Unlike purification's
one-sided lever this is a genuinely **two-sided** decision, and — the key call (user-approved, against the
`gradual-failure-preferred` policy) — the **radial** profile makes *both* failures graded, not a cliff:

- pull **too slow** (ξ<ξ_t at the rim) → interstitial **dislocations → a leakage rim** (graded);
- pull **too fast** (ξ>ξ_t at the centre) → vacancy **voids/COPs → a core** (graded);
- the **clean OSF ring** sits between, and pull rate moves it — an interior optimum ~`V*` (≈96% at the
  hot zone; it caps below 100% because the OSF core/rim always cost a few dies — perfect silicon is hard,
  hence `CLEAN_BAND = 0.90`).

A uniform gradient would make the slow side an all-or-nothing **leakage cliff** (verified); the radial
profile (A2's already-wired knob — *used*, not rebuilt) is what grades it. `forecast` names the channel by
reading the growth regime (dislocation leakage vs grown-in voids vs the purification roots). The
multi-step "watch it develop" is `boule_profile` — the axial Scheil `V_t` drift seed→tail, which a faster
pull **flattens** (CG-1). **Honest caveat:** "no economics needed" is only *bracketed* — within the clean
window what separates pulls is **throughput** (faster = more wafers) = the same deferred economics.

**Deferred here:** Level-2 *variable mid-pull schedule* (a true recalibrate-as-you-grow = variable-`k`
Scheil, new physics); C1 oxygen/thermal-donors, CG-3 Stefan (already standalone deepenings); the
across-wafer-to-cut handoff (the boule's axial drift feeds phase 3).

## Deferred (explicit)

- **The refining / grade economics — the cost side of the decision (the #1 open item).** Today `finish`
  charges only the wafer cost: refining is free and every grade is the same price, so the optimal play is
  trivially "refine until clean" — a *one-sided cleanup lever*, not yet a two-sided decision. The
  trade-off the user named ("more passes = cleaner but costs money/time") plus a **grade price** (cheap
  dirty MGS vs expensive clean EGS) makes *how much to refine* a real Goldilocks decision: the ring
  penalizes under-refining, cost penalizes over-refining (the shape the G7 oxide lever already has). The
  consequence spectrum (the forecast bands) is built; this is its missing other half — the next increment.
- **The other eight stages' interactive logic** — they run at recipe defaults today (the journey carries
  them); built when each has a consumer.
- **All difficulty mechanics** — per the user's "start easy, difficulty later."
- **The live interactive UI** — a notebook `interact` cell and/or a Textual journey screen driving the
  headless core. The scripted playthrough + figure is phases 1–2's visible artifact; the live UI is the
  next increment.

## References

- ADR 0005 — the fab-game layering (`fab_game → chip`, one-way).
- `docs/plans/fab-game.md` — the G1–G7 line build (the physics the journey sequences).
- `docs/plans/scope-edge-backlog.md` — the anti-over-build bar.
- memory: `gradual-failure-preferred` (the Na ring + the policy), `fab-game`.
