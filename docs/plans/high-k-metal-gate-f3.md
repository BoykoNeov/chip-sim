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

## Open questions — status after slice 1

1. **Where the leakage output lives** — OPEN (slice 2, the `steps.py` wiring). Lean unchanged: a new
   field beside `leakage`/`BV`/`t_rr`, `None` on a bare die. `chip/high_k.py` already returns the
   `GateStack` record the consumer will read.
2. **Demo home** — OPEN (slice 3). Lean unchanged: standalone `highk_history.py` — the consumer is the
   *device*, not the furnace.
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
