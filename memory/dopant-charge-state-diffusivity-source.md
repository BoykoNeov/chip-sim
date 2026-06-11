---
name: dopant-charge-state-diffusivity-source
description: Cited Fair charge-state concentration-dependent diffusivity D(N)=D⁰+D⁻(n/nᵢ)+D⁼(n/nᵢ)² (B/P/As/Sb in Si) + nᵢ(T) + active-carrier plateau cap that Microchip v1.3's high-concentration box uses — the conc-enhanced counterpart of the intrinsic Fair D(T)
metadata:
  node_type: memory
  type: reference
  originSessionId: c438a374-74f6-4a68-a971-19a793538ac4
---

The **concentration-dependent (charge-state) dopant diffusivity** Microchip v1.3 uses for the
high-concentration "box" profile ([[chip-highconc-v13]], `chip/diffusion_highconc.py`). This is the
conc-enhanced **`D(N)`** counterpart of the intrinsic Arrhenius **`D(T)`** in
[[dopant-diffusivity-source]] — **one Fair/Plummer lineage**, the same standard text as
[[deal-grove-oxidation-source]]. Split out of the v1.3 build note 2026-06-10 so the source pin lives
on its own (parallel to the Phase-1a intrinsic note).

**The model — Fair charge-state diffusivity (the box driver).** At high doping `D` is the sum over the
charge states of the vacancy/interstitialcy the dopant pairs with, each weighted by a power of the
carrier ratio `n/nᵢ`:

    D_eff(n) = D⁰ + D⁻·(n/nᵢ) + D⁼·(n/nᵢ)²      (n-type: P, As, Sb)
    D_eff(p) = D⁰ + D⁺·(p/nᵢ)                   (p-type: B)

each component Arrhenius `Dˣ = Dˣ₀·exp(−Eˣ/kT)` (k = 8.617e-5 eV/K, T in kelvin). The majority carrier
comes from **charge neutrality**, `n = N/2 + √((N/2)² + nᵢ²)`, so `n → nᵢ` as `N → 0` (D smoothly
recovers its intrinsic value `D⁰+D⁻+D⁼`) and `n → N` as `N ≫ nᵢ`. **Phosphorus is the showcase:** its
doubly-negative-vacancy `D⁼` term gives the strong `(n/nᵢ)²` dependence that drives the **boxiest**
profile.

**Coefficients** (cm²/s, eV — verified verbatim against `CHARGE_STATE_TERMS` in `diffusion_highconc.py`):

| Dopant | D⁰ (D0/Ea) | single — D⁻ or D⁺ (D0/Ea) | double D⁼ (D0/Ea) |
|---|---|---|---|
| **B** (p, uses D⁺) | 0.05 / 3.5 | 0.95 / 3.5 | — |
| **P** (n) | 3.85 / 3.66 | 4.44 / 4.0 | **44.2 / 4.37** ← drives the box |
| **As** (n) | 0.011 / 3.44 | 31.0 / 4.15 | — |
| **Sb** (n) | 0.214 / 3.65 | 15.0 / 4.08 | — |

**Lineage note (load-bearing):** the neutral `D⁰` for **P (3.85/3.66)** and **Sb (0.214/3.65)** match
the Phase-1a intrinsic `DOPANTS` values *exactly* — the Phase-1a "intrinsic D" was Fair's neutral
component all along. **Boron is the exception:** its charge-state sum `D⁰+D⁺ ≈ 1.0 / 3.5` is ~30 %
above the Phase-1a B value `0.76/3.46` (a different Fair fit, **not** a transcription bug) — so a boron
box uses *this* slide-15 set, not `DOPANTS`.

**nᵢ(T)** — the standard process-simulation form `nᵢ = 3.87e16·T^1.5·exp(−0.605 eV/kT)` cm⁻³ (Plummer
Ch. 7). It sets *where* the enhancement bites: at diffusion temperatures it is enormous
(`nᵢ(1000 °C) ≈ 7e18`, eight orders above the room-T `1.4e10`), so only the near-surface `N ≳ nᵢ`
region is enhanced and the deep tail stays intrinsic. Cross-checked: `1.4e10` @300 K, `3.7e18` @890 °C
(vs Velichko's directly-read `4.6e18` @890 °C). Enters only through the ratio `n/nᵢ`.

**Active-carrier plateau cap** `n_active_max ≈ 3.4e20` cm⁻³ (phosphorus, Velichko) — the electrically
*active* electron concentration saturates well below the chemical solubility once clustering sets in.
Passing it caps the carrier driving `D`, which both tames the raw `(n/nᵢ)²` magnitude (uncapped ×486 →
physical **×42**) and produces the flat-topped plateau shape. `None` = uncapped full activation `n = N`
(the raw equilibrium upper bound). Omitted built-in-**field** factor `h = 1 + N/√(N²+4nᵢ²)` is a
further ≤2× enhancement (Plummer slide 14), flagged as approximated.

**Scope edge (named, NOT modeled):** this is an **equilibrium** charge-state model — it delivers the
high-conc enhancement, the steep box **front**, and the deeper junction, but **not** the anomalous
extended phosphorus **tail/kink** nor the concentration **plateau**, which are **non-equilibrium**
point-defect physics (P–V pair dissociation injecting Si self-interstitials, dopant clustering,
buried-layer enhanced diffusion). That is the honest ceiling, same exact-anchor-vs-scope-edge
discipline as Phase-1a's constant-D and v1.1's thin-dry anomaly.

**Sources (directly read at build).**
- **Model + coefficients + box benchmark** — **Plummer, Deal & Griffin, *Silicon VLSI Technology***
  (Prentice Hall, 2000), Ch. 7 (eqns **7.18** the charge-state sum / **7.19** the Arrhenius components;
  the slide-15 coefficient table; box-profile slides 15/25/27). The *same* Plummer text cited for the
  Phase-1a Fair `D(T)` ([[dopant-diffusivity-source]]) and the Phase-2 Deal–Grove constants
  ([[deal-grove-oxidation-source]]) — one coherent lineage.
- **Primary** — **R. B. Fair & J. C. C. Tsai, *J. Electrochem. Soc.* 124, 1107 (1977)** — the
  phosphorus charge-state model + emitter-dip.
- **Non-equilibrium kink/tail scope edge + high-T nᵢ cross-check** — **O. I. Velichko, "A comprehensive
  model of high-concentration phosphorus diffusion in silicon," *arXiv*:1905.10667 (2019)** — the
  plateau/kink/tail decomposition, `n_active_max ≈ 3.4e20`, and `nᵢ(890 °C) = 4.6e18`.

**Non-circularity:** the coefficients are **cited diffusion data, not fit to the box** — which is what
makes the v1.3 box-front / deeper-`x_j` result a genuine cross-check, not a refit (same story as the
intrinsic note's Irvin cross-check, [[irvin-sheet-resistance-source]]).
