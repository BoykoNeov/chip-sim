---
name: historical-modes-b5
description: "project (2026-07-10): historical-modes B5 BUILT — LOCOS bird's beak; 2-D engine consumer via normalized modulation m; the plan is COMPLETE (all 7 modes)"
metadata:
  node_type: memory
  type: project
  originSessionId: 8a27fa66-0ea3-4150-87cb-94445b76c189
---

**Historical-modes B5 BUILT** (`chip/locos_history.py` + `demo_locos_history.py` + `test_locos_history.py`;
gallery card `hist·B5`; H0 timeline rung stage=**Isolation**; `chip-locos-history.png`; commit `dcf079c`).
The **last historical chunk** — the plan is now COMPLETE (order A1→A3→B6→H0→A2→A4→**B5 ✅**, all seven modes).
Pure additive **consumer** of the 2-D engine (`Diffusion2D`+`MaskedSurface`, [[lateral-diffusion-2d]]/
[[chip-device-2d-v111]]) + `chip.oxidation.grow_oxide` — the 2-D oxidation regime's **second** consumer.
See [[historical-modes-a4]], [[historical-modes-h0]], [[locos-birds-beak-source]], [[deal-grove-oxidation-source]],
[[gradual-failure-preferred]].

**The physics.** LOCOS (local oxidation of silicon, ≈1980s isolation): a Si₃N₄ mask over the **active**
areas blocks the oxidant while a thick **field oxide** grows between devices. Oxidant diffuses **laterally
under the nitride edge** → the classic **bird's beak** eats active area. Below a min drawn active width the
two beaks **merge** and the island **pinches off** — the isolation-density wall **STI** (vertical walls, no
lateral oxidant path) cleared (F7 forward in `future-steps.md`; B5 is its historical/displayable form).

**THE load-bearing build call (advisor, the A4 discriminator applied — same shape as [[historical-modes-a4]]).**
Ran "delete the 2-D solve — does the headline change?": (1) the **encroachment MAGNITUDE** (beak length, min
pitch=2·L_beak) is **geometric/FLAGGED** — presenting it as an engine output = the A4 free-contour trap
("calling a tuned length emergent"); (2) the **TOPOLOGY** (two-beak merge → pinch-off) **does** change → that
is what the engine earns, exactly [[chip-device-2d-v111]]'s two-window pattern (a *different BC topology* =
independent cross-check). **THE SEAM LANDMINE (advisor):** a transient linear scalar in `Diffusion2D`
penetrates as `√(Dt)` (erfc), **NOT** Deal–Grove `√(Bt)` — so the 2-D field must **not** set thickness.
Resolution: the solve produces a **normalized lateral modulation `m(x)∈[0,1]`** (1 in open field → 0 under
nitride) and `t_ox = grow_oxide · m` — Deal–Grove stays the thickness source; open-field cells are pinned
`m=1` **by construction** (`np.where(open_mask,1,N[:,0])`) so the planar seam is **exact, not tolerance-bound**.
`L_D = BEAK_DIFFUSION_FACTOR·t_field` (flagged 3.0 → beak/field≈0.91, ~cited 0.85×) — DON'T extract a physical
oxidant D (needs C*,N₁ = over-build); own the length as **flagged calibration**.

**THE reconcile (primary data overruled an advisor prediction — [[commit-at-end-of-batch]] surfacing rule).**
Advisor first predicted the front-interaction near merge would be **below the resolved scale** (like
device_2d). My solve showed the **opposite**: two-window pinches at drawn ≈2.5 µm while single-edge
2·L_beak=0.93 µm — a **large, fully-resolved** divergence (opposing beaks' linear-availability **tails
superpose**, L_D≈3×beak drags them out). Reconcile verdict: don't headline the 2.5 µm as physics (uncalibrated
model output — the A4 trap), and don't call it an artifact and headline 2·beak (revives the decorative-solve
problem). **Disciplined middle:** the interaction-driven *earlier* pinch-off is the load-bearing 2-D fact
presented **qualitatively** (presence + sign only: LOCOS worse than 2·L_beak); the **merge coefficient is
FLAGGED**. Headline the **coefficient-free** claim: **min isolable active pitch ∝ field-oxide thickness**
(beak ∝ t_field); STI clears it.

**Triad.** *Tight:* planar seam (`grow_oxide` **bit-for-bit**; `m≡1` no-nitride & field plateau exact);
sign/topology (beak inward only, `m∈[0,1]` max-principle, active width monotone↓ → pinch-off); two-window ≡
subtraction `W−2·L_beak` **at wide stripes** (~1 cell, ≳ several µm — NOT near the knee). *Earned 2-D finding
(direction only):* beaks overlap → pinch-off *before* 2·L_beak. *Flagged:* `BEAK_DIFFUSION_FACTOR`,
`ACTIVE_MODULATION_THRESHOLD`, the merge coefficient. *Named ceilings:* linear caricature (no moving Si/SiO₂
boundary, no volume-expansion stress/nitride lift/Kooi white-ribbon); ratio's thickness-saturation not modelled
(fixed factor); pinch-off a per-stripe cliff ([[gradual-failure-preferred]] graded fraction named-not-built).
**Citation FIXED mid-build (advisor blind-spot catch):** dropped unverified Wolf/Plummer §-numbers I'd carried
from recall; web-verified ≈0.85× + the lateral-under-nitride mechanism vs TU Wien Filipovic §6.1.4. Fast lane
green (990 passed, +12 B5 tests). README/plan/H0-timeline/physics-gallery all regenerated; committed+pushed to
`main` ([[commit-at-end-of-batch]]).
