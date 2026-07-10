---
name: locos-birds-beak-source
description: "reference (B5): LOCOS bird's-beak encroachment ≈ 0.85× field-oxide thickness; mechanism = lateral oxidant diffusion under the nitride; ratio saturates at thick oxide"
metadata:
  node_type: memory
  type: reference
  originSessionId: 8a27fa66-0ea3-4150-87cb-94445b76c189
---

**Source pin for `chip/locos_history.py` (B5)** — the cited/FLAGGED bird's-beak magnitude. Used to
calibrate `BEAK_DIFFUSION_FACTOR` (3.0 → modelled beak/field-oxide ≈ 0.91). See [[historical-modes-b5]],
[[deal-grove-oxidation-source]].

**What is cited (web-verified at build, NOT carried from memory):**
- **Ratio.** Bird's-beak length ``L_bb`` ≈ **0.85×** the grown field-oxide thickness — the widely-quoted
  LOCOS textbook rule of thumb (order-unity fraction). My model lands 0.91 (flagged, ~this band).
- **Mechanism.** The beak is caused by **lateral diffusion of the oxidant under the nitride mask** — the
  nitride cannot fully block oxidation because oxidant reaches the Si surface laterally. This is exactly
  what the normalized masked-`Diffusion2D` modulation models.
- **Named ceiling (from the source).** ``L_bb / t_ox`` **decreases as the field oxide thickens**, toward a
  **saturation length** — so the ~0.85× is not a universal constant. My fixed-factor model does NOT capture
  that thickness-dependence (a named scope edge). Higher T → shorter/lower beak (oxidation rate up vs lateral
  diffusion) — also not modelled.

**Where it came from.** Filipovic, *Topography Simulation of Novel Processing Techniques* (TU Wien
dissertation), **§6.1.4 "Oxidation with LOCOS"** (iue.tuwien.ac.at) — confirms the lateral-under-nitride
mechanism and the ratio's saturation-with-thickness behaviour; the ≈85% numeric is the common textbook
figure (surfaced across the LOCOS literature). **CORRECTION LOGGED:** the first draft's in-code citation
named "Wolf, *Silicon Processing for the VLSI Era* Vol. 2 §7; Plummer–Deal–Griffin §9" from **recall** — those
section numbers were **not opened** and were removed (advisor blind-spot catch: don't dress recall as a
page-pinned citation; the ratio is flagged, so this never threatened correctness, but the §-numbers were
unverified). The honest pin is the ~0.85× rule + the mechanism above.
