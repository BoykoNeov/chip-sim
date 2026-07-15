---
name: high-k-gate-f3
description: "project (2026-07-15): F3 slice 1 BUILT (chip/high_k.py) — EOT is an IDENTITY (device.py untouched); the search overturned the plan's single-λ; fully-explicit WKB predicts the 2 Å slope"
metadata:
  type: project
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

**Remaining F3:** `DeviceKnobs.dielectric` knob (`None` = seam) → `steps.py:device_step` (EOT into the
existing `t_ox_um` arg; `gate_leakage` as a **new additive output**, never folded into [[fab-game-g4b]]'s
SRH `lifetime.py` leakage and never moving `V_t`/`I_Dsat`) → `highk_history.py` Tier-2 mode + demo +
gallery rung. Then **F4 (BEOL interconnect RC)** is the last PROMOTABLE roadmap step.
