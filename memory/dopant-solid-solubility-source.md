---
name: dopant-solid-solubility-source
description: Cited Trumbore (1960) solid-solubility limits of B/P/As in Si — the predeposition Dirichlet surface value for Microchip Phase 1a
metadata:
  node_type: memory
  type: reference
  originSessionId: microchip-phase-1a
---

The **solid-solubility limit `N_s`** Microchip Phase 1a uses as the **predeposition
Dirichlet surface concentration** (the constant-source BC value in
`diffusion_dopant.py` — see [[bigsim-program]] Microchip Phase 1a). A real predep
holds the surface at the dopant's **maximum equilibrium solubility** in silicon, so
`N_s` is that thermodynamic ceiling — *not* a free knob.

**Source: F. A. Trumbore (1960)**, "Solid Solubilities of Impurity Elements in
Germanium and Silicon," *Bell System Technical Journal* **39**:205–233 — the canonical
solubility compilation. *(The ECE-Illinois reproduction garbled this cite as "19, 911,
1976"; the correct one is BSTJ 39:205, 1960.)*

**Magnitudes** (atoms/cm³, over the ~800–1200 °C diffusion range; all "exceeding
5×10²⁰" per the directly-read CityU Chapter 8):
- **B**: *retrograde*, peak ≈ 5×10²⁰ near ~1185 °C; ~few×10²⁰ at typical 950–1100 °C predep temps.
- **P**: ≈ 1.2–1.3×10²¹ around 1000–1100 °C (retrograde, max ≈ 2.5 at% near 1180 °C).
- **As**: ≈ 1.5–2×10²¹ (the highest n-type solubility).

**Non-circularity:** `N_s` is a cited **equilibrium-thermodynamics** fact (solubility),
independent of both the diffusion data ([[dopant-diffusivity-source]]) and of junction
depth — so using it as the predep BC keeps the predep dose `Q = 1.13·N_s·√(Dt)` a
genuine *prediction* (the flux-bookkeeping conservation leg), not a tuned input.

**Named scope edge (couples to the diffusivity edge).** At/near the solubility limit,
dopants **cluster/precipitate** and the **electrically-active** concentration falls
below the chemical solubility (especially As); and this high-`N_s` surface is exactly
the **concentration-enhanced `D(N)`** regime that makes constant-D erfc weakest (the
predep-leg wrinkle in [[dopant-diffusivity-source]]). v1 takes `N_s` as a **fixed
Dirichlet scalar** (the textbook reduction) and flags active-vs-chemical solubility +
clustering as the ceiling.
