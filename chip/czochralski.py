"""Czochralski crystal growth: the Scheil axial segregation profile (the front-of-line physics).

The first step of the fab line proper, and the **first new front-of-line physics** the fab-line
game adds on top of chip-sim (plan §5 step 2, §7; ADR 0005). A Czochralski puller draws a single
silicon boule from a doped melt; because a dopant's equilibrium **segregation coefficient**
``k = C_solid/C_liquid`` is ≠ 1, the solid that freezes first is *not* the same concentration as
the melt, and as the boule grows the rejected (``k<1``) solute piles up in the shrinking melt — so
the dopant concentration **varies down the boule's length**. Each wafer sliced from a different
axial position therefore starts at a different substrate doping (and resistivity), which then sets
a different device ``V_t`` — the Scheil spread is the front-of-line *cause* of a batch's V_t spread.

The Scheil equation (normal freezing, the closed form)
------------------------------------------------------
With ``z`` the **fraction of the melt already solidified** (``0`` at the seed end, ``→1`` at the
tail), a well-mixed melt and a constant ``k`` give the **Scheil / normal-freezing** profile::

    C_s(z) = k·C_0·(1 − z)^(k−1)                                  (cm⁻³)

where ``C_0`` is the initial melt concentration. We parameterize instead by the **seed-end
concentration** ``N_seed ≡ C_s(0) = k·C_0`` — the physically natural knob (it is the spec'd doping
of wafer #1) and the one that makes the ``z=0`` slice *exact* (``(1−0)^(k−1) = 1`` for any ``k``)::

    C_s(z) = N_seed·(1 − z)^(k−1),      C_0 = N_seed / k

For ``k < 1`` (B, P, As, Sb — every shallow dopant in Si) the solute is rejected into the melt, so
``C_s`` **rises** down the boule (monotonically, diverging as ``z→1``). For ``k = 1`` it is uniform.

Purification is the *same* equation read the other way: the seed end gets only a fraction ``k`` of
the melt's average concentration (``C_s(0)/C_0 = k``), so a species with a **tiny** ``k`` (metals:
Fe ~1e-5, Cu ~1e-4) is scrubbed from the seed end by ~5 orders of magnitude, while B (``k ≈ 0.8``)
is barely purified. That contrast — superb metal removal, poor dopant removal — is *why* Czochralski
(and zone refining) purify, straight from the cited ``k`` table (the §5a / G4 purification story
builds on it).

Validation triad (plan §7) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight) — the ``k→1`` uniform-doping limit + the exact seed-end value.** At
  ``k = 1`` the profile collapses to the constant ``C_s ≡ N_seed`` (no segregation), to machine
  precision; and ``C_s(0) = N_seed`` **exactly** for any ``k`` — the seam the fab-line harness
  (G2) relies on to reproduce ``demo_device`` bit-for-bit at the seed slice.
* **Conservation (tight) — the solute mass balance.** All the dopant charged into the melt ends up
  in the boule: the axial integral of ``C_s`` over the whole boule recovers the initial melt
  concentration, ``∫₀¹ C_s(z) dz = N_seed/k = C_0`` (the ``z→1`` divergence of ``C_s`` is
  **integrable** for ``k>0``). The closed-form partial integral ``(N_seed/k)·(1 − (1−z)^k)``
  (:func:`scheil_cumulative`) is checked against direct quadrature on ``[0, z≤0.9]`` (off the
  singular endpoint) and against the analytic full-boule limit ``N_seed/k``.
* **Benchmark (loose) — the cited ``k`` table + the resistivity it implies.** The equilibrium
  segregation coefficients are the canonical **Trumbore (1960, BSTJ 39:205)** values — the *same*
  reference already cited for solid solubility ([[dopant-solid-solubility-source]]), which also
  tabulates distribution coefficients (B ≈ 0.80, P ≈ 0.35 verified against the source). The boule's
  resistivity ``ρ(z) = 1/(q·μ(N)·N)`` reuses the **Masetti** ``μ(N)`` of :mod:`chip.junction` (an
  *independent* transport model — the same non-circular cross-check the junction ``R_s`` uses). The
  resistivity-spread *magnitudes* down the boule are the loose leg, and the ``z→1`` tail is
  unphysical (you never solidify the whole melt) — so the tight legs are the limit and the integral,
  **not** a tail number.

Named scope edge (the honest ceiling)
-------------------------------------
* **Equilibrium, well-mixed melt, constant ``k``.** Scheil assumes complete melt mixing and an
  interface at equilibrium. Real growth has a diffusion boundary layer, so the *effective*
  ``k_eff(v)`` rises toward 1 with pull rate/stirring — now **BUILT (CG-1, opt-in)** as the
  Burton–Prim–Slichter closed form (:func:`effective_segregation_coefficient`, §1b): pull rate
  becomes a live knob that flattens the Scheil drift, with ``k₀`` the tight Trumbore anchor and the
  ``δ``/``D`` ``v``-dependence the calibrated/flagged leg (off by default → the well-mixed ``k₀``
  limit, the seam). Its **deferred brakes** — constitutional supercooling / **striations**, the
  **V/G point-defect (void) criterion** (CG-2), the dislocation-free Dash neck and a max-pull limit —
  are still out (plan §6a fidelity ladder: Scheil/BPS-limit **High**, the ``v``-magnitude Mid, the
  defect cost not yet modelled). So CG-1 has **no in-model cost to pulling faster** — the cost is CG-2,
  named not built.
* **Oxygen / thermal donors are a separate, looser story.** Crucible-oxygen incorporation is *not*
  dopant segregation (its ``k`` is contested ~0.25–1.4 and incorporation is dissolution-controlled),
  and the ~450 °C thermal-donor kinetics that make some of it electrically active are a calibrated
  consequence model — held as the fenced contamination follow-on (plan §5a bucket 4 / G4), **not**
  asserted with Scheil's anchors.
* **Full dopant activation at 300 K** (inherited from the Masetti/junction resistivity model): the
  electrically-active concentration is taken equal to the chemical one — fine at the substrate
  ``~1e15–1e17`` here; the active-vs-chemical edge is the repo's standing ceiling.

Units — semiconductor-conventional CGS (as :mod:`chip.junction` / :mod:`chip.device`)
------------------------------------------------------------------------------------
``z`` dimensionless ∈ ``[0, 1)``; concentration ``N`` in **cm⁻³**; mobility ``μ`` in **cm²/V·s**;
``q`` in **C** → resistivity ``ρ = 1/(qμN)`` in **Ω·cm** directly. Boule geometry (length/diameter)
is carried in **mm** for the narrative only — it does not enter the physics.

Validation boundary
-------------------
No shared engine here — the Scheil profile is a closed form (like Deal–Grove / the compact ``V_t``),
so this module's tests carry the whole triad: the ``k→1`` limit + exact seed value (analytic), the
solute mass balance (conservation), and the cited Trumbore ``k`` + Masetti resistivity (benchmark).
The ``k`` values are pinned to the cited source, **not** carried from memory.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .junction import Q_ELEMENTARY, mobility

# --------------------------------------------------------------------------- #
# 1. The cited segregation-coefficient table (Trumbore 1960) — the benchmark anchor
# --------------------------------------------------------------------------- #
# Equilibrium segregation (distribution) coefficients k₀ = C_solid/C_liquid in silicon, the
# canonical Trumbore (1960, BSTJ 39:205) values — the same reference already cited for solid
# solubility ([[dopant-solid-solubility-source]]), which also tabulates distribution coefficients.
# B ≈ 0.80 and P ≈ 0.35 are the load-bearing, source-verified pair (the substrate is boron, whose
# near-unity k is *why* it barely segregates). The metal entries are illustrative,
# order-of-magnitude values for the purification-scrubbing contrast (tiny k → scrubbed hard) —
# flagged, not asserted tight, and never on the device path.
#
# NB — a *different* segregation than v1.2's: this is the dopant's melt↔crystal coefficient at
# Czochralski growth; the v1.2 ``m`` ([[dopant-segregation-source]]) is the dopant's Si↔SiO₂
# coefficient at oxidation. Same word, different interface — kept distinct on purpose.
SEGREGATION_K: dict[str, float] = {
    "B": 0.80,     # boron     — near unity → barely segregates (the substrate; load-bearing)
    "P": 0.35,     # phosphorus
    "As": 0.30,    # arsenic
    "Sb": 0.023,   # antimony  — strong segregation
    # Illustrative fast-segregating impurities (order-of-magnitude; the scrubbing contrast, flagged) —
    # used by the G4 purification module (:mod:`chip.purification`), which reuses this one table:
    "Fe": 8.0e-6,  # deep-level metal — scrubbed ~5 orders in one zone pass
    "Cu": 4.0e-4,  # deep-level metal
    "Na": 1.0e-2,  # mobile ion (sodium) — strong segregator; the device-poisoning oxide contaminant (G4)
}


def segregation_coefficient(dopant: str) -> float:
    """The equilibrium segregation coefficient ``k = C_solid/C_liquid`` for ``dopant`` (Trumbore 1960)."""
    if dopant not in SEGREGATION_K:
        raise KeyError(f"no segregation coefficient for {dopant!r} (have {sorted(SEGREGATION_K)})")
    return SEGREGATION_K[dopant]


# --------------------------------------------------------------------------- #
# 1b. Pull rate → effective segregation k_eff(v) — Burton–Prim–Slichter (CG-1)
# --------------------------------------------------------------------------- #
# Scheil's equilibrium ``k₀`` assumes a *well-mixed* melt. Real growth leaves a thin diffusion
# **boundary layer** ``δ`` at the freezing interface, across which rejected solute (``k₀<1``) piles
# up — so the interface sees a richer liquid and the **effective** segregation coefficient rises
# toward 1. Burton–Prim–Slichter (J. Chem. Phys. 21:1987, 1953) give it in closed form::
#
#     k_eff = k₀ / [ k₀ + (1 − k₀)·e^(−Δ) ],     Δ = v·δ / D      (dimensionless)
#
# with ``v`` the growth (pull) rate, ``δ`` the boundary-layer thickness (set by crucible/crystal
# rotation — faster stirring → thinner ``δ``), and ``D`` the solute diffusivity in the melt. ``Δ`` is
# the **normalized growth velocity**: the limits are exact and physical —
#   * ``Δ → 0`` (slow pull / vigorous stirring): ``k_eff → k₀`` **exactly** — the well-mixed Scheil
#     limit (the seam: the fab-line boule reproduces G2 bit-for-bit when CG-1 is off);
#   * ``Δ → ∞`` (fast pull / no stirring): ``k_eff → 1`` — **complete solute trapping**, no
#     segregation, a uniform axial profile.
# So **pulling faster flattens the Scheil drift** (``k_eff`` toward 1 → ``C_s(z)`` flatter). Fidelity
# is **Mid** (plan §7): ``k₀`` stays the **tight** Trumbore anchor; the ``v``-dependence — i.e. the
# ``δ`` and ``D`` magnitudes below — is the **calibrated/flagged** leg.
#
# HONEST MAGNITUDE (load-bearing — boron barely segregates already). For the boron substrate
# (``k₀=0.80``) at *realistic* Si pull (≈0.5–2 mm/min → ``Δ≈0.07–0.28``) ``k_eff`` rises only to
# ≈0.81–0.84 — a **modest** flattening. A near-flat boule (``k_eff≳0.99``) needs ``Δ≳3``, i.e. pull
# rates well **beyond realistic Si growth** (~20 mm/min here). The dramatic-flattening regime is
# therefore an *illustrative* extrapolation, flagged as such — not a claim about real Si CZ.
#
# These δ/D are FLAGGED representative house values (the calibrated leg), NOT tight-cited: the melt
# diffusivity of a light solute in molten Si is ~1e-4..1e-3 cm²/s, and the rotation-set boundary
# layer is ~0.01..0.05 cm. Only the BPS *form* and its limits are asserted; the Δ-mapping magnitude
# is house (like the game's other flagged process bands).
BPS_MELT_DIFFUSIVITY_CM2_S: float = 2.4e-4   # solute diffusivity in molten Si (flagged, ~1e-4..1e-3)
BPS_BOUNDARY_LAYER_CM: float = 0.02          # diffusion boundary layer ~200 µm (flagged; rotation-set)


def normalized_growth_velocity(
    pull_rate_mm_min: float,
    *,
    boundary_layer_cm: float = BPS_BOUNDARY_LAYER_CM,
    melt_diffusivity_cm2_s: float = BPS_MELT_DIFFUSIVITY_CM2_S,
) -> float:
    """The dimensionless BPS normalized growth velocity ``Δ = v·δ/D`` from physical inputs.

    Converts ``pull_rate_mm_min`` (mm/min → cm/s) and combines with the **flagged** boundary layer
    ``δ`` (cm, rotation-set) and melt diffusivity ``D`` (cm²/s). ``Δ ≥ 0``; ``Δ = 0`` at zero pull
    (the well-mixed limit). Only the *form* is physics; the ``δ``/``D`` magnitudes are house numbers.
    """
    if pull_rate_mm_min < 0.0:
        raise ValueError(f"pull rate must be ≥ 0, got {pull_rate_mm_min}")
    if boundary_layer_cm <= 0.0 or melt_diffusivity_cm2_s <= 0.0:
        raise ValueError("boundary layer and melt diffusivity must be > 0")
    v_cm_s = pull_rate_mm_min * 0.1 / 60.0       # mm/min → cm/s
    return v_cm_s * boundary_layer_cm / melt_diffusivity_cm2_s


def effective_segregation_coefficient(k0: float, normalized_velocity: float) -> float:
    """Burton–Prim–Slichter effective coefficient ``k_eff = k₀/[k₀+(1−k₀)·e^(−Δ)]`` (CG-1).

    ``k0`` the equilibrium (Trumbore) coefficient ∈ ``(0, 1]``; ``normalized_velocity`` the
    dimensionless ``Δ = v·δ/D ≥ 0`` (:func:`normalized_growth_velocity`). Returns ``k0`` **exactly**
    at ``Δ=0`` (the well-mixed Scheil seam), rises monotonically toward **1** as ``Δ→∞`` (complete
    solute trapping), and is ``1`` for any ``Δ`` when ``k0=1`` (nothing to segregate). Bounded in
    ``[k0, 1]``. The structural identity ``1/k_eff − 1 = (1/k₀ − 1)·e^(−Δ)`` (the segregation deficit
    decays exponentially in ``Δ``) holds exactly — a regression guard, not a conservation law.
    """
    if not 0.0 < k0 <= 1.0:
        raise ValueError(f"k0 must be in (0, 1], got {k0}")
    if normalized_velocity < 0.0:
        raise ValueError(f"normalized velocity Δ must be ≥ 0, got {normalized_velocity}")
    return k0 / (k0 + (1.0 - k0) * math.exp(-normalized_velocity))


# --------------------------------------------------------------------------- #
# 2. The Scheil profile + its closed-form axial integral (analytic + conservation legs)
# --------------------------------------------------------------------------- #
def scheil_profile(z, N_seed: float, k: float):
    """Scheil axial concentration ``C_s(z) = N_seed·(1−z)^(k−1)`` (cm⁻³), seed-end-parameterized.

    ``z`` (fraction solidified, ``∈ [0, 1)``) scalar or array; ``N_seed = C_s(0)`` the seed-end
    concentration (cm⁻³); ``k`` the segregation coefficient. Returns ``N_seed`` **exactly** at
    ``z=0`` for any ``k`` (the seam), rises monotonically for ``k<1``, is uniform for ``k=1``, and
    diverges as ``z→1`` (the unphysical tail — you never freeze the whole melt).
    """
    z = np.asarray(z, dtype=float)
    if np.any(z < 0.0) or np.any(z >= 1.0):
        raise ValueError("z (fraction solidified) must be in [0, 1)")
    out = N_seed * (1.0 - z) ** (k - 1.0)
    return float(out) if out.ndim == 0 else out


def melt_concentration(N_seed: float, k: float) -> float:
    """Initial melt concentration ``C_0 = N_seed / k`` (cm⁻³) — the seed value un-segregated.

    Also the axial average of ``C_s`` over the whole boule (the conserved solute:
    ``∫₀¹ C_s dz = C_0``). For ``k<1`` it exceeds ``N_seed`` (the melt is richer than the seed end).
    """
    return N_seed / k


def scheil_cumulative(z, N_seed: float, k: float):
    """Axial integral ``∫₀^z C_s dz' = (N_seed/k)·(1 − (1−z)^k)`` (cm⁻³) — the solute solidified by ``z``.

    The closed-form antiderivative of :func:`scheil_profile` and the conservation leg: as ``z→1`` it
    → ``N_seed/k = C_0`` (all the charged solute), the mass-balance identity — and it stays finite
    because the ``z→1`` divergence of ``C_s`` itself is *integrable* for ``k>0``.
    """
    z = np.asarray(z, dtype=float)
    out = (N_seed / k) * (1.0 - (1.0 - z) ** k)
    return float(out) if out.ndim == 0 else out


# --------------------------------------------------------------------------- #
# 3. Resistivity from doping — reusing the cited Masetti μ(N) (the independent bridge)
# --------------------------------------------------------------------------- #
def resistivity(N, dopant: str):
    """Bulk resistivity ``ρ = 1/(q·μ(N)·N)`` (Ω·cm) at doping ``N`` (cm⁻³), with Masetti ``μ(N)``.

    Reuses :func:`chip.junction.mobility` — the cited Masetti transport model, deliberately
    independent of any resistivity-vs-doping chart (the same non-circular cross-check the junction
    ``R_s`` uses). For ``N = 1e17`` boron, ``ρ ≈ 0.2 Ω·cm`` (the textbook value); ``ρ`` decreases
    monotonically with doping. Carries the full-activation scope edge (chemical ≈ active here).

    Note the table asymmetry: :data:`SEGREGATION_K` knows Sb/Fe/Cu (for the segregation/scrubbing
    story) but Masetti ``μ(N)`` only has **B/P/As** — so resistivity is defined for those three.
    ``mobility`` raises a clear ``KeyError`` for the rest; off the G2 path (the substrate is B, and
    the metals are used only for the ``C_s(0)/C_0 = k`` scrubbing identity, which never needs ρ).
    """
    N = np.asarray(N, dtype=float)
    rho = 1.0 / (Q_ELEMENTARY * mobility(N, dopant) * N)
    return float(rho) if rho.ndim == 0 else rho


# --------------------------------------------------------------------------- #
# 4. The boule + its axial slices (the seam the fab-line game consumes)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BouleSlice:
    """One wafer-slice's substrate state read off the boule at axial position ``z`` — plain scalars.

    ``z`` the fraction solidified at this slice; ``N_A`` (cm⁻³) the Scheil substrate doping there;
    ``resistivity_ohm_cm`` the resistivity it implies. The loose-coupling currency a consumer (the
    fab-line game) reads to set a wafer's starting substrate.
    """

    z: float
    dopant: str
    N_A: float
    resistivity_ohm_cm: float


@dataclass(frozen=True)
class Boule:
    """A Czochralski boule: a seed-end-doped single crystal with a Scheil axial dopant profile.

    ``dopant`` the substrate species; ``N_seed`` (cm⁻³) the seed-end (``z=0``) concentration; ``k``
    its segregation coefficient (defaults to the cited Trumbore value for ``dopant``).
    ``length_mm``/``diameter_mm`` are narrative geometry only (they do not enter the physics). The
    axial profile is the Scheil closed form; :meth:`slice` reads ``(N_A, ρ)`` at a fraction ``z``.
    """

    dopant: str = "B"
    N_seed: float = 1.0e17
    k: float | None = None            # None → the cited Trumbore value for ``dopant``
    length_mm: float = 200.0
    diameter_mm: float = 200.0

    def __post_init__(self) -> None:
        if self.k is None:
            object.__setattr__(self, "k", segregation_coefficient(self.dopant))

    @property
    def melt_concentration(self) -> float:
        """The initial melt concentration ``C_0 = N_seed/k`` (cm⁻³) — also the conserved axial average."""
        return melt_concentration(self.N_seed, self.k)

    def axial_doping(self, z):
        """Substrate doping ``N_A(z) = C_s(z)`` (cm⁻³) at fraction solidified ``z`` (scalar or array)."""
        return scheil_profile(z, self.N_seed, self.k)

    def axial_resistivity(self, z):
        """Substrate resistivity ``ρ(z)`` (Ω·cm) at fraction solidified ``z`` (Masetti ``μ(N(z))``)."""
        return resistivity(self.axial_doping(z), self.dopant)

    def slice(self, z: float) -> BouleSlice:
        """Read the wafer-slice substrate state at axial position ``z`` → :class:`BouleSlice`.

        ``slice(0.0).N_A == N_seed`` **exactly** (the seam). The slice is the boule's hand-off to a
        consumer: a wafer at ``z`` starts at this doping and resistivity.
        """
        return BouleSlice(
            z=float(z), dopant=self.dopant,
            N_A=float(self.axial_doping(z)),
            resistivity_ohm_cm=float(self.axial_resistivity(z)),
        )
