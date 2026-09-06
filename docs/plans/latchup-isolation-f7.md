# Plan — F7 remainder: trench isolation and the latchup wall (historical mode B12)

**The discriminating observable, stated first (the licence):** a **latchup margin** — whether the
parasitic four-layer (pnpn) structure between an n-channel device and its neighbouring well can be
triggered, and how much room the line has before it can be. Nothing in the sim computes this today.
It is the electrical observable `future-steps.md` fenced F7's remainder behind, and it is the reader
that turns the already-built LOCOS→STI *geometry* contrast into an era with a **bill**: STI cleared
the density wall the bird's beak set, and the density it bought is what lit the thyristor.

Status: **PLANNED** (2026-09-06). Picked by the user over the alternatives after the roadmap's
promotable section was found honestly empty. Historical mode **B12** — the isolation rung's second
half, and the **first mode whose subject is a failure the sim cannot currently have**.

---

## 0. The gate re-check, done first (and what it found — the fourth time)

The standing instruction (`roadmap-page` memory; `future-steps.md`) is to re-check a slice's gate
against the **tree**, not the prose, before building. Done, and it split F7's remainder in two:

* **The geometry half is already built.** `chip/locos_history.py:404` carries
  `LocosCrossSection.sti_active_um` — *"The STI successor's active width — the drawn width itself
  (vertical walls, no beak)."* The LOCOS-vs-STI **active-width** contrast, the thing the roadmap card
  describes as unbuilt ("the STI trench etch/fill step itself"), needs **no new code**. That is the
  **fourth** roadmap gate on this page found already released by someone going to build, and again not
  by a test.
* **The electrical half is genuinely absent.** `grep -riE "latchup|substrate_current|well_current"`
  over `chip/` and `fab_game/` hits **only** roadmap prose (`chip/roadmap_gallery.py`,
  `chip/roadmap_figures.py`). No well, no pMOS, no bipolar transistor of any kind. This gate is real.

So the slice is **not** "build the STI process." It is: build the **observable**, and let the
already-built geometry feed it. The trench's *process* detail (etch/fill/CMP of the trench) stays a
named scope edge — `chip/cmp.py` (F8) already owns polish, and a trench-fill recipe would add no
observable this plan does not already deliver.

---

## 1. The physics, and exactly which parts are cited

Two **independent** conditions must both hold for latchup. This is the plan's spine, and it is the
same shape as F3's "one thickness, two currencies": one structure, two criteria, moved by **different
processes**.

**(A) The sustaining condition — loop gain.** The cross-coupled parasitic npn (n⁺ source / p-substrate
/ n-well) and pnp (p⁺ / n-well / p-substrate) form a regenerative loop that can only stay latched if

> `β_npn · β_pnp > 1`

— **CITED verbatim**, TU Graz (Hadley, *Latch-Up*): *"The product of the gains of the two parasitic
transistors in the feedback loop, β₁×β₂, has to be greater than one to make latch-up possible."*
Independently corroborated by EDN/Planet Analog: *"The transistor current gain product of Qn and Qp
must be greater than 1."*

**(B) The triggering condition — the resistive drop.** The loop only *starts* if enough current flows
through the substrate/well shunt resistance to forward-bias a base–emitter junction:

> `I · R_sub > 0.7 V`

— **CITED verbatim**, TU Graz: *"sufficient current flows through R_p to turn on the npn-transistor
(I*Rp > 0.7 V)."* Corroborated by the trigger-current definition found in the same search (*"the
current necessary to shift the net potential of the two independent diodes by +0.7 V"*), and by EDN's
*"The holding current has been shown to be strongly dependent on Rwell and Rsub… a low Rwell or Rsub
means a higher current has to flow to maintain forward bias."*

**The two levers are moved by different processes — and they are independent lengths.** `R_sub` is the
resistance from the injection point to the nearest **substrate tap**; the spacing that sets the
parasitic npn's **base width** is n⁺-to-well. These are different geometries and both sources treat
them as separate design levers (EDN lists *"reduce beta by increasing device spacing"* and *"increase
well and substrate doping concentrations to reduce Rwell and Rsub"* as two items). **The model must
not couple them.** A model in which `R_sub ∝ spacing` manufactures a sign reversal that is an artifact
of its own geometry lump, not physics — the calibration-wearing-a-physics-hat trap `locos_history.py`
names. Consequence, stated up front: **the resistance term is silent on spacing** (not wrong there),
and **the gain term is silent on doping**.

**Direction with spacing — CITED, and a recorded reading trap.** TU Graz: *"Larger spacing of
source/drain areas to the well-borders will increase the base width and worsens the parasitic
transistor."* "Worsens the parasitic transistor" = makes it a *worse transistor* = **lower β** = more
immune. An automated summary of that page glossed it as *"thereby increasing β"*, which **inverts the
sign**. EDN is the discriminator and settles it: *"Reduce beta by increasing device spacing."* This
inversion goes in the source memory as a named trap, the way `locos-birds-beak-source.md` records its
own correction.

**Trench depth — CITED:** shallow-trench isolation is 250–400 nm deep (0.25/0.18 µm-generation STI
studies; one 0.25 µm process quoted at 0.4 µm, gap-fill aspect ratios ~3:1). Direction cited too — TU
Graz: *"Deep trenches … avoid or weakens the parasitics"*; and from the latchup-immunity literature,
*"even a shallow trench is remarkably effective in raising the holding voltage."*

**Substrate engineering — CITED direction:** TU Graz lists as prevention *"EPI layer is more lightly
doped than the substrate that is highly doped"*; EDN: *"Increase well and substrate doping
concentrations to reduce Rwell and Rsub. For example using retrograde doped wells."*

---

## 2. What the sim already computes, and therefore what is *not* new physics

The reason this is buildable at all is that **both** terms borrow validated machinery:

| Term | Where it comes from | Status |
|------|--------------------|--------|
| Minority-carrier diffusion length `L = √(D·τ)` | `chip.lifetime.diffusion_length` / `srh_lifetime` — τ already falls with metal contamination (G4b), dislocations (A1) and implant damage (F1 slice 4) | **existing, validated** |
| Substrate resistivity `ρ(N)` | `chip.junction.mobility` (Masetti 1983, cited) → `ρ = 1/(q·N·µ(N))` | **existing, cited** |
| The device-to-well spacing | `chip.locos_history` — the active width LOCOS leaves vs the drawn width STI keeps (`sti_active_um`) | **existing (this slice's whole point)** |
| Base transport factor → β | `α_T = 1/cosh(W_B/L)`, `β = α_T/(1−α_T)` — standard bipolar closed form, **no fitted prefactor** | **derived, not fitted** |

That last row matters for the honesty ladder: β has **no flagged coefficient**. Its only idealization
is **emitter efficiency γ = 1**, which makes β an **upper bound** — i.e. the model is *pessimistic*
about latchup, which is the safe direction for a failure model and is named, not hidden.

**The consequence worth stating:** because `L = √(D·τ)` and τ is the contamination lifetime, a
**dirtier wafer has a weaker parasitic transistor**. That is real (lifetime-killing was historically
used to suppress latchup) and it composes the new module with the existing contamination chain
instead of inventing a length.

**The guard that must ride with it.** The *same* τ feeds `chip.lifetime.generation_leakage_density`,
so a wafer made latchup-immune by contamination has **bought that immunity with leakage**. Any read of
latchup against τ — in a test, a demo figure, or a game grade — **must report the leakage at the same
τ beside it**. Immunity shown alone would be a free lunch this model has not earned, and the pair is
the honest statement: lifetime-killing trades one failure for another.

---

## 3. The honesty ladder (the `historical-modes.md` triad)

* **Tight.**
  1. **The seam** — isolation knob absent (`None`) ⇒ no latchup evaluated, no per-die record, and the
     whole existing suite byte-identical. Same shape as `polish_s=None` (F8) and `implant=None` (F1).
  2. **The two cited criteria reproduced exactly** — `I·R = 0.7 V` at the trigger point and
     `β_npn·β_pnp = 1` at the sustaining boundary are *definitions* the code satisfies by
     construction, and each is asserted as an identity in tests.
  3. **Monotonic directions, all cited:** β falls monotonically with base width; base width grows with
     spacing and with trench depth; trigger current rises monotonically as substrate resistance falls.
     Sign-robust, coefficient-free.

  Three legs, not four. The short-base asymptote `β = 1/(cosh(W/L) − 1) → 2L²/W²` **is** tested, but it
  is **not** a tight leg: it pins a Taylor expansion of the form the code already chose, not a physical
  claim. Kept as a regression on the algebra, counted as nothing.
* **The earned finding (direction, never a coefficient).** *The isolation change that cleared one wall
  built the next.* STI keeps the drawn active width (already in the tree), so it buys pitch; the pitch
  it buys is the parasitic base width; the base width sets the gain. Run the same drawn geometry
  through both isolation schemes and the loop gain **rises** for the scheme that packs tighter. Only
  the **sign** is claimed. The exact spacing at which loop gain crosses 1 rides the base-width
  geometry and is **not** asserted.
* **Flagged — the magnitudes.**
  * `SUBSTRATE_TAP_PATH_UM` / the tap cross-section — a house geometry lump for `R_sub`, exactly like
    F4's wire length `L` and B7's `CONTACT_LENGTH_UM`. **Every headline must be a ratio in which it
    cancels.** An absolute trigger current in mA is reportable but is *never* the headline.
  * The trench's contribution to base width (`W_B = spacing + 2·trench_depth` — the carrier must go
    *under* the trench). The **form** is geometric and the **depth** is cited; the "2×" is the honest
    straight-line detour and is named as such, not fitted.
  * γ = 1 (emitter efficiency) ⇒ β is an upper bound ⇒ the model over-predicts latchup.

---

## 4. The seam

`RecipeKnobs.isolation = IsolationKnobs()` with `scheme: str | None = None`. **`None` ⇒ no isolation
step runs**: no latchup evaluation, no per-die record, no spec field consulted, and the fab-game
regression suite is byte-identical. `"locos"` and `"sti"` both engage the step and differ *only* in
the active width they hand downstream (`locos_cross_section(...)` vs the drawn width) — which is the
whole point: **one number differs, and it changes which failure the line has.**

---

## 5. The slices

### S1 — `chip/latchup.py`: the two conditions, closed form — ✅ **BUILT 2026-09-06**

**As built, and the one thing the plan did not anticipate.** The module, `chip/tests/test_latchup.py`
(26 legs, fast-lane, import+numeric only), and nothing else touched. Numbers land where intended:
ρ = 13.5 Ω·cm at 1e15 cm⁻³ (correct for p-Si), `R_sub` ≈ 940 Ω, trigger current ≈ 0.75 mA — the right
order for real latchup.

**The gain condition does not discriminate, and that is now a stated property of the module.** With
γ = 1 and `W_B ≪ L` (a µm-scale base against a diffusion length of ~27 µm contaminated, ~1900 µm
clean), each β lands at 10²–10⁶ and the product at 10⁴–10¹² — against real parasitic laterals of ~1–50.
The cause is physical, not numerical: **recombination is not what limits these transistors, geometry
is** (most of the injected carrier goes *down* into the substrate, not laterally to the well, and that
collection efficiency needs a 2-D structure this module does not have). So the sustaining condition is
satisfied at every geometry the model spans, which is what an unbounded β *must* give and is therefore
**not a finding**. It is reported, tested as an embarrassment (`loop_gain > 1e6` is asserted, so the
admission cannot quietly stop being true), and excluded from every claim.

**Consequence for the rest of the plan:** the gain term is usable **only comparatively** — sign and
ratio between two isolation schemes at the same τ — and the **trigger condition is the discriminating
one**. It happens to agree with the fact that every prevention measure the sources list (epi
substrates, guard rings, substrate taps) is a resistance or collection measure rather than a
gain-killing one; the module claims the *agreement*, not a derivation of it. This strengthens S4 (the
substrate is the lever) and narrows S3's figure to a comparison rather than a threshold.

The decoupling is asserted mechanically, not just written down: `R_sub` is *exactly* invariant to
spacing and the loop gain *exactly* invariant to doping, and every quotable leg is asserted invariant
to the flagged tap geometry (with the absolute value shown to move, proving the cancellation is real).

The module. Cited constants (`BE_TURN_ON_V = 0.7`, `LOOP_GAIN_CRITICAL = 1.0`, `STI_DEPTH_UM` in the
cited 0.25–0.40 band), the base-width geometry, `β` from the cosh transport factor against
`chip.lifetime.diffusion_length`, `R_sub` from `chip.junction.mobility`, and a `LatchupMargin` result
bundling loop gain, trigger current and the two-condition verdict. Plain scalars/dataclass — the
loose-coupling currency (ADR 0002). No existing module is touched.

Tests: the two identities; the short-base asymptote; the three monotonicities; the seam (module
unimported by anything on the default path).

### S2 — the game knob: latchup is a **wafer** property, not a die one — ✅ **BUILT 2026-09-06**

**As built.** `IsolationKnobs` (`scheme=None` seam, `"locos"`/`"sti"`) → `isolation_step` (per-die,
inert) → a wafer-level `StepRecord` → one clause in `SpecSet.verdict` on the flatness-scrap precedent →
a failure-trail line that names the wafer number that killed the part *and* the die number that did
not. 17 legs in `fab_game/tests/test_isolation.py`.

**The era result, and it is a number rather than a sign.** Because `β ≈ 2L²/W_B²`, a *ratio* of two
schemes' loop gains is the inverse square of their base-width ratio — the diffusion length cancels, so
the ratio is independent of lifetime, of `D`, of the γ=1 idealization, and of the flagged tap geometry
(which does not appear in it at all). Where the absolute gain is a useless bound, the ratio is pure
geometry:

| | device-to-well spacing | parasitic base | loop gain | vs LOCOS |
|---|---|---|---|---|
| LOCOS (drawn 2.0 + **B5's computed beak** 0.926) | 2.926 µm | 2.926 µm | 6.73e11 | — |
| STI, trench ignored | 2.00 µm | 2.00 µm | 1.44e12 | **2.140× = (2.926/2.0)²** |
| STI, trench counted | 2.00 µm | 2.70 µm | 7.90e11 | **1.174× = (2.926/2.7)²** |

**LOCOS's spacing is not a house constant.** It is the drawn width plus the bird's beak
:mod:`chip.locos_history` already computes at its reference recipe (0.926 µm, the beak eating active
area from both edges), pinned as `chip.latchup.LOCOS_BEAK_ALLOWANCE_UM` so the game need not run a 2-D
solve per wafer, with a test asserting it still matches B5. **That is what makes B12 the second half of
B5 rather than a module beside it** — the spacing LOCOS gives up is the beak B5 computed.

**The trench pays back 85 % of the density penalty — and no more.** That is the honest era sentence:
the successor did not merely trade one wall for another, it *partly* paid for what it took, and the
remainder is the bill. Both halves are asserted (the trench helps; it does not get back under LOCOS),
because either alone misrepresents it.

**The cancellation's precision, stated at the level it is true.** "L cancels" is exact only in the
short-base limit. At τ = 1e-7 s (diffusion length ~19 µm against a 3 µm base) the cosh corrections stop
vanishing, and across four orders of magnitude of lifetime the ratio drifts by **< 0.05 %** — near-
invariant, not invariant. The test pins the drift rather than the overclaim.

*The build's reasoning, retained:*

> ### S2 — the game knob: latchup is a **wafer** property, not a die one

**The plan's expectation here was tested and failed, and the correction is the slice.** What follows in
italics is what this section said before the build; it is kept because the measurement that overturned
it is the finding.

Measured on a real 21-die wafer run (`Recipe()`, seed 3, variation on): the minority-carrier lifetime is
**identical on every die** (contamination is a wafer-level vector), the substrate resistivity is a
**wafer-level number**, and the only genuine per-die spread — the printed CD, 165.6→170.1 nm — reaches
the spacing, which reaches the **gain**. The gain is the condition S1 showed does not discriminate.

So: **the discriminating condition is wafer-uniform, and the per-die axis reaches only the inert one.**
Latchup here is all dies or none. It is built on the precedent already in the tree — the flatness scrap
(`SpecSet.verdict`'s `geometry_reason`) is computed once per wafer and applied to every die.

**What was explicitly refused.** Grading it would have meant giving the substrate a radial resistivity
profile. That is new, uncited physics introduced *specifically* to produce a gradient the plan expected
— the fudge the standing `gradual-failure-preferred` rule warns against, not the honest move it
endorses (which is non-uniformity of the offending quantity *when the quantity is really non-uniform*).
The offending quantity is genuinely uniform here.

**What is reported instead, and why it is stronger.** The per-die loop gain *is* recorded, along with
the fact that it costs nothing: the isolation change moves a quantity that cannot bin out a die, and
the substrate moves the one that can. That is the finding S4 then pays off.

**The drift direction, stated because it inverts the house pattern.** Boron's segregation coefficient
is below 1, so concentration *rises* down the boule, resistivity falls, and the trigger current rises:
51.5 mA at `z=0.0` → 74.0 mA at `z=0.9`. **The first wafers off the boule are the vulnerable ones** —
the opposite of the direction every other knob in this game teaches (later slices are worse for `V_t`).

**Not tuned to fail.** At the default recipe the trigger is 51 mA against a 2 mA disturbance — a ~25×
margin, no failure, and it stays that way. The sign is structural; the threshold rides the flagged tap
geometry, so the figure draws the curve rather than quoting a crossing point (F8 S4's precedent).

*The original sketch, retained:*

> ### S2 — the game knob: latchup as a graded wafer failure

`IsolationKnobs` in `fab_game/recipe.py` → the pipeline. The wafer already carries per-die
non-uniformity (`fab_game/variation.py`) and substrate doping already varies down the boule (the G2
Scheil drift), so **the margin varies die to die** and the failure arrives as a *fraction of dies
latched*, not a wafer-wide cliff — the standing `gradual-failure-preferred` preference, and the
`locos_history.py` scope edge ("a graded fraction of islands lost … named here, not built") finally
paid.

The composition to look for, and to report honestly whichever way it lands: the tighter-packed scheme
should cost parts that the looser one did not — but the *same* Scheil drift that moves `V_t` also
moves substrate doping and therefore `R_sub`, so the latched dies and the `V_t`-rejected dies may or
may not be the same dies. Whether the new failure is **correlated or independent** decides whether it
costs yield or merely re-labels dies already lost — the question F8's S4 asked of the wire, asked of
the substrate.

### S3 — B12: the era figure on the timeline — ✅ **BUILT 2026-09-06**

`chip/demo_latchup_history.py` + `chip/tests/test_demo_latchup_history.py` (11 legs), picked up by the
existing `demo_*_history.py` glob, and a `HistoryMode` rung placed **immediately after B5** rather than
in tag order — the timeline should read the isolation arc as one story, not two topics separated by
five unrelated rungs. The thumbnail manifest guard fired on the new figure exactly as designed
(`no thumbnail for figures/chip-latchup-history.png — run python -m chip.thumbnails`), so the figure,
its thumbnail and both gallery editions are regenerated and committed together.

**The figure's structure is the finding, restated visually: the panel that moves is not the panel that
decides.** Left, the parasitic gain against base width, with the three era points on one curve and the
between-scheme *ratios* labelled (they are coefficient-free; the axis is labelled as a bound and the
absolute values are explicitly not a claim). Right, the trigger current against substrate resistivity,
with the disturbance drawn as a line and the isolation scheme **absent from the panel entirely**.

**The demo composes from B5 rather than restating it.** It calls `locos_history.birds_beak_length_um`
for LOCOS's allowance, and a test asserts that chain — because if it broke, the figure would silently
become two house numbers being compared, which is exactly the failure the rung exists to avoid.

**Two things the panels deliberately refuse.** The right panel quotes **no crossing point** (it rides
the flagged tap geometry) and the band it draws for this simulator's own boule sits comfortably on the
safe side — asserted, so the figure cannot drift into implying this line is in danger. The left panel
labels its y-axis as an upper bound in the axis text itself, not in a footnote.

### S3 — the original sketch, retained

`chip/demo_latchup_history.py`, picked up by the existing `demo_*_history.py` glob in
`chip/history_gallery.py` (H0's shared consumer — no gallery machinery changes). The rung reads
period → wall → successor: LOCOS's beak sets the pitch floor → STI removes the beak and the pitch
collapses → the loop gain crosses 1 → the fix is the substrate, not the isolation.

### S4 — the finale: the substrate is the lever the geometry cannot be

The closing composition, and the one that answers "so what did they actually *do* about it."

The gain lever runs the wrong way against scaling: every node wants tighter spacing, and tighter
spacing raises β. The resistance lever does not care about spacing at all — and it is the one a
*process* can move without giving back the density. A lightly-doped uniform wafer makes the current
run a long way sideways to reach a tap; a heavily-doped wafer with a thin lightly-doped layer grown on
top replaces that lateral run with a short vertical hop into a near-shorting substrate.

`R_uniform ≈ ρ·L_tap/A_lat` vs `R_epi ≈ ρ·t_epi/A_vert`. With the grown layer's doping matching the old
bulk, ρ cancels; the cross-sections do **not**, so the ratio is **dominated by `t_epi/L_tap`** with an
O(1) geometric factor — claimed as *dominated by*, **not** as prefactor-free. Thinner grown layer ⇒
higher trigger current, monotonically. The literature's *optimum* layer thickness is **named as a
ceiling and not reproduced** — it involves the vertical pnp this model does not carry.

**The F6 trigger, recorded not argued.** Per the CMP precedent, one sentence goes on the F6 card in
`future-steps.md`: *"latchup trigger current reads substrate resistance ⇒ re-check F6's gate."* That is
the whole of it. Whether F6's stated deferral reason survives that trigger is for whoever picks the
card up to settle against the tree — it is not content in this slice, and this plan makes no claim
about it.

---

## 6. Named scope edges (honest ceilings, stated so the omission is not silent)

* **No pMOS, no well, no bipolar device model.** The parasitic pair is a *lumped two-transistor
  criterion*, not a simulated structure. There is no pMOS in the sim and this plan does not add one;
  `β_pnp` is the vertical device and is carried at the same lumped level as `β_npn`. **This is the
  reason the headline is a direction and never a trigger current.**
* **The trench process itself.** Etch profile, liner, fill, and the trench's own CMP are not modelled;
  the trench enters as a **depth** that lengthens the parasitic base and as the absence of a beak.
  STI-induced **stress** on the channel (real, and interacting with F5's strain module) is named and
  not built.
* **Guard rings, substrate taps as a density, well taps.** Cited as the other prevention families;
  the model carries a single lumped tap path, so "add more taps" is not a knob.
* **Holding voltage / holding current.** Cited as existing (*"any structure with a latchup holding
  voltage higher than its supply voltage will be immune"*), not computed — it needs the on-state
  I–V of the latched thyristor.
* **γ = 1.** β is an upper bound; the model is pessimistic about latchup.
* **Transient / external triggers.** Real latchup is usually triggered by an I/O overshoot or a
  radiation event injecting the current. The model takes the injected current as **given** and reports
  the margin against it; it does not model the injection source.

---

## 7. Units

Lengths **µm** (spacing, base width, trench depth, grown-layer thickness, tap path) matching the
`chip.oxidation`/`locos_history` currency — **except** `chip.lifetime.diffusion_length`, which returns
**cm** (its module's currency, `D_MINORITY` in cm²/s). The conversion is done **once**, at the module
boundary in `chip/latchup.py`, and is asserted in a test — a units seam of exactly the kind that has
bitten this repo before. Doping cm⁻³; resistivity Ω·cm; resistance Ω; current A (reported mA);
voltages V; β and loop gain dimensionless.

---

## 8. Order and the one decision deferred to build time

S1 → S2 → S3 → S4, the house order (module → knob → era figure → composition). The one thing
deliberately left to build time: **whether S2 grades or rejects.** If the latched fraction turns out
to be perfectly correlated with the dies `V_t` already rejects, the knob costs nothing and the honest
report is that the new failure is *redundant on this line* — which would be a real finding and must be
reported as one, not tuned away. F8's S4 is the precedent: the composition was allowed to overturn the
plan's expectation, and the correction was the result.
