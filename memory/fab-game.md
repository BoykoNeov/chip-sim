---
name: fab-game
description: New direction — a gamified full-line fab simulator (sand→chip) layered on top of chip-sim; vision synced + plan/ADR 0005 drafted 2026-06-12
metadata:
  type: project
---

**project (2026-06-12):** a NEW direction — a **gamified, full-production-line fab
simulator** (*sand → packaged chip*) built **on top of** chip-sim, not replacing it. Vision
synced with the user across two AskUserQuestion rounds, then **`docs/plans/fab-game.md` +
`docs/decisions/0005-fab-game-layering.md` drafted** (advisor-reviewed; docs-only commit).

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

Inherits chip-sim's tar pits (no TCAD/EMF, microchip §5) + the export-control **educational
carve-out** (generic textbook physics, no real recipes/targeting). [[engine-unfrozen]] is the
reusable engine spine; [[lateral-diffusion-2d]]/[[chip-device-2d-v111]] are the 2-D reuse.
