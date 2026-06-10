# `chip` — the microchip fabrication simulator

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
> cited rate constants are tabulated in (its v1.1 **Massoud block** computes in the *Massoud*
> tables' native **nm-minute** — the same rule applied per cited *dataset* — exporting µm at the
> boundary). *Lithography* (`litho.py`) uses **litho-native nm** —
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
  is its contract (cited `B`/`B/A`, the deferred OED/segregation coupling).
  Saves `docs/figures/chip-oxidation.png`.
- **To work on the thin-dry (Massoud) correction (v1.1, Phase 2's promoted scope edge):**
  `oxidation.py` §5 + the v1.1 block of `tests/test_oxidation.py`, the demo `demo_thin_oxide.py` +
  `tests/test_demo_thin_oxide.py`, and `plots.thin_oxide_figure`. The cited **Massoud time-decay**
  model `dx/dt = (B + K₁e^(−t/τ₁) + K₂e^(−t/τ₂))/(A+2x)` — closed form (the quadratic identity
  gains two saturating doses `Mᵢ = Kᵢτᵢ`), **dry O₂ / 800–1000 °C / (100)(111)(110) only**
  (refuses outside the cited fit), on **Massoud's own coherent `B`,`B/A` set** (not spliced onto
  the 1965 constants). `grow_oxide_massoud` → `OxideGrowth(model="massoud")`; the default
  `grow_oxide` path stays bit-for-bit plain Deal–Grove. The module docstring §5 is its contract
  (the τ sign-typo finding, the thin-seed-only `x_initial` edge). Saves
  `docs/figures/chip-thin-oxide.png`.
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
- **To work on the back-coupling (v1.2 — OED + dopant segregation):** `coupling.py` +
  `tests/test_coupling.py`, the demo `demo_coupling.py` + `tests/test_demo_coupling.py`, and
  `plots.coupling_figure`. The **Phase-1↔2 back-reaction** (oxidation reaching back on the dopant
  profile), built **entirely on the frozen engine** — OED is its already-frozen variable-`D(t)`
  callable, segregation a `Neumann(flux(t))` BC — **no engine amendment** (the decisive finding;
  contrast the unbuilt `D(N)` case, which *would* need one). `oxidize_couple` runs an oxidizing
  anneal: **OED** enhances `D` (cited `f_I`; `oed_enhancement_factor`/`interstitial_supersaturation`),
  **segregation** partitions dopant at the moving interface (cited `m`; `segregation_flux` → boron
  depletes, phosphorus piles up). The module docstring is its contract (the unified `dx_ox/dt=0`
  degenerate seam, the OED effective-`∫D dt` analytic leg, the validated-vs-calibrated split, and the
  **swept-sliver scope edge** — boron depletion robust, phosphorus pile-up direction-real-but-~2×-high
  on the fixed grid). Saves `docs/figures/chip-oed-segregation.png`.
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
- **v1.1 — the Massoud thin-dry correction (Phase 2's scope edge, promoted): BUILT** (2026-06-10).
  `oxidation.py` §5 — the cited Massoud **time-decay** enhancement (Massoud & Plummer, *J. Appl.
  Phys.* 62:3416, 1987; refit `B`/`B/A` from *JECS* 132:1746, 1985; constants per Hollauer TU Wien
  diss. 2007 Tables 2.3/2.4, dry O₂ 800–1000 °C, three orientations) with its **exact closed form**
  `x²+Ax = Bt + ΣMᵢ(1−e^(−t/τᵢ)) + (xᵢ²+Axᵢ)` + `solve_ivp` cross-check + degenerate-recovery seam
  (`K=0` → plain Deal–Grove bit-for-bit; the default path untouched). + `demo_thin_oxide.py` +
  `plots.thin_oxide_figure`. Banked artifact: the **gate-oxide before/after** — the Phase-4 recipe
  (dry 1000 °C/20 min) grows **14.1 nm under v1 Deal–Grove but 23.3 nm under Massoud (×1.65)**,
  and feeding both to Phase 4 moves **V_t by +0.44 V** — the thin-dry anomaly was a V_t-sized error
  in the chain, not a footnote (`docs/figures/chip-thin-oxide.png`). 16-test mini-triad green
  (11 module + 5 demo): the integrated quadratic identity to machine precision, the saturating
  `M₁+M₂` dose, the cited-table pins + Hollauer's own Fig.-2.19 point, the τ **sign-typo finding**
  (the dissertation prints `exp(−E_τ/kT)`; only `exp(+E_τ/kT)` reproduces its own figure — the
  positive sign is pinned in code and tests).
- **v1.2 — the Phase 1↔2 back-coupling (OED + dopant segregation): BUILT** (2026-06-10). `coupling.py`
  — the named §3 deferral of both `oxidation` and the plan, **promoted** (the steel-ferrite-bay /
  Massoud move). Two oxidation back-reactions on the Phase-1 profile, both expressible **within the
  frozen engine** (the decisive architecture finding — **no contract amendment**): **OED**
  (oxidation-enhanced diffusion) is the engine's already-frozen variable-`D(t)` callable
  (`D_eff/D_inert = 1 + f_I·Δ`, supersaturation `Δ ∝ (dx_ox/dt)^0.5`, cited `f_I` B 0.30 / P 0.38);
  **segregation** is a `Neumann(flux(t))` BC (`J = N_surf·(0.44 − 1/m)·dx_ox/dt`, cited `m` B 0.3 / P
  10 → boron depletes, phosphorus piles up). + `demo_coupling.py` + `plots.coupling_figure`. Banked
  artifact: **boron depletion beside phosphorus pile-up**, each decomposing inert → +OED (deeper,
  ×~2 effective `∫D dt`) → +segregation (surface reshaped) (`docs/figures/chip-oed-segregation.png`).
  19-test triad: the **unified degenerate seam** (`dx_ox/dt=0` → plain `drive_in` bit-for-bit — drop
  the wrong `m→∞` anchor, the advisor's first call), the **OED ≡ effective-`∫D dt`** analytic leg (the
  frozen variable-`D` τ-substitution), OED-alone dose conservation, the cited `f_I`/`m` direction
  benchmarks. **The named scope edge (the advisor's blocking call): the swept-sliver double-count** —
  the segregation flux is a *moving-interface* mass balance run on a *non-moving* grid, so the `0.44·R`
  recession term is counted twice; the **`m→∞` inert-oxide diagnostic** pins the artifact (spurious
  ~10% silicon-dose gain). Consequence owned in code/tests/figure: **boron depletion robust**
  (oxide-uptake-dominated, the device-relevant case), **phosphorus pile-up direction real but
  magnitude ~2× high**; the coupled "conservation" is an **accounting identity, not a magnitude
  check**. Sb kept a *qualitative* ORD scope edge (`f_I`=0.015 → ≈1.05, not a retardation number).
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
jupyter lab chip/chip.ipynb  # (classic UI: `pip install notebook`, then `jupyter notebook`)
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
./run_tests.ps1 chip   # scope to chip while iterating
```

`pyproject.toml`'s `testpaths` already carries `projects`, so `chip/tests/` is collected
with no config change; `pythonpath = ["."]` lets chip import the frozen engine as `engines.diffusion…`.
The notebook smoke-test (`tests/test_chip_notebook.py`) is `slow`-marked, so the fast lane deselects it;
it runs in the full gate (`python -m tools.gate chip` / `./run_tests.ps1`).
