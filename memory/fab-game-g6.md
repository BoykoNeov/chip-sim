---
name: fab-game-g6
description: "fab-game G6 BUILT — chip/packaging.py (cumulative assembly-yield funnel Πyᵢ) + game-side speed binning; the back end, line now complete sand→binned chip"
metadata: 
  node_type: memory
  type: project
  originSessionId: af9f62ce-8ebb-4040-af52-740987896b9f
---

**project (2026-06-13):** **G6 BUILT** — the **back end**: assembly-yield funnel + final-test
**speed binning** (plan §6 G6, §5 step 9). The line now runs **front-to-back, sand → a binned,
packaged chip**; G6 is the last *physics* G-step ([[fab-game]] — G7 is the roguelike shell, not new
physics).

**New cited physics `chip/packaging.py` (triad 15) — SINGLE-HEADED on purpose.** The **cumulative
(multiplicative) assembly-yield funnel**: a part must survive every back-end op (dice→attach→bond→
encapsulate), so `Y_assembly = Π yᵢ` (`assembly_yield(*ys)`; `expected_packaged(n,*ys)=n·Y` = the
convergence-target count). Cited **yield funnel** (Sze *VLSI Technology* yield ch. — same text as
[[fab-game-g3]]'s defect law; May & Spanos Ch.5 cumulative-yield; Tummala assembly-step decomposition).
**Triad honesty (advisor):** tight = `yᵢ=1` ⇒ Y=1 **bit-exact** seam (+ single-step returns itself);
identity = **multiplicativity** `Y(A∪B)=Y(A)·Y(B)` + `yⁿ` (genuine, *status* of [[fab-game-g3]]
area-additivity) — **BUT the algebra is structural**: that `Πyᵢ` is the *only* independent-composition
law is validated by the **REALIZATION**, not the arithmetic → the load-bearing non-circular leg is the
**game-side per-die Bernoulli → empirical packaged yield → Πyᵢ** (LLN convergence, exactly G3's
placement→`exp(−D₀A)`). Benchmark loose = flagged `ASSEMBLY_STEPS` per-step yields + monotonicity
orderings (the numbers are house; only forms/orderings asserted).

**THE advisor trap (the one that would've cost a dishonest leg): binning is NOT physics.** My resolved
plan had a Gaussian `bin_fractions(μ,σ,edges)` "convergence" — advisor killed it: **near-tautological**
(bin your own Gaussian draws against your own CDF) AND the game's realized `I_Dsat` is **nonlinear /
non-Gaussian** (Bossung+etch+`W/L`, tiny die sample) so it would NOT converge. The convergence story
belongs to **assembly only**. Binning = a **grading policy** (ADR 0005 §1) → **game layer,
deterministic partition**: `SpeedBins`/`SpeedBin` in `spec.py`, `assign(i_dsat_mA)→label-or-reject`,
default = **one open bin "pass"** (the seam). So `chip/packaging.py` carries **only** the assembly
funnel (focused, not two-headed).

**Game wiring:** `PackagingKnobs` (4 per-step yields, all default **1.0** = seam); `packaging_step`
runs **after** the front-end `test` step (back-end). The assembly kill = a per-die **Bernoulli gated on
`assembly_yield<1 AND variation.enabled`, drawn LAST** (the [[fab-game-g5]] conditional-draw-last trap
again: perfect back end / NO_VARIATION → no draw → **G1–G5 byte-for-byte unchanged**; assembly loss is
*stochastic*, gated on the variation layer like the G3 killer-particle scatter). Binning sorts survivors
by **`I_Dsat` as the speed proxy** (clock speed ∝ drive current). `Die` gains `assembled` + `bin`. A
non-survivor = **assembly scrap** (functional kill, **irreversible** — cracked die=scrap); a too-slow
survivor = **bin-out** (`bin="reject"`, a *working but out-of-grade* fail, distinct from a front-end
parametric fail). `diagnose` names both. **Front-end-failed dies are NOT packaged** (no double-count) —
the **four-way partition** {front-end fail / assembly scrap / bin-out / binned-good} tiles the map,
good+bad=total closes; the `packaging` provenance summary carries the **funnel** (front→final yield) +
the bin histogram.

**The advisor done-check caught a latent bug (blocking-ish):** `packaging_step` runs *after* `test`,
but `rework_litho`/`rework_polish` re-score any `verdict.failed` die through `_verdict_die`, which only
checks geometry/defect/resolved/voided/parametrics — **never `assembled`/bin-out**. So a back-end
assembly scrap (verdict.failed, `assembled=False`, but fine front-end params) would re-pass on
re-exposure → **resurrected a cracked die** (incoherent `passed ∧ assembled=False`), contradicting the
"cracked die = scrap" invariant. Latent (every test/demo runs *default* packaging → no scrap at rework
time → green), but a player reworking a lossy-assembly wafer hits it. **Fix:** both rework loops now
skip dies with `assembled is not None` (reached the back end) — only front-end fails (`assembled is
None`) are re-attempted; a back-end death stays dead, never counted recovered. (Also gated the
`diagnose` etch line on `bias>0` — G6 made diagnose run on clean-etch deaths → a contradictory "etch
bias 0.0 nm shrank the CD" line in the trail.) Lesson: **adding a post-`test` failure mode means every
rework path must learn which failures it can/can't reverse.**

**Pedagogy (the G6 win):** binning turns **process spread → a value distribution** — a *tight* process
(default CD control) fills the premium bin; a *loose* one (poor line-width control, `cd_sigma`) spreads
the grades and **bins a tail OUT**; and the headline "**works but never shipped**" point — a back-end
assembly scrap with a **perfect front end** (V_t/CD/I_Dsat all fine). Banked `demo_packaging` /
`fab-game-g6.png` (3 panels: the assembly funnel narrowing at the wire-bond | tight-vs-loose `I_Dsat`
bin histogram | the packaged-outcome wafer map). Extended `run_line` (the `test` step is **no longer
last** — `packaging` is); updated `test_provenance_is_append_only` (+`packaging` on both step lists).
Default knobs (perfect assembly + one open bin) ⇒ the seam.

Fast lane 451→**476** (+25: `chip/tests/test_packaging.py` 9, `fab_game/tests/test_packaging.py` 12 —
incl. the advisor-caught **rework-guard** test — `test_demo_packaging.py` 4); **no engine amendment, no
ADR, no chip gallery card**. **Rebond named &
DEFERRED** (plan's "rebond rare; cracked die = scrap" — the reworkable/irreversible contrast is already
banked at [[fab-game-g4]]/[[fab-game-g5]], so cracked=scrap is the honest default, no new rework path).
Next = **G7** (roguelike framing + scoring + Textual TUI; sandbox) — the game shell over the now-complete
sim, no new physics. [[fab-game-g5]] [[engine-unfrozen]]
