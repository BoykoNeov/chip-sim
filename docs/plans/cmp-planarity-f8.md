# Plan — F8 CMP / planarity (the step that gave the wire a spread of its own)

> **STATUS: PLANNED (2026-08-19).** Chosen off the post-F5 re-triage. Historical mode reserved: **B11**
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

**S2 — the game knob + the per-die wire (the payload).** `cmp` knob; `Die.metal_thickness_nm`; the
`radius_frac` → pressure → removal → thickness chain; `WireGeometry(thickness_um=…)` per die at
`steps.py:478`; under-polish residual → `bridged`-style functional short, graded by radius. The assertion
that earns the slice: **with the knob on, the delay histogram has a component the `I_Dsat` histogram
cannot explain** — measured, not asserted. Knob `None` ⇒ byte-for-byte the current delay.

**S3 — B11 demo + the history gallery.** The era spine, from the source's own first paragraph: *copper
cannot be plasma-etched* ⇒ damascene ⇒ CMP is **not an optimisation, it is the enabling step** — F4's Cu
era literally does not exist without F8. Period → wall → successor, glob-anchored per H0.

**S4 — not pre-committed.** Candidates, to be chosen from what S1–S3 actually turn up: the wall (why
polishing longer cannot close the window); the scale gap (what the sub-micron regime the source could not
measure would change); or the composition with F4's `wire_share`.

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
