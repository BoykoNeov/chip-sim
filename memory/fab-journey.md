---
name: fab-journey
description: the staged sand→chip journey front-end — phases 1-5 (purification + crystal growth + slice/cut + S/D diffusion + oxidation) BUILT; the cost-side decision + difficulty + live UI deferred
metadata: 
  node_type: memory
  type: project
  originSessionId: dbb05de6-d8c9-43a5-8b51-794f149318e3
---

The staged sand→chip **journey** — a new player-facing front-end (sibling to the roguelike
`game.py` and the `dashboard`): build ONE wafer's recipe **stage by stage**, a decision per
fab stage with the downstream consequence shown. Plan `docs/plans/fab-journey.md` (the full
vision + phased order + the four-beat pattern: **decide → advance/observe → forecast →
commit**). Phases 1-3 add zero new physics (compose `run_line` + `score_wafer`, ADR 0005);
**phase 4 is the documented exception** — it adds one genuine device term (see below). The
scaffold is deliberately THIN (an accumulating `Recipe` + the current stage's decision), NOT a
9-stage state machine — a stage gets built when it has a consumer (anti-over-build).

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

**THE #1 open item (advisor — deferred but NAMED, not silently shipped) — now shared by THREE stages:**
purification, slice/cut *and* S/D diffusion are all ONE-SIDED absent economics. Purification: refining
is **free** + grades are one price → "refine until clean". Slice/cut: cutting at the seed is always safest
→ "camp at the seed"; value of cutting deeper = **more wafers per boule** = throughput. Diffusion: more
predep dose only lowers `R_s` → "predep forever"; cost of more dose = **thermal budget / cycle time**. The
**cost side** — per-pass / per-wafer-vs-throughput / per-budget — is the same missing half for all three:
the ring/Scheil-drift/`R_s` penalizes under-doing it, cost penalizes over-doing it (the two-sided
Goldilocks shape the G7 oxide lever has). The consequence spectrum (forecast bands) is built for all;
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

**Phase 4 (S/D diffusion) BUILT 2026-06-14** — `JourneyState.diffuse(predep_C, predep_min)` (new `predep_C`
overlay field; engaging it turns on the consumer). **THE one stage that adds REAL physics** (advisor-gated):
the diffusion was a journey DEAD END — the step records `x_j`/`R_s` per die but **nothing scored consumes
them** (device reads `N_A`/`t_ox`/CD; specs are CD/I_Dsat/V_t/NILS/leakage, none on `R_s`) → the dose was
**inert** (verified by grep + a dynamic-range probe BEFORE building). **The consumer (new device term):**
`R_s` → S/D parasitic **series resistance** `R_series = R_s·n_□` → **source degeneration** solving
`I_D = β·(V_GS−V_t−I_D·R_S)²` — `chip.device.saturation_current` gained additive `R_series_ohm` (**default
0.0 → bit-for-bit ideal closed form = the seam**; own triad: seam + self-consistency residual + small-signal
`g_m=g_m0/(1+g_m0 R_S)`, `chip/tests/test_device.py`). Under-diffused (cool/short) predep → high `R_s` →
starved `I_Dsat` → fails the **EXISTING** I_Dsat floor (no new spec). **THE empirical gate (advisor, decided
the design):** the **predep is the lever, NOT the drive-in** — drive-in conserves dose (sealed Neumann) so
it swings `x_j` 10× but *lowers* `R_s` (the same trap a slow pull was for Scheil). House geometry `n_□≈0.15`
(`DIFFUSION_SD_CONTACT_SQUARES`; a WIDE W=10µm device → L_access/W≈1.5µm/10µm — NOT the ~1-5 of a square
device the advisor first assumed; nominal R_series≈12Ω in-window, under-diffused walks it out). **Graded,
one-sided:** existing radial `t_ox` non-uniformity grades it — edge oxide thinner → higher C_ox → more drive
→ survives; thicker-oxide **CENTRE** crosses the floor first → an `I_Dsat` **centre-WEIGHTED core** (advisor:
NOT phase-3-clean — fail mean r≈0.63 vs pass 0.81, CD scatter blurs it, span 0–0.98; same radial sense as
the slice `V_t` core but a DIFFERENT channel: drive-low vs threshold-high, AND noisier). **One-sided like
purify/slice** — more dose only helps; over-diffusion's short-channel harm is the device model's OMITTED
scope edge → NOT faked (gradual-failure "inflate an unrelated variable" fudge avoided). `_dominant_channel`
keys on direction (`I_Dsat` *low* + consumer on → series-R, vs defocus/over-etch *high*). `diffusion_trajectory`
= watch-the-dose view (predep TIME at `DEMO_PREDEP_C=900` → R_s/x_j/I_Dsat; time gives a wider graded band
than T at full 10-min). demo_journey now **FOUR-stage (4×3 figure**, the diffusion dose-read + arc + I_Dsat
centre-core map join the rows); journey/demo tests pin graded core, channel, one-sidedness, no-diffuse seam.
Honesty: the plan's "journey adds zero new physics" is **formally false at phase 4** — recorded in the plan +
module docstrings, not carried stale.

**Phase 5 (oxidation) BUILT 2026-06-14** — `JourneyState.oxidize(minutes)` (gate-oxide **time** at dry/recipe-T;
new `oxide_min` overlay). **The cleanest stage + the inverse of phase 4:** (a) **genuinely two-sided, NO economics**
(like growth) — `t_ox` is read TWO ways at once: `V_t=…+Q_dep/C_ox` UP, `I_Dsat∝C_ox(…)²` DOWN → too thin → low
`V_t`/over-current, too thick → high `V_t`/starved drive, clean window ~17–22min (≈14nm@20min); (b) **RESTORES
"zero new physics"** that phase 4 broke (the t_ox→V_t/I_Dsat chain is the device's *core* read — no new term).
Lever = **time** not (T,min) (monotone reaction-limited; T risks the Massoud band). **Graded by its OWN radial
`t_ox` non-uniformity** (edge ~2.5% thinner, `Variation.t_ox_edge_frac`) — the spread phases 3–4 *borrowed*,
finally grading its HOME (advisor honesty: NOT "first stage graded by native variation" — purification's Na ring is
too; the real novelty = borrowed-spread-comes-home + **opposite radii**). **THE only stage whose two sides fail at
OPPOSITE radii:** under → thinnest **rim** first → EDGE RING (echoes stage-1 Na ring); over → thickest **centre**
first → CENTRE CORE (echoes slice/diffusion cores). **Channel discriminator = THE load-bearing item (advisor):**
oxidation collides with Scheil(V_t-high)/Na(V_t-low)/series-R(I_Dsat-low); the V_t/I_Dsat **sign is NOT unique** (a
deep Scheil cut also raises V_t + drags I_Dsat down) → `_dominant_channel` keys on the **inherited `t_ox` itself**
(`_oxidation_root`, checked FIRST, off `_nominal_oxide_nm` by >6% flagged band; nominal recipe's ~3% spread never
trips → seam + phase 1–4 channel tests untouched). **THE test runs the oxide failure on a FULL journey** (committed
cut + diffusion consumer ON, both over+under) → proves no mis-attribution. **Coupling:** how much oxide before the
`V_t` ceiling = set by the **cut** (deeper cut → higher N_A → higher baseline V_t → less ceiling room; verified
24.5→19.5min as z 0→0.85) — sibling of pull↔cut, existing `V_t=f(N_A,t_ox)`, no new physics. **Seam = lever at
NOMINAL** (advisor) — `oxide_min=None`⇒nominal 20min (a MOSFET always has gate oxide), NOT an off switch. demo now
**5-stage (5×3 fig)**; map = under-oxidized **edge ring** (spans both ring topologies). Showcase sweep on a
**latitude baseline** (mid cut, ideal downstream) so both sides grade; the accumulated deep-cut+lean-predep wafer's
tighter window = the margins-compound coupling, not a bug. **Same discriminator applied to `pipeline.diagnose()`
too** (advisor nudge — repo closes rather than carries): over-oxide I_Dsat-low names the oxide not series-R, before
that fingerprint (2 boundary cases stay deferred-latent: fully-dead-thick worst-die on the thinner rim → Scheil;
thick I_Dsat-high → impossible w/o CD-collapse). **#1 open item still 3 stages** (purify/slice/diffuse — oxidation is the no-economics exception, like growth).

**Deferred:** the remaining stages' interactive logic (stages 6–8 + wafer-prep's polish half run at recipe
defaults today — see the plan's stage table), all difficulty mechanics ("start easy, difficulty later"),
the live UI (notebook `interact` / Textual journey screen — the scripted playthrough is phases 1–5's artifact).
Default grade `solar` is an *intermediate* (already partly-refined) feed, chosen for the clean
ring at 0.25 steps; the raw-"sand" MGS narrative is noted in the demo. [[fab-game]]
[[gradual-failure-preferred]] [[scope-edge-backlog]]
