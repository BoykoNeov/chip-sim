---
name: litho-aerial-image-source
description: "Microchip P3: cited Rayleigh k₁ (0.25 two-beam / 0.5 coherent / ~0.28 best) + NILS=CD·d(lnI)/dx printability rule that litho.py benchmarks against"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 054186d1-0f35-4a9d-ae1e-502e7595d2e4
---

Microchip **Phase 3 (lithography aerial image)** benchmark constants, pinned at build
(2026-06-09) — the `[[…-source]]` discipline (cited, not from memory). Source: **Chris A.
Mack, lithoguru.com** (the free online teaching corpus behind *Fundamental Principles of
Optical Lithography*, Wiley 2007); corroborated by Levinson *Principles of Lithography* and
Wong *Resolution Enhancement Techniques in Optical Lithography* (SPIE).

**Rayleigh resolution** `R = k₁·λ/NA`, with `R` the resolvable **half-pitch** (CD):
- **k₁ = 0.25** — the *physical lower limit*, **two-beam imaging** (extreme off-axis / dipole:
  the 0th and one 1st order span the full pupil 2·NA/λ). "The lowest we can go."
- **k₁ = 0.5** — the conventional **coherent** (on-axis, three-beam ±1) half-pitch limit.
- Early processes k₁ = 1.0; **today's best ≈ 0.28** (so 0.25 is a hard floor, not reached).
- Two-beam vs conventional = **50 % resolution improvement** + enhanced depth of focus.
  Source: Mack, *Lecture 48 — Resolution and Immersion* (lithoguru.com/scientist/CHE323/Lecture48.pdf).

**NILS — normalized image log-slope** (the printability metric):
- `NILS = w · d(ln I)/dx` evaluated at the **feature edge**, `w` = nominal feature width (CD).
  "The best single metric to judge the lithographic usefulness of an aerial image" — a steep
  bright→dark transition = good edge definition.
- Printability rule of thumb: **NILS ≥ 1** = minimally resolved; each unit of NILS ≈ **+10 %
  exposure latitude** (EL ≈ 10·NILS at ±10 % CD), so the robust-process target is **NILS ≳ 2**
  (≈ 20 % EL). Source: Mack, *Using the Normalized Image Log-Slope* tutorials
  (lithoguru.com/scientist/litho_tutor/TUTOR32–36); IUE-Vienna Kirchauer thesis §3.2.2 (the NILS≥1 floor).

**How litho.py uses it** (the validated-vs-calibrated split). The k₁ values are **validated as a
consequence**, not echoed: the Abbe pupil-cutoff arithmetic *derives* k₁=0.5 (on-axis, ±1 just fit
`1/p ≤ NA/λ`) and k₁=0.25 (off-axis point, 0+1 span `1/p ≤ 2NA/λ`) — the off-axis source point makes
the two-beam cos² **emerge from the workhorse**. The **contrast/NILS-vs-pitch** benchmark curve is
asserted *loosely* (the trend: contrast → 0 as pitch → the cutoff; NILS falls below the printable
band there); the NILS≳2 rule is the cited calibration, not a derived fact. Non-circular: NILS/contrast
come from the optics (pupil + Abbe), the printability *threshold* is the external cited rule.

**v1.4 addendum — depth of focus, the Bossung curve, defocus-induced frequency doubling** (pinned
2026-06-10, same Mack source). `DOF = k₂·λ/NA²` (the *second* Rayleigh equation, companion to
`R = k₁·λ/NA`): resolution scales `λ/NA`, focus latitude scales `λ/NA²`, so pushing NA trades DOF
quadratically ("the litho squeeze"). **`k₂ = 0.5`** is **derived not cited cold** (the same
validated-as-a-consequence split as k₁): the on-axis three-beam image's fundamental nulls at defocus
phase `φ = π/2`, which at the resolution limit (`sinθ → NA`) lands at `z = λ/2NA²` → `k₂ = 0.5` — but
that value is **paraxial** (`1−cosθ ≈ NA²/2`), so the *exact* full-cosθ null sits ~24% inside it at
NA 0.85 and converges onto it as NA→0 (the honest high-NA caveat). The **Bossung curve** = printed
CD vs defocus at fixed dose (the focus-exposure picture; the **process window** = the focus×dose
region holding CD in spec). **Defocus-induced frequency doubling / contrast reversal:** at the φ=π/2
fundamental null the *image* does NOT go flat — it collapses to a pure double-frequency fringe (the
defocus-independent 2nd harmonic survives), so the printability metric must read the **fundamental
coefficient**, not the max−min contrast. Source: Mack, lithoguru *Optical Lithography Modeling* /
the defocus & DOF lectures. Used by `litho.py` §7 (v1.4) — `defocus_phase`, `depth_of_focus`,
`fundamental_amplitude`; see [[litho-defocus-v14]].

Related: this is the chip project's one **genuinely-new** module (Fourier optics), chip-local not
promoted to `engines/` — see [[bigsim-program]]. Sits in the **export-control carve-out** (generic
textbook Fourier optics, no recipes/targeting). Companions: [[deal-grove-oxidation-source]] (P2),
[[dopant-diffusivity-source]] (P1a), [[peb-acid-diffusion-source]] (v1.7 — same Mack corpus + the
same Kirchauer IUE-Vienna thesis as the NILS≥1 floor pinned here).
