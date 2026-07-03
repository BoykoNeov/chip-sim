---
name: implant-pearson-skew
description: "ion-implant slice 2 — Pearson-IV skew (opt-in shape=\"pearson\"); boron negative skew → peak DEEPER than R_p"
metadata: 
  node_type: memory
  type: project
  originSessionId: 751a45fa-338a-4153-8f7c-acd8b1b19f39
---

Ion-implantation **slice 2 = Pearson-IV skew** BUILT (2026-07-03, `chip/diffusion_dopant.py` §5b;
plan `docs/plans/ion-implantation.md` slice 2 marked done). The tightened, *asymmetric* as-implanted
profile over slice 1's symmetric Gaussian ([[range-statistics-source]]).

**Seam:** new `Implant.shape` field, default `"gaussian"` = slice-1 bit-for-bit (whole existing suite
byte-identical, the opt-in discipline cf. implant=None); `"pearson"` opts into the four-moment form.
API: `skew_kurtosis(species,E)→(γ,β)`, `range_moments→(R_p,ΔR_p,γ,β)`, `pearson4_profile(...)`,
`_pearson4_coeffs`. `Implant.moments()`.

**The physics / the SIGN (cited, load-bearing):** a light ion (boron) **backscatters toward the
surface** → **NEGATIVE skewness γ** → **peak (mode) sits DEEPER than R_p** (mode = R_p+b1, b1>0) with a
longer tail toward the surface; γ grows *more negative* with energy (boron flips to +skew only sub-keV,
far below device energies). Cited: **Plummer, Deal & Griffin, *Silicon VLSI Technology* §8** — "light
ions backscatter to skew the profile up; heavy ions scatter deeper" (four-moment defs eqs 9–12) — and
the Pearson-IV-for-implant-profiles literature (*Radiation Effects* 46, 1980). The phrase "B skews
toward the surface" = TAIL toward surface = negative γ (NOT peak-toward-surface; that's +γ). Resolved a
genuine sign ambiguity: "positive skewness places the peak closer to the surface than R_p" → boron −γ →
peak deeper.

**The math (derived from scratch, self-verifying):** Pearson-IV = closed-form solution of the Pearson
ODE `d(ln p)/ds = (s−b1)/(b0+b1 s+b2 s²)`, s=x−R_p, a=b1; coeffs `D=10β−12γ²−18`,
`b0=−σ²(4β−3γ²)/D`, `b1=−γσ(β+3)/D`, `b2=−(2β−3γ²−6)/D` (σ=ΔR_p). Integrates to
`p=|denom|^(1/2b2)·exp[(2c/W)·arctan((2b2 s+b1)/W)]`, `c=−b1(2b2+1)/2b2`, `W=√(4b0b2−b1²)`. Reproduces
mean=R_p, var=σ² **EXACTLY** + γ,β by design (numerically verified to 4+ digits — the tight test legs,
catch any sign error). Mode at s=b1.

**Type-IV guard (honest cost):** needs complex denom roots (b2<0 AND 4b0b2−b1²>0); `pearson4_profile`
RAISES outside it (no negative-base power). Real boron kurtosis is ≈3 (Gaussian) but that's OUT of type
IV → β pinned into the ≳4 band → **γ magnitude AND β are house-calibrated/FLAGGED** (`_SKEW_KURTOSIS`,
boron only — other species raise, no fabricated skew). SIGN/TREND cited, numbers not table anchors.

**Truncation now TWO-SIDED** (vs Gaussian's surface-only): power-law |s|^(1/b2) tail loses dose at both
ends → analytic ∫=Q is a flagged two-sided leg; the TIGHT dose leg stays **structural** (sealed no-flux
`drive_in` conserves whatever grid-dose it's handed, shape-independent).

**Consumer:** the *existing* drive-in consumes the skewed IC (no new consumer needed — slice 2 tightens
an already-licensed regime, needn't independently clear the discriminating-consumer bar). Per advisor:
did NOT fabricate a V_t effect (skew is dose-conserving → V_t dose-only to first order); the x_j-shift
at matched (Q,R_p) is a named scope note, not built. Demo = `chip-implant-pearson.png` (Gaussian vs
Pearson-IV, 120 keV B, +8.6 nm mode shift). Remaining: slice 3 channeling tail, slice 4 damage→leakage.
[[range-statistics-source]] [[dopant-diffusivity-source]]
