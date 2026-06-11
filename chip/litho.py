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
  treatment), an **aberration-free pupil apart from defocus** (the **defocus** phase is modelled in
  **v1.4** — see below — but no other Zernikes: coma/astigmatism/spherical are out), **Abbe not
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
  closes at dense pitch (at 193 nm / n 1.7 / a keep-half-the-fundamental floor: ~151 nm —
  numerically near this system's v1 resolution cutoff, a coincidence of these parameters, not a
  law). Scope edges, named: **linear exposure** (latent acid ∝ I — no Dill bleaching/saturation),
  **constant D** (the CAR reaction–diffusion system — concentration-dependent ``D(h)``, acid loss,
  deprotection kinetics — is the cited next rung), development still a constant threshold, and the
  lateral blur is 1-D in ``x`` while the standing-wave smoothing is 1-D in ``z`` (no coupled 2-D
  ``(x,z)`` resist volume — the engine's own last deferred regime).
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
               defocus_nm: float = 0.0):
    """Partially-coherent aerial image by the **Abbe sum over source points** (not Hopkins TCC).

    For each source point ``f_s`` (an illumination direction), the mask spectrum shifts so order ``m``
    sits at ``f_m + f_s`` in the pupil; the pupil passes it iff ``|f_m + f_s| ≤ f_cut = NA/λ``. The
    survivors interfere into a coherent sub-image (:func:`coherent_image`) evaluated at the **object**
    frequencies ``f_m`` (the common illumination carrier ``exp(2πi·f_s·x)`` has unit modulus and drops
    out of the intensity). The partially-coherent image is the **incoherent average** over the source::

        I(x) = (1/N_s)·Σ_{f_s} | Σ_m c_m·P(f_m + f_s)·D(f_m + f_s; z)·exp(2πi·f_m·x) |²

    where ``D`` is the :func:`defocus_phase` of each collected order (``z = defocus_nm``; ``D ≡ 1`` and the
    image is **bit-for-bit** the in-focus one when ``z = 0`` — the v1.4 degenerate seam). The defocus phase
    keys on the **full pupil coordinate** ``f_m + f_s`` (the order's true propagation angle), so an off-axis
    source point shifts an order's defocus sensitivity along with its pupil position.

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
        passed = [(f, c * defocus_phase(f + fs, imaging, defocus_nm))
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
    it at a fixed ``threshold`` to trace a **Bossung** CD-vs-defocus curve. The high-level entry mirroring
    :func:`oxidation.grow_oxide`. Returns a :class:`PrintedFeature`.

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
                            defocus_nm=defocus_nm)
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
                               defocus_nm=defocus_nm)
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
    ``method="crank_nicolson"`` by default — the contract's stated CN use case (temporal accuracy on
    a smooth, band-limited profile at moderate dt; the harmonics that survive the bake sit far below
    CN's oscillation scale), which is what makes the per-harmonic analytic anchor tight; conservation
    is structural (telescoping fluxes) under either method.
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
