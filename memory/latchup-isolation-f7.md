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
