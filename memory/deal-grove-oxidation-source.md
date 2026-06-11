---
name: deal-grove-oxidation-source
description: "Microchip P2: cited Deal–Grove linear-parabolic oxide-growth rate constants (B, B/A; wet/dry) that oxidation.py uses"
metadata:
  node_type: memory
  type: reference
  originSessionId: microchip-phase-2
---

The **Deal–Grove thermal-oxidation rate constants** BigSim's Microchip Phase-2 model uses
(`AMBIENTS` in `projects/chip/oxidation.py`). Linear-parabolic law `x_ox² + A·x_ox = B(t+τ)`
with Arrhenius rate constants, **(111) silicon**, native **µm-hour-eV** (k = 8.617e-5 eV/K):

| ambient | B (parabolic) = C_B·exp(−Ea_B/kT) | B/A (linear) = C_lin·exp(−Ea_lin/kT) |
|---|---|---|
| **dry O₂**  | C_B = 7.72e2 µm²/hr, Ea_B = **1.23 eV** | C_lin = 6.23e6 µm/hr, Ea_lin = **2.00 eV** |
| **wet H₂O** | C_B = 3.86e2 µm²/hr, Ea_B = **0.78 eV** | C_lin = 1.63e8 µm/hr, Ea_lin = **2.05 eV** |

- **Orientation** (linear B/A only — B is orientation-independent, oxidant diffusion through
  amorphous oxide): `(B/A)₍₁₁₁₎ = 1.68·(B/A)₍₁₀₀₎`, so (100) divides by 1.68. Default in code = (100)
  (the device-relevant MOS face); the benchmark test pins (111) = the cited table exactly.
- **Silicon consumed** = `0.44·x_ox` (Si→SiO₂ number-density bookkeeping: ~2.2e22 Si/cm³ oxide vs
  ~5.0e22/cm³ crystal). Of each µm oxide, 0.44 µm is below the original surface, 0.56 µm above.
- **`Ea_B(wet) = 0.78 eV` is the TABLE value** — pinned deliberately over the **0.71 eV** that floats
  in prose summaries (both WebFetch reads of the IUE table agreed on 0.78; only the search-summary
  prose said 0.71). A future session must not "correct" it to 0.71.

**Source, pinned at build (2026-06-09, NOT carried from memory — the [[carburize-diffusivity-source]]
pattern).** Deal & Grove (1965), *J. Appl. Phys.* 36:3770; tabulated in **Plummer–Deal–Griffin** /
Jaeger (the same standard lineage Phase-1a's Fair `D(T)` cites — one coherent reference family). Read
from the **IUE-Vienna** theses (Filipovic node31 + Hollauer node16, two independent reproductions
agreeing). CityU AP6120 Ch. 4 is a scanned PDF (not WebFetch-extractable) so the IUE pages were used.

**Sanity check vs published points (the loose benchmark leg):** (100), 1100 °C, 1 h →
**dry ≈ 0.099 µm**, **wet ≈ 0.642 µm** (wet ~6.5× faster); both within ~10–15 % of textbook tables.

**Benchmark strength, stated precisely (advisor, the validated-vs-calibrated discipline — DON'T
overstate the carburize parallel).** The benchmark leg rests on **citation fidelity** (constants
pinned to the published table — not a tautology, they could be miscited) + the independent tight
**algebraic-identity** leg. The thickness comparison is a **consistency check, NOT an independent
cross-check**: unlike carburize's `D` (from *tracer-diffusion*, a different measurement domain than
the case depth it predicts → genuinely independent), Deal–Grove's `B`/`B/A` were **originally fit to
oxide-thickness-vs-time data** (the 1965 paper), so thickness-from-constants vs published thickness
is closer to model-vs-itself. So thickness is asserted *loosely*, constants *tightly* — the honest
split. (The 0.78-vs-0.71 disambiguation is itself a fidelity check: paired with C_B(wet)=3.86e2, only
Ea=0.78 reproduces published B(1000 °C)≈0.29–0.32 µm²/hr; 0.71 gives ~2× high.)

**Named scope edge — the thin-dry (Massoud) anomaly:** for *dry* O₂ below ~30 nm the real oxide
grows **faster** than plain Deal–Grove's finite linear rate predicts (Deal & Grove themselves fit a
nonzero initial `x_i ≈ 20 nm`/`τ > 0` to absorb it; Massoud added an empirical exp term). v1 was
**plain Deal–Grove — it did NOT model the Massoud enhancement**, so the thin-dry regime was the
honest ceiling (the carburize constant-D analogue). The model otherwise stays the exact closed form.
**PROMOTED in v1.1** (2026-06-10): the Massoud exp-term is now built as `oxidation.py` §5
(`model="massoud"`, opt-in — plain DG stays the default and bit-for-bit unchanged) →
[[massoud-thin-oxide-source]]. See [[bigsim-program]] for the program-level non-circularity discipline.
