---
name: high-k-gate-f3
description: "project (2026-07-15 → slice 3 BUILT 2026-07-17): F3 high-κ — EOT is an IDENTITY (device.py untouched); knob = material-only; B8 demo rides high_k.py (no Tier-2 wrapper); ladder capped at the honest regime. Only the IL slice remains"
metadata: 
  node_type: memory
  type: project
  originSessionId: b2dd0b8e-9346-4717-9573-14712a863ee8
---

**F3 slice 1 BUILT (2026-07-15)** — `chip/high_k.py` + 23 tests, fast lane green, **no existing file
touched** (`device.py` included, as scoped). Plan: `docs/plans/high-k-metal-gate-f3.md`. Constants:
[[high-k-dielectric-source]].

**The payload.** One gate thickness feeds **two currencies with different functional dependence**:
`C_ox = ε_ox/EOT` (**linear**, electrical) vs `J_g = J₀·exp(−α·t_phys)` (**exponential**, physical). At
fixed EOT, HfO₂ (κ=25) is **6.4× thicker** while `V_t`/`I_Dsat` sit **exactly** still → leakage collapses.
No scalar can fake it. (Era: SiO₂ hit the wall ~1.4 nm; HfO₂ shipped at 45 nm in 2007.)

**Why `device.py` is untouched — the identity, not a favour.** `C_ox = ε_SiO₂/EOT` with `EOT ≡ t_phys·3.9/κ`
expands to **`ε₀·κ/t_phys`** = Robertson eq. (1), *the true physical capacitance*. So feeding EOT into the
existing SiO₂ path is **correct physics with zero barrier content**, and `V_t`/`I_Dsat` invariance is
**unconditional** for any material. **The test asserts this against the real `device.py`** — that assertion
*is* the "don't touch device.py" proof. (Scope-time audit also found `oxide_field` never reads `t_ox` in
code — only its docstring's equivalence, which becomes the *equivalent*-oxide field. Don't "fix" it.)

**THE FINDING — the search overturned the plan's model.** Plan (and recall) had `J_g ∝ exp(−t/λ)`, single
λ: **wrong across materials.** κ ↔ band gap are **inversely correlated** (Robertson Fig. 5), so oxides that
buy thickness *also* have lower `φ_B` **and** lower `m*`, both entering as `α ∝ √(m*·φ_B)`. SiO₂
(3.2 eV, 0.5) decays **~3.2× faster/nm** than HfO₂ (1.4 eV, 0.11) ⇒ **6.4× thickness → only ~2× exponent**
(+5.6 decades @EOT=1 nm, lit. ~3–5). **The discriminator was NOT affected** — only leakage *magnitude*.

**Advisor (reconciled, not overruled).** It warned against the **half-physical middle** (per-material `φ_B`
+ shared `m*` — still overstates; Yeo's FoM is barrier AND mass AND κ) and leaned toward bundling into a
**calibrated per-material λ**, making fully-explicit *conditional on `m*` being citable*. It is
(SiO₂ ~0.5; HfO₂ 0.11±0.03) → **took the fully-explicit branch**, because it buys a **non-circular
cross-check a calibrated λ structurally cannot**: constants never fitted to leakage *predict* the textbook
**~1 decade per 2 Å** SiO₂ slope (model: **1.78 Å**). Advisor was also right that the κ-optimum is **free**
— don't build it (see below).

**Two design moves worth keeping.**
- **Shared prefactor is the HONEST choice, not a shortcut.** Any per-material `J₀` would be *invented*;
  sharing makes it **cancel exactly** in fixed-EOT ratios → `leakage_decades_saved` has **no calibrated
  constant in it at all**. Flagged magnitude, cited ratio.
- **"More κ is better" is FALSE — computed, not asserted, and for free.** TiO₂ (κ=80, φ_B=**0**) → `α=0`:
  buys 20× thickness, leaks flat out at every thickness. Needs **no `m*`** (mass-independent at φ_B=0), so
  Robertson's requirement-4 (offset >1 eV) falls out of the cited table with zero extra machinery.

**Open-question reversal:** the **interfacial layer** flips from the plan's "lean: include" to **its own
slice** — with the barrier now modelled, an IL is a **series tunnel barrier**, not just a series
capacitance; carrying it on the `C_ox` side only would be the very half-physical middle the module rejects.
Named as a scope edge (the honest EOT floor).

---

**SLICE 2 BUILT (2026-07-17)** — the game knob + wiring: `DeviceKnobs.dielectric` (registry key, `None` =
seam), `Die.j_gate`, `steps.py:device_step`, `fab_game/tests/test_gate_dielectric.py` (8 tests). Fast lane
green; **`device.py` AND `chip/high_k.py` both untouched** — slice 2 is pure wiring. Footprint matches F2's
exactly (`recipe.py` + `steps.py`; no dashboard/guide/TUI surface enumerates knobs).

**THE DESIGN CALL — the knob carries the MATERIAL ONLY and reads the inherited `die.t_ox_um` as the stack's
*target EOT*** (the matched-EOT historical move), NOT an explicit deposited `(material, t_phys)`. Advisor
confirmed, three reasons: (1) **slice 1's API is already EOT-target-shaped** — `gate_stack(eot_um, …)` takes
EOT, so an explicit-`t_phys` knob fights its own signature; (2) **it is F2's precedent exactly** —
`contact_scheme` reads `die.R_s` through a richer model without writing back (explicit deposit would instead
*discard* the Phase-2 grown oxide, cutting the gate loose from oxidation); (3) **the `eot()` identity branch
was built for this seam** — `if kappa == K_SIO2: return t_phys_um` exists so `"SiO2"` reaches
`threshold_voltage` with the *same float*; only this parameterization exercises it.

**The honesty worry, resolved (worth not re-litigating):** reading `t_ox_um` as an EOT target is *not* a new
semantic overload — the device read **already** treats it as the electrical thickness; that IS slice 1's
identity insight (physical and electrical merely *coincide* for SiO₂). The field keeps meaning "what the
furnace grew" and is never written back (F2's `die.R_s` access-only discipline). Hybrid
`(material, t_phys=None)` rejected: 2nd code path, fragile seam, no consumer.

**What slice 2 proved that slice 1 could not.** The `device.py`-untouched claim is only assertable *here*,
against the real device model: at fixed EOT, `V_t`/`I_Dsat`/`C_ox` come out **byte-for-byte identical for
all 4 materials** while `j_gate` spans 22 decades. **Why the invariance is exact — stronger than the
identity framing** (advisor): `steps.py` passes `die.t_ox_um` *as* the `eot_um` arg and `gate_stack` echoes
it back, so `t_ox_electrical_um` is the **same float** for every material — at the wiring level this is the
trivially-exact "same input → same output", not a float-identity round-trip (that's slice 1's job, tested
there). The test still earns its keep: had the wiring fed `t_phys`, `hfo2.V_t == sio2.V_t` would fail.
Driven @EOT=2 nm: SiO₂ `t_phys`=2 nm/1.5e-3 A/cm²; HfO₂ 12.8 nm/1.1e-14 (+11.1 dec — decades ∝ EOT, so ≈2×
the +5.6 @1 nm); TiO₂ 41 nm/**2.8e+8** (= `J₀` exactly, −11.3 dec — 41 nm of dielectric buys *nothing*).
SiO₂ @1.5 nm reads exactly 1.000 A/cm² — the Robertson calibration anchor showing through.

⚠️ **DO NOT FEATURE THOSE MAGNITUDES LITERALLY (slice-3 trap, advisor).** The "22 decades" / HfO₂ 1.1e-14 @
12.8 nm numbers are **extrapolated outside the validated direct-tunnelling regime (~1–1.5 nm EOT)** — real
HfO₂ at ~13 nm is **trap-limited, not tunnel-limited** (already a named module scope edge), and +11 dec
@EOT=2 nm vs lit **~3–5 @1 nm** would read as a datasheet claim it is not. Internal-only in slice 2 (fine).
**Slice 3 must:** cap the ladder near **EOT ~1–1.5 nm**, and feature `decades_saved` with the "**≳ N**,
exponent-dominated, trap floor not modelled" caveat. **Ladder = the wall:** 3→1.2 nm EOT costs SiO₂ **10
decades** of leakage (the *shape* is the payload; the sign/monotonicity is the honest claim).

**Ladder/seam ordering (the teaching shape):** `None` (nothing emitted, byte-for-byte today) → `"SiO2"` (the
*engaged* seam — same device, leakage readout **ON**) → `"HfO2"` (same device, leakage gone). Fingerprint
keys only when engaged; `j_gate=None` on knob-off/refused/bare (gap ≠ fake zero). Gate tunnelling asserted
**separate** from [[fab-game-g4b]]'s SRH channel (`j_leak`/`τ`/`t_rr` unmoved). **Not scored by any target
yet** — a window would need the flagged absolute `J₀`, whereas `decades_saved` is prefactor-free.

---

**SLICE 3 BUILT (2026-07-17)** — `chip/demo_highk_history.py` = **B8**, the 8th timeline mode + both gallery
rungs + `test_demo_highk_history.py` (7 tests). Fast lane green (1048). **`device.py`, `high_k.py`, `fab_game/`
all untouched** — slice 3 is a display surface. Slotted **B5→B8→B6** (the gate stack's place on the process
spine, not appended).

**NO `highk_history.py` — a deliberate deviation from the plan's own "What to touch"** (that line predates F2).
Advisor concurred: a Tier-2 `*_history.py` earns its place only by carrying **period physics the base lacks**
(A2 blur, A4 swelling, B5 beak); `high_k.py` already holds SiO₂/HfO₂/TiO₂ as registry entries and
`gate_stack()` is *documented* as "the demo's unit of comparison" → a wrapper = zero physics. **B7 is the
precedent** (`contact_resistance.py` + `demo_silicide_history.py`, no `silicide_history.py`). Rule of thumb:
**demo rides the base module unless there's distinct period physics to hold.**

**The magnitude trap governed the build (it was the acceptance criterion, not a caveat).** Ladder capped at
**EOT = 1.0 nm** — the 45 nm target, *inside* the validated direct-tunnelling regime — where the model lands
**on top of published data** (SiO₂ 6.5e2, HfO₂ 1.8e-3 A/cm²) and the featured win is **+5.6 dec** (m* band
3.9–9.5; lit ~3–5). Wall reads **EOT ≈ 1.50 nm** (the J₀ anchor showing through). **The trap has a SECOND
end nobody flagged:** off the *thick* end HfO₂ runs to ~**1e-22 A/cm²** (meaningless — trap-limited long
before). Fix = the left panel's **display floor as an honesty device**: curves **exit the axis** rather than
print a fabricated number, which *also* un-squashes the SiO₂ wall (the payload) from ⅓ of the panel. **2 of
7 tests are honesty guards, not physics guards** (ladder cap; never round a "≳ N" claim **up** — 5.6 must not
read 6), pinned because they're claims about *where the model may speak*.

**The bug the build caught (worth remembering — it nearly shipped).** At a 1 nm gate `Q_dep/C_ox` collapses →
unadjusted n-MOS reads **V_t ≈ 0.02 V**, a device that never turns off, headed for a student-facing figure.
Fix = the **V_t-adjust implant `device.py` already had** (§5 `implant_dose`/`implant_kind`, cf. `demo_implant`)
→ V_t ≈ 0.35 V. **Cannot disturb the invariance**: ΔV_t = q·dose/C_ox reads the *same* C_ox all 3 share
(asserted). Lesson: a *representative* recipe at a scaled node isn't representative without the era's knobs.

**Remaining F3:** the **interfacial-layer** slice only (series tunnel barrier + series capacitance, both sides
at once — the honest EOT floor). Then **F4 (BEOL interconnect RC)** = last PROMOTABLE roadmap step.

**ROADMAP CARD — USER DECIDED 2026-07-17: LEAVE IT until the IL slice lands.** So **"F3 ships" ≡ IL done**,
not slices 1–3 — the F3 card stays on `docs/roadmap.html` (schematic, "not simulator output") meanwhile, and
comes off with the IL slice. **Don't re-ask, and don't pull it early**; the card understating what exists
today is accepted cost. Rejected alternatives: pull now (treat IL as a follow-on), pull + add an `F3-IL` card.
([[roadmap-page]] graduation rule.)
