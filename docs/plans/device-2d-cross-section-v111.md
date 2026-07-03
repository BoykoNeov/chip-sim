# Plan — v1.11: the 2-D MOSFET cross-section (lateral S/D diffusion → effective channel length)

## Context

The project is feature-complete against its plan, so this is a **deepening** in the
established discipline (promote a named edge that has a named consumer). Two built capabilities
sit next to each other but were never composed:

* **v1.8** (`chip/diffusion_2d.py`) computes the 2-D dopant field of a masked constant-source
  diffusion — dopant curving *down and laterally under a mask edge* — but only demos it in
  isolation (lateral/vertical ratio).
* **Phase 4** (`chip/device.py`) reads a MOS `V_t` and a long-channel `I_Dsat` off scalar
  process outputs, with the litho CD as a **geometry-only** channel length `L` (it deliberately
  does **not** enter `V_t` — short-channel rolloff/DIBL is the named §5 tar pit).

The composition is exactly how a real self-aligned MOSFET is built: **the gate is the mask** for
the S/D diffusion, so the S/D dopant diffuses *under the gate edges*, and the lateral encroachment
`ΔL` shrinks the channel to an **effective** length `L_eff = L_drawn − 2·ΔL`. That `L_eff` is the
honest place 2-D geometry moves a device number: it feeds the **drive current** (`I_Dsat ∝ W/L`),
while `V_t` stays long-channel. This hits the project's "process → device" thesis using
built-but-underused capability, and stays out of the tar pit by construction.

**Hard boundary (the advisor's constraint):** this shows honest 2-D *geometry* driving the channel
length and the current. It must **NOT** claim short-channel `V_t` / DIBL — the device model under
the gate stays 1-D/long-channel. That boundary is turned into an asserted test (below).

## Approach

A new chip-local module composes the two validated pieces; no engine change, no new physical
constant beyond a cited geometry fact.

> **Revised after the advisor's pre-build review (the upgrade).** The two "conservation" legs
> I first proposed (`V_t` invariant to `L`, `I_Dsat ∝ 1/L`) are **by-construction** — `device.py`
> never puts `L` into `V_t`, and `I_Dsat` is literally `∝W/L`, so they can't fail unless someone
> edits `device.py`. By this repo's own standard (device.py's Gauss leg = "a self-consistency
> check… the genuinely-independent verification is the Poisson anchor"; v1.2/v1.3's "tautological"
> reframes) they are **regression guards, not anchors** — billed as such. The independent anchor is
> the **two-window solve** below, which also yields the module's own new scope edge.

### New module — `chip/device_2d.py` (parallels `diffusion_2d.py`)

Two ways to get the effective channel length — the cheap textbook approximation and the honest
direct solve — with the second cross-checking (and bounding the validity of) the first:

* **The cheap approximation (textbook):** the single *isolated* gate edge via the **existing**
  `diffusion_2d.lateral_diffusion` (gate edge = mask edge) + `junction_geometry(profile,
  N_B=channel_N_A)` → lateral reach `ΔL` → `L_eff_approx = L_drawn − 2·ΔL`. This is the cited
  `L_eff = L_drawn − 2·L_{D,lateral}` relation.
* **The honest direct solve (the anchor + the new physics):** a **two-window half-cell** — gate
  centre at `x=0` as a no-flux symmetry plane, the S/D window *outside* (`window = x ≥ L_drawn/2`,
  sealed under the gate near centre) — is exactly the right half of the symmetric two-S/D device.
  Read the n⁺/p **surface** junction `x_j` directly → `L_eff_true = 2·x_j` (never via the
  subtraction). New solve config; the 2-D engine already does masked surfaces (one boolean flip of
  v1.8's `window`).
* **`mosfet_cross_section(..., lateral=True)`** — builds the device with the **existing**
  `device.threshold_voltage(N_A, t_ox, gate, channel_length_um=L_eff_true)` and
  `device.saturation_current(...)`; also computes `I_Dsat` at `L_drawn` (what the shortening buys).
  **Exact seam knob `lateral=False`** → `ΔL=0`, `L_eff=L_drawn`, recovers Phase 4 **bit-for-bit**.
* `MOSFET2D` frozen dataclass — the 2-D field, the S/D junction geometry, `L_drawn`, `delta_L`
  (single-edge), `L_eff_approx`, `L_eff_true`, the `MOSDevice`, `I_Dsat` at `L_eff` vs `L_drawn`.
  Plain arrays/scalars (ADR 0002).
* **Punchthrough:** when the two lateral fronts merge, `L_eff_true → 0` *before* the subtraction
  predicts (the fronts pile up under the no-flux gate). The module **refuses** at `L_eff_true ≤ 0`
  (the v1.7 "refuse, don't mis-handle" pattern) — but now it is the *direct solve* that detects it,
  grounded physics, not just `2·ΔL ≥ L_drawn` arithmetic.

### Demo recipe — a coherent **longer-channel** node where long-channel `V_t` is honestly valid

A self-consistent ~0.5 µm-node n-MOSFET (deeper S/D `x_j`, ~10–12 nm gate oxide, channel `N_A`
matched to the node — **not** the 180 nm-node shallow S/D bolted onto a long gate), so `L_eff` is
comfortably > 0 and the shortening is clean. We demo in the regime where long-channel `V_t` is
correct (reinforcing the honesty). The figure **sweeps `L_drawn`** from long-channel down toward
punchthrough at **fixed S/D process**, showing `L_eff_true` and `L_eff_approx` overlapping at wide
gates and **diverging** as `L_drawn → 2·ΔL` (the named scope edge), with `V_t` flat across the whole
sweep (the boundary). (S/D lateral step = v1.8 constant-source masked diffusion; the
constant-source-vs-two-step idealization is a minor named edge.)

### Validation triad (the v1.11 module tests)

**This is a *validation* deepening, not new-physics** (the advisor's reconcile, on the data): the
independent two-window solve **confirms** the textbook subtraction across the open range *and* the
punchthrough threshold; the front-interaction effect that would split them near the knee is below the
resolved scale (checked, not found — not asserted).

* **Analytic (tight) — a Phase-4 seam + the independent cross-check.**
  (a) **Exact `lateral=False` seam:** `L_eff=L_drawn` and the assembled `MOSDevice` equals
  `device.threshold_voltage(..., channel_length_um=L_drawn)` **bit-for-bit** (the σ=0/z=0/K=0
  pattern; anchors the composition to Phase 4).
  (b) **Two-window ≡ subtraction, persisting toward the knee:** `L_eff_true` (direct solve) matches
  `L_drawn − 2·ΔL` (isolated-edge) to ~grid precision (~few %) **across the open range, asserted down
  toward punchthrough** — not just at a wide gate (where it agrees almost by construction). A genuine
  cross-check: *different BC topology* (two windows + symmetry plane vs one semi-infinite edge), so it
  fails on a config/topology bug or if superposition broke; inherits v1.8's erfc-window-column anchor on `ΔL`.
* **Conservation (regression guards — by-construction, billed honestly).** `V_t(L)` constant and
  `I_Dsat(L_eff)/I_Dsat(L_drawn) = L_drawn/L_eff` — kept as guards that the boundary stays clean
  (no `L` in `V_t`; the only `L` coupling is geometric `W/L`), **not** as anchors (they hold by
  construction, the device.py self-consistency-leg framing).
* **Benchmark (loose) — the cited lateral ratio drives a named device effect + the punchthrough limit.**
  The v1.8 cited lateral/vertical ≈ 0.75–0.85 ([[lateral-diffusion-source]]) shortens the drawn gate
  by `2·ΔL` (a quantified %; `L_eff = L_drawn − 2·L_{D,lateral}` pinned to a cited device text —
  Sze / Plummer / Taur–Ning), and the channel **punches through at `L_drawn ≈ 2·ΔL`** — the
  two-window solve confirming the threshold. Loose: inherits v1.8's ~5–10%-high ratio.

### Named scope edges (the honest ceiling — the whole point)

* **No short-channel `V_t` rolloff / DIBL.** `V_t` stays long-channel; 2-D geometry moves the
  *channel length* and the *current*, never the *threshold*. The §5 / Phase-4 DIBL tar pit stays
  out, guarded by the `V_t`-invariance regression test.
* **The isolated-edge / superposition approximation.** `L_drawn − 2·ΔL` is exact only where the two
  S/D fronts don't interact; the front-pile-up that would correct it near the knee is **below the
  resolved scale here** (checked) — named as the honest ceiling, not a featured number. The direct
  two-window solve is what *grounds* the punchthrough as a real concentration crossing.
* **Punchthrough refused** — `L_eff_true ≤ 0` raises (a hard physical floor, vs the subtraction's
  `max`-clamp on a negative; the two agree on the `≈ 2·ΔL` threshold).
* **Constant-D S/D** (v1.8's equilibrium model; the 2-D engine has no `D(N)` path — a named edge).
* **Self-aligned ideal mask / 1-D vertical device** — perfect gate-edge step, no gate-fringing
  field, no 2-D Poisson (the tar pit); the device electrostatics under the gate stay 1-D.

## Files to change

| File | Change |
|---|---|
| `chip/device_2d.py` | **new** — `mosfet_cross_section`, `MOSFET2D`, punchthrough guard (reuses `diffusion_2d` + `device`) |
| `chip/demo_device_2d.py` | **new** — banked demo: prints the cross-section table, saves `docs/figures/chip-device-2d.png` (mirrors `demo_device.py`) |
| `chip/plots.py` | **new** `device_2d_figure(data)` — left: the 2-D S/D cross-section curving under the gate (gate drawn on top, `L_drawn` vs `L_eff` marked, n⁺ junction contour); right: mechanism — `L_eff` & `I_Dsat` vs `L_drawn` with the **punchthrough floor**, and `V_t` flat |
| `chip/tests/test_device_2d.py` | **new** — the triad above |
| `chip/tests/test_demo_device_2d.py` | **new** — demo integration (mirrors `test_demo_*`) |
| `chip/gallery.py` | add `Demo("demo_device_2d", "v1.11", …)` to `DEEPENINGS` |
| `docs/index.html` | regenerate via `python -m chip.gallery` (guarded by `test_gallery.py`) |
| `README.md` | add a v1.11 row to the deepenings catalog table |
| `chip/README.md` | add the v1.11 *Status* writeup |
| `docs/plans/microchip-fabrication.md` | add the §10 v1.11 build-log entry |
| `memory/chip-device-2d-v111.md` + `memory/MEMORY.md` | new memory note + index pointer |

No `pyproject.toml` change (`testpaths` already covers `chip`); no engine edit, no new ADR
(chip-local composition); no `tools/gate.py` (that manifest is in the BigSim monorepo, not here).

## Verification

1. **Fast lane green:** `./run_tests.ps1 -m "not slow" -n auto` — the new `test_device_2d.py`
   triad + `test_demo_device_2d.py` pass; total count rises from 254 (expect +~16).
2. **Demo runs & banks the figure:** `python -m chip.demo_device_2d` prints the cross-section
   table (recipe → `x_j`, `ΔL`, `L_drawn → L_eff`, `V_t` unchanged, `I_Dsat` boost) and saves
   `docs/figures/chip-device-2d.png`; eyeball the figure (S/D curving under the gate, the
   shortening, the flat `V_t`).
3. **Gallery not stale:** `python -m chip.gallery` regenerates `docs/index.html`;
   `test_gallery.py` stays green (the new card present, figure introspected).
4. **Boundary check (manual):** confirm the `V_t`-invariance test fails if `L` were wired into
   `V_t` — i.e. the guard actually guards.
5. **Commit + push** to `main` with a conventional message (per the commit-at-end-of-batch
   convention), fast lane green first.
