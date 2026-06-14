---
name: fab-journey
description: the staged sand→chip journey front-end — phases 1-3 (purification + crystal growth + slice/cut) BUILT; the cost-side decision + difficulty + live UI deferred
metadata: 
  node_type: memory
  type: project
  originSessionId: dbb05de6-d8c9-43a5-8b51-794f149318e3
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

**THE #1 open item (advisor — deferred but NAMED, not silently shipped) — now shared by TWO stages:**
the purification *and* the slice/cut decisions are both ONE-SIDED absent economics. Purification: refining
is **free** + grades are one price → "refine until clean". Slice/cut: cutting at the seed is always safest
→ "camp at the seed"; the value of cutting deeper = **more wafers per boule** = throughput. The **cost
side** — a grade/per-pass refining price + a per-wafer-vs-throughput cost — is the same missing half for
both: the ring/Scheil-drift penalizes under-doing it, cost penalizes over-doing it (the two-sided
Goldilocks shape the G7 oxide lever has). The consequence spectrum (forecast bands) is built for both;
**the natural next increment.** (Crystal growth is the exception — the radial hot zone gave it
two-sidedness with NO economics.)

**Phase 2 (crystal growth) BUILT 2026-06-14** — `JourneyState.grow(pull_rate)` (the boule pull
lever) on a FIXED RADIAL hot zone (`GROWTH_G_CENTER_K_PER_MM=4`, `GROWTH_RADIAL_BOOST=4`).
Genuinely **two-sided** (no economics needed): slow → dislocation **leakage rim**, fast → void
**core**, clean **OSF ring** between, interior optimum ~2 mm/min (≈96%). **THE call (user-approved
vs [[gradual-failure-preferred]]):** a UNIFORM gradient makes the slow side a leakage **CLIFF**
(verified 0.5→0%, 0.75→100%) — the **radial** profile (A2's already-wired knob, *used* not rebuilt)
grades BOTH sides. Caps <100% (OSF core/rim always cost a few) → `CLEAN_BAND` lowered 0.95→**0.90**,
`DEFAULT_GRID_N` 9→**11** (coarse dicing over-weights core/rim). `forecast`/`_dominant_channel` reads
the growth regime to name dislocation-leakage vs grown-in-voids (vs the purification roots);
`boule_profile` = the axial Scheil drift (CG-1 flattens it faster). **Honest caveat:** "no economics"
is only BRACKETED — within the clean window throughput (faster=more wafers) is the same deferred cost.
demo_journey now a TWO-stage playthrough (2×3 figure); 28 journey tests (the policy test:
`test_growth_window_is_two_sided_and_graded_on_both_sides`). **Deferred here:** Level-2 variable mid-pull
schedule (variable-k Scheil = new physics); C1/CG-3 (standalone deepenings).

**Phase 3 (slice/cut) BUILT 2026-06-14** — `JourneyState.cut(slice_z)` (axial fraction ∈ [0,1); new
`slice_z` overlay field, composes with the growth overlay on the shared `czochralski` knobs). **The first
stage that READS a prior committed decision** — the journey's "watch it propagate" payoff, finally end to
end. The cut reads the boule's axial **Scheil drift** (`boule_profile` = the watch-it-develop view): boron
`k<1` walks `V_t` UP toward the tail → cut too deep → above the `V_t` window. **Graded, NOT a cliff, with
ZERO new physics:** the *existing* radial `t_ox` non-uniformity spreads `V_t` across the map so the CENTRE
dies (nominal, highest `V_t`) cross the high ceiling first while the RIM (thinner oxide → lower `V_t`)
survives longest → a `V_t` **centre CORE** (arc clean → middle band ~z 0.87–0.90 → dead at the tail). **THE
finding (advisor caught my prose backwards before push):** it is a centre core, NOT an edge ring — the
*inverse* radial signature of stage-1's Na edge ring (Na edge-loaded, pushes `V_t` DOWN→low bound→rim
first; here the HIGH bound is hit centre-first). Verified by radial yield (0%→95% centre→rim) not assumed.
**THE coupling (the headline test `test_slice_consequence_is_coupled_to_the_phase2_pull`):** how deep you
can cut is set by the **phase-2 pull** — a fast pull flattened the drift (CG-1) so a flat boule cuts DEEP;
a slow pull already lost the wafer to its A1 dislocation **leakage rim** BEFORE the cut → "a bad pull can't
be sliced away." `_dominant_channel` disambiguates the cut's `V_t`-**high** Scheil-drift root (keyed on
direction `(high)` AND `slice_z>0`) from purification's `V_t`-**low** Na — the existing worst-die heuristic
names the leakage rim on the slow-pull side (no new priority logic). **Honest scope (advisor):** this is the
**cut**, not all of wafer-prep — polish/flatness (TTV/bow/CMP) + the killer-defect map run at DEFAULTS;
flatness is a binary scrap and **TTV→focus-budget is a named scope edge** (new physics, deferred).
One-sided absent economics (→ the #1 open item, now shared). No-cut **seam** proven (`cut(0)` ≡ no-cut
forecast). The stale commit-docstring "third stage = refactor" note UPDATED (the overlay holds for 3
idempotent stages; refactor tips only at order-dependent/non-idempotent folding). `demo_journey` now a
THREE-stage playthrough (**3×3** figure: slice-arc + the coupling + the `V_t` centre-core map join the rows);
**299 fab_game tests green** (+9: graded ring, coupling, channel, commit-fold, range guard, seam).
**Deferred:** the across-wafer/polish handoff + the killer-defect map (wafer-prep's other half).

**Deferred:** the remaining stages' interactive logic (stages 4–8 + wafer-prep's polish half run at recipe
defaults today — see the plan's stage table), all difficulty mechanics ("start easy, difficulty later"),
the live UI (notebook `interact` / Textual journey screen — the scripted playthrough is phases 1–3's artifact).
Default grade `solar` is an *intermediate* (already partly-refined) feed, chosen for the clean
ring at 0.25 steps; the raw-"sand" MGS narrative is noted in the demo. [[fab-game]]
[[gradual-failure-preferred]] [[scope-edge-backlog]]
