# Plan — F5 strained silicon (the term the process never touched)

> **STATUS: PLANNED (2026-08-10).** Roadmap card `F5` (`chip/roadmap_gallery.py:88`) is live and stays up
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
  mobility enhancement, and its cited **drive-current** enhancement. The elasticity bound (trap #1) is
  **part of S1's API surface**, not a later correction: the module should make it hard to read a
  drive-current number without meeting the bound. `device.py` untouched. Pure, cited, unit-tested.
- **S2 — the game knob.** `DeviceKnobs.strain` (`None` = seam) resolved at `steps.py:380`, where the
  `saturation_current` call already sits next to `R_series_ohm` and `C_ox` — no new step invented (there is
  no strain step, and inventing one would claim more than F5 models; the F4 knob precedent). Composes with
  F4's `DelayBins` for free: the strain win is damped by exactly `1 − wire_share`, which is the first time
  the game prices one era's gain against another era's wall.
- **S3 — the B10 history mode + demo.** The 10th timeline rung. The era contrast is the **fork**: one node,
  two processes, opposite signs, because the carriers disagree. **Gallery/manifest note:** both manifests
  are glob-anchored — the demo file and its rungs must land in the **same commit** or
  `assert_manifest_complete()` fails (F3 slice 3's trap, re-hit at F4).
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

## Open questions (to settle before/at S1)

1. **Where the elasticity bound lives in the API.** A returned `(mobility_factor, drive_factor_bound)`
   pair? A function that refuses to hand back a drive number without the bound attached? The requirement is
   that reading only the optimistic number should take *effort*, not be the default path.
2. **Does the registry carry the cited drive-current enhancements as data** (allowing the module to expose
   the measured ≈0.5 elasticity as a **cited cross-check** on its own bound), or are those demo-only?
   Leaning: carry them — it makes the bound self-documenting and gives S1 a non-circular check, which is
   the leg F4's IBM ~40% comparison could not supply.
3. **Does S3 need a `strain_history.py` wrapper, or does the demo ride `strain.py` directly?** The B7/B8/B9
   precedent says **ride the base module** when the period physics is already in it — and here both era
   mechanisms are registry entries, so almost certainly no wrapper.
