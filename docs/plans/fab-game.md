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
ripples to a dead die.* Defocus the exposure → the printed CD goes out of window → the
channel length collapses → `V_t`/`I_Dsat` leave spec → that die fails, and the failure trail
names defocus as the cause. Built **entirely on physics that already passes triads** (Phases
1–4 of the microchip plan), so the *mechanism* — state, propagation, spec, yield, rework — is
proven before a single new equation is added. This is the analogue of the microchip plan's
"cheapest end-to-end process→device demo," now with failure and yield.

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
| 1 | **Silicon purification** (MGS → Siemens TCS CVD → EGS; opt. zone refining) | distillation / segregation → residual contamination field | **Low** (phenomenological, calibrated-flagged) | **New** (chip-sim) | re-refine (costly) | high C/O/metals → ↑ `D`, ↓ lifetime downstream |
| 2 | **Czochralski growth** (pull rate, rotation, melt T, seed) → boule | **Scheil** axial dopant segregation; oxygen; dislocation-free (Dash neck) | **Scheil = High** (closed form, exact `k→1` limit + conservation); dislocation/oxygen Low | **New** (chip-sim) | irreversible (scrap/low-grade) | too-fast pull → dislocations / striations / resistivity spread |
| 3 | **Wafer prep** (slice → lap → etch → CMP → edge round → clean) | geometric/mechanical bookkeeping + particle statistics | geometry exact, **particles stochastic** | **New** (chip-sim) | re-polish/re-clean (costly, eats thickness) | TTV/bow out of spec; particle map seeds killer defects |
| 4 | **Oxidation** (Deal–Grove / Massoud, wet/dry) | the validated oxide-growth closed form → local `t_ox` | **High** ✓ | **Reuse** `chip/oxidation.py` | strip & regrow oxide | `t_ox` out of window → `V_t` error |
| 5 | **Lithography** (aerial image + defocus/Zernike + PEB/CAR) | the validated optics → printed CD + overlay | **High** ✓ | **Reuse** `chip/litho.py` | strip resist, re-coat & re-expose | defocus/overlay → CD out of spec → wrong `L_eff`/misalign |
| 6 | **Dopant diffusion / implant + anneal → junction** | the engine + `D(N)` + 2-D lateral → profile, `x_j`, `R_s`, `L_eff` | **High** ✓ | **Reuse** `engines/diffusion`, `chip/diffusion_dopant.py`, `junction.py` | irreversible (can't un-diffuse) | over/under-drive → wrong `x_j`; lateral → punchthrough |
| 7 | **Etch & deposition (+ CMP planarization)** | rate × time + anisotropy/selectivity/conformality/uniformity fields | **Low** (phenomenological, honest) | **New** (chip-sim) | depo sometimes strippable; over-etch irreversible | over/under-etch; non-conformal step coverage |
| 8 | **Device extraction** (MOS `V_t`, `I_Dsat`, `L_eff` via 2-D) | the validated compact model, per die | **High** ✓ | **Reuse** `chip/device.py`, `device_2d.py` | n/a (a readout) | parametric out of spec for that die |
| 9 | **Packaging & test** (dice → attach → wire-bond → encapsulate → final test → bin) | assembly-yield + parametric/functional test against spec | **stochastic** yield model | **New** (chip-sim) | limited (rebond rare; cracked die = scrap) | dicing/bond defects; parametric bin-out |

**The propagation web (the pedagogy).** Contamination → `D` & minority-carrier lifetime;
Scheil resistivity → `V_t` spread across the batch; defocus/overlay → `L_eff`/misalignment;
over-drive → punchthrough; particles → killer defects → dead dies. These edges are *physics
wired through the state*, not scripted sad-faces — that is what makes it a simulation.

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
- **G2 — Czochralski + Scheil + boule→batch.** The first new physics, in chip-sim: the
  **Scheil** equation (the verifiable front-of-line win — see §7), the boule with axial
  resistivity variation, slicing into a wafer batch where each wafer starts different; wire
  resistivity into the device readout.
- **G3 — Wafer prep + particles + the die map made physical.** Defect events placed at
  locations on the across-wafer map; killer-defect functional yield; geometry (TTV/bow)
  bookkeeping.
- **G4 — Silicon purification + the contamination field.** The residual-impurity field, wired
  to `D` and lifetime downstream — the longest-range propagation edge.
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
  `k→1` limit and the conservation integral, not a number near the tail. Purification, etch,
  and packaging are **flagged phenomenology** — honest, calibrated, scope-edge named.
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
