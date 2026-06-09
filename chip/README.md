# `projects/chip` — the microchip fabrication simulator

*Process recipe in, device out.* Project #2 of the program and the **first consumer of the
frozen diffusion/heat spine** (`engines/diffusion`): it builds **no** new shared engine — it
proves the spine reuses. Dopant profiles *are* the carbon-diffusion code Steel froze, in **mass
mode**. Full plan: [`docs/plans/microchip-fabrication.md`](../../docs/plans/microchip-fabrication.md).

> **Units — each module computes in its cited data's native units** (the deliberate departure from
> Steel's project-wide SI), so **no load-bearing constant is converted on the way in**; **µm is the
> cross-module length currency** (junction depths and oxide thicknesses both reported in µm).
> *Dopant diffusion* (`diffusion_dopant.py`, `junction.py`) uses **semiconductor CGS** — cm /
> cm²·s⁻¹ / cm⁻³ / cm²·V⁻¹·s⁻¹ — the native units of Fair `D₀`, Trumbore `N_s`, Masetti `μ` (the
> frozen engine is unit-agnostic, fed cm + seconds; `R_s` falls out in Ω/sq directly). *Oxidation*
> (`oxidation.py`) uses **Deal–Grove-native µm-hour** — `B` (µm²/hr), `B/A` (µm/hr) — the units the
> cited rate constants are tabulated in. *Lithography* (`litho.py`) uses **litho-native nm** —
> wavelengths (193 nm) and feature sizes are quoted in nm — exposing the printed CD in µm at the
> boundary. **One unit system *within* each module; native units *per* module** (Steel's "one system
> throughout" was about not splitting units inside the engine-coupled computation — here each module is
> self-contained). See each module's docstring.

## Load pointer (per-session working set, ARCHITECTURE.md §11)

- **To work on dopant diffusion (Phase 1a):** `diffusion_dopant.py` + its `tests/`. It loads the
  frozen `engines/diffusion/CONTRACT.md` (**mass mode**: Dirichlet predep surface / Neumann(0)
  sealed drive-in) — `predeposit` → `erfc`, `drive_in` → near-Gaussian, `two_step` chains them.
  The module docstring is its contract (the cited Fair `D(T)`, the exact-anchor-vs-realistic-demo
  split, the constant-D scope edge).
- **To work on the junction reading (Phase 1a):** `junction.py` + `tests/test_junction.py`. It
  consumes a `diffusion_dopant` profile (plain `(x, N)` arrays) → junction depth `x_j` (crossing
  the background `N_B`) + sheet resistance `R_s` (the Masetti `μ(N)` conductance integral),
  benchmarked against Irvin's curves. The module docstring is its contract.
- **To work on the banked artifact (Phase 1a):** `demo_junction.py` + `tests/test_demo_junction.py`
  (the end-to-end integration test) and `plots.py` (the figure — `[viz]` extra). The demo wires
  `two_step` → `analyze_junction` → `plots` and saves `docs/figures/chip-junction.png`.
- **To work on oxidation (Phase 2):** `oxidation.py` + `tests/test_oxidation.py`, the demo
  `demo_oxidation.py` + `tests/test_demo_oxidation.py`, and `plots.oxidation_figure`. A **chip-local
  closed form** (Deal–Grove `x²+Ax=B(t+τ)`, wet/dry) — **does not touch the frozen engine**;
  `grow_oxide` → `OxideGrowth` (`t_ox` in µm, the cross-module currency), `oxide_thickness`/
  `linear_limit`/`parabolic_limit`/`growth_rate` the closed form + limits + ODE. The module docstring
  is its contract (cited `B`/`B/A`, the Massoud thin-dry scope edge, the deferred OED/segregation
  coupling). Saves `docs/figures/chip-oxidation.png`.
- **To work on lithography (Phase 3):** `litho.py` + `tests/test_litho.py`, the demo `demo_litho.py`
  + `tests/test_demo_litho.py`, and `plots.litho_figure`. The chip's **one genuinely-new module** —
  **Fourier optics**, chip-local (not promoted to `engines/`); **does not touch the frozen engine**.
  Core: `coherent_image` (the `|Σ orders|²` primitive) → `two_beam_image` (the exact `4cos²(πx/p)`
  anchor) + `abbe_image` (the partially-coherent **Abbe sum-over-source** workhorse, with
  `conventional_source`/`offaxis_source`); `rayleigh_resolution` (`R=k₁λ/NA`), `transmitted_power` (the
  Parseval power-balance), `image_contrast`/`nils`, `print_cd` + `expose_grating` (constant-threshold
  resist → CD in nm/µm). The module docstring is its contract (cited `k₁`/NILS, the
  scalar/no-defocus/Abbe-not-Hopkins/threshold-resist scope edge). Saves `docs/figures/chip-litho.png`.
- **To use the diffusion/heat spine:** load `engines/diffusion/CONTRACT.md` only — never Steel's
  or chip's internals. Chip instantiates the same contract Steel's `carburize.py` did (mass mode).

## Status

- **Phase 1a — dopant diffusion & the pn junction: BUILT** (2026-06-09). `diffusion_dopant.py`
  (predep `erfc` / drive-in Gaussian, cited Fair `D(T)` for B/P) + `junction.py` (junction depth +
  Masetti/Irvin sheet resistance) + the banked two-step boron pn-junction demo (`x_j` ≈ 1.05 µm,
  `R_s` ≈ 134 Ω/sq into a 1e15 n-type wafer). 28-test triad green.
- **Phase 2 — Deal–Grove oxidation: BUILT** (2026-06-09). `oxidation.py` (the linear-parabolic
  closed form `x²+Ax=B(t+τ)`, wet/dry, cited rate constants — a chip-local analytic/ODE module,
  **not** the PDE engine) + `demo_oxidation.py` + `plots.oxidation_figure`. Banked artifact: oxide
  thickness vs time wet-vs-dry with the linear/parabolic regimes annotated, beside the growth-rate
  mechanism (`docs/figures/chip-oxidation.png`); (100) 1100 °C/1 h → dry ≈ 0.10 µm, wet ≈ 0.64 µm.
  23-test triad green.
- **Phase 3 — lithography aerial image: BUILT** (2026-06-09). `litho.py` (the chip's one genuinely-new
  module — **Fourier optics**, chip-local, does **not** touch the engine): the exact two-beam `4cos²(πx/p)`
  anchor + the **Abbe sum-over-source** partially-coherent workhorse (not Hopkins TCC), Rayleigh
  `R=k₁λ/NA` *derived from the pupil cutoff* (k₁=0.5 coherent / 0.25 two-beam), constant-threshold resist
  → CD. + `demo_litho.py` + `plots.litho_figure`. Banked artifact: the aerial image **assembling from its
  diffraction orders** beside the **contrast-vs-pitch** resolution curve (`docs/figures/chip-litho.png`);
  193 nm ArF, NA 0.85, σ 0.5 → contrast/NILS/CD fall toward the cutoff, image goes flat below ~151 nm
  pitch. 25-test triad green (19 litho + 6 demo).
- **Phase 4 — compact MOS `V_t`:** planned.

## Test runner (tiered gate, ADR 0003)

```powershell
# from repo root
./run_tests.ps1 -m "not slow"   # routine commit gate (whole-repo fast lane, ~9 s — collects chip)
./run_tests.ps1 projects/chip   # scope to chip while iterating
```

`pyproject.toml`'s `testpaths` already carries `projects`, so `projects/chip/tests/` is collected
with no config change; `pythonpath = ["."]` lets chip import the frozen engine as `engines.diffusion…`.
