# Plan — F5 strained silicon (the term the process never touched)

> **STATUS: S1 + S2 + S3 BUILT (2026-08-10); S4 uncommitted.** Roadmap card `F5`
> (`chip/roadmap_gallery.py:88`) is live and stays up
> until the last slice ships (the F3/F4 graduation rule). Predecessor F4 (BEOL interconnect) completed
> 2026-08-10 and **F5 is the head of the promotable queue** (`future-steps.md:67`).
>
> **Scope note on the name.** The roadmap card is titled *"SiGe strained source/drain"*, which is the
> **pMOS** half of the strain era. The simulator has no p-MOSFET (`device.py:9` — "textbook long-channel
> n-MOSFET, p-type substrate"; no polarity switch exists), so the plan is titled *strained silicon* and
> the carrier fork below is the first thing it settles. SiGe is fully present — as cited data and as the
> demo's contrast — but it is **not** the leg that reaches `I_Dsat`.

## The discriminating observable, stated first (the build's licence)

`I_Dsat = ½·µ·C_ox·(W/L)·(V_GS − V_t)²`. Every factor on the right has been a **process outcome** since
Phase 4 — except one:

| Factor | Set by | Since |
|---|---|---|
| `C_ox` | the oxide furnace (P2), then the dielectric (F3) | P2 / F3 |
| `W/L` | the litho CD (P3) | P3 |
| `V_t` | channel doping (P1a), `Q_ox` (G4a), the adjust implant (F1) | P4 / F1 |
| **`µ`** | **nothing. `MU_N_EFF = 450.0`, a module constant flagged "illustrative"** (`device.py:438`) | **never** |

**F5 makes the channel material itself a process outcome.** Strain is a *mechanical* state, not a chemical
one — so this is the first time a device number in the sim moves without changing a dopant, a thickness,
or a length. That is the observable the current model cannot produce, and it is why F5 clears the bar.

## The seam — and it already exists

`saturation_current(mos, V_GS, width_um, mu_eff=MU_N_EFF, R_series_ohm=0.0)` (`device.py:441`).
**`mu_eff` has been a defaulted parameter since P4.** F5 does not add a seam; it *uses* one that was
written before the slice existed. So:

| State | `mu_eff` passed | vs today |
|---|---|---|
| **knob absent (default)** | not passed → `MU_N_EFF` | **byte-for-byte identical** ← the seam |
| **`strain="tensile_cesl"`** | `MU_N_EFF · enhancement` | the 2003 nMOS rung |

**`device.py` stays untouched — the fourth consecutive slice** (F2 rode `R_series_ohm`, F3 rode the EOT
identity, F4 read `I_Dsat` as a loose scalar). The house discipline holds without an argument.

**Scoped honestly: "the seam predates the slice" is a claim about `device.py`, not about the game wiring.**
S2 still has to resolve a knob to a number at `steps.py:380`, which today passes `R_series_ohm=` only — so
it costs a `DeviceKnobs` field, a resolution branch, and a `None` path that reproduces the prior value
exactly. That is precisely the shape of the F2 block sitting immediately above it (`steps.py:371–379`).
Cheap, and it still leaves `device.py` alone — but **not free**, and the plan should not read as if it were.

**Mechanical, and it is a real trap:** do **not** rescale `MU_N_EFF` in place. `test_device.py:300`
computes `beta = 0.5 * dev.MU_N_EFF * m.C_ox * (W/L)` **by hand** to pin the source-degeneration
quadratic; mutating the constant silently re-baselines that test instead of failing it. Multiply and pass.

## The carrier fork — DECIDED (the API-blocking question)

The era's two mechanisms want **opposite strain signs**, because electrons and holes respond to opposite
stresses. The simulator has only the n-channel device. Three options, and why two lose:

- **Add a pMOS to `device.py`.** This is F5 becoming *"add CMOS to the simulator"* — a whole device
  front-loaded before the slice says anything about strain. Rejected on scope.
- **Compute the SiGe pMOS drive current anyway.** Rejected as decoration. F4's three-rung seam had a
  middle rung where a *real* quantity was emitted and read by no one; a p-channel drive current for a
  p-channel device that does not exist is not that — it is a number with nothing behind it.
- **✅ Make the module carrier-generic and return a mobility ENHANCEMENT FACTOR.** An enhancement factor
  is a **material/carrier property, not a device output**, so the hole entry is honest cited data with no
  p-MOSFET required. The registry carries both signs; the *wired* leg is the carrier the sim has.

**So: the wired leg is nMOS tensile** (the tensile nitride capping layer — historically correct, same node,
same technology). **SiGe stays fully present** as the compressive twin in the registry and as the demo's
contrast, and *"the two carriers want opposite strain signs, so the strain era needed two different
processes"* is the era's actual answer and the slice's cleanest teaching point.

**The sourcing-bar worry does not materialize** (it was worth checking — an unwired leg sourced *better*
than the wired one would be an awkward inversion). Both legs come from the **same Intel 90 nm paper**.

## Trap #1 — the magnitude trap, and the primary source hands us the number

This is the F5 analogue of F4's sign trap, and it is the single most important thing in this plan.

`saturation_current` is **explicitly long-channel**, so it carries `I ∝ µ` — a µ→I elasticity of **1**.
The 90 nm strain-era device is **velocity-saturated** (`I_Dsat ≈ W·C_ox·v_sat·(V_GS − V_t)`, and `v_sat`
is nearly strain-independent), so the real elasticity is well under 1. The model will therefore
**overstate the drive-current win**, and the overstatement is not a hand-wave — the cited source measures
it on both carriers:

| Carrier | Mechanism (Intel 90 nm) | Mobility | Drive current | **Elasticity** |
|---|---|---|---|---|
| holes (pMOS) | SiGe S/D, **17% Ge**, uniaxial compressive | **>50%** | **+25%** | **≈ 0.5** |
| electrons (nMOS) | tensile nitride capping layer | **+20%** | **+10%** | **≈ 0.5** |

**≈ 0.5 on both carriers, from one paper.** So "the long-channel read overstates by ~2× at 90 nm" is
arithmetic on cited numbers, not an estimate the build has to defend. Report the coincidence **as a
coincidence** — two mechanisms landing on the same ratio is not a law, and a second source has
**100% mobility → 35% drive** at L = 25 nm, i.e. the elasticity **degrades further as `L` shrinks**.

**How to handle it (the F4 discipline):**

1. **Headline the mobility, not the drive current.** µ is what strain actually buys; the drive current is
   what a long-channel model *infers* from it.
2. **Label the drive read an explicit upper bound with its direction named** — velocity saturation
   named-not-built, exactly as F4 named repeater insertion and low-κ.
3. **Do NOT add an elasticity knob defaulting to 1.** That is inflating an unrelated variable to buy back
   a number the model has not earned — the fudge shape [[gradual-failure-preferred]] rejects. The bound is
   a *documented limit*, not a tunable.
4. **Bound it at S1.** F4's S1 shipped an unbounded headline, the review forced a retraction, and S2/S3/S4
   all inherited the correction. Pay it up front this time.

## Trap #2 — biaxial ≠ uniaxial, and the obvious caveat is the wrong one

The tempting caveat — *"strain enhancement erodes at the high vertical fields scaled devices run at"* — is
a **biaxial** result and does **not** transfer. Intel's uniaxial S/D strain explicitly survives it:
*"the hole mobility enhancement is present at large vertical electric fields in nanoscale transistors,
making this strain technique useful for advanced logic technologies."* Importing the biaxial caveat would
be recalling instead of citing — the exact failure the F3 verification ledger exists to prevent. **The
registry entries are uniaxial; say so, and do not carry a field-dependence the sources deny.**

## Trap #3 — the F4 composition is the payload, and it must stay prefactor-free

F4 proved `∂ln f/∂ln I_Dsat = 1 − wire_share`, **exact at every `I_Dsat`**, not a linearization. F5 is the
first slice that gets *priced* by a previous slice's law: strain buys drive current, and the wire keeps a
fixed fraction of it. The arc is real — **the era that made transistors faster arrived after wires had
started setting the clock** — and it composes with trap #1 into the honest chain:

> +20% mobility → **at most** +20% drive current (long-channel bound; ~+10% measured) → **×(1 − wire_share)**
> on chip speed.

**But do not compute a 90 nm `wire_share`.** `interconnect.py`'s bulk path is bulk-ρ only and
`bulk_regime_ok` refuses below ~0.194 µm — 90 nm is *deep inside that refusal*, so a 90 nm number needs
S4's narrow-wire path, not the bulk one. **State the damping as the exact law, not as a figure.** (This is
F4's own S3 lesson: the cap is binding, not cosmetic.)

## Verification ledger (web-verified 2026-08-10 — the F3/F4 discipline: cite, don't recall)

**VERIFIED (Intel 90 nm logic technology, IEDM 2003 / the associated papers — both legs, one source):**
SiGe S/D selective epitaxy → longitudinal **uniaxial compressive** stress → hole mobility **>50%** ·
**17% Ge** in the S/D · tensile silicon-nitride capping layer → **tensile** strain in the nMOS → electron
mobility **+20%** · saturated drive currents **+10% (nMOS)** and **+25% (pMOS)** · record pMOS drive
**700 µA/µm** (high `V_t`) / **800 µA/µm** (low `V_t`) at 1.2 V · the hole-mobility enhancement **persists
at large vertical fields**.

**VERIFIED (independent, and it is the bound's direction):** at short/narrow geometry (L = 25 nm,
W = 77 nm) a **100%** long/wide mobility enhancement yields **35%** saturation drive enhancement — the
µ→I elasticity **falls with `L`**, and strain increasingly acts through *injection velocity* rather than
mobility in the quasi-ballistic regime. ⇒ the long-channel elasticity of 1 is an **upper bound whose
looseness grows** as the era advances. Named-not-built.

**VERIFIED (the successor arc):** dual stress liner — compressive CESL over pMOS, tensile CESL over nMOS —
is the generalization of the 90 nm pair, with ~10% / ~17% performance gains reported. The CESL route is a
**named** later rung, not a second registry entry to build at S1.

**FLAGGED / verify at build:** the compressive stress in **GPa** for a given Ge% (the roadmap card says
"~2 GPa @ 20% Ge"; the searches returned Ge% and mobility but **not** a pinned GPa figure — so a
stress→mobility *function* is not yet sourced at the bar this project uses) · whether mobility enhancement
vs Ge% is linear over the useful range · the biaxial "up to 100% hole-µ" figure on the roadmap card is a
**range top** under a *different* (biaxial) strain type — **do not headline it**.

**HOUSE LUMPS (name them like F4's `L` and F2's `CONTACT_LENGTH_UM`):** `MU_N_EFF = 450.0` itself, which
F5 *inherits* rather than fixes — every F5 number is a **ratio against it**, which is exactly why the
headline must be an enhancement factor. A ratio cancels the lump; an absolute µ does not.

## Live finding — the published roadmap card states a gate this plan just falsified

Planning F5 falsified the F5 card's own text, on the **published** page. This is precisely the failure mode
F4's S4 named: *the golden-HTML currency tests confirm the prose did not **change**, never that it is still
**true***. Three claims are now wrong or unsourced, in `roadmap_gallery.py:88` and stamped **into the
schematic image** by `roadmap_figures.py:87–115`:

| Where | Claim on the page | Status |
|---|---|---|
| card `gate=` + figure caption | *"a strain-aware mobility model µ(strain) in `device.py` — **none exists yet**"* | **FALSE.** `saturation_current(..., mu_eff=MU_N_EFF)` has been a defaulted argument since P4. The gate is **lifted**, and `device.py` needs no change at all. |
| figure caption | *"hole mobility µ↑ (**up to ~2× at ~20% Ge**)"* | **Range top, wrong strain type.** ~100% is the **biaxial** figure; the cited uniaxial S/D result is **>50% at 17% Ge**. F4's `floor_decades` rule in µ's currency: never round a win up. |
| figure body | *"compressive strain **~2 GPa**"* | **Unsourced at this project's bar** — the searches returned Ge% and mobility, not a pinned GPa figure. |

**This is an S1 task, not a later cleanup**, and it is the *second* card whose gate turned out to be
already released by prior work (F8's was released by F4's build). Fixing it touches the drawing, the card,
the regenerated PNG and **both** HTML editions (`python -m chip.roadmap_figures`, then
`python -m chip.roadmap_gallery`) — an outward-facing change, so it lands deliberately rather than as a
side effect. **The card itself stays up until the last slice** (the graduation rule is unchanged); what
changes is that it stops claiming a gate that is not there.

**The durable lesson to carry (it generalizes past F5):** a roadmap card's `gate` is a **claim about the
current tree**, and the tree moves under it. Nothing re-checks those claims — the manifest guard pins
card↔schematic and the golden tests pin page↔renderer, but **no test pins gate↔reality**. Both times a gate
has been re-examined (F8, F5) it had already been released.

## Slices (resist front-loading — S4 is deliberately not pre-committed)

- **S1 — `chip/strain.py`.** Carrier-generic mobility enhancement: a registry of cited strain mechanisms
  (`tensile_cesl` → electrons; `sige_sd` → holes), each carrying its sign, its mechanism, its cited
  mobility enhancement, **and its cited drive-current enhancement** (open question 2, decided below). The
  elasticity bound (trap #1) is **enforced by a test, not by API shape** — see open question 1. `device.py`
  untouched. Pure, cited, unit-tested. **Also S1: the falsified roadmap card** (the section above).
- **S2 — the game knob. ✅ BUILT 2026-08-10.** `DeviceKnobs.strain` (`None` = seam) resolved at the
  `saturation_current` call, which already sat next to `R_series_ohm` and `C_ox` — no new step invented
  (there is no strain step, and inventing one would claim more than F5 models; the F4 knob precedent).
  `device.py`, `spec.py` and `state.py` all untouched. What the build settled and found:
  - **The knob passes the seam value rather than branching around it.** `strained_channel(MU_N_EFF, None)`
    returns `MU_N_EFF` exactly, and that *is* `saturation_current`'s own default — so one call site, and
    **every default run exercises `chip.strain`'s seam on every die** (`test_seam.py`'s
    `d.i_dsat == demo_device.compute().i_dsat` is now standing proof of it). A branch would have left that
    path untested from the consumer side. The `strain.py` docstring clause promising the opposite is fixed.
  - **THE STRUCTURAL BREAK — the first knob here that is not additive.** `bv_V`, `t_rr`, `j_gate`, `τ_total`
    each bolt a *new* output onto an unchanged device, so engaging one alone changes nothing scored; F4
    needed the **pair** (knob + delay binning). Strain moves `I_Dsat`, which `SpeedBins` has graded since
    G6, so the knob **alone re-grades the wafer with no new scoring surface at all**. That is a property of
    strain being a *process* change to a *device term*, not a new reading beside one.
  - **And the re-grading is a statement about the LADDER, not about sorting.** Strain is common-mode and
    **multiplicative**: every die by exactly the same factor ⇒ the coefficient of variation is unchanged and
    the rank order is exactly preserved. The **mirror of F4**, whose common-mode τ_wire was *additive* and
    therefore *compressed* the relative spread. At the G6 ladder the whole graded population lands on
    `premium` — because the level moved under fixed edges, not because the line learned to sort.
    **The control that proves there is nothing else in it** (F4's `τ_wire = 0` identity, in F5's currency):
    scale the `I_Dsat` window *and* every bin edge by the same factor — what a fab does when it qualifies a
    new process — and the wafer comes back **grade for grade and verdict for verdict identical**. So both
    game-level effects are a level shift and nothing more; the construction puts no thumb on the scale.
  - **THE UNCOMFORTABLE HALF (recorded, not tuned away): the win costs yield against a window written before
    it existed.** `DEFAULT_SPECS`'s `I_Dsat` ceiling exists to catch *CD-collapse over-current* — on an
    unstrained line the only way to be 20% over-current was for the geometry to be wrong. Strain lifts the
    histogram by exactly that much with the geometry bit-for-bit correct: a loose-CD wafer goes **89/89 →
    77/89**, every loss a parametric `I_Dsat`-high fail and no new failure mode. A **spec** artefact, not a
    physical consequence; re-centring the window is a market decision (F4's binning-edge class), and
    re-centring it quietly so the slice reads better is the fudge shape this project rejects.
  - The F4 composition stayed **one test, not a panel** (F4's own S2 earned its inversion by overturning a
    *false premise sitting in the tree* — `SpeedBin`'s `f ∝ I_Dsat` docstring — and F5's S2 has none to
    overturn). Asserted as the **structural identities**, not F4's `∂ln f/∂ln I = 1 − wire_share`: that is
    an exact *derivative*, so a finite +20% step would need a tolerance and prove less. `τ_wire`
    byte-identical, `τ_gate` scaling by exactly the inverse drive ratio, speed gain strictly under the
    drive gain.
  - The realized gain is the **full factor** on the ideal-contact path (`sd_contact_squares = 0`, the game's
    default) — elasticity 1 end-to-end, which is *why* it is an upper bound — and strictly **below** it once
    source degeneration is engaged, the one sub-linearizing mechanism the model does carry. The record
    carries `mu_factor` beside `drive_factor_cited` and `drive_overstatement` so the bound travels with the
    number; the overstatement is the **mechanism's** cited ratio, not a correction applied to that die.
- **S3 — the B10 history mode + demo. ✅ BUILT 2026-08-10.** `chip/demo_strain_history.py` + its test; the
  10th timeline rung, slotted **between B8 and B6** (the timeline is process order, not chronological —
  the channel sits after the gate dielectric and before contact metal). Fast lane 1164 → 1174. What the
  build settled and found:
  - **The period is a POINT, not a curve — so the panel had to be built around that.** Every prior rung
    (B5–B9) draws a period *line* the modern one departs from; here the period is the factor `1.0`, and
    the only way to draw an unstrained channel is as the point both paths leave from. That is what makes
    the **seam** load-bearing on the figure and not just in the API: `strained_channel(MU_N_EFF, None)`
    is `saturation_current`'s own default, so the two paths start on one point *by identity*.
  - **THE WALL IS A COMPOSITION WITH B8, AND THE HONEST CLAIM IS ORTHOGONALITY — NOT AN EXCHANGE RATE.**
    The first sketch was "the oxide thinning that buys the same +20% drive costs N decades of gate
    leakage." Review killed the framing: it needs an unverified 90 nm-era `t_ox`/leakage claim, and the
    naive `I ∝ 1/t_ox` read is wrong **in the flattering direction** (thinning also drops `V_t`, so drive
    rises *faster* than `1/t_ox` ⇒ less thinning is needed ⇒ the oxide lever is **cheaper** than naive
    says). The tight claim underneath it is that `high_k.gate_leakage` takes a thickness and a
    dielectric — **mobility is not one of its arguments**, so `∂J_g/∂µ = 0` **structurally**, the exact
    shape of B9's `∂τ_wire/∂I_Dsat = 0`. F3/B8's "one thickness, two currencies" read from the other
    side: **one knob, one currency**. Pinned as a bit-for-bit identity under an *absurd* mobility, so a
    future path from µ to the gate stack fails the test instead of quietly turning a structural fact into
    a numerical coincidence.
  - **The exchange rate survives as a CONSISTENCY note, quoted in the direction that does not flatter the
    slice.** Two defensible conventions differ by ~2×: fixed channel doping (this demo's ladder — `V_t`
    sags, an 8% thinning suffices) = **≳0.90 decades**; re-adjusting `V_t` at every rung (what a fab
    does, `I ∝ C_ox` exactly) = **≳1.88**. The demo headlines the **cheap** one — the reading most
    favourable to the lever strain is being compared against — and a test pins that ordering, because
    flipping it would round F5's win up (F4's `floor_decades` rule in the leakage currency). **The band
    is recipe-carrying; strain's zero is not.**
  - **The hole leg is marked cited-only ON THE FIGURE, not just in the API.** The plan rejected computing
    a p-drive current as decoration; two bars side by side would have re-introduced exactly that read at
    the display layer. The panel captions each mechanism on **its own side of the zero** (the fork drawn
    literally), labels the hole bars `CITED DATA ONLY (no pMOS)`, and the demo **carries
    `nmos_mobility`'s raised message verbatim** rather than paraphrasing it.
  - **No wrapper** — open question 3, answered by the build: the demo rides `chip.strain` directly, as
    B7/B8/B9 rode their base modules. Both era mechanisms were already registry entries; a
    `strain_history.py` would have held nothing.
  - **The F4 composition stayed off every axis** (trap #3): stated in `print_summary` as the exact law
    `∂ln f/∂ln I_Dsat = 1 − wire_share`, with a test asserting the demo never calls `interconnect.delay`
    or `crossover_width_um` — a 90 nm line is deep inside the bulk path's refusal.
  - **Gallery/manifest note (held):** both manifests are glob-anchored — the demo file and its two
    entries land in the **same commit** or `assert_manifest_complete()` fails (F3 slice 3's trap, re-hit
    at F4).
- **S4 — NOT pre-committed.** It should fall out of what S1's sourcing turns up, the way F4's S4 did. The
  structural analogue to F3's IL and F4's axis change would be *"strain is a one-time boost, not a scaling
  path"* — which is why the industry changed the axis again to FinFET, handing off to F9 as F4 handed off
  to F8. **Candidate only**, and note trap #2 kills the most obvious mechanism for it.

**Roadmap card graduation** (`roadmap_gallery.py:88`) lands with the **last** slice, on F3's reading of
"shipped" — `SLICES` and `FIGURES` cut together (the manifest guard pins card↔schematic).

## Scope discipline (the honest NO's)

- **A p-MOSFET: NO.** The carrier fork above exists precisely so F5 does not need one. If a later slice
  wants CMOS, that is its own plan with its own consumer.
- **A stress→mobility physical model (deformation potential, band warping): NO.** The sourced quantity is
  the **enhancement factor per cited mechanism**; a GPa→µ function is not sourced at this project's bar
  (see FLAGGED), and building one would fabricate the calibration F5 is trying to avoid.
- **Velocity saturation: NAME, DON'T BUILD.** It is the mechanism that makes the drive read a bound. Adding
  it would mean replacing the long-channel `I_Dsat` — i.e. rewriting `device.py`, which four consecutive
  slices have avoided, and which is a *device-model* change, not a *process* one. It is also the F4
  "repeater insertion" analogue: the mechanism that stops the extrapolation being real.
- **Strain relaxation / defect generation / SiGe critical thickness: NAME, DON'T BUILD.** A yield/reliability
  currency, not a drive-current one — the same reason F4 kept electromigration out.
- **`device_2d.py` (lines 289–290): DECIDE, don't drift.** It calls `saturation_current` twice for the
  `L_eff` comparison. **Proposed: leave it alone** — its payload is `L_drawn` vs `L_eff`, a *geometric*
  contrast, and a mobility factor multiplies both reads identically and cancels. Recorded as a decision so
  a later reader does not read it as an oversight.
- **`I_Dsat` keeps its meaning.** `mu_eff` is passed at the read, never written back into `MOSDevice` —
  the F2 (`die.R_s`) / F3 (`die.t_ox_um`) / F4 (`τ_gate`) discipline.

## Open questions

1. **Where the elasticity bound is enforced. ✅ DECIDED — by a TEST, not by API shape.** The tempting
   framing ("make reading only the optimistic number take *effort*") asks for something the seam cannot
   give: **the wired path *is* the optimistic number.** `mu_eff = MU_N_EFF · enhancement` fed to a
   long-channel `I_Dsat` yields elasticity 1 **by construction**, and F5 is not touching
   `saturation_current` — so no `strain.py` API can refuse to produce the number that another module
   computes. Enforcement therefore belongs **where the claim is made**: a test pinning that each registry
   entry's cited `drive_factor` is **≈ half** its cited `mobility_factor`, so any later slice that starts
   treating the long-channel read as *the* drive result confronts the ratio head-on. This is F4's
   standard-form test (the one that made a convention change confront its own direction), not an API trying
   to be un-misreadable.
2. **Does the registry carry the cited drive-current enhancements as data? ✅ DECIDED — yes.** It makes the
   bound self-documenting, it is what open question 1's test asserts against, and it gives S1 a
   **non-circular cross-check** — the measured ≈0.5 elasticity is an *independent* quantity the model does
   not compute, which is exactly the leg F4's IBM ~40% comparison could not supply (that one was a
   consistency check, since `R_Al/R_Cu ≡ ρ_Al/ρ_Cu` at fixed geometry).
3. **Does S3 need a `strain_history.py` wrapper, or does the demo ride `strain.py` directly? ✅ CLOSED by
   the S3 build — no wrapper.** The B7/B8/B9 precedent held exactly as expected: both era mechanisms were
   already registry entries, so `demo_strain_history.py` imports `chip.strain`, `chip.device` and
   `chip.high_k` directly and a wrapper module would have contained nothing but re-exports.
