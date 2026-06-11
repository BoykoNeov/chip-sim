---
name: massoud-thin-oxide-source
description: "Microchip P2 v1.1: cited Massoud thin-dry-oxide (rapid-growth) rate constants + the coherent-set rule + the τ sign-typo finding that oxidation.py §5 uses"
metadata:
  node_type: memory
  type: reference
  originSessionId: microchip-v1.1-massoud
---

The **Massoud thin-dry-oxide correction** BigSim's Microchip v1.1 uses (`oxidation.py`
§5, `model="massoud"`) — the named [[deal-grove-oxidation-source]] thin-dry scope edge,
now PROMOTED (the steel-ferrite-bay move). Engine untouched; the plain Deal–Grove path
stays **bit-for-bit unchanged** (`grow_oxide` never applies the enhancement; the K=0
degenerate recovers DG, pinned in tests).

**The model — Massoud's time-decay formulation** (chosen over the thickness-decay sibling
because it INTEGRATES IN CLOSED FORM, keeping the module's exact-anchor discipline):

    dx/dt = (B + K1·e^(−t/τ1) + K2·e^(−t/τ2)) / (A + 2x)
    →  x² + Ax = Bt + Σ Kiτi(1 − e^(−t/τi)) + (xi² + A·xi)

Valid **dry O₂, 800–1000 °C, (100)/(111)/(110)** — the module REFUSES outside the cited
fit. Native **nm-min** (the Massoud tables' own units; µm at the boundary).

**Source (gathered 2026-06-10, pinned at build — NOT carried from memory):** Massoud &
Plummer, *J. Appl. Phys.* **62(8):3416–3423 (1987)** + Massoud/Plummer/Irene, *JECS*
**132(7):1746 & 132(11):2685 (1985)**, as compiled in **Hollauer, TU Wien dissertation
(2007) §2.7 Tables 2.3/2.4**. (The SAME dissertation §4.1 also pins the v1.2 dopant
segregation coefficients — [[dopant-segregation-source]]; one dissertation, two pins.)

**Two durable source calls:**
1. **The COHERENT-SET rule** — the Ki/τi ride **Massoud's own refit** B, B/A (Table 2.3,
   T<1000 °C), never spliced onto the DG-1965 constants. (A set must be self-consistent.)
2. **The τ SIGN-TYPO finding** — Hollauer prints `τi = τi0·exp(−E/kT)`, which gives
   *femtosecond* decays; only **exp(+E/kT)** (τ1≈1.2 / τ2≈7.5 min at 1000 °C) reproduces
   the dissertation's own **Fig. 2.19** (~25 nm @ 1000 °C/20 min). Also Table 2.4's 8th-row
   label "τ1⁰" is a typo for **τ2⁰**. A future session must not "correct" the sign back.

**The effect it buys (the banked before/after, `docs/figures/chip-thin-oxide.png`):** the
Phase-4 gate recipe (dry 1000 °C/20 min) grows **14.1 nm under plain DG → 23.3 nm under
Massoud (×1.65)**, and the Phase-4 readout moves **V_t 0.547 → 0.991 V (ΔV_t = +0.44 V)** —
the thin-dry anomaly was a V_t-sized error in the process→device chain, not a footnote. See
[[bigsim-program]] for the program-level exact-anchor / non-circularity discipline.
