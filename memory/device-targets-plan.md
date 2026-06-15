---
name: device-targets-plan
description: "PLAN written (not built) — \"good is relative\" multi-target specs + disposition/salvage; the 2-level declaration honesty correction; 5-slice staging, slice 1 = zero-new-physics spine"
metadata: 
  node_type: memory
  type: project
  originSessionId: ed2a8058-2e3f-4914-86c8-d4b78172b743
---

**`docs/plans/device-targets.md` — PLAN WRITTEN 2026-06-15, NOT yet built.** The next front-end
direction after the journey (user-initiated): the *same* physical property is good for one product,
bad for another — "**good is application-relative**" (the DTCO lesson). A **declare-a-target** strategy
layer + a **disposition/salvage** mechanic re-scoring the same wafer against sibling specs.

**Already graded (don't reinvent):** yield is continuous, and **speed binning** (`SpeedBins` in
`spec.py`, priced in `scoring.py`) already IS "functional-but-suboptimal" (the bin-out = a working
out-of-grade part). The NEW lever = multiple targets with **partially-inverted** spec windows on the
*same* wafer (today there's ONE `DEFAULT_SPECS` = fast-logic).

**THE honesty correction (user probed "is harvest-the-tail real?", advisor-confirmed) → a 2-level
declaration:** (1) **device family** = mask/structure, committed UP FRONT, CANNOT salvage across
(logic-family vs power-family); (2) **flavor within a family** (logic↔low-power↔HV-I/O share a base
flow) — an off-target lot CAN be dispositioned to a sibling = real *engineering disposition / MRB*
(the salvage path, NOT the main loop). Reassigning a finished wafer to a genuinely DIFFERENT device
(logic→power rectifier) is **NOT real** (mask commits structure) → the rectifier is its **own declared
run**, never a harvest.

**Inversions spread across steps (NOT clumped on oxide):** growth=substrate resistivity (low-R logic vs
high-res HV/RF breakdown) + oxygen (donors-bad vs gettering-good); diffusion=junction depth (shallow vs
deep); oxidation=`t_ox` (thin vs thick); lifetime=deep-level metals (killer vs fast reverse-recovery).
**Two KINDS, keep separate (advisor):** **cross-target** (resistivity/junction/oxide/lifetime = market
segmentation, powers the mechanic) vs **dual-use** (oxygen within ONE device = a process-trade-off
lesson, its own slice/framing). **Physics tripwire:** do NOT conflate gate-oxide *dielectric* breakdown
(~10 MV/cm SiO₂) with junction *avalanche* breakdown (BV∝N^−3/4, Sze); reverse recovery `t_rr∝τ` — keep
new outputs CITED, not house-fudged.

**TWO empirical gates FIRST (verify like phase-5's two-sided window):** (1) the target windows genuinely
**CROSS** (partially disjoint, NOT nested — else logic⊂low-power → trivial re-grade, teaches nothing;
e.g. logic V_t[0.45,0.68] vs low-power[0.60,0.85]); (2) the declaration actually **MOVES the recipe
optimum** (else cosmetic relabeling — low-power *wants* the deeper-cut/thicker-oxide that the phase-5
over-oxidation corner shows STARVES logic). **Agency (user):** maximize choice now, narrow later; player
PICKS the disposition + DECLARES the target; educational `guide.py` explains each readout *relative to
the declared target* + walks the pick.

**5-slice staging (one journey-phase-sized each, new physics rationed):** S1 = the **zero-new-physics
spine** (`DeviceTarget` = SpecSet+bins+prices+optimum-hint; up-front declaration; disposition readout;
built on the PROVEN logic↔low-power V_t/t_ox crossing; tests = the 2 gates + bookkeeping + the
declare-FAST_LOGIC seam). S2 = HV-I/O + cited avalanche BV. S3 = resistivity inversion at growth. S4 =
the oxygen dual-use. S5 = the power-rectifier family (own run, cited `t_rr`). Only S1 fully specified.
Intersects the journey's #1 open item (the cost side — per-target price curves). [[fab-journey]]
[[fab-game]] [[gradual-failure-preferred]] [[scope-edge-backlog]]
