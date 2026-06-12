---
name: litho-zernike-v110
description: "Microchip v1.10 lithographic Zernike aberrations (coma/astigmatism/spherical) BUILT 2026-06-12 (litho.py §10, 15-test mini-triad, fast lane 254→269): same v1.4 finding (a pupil PHASE, fits inside the module, no new path); THE load-bearing trap = fundamental_amplitude can't tell coma from defocus → use the COMPLEX-fundamental PHASE (coma=placement error); spherical rim-zero trap → interior pair; balanced Zernike forms + one φ_g scalar (astig H↔V split); no Strehl asserted"
metadata:
  node_type: memory
  type: project
  originSessionId: chip-litho-zernike-v110
---

Microchip **v1.10 — lithographic Zernike aberrations: coma, astigmatism & spherical** — BUILT
2026-06-12. Phase 3's §-named scope edge (**"aberration-free pupil apart from defocus"**) **promoted**
(the [[litho-defocus-v14]] / Massoud / [[chip-coupling-v12]] move). `chip/litho.py` §10 +
`demo_zernike.py` + `plots.zernike_figure`; 11 module (`tests/test_zernike.py`) + 4 demo
(`tests/test_demo_zernike.py`) tests; whole-repo fast lane **254 → 269** (+15). Banked artifact
`docs/figures/chip-zernike.png` (3 panels: coma's lateral image shift + the linear Δx-vs-coma inset | the
astigmatism H↔V through-focus best-focus split | the spherical through-focus family, peaks drifting with
pitch). **No engine touch, no ADR** (litho has no engine underneath — pure Fourier optics).

**The decisive finding (same as v1.4):** a Zernike aberration is a pure **phase** on the pupil, and
`coherent_image` already sums *complex* amplitudes — so it fits **inside the litho module with no new
code path**. `zernike_phase(f_total, img, ab) = exp(i·2π·W(u))` on the 1-D pupil slice the orders ride
(`u = f_total/f_cut`, |u|≤1), `W` = the standard **balanced-Zernike** radial polynomials (drop piston):
**coma** `(3u³−2u)·cosφ_g` (ODD), **astig** `u²·cos2φ_g` (EVEN), **spherical** `6u⁴−6u²` (EVEN). An
`Aberrations` frozen dataclass (coeffs in **waves** + `grating_azimuth_deg` φ_g) threaded through
`abbe_image`/`expose_grating` as `aberrations=None`; `None`/all-zero short-circuits to the float `1.0` →
unaberrated path **bit-for-bit** (all prior litho tests untouched). **Kept SEPARATE from `defocus_nm`**
(different convention: waves/paraxial-Zernike here vs v1.4's exact nm `1−cosθ` — folding them muddies both).

**THE load-bearing advisor fix (the v1.4 "assert the right observable" analogue):** the cos-only
`fundamental_amplitude` returns `4c₀c₁cosφ` for **BOTH** coma and defocus — it **cannot distinguish
them**. The discriminator is the **complex** fundamental `fundamental_complex(x,I,p) = 2·⟨I,e^{−2πix/p}⟩`
(Re ≡ `fundamental_amplitude`; **phase = the lateral fringe shift**): for the on-axis three-beam image
its phase is **exactly the ±1 order's aberration phase** — `0` for the even defocus, the coma shift for
the odd coma — to machine precision (verified 4.4e-16). So **coma is a pattern PLACEMENT error**, not a
contrast loss. Without this the test suite passes but is hollow (a coma test on `fundamental_amplitude`
would mirror a defocus test exactly).

**The mini-triad.** *Analytic (tight):* (a) the no-aberration seam **bit-for-bit** (`np.array_equal`);
(b) **parity** — an EVEN aberration (astig, spherical) leaves a symmetric two-beam pair **invariant** to
machine precision (equal even phase factors out of `|Σ|²`), the ODD coma gives the beams *opposite* phase
→ a **pure lateral shift**, contrast preserved (the v1.4 defocus-dipole-invariance, now driven by
PARITY); (c) the **coma↔defocus phase discriminator** (above). *Conservation (tight):* aberrations are
**unitary** — phase-only ⇒ `|c_m|²` untouched ⇒ `mean(image)=Σ|c_m|²=transmitted_power` at every
coefficient (the v1.4 leg extended for free; `transmitted_power` never sees the phase). *Benchmark
(loose):* coma → placement error (∝ coeff) + asymmetric image the **v1.7/v1.9 PEB cell refuses** (same
as the v1.4 off-axis-defocus refusal); astig → the **H↔V best-focus split** (φ_g=0 vs 90° focus at
opposite planes — what a defocus offset CANNOT mimic, the thing that makes astig ≠ defocus in 1-D);
spherical → **pitch-dependent best focus** (the balanced `−6u²`).

**Durable advisor calls / traps (the steering this build turned on):**
1. **Gating:** the approach is right, don't relitigate — pupil phase, fits inside the module, parity
   anchor + free conservation leg are sound. Build it.
2. **THE load-bearing trap — `fundamental_amplitude` can't separate coma from defocus** → the complex-
   fundamental phase (or sin/quadrature projection `−4c₀c₁sinφ`). The cleanest tight anchor, invisible
   to the v1.4 metric.
3. **The spherical rim-zero trap:** balanced `6u⁴−6u²` is **0 at the pupil rim u=±1** (and u=0), so an
   even-invariance dipole-at-rim test is *trivially* 0=0 for spherical (tests nothing). Use an
   **interior pair u=±1/√2** (where it peaks at −1.5); astig (`u²=1` at rim) is the clean nonzero rim
   even-invariance test. (Verified: rim spherical phase = 1.0 exactly, interior ≠ 1.)
4. **astig ≡ defocus is PARAXIAL only:** `u²` is the paraxial defocus form, but v1.4's `defocus_phase`
   is the *exact* `1−cosθ` — so the degeneracy is exact only as NA→0 (named, the same high-NA honesty
   as the k₂ gap). The φ_g H↔V split is the testable separator.
5. **Use the balanced Zernike forms** (the cited definition; spherical's built-in `−6u²` *gives* the
   pitch-dependent-focus signature for free) and **add the one φ_g scalar** (astig's H↔V split is its
   first-class deliverable — not over-building, the consumer is the named aberration).
6. **No Strehl/Maréchal number asserted** — it needs the 2-D pupil-disk integral, not a handful of 1-D
   slice samples; λ/14 (≈0.07 waves, Strehl 0.8) quoted only as **scale**, the honest discrete-1-D caveat.

**Demo numbers (193 nm ArF, NA 0.85, on-axis, pitch 350 nm):** coma 0.15 waves → **Δx = +25 nm** (7.2 %
of pitch) placement error; astig 0.25 waves → H/V best focus **∓122 nm** (244 nm split); spherical 0.08
waves → best focus **+87/+130/+158 nm** at pitch 290/340/390 (a 71 nm drift), unaberrated pinned at z=0.

**Scope edges named-not-modelled:** the **1-D pupil slice** of the 2-D Zernikes (orders sample only the
f_x axis — a true 2-D pupil would need contacts/2-D mask, the litho §3 ceiling); the **peak (Seidel-
balanced) coefficient in waves**, not the Noll RMS-normalized 2-D coefficient; **paraxial** astig≡defocus
degeneracy; **no Strehl/Maréchal** assertion; only the three named low-order Zernikes (no trefoil / higher
order). Source pin (balanced Zernike forms + the litho signatures + Maréchal scale) appended to
[[litho-aerial-image-source]] (Mack / Born & Wolf §9.2 / Noll 1976). Units stay litho-native **nm** (the
aberration coefficients in waves are dimensionless); notebook gains no section (as v1.1–v1.9).
