# Plan — F3 high-κ gate dielectric (the EOT/leakage split one thickness can't carry)

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

## Model class (search for the constants at build — do NOT recall)

- **Direct tunneling** through the gate stack. The minimum honest core is the **exponential dependence on
  physical thickness** — that is the tight leg. Candidate forms to check at build: WKB / Fowler–Nordheim
  vs direct-tunneling (Schuegraf–Hu) — pick per what's citable, prefer the simplest form that carries the
  exponential and the `V_g` dependence.
- **Anchors to verify at build (bounds only — re-check anything landing wildly outside):**
  - `κ`: SiO₂ **3.9** (already pinned as `EPS_OX` in `device.py`); HfO₂ **≈20–25** (verify).
  - The SiO₂ leakage wall: **~1.2 nm** and roughly **~1 decade of `J_g` per ~2 Å** (verify — this slope is
    the model's whole calibration).
  - Candidate sources: **Wilk / Wallace / Anthony, "High-κ gate dielectrics", JAP 89:5243 (2001)**;
    **ITRS gate-leakage-vs-EOT** curves; Plummer/Sze gate-tunneling section.
- **Honest flagging (the F2 discipline):** the tunneling **prefactor / absolute A/cm²** is
  **CALIBRATED-flagged**. The **robust tight leg** is the *sign and the exponent*: at fixed EOT, growing
  `t_phys` by `κ/3.9` collapses `J_g` exponentially while `C_ox` is **exactly** invariant. That invariance
  is an **identity**, not a fit — it is the assertable test.

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

## Open questions to resolve at build

1. **Where the leakage output lives** — a new field on the device record, alongside the existing
   `leakage`/`BV`/`t_rr` additive outputs? (Lean: yes, and refuse/`None` on a bare die like the others.)
2. **Demo home** — standalone `highk_history.py` Tier-2 mode vs. an extension of the A3 oxidation arc
   (`oxidation_history.py`). (Lean: standalone — the consumer is the *device*, not the furnace.)
3. **Interfacial layer in the core or flagged?** (Lean: core, `t_IL=0` seam — see above.)
4. **Which high-κ anchors "modern"** — HfO₂ is the 2007/45 nm-correct choice; Al₂O₃/ZrO₂ are era
   co-travelers worth at most a constant-table row.
5. **Tunneling form** — direct-tunneling closed form vs. a simpler cited `J(t_phys, V_g)` fit. Pick per
   what is *citable*, not what is prettiest.
