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

## G4 — silicon purification + the contamination consequence model

The front of the line: a feedstock **grade** is a starting **impurity vector**, and **purification is
segregation** — [`chip/purification.py`](../chip/purification.py) (triad-tested) is the **Pfann**
single-pass zone-refining closed form `C(u)/C₀ = 1 − (1−k)e^(−k·u)`, reusing Czochralski's one cited
Trumbore `k` table. The teachable result is straight off that table: a tiny-`k` metal (Fe `k≈8e-6`) is
scrubbed ~5 orders in one pass, while boron (`k≈0.8`) is barely touched — segregation cleans metals
superbly but cannot purify the dopants. Then each surviving impurity reaches a device number **only as
far as a receiving variable exists** (the crux — propagation is gated by the consequence model, not the
engine):

- **G4a — Na → oxide charge, residual B/P → net doping.** Mobile-ion **Na** incorporates into the gate
  oxide as charge `Q_ox`, lifting `chip.device`'s named `Q_ox=0` edge (`ΔV_FB = −Q_ox/C_ox`) → `V_t`
  **down**; residual **B/P** fold into the effective channel doping. A dirty **MGS** feed (one pass)
  walks `V_t` out the bottom → scrapped on `V_t`, the trail naming the Na.
- **G4b — deep-level metals → SRH lifetime → junction leakage** (the consequence net doping *cannot*
  carry). [`chip/lifetime.py`](../chip/lifetime.py) (triad-tested) is the **Shockley–Read–Hall**
  recombination centre: `1/τ = 1/τ_bulk + Σ σ_n·v_th·N_metal` (p-type low-injection → the **electron**
  cross-section governs) and the generation-limited reverse leakage `J_gen = q·n_i·W/(2τ) ∝ N_metal`.

> a **metal-laden but Na/dopant-clean** feed (the flagged `"metal"` grade) → `V_t` reads **fine**, yet
> the diode is **leaky** → the wafer is scrapped on **leakage**, the trail naming deep-level-metal SRH.
> *V_t is a bystander* — the device effect net doping can't see. Rework = more zone passes (tiny `k`
> scrubs by `k²`/pass → one extra pass recovers lifetime/leakage).

The SRH law's **tight legs are the machinery, not the magnitudes** (plan §7 loose tier): the analytic
leg is the low-injection reduction of the full `U(n,p)` statistics (`σ_p`, `E_t` drop out → `σ_n`); the
conservation leg is **detailed balance** `U=0` at `p·n=n_i²` (exact for any parameters). The capture
cross-sections (Sze; Graff) + the clean-FZ `τ~ms` / `[Fe]~1e12→µs` order are **flagged loose**
([`chip/tests/test_lifetime.py`](../chip/tests/test_lifetime.py)). The leakage is computed *inside* the
device step (a new die field + an *optional* leakage spec window), so the provenance/bookkeeping is
unchanged and the metals never touch `V_t`/`I_Dsat`. **Gettering / precipitation / oxide breakdown**
stay named **Tier-3** edges.

## Module map

- **`state.py`** — the immutable `WaferState` / `Die` die-map + append-only `DieStepRecord`
  provenance (the "why did this die?" trail). G2 added the substrate fields `slice_z` /
  `resistivity_ohm_cm`; G3 added per-die **`defects`** / `killed_by_defect`, the wafer-level
  **`geometry`**, the `DefectEvent` type, and the **single** `die_area_cm2` / cell-geometry helpers;
  G4 added the wafer-level **`contamination`** vector and the per-die **`tau`** / **`j_leak`** (G4b).
- **`recipe.py`** — the per-step knob dataclasses; `DEFAULT_RECIPE` **is** `chip.demo_device`'s
  coherent n-MOSFET recipe (the seam anchor). G2 added **`CzochralskiKnobs`**; G3 added
  **`WaferPrepKnobs`** (geometry + the killer-defect density); G4 added **`PurificationKnobs`**
  (feedstock grade + zone passes, defaulting to a clean feed) + the derived `contamination` /
  `effective_channel_N_A` recipe properties.
- **`variation.py`** — the seeded stochastic spread: a center-to-edge trend routed *through the
  physics* + die-to-die output scatter. `NO_VARIATION` collapses to one physics call (the seam).
  Magnitudes are **flagged house defaults**, not cited.
- **`defects.py`** (G3) — the seeded **per-die Poisson** killer-particle placement (off without
  touching the RNG when the stochastic layer is disabled or the line is clean — the seam).
- **`spec.py`** — spec windows → the per-die verdict (NILS / CD / I_Dsat / V_t); G3 added the
  killer-defect **functional** gate and the wafer-level **`GeometrySpec`** (TTV/bow) scrap gate; G4b
  added the *optional* **leakage** window (`SpecWindow.optional` — a die not scored on leakage isn't
  failed "missing").
- **`steps.py`** — the deterministic step wrappers; G3 added `wafer_prep_step` (geometry + defects);
  G4 wired the **device step's contamination reads** (Na→`Q_ox`→`V_t`; G4b Fe/Cu→`chip.lifetime`→the
  leakage field), all *inside* `device_step` (no new pipeline step).
- **`pipeline.py`** — `run_line` (the driver, one seeded RNG in fixed die order; the wafer-level
  purification + wafer-prep run first), `wafer_yield`, `diagnose` (the failure trail, + killer-defect /
  `Q_ox` / deep-level-metal leakage branches), `rework_litho`, G3's **`rework_polish`**, and G2's
  **`run_batch`**.
- **`demo_fab_game.py`** + **`demo_boule.py`** + **`demo_wafer_prep.py`** + **`demo_purification.py`**
  + **`demo_lifetime.py`** + **`plots.py`** — the banked artifacts (`fab-game-g1.png` defocus;
  `fab-game-g2.png` boule → V_t; `fab-game-g3.png` particle map + yield law + TTV scrap;
  `fab-game-g4.png` Na → V_t scrap + rework; `fab-game-g4b.png` metals → leaky diode + rework).
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
- **`test_contamination.py`** (G4a) — purification scrubs the wafer; a dirty feed's Na walks `V_t`
  out of spec (named), more passes recover, a clean grade is the seam.
- **`test_leakage.py`** (G4b) — the metals → SRH lifetime → junction-leakage wiring: a metal feed is
  scrapped on **leakage** (not `V_t`) and named; more passes recover; clean is the baseline seam.
- **`test_demo_purification.py`** / **`test_demo_lifetime.py`** (G4a/G4b) — the banked artifacts'
  theses (the Na→`V_t` kill + rework; the isolated metal → leaky-diode kill + rework).

## Run it

```sh
python -m fab_game.demo_fab_game          # prints the story, banks docs/figures/fab-game-g1.png
python -m fab_game.demo_boule             # the G2 boule → V_t spread, banks docs/figures/fab-game-g2.png
python -m fab_game.demo_wafer_prep        # the G3 particle map + yield law + TTV scrap, banks fab-game-g3.png
python -m fab_game.demo_purification      # the G4a Na → V_t scrap + rework, banks fab-game-g4.png
python -m fab_game.demo_lifetime          # the G4b metals → leaky diode + rework, banks fab-game-g4b.png
pytest fab_game/ -q                       # the mechanics suite (rides the fast lane)
jupyter lab fab_game/fab_game.ipynb       # the interactive skin (needs the [viz,notebook] extras)
```
