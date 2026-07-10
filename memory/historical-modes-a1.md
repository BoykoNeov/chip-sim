---
name: historical-modes-a1
description: "project (2026-07-10): historical-modes backward axis opened; A1 pre-implant doping dose-control wall BUILT"
metadata: 
  node_type: memory
  type: project
  originSessionId: 601bec46-6810-41f2-a6af-919ed1b6c8d9
---

**Historical-modes** = the NEW *backward* axis (`docs/plans/historical-modes.md`), complement to the
*forward* `future-steps.md`: re-run a process we already model in its **period-limited mode** so the
limitation explains why the modern version won. Load-bearing decision (answers "what about historical
modes with NO consumer?"): a **three-tier** relaxation of the anti-over-build bar — **Tier-1** has a real
device consumer (build anytime); **Tier-2** has no dedicated consumer but a *displayable* limitation
(build only after the **H0 era display surface** exists — the shared consumer that legitimises the
consumer-less modes); **Tier-3** not observable → don't build (honest NO's: grown/alloy/mesa structures,
Ge devices, tool colour). Ordering was flipped from "H0 first" to **A1 → A3 → B6 → H0 → A2 → A4 → B5**
(advisor + user): H0 only needs to precede the Tier-2 chunks, so leading with it = a display surface over
one recycled figure (over-build). Chunks: A1 doping, A3 HCl/HP oxidation, B6 Al spiking, A2 litho
tool/wavelength, A4 resist generations, B5 LOCOS bird's beak (gives the 2-D engine a consumer).

**A1 BUILT** (`chip/doping_history.py` + `demo_doping_history.py` + tests; gallery card `hist·A1`; pure
additive consumer, no engine change). The discriminator is the **dose-control wall**, NOT depth: the
two-step predep→drive-in *can* partly decouple Q from x_j (so the plan's original "dose∝depth can't
decouple" was loose — corrected). The real wall: the surface floods at the solid-solubility limit `N_s`
(a Trumbore constant, not a knob), so a constant source can't reproducibly meter a **light** dose (5e11
boron needs a sub-ms predep). `demo_implant.py:122` "matched" that light dose only by tuning `N_s` BELOW
solubility (the cheat) — A1 is the honest accounting. The wall is a **FLAGGED controllability proxy**
(`predep_dose_floor = 1.128·N_s·√(D·t_min)`), sign-robust only across a stated `(T_predep,t_min)` box
(`{800,900}°C×{0.1,1}s` → boron floor 7e11…1.1e13, above 5e11 with margin ~1.4×). **Tight** legs = the
predep dose identity + the **seam** (constant `DopingSource` at solubility reproduces `predeposit`
bit-for-bit — enforced by `surface_conc` being a *property* that references `DOPANTS[species].
N_solid_solubility`, so it can't drift). Source registry = period texture; the one real physics axis is
**constant** (POCl₃/BBr₃, pinned at solubility) vs **limited** (spin-on-glass, meters a lower dose — the
pre-implant workaround, but imprecise / no independent depth). See [[device-targets-plan]],
[[implant-damage-leakage]], [[dopant-solid-solubility-source]].
