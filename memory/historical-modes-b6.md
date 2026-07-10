---
name: historical-modes-b6
description: "project (2026-07-10): historical-modes B6 BUILT — Al junction spiking → graded shorted-area fraction → lifetime.py j_leak; all Tier-1 modes done, H0 next"
metadata:
  node_type: memory
  type: project
  originSessionId: 601bec46-6810-41f2-a6af-919ed1b6c8d9
---

**Historical-modes B6 BUILT** (`chip/metallization_history.py` + `demo_metallization_history.py` + tests;
gallery card `hist·B6`; `chip-metallization-history.png`). Pure additive **consumer** of `lifetime.py` +
`junction.py` — no engine change, nothing it consumes touched, same discipline as [[historical-modes-a1]]
/ [[historical-modes-a3]]. The third and **last Tier-1** mode → **H0 (era display surface) is next**
(order A1 ✅ → A3 ✅ → **B6 ✅** → H0 → A2 → A4 → B5; all Tier-1 real-consumer modes now landed).

**The physics chain (the payload coupling):** pre-barrier metallization (evaporated Al) sintered
sub-eutectically → Si dissolves into Al up to solid solubility `S(T)` (rises toward ~1.5 wt% at the 577 °C
Al–Si eutectic, [[aluminium-spiking-source]]); localized grain-boundary dissolution → **spikes** deeper
than the average recession → short a **shallow** junction. *The shallower `x_j` (which implant enables),
the worse* — the discriminator. `d_spike = κ·si_uptake·t_Al·S_vol(T)`, `S_vol = S_wt·ρ_Al/ρ_Si`.

**Graded failure, the load-bearing modelling decision** (per [[gradual-failure-preferred]] — its cleanest
application yet): the honest failure is **spatial non-uniformity of spike depth** → a shorted-**AREA**
fraction `f_short = exp(−x_j/d_spike)` (smooth 0→1; ↑ as `x_j`↓, ↑ as `T`/`t_Al`↑; →1 as `d_spike≫x_j`),
**not** a cliff at `spike > x_j`. `f_short` is the yield gradient (the analogue of the edge-loaded Na
ring's outboard-die kills). Advisor's key catch: with a huge `J_short` the spec-cross is at *tiny*
`f_short`, so on a log `j_leak` axis it can *look* like a cliff — so the demo **foregrounds `f_short`**
(the genuinely graded observable) on the left, and is explicit that a shorted contact's own leakage is
catastrophic (`j_leak` on the right sits far above spec at even small `f_short` — that IS the point, a
spiked contact is dead). Left panel = `f_short` vs `x_j` across schemes (the shallower-worse coupling);
right = `j_leak` (log) vs sinter T with the barrier flat on the seam floor.

**Registry** mirrors A1's `DopingSource` on ONE physics axis, `si_uptake` (how much Si the metal still
draws from the contact): `"Al"` (pure, uptake 1 = the wall) → `"Al-Si"` (pre-saturated ~0.08 flagged,
partial fix) → `"barrier"` (Ti/TiN, uptake **0** = the modern default). **Seam:** default `barrier` →
`d_spike ≡ 0` → `f_short ≡ 0` → `j_leak` = `lifetime.generation_leakage_density` **byte-for-byte** (a
structural `(1−0)·J=J`, tested `==` not approx). Opt-in enables the period wall (A1 polarity).

**Deliberate divergence from the plan sketch** (advisor-endorsed, documented in-module + commit + plan):
the plan said B6 writes *through* `lifetime.py` "mirror of A1 dislocation / G4b metal plugs" — those add a
`1/τ` recombination term. Spiking is a **geometric ohmic short, not an SRH centre**, so routing it through
`1/τ` would be *physically wrong* (it doesn't shorten minority-carrier lifetime; it bridges the junction).
Instead it blends an ohmic-short density into `j_leak` at the **current** level, over `f_short`, reusing
lifetime's intact baseline — lands on the same observable without the wrong mechanism. (Named alt if you
ever want the plan verbatim: a `shorted_fraction` term on `lifetime.device_leakage` at the current level.)

**Scope edges** (named, not silent): **solubility-saturated worst case** — takes the Al as having reached
equilibrium Si solubility at the sinter T; anneal *time* enters only as time-to-saturation (dropped the
plan's `f(T,time)` → `f(T,t_Al)`, sink size carried by thickness). Sub-eutectic only (S clamped above
577 °C). Aggregate `j_leak` graded via `f_short`, but per-shorted-contact leakage taken ohmic-catastrophic
(fixed flagged `J_short`, magnitude deliberately non-load-bearing). Tight = seam + sign/topology; flagged =
`S(T)` curve, `κ=40`, exp-shape, `J_short`. Calibrated so pure Al shorts ~0.2 µm @450–500 °C, 0.8 µm line
(the on-record box). Also backfilled the A3 README row (missed at A3 build). See [[fab-game-g4b]] (the
leakage channel), [[implant-damage-leakage]], [[device-targets-plan]].
