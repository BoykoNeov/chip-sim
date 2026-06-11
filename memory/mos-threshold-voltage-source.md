---
name: mos-threshold-voltage-source
description: "Microchip P4: cited MOS threshold-voltage formula + constants + the MIT 6.012 worked-example benchmark (Vt≈0.58V) that device.py reproduces"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 541507d0-af78-4165-8a88-d0da06dcce4f
---

Microchip Phase 4 (`projects/chip/device.py`) pins the compact **MOS threshold
voltage** model and its benchmark to cited sources at build (the per-constant
`[[…-source]]` discipline, not carried from memory). See [[deal-grove-oxidation-source]],
[[dopant-diffusivity-source]] for the upstream process constants this consumes.

**The formula (textbook long-channel n-MOSFET, p-substrate).**
`V_t = V_FB + 2·φ_F + (1/C_ox)·√(2·q·ε_Si·N_A·(2·φ_F))`, with
`φ_F = (kT/q)·ln(N_A/n_i)`, `C_ox = ε_ox/t_ox`, `V_FB = −(φ_gate + φ_F)` (ideal
oxide, Q_ox=0). Body effect (Shichman–Hodges √-law):
`V_t(V_SB) = V_t0 + γ·(√(2φ_F+V_SB) − √(2φ_F))`, `γ = √(2qε_Si N_A)/C_ox`.
Sources: **Wikipedia "Threshold voltage"** (canonical forms), **Chenming Hu,
*Modern Semiconductor Devices for ICs*, Ch.5** (Berkeley, free:
chu.berkeley.edu/wp-content/uploads/2020/01/Chenming-Hu_ch5-1.pdf), Sze/Plummer lineage.

**Constants (CGS-cm — per-module native units, matching Phase 1a):**
ε₀ = 8.854e-14 F/cm; ε_Si = 11.7·ε₀ = 1.036e-12; ε_ox = 3.9·ε₀ = 3.453e-13;
q = 1.602e-19 C; kT/q = 0.0259 V @300 K; **n_i = 1.0e10 cm⁻³** (the value that
reproduces the MIT example — 1.45e10 shifts φ_F ~10 mV, a named calibration choice);
degenerate-poly gate φ_gate = ±E_g/2 ≈ ±0.55 V (n⁺/p⁺-poly).

**The benchmark — MIT 6.012 PS3 (Spring 2007), Problem 2** (the worked example;
web.mit.edu/6.012/PS3solutions.pdf, read as image-PDF): n⁺-poly gate, p-substrate
**N_A = 1e17 cm⁻³**, **t_ox = 15 nm** → φ_F ≈ 0.42 V, **C_ox = 2.3e-7 F/cm²**,
**V_FB = −0.97 V**, **V_t ≈ 0.58 V**. device.py reproduces 0.589 V. Parts b,c double
as the **conservation cross-check**: above threshold `Q_inv = −C_ox(V_GB−V_t)` gives
−1e-6 C/cm² at V_GB ≈ 4.9 V, and Gauss `E_ox = Q_G/ε_ox` = 2.9e6 V/cm for Q_G=1e-6.

**Non-circularity:** every constant is an independent physical fact (universal
constants + the poly band-edge), none fit to a V_t; the inputs N_A (Phase-1 Fair D)
and t_ox (Phase-2 Deal–Grove) arrive from upstream with their own cited data — so
reproducing 0.58 V is a cross-check, not a refit.

**Scope edge named (not modeled):** long-channel only (no short-channel rolloff —
litho CD is geometry-only, the 2-D charge-sharing/DIBL tar pit stays outside the line);
ideal oxide (Q_ox=0), uniform channel, degenerate-poly gate (no metal work-function
table), forward-coupling only (segregation/OED deferred).

**Analytic anchor is NOT the √-law** (it's the same formula rearranged — a γ-consistency
check only). The genuine tight anchor is an **independent depletion-Poisson integration**
(`solve_ivp` + `brentq` on ψ″=qN_A/ε_Si, root-find W where ψ_s=2φ_F → Q_dep=qN_A·W
recovers √(2qε_Si N_A·2φ_F) to ~1e-9) — the Phase-2 solve_ivp analogue.
