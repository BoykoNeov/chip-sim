---
name: device-targets-plan
description: "\"good is relative\" multi-target specs — SLICE 1 BUILT (fab_game/targets.py: DeviceTarget + FAST_LOGIC/LOW_POWER + regrade/disposition); 2-level declaration; 5-slice staging, S2–S5 still planned"
metadata: 
  node_type: memory
  type: project
  originSessionId: ed2a8058-2e3f-4914-86c8-d4b78172b743
---

**`docs/plans/device-targets.md` — PLAN WRITTEN 2026-06-15; SLICE 1 BUILT 2026-06-15.** The next front-end
direction after the journey (user-initiated): the *same* physical property is good for one product,
bad for another — "**good is application-relative**" (the DTCO lesson). A **declare-a-target** strategy
layer + a **disposition/salvage** mechanic re-scoring the same wafer against sibling specs.

**SLICE 1 (the zero-new-physics spine) BUILT — `fab_game/targets.py` + `tests/test_targets.py`:**
`DeviceTarget(name, specs, prices, optimum_hint)` (specs EMBEDS the speed bins — DRY with `SpecSet.speed_bins`,
NOT a separate field). `FAST_LOGIC` = `replace(DEFAULT_SPECS, speed_bins=MARKET_BINS)` + `BIN_PRICES` (the
incumbent; declaring it == the pre-targets game **bit-for-bit**, value-equality seam). `LOW_POWER` = crossing
`V_t∈[0.60,0.85]` (overlaps logic's `[0.45,0.68]` only on `[0.60,0.68]`) + lower-FLOOR-only `I_Dsat∈[2.0,4.2]`
(low drive = a FEATURE) + own lower bins (premium≥2.7) + own prices. `MOSFET_FLAVORS=(FAST_LOGIC,LOW_POWER)`
(one family, dispositionable; cross-FAMILY re-grade NOT offered). **`regrade(wafer,target)`** re-scores a
FINISHED wafer's dies against a sibling's windows+bins — **zero new physics, never re-fabs** (advisor's
load-bearing call: re-running the line would shift the assembly-RNG order → physics-irrelevant drift);
preserves physical functional kills + the irreversible `assembled is False` scrap; `assembled is None`
(declared-target front-end-fail, now passes sibling) → SHIPS, **exact at the lossless default back-end**
(only a lossy back-end opens the gap — deferred, no RNG re-draw). **`disposition(wafer, targets)`** = the
"which SKU?" menu, best-revenue-first (wafer cost sunk). **Wiring:** `MARKET_BINS` MOVED game.py→targets.py
(broke the game↔targets cycle); `GameConfig.market`/`prices` fields REPLACED by one `target: DeviceTarget =
FAST_LOGIC` (no caller passed market/prices); `specs`/`prices` now derive from it. **Calibrated against the
real line FIRST** (advisor): oxide sweep 18min→FL strictly wins, 26min→LP strictly wins (the **crossing**,
not an argmax — argmax ties on the overlap); deep-cut z=0.85 → V_t 0.71 (FL-reject) ships LP at 100%/premium
= the harvest headline. **Blind spot left noted (non-blocking):** `journey.forecast`/`boule_profile` still
band against `DEFAULT_SPECS` (coarse "did it bite" guide, not a SKU verdict) — a target-aware forecast is a
later UI slice; `finish` already scores the real wafer against the declared target. 331 fab_game tests green
(2 PRE-EXISTING gallery-HTML staleness failures from the phase-5 commit, NOT mine).

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
