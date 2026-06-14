# Plan — the staged sand→chip journey

A player-facing front-end that the roguelike (`fab_game/game.py`, one boule, wafers as turns) and the
dashboard (`fab_game/dashboard.py`, four live sliders) never gave: build **one wafer's recipe stage by
stage**, making a real decision at each fab stage and watching it land downstream — from no-effect,
through a graded yield ring, to an outright scrap.

This is a **phased** build. It is also, deliberately, *mostly* a *sequencing/exposure* problem over
already-validated physics: the `Recipe` (`fab_game/recipe.py`) is already grouped by fab stage, and
`run_line` already chains them. Phases 1–3 add **zero new physics** — they compose `run_line` +
`score_wafer` and surface a decision + a consequence at each stage (ADR 0005). **Phase 4 is the documented
exception:** the diffusion outputs (`x_j`/`R_s`) fed *nothing scored* (the device reads `N_A`/`t_ox`/CD,
never `R_s`), so the dose was inert — making it a real decision required one genuine device term (an
additive S/D series resistance on `chip.device.saturation_current`, default-0 seam). See Phase 4 below.

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
| **3** | **Wafer prep — slice/cut** | **BUILT** | where down the boule to cut this wafer — it reads the axial Scheil drift (cut too deep → a graded V_t **centre core** → dead), and how deep you can cut is set by the **phase-2 pull** (the first stage coupled to a prior decision). Polish/flatness/killer-defect deferred (TTV→defocus is a named scope edge) |
| **4** | **S/D diffusion** | **BUILT** | the **predep dose** → diffused-layer sheet resistance `R_s` → (a new S/D **series-resistance** device term) source degeneration that **starves** `I_Dsat` → a graded `I_Dsat` **centre core**. The drive-in is *not* the lever (it conserves dose). The **one stage that adds real physics** (the dose was inert — `R_s` fed nothing scored); lands on the existing `I_Dsat` spec |
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

## Phase 3 — the slice/cut stage (BUILT 2026-06-14)

On the committed, grown boule the decision is **where down it to cut** this wafer
(`JourneyState.cut(slice_z)`, the axial fraction ∈ [0, 1)). It is the **first stage that reads a prior
committed decision** — the journey's "watch the consequence propagate" payoff, finally realized end to end:

- The cut reads the boule's axial **Scheil drift** (phase 2 / G2): boron's `k < 1` walks the substrate
  doping — so `V_t` — *up* toward the tail (`boule_profile` is the *watch-it-develop* view of exactly this
  profile). Cut too deep and the wafer lands above the `V_t` window.
- The consequence is **graded, not a cliff** (the gradual-failure policy, **zero new physics**): the radial
  `t_ox` non-uniformity already in the line spreads `V_t` across the die map, so the **centre dies (nominal,
  highest `V_t`) cross the high ceiling first** while the **rim** (thinner gate oxide → lower `V_t`) survives
  longest → a `V_t` **centre core** before the whole wafer goes out. This is the *inverse* radial signature
  of stage-1's Na **edge** ring (Na is edge-loaded and pushes `V_t` *down* into the low bound, so the rim
  fails first; here the high bound is hit centre-first — a nice two-V_t-failure contrast). The arc walks
  **clean** (near the seed) → a graded middle band (~z 0.87–0.90) → **dead** (the tail).
- **The coupling (the headline):** how deep you can cut and stay in spec is set by the **phase-2 pull**. A
  *faster* pull flattened the drift (CG-1), so a **flat boule can be cut deep**; a *slow*-pulled boule is
  already lost to its interstitial **dislocation leakage rim** (A1) *before* the cut, so cut depth can't
  rescue it — "a bad pull can't be sliced away." The forecast names the channel correctly on each side (the
  Scheil-drift `V_t`-*high* root when cut deep, distinct from purification's mobile-ion `V_t`-*low* Na; the
  leakage rim when slow-pulled — the existing worst-die heuristic resolves the multi-channel wafer).

**Scope (honest — this is the *cut*, not all of wafer-prep).** Phase 3 ships the slice/cut decision; the
rest of the wafer-prep stage — **polish/flatness** (TTV/bow/CMP) and the **killer-defect map** — runs at
recipe defaults. Flatness today is a *binary* whole-wafer scrap (out-of-spec → reject), and the wire that
would grade it (**TTV → focus budget → an edge ring of CD/NILS**) is an explicit **named scope edge** =
new physics, deferred (per `chip.wafer_prep`'s own ceiling note). So "wafer-prep BUILT" means the slice/cut
*decision*; polish + defects are carried, not yet decisions.

**Honestly one-sided absent economics** (like purification): cutting at the seed (`slice_z` 0) is always
safest, and "use more of the boule" (a deeper cut = more wafers per boule = throughput) is the **same
deferred cost side** as purification's refining effort. What makes the cut a real decision *today* is the
phase-2 coupling, not a price — the economics is named, not faked (no manufactured low-`V_t` failure at the
seed, which would be the `gradual-failure-preferred` "inflate an unrelated variable" fudge).

`demo_journey.py` is now a **three-stage** playthrough (a 3×3 figure: the slice-arc, the coupling, and the
`V_t` centre-core wafer map join the purification + growth rows); `test_journey.py` pins the graded core, the
coupling, the channel naming, and the no-cut **seam** (an explicit `cut(0)` reproduces the no-cut forecast).

## Phase 4 — the S/D diffusion stage (BUILT 2026-06-14)

On the cut wafer the decision is the **predep dose** (`JourneyState.diffuse(predep_C, predep_min)`) — how
much dopant to lay down before the drive-in redistributes it. It is the **one stage that adds real
physics**, because the diffusion was a genuine *dead end* for the journey:

- **The gap (verified empirically before building).** The diffusion step records `x_j`/`R_s` on every die,
  but **nothing scored consumes them** — `device_step` reads `N_A`/`t_ox`/CD, the spec windows are
  `CD/I_Dsat/V_t/NILS/leakage`, none on `R_s`. So changing the diffusion knobs moved `x_j`/`R_s` but
  changed **no** yield: the dose was inert. (Confirmed by grep + a dynamic-range probe.)
- **The consumer (the new term).** `R_s` → a parasitic S/D **series resistance** `R_series = R_s·n_□` →
  **source degeneration** that degrades the drive current: the device self-consistently solves
  `I_D = β·(V_GS − V_t − I_D·R_S)²` (`chip.device.saturation_current` gained an additive `R_series_ohm`,
  **default 0.0 → bit-for-bit the ideal closed form**, the seam; its own triad leg = the seam + the
  self-consistency residual + the small-signal `g_m = g_m0/(1+g_m0 R_S)`). So an **under-diffused**
  (cool/short) predep → high `R_s` → starved `I_Dsat` → fails the **existing** `I_Dsat` floor (no new
  spec). The journey engages the consumer with a flagged house geometry `n_□ ≈ 0.15` (a wide `W = 10 µm`
  device: `L_access/W ≈ 1.5 µm/10 µm`), so nominal `R_series ≈ 12 Ω` sits comfortably inside the window and
  an under-diffused predep walks it out.
- **The drive-in is *not* the lever** — it conserves dose (sealed Neumann both ends), so it swings `x_j`
  but barely moves `R_s` (the same trap a slow pull was for the Scheil drift; verified — drive-in 950→1100 °C
  *lowers* `R_s` while `x_j` grows 10×). The **predep** is the dose lever.
- **Graded, one-sided.** The radial `t_ox` non-uniformity already in the line grades the consequence: the
  edge's thinner gate oxide gives more drive (higher `C_ox`), so the **thicker-oxide centre** dies cross
  the `I_Dsat` floor first → a graded `I_Dsat` **centre core** (same radial sense as the slice `V_t` core,
  a *different channel*: drive-current-low vs threshold-high). **One-sided** like purification/slice — more
  dose only lowers `R_s`; the over-diffusion harm (short-channel rolloff) is the device model's *omitted*
  scope edge, so a high-dose failure is **not faked** (the gradual-failure "inflate an unrelated variable"
  fudge avoided). The cost side (thermal budget / "use the least dose in spec") is the same deferred
  economics shared by purification and slice.

`forecast` names the channel by direction (`I_Dsat` *low* + consumer engaged → series resistance, distinct
from a defocus/over-etch *high*-`I_Dsat` over-current); `diffuse` logs the resulting `R_s`/`x_j`;
`diffusion_trajectory` is the *watch-the-dose-set-the-junction* view (predep time → `R_s`/`x_j`/`I_Dsat`).
`demo_journey.py` is now a **four-stage** playthrough (a 4×3 figure: the diffusion dose-read, the arc, and
the `I_Dsat` centre-core map join the prior three rows); `test_journey.py`/`test_demo_journey.py` pin the
graded core, the channel naming, the one-sidedness, and the no-diffuse **seam** (consumer off ⇒
`sd_contact_squares = 0` ⇒ ideal-contact `I_Dsat`). `chip/tests/test_device.py` carries the device term's
triad.

## Deferred (explicit)

- **The economics — the cost side of the decision (the #1 open item, now shared by THREE stages).** Today
  `finish` charges only the wafer cost, so three stages are *one-sided absent a price*: **purification**
  (refining is free + every grade is the same price → "refine until clean"), **the slice/cut** (cutting
  at the seed is always safest → "camp at the seed"; the value of cutting deeper = **more wafers per boule**
  = throughput), and **the S/D diffusion** (more dose only lowers `R_s` → "predep forever"; the cost of
  more dose = thermal budget / cycle time). A **per-pass / per-wafer-vs-throughput / per-budget** cost is
  the same missing half across all three: the ring/Scheil-drift/`R_s` penalizes under-doing it, cost
  penalizes over-doing it (the two-sided Goldilocks shape the G7 oxide lever already has). The consequence
  spectrum (the forecast bands) is built for all; the cost side is its other half — the natural next
  increment. (Crystal growth is the exception — its two-sidedness needed no economics; the radial hot zone
  supplied it.)
- **The polish/flatness + killer-defect half of wafer-prep** — phase 3 ships the *cut*; TTV/bow/CMP +
  the defect map run at defaults (flatness is a binary scrap, and TTV→focus-budget is a named scope edge =
  new physics). Built when graded.
- **The remaining stages' interactive logic (5–8 + wafer-prep's polish half)** — they run at recipe
  defaults today (the journey carries them); built when each has a consumer.
- **All difficulty mechanics** — per the user's "start easy, difficulty later."
- **The live interactive UI** — a notebook `interact` cell and/or a Textual journey screen driving the
  headless core. The scripted playthrough + figure is phases 1–4's visible artifact; the live UI is the
  next increment.

## References

- ADR 0005 — the fab-game layering (`fab_game → chip`, one-way).
- `docs/plans/fab-game.md` — the G1–G7 line build (the physics the journey sequences).
- `docs/plans/scope-edge-backlog.md` — the anti-over-build bar.
- memory: `gradual-failure-preferred` (the Na ring + the policy), `fab-game`.
