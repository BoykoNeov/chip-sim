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
(`projects/chip/litho.py`), **not** promoted to `engines/`: only chip uses it, so
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
  projects/chip/
    diffusion_dopant.py             # frozen-engine instantiation: predep(erfc)/drive-in(Gaussian);
                                     #   dopant Arrhenius D(T) for B/P/As                          (Phase 1)
    junction.py                     # profile → junction depth x_j + sheet resistance (Irvin)      (Phase 1)
    oxidation.py                    # Deal–Grove linear-parabolic oxide growth (wet/dry)           (Phase 2)
    litho.py                        # Fourier/Abbe aerial image + threshold resist → CD            (Phase 3)
    device.py                       # compact MOS V_t (process → device)                           (Phase 4)
    process.py                      # the recipe driver: chains oxidation→diffusion→litho→device
    plots.py                        # chip-local figures (→ promote to viz/ by rule-of-three)
    demo_junction.py / demo_oxidation.py / demo_litho.py / demo_process.py   # banked artifacts
    chip.ipynb                      # OPTIONAL single teaching notebook (see §9) — only if it earns it
    README.md                       # per-module map + per-session load pointer
    tests/                          # the validation triads (the seal)
  pyproject.toml                    # testpaths += projects/chip (§7)
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

Single command, fast, runs the whole suite (engines + steel + chip) so any session
verifies cheaply (ARCHITECTURE.md §6):

```powershell
# from repo root
./run_tests.ps1          # wraps:  pytest -q
```

`pyproject.toml`'s `testpaths` gains `projects/chip` (it already carries `engines`
and `projects`); the existing `pythonpath = ["."]` lets chip tests import the frozen
engine as `engines.diffusion…` with no install step. The frozen
`engines/diffusion/tests/` seal must stay green for any chip change (it is the
contract Chip relies on).

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
  So Chip defaults to the **static-figure floor plus *at most one* teaching notebook**
  (`chip.ipynb`: process-recipe sliders → profile/junction/`V_t`), and **builds no
  Streamlit app** unless a specific payoff later demands it. *(Stated explicitly so a
  future session does not reflexively rebuild Steel's dual surface here.)*
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
