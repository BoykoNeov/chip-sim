"""Lithography: the aerial image — two-beam cos² anchor + Abbe sum-over-source (Chip Phase 3).

The pattern-transfer step, and the project's **risk phase** — so the tractability gradient lives
**inside this module**, not just in the scope ceiling. This is the chip project's **one genuinely-new
module**: where Phase 1a reused the PDE spine (dopant diffusion) and Phase 2 was a small
closed-form ODE (Deal–Grove oxidation), lithography is **Fourier optics** — and it stays *chip-local*
(`chip/litho.py`), **not** promoted to `engines/`: only chip uses it, so per the rule-of-three
it stays project-local until a stabilized interface has ≥3 uses (plan §2).

The model — diffraction-limited imaging of a line/space mask
------------------------------------------------------------
A photomask carrying a periodic **line/space** grating (pitch ``p``) diffracts the illuminating light
into discrete **orders** at spatial frequencies ``f_m = m/p``. The projection lens — a low-pass filter
of cutoff ``f_cut = NA/λ`` (the **pupil**) — collects only the orders with ``|f| ≤ f_cut``; the survivors
interfere in the wafer plane to form the **aerial image** ``I(x)`` (intensity vs position). Fewer orders
collected → a coarser image; when only the DC (0th) order survives, the image is flat and the pattern
**stops resolving**. The whole module is built on one primitive — :func:`coherent_image`, the squared
modulus of a sum of collected orders — used twice:

  * **Coherent two-beam imaging** (the exact anchor). Two equal beams (0th + 1st order) interfere to a
    pure ``4·cos²(πx/p)`` fringe (:func:`two_beam_image`). This is where the **Rayleigh resolution**
    ``R = k₁·λ/NA`` lives (``R`` = resolvable half-pitch): ``k₁ = 0.5`` for conventional on-axis
    (three-beam ±1) imaging, and the physical floor ``k₁ = 0.25`` for two-beam (extreme off-axis)
    imaging — both *derived from the pupil-cutoff arithmetic*, not echoed.
  * **Abbe sum-over-source** (the tractable workhorse, :func:`abbe_image`). Real illumination is
    **partially coherent**: a source of finite angular extent (partial-coherence factor ``σ``). Abbe's
    method sums the coherent sub-image from each **source point** incoherently over the source —
    deliberately **not** the 4-D Hopkins transmission-cross-coefficients (the litho tar pit; scope edge).

A **constant-threshold resist** (:func:`print_cd`) then clips the aerial image at a fixed intensity to
a printed **critical dimension** (CD) — *recipe in, feature out* (the Phase-4 device geometry).

Validation triad (plan §3) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight, on its idealization).** The exact two-beam image is ``4·cos²(πx/p)`` to
  machine precision (two **equal** unit orders through :func:`coherent_image` — pure trig). **Rayleigh
  emerges from the pupil**: on-axis, the ±1 orders just fit (``1/p ≤ f_cut``) at ``p = λ/NA`` → half-pitch
  ``λ/2NA`` = ``k₁=0.5``; with the off-axis source point (:func:`offaxis_source`) the 0th and a 1st order
  span the *full* pupil ``1/p ≤ 2·f_cut`` at ``p = λ/2NA`` → ``k₁=0.25`` — and at that pitch the pupil
  selects **exactly {0, +1}**, so the two-beam cos² *falls out of the Abbe workhorse itself*. **Scope
  edge, named (the §5 risk-phase gradient, *inside* the module):** v1 is **scalar** diffraction (no
  vector/polarization — honest only at low/moderate NA; immersion NA>1 needs the vector + index
  treatment), an **aberration-free pupil apart from defocus and the low-order Zernikes** (the
  **defocus** phase is modelled in **v1.4** — see below — and **coma/astigmatism/spherical** as a
  Zernike pupil phase in **v1.10** — see §10 below), **Abbe not
  Hopkins** (a *method* choice — same answer, different cost — named because Hopkins is the tar pit), a
  **constant-threshold resist** (the **PEB acid-diffusion blur** is modelled in **v1.7** — see §8
  below — but development kinetics are not: the clip is still a constant threshold, now applied to
  the *post-bake latent* image), a **1-D
  line/space** mask (no 2-D contacts / line-ends / OPC), and a **1-D uniform source line** (not the
  chord-weighted projection of a real 2-D circular σ-disk). These are named, not papered over — the same
  discipline as oxidation's Massoud thin-dry anomaly.

* **Conservation (tight) — power balance.** The **DC (zero-frequency) Fourier component of the aerial
  image equals the total optical power passed by the pupil**, ``Σ_collected |c_m|²`` (and for a single
  on-axis order that is just the zeroth order). This is Parseval: in ``|Σ_m a_m·exp(2πi f_m x)|²`` the
  cross terms sit at nonzero difference frequencies and average to zero, leaving the spatial mean equal
  to ``Σ|a_m|²``. So ``mean(``:func:`abbe_image```) == ``:func:`transmitted_power` — computed two
  independent ways (a squared-sum image vs a sum of squared amplitudes), agreeing to machine precision.
  A physical power-balance check, not merely a transform identity.

* **Benchmark (loose).** **Contrast and NILS vs pitch** vs the classic litho resolution curves: contrast
  ``(I_max−I_min)/(I_max+I_min)`` falls to 0 as pitch → the pupil cutoff (the pattern stops resolving),
  and **NILS** (normalized image log-slope, :func:`nils`) drops below the printable band — the ``k₁``
  trend as NA/σ vary. Pinned to a cited source (the ``[[litho-aerial-image-source]]`` note — Mack,
  *Fundamental Principles of Optical Lithography* / lithoguru.com; **not** from memory): ``k₁=0.25``
  two-beam floor, ``k₁≈0.28`` today's best, ``NILS ≳ 2`` for a robust process (~20% exposure latitude).

Units — litho-native nm; µm at the cross-module boundary
--------------------------------------------------------
=====================  ==============  =====================================================
quantity               unit           note
=====================  ==============  =====================================================
wavelength λ           **nm**          litho-native (365 i-line, 248 KrF, 193 ArF)
pitch p, position x    **nm**          feature sizes are quoted in nm near the resolution limit
spatial frequency f    **1/nm**        ``f_cut = NA/λ``; orders at ``m/p``
NA, σ, contrast, NILS  dimensionless   ratios — unit-agnostic
CD (printed feature)   **nm** + µm     ``cd_um = cd_nm·1e-3`` — µm is the cross-module length currency
=====================  ==============  =====================================================
The per-module native-units principle (Phase 1a was CGS-cm, Phase 2 µm-hour): litho computes in **nm**
(its data's native unit) and exposes the CD in **µm** at the boundary for the Phase-4 MOS geometry.
Because the image is built from ratios (``f·λ/NA``), the absolute length unit only enters through λ and
the position grid — so nm is a convenience, not load-bearing.

Validation boundary
-------------------
There is no shared engine here (litho *is* its own Fourier-optics computation), so its tests carry the
whole triad: the exact two-beam ``cos²`` + the Rayleigh ``k₁`` derived from the pupil (analytic), the
Parseval power balance computed two ways (conservation), and the contrast/NILS-vs-pitch trend against
the cited ``k₁``/NILS rules (benchmark, loose). The benchmark's strength rests on **citation fidelity**
(the ``k₁``/NILS values pinned to the published source — NOT a tautology, they could be miscited) plus
the independent tight legs (the cos² identity and the power balance, both to machine precision). The
``k₁`` values are themselves *validated as a consequence* of the pupil arithmetic, not calibrated — the
honest split.

v1.4 — defocus, the depth of focus, and the Bossung curve (the promoted scope edge)
-----------------------------------------------------------------------------------
The §-named "ideal in-focus pupil" edge, **promoted** (the steel-ferrite-bay / oxidation-Massoud move):
defocus is a pure **phase** aberration on the pupil, so it fits the existing machinery with no new path —
:func:`coherent_image` already sums complex amplitudes, and :func:`defocus_phase` multiplies each collected
order by ``exp(i·(2π/λ)·z·(1 − cosθ))`` keyed to its **full pupil coordinate** ``f_m + f_s``. ``z = 0``
returns the v1 image bit-for-bit (the degenerate seam). The mini-triad:

* **Analytic (tight).** (a) The degenerate seam (``z = 0`` → in-focus, bit-for-bit). (b) **A symmetric
  two-beam (dipole) image is defocus-invariant to machine precision** — both beams ride the pupil at the
  same ``|f|`` → an *identical* defocus phase that factors out of ``|Σ|²`` → the image is literally
  unchanged at every ``z`` (the "infinite DOF of the dipole"); an *asymmetric* two-beam (0 & +1) instead
  keeps its contrast but **shifts the fringe laterally** (a relative phase, a pattern-placement error, not
  a contrast loss). (c) **The on-axis three-beam fundamental is exactly ``4·c₀·c₁·cos φ``** — the
  :func:`fundamental_amplitude` projection onto ``cos(2πx/p)`` (NOT the contrast metric, which keeps the
  defocus-independent second harmonic ``4c₁²cos²ψ``), nulling at ``φ = π/2``. *That* null is the
  depth-of-focus event; past it the image is a pure double-frequency fringe (defocus-induced **frequency
  doubling / contrast reversal**, Mack).
* **Conservation (tight) — defocus is unitary.** Phase-only ⇒ ``|amplitude|²`` unchanged ⇒ the
  power balance ``mean(image) = Σ|c_m|² =`` :func:`transmitted_power` holds at **every** defocus to
  machine precision. A real check that the implementation added *phase*, not amplitude.
* **Benchmark (loose) + the k₂ tie.** The Bossung curve (CD vs defocus at fixed dose) broadens/collapses
  with ``|z|``; the usable defocus is the Rayleigh ``DOF = k₂·λ/NA²`` (:meth:`Imaging.depth_of_focus`),
  ``k₂ = 0.5`` **derived** from the ``φ = π/2`` fundamental null at the resolution-limited pitch
  (``sinθ → NA`` ⇒ ``z = λ/2NA²``), not cited cold — the same validated-as-a-consequence split as ``k₁``.

v1.7 (§8) — PEB acid-diffusion blur: the resist back-end is a diffusion solve (the promoted edge)
--------------------------------------------------------------------------------------------------
The §-named "constant-threshold resist (no acid diffusion / PEB blur)" edge, promoted — and the
finding inverts this module's founding line: litho, the chip's one module that "does not touch the
engine", now **rides it** — because the post-exposure bake IS the program's PDE. Exposure writes a
**latent acid image** (∝ the aerial image — the linear-exposure idealization, named below); the
bake diffuses it (Fick's law on the acid/PAC concentration); development clips the **diffused
latent image**, not the aerial image. That bake is ``engines.diffusion`` in **acid mode** — ``u`` =
latent acid, constant ``D``, ``Neumann(0)`` both faces (the cited sealed-film "no out-diffusion"
BC, Kirchauer §7.1.2) — run by :func:`peb_blur` on the **half-period symmetry cell** ``[0, p/2]``,
whose no-flux faces are the even image's mirror planes and whose Neumann eigenmodes ``cos(2πjx/p)``
are exactly the image's harmonics: the bounded engine solve IS the infinite periodic blur, not an
approximation of it. One knob survives: the **diffusion length** ``σ = √(2·D·t)``
(:func:`peb_diffusion_length`). The mini-triad:

* **Analytic (tight).** (a) The degenerate seam — ``σ = 0`` is the unblurred path **bit-for-bit**
  (:func:`peb_blur` returns its input untouched; ``expose_grating``'s default never enters the PEB
  branch). (b) **Per-harmonic Gaussian attenuation:** the engine blur multiplies each image
  harmonic ``cos(2πkx/p)`` by ``exp(−2π²k²σ²/p²)`` — the closed-form periodic heat kernel — to the
  discretization floor (the FV eigenvalue gap ``(kΔx)²/12`` + the CN time error); a bare Neumann
  eigenmode decays by exactly its eigenvalue exponential.
* **Conservation (tight).** No-flux ⇒ the bake conserves acid dose ⇒ the image **mean** — and with
  it the v1 Parseval power balance ``mean(image) = Σ|c_m|² = transmitted_power`` — survives the
  bake at **every** σ to machine precision: blur redistributes the latent image, it neither makes
  nor loses acid. (Corollary: the default mean-clip dose is blur-invariant.)
* **Benchmark (loose) + the PEB window.** Contrast/NILS/CD degrade monotonically with σ (the cited
  20/40/60 nm PEB simulation series, Mack); and the **trade-off that defines the bake**: smoothing
  **standing waves** (depth ripple of period ``λ/2n`` — :func:`standing_wave_period`, Mack's
  eq. (12), blurred by the *same* :func:`peb_blur` along ``z``) needs ``σ ≳ λ/4n`` (the cited
  half-period rule), while keeping the lateral image needs ``σ ≪ p`` — the **PEB window**, which
  closes at the pitch ``p_close = λ/(4nc)`` where that floor meets a keep-half-the-fundamental
  ceiling (~151 nm at 193 nm / n 1.7). ``p_close`` is **NA-independent** (resist index + keep floor
  only), while this system's partial-coherence optical cutoff ``λ/(NA(1+σ))`` slides with the lens;
  their ratio ``NA(1+σ)/(4nc)`` is therefore **λ-independent**, and at NA 0.85 / σ 0.5 it is ≈ 1.0006
  — closure and cutoff land on the *same* ~151 nm not by law but because two independent parameter
  groups (lens+source ``NA(1+σ)=1.275`` vs resist+floor ``4nc=1.274``) happen to match to 0.06%: a
  **λ-independent coincidence**, with an NA-mechanism. Push the lens to NA 0.93 and the cutoff slides
  to ~138 nm while ``p_close`` stays pinned at 151 — a band where the lens images but the bake cannot
  hold it (the lens out-resolves the bake; why the BARC). Scope edges, named: **linear exposure**
  (latent acid ∝ I — no Dill bleaching/saturation),
  **constant linear-blur D** (the **CAR reaction–diffusion** system — acid-catalyzed deprotection,
  first-order acid loss, free-volume ``D(m)`` — is **promoted in v1.9**, see §9 below), development
  still a constant threshold, and the lateral blur is 1-D in ``x`` while the standing-wave smoothing
  is 1-D in ``z`` (no coupled 2-D ``(x,z)`` resist volume — the engine's own last deferred regime).

v1.9 (§9) — CAR reaction–diffusion PEB: chemical amplification competes with diffusion + loss
----------------------------------------------------------------------------------------------
The §8-named "constant D (no CAR reaction–diffusion)" edge, promoted — and where v1.7 found the bake
*is* the engine's pure linear PDE, the **realistic** chemically-amplified bake is a coupled
**two-field reaction–diffusion** system that does **not** fit the single-field engine natively, so it
is built **consumer-side by operator splitting** with the engine carrying only the acid-diffusion
sub-step (the v1.2 moving-boundary move; no engine amendment). The cited model (Kirchauer §7.1.2,
the same thesis as §8 — ``[[peb-acid-diffusion-source]]``), on the blocked-site fraction ``m`` (1→0)
and the acid ``h``::

    ∂m/∂t = −k_amp · m · hⁿ                         (deprotection: acid catalyzes the cleavage)
    ∂h/∂t = −k_loss · h + ∂ₓ(D_h(m) ∂ₓh)            (acid: first-order loss + Fickian diffusion)

Two facts make the split clean. (1) **Acid is a pure catalyst** — the ``h`` equation has *no* ``h·m``
sink (deprotection consumes blocked sites, not acid), so ``∫h dx`` is conserved at ``k_loss = 0`` and
decays *exactly* ``e^{−k_loss·t}`` otherwise — the tight conservation anchor. (2) The **local reaction
flow integrates in closed form** (``h`` decays exactly; ``m = m·exp(−k_amp·hⁿ·Φ)``,
``Φ = (1−e^{−n·k_loss·dt})/(n·k_loss)``) and is a semigroup, so composing Strang sub-steps reproduces
the single flow to machine precision. :func:`car_peb` Strang-splits a bake (½-reaction · diffuse ·
½-reaction): the engine diffuses ``h`` (``Neumann(0)`` sealed faces, ``D_h(m)`` frozen per step from
the lagged deprotection — the array-``D`` path) and :func:`_car_react` applies the exact reaction.
The diffusion sub-step is **backward Euler, NOT v1.7's Crank–Nicolson**: ``hⁿ`` with non-integer ``n``
is a NaN trap on any negative ring, and BE's discrete maximum principle keeps ``h ≥ 0`` so the bake
both never NaNs *and* keeps the ``∫h`` conservation exact (a CN ring would force a mass-adding clamp).
Development clips the **deprotection profile** ``1−m`` (the chemically-faithful resist model —
:func:`expose_grating_car`), where v1.7 clipped the acid image. The mini-triad:

* **Analytic (tight).** (a) The degenerate seam — ``k_amp = k_loss = 0`` is the v1.7 linear blur
  **bit-for-bit** (``car_peb`` short-circuits to :func:`peb_blur`; ``m`` stays 1, deprotection 0).
  (b) A **spatially-flat** acid sees identity diffusion (``Neumann(0)``), so the split is the exact
  reaction flow — the deprotection matches the closed-form ODE to **machine precision** (both
  ``k_loss = 0`` and ``k_loss > 0``).
* **Conservation (tight).** Acid is a catalyst ⇒ ``∫h dx`` is conserved (``k_loss = 0``) or decays
  exactly ``e^{−k_loss·t}`` — on flat *and* structured images, to machine precision — and the
  deprotection ``1−m`` stays in ``[0, 1]`` and is monotone in bake time (``m`` only ever decreases).
* **Benchmark (loose).** **Chemical amplification sharpens** — in the amplification-dominated (small-
  ``D``) regime the superlinear ``hⁿ`` map makes the deprotection edge *steeper* than the acid's
  (``NILS`` up), the signature that makes CAR high-resolution; while **diffusion + loss degrade** the
  latent image (``contrast``/``NILS`` fall with ``D·t`` and over-bake) — the competition that sets the
  CAR resolution floor. A *regime* claim, not a monotone law (at large ``σ`` blur wins). Cited APEX-E
  @ 90 °C constants (``k_amp = 2.0/s``, ``k_loss = 0.0033/s``, ``n = 1.8``, ``D_h,0 = 0.0933 nm²/s``).
  Scope edges still named: **linear exposure** (no Dill), **constant-threshold development** (no Mack
  dissolution-rate kinetics), the free-volume ``D_h,1`` coefficient **uncalibrated** (illustrative;
  default constant ``D``), and the ``x``/``z`` blurs uncoupled (no 2-D resist volume).

v1.10 (§10) — Zernike aberrations: coma, astigmatism & spherical, a pupil phase (the promoted edge)
---------------------------------------------------------------------------------------------------
The §-named "aberration-free pupil apart from defocus" edge, promoted — and it lands on the **same
finding as v1.4**: a Zernike aberration is a pure **phase** on the pupil, so :func:`coherent_image`
already images through it with no new path. Each line/space order rides the pupil at the normalized
1-D slice coordinate ``u = f_total/f_cut`` (``f_total = f_m + f_s``, ``|u| ≤ 1`` for a collected
order), and :func:`zernike_phase` multiplies it by ``exp(i·2π·W(u))`` with the wavefront error the
sum of the standard **balanced-Zernike** radial polynomials on that θ = 0/π slice (in waves)::

    W(u) = coma·(3u³−2u)·cos φ_g  +  astigmatism·u²·cos 2φ_g  +  spherical·(6u⁴−6u²)

— coma the **odd** ``3u³−2u`` (with a built-in tilt balance), astigmatism/spherical **even** (the
spherical ``−6u²`` is the defocus balance). The coefficients are an :class:`Aberrations` frozen
dataclass (in waves), threaded through :func:`abbe_image`/:func:`expose_grating` as ``aberrations=None``;
the unaberrated default short-circuits to the float ``1.0`` so the image is v1 **bit-for-bit**. Kept
**separate from** ``defocus_nm`` (waves/paraxial-Zernike here vs v1.4's exact nm ``1 − cosθ``). The
mini-triad:

* **Analytic (tight).** (a) The degenerate seam — all-zero (or ``aberrations=None``) is the v1 image
  **bit-for-bit**. (b) **Parity.** An EVEN aberration (astigmatism, spherical) leaves a symmetric image
  symmetric — a symmetric two-beam pair carrying *equal* even phase has it factor out of ``|Σ|²`` → the
  image is unchanged to machine precision (astig at the pupil rim, spherical at an *interior* pair — the
  rim is *trivial* for spherical, whose balanced form is 0 at ``u = ±1``, so the interior pair is the
  real test). The ODD coma instead gives the two beams *opposite* phase → a **pure lateral fringe
  shift**, contrast preserved (the dipole the v1.4 *defocus* left invariant, coma *translates*). (c)
  **The coma↔defocus discriminator (the load-bearing anchor).** For the on-axis three-beam image both
  defocus and coma give the *same* fundamental magnitude ``4c₀c₁cos φ`` — the cos-only
  :func:`fundamental_amplitude` cannot tell them apart. The **complex** fundamental
  (:func:`fundamental_complex`) can: its phase is **exactly** the ±1 order's aberration phase — ``0`` for
  even defocus, the coma shift for odd coma — to machine precision.
* **Conservation (tight) — aberrations are unitary.** Phase-only ⇒ ``|amplitude|²`` is untouched ⇒ the
  power balance ``mean(image) = Σ|c_m|² =`` :func:`transmitted_power` holds at **every** aberration level
  to machine precision (``transmitted_power`` never sees the phase — a real check the build added *phase*,
  not amplitude). The v1.4 defocus conservation leg, extended for free.
* **Benchmark (loose) — the litho-native signatures (not a Strehl number).** Coma → **pattern placement
  error** (the fringe shift ∝ the coma coefficient) and an **asymmetric image** (which the v1.7/v1.9 PEB
  symmetry cell **refuses**, the same way it refuses the v1.4 off-axis-defocus fringe shift). Astigmatism
  → an **H↔V best-focus split** (``φ_g = 0`` vs 90° shift best focus in *opposite* directions; a plain
  defocus offset does not) — the signature that makes astig ≠ defocus in 1-D. Spherical → **pitch-
  dependent best focus** (the balanced ``−6u²`` makes the best-focus defocus offset depend on where the
  orders ride the pupil; pure-defocus best focus is pitch-independent at ``z = 0``). Scope edges, named:
  the **1-D pupil slice** of the 2-D Zernikes (the orders sample only the ``f_x`` axis), the coefficient
  on the *peak* (Seidel-balanced) polynomial in waves (not the Noll RMS-normalized 2-D coefficient),
  astig's degeneracy with a **paraxial** ``u²`` defocus (exact only as ``NA → 0``, since v1.4's defocus
  is the full ``1 − cosθ``), and a Strehl/Maréchal number left **un-asserted** (it needs the 2-D pupil-disk
  integral, not a handful of slice samples — the honest discrete-1-D caveat).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from engines.diffusion import Diffusion1D, Neumann, uniform_grid

# --------------------------------------------------------------------------- #
# Constants — unit conversion + the cited resolution / printability benchmarks
# --------------------------------------------------------------------------- #
UM_PER_NM = 1.0e-3        # 1 nm = 1e-3 µm — CD reported in both; µm is the cross-module length currency

# Rayleigh k₁ factors (half-pitch R = k₁·λ/NA), pinned to litho-aerial-image-source (Mack / lithoguru):
K1_COHERENT = 0.5        # conventional coherent (on-axis, three-beam ±1) half-pitch limit
K1_TWO_BEAM = 0.25       # two-beam (extreme off-axis / dipole) physical half-pitch floor ("lowest we can go")

# NILS printability rule of thumb (litho-aerial-image-source): ≥1 minimally resolved, ≳2 robust process.
NILS_PRINTABLE = 2.0

# Rayleigh second-equation depth-of-focus factor (DOF = k₂·λ/NA²), litho-aerial-image-source (Mack).
# 0.5 is **derived** here, not echoed: the on-axis three-beam image's fundamental nulls at defocus phase
# φ = π/2 (see §7), which at the resolution-limited pitch (the ±1 orders riding the pupil rim, sinθ→NA)
# lands at z = λ/(2·NA²) → k₂ = 0.5 — the same validated-as-a-consequence honest split as k₁.
K2_DOF = 0.5

# PEB diffusion-length teaching series (nm), pinned to peb-acid-diffusion-source (Mack, lithobasics):
# the profile-simulation series Mack uses to show PEB smoothing (20/40/60 nm) — the v1.7 demo's sweep
# scale and the loose "tens of nanometres" benchmark band. The smoothing *rule* is separate (cited,
# Mack's glossary): σ must exceed the standing-wave HALF period λ/4n to erase the ridges.
PEB_DIFFUSION_SERIES_NM = (20.0, 40.0, 60.0)

# Pupil-edge inclusion tolerance: an order landing *exactly* on the rim |f|=f_cut is physically
# collected, so include it despite floating-point round-off (load-bearing for the k₁ limit cases,
# where the two-beam orders sit exactly at ±f_cut).
_F_TOL = 1.0e-9


# --------------------------------------------------------------------------- #
# 1. The imaging system — wavelength, NA, partial coherence; the Rayleigh map
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Imaging:
    """A projection imaging system: exposure wavelength, lens NA, illumination partial coherence.

    ``wavelength_nm`` is λ (365 i-line, 248 KrF, 193 ArF); ``NA`` the projection-lens numerical
    aperture (the pupil cutoff ``f_cut = NA/λ``); ``sigma`` the partial-coherence factor
    ``σ = (illumination NA)/(projection NA)`` (0 = fully coherent on-axis; ~0.3–0.9 conventional;
    drives :func:`conventional_source`). Plain scalars — the recipe knobs.
    """

    wavelength_nm: float
    NA: float
    sigma: float = 0.5

    @property
    def f_cut(self) -> float:
        """Pupil cutoff spatial frequency ``NA/λ`` (1/nm) — the coherent diffraction-collection limit."""
        return self.NA / self.wavelength_nm

    def resolution(self, k1: float = K1_TWO_BEAM) -> float:
        """Rayleigh resolvable half-pitch ``R = k₁·λ/NA`` (nm). ``k1`` default 0.25 (the two-beam floor)."""
        return k1 * self.wavelength_nm / self.NA

    @property
    def pitch_min_coherent(self) -> float:
        """Smallest pitch resolved under on-axis coherent illumination, ``λ/NA`` (nm) → half-pitch ``k₁=0.5``."""
        return self.wavelength_nm / self.NA

    @property
    def pitch_min_two_beam(self) -> float:
        """Smallest pitch resolved with off-axis two-beam illumination, ``λ/(2·NA)`` (nm) → ``k₁=0.25``."""
        return self.wavelength_nm / (2.0 * self.NA)

    def depth_of_focus(self, k2: float = K2_DOF) -> float:
        """Rayleigh depth of focus ``DOF = k₂·λ/NA²`` (nm) — the focus latitude (companion to :meth:`resolution`).

        The second Rayleigh equation: as resolution scales like ``λ/NA``, the usable defocus scales like
        ``λ/NA²`` — so pushing NA for resolution costs DOF quadratically (the litho squeeze). ``k2`` default
        0.5 (:data:`K2_DOF`), the value the on-axis three-beam fundamental null derives (see :func:`defocus_phase`).
        """
        return k2 * self.wavelength_nm / (self.NA ** 2)


def rayleigh_resolution(wavelength_nm: float, NA: float, k1: float = K1_TWO_BEAM) -> float:
    """Rayleigh resolvable half-pitch ``R = k₁·λ/NA`` (nm) — the standalone form of :meth:`Imaging.resolution`.

    ``k1`` selects the regime: 0.5 conventional coherent, 0.25 the two-beam physical floor (the cited
    ``[[litho-aerial-image-source]]`` values). ``R`` is the half-pitch (= CD of a dense 1:1 line/space).
    """
    return k1 * wavelength_nm / NA


def rayleigh_depth_of_focus(wavelength_nm: float, NA: float, k2: float = K2_DOF) -> float:
    """Rayleigh depth of focus ``DOF = k₂·λ/NA²`` (nm) — the standalone form of :meth:`Imaging.depth_of_focus`.

    The focus-budget companion to :func:`rayleigh_resolution`: resolution scales ``λ/NA``, DOF scales
    ``λ/NA²``, so the two trade against NA. ``k2`` default 0.5 (:data:`K2_DOF`).
    """
    return k2 * wavelength_nm / (NA ** 2)


# --------------------------------------------------------------------------- #
# 2. The mask spectrum — diffraction orders of a binary line/space grating
# --------------------------------------------------------------------------- #
def grating_orders(pitch_nm: float, n_orders: int = 15, duty: float = 0.5):
    """Fourier orders of a binary line/space amplitude grating: list of ``(f_m, c_m)``.

    ``f_m = m/pitch`` is the spatial frequency (1/nm) of order ``m = −n_orders … +n_orders``; ``c_m`` the
    real Fourier amplitude of the transmission (1 in the clear openings, 0 in chrome). ``duty`` is the
    **clear fraction** (0.5 = equal lines and spaces). The classic square-wave spectrum::

        c₀ = duty,   c_m = sin(π·m·duty)/(π·m)   (m ≠ 0)

    — at 50% duty only the odd orders survive (``c₁ = 1/π``, ``c₂ = 0``, ``c₃ = −1/3π`` …). The
    coefficients are real and even, so the grating (and its aerial image) is **symmetric about x=0**, a
    clear-space centre. Note ``c₀ ≠ c₁`` for a real grating — the two-beam *idealization*
    (:func:`two_beam_image`) takes them equal; this realistic spectrum does not (visibility < 1).
    """
    if not 0.0 < duty < 1.0:
        raise ValueError(f"duty must be in (0, 1), got {duty}")
    orders = []
    for m in range(-n_orders, n_orders + 1):
        c = duty if m == 0 else math.sin(math.pi * m * duty) / (math.pi * m)
        orders.append((m / pitch_nm, c))
    return orders


# --------------------------------------------------------------------------- #
# 3. The core primitive + the exact two-beam anchor
# --------------------------------------------------------------------------- #
def coherent_image(x_nm, orders):
    """Coherent aerial image ``I(x) = |Σ_m a_m·exp(2πi·f_m·x)|²`` from collected ``(f_m, a_m)`` orders.

    The **core primitive** of the whole module: the orders the pupil collects interfere coherently, and
    the intensity is the squared modulus of their summed complex amplitude. Both the exact two-beam
    anchor (:func:`two_beam_image`, two equal orders) and the Abbe workhorse (:func:`abbe_image`, this
    summed over source points) are this one function. ``orders`` amplitudes may be complex; ``x_nm`` a
    scalar or NumPy array (nm).
    """
    x = np.asarray(x_nm, dtype=float)
    E = np.zeros(x.shape, dtype=complex)
    for f, a in orders:
        E += a * np.exp(2j * np.pi * f * x)
    intensity = np.abs(E) ** 2
    return float(intensity) if intensity.ndim == 0 else intensity


def two_beam_image(x_nm, pitch_nm: float):
    """The exact two-beam aerial image — two equal-amplitude orders (0th + 1st) → ``4·cos²(πx/p)``.

    The analytical anchor. Two beams of equal unit amplitude at ``f=0`` and ``f=1/p`` interfere to
    ``|1 + exp(2πi·x/p)|² = 2(1 + cos(2πx/p)) = 4·cos²(πx/p)`` — a pure cos² fringe of period ``p``,
    **full visibility** (``I_min = 0`` at ``x = p/2``, ``I_max = 4`` at ``x = 0``). This is
    :func:`coherent_image` with exactly two **equal** orders — the *idealization*, kept separate from a
    real grating's image (whose 0th and 1st orders are unequal — ``c₀=duty``, ``c₁≈1/π`` at 50% — so its
    visibility is < 1). The exact form is validated on its idealization; the realistic grating's job is
    contrast/CD (the Phase 1a exact-anchor-vs-realistic-demo discipline).
    """
    return coherent_image(x_nm, [(0.0, 1.0), (1.0 / pitch_nm, 1.0)])


# --------------------------------------------------------------------------- #
# 4. The Abbe sum-over-source workhorse + its source constructors
# --------------------------------------------------------------------------- #
def on_axis_source():
    """The single on-axis source point (σ = 0, fully coherent illumination): ``f_s = 0``."""
    return np.array([0.0])


def conventional_source(imaging: Imaging, n_source: int = 21):
    """A conventional (disk) illuminator: ``n_source`` points uniform on the line ``|f_s| ≤ σ·NA/λ`` (1/nm).

    The 1-D teaching model of a partially-coherent conventional source — a uniform *line* of source
    points of half-width ``σ·f_cut``. (Scope edge, named: a 1-D uniform line, **not** the chord-weighted
    projection of a real 2-D circular σ-disk.) ``σ = 0`` collapses to the on-axis point. Larger σ →
    broader source → smoother but lower-contrast image (more partial coherence).
    """
    s = imaging.sigma
    if s <= 0.0:
        return on_axis_source()
    return np.linspace(-s * imaging.f_cut, s * imaging.f_cut, n_source)


def offaxis_source(imaging: Imaging):
    """A single off-axis source point at the pupil edge ``f_s = −NA/λ`` — the two-beam (k₁ = 0.25) pole.

    The extreme-off-axis illumination that places the 0th order at one pupil rim and lets a 1st order as
    fine as ``f = 2·NA/λ`` reach the other rim — so a grating with pitch as small as ``λ/(2·NA)``
    (``k₁=0.25`` half-pitch) still passes **two beams** and images. One pole of a dipole; the constructor
    behind the ``k₁=0.25`` limit, and the source for which the two-beam cos² emerges from :func:`abbe_image`.
    """
    return np.array([-imaging.f_cut])


def defocus_phase(f_total, imaging: Imaging, defocus_nm: float):
    """Pupil **defocus phase** ``exp(i·(2π/λ)·z·(1 − cosθ))`` of an order at pupil frequency ``f_total`` (v1.4).

    Defocus is a pure *phase* aberration: an order leaving the pupil at angle θ (``sinθ = f_total·λ``, the
    **full** pupil coordinate ``f_m + f_s``) is delayed, relative to the on-axis ray, by the optical-path
    error ``z·(1 − cosθ)`` over a defocus ``z`` — a phase ``(2π/λ)·z·(1 − cosθ)``. (Referenced to the
    on-axis ray so ``f_total = 0`` carries no phase; the absolute reference is immaterial — a phase common
    to *all* orders factors out of ``|Σ|²``.) Because it is phase-only, ``|amplitude|²`` is unchanged, so
    defocus **conserves power** (the §-conservation leg) and is *unitary* — it redistributes the image, it
    does not dim it.

    Returns the literal float ``1.0`` when ``defocus_nm == 0`` so the in-focus path is **bit-for-bit** the
    v1 image (the degenerate seam). ``f_total`` may be a scalar or array (1/nm). Scope edge: ``cosθ`` uses
    the **full** ``√(1 − (f_total·λ)²)`` (not the paraxial ``1 − ½(f_total·λ)²``), exact for the scalar
    model; an evanescent order (``|f_total|·λ ≥ 1``, only reachable at immersion ``NA ≥ 1`` — the named
    vector scope edge) is outside v1, and a collected order under a dry ``NA < 1`` pupil never reaches it.
    """
    if defocus_nm == 0.0:
        return 1.0
    ft_lambda = np.asarray(f_total, dtype=float) * imaging.wavelength_nm
    cos_theta = np.sqrt(np.maximum(1.0 - ft_lambda ** 2, 0.0))
    phase = (2.0 * np.pi / imaging.wavelength_nm) * defocus_nm * (1.0 - cos_theta)
    return np.exp(1j * phase)


def abbe_image(x_nm, orders, imaging: Imaging, source_fs=None, n_source: int = 21,
               defocus_nm: float = 0.0, aberrations: "Aberrations | None" = None):
    """Partially-coherent aerial image by the **Abbe sum over source points** (not Hopkins TCC).

    For each source point ``f_s`` (an illumination direction), the mask spectrum shifts so order ``m``
    sits at ``f_m + f_s`` in the pupil; the pupil passes it iff ``|f_m + f_s| ≤ f_cut = NA/λ``. The
    survivors interfere into a coherent sub-image (:func:`coherent_image`) evaluated at the **object**
    frequencies ``f_m`` (the common illumination carrier ``exp(2πi·f_s·x)`` has unit modulus and drops
    out of the intensity). The partially-coherent image is the **incoherent average** over the source::

        I(x) = (1/N_s)·Σ_{f_s} | Σ_m c_m·P(f_m + f_s)·D·A·exp(2πi·f_m·x) |²

    where ``D`` is the :func:`defocus_phase` and ``A`` the :func:`zernike_phase` of each collected order,
    both keyed to the **full pupil coordinate** ``f_m + f_s`` (the order's true propagation angle / slice
    position). ``z = defocus_nm`` and ``aberrations`` (coma/astigmatism/spherical, v1.10) are both pure
    phase: ``D ≡ A ≡ 1`` and the image is **bit-for-bit** the unaberrated, in-focus one when ``z = 0`` and
    ``aberrations`` is ``None`` (the degenerate seam).

    ``source_fs`` is an explicit array of source spatial frequencies (build it with
    :func:`conventional_source`, :func:`on_axis_source`, or :func:`offaxis_source`); if omitted, a
    conventional disk of ``n_source`` points from ``imaging.sigma`` is used. The explicit-source design
    is deliberate: a uniform σ-disk cannot express extreme off-axis, so ``k₁=0.25`` needs the off-axis
    point handed in (a σ-disk conventional source tops out near ``k₁≈0.35–0.5``).
    """
    if source_fs is None:
        source_fs = conventional_source(imaging, n_source)
    source_fs = np.atleast_1d(np.asarray(source_fs, dtype=float))
    cutoff = imaging.f_cut * (1.0 + _F_TOL)
    x = np.asarray(x_nm, dtype=float)
    total = np.zeros(x.shape, dtype=float)
    for fs in source_fs:
        passed = [(f, c * defocus_phase(f + fs, imaging, defocus_nm)
                   * zernike_phase(f + fs, imaging, aberrations))
                  for (f, c) in orders if abs(f + fs) <= cutoff]
        total = total + coherent_image(x, passed)
    return total / len(source_fs)


def transmitted_power(orders, imaging: Imaging, source_fs=None, n_source: int = 21) -> float:
    """Total optical power passed by the pupil, ``Σ_m |c_m|²·P(f_m+f_s)`` averaged over the source.

    The **conservation quantity, computed independently of the image**: for each source point, sum the
    squared amplitudes of the orders the pupil collects, and average over the source. By Parseval this
    equals the **DC (zero-frequency) component of the aerial image** — its spatial mean — because the
    cross terms in ``|Σ a_m·exp(2πi f_m x)|²`` sit at nonzero difference frequencies and average to
    zero. The power-balance check: ``mean(``:func:`abbe_image```)`` must equal this to machine precision
    (two independent computations — a squared sum vs a sum of squares).
    """
    if source_fs is None:
        source_fs = conventional_source(imaging, n_source)
    source_fs = np.atleast_1d(np.asarray(source_fs, dtype=float))
    cutoff = imaging.f_cut * (1.0 + _F_TOL)
    total = 0.0
    for fs in source_fs:
        total += sum(abs(c) ** 2 for (f, c) in orders if abs(f + fs) <= cutoff)
    return total / len(source_fs)


# --------------------------------------------------------------------------- #
# 5. Image-quality metrics — contrast and NILS (the benchmark legs)
# --------------------------------------------------------------------------- #
def image_contrast(intensity) -> float:
    """Aerial-image contrast (modulation) ``C = (I_max − I_min)/(I_max + I_min)`` ∈ [0, 1].

    The fringe visibility of the image: 1 for a fully-modulated two-beam ``cos²`` (``I_min = 0``),
    falling to 0 as the pattern stops resolving (only the DC order passes → a flat image). The y-axis of
    the contrast-vs-pitch benchmark curve (where it crosses ~0 marks the resolution limit).
    """
    intensity = np.asarray(intensity, dtype=float)
    i_max, i_min = float(intensity.max()), float(intensity.min())
    denom = i_max + i_min
    return 0.0 if denom == 0.0 else (i_max - i_min) / denom


def nils(x_nm, intensity, edge_nm: float, linewidth_nm: float) -> float:
    """Normalized image log-slope ``NILS = w · |d(ln I)/dx|`` at the feature edge (Mack).

    The printability metric: the normalized steepness of the bright→dark transition at the **geometric
    design edge** ``edge_nm`` (e.g. ``x = p/4`` for a 50%-duty grating — *not* a threshold crossing, so
    it is exposure-/threshold-free), scaled by the nominal feature width ``w = linewidth_nm`` to be
    dimensionless. Rule of thumb (``[[litho-aerial-image-source]]``): ``NILS ≥ 1`` minimally resolved,
    ``NILS ≳ 2`` for a robust process (~20% exposure latitude). Higher NILS = steeper edge = better CD control.
    """
    x = np.asarray(x_nm, dtype=float)
    intensity = np.asarray(intensity, dtype=float)
    log_i = np.log(np.maximum(intensity, 1e-300))
    slope = np.gradient(log_i, x)
    slope_at_edge = float(np.interp(edge_nm, x, slope))
    return linewidth_nm * abs(slope_at_edge)


def fundamental_amplitude(x_nm, intensity, pitch_nm: float) -> float:
    """The image's **fundamental** Fourier coefficient at ``1/pitch`` — the projection ``⟨I, cos(2πx/p)⟩`` (v1.4).

    The signed amplitude of the ``cos(2πx/p)`` component of the aerial image, by the quadrature projection
    ``(2/L)·∫₀ᴸ I(x)·cos(2πx/p) dx`` over one period ``L = pitch`` (a uniform grid sampling one full period,
    ``endpoint=False``, makes the discrete sum exact for the band-limited image). This is the **defocus-clean
    observable**: for the on-axis three-beam image ``I = c₀² + 4c₁²cos²ψ + 4c₀c₁cosφ·cosψ`` the higher term
    ``4c₁²cos²ψ`` is a *defocus-independent* second harmonic (at ``2/p``) that is orthogonal to ``cos(2πx/p)``
    — so this projection returns exactly ``4·c₀·c₁·cos φ`` and **nulls at the defocus phase φ = π/2**. The
    plain :func:`image_contrast` does *not* (it sees the surviving second harmonic — defocus-induced frequency
    doubling), which is why the tight defocus anchor asserts on *this*, not on contrast.
    """
    x = np.asarray(x_nm, dtype=float)
    intensity = np.asarray(intensity, dtype=float)
    return float(2.0 * np.mean(intensity * np.cos(2.0 * np.pi * x / pitch_nm)))


# --------------------------------------------------------------------------- #
# 6. Constant-threshold resist → printed CD, and the bundled exposure result
# --------------------------------------------------------------------------- #
def _threshold_crossings(x: np.ndarray, y: np.ndarray, level: float) -> np.ndarray:
    """x-positions where ``y`` crosses ``level``, by linear interpolation between samples."""
    d = y - level
    sign_change = np.where(np.diff(np.signbit(d)))[0]
    crossings = []
    for i in sign_change:
        d0, d1 = d[i], d[i + 1]
        if d1 == d0:
            crossings.append(x[i])
        else:
            crossings.append(x[i] - d0 * (x[i + 1] - x[i]) / (d1 - d0))
    return np.asarray(crossings)


def print_cd(x_nm, intensity, threshold: float, polarity: str = "dark") -> float:
    """Constant-threshold resist: the printed critical dimension (CD, nm) from where ``I`` crosses ``threshold``.

    The simplest resist model — the printed feature edge is where the aerial intensity equals the fixed
    ``threshold`` (a fixed exposure dose). ``polarity`` selects which part prints as the line:
    ``"dark"`` (the line is where ``I < threshold`` — a clear-field mask / positive resist printing the
    dark fringe as a resist line) or ``"bright"`` (``I > threshold``). Returns the line width of the
    feature **centred in the supplied x-range** (so pass at least one period with the feature interior,
    not wrapping the array ends). Returns 0.0 if the image never crosses the threshold (unresolved /
    fully above or below). Hold ``threshold`` *fixed* across a pitch sweep (the point is fixed dose,
    varying pitch → watch CD collapse).
    """
    x = np.asarray(x_nm, dtype=float)
    intensity = np.asarray(intensity, dtype=float)
    crossings = _threshold_crossings(x, intensity, threshold)
    if crossings.size < 2:
        return 0.0
    centre = x[np.argmin(intensity)] if polarity == "dark" else x[np.argmax(intensity)]
    left = crossings[crossings <= centre]
    right = crossings[crossings >= centre]
    if left.size == 0 or right.size == 0:
        return 0.0
    return float(right.min() - left.max())


@dataclass(frozen=True)
class PrintedFeature:
    """The line/space readout from one aerial image at a constant resist threshold — *recipe → feature*.

    ``cd_nm`` is the printed critical dimension (line width, nm); ``cd_um`` the same in **µm** (the
    cross-module length currency → the Phase-4 MOS channel geometry). ``contrast`` and ``nils`` are the
    image-quality metrics; ``threshold`` the resist clip level; ``pitch_nm`` the grating pitch; ``resolved``
    whether the image modulates at all (contrast above a small floor). ``peb_diffusion_length_nm`` (v1.7)
    is the bake's acid diffusion length σ — when nonzero, every metric above reads the **post-bake
    latent** image, not the aerial image (0.0 = the v1 aerial-image readout). Plain scalars — the
    loose-coupling currency Phase 4 consumes.
    """

    pitch_nm: float
    cd_nm: float
    contrast: float
    nils: float
    threshold: float
    peb_diffusion_length_nm: float = 0.0

    @property
    def cd_um(self) -> float:
        """Printed CD in micrometres (``cd_nm·1e-3``) — the cross-module length currency."""
        return self.cd_nm * UM_PER_NM

    @property
    def resolved(self) -> bool:
        """Whether the pattern resolves at all (contrast above a small floor — else a flat image)."""
        return self.contrast > 1.0e-3


def expose_grating(
    imaging: Imaging,
    pitch_nm: float,
    source_fs=None,
    n_source: int = 21,
    n_orders: int = 15,
    duty: float = 0.5,
    threshold: float | None = None,
    n_x: int = 512,
    defocus_nm: float = 0.0,
    aberrations: "Aberrations | None" = None,
    peb_diffusion_length_nm: float = 0.0,
    peb_n_steps: int = 200,
) -> PrintedFeature:
    """Image a line/space grating and read the printed feature — the Phase-3 'recipe in, CD out' entry.

    Builds the grating spectrum (:func:`grating_orders`), forms the partially-coherent Abbe image over
    **one period** (``n_x`` points, ``endpoint=False`` — so the spatial mean is exact), and reads the
    contrast, NILS (at the nominal edge ``x = duty·p/2``, with ``w = (1−duty)·p`` the line width), and
    the constant-threshold CD of the dark line. ``threshold`` defaults to the **image mean** (a balanced
    clip → nominal duty on a well-resolved image); pass a fixed value to sweep pitch at constant dose.
    ``defocus_nm`` (v1.4) images out of focus (``z = 0`` is the in-focus default, bit-for-bit v1) — sweep
    it at a fixed ``threshold`` to trace a **Bossung** CD-vs-defocus curve. ``aberrations`` (v1.10) adds a
    Zernike pupil phase (coma/astigmatism/spherical — :class:`Aberrations`, ``None`` = unaberrated,
    bit-for-bit v1); coma's asymmetric image is **refused** by the PEB path below (no mirror plane). The
    high-level entry mirroring :func:`oxidation.grow_oxide`. Returns a :class:`PrintedFeature`.

    ``peb_diffusion_length_nm`` (v1.7) bakes the resist before development: the latent acid image
    (∝ the aerial image — the linear-exposure scope edge) is diffused by :func:`peb_blur` on the
    half-period symmetry cell ``[0, p/2]``, and **every metric then reads the post-bake latent
    image** (the diffused-image resist model). Because the blur's no-flux faces must be cell *faces*,
    this path samples the period at the half-offset cell centers ``x = (j+½)·p/n_x`` — still a
    uniform full-period sampling, so the mean/projections stay exact; the ``σ → 0`` limit approaches
    the v1 metrics within sampling resolution, while the ``σ = 0`` default IS the v1 path bit-for-bit
    (the degenerate seam). Requires an even ``n_x`` and an **even (symmetric) image** — a symmetric
    grating under a symmetric source; an off-axis pole under defocus shifts the fringe (v1.4) off the
    mirror planes and is refused. Conservation makes the default mean-clip dose blur-invariant.
    """
    orders = grating_orders(pitch_nm, n_orders=n_orders, duty=duty)
    if peb_diffusion_length_nm != 0.0:
        if n_x % 2:
            raise ValueError(f"PEB blur needs an even n_x (half-period symmetry cells), got {n_x}")
        x = (np.arange(n_x) + 0.5) * (pitch_nm / n_x)
        aerial = abbe_image(x, orders, imaging, source_fs=source_fs, n_source=n_source,
                            defocus_nm=defocus_nm, aberrations=aberrations)
        if not np.allclose(aerial, aerial[::-1], rtol=1e-8, atol=1e-9 * float(aerial.max())):
            raise ValueError(
                "PEB blur requires an even (symmetric) aerial image — a symmetric grating under a "
                "symmetric source. An asymmetric image (e.g. an off-axis pole under defocus — the "
                "v1.4 fringe shift) has no mirror plane at x=0/p/2, so the half-period no-flux "
                "domain does not represent its periodic blur."
            )
        half = n_x // 2
        blurred = peb_blur(aerial[:half], pitch_nm / 2.0, peb_diffusion_length_nm,
                           n_steps=peb_n_steps)
        intensity = np.concatenate([blurred, blurred[::-1]])   # mirror back: even about p/2
    else:
        x = np.linspace(0.0, pitch_nm, n_x, endpoint=False)
        intensity = abbe_image(x, orders, imaging, source_fs=source_fs, n_source=n_source,
                               defocus_nm=defocus_nm, aberrations=aberrations)
    contrast = image_contrast(intensity)
    edge_nm = duty * pitch_nm / 2.0
    linewidth_nm = (1.0 - duty) * pitch_nm
    image_nils = nils(x, intensity, edge_nm, linewidth_nm)
    clip = float(intensity.mean()) if threshold is None else threshold
    cd = print_cd(x, intensity, clip, polarity="dark")
    return PrintedFeature(
        pitch_nm=pitch_nm, cd_nm=cd, contrast=contrast, nils=image_nils, threshold=clip,
        peb_diffusion_length_nm=peb_diffusion_length_nm,
    )


# --------------------------------------------------------------------------- #
# 8. v1.7 — PEB acid-diffusion blur: the resist back-end rides the engine
# --------------------------------------------------------------------------- #
def standing_wave_period(wavelength_nm: float, n_resist: float) -> float:
    """Standing-wave intensity period in the resist, ``λ/(2·n_resist)`` (nm) — Mack's eq. (12).

    Interference between the wave travelling down through the resist and its substrate reflection
    makes the exposure intensity oscillate with **depth** as ``cos(4π·n·z/λ)`` — period ``λ/2n``
    (Mack, *Lithography Tutor* Spring 1994, eqs. (11)–(12) / *Applied Optics* 25:1958 1986; the
    cited ``[[peb-acid-diffusion-source]]``). The classic PEB job is to smooth these ridges; the
    cited rule of thumb (Mack's glossary) is a diffusion length of at least the standing-wave
    **half period** ``λ/4n`` — the lower edge of the v1.7 PEB window. (The cited mitigation list —
    ARC / dyed resist / PEB — is why modern stacks lean on a BARC where the window closes.)
    """
    return wavelength_nm / (2.0 * n_resist)


def peb_diffusion_length(diffusivity_nm2_s: float, t_seconds: float) -> float:
    """PEB diffusion length ``σ = √(2·D·t)`` (nm) — the one knob the whole bake recipe reduces to.

    The 1-D diffusion length of the acid (chemically amplified resist) or photoactive compound
    (conventional resist) over a bake of ``t_seconds`` at diffusivity ``D`` (nm²/s) — the cited
    ``σ_PEB = √(2·D_PEB·t_PEB)`` (Kirchauer §7.1.2 / Mack 1995). Only the *product* ``D·t`` enters
    a constant-D blur, so :func:`peb_blur` takes σ directly; this is the recipe-facing map onto it
    (bake hotter or longer → larger σ — same blur).
    """
    if diffusivity_nm2_s < 0.0 or t_seconds < 0.0:
        raise ValueError(f"need D ≥ 0 and t ≥ 0, got D={diffusivity_nm2_s}, t={t_seconds}")
    return math.sqrt(2.0 * diffusivity_nm2_s * t_seconds)


def peb_blur(latent, length_nm: float, diffusion_length_nm: float,
             n_steps: int = 200, method: str = "crank_nicolson") -> np.ndarray:
    """Diffuse a latent resist profile through one bake — ``engines.diffusion`` in **acid mode** (v1.7).

    ``latent`` samples a 1-D latent image (acid / PAC concentration, arbitrary units) at the **cell
    centers** of a sealed film domain ``[0, length_nm]`` (cell ``i`` at ``(i+½)·Δx``): the engine
    solves Fick's law ``∂a/∂t = D·∂²a/∂x²`` with ``Neumann(0)`` at both faces — the cited
    homogeneous-Neumann "no out-diffusion through the resist surface" BC (Kirchauer §7.1.2). For the
    lateral image that sealed domain is the **half-period symmetry cell**: the faces at ``x = 0`` and
    ``x = p/2`` are an even periodic image's mirror planes, and its cosine harmonics ``cos(2πjx/p)``
    are exactly the domain's Neumann eigenmodes — so the bounded solve IS the infinite periodic blur
    (each harmonic decays by the periodic heat kernel ``exp(−2π²j²σ²/p²)``), not an approximation of
    it. The same primitive smooths the **standing-wave depth ripple** (a film-thickness domain along
    ``z`` — the acid physically *cannot* leave the film, so there no-flux is the literal BC, not a
    symmetry trick).

    Physically only ``D·t`` enters (``σ² = 2·D·t``), so the blur takes the **diffusion length** σ
    directly and marches a unit bake at ``D = σ²/2``. ``diffusion_length_nm = 0`` returns the input
    **unchanged** (bit-for-bit, never touching the engine — the degenerate seam).
    ``method="crank_nicolson"`` by default. CN has **no** unconditional discrete max-principle, so on
    a sharp input it could ring — and acid must stay ≥ 0; what makes it safe here is **band-limiting
    by the optics**: the latent image carries only a handful of harmonics, all far below CN's
    oscillation scale, so there is no high-frequency content for CN to overshoot on (the bounds test
    confirms no ringing). With negativity ruled out by the band limit, the only thing left to choose
    on is fidelity to the calibrated ``σ = √(2·D·t)`` blur — and CN, 2nd-order in time, matches the
    exact per-harmonic heat kernel to the discretization floor (the FV eigenvalue gap ``(kΔx)²/12``),
    which is what makes the analytic anchor tight. ``method="backward_euler"`` is available for a
    guaranteed max-principle on a non-band-limited input, at a **less accurate** match to the kernel
    (~6× the CN error at equal ``n_steps``). Conservation is structural (telescoping fluxes) under
    either method.
    """
    a = np.asarray(latent, dtype=float)
    if diffusion_length_nm < 0.0:
        raise ValueError(f"diffusion_length_nm must be ≥ 0, got {diffusion_length_nm}")
    if diffusion_length_nm == 0.0:
        return a.copy()
    grid = uniform_grid(length_nm, a.size)
    solver = Diffusion1D(grid, 0.5 * diffusion_length_nm ** 2,
                         Neumann(0.0), Neumann(0.0), method=method)
    return solver.solve(a, 1.0, 1.0 / n_steps)


# --------------------------------------------------------------------------- #
# 9. v1.9 — CAR reaction–diffusion PEB: amplification competes with diffusion + loss
# --------------------------------------------------------------------------- #
# Cited APEX-E (IBM) @ 90 °C constants for the two-field CAR PEB model (peb-acid-diffusion-source,
# Kirchauer §7.1.2 — the same thesis as the v1.7 linear blur). k_peb,1 = the deprotection
# (amplification) rate constant, k_peb,2 = the first-order acid-loss rate constant, n = the acid
# reaction order in the deprotection rate, D_h,0 = the base acid diffusivity.
CAR_K_AMP_APEX_E = 2.0          # 1/s   — k_peb,1, the acid-catalyzed deprotection rate constant
CAR_K_LOSS_APEX_E = 0.0033      # 1/s   — k_peb,2, the first-order acid-loss rate constant
CAR_REACTION_ORDER_APEX_E = 1.8  # —     — n, the acid order in the deprotection rate ∝ hⁿ·m
CAR_D_H0_APEX_E = 0.0933        # nm²/s — D_h,0, the base acid diffusivity at 90 °C


@dataclass(frozen=True)
class CARBake:
    """A chemically-amplified-resist post-exposure-bake recipe — the cited two-field model (v1.9).

    The Kirchauer §7.1.2 reaction–diffusion system (``[[peb-acid-diffusion-source]]``) on the
    blocked-site fraction ``m`` (1 → 0 as the resist deprotects) and the acid concentration ``h``::

        ∂m/∂t = −k_amp · m · hⁿ                       (deprotection: acid catalyzes the cleavage)
        ∂h/∂t = −k_loss · h + ∂ₓ(D_h(m) ∂ₓh)          (acid: first-order loss + Fickian diffusion)

    Acid is a **pure catalyst** (no ``h·m`` sink on the ``h`` equation — deprotection consumes blocked
    sites, not acid), which is what makes ``∫h dx`` conserved at ``k_loss = 0`` (the tight conservation
    leg). The diffusivity is the cited **linear free-volume** model ``D_h = D_h0 + D_h1·(1−m)`` — only
    ``D_h0`` is a cited value, so ``D_h1`` defaults to 0 (constant ``D``); ``D_h1 > 0`` (the polymer
    diffuses acid faster as it deprotects) is **illustrative, not calibrated**. Defaults are the cited
    APEX-E @ 90 °C constants. ``t_bake_s`` is the bake duration (seconds) — unlike the v1.7 blur, where
    only the product ``D·t`` mattered, here the bake time independently sets the deprotection and the
    acid loss, so it is a separate knob.
    """

    t_bake_s: float
    k_amp: float = CAR_K_AMP_APEX_E
    k_loss: float = CAR_K_LOSS_APEX_E
    reaction_order: float = CAR_REACTION_ORDER_APEX_E
    D_h0_nm2_s: float = CAR_D_H0_APEX_E
    D_h1_nm2_s: float = 0.0


@dataclass(frozen=True)
class CARFeature:
    """The line/space readout from a CAR-baked, developed grating — the v1.9 chemically-faithful resist.

    Where :class:`PrintedFeature` reads the aerial (or v1.7 post-bake latent acid) image, this reads
    the **deprotection profile** ``1−m`` that survives the reaction–diffusion bake: ``cd_nm`` is the
    printed critical dimension (the line — the *low*-deprotection / still-protected region —
    developed at ``develop_threshold`` on ``1−m``), ``contrast`` / ``nils`` the deprotection-image
    quality, ``peak_deprotection`` the brightest-point conversion (a check the bake is in the partial,
    not fully-saturated, regime). Plain scalars — the Phase-4 loose-coupling currency.
    """

    pitch_nm: float
    cd_nm: float
    contrast: float
    nils: float
    develop_threshold: float
    peak_deprotection: float

    @property
    def cd_um(self) -> float:
        """Printed CD in micrometres (``cd_nm·1e-3``) — the cross-module length currency."""
        return self.cd_nm * UM_PER_NM

    @property
    def resolved(self) -> bool:
        """Whether the deprotection image modulates at all (contrast above a small floor)."""
        return self.contrast > 1.0e-3


def _car_react(m: np.ndarray, h: np.ndarray, dt: float, bake: CARBake):
    """The exact local reaction flow over ``dt`` — acid first-order loss + acid-catalyzed deprotection.

    The reaction operator (the Strang split's non-diffusive half) integrates in **closed form**: the
    acid decays ``h(τ) = h·e^{−k_loss·τ}``, and the deprotection, driven by that decaying acid, is
    ``m(dt) = m·exp(−k_amp·hⁿ·Φ)`` with ``Φ = ∫₀^{dt} e^{−n·k_loss·τ} dτ = (1−e^{−n·k_loss·dt})/(n·k_loss)``
    (``→ dt`` as ``k_loss → 0``). This is the exact flow of a semigroup, so composing sub-steps
    reproduces the single-shot flow to machine precision — which is why the spatially-flat anchor
    (where diffusion is identity) lands on the analytic ODE exactly. ``h`` is clamped ``≥ 0`` before
    the ``hⁿ`` (defensive; the backward-Euler diffusion sub-step already guarantees it).
    """
    n = bake.reaction_order
    h_pos = np.maximum(np.asarray(h, dtype=float), 0.0)
    phi = ((1.0 - math.exp(-n * bake.k_loss * dt)) / (n * bake.k_loss)
           if bake.k_loss > 0.0 else dt)
    m_new = m * np.exp(-bake.k_amp * h_pos ** n * phi)
    h_new = h_pos * math.exp(-bake.k_loss * dt)
    return m_new, h_new


def car_peb(acid, length_nm: float, bake: CARBake, n_steps: int = 200):
    """Reaction–diffusion PEB bake on a sealed film ``[0, length_nm]`` — Strang operator splitting (v1.9).

    The realistic chemically-amplified bake is a coupled two-field system (acid ``h`` + blocked-site
    fraction ``m``) that does not fit the single-field engine natively (the ``−k_loss·h`` loss is
    proportional to ``u``; ``m`` is a second field; ``D_h`` depends on ``m`` not ``h``), so it is built
    **consumer-side by operator splitting** — the engine carries only the acid-**diffusion** sub-step
    (``engines.diffusion``, ``Neumann(0)`` sealed faces, ``D_h(m) = D_h0 + D_h1·(1−m)`` frozen per step
    from the lagged deprotection — the array-``D`` path), while :func:`_car_react` applies the **exact**
    local reaction. Each Strang step is ½-reaction · diffuse · ½-reaction.

    The diffusion sub-step is **backward Euler — not v1.7's Crank–Nicolson**: ``hⁿ`` with non-integer
    ``n`` NaNs on any negative ring, and BE's discrete maximum principle keeps ``h ≥ 0`` so the bake
    never NaNs *and* keeps ``∫h`` conservation exact (a CN ring would need a mass-adding clamp). That
    caps the time accuracy at first order (BE-limited), not the Strang split's formal second — honest,
    and the tight anchors do not depend on it. The **no-reaction limit** (``k_amp = k_loss = 0``)
    short-circuits to :func:`peb_blur` (the v1.7 linear blur, ``σ = √(2·D_h0·t)``) **bit-for-bit** —
    CAR reduces to the linear acid-diffusion blur there (``m`` stays 1, deprotection 0).

    Returns ``(deprotection, acid)`` — ``deprotection = 1 − m`` (the developable latent image) and the
    final acid field, both cell-centered arrays the size of ``acid``.
    """
    a = np.asarray(acid, dtype=float)
    if bake.t_bake_s < 0.0:
        raise ValueError(f"t_bake_s must be ≥ 0, got {bake.t_bake_s}")
    if n_steps < 1:
        raise ValueError(f"n_steps must be ≥ 1, got {n_steps}")
    if bake.k_amp == 0.0 and bake.k_loss == 0.0:
        # No reaction: m stays 1 (deprotection 0), and the acid is a pure linear blur with constant
        # D_h0 (m≡1 ⇒ the D_h1 term vanishes) — the v1.7 path, reproduced bit-for-bit.
        sigma = math.sqrt(2.0 * bake.D_h0_nm2_s * bake.t_bake_s)
        return np.zeros_like(a), peb_blur(a, length_nm, sigma, n_steps=n_steps)
    if bake.t_bake_s == 0.0:
        return np.zeros_like(a), a.copy()
    if bake.D_h0_nm2_s <= 0.0:
        raise ValueError(
            f"D_h0_nm2_s must be > 0 for the active-reaction diffusion sub-step "
            f"(the harmonic-mean face diffusivity is undefined at D=0), got {bake.D_h0_nm2_s}"
        )

    grid = uniform_grid(length_nm, a.size)
    h = a.copy()
    m = np.ones_like(a)
    dt = bake.t_bake_s / n_steps
    constant_D = bake.D_h1_nm2_s == 0.0
    solver = (Diffusion1D(grid, bake.D_h0_nm2_s, Neumann(0.0), Neumann(0.0),
                          method="backward_euler") if constant_D else None)
    for _ in range(n_steps):
        m, h = _car_react(m, h, 0.5 * dt, bake)
        if not constant_D:                       # D_h(m) frozen at the current deprotection (array-D)
            Dc = bake.D_h0_nm2_s + bake.D_h1_nm2_s * (1.0 - m)
            solver = Diffusion1D(grid, Dc, Neumann(0.0), Neumann(0.0), method="backward_euler")
        h = solver.step(h, dt)
        m, h = _car_react(m, h, 0.5 * dt, bake)
    return 1.0 - m, h


def expose_grating_car(
    imaging: Imaging,
    pitch_nm: float,
    bake: CARBake,
    source_fs=None,
    n_source: int = 21,
    n_orders: int = 15,
    duty: float = 0.5,
    acid_dose: float = 1.0,
    develop_threshold: float = 0.5,
    n_x: int = 512,
    defocus_nm: float = 0.0,
    n_steps: int = 200,
) -> CARFeature:
    """Image a grating, bake it through the CAR reaction–diffusion PEB, and develop on the deprotection.

    The v1.9 chemically-faithful resist back-end (the §9 counterpart of :func:`expose_grating`): the
    Abbe aerial image writes a **latent acid** image (``∝`` the image — the linear-exposure scope edge —
    normalized so its peak is ``acid_dose``, the exposure knob), :func:`car_peb` runs the reaction–
    diffusion bake on the **half-period symmetry cell** ``[0, p/2]`` (the same v1.7 construction — the
    reaction is pointwise so an even acid stays even: even ``h`` → even ``m`` → even ``D_h``), and
    development clips the **deprotection profile** ``1−m`` at ``develop_threshold`` (the still-protected,
    low-deprotection region prints as the resist line — the ``"dark"`` polarity). Returns a
    :class:`CARFeature` whose ``contrast``/``nils``/``cd_nm`` read that developed deprotection image.

    Requires an even ``n_x`` and an **even (symmetric) aerial image** — an off-axis pole under defocus
    shifts the fringe (v1.4) off the mirror planes and is **refused**, not silently mis-baked (the same
    Massoud refuse-outside-the-fit discipline as the v1.7 PEB path).

    **Dose × bake-time must be co-tuned** (the recipe footgun): ``acid_dose`` and the ``bake.t_bake_s``
    are coupled through the cited amplification ``k_amp·hⁿ·t``. The default ``acid_dose = 1.0`` (peak
    latent acid = the full blocked-site density) is the *over-exposed extreme* — paired with a
    realistic ~60 s bake at the cited ``k_amp = 2.0/s`` it saturates **every** pixel (``1−m → 1``
    everywhere → a flat, contrast-0 deprotection → ``cd = 0``). Use a small dose for a long bake (the
    demo uses ``acid_dose ≈ 0.13`` at ~60 s — photoacid is a small fraction of the blocked-site
    density), or a short bake at dose 1.0; ``peak_deprotection`` on the returned :class:`CARFeature`
    flags the regime (well below 1.0 ⇒ partial / well-formed; pinned at 1.0 ⇒ saturated).
    """
    if n_x % 2:
        raise ValueError(f"CAR PEB needs an even n_x (half-period symmetry cells), got {n_x}")
    orders = grating_orders(pitch_nm, n_orders=n_orders, duty=duty)
    x = (np.arange(n_x) + 0.5) * (pitch_nm / n_x)
    aerial = abbe_image(x, orders, imaging, source_fs=source_fs, n_source=n_source,
                        defocus_nm=defocus_nm)
    if not np.allclose(aerial, aerial[::-1], rtol=1e-8, atol=1e-9 * float(aerial.max())):
        raise ValueError(
            "CAR PEB requires an even (symmetric) aerial image — a symmetric grating under a "
            "symmetric source. An asymmetric image (e.g. an off-axis pole under defocus — the v1.4 "
            "fringe shift) has no mirror plane at x=0/p/2, so the half-period sealed-cell bake does "
            "not represent its periodic reaction–diffusion."
        )
    h0 = acid_dose * aerial / float(aerial.max())    # latent acid ∝ image, peak = the exposure dose
    half = n_x // 2
    depro_half, _ = car_peb(h0[:half], pitch_nm / 2.0, bake, n_steps=n_steps)
    deprotection = np.concatenate([depro_half, depro_half[::-1]])   # mirror back: even about p/2
    contrast = image_contrast(deprotection)
    edge_nm = duty * pitch_nm / 2.0
    linewidth_nm = (1.0 - duty) * pitch_nm
    image_nils = nils(x, deprotection, edge_nm, linewidth_nm)
    cd = print_cd(x, deprotection, develop_threshold, polarity="dark")
    return CARFeature(
        pitch_nm=pitch_nm, cd_nm=cd, contrast=contrast, nils=image_nils,
        develop_threshold=develop_threshold, peak_deprotection=float(deprotection.max()),
    )


# --------------------------------------------------------------------------- #
# 10. v1.10 — Zernike aberrations: coma, astigmatism & spherical (a pupil phase)
# --------------------------------------------------------------------------- #
# Cited Zernike convention (litho-aerial-image-source — Mack, *Optical Lithography Modeling*; Born &
# Wolf §9.2 / Noll 1976 for the polynomials). The low-order aberrations as the standard piston-/tilt-
# balanced Zernike radial polynomials, evaluated on the 1-D pupil slice the line/space orders ride
# (θ = 0/π, the f_x axis), in the normalized coordinate u = f_total/f_cut:
#
#   defocus      Z4   2ρ²−1        → (modelled exactly already, as defocus_phase's 1−cosθ form)
#   astigmatism  Z5   ρ²cos2θ      → u²·cos(2φ_g)         (EVEN; ≡ a paraxial-defocus curvature along x)
#   coma         Z7   (3ρ³−2ρ)cosθ → (3u³−2u)·cos(φ_g)    (ODD; shifts the fringe → placement error)
#   spherical    Z9   6ρ⁴−6ρ²+1    → 6u⁴−6u²              (EVEN; the −6u² balance → pitch-dependent focus)
#
# Coefficients are in WAVES (wavefront error / λ); the pupil phase is exp(i·2π·W(u)). Piston drops (a
# phase common to all orders factors out of |Σ|²). Like defocus this is pure PHASE → fits coherent_image
# with no new path, conserves power (unitary), and no-aberration is the v1 image bit-for-bit.
@dataclass(frozen=True)
class Aberrations:
    """Low-order Zernike wavefront aberrations on the pupil — coma, astigmatism, spherical (v1.10).

    Coefficients in **waves** (wavefront error in units of λ): ``coma`` (Z7 x-coma, the ODD ``3u³−2u``
    term — a fringe shift / pattern-placement error), ``astigmatism`` (Z5 0°/90°, the EVEN ``u²·cos2φ_g``
    term — orientation-dependent best focus), ``spherical`` (Z9 primary, the EVEN ``6u⁴−6u²`` term —
    pitch-dependent best focus). ``grating_azimuth_deg`` (``φ_g``) is the line/space orientation relative
    to the aberration axis: it projects coma by ``cos φ_g`` and astigmatism by ``cos 2φ_g`` (``φ_g = 0`` =
    horizontal lines, 90° = vertical — astigmatism **flips sign** between them, which is exactly what
    distinguishes it from a plain defocus offset), and leaves the rotationally-symmetric spherical term
    unchanged. All-zero (the default) is the unaberrated pupil: :func:`zernike_phase` returns the literal
    ``1.0`` and the image is v1 bit-for-bit. Plain scalars — recipe knobs, like :class:`Imaging`. Kept
    **separate from** ``defocus_nm`` (a different convention: waves/paraxial-Zernike here vs the exact nm
    ``1 − cosθ`` defocus of v1.4 — folding them would muddy both).
    """

    coma: float = 0.0
    astigmatism: float = 0.0
    spherical: float = 0.0
    grating_azimuth_deg: float = 0.0

    @property
    def is_zero(self) -> bool:
        """Whether every aberration coefficient vanishes (the unaberrated pupil → the bit-for-bit seam)."""
        return self.coma == 0.0 and self.astigmatism == 0.0 and self.spherical == 0.0


def zernike_phase(f_total, imaging: Imaging, aberrations: "Aberrations | None"):
    """Pupil **aberration phase** ``exp(i·2π·W(u))`` from low-order Zernikes, on the 1-D order slice (v1.10).

    The companion to :func:`defocus_phase`: a collected order at full pupil frequency ``f_total``
    (``f_m + f_s``) rides the pupil at the normalized slice coordinate ``u = f_total/f_cut`` (``|u| ≤ 1``),
    and the wavefront error there (in waves) is the sum of the standard **balanced-Zernike** radial
    polynomials evaluated on that θ = 0/π slice::

        W(u) = coma·(3u³−2u)·cos φ_g  +  astigmatism·u²·cos 2φ_g  +  spherical·(6u⁴−6u²)

    — coma **odd** (it shifts the fringe), astigmatism/spherical **even**. The pupil phase is
    ``exp(i·2π·W)`` (waves → radians). Phase-only, so ``|amplitude|²`` is unchanged and aberrations
    **conserve power** (the §-conservation leg) exactly like defocus. Returns the literal float ``1.0``
    when ``aberrations`` is ``None`` or all-zero — so the unaberrated path is the v1 image **bit-for-bit**
    (the degenerate seam). ``f_total`` may be a scalar or array (1/nm).

    Scope edge (named, the §3/§7 discipline): this is the **1-D pupil slice** of the 2-D Zernikes (the
    line/space orders sample only the ``f_x`` axis), with the coefficient on the **peak** (Seidel-balanced)
    polynomial in waves — not the Noll RMS-normalized 2-D coefficient. Astigmatism along ``φ_g`` is
    degenerate with a **paraxial** ``u²`` defocus, while v1.4's :func:`defocus_phase` is the *exact*
    ``1 − cosθ`` — so the degeneracy is exact only as ``NA → 0``; the ``φ_g`` projection makes the H↔V
    best-focus split (which a defocus offset cannot mimic) the testable signature of astigmatism.
    """
    if aberrations is None or aberrations.is_zero:
        return 1.0
    u = np.asarray(f_total, dtype=float) / imaging.f_cut
    phi_g = math.radians(aberrations.grating_azimuth_deg)
    W = (aberrations.coma * (3.0 * u ** 3 - 2.0 * u) * math.cos(phi_g)
         + aberrations.astigmatism * u ** 2 * math.cos(2.0 * phi_g)
         + aberrations.spherical * (6.0 * u ** 4 - 6.0 * u ** 2))
    return np.exp(2j * np.pi * W)


def fundamental_complex(x_nm, intensity, pitch_nm: float) -> complex:
    """The image's **complex** fundamental Fourier coefficient at ``1/pitch`` — ``2·⟨I, e^{−2πix/p}⟩`` (v1.10).

    The quadrature-aware companion to :func:`fundamental_amplitude`, and the **coma↔defocus discriminator**
    the cos-only projection cannot see. Its **real part is exactly** :func:`fundamental_amplitude` (the
    ``cos`` projection), and its **phase is the lateral fringe shift**. For the on-axis three-beam image
    both defocus (even) and coma (odd) give the same fundamental *magnitude* ``4c₀c₁cos φ`` — invisible to
    the v1.4 metric — but defocus leaves the image even (phase 0, zero quadrature) while coma translates
    the fringe (the fundamental phase is **exactly** the ±1 order's odd aberration phase). ``np.angle`` of
    this is that shift; ``abs`` its magnitude. A balanced Fourier projection over one period on a uniform
    grid sampling ``endpoint=False`` — exact for the band-limited image.
    """
    x = np.asarray(x_nm, dtype=float)
    intensity = np.asarray(intensity, dtype=float)
    return complex(2.0 * np.mean(intensity * np.exp(-2j * np.pi * x / pitch_nm)))
