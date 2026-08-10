---
name: strained-silicon-f5
description: "F5 strained silicon — chosen over F8, S1+S2 BUILT 2026-08-10; the carrier fork, the elasticity bound, the first non-additive knob, and the falsified roadmap card"
metadata: 
  node_type: memory
  type: project
  originSessionId: a2c43319-403d-4ea8-b282-cb56454922b7
  modified: 2026-08-10T08:11:11.953Z
---

**F5 = strained silicon** (roadmap card title: "SiGe strained source/drain"), **PLANNED 2026-08-10**,
plan at `docs/plans/strained-silicon-f5.md`. Chosen over **F8 (CMP)** — F8's *conceptual* gate was
released by [[beol-interconnect-source]], but its remaining gate is a **refactor** (F4's wire geometry is a
module-level house line, so per-die dishing needs the cross-section to become per-die *before* any CMP
physics lands), whereas F5's gate was already lifted by an argument written at P4.

**S1 BUILT 2026-08-10** (`chip/strain.py` + tests, fast lane 1132 → 1151) — the build's own findings, incl.
the elasticity **definition** trap, live in [[strained-silicon-source]].

**S2 BUILT 2026-08-10** (`DeviceKnobs.strain` + `fab_game/tests/test_strain_knob.py`, fast lane 1151 →
1164). `device.py`, `spec.py`, `state.py` all untouched. Four things the build settled:

1. **THE STRUCTURAL BREAK — the first game knob that is NOT additive.** `bv_V`/`t_rr`/`j_gate`/`τ_total`
   each bolt a *new* output onto an unchanged device ⇒ engaging one alone changes nothing scored, and
   [[beol-interconnect-source]]'s F4 needed the **pair** (knob + delay binning). Strain moves `I_Dsat`
   itself — the currency `SpeedBins` has graded since G6 — so **the knob alone re-grades the wafer with no
   new scoring surface**. Strain is a *process* change to a *device term*, not a reading beside one.
2. **But the re-grading is a claim about the LADDER, not about sorting.** Strain is common-mode and
   **multiplicative** (every die × the same factor) ⇒ CV unchanged, rank order exactly preserved; the whole
   graded population lands `premium` only because the level moved under fixed edges. **Mirror of F4**,
   whose common-mode `τ_wire` was *additive* and therefore **compressed** the relative spread. **CONTROL**
   (F4's `τ_wire=0` identity in F5's currency): scale the `I_Dsat` window **and** every bin edge by the same
   factor and the wafer returns **grade-for-grade, verdict-for-verdict identical** ⇒ both game effects are a
   level shift and nothing else.
3. **The uncomfortable half, recorded not tuned: the win COSTS YIELD.** `DEFAULT_SPECS`'s `I_Dsat` ceiling
   was written to catch *CD-collapse over-current* (on an unstrained line, 20% over-current ⇒ wrong
   geometry). Strain lifts the histogram exactly that far with geometry bit-for-bit correct ⇒ a loose-CD
   wafer goes **89/89 → 77/89**, all `I_Dsat`-high, no new failure mode. A **spec** artefact; re-centring
   the window is a market call (F4's binning-edge class) and doing it quietly would be the
   [[gradual-failure-preferred]] fudge.
4. **Pass the seam, don't branch around it.** `strained_channel(MU_N_EFF, None) == MU_N_EFF` exactly *is*
   `saturation_current`'s default ⇒ one call site, and **every default run exercises `chip.strain`'s seam
   per die** (`test_seam.py`'s `i_dsat == demo_device.compute().i_dsat` = standing proof). A branch leaves
   that path untested consumer-side. The F4 composition stayed **one test**, asserted as structural
   identities (`τ_wire` byte-identical, `τ_gate` ∝ inverse drive ratio) — *not* `∂ln f/∂ln I = 1−wire_share`,
   which is an exact derivative and would need a tolerance over a finite +20% step.

Remaining: **S3** the B10 history mode + demo, **S4** uncommitted.

**The observable:** `µ` is the **one factor in `I_Dsat` no process step has ever moved** — `MU_N_EFF = 450.0`
has been a module constant since Phase 4. Strain is a *mechanical* state, so F5 is the first device number
that moves without changing a dopant, a thickness, or a length.

**Three decisions the plan settles before any code:**

1. **The seam PREDATES the slice.** `saturation_current(..., mu_eff=MU_N_EFF)` (`device.py:441`) has carried
   a defaulted mobility argument since P4 ⇒ `device.py` untouched for the **4th consecutive slice**
   (after [[high-k-gate-f3]], [[historical-modes-b7]], F4). **Trap: do NOT rescale `MU_N_EFF` in place** —
   `test_device.py:300` computes `beta` from it by hand and would silently re-baseline instead of failing.
2. **The carrier fork.** SiGe S/D is a **pMOS** technique; the sim is n-channel-only (`device.py:9`, no
   polarity switch — *verified*, not assumed). Rejected: adding a pMOS (= "add CMOS to the simulator",
   scope), and computing a p-drive-current for a device that doesn't exist (decoration — weaker than F4's
   3-rung seam, whose middle rung was a *real* quantity nobody read). **Decided: carrier-generic module
   returning mobility ENHANCEMENT FACTORS** — a material/carrier property, not a device output, so the hole
   entry is honest data with no p-MOSFET behind it. **Wired leg = nMOS tensile nitride cap**; SiGe stays as
   the compressive twin + the demo contrast ("the two carriers want opposite strain signs" = the era's real
   answer). Both legs cited from the **SAME Intel 90 nm paper**, so the unwired leg is not better-sourced
   than the wired one (the inversion worth checking, checked).
3. **The magnitude trap, and the primary source hands over the number.** Long-channel ⇒ µ→I elasticity **1**;
   the 90 nm device is **velocity-saturated**. Cited: holes **>50% µ → +25% drive**, electrons
   **+20% µ → +10% drive** — **elasticity ≈ 0.5 on BOTH carriers from one paper** (report the coincidence
   *as* a coincidence), and **100% µ → 35% drive at L = 25 nm**, so it **degrades as `L` shrinks**.
   ⇒ **headline the mobility**, label the drive read an **upper bound with its direction named**, velocity
   saturation named-not-built, and **explicitly NO elasticity knob** (that is the [[gradual-failure-preferred]]
   fudge shape). **Bound it at S1** — F4's S1 shipped an unbounded headline and the review forced a
   retraction S2–S4 all inherited.

**A caveat I had assumed, CORRECTED by the sources:** "strain enhancement erodes at high vertical field" is
a **BIAXIAL** result. Intel's **uniaxial** S/D strain explicitly *survives* it. So the most obvious S4
mechanism ("strain doesn't scale") is dead on that leg, and **S4 stays uncommitted** (F4's anti-front-load
discipline).

**Also flagged:** the "~2 GPa @ ~20% Ge" and "up to 100% hole-µ" figures on the roadmap card are a *biaxial*
range top and an unsourced GPa — do not headline either. Cited Ge% is **17%**.

**FINDING — a published card's `gate` had already been falsified; FIXED 2026-08-10 (commit `9ece311`).**
`roadmap_gallery.py` **and the stamped schematic** both claimed *"a µ(strain) model in `device.py` — none
exists yet"* (false), *"up to ~2× at ~20% Ge"* (biaxial range top), and *"~2 GPa"* (unsourced) — all three
corrected, card status → *Planned*, card itself stays up until the last slice per [[roadmap-page]]'s
graduation rule. Fixed **immediately rather than at S1** because editing the `future-steps.md` triage row
had already broken the card↔triage **verbatim** pairing (`roadmap_gallery.py:61`), and deferring would ship
a knowingly-broken invariant.

**⇒ THE DURABLE RULE (recorded in the `SLICES` header): a card's `gate` is a claim about the CURRENT TREE,
and the tree moves under it. When a slice is picked up, RE-CHECK ITS GATE AGAINST THE TREE FIRST.** This
was the **second** gate found already-released (F8's by the F4 build), and **both times it was found by
someone going to build the slice, never by a test**. Nothing pins gate↔reality: the manifest guard pins
card↔schematic, the goldens pin page↔renderer, so between them they confirm the prose did not **CHANGE**,
never that it is still **TRUE** — F4-S4's named failure mode.
