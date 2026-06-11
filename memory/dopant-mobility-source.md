---
name: dopant-mobility-source
description: Cited Masetti (1983) carrier-mobility μ(N) model — the R_s conductance-integral integrand for Microchip Phase 1a junction.py
metadata:
  node_type: memory
  type: reference
  originSessionId: microchip-phase-1a
---

The **carrier-mobility model `μ(N)`** Microchip Phase 1a's `junction.py` uses to turn a
diffused dopant profile into a **sheet resistance** (see [[bigsim-program]] Microchip
Phase 1a). The non-circular R_s design computes

    R_s = 1 / ∫₀^{x_j} q · μ(N(x)) · N(x) dx

so `μ(N)` is the **integrand** — load-bearing, not optional — and is deliberately an
**independent** model from the **Irvin** `R_s·x_j` chart it is benchmarked against
([[irvin-sheet-resistance-source]]), so the two sides of the cross-check stay
independent.

**Source: G. Masetti, M. Severi & S. Solmi (1983)**, "Modeling of carrier mobility
against carrier concentration in arsenic-, phosphorus-, and boron-doped silicon,"
*IEEE Trans. Electron Devices* **30**(7):764–769. The standard empirical
`μ(N)` for silicon — a Caughey–Thomas-type form fit **per dopant** (As, P, B) over the
**high-doping range** (it explicitly resolves that As-doped Si has lower electron
mobility than P-doped above ~1e19 cm⁻³). That high-`N` range is **exactly** the
solubility-limit predep regime ([[dopant-solid-solubility-source]]) — which is why
Masetti is the right pick over a low-field/lightly-doped mobility model.

> **Why this is pinned now, not "at build" (the advisor's asymmetry catch).** It was
> first deferred as "consumed at code-time by junction.py" — but the dopant diffusivity
> ([[dopant-diffusivity-source]]) is *also* consumed at code-time (by
> `diffusion_dopant.py`) and was pinned. Same logic ⇒ same treatment: μ(N) is a single
> named standard model (cleanly citeable, unlike the diffusivity's irreducible
> literature spread), so the Phase-1a source set is closed here rather than deferred.

**Non-circularity:** μ(N) is a cited **transport** model, independent of the diffusion
data, the solubility, and the Irvin benchmark — so the computed `R_s` vs Irvin's
published `R_s·x_j` is a genuine cross-check. **Named scope edge:** Masetti assumes
**full activation at 300 K**; at the solubility-limit surface the *electrically active*
N (what carries current) is below the *chemical* N (what the diffusion profile tracks)
— the same active-vs-chemical ceiling flagged in [[dopant-solid-solubility-source]].
