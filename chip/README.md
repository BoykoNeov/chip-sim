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
> boundary. *The device* (`device.py`) uses **semiconductor CGS** (like dopant diffusion) — ε in F/cm,
> charge in C/cm², `C_ox` in F/cm² — consuming the upstream `t_ox` in µm (→cm at its boundary) and the
> channel `N_A` in cm⁻³. **One unit system *within* each module; native units *per* module** (Steel's
> "one system throughout" was about not splitting units inside the engine-coupled computation — here
> each module is self-contained). See each module's docstring.

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
- **To work on the device (Phase 4):** `device.py` + `tests/test_device.py`, the demo
  `demo_device.py` + `tests/test_demo_device.py`, and `plots.device_figure`. The **process → device**
  payoff — a chip-local compact closed form (**does not touch the engine**): `threshold_voltage`
  (`V_t = V_FB + 2φ_F + Q_dep/C_ox`) consuming a channel `N_A` (Phase 1) + a gate `t_ox` (Phase 2) +
  a litho CD (Phase 3, *geometry only*); `fermi_potential`/`oxide_capacitance`/`flatband_voltage`/
  `depletion_charge` the building blocks, `depletion_charge_poisson` the **independent Poisson anchor**,
  `threshold_voltage_body_effect` the √-law, `gate_charge`/`inversion_charge`/`oxide_field` the
  charge-neutrality/Gauss conservation, `saturation_current` the honest long-channel drive readout. The
  module docstring is its contract (cited MIT 6.012 benchmark, the long-channel/ideal-oxide scope edge).
  Saves `docs/figures/chip-device.png`.
- **To work on the teaching notebook (§9):** `chip.ipynb` + `tests/test_chip_notebook.py`. A *thin
  skin* on the four phase modules — each compute cell calls the validated module **directly** (a
  static figure per section, embedded in the committed `.ipynb`), with `ipywidgets.interact` as sugar
  on top; the test executes it headless (`nbclient`) and asserts no cell errors (`slow`-marked, gated
  on the `[notebook]` extra **and** a registered kernelspec — a clean checkout skips). Needs
  `pip install -e .[viz,notebook]`. **Why the direct cells, not interact callbacks:** `interact`
  captures exceptions in an `Output` widget, so a break in an interact callback never reaches the test
  — the validated calls must live in plain cells (the same rule as Steel's `steel.ipynb`).
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
- **Phase 4 — compact MOS `V_t` (process → device): BUILT** (2026-06-09). `device.py` (the compact
  closed form `V_t = V_FB + 2φ_F + Q_dep/C_ox`, body-effect √-law, charge-neutrality/Gauss, optional
  long-channel `I_Dsat` — a chip-local model, **not** the engine) + `demo_device.py` +
  `plots.device_figure`. Banked artifact: the **whole process→device flow on one figure** — a coherent
  n-MOSFET chained diffusion → oxidation → litho → `V_t` (`docs/figures/chip-device.png`); channel
  `N_A` = 1e17, dry-O₂ 14 nm gate oxide, 167 nm litho gate, shallow n⁺ S/D (`x_j` ≈ 0.10 µm <
  gate length → coherent cross-section) → **`V_t` ≈ 0.55 V** (cf. the cited MIT 6.012 worked example
  at exactly 15 nm → 0.58 V). 20-test triad green (15 device + 5 demo): the **independent
  depletion-Poisson anchor** (not the √-law), charge-neutrality/Gauss conservation, the MIT benchmark.
- **Experimentation surface — the teaching notebook: BUILT** (2026-06-09). `chip.ipynb` — the single
  interactive surface chip's pedagogy calls for (plan §9 / ADR 0002: chip is *not* the flagship, so
  **no Streamlit app**). One section per phase, each with `ipywidgets` sliders re-running the validated
  module live; ends on the coherent process→device flow. Headless smoke-test
  `tests/test_chip_notebook.py` (`slow`). See below.

## Interactive surface — the teaching notebook (`chip.ipynb`, §9)

The *education* artifact (target #1): the four phase modules with the knobs exposed. A guided
"process recipe in, device out" narrative — diffusion → the pn junction, Deal–Grove oxidation,
the lithography aerial image, and the compact MOS `V_t` — with **ipywidgets sliders** (diffusion
time/temperature & dopant, oxidation furnace temperature & crystal face, exposure pitch/NA/σ,
channel doping & gate-oxide time) re-running `diffusion_dopant`/`junction`/`oxidation`/`litho`/`device`
live. The payoff section turns a **process knob** (gate-oxide time, channel `N_A`) and watches `V_t`
move — the chip counterpart of Steel's four-curves anchor.

```powershell
pip install -e .[viz,notebook]        # matplotlib (viz) + jupyterlab + ipywidgets + the nbclient/ipykernel run stack
jupyter lab projects/chip/chip.ipynb  # (classic UI: `pip install notebook`, then `jupyter notebook`)
```

It is a **thin skin** (ADR 0002), built to the same rule as Steel's `steel.ipynb`: every *compute*
cell calls the validated module **directly** (a static figure per section, embedded in the committed
`.ipynb` so it reads on GitHub without a kernel), and `interact` is sugar layered on top. That split is
load-bearing — `ipywidgets.interact` runs its callback inside an `Output` that **captures** exceptions,
so a break inside an interact callback would never reach the smoke-test; the validated calls therefore
live in plain cells. `tests/test_chip_notebook.py` executes the notebook headless (`nbclient`,
`allow_errors=False`) and asserts **no cell errors** — *that it runs clean*, not a physics check
(ADR 0002) — `slow`-marked and gated on the `[notebook]` stack **and** a registered kernelspec, so a
headless/clean checkout skips rather than errors. Like the notebook itself, this layer adds **reach,
not correctness**: the per-phase triads already validate the numbers.

## Test runner (tiered gate, ADR 0003)

```powershell
# from repo root
./run_tests.ps1 -m "not slow"   # routine commit gate (whole-repo fast lane, ~9 s — collects chip)
./run_tests.ps1 projects/chip   # scope to chip while iterating
```

`pyproject.toml`'s `testpaths` already carries `projects`, so `projects/chip/tests/` is collected
with no config change; `pythonpath = ["."]` lets chip import the frozen engine as `engines.diffusion…`.
The notebook smoke-test (`tests/test_chip_notebook.py`) is `slow`-marked, so the fast lane deselects it;
it runs in the full gate (`python -m tools.gate chip` / `./run_tests.ps1`).
