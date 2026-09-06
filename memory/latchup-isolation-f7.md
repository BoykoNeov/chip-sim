---
name: latchup-isolation-f7
description: "F7's remainder built as historical mode B12 (2026-09-06, 4 slices) — CMOS latchup, the bill STI's density came with; latchup is a WAFER property and the gain condition never discriminates"
metadata: 
  node_type: memory
  type: project
  originSessionId: b8a3cd30-8ce9-4a81-82ba-4c7854e2e482
  modified: 2026-09-06T11:47:11.424Z
---

**F7 remainder → historical mode B12**, 4 slices, 2026-09-06. Plan:
`M:\claud_projects\chip-sim\docs\plans\latchup-isolation-f7.md`. Code: `chip/latchup.py`,
`chip/demo_latchup_history.py`, `IsolationKnobs` in `fab_game/recipe.py`. Sources:
[[latchup-source]]. Chosen by the user after the roadmap's promotable section was found honestly empty.

**THE GATE WAS HALF-OPEN — the 4th time.** `LocosCrossSection.sti_active_um` had been in
`locos_history.py` since B5, so the LOCOS→STI *geometry* contrast needed no code. Again found by going
to build, never by a test (see [[roadmap-page]]). The electrical half was genuinely absent (no well, no
pMOS, no bipolar anywhere).

**The spine — two INDEPENDENT cited conditions, never coupled** (shape of [[high-k-gate-f3]]'s "one
thickness, two currencies"). See [[latchup-source]] for the citations and the decoupling rule.

**S1 finding — the gain condition ADMITS it cannot discriminate.** γ=1 with `W_B ≪ L` ⇒ β 10²–10⁶
(product 10⁴–10¹²) vs real ~1–50. Cause is *physical*: recombination is not what limits these
transistors, **geometry is**. So the sustaining condition holds at every geometry ⇒ **not a finding**,
it is what an unbounded β must give. Tested as an embarrassment (`loop_gain > 1e6` asserted) so the
admission can't quietly stop being true. **The trigger condition is the binding one.**

**S2 finding — latchup is a WAFER property, and the plan's expectation was WRONG.** Measured on a real
21-die run: τ identical on every die, ρ one number per wafer, and the only real per-die spread (printed
CD 165.6→170.1 nm) reaches the *spacing* ⇒ the *gain* ⇒ the inert condition. So it is all dies or none,
built on the flatness-scrap precedent. **Grading it was REFUSED** — a radial resistivity profile would
be uncited physics invented to produce the gradient the plan wanted, the fudge
[[gradual-failure-preferred]] warns about (its "honest move" needs the quantity to *really* be
non-uniform). Instead the per-die gain is recorded **with** the fact that it grades nothing.

**The era number is coefficient-free.** `β ≈ 2L²/W_B²` ⇒ a between-scheme *ratio* is the inverse square
of base widths; L cancels ⇒ independent of τ, D, γ, and the flagged tap geometry. LOCOS spacing =
drawn 2.0 + **B5's computed beak** 0.926 (pinned as `LOCOS_BEAK_ALLOWANCE_UM`, test asserts it still
matches `locos_history` — this is what makes B12 the *second half* of B5, not a module beside it).
STI bare = (2.926/2.0)² = **2.140×**; with trench = (2.926/2.7)² = **1.174×** ⇒ **the trench pays back
85 % of the density penalty and no more**, and the remainder is the bill. Cancellation exact only in
the short-base limit: across 4 orders of τ the ratio drifts **< 0.05 %** (test pins the drift, not the
overclaim).

**DRIFT INVERTS THE HOUSE PATTERN:** boron k<1 ⇒ ρ falls down the boule ⇒ trigger RISES (51.5 mA at
z=0 → 74.0 at z=0.9) ⇒ **the FIRST wafers off the boule are the vulnerable ones**, opposite to every
other knob ([[fab-game-g2]]).

**S4 — the substrate is the lever the geometry cannot be.** `R = ρ_epi·t_epi/A + ρ_handle·path/A` —
**both terms kept**, because the handle's term is a **floor** (thinning stops paying; 1008 mA here).
Improvement is **DOMINATED BY** tap-path/t_epi (ρ cancels ⇒ geometry) and **always short of it** by
exactly the handle term — asserted both ways, since equality would make the floor a fiction. Same
wafer + same disturbance + same isolation, only the substrate changes ⇒ the scrapped part survives, and
the loop gain is **exactly** unchanged. Cited *optimum* thickness NOT reproduced (needs the vertical
pnp). **Not F6** — device numbers byte-identical.

**Not tuned to fail:** default margin ~26×, stays. Tests that need a latched wafer raise the *injected
disturbance*, never the house geometry.

**Card REWRITTEN not graduated:** the STI *process* is still unbuilt, but its gate is now sharper —
a trench recipe adds **no observable B12 has not delivered**. **F6 trigger RECORDED** (one sentence,
not argued): latchup trigger current reads substrate resistance ⇒ re-check F6's gate.

## The 2026-09-06 follow-on batch — the player surface, and a live bug it exposed

Asked for two things: an F6 re-check (the trigger B12 recorded) and a **deliberate wafer-kill moment**.
The user's standing policy was amended first — a whole-wafer kill is now explicitly WELCOME when the
physics really is all-or-nothing, which retroactively blesses S2's refusal to grade
([[gradual-failure-preferred]]).

**A LIVE BUG, and the most valuable thing in the batch.** `targets.regrade` carried the wafer-level
**flatness** scrap into a sibling target's verdict but **not the latchup one** — B12 added the second
scrap on the explicitly-stated "same precedent" as the first and never updated the re-grade path. At
`N_seed = 2.5e15` a wafer the line scrapped on latchup re-graded as the high-res part to **37/37 passing**
— a shorted wafer sold whole. Masked at most other dopings only because some *other* window happened to
catch the die, which is why no test saw it. Fixed (read off the isolation step's own record, exactly as
`pipeline._test_wafer` does) + pinned. **The rule:** flatness is target-relative (a part may tolerate more
bow) so `regrade` re-checks it; latchup is a pass/fail the LINE computed — target-INVARIANT, like the
assembly scrap.

**THE TRAP — where the kill actually lives.** The kill could NOT be homed on the default logic product:
its `V_t` window rejects every substrate light enough to latch, so latchup is masked there *everywhere*
(pinned as a test, since the obvious "harmless until isolation" test is FALSE). It belongs to the
**high-res** family, whose window deliberately opens on the light substrates logic rejects: the window
runs **2.5e15 → 1e16** and the latchup crossing at **~2.7e15 falls INSIDE it**. So the lightest sliver of
a legitimate published spec passes every one of its own criteria and is still scrap — and the player is
*pulled* there, because lighter buys both the native low `V_t` and `BV ∝ N_A^-3/4`. `demo_latchup_trap.py`
(gallery B12, 21st fab-game demo) + `journey.substrate_trajectory` (see it coming) + the forecast naming
**GROW** not the isolation stage (attribute it afterwards).

**Journey levers added:** `grow(pull_rate, N_seed=...)` (doping is committed AT growth) and a new
`isolate(scheme)` stage — both true seams. `_dominant_channel` learned the two wafer-level roots; before,
it fell through to the reason verbatim, which says *what* happened but never *which decision* armed it.

**The F6 re-check verdict — NOT the house released-gate pattern.** 5th card pickup, but unlike the
previous four the stated gate was **not** found released: it was aimed at only one of three legs. Card
split — resistance leg BUILT, retrograde-well leg STILL DEFERRED (genuinely overlaps F1), **out-diffusion
leg PROMOTABLE**. The finding that promotes it: B12's own floor sits at **0.025 µm**, 12× below the
thinnest layer its figure plots, so *nothing in the model stops thinning*; the limit that really binds is
handle dopant out-diffusing up into the growing layer (`√(Dt) ≈ 0.05–0.7 µm`, from the tree's own Fair
`D(T)` + charge-state `D(N)`). Robust claim = the **order of magnitude**, not any floor value (growth T/t
are house numbers). Discriminator = **Sb creeps least** — which is *why* Sb is the real buried-layer
dopant. The B12 figure caption ("thinning stops paying here") was **overstating** and was corrected as
part of this finding. Written up in `docs/plans/future-steps.md` → "The F6 re-check".
