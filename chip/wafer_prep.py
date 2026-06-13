"""Wafer prep: the defect-limited yield law + the wafer-geometry bookkeeping (front-of-line).

The third front-of-line step of the fab line proper (plan §5 step 3, §7; ADR 0005), and the
physics the fab-line game's **G3** consumes to make the across-wafer die map *physical*. Two parts,
laddered honestly per the plan's fidelity ladder ("geometry exact, particles stochastic"):

1. **The defect-limited yield law (the cited triad core).** A wafer carries random *killer*
   particle defects; a die that catches one is dead — *functionally*, regardless of its parametric
   device. With a **killer-defect density** ``D₀`` (defects/cm²) and a die critical **area** ``A``
   (cm²), the probability a die catches **zero** killer defects — its yield — is the zero-term of a
   Poisson process::

       Y(D₀, A) = exp(−D₀·A)                                   (Poisson / Murphy)

   Real defects **cluster** (they are not independent), which *raises* yield over the Poisson
   estimate; the canonical generalization is the **negative-binomial** (gamma-compound-Poisson)
   model with a clustering parameter ``α``::

       Y(D₀, A, α) = (1 + D₀·A/α)^(−α)                          (Stapper, clustered)

   which → the Poisson form as ``α → ∞`` (no clustering). This module builds the **Poisson** law as
   the tight, asserted core and carries the negative-binomial **formula** for the ``α→∞`` limit
   test; the *clustered placement* (a spatially-correlated defect realization) is the **named scope
   edge**, deferred (the game places defects as an un-clustered Poisson process — see
   :mod:`fab_game.defects`).

2. **The wafer-geometry bookkeeping (exact, house numbers).** Slicing a boule, then lapping +
   CMP, sets a wafer's **thickness**, its **TTV** (total thickness variation — the flatness that a
   later litho step's depth-of-focus budget must tolerate), and its **bow**. This is deterministic
   mechanical bookkeeping ("geometry exact"): material removal eats thickness and improves TTV; bow
   is set up front (crystal/slicing) and CMP does **not** fix it (that is anneal / edge-grind, out
   of scope). The numbers here are illustrative **house** values, flagged — only the *relations*
   (removal reduces thickness; CMP reduces TTV) are asserted.

Validation triad (plan §7) — what is tight vs loose
---------------------------------------------------
* **Analytical limit.** ``Y(0)=1`` **exactly** (no defects / zero area → perfect yield — the one
  bit-exact anchor), and the **negative-binomial → Poisson limit** ``(1+D₀A/α)^(−α) → exp(−D₀A)``
  as ``α→∞`` (a *convergent* limit, asserted to a tolerance — not bit-for-bit, unlike Czochralski's
  ``k→1``). Clustering (finite ``α``) always *raises* yield over Poisson — also asserted.
* **Conservation / identity (tight).** **Area additivity** of the Poisson law:
  ``Y(A₁+A₂) = Y(A₁)·Y(A₂)`` (a die of combined area kills exactly as two independent sub-dies do —
  the multiplicativity that makes ``Y=exp(−D₀A)`` the *only* defect-independent law). And
  ``Y = exp(−λ)`` with ``λ = D₀·A`` the mean killer count (:func:`expected_killer_defects`) — the
  Poisson rate the stochastic placement (:mod:`fab_game.defects`) must converge to.
* **Benchmark (loose) — the cited yield models + an illustrative ``D₀`` band.** The forms are the
  textbook **Murphy (1964, Proc. IEEE 52:1537)** Poisson/compound-Poisson and **Stapper**
  negative-binomial (gamma-compound-Poisson; α→∞ → Poisson) yield models (Sze, *VLSI Technology*,
  yield chapter). The ``D₀`` magnitudes (:data:`DEFECT_DENSITY_BANDS`) are **flagged illustrative**
  process levels (a clean mature line vs a dirty development line), not asserted fab numbers — and
  the coarse die map means the per-die area ``A`` is itself illustrative (ADR 0005 §5: the game is
  scored on mechanics, not magnitudes). Murphy's triangular-``f(D)`` model corresponds to a
  negative-binomial ``α ≈ 4.2`` — a named landmark, not asserted.

Named scope edge (the honest ceiling)
-------------------------------------
* **Un-clustered placement.** The asserted law and the game's placement are **Poisson**
  (independent defects). Real defects cluster, so a single wafer's yield has more spread than
  Poisson predicts; the negative-binomial captures the *mean*, but a **spatially-clustered**
  realization (and a fitted ``α``) is the calibrated edge — built here only as the ``α→∞`` limit
  formula, not as a clustered sampler.
* **Geometry is house bookkeeping**, not a stress/curvature model. Bow is carried, not derived
  from film stress (no Stoney's-equation curvature); CMP improves TTV by a flagged efficiency, not
  a contact-mechanics removal model. The *relations* are exact; the *magnitudes* are illustrative.
* **TTV does not yet feed the focus budget.** A non-flat wafer eats a litho step's depth of focus
  (residual site-flatness, not raw bow — wafers are vacuum-chucked flat in the scanner); G3 gates
  geometry (out-of-spec → scrap) but does **not** wire TTV into the defocus chain. That focus-budget
  edge is the immediate next propagation wire (it would add a flagged house mapping nm-TTV → nm of
  defocus onto the existing center-to-edge focus term).

Units
-----
Defect density ``D₀`` in **cm⁻²**; area ``A`` in **cm²** → ``λ = D₀·A`` dimensionless; yield ``Y``
dimensionless ∈ ``(0, 1]``. Wafer geometry (thickness / TTV / bow) in **µm**.

Validation boundary
-------------------
No shared engine — the yield law is a closed form (like Deal–Grove / Scheil / the compact ``V_t``),
so this module's tests carry the whole triad: the ``Y(0)=1`` + ``α→∞`` limits (analytic), area
additivity + the ``λ`` identity (conservation), and the cited Murphy/Stapper forms + an illustrative
``D₀`` band (benchmark). The stochastic *placement* and its convergence to ``exp(−D₀A)`` live in the
game layer (:mod:`fab_game.defects`, a mechanics invariant), where the randomness belongs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# 1. The defect-limited yield law — Poisson core + the negative-binomial limit
# --------------------------------------------------------------------------- #
def expected_killer_defects(defect_density, area_cm2):
    """Mean killer-defect count ``λ = D₀·A`` on a die of area ``area_cm2`` (cm²) — the Poisson rate.

    ``defect_density`` in cm⁻², ``area_cm2`` in cm² (scalar or array). This is the rate the
    stochastic placement (:mod:`fab_game.defects`) draws against, and the ``λ`` in ``Y = exp(−λ)``.
    """
    lam = np.asarray(defect_density, dtype=float) * np.asarray(area_cm2, dtype=float)
    return float(lam) if lam.ndim == 0 else lam


def poisson_yield(defect_density, area_cm2):
    """Defect-limited die yield ``Y = exp(−D₀·A)`` — the Poisson zero-defect probability (Murphy).

    The probability a die of critical area ``area_cm2`` (cm²) catches **zero** killer defects at
    density ``defect_density`` (cm⁻²). Returns ``1.0`` **exactly** at zero density or zero area (the
    bit-exact analytic anchor), decreases monotonically in both ``D₀`` and ``A``, and is multiplicative
    in area (:func:`negative_binomial_yield` generalizes it for clustered defects). Scalar or array.
    """
    lam = expected_killer_defects(defect_density, area_cm2)
    y = np.exp(-np.asarray(lam, dtype=float))
    return float(y) if y.ndim == 0 else y


def negative_binomial_yield(defect_density, area_cm2, alpha: float):
    """Clustered die yield ``Y = (1 + D₀·A/α)^(−α)`` — Stapper's negative-binomial model.

    ``alpha`` is the clustering parameter: small ``α`` → strongly clustered defects (yield well
    above Poisson), large ``α`` → little clustering. As ``α → ∞`` this → :func:`poisson_yield`
    (the no-clustering limit). For any finite ``α > 0`` it is **≥** the Poisson yield (clustering
    concentrates defects on fewer dies → more zero-defect dies). Murphy's triangular-``f(D)`` model
    corresponds to ``α ≈ 4.2``. ``Y(0)=1`` exactly. Scalar or array (over density/area).
    """
    if alpha <= 0.0:
        raise ValueError(f"clustering parameter alpha must be > 0, got {alpha}")
    lam = np.asarray(expected_killer_defects(defect_density, area_cm2), dtype=float)
    y = (1.0 + lam / alpha) ** (-alpha)
    return float(y) if y.ndim == 0 else y


# Illustrative killer-defect density levels (cm⁻²) — FLAGGED house process levels, not cited fab
# numbers. A clean mature line carries far fewer killer defects than an immature development line;
# the ratio is the teachable contrast (cleaner line → higher yield at the same die area). These set
# the game's defect knob; the *law* (exp(−D₀A)) is what is cited, the magnitudes are house.
DEFECT_DENSITY_BANDS: dict[str, float] = {
    "development": 0.5,     # cm⁻² — a dirty / immature line (low yield)
    "pilot": 0.15,          # cm⁻² — ramping
    "production": 0.05,     # cm⁻² — a clean mature line (high yield)
}


# --------------------------------------------------------------------------- #
# 2. Wafer-geometry bookkeeping — slice → lap/CMP (exact, house numbers)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class WaferGeometry:
    """A wafer's prepped geometry — plain scalars the fab-line game gates on (the §3 geometry field).

    ``thickness_um`` the final wafer thickness; ``ttv_um`` the total thickness variation (flatness —
    the smaller the better, what a litho depth-of-focus budget must tolerate); ``bow_um`` the wafer
    bow (set at slicing/crystal, *not* fixed by CMP). All in µm. Illustrative house numbers — only
    the relations (removal reduces thickness, CMP reduces TTV) are physics; the values are flagged.
    """

    thickness_um: float
    ttv_um: float
    bow_um: float


def prep_geometry(
    *,
    incoming_thickness_um: float = 800.0,
    slice_ttv_um: float = 2.0,
    slice_bow_um: float = 25.0,
    removal_um: float = 60.0,
    ttv_improvement: float = 0.85,
) -> WaferGeometry:
    """Slice → lap + CMP → the prepped :class:`WaferGeometry` (exact mechanical bookkeeping).

    Lapping/CMP **removes** ``removal_um`` of silicon (thickness shrinks) and **improves** TTV by the
    fraction ``ttv_improvement`` ∈ ``[0, 1]`` (the planarizing action — final TTV =
    ``slice_ttv_um·(1 − ttv_improvement)``). **Bow is carried through unchanged**: it is set by the
    crystal/slicing and CMP does not correct it (that is anneal / edge-grind — out of scope). Raises
    if the removal would consume the whole wafer (a re-polish that eats too much — the physical limit
    the game's re-polish rework runs into). Deterministic — no randomness here ("geometry exact").
    """
    if not 0.0 <= ttv_improvement <= 1.0:
        raise ValueError(f"ttv_improvement must be in [0, 1], got {ttv_improvement}")
    thickness_out = incoming_thickness_um - removal_um
    if thickness_out <= 0.0:
        raise ValueError(
            f"removal {removal_um} µm ≥ incoming thickness {incoming_thickness_um} µm — "
            "nothing left of the wafer")
    return WaferGeometry(
        thickness_um=thickness_out,
        ttv_um=slice_ttv_um * (1.0 - ttv_improvement),
        bow_um=slice_bow_um,
    )
