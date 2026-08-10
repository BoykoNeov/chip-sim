---
name: strained-silicon-f5
description: "F5 strained silicon — COMPLETE (4 slices, card graduated) 2026-08-10; the carrier fork, the elasticity bound, the first non-additive knob, the falsified roadmap card, the flattering-direction trap, and the bracket-not-a-curve finale"
metadata: 
  node_type: memory
  type: project
  originSessionId: a2c43319-403d-4ea8-b282-cb56454922b7
  modified: 2026-08-10T09:23:07.431Z
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

**S3 BUILT 2026-08-10** (`chip/demo_strain_history.py` + test; **B10**, the 10th timeline rung, slotted
**B8 → B10 → B6** — the timeline is *process* order, not chronological. Fast lane **1165 → 1175**,
measured at `HEAD~1` in a worktree; the S2 note's 1164 was off by one). **No wrapper** (open question 3
closed): rides `chip.strain` directly, the B7/B8/B9 precedent. What it settled:

1. **THE DURABLE ONE — a display-layer composition with a prior slice can be wrong in the FLATTERING
   direction with every input cited.** The B10 wall was first sketched as an *exchange rate* against B8:
   "the oxide thinning that buys the same +20% drive costs N decades of gate leakage." No bad citation
   needed to overstate F5 — only the naive `I ∝ 1/t_ox` read, which is wrong because thinning **also
   drops `V_t`**, so drive rises *faster* than `1/t_ox` ⇒ **less** thinning suffices ⇒ the rival lever is
   **cheaper** than naive says. **The fix is the general move: find the STRUCTURAL claim under the
   numerical one and demote the number to a flagged band.** Here: `high_k.gate_leakage` takes a thickness
   and a dielectric — **mobility is not one of its arguments** ⇒ `∂J_g/∂µ = 0` *structurally* (B9's
   `∂τ_wire/∂I_Dsat = 0` shape; F3/B8's "one thickness, two currencies" inverted to **one knob, one
   currency**). Pinned as a bit-for-bit identity under an *absurd* mobility, so a future µ→gate-stack path
   fails a test instead of silently turning a structural fact into a coincidence. Same class as the
   [[gradual-failure-preferred]] fudge but at the **figure** layer, which is new.
2. **The surviving exchange rate is quoted in the direction that does NOT flatter the slice.** Two
   defensible conventions differ ~2×: fixed channel doping (`V_t` sags, an 8% thinning suffices) =
   **≳0.90 decades**; re-adjusting `V_t` per rung (what a fab does, `I ∝ C_ox` exactly) = **≳1.88**. The
   demo headlines the **cheap** one and a *test pins that ordering* — flipping it rounds the win up
   (F4's `floor_decades` rule in the leakage currency). **The band is recipe-carrying; the zero is not.**
3. **The period is a POINT, not a curve** — and that recurs for *every* "no process ever touched this
   term" slice. B5–B9 each draw a period *line* the modern one departs from; an unstrained channel is the
   factor `1.0`, so the only honest drawing is the point **both paths leave from** — which puts the seam
   on the *figure*, not just in the API (`strained_channel(MU_N_EFF, None)` **is**
   `saturation_current`'s default, so they start together by identity).
4. **The unwired leg must be marked cited-only ON THE FIGURE, not only at the API.** The plan rejected a
   computed p-drive as decoration; two bars side by side re-introduce exactly that read at the display
   layer. Each mechanism is captioned on **its own side of the zero** (the fork drawn literally), the hole
   bars say `CITED DATA ONLY (no pMOS)`, and the demo prints `nmos_mobility`'s raised message **verbatim
   and soft-wrapped** — truncating it cut after the *fact* ("is a pMOS technique") and lost the *reasoning*.
5. **Two review catches worth the pattern.** The bound panel must be built from `long_channel_drive_factor`,
   never by sweeping `strain.elasticity()` (which *raises* at µ ≤ 1, and the axis starts at exactly 1.0).
   And a "this demo never computes X" guard written as a **token blacklist is evadable by aliasing** —
   `"wire_share="` never matched the legitimate `1 − wire_share`, and `ic.delay(...)` would have walked
   past it; re-anchored on the **import lines**, the one spelling that cannot be dodged.

The F4 composition stayed **off every axis** (trap #3): stated in `print_summary` as the exact law
`∂ln f/∂ln I_Dsat = 1 − wire_share`, never evaluated — a 90 nm line is deep inside `interconnect`'s bulk
refusal.

**S4 BUILT 2026-08-10 — "why the era ended"; F5 COMPLETE and the card GRADUATED** (fast lane
**1174 → 1180**; the S3 note's 1175 was the same tree counted *including* the one `slow` notebook test —
same commit, different convention, not an error to correct). The pre-registered candidate (*"a one-time
boost, not a scaling path"*) survived, but **not in the currency first reached for**:

1. **THE DURABLE ONE — the SECOND flattering-direction slip in two slices, and this time in a helper that
   was legitimate elsewhere.** S4 was first priced in B9's currency: `nodes_bought = ln(x)/ln(0.7)` ⇒
   "+20% drive ≈ 0.51 of a node". **Wrong: `I_Dsat ∝ W/L` and a node shrinks BOTH ⇒ `W/L` is invariant
   and a geometric node buys ZERO drive per device in this model.** The arithmetic silently assumed
   constant-`W`. B9's use was sound only because a **wire's width is its own dimension** — a drive-current
   ratio is not that currency. ⇒ **A house helper carries its OWN slice's denominator with it; re-deriving
   what one node buys IN THE READING SLICE'S CURRENCY is the check.** Dropped entirely: the claim is now
   *repeatability* (a lever pulled once vs a lever pulled every node), which needs **no denominator**.
2. **The delivered gain is a BRACKET between two cited endpoints, never a curve.**
   `delivered_drive_bracket()` takes a mechanism and **no geometry argument** — pinned by a *signature*
   test, because a function taking an `L` and returning a fraction **is** the forbidden elasticity knob
   ([[gradual-failure-preferred]]'s fudge shape) wearing a hat. Two papers, two geometries, two µ
   magnitudes license a **direction and a width**, nothing finer. Model **1.20×** > cited 90 nm **1.10×** >
   cited 25 nm **1.070×**. An inverted bracket **raises** rather than swapping its ends.
3. **THE STRUCTURAL RESULT — the model is blind to the decay BY CONSTRUCTION.** In the
   strained/unstrained ratio, `W`, `L`, `C_ox` and `V_t` **all cancel** ⇒ `MODEL_ELASTICITY` = **1 at every
   channel length**; the sim reports the same +20% at 90 nm and at 25 nm. Asserted bit-for-bit over four
   decades of `L`. **That is WHY the bracket must enter as cited data from OUTSIDE the model** — and the
   third slice running whose payload is a structural zero/invariance (S3's `∂J_g/∂µ = 0`, B9's
   `∂τ_wire/∂I_Dsat = 0`). The treadmill is its price form: the same +10% drive costs +20% µ at 90 nm and
   **+28.6%** at 25 nm.
4. **NECESSITY WAS THE REAL GATE, and it was nearly a NO.** S3's right panel *already drew* both cited
   elasticity lines ⇒ a re-cut figure would have been a restatement, and the honest alternative was
   graduating with S4 **named-not-built**. S4 earns its place only because it changes what the **module**
   can say. **Write that sentence before building a finale slice.**
5. **Graduation is the bigger half and it is what ends up half-done.** Enumerated before coding:
   `SLICES`+`FIGURES` cut together (manifest guard), the banked `roadmap-f5.png` **deleted**, the
   graduation paragraph in the comment block (now three), `future-steps.md`'s **row AND the queue prose**
   (F8 inherits the head — **by default, not by strength**; its refactor gate is unchanged, so the next
   pick is worth re-triaging rather than taking from the top), the plan STATUS, and the gate re-check over
   F6–F10 (`GLOBAL_WIRE_LENGTH_UM` still a house line, `engines/` still 1-D+2-D ⇒ none released).

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
