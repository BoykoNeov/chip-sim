"""Lithography: the aerial image — two-beam cos² anchor + Abbe sum-over-source (Chip Phase 3).

The pattern-transfer step, and the project's **risk phase** — so the tractability gradient lives
**inside this module**, not just in the scope ceiling. This is the chip project's **one genuinely-new
module**: where Phase 1a reused the frozen PDE spine (dopant diffusion) and Phase 2 was a small
closed-form ODE (Deal–Grove oxidation), lithography is **Fourier optics** — and it stays *chip-local*
(`projects/chip/litho.py`), **not** promoted to `engines/`: only chip uses it, so per the rule-of-three
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
  treatment), an **ideal in-focus aberration-free pupil** (no defocus phase, no Zernikes), **Abbe not
  Hopkins** (a *method* choice — same answer, different cost — named because Hopkins is the tar pit), a
  **constant-threshold resist** (no acid diffusion / PEB blur / development kinetics), a **1-D
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
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Constants — unit conversion + the cited resolution / printability benchmarks
# --------------------------------------------------------------------------- #
UM_PER_NM = 1.0e-3        # 1 nm = 1e-3 µm — CD reported in both; µm is the cross-module length currency

# Rayleigh k₁ factors (half-pitch R = k₁·λ/NA), pinned to litho-aerial-image-source (Mack / lithoguru):
K1_COHERENT = 0.5        # conventional coherent (on-axis, three-beam ±1) half-pitch limit
K1_TWO_BEAM = 0.25       # two-beam (extreme off-axis / dipole) physical half-pitch floor ("lowest we can go")

# NILS printability rule of thumb (litho-aerial-image-source): ≥1 minimally resolved, ≳2 robust process.
NILS_PRINTABLE = 2.0

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


def rayleigh_resolution(wavelength_nm: float, NA: float, k1: float = K1_TWO_BEAM) -> float:
    """Rayleigh resolvable half-pitch ``R = k₁·λ/NA`` (nm) — the standalone form of :meth:`Imaging.resolution`.

    ``k1`` selects the regime: 0.5 conventional coherent, 0.25 the two-beam physical floor (the cited
    ``[[litho-aerial-image-source]]`` values). ``R`` is the half-pitch (= CD of a dense 1:1 line/space).
    """
    return k1 * wavelength_nm / NA


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


def abbe_image(x_nm, orders, imaging: Imaging, source_fs=None, n_source: int = 21):
    """Partially-coherent aerial image by the **Abbe sum over source points** (not Hopkins TCC).

    For each source point ``f_s`` (an illumination direction), the mask spectrum shifts so order ``m``
    sits at ``f_m + f_s`` in the pupil; the pupil passes it iff ``|f_m + f_s| ≤ f_cut = NA/λ``. The
    survivors interfere into a coherent sub-image (:func:`coherent_image`) evaluated at the **object**
    frequencies ``f_m`` (the common illumination carrier ``exp(2πi·f_s·x)`` has unit modulus and drops
    out of the intensity). The partially-coherent image is the **incoherent average** over the source::

        I(x) = (1/N_s)·Σ_{f_s} | Σ_m c_m·P(f_m + f_s)·exp(2πi·f_m·x) |²

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
        passed = [(f, c) for (f, c) in orders if abs(f + fs) <= cutoff]
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
    whether the image modulates at all (contrast above a small floor). Plain scalars — the loose-coupling
    currency Phase 4 consumes.
    """

    pitch_nm: float
    cd_nm: float
    contrast: float
    nils: float
    threshold: float

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
) -> PrintedFeature:
    """Image a line/space grating and read the printed feature — the Phase-3 'recipe in, CD out' entry.

    Builds the grating spectrum (:func:`grating_orders`), forms the partially-coherent Abbe image over
    **one period** (``n_x`` points, ``endpoint=False`` — so the spatial mean is exact), and reads the
    contrast, NILS (at the nominal edge ``x = duty·p/2``, with ``w = (1−duty)·p`` the line width), and
    the constant-threshold CD of the dark line. ``threshold`` defaults to the **image mean** (a balanced
    clip → nominal duty on a well-resolved image); pass a fixed value to sweep pitch at constant dose.
    The high-level entry mirroring :func:`oxidation.grow_oxide`. Returns a :class:`PrintedFeature`.
    """
    orders = grating_orders(pitch_nm, n_orders=n_orders, duty=duty)
    x = np.linspace(0.0, pitch_nm, n_x, endpoint=False)
    intensity = abbe_image(x, orders, imaging, source_fs=source_fs, n_source=n_source)
    contrast = image_contrast(intensity)
    edge_nm = duty * pitch_nm / 2.0
    linewidth_nm = (1.0 - duty) * pitch_nm
    image_nils = nils(x, intensity, edge_nm, linewidth_nm)
    clip = float(intensity.mean()) if threshold is None else threshold
    cd = print_cd(x, intensity, clip, polarity="dark")
    return PrintedFeature(
        pitch_nm=pitch_nm, cd_nm=cd, contrast=contrast, nils=image_nils, threshold=clip,
    )
