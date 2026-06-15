"""Junction avalanche breakdown: a diffused junction's depth → its reverse breakdown voltage (device-targets slice 2).

The **new device output** the HV-I/O target needs (``docs/plans/device-targets.md`` slice 2). Phase-4 S/D
diffusion already produced a junction depth ``x_j`` and a sheet resistance ``R_s``; ``R_s`` became a device
consequence through source degeneration (:func:`chip.device.saturation_current`), but ``x_j`` fed **nothing
scored** — the long-channel ``V_t``/``I_Dsat`` reads never look at it. This module is the consumer that makes
``x_j`` a *device* number: the **avalanche breakdown voltage** ``BV`` of the drain–body junction, which a
short-channel logic part can ignore but an I/O-tolerant part lives or dies by.

Why this is slice 2's axis (the structural point — advisor 2026-06-15)
---------------------------------------------------------------------
``BV`` depends on **two** things, and that is the whole reason it earns its own slice rather than collapsing
into the growth/substrate slice (slice 3):

* the **lighter-doped side's doping** ``N_B`` (here the p-body / substrate ``N_A``) through the famous
  one-sided-abrupt law ``BV ∝ N_B^(−3/4)`` — *this is slice 3's lever* (a high-resistivity substrate buys a
  high BV), built here but **not** demonstrated as the slice-2 cross; and
* the **junction depth** ``x_j`` through *junction-curvature field crowding* — a shallow junction has a small
  radius of curvature at its cylindrical edge, the field crowds there, and breakdown comes **early** (a low
  BV); a deeper junction relaxes the curvature toward the planar limit. *This is slice 2's lever* (the
  diffusion drive-in sets ``x_j``).

The curvature term is what lets two wafers with **identical ``V_t``** (same substrate, same oxide) have
**different ``BV``** (different drive-in) — so ``BV`` is a genuinely *independent* device axis from ``V_t``,
not a relabel of the substrate doping. That independence is the device dimension slice 2 adds.

The model — avalanche from the cited ionization integral over the cylindrical field (no empirical fit)
-----------------------------------------------------------------------------------------------------
Avalanche breakdown is when the **ionization integral reaches unity** — one carrier crossing the depletion
region creates, on average, one more::

    ∫ α(E(r)) dr = 1 ,   α(E) = a · E^m   (the impact-ionization coefficient; Si: a ≈ 1.8e-35, m = 7)

For a **one-sided abrupt cylindrical junction** (the n⁺ S/D of radius ``r_j ≈ x_j`` in the p-body ``N_B``)
the depletion field from Gauss's law in cylindrical coordinates is::

    E(r) = (q·N_B / (2·ε·r)) · (r_d² − r²) ,    r_j ≤ r ≤ r_d

— **peaked at the junction surface** ``r = r_j`` (the field crowding), falling to 0 at the depletion edge
``r_d``. :func:`cylindrical_breakdown` root-finds the ``r_d`` at which ``∫α dr = 1`` and then integrates
``BV = ∫E dr``. This is the **same computation** Sze / Baliga–Ghandhi do; the curvature reduction *emerges*
from the electrostatics rather than being read off an empirical curve, so there is **no remembered
transcendental fit** — only the cited ionization power law and cylindrical Poisson. (The repo discipline:
the analytic leg is an independent recomputation, like :mod:`chip.device`'s depletion-Poisson solve.)

The **plane-parallel limit** (a flat junction, ``r_j → ∞``) reduces to the textbook one-sided-abrupt
closed form ``BV_pp = ε·E_m²/(2·q·N_B)`` with the self-consistent peak field ``E_m = (8·q·N_B/(a·ε))^(1/8)``
— which **is** the cited ``BV_pp ≈ 5.34e13·N_B^(−3/4) V`` (Baliga) and the cited ``E_crit ≈ 3–5e5 V/cm``,
both falling out of the *one* ionization coefficient. :func:`cylindrical_breakdown` recovers it as
``x_j → ∞``, and a deep diffused junction approaches it from below.

Validation triad (ADR 0005 §5 — cite the form, flag the magnitude)
------------------------------------------------------------------
* **Analytical limit (tight).** As ``r_j → ∞`` the cylindrical solve reduces to the plane-parallel closed
  form :func:`plane_parallel_breakdown` (the curvature ratio → 1); the planar form itself reproduces the
  cited ``BV_pp ∝ N_B^(−3/4)`` law. Monotonicity is exact and *by construction*: ``BV`` rises with ``x_j``
  (toward the planar ceiling) and falls with ``N_B`` — the two cited directions.
* **Benchmark (loose).** The cited Sze worked point — a Si one-sided abrupt junction at ``N_B = 1e15`` with
  ``r_j = 1 µm`` breaks down at ~80 V vs ~330 V plane-parallel (a curvature ratio ≈ 0.24,
  [[avalanche-breakdown-source]]). The model independently lands the **ratio** at ≈ 0.24 (the planar
  magnitude ~10 % low — the same flagged spread the repo carries elsewhere). The ionization coefficient
  ``a``, ``m`` are order-of-magnitude literature values (Baliga / Sze), **flagged**, never asserted tight.

Named scope edge (the honest ceiling)
-------------------------------------
* **Abrupt one-sided junction, cylindrical edge.** Real diffused S/D profiles are graded (erfc/Gaussian),
  not abrupt, and the worst point is the **spherical** corner (lower BV still) — both reduce BV further; the
  abrupt-cylindrical model is the standard first approximation and a mild *over*-estimate. ``r_j ≈ x_j`` is
  the textbook curvature-radius identity for a diffused planar junction (Sze, Baliga).
* **Bulk avalanche only.** Oxide-edge field plates, surface charge, and **gate-oxide dielectric breakdown**
  (a *different* mechanism — ~10 MV/cm in SiO₂, not modelled here) are out; this is the *junction* avalanche
  the I/O drain–body diode sees. (The plan's physics tripwire: do not conflate the two.)
* **A single effective ionization coefficient.** ``α = a·E^7`` lumps the electron/hole coefficients into one
  effective Si power law (Baliga's form); the rigorous treatment carries ``α_n ≠ α_p``. Folded into the
  flagged ``a``.

Units — semiconductor-conventional CGS (as :mod:`chip.device` / :mod:`chip.junction` / :mod:`chip.lifetime`)
-----------------------------------------------------------------------------------------------------------
``N_B`` in **cm⁻³**; radius/width ``r`` in **cm** (junction depth enters in **µm**, the cross-module length
currency, converted at the boundary); field ``E`` in **V/cm**; ``α`` in **cm⁻¹**; ``BV`` in **V**. Reuses
the same ``ε_Si`` (:mod:`chip.device`) and ``q`` (:mod:`chip.junction`) the rest of the device stack uses.

Validation boundary
-------------------
No shared engine — the breakdown is a closed-form law plus a 1-D root-find (like the compact ``V_t`` / the
SRH lifetime / Deal–Grove), so this module's tests carry the whole triad: the plane-parallel reduction +
the ``N_B^(−3/4)`` law (analytic limit), the monotonic curvature directions (by construction), and the cited
Sze curvature-ratio point (benchmark). The ionization coefficient is pinned to the cited source, *not*
carried from memory; its magnitude is a flagged house value.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .device import EPS_SI
from .diffusion_dopant import CM_PER_UM
from .junction import Q_ELEMENTARY

# --------------------------------------------------------------------------- #
# The cited impact-ionization coefficient α(E) = a·E^m (Si) — the loose benchmark leg.
# --------------------------------------------------------------------------- #
# a, m for silicon's effective avalanche ionization coefficient (Baliga, *Fundamentals of Power
# Semiconductor Devices* §3; Sze, *Physics of Semiconductor Devices* §2.4). FLAGGED order-of-magnitude
# literature values: this single effective power law reproduces BOTH the plane-parallel BV ∝ N^(−3/4)
# law AND the cited critical field E_crit ~3–5e5 V/cm — so it is the one knob the whole breakdown rides,
# and it carries the loose tier (the magnitudes are flagged, only the form + the N^(−3/4) trend cited).
A_IONIZATION: float = 1.8e-35      # cm⁶·V⁻⁷ → α in cm⁻¹ (with E in V/cm)
M_IONIZATION: int = 7              # the Si avalanche power-law exponent (the cited high-field power)


def ionization_coefficient(E: float) -> float:
    """Impact-ionization coefficient ``α(E) = a·E^m`` (cm⁻¹) at field ``E`` (V/cm) — the cited avalanche law.

    The rate at which a carrier creates electron–hole pairs per unit length; avalanche breakdown is when its
    integral over the depletion region reaches unity. The steep ``E^7`` is why breakdown is so sensitive to
    the *peak* field — and hence to junction curvature.
    """
    if E < 0.0:
        raise ValueError(f"field E must be ≥ 0, got {E}")
    return A_IONIZATION * E ** M_IONIZATION


# --------------------------------------------------------------------------- #
# 1. The plane-parallel limit — the cited one-sided-abrupt closed form (BV ∝ N^(−3/4))
# --------------------------------------------------------------------------- #
def plane_parallel_field(N_B: float, a: float = A_IONIZATION, m: int = M_IONIZATION) -> float:
    """Peak field at plane-parallel breakdown ``E_m = (8·q·N_B/(a·ε))^(1/(m+1))`` (V/cm) — the cited E_crit.

    Solving the ionization integral for the **triangular** field of a flat one-sided abrupt junction
    (``∫₀^W a·E_m^m·(1−x/W)^m dx = a·E_m^m·W/(m+1) = 1`` with ``W = ε·E_m/(q·N_B)`` from Poisson) gives this
    self-consistent peak field — the **critical field** ``E_crit``. For Si it is ~3e5 V/cm at ``N_B = 1e15``
    rising to ~5e5 at ``1e17`` (the cited weak ``N^(1/8)`` doping dependence), reproduced from the *one*
    ionization coefficient.
    """
    if N_B <= 0.0:
        raise ValueError(f"N_B must be positive, got {N_B}")
    return (8.0 * Q_ELEMENTARY * N_B / (a * EPS_SI)) ** (1.0 / (m + 1))


def plane_parallel_breakdown(N_B: float, a: float = A_IONIZATION, m: int = M_IONIZATION) -> float:
    """Plane-parallel breakdown voltage ``BV_pp = ε·E_m²/(2·q·N_B)`` (V) — the cited ``BV_pp ∝ N_B^(−3/4)``.

    The textbook one-sided abrupt-junction breakdown of a **flat** (infinite-radius) junction: the depletion
    width at breakdown is ``W = ε·E_m/(q·N_B)`` and ``BV = ½·E_m·W`` (the triangular field's area). With the
    self-consistent ``E_m ∝ N_B^(1/8)`` (:func:`plane_parallel_field`) this is ``∝ N_B^(2/8 − 1) =
    N_B^(−3/4)`` — the cited Baliga form ``≈ 5.34e13·N_B^(−3/4) V`` ([[avalanche-breakdown-source]]). It is
    the **ceiling** the curvature-reduced :func:`cylindrical_breakdown` approaches as ``x_j → ∞``.
    """
    E_m = plane_parallel_field(N_B, a, m)
    return EPS_SI * E_m ** 2 / (2.0 * Q_ELEMENTARY * N_B)


# --------------------------------------------------------------------------- #
# 2. The cylindrical solve — curvature crowding from the ionization integral (the reading)
# --------------------------------------------------------------------------- #
def _field_prefactor(N_B: float) -> float:
    """``K = q·N_B/(2·ε)`` (V/cm²) — the cylindrical depletion field is ``E(r) = K·(r_d²/r − r)``."""
    return Q_ELEMENTARY * N_B / (2.0 * EPS_SI)


def _ionization_integral(r_d: float, r_j: float, N_B: float,
                         a: float = A_IONIZATION, m: int = M_IONIZATION) -> float:
    """The avalanche ionization integral ``∫_{r_j}^{r_d} α(E(r)) dr`` over the cylindrical field (closed form).

    With ``E(r) = K·(r_d²/r − r)`` and ``α = a·E^m``, the integrand is ``a·K^m·(r_d²/r − r)^m``. Evaluated in
    the **normalized** variable ``s = r/r_d`` (so ``E = K·r_d·(1−s²)/s`` and the integral is
    ``a·K^m·r_d^(m+1)·∫_{ρ}^{1} ((1−s²)/s)^m ds`` with ``ρ = r_j/r_d``): the binomial sum is then over **O(1)**
    powers of ``s ∈ (0, 1]`` (plus a single ``ln`` term), so it is exact *and* cancellation-safe even for a
    deep junction (``ρ → 1``, where a binomial in the raw radii catastrophically cancels). Avalanche
    breakdown is the ``r_d`` at which this reaches ``1``.
    """
    K = _field_prefactor(N_B)
    rho = r_j / r_d
    total = 0.0
    for j in range(m + 1):
        coeff = math.comb(m, j) * ((-1) ** j)                # (1−s²)^m = Σ C(m,j)(−1)^j s^(2j)
        e = 2 * j - m                                        # ∫ s^e ds  (e = 2j−m, from the /s^m)
        if e == -1:
            total += coeff * (-math.log(rho))                # ∫_ρ^1 s⁻¹ ds = −ln ρ
        else:
            total += coeff * (1.0 - rho ** (e + 1)) / (e + 1)
    return a * K ** m * r_d ** (m + 1) * total


def _depletion_voltage(r_d: float, r_j: float, N_B: float) -> float:
    """The junction voltage ``∫_{r_j}^{r_d} E(r) dr = K·r_d²·[−ln ρ − (1−ρ²)/2]`` (V), ``ρ = r_j/r_d`` (closed form).

    The same normalized ``s = r/r_d`` form as :func:`_ionization_integral` (so ``E = K·r_d·(1−s²)/s`` and the
    integral is ``K·r_d²·∫_ρ^1 (1/s − s) ds``) — cancellation-safe as the junction deepens (``ρ → 1``), where
    the raw ``r_d²·ln(r_d/r_j) − (r_d²−r_j²)/2`` form loses its small ``O((r_d−r_j)²)`` difference."""
    K = _field_prefactor(N_B)
    rho = r_j / r_d
    return K * r_d * r_d * (-math.log(rho) - 0.5 * (1.0 - rho * rho))


def cylindrical_breakdown(N_B: float, r_j_cm: float,
                          a: float = A_IONIZATION, m: int = M_IONIZATION) -> float:
    """Avalanche breakdown voltage ``BV`` (V) of a one-sided abrupt **cylindrical** junction (the reading).

    Root-finds the depletion edge ``r_d`` at which the ionization integral (:func:`_ionization_integral`)
    over the curvature-crowded field reaches unity, then returns the junction voltage ``∫E dr``
    (:func:`_depletion_voltage`). ``N_B`` (cm⁻³) is the **lighter-doped** body/substrate; ``r_j_cm`` the
    junction radius of curvature ``≈ x_j`` (cm). A **shallow** junction (small ``r_j``) crowds the field at
    its edge → breakdown early → **low BV**; a **deep** junction relaxes toward the planar ceiling
    :func:`plane_parallel_breakdown`. Reduces to that ceiling as ``r_j → ∞`` (the analytic-limit seam).
    """
    if not math.isfinite(N_B) or N_B <= 0.0:
        raise ValueError(f"N_B must be finite and positive, got {N_B}")
    if not math.isfinite(r_j_cm) or r_j_cm <= 0.0:    # nan slips past a bare `<= 0` (nan comparisons are False)
        raise ValueError(f"junction radius r_j must be finite and positive, got {r_j_cm}")
    from scipy.optimize import brentq

    # Bracket r_d ∈ (r_j, r_j + many·W_pp): the integral is 0 at r_d=r_j and monotone-increasing in r_d.
    # The plane-parallel depletion width sets the scale; expand the upper bound until the integral clears 1.
    W_pp = EPS_SI * plane_parallel_field(N_B, a, m) / (Q_ELEMENTARY * N_B)
    lo = r_j_cm * (1.0 + 1.0e-12)
    hi = r_j_cm + W_pp
    for _ in range(60):
        if _ionization_integral(hi, r_j_cm, N_B, a, m) > 1.0:
            break
        hi = r_j_cm + 2.0 * (hi - r_j_cm)
    else:                                                    # pragma: no cover — unreachable for physical N_B
        raise RuntimeError(f"could not bracket the breakdown depletion edge for N_B={N_B}, r_j={r_j_cm}")
    r_d = brentq(lambda rd: _ionization_integral(rd, r_j_cm, N_B, a, m) - 1.0, lo, hi,
                 xtol=1.0e-12, rtol=1.0e-12)
    return _depletion_voltage(r_d, r_j_cm, N_B)


# --------------------------------------------------------------------------- #
# 3. The bundled breakdown reading (the loose-coupling currency the device step lifts onto the die)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class JunctionBreakdown:
    """A diffused junction's avalanche breakdown: the cylindrical BV, the planar ceiling, and the geometry.

    ``bv`` (V) the curvature-reduced avalanche breakdown of the drain–body junction; ``bv_pp`` (V) the
    plane-parallel ceiling it approaches as the junction deepens; ``N_B`` (cm⁻³) the lighter-doped body the
    breakdown reads; ``x_j_um`` (µm) the junction depth (``= r_j``). Plain scalars — the loose-coupling
    currency the fab-line game's device step lifts onto the die (a new field), the analogue of
    :class:`chip.junction.Junction` / :class:`chip.lifetime.DiodeLeakage`.
    """

    bv: float
    bv_pp: float
    N_B: float
    x_j_um: float

    @property
    def curvature_ratio(self) -> float:
        """``BV / BV_pp`` ∈ (0, 1] — how far curvature crowding pulls breakdown below the planar ceiling."""
        return self.bv / self.bv_pp


def junction_breakdown(N_B: float, x_j_um: float) -> JunctionBreakdown:
    """Read a junction's avalanche breakdown off its body doping ``N_B`` (cm⁻³) and depth ``x_j_um`` (µm).

    Convenience wiring of :func:`cylindrical_breakdown` (the reading) + :func:`plane_parallel_breakdown`
    (the ceiling) for the device step. ``x_j_um`` is the S/D junction depth from the diffusion step (taken
    as the curvature radius ``r_j``); ``N_B`` is the p-body/substrate ``effective_channel_N_A`` (the
    lighter-doped side the drain–body junction breaks down into). *A shallow junction in, a low breakdown
    out — the device consequence the junction depth could not previously reach.*
    """
    bv = cylindrical_breakdown(N_B, x_j_um * CM_PER_UM)
    return JunctionBreakdown(bv=bv, bv_pp=plane_parallel_breakdown(N_B), N_B=N_B, x_j_um=x_j_um)
