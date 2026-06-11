---
name: dopant-segregation-source
description: Microchip v1.2 — cited dopant segregation coefficient m (definition + B/P values) from Hollauer (the SAME diss. as the Massoud pin) that coupling.py pins
metadata: 
  node_type: memory
  type: reference
  originSessionId: b15dfec1-90c9-4055-b898-964fda138764
---

Microchip v1.2 (the Phase 1↔2 back-coupling, `coupling.py`): the cited source for **dopant
segregation** at the moving Si/SiO₂ interface — pinned at build.

**Definition (load-bearing — pin it, the τ-sign-typo discipline).**
`m = (solubility in Si) / (solubility in SiO₂)`. **Inverting it flips depletion↔pile-up**, so the
definition is pinned *with* the source, like the Massoud τ-sign. Source: **Hollauer, TU Wien
dissertation (2007) §4.1 "Dopant Redistribution", Table 4.1** — the **SAME dissertation** that pins
the Massoud thin-dry oxidation ([[massoud-thin-oxide-source]]); one coherent lineage, two pins.

**Values (Table 4.1):**
- **Boron: m = 0.1–0.3** (`coupling.py` uses 0.3). m < 1 → boron prefers the oxide → silicon surface
  **DEPLETES**.
- **Phosphorus: m ≈ 10.** m > 1 → rejected by the oxide → silicon surface **PILES UP** (snowplow).

**The flux BC `coupling.py` derives (a moving-interface mass balance):**
`J_surface = N_surf·(0.44 − 1/m)·(dx_ox/dt)` into the silicon, where `0.44` = the cited Si/SiO₂
consumption ratio (`oxidation.SI_SIO2_RATIO`, [[deal-grove-oxidation-source]]). Sign: B `0.44−3.3<0`
(out → depletion), P `0.44−0.1>0` (in → pile-up). **No free transport coefficient** — the
coefficient is the cited `m` and the cited `0.44`.

**Critical scope-edge finding (the swept-sliver double-count — see [[chip-coupling-v12]]):** the
`0.44·R` term IS the interface recession, but `coupling.py` runs this flux on a *non-moving* grid →
the swept silicon sliver is counted twice. So **boron depletion is robust** (oxide-uptake-dominated)
but **phosphorus pile-up magnitude is ~2× inflated** (direction real — pile-up is intrinsically a
moving-boundary effect; the `m→∞` inert-oxide diagnostic exposes a ~10% spurious silicon-dose gain).

OED half = [[oed-source]]. Used by [[chip-coupling-v12]].
