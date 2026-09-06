---
name: cmp-planarity-f8
description: "F8 CMP / planarity, COMPLETE (4 slices) — S1 the s/(1−s) law + erosion-not-dishing, S2 the game knob (the wire's first per-die spread), S3 the B11 demo, S4 the SECOND F4 clause to go (the polished wire costs PARTS, not just grades); card graduated"
metadata:
  node_type: memory
  type: project
  modified: 2026-09-06
---

**F8 = CMP / planarity**, plan at `docs/plans/cmp-planarity-f8.md`, historical mode reserved **B11**.
Chosen off the post-F5 re-triage (2026-08-19). Its published gate ("F4's geometry is a module-level house
line ⇒ a refactor") was **false on re-check** — `delay()` already took `WireGeometry` as an argument and
`Die` already carried `radius_frac`; the third gate on the roadmap page found already-released, all by
someone going to build (see [[roadmap-page]]). Decided: the stale card **graduates at S4**, not corrected in
flight.

**The observable** (the plan's licence): F4's `∂ln f/∂ln I_Dsat = 1 − wire_share` was derived under "τ_wire
contributes no spread of its own", and that clause was true of the tree only because `steps.py` read a
default-constructed `WireGeometry()` on every die. CMP is the step upstream of the wire ⇒ **F8 modifies
F4's premise rather than decorating it**: a chip-speed spread with a non-transistor source.

**S1 BUILT 2026-08-19** (`chip/cmp.py`, 38 tests). Headline closed form **`overpolish/t_over = s/(1−s)`** —
no house constant; exactly 0 at s=0 ⇒ *dishing is bought by non-uniformity and nothing else* ⇒ the fix is
polish **uniformity**, never polish *less*. Window collapse `s_crit = L/(2+L)`; `polish_window_um` returns
`None` past it. Preston `RR=K·P·V`: at matched speeds `|v_rel| = ω·d` at EVERY point (derived) ⇒ **V cannot
carry a radial signature, P must** (F4's "R story not C story" shape). Primary source (Park et al., VMIC
1998, read in full) **refutes** the tidy secondary split (dishing←width, erosion←density): Fig 4b dishing vs
density non-monotonic (peaks 60–70 %), Fig 6 erosion depends on pitch. Built each on its primary axis, cross
terms named-not-built. **Scale gap is two numbers**: nearest measured pitch ≈4× the sim's (monotone legs
port), break point ≈200–400× (refused). Fig 5's log-linear dishing crosses zero at ~1 µm ⇒ `dishing_efficiency`
returns **exactly 0** sub-micron ⇒ **at the sim's scale the loss is an EROSION story**. `DISH_SCALE` is a
**calibration** (the source normalizes its dishing axis) and is quarantined by an invariance test — quoting
its 25–90 % band match as a cross-check would be the F5-S3 flattering-direction trap one layer down.

**S2 BUILT 2026-09-02** (`CmpKnobs` + `Recipe.cmp`, `cmp_step`, `Die.metal_thickness_nm`/`shorted`/
`polished_out`, `chip/cmp.py` §5 radial chain; `test_cmp_knob.py` 24 + 10 chip-side; fast lane 1218 → 1252).

1. **The earning assertion in its sharpest form:** zero variation ⇒ one transistor on every die (one
   `I_Dsat`, one `τ_gate`) and the delay STILL spreads, monotone in radius. `1 − wire_share` is per-die.
2. **Two seams.** `polish_s=None` ⇒ *no step at all* (no record anywhere; bookkeeping step list untouched).
   Engaged at the clear-everywhere time ⇒ the **centre die is byte-for-byte F4** (the slowest site removes
   exactly the overburden) and the `s/(1−s)` overpolish lands on every other die; `s=0` at the clear time
   ⇒ F4 on every die.
3. **Refusal by name, in the registry:** `chip.cmp.DAMASCENE_METALS = ("Cu",)`. Al is subtractively etched
   ⇒ CMP planarizes the dielectric, never the wire ⇒ the observable does not exist there. `None` refused too.
4. **Trench depth is not a knob** (= `WireGeometry().thickness_um`); density = `W/pitch` (the source's
   definition) ⇒ ONE new house number (pitch), and "no loss" ≡ "the F4 wire" by construction.
5. **The short is graded by radius in closed form** (`shorted_radius_frac`, `r² < (t_over/R̄−1+s)/(2s)`);
   pipeline shorted set == `{r < r*}` exactly; the disc grows ring by ring as the polish shortens
   ([[gradual-failure-preferred]] via spatial non-uniformity of the offending quantity). Shorted trench is
   untouched (nominal H): copper left BETWEEN lines. Runaway ⇒ `polished_out` (no conductor ⇒ no delay).
6. **Grading by position:** `DelayBins` anchored on the centre part + identical transistors ⇒ at s=0.2 the
   outer 40/89 fall typical→value, monotone outward, `I_Dsat` histogram a delta.
7. **Magnitudes FLAGGED:** rim copper loss 1.2/2.5/5.7 % at s=0.05/0.10/0.20 (delay +0.9/+1.9/+4.3 %); ALL
   erosion (`dish_loss` exactly 0.0 at the 0.5 µm house pitch) ⇒ the lever is pattern density (dummy fill —
   S3's successor). `PRESTON_K` 1.67e-2 → 2.4e-3 (≈0.5 µm/min; a rate, no headline reads it).
8. **Knife-edge closed:** the clear time is a float boundary; a 1e-17 residual read as a short. `cmp_step`
   snaps a removal within float tolerance of the overburden.
9. **Step order = readout order:** CMP runs after the etch and BEFORE the device step (where `τ_total` is
   computed). Litho rework re-reads the same polished wire (die state).

**S3 BUILT 2026-09-02** (`chip/demo_cmp_history.py` → `chip-cmp-history.png`; `test_demo_cmp_history.py`
10 tests; B11 rung after B9; `hist·B11` gallery card; 4 pages regenerated). Three panels: **the wall** (window
in overburdens; floor `1/(1−s)` = `s/(1−s)` above "just cleared"; `s_crit` **0.275** @ +10 % R-budget, 0.455
@ +25 % — the budget moves the crossing, the closure is structural), **the payload** (B9's own period
transistor by value, `τ_gate` ONE float on every curve; Al flat at 1.39× off-scale; uniform Cu = F4
bit-for-bit; the real polish bends +0.9/+1.8/+4.3 % at s=0.05/0.10/0.20; a 10 %-short polish shorts the disc
`r < 0.71`, half the area, while the rim is STILL over-polished), **the successor** (`loss = η(d)·2s/(1−s)·
t_over/H₀` — two levers: uniformity, which MUST be pressure (`V ≡ ω·d`), and density (design-rule windows /
slotting / dummy fill over the cited 50–100 µm planarization length); **"polish less" is NOT A LEVER**, on
the figure). The float knife-edge moved INTO `chip.cmp.polish` (the demo hit it too). Suptitle pins the
enabling claim + the `s`-is-a-house-number flag.

**S4 BUILT 2026-09-06** — candidate (b), the composition with the game's grading
(`fab_game/demo_cmp_grading.py` → `fab-game-f8.png`, the `F8` gallery card, `test_demo_cmp_grading.py`
14 tests). **It ends a SECOND F4 clause.** F4 concluded *"a grading loss, never a yield loss"* because
`DelayBins.from_speed_bins` compresses **symmetrically**: a die at a bin edge sits `τ_wire·(1−I_nom/I_edge)`
off it — positive above nominal, **negative below**, so the slow tail is RESCUED from the bin-out. Derived
under the same premise S2 killed. The polished rim carries `τ_wire·(R/R_nom−1)`: strictly positive, no
`I_Dsat` in it ⇒ **the sign is structural, only the size is a house number.**

1. **One wafer, three policies, and a bin-out IS a yield fail here** (`packaging_step` flips the verdict;
   `wafer_yield` counts verdicts). Loose CD control, 89 dies: drive current **2** bin-outs (0.978) → F4's
   true currency **0** (1.000) → polished at s=0.20 **8** (0.910). Transistors byte-identical across all
   three (CMP draws no randomness) ⇒ one `I_Dsat` histogram, three outcomes.
2. **Neither mechanism alone.** Tight transistors + the same polish: 0 (to s=0.22). Loose + no polisher: 0.
   Only together. Lost parts are below nominal AND past r=0.61 — but 37 are below nominal and 60 sit that
   far out, so the loss is a **subset of** that intersection, never the intersection.
3. **THE CORRECTION THAT MATTERS (advisor caught it; my own probe data contradicted my bolded claim).**
   "It withdraws the rescue from a slow die" is true of **1 of the 8**. The other **7 were sellable under
   BOTH prior policies**, one graded `typical`. The real — stronger — result: the polished wire **creates
   bin-outs no grading policy had**, out of parts the old policy called good. The first test's *name*
   claimed the withdrawal while its *body* only checked "below nominal, out at the rim".
4. **Not extra spread — the OPPOSITE sign.** The transistor's own radial trend leaves the rim marginally
   faster (r vs `I_Dsat` **+0.25**), so unpolished the delay gradient is **−0.09**; polished, **+0.45**.
   The polisher **reverses the wafer's speed gradient**; the parts it costs sit where the transistor said
   the dies were fast. Not predicted — found by measuring.
5. **The threshold is drawn, not quoted.** At the knob's default s=0.10 the polisher costs NO part; first
   loss at s≈0.14 loose, ≈0.24 tight. Cranking `s` until one fell off = the `DISH_SCALE`/F5-S3
   flattering-direction trap.
6. **The anchor dissolves at the clear time** — `from_speed_bins` warns hand-picked ps edges manufacture
   the collapse, so the ladder is G6's fractions on the **nominal part**, which at the clear-everywhere
   time **is** the centre die (S2's seam). Two candidate anchors, one object.
7. **Live finding fixed here:** `pipeline.diagnose` hardcoded every bin-out as *"I_Dsat too low…"* — under
   delay grading that credits the TRANSISTOR with a failure the WIRE caused, the exact inverse of the
   thesis. Now forks on the packaging record's `tau_total_ps`.
8. **The sweep is a closed form pinned against the pipeline** (60 wafer runs ≈ 15 s of fast lane): each
   die's recorded `τ_gate`/`τ_wire` re-read at the polished thickness, exact because `τ_wire ∝ R` and `C`
   never reads `H` (F4's cited invariance). Pinned at two spreads.

`chip/` untouched by S4 entirely; `device.py`/`interconnect.py` untouched for the **fifth** consecutive
slice. **Card graduated** — and with it the roadmap's *promotable* section is now **EMPTY**, rendering its
emptiness rather than being deleted: nothing left has both a released gate and a named consumer, so the
next slice is a **re-triage**, not a pick off the top (see [[roadmap-page]]).
