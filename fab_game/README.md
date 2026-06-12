# `fab_game` — the fab-line game (G1: the harness + the vertical slice)

A gamified, full-production-line layer built **on top of** chip-sim: *recipe in → **yield** out, and
you can see **why** a die died.* Full plan: [`docs/plans/fab-game.md`](../docs/plans/fab-game.md);
the layering decision: [ADR 0005](../docs/decisions/0005-fab-game-layering.md).

> **Two layers, one repo, a one-way dependency.** The validated physics stays in `chip/` + `engines/`
> (cited triads); `fab_game/` owns only what *cannot* be physics-validated — the wafer state, the
> pipeline, spec windows, the stochastic spread + yield, and rework. The import direction is
> **`fab_game → chip/engines`, never the reverse**, enforced mechanically by
> `tests/test_import_direction.py`. New *process physics* always lands in the physics layer; this
> package holds balance, spec limits, and fun.

## G1 — the dramatic win (this slice)

**All reuse, zero new physics.** G1 wires the *already-validated* diffusion → oxidation →
lithography → device back end through a state / variation / spec / yield / rework harness and banks
one artifact: **one bad knob → a dead die, with the failure trail.** The chain is

> defocus → the aerial image loses edge sharpness (**NILS** collapses) → the gate no longer prints
> reliably → those dies leave spec → the wafer **yield** drops, and the trail names *defocus*.

A center-to-edge focus bowl makes the failure **spatial** (the edge ring dies, the centre survives);
a litho **rework** (strip & re-expose at corrected focus) recovers it. The defocus chain rides
**CD → channel length → I_Dsat** and the **NILS** printability floor — **never `V_t`** (the device
model's own scope edge: `V_t` has no channel-length term; only `saturation_current` reads the CD).

## Module map

- **`state.py`** — the immutable `WaferState` / `Die` die-map + append-only `DieStepRecord`
  provenance (the "why did this die?" trail). G1-minimal: only what the back end consumes/produces
  (no contamination/geometry/defect machinery yet — those arrive with their named consumers at G2+).
- **`recipe.py`** — the per-step knob dataclasses; `DEFAULT_RECIPE` **is** `chip.demo_device`'s
  coherent n-MOSFET recipe (the seam anchor).
- **`variation.py`** — the seeded stochastic spread: a center-to-edge trend routed *through the
  physics* + die-to-die output scatter. `NO_VARIATION` collapses to one physics call (the seam).
  Magnitudes are **flagged house defaults**, not cited.
- **`spec.py`** — spec windows → the per-die verdict (NILS / CD / I_Dsat / V_t).
- **`steps.py`** — the deterministic step wrappers over the four validated `chip/` modules.
- **`pipeline.py`** — `run_line` (the driver, one seeded RNG in fixed die order), `wafer_yield`,
  `diagnose` (the failure trail), and `rework_litho` (the minimal reworkable path).
- **`demo_fab_game.py`** + **`plots.py`** — the banked artifact (`docs/figures/fab-game-g1.png`).
- **`fab_game.ipynb`** — the thin notebook skin (a live defocus slider; not in the correctness path).

## Test discipline (ADR 0005 §5) — mechanics invariants, not cited magnitudes

- **`test_seam.py`** — the load-bearing one: nominal + zero variation reproduces
  `chip.demo_device` **bit-for-bit** (the harness does not change the physics).
- **`test_determinism.py`** — same (seed, recipe) → identical wafer; a different seed moves it.
- **`test_propagation.py`** — the device genuinely *reads* the inherited `t_ox`/`CD` (monotone,
  physics-guaranteed), and refuses on an upstream functional fail.
- **`test_bookkeeping.py`** — good + bad = total; provenance append-only; rework accounting closes.
- **`test_import_direction.py`** — the one-way boundary holds.
- **`test_demo_fab_game.py`** — the banked artifact's thesis (the dramatic win + rework recovery).

## Run it

```sh
python -m fab_game.demo_fab_game          # prints the story, banks docs/figures/fab-game-g1.png
pytest fab_game/ -q                       # the mechanics suite (rides the fast lane)
jupyter lab fab_game/fab_game.ipynb       # the interactive skin (needs the [viz,notebook] extras)
```
