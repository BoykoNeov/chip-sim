---
name: dopant-diffusivity-source
description: Cited Fair/Plummer intrinsic dopant Arrhenius D(T) (B/P/As/Sb in Si) + erfc/Gaussian forms that Microchip Phase 1a uses
metadata:
  node_type: memory
  type: reference
  originSessionId: microchip-phase-1a
---

The **dopant diffusivity** Microchip Phase 1a instantiates the frozen
`engines/diffusion` with (`diffusion_dopant.py`, the predep/drive-in chain — see
[[bigsim-program]] Microchip Phase 1a). Two distinct things were pinned at build:

**1. The Arrhenius D(T) constants — Fair's intrinsic-diffusivity model**
(R. B. Fair, *Impurity Doping Processes in Silicon*, 1981), the canonical
compilation reproduced in **Plummer, Deal & Griffin, *Silicon VLSI Technology***
(the same standard text Phase 2's Deal–Grove constants cite — one coherent
citation lineage). Form:

    D(T) = D0 · exp(−Ea / kT),   k = 8.617e-5 eV/K,   T in KELVIN

| Dopant | D0 (cm²/s) | Ea (eV) | confidence |
|---|---|---|---|
| **B**  (p-type) | **0.76**  | **3.46** | standard Fair intrinsic value |
| **P**  (n-type) | **3.85**  | **3.66** | confirmed verbatim (two independent sources) |
| Sb (n-type)     | 0.214     | 3.65     | confirmed verbatim (ebrary/Plummer) |
| As (n-type)     | *widest spread — pin at build* | ~3.4–4.1 | see scope edge |

*Provenance note:* **P (3.85/3.66) and Sb (0.214/3.65) were confirmed verbatim** in the
Fair-via-PDG lineage. Boron's **value 0.76/3.46 is the standard, sane intrinsic boron
number** (sanity-checked below), but its *Fair-via-PDG attribution* specifically was not
verbatim-verified — the unconfirmed part is the citation lineage, not the number, and
confirmed-P alone covers the pn-junction demo regardless.

> **Units (SUPERSEDED at build, 2026-06-09 — kept honest).** This note's pre-code
> guess said "convert to engine m²/s at the boundary (1 cm²/s = 1e-4 m²/s)" assuming
> SI like the carbon spine. **The built code does the opposite — and the advisor
> confirmed it:** `diffusion_dopant.py` works in **CGS-semiconductor throughout**
> (cm / cm²·s⁻¹ / cm⁻³ / cm²·V⁻¹·s⁻¹), because the frozen engine is **unit-agnostic**
> (it bakes in NO physical constant — verified; "SI throughout" in CONTRACT.md
> describes Steel's two modes only) and the cited dopant data (Fair `D₀`, Trumbore
> `N_s`, Masetti `μ`) is **native cm-units**. Feeding the engine cm avoids 3 boundary
> conversions on load-bearing numbers for 1 trivial cm→µm output, and sheet resistance
> falls out in Ω/sq directly. So **no conversion happens** — `D(T)` stays in cm²/s.
> (eV is still used for the Arrhenius `kT`, `k = 8.617e-5 eV/K`, T in kelvin.) The
> **anchor demo (boron) and the second dopant (phosphorus) are both confirmed** — they
> cover the pn-junction demo; As is *not* needed for the anchor and is the spread
> example below. See [[bigsim-program]] Microchip Phase 1a for the full build record.

**2. The profile FORMS + the predep dose identity** — pinned to a directly-read
teaching chapter (CityU AP6120 *Chapter 8: Diffusion*, `cityu.edu.hk/phy/appkchu/AP6120/8.PDF`),
which gives exactly the BC pair the frozen engine ships:
- **Predeposition** = constant-surface `C(0,t)=C_s` (Dirichlet) → `C = C_s·erfc(x/2√Dt)`;
- **Drive-in** = constant-total-dose `∫C dx = S`, sealed surface (Neumann 0) → Gaussian `C = (S/√(πDt))·exp(−x²/4Dt)`;
- **Predep dose identity** `Q(t) = (2/√π)·C_s·√(Dt) ≈ 1.13·C_s·√(Dt)` — the plan's
  Phase-1 **flux-bookkeeping** conservation leg (the carburize Dirichlet analogue).

**Sanity check (the advisor's one-junction check passed).** Fair intrinsic boron at
1100 °C / 1 h gives `2√(Dt) ≈ 0.47 µm` — a sane junction-depth scale (matches CityU
Example 8.1's 0.76–0.94 µm). *Recipe in, ~µm junction out.*

**Non-circularity (the load-bearing story, parallel to [[carburize-diffusivity-source]]):**
`D0, Ea` are **cited diffusion data, not fit to junction depth** — which is exactly
what makes the Phase-1 `x_j`/`R_s` vs **Irvin** benchmark ([[irvin-sheet-resistance-source]])
a genuine **cross-check** rather than a refit. **SUPREM** is referenced for
cross-check only, never copied.

**Named scope edge (bites harder than carburize did).** The exact erfc/Gaussian forms
hold only for **constant, intrinsic D** — *validated tight* on the ∝√(Dt) scaling and
the profile **form** (constant-D / moderate-dose regime). Two things are the honest
ceiling: (a) real high-concentration diffusion is **concentration-enhanced `D(N)`**
(the phosphorus box / kink-and-tail; As–vacancy clustering) — **BUILT in v1.3**
([[chip-highconc-v13]]: the Fair charge-state box, recovered *within* the frozen engine
via a consumer-side lagged-closure hook — no amendment; the engine's nonlinear `D(u)`
stays unbuilt, the lag lives in the consumer. The box **front** + deeper junction are
captured; the anomalous **tail/kink** stays the named ceiling there); (b) the dopants
diffuse by **different mechanisms**
(B, P interstitial; Sb vacancy), so a single intrinsic Arrhenius is a reduction — *the
literature spread in D0/Ea is this content, not an error to resolve.* **The wrinkle
carburize did not have:** predeposition runs **at the solid-solubility limit**
([[dopant-solid-solubility-source]]) = high concentration = **precisely where
constant-D erfc is weakest**, so the scope edge bites the *predep leg specifically*.
Evidence it's real: intrinsic P at 1000 °C ≈ 1.25e-14 cm²/s, but CityU Example 8.1
uses ~1e-13 at 975 °C (concentration-enhanced). Hence the plan's split — the **exact
erfc/Gaussian legs are validated on their idealizations** (constant-D), the **realistic
predep→drive-in demo's job is the junction**, not the exact form. `D0,Ea` values
themselves are *calibrated/flagged* literature constants; the *form* is validated.
