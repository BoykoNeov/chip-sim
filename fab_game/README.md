# `fab_game` — the fab-line game (G1: the harness · G2: the boule · G3: the physical die map)

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

## G3 — wafer prep + particles + the die map made physical

G2 gave each wafer a substrate; **G3 makes the across-wafer map physical.** New cited physics in
[`chip/wafer_prep.py`](../chip/wafer_prep.py) (triad-tested): the **defect-limited yield law** — a
die that catches a killer particle is dead *functionally*, with probability `Y = exp(−D₀·A)` of
zero defects (the **Murphy / Poisson** model; **Stapper**'s negative-binomial `(1+D₀A/α)^(−α)` for
clustered defects rides as the `α→∞` limit + named scope edge) — plus the exact **geometry**
bookkeeping (slice → lap/CMP sets thickness / TTV / bow).

> killer particles scattered at **locations** on the die map → dies they hit die *functionally* →
> yield; **and** a weak CMP leaves the **TTV** out of flatness spec → the wafer is **scrapped**,
> recoverable by a re-polish that **eats thickness**.

The placement (`fab_game/defects.py`) draws killer particles as a **per-die Poisson** process —
which, by the Poisson restriction/superposition property, *is* the global wafer scatter restricted
to each die's cell, against the **single** `state.die_area_cm2` that the closed form also uses. The
banked artifact ([`demo_wafer_prep.py`](demo_wafer_prep.py) → `docs/figures/fab-game-g3.png`) shows
the empirical defect yield **converging to the cited `exp(−D₀·A)` law** as the random placement is
swept over density — the game-layer wiring tied back to the validated physics. A killer defect is a
**functional** fail (the transistor exists but is dead — distinct from an unresolved litho image,
where the device *refuses*); geometry is a **wafer-level scrap** gate.

The yield *law* is validated as cited physics in [`chip/tests/test_wafer_prep.py`](../chip/tests/test_wafer_prep.py)
(`Y(0)=1` exact + `α→∞`→Poisson limit; area-additivity `Y(A₁+A₂)=Y(A₁)·Y(A₂)` conservation; cited
Murphy/Stapper forms + an illustrative `D₀` band). **Clustered placement** (a fitted `α`) and the
**TTV→focus-budget** propagation wire are named scope edges, deferred.

## Module map

- **`state.py`** — the immutable `WaferState` / `Die` die-map + append-only `DieStepRecord`
  provenance (the "why did this die?" trail). G2 added the substrate fields `slice_z` /
  `resistivity_ohm_cm`; G3 added per-die **`defects`** / `killed_by_defect`, the wafer-level
  **`geometry`**, the `DefectEvent` type, and the **single** `die_area_cm2` / cell-geometry helpers.
- **`recipe.py`** — the per-step knob dataclasses; `DEFAULT_RECIPE` **is** `chip.demo_device`'s
  coherent n-MOSFET recipe (the seam anchor). G2 added **`CzochralskiKnobs`**; G3 added
  **`WaferPrepKnobs`** (geometry + the killer-defect density, defaulting to a clean line).
- **`variation.py`** — the seeded stochastic spread: a center-to-edge trend routed *through the
  physics* + die-to-die output scatter. `NO_VARIATION` collapses to one physics call (the seam).
  Magnitudes are **flagged house defaults**, not cited.
- **`defects.py`** (G3) — the seeded **per-die Poisson** killer-particle placement (off without
  touching the RNG when the stochastic layer is disabled or the line is clean — the seam).
- **`spec.py`** — spec windows → the per-die verdict (NILS / CD / I_Dsat / V_t); G3 added the
  killer-defect **functional** gate and the wafer-level **`GeometrySpec`** (TTV/bow) scrap gate.
- **`steps.py`** — the deterministic step wrappers; G3 added `wafer_prep_step` (geometry + defects).
- **`pipeline.py`** — `run_line` (the driver, one seeded RNG in fixed die order; wafer prep is now
  step 1), `wafer_yield`, `diagnose` (the failure trail, +a killer-defect branch), `rework_litho`,
  G3's **`rework_polish`** (re-CMP a TTV scrap, eats thickness), and G2's **`run_batch`**.
- **`demo_fab_game.py`** + **`demo_boule.py`** + **`demo_wafer_prep.py`** + **`plots.py`** — the
  banked artifacts (`fab-game-g1.png` defocus; `fab-game-g2.png` boule → V_t; `fab-game-g3.png` the
  particle map + the cited yield law + the TTV scrap/re-polish).
- **`fab_game.ipynb`** — the thin notebook skin (not in the correctness path).

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
- **`test_defects.py`** (G3) — placement determinism + the load-bearing **convergence** leg (the
  empirical kill rate → the cited `exp(−D₀·A)`, against the single die area), and the
  killer-defect → functional-fail wiring.
- **`test_geometry.py`** (G3) — the TTV/bow **scrap** gate and the `rework_polish` accounting
  (recovers a TTV scrap, eats thickness; cannot fix bow or remove a killer particle).

## Run it

```sh
python -m fab_game.demo_fab_game          # prints the story, banks docs/figures/fab-game-g1.png
python -m fab_game.demo_boule             # the G2 boule → V_t spread, banks docs/figures/fab-game-g2.png
python -m fab_game.demo_wafer_prep        # the G3 particle map + yield law + TTV scrap, banks fab-game-g3.png
pytest fab_game/ -q                       # the mechanics suite (rides the fast lane)
jupyter lab fab_game/fab_game.ipynb       # the interactive skin (needs the [viz,notebook] extras)
```
