---
name: high-k-gate-f3
description: "project (2026-07-15 → COMPLETE 2026-07-17, all 4 slices): F3 high-κ — EOT is an IDENTITY (device.py untouched); knob = material-only; B8 demo rides high_k.py; the IL is additive on BOTH currencies → the honest EOT floor. Roadmap card PULLED; next = F4"
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

---

**SLICE 4 BUILT (2026-07-17) — the interfacial layer. F3 IS COMPLETE (all 4 slices); CARD PULLED.**
`high_k.py` §5 (`Layer`, `stack_eot_um`, `stack_tunnel_exponent`, `stack_leakage`, `eot_floor_um`,
`Dielectric.decay_per_eot_um`) + `gate_stack(…, t_il_um=0.0)` + B8's 3rd panel + 14 tests. Fast lane green
(**1062**). **`device.py` AND `fab_game/` untouched.** No IL game knob — advisor: the demo is the consumer,
a knob without one is the over-build the repo's bar rejects. (`fab_game` calls `gate_stack(t_ox, material)`,
so the `t_il_um=0.0` sub-seam covers it with zero game change.)

**THE SLICE IN ONE LINE: both currencies are ADDITIVE over series layers, each with its own per-layer
coefficient.** Series caps ⇒ EOTs add (`EOT = EOT_IL + EOT_HK`, Ando eq. 1 — cited); series barriers ⇒ WKB
exponents add (`Σ αᵢ·tᵢ`, each layer its **own** (φ_B, m*) — the path integral, not Ando). **`device.py`
survives AGAIN, same reason as slice 1:** a sum of series EOTs **is** an EOT → one number still arrives →
the invariance is now over stack **STRUCTURE**, not just material (asserted: a 2-layer stack and a 1-layer
SiO₂ gate at one EOT give identical `V_t`/`C_ox`).

**THE PAYLOAD — the IL is the *better barrier* and STILL a pure loss; only both sides together get the sign
right.** SiO₂ φ_B=3.2 > HfO₂ 1.4, so a **capacitance-only IL would have got the barrier term's sign
BACKWARDS** (not merely been incomplete — this vindicates the slice-1 deferral, harder than expected). The
tiebreak = the FoM **`α·κ/3.9` = exponent bought per nm of EOT *spent*** (`decay_per_eot_um`) — Yeo's
three-term (barrier AND mass AND κ) finally explicit: **SiO₂ 12.96/nm vs HfO₂ 25.78/nm**. The IL spends the
budget at **half value**, and that ~2× **IS the whole high-κ win, handed back**. Cost is **LINEAR**:
**−0.56 dec/Å**, hitting **exactly 0** at `t_IL = EOT` (high-κ squeezed out → a plain SiO₂ gate again).
**The floor and the cost are the same line.** ⚠️ The 0.557 dec/Å ≈ SiO₂'s own 0.563 thinning slope is a
**COINCIDENCE** (only because FoM ratio ≈2 ⇒ the difference ≈ SiO₂'s own value) — flagged as such, not a law.

**The floor = the module's TIGHTEST claim:** `EOT > t_IL·(3.9/K_IL)` for **any** κ (even κ=2000) —
geometric, prefactor-free, **zero barrier physics**. `gate_stack` **RAISES** below it rather than
extrapolating. This is why "just use more κ" was never the end of the story.

**FRAMING DECIDED BY A NUMBER, NOT A LEAN (advisor).** The IL halves the win (5.6 → 2.8 @EOT=1 nm). Whether
that reads "corrects an overstatement" or "brackets from below" turned on the lit matched-EOT figure →
searched: **~2–6 decades**, **WIDER than either model number** (⚠️ this **corrects** the earlier recalled
"~3–5"). So **both endpoints sit inside the band**, and the IL is **one mechanism spreading it, NOT the
explanation**. **Do not upgrade to "now matches published better."** → [[high-k-dielectric-source]].

**THE TRAP THE ADVISOR CAUGHT PRE-SHIP:** the demo's "HfO₂ 1.8e-3 lands on published data" is a **no-IL**
statement; with-IL reads ~1 A/cm² — **~3 decades apart, both can't stand unlabelled on one figure**.
**J₀ was NOT re-anchored** (the whole prefactor-free discipline rests on it being shared). Fix = plot both,
**labelled**: "idealized: no IL" vs **"as built (2007, 45 nm)"** — the **era label moved to the as-built
bar** (it had been sitting on the ceiling no fab can build). Pinned by an honesty test. The new 3rd panel is
**prefactor-free** (a ratio cancels J₀) — that's what earns it the headline.

**ROADMAP CARD PULLED** — the user's 2026-07-17 call (**"F3 ships" ≡ IL done**) discharged. Touched
`roadmap_gallery.py` `SLICES` + `roadmap_figures.py` `FIGURES` (`_draw_f3` deleted) +
`docs/figures/roadmap-f3.png` deleted + both editions regenerated; **the manifest guard pins
card↔schematic, so both must go together**. Graduation note left in the section subtitle (honest, not a
card). `future-steps.md` F3 row → ✅ BUILT. → [[roadmap-page]].

**NEXT: F4 (BEOL interconnect RC)** = the last PROMOTABLE roadmap step, now head of the queue.
([[roadmap-page]] graduation rule.)
