---
name: fab-game
description: New direction — a gamified full-line fab simulator (sand→chip) layered on top of chip-sim; vision synced + plan/ADR 0005 drafted 2026-06-12
metadata: 
  node_type: memory
  type: project
  originSessionId: dffe5088-7201-43e3-953e-bf624ab3edb8
---

**project (2026-06-12):** a NEW direction — a **gamified, full-production-line fab
simulator** (*sand → packaged chip*) built **on top of** chip-sim, not replacing it. Vision
synced with the user across two AskUserQuestion rounds, then **`docs/plans/fab-game.md` +
`docs/decisions/0005-fab-game-layering.md` drafted** (advisor-reviewed; docs-only commit).

**>> G1 BUILT 2026-06-12 → [[fab-game-g1]]** (the harness + vertical slice: `fab_game/` wired
through the validated back end, "one bad knob → dead die + failure trail", 5 mechanics invariants
green, fast lane 314). The defocus chain's primary signature = **NILS** not CD (plan §1 corrected).

**>> §9 guided ipywidgets slice BUILT 2026-06-14** (`fab_game/dashboard.py` + `plots.dashboard_figure`
+ the `fab_game.ipynb` "command the whole line" section): a thin, **tested** skin over `run_line`
(`run_dashboard`/`dashboard_summary`, 4 dramatic+legible knobs — defocus→edge ring · D₀→scattered
kills · slice_z→Scheil drift · t_ox→the G7 rescue lever) = the **headless, tested core of the
deferred Textual TUI**. Variation **ON** (else the map is a binary all-pass/all-fail flip, not a
story — the advisor's catch). Reuses `LineResult` (no new dataclass); **dropped a profit readout** —
default `speed_bins` grade everything `"pass"` so `score_wafer` prices revenue 0 → a profit line
would be a binning-policy artifact, not a signal. The real safety net is `tests/test_dashboard.py`
(10 tests), NOT the notebook run (`interact` swallows callback exceptions). **Remaining front-end =
the Textual TUI + tycoon — both still deferred** (the named-consumer physics backlog stays exhausted).
**Textual TUI shape DRAFTED, not built (2026-06-14): `docs/plans/fab-game-tui.md`** — v1 = a thin
terminal driver of the §9 `run_dashboard`/`dashboard_summary` core (new `[tui]` extra carrying
`textual`; one new headless helper `plots.wafer_map_text`; `importorskip`-gated `run_test()` pilot
via an `asyncio.run` wrapper, NOT `pytest-asyncio`; xdist-safety to be verified, slow-mark escape
hatch if it flakes like the notebook); v2 = the G7 `GameSession` roguelike loop. No new physics/ADR.

**The seven synced choices:** (1) **full grand tour** — every distinct step,
purification→Czochralski→wafer-prep→oxidation→litho→diffusion→etch/depo→device→dice/bond/test,
repeats collapsed; (2) **both failure models** — deterministic physics mean + stochastic
spread + spec windows → yield; (3) **boule→wafer-batch** (axial **Scheil** variation → each
slice starts different) **+ across-wafer die map** (per-die parameter/defect field, NOT a
full-wafer PDE); (4) **continuous recipe knobs**; (5) **physically-realistic rework** (re-polish
/ strip-&-regrow oxide / re-coat resist reworkable; dislocated crystal + over-driven junction
irreversible); (6) **roguelike-first + sandbox now, tycoon later**; (7) **no game engine as
authority** — Python sim is the source of truth, thin UI (notebook → Textual TUI → web).

**The architecture (ADR 0005):** two layers, one repo to start. **Physics layer** (`chip/`,
`engines/`) stays validated + GROWS the new process physics (purification, CZ/Scheil, wafer
prep, etch/depo, packaging) as cited triads; **game layer** = a new **`fab_game/` subpackage**
owning `WaferState`/die-map, pipeline driver, spec windows, stochastic+yield, rework, scoring,
UI. **One-way import** `fab_game → chip/engines` (import-direction guard test), **in-repo first,
split when mature** (rule-of-three + the BigSim monorepo→split precedent). Game tested for
**mechanics invariants** (determinism under seed, propagation-actually-wired, state bookkeeping,
seam-reproduces-existing-demos) NOT cited magnitudes.

**Build order = vertical slice FIRST** (advisor, load-bearing): **G1** = the harness +
WaferState wired through the *already-validated* diffusion→oxidation→litho→device back end
(the `process.py` that was never built — `device.py` only consumes scalars, chaining lives in
`demo_device.py`), banking "one bad knob → a dead die + the failure trail", ZERO new physics.
**Then G2** Czochralski/**Scheil** (the one verifiable front-of-line win: `C_s(z)=k·C₀·(1−z)^{k−1}`,
exact `k→1`=C₀ + `∫=C₀` conservation legs are tight; **diverges as z→1** so spread numbers are the
LOOSE leg). Then wafer-prep/particles (G3), purification/contamination field (G4), etch/depo (G5),
packaging/test (G6), roguelike shell + TUI (G7).

**OPEN (flagged, advisor-caught, settle at G2):** *unit of a run* — single-wafer-roguelike vs
boule→batch are in tension; Scheil's payoff is seeing resistivity vary DOWN the boule, which a
single-wafer view never shows. Clean reconcile = single-wafer run that surfaces where your slice
sits on the boule's Scheil curve. Other G1 opens: WaferState schema + die-grid resolution,
spec-window sources, variation σ defaults, pipeline-vs-state-machine, seeded-RNG home.

**CONTAMINATION/PURIFICATION feasibility (folded into plan §5a, advisor-verified 2026-06-12):**
THE crux = propagation is gated by the **device's receiving variable, NOT the engine** — today
that's **net doping**, so "simulate bad purification" = **extend the consequence model**, not
diffuse more species (engine is single-field, multi-species = independent runs). **Four buckets:**
(1) shallow dopant B/P → net doping → rides existing flow **FREE**; (2) Na → oxide charge → lift
`device.py`'s named `Q_ox=0` edge (`ΔV_FB=−Q_ox/C_ox`) **near-free**; (3) deep-level metal Fe/Cu/Ni
→ **SRH recombination center** (lifetime/leakage) NOT doping → propagates to **NOTHING today** (needs
new device output); (4) **oxygen** (crucible) → **thermal donors** via ~450°C kinetics → net doping
(the CZ-native first contamination demo). Metals: fast interstitial → flat profile → diffusion solve
**nearly pointless** → model as areal-dose budget + active fraction + SRH, NOT transport; fate
(gettering/precip) = Tier-3 edge. Unifying thread = the repo's existing **active-vs-chemical** edge
generalized. **Purification = segregation** (Pfann `C/C₀=1−(1−k)e^(−kx/L)` / Scheil), triad-able,
cited `k` (**Trumbore 1960 — ALREADY a repo citation**; Fe~1e-5/Cu~1e-4 vs B~0.8/P~0.35 = why
refining scrubs metals not B/P); Siemens distillation = a **grade knob**, NOT a column sim. **Tiers:**
T1 segregation+dopant/O+Na (cheap+verifiable), T2 a new `lifetime.py` SRH τ+leakage device output
(loose magnitudes), T3 gettering/oxide-breakdown/distillation (name+flag). Tight leg = segregation;
loose = metal magnitudes.

Inherits chip-sim's tar pits (no TCAD/EMF, microchip §5) + the export-control **educational
carve-out** (generic textbook physics, no real recipes/targeting). [[engine-unfrozen]] is the
reusable engine spine; [[lateral-diffusion-2d]]/[[chip-device-2d-v111]] are the 2-D reuse;
[[dopant-solid-solubility-source]] (Trumbore 1960) already covers the segregation `k`.
