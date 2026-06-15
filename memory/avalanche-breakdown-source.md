---
name: avalanche-breakdown-source
description: "device-targets slice 2: cited junction avalanche breakdown BV(N_B, x_j) — Baliga planar BV∝N^-3/4 + cylindrical curvature DERIVED from the ionization integral (no remembered fit); Sze anchor 0.24"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6bc81d21-2826-4752-8a52-f93d17aa1952
---

`chip/breakdown.py` (device-targets **slice 2**) is the new cited device output the HV-I/O target needs:
the drain–body junction **avalanche breakdown voltage** `BV`. The consumer that finally makes the S/D
diffusion **depth** `x_j` a device number (it fed nothing scored — `V_t`/`I_Dsat` never read it). Built
2026-06-15. See [[device-targets-plan]], [[mos-threshold-voltage-source]] (the device stack it joins).

**The two cited handles (the structural point — advisor).** `BV` depends on (1) the **lighter-doped side**
`N_B` (here the p-body / substrate `effective_channel_N_A`) via `BV ∝ N_B^(−3/4)`, and (2) the junction
**depth** `x_j` via *cylindrical-edge field crowding* (a shallow junction → small radius of curvature →
field crowds → breakdown early → low BV; deep → planar ceiling). Handle (2) is **slice 2's** axis (the
diffusion drive-in sets `x_j`); handle (1) is **slice 3's** (high-resistivity substrate). The curvature
term is what lets two wafers with **identical `V_t`** (same N_A + t_ox) have **different BV** — so BV is a
genuinely independent axis from `V_t`, not a relabel of the substrate doping.

**The model — DERIVED from the cited ionization integral, NOT an empirical curvature fit.** Avalanche =
`∫α(E(r)) dr = 1` with `α = a·E^m` (Si effective: **a ≈ 1.8e-35, m = 7**, Baliga). Over the one-sided abrupt
**cylindrical** depletion field `E(r) = (q·N_B/(2ε·r))·(r_d²−r²)` (peaked at the junction surface `r=r_j`),
root-find `r_d` where the integral = 1, then `BV = ∫E dr`. `r_j ≈ x_j` (textbook diffused-junction curvature
radius). The integrals are closed-form (binomial) — evaluated in the **normalized** `s = r/r_d` to be
cancellation-safe as the junction deepens (`ρ=r_j/r_d → 1`); the raw-radius binomial catastrophically
cancels (returned 0 past ~x_j 12µm — irrelevant, real junctions <1µm). Mirrors `device.py`'s independent
depletion-Poisson solve philosophy. The plane-parallel limit (`r_j→∞`) is the closed form
`BV_pp = ε·E_m²/(2qN)` with `E_m = (8qN/(aε))^(1/8)` — reproduces **Baliga `BV_pp ≈ 5.34e13·N_B^(−3/4) V`**
(verified via web search) AND the cited critical field `E_crit ~3–5e5 V/cm`, both from the ONE coefficient.

**Why the derivation, not the published transcendental fit (the de-risking).** Could not recover Baliga &
Ghandhi's exact normalized cylindrical closed form (Solid-State Electronics 19, 739, 1976) from free
sources (scanned PDFs unparseable). A remembered ln-form *fit the anchor but diverged unphysically* at large
`r_j/W` (η→∞ not →1) — the exact remembered-exponent trap the advisor warned of. So I derived BV from first
principles instead → **zero remembered-exponent risk**, only the cited `α=a·E^m`.

**The benchmark (loose) — Sze curvature anchor.** Sze's worked Si one-sided abrupt junction: N_B=1e15,
r_j=1µm → BV ≈ 80 V vs ≈ 330 V plane-parallel (ratio ≈ 0.24). The derived model lands **ratio = 0.238**
(~1% on the ratio — a genuine independent cross-check) and BV ≈ 70 V (planar ~10% low — the flagged
spread). `a`, `m` are flagged order-of-magnitude literature values; only the form + the N^(−3/4) trend are
cited. Source: **Sze & Ng, *Physics of Semiconductor Devices* §2.4.2** (junction curvature); **Baliga,
*Fundamentals of Power Semiconductor Devices* §3** (the BV_pp/E_crit/ionization power law); **Baliga &
Ghandhi 1976** (the cylindrical-junction result the derivation reproduces).

**Operating band (nominal 1e17 substrate):** drive-in 8→120 min walks x_j 0.10→0.27µm → BV 4.9→6.6 V; HV-I/O
floor = **6.0 V** (flagged) → a shallow (default) junction is HV-reject, a deliberate deep drive-in clears
it. BV is **uniform per wafer** (x_j, N_A both wafer-level — no per-die variation), so it's a clean
whole-wafer axis (no ring/core), orthogonal to the radial t_ox→V_t spread.

**Scope edges named:** abrupt one-sided junction + cylindrical edge (real graded profiles + the spherical
corner break down lower — a mild over-estimate); bulk avalanche only (NOT gate-oxide dielectric breakdown
~10 MV/cm — the plan's tripwire: do not conflate); single effective `α` (lumps `α_n≠α_p`).
