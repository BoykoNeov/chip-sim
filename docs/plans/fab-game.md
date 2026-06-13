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
  > **G2 BUILT (2026-06-12).** `chip/czochralski.py` — Scheil `C_s(z)=N_seed·(1−z)^(k−1)`
  > (**seed-end** parameterized so the `z=0` slice is `1e17` *exactly* → the `demo_device` seam
  > survives), cited Trumbore `k` (B 0.80 / P 0.35 verified), the boule + axial resistivity (reusing
  > the Masetti `μ(N)` of `junction.py`), triad-tested (`test_czochralski.py`, 12). Wired into
  > `fab_game` (`CzochralskiKnobs`; `channel_N_A` is now a boule-slice **property**; `run_batch` down
  > the boule); banked artifact `fab_game/demo_boule.py` — the Scheil V_t walk (0.547→0.747 over
  > z=0→0.9) scraps the boule tail purely from substrate doping. **Oxygen→thermal-donors was
  > DEFERRED** to a fenced G2 follow-on / G4: its `k` is contested (~0.25–1.4) and the donor kinetics
  > are calibrated, so folding it into the same module would borrow Scheil's tight anchors for a loose
  > number (advisor). Fast lane 314→**338** (+24); no engine amendment, no ADR, no chip gallery card.
- **G3 — Wafer prep + particles + the die map made physical.** Defect events placed at
  locations on the across-wafer map; killer-defect functional yield; geometry (TTV/bow)
  bookkeeping.
  > **G3 BUILT (2026-06-13).** New cited physics `chip/wafer_prep.py` — the **defect-limited yield
  > law** `Y = exp(−D₀·A)` (Murphy/Poisson; Stapper negative-binomial `(1+D₀A/α)^(−α)` as the
  > `α→∞` limit + named clustered-placement scope edge) + exact geometry (slice→lap/CMP →
  > thickness/TTV/bow), triad-tested (`test_wafer_prep.py`, 14: `Y(0)=1` exact + `α→∞`→Poisson;
  > area-additivity `Y(A₁+A₂)=Y(A₁)·Y(A₂)` conservation; cited `D₀` band). Wired into `fab_game`:
  > `fab_game/defects.py` scatters killers as a **per-die Poisson** process (= the global wafer
  > scatter restricted to each die's cell, by the Poisson restriction property) against the
  > **single** `state.die_area_cm2` the closed form also uses; a killer defect is a **functional**
  > fail (distinct from a litho refusal); wafer-level **geometry scrap** gate (`GeometrySpec`) +
  > `rework_polish` (re-CMP eats thickness). Banked `demo_wafer_prep`/`fab-game-g3.png` — the
  > particle map + the empirical yield **converging to the cited Poisson law** + the TTV scrap/re-polish.
  > Default `defect_density=0.0` (clean line) so the seam + the G1/G2 demos are byte-for-byte
  > unchanged. Fast lane 338→**369** (+31); no engine amendment, no ADR, no chip gallery card.
- **G4 — Silicon purification + the contamination consequence model (§5a).** **Segregation
  purification** as real physics (Pfann zone-refining `C/C₀ = 1−(1−k)e^(−kx/L)` + cited `k`; the
  *grade knob* for the Siemens route). Then the contamination buckets wired to their
  consequences: dopant & Na ride the existing flow (Tier 1); the **Tier-2 device output** — a new
  `lifetime.py` (SRH `τ(N_metal)` + junction leakage) — lands the metals' effect that net doping
  can't carry. Gettering/precipitation stays a named edge (Tier 3).
  > **G4a BUILT (2026-06-13).** Split along the plan §7 tight/loose boundary (advisor): **G4a = the
  > verifiable purification physics + Tier-1 consequences**; the loose Tier-2 SRH `lifetime.py` is the
  > fenced **G4b** follow-on. New cited physics `chip/purification.py` — the **Pfann single-pass**
  > zone-refining closed form `C(u)=C₀[1−(1−k)e^(−k·u)]` (`u=x/L`), reusing czochralski's one
  > `SEGREGATION_K` table (Na added there), with a full triad: tight `k→1≡C₀` (bit-exact) + the
  > `C(0)/C₀=k` scrubbing identity + steady-state `C→C₀`; **conservation REFRAMED** — the single-pass
  > formula omits the final-zone pile-up, so `∫C` falls *short* of the charge by exactly the closed-form
  > swept-out deficit `(C₀/k)(1−k)(1−e^{−k u})` (verified numerically first; "mass recovers C₀" is the
  > **named edge**, *not* claimed — unlike Scheil); benchmark = the cited Trumbore `k` + flagged
  > `FEEDSTOCK_GRADES` (MGS/solar/EGS/clean). `chip/device.py` **lifts the named `Q_ox=0` edge**
  > (`ΔV_FB=−Q_ox/C_ox`, default 0 → byte-unchanged seam; D_it still out). Wired into `fab_game`:
  > `PurificationKnobs(grade, zone_passes)` → a wafer-level `Contamination` vector (uniform across the
  > die map, like `slice_z`); **Na → gate-oxide `Q_ox` → V_t down** (the headline) and **residual B/P →
  > net doping** (folded into `effective_channel_N_A`); deep-level **metals ride along, scrubbed, with
  > NO consequence yet** (the G4b gap). Banked `demo_purification`/`fab-game-g4.png`: the scrubbing
  > contrast (Fe ×8e-6 vs B ×0.8 in one pass) + a dirty **MGS feed → residual Na → V_t crashes to 0.374
  > → wafer scrapped on V_t**, the trail naming the contamination; **rework = more zone passes** (2nd
  > pass scrubs the Na → V_t recovers, residual boron persists). Default `grade="clean"` → clean vector
  > → the G1/G2/G3 demos byte-for-byte unchanged. Fast lane 373→**400** (+27); no engine amendment, no
  > ADR, no chip gallery card.
  >
  > **G4b BUILT (2026-06-13).** The deferred Tier-2 output, landing the deep-level metals' device
  > consequence net doping cannot carry. New cited physics `chip/lifetime.py` — the **Shockley–Read–Hall**
  > recombination centre: `1/τ = 1/τ_bulk + Σ σ_n·v_th·N_metal` (the p-type low-injection limit, so the
  > **electron** cross-section governs) + the generation-limited junction reverse leakage
  > `J_gen = q·n_i·W/(2τ) ∝ 1/τ ∝ N_metal`, triad-tested (`test_lifetime.py`, 12). The **tight legs are
  > the SRH machinery, not the magnitudes** (plan §7 loose tier): the analytic leg is the *low-injection
  > reduction of the full `U(n,p)` statistics* — `σ_p` and `E_t` drop out, leaving `σ_n` (a closed-form
  > limit, like Czochralski's `k→1`, not solver-grade independence); the conservation leg is **detailed
  > balance** `U=0` at `p·n=n_i²`, exact for *any* parameters; the benchmark (cited Sze/Graff capture
  > cross-sections, the clean-FZ `τ~ms`/`[Fe]~1e12→µs` order) is **flagged loose**. Wired into `fab_game`:
  > the contamination's **Fe/Cu → `chip.lifetime.device_leakage` → a new die leakage field → an optional
  > leakage spec window** (computed *inside* `device_step`, so the provenance/bookkeeping is unchanged;
  > the metals **never touch `V_t`/`I_Dsat`**). A new flagged `"metal"` feedstock grade (Na/dopant-clean,
  > metal-laden) **isolates the story**: one pass → `V_t` reads fine but leakage blows the window → the
  > wafer is scrapped on **leakage**, the trail naming deep-level-metal SRH (vs G4a's Na→V_t). The single
  > binding calibration — solar-grade's once-refined residual Cu (~2e12) must clear the 10 nA/cm² window —
  > holds with margin; rework = more zone passes (the tiny-k metals scrub by `k²`/pass → one extra pass
  > recovers lifetime/leakage). Banked `demo_lifetime`/`fab-game-g4b.png` (τ/leakage scaling | the isolated
  > metal kill | the rework). Default `grade="clean"` ⇒ `τ=τ_bulk` + baseline leakage ⇒ the seam + the
  > G1–G4a demos byte-for-byte unchanged. Fast lane 401→**423** (+22); no engine amendment, no ADR, no chip
  > gallery card. **Tier-3 (gettering/precipitation, oxide breakdown) stays the named edge.**
- **G5 — Etch / deposition / CMP.** The missing mid-line operations (phenomenological, honest).
  > **G5 BUILT (2026-06-13).** The mid-line step between litho and the device, the plan's **flagged-
  > phenomenology** tier (§7). New cited physics `chip/etch_deposition.py` — two sections: **(1)
  > pattern-transfer etch** — anisotropy ``A`` → etch bias ``2·(1−A)·h·(1+OE)`` shrinks the resist CD
  > into the gate CD (over-etch deepens the etch → widens the undercut → CD ↓), with the over-etch
  > underlayer loss ``OE·h/S``; **(2) deposition step coverage** — a keyhole void when the gap aspect
  > ratio ``h/(pitch−CD)`` exceeds ``AR_crit = SC/(1−SC)`` (a poor PVD voids the gap a conformal CVD
  > fills). Triad (`test_etch_deposition.py`, 14): **the one genuinely tight leg is the bit-for-bit
  > seam** (``A=1`` ⇒ bias 0 for any film/over-etch; ``SC=1`` ⇒ never voids), the bias/underlayer/AR
  > algebra is **machinery (regression guards), not a conservation anchor** (advisor: there is no
  > only-possible-law content here, unlike wafer-prep area-additivity / SRH detailed balance), and the
  > magnitudes (anisotropy, step coverage, the pinch-off AR) are **flagged house numbers** — only the
  > cited *forms* (Wolf & Tauber; Plummer–Deal–Griffin; Campbell) and the band orderings are asserted.
  > **CMP planarization is named and DEFERRED** (advisor: no device consumer in the compact model — its
  > real consumers, dishing→metal-opens and planarity→next-litho focus budget, are unwired, and TTV→focus
  > is *already* a named `wafer_prep` edge; don't let "(+ CMP)" pull filler in). Wired into `fab_game`:
  > `EtchDepositionKnobs` (default = perfectly anisotropic + conformal = the seam) + an
  > `etch_deposition_step` inserted **after litho, before device** that **overwrites `cd_nm`** (the
  > device reads the etched gate CD — the propagation needs no device change) and gates the gap-fill on
  > conformality vs the gate aspect ratio (a **void → a functional kill**, parallel to a killer particle).
  > The aspect ratio is **derived from the inherited gate geometry** (height + ``pitch−CD``), a genuine
  > propagation. The optional etch-rate non-uniformity is a **conditional 4th RNG draw** (only fires when
  > its σ>0, drawn last → the G1–G4 banked demos are byte-identical — the advisor's trap). Two graceful
  > degradations (degrade, don't crash): an unresolved litho image passes through to the device's refusal,
  > and a runaway over-etch that would consume the whole line is a functional kill. New `rework_deposition`
  > banks the plan's **reworkable/irreversible contrast** — a depo void is strippable (re-deposit
  > conformally → recovers), the etched CD is irreversible (a perfect re-fill can't undo it). Banked
  > `demo_etch`/`fab-game-g5.png` (the over-etch CD walk out of window | the PVD-voids/CVD-fills map | the
  > rework contrast). Default knobs ⇒ the seam ⇒ G1–G4 demos byte-for-byte unchanged. Fast lane 423→**451**
  > (+28); no engine amendment, no ADR, no chip gallery card.
- **G6 — Packaging & test & binning.** The back-end assembly yield + parametric/functional test.
- **G7 — Roguelike framing + scoring + a Textual TUI; sandbox mode.** The game shell over the
  proven sim. (Tycoon deferred — same harness, different objective.)

### 6a. Crystal-growth deepenings (G2 follow-ons — deferred; detailed when their time comes)

Three refinements of the Czochralski step (§5 step 2) — the directions a *"crystal-growth
simulator"* framing points at (heat diffusion, the crystal interface, pull rate → defects). Each
is **already fenced today as a named scope edge** (in `chip/czochralski.py` / §8); parked here so it
has a home and a cited model, **not yet detailed**. Ordered by feasibility against the repo's bar —
*a cited model + a validation triad + a real device/yield consumer, not physics for its own sake*:

- **CG-1 — Pull rate → effective segregation `k_eff(v)` (Burton–Prim–Slichter).** The easy win,
  and *already* `czochralski.py`'s #1 named scope edge. A diffusion boundary layer at the interface
  makes the *effective* coefficient `k_eff = k₀ / [k₀ + (1−k₀)·e^(−v·δ/D)]` rise toward 1 with pull
  rate `v` (`δ` = boundary-layer thickness, set by rotation). Cited **Burton–Prim–Slichter, J. Chem.
  Phys. 21:1987 (1953)**. **Fits inside the existing `Boule`/`CzochralskiKnobs` consumer** — `k_eff`
  replaces the equilibrium `k` in the Scheil profile, turning *pull rate* into a live knob that moves
  the axial doping (and the V_t walk the G2 demo already exploits). Fidelity **Mid**: `k₀` stays the
  tight Trumbore anchor, the `v`-dependence (via `δ`) is the calibrated leg. **No engine touch, no
  ADR** — closed form, consumer-side, like Scheil itself.
- **CG-2 — Voronkov `V/G` point-defect / void criterion (the unifier).** The high-value one: it
  ties **pull rate**, the **thermal gradient** (the "heat diffusion" bullet), and **crystallographic
  defect formation** into one mechanism. The ratio of pull rate `V` to the axial thermal gradient `G`
  at the interface, against a critical `ξ_t ≈ 0.13 mm²/(K·min)`, decides the grown-in regime:
  `V/G > ξ_t` → **vacancy-rich** (voids / COPs), `V/G < ξ_t` → **interstitial-rich** (dislocation
  loops; the OSF ring sits at the V/I boundary). Cited **Voronkov, J. Crystal Growth 59:625 (1982)**.
  **Where heat earns its place:** `G` is the interface thermal gradient — supplied as a knob or from
  the **already-shipped heat-mode engine** (`Robin` convective BC; see `test_robin_heat.py` — no new
  engine physics). **Consumer:** defect type → gate-oxide-integrity degradation → a **killer-defect
  yield hit that plugs straight into the G3 defect map** (`fab_game/defects.py`). Fidelity **Mid**:
  the criterion is clean/cited; `ξ_t` and the void→GOI→yield mapping are the loose/flagged leg. **No
  new engine physics** (algebraic criterion + the existing heat mode); no ADR unless a dedicated
  thermal solve is added.
- **CG-3 — Stefan moving-interface solidification (the honest hard one).** The actual solid–liquid
  front — latent heat, the interface position/shape, facets — as a **free-boundary (Stefan) problem**:
  `L·ρ·dX/dt = k_s·(∂T/∂x)|_s − k_l·(∂T/∂x)|_l`, the front `X(t)` advancing against the heat-flux
  jump. This is the **one item that is genuine new *engine* physics**: a moving boundary with a
  phase-change source, which the parabolic engine does not do (the `MaskedSurface`/`Robin` BCs are
  fixed-domain). There is a lighter precedent — v1.2 oxide growth handled a moving boundary
  **consumer-side** with a receding mesh — but a faithful Stefan solve would likely warrant an
  **engine amendment + ADR**. **Deferred behind a named consequence:** build it only when a
  device/yield outcome needs it (interface shape → facet/striation → resistivity striations or
  micro-defects), per the repo's anti-over-build rule (the "build explicit, *not* 2-D" lesson — no
  regime without its named consumer). Fidelity **Low/flagged**; engine: **likely an ADR**, unlike
  CG-1/CG-2.

**The synergy (why these three, in this order).** CG-1 makes pull rate move the *doping*; CG-2 makes
the *same* pull rate (plus the heat field) move the *defect type* and feed yield; CG-3 is the
underlying front both ride on — and the only one that pays an engine-physics cost, so it waits.

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
- **The unit of a roguelike run — one wafer/slice vs one boule/batch. → RESOLVED at G2
  (2026-06-12).** The synced answers *single-wafer roguelike* and *boule→batch* were in tension: do
  you follow one slice at axial position `z` (the boule just sets your starting resistivity), or
  process the whole batch (which leans tycoon)? A pedagogical wrinkle rode on it — Scheil's payoff is
  seeing resistivity vary *down the boule*, which a strictly single-wafer view never shows. **The
  reconciliation built is the one this bullet anticipated: the unit of a run is one wafer at axial
  `slice_z`** (a `CzochralskiKnobs.slice_z` field; the boule is *shared context* that sets that
  wafer's starting substrate via the `channel_N_A` Scheil-slice property). The boule→batch view is
  **`run_batch`** — an analysis/demo sweep down the boule that surfaces where each slice sits on the
  Scheil curve (the `demo_boule` artifact), **not** the roguelike loop. So "single-wafer run, but
  surface where your slice sits on the boule's Scheil curve" is realized: single-wafer stays the
  unit; the batch is a view. (The axial boule story is per-wafer, so it composes orthogonally with
  the radial die-map story; G1's "diffusion once, broadcast" survives within each wafer.)
- The exact `WaferState` schema and the die-grid resolution (how many sites per wafer).
- The spec-window source — cited where possible (device targets), house numbers where not.
- The variation-magnitude defaults (the stochastic layer's σ's) — cited vs calibrated-flagged.
- The pipeline representation (an explicit step list vs a small state machine) and how rework
  re-enters it.
- Where the seeded RNG lives so determinism + reproducible roguelike seeds are both clean.
