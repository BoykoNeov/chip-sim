# Plan — F8 CMP / planarity (the step that gave the wire a spread of its own)

> **STATUS: COMPLETE — S1 ✅ 2026-08-19, S2 ✅ 2026-09-02, S3 ✅ 2026-09-02, S4 ✅ 2026-09-06 (the roadmap card graduated with it).** Chosen off the post-F5 re-triage. Historical mode: **B11**
> (B10 = F5 strain is the current highest — `chip/demo_strain_history.py`). Roadmap card `F8` graduates
> on the last slice, on the F3/F4/F5 reading of "shipped".

## The discriminating observable, stated first (the build's licence)

F4 shipped a law and stated it sharply (`chip/interconnect.py`, `Delay.sensitivity`):

> `∂ln f / ∂ln I_Dsat = 1 − wire_share`, because `τ_wire` is a **common-mode** additive floor — it shifts
> every die's delay by the same amount and **contributes no spread of its own**.

That sentence is true of the tree **because nothing in the tree can make a wire differ from die to die**.
`fab_game/steps.py:478` reads `ic.delay(ic.WireGeometry(), …)` — a *default-constructed* cross-section,
the same `W` and `H` on every die on every wafer. The wire's zero spread is not a physical finding; it is
an artifact of there being no process step upstream of it.

**CMP is that step.** Polishing is where wire thickness is actually set, and it is set *non-uniformly* —
by where the die sits on the wafer, and by what is printed around the line. So F8's observable is:

| | today | after F8 |
|---|---|---|
| `τ_gate` | per-die (reads this die's `I_Dsat`) | per-die |
| `τ_wire` | **identical on every die** | **per-die** (its own across-wafer signature) |
| delay spread | entirely transistor-sourced | transistor **+ a wire term the transistor cannot explain** |

That is a genuinely new output: **a speed spread with a non-transistor source.** No current knob can
produce it — every existing per-die number (`V_t`, `I_Dsat`, `j_leak`, `bv`, `t_rr`, `j_gate`) is
downstream of the device, and `τ_wire` is provably not (`∂τ_wire/∂I_Dsat = 0`, enforced by construction in
`delay()`). F8 does not decorate F4's law; **it modifies its premise.**

The second observable is a failure mode, and it is the one the primary source leads with — see *the
two-sided window* below.

## The seam — and, as with F5, it is already there

`delay(geometry: WireGeometry, …)` **takes the geometry as an argument** (`chip/interconnect.py:578`), and
`WireGeometry` is a frozen dataclass with defaulted `width_um`/`thickness_um`. So:

| State | geometry passed | vs today |
|---|---|---|
| **knob absent (default)** | `WireGeometry()` | **byte-for-byte identical** ← the seam |
| **`cmp=` set** | `WireGeometry(thickness_um=post-CMP H)` | the per-die line |

**`chip/interconnect.py` stays untouched, and so does `device.py`** — F8 rides an existing parameter
exactly as F5 rode `mu_eff` and F2 rode `R_series_ohm`. The die gains one field and `steps.py` gains one
resolution branch.

### Live finding — the published roadmap card overstates F8's gate

`chip/roadmap_gallery.py` (card `F8`) says the remaining gate is that *"F4's wire geometry is a
module-level house line … so a per-die CMP variation needs the cross-section to become a per-die quantity
first"*, and `future-steps.md` calls that a **refactor** and the reason F8 heads the queue "by default
rather than by strength."

**Re-checked against the tree (the roadmap's own standing instruction, `roadmap_gallery.py:100–104`): the
gate is real but it is not a refactor.** The geometry is already a *parameter*, not a constant inlined in
`delay()`; and `Die` already carries `radius_frac`, documented as "the handle the center-to-edge variation
trend reads" (`fab_game/state.py:~99`). The work is a die field + a call-site change, which is the same
size as the F5 knob block sitting next to it. This is the **second consecutive slice whose gate was
lifted before the slice was written**, and it is worth recording as a pattern rather than a coincidence.

**Decision needed (see Open questions):** whether to correct the card text now or let it graduate.

## The primary source, and the trap in the secondary summaries

**Park, Tugbawa, Yoon, Boning, Chung (MIT EECS); Muralidhar, Hymes (SEMATECH); Gotkis, Alamgir, Walesa,
Shumway (IPEC/Planar); Wu, Zhang (Rodel); Kistler, Hawkins (Cabot) — "Pattern and Process Dependencies in
Copper Damascene Chemical Mechanical Polishing Processes", VMIC, Santa Clara, June 1998.** Retrieved and
read in full 2026-08-19 (6 pp.).

**The trap — and I walked into it before reading the paper.** Search summaries state a tidy split:
*dishing depends on line **width**, erosion on pattern **density***. It is memorable, it is the shape this
repo likes (F2's two `R_sh` exponents, F3's two currencies, F4's two terms), and **the primary source
refutes it in two places**:

* Fig. 4b — dishing vs *density* at fixed pitch is strong **and non-monotonic**: it rises to a peak at
  **60–70 %** density and then *falls sharply*.
* Fig. 6 — erosion depends on *pitch*, and the paper flags this explicitly: *"different than Steigerwald
  et al. [1] where oxide line space or pitch dependence of erosion is not observed or explored."*

Both quantities depend on both variables. Building the clean split would have been building the summary,
not the physics — the `locos-birds-beak-source.md` lesson (primary data overruled the recalled shape) and
the F5-S3 flattering-direction trap, arriving one layer earlier this time.

### Scale honesty — the part that must NOT be ported

The masks are **2–1000 µm** pitch, blocks up to **3 mm**, and the stated break point is an **oxide line
space of ~100 µm**. The sim's global wire is **250 nm**. Those are three orders of magnitude apart, and
the paper says so itself in its future work: the sub-micron electrical mask *"will enable us to explore
issues not apparent with the large features used in this study."*

⇒ **The 60–70 % density peak and the 100 µm break point are cited observations at the source's scale and
are explicitly NOT extrapolated into the model.** What the model may ride is the monotone,
repeatedly-confirmed core (dishing ↑ with width/pitch, erosion ↑ with density, total loss ≈ linear in
log pitch) and the **fractional** currency below.

### The currency that dodges the house lump

The figures report **normalized** dishing/erosion (0–1) — no absolute nanometres are recoverable. But
Fig. 8 reports **"percentage of copper removed from trenches"** directly, spanning ≈ **25–90 %** across
processes and pitches, and *"varies approximately linearly with the logarithm of the pitch."*

That is exactly the quantity `R ∝ 1/(W·H)` wants: a **fractional** thickness loss. So the module's core
read is `H_post/H_nominal = 1 − loss`, and the resistance rise is `1/(1 − loss)` — **prefactor-free**, the
F3/F4 discipline. No absolute-nm house constant is needed anywhere in the load-bearing path.

## The two-sided window — the source's own framing, and the wall

The paper's motivating paragraph, near-verbatim:

> To ensure that there is no residual copper and barrier material in the region between the trenches, and
> hence **no shorting of any two copper lines**, requires that one clears excess copper **everywhere** on
> the die and wafer. This requirement typically implies **overpolish** in some regions … leading to
> dishing of copper and erosion of oxide.

So dishing is **not a defect to be eliminated — it is the price of not shorting**:

* **Under-polish** → residual copper between trenches → **lines bridge → functional short.** (The game
  already has this failure's twin: D1's under-etch residual bridge, `fab_game` §3.)
* **Over-polish** → dishing + erosion → **thinner wire → higher `R` → higher `τ_wire` → slower part.**

Both sides are read off the *same* removal number, so there is a genuine optimum and a genuine **wall**:
as the across-wafer removal spread widens, the window closes — no single polish time clears the slow
region without over-thinning the fast one. That is the F8 headline and it is structural, not calibrated.

**Gradual, not a cliff (the [[gradual-failure-preferred]] discipline).** The short is *not* wafer-wide at
a threshold. Removal is radius-dependent, so residual copper survives only where local removal fell short
— a **fraction of dies, grouped by radius**, exactly the honest move that memory prescribes (spatial
non-uniformity of the offending quantity, never an inflated unrelated variable). The existing
`radius_frac` handle carries it for free.

## The tight leg — why the across-wafer signature is a *pressure* story

**Preston's equation** (cited; glass-polishing origin, standard in CMP): removal rate `RR = K·P·V`, linear
in down-force `P` and in pad–wafer relative speed `V`. The source's Table 1a varies exactly these
(down force 2.0 / 3.5 / 5.0 psi; platen 70 / 60 / 35 rpm) and reports that the pattern trends hold while
the magnitudes shift — i.e. the process knobs scale the curves, they do not reshape them.

**The kinematic identity (DERIVED here, not recalled — the `avalanche-breakdown-source` discipline).**
In the standard rotary configuration the platen spins at `ω_p` about `O`, the carrier spins at `ω_w` about
its own centre `C`, fixed at distance `d` from `O`. For a wafer point at `r` from `C`:

```
v_rel = v_wafer − v_pad = ω_w × r − ω_p × (d + r) = (ω_w − ω_p) × r − ω_p × d
```

At **matched speeds** `ω_w = ω_p = ω` the `r` term vanishes identically: `|v_rel| = ω·d` **at every point
on the wafer**, independent of position. (Real tools run near-matched for this reason; off-match, the
literature's kinematic models put the across-wafer velocity spread at only a few percent.)

⇒ **Preston's `V` cannot produce a centre-to-edge signature. `P` must.** The cited mechanism is the wafer-
edge contact "hot spot" — the pad is cut by the wafer edge and the local pressure exceeds the average —
plus retaining-ring pressure mismatch. This is the same shape as F4's *"the crossover is an R story, not a
C story"*: one of the two factors in the product is structurally barred from carrying the effect.

**Flagged, and flagged loudly:** the *sign and existence* of the edge effect are cited; the **amplitude**
is a house number. The source deliberately **averaged nine dies per wafer** to remove within-wafer
variation, so it supplies no radial profile at all. The radial amplitude is F8's `GLOBAL_WIRE_LENGTH_UM` /
`CONTACT_LENGTH_UM` / `SPIKE_CONCENTRATION` — a named, isolated lump, and **no headline may depend on it.**

## The honesty ladder

* **Tight — the premise change.** `τ_wire` gains per-die spread; F4's `1 − wire_share` was derived under
  "the wire contributes no spread of its own", and that clause stops holding. Structural, prefactor-free.
* **Tight — `R ∝ 1/H` exactly**, so fractional loss → `1/(1−loss)` resistance rise. No constants.
* **Tight — the two-sided window.** Clearing everywhere ⇒ overpolishing somewhere ⇒ dishing is the *cost
  of not shorting*, and the window closes as removal spread grows. From the source's own requirement.
* **Tight — the Preston kinematic identity.** `V` is exactly position-independent at matched speeds ⇒ the
  radial signature is a pressure story. Derived above.
* **Cited, monotone only.** Dishing ↑ with width/pitch; erosion ↑ with density; total trench-copper loss
  ≈ linear in log(pitch), spanning 25–90 %.
* **Cited but NOT modelled (deliberate).** The 60–70 % dishing peak and the ~100 µm break point — real,
  mechanistically explained by the source (beyond ~100 µm the oxide supports the pad load; below it the
  oxide does not, so oxide polishes fast → more erosion, *less* dishing), and **three orders of magnitude
  off the sim's feature size.** Reported in prose and the demo, never in a number that feeds a device.
* **Flagged — the magnitudes.** The radial pressure amplitude, the nominal pre-CMP copper thickness, the
  house pattern density/pitch (the sim has never carried a layout density), and Preston's `K`. Absolute
  picoseconds remain, as in F4, **not a claim this module makes.**

## Slices (F5 discipline: resist front-loading — S4 is deliberately not pre-committed)

**S1 — `chip/cmp.py`, the module. ✅ BUILT 2026-08-19** (`chip/cmp.py`, `chip/tests/test_cmp.py`, 38
tests). What it settled beyond the plan:

* **The headline closed form is `s/(1−s)`** — the overpolish the clear-everywhere requirement *forces*,
  in units of the overburden, with **no house constant**. At `s = 0` it is exactly zero: a perfectly
  uniform polish dishes nothing, at any pattern, for any time. **Dishing is bought by non-uniformity and
  by nothing else**, which is why the fix is polish *uniformity* and never polish *less* — polishing less
  does not reduce `s`, it only fails to clear.
* **The window collapses at `s_crit = L/(2+L)`**, `L ≡ loss_max·H₀/(η·t_over)`. Past it **no polish time
  exists**. `polish_window_um` returns `None` there rather than a crossed interval.
* **The scale refusal turned into the module's second finding.** Fig. 5's log-linear dishing trend
  crosses zero at ~1 µm pitch, so `dishing_efficiency` returns **exactly 0.0** for a sub-micron line —
  and therefore **at the sim's dimensions the loss is an EROSION story, not a dishing story.** Dishing is
  a wide-feature problem (pads, power rails, the source's own 3 mm blocks). This resolves the scale gap
  honestly instead of clamping through it.
* **The scale gap is two numbers, not one** (`CitedExperiment.scale_gap`): the smallest *measured* pitch
  is only ≈4× the sim's, but the break point sits ≈200–400× away. That asymmetry is precisely what makes
  the monotone legs portable and the break point not — the plan had asserted a single "three orders of
  magnitude", which was wrong for the near end and is corrected here.
* **`W` does not move** (open question #1, closed): dishing thins the copper and erosion thins the oxide
  under it; neither redefines the trench sidewalls the etch cut. `H` alone, which is also all
  `wire_resistance` needs.
* **A calibration was found and quarantined.** `DISH_SCALE` is a free multiplier — the source's dishing
  axis is *normalized*, so nothing in the paper fixes it. Set as it is, sweeping wafer non-uniformity
  7 %→20 % reproduces the cited **25–90 %** trench-loss band. **That is a calibration, not a prediction**,
  and reporting it as a cross-check would have been the F5-S3 flattering-direction trap one layer down.
  A test (`test_every_quotable_leg_is_invariant_to_the_calibrated_constant`) now asserts that no quotable
  leg moves when `DISH_SCALE` moves, with a companion test proving the constant is quarantined rather
  than inert.

*Original plan text for S1:* Preston removal; the clear-everywhere requirement; pattern-dependent
fractional trench-copper loss (monotone legs only); post-CMP thickness; the two-sided window as a closed
form (the polish range that clears residue without over-thinning). The derived kinematic identity as an
asserted invariant. No game wiring. Tests pin: the seam (zero overpolish ⇒ nominal thickness), the
monotone dependences, `1/(1−loss)` resistance, and the window's collapse as spread grows.

**S2 — the game knob + the per-die wire (the payload). ✅ BUILT 2026-09-02** (`fab_game/recipe.py`
`CmpKnobs` + `Recipe.cmp`; `fab_game/steps.py` `cmp_step` + the device-step read; `Die.metal_thickness_nm` /
`shorted` / `polished_out`; two verdict gates; the pipeline's 3c step, the damascene refusal and the
`diagnose` branch; `chip/cmp.py` §5 the radial pressure chain; `fab_game/tests/test_cmp_knob.py`, 24
tests + 10 chip-side; fast lane 1218 → 1252). What it settled beyond the plan:

* **The earning assertion holds in its sharpest form.** With *zero* variation every transistor on the
  wafer is the same transistor — one `I_Dsat`, one `τ_gate` — and the chip delay still spreads, monotone
  in radius, because the wire under the rim was polished thinner. `1 − wire_share` is a per-die number
  now; F4's clause is gone. Measured on the wafer, not asserted from the module.
* **The seam is "no step at all", and there is a second seam inside the engaged run.** `polish_s=None`
  adds nothing to the flow (no per-die or wafer record — the bookkeeping test's step list is untouched),
  the way F4 emits no delay until `interconnect` is set. Engaged and set to the clear-everywhere time, the
  **centre die is byte-for-byte F4**: the slowest site removes exactly the overburden, so the forced
  overpolish `s/(1−s)` lands on *every other die* — the headline law seen from the wafer. And a uniform
  polish (`s=0`) at the clear time reproduces F4 on every die: the two-sided window's seam, wafer-wide.
* **The refusal is the era's teaching point, and it lives in the registry.** `chip.cmp.DAMASCENE_METALS
  = ("Cu",)`: copper cannot be plasma-etched, so damascene + CMP defines the copper line and *only* the
  copper line; aluminium is subtractively etched, so a polish there planarizes the dielectric and never
  sets the wire — the observable F8 exists for does not exist on an Al line. The pipeline refuses `"Al"`
  and `None` **by name**, the F4 (Ru) / F5 (SiGe) pattern one slice on.
* **The trench depth is not a knob.** It is `WireGeometry().thickness_um`, and the line width is
  `WireGeometry().width_um`, so the pattern density is `W/pitch` — the source's own definition — and the
  slice adds **one** house layout number (the pitch), not two. "No loss" and "the F4 wire" are the same
  number by construction rather than by agreement.
* **The short is graded by radius in closed form.** `chip.cmp.shorted_radius_frac` gives the edge `r*` of
  the centre disc that has not cleared (`r² < (t_over/R̄ − 1 + s)/(2s)`); the pipeline's shorted set is
  exactly `{r < r*}`, the shorted trench is untouched (nominal thickness — the failure is copper left
  standing *between* the lines), and shortening the polish grows the disc ring by ring, never
  nothing→everything (the [[gradual-failure-preferred]] structure, delivered by moving the offending
  quantity across the wafer). A runaway polish that removes the trench is a third, graceful outcome
  (`polished_out`: no conductor ⇒ no delay ⇒ a functional kill, not a divide).
* **Grading by position.** Anchor F4's `DelayBins.from_speed_bins` on the centre part and run a wafer of
  identical transistors: at `s=0.2` the outer 40 of 89 dies fall from `typical` to `value`, monotone
  outward, with the `I_Dsat` histogram a single value. That is a speed grade set by where the die sat
  on the polisher — the first grading signature in the game with no transistor behind it.
* **The magnitudes, flagged as they were promised to be.** At the clear time the rim loses 1.2 / 2.5 /
  5.7 % of its copper for `s` = 0.05 / 0.10 / 0.20 (delay +0.9 / +1.9 / +4.3 %). All erosion: at the house
  0.5 µm pitch `dish_loss` is *exactly* 0.0 on every die (S1's zero crossing), so the whole per-die
  spread is oxide erosion — and its lever is pattern **density**, which is what S3's successor (dummy
  fill) is about. `PRESTON_K` was re-set 1.67e-2 → 2.4e-3 so the house 3.5 psi / 1 m/s gives ≈0.5 µm/min
  and a clear at ~1 min rather than ~10 s; a rate, no headline reads it (the S1 quotable-leg invariance
  test still passes untouched).
* **A numerical knife-edge, closed.** The clear time is a boundary (residual 0, overpolish 0) reached
  through `K·P·V·t` float arithmetic; a 1e-17 µm residual is rounding, not copper, and would have read as
  a functional short. `cmp_step` snaps a removal within float tolerance of the overburden onto it.
* **Step order is readout order.** CMP runs after the gate etch and *before* the device step, because the
  device step is where `τ_total` is computed and the wire it reads has to exist — the device step is the
  readout of the finished wafer, not the transistor's chronology. Litho rework re-reads the same polished
  wire (die state), which is also what a strip-and-re-expose physically does.

*Original plan text for S2:* `cmp` knob; `Die.metal_thickness_nm`; the `radius_frac` → pressure → removal
→ thickness chain; `WireGeometry(thickness_um=…)` per die at `steps.py:478`; under-polish residual →
`bridged`-style functional short, graded by radius. The assertion that earns the slice: **with the knob
on, the delay histogram has a component the `I_Dsat` histogram cannot explain** — measured, not asserted.
Knob `None` ⇒ byte-for-byte the current delay.

**S3 — B11 demo + the history gallery. ✅ BUILT 2026-09-02** (`chip/demo_cmp_history.py` →
`docs/figures/chip-cmp-history.png`; `chip/tests/test_demo_cmp_history.py`, 10 tests; the B11 rung in
`chip/history_gallery.py` after B9 and the `hist·B11` card in `chip/gallery.py`; all four pages regenerated).
What it settled beyond the plan:

* **The figure is three panels and the middle one is the slice.** *Left — the wall:* the window in
  overburdens, floor `1/(1−s)` (the clear-everywhere requirement; the floor sits exactly `s/(1−s)` above
  "just cleared", no constant), a resistance-budget ceiling, and the closure at `s_crit = L/(2+L)` —
  **0.275** at a +10 % wire-R budget, 0.455 at +25 %: the *budget* moves the crossing, the closure is
  structural. *Middle — one transistor, many delays:* B9's own period transistor held fixed (`τ_gate` one
  float on every curve), the subtractively-etched Al line flat at 1.39× (off-scale, said so), uniformly
  polished Cu flat at F4's number bit-for-bit (the seam), and the real polish at the clear-everywhere time
  bending upward toward the rim — +0.9 / +1.8 / +4.3 % at `s` = 0.05 / 0.10 / 0.20 — plus the other side of
  the window: a polish 10 % short shorts the centre disc `r < r* = 0.71` (half the wafer's area) while the
  rim is *still* over-polished. *Right — the successor:* the rim loss as `η(d) · 2s/(1−s) · t_over/H₀`, a
  product of two levers swept over density, with dishing exactly 0 at this pitch and the cited 50–100 µm
  planarization length named.
* **The successor is stated as the two factors, not as a model.** Uniformity has to be a *pressure* fix
  (the identity: `V ≡ ω·d` at matched speeds, so the zoned-pressure head and endpoint detection are where
  the work went), and density control is design-rule density windows, slotting and dummy fill (cited
  practice, no numbers claimed). **"Polish less" is named as *not a lever*** — the S1 headline on the
  figure — because it lowers neither factor, it only fails to clear.
* **The period transistor is B9's, by value.** Same four constants as `demo_beol_history`, so the two rungs
  read one device through the untouched `device.py`; on this figure it is a bystander, and the test pins
  `τ_gate` as one float across every curve because `delay()` reads `I_Dsat` in the gate term only.
* **The knife-edge moved into the physics.** The demo hit the same float boundary S2 had (the `s = 0.05`
  centre read as shorted by a 1e-17 µm residual), so the snap now lives in `chip.cmp.polish` — the S1 seam
  test "exactly clearing costs nothing" is exactly this point — and `cmp_step` no longer carries its own.
* **What is on the suptitle, pinned by the words test:** the enabling claim (COPPER CANNOT BE PLASMA-ETCHED),
  the flag (THE RADIAL AMPLITUDE `s` IS A HOUSE NUMBER — the source averaged nine dies per wafer), and the
  two closed forms by name.

*Original plan text for S3:* The era spine, from the source's own first paragraph: *copper cannot be
plasma-etched* ⇒ damascene ⇒ CMP is **not an optimisation, it is the enabling step** — F4's Cu era
literally does not exist without F8. Period → wall → successor, glob-anchored per H0.

**S4 — the grading composition, and the second F4 clause. ✅ BUILT 2026-09-06** (`fab_game/demo_cmp_grading.py`
→ `docs/figures/fab-game-f8.png`; `fab_game/plots.py` `cmp_grading_figure`; the `F8` card in
`fab_game/gallery.py`; a fix in `fab_game/pipeline.py` `diagnose`; `fab_game/tests/test_demo_cmp_grading.py`,
13 tests). Option (b) was chosen over (a). What it settled beyond the plan:

* **The clause that goes is "a grading loss, never a yield loss."** F4's `DelayBins.from_speed_bins`
  proves in its own docstring that the true currency compresses the distribution **symmetrically** — a die
  at a bin edge sits `τ_wire·(1 − I_nom/I_edge)` off it, *positive* above nominal and **negative below**,
  so the slow tail is **rescued** from the bin-out. That was derived under the clause S2 already ended.
  The polished rim carries `τ_wire·(R/R_nom − 1)`: strictly positive, no `I_Dsat` in it, nothing to
  compensate it — so the rescue can be cancelled outright. **The sign is structural; only the size is a
  house number.** Same shape as S2 one layer up: S2 ended "the wire contributes no spread of its own",
  S4 ends "…and it can only cost a grade."
* **Measured on one wafer, three policies, and a bin-out is a yield fail here** (`packaging_step` flips
  the verdict; `wafer_yield` counts verdicts). Loose CD control, 89 dies: drive-current grading **2**
  bin-outs (yield 0.978) → F4's true currency **0** (1.000, it rescues both) → the polished wire at
  `s = 0.20` **8** (0.910). The transistors are byte-identical across all three (CMP draws no
  randomness), so one `I_Dsat` histogram produces three outcomes.
* **Neither mechanism alone loses a part** — the F4-S4 shape one slice on. Tight transistors under the
  same polish: 0 bin-outs (to `s = 0.22`). Loose transistors with no polisher: 0 (F4 rescues them). Only
  the two together. And every part lost was **already below nominal** *and* out past `r = 0.61`, while 37
  dies are below nominal and 60 are out that far — the intersection is the loss. **The polisher never
  rejects a fast die; it withdraws the rescue from a slow one.**
* **It is not extra spread on top of the transistor's — it is the opposite sign.** The transistor has a
  weak radial trend of its own here (focus bowl + oxide trend leave the rim marginally *faster*: radius vs
  `I_Dsat` **+0.25**), so the unpolished wafer's delay is, if anything, faster outward (**−0.09**).
  Polished: **+0.45**. The polisher **reverses the wafer's speed gradient**, and the parts it costs sit
  where the transistor said the dies were fast. Not predicted by the plan; found by measuring.
* **The threshold is a house number and is drawn as a curve, not quoted as a point.** At the knob's own
  default spread (`s = 0.10`) the polisher still costs **no** part; the first goes at `s ≈ 0.14` loose,
  `s ≈ 0.24` tight. Cranking `s` until a part fell off would have been the `DISH_SCALE` / F5-S3
  flattering-direction trap; the panel sweeps `s` instead and the sign is the claim.
* **The anchor dissolves at the clear time.** `from_speed_bins` warns that hand-picked ps edges can
  manufacture the collapse out of a threshold choice, so the ladder is G6's own grade fractions anchored on
  the **nominal part** — and at the clear-everywhere polish time that part **is** this wafer's centre die
  (S2's seam), byte-for-byte. The two candidate anchors are the same object, so there is no choice to make.
* **Live finding, fixed in this slice.** `pipeline.diagnose` hardcoded every bin-out as *"I_Dsat too low
  for the slowest sellable speed bin"* — under delay grading that credits the **transistor** with a
  failure the **wire** caused, the precise inverse of this slice's thesis. It now forks on the currency
  that actually graded (the packaging record's `tau_total_ps`) and points at the CMP line above it.
* **The sweep is a closed form, pinned against the pipeline.** 60 wafer runs for one curve is ~15 s of
  fast lane; instead each die's recorded `τ_gate`/`τ_wire` are re-read at the polished thickness, which is
  exact because `τ_wire` is linear in `R` and `C` never reads `H` (F4's cited invariance). The test pins
  the shortcut against the real line at two spreads.
* **Nothing in `chip/` moved.** `device.py` and `interconnect.py` untouched for the **fifth** consecutive
  slice; `chip/cmp.py` untouched by S4 entirely. The slice is the game layer reading F4's `DelayBins` over
  F8's per-die wire.

*Original plan text for S4 (not pre-committed):* Candidates, to be chosen from what S1–S3 actually turn up: the wall (why
polishing longer cannot close the window); the scale gap (what the sub-micron regime the source could not
measure would change); or the composition with F4's `wire_share`. *After S3 (2026-09-02):* the wall and
the composition are now both on the B11 figure (the window's closure; `τ_gate` fixed while `τ_wire`
spreads), so the live candidates narrow to (a) **the scale gap made mechanical** — the sub-micron regime is
erosion-only here *because* the cited dishing trend crosses zero, and a slice that asks what the source's
own planned sub-micron mask would have changed is the honest next question; or (b) **the composition with
the game's grading** — a per-die `wire_share` means F4's `DelayBins` inversion now has a radial signature,
and S2's "grading by position" is measured but not yet a banked fab-game artifact. Either graduates the
card; neither is pre-committed.

## Scope discipline (the honest NO's)

* **No slurry chemistry, no pad mechanics, no dishing-model fitting.** The module takes a removal and a
  pattern and returns a thickness. Preston + the pattern dependence is the whole physics.
* **No absolute dishing in nanometres.** The source normalizes; we ride fractions.
* **No sub-micron extrapolation** of the break point (above).
* **No new litho/layout subsystem.** Pattern density enters as a knob-level house quantity, not as a
  printed layout the sim resolves.
* **No copper-thickness feedback into `C`.** F4's cited invariance says `c_pul` does not read `W`/`H`;
  dishing changes `R` only. Touching `C` here would silently contradict the F4 source.

## Decisions taken (2026-08-19, user)

1. **The CMP step gets its own step**, not an extension of `fab_game/etch_deposition.py`. It is a distinct
   process step historically and the two-sided window is *its own* trade-off — burying it inside the
   front-end gate etch would hide the very thing the slice exists to show. Cost accepted: a new step in
   the flow. (The D1 bridging-short machinery is still the pattern to *follow* for the under-polish short,
   just not the place to live.)
2. **The stale `F8` roadmap card graduates rather than being corrected in flight** — the correction is
   recorded here (see *Live finding*), and the card + schematic come off together at S4, on the F3/F4/F5
   precedent. Avoids regenerating a schematic that is about to be deleted.

## Open questions

1. **Whether `W` moves too.** Erosion thins the oxide *between* lines; dishing thins the copper. Modelling
   `H` alone is the honest minimum; whether the plan also wants a `W` effect is an S1 decision.
