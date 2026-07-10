# Plan — F2 silicide / contact resistance (the two-term series-R the diffusion consumer flattened)

> **✅ BUILT 2026-07-10 as historical-mode B7.** `chip/contact_resistance.py` (TLM two-term series-R) +
> `chip/demo_silicide_history.py` + `chip/tests/test_contact_resistance.py` (10 tests); gallery rung
> `hist·B7`; `docs/figures/chip-silicide-history.png`. Consumer: `DeviceKnobs.contact_scheme` (None
> default = access-only seam) threaded through `fab_game/steps.py:device_step`; both `pipeline.py` call
> sites unchanged; `chip/device.py` untouched. Cited constants → `memory/silicide-contact-source.md`.
> **Advisor reframes at build:** the discriminator is the *exponent gap* (access linear, contact
> sublinear), not the "4.5×" number → per-scheme `ρ_c` carried freely; the `coth` moves the contact
> exponent (½ at long contacts → 0 / `R_sh`-independent at scaled sub-µm ones — the `ρ_c`/area regime
> where "lower `ρ_c` is the next frontier" lives); the robust tight leg is *contact-share rises as `R_sh`
> falls for any `ρ_c`*, and the bottleneck **flip** is a calibrated operating point. See below for the
> as-scoped plan (unchanged).

**The discriminating observable, stated first (the build's licence):** the parasitic source series
resistance `R_series` is **two terms with different exponents in the sheet resistance `R_sh`**, and no
single scalar can move both:

- **Access** (the diffused sheet under the contact-to-channel run): `R_access = R_sh · n_□` — **linear in
  `R_sh`**. This is what the diffusion consumer already models.
- **Contact** (the metal↔silicon interface, transfer-length model): `R_contact = √(ρ_c·R_sh)/W ·
  coth(L_c/L_T)`, `L_T = √(ρ_c/R_sh)` — **scales as `√R_sh`**.

Self-aligned silicide (salicide) shunts the S/D with a low-resistivity film, dropping `R_sh` ~20×. So
**access drops ~20× but contact drops only ~√20 ≈ 4.5×**. The device number that falls out for free and
that a fudge factor *cannot fake*: **silicide solves the access resistance so thoroughly that the
*contact* becomes the new bottleneck** — the historical reason contact engineering (lower `ρ_c`, more
contacts, later Ni over Ti/Co) became the next-era frontier. That crossover — two terms with different
`R_sh` exponents, one era-transition flipping which dominates — is the observable that clears the repo's
standing bar (**no regime without a consumer that discriminates**, the v1.6 "build explicit, NOT 2-D"
lesson). A pure "multiply `R_series` by 0.3" sheet shunt would *not* clear it; it would be decoration.

Standing consumer set by the user **2026-07-03**: **the game — historical processes, education.**

## The consumer (why this passes the bar)

1. **The `I_Dsat` source-degeneration seam is already wired.** `chip.device.saturation_current` already
   consumes `R_series_ohm` on the *source side only* (Sze–Ng: drain access does not reduce saturation
   current). F2 does **not** touch `device.py` — it feeds a *better-modelled* `R_series` into the existing
   quadratic. This is what makes F2 "the cheapest promotable step."
2. **Educational contrast (the named consumer):** the same wafer run **direct-Al → salicide** recovers
   `I_Dsat`, and the recovery is *lopsided* (access collapses, contact lingers) — you can watch the
   bottleneck move from access to contact. That lopsidedness is the teaching payload; a scalar can't show
   it.

## The seam — three states, and the byte-for-byte anchor is NOT an era

(Advisor correction to the naïve "silicide-off = direct-Al" framing.) Today's `R_series = R_s · n_□` has
**no contact term at all**. So *both* eras are departures from today; the byte-for-byte anchor is the
**ρ_c-free computation**, not the Al era:

| State | `R_series` | vs today |
|-------|-----------|----------|
| **ρ_c model OFF (default)** | `R_sh · n_□` (access only) | **byte-for-byte identical** ← the seam |
| **Direct Al (opt-in)** | `R_access(R_sh_diff) + R_contact(ρ_c^Al, R_sh_diff)` | **higher** (adds a high-ρ_c contact term) |
| **Salicide (opt-in)** | `R_access(R_sh_sil) + R_contact(ρ_c^sil, R_sh_sil)` | **lower** (both terms shrink, access more) |

**Load-bearing definition:** `die.R_s` stays **purely the diffused access sheet resistance** (already its
documented meaning — verified in `fab_game/journey.py`: "diffused-layer **sheet resistance** `R_s`", never
lumped with contact). F2's contact term is **additive on top of** the existing `R_sh·n_□`, never folded
into `die.R_s`. This prevents double-counting the moment a contact term exists.

## Model class (search for the constants at build — do NOT recall)

- **Transfer-length model (TLM):** `R_c = (√(ρ_c·R_sh)/W)·coth(L_c/L_T)`, `L_T = √(ρ_c/R_sh)`. Cite
  **Schroder, *Semiconductor Material and Device Characterization*** (TLM chapter) and/or **Plummer Ch. on
  contacts / Sze–Ng §3**. The `coth(L_c/L_T)` current-crowding saturation is ~free once `L_T` exists —
  include it (it *is* the "bigger contact buys nothing past `L_T`" lesson) but the `√(ρ_c·R_sh)` term is
  the minimum honest core.
- **Constants to cite (sanity bounds only — re-check anything landing wildly outside):**
  - direct Al–Si `ρ_c ≈ 10⁻⁶ Ω·cm²`; silicide `ρ_c ≈ 10⁻⁷–10⁻⁸ Ω·cm²`
  - diffused S/D sheet `R_sh ≈ 50–100 Ω/□`; silicide sheet `R_sh ≈ 1–10 Ω/□`
  - Salicide films: TiSi₂ / CoSi₂ / NiSi (the era ladder).
- **Optional depth, flag don't build:** the **TiSi₂ C49→C54 narrow-line resistivity wall** — a real
  era-transition observable (why the industry moved Ti→Co→Ni). Name it as a scope edge; build only if we
  later want the CoSi₂/NiSi arc.

## What to touch (enumerated)

- **New physics module** `chip/contact_resistance.py` — the TLM `R_contact` + access-with-shunt
  `R_access`. Mirrors F1's physics-module shape (`diffusion_dopant.py §5`). Pure, cited, unit-tested.
- **`fab_game/steps.py:322`** — the consumer swap. Today: `R_series = die.R_s * sd_contact_squares`. New:
  `R_series = R_access(tech) + R_contact(tech, ρ_c, R_sh, W, L_c)`, behind a `contact`/`silicide` knob.
  Knob absent / ρ_c-model off → **exactly today's value** (the seam; keep the `R_series_ohm` record key
  emitted only when engaged so clean records are byte-unchanged, per the established fingerprint pattern).
- **`chip/device.py` — DO NOT TOUCH.** Confirm-in-plan: the `R_series_ohm` seam already consumes the
  source-side total correctly.
- **Historical demo** — a direct-Al → salicide `I_Dsat`-recovery figure for the history gallery (fits the
  existing tier-2/`HistoryMode` consumer pattern used by B5/B6). Decide at build whether it's a standalone
  `*_history.py` mode or folded into the metallization arc adjacent to B6 (`metallization_history.py`).
- **`memory/silicide-contact-source.md`** — cited constants + TLM form (project citation discipline;
  sibling to `aluminium-spiking-source.md`).

## Scope discipline (the honest NO's)

- **No new `device.py` physics.** The seam is sufficient; adding short-channel/drain-side terms here would
  be over-build.
- **Minimum honest core = the two-term (access + `√(ρ_c·R_sh)` contact) model.** Sheet-shunt-only is a
  scalar → rejected. `coth` saturation kept (≈free). C49→C54 wall deferred as a flagged edge.
- **`die.R_s` meaning unchanged** — access-only; contact is additive downstream.

## Open questions to resolve at build

1. **Contact geometry inputs** — `L_c` (contact length) and `W` for the TLM. Reuse the journey's existing
   `sd_contact_squares` / `width_um` geometry, or introduce a minimal contact-length knob? (Lean: derive
   from existing geometry to avoid a new knob.)
2. **Demo home** — standalone silicide history mode vs. extension of the B6 metallization arc.
3. **Which silicide anchors the "modern" era** — TiSi₂ (period-correct 1980s salicide) vs NiSi
   (present-day). Pick per the history arc we want to teach.
