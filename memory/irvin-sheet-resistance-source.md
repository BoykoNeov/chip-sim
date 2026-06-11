---
name: irvin-sheet-resistance-source
description: Cited Irvin (1962) resistivity/sheet-resistance curves — the junction-depth benchmark for Microchip Phase 1a (graphical, NOT a callable function)
metadata:
  node_type: memory
  type: reference
  originSessionId: microchip-phase-1a
---

The **sheet-resistance benchmark** for Microchip Phase 1a's `junction.py` (profile →
junction depth `x_j` + sheet resistance `R_s` — see [[bigsim-program]] Microchip
Phase 1a).

**Source: J. C. Irvin (1962)**, "Resistivity of Bulk Silicon and of Diffused Layers in
Silicon," *Bell System Technical Journal* **41**:387–410 (freely on archive.org,
`bstj41-2-387`). Provides (a) the **bulk resistivity ρ(N)** of n-/p-type Si at 300 K
vs dopant concentration, and (b) **"Irvin's curves"**: the average conductivity /
sheet-resistance × junction-depth product `R_s·x_j` as a function of surface
concentration `N_s` and background `N_B`, for **erfc and Gaussian** diffused profiles.

> **CRITICAL distinction the advisor flagged — keep it in the note so a future session
> doesn't think "Irvin's curves" is callable.** Irvin's curves are **graphical**.
> - **What the benchmark CITES:** Irvin's published `R_s·x_j` chart — `junction.py`'s
>   computed `x_j`, `R_s` are compared against it (the cross-check).
> - **What the code COMPUTES:** `R_s = 1 / ∫₀^{x_j} q·μ(N(x))·N(x) dx` — a numerical
>   conductance integral of the diffused profile, with a concrete **mobility model
>   `μ(N)` now pinned: Masetti (1983)** ([[dopant-mobility-source]]). `x_j` is the level
>   set where the diffused profile crosses `N_B`.

**Non-circularity:** `R_s` falls out of the integrated profile + an **independent**
mobility/resistivity model; comparing to Irvin's measurement-based chart is then a
genuine cross-check — *not* a refit. (Use an independent `μ(N)` for the integrand
rather than Irvin's own ρ(N), so the two sides of the benchmark stay independent.)
The Phase-1 diffusivity ([[dopant-diffusivity-source]]) and solubility
([[dopant-solid-solubility-source]]) being cited-not-fit is what makes the whole
`x_j`/`R_s` comparison a cross-check rather than a tautology. **SUPREM** is a reference
process simulator for validation, used as facts, never copied.

**Named scope edge:** Irvin's curves assume **full dopant activation** and **300 K**;
at the solubility-limit surface, active < chemical concentration
([[dopant-solid-solubility-source]]), so the high-`N_s` end is the honest ceiling.
