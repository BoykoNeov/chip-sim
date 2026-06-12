# The Fab-Line Game — Project Plan

> A new direction built **on top of** chip-sim: a gamified, full-production-line
> fabrication simulator — *sand to packaged chip* — where every step can fail and
> failure propagates downstream as real physics. Layering, the one-way dependency, and
> the no-game-engine call are settled in **[ADR 0005](../decisions/0005-fab-game-layering.md)**;
> this plan is the *what* and the *build order*. Working title only — the package is
> `fab_game/`; the game's name is open.

---

## 1. Vision & the dramatic early win

**Vision.** Take a learner from a bucket of sand to a binned, packaged chip — through
**silicon purification → Czochralski crystal growth → wafer prep → oxidation → lithography
→ dopant diffusion → etch/deposition → device → dicing/bond/test** — with the dozens of
repeated litho/etch cycles **collapsed to one representative of each distinct operation**.
Every step exposes **continuous recipe knobs** (temperature, time, pull rate, dose, focus,
overlay…). Every step can **fail**: a deterministic physics core sets the nominal outcome
from your knobs and the wafer's inherited state, a **stochastic** layer spreads it, and a
**spec window** decides pass/fail. Damage **propagates** because the degraded output state
*is* the next step's input — contamination raises diffusivity and kills lifetime ten steps
later; a too-fast crystal pull spreads resistivity across the batch; a defocused exposure
shrinks the channel into punchthrough. The payoff is **yield** — and, crucially, *why* a die
died, traced back through the line. The frame is a **roguelike** (a boule/wafer's journey,
consequences stick, realistic rework where physical) with a **sandbox** mode now and a
possible **tycoon** mode later.

**This is chip-sim's "recipe in, device out" loop turned into "recipe in, *yield* out, and
you can see *why*."**

**The dramatic early win (the first banked artifact).** *A wafer carrying a live
`WaferState` runs the existing, already-validated back end — diffusion → oxidation →
lithography → device — through the spec/failure/yield harness, and one bad knob visibly
ripples to a dead die.* Defocus the exposure → the gate image degrades → the die leaves spec →
that die fails, and the failure trail names defocus as the cause. Built **entirely on physics
that already passes triads** (Phases 1–4 of the microchip plan), so the *mechanism* — state,
propagation, spec, yield, rework — is proven before a single new equation is added. This is the
analogue of the microchip plan's "cheapest end-to-end process→device demo," now with failure and
yield.

> **G1-built refinement of the defocus chain (the validated mechanism).** The original prose
> here read *"defocus → CD out of window → channel collapses → `V_t`/`I_Dsat` leave spec"*; G1
> on the validated `litho.py` shows that is the *extreme*-defocus regime, not the primary one.
> For a symmetric line/space feature the **CD midpoint is defocus-robust** — defocus's first
> casualty is **image sharpness (NILS)**, the cited printability metric, which collapses
> (4.6→1.5 over 0–200 nm) while the CD barely moves. So the banked demo's moderate-defocus
> failure is **NILS below the printability floor** (an edge ring, via the center-to-edge focus
> bowl). Only *extreme* defocus finally collapses the CD out of window — and when it does it
> **raises** `I_Dsat` (shorter channel over-drives → an I_Dsat **ceiling**, not a floor). And
> **`V_t` is never on the defocus chain** (the device model's own scope edge: `V_t` carries no
> channel-length term — only the drive current reads the CD). The demo demonstrates *both*: the
> NILS edge ring at defocus = 90 nm and the literal CD/`I_Dsat` collapse at 320 nm.

---

## 2. Relationship to chip-sim — the two layers (see ADR 0005)

| Layer | Lives in | Owns | Validated by |
|---|---|---|---|
| **Physics** | `chip/`, `engines/` | the validated process models + the diffusion engine; **grows** the new process physics (purification, Czochralski/Scheil, wafer prep, etch/depo, packaging) + the physical variation models | cited **triads** (analytic + conservation + benchmark) |
| **Game** | `fab_game/` (new) | `WaferState`/boule/die-map, the pipeline state machine, spec windows, stochastic spread + yield + binning, rework rules, scoring, UI | **mechanics** invariants (not cited magnitudes) |

**One-way dependency:** `fab_game → chip/engines`, never the reverse — enforced by an
import-direction test. **In-repo subpackage first**, split to its own repo only once the
consumed API matures (rule-of-three + the BigSim monorepo→split precedent). New *physics*
always lands in the physics layer; `fab_game` holds only what cannot be cited (balance, spec
limits, fun). Full rationale + alternatives in ADR 0005.

---

## 3. The wafer state — what flows between steps

A wafer is **not** a scalar here (the synced choice: *across-wafer die map* + *boule→batch*).
The state is a field that accumulates physical history. Sketch (final shape settled at build):

```
Boule                       # Czochralski output
  axial_resistivity(z)      # the Scheil profile → each slice starts different
  oxygen, dislocation_free_length, diameter
  → slice(z) → Wafer

WaferState                  # an immutable snapshot; each step returns a NEW one
  provenance: [StepRecord]  # append-only — the failure trail ("why did this die?")
  contamination: Field      # C / O / metals / stray dopant (from purification) → feeds D, lifetime
  geometry: thickness, TTV, bow/warp, surface_roughness
  dies: Grid[Die]           # the across-wafer die map — a coarse lateral grid of die SITES
    Die
      site: (i, j)
      # local process params (center-to-edge trend + noise put these here):
      t_ox, dopant_profile / x_j / R_s, CD, overlay, L_eff
      defects: [DefectEvent]    # particles etc. — at LOCATIONS (killer-defect yield)
      device: { V_t, I_Dsat }   # once extracted
      verdict: pass | fail(reason)   # against the spec windows
  batch_context: boule_position, wafer_id, rework_log
```

**The honest scope of "across-wafer die map" (so we stay synced):** it is a **per-die
parameter/defect field**, *not* a full-wafer 3-D PDE. Each die site carries its own local
process parameters drawn from a **center-to-edge trend + stochastic noise + discrete particle
events**; the deep 1-D-depth physics (the closed forms, the diffusion solves) runs **per die
site** (or per representative site). The fine 2-D engine (`diffusion2d`) stays for *local*
mask-edge physics, not whole-wafer maps. This is how real fabs model within-wafer
non-uniformity, and it keeps the state tractable.

---

## 4. The failure & yield model

Every step is `state_out = step(state_in, knobs, rng)` — a pure function of the inherited
state, the recipe knobs, and a **seeded** RNG.

- **Deterministic core.** The physics computes the *nominal* outputs from `knobs` +
  `state_in`. This is the validated, reproducible part.
- **Stochastic spread.** A variation layer perturbs the nominal: process variation (dose
  scatter, focus jitter, center-to-edge thickness/CD non-uniformity) as continuous noise;
  particles/defects as **discrete Poisson events** placed on the die map. All randomness is
  drawn from one seeded generator, so a run is fully reproducible (a roguelike "seed").
- **Spec windows → verdict.** Each critical output has a spec `[lo, hi]`. A die fails
  **parametrically** if a critical parameter leaves its window, or **functionally** if a
  killer defect lands on it. `yield = good dies / total`.
- **Propagation.** No scripted dependency graph — damage propagates because each downstream
  step *reads the inherited field* (the diffusion step consumes the contamination level and
  adjusts `D`; the device step reads the local `t_ox`, `x_j`, `CD`). **The wiring is the
  work** (ADR 0005 / advisor): the state must be rich enough, and each step's physics must
  depend on the fields it physically should.
- **Rework (physically realistic).** Each step declares `reworkable` + a cost. Some allow a
  costly redo that resets that step's contribution (re-polish — at the cost of thickness;
  strip-and-regrow oxide; strip resist and re-coat/re-expose — litho rework is a real fab
  step). Others are **irreversible** (a dislocated crystal, an over-driven junction). The
  rework *rules* live in `fab_game`; whether a step is physically reworkable is a property of
  its physics. In **sandbox** mode any step re-runs freely; in **roguelike** mode consequences
  stick and only the physical rework paths are available.

---

## 5. The steps — collapsed, with fidelity & rework (the narrative line, front to back)

One representative of each distinct operation. **Fidelity** is laddered honestly (per the
synced "as real as reasonable" + "hard to verify"): some steps are genuine validated physics,
some are flagged phenomenology, the yield/defect parts are explicitly stochastic models.

| # | Step | Physics | Fidelity | Reuse / New | Rework | A failure looks like |
|---|---|---|---|---|---|---|
| 1 | **Silicon purification** (grade knob MGS/solar/EGS) **+ zone refining** | **segregation** (Pfann/Scheil) scrubs metals → a contamination *vector*; distillation = a grade knob, not a column sim (§5a) | **segregation High** (closed form, cited `k`); distillation/CVD Low (knob) | **New** (chip-sim) | re-refine / more zone passes (costly) | high C/O/metals → effect depends on species (§5a) |
| 2 | **Czochralski growth** (pull rate, rotation, melt T, seed) → boule | **Scheil** axial dopant segregation; **crucible oxygen → thermal donors** (§5a); dislocation-free (Dash neck) | **Scheil/O-segregation High**; donor kinetics Mid; dislocation Low | **New** (chip-sim) | irreversible (scrap/low-grade) | too-fast pull → dislocations / striations / resistivity spread |
| 3 | **Wafer prep** (slice → lap → etch → CMP → edge round → clean) | geometric/mechanical bookkeeping + particle statistics | geometry exact, **particles stochastic** | **New** (chip-sim) | re-polish/re-clean (costly, eats thickness) | TTV/bow out of spec; particle map seeds killer defects |
| 4 | **Oxidation** (Deal–Grove / Massoud, wet/dry) | the validated oxide-growth closed form → local `t_ox` | **High** ✓ | **Reuse** `chip/oxidation.py` | strip & regrow oxide | `t_ox` out of window → `V_t` error |
| 5 | **Lithography** (aerial image + defocus/Zernike + PEB/CAR) | the validated optics → printed CD + overlay | **High** ✓ | **Reuse** `chip/litho.py` | strip resist, re-coat & re-expose | defocus/overlay → CD out of spec → wrong `L_eff`/misalign |
| 6 | **Dopant diffusion / implant + anneal → junction** | the engine + `D(N)` + 2-D lateral → profile, `x_j`, `R_s`, `L_eff` | **High** ✓ | **Reuse** `engines/diffusion`, `chip/diffusion_dopant.py`, `junction.py` | irreversible (can't un-diffuse) | over/under-drive → wrong `x_j`; lateral → punchthrough |
| 7 | **Etch & deposition (+ CMP planarization)** | rate × time + anisotropy/selectivity/conformality/uniformity fields | **Low** (phenomenological, honest) | **New** (chip-sim) | depo sometimes strippable; over-etch irreversible | over/under-etch; non-conformal step coverage |
| 8 | **Device extraction** (MOS `V_t`, `I_Dsat`, `L_eff`; **+ τ / leakage**) | the validated compact model **+ a new SRH lifetime + junction-leakage output** (§5a Tier 2) | `V_t`/`I_Dsat` **High** ✓; τ/leakage Mid (cited, loose) | **Reuse** `device.py`/`device_2d.py` **+ new `lifetime.py`** | n/a (a readout) | parametric OR lifetime/leakage out of spec |
| 9 | **Packaging & test** (dice → attach → wire-bond → encapsulate → final test → bin) | assembly-yield + parametric/functional test against spec | **stochastic** yield model | **New** (chip-sim) | limited (rebond rare; cracked die = scrap) | dicing/bond defects; parametric bin-out |

**The propagation web (the pedagogy).** Contamination → `D` & minority-carrier lifetime;
Scheil resistivity → `V_t` spread across the batch; defocus/overlay → `L_eff`/misalignment;
over-drive → punchthrough; particles → killer defects → dead dies. These edges are *physics
wired through the state*, not scripted sad-faces — that is what makes it a simulation.

### 5a. Contamination & purification — the consequence model

*(The feasibility analysis behind steps 1–2 — where "badly purified materials" becomes physics.
Advisor-reviewed; the physics claims below are verified.)*

**The crux — propagation is gated by the device's *receiving variable*, not the engine.** The
diffusion engine carries any impurity for free: one independent species run per contaminant,
its own cited Arrhenius `D` (the engine is single-field, so multi-species = independent runs
combined at the end — confirmed against `CONTRACT.md`). But a contaminant only propagates to a
device number *as far as some device variable can receive it.* Today that variable is **net
doping** — so "simulate bad purification" is really **"extend the consequence model,"** not
"diffuse more species."

**Four buckets — the *effect* differs, not the transport:**

| Bucket | Example | Effect | Propagates today? | Cost |
|---|---|---|---|---|
| Shallow dopant | residual B/P | **net doping** | **free** — add to the net profile; `junction.py`/`device.py` already read it | nil |
| Mobile ion | Na | **oxide charge** | **near-free** — lift `device.py`'s named `Q_ox=0` edge: `ΔV_FB = −Q_ox/C_ox` | trivial |
| Deep-level metal | Fe/Cu/Ni | **SRH recombination center** (lifetime, leakage) — *not* doping | **no** — needs a new device output | Tier-2 module |
| Reactive/aggregating | **oxygen** (crucible) | **thermal donors** via ~450 °C kinetics → net doping | **yes — once kinetics give the active fraction** | small kinetics |

- **Metals: the diffusion solve is nearly pointless.** A fast interstitial (≈10 orders faster
  than substitutional B/P) gives a *flat* profile — so model a metal as an **areal-dose budget +
  active fraction + SRH consequence**, not a transport run. Its real fate (gettering /
  precipitation at junctions, the actual device-killer) is a named **Tier-3** edge.
- **The unifying thread** is the repo's existing **active-vs-chemical** scope edge
  (`junction.py` full-activation; v1.3's `n_active_max` plateau), generalized: *chemical
  concentration → electrically-active fraction → device effect*, the mapping differing by
  species (dopant ≈100 % net doping; metal ≈0 % doping / X % recombination; oxygen
  donor-kinetics-gated). This makes contamination a **backbone**, not a bolt-on.

**Purification is segregation — the verifiable win.** Zone refining and CZ purify by `k<1`
segregation: single-pass **Pfann** `C(x)/C₀ = 1 − (1−k)·e^(−kx/L)`, **Scheil**
`C_s(z) = k·C₀·(1−z)^{k−1}` — closed-form, triad-able, cited `k` (**Trumbore 1960 — already in
our citations** for solid solubility, also tabulates distribution coefficients). The tiny `k`
for metals (Fe ~1e-5, Cu ~1e-4) vs near-unity for B/P (~0.8 / ~0.35) is *why* refining scrubs
metals superbly and barely touches B/P — a teachable result straight from the `k` table. Tight
legs: the `k→1` limit + mass conservation; calibrated edge: `k_eff(v)` (Burton–Prim–Slichter,
growth-rate/stirring). The **Siemens chlorosilane distillation is a different domain**
(separations, weak coupling to the device payoff) → model it as a **grade knob** (MGS / solar /
EGS → a starting impurity vector), **not** a column sim.

**Build tiers:**
- **Tier 1 — build, cheap *and* verifiable.** Segregation purification (Pfann/Scheil) + dopant
  & oxygen contaminants through net doping + Na → `Q_ox`. Most of the "bad purification" story,
  and the verifiable part.
- **Tier 2 — one bounded new module (`lifetime.py`), worth it.** SRH lifetime `τ(N_metal)` +
  junction reverse-leakage as **new device outputs** — because the game wants "**does it
  work?**" beyond `V_t` anyway (a leaky, low-lifetime diode is how a metal contaminant kills
  yield). Cited (Sze; Graff, *Metal Impurities in Silicon*), magnitudes **loose**.
- **Tier 3 — name and flag, do not first-principles.** Gettering/precipitation, oxide
  breakdown / `D_it` degradation, the Siemens distillation column.

**Validation honesty.** The **tight** leg of the whole contamination feature is the
**segregation math** (Pfann/Scheil — exact `k→1` + mass conservation). The **metal
device-degradation magnitudes** (capture cross-sections, active fractions, `D_it`) are
**calibrated/loose** — flagged, not asserted with Scheil's anchors.

---

## 6. Build order — vertical slice first, then fill the line

The narrative line (§5) runs front-to-back; the **build** runs slice-first, so the
machinery is proven on validated physics before the least-verifiable new physics is written.
Each phase banks a demonstrable artifact (the program invariant: every stage ships a working
thing).

- **G1 — The harness + the vertical slice (the dramatic win).** `fab_game/`: the
  `WaferState`/die-map objects, the `step(state, knobs, rng)` protocol, the pipeline driver,
  spec windows, the deterministic+stochastic+yield model, and the rework mechanic — wired
  through the **existing** diffusion → oxidation → litho → device back end. Notebook UI. The
  banked artifact: one bad knob → a dead die, with the failure trail. **All reuse, zero new
  physics** — proves the mechanism. *(This is the `process.py` that was never built, now with
  state, variation, and yield.)*
- **G2 — Czochralski + Scheil + boule→batch (+ the first contamination demo).** The first new
  physics, in chip-sim: the **Scheil** equation (the verifiable front-of-line win — see §7 / §5a)
  for axial dopant *and* **crucible-oxygen** segregation, the boule with axial resistivity
  variation, slicing into a wafer batch where each wafer starts different; wire resistivity into
  the device readout. **Oxygen → thermal donors is the first contamination story** (§5a bucket 4)
  — CZ-native, and it rides the existing net-doping flow once the donor kinetics give the active
  fraction.
- **G3 — Wafer prep + particles + the die map made physical.** Defect events placed at
  locations on the across-wafer map; killer-defect functional yield; geometry (TTV/bow)
  bookkeeping.
- **G4 — Silicon purification + the contamination consequence model (§5a).** **Segregation
  purification** as real physics (Pfann zone-refining `C/C₀ = 1−(1−k)e^(−kx/L)` + cited `k`; the
  *grade knob* for the Siemens route). Then the contamination buckets wired to their
  consequences: dopant & Na ride the existing flow (Tier 1); the **Tier-2 device output** — a new
  `lifetime.py` (SRH `τ(N_metal)` + junction leakage) — lands the metals' effect that net doping
  can't carry. Gettering/precipitation stays a named edge (Tier 3).
- **G5 — Etch / deposition / CMP.** The missing mid-line operations (phenomenological, honest).
- **G6 — Packaging & test & binning.** The back-end assembly yield + parametric/functional test.
- **G7 — Roguelike framing + scoring + a Textual TUI; sandbox mode.** The game shell over the
  proven sim. (Tycoon deferred — same harness, different objective.)

---

## 7. Validation discipline

- **New physics (physics layer) — the cited triad, unchanged.** Each new module names its
  analytic limit, a conservation law, and a published benchmark, with the non-circularity
  split and the scope edge. The **showcase is Czochralski/Scheil**: `C_s(z) = k·C_0·(1−z)^{k−1}`
  is a closed form with an **exact `k→1` limit** (uniform doping) and a **mass-conservation**
  check (∫ over the boule recovers the charged dose) — it drops straight into the triad
  pattern and is the one genuinely-verifiable front-of-line physics win. Caveat the
  **benchmark leg** owns: `C_s` diverges as `z→1` (you never solidify the full melt), so the
  realistic resistivity-*spread* numbers are the loose/calibrated leg — the tight legs are the
  `k→1` limit and the conservation integral, not a number near the tail. For **contamination**
  (§5a) the same split holds: segregation purification (Pfann/Scheil) is the *tight* leg, while
  the metal device-degradation magnitudes (SRH cross-sections, active fractions, `D_it`) are
  the *loose/calibrated* leg. Etch and packaging are **flagged phenomenology** — honest,
  calibrated, scope-edge named.
- **Game mechanics (`fab_game`) — invariants, not magnitudes** (ADR 0005): the
  import-direction guard; **determinism** under a fixed seed; **propagation actually wired**
  (a worse inherited field never yields a better downstream observable where physics forbids
  it); **state bookkeeping** (good+bad = total, provenance append-only, rework accounting
  closes); and the **seam test** (nominal knobs + zero variation reproduce the existing demo
  numbers bit-for-bit). Heavy / live-kernel / UI tests carry the `slow` marker (ADR 0003).

---

## 8. Scope ceiling — what we deliberately do not simulate

Inherits the microchip plan's tar pits and adds the game's:

- **No full 2-D/3-D TCAD** (Poisson + drift-diffusion on a device mesh) and **no rigorous
  EMF / Hopkins-TCC litho** — the microchip §5 walls stand. We target the *consequence*
  (1-D-depth process profiles + aerial-image litho + compact device), now per die site.
- **The across-wafer map is a per-die parameter field, not a full-wafer PDE** (§3).
- **Front-of-line physics is phenomenological where named** (purification, etch, packaging) —
  the honest fidelity ladder, not a pretense of first-principles everywhere.
- **No economic/market model** beyond a simple budget/cost for rework and tooling — the
  **tycoon** layer is deferred (same harness, a different objective + scoring).
- **No game engine as authority** — Python sim is the source of truth; UI is a thin skin
  (ADR 0005).

**Terms of use (inherited, microchip §6).** This stays firmly in the
**published-information / educational carve-out**: generic textbook physics (Scheil, Siemens
CVD, Deal–Grove, erfc/Gaussian diffusion, Fourier-optics litho, compact `V_t`, statistical
yield) from first principles, with original code/prose — **no real-fab recipes, no
leading-node specifics, no proprietary tool data, no targeting**. Reference constants are
cited, not redistributed. Adding the full line does not change this: a generic *teaching*
production line is still generic illustrative physics.

---

## 9. Visualization & UX

Per ADR 0002 (compute headless; views consume plain arrays; a figure is never in the
correctness path) and ADR 0005 (no game engine as authority):

- **Notebook + ipywidgets first** (matches `chip.ipynb`): the vertical slice as a guided,
  slider-driven run — choose a recipe, run the line, watch the wafer map and the failure trail.
- **A Textual TUI next** for the roguelike "command the line, watch it ripple" feel — terminal,
  Python-native, still a thin skin.
- **A web app** (Streamlit / small FastAPI+JS) only if a shareable surface is wanted.
- **A real game engine** (Godot) only for a possible tycoon future — and even then the Python
  sim stays the authority, the engine is a pure front-end.

---

## 10. Immediate next step

**Plan + ADR 0005 banked (this document + the decision record).** The next build is **G1 —
the harness + the vertical slice**: stand up `fab_game/` with the `WaferState`/die-map, the
`step` protocol + pipeline driver, the spec/stochastic/yield/rework model, and the
import-direction guard, wired through the existing diffusion → oxidation → litho → device back
end — banking the "one bad knob → a dead die, with the failure trail" artifact in the notebook.
All reuse, zero new physics: prove the mechanism first, then add Czochralski/Scheil (G2).

**Open questions to settle at G1 (named, not pre-decided):**
- **The unit of a roguelike run — one wafer/slice vs one boule/batch.** The synced answers
  *single-wafer roguelike* and *boule→batch* are in tension: do you follow one slice at axial
  position `z` (the boule just sets your starting resistivity), or process the whole batch
  (which leans tycoon)? A pedagogical wrinkle rides on it — Scheil's payoff is seeing
  resistivity vary *down the boule*, which a strictly single-wafer view never shows; a clean
  reconciliation is "single-wafer run, but surface where your slice sits on the boule's Scheil
  curve." Does not block G1 (no boule there); becomes load-bearing at **G2**.
- The exact `WaferState` schema and the die-grid resolution (how many sites per wafer).
- The spec-window source — cited where possible (device targets), house numbers where not.
- The variation-magnitude defaults (the stochastic layer's σ's) — cited vs calibrated-flagged.
- The pipeline representation (an explicit step list vs a small state machine) and how rework
  re-enters it.
- Where the seeded RNG lives so determinism + reproducible roguelike seeds are both clean.
