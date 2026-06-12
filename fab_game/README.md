# `fab_game` — the fab-line game (G1: the harness + slice · G2: the Czochralski boule)

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

## G2 — Czochralski + the Scheil axial-resistivity boule (the first new physics)

The first new, cited **front-of-line** physics ([`chip/czochralski.py`](../chip/czochralski.py),
triad-tested): a Czochralski boule grown from a boron melt has a **Scheil** axial dopant profile,
`C_s(z) = N_seed·(1−z)^(k−1)` (seed-end parameterized so the `z=0` slice is `1e17` *exactly* — the
seam survives). Because boron's segregation coefficient `k ≈ 0.8 < 1` (Trumbore 1960), the solid
that freezes later is *more* doped, so wafers sliced down the boule start at successively higher
substrate doping. That rising `N_A` **alone** walks the device `V_t` up across the spec window — so
the boule's **tail is scrapped**, purely from one crystal-growth knob:

> Scheil segregation → axial resistivity/`N_A` spread → device `V_t` spread → yield down the boule.

**Unit-of-run (the plan §10 question, resolved here):** a *run* is **one wafer at axial `slice_z`**
(`CzochralskiKnobs.slice_z`); the boule is shared context that sets the wafer's starting substrate
(`channel_N_A` is now a boule-slice **property**). `run_batch` is the sweep *down* the boule — an
analysis/demo view that surfaces where each slice sits on the Scheil curve, **not** the roguelike
loop. The axial boule story is per-wafer, so it composes orthogonally with the radial die map.

The Scheil maths are validated as cited physics in [`chip/tests/test_czochralski.py`](../chip/tests/test_czochralski.py)
(`k→1` uniform limit + exact seed; `∫₀¹ C_s = C_0` conservation; cited `k` + Masetti resistivity).
**Oxygen → thermal donors** (the planned G2 contamination demo) is **deferred** to a fenced
follow-on / G4 — its `k` is contested and the donor kinetics are calibrated, so it must not borrow
Scheil's tight anchors.

## Module map

- **`state.py`** — the immutable `WaferState` / `Die` die-map + append-only `DieStepRecord`
  provenance (the "why did this die?" trail). G2 added the wafer-level substrate fields `slice_z`
  and `resistivity_ohm_cm` (the boule slice; both `None`-defaulted for back-compat).
- **`recipe.py`** — the per-step knob dataclasses; `DEFAULT_RECIPE` **is** `chip.demo_device`'s
  coherent n-MOSFET recipe (the seam anchor). G2 added **`CzochralskiKnobs`** (the substrate is
  *grown*, not set): `channel_N_A` / `substrate_resistivity_ohm_cm` are now boule-slice **properties**.
- **`variation.py`** — the seeded stochastic spread: a center-to-edge trend routed *through the
  physics* + die-to-die output scatter. `NO_VARIATION` collapses to one physics call (the seam).
  Magnitudes are **flagged house defaults**, not cited.
- **`spec.py`** — spec windows → the per-die verdict (NILS / CD / I_Dsat / V_t).
- **`steps.py`** — the deterministic step wrappers over the four validated `chip/` modules.
- **`pipeline.py`** — `run_line` (the driver, one seeded RNG in fixed die order), `wafer_yield`,
  `diagnose` (the failure trail), `rework_litho` (the minimal reworkable path), and G2's
  **`run_batch`** (slice a wafer batch down the boule → `BatchResult`, the Scheil-spread view).
- **`demo_fab_game.py`** + **`demo_boule.py`** + **`plots.py`** — the banked artifacts
  (`docs/figures/fab-game-g1.png`, the defocus story; `fab-game-g2.png`, the boule → V_t spread).
- **`fab_game.ipynb`** — the thin notebook skin (a live defocus slider + the G2 boule sweep; not in
  the correctness path).

## Test discipline (ADR 0005 §5) — mechanics invariants, not cited magnitudes

- **`test_seam.py`** — the load-bearing one: nominal + zero variation reproduces
  `chip.demo_device` **bit-for-bit** (the harness does not change the physics).
- **`test_determinism.py`** — same (seed, recipe) → identical wafer; a different seed moves it.
- **`test_propagation.py`** — the device genuinely *reads* the inherited `t_ox`/`CD` (monotone,
  physics-guaranteed), and refuses on an upstream functional fail.
- **`test_bookkeeping.py`** — good + bad = total; provenance append-only; rework accounting closes.
- **`test_import_direction.py`** — the one-way boundary holds.
- **`test_demo_fab_game.py`** — the banked artifact's thesis (the dramatic win + rework recovery).
- **`test_boule.py`** (G2) — the boule wired: seed-slice seam exact, the Scheil `N_A`→`V_t`
  propagation, determinism / no new RNG (Scheil is a closed form), and batch bookkeeping.
- **`test_demo_boule.py`** (G2) — the boule artifact's thesis (the V_t walk scraps the tail).

## Run it

```sh
python -m fab_game.demo_fab_game          # prints the story, banks docs/figures/fab-game-g1.png
python -m fab_game.demo_boule             # the G2 boule → V_t spread, banks docs/figures/fab-game-g2.png
pytest fab_game/ -q                       # the mechanics suite (rides the fast lane)
jupyter lab fab_game/fab_game.ipynb       # the interactive skin (needs the [viz,notebook] extras)
```
