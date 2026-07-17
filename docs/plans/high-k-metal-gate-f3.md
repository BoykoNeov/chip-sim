# Plan — F3 high-κ gate dielectric (the EOT/leakage split one thickness can't carry)

> **SLICE 1 BUILT (2026-07-15)** — `chip/high_k.py` + `chip/tests/test_high_k.py` (23 tests, fast lane
> green; no existing file touched, `device.py` included). The EOT identity, the WKB tunnelling exponent,
> the cited dielectric registry, and the prefactor-free `leakage_decades_saved`. Cited constants →
> `memory/high-k-dielectric-source.md`.
>
> **The build corrected this plan's physics — see "Model class" below.** The plan's `J_g ∝ exp(−t/λ)`
> with a *single* λ was **wrong across materials**: κ and the band gap are inversely correlated
> (Robertson Fig. 5), so the high-κ oxides that buy thickness *also* have a lower barrier φ_B **and** a
> lower tunnelling mass m*, both of which enter the exponent as `α ∝ √(m*·φ_B)`. HfO₂'s 6.4× thickness
> gain nets to only **~2× in the exponent**, not 6.4×. The discriminator itself is **unchanged** (see the
> identity note below); only the leakage *magnitude* moves. Remaining: the game knob, the `steps.py`
> wiring, the history mode + demo, and the interfacial-layer slice.
>
> **SLICE 2 BUILT (2026-07-17)** — the game knob + the `steps.py` wiring (`DeviceKnobs.dielectric`,
> `Die.j_gate`, `fab_game/tests/test_gate_dielectric.py`, 8 tests; fast lane green, **`device.py` and
> `chip/high_k.py` both untouched**). Closes **open Q1**. The knob carries the **material only** and reads
> the *inherited* `die.t_ox_um` as the stack's **target EOT** — the matched-EOT historical move — rather
> than carrying an explicit `t_phys` (see "The knob's parameterization" below). This is the slice that
> makes the F3 discriminator *assertable end-to-end*: at a fixed EOT, `V_t`/`I_Dsat`/`C_ox` come out
> **byte-for-byte identical for every material** through the real, untouched `device.py`, while `j_gate`
> moves 22 decades across the registry — the proof the "don't touch `device.py`" claim was making.
> Remaining: the history mode + demo (slice 3), and the interfacial-layer slice.
>
> **SLICE 3 BUILT (2026-07-17)** — the history mode + demo: `chip/demo_highk_history.py` (**B8**, the 8th
> timeline mode), both gallery manifests, `chip/tests/test_demo_highk_history.py` (7 tests). Fast lane green
> (1048); **`device.py`, `chip/high_k.py` and `fab_game/` all untouched** — slice 3 is a display surface.
> Closes **open Q2**. **Deliberate deviation from "What to touch" below: NO `chip/highk_history.py`.** That
> line predates F2 establishing the demo-rides-the-base-module pattern (B7 = `contact_resistance.py` +
> `demo_silicide_history.py`, no `silicide_history.py`). A Tier-2 `*_history.py` exists to carry *period
> physics the base module lacks* (A2's proximity blur, A4's swelling, B5's beak); `high_k.py` already carries
> SiO₂/HfO₂/TiO₂ as first-class registry entries and `gate_stack()` is documented as "the demo's unit of
> comparison" — a wrapper would hold **zero** distinct physics. Advisor concurred.
>
> **The magnitude trap (below) governed the build, and cost two design moves:** (a) the ladder is capped at
> **EOT = 1.0 nm** — the 45 nm node's target, where the model sits *inside* the validated direct-tunnelling
> regime and its numbers land **on top of published data** (SiO₂ 6.5e2, HfO₂ 1.8e-3 A/cm²); the featured win
> is **+5.6 decades**, inside the flagged m* band (3.9–9.5) and adjacent to lit ~3–5. (b) The left panel's
> **display floor is an honesty device**: HfO₂ off the *thick* end runs to ~1e-22 A/cm² (meaningless — real
> stacks are trap-limited long before), so curves are allowed to **exit the axis** rather than print a
> fabricated number, which also stops the SiO₂ wall — the payload — being squashed into a third of the panel.
> Two of the 7 tests are **honesty guards, not physics guards** (the ladder cap; no rounding a "≳ N" claim
> up), pinned because they are claims about *where the model may speak*.
>
> **One real bug the build surfaced:** at a 1 nm gate the depletion term collapses and an unadjusted n-MOS
> reads **V_t ≈ 0.02 V** — a device that never turns off, which would have shipped in a student-facing
> figure. Fixed with the **V_t-adjust implant** `device.py` already supports (§5, `implant_dose`/
> `implant_kind`) → V_t ≈ 0.35 V, an honest 45 nm threshold. It cannot disturb the invariance: ΔV_t =
> q·dose/C_ox reads the *same* C_ox all three materials share (asserted).
>
> Remaining: the **interfacial-layer** slice (the honest EOT floor — series tunnel barrier *and* series
> capacitance, both sides at once) — and nothing else.
>
> **The roadmap card — USER DECIDED (2026-07-17): leave it until the IL slice lands.** So for the graduation
> rule, **"F3 ships" means the IL slice is done**, not slices 1–3: the F3 card stays on `docs/roadmap.html`
> (schematic, "not simulator output") until then, and the card understating what already exists is the
> accepted cost. Do not pull it early. (Alternatives put to the user and rejected: pull now and treat the IL
> as a follow-on; pull and add a standalone `F3-IL` card.)

**The discriminating observable, stated first (the build's licence):** the gate oxide thickness feeds
**two device quantities with different functional dependence**, and no single scalar can move both:

- **Capacitance** `C_ox = ε_ox/EOT` — set by the **electrical** thickness `EOT = t_phys·(3.9/κ)`.
  **Linear in EOT, blind to κ and `t_phys` separately.** This is what the model already computes.
- **Direct gate tunneling** `J_g ∝ exp(−t_phys/λ)` — set by the **physical** thickness `t_phys`.
  **Exponential in `t_phys`, blind to EOT.**

At **fixed EOT**, swapping SiO₂ (κ=3.9) for HfO₂ (κ≈20–25 — *verify at build*) multiplies the physical
thickness by `κ/3.9` ≈ 5–6× while leaving `C_ox`, `V_t` and `I_Dsat` **exactly where they were**. The
tunneling current, exponential in that thickness, collapses by orders of magnitude. The device number
that falls out for free and that a fudge factor *cannot* fake: **the same electrical gate, orders of
magnitude less leakage, purely because the dielectric got physically thicker** — the historical reason
SiO₂ stopped scaling at ~1.2 nm (a few atomic layers; leakage ran away) and 45 nm went to HfO₂ in 2007.

That split — one input, two currencies, one era transition that moves them independently — is the
observable that clears the repo's standing bar (**no regime without a consumer that discriminates**, the
v1.6 "build explicit, NOT 2-D" lesson). A scalar "high-κ cuts leakage by 1000×" would *not* clear it; it
would be decoration. **High-κ splits one thickness into two currencies, and that split is the payload.**

Standing consumer set by the user **2026-07-03**: **the game — historical processes, education.**

## The consumer (why this passes the bar)

1. **The `C_ox` path is already wired, and it is already electrical.** `chip.device.oxide_capacitance`
   computes `ε_ox/t_ox` — an `EOT` **is** the number that belongs there by definition. F3 does **not**
   touch `device.py`; it feeds a *correctly-computed EOT* into the existing capacitance path. Same move as
   F2 feeding a better `R_series` into the existing `I_Dsat` quadratic — this is what makes F3 the
   contained promotable step.
2. **Educational contrast (the named consumer):** the same wafer run **thin-SiO₂ → high-κ at equal EOT**
   holds `V_t`/`I_Dsat` fixed and drops gate leakage off a cliff; and the *thin-SiO₂ scaling ladder* walks
   `t_ox` down until leakage runs away — the wall that motivated the swap. Neither is fakeable by a scalar.

## The seam — the κ=3.9 identity, verified against every `t_ox` consumer

`EOT = t_phys·(3.9/κ)`, so **at κ=3.9, `EOT == t_phys`** and every existing number is byte-for-byte
today's. The knob carries `(t_phys, κ)`; absent → today's `t_ox` flows through untouched.

| State | `C_ox` input | Gate leakage | vs today |
|-------|-------------|--------------|----------|
| **`dielectric` knob absent (default)** | `t_ox` (as today) | not emitted | **byte-for-byte identical** ← the seam |
| **SiO₂ (κ=3.9, opt-in)** | `EOT == t_phys` (identity) | `J_g(t_phys)` | `V_t`/`I_Dsat` **unchanged**; leakage is a *new additive output* |
| **HfO₂ (opt-in)** | `EOT = t_phys·3.9/κ` | `J_g(t_phys)`, collapsed | at matched EOT: `V_t`/`I_Dsat` **unchanged**, leakage orders down |

**The `t_ox` consumer audit (done at scope — this is what makes "device.py untouched" survive):**

- `device.oxide_capacitance` / `body_effect_coefficient` / `threshold_voltage` / `saturation_current` —
  **electrical only** (`ε_ox/t_ox`). EOT substitutes *exactly*; this is the definition of EOT.
- `device_2d.py:287-288` — passes `t_ox_um` straight to `device.threshold_voltage`. Electrical. Fine.
- `device.oxide_field` — computes `gate_charge/EPS_OX`; **does not read `t_ox` in code at all** (only the
  docstring's `(V_GB−V_FB−2φ_F)/t_ox` equivalence). Under EOT that identity stays **self-consistent** —
  it becomes the *equivalent-oxide* field, not the physical field in the HfO₂ (which is lower by `3.9/κ`).
  Only caller is the conservation test (`test_device.py:242`). **Nothing breaks; flag the renaming in the
  docstring, do not "fix" the physics.**
- `locos_history.py`, `oxidation.py`, `coupling.py` — **physical** thickness (field oxide, Deal–Grove
  growth, moving boundary). **Never see the gate-stack knob**; F3 does not reach Phase 2's grown oxide.

**Load-bearing definition:** `die.t_ox_um` stays **the physically grown Deal–Grove thickness** — its
documented meaning. F3's EOT is computed *at the device read*, never folded back into `die.t_ox_um`.
(Same discipline as F2 keeping `die.R_s` access-only.) Otherwise the Phase-2 oxidation record silently
starts lying about what the furnace grew.

## Model class — RESOLVED AT BUILD (the search overturned the recalled form)

**Built: rectangular-barrier WKB, `α = 2√(2 m* φ_B)/ħ`, with `(φ_B, m*)` carried PER MATERIAL.** The
plan's single-λ form is *only* valid within one material. Resolutions:

- **The correction (open Q5, and a plan error).** κ ↔ band gap are **inversely correlated** (Robertson
  Table 2 / Fig. 5): buying κ costs barrier. Both `φ_B` **and** `m*` enter under the *same* √, so they
  move as a **pair** — a per-material `φ_B` with a shared `m*` is a *half-physical middle* that still
  overstates the win (advisor). SiO₂ (3.2 eV, 0.5 m₀) decays **~3.2× faster per nm** than HfO₂ (1.4 eV,
  0.11 m₀) ⇒ HfO₂'s 6.4× thickness → **~2×** exponent, **+5.6 decades** at EOT=1 nm (lit. ~3–5). ✅
- **Why the discriminator is untouched.** `C_ox = ε_SiO₂/EOT` with `EOT ≡ t_phys·3.9/κ` expands to
  **`ε₀·κ/t_phys`** — Robertson's own eq. (1), the *true physical capacitance*. The EOT route is an
  **identity with zero barrier physics in it**, so `V_t`/`I_Dsat` invariance is unconditional and
  `device.py` needs no change. The barrier only moves leakage *magnitude*. (Asserted against the real
  `device.py` in the tests — that assertion **is** the "don't touch device.py" proof.)
- **Anchors — VERIFIED (all from Robertson, *Eur. Phys. J. Appl. Phys.* **28**, 265 (2004), Table 2, as
  one coherent set):** κ(SiO₂)=**3.9**/φ_B=**3.2 eV**; κ(HfO₂)=**25** (the plan's "20–25" → pinned
  25)/φ_B=**1.4 eV**. The wall is **~1.4 nm** (plan recalled ~1.2). `m*` is **FLAGGED** (fit-extracted:
  SiO₂ ~0.5, HfO₂ 0.11 ± 0.03, spread **0.08–0.2** — the dominant uncertainty, banding the win 3.9–9.5
  decades). *Note the source swap: Wilk/Wallace/Anthony was not reachable; Robertson is the better fit
  (it carries the κ↔gap correlation the headline needs).*
- **The non-circular cross-check (unplanned, and the reason for going fully explicit).** The cited pairs —
  sourced from band-offset/effective-mass work, **never fitted to a leakage curve** — *predict* the
  textbook **~1 decade per ~2 Å** SiO₂ slope (model: **1.78 Å**). A calibrated per-material λ (the
  advisor's alternative) is fitted *from* leakage data and could never make this check. Same spirit as
  Irvin-vs-Masetti elsewhere in the repo.
- **Honest flagging (the F2 discipline).** The prefactor `J0_REFERENCE` is a **house lump** pinned at one
  cited SiO₂ point (1.5 nm → 1 A/cm² @1 V) and **shared across materials** — which is the *honest* choice,
  not a shortcut: any per-material prefactor would be invented, and sharing makes it **cancel exactly** in
  every fixed-EOT ratio, so `leakage_decades_saved` contains **no calibrated constant at all**.

## What to touch (enumerated)

- **New physics module `chip/high_k.py`** — `eot()` (the `t_phys·3.9/κ` identity), `gate_leakage()` (the
  tunneling `J_g`), and a small `GateStack` record. Pure, cited, unit-tested. Mirrors `contact_resistance.py`.
- **`fab_game/recipe.py:DeviceKnobs`** — a `dielectric` knob (`None` default = seam), sibling to F2's
  `contact_scheme`. Carries `(material/κ, t_phys)`.
- **`fab_game/steps.py:device_step`** — compute `EOT` → pass as the existing `t_ox_um` argument; emit
  `gate_leakage` as a **new additive output**, only when engaged (the established fingerprint pattern, so
  clean records stay byte-unchanged).
- **`chip/device.py` — DO NOT TOUCH.** The audit above is the proof.
- **Historical demo + Tier-2 history mode** (`chip/highk_history.py` + `demo_highk_history.py`) — the
  `t_ox` scaling ladder into the leakage wall, then the HfO₂ escape at matched EOT. Gallery rung; figure.
- **`memory/high-k-dielectric-source.md`** — cited constants (project citation discipline).

## Scope discipline (the honest NO's)

- **Metal gate: FLAG, DON'T BUILD.** It rode in *with* high-κ in 2007 but for a **different**
  discriminator (poly-depletion + Fermi-level pinning → work-function `V_t` tuning). Building it here
  dilutes the single clean leakage-wall payload. Name it as a scope edge; it can be its own slice if the
  `gate` work-function knob ever wants deepening.
- **Interfacial SiO₂ layer: name it, decide core-vs-edge at build.** A real stack is
  `EOT = t_IL + t_hk·(3.9/κ)` — the honest reason EOT scaling *also* stalled (you can't get below the IL).
  Cheap, and a genuine teaching point (the ceiling on the escape). **Lean: include** — it costs one term
  and it stops the model claiming unlimited EOT scaling. `t_IL = 0` is a clean sub-seam.
- **No quantum-mechanical / poly-depletion EOT corrections** in the core (`C_ox` inversion-layer
  thickening). Named edge.
- **No `t_ox` physical-meaning change.** EOT is computed at the device read, never written back.
- **No new junction-leakage coupling.** Gate leakage is a *separate channel* (tunneling, not SRH
  generation) — additive, never folded into `lifetime.py`'s `device_leakage`, and it **never moves**
  `V_t`/`I_Dsat` (the same discipline as `BV` and the SRH leakage).

## The knob's parameterization — RESOLVED AT SLICE 2 (material-only, EOT = the inherited `t_ox`)

`DeviceKnobs.dielectric` is a **registry key and nothing else** (`"SiO2"`|`"HfO2"`|`"TiO2"`, `None` = the
seam) — a clean parallel to F2's `contact_scheme`. It **re-implements the incumbent electrical gate in the
chosen material**: the inherited `die.t_ox_um` is read as the stack's *target EOT*, and `gate_stack()`
reports the `t_phys = EOT·κ/3.9` that target needs. The alternative — a knob carrying an explicit deposited
`(material, t_phys)` — was **rejected** at build:

- **Slice 1's API is already EOT-target-shaped.** `gate_stack(eot_um, …)` and `leakage_decades_saved(eot_um,
  …)` both take **EOT**; an explicit-`t_phys` knob would fight that signature and make every caller
  pre-compute `physical_thickness_for_eot` by hand.
- **It is F2's precedent exactly.** `contact_scheme` reads `die.R_s` and feeds it through a richer model
  without writing back; F3 reads `die.t_ox_um` the same way. An explicit deposit would instead *discard*
  the Phase-2 grown oxide, cutting the device gate loose from the oxidation stage.
- **The `eot()` identity branch was built for this seam.** `if kappa == K_SIO2: return t_phys_um` exists so
  that `dielectric="SiO2"` reaches `device.threshold_voltage` with the *same float*. Only this
  parameterization exercises it — and it is what makes the engaged seam byte-for-byte rather than ≈.
- **No semantic overload on `t_ox_um`** (the honesty check this had to clear): the device read *already*
  treats `t_ox_um` as the **electrical** thickness — that is slice 1's identity insight, that physical and
  electrical merely *coincide* for SiO₂. The field keeps storing what the furnace grew and is never
  mutated; the matched-EOT counterfactual is the historical move itself (HfO₂ at 45 nm targeted the EOT the
  SiO₂ roadmap called for). A hybrid `(material, t_phys=None)` mode was rejected too: a second code path,
  a fragile seam (explicit SiO₂ only matches if the caller hand-passes `t_phys == t_ox`), and no consumer —
  slice 3's scaling ladder drives thinning through `die.t_ox_um` upstream anyway.

## Open questions — status after slice 2

1. **Where the leakage output lives — RESOLVED (slice 2).** `Die.j_gate` (A/cm²), a new field beside
   `bv_V`/`t_rr`, `None` on a bare/refused die *and* whenever the knob is off (the gap-vs-fake-zero rule).
   The record carries `dielectric`/`t_phys_um` in `knobs_in` and `j_gate_A_cm2`/`decades_saved` in
   `outputs`, **only when engaged** (the established fingerprint discipline → a knob-off device record is
   byte-unchanged). Not scored by any target: gate leakage is a *separate channel* from the SRH junction
   leakage — additive, never folded into `lifetime.py`'s `device_leakage`, and asserted not to move
   `j_leak`/`τ`/`t_rr`. A scoring window is a **later** decision (it would need the flagged absolute `J₀`,
   whereas `decades_saved` is prefactor-free).
2. **Demo home — RESOLVED (slice 3): `chip/demo_highk_history.py` alone, riding `chip/high_k.py` directly.**
   The lean ("standalone, the consumer is the *device*, not the furnace") was right about the *home*; the
   `highk_history.py` half was dropped — see the slice-3 header note. It lands as **B8** on the timeline
   (`stage="Gate dielectric"`, era ≈2000s), slotted between **B5** (isolation) and **B6** (metallization) —
   the gate stack's place on the process spine, not appended. Both gallery manifests are **glob-anchored**,
   so the demo file and both rungs had to land in the same commit or `assert_manifest_complete()` fails.

   ⚠️ **The magnitude trap slice 3 inherits (raised at slice 2, do not walk into it).** Slice 2's driven
   numbers — HfO₂ `j_gate` = 1.1e-14 A/cm² at `t_phys` = 12.8 nm, a 22-decade span across the registry,
   **+11 decades saved at EOT = 2 nm** — are **extrapolated outside the regime the model is validated in**
   (direct tunnelling, ~1–1.5 nm EOT). Real HfO₂ at ~13 nm is **trap-limited, not tunnel-limited** (already
   a named module scope edge), and lit. puts the win at **~3–5 decades at EOT = 1 nm**. Internal to slice 2
   (nothing renders them), but a *demo* puts them in front of a student, where +11 decades would read as a
   datasheet claim it is not. **Slice 3 must therefore:** (a) **cap the ladder near EOT ≈ 1–1.5 nm** — the
   era's actual wall — rather than walking it to 2–3 nm where the HfO₂ advantage is dramatically
   overstated; (b) feature `decades_saved` with the module's own caveat (**"≳ N decades**, exponent-
   dominated"; trap floor not modelled); and (c) lead with the **shape** (monotone, sign, the wall) —
   which is the honest payload — not the absolute count.
3. **Interfacial layer core-vs-edge — RESOLVED: its own slice. ⚠️ This REVERSES the plan's "lean:
   include", and the reason is the build's physics correction.** With the barrier now in the model an IL
   is a **series tunnel barrier**, not merely a series capacitance. Carrying it on the `C_ox` side only
   (`EOT = t_IL + t_hk·3.9/κ`) while ignoring the barrier it adds would be *exactly* the half-physical
   middle this module rejects everywhere else. It stays a **named scope edge in the module docstring**
   (the honest EOT floor) until it can be built on both sides at once.
4. **Which high-κ anchors "modern" — RESOLVED: HfO₂ (κ=25, φ_B=1.4).** Registry is SiO₂ + HfO₂ + **TiO₂**
   (κ=80, φ_B=**0**) as the counterexample. Al₂O₃/ZrO₂/La₂O₃/Si₃N₄ are **docstring table rows only**:
   their `m*` is not separately sourceable, and a `Dielectric` without a cited `(φ_B, m*)` pair could only
   carry an invented exponent. TiO₂ needs no `m*` — at `φ_B=0`, `α=0` for *any* mass, so the "κ=80 buys
   20× the thickness and still leaks" lesson is **mass-independent**. Robertson's requirement 4 (offset
   >1 eV) thus falls out **computed**, not asserted: **"more κ is better" is false, for free.**
5. **Tunneling form — RESOLVED:** rectangular-barrier WKB with per-material `(φ_B, m*)`. See "Model
   class". Bias dependence (trapezoidal/field-lowering, image-force) is a **named scope edge**: the
   barrier is rectangular at a fixed reference bias, valid in the direct-tunnelling regime (`V_g < φ_B`)
   the 1.2–2 nm era stacks live in.
