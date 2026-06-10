# Microchip Fabrication Simulator — Project Plan

> Per-project plan **#2** of the educational-simulator program. Built to the
> **Section 10 template** of `ARCHITECTURE.md`; inherits Sections 2–9 as fixed
> invariants (compliance check in §8 below). This is the **second** project in
> build order (Steel → Microchip → Planet) and the **first consumer of the frozen
> diffusion/heat spine** — it builds *no* new shared engine, it proves the spine
> reuses (ARCHITECTURE.md §4).

---

## 1. One-line vision & the dramatic early win

**Vision.** *Process recipe in, device out:* take a bare silicon wafer, run it
through a sequence of fab steps — oxidation, dopant diffusion, lithography — and
watch a working **device parameter** (a junction, a threshold voltage) emerge from
real process physics, not a lookup table. This is the **process → device** loop,
the chip analogue of Steel's process → properties loop.

**The anchor demo (Phase 1's banked artifact).** *A pn junction from a two-step
diffusion.* A constant-source **predeposition** lays down an `erfc` dopant profile
at the solid-solubility limit; a sealed-surface **drive-in** then redistributes
that fixed dose deeper, the profile morphing toward a **Gaussian**; the **junction
depth** `x_j` emerges where the diffused profile crosses the background doping, and
the **sheet resistance** falls out of the integrated profile. The whole thing is
computed by the **frozen `engines/diffusion` solver with zero new engine code** —
predep is a Dirichlet surface, drive-in is a no-flux surface, both in mass mode.
*Recipe in (times, temperatures), junction out* — the cheapest, most direct proof
that the spine Steel built and froze reuses verbatim (dopant profiles **are** the
carbon-diffusion code, ARCHITECTURE.md §4.2), and simultaneously the integration
test for the Phase-1 module.

---

## 2. Shared engines consumed

| Engine | Status here | Contract pointer |
|---|---|---|
| **Diffusion/heat (Fick / erfc)** — the program spine | **`[reuse frozen ✓ — Steel Phase 1a]`** | `engines/diffusion/CONTRACT.md`. Loaded as the **one-page contract**, never Steel's internals (ARCHITECTURE.md §6/§11). Chip instantiates **mass mode** (`u = N`, dopant concentration; `D = D₀·exp(−Q_a/kT)` Arrhenius for B/P/As in Si): predeposition = **Dirichlet** surface (solid-solubility `N_s`), drive-in = **Neumann(0)** surface (sealed) + far-field Neumann(0). Exactly the mass-mode face `projects/steel/carburize.py` already exercised. |

**No new shared engine is built here.** The one genuinely-new module Chip adds is
the **aerial-image Fourier optics** (Phase 3) — but it is *chip-local*
(`chip/litho.py`), **not** promoted to `engines/`: only chip uses it, so
per invariant 5 / rule-of-three it stays project-local until a stabilized interface
has ≥3 uses (the same call `projects/steel/pathint.py` makes). Thermal oxidation
(Phase 2) is a small analytic/ODE module, also chip-local.

> **Freeze-before-reuse (invariant 5).** The diffusion solver was sealed behind its
> validation suite at the end of **Steel Phase 1a**; Chip is the first downstream
> consumer and touches only its `CONTRACT.md`. If Chip ever needs a behaviour the
> frozen contract does not promise (e.g. concentration-dependent `D(u)` — see the
> §3 Phase-1 scope edge), that is a **v1.1 contract amendment**, deliberate and
> tested, never an ad-hoc reach into the engine internals.

**Language & performance.** Python + NumPy/SciPy, per ADR 0001 (the program
default; chip compute is sub-second — 1-D profiles and a 1-D aerial image — so the
slider → re-run loop needs no special engineering). Engine contracts stay
data-oriented (arrays in/out), the seam ADR 0001 reserves for a future compiled
module.

---

## 3. Phases — each a complete, demonstrable artifact

Every phase names its **validation triad** concretely — an *analytical limit*, a
*conservation law*, and a *published benchmark* (invariant 3 / ARCHITECTURE.md §7).
Per the program discipline (and the way Steel recorded it), each phase also names
the **non-circularity split** — what is *validated* (asserted tight, anchored to an
independent fact) vs what is *calibrated* (a cited constant, flagged) — and its
**scope edge** (the regime where the model is honestly wrong).

### Phase 1 — Dopant diffusion & the pn junction (the foundation, spine reuse)

The constant-source **predeposition** (`erfc`) and limited-source **drive-in**
(`Gaussian`), then the **junction** and **sheet resistance** they produce. The
frozen engine in mass mode supplies the profile; chip adds only the dopant
Arrhenius `D(T)`, the junction reading, and the Irvin sheet-resistance map.

**Validation triad — Phase 1**
- *Analytical limit (constant D).* Predep matches `N(x,t) = N_s·erfc(x/2√(Dt))`;
  drive-in from a **delta-function surface dose** matches the exact **Gaussian**
  `N(x,t) = (Q/√(πDt))·exp(−x²/4Dt)`. These exact anchors hold the engine to its
  frozen erfc/Gaussian guarantee. **Scope edge, named (mirrors carburize's
  constant-D-vs-Tibbetts):** the analytic forms are exact only for **constant D**;
  real high-concentration diffusion is **concentration-enhanced** `D(N)` (the
  phosphorus kink-and-tail), which the frozen engine does **not** model (full
  `D(u)` is the contract's v1.1-flagged-unbuilt case). So the exact leg is
  validated in the **constant-D / moderate-dose** regime, and `D(N)` is the scope
  ceiling — *not* silently papered over.
- *Conservation.* The drive-in **dose `∫N dx` is conserved to machine precision**
  (sealed surface = no-flux both ends → the engine's own exact finite-volume
  guarantee, re-confirmed for this BC pair). The predep dose *grows* as the exact
  flux-bookkeeping identity `Q(t) = 2 N_s √(Dt/π)` (the engine's `flux`
  diagnostic integrated over time — the same identity carburize used for its
  Dirichlet surface).
- *Benchmark.* **Junction depth** `x_j(√Dt)` and **sheet resistance** `R_s` vs
  **Irvin's curves** (and SUPREM as the reference tool, used as *facts* not copied)
  — genuine cross-checks because `D₀, Q_a` are **cited diffusion data**, not fit to
  junction depth.

> **Keep the exact anchor separate from the realistic demo (Steel's split).** The
> *exact-Gaussian* leg uses the delta-IC idealization. The **banked demo** runs the
> realistic **predep(erfc) → drive-in** chain, whose drive-in starts from the actual
> `erfc` profile and is therefore only **near-Gaussian** — so the demo is *not*
> asserted against the exact Gaussian (that would let a realistic approximation
> wound the exact analytic leg). The demo's job is the *junction*; the exact forms
> are validated on their idealizations.

**Banked artifact:** the two-step profile — `erfc` predep → `Gaussian`-ish drive-in
on one depth axis, the junction depth marked where it crosses `N_B`, with `x_j` and
`R_s` reported. *Recipe in, junction out.*

### Phase 2 — Thermal oxidation (Deal–Grove): the second exact anchor

The **Deal–Grove** linear-parabolic model of oxide growth — `x_ox² + A·x_ox =
B(t+τ)` — with its **linear** (reaction-limited, thin-oxide, rate `B/A`) and
**parabolic** (diffusion-limited, thick-oxide, rate `B`) regimes. A small chip-local
module (an analytic/ODE solve, **not** the frozen PDE engine — Deal–Grove is its
own closed form). Grows oxide for **wet** and **dry** O₂.

**Validation triad — Phase 2**
- *Analytical limit.* The exact Deal–Grove `x_ox(t)` and its two limits:
  `x_ox ≈ (B/A)·t` (thin) and `x_ox ≈ √(Bt)` (thick). **Scope edge, named:** the
  **thin-dry-oxide anomaly** (the Massoud regime — Deal–Grove under-predicts the
  initial dry-oxide growth) is a *known* model failure; it is named as a limit so a
  benchmark there does not wound the exact leg.
- *Conservation.* **Silicon consumed = `0.44·x_ox`** (the Si→SiO₂ volume/number
  bookkeeping — growing oxide eats silicon at the fixed molar-volume ratio). A free
  mass-balance check on the moving boundary.
- *Benchmark.* The rate constants `B` (parabolic) and `B/A` (linear), **wet vs
  dry**, vs published Deal–Grove tables (Deal & Grove 1965 / Plummer–Deal–Griffin /
  Jaeger — **pinned to a cited source at build time**, the `[[carburize-diffusivity-source]]`
  pattern; *not* carried from memory).

**Deferred coupling, named:** oxidation redistributes dopant at the moving Si/SiO₂
interface (**segregation**) and **oxidation-enhanced diffusion (OED)** speeds the
underlying diffusion — the Phase-1↔Phase-2 *back-coupling*. v1 takes only the
**forward** direction (Phase 4 consumes a Phase-1 profile *and* a Phase-2 oxide);
the OED/segregation back-reaction is **out of v1**, a named deferral (the same plain-array
seam keeps it slottable later).

**Banked artifact:** oxide thickness vs time, **wet vs dry**, with the linear and
parabolic regimes annotated on the curve.

### Phase 3 — Lithography: the aerial image (the one genuinely-new module)

The pattern-transfer step, and the project's **risk phase** — so the tractability
gradient lives **inside the module**, not just in the §5 ceiling:

- **Coherent two-beam imaging** (a line/space at the resolution limit → a `cos²`
  intensity fringe) is the **exact anchor**, and where the **Rayleigh resolution**
  `R = k₁·λ/NA` lives (k₁ = 0.25 for the two-beam limit).
- **Abbe sum-over-source** (integrate the coherent image over points of a partially-
  coherent source of partial-coherence `σ`) is the **tractable workhorse** for real
  partial coherence — deliberately **not Hopkins TCCs** (the 4-D transmission-cross-
  coefficient formulation is the litho tar pit; named in §5).
- A **constant-threshold resist** model turns the aerial image into a printed
  critical dimension (CD).

**Validation triad — Phase 3**
- *Analytical limit.* The two-beam `cos²` aerial image and **Rayleigh `R = k₁λ/NA`**
  exact.
- *Conservation.* The **DC component of the aerial image = the zeroth diffraction
  order = total transmitted power** through the pupil (the Abbe sum preserves
  integrated intensity — a physical power-balance check, not merely a transform
  identity).
- *Benchmark.* **Image contrast / NILS (normalized image log-slope) vs pitch** vs
  the classic litho resolution curves; the `k₁` trend as NA/σ vary.

**Banked artifact:** an aerial image (intensity vs position) for a line/space near
the resolution limit, beside a **contrast-vs-pitch** curve showing where the pattern
stops resolving.

### Phase 4 — Process → device (the compact model): closing the loop

The payoff: chain the steps into a **device parameter**. A compact **MOS threshold
voltage** `V_t = V_FB + 2φ_F + √(2 ε_Si q N_A (2φ_F)) / C_ox`, with `C_ox =
ε_ox/t_ox` — where **`t_ox` comes from Phase 2**, the channel doping `N_A` from a
**Phase-1** profile, and the device geometry from a **Phase-3** litho-defined CD.
This is the analogue of Steel's structure→properties map (a compact closed form, the
*consequence* of the process, **not** a meshed device solve).

**Validation triad — Phase 4**
- *Analytical limit.* The textbook `V_t` closed form, and the **body-effect √-law**
  (`V_t` vs source-body bias `V_SB`, the `γ√(2φ_F+V_SB)` term) — exact.
- *Conservation.* **MOS charge neutrality / Gauss's law**: the gate charge balances
  the depletion + inversion charge (`Q_g = −(Q_dep + Q_inv)`).
- *Benchmark.* `V_t` vs process knobs (oxide thickness `t_ox`, channel doping
  `N_A`) vs textbook / SPICE-level values (Sze / Plummer — reference facts).

**Banked artifact:** the **whole forward flow on one figure** — oxidation → diffusion
→ litho-defined geometry → `V_t` — *the cheapest end-to-end process→device demo*, the
chip counterpart of Steel's four-curves anchor.

---

## 4. Module map & contracts

Small files, so any single task loads with its neighbours' *contracts*, not their
internals (ARCHITECTURE.md §6). Mirrors the `projects/steel/` layout.

```
BigSim/
  engines/diffusion/CONTRACT.md     # the FROZEN spine Chip consumes (load this, not steel/)
  chip/
    diffusion_dopant.py             # frozen-engine instantiation: predep(erfc)/drive-in(Gaussian);
                                     #   dopant Arrhenius D(T) for B/P/As                          (Phase 1)
    junction.py                     # profile → junction depth x_j + sheet resistance (Irvin)      (Phase 1)
    oxidation.py                    # Deal–Grove linear-parabolic oxide growth (wet/dry)           (Phase 2)
    litho.py                        # Fourier/Abbe aerial image + threshold resist → CD            (Phase 3)
    device.py                       # compact MOS V_t (process → device)                           (Phase 4)
    process.py                      # the recipe driver: chains oxidation→diffusion→litho→device
    plots.py                        # chip-local figures (→ promote to viz/ by rule-of-three)
    demo_junction.py / demo_oxidation.py / demo_litho.py / demo_process.py   # banked artifacts
    chip.ipynb                      # single teaching notebook (see §9) — BUILT: per-phase sliders → V_t
    README.md                       # per-module map + per-session load pointer
    tests/                          # the validation triads (the seal)
  pyproject.toml                    # testpaths += chip (§7)
```

**Contracts kept short.** Each module's docstring is its contract (the steel
convention). `diffusion_dopant.py` is the only module that loads
`engines/diffusion/CONTRACT.md`; the rest exchange **plain arrays** — a profile
`N(x)`, an oxide thickness `t_ox`, an aerial image `I(x)`, a device scalar — the
loose-coupling currency (§5 / ADR 0001).

---

## 5. Scope ceiling — consequence, not mechanism

**The named tar pit:** full **2-D / 3-D coupled TCAD** — Poisson + drift-diffusion
(+ thermal) on a device mesh — and **rigorous EMF / vector mask** lithography with
**Hopkins-TCC** partial coherence (ARCHITECTURE.md §8). These are research/compute
walls, not token problems.

**What we target instead — the consequence:** *1-D process profiles + aerial-image
litho + a compact device model.* A learner sees *"junction at 0.8 µm, R_s = 45 Ω/sq,
V_t = 0.7 V,"* and *why* (which recipe knob moved it) — not a meshed carrier-transport
field. The deep end here is **honest closed-form / 1-D process physics with exact
anchors** (Deal–Grove, erfc/Gaussian, Rayleigh, compact `V_t`) — rich, validated,
feasible — with TCAD/EMF left explicitly outside the line.

**Loose-coupling / extensibility hook (ARCHITECTURE.md §8 mandate):** modules exchange
plain arrays/scalars. That boundary is exactly where a future **2-D TCAD** module
could consume a 1-D profile as its initial condition, or a **rigorous-litho** module
replace the Abbe image — designed-for, not built. Nothing in v1 forecloses it.

---

## 6. Terms-of-use status

**The one place Chip differs from Steel** (which was "no export-control dimension").
Per ARCHITECTURE.md §9, **advanced chipmaking *has* an export-control dimension** —
but the **published-information / educational carve-out** covers a generic-parameter
teaching tool, and the line is *generic illustrative physics vs. specific real-system
recipes or targeting.*

- **This project sits firmly in the carve-out.** It implements **generic textbook
  physics** (Deal–Grove oxidation, `erfc`/Gaussian diffusion, Fourier-optics aerial
  imaging, the compact MOS `V_t`) from first principles, with **original code/prose**.
  It contains **no real-fab process recipes, no advanced-/leading-node specifics, no
  proprietary tool data, and no targeting** of any fielded system. (Not legal advice;
  the §9 carve-out is the settled program position.)
- **Copyright:** a non-issue (§9) — equations and physical facts are not
  copyrightable; no verbatim listings or figures are copied.
- **Datasets / reference facts:** the **published rate constants** (Deal–Grove `B`,
  `B/A`; dopant Arrhenius `D₀, Q_a`; Irvin sheet-resistance curves) are used as
  **reference facts for comparison**, each **pinned to a cited source at build time**
  (a `[[…-source]]` memory note per constant, the carburize pattern), not
  redistributed as datasets. **SUPREM** (the reference process simulator) is for
  **validation**, never copied.

---

## 7. Test runner

The **tiered gate** (ADR 0003): the routine commit gate is the whole-repo fast lane,
the full gate is exceptional.

```powershell
# from repo root
./run_tests.ps1 -m "not slow"   # routine commit gate (fast lane, ~8 s)
./run_tests.ps1                 # full gate — EXCEPTIONAL: a shared engines/ edit,
                                #   root-config, a release, or CI
```

`pyproject.toml`'s `testpaths` gains `chip` (it already carries `engines`
and `projects`); the existing `pythonpath = ["."]` lets chip tests import the frozen
engine as `engines.diffusion…` with no install step. Any new chip test that drives a
live external solver / kernel / subprocess gets the `slow` marker. Editing the frozen
`engines/diffusion` is the cross-cutting case that *triggers the full gate* — its
`tests/` seal must stay green (it is the contract Chip relies on).

> **On completion, build the per-project gate (committed — user direction, 2026-06-09).**
> Microchip is the trigger: once it lands, the interim whole-repo fast lane is replaced
> by a **per-project gate** — a commit to a project runs only the tests concerning that
> project (its own + the tests of the modules it uses), driven by a **single source of
> truth** (project → used engines/modules → test suites). Microchip is the first point
> that manifest has a second, distinct entry to validate against. Design it then; see
> ADR 0003 → *Successor* (also still-open there: the `slow` set for chip's heavy tests,
> and whether the full-gate rot-catcher is CI).

---

## 8. Invariant-compliance check (against ARCHITECTURE.md §2–9 — not re-litigated)

| Program invariant | How this plan honors it |
|---|---|
| 1 — build toolkit once, solver-heavy first | Builds **no** new shared engine; reuses the frozen diffusion spine. The one new module (Fourier optics) stays chip-local until rule-of-three. |
| 2 — phase so each stage banks a working artifact | Four phases, each an explicit banked artifact (junction, oxide curve, aerial image, the process→device flow). |
| 3 — validation triad from day one | Instantiated *concretely per phase* in §3 (analytic + conservation + benchmark), each with its non-circularity split + scope edge. |
| 4 — target consequence where mechanism is a wall | §5: 1-D profiles + aerial-image litho + compact device, instead of 2-D/3-D TCAD + rigorous EMF litho. |
| 5 — reuse only frozen modules | Consumes `engines/diffusion/CONTRACT.md` (sealed in Steel 1a); any new engine behaviour is a deliberate v1.1 contract amendment, not an internal reach. |
| 6 — updating docs is part of every change | This plan + per-module README + `docs/decisions/` are maintained per change; ARCHITECTURE.md §11 pointer updated as Chip progresses. |
| Terms of use (§9) | §6: the **export-control carve-out** is explicitly invoked (the one difference from Steel) — generic physics, no recipes/targeting; reference constants cited, not redistributed. |

---

## 9. Visualization & UX

Per ARCHITECTURE.md §12 / ADR 0002: compute stays headless; views consume the
engine's plain arrays; a figure is never in the correctness path.

- **Floor (universal):** the §3 banked figures — the junction profile, the Deal–Grove
  curve, the aerial image, the process→device flow — as **static matplotlib figures**
  (the opt-in `[viz]` extra), testable against numeric output.
- **Mechanism views** (the "teach *why*" target, ADR 0002 §5): the **`erfc` → Gaussian
  profile morph** as predep gives way to drive-in (why the junction moves), and the
  **aerial image assembling from its diffraction orders** (why a pitch stops
  resolving) — not bare readouts.
- **Experimentation — deliberately lean (the ADR-0002 "both consistency guard").**
  **Chip is *not* the flagship.** Steel, as the flagship, shipped **both** a teaching
  notebook **and** a Streamlit app as the demonstrator; ADR 0002 is explicit that
  *later sims pick the interactive surface their pedagogy needs, not both by reflex.*
  So Chip ships the **static-figure floor plus a *single* teaching notebook**
  (`chip.ipynb` — **BUILT 2026-06-09**: process-recipe sliders → profile/junction,
  oxide, aerial image, and `V_t`, one section per phase, ending on the process→device
  flow), and **builds no Streamlit app** unless a specific payoff later demands it.
  *(Stated explicitly so a future session does not reflexively rebuild Steel's dual
  surface here.)* The notebook is a *thin skin* (the steel pattern): each compute cell
  calls the validated module directly, `interact` is sugar, and a `slow` headless
  smoke-test (`tests/test_chip_notebook.py`) asserts it executes clean.
- **Toolkit:** plot primitives start chip-local in `plots.py`; promotion to the shared
  `viz/` is by rule-of-three (ARCHITECTURE.md §6). Steel's `plots.py` is the second
  data point — a third reuse (chip) of a primitive (e.g. the profile-vs-depth line, the
  sweep-comparison grid) is exactly what would trigger promotion.

Responsiveness is free: chip compute is sub-second (1-D), so slider → re-run → re-plot
needs no special engineering (ADR 0001 scope).

---

## 10. Immediate next step

**Plan banked (this document).** The build order (ARCHITECTURE.md §4) now advances
from a 100 %-complete Steel to Chip.

> **Phase 1a — BUILT (2026-06-09).** `chip/` created: `diffusion_dopant.py`
> (predep `erfc` Dirichlet / drive-in Gaussian Neumann(0), cited Fair `D(T)` for B/P, in
> **CGS-semiconductor units** — the advisor-confirmed departure from Steel's SI, since the
> engine is unit-agnostic and the cited data is native cm/cm²·s⁻¹/cm⁻³), `junction.py`
> (junction depth + **Masetti `μ(N)`** sheet-resistance conductance integral, Irvin
> cross-check), `plots.py` + `demo_junction.py` (the banked two-step boron pn-junction:
> `x_j` ≈ 1.05 µm, `R_s` ≈ 134 Ω/sq into a 1e15 n-type wafer → `docs/figures/chip-junction.png`).
> Triad sealed by 28 tests (whole-repo fast gate **268 green**): the exact `erfc`/`Gaussian`
> anchors on their idealizations (constant-D), dose conservation + the predep flux identity, and
> a **deep-tail (z≈3) numeric-vs-analytic `x_j` certification** that licenses the realistic demo's
> numeric junction. Masetti coefficients pinned online (IUE-Vienna + allpix²/CERN). **Next = Phase 2
> (Deal–Grove oxidation).**

> **Phase 2 — BUILT (2026-06-09).** `chip/oxidation.py` — the Deal–Grove linear-parabolic
> closed form `x_ox² + A·x_ox = B(t+τ)` for **wet** and **dry** oxidation, the **first chip module
> that does not touch the frozen engine** (oxide growth is its own closed form; a chip-local
> analytic/ODE module per §2/§3). With `demo_oxidation.py` + `plots.oxidation_figure` (the banked
> artifact: oxide-thickness-vs-time wet-vs-dry log-log, riding the **linear `(B/A)·t`** asymptote
> when thin and bending onto the **parabolic `√(Bt)`** when thick, beside a growth-rate mechanism
> panel → `docs/figures/chip-oxidation.png`; (100) 1100 °C/1 h → **dry ≈ 0.099 µm / wet ≈ 0.642 µm,
> wet ~6.5× faster**). **23-test triad** sealed; whole-repo fast gate **291 green** (+23). Triad:
> *analytic* = the algebraic identity `x²+Ax−B(t+τ)=0` to machine precision + the linear/parabolic
> asymptotes + an independent **ODE** integration of `dx/dt=B/(A+2x)` recovering the closed form
> (<1e-6) + the τ machinery recovering an initial oxide exactly; *conservation* = silicon consumed
> `0.44·x_ox` with the moving-boundary `0.44`-below / `0.56`-above bookkeeping closing exactly;
> *benchmark* = the cited rate constants pinned exactly + the wet≫dry thickness band. Durable calls:
> **units = Deal–Grove-native µm-hour** (the per-module native-units principle — Fair `D₀` was native
> cm²/s→CGS, `B/A` is native µm/hr→µm-hr; µm the cross-module currency; the README's "one system
> throughout" prose reworded so docs don't self-contradict), constants pinned online to a cited
> source (`[[deal-grove-oxidation-source]]` — IUE-Vienna → Plummer–Deal–Griffin / Deal & Grove 1965;
> **wet `Ea_B = 0.78 eV` table value**, not the 0.71 in prose summaries; **1.68 orientation factor on
> the linear `B/A` only**, default (100); Si `0.44`), and the **thin-dry (Massoud) anomaly named not
> modeled** (v1 is plain Deal–Grove — the honest ceiling). The OED/segregation back-coupling stays
> the named §3 deferral (forward-only). **Next = Phase 3 (lithography aerial image).**

> **Phase 3 — BUILT (2026-06-09).** `chip/litho.py` — the **lithography aerial image**, the
> chip project's **one genuinely-new module** (Fourier optics) and its risk phase; **chip-local, not
> promoted to `engines/`** (rule-of-three), and like Phase 2 it **does not touch the frozen PDE engine**
> (it is its own diffraction computation). One core primitive `coherent_image` (= `|Σ_m a_m·e^{2πi f_m x}|²`)
> used twice: the exact **two-beam anchor** `two_beam_image` (two equal orders → `4·cos²(πx/p)` to machine
> precision) and the **Abbe sum-over-source** workhorse `abbe_image` (partial coherence by incoherent
> source-point summation — **deliberately not Hopkins TCC**, the named tar pit). With `demo_litho.py` +
> `plots.litho_figure` (the banked artifact: the aerial image **assembling from its diffraction orders**
> beside the **contrast-vs-pitch** resolution curve → `docs/figures/chip-litho.png`; 193 nm ArF, NA 0.85,
> σ 0.5 → contrast/NILS/CD fall toward the cutoff, the image goes flat below the σ-source pitch limit
> ~151 nm). **25-test triad** sealed; whole-repo fast gate **316 green** (+25). Triad: *analytic* = the
> exact `4cos²` (pure trig) + **Rayleigh `R=k₁λ/NA` derived from the pupil cutoff** (k₁=0.5 coherent on-axis
> where ±1 just fit `1/p ≤ NA/λ`; k₁=0.25 two-beam where the off-axis pole spans the full pupil `1/p ≤
> 2NA/λ` and **exactly {0,+1} pass → cos² emerges from the workhorse itself**); *conservation* = the
> **Parseval power balance** — the image's DC (spatial mean) = total power passed by the pupil `Σ|c_m|²`,
> computed two independent ways (a squared sum vs a sum of squares) to machine precision; *benchmark* =
> contrast/NILS-vs-pitch trend vs the cited curves (loose). Durable calls: **units = litho-native nm**
> (per-module native-units principle; CD exposed in µm at the boundary), constants pinned online
> (`[[litho-aerial-image-source]]` — Mack / lithoguru: **k₁=0.25 two-beam floor / 0.5 coherent / ≈0.28
> best**, **NILS≥1 minimally resolved / ≳2 robust**), the **explicit-source-array API** (a σ-disk can't
> express extreme off-axis, so k₁=0.25 needs the off-axis point handed in — advisor call), the
> **exact-cos²-vs-realistic-grating split** kept (a real 50%-duty grating has `c₀=0.5≠c₁=1/π` → visibility
> 0.906 < the ideal cos²'s 1.0 — *not* asserted against the exact form, the Phase 1a discipline), **NILS at
> the geometric design edge** (threshold-free), and the **scope edge named not modeled**: scalar (no
> vector/polarization — honest at low/moderate NA), **ideal in-focus aberration-free pupil** (no defocus/
> Zernikes), Abbe-not-Hopkins, constant-threshold resist (no acid diffusion/PEB blur), 1-D line/space, and
> a 1-D uniform source line (not the chord-weighted 2-D-disk projection). **Next = Phase 4 (compact MOS Vt
> — the process→device payoff, consuming a Phase-1 profile + a Phase-2 oxide + a Phase-3 CD).**

> **Phase 4 — compact MOS V_t (process → device): BUILT (2026-06-09).** `chip/device.py` — the
> **payoff** phase that closes the loop: a chip-local **compact closed form** ``V_t = V_FB + 2·φ_F +
> Q_dep/C_ox`` (like Phase 2, it does **not** touch the frozen engine — it is its own algebra) consuming
> the three upstream process outputs as **one coherent n-MOSFET**: the channel ``N_A`` (a Phase-1 p-type
> substrate), the gate ``t_ox`` (a Phase-2 *thin dry* oxide — the gate-oxide regime, **not** the banked
> field oxide), and the gate CD (a Phase-3 litho feature → channel length ``L``). With `demo_device.py` +
> `plots.device_figure` (the banked artifact: the **whole forward flow on one figure** — diffusion →
> oxidation → litho → the ``V_t`` *waterfall* → `docs/figures/chip-device.png`; channel ``N_A``=1e17,
> dry-O₂ 1000 °C/20 min → 14 nm gate oxide, 193 nm-ArF litho → 167 nm gate, shallow n⁺ S/D
> (``x_j`` ≈ 0.10 µm < the gate length → a coherent cross-section, not punchthrough) → **``V_t`` ≈ 0.55 V**,
> ``I_Dsat`` ≈ 3.3 mA). **20-test triad** sealed (15 device + 5 demo-integration); whole-repo fast gate
> **336 green** (+20). Triad:
> *analytic* = an **INDEPENDENT depletion-Poisson integration** — ``solve_ivp`` on ``ψ″=q·N_A/ε_Si`` +
> ``brentq`` root-find of the depletion width where ``ψ_s=2φ_F``, recovering ``Q_dep=√(2qε_Si N_A·2φ_F)``
> to ~1e-9 (the **Phase-2 solve_ivp analogue** — *not* the body-effect √-law, which is the same formula
> rearranged and kept only as a cheap γ-consistency check; the advisor's blocking correction);
> *conservation* = MOS **charge neutrality / Gauss** — ``Q_g = −(Q_dep+Q_inv)`` closes to machine
> precision, ``Q_inv=−C_ox(V_GB−V_t)`` above threshold, ``E_ox=Q_g/ε_ox``; *benchmark* = the cited
> **MIT 6.012 PS3 P2** worked example (n⁺-poly / p-1e17 / 15 nm → ``V_FB``=−0.97 V, ``C_ox``=2.3e-7,
> ``V_t``≈0.58 V; parts b,c = the conservation cross-check) + the ``V_t``-vs-(``N_A``,``t_ox``) trends.
> Durable calls: **units = semiconductor CGS-cm** (as Phase 1a — ε in F/cm, charge C/cm²; ``t_ox`` µm→cm
> and CD µm at the boundary), constants pinned online (`[[mos-threshold-voltage-source]]` — Wikipedia /
> Chenming Hu Ch.5 / MIT 6.012; **n_i=1.0e10** the MIT-reproducing pin, 1.45e10 named as +~10 mV),
> **CD = geometry-only** (sets ``L`` and the honest long-channel ``I_Dsat``∝W/L, **does not** enter the
> long-channel ``V_t`` — short-channel rolloff is the 2-D charge-sharing/DIBL tar pit, the named §5 scope
> ceiling; the advisor's other blocking call — coupling CD into ``V_t`` would destroy the exact anchor),
> **one coherent device** (not three unrelated numbers — the banked field oxide / 1e15 n-wafer would
> blow up ``C_ox`` / mismatch the channel type), ideal-oxide/uniform-channel/degenerate-poly-gate scope
> edge named. **MICROCHIP COMPLETE (all 4 phases). NEXT = build the committed manifest-backed per-project
> gate (ADR 0003 successor — the §7 user direction, now that Microchip provides a 2nd manifest entry).**

> **v1.1 — the Massoud thin-dry correction: BUILT (2026-06-10).** Phase 2's **named scope edge,
> promoted** (the steel-ferrite-bay move: yesterday's honest ceiling becomes today's phase) —
> `oxidation.py` §5, chip-local, the frozen engine untouched, the **plain path bit-for-bit unchanged**
> (`grow_oxide` never applies the enhancement; `K=0` degenerate recovery pinned). The cited model is
> Massoud's **time-decay formulation** ``dx/dt = (B + K₁e^(−t/τ₁) + K₂e^(−t/τ₂))/(A+2x)`` — chosen
> over the sibling thickness-decay form (`+Cᵢe^(−x/Lᵢ)`, L₁≈1 nm/L₂≈7 nm) because it **integrates in
> closed form**: ``x²+Ax = Bt + ΣKᵢτᵢ(1−e^(−t/τᵢ)) + (xᵢ²+Axᵢ)`` — so v1.1 keeps the module's
> exact-anchor discipline (machine-precision identity + independent `solve_ivp` cross-check) instead of
> going numeric-only. Constants pinned at build (the massoud-thin-oxide source pin): Massoud & Plummer,
> *J. Appl. Phys.* **62**(8):3416–3423 (1987) + Massoud/Plummer/Irene, *JECS* **132**(7):1746 & (11):2685
> (1985), as compiled in **Hollauer, TU Wien diss. (2007) §2.7 Tables 2.3/2.4** — dry O₂ only,
> **800–1000 °C, (100)/(111)/(110)**, and the module **refuses** outside the cited fit
> (refuse-don't-extrapolate; the Massoud `B`,`B/A` Arrhenius is a two-piece fit split at 1000 °C).
> Durable source calls: **the coherent-set rule** (the `Kᵢ`/`τᵢ` ride Massoud's *own refit* `B`,`B/A` —
> Table 2.3's, ≠ the 1965 table — never spliced onto the v1 constants; thick-regime disagreement between
> the two fits is honest, not a bug) and **the τ sign-typo finding** (Hollauer's eqs (2.39)–(2.40) print
> `τᵢ = τᵢ⁰·exp(−E/kT)`, which with `τ⁰~1e-7 min` gives femtosecond decays; the **positive** exponent
> gives τ₁≈1.2/τ₂≈7.5 min at 1000 °C and reproduces the dissertation's **own Fig. 2.19** ≈25 nm @
> 1000 °C/20 min — the consistency check that disambiguated the typo; also Table 2.4's 8th row label
> "τ₁⁰" is a second typo for τ₂⁰). Banked artifact (`demo_thin_oxide.py` →
> `docs/figures/chip-thin-oxide.png`): the **gate-oxide before/after** — the Phase-4 recipe (dry
> 1000 °C/20 min, (100)) grows **14.1 nm (v1 plain Deal–Grove) vs 23.3 nm (Massoud, ×1.65)**, and the
> Phase-4 readout moves **V_t 0.547 → 0.991 V (ΔV_t = +0.44 V)** — *the thin-dry anomaly was a V_t-sized
> error in the process→device chain, not an oxidation footnote* (the demo's payoff line). **16-test
> mini-triad** sealed (11 module + 5 demo): *analytic* = the integrated quadratic identity to 1e-12 +
> ODE recovery <1e-6 + `K=0`→Deal–Grove + the saturation theorem (the burst is worth exactly `M₁+M₂` of
> `x²+Ax`, then pure linear-parabolic — the ~25 nm ceiling in time form); *conservation* = the 0.44
> moving-boundary bookkeeping is growth-law-independent and closes exactly; *benchmark* = all three
> orientations' table pins + hand-checked evaluated magnitudes + Hollauer's own growth curve. Scope
> edges named: time-decay ties the burst to *onset* (thin/native seeds only for `x_initial`), wet has
> no anomaly, T>1000 °C Massoud constants exist but are out (no enhancement there). Units: the §5 block
> computes in the tables' native **nm-min** (the per-cited-*dataset* sharpening of the per-module
> native-units rule), µm at the boundary. SHARED-FILE ASKS: the `massoud-thin-oxide-source` memory note
> (this addendum carries the full pin meanwhile).

> **v1.2 — the Phase 1↔2 back-coupling (OED + dopant segregation): BUILT (2026-06-10).** The named §3
> deferral of *both* Phase 1 (the `D(N)`-adjacent back-reaction) and Phase 2 (the OED/segregation
> coupling), **promoted** (the steel-ferrite-bay / Massoud move). `chip/coupling.py`, chip-local,
> consuming a `diffusion_dopant` profile + an `oxidation` rate. **The decisive architecture finding: both
> effects are expressible *within the frozen engine* — no contract amendment.** *OED* (oxidation-enhanced
> diffusion) is a **position/time-dependent `D(x,t)`** (it tracks the oxidation rate + depth, **not** the
> concentration `N`), so it is the engine's *already-frozen variable-`D(t)` callable* case
> (`test_variable_d`) — pointedly **not** the unbuilt nonlinear `D(N)` case (that one *would* need a v1.1
> amendment; it stays the named `diffusion_dopant` scope edge). *Segregation* is a time-dependent
> `Neumann(flux(t))` surface BC. Model: `D_eff/D_inert = 1 + f_I·Δ`, supersaturation `Δ = Δ_ref·(dx_ox/dt /
> R_ref)^0.5` (the cited half-power law), cited `f_I` (B 0.30 / P 0.38 / Sb 0.015 — the dual I/V
> quantification paper) reproducing **enhanced (B, P) vs un-enhanced (Sb)**; segregation flux `J =
> N_surf·(0.44 − 1/m)·(dx_ox/dt)`, cited `m = solubility_Si/solubility_SiO₂` (B 0.3 / P 10 — **Hollauer §4.1
> Table 4.1, the SAME dissertation as the Massoud pin**) giving **boron depletion / phosphorus pile-up**.
> With `demo_coupling.py` + `plots.coupling_figure` (the banked artifact: boron depletion beside phosphorus
> pile-up, each decomposing inert → +OED [deeper, ×~2 effective `∫D dt`] → +segregation → `docs/figures/
> chip-oed-segregation.png`). **19-test triad** sealed; chip gate **152 green** (+19). Triad:
> *analytic* = the **unified degenerate seam** (`dx_ox/dt=0` collapses both effects → plain `drive_in`
> bit-for-bit) + the **OED ≡ effective-`∫D dt`** leg (the frozen variable-`D` τ-substitution: a warm-started
> Gaussian under OED matches the analytic Gaussian at age `a₀+∫D_eff dt`); *conservation* = OED-alone-sealed
> dose machine-exact (a real check) + the coupled `Si+oxide` identity (an **accounting** identity, not a
> magnitude check); *benchmark* = cited `f_I` (enhanced ordering P>B; Sb un-enhanced) + cited `m`
> (depletion/pile-up directions). Durable advisor calls: **(1)** the degenerate anchor is `dx_ox/dt→0`, **not**
> `m→∞` (the advisor's first correction — `m→∞` = oxide accepts nothing = *maximum pile-up*, not sealed; the
> wrong anchor was dropped). **(2) The named scope edge — the swept-sliver double-count** (the advisor's
> blocking call): the segregation flux is a **moving-*interface* mass balance run on a *non-moving* grid**, so
> the `0.44·R` recession term ("dopant freed by consumed silicon") is **counted twice** (the swept region is
> kept in the domain *and* its dopant re-injected at the surface). Pinned by the **`m→∞` inert-oxide
> diagnostic** (an inert oxide must conserve silicon dopant; the model spuriously *gains* ~10% of the dose).
> Consequence owned in code+tests+figure: **boron depletion is robust** (oxide-uptake-dominated, `1/m=3.3`
> vs the `0.44` double-count ≈13% — the device-relevant case), **phosphorus pile-up direction is real but
> magnitude ~2× inflated**; the coupled "conservation" reframed as an accounting identity (tautological —
> closes for any flux). The real fix (advance the interface / remap the ~1-cell swept region) is a
> Stefan-problem treatment the pure-diffusion engine can't express — named, not silently carried. **(3)**
> Sb stays a *qualitative* ORD scope edge (`f_I`=0.015 → factor ≈1.05 = a small *wrong-sign* residual, **not**
> a retardation number — true ORD needs the unmodeled vacancy-undersaturation term). The OED amplitude is
> **calibrated (flagged)**; the tight legs (degenerate, effective-`∫D dt`, OED conservation) hold for any
> amplitude. Units: semiconductor CGS-cm (the diffusion side), the oxidation rate consumed at the boundary
> (unit-free ratio for `Δ`, cm/s for the flux). SHARED-FILE ASKS: the `oed-source`, `dopant-segregation-source`,
> and (finally) `massoud-thin-oxide-source` memory notes.

**Phase 1a — dopant diffusion & the pn junction.** Instantiate the **frozen
`engines/diffusion`** in mass mode (`diffusion_dopant.py`): a constant-source
**predeposition** (Dirichlet `N_s`) → `erfc`, and a sealed-surface **drive-in**
(Neumann(0)) → Gaussian, with a **cited** B/P/As Arrhenius `D(T)` (pinned to a
source at build). Then `junction.py` (junction depth + Irvin sheet resistance) and
the banked **pn-junction demo**. Validation triad: the exact `erfc`/Gaussian anchors
(constant-D regime; `D(N)` named as the scope edge), the drive-in **dose
conservation** (the engine's own no-flux guarantee) + the predep flux-bookkeeping
identity, and the **junction-depth / sheet-resistance benchmark** vs Irvin/SUPREM.
This is **low-risk spine reuse** — `projects/steel/carburize.py` already exercised the
identical mass-mode instantiation — so it is a fast validated win that proves the
program's core thesis: the spine reuses.

**Phase 1a reference sources — pinned at build (gathered 2026-06-09).** Per the
program discipline (cited reference facts, not carried from memory — the
`[[…-source]]` memory-note pattern), the three Phase-1a constants are pinned:

- **Dopant Arrhenius `D(T) = D0·exp(−Ea/kT)`** — `[[dopant-diffusivity-source]]`.
  **Fair (1981)** intrinsic model, reproduced in **Plummer–Deal–Griffin** (same text
  Phase 2's Deal–Grove constants cite — one coherent lineage). **B: 0.76 cm²/s,
  3.46 eV; P: 3.85 cm²/s, 3.66 eV** (both confirmed; they cover the pn-junction
  demo); Sb 0.214/3.65; As is the widest-spread case (pin at build, the
  multi-mechanism scope-edge example). Units: **eV + cm²/s**, convert to engine m²/s
  at the boundary. erfc/Gaussian forms + the predep dose identity
  `Q = (2/√π)·C_s·√(Dt) ≈ 1.13·C_s·√(Dt)` are from a directly-read teaching chapter
  (CityU AP6120 Ch. 8).
- **Predep surface concentration `N_s` (solid-solubility limit)** —
  `[[dopant-solid-solubility-source]]`. **Trumbore (1960), BSTJ 39:205–233** (B
  retrograde ~5×10²⁰ peak; P ~1.2–1.3×10²¹; As ~1.5–2×10²¹).
- **Sheet-resistance benchmark `R_s·x_j`** — `[[irvin-sheet-resistance-source]]`.
  **Irvin (1962), BSTJ 41:387–410.** *Graphical, not callable:* the benchmark **cites**
  Irvin's `R_s·x_j` chart; `junction.py` **computes** `R_s = 1/∫q·μ(N)·N dx`.
- **Mobility model `μ(N)` (the R_s integrand)** — `[[dopant-mobility-source]]`.
  **Masetti, Severi & Solmi (1983), IEEE TED 30(7):764–769** — per-dopant As/P/B over
  the high-doping range (the predep solubility regime), kept **independent** of Irvin so
  the R_s cross-check stays non-circular.

**The named scope edge, sharpened by these sources.** Predep runs *at* the
solid-solubility limit = high concentration = exactly where the frozen engine's
**constant-D** erfc is weakest (real `D(N)` is concentration-enhanced — the P
kink-and-tail; the engine's flagged-unbuilt v1.1 case). So the constant-D-vs-`D(N)`
edge (carburize's Tibbetts analogue) **bites the predep leg specifically harder** than
it did for carburizing — the exact erfc/Gaussian legs are validated on their
*idealizations*, and the realistic predep→drive-in demo's job is the *junction*.
