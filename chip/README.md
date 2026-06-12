# `chip` — the microchip fabrication simulator

*Process recipe in, device out.* Project #2 of the program and the **first consumer of the
diffusion/heat spine** (`engines/diffusion`): it builds **no** new shared engine — it
proves the spine reuses. Dopant profiles *are* the carbon-diffusion code Steel froze, in **mass
mode**. Full plan: [`docs/plans/microchip-fabrication.md`](../../docs/plans/microchip-fabrication.md).

> **Units — each module computes in its cited data's native units** (the deliberate departure from
> Steel's project-wide SI), so **no load-bearing constant is converted on the way in**; **µm is the
> cross-module length currency** (junction depths and oxide thicknesses both reported in µm).
> *Dopant diffusion* (`diffusion_dopant.py`, `junction.py`) uses **semiconductor CGS** — cm /
> cm²·s⁻¹ / cm⁻³ / cm²·V⁻¹·s⁻¹ — the native units of Fair `D₀`, Trumbore `N_s`, Masetti `μ` (the
> engine is unit-agnostic, fed cm + seconds; `R_s` falls out in Ω/sq directly). *Oxidation*
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
  `engines/diffusion/CONTRACT.md` (**mass mode**: Dirichlet predep surface / Neumann(0)
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
  closed form** (Deal–Grove `x²+Ax=B(t+τ)`, wet/dry) — **does not touch the engine**;
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
  **Fourier optics**, chip-local (not promoted to `engines/`); the *imaging* path does not touch the
  engine (its v1.7 **PEB resist back-end does** — see below).
  Core: `coherent_image` (the `|Σ orders|²` primitive) → `two_beam_image` (the exact `4cos²(πx/p)`
  anchor) + `abbe_image` (the partially-coherent **Abbe sum-over-source** workhorse, with
  `conventional_source`/`offaxis_source`); `rayleigh_resolution` (`R=k₁λ/NA`), `transmitted_power` (the
  Parseval power-balance), `image_contrast`/`nils`, `print_cd` + `expose_grating` (constant-threshold
  resist → CD in nm/µm). The module docstring is its contract (cited `k₁`/NILS, the
  scalar/Abbe-not-Hopkins/threshold-resist scope edge — **defocus is now modelled, v1.4 below**). Saves
  `docs/figures/chip-litho.png`.
- **To work on defocus & the depth of focus (v1.4 — Phase 3's "in-focus pupil" scope edge, promoted):**
  `litho.py` §7 + `tests/test_defocus.py`, the demo `demo_defocus.py` + `tests/test_demo_defocus.py`, and
  `plots.defocus_figure`. Defocus is a pure **phase** aberration, so it lives **inside** the existing
  Fourier-optics machinery — **no new path, no engine touch**: `defocus_phase` (the pupil phase
  `exp(i·(2π/λ)·z·(1−cosθ))` on the full pupil coordinate `f_m+f_s`; `z=0` → in-focus **bit-for-bit**)
  multiplies each collected order, threaded through `abbe_image`/`expose_grating` (`defocus_nm=0.0`).
  `Imaging.depth_of_focus`/`rayleigh_depth_of_focus` (`DOF=k₂λ/NA²`, `K2_DOF=0.5`), `fundamental_amplitude`
  (the `⟨I,cos(2πx/p)⟩` projector — the defocus-clean observable). The module docstring §7 is its contract
  (the symmetric-dipole infinite-DOF anchor, the three-beam fundamental `4c₀c₁cosφ` nulling at φ=π/2, the
  unitary power-conservation leg, the derived-not-cited `k₂=0.5`). Saves `docs/figures/chip-defocus.png`.
- **To work on the PEB acid-diffusion blur (v1.7 — Phase 3's "constant-threshold resist" scope edge,
  promoted):** `litho.py` §8 + `tests/test_peb.py`, the demo `demo_peb.py` + `tests/test_demo_peb.py`,
  and `plots.peb_figure`. The post-exposure bake IS a diffusion solve, so litho's resist back-end
  **rides the engine** (the finding that inverts the module's founding line): `peb_blur` runs
  `engines.diffusion` in **acid mode** — `u` = latent acid, constant `D`, `Neumann(0)` both faces (the
  cited sealed-film BC) — on the **half-period symmetry cell** `[0, p/2]`, whose Neumann eigenmodes are
  exactly the even image's cosine harmonics (the bounded solve IS the infinite periodic blur);
  `peb_diffusion_length` (`σ=√(2Dt)`), `standing_wave_period` (`λ/2n`), `PEB_DIFFUSION_SERIES_NM`,
  threaded as `expose_grating(..., peb_diffusion_length_nm=σ)` (every metric then reads the post-bake
  latent image; `σ=0` → v1 bit-for-bit). The module docstring §8 is its contract (the per-harmonic heat
  kernel `exp(−2π²k²σ²/p²)`, the dose-conservation/power-balance leg, the **PEB window** — erase the
  `λ/2n` ripple, keep the image — and the linear-exposure / constant-`D` / no-`(x,z)`-volume scope
  edges). Saves `docs/figures/chip-peb.png`.
- **To work on lateral diffusion under a mask edge (v1.8 — the 2-D regime, the engine's last deferred
  regime pulled in):** `chip/diffusion_2d.py` + `tests/test_diffusion_2d.py`, the demo
  `demo_lateral_diffusion.py` + `tests/test_demo_lateral_diffusion.py`, and
  `plots.lateral_diffusion_figure`. The consumer that finally pulls in the **2-D engine**
  (`engines/diffusion/diffusion2d.py` — `Diffusion2D`/`Grid2D`/`MaskedSurface`, the third exercise of
  the unfreeze; its CONTRACT invariant 7 is the seal). `lateral_diffusion` runs a boron constant source
  through a mask **window** (`MaskedSurface`: Dirichlet `N_s` under the window, no-flux under the mask;
  other three edges `Neumann(0)`) — that piecewise surface BC is what makes the problem **non-separable**;
  `junction_geometry` reads the vertical (window-centre) and lateral (under-mask) junctions and their
  ratio. The module docstring is its contract (the dimensional-collapse seam to the 1-D engine = the
  tight anchor; the lateral/vertical ratio = the **loose** cited benchmark, ≈0.82 at `C_B/N_s=1e-4`
  after Kennedy–O'Brien 1965, the model running slightly high; the constant-source / isotropic-`D` /
  3-D scope edges). Saves `docs/figures/chip-lateral-diffusion.png`.
- **To work on the CAR reaction–diffusion PEB (v1.9 — Phase 3's "constant-`D`" scope edge, promoted):**
  `litho.py` §9 + `tests/test_car.py`, the demo `demo_car.py` + `tests/test_demo_car.py`, and
  `plots.car_figure`. Where v1.7 found the bake IS the engine's pure linear PDE, the realistic
  chemically-amplified bake is a coupled **two-field** reaction–diffusion system (acid `h` +
  blocked-site fraction `m`) that does **not** fit the single-field engine natively, so it rides the
  engine **consumer-side by operator splitting** (the v1.2 moving-boundary move; no engine amendment):
  the engine carries only the acid-**diffusion** sub-step (`Neumann(0)` sealed faces, `D_h(m)` array-`D`
  frozen per step), while `litho._car_react` integrates the local reaction (acid-catalyzed deprotection
  + first-order acid loss) in **closed form**. `CARBake` (the cited APEX-E recipe) → `car_peb` (the
  Strang-split bake, returning `(deprotection, acid)`) → `expose_grating_car` (develop on the
  deprotection `1−m`, the chemically-faithful resist). The module docstring is its contract (the tight
  anchors = the no-reaction → v1.7-blur bit-for-bit seam and the flat-field exact-ODE; the catalyst
  `∫h` conservation; the **loose** amplification-sharpens / diffusion-loss-degrade benchmark; the linear-
  exposure / constant-threshold-develop / uncalibrated-`D_h1` scope edges). Saves `docs/figures/chip-car.png`.
- **To work on Zernike aberrations (v1.10 — Phase 3's "aberration-free pupil apart from defocus" scope
  edge, promoted):** `litho.py` §10 + `tests/test_zernike.py`, the demo `demo_zernike.py` +
  `tests/test_demo_zernike.py`, and `plots.zernike_figure`. The **same finding as v1.4 defocus** — a
  Zernike aberration is a pure **phase** on the pupil, so `coherent_image` images through it with no new
  path. An `Aberrations` dataclass (coma / astigmatism / spherical in **waves** + a `grating_azimuth_deg`
  φ_g) → `zernike_phase` (the balanced-Zernike radial polynomials on the 1-D pupil slice: coma ODD
  `3u³−2u`, astig EVEN `u²cos2φ_g`, spherical EVEN `6u⁴−6u²`) threaded through `abbe_image`/`expose_grating`
  as `aberrations=None`; `fundamental_complex` is the quadrature-aware fundamental that **distinguishes
  coma from defocus** (its phase = the coma fringe shift, where the cos-only `fundamental_amplitude` is
  blind). The module docstring is its contract (the tight anchors = the no-aberration bit-for-bit seam,
  the even/odd **parity pair**, the coma↔defocus phase discriminator, and unitary power conservation; the
  **loose** signatures = coma placement error / astig H↔V best-focus split / spherical pitch-dependent
  focus; scope edges = the 1-D pupil slice, paraxial-astig degeneracy, no asserted Strehl). Saves
  `docs/figures/chip-zernike.png`.
- **To work on the 2-D MOSFET cross-section (v1.11 — the 2-D engine wired into the device flow):**
  `device_2d.py` + `tests/test_device_2d.py`, the demo `demo_device_2d.py` +
  `tests/test_demo_device_2d.py`, and `plots.device_2d_figure`. Composes **v1.8** (`diffusion_2d`, the
  masked 2-D diffusion) with **Phase 4** (`device`): the gate is the S/D's self-aligned mask, so the
  lateral encroachment `ΔL` shortens the channel to `L_eff = L_drawn − 2·ΔL`, which feeds `I_Dsat`
  (`V_t` stays long-channel — the guarded boundary). `mosfet_cross_section` (the headline, with the
  `lateral=False` Phase-4 seam + the punchthrough refusal), `effective_channel_um` (the cheap two-window
  sweep), and the `_isolated_edge` / `_two_window_solve` internals. A **validation deepening** — the
  two-window solve **confirms** the textbook `L_drawn − 2·ΔL` and the punchthrough limit `≈ 2·ΔL`; the
  module docstring is its contract (tight = the bit-for-bit seam + two-window≡subtraction toward the
  knee; guards = `V_t`∥L and `I_Dsat ∝ 1/L`; loose = the cited lateral ratio + punchthrough). Saves
  `docs/figures/chip-device-2d.png`.
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
  profile), built **entirely on the engine** — OED is its already-supported variable-`D(t)`
  callable, segregation a `Neumann(flux(t))` BC — **no engine amendment** (OED is a *linear* `D(t)`
  of oxidation rate, genuinely engine-native; contrast the genuinely-**nonlinear** `D(N)` of v1.3,
  which *was* promoted to the engine's native `StateDependent` Picard path at the unfreeze — v1.5).
  `oxidize_couple` runs an oxidizing
  anneal: **OED** enhances `D` (cited `f_I`; `oed_enhancement_factor`/`interstitial_supersaturation`),
  **segregation** partitions dopant at the moving interface (cited `m`; `segregation_flux` → boron
  depletes, phosphorus piles up). The module docstring is its contract (the unified `dx_ox/dt=0`
  degenerate seam, the OED effective-`∫D dt` analytic leg, the validated-vs-calibrated split, and the
  **swept-sliver scope edge** — boron depletion robust, phosphorus pile-up direction-real-but-~2×-high
  on the fixed grid). Saves `docs/figures/chip-oed-segregation.png`.
- **To work on concentration-dependent diffusivity (v1.3 — the high-concentration box):**
  `diffusion_highconc.py` + `tests/test_diffusion_highconc.py`, the demo `demo_diffusion_highconc.py`
  + `tests/test_demo_diffusion_highconc.py`, and `plots.highconc_figure`. The Phase-1 **`D(N)`** scope
  edge, promoted. **`D(N)` now runs on the engine's native nonlinear path** (`StateDependent` + Picard
  = the fully-implicit nonlinear backward-Euler solve): the v1.3 consumer-side lagged-coefficient hook
  (a workaround for the then-frozen engine) was **promoted into the engine** at the unfreeze — so
  `_diffuse_dn` is now a thin step-loop over a `StateDependent` solver, and the degenerate-seam /
  convergence invariants live in `engines/diffusion/tests/test_nonlinear_d.py`.
  `effective_diffusivity` is the cited **Fair charge-state** `D_eff = D⁰+D⁻(n/n_i)+D⁼(n/n_i)²`
  (`CHARGE_STATE_TERMS`, Plummer Ch. 7 / Fair–Tsai 1977); `intrinsic_carrier_concentration` the `n_i(T)`;
  `predeposit_highconc`/`drive_in_highconc` the fab steps (the box), `constant_D_predeposit` the
  baseline, `n_active_max` the activation/plateau cap. The module docstring is its contract (the native
  path, the model's `D_eff → D⁰+D⁻+D⁼` low-conc limit / Boltzmann-similarity / conservation-as-machinery
  triad, and the **scope edge** — the box front captured, the anomalous **tail/kink** named-not-modelled).
  Saves `docs/figures/chip-highconc.png`.
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
  engine** (the decisive architecture finding — **no contract amendment**): **OED**
  (oxidation-enhanced diffusion) is the engine's already-supported variable-`D(t)` callable
  (`D_eff/D_inert = 1 + f_I·Δ`, supersaturation `Δ ∝ (dx_ox/dt)^0.5`, cited `f_I` B 0.30 / P 0.38);
  **segregation** is a `Neumann(flux(t))` BC (`J = N_surf·(0.44 − 1/m)·dx_ox/dt`, cited `m` B 0.3 / P
  10 → boron depletes, phosphorus piles up). + `demo_coupling.py` + `plots.coupling_figure`. Banked
  artifact: **boron depletion beside phosphorus pile-up**, each decomposing inert → +OED (deeper,
  ×~2 effective `∫D dt`) → +segregation (surface reshaped) (`docs/figures/chip-oed-segregation.png`).
  19-test triad: the **unified degenerate seam** (`dx_ox/dt=0` → plain `drive_in` bit-for-bit — drop
  the wrong `m→∞` anchor, the advisor's first call), the **OED ≡ effective-`∫D dt`** analytic leg (the
  variable-`D` τ-substitution), OED-alone dose conservation, the cited `f_I`/`m` direction
  benchmarks. **The named scope edge (the advisor's blocking call): the swept-sliver double-count** —
  the segregation flux is a *moving-interface* mass balance run on a *non-moving* grid, so the `0.44·R`
  recession term is counted twice; the **`m→∞` inert-oxide diagnostic** pins the artifact (spurious
  ~10% silicon-dose gain). Consequence owned in code/tests/figure: **boron depletion robust**
  (oxide-uptake-dominated, the device-relevant case), **phosphorus pile-up direction real but
  magnitude ~2× high**; the coupled "conservation" is an **accounting identity, not a magnitude
  check**. Sb kept a *qualitative* ORD scope edge (`f_I`=0.015 → ≈1.05, not a retardation number).
- **v1.3 — concentration-dependent diffusivity `D(N)` (the high-concentration box): BUILT** (2026-06-10).
  `diffusion_highconc.py` — the Phase-1 `D(N)` scope edge, promoted. **The decisive finding: `D(N)` — the
  case both `CONTRACT.md` and §3 flagged as a v1.1 engine amendment — fits *within* the engine, no amendment.** The consumer's step-loop + a `D(t)` closure over the evolving field = a
  **lagged-coefficient `D(N)`** (one solve/step, zero engine edits), Picard-converging to the
  fully-implicit nonlinear solve (`2==6`, dt-stable). Cited **Fair charge-state** model
  `D_eff = D⁰+D⁻(n/n_i)+D⁼(n/n_i)²` (Plummer Ch. 7 / Fair–Tsai 1977); `n_i(T)=3.87e16·T^1.5·exp(−0.605/kT)`.
  Phosphorus's `D⁼` `(n/n_i)²` term drives the **box**. + `demo_diffusion_highconc.py` +
  `plots.highconc_figure`. Banked artifact: constant-`D` `erfc` vs the `D(N)` box (capped-physical +
  uncapped upper bound) + the `D_eff/D_intrinsic` mechanism (`docs/figures/chip-highconc.png`); P predep
  1000 °C/30 min → `x_j` **0.34 → 0.76 µm** (×2.2 deeper, capped; ×42 surface `D`). **14-test triad:** the
  **degenerate seam** (constant `D` through the closure == scalar engine **bit-for-bit** — the hook *is*
  the engine), **Boltzmann similarity** (`x/√t` collapse, model-independent, holds for the stiff `n²`),
  **dose conservation** with `D(N)` active (a **machinery** check — telescoping is `D`-independent — *not*
  a magnitude validation), the box-front/deeper-junction benchmark (cited not fit), Picard convergence.
  Scope edge named-not-modelled: equilibrium `D(n)` captures the box **front** + deeper junction, **not**
  the anomalous **tail/kink** (non-equilibrium I-injection/clustering — Velichko 2019, Fair–Tsai
  emitter-dip); full activation (`n=N`) is the flagged approximation, made adjustable by the
  `n_active_max` plateau cap. **No ADR / no engine re-seal** (the finding obviated them); seal intact.
  *(Superseded 2026-06-10 by the v1.5 promotion below: with the engine unfrozen, this nonlinear solve
  moved into the engine's native `StateDependent` Picard path — the lagged-closure hook is gone.)*
- **v1.4 — lithographic defocus, the depth of focus & the Bossung curve: BUILT** (2026-06-10).
  `litho.py` §7 — Phase 3's **"ideal in-focus pupil"** scope edge, promoted. Defocus is a pure **phase**
  aberration, so it fits **inside** the litho module (no new path, engine untouched): `defocus_phase`
  multiplies each collected order by `exp(i·(2π/λ)·z·(1−cosθ))` (keyed to the full pupil coordinate
  `f_m+f_s`), threaded through `abbe_image`/`expose_grating` — `z=0` is the in-focus image **bit-for-bit**.
  + `demo_defocus.py` + `plots.defocus_figure`. Banked artifact: the **Bossung curve** (printed CD vs
  defocus, a dose family, the process window + `DOF=k₂λ/NA²` marked) beside the **through-focus
  fundamental** (the on-axis three-beam coefficient riding the exact `4c₀c₁cosφ` envelope, nulling at
  φ=π/2, then reversing — defocus-induced frequency doubling; the σ-source curve softens the null)
  (`docs/figures/chip-defocus.png`); 193 nm ArF, NA 0.85, σ 0.5, 240 nm pitch → DOF ≈ 134 nm, the φ=π/2
  null at ±119 nm. **16-test mini-triad** (11 module + 5 demo): *analytic* = the **z=0 bit-for-bit seam**,
  the **symmetric-dipole infinite-DOF** (equal pupil radii → identical phase factors out → image
  unchanged at every z, to machine precision), the asymmetric two-beam **fundamental = 2cosφ** (modulation
  rotates, contrast preserved), the on-axis three-beam **fundamental = 4c₀c₁cosφ** to machine precision
  (NOT the contrast metric — which keeps the defocus-independent 2nd harmonic → frequency doubling at the
  null, pinned); *conservation* = **defocus is unitary** (phase-only → `mean(image)=Σ|c_m|²=transmitted_power`
  at every z, machine precision); *benchmark* = the Bossung CD/NILS degradation + `k₂=0.5` **derived** from
  the φ=π/2 null at the resolution limit (paraxial; the exact full-cosθ null converges onto it as NA→0).
  Zernike aberrations (coma/astigmatism/spherical) and immersion NA≥1 (vector) stay the named scope edges.
- **v1.5 — `D(N)` promoted to the engine's native nonlinear path (the first exercise of the unfreeze): BUILT**
  (2026-06-10). With the engine **unfrozen** (ADR 0004 — open + test-gated), v1.3's consumer-side
  lagged-coefficient hook (a workaround for the then-frozen engine) was promoted **into the engine itself**:
  `engines/diffusion` gained a native nonlinear diffusivity `StateDependent(func)`, solved per step by
  **Picard** (the fully-implicit nonlinear backward-Euler solve). `diffusion_highconc.py`'s `_diffuse_dn` is
  now a thin step-loop over a `StateDependent` solver — no field holder, no `picard_iters` corrector knob (the
  engine converges the step). **Picard, not Newton** (deliberate): each iterate is an ordinary linear
  backward-Euler solve with `D≥0`, so the nonlinear path inherits the engine's monotonicity + structural
  conservation **per iterate**. **Additive:** only `StateDependent` enters the loop, so the **18 prior engine
  invariants pass unmodified** — the proof the amendment did not break a consumer. New engine seal
  `engines/diffusion/tests/test_nonlinear_d.py` (**10 tests:** the degenerate seam `StateDependent(const)==scalar`
  **bit-for-bit** (backward-Euler *and* Crank–Nicolson), the Picard fixed-point residual, no-flux conservation
  with `D(u)` active, the model-independent **Boltzmann-similarity** collapse, lagged→converged consistency, an
  in-bounds front). Engine suite **18→28**; whole-repo fast lane **188**. `CONTRACT.md`'s "nonlinear `D(u)` is v1.1, not built" line is
  now **built** (invariant 6); 2-D / explicit stay the deferred regimes. The box physics + demo numbers are
  unchanged (v1.3's `picard_iters=2` was already ~converged), so the v1.3 banked figure stands. **No new ADR**
  — ADR 0004 names native nonlinear `D(u)` as *the* example of an ordinary test-gated edit.
- **v1.7 — PEB acid-diffusion blur (Phase 3's "constant-threshold resist" scope edge, promoted): BUILT**
  (2026-06-11; v1.6 was the engine's explicit `forward_euler` amendment — no chip surface). `litho.py`
  §8 — and the architecture finding **inverts litho's founding line**: the post-exposure bake IS the
  program's PDE (Fick's law on the latent acid/PAC — Kirchauer §7.1.2: `σ=√(2Dt)`, Gaussian-kernel
  solution, sealed-film homogeneous-Neumann BC), so the chip's one engine-free module now runs its
  resist back-end on `engines.diffusion` in **acid mode** (no engine amendment — pure consumer; the
  spine's third chip use). `peb_blur` solves on the **half-period symmetry cell** `[0, p/2]` (no-flux
  faces = the even image's mirror planes; Neumann eigenmodes = the image's cosine harmonics → the
  bounded solve IS the infinite periodic blur), threaded as `expose_grating(...,
  peb_diffusion_length_nm=σ)` — development then clips the **post-bake latent image** (the
  diffused-image resist model; `σ=0` → v1 **bit-for-bit**). + `demo_peb.py` + `plots.peb_figure`.
  Banked artifact: the **latent image dissolving** over the cited 20/40/60 nm series beside the **PEB
  window** (engine retention points riding the two analytic heat kernels — erase the `λ/2n`
  standing-wave ripple, keep the pitch-`p` fundamental) (`docs/figures/chip-peb.png`); 193 nm ArF,
  NA 0.85, 240 nm pitch, n_resist 1.70 → window σ ∈ [28, 45] nm, closing at `p_close = λ/4nc` ≈ 151 nm
  (**NA-independent** — resist index + keep-floor only); this lands on the partial-coherence cutoff
  `λ/NA(1+σ)` ≈ 151 nm — a **λ-independent coincidence** (ratio `NA(1+σ)/4nc` ≈ 1.0, two independent
  parameter groups matched to 0.06%), not a law. At NA 0.93 the cutoff slides to ≈138 nm while
  `p_close` stays pinned, so a 145 nm pitch **images fine but cannot survive a ridge-erasing bake**
  (the lens out-resolves the bake → why modern stacks use a BARC; the cited ARC/dye/PEB mitigation list).
  **17-test mini-triad** (12 module + 5 demo): *analytic* = the **σ=0 bit-for-bit seam** + σ→0
  continuity, a bare **Neumann eigenmode decaying by its exact eigenvalue exponential**, a realistic
  Abbe image attenuated **per harmonic** by the periodic heat kernel `exp(−2π²k²σ²/p²)` (engine vs
  closed form, ~2e-6 floor), max-principle bounds; *conservation* = **the bake conserves acid dose**
  → the v1 Parseval power balance survives every σ to machine precision (corollary: the mean-clip
  dose is blur-invariant); *benchmark* = monotone contrast/NILS/CD degradation over the cited series
  (NILS through the cited ≥1 floor), the CD collapsing onto the pure-fundamental `p/2` readout, the
  **half-period smoothing rule** opening the window at 240 nm and closing it at dense pitch.
  Asymmetric images (off-axis pole + defocus — no mirror plane) are **refused, not mis-blurred**;
  linear exposure (no Dill), constant `D` (no CAR reaction–diffusion), and the uncoupled `x`/`z`
  treatment stay the named scope edges.
- **v1.8 — lateral diffusion under a mask edge (the 2-D regime, the engine's last deferred regime,
  finally pulled in): BUILT** (2026-06-12; the THIRD exercise of the unfreeze, and the consumer
  v1.6's advisor said to *wait* for). `engines/diffusion` gained a *new module* `diffusion2d.py`
  (`Diffusion2D`, tensor-product `Grid2D`, the `MaskedSurface` window/mask edge BC — see the engine
  CONTRACT invariant 7); the chip consumer is `chip/diffusion_2d.py` (`lateral_diffusion`,
  `junction_geometry`). A boron constant source (Trumbore `N_s`, 1100 °C / 60 min) enters through a
  mask window and diffuses **down and sideways under the mask**; the pn junction is a 2-D contour that
  curves up under the mask edge. **The design crux (advisor): the problem is only genuinely 2-D
  because of the piecewise `MaskedSurface` BC** — a sealed drive-in from a windowed IC would be
  separable (the outer product of two 1-D runs) and would not need the regime. **The tight anchor is
  the dimensional-collapse seam** (the window-centre column == the analytic 1-D `erfc` junction
  `erfcinv(C_B/N_s)·2√(Dt)` to numerical precision), **not** the outer-product theorem (continuous-only;
  discrete BE breaks it at O(dt²) — a Kronecker sum, demoted to an O(dt) convergence check).
  + `demo_lateral_diffusion.py` + `plots.lateral_diffusion_figure`. Banked artifact: the `N(x,y)`
  field with the junction curving under the mask, beside the **lateral/vertical ratio vs C_B/N_s**
  (`docs/figures/chip-lateral-diffusion.png`); device junction → vertical ≈ 0.85 µm, ratio ≈ 0.90.
  **9-test mini-triad** (5 consumer + 4 demo). **The benchmark is honestly LOOSE** (advisor): the
  ratio is **domain-converged** (a 2× domain is bit-identical → not a wall artifact), the shallow
  contours sit in the cited **0.75–0.85** band and the ratio **rises toward deeper contours**
  (Kennedy–O'Brien 1965 — the junction sits closer to its source at the surface); but at the one cited
  point (≈ 0.82 at `C_B/N_s = 1e-4`) the model runs ~5–10 % high, so the device deep-contour ~0.90 is
  the **model's own value within the read-off uncertainty of a 1965 graph, not a sourced number** — the
  validation weight is the tight erfc anchor, not hitting 0.8. (For this constant-source geometry the
  maximum lateral encroachment is at the surface — surface ≡ max-over-depth.) Engine suite **34→45**;
  whole-repo fast lane **218→238**. **No new ADR** (ADR 0004 pre-authorizes the engine amendment).
  Anisotropic / time-dependent `D`, Gaussian (limited-source) lateral, and 3-D stay the scope edges.
- **v1.9 — CAR reaction–diffusion PEB (Phase 3's "constant-`D`" scope edge, promoted): BUILT**
  (2026-06-12). `litho.py` §9 — and where v1.7 found the bake IS the engine's pure linear PDE, the
  realistic chemically-amplified bake is a coupled **two-field** reaction–diffusion system (Kirchauer
  §7.1.2, the same thesis as v1.7 — `[[peb-acid-diffusion-source]]`): on the blocked-site fraction `m`
  (1→0) and the acid `h`, `∂m/∂t = −k_amp·m·hⁿ` (deprotection) and `∂h/∂t = −k_loss·h + ∂ₓ(D_h(m)∂ₓh)`
  (acid: first-order loss + diffusion). It does **not** fit the single-field engine natively (the
  `−k_loss·h` loss is ∝`u`; `m` is a second field; `D_h` depends on `m` not `h`), so it is built
  **consumer-side by operator splitting** (the v1.2 moving-boundary move; **no engine amendment, no
  ADR**): the engine carries only the acid-**diffusion** sub-step (`Neumann(0)` sealed faces, `D_h(m)`
  array-`D` frozen per step from the lagged deprotection), while `_car_react` integrates the local
  reaction in **closed form**. `car_peb` Strang-splits the bake (½-react · diffuse · ½-react) and
  `expose_grating_car` develops on the **deprotection** `1−m` (the chemically-faithful resist, where
  v1.7 clipped the acid). **The diffusion sub-step is backward Euler — NOT v1.7's CN** (advisor):
  `hⁿ` with non-integer `n` NaNs on any negative ring, and BE's max principle keeps `h≥0` so the bake
  never NaNs *and* keeps `∫h` conservation exact (a CN ring would need a mass-adding clamp). +
  `demo_car.py` + `plots.car_figure`. Banked artifact: the **latent image developing** (the deprotection
  edge sharpening above the acid) beside the **PEB process window** (CD vs bake time + the exact
  acid-loss decay) (`docs/figures/chip-car.png`); 193 nm ArF, NA 0.85, 240 nm pitch, cited APEX-E @
  90 °C (`k_amp=2.0/s`, `k_loss=0.0033/s`, `n=1.8`, `D_h,0=0.0933 nm²/s`; the exposure dose + bake
  times are illustrative knobs). **16-test mini-triad** (11 module + 5 demo): *analytic* = the
  **no-reaction → v1.7-blur bit-for-bit seam** and the **flat-field exact-ODE** (a uniform acid sees
  identity diffusion ⇒ the split is the closed-form reaction flow, machine precision); *conservation*
  = **acid is a pure catalyst** (no `h·m` sink) ⇒ `∫h` conserved at `k_loss=0` / decays exactly
  `e^{−k_loss·t}`, deprotection bounded in `[0,1]` and monotone in bake; *benchmark (loose)* =
  **amplification sharpens** (the superlinear `hⁿ` edge steeper than the acid's — NILS up, the regime,
  not a law) vs **diffusion + loss + over-bake degrade** (the acutely bake-sensitive CD). Asymmetric
  images are **refused** (the half-period cell, as v1.7); linear exposure (no Dill), constant-threshold
  development (no Mack dissolution kinetics), the uncalibrated free-volume `D_h,1`, and the uncoupled
  `x`/`z` blurs stay the named scope edges. Whole-repo fast lane **238→254**.
- **v1.10 — Zernike aberrations (coma, astigmatism & spherical), a pupil phase: BUILT** (2026-06-12).
  `litho.py` §10 — Phase 3's "aberration-free pupil apart from defocus" scope edge, promoted on the
  **same finding as v1.4**: a Zernike aberration is a pure **phase** on the pupil, so `coherent_image`
  images through it with no new path. An `Aberrations` dataclass (coma / astigmatism / spherical in
  **waves** + a `grating_azimuth_deg` φ_g) and `zernike_phase` (the balanced-Zernike radial polynomials
  on the 1-D pupil slice `u = f_total/f_cut`: coma `(3u³−2u)cosφ_g` ODD, astig `u²cos2φ_g` EVEN,
  spherical `6u⁴−6u²` EVEN → `exp(i·2π·W)`), threaded through `abbe_image`/`expose_grating` as
  `aberrations=None` (the unaberrated seam **bit-for-bit**), kept **separate from** `defocus_nm`
  (waves/paraxial-Zernike vs v1.4's exact nm `1−cosθ`). + `fundamental_complex` + `demo_zernike.py` +
  `plots.zernike_figure` → `docs/figures/chip-zernike.png` (coma's placement shift + the Δx-vs-coma
  inset, the astigmatism H↔V best-focus split, the spherical through-focus family). **15-test mini-triad**
  (11 module + 4 demo): *analytic* = the no-aberration **bit-for-bit seam**, the **parity pair** (even
  astig/spherical leave a symmetric dipole invariant; odd coma pure-shifts it, contrast preserved — the
  spherical case on an **interior** pair, since balanced `6u⁴−6u²` is trivially 0 at the rim), and **THE
  coma↔defocus discriminator** (the cos-only `fundamental_amplitude` returns `4c₀c₁cosφ` for *both*; the
  **complex** fundamental's phase is the coma fringe shift exactly — the v1.4 "assert the right observable"
  analogue, advisor); *conservation* = aberrations are **unitary** (`mean(image)=Σ|c_m|²=transmitted_power`
  at every coefficient — the v1.4 leg extended for free); *benchmark (loose)* = the litho-native signatures
  — coma → **placement error** + an asymmetric image the PEB cell **refuses**, astig → the **H↔V best-focus
  split** (what a defocus offset cannot mimic), spherical → **pitch-dependent best focus**. Scope edges
  named: the 1-D pupil slice of the 2-D Zernikes, the peak (not Noll RMS) coefficient, the **paraxial**
  astig≡defocus degeneracy (exact only as NA→0), and a **Strehl/Maréchal number left un-asserted** (needs
  the 2-D pupil-disk integral, not 1-D slice samples; λ/14 quoted only as scale). Whole-repo fast lane
  **254→269**. **No new ADR.**
- **v1.11 — the 2-D MOSFET cross-section (lateral S/D diffusion → effective channel length): BUILT**
  (2026-06-12). `device_2d.py` — the composition that wires the engine's **2-D regime** (v1.8,
  `diffusion_2d`) into the **process→device** payoff (Phase 4, `device`). A real self-aligned MOSFET
  forms its S/D with **the gate as the mask**, so the n⁺ S/D diffuses *down and sideways under the gate
  edges*, shrinking the drawn channel to an **effective** length `L_eff = L_drawn − 2·ΔL`. That `L_eff`
  is the honest place 2-D geometry moves a device number — it feeds the drive current (`I_Dsat ∝ W/L`,
  a shorter channel drives more current) while **`V_t` stays long-channel** (short-channel rolloff /
  DIBL is the named 2-D-electrostatics tar pit, left out — and a regression guard asserts `L` never
  leaks into `V_t`). A **validation deepening** (advisor-framed): the independent **two-window half-cell**
  solve (gate centre = a no-flux symmetry plane, S/D window *outside* — exactly the right half of the
  symmetric two-S/D device) reads the channel **directly** junction-to-junction (`L_eff_true = 2·x_j`)
  and **confirms** the textbook subtraction across the open range *and* the **punchthrough** limit at
  `L_drawn ≈ 2·ΔL`; its worth over "subtraction + clamp" is **physical grounding** (a real `N = N_channel`
  crossing → a hard `L_eff = 0` floor at front-merge) and **independence** (a *different BC topology*, so
  the agreement fails on a config/topology bug or if superposition broke). The front-interaction effect that would
  split the two near the knee is **below the resolved scale** (checked, not featured). Coherent ~0.5 µm
  node: p-channel `N_A = 1e17`, dry gate oxide ~11 nm, n⁺-P S/D 1000 °C / 6 min → `x_j` 0.12 µm, `ΔL`
  0.10 µm (ratio 0.86); headline `L_drawn` 0.50 µm → **`L_eff` 0.29 µm (42 % shorter)**, `I_Dsat` **×1.72**,
  `V_t` **0.38 V flat**; punchthrough ~0.21 µm. **13-test triad** (9 module + 4 demo): *analytic* = the
  exact **`lateral=False` seam** (recovers Phase 4 **bit-for-bit**, the σ=0/z=0/K=0 pattern) + **two-window
  ≡ subtraction asserted *down toward the knee*** (the genuine cross-check — different BC topology, not a
  wide-gate triviality); *conservation* = the **`V_t`∥L and `I_Dsat ∝ 1/L` guards** (by-construction —
  billed as guards, **not** anchors, the device.py self-consistency-leg framing); *benchmark (loose)* =
  the v1.8 cited lateral/vertical ratio → the ~40 % shortening + the punchthrough threshold `≈ 2·ΔL`.
  `demo_device_2d.py` + `plots.device_2d_figure` → `docs/figures/chip-device-2d.png` (the n⁺ S/D curving
  under the gate beside the `L_eff`-vs-`L_drawn` validation with `V_t` flat). Scope edges named: no
  short-channel `V_t`/DIBL (guarded), the **isolated-edge / superposition approximation** (the divergence
  is below the resolved scale here), punchthrough **refused**, constant-D S/D (the 2-D engine has no
  `D(N)` path), and the 1-D vertical device / ideal self-aligned mask. Cited: `L_eff = L_drawn −
  2·L_{D,lateral}` (Sze / Plummer / Taur–Ning) + v1.8's `[[lateral-diffusion-source]]`. Whole-repo fast
  lane **273→286**. **No engine edit, no new ADR** (chip-local composition of two validated modules).
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
./run_tests.ps1 -m "not slow" -n auto   # routine commit gate (fast lane, PARALLEL — ~16 s vs ~53 s serial; -n auto capped at half the logical cores)
./run_tests.ps1 chip   # scope to chip while iterating
```

`pyproject.toml`'s `testpaths` already carries `chip`, so `chip/tests/` is collected
with no config change; `pythonpath = ["."]` lets chip import the engine as `engines.diffusion…`.
The notebook smoke-test (`tests/test_chip_notebook.py`) is `slow`-marked, so the fast lane deselects it
(and `-n auto` therefore rides only the fast lane, never co-scheduling the notebook with the 286 —
**the pin**, ADR 0003 amendment); it runs in the serial full gate (bare `./run_tests.ps1`).
