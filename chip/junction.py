"""The junction reading: a dopant profile → junction depth ``x_j`` + sheet resistance ``R_s`` (Chip Phase 1a).

Where :mod:`diffusion_dopant` produces the profile ``N(x)``, this module reads the **device
parameters** off it — the chip analogue of Steel's microstructure→hardness map. Two outputs,
both plain numbers a learner recognizes:

  * **Junction depth** ``x_j`` — the depth where the diffused dopant profile crosses the wafer's
    **opposite-type background doping** ``N_B``. Above ``x_j`` the diffused dopant dominates (one
    type); below it the background dominates (the other) — that sign change *is* the pn junction.
  * **Sheet resistance** ``R_s`` — the lateral resistance of the diffused layer, per square:

        R_s = 1 / ∫₀^{x_j} q · μ(N(x)) · N(x) dx        (Ω/sq)

    a **conductance integral** of the profile, with a concentration-dependent carrier mobility
    ``μ(N)``. Because the heavily-doped layer has ``N ≫ N_B`` over almost all of ``[0, x_j]``, the
    majority-carrier density is ``≈ N(x)`` (the background-subtraction is negligible until the very
    edge), so the textbook integrand ``q·μ·N`` is used.

The benchmark, and why it is a genuine cross-check (non-circularity)
-------------------------------------------------------------------
``x_j`` and ``R_s`` are benchmarked against **Irvin's** (1962, BSTJ 41:387) published
``R_s·x_j`` curves. Two independent cited facts make this a cross-check, not a refit:

  * the diffusivity ``D₀, Ea`` (Fair) is cited *diffusion* data, **not** fit to junction depth
    (:mod:`diffusion_dopant`); and
  * the mobility ``μ(N)`` here is the **Masetti** (1983, IEEE TED 30:764) model — a cited
    *transport* model, deliberately **independent** of Irvin's own resistivity curves, so the two
    sides of the ``R_s`` comparison stay independent.

Irvin's curves are **graphical**, so the benchmark *cites* them (compares ``R_s``/``x_j`` to the
published chart's band and trends); it does not call them. ``R_s`` is *computed* from the profile
+ Masetti ``μ(N)``; the comparison to Irvin is then honest.

Mobility model — Masetti–Severi–Solmi (1983), silicon, 300 K
------------------------------------------------------------
A Caughey–Thomas form with Masetti's high-doping correction (the ``−μ_1`` dip and the ``exp(−P_c/N)``
low-end floor):

    μ(N) = μ_min1·exp(−P_c/N) + (μ_max − μ_min2)/(1 + (N/C_r)^α) − μ_1/(1 + (C_s/N)^β)

with ``N`` the total local ionized dopant (≈ the profile value in the single-dopant layer).
Per-dopant parameters (cm²/V·s, cm⁻³) are the canonical Masetti Table-I values, verified against
two independent reproductions (IUE-Vienna for P; allpix²/CERN for B & P). **B and P** (the
pn-junction-demo pair) and **As** are provided.

Named scope edge (the active-vs-chemical ceiling)
-------------------------------------------------
Both Masetti and Irvin assume **full dopant activation at 300 K**. At/near the predep
**solid-solubility** surface, dopants cluster and the **electrically active** concentration falls
below the **chemical** concentration the diffusion profile tracks (especially As) — so the
high-``N_s`` end is the honest ceiling. v1 takes ``N(x)`` as fully active (the textbook reduction)
and flags active-vs-chemical as the limit; it is the same ceiling :mod:`diffusion_dopant` names for
the constant-D erfc at the solubility limit.

Units — semiconductor-conventional CGS (as :mod:`diffusion_dopant`)
------------------------------------------------------------------
``x`` in **cm** (reported µm), ``N`` in **cm⁻³**, ``μ`` in **cm²/V·s**, ``q`` in **C** → ``R_s`` in
**Ω/sq** directly (``[C·cm⁻³·cm²V⁻¹s⁻¹·cm] = S/□``, inverted). One unit system throughout.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .diffusion_dopant import Dopant, DopantProfile, DOPANTS, CM_PER_UM

# Elementary charge (C) — the only new physical constant here.
Q_ELEMENTARY = 1.602176634e-19


# --------------------------------------------------------------------------- #
# 1. Masetti (1983) carrier mobility μ(N) — the R_s integrand (cited, independent of Irvin)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MasettiParams:
    """Masetti–Severi–Solmi (1983) mobility parameters for one dopant (cm²/V·s, cm⁻³).

    ``mu_max`` is the lattice (low-doping) mobility; ``mu_min1``/``mu_min2`` the high-doping floors
    of the exponential and Caughey–Thomas terms; ``mu_1`` the ultra-high-doping dip; ``Pc``/``Cr``/
    ``Cs`` the reference concentrations; ``alpha``/``beta`` the exponents. (For donors ``Pc=0`` so
    the exponential term reduces to the constant ``mu_min1``.)
    """

    mu_max: float
    mu_min1: float
    mu_min2: float
    mu_1: float
    Pc: float
    Cr: float
    Cs: float
    alpha: float
    beta: float


# Canonical Masetti Table-I silicon values (300 K), verified vs IUE-Vienna (P) and allpix²/CERN
# (B, P). Keyed by dopant name; donors (P/As) carry their electron set, the acceptor (B) its holes.
MASETTI: dict[str, MasettiParams] = {
    "P":  MasettiParams(mu_max=1414.0, mu_min1=68.5, mu_min2=68.5, mu_1=56.1,
                        Pc=0.0,       Cr=9.20e16, Cs=3.41e20, alpha=0.711, beta=1.98),
    "As": MasettiParams(mu_max=1417.0, mu_min1=52.2, mu_min2=52.2, mu_1=43.4,
                        Pc=0.0,       Cr=9.68e16, Cs=3.43e20, alpha=0.680, beta=2.00),
    "B":  MasettiParams(mu_max=470.5, mu_min1=44.9, mu_min2=0.0,  mu_1=29.0,
                        Pc=9.23e16,   Cr=2.23e17, Cs=6.10e20, alpha=0.719, beta=2.00),
}


def mobility(N, dopant: Dopant | str) -> np.ndarray | float:
    """Masetti carrier mobility ``μ(N)`` (cm²/V·s) at local dopant concentration ``N`` (cm⁻³).

    ``N`` may be a scalar or an array. Picks the per-dopant parameter set (``B``/``P``/``As``);
    the value is the majority-carrier mobility (holes for B, electrons for P/As). Well-behaved at
    ``N→0`` (→ ``mu_max``, the lattice mobility) and decreasing through the doping range.
    """
    name = dopant if isinstance(dopant, str) else dopant.name
    if name not in MASETTI:
        raise KeyError(f"no Masetti mobility parameters for dopant {name!r} "
                       f"(have {sorted(MASETTI)})")
    p = MASETTI[name]
    N = np.asarray(N, dtype=float)
    Nc = np.maximum(N, 1.0)            # floor away from 0 for the 1/N terms (deep tail)
    mu = (
        p.mu_min1 * np.exp(-p.Pc / Nc)
        + (p.mu_max - p.mu_min2) / (1.0 + (Nc / p.Cr) ** p.alpha)
        - p.mu_1 / (1.0 + (p.Cs / Nc) ** p.beta)
    )
    return float(mu) if mu.ndim == 0 else mu


# --------------------------------------------------------------------------- #
# 2. Junction depth — where the profile crosses the background doping
# --------------------------------------------------------------------------- #
def junction_depth(x: np.ndarray, N: np.ndarray, N_background: float) -> float:
    """Junction depth ``x_j`` (cm): the first depth where ``N(x)`` falls through ``N_background``.

    The profile decreases from the surface; the junction is the crossing ``N(x_j) = N_B``.
    Interpolated **in log N** (the profile is exponential-tailed there, so log-linear is the
    faithful interpolant — this is the deep-tail region the demo's x_j lives in, ``z = x/2√(Dt) ≈ 3``).
    Returns ``nan`` if the surface is already below ``N_B`` or the profile never crosses it within
    the domain (the junction is not resolved — deepen the domain).
    """
    x = np.asarray(x, dtype=float)
    N = np.asarray(N, dtype=float)
    if N[0] <= N_background:
        return float("nan")                          # surface below background — no junction
    below = N < N_background
    if not below.any():
        return float("nan")                          # never crosses in the domain
    i = int(np.argmax(below))                         # first cell below N_B; cross in [i-1, i]
    n0, n1 = N[i - 1], N[i]
    if n0 <= 0.0 or n1 <= 0.0:
        return float(np.interp(N_background, [n1, n0], [x[i], x[i - 1]]))  # linear fallback
    # log-linear: x_j = x0 + (x1−x0)·(lnN_B − ln n0)/(ln n1 − ln n0)
    f = (math.log(N_background) - math.log(n0)) / (math.log(n1) - math.log(n0))
    return float(x[i - 1] + f * (x[i] - x[i - 1]))


# --------------------------------------------------------------------------- #
# 3. Sheet resistance — the conductance integral over the diffused layer
# --------------------------------------------------------------------------- #
def sheet_resistance(
    x: np.ndarray, N: np.ndarray, dopant: Dopant | str,
    x_j: float, N_background: float = 0.0,
) -> float:
    """Sheet resistance ``R_s = 1/∫₀^{x_j} q·μ(N)·N dx`` (**Ω/sq**) of the diffused layer.

    Integrates the conductivity ``σ(x) = q·μ(N(x))·N(x)`` (Masetti ``μ``) from the surface to the
    junction ``x_j`` by the trapezoid rule on the profile's own grid (with ``x_j`` appended as the
    upper limit). ``N_background`` is subtracted from the carrier density (net majority carrier
    ``N − N_B``, clipped ≥ 0); since ``N ≫ N_B`` over the layer this is a negligible correction
    except at the very edge. Returns ``nan`` for a non-finite/zero ``x_j``.
    """
    if not math.isfinite(x_j) or x_j <= 0.0:
        return float("nan")
    x = np.asarray(x, dtype=float)
    N = np.asarray(N, dtype=float)
    mask = x < x_j
    if mask.sum() < 1:
        return float("nan")
    xx = np.concatenate([x[mask], [x_j]])
    NN = np.concatenate([N[mask], [N_background]])        # carrier density → N_B at the junction
    carriers = np.clip(NN - N_background, 0.0, None)      # net majority carrier
    sigma = Q_ELEMENTARY * mobility(NN, dopant) * carriers
    conductance = float(np.trapezoid(sigma, xx))         # ∫σ dx  → S/sq
    if conductance <= 0.0:
        return float("nan")
    return 1.0 / conductance


# --------------------------------------------------------------------------- #
# 4. The bundled junction reading (the seam the demo + benchmark consume)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Junction:
    """A pn junction read off a diffused profile: depth, sheet resistance, and the Irvin product.

    ``x_j`` (cm; ``x_j_um`` in µm) is the junction depth into background ``N_background``; ``R_s``
    (Ω/sq) the diffused-layer sheet resistance; ``N_surface`` the (chemical) surface concentration.
    ``rho_avg = R_s·x_j`` (Ω·cm) is the layer's average resistivity — the quantity **Irvin's
    curves plot** vs surface concentration, so it is the natural cross-check handle. ``dopant`` is
    the species name.
    """

    dopant: str
    x_j: float
    R_s: float
    N_surface: float
    N_background: float

    @property
    def x_j_um(self) -> float:
        """Junction depth in micrometres (the reported unit)."""
        return self.x_j / CM_PER_UM

    @property
    def rho_avg(self) -> float:
        """Average layer resistivity ``R_s·x_j`` (Ω·cm) — Irvin's plotted quantity (``nan`` if unresolved)."""
        return self.R_s * self.x_j


def analyze_junction(
    profile: DopantProfile, dopant: Dopant | str, N_background: float,
) -> Junction:
    """Read the junction (``x_j``, ``R_s``) off a diffused ``profile`` against ``N_background``.

    Convenience wiring of :func:`junction_depth` + :func:`sheet_resistance` for the demo and the
    benchmark. ``dopant`` selects the Masetti mobility set; ``N_background`` (cm⁻³) is the wafer's
    opposite-type doping.
    """
    name = dopant if isinstance(dopant, str) else dopant.name
    xj = junction_depth(profile.x, profile.N, N_background)
    Rs = sheet_resistance(profile.x, profile.N, name, xj, N_background)
    return Junction(
        dopant=name, x_j=xj, R_s=Rs,
        N_surface=float(profile.N[0]), N_background=float(N_background),
    )
