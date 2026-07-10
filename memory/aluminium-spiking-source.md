---
name: aluminium-spiking-source
description: "historical-modes B6: cited Al–Si eutectic 577 °C + ~1.5 wt% max Si solid solubility in Al (Murray–McAlister 1984); spiking mechanism + alloy/barrier fixes"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5003c70b-3983-40a8-b809-cdbd4bd06812
---

**Cited source for B6 aluminium junction spiking** (`chip/metallization_history.py`,
[[historical-modes-b6]]). The two **cited** legs (direction + one anchor); everything else in the module
is flagged house calibration.

* **Al–Si binary phase diagram — Murray & McAlister, *Bull. Alloy Phase Diagrams* 5(1):74 (1984).**
  Eutectic at **577 °C**, eutectic composition ~11.3 wt% Si; the **maximum solid solubility of Si in Al**
  is **~1.5 wt%** (≈1.59 at%) *at* the 577 °C eutectic, falling steeply below it (a fraction of a percent
  at 400–500 °C). These two numbers (`AL_SI_EUTECTIC_CELSIUS=577`, `SI_IN_AL_EUTECTIC_WT=0.015`) are the
  cited anchors; the Arrhenius `S(T)=S₀·exp(−Eₐ/kT)` (`S0=7.84`, `Eₐ=0.458 eV`) is a **house fit** to two
  phase-diagram points (~1.5 wt% @577 °C, ~0.5 wt% @450 °C), clamped at the eutectic max above 577 °C
  (above which the contact melts/alloys — a different regime, not modelled). Only the **direction** (Si
  solubility rises with T) + the eutectic value are asserted.

* **The spiking mechanism + the historical fixes — textbook** (Sze, *VLSI Technology*; Ghandhi, *VLSI
  Fabrication Principles*; Murarka, *Silicides for VLSI Applications*). During a sub-eutectic contact
  sinter, Si dissolves into the Al (the film is the sink); dissolution **localizes** at grain-boundary /
  crystallographic spots, so a few Al **spikes** penetrate far deeper than the area-average recession →
  short a **shallow** junction. The fix ladder the module's `SCHEMES` registry encodes: pure Al (the wall)
  → **Al–Si alloy** (Al pre-saturated with ~1% Si, draws little more — the first fix) → **diffusion
  barrier** (Ti/TiN, Ti–W — blocks Si transport, the modern default) → Cu damascene (the F4-forward
  successor, out of scope).

Cross-refs: converts weight→volume solubility via `ρ_Al/ρ_Si` (2.70/2.33). See [[historical-modes-b6]],
[[fab-game-g4b]] (the `lifetime.py` leakage channel this lands on), [[implant-damage-leakage]] (a
*different* leakage contributor — recombination, anneals out; spiking is a geometric short).
