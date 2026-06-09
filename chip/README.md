# `projects/chip` — the microchip fabrication simulator

*Process recipe in, device out.* Project #2 of the program and the **first consumer of the
frozen diffusion/heat spine** (`engines/diffusion`): it builds **no** new shared engine — it
proves the spine reuses. Dopant profiles *are* the carbon-diffusion code Steel froze, in **mass
mode**. Full plan: [`docs/plans/microchip-fabrication.md`](../../docs/plans/microchip-fabrication.md).

> **Units — semiconductor-conventional CGS** (the deliberate departure from Steel's SI metres):
> **cm / cm²·s⁻¹ / cm⁻³ / cm²·V⁻¹·s⁻¹**, the native units of the cited dopant data (Fair `D₀`,
> Trumbore `N_s`, Masetti `μ`), so no load-bearing constant is converted on the way in and sheet
> resistance falls out in Ω/sq directly. The frozen engine is unit-agnostic; we feed it cm and
> seconds. Lengths reported in **µm**. **One unit system throughout** — see `diffusion_dopant.py`.

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
- **To use the diffusion/heat spine:** load `engines/diffusion/CONTRACT.md` only — never Steel's
  or chip's internals. Chip instantiates the same contract Steel's `carburize.py` did (mass mode).

## Status

- **Phase 1a — dopant diffusion & the pn junction: BUILT** (2026-06-09). `diffusion_dopant.py`
  (predep `erfc` / drive-in Gaussian, cited Fair `D(T)` for B/P) + `junction.py` (junction depth +
  Masetti/Irvin sheet resistance) + the banked two-step boron pn-junction demo (`x_j` ≈ 1.05 µm,
  `R_s` ≈ 135 Ω/sq into a 1e15 n-type wafer). 27-test triad green.
- **Phase 2 — Deal–Grove oxidation:** next (a chip-local analytic/ODE module, not the PDE engine).
- **Phase 3 — lithography aerial image; Phase 4 — compact MOS `V_t`:** planned.

## Test runner (tiered gate, ADR 0003)

```powershell
# from repo root
./run_tests.ps1 -m "not slow"   # routine commit gate (whole-repo fast lane, ~9 s — collects chip)
./run_tests.ps1 projects/chip   # scope to chip while iterating
```

`pyproject.toml`'s `testpaths` already carries `projects`, so `projects/chip/tests/` is collected
with no config change; `pythonpath = ["."]` lets chip import the frozen engine as `engines.diffusion…`.
