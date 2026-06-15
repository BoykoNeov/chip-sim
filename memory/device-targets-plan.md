---
name: device-targets-plan
description: "\"good is relative\" multi-target specs — ALL 5 SLICES BUILT, plan COMPLETE (targets.py: DeviceTarget + FAST_LOGIC/LOW_POWER/HV_IO + regrade/disposition; S2 cited junction avalanche BV chip/breakdown.py; S3 high-res NATIVE part on the substrate axis; S4 oxygen DUAL-USE internal gettering czochralski.py §1h; S5 POWER_RECTIFIER family on the LIFETIME axis — cited t_rr∝τ chip/reverse_recovery.py, the structure/device-family field + family guard); 2-level declaration (family+substrate commits)"
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

**SLICE 2 (HV-I/O flavor + cited avalanche BV) BUILT 2026-06-15 — `chip/breakdown.py` +
`fab_game/targets.py` (`HV_IO`) + `tests/test_breakdown.py`, `tests/test_targets_hv.py`.** The cited
device output `x_j` finally feeds: drain–body junction **avalanche breakdown** `BV` — see
[[avalanche-breakdown-source]]. **THE structural finding (advisor):** the long-channel model makes the
junction-depth axis *align*, NOT cross fast-logic (deeper x_j is fast-logic-neutral-to-good AND HV-good —
the plan's "shallow=logic" reason is the short-channel effect `device.py` omits). The reframe that
dissolves it: **`x_j` is not the crossing axis — it's the axis that DECOUPLES BV from `V_t`** (the curvature
term lets two wafers with identical `V_t` have different BV). So the fast-logic↔HV cross rides V_t/oxide
(HV = the highest-V_t flavor, `V_t∈[0.72,1.10]` crossing low-power's `[0.60,0.85]` from ABOVE → un-nested),
and BV is an orthogonal floor (`6.0V`, FLAGGED) gated by the diffusion **drive-in**. **Physics built from
first principles** (NOT a remembered fit — the advisor's exact trap): a remembered Baliga ln-form fit the
Sze anchor but DIVERGED unphysically at large r_j/W, so BV is DERIVED from the cited ionization integral
`∫α dr=1` (`α=1.8e-35·E^7`) over the cylindrical depletion field → reproduces Sze's 0.24 curvature ratio to
~1% AND Baliga's `BV_pp=5.34e13·N^-3/4` — zero remembered-exponent risk. BV is **uniform per wafer** (x_j/N_A
wafer-level → no ring/core, a clean whole-wafer axis). Seam: BV output + `bv` spec window are OPTIONAL+OPEN
for the logic flavors → byte-for-byte (mirrors `leakage`); HV prices STRICTLY > low-power so a deep junction
flips the best SKU LP→HV (physics gates availability, price ranks). The 2 gates re-proven on the drive-in
axis (BV decouples from V_t at fixed oxide; deep drive-in flips the optimum). Full suite green (the chip
notebook is the known [[chip-notebook-flake]], unrelated). **S3 next** = substrate-resistivity inversion at
growth (turns BV's OTHER knob, `N_A`, for a genuine HV part).

**SLICE 3 (substrate-resistivity axis) BUILT 2026-06-15 — `fab_game/targets.py` (`HIGH_RES` + `substrate`
field + `disposition` substrate-class guard + `HIGH_RES_FAMILY`) + `tests/test_targets_highres.py`. ZERO
new physics** (Option B, advisor-steered — Option A rejected). Turns BV's OTHER knob = the substrate doping
`N_A` itself (`BV∝N_A^−3/4`, set at growth), where S2 turned `x_j`. **THE structural finding (advisor,
verified on the line — the S2 pattern AGAIN):** single-doping model → substrate doping sets **both** BV AND
V_t and moves them **opposite-sign, COUPLED** (1e17→1e16: BV ~5→12V, V_t +0.55→+0.01V *together*; I_Dsat is
`N_A`-independent → V_t/BV the only axes). So resistivity CANNOT give S2's *high-V_t* hv-io its BV (x_j was
S2's lever precisely because it lifts BV *without* touching V_t). **Resolution = the coupling IS the
inversion:** the high-BV part needn't be high-V_t → a high-res substrate runs a **NATIVE** device (MOSFET
*without* a threshold implant) at low/~0 V_t (a logic **REJECT** — *that's* the feature) + high BV. Native
V_t window `[−0.15,0.35]` **DISJOINT** from logic; BV floor `10V` sits **ABOVE the low-R plane-parallel
ceiling** `BV_pp(1e17)≈9.3V` → **physically unreachable** on the logic substrate by ANY drive-in, cleared
only by the lighter boule (`BV≈12V` at 1e16) = a hard **SUBSTRATE** gate. **Substrate COMMIT (advisor):**
resistivity committed at GROWTH → the native part is its **own declared run** (2nd up-front commitment
alongside the device family — new `DeviceTarget.substrate` tag), NOT a same-wafer disposition sibling
(closer to S5 than S1/S2). Both gates re-proven on the substrate axis (two declared runs cross as **mutual
rejection**; declaring moves the growth `N_seed` optimum heavy↔light); `disposition` guard raises on a
mixed-class menu + physics independently makes cross-substrate re-grade ~0%. **DEFERRED named edge:**
high-V_t HV on a light substrate via a channel/drift threshold-adjust implant (**LDMOS**) — implant lifts
V_t but not I_Dsat → high-res+implant would *strictly dominate* logic → crossing dissolves; rescue needs
added mobility degradation = more physics, past slice size (filed w/ A2 Robin-G / E1 heat-mode / CG-3
transient). Native `bv` window is **REQUIRED** (not optional like HV-I/O — BV is the SKU's defining property
& the native low-V_t window won't reject a no-BV die; advisor catch, mirror of S2 nan-guard). 353 fab_game
tests green.

**SLICE 4 (oxygen DUAL-USE = internal gettering) BUILT 2026-06-15 — `chip/czochralski.py §1h`
`internal_gettering_efficiency` + `chip/purification.py` `getter_metals`+`"trace-metal"` grade + fab_game
wiring (`CzochralskiKnobs.forming_gas_anneal_min`/`.internal_gettering_efficiency`; `device_step`
`gettering_efficiency`; diagnose dual-use line) + `demo_internal_gettering.py`/`fab-game-s4.png` + tests.**
The **process-trade-off** slice (NOT segmentation — no new SKU, `targets.py` untouched). Crucible oxygen's
TWO faces on ONE device: liability (C1 thermal donors → V_t↓) + asset (oxygen precipitates **getter**
Fe/Cu out of the device region → leakage↓; cited Tan–Gardner–Tice PRL 64:196 1990 [[internal-gettering-source]]).
**Gate (advisor: BLOCKS — sweep `[O_i]` BEFORE any module): interior optimum exists** — `trace-metal`
feed (base leak 36 nA/cm²) gives a clean **two-sided Goldilocks** (low O→leak-fail, high O→V_t-fail, **9e17–1.1e18
passes both**, leak-fail *just below* / V_t-fail *just above*). **Two advisor structural calls honored:**
(1) **Option B over A** — IG is for MODERATE contamination (10× feed = a purification pass, a *different*
lesson) → demo feed = nameable `0.4×metal`, `O_crit` stays **cited** ~12 ppma≈6e17 (ppma↔cm⁻³=5e16/ppma
atomic frac), efficiency magnitude FLAGGED; (2) **trade-off lives on the `[O_i]` LEVEL not the anneal**
(precipitation consumes the donor O → on the anneal axis effects move *together*, skippable) → donor cost
anchored to the **universal forming-gas/sinter ~450 °C** (<550 °C TD window, web-verified) via new
`forming_gas_anneal_min` (**defaults 0 → C1 seam byte-for-byte**, summed into the effective donor anneal;
`chip.czochralski.thermal_donor_density` untouched) → donors **non-skippable**. **Orthogonal channels
(double-count guard):** gettering touches **Fe/Cu ONLY** (`getter_metals`, never Na/Q_ox/V_t), applied
ONCE in the leak read → V_t byte-for-byte under pure gettering (leak 36.4→1.83, V_t bit-identical).
**EMERGENT FINDING (kept+named, not a fudge):** honest leak off `effective_channel_N_A` surfaces a real
**donor→N_A→depletion-width coupling** (`W∝1/√N_A`→`J∝W`) → below-threshold O makes the diode marginally
leakier + a past-the-cap U-turn, **both deep in already-failed territory** (verdict-relevant leak monotone)
→ window/lesson untouched, NOT the deferred over-precipitation U-shape. **Master seam: no `[O_i]` ⇒ no
gettering AND no donors ⇒ G1–G7 byte-for-byte.** DEFERRED: residual-`[O_i]` partitioning, per-metal
selectivity (Fe vs Cu), over-precipitation/denuded-zone U-shape. Full chip+fab_game suites green.

**SLICE 5 (power-rectifier family = the LIFETIME axis) BUILT 2026-06-15 — `chip/reverse_recovery.py` (cited
`t_rr∝τ`) + `fab_game/targets.py` (`POWER_RECTIFIER` + new `DeviceTarget.structure` device-family field +
`POWER_FAMILY` + `disposition` family guard) + `t_rr` wired through `Die`/`spec`/`device_step` +
`tests/test_reverse_recovery.py`, `tests/test_targets_power.py` + `demo_reverse_recovery.py`/`fab-game-s5.png`.**
The richest, LAST inversion → **plan COMPLETE**. G4b's deep-level metals kill `τ` → leakage `J_gen∝1/τ` (logic
killer); the rectifier reads the **SAME `τ` the OPPOSITE way** — reverse recovery `t_rr∝τ` (charge-control
storage time), so a **short `τ`** (a leaky logic reject) is a **FAST rectifier**: **the lifetime killer is
the feature**. **One cited output, ZERO new lifetime physics** (`τ` IS the G4b reading) — and **DERIVED not a
remembered fit** (S2 discipline): solving `dQ/dt=−Q/τ−I_R`, `Q(0)=I_F·τ` → `t_s=τ·ln(1+I_F/I_R)` (op-point
`K=ln(1+I_F/I_R)` + non-`τ` fall time `t_f` flagged/named); [[reverse-recovery-source]]. **2-level declaration
COMPLETED:** rectifier = a **different DEVICE FAMILY** (diode≠MOSFET, committed at the mask, never a
disposition of a logic wafer) → new **`structure`** tag (`"mosfet"`/`"rectifier"`, the FIRST level) + a
`disposition` **family guard**. Honest subtlety (advisor-grade): rectifier **SHARES the light high-res
substrate** with the S3 native MOSFET (needs the light boule for BV; floor `10V` = the same hard substrate
gate) → the **family guard, NOT the substrate one, is the binding** separator — they cross on the **lifetime**
axis while sharing a substrate. Honesty ceiling NAMED: the line scores the *shared* silicon physics (junction
BV + carrier `τ`) a diode & MOSFET both have, NOT a distinct vertical-diode structure (a declared-run scoring
lens, not a re-fab). **Leakage INVERSION made literal:** rectifier leakage window **OPEN** (the leakage that
fails logic is not its axis) — only gates are `t_rr` (REQUIRED ceiling) + `BV` (REQUIRED floor; both nan-guarded
like S3), `V_t`/`I_Dsat`/CD/NILS open, single `"pass"` bin. **Both gates on the lifetime axis (verified):**
G1 = mutual rejection on the SAME high-res substrate (clean→native-good/rect-reject `t_rr≈6.9e5ns≫500`;
metal→rect-good `t_rr≈69ns`/native-reject leak≈288≫10; metals Na-clean→move `τ` NOT `V_t`/`BV`; bands DISJOINT
`τ`: rect≲0.72µs, logic≳2.88µs, dead-zone between) + a low-R metal wafer is STILL rect-reject on BV (~5V) →
"good-is-relative needs BOTH commits" (lifetime=cross, substrate=gate); G2 = declaring moves the purification
optimum clean↔metal. **Seam:** `t_rr` purely additive (never moves `V_t`/`I_Dsat`; MOSFET targets leave its
window open) → G1–G7 byte-for-byte. **DEFERRED:** `t_f` (not `τ`-scaling), constant-`I_R` idealization,
finite rectifier leakage rating + `t_rr`/current performance grade, distinct vertical-diode structure. 803
chip+fab_game tests green. **ALL 5 SLICES BUILT — plan complete.**

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
