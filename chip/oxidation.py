"""Thermal oxidation: the Deal–Grove linear-parabolic model (Chip Phase 2).

The second exact anchor of the chip project, and its **one genuinely-closed-form** step.
Where Phase 1a diffused dopant atoms *into* silicon (the frozen PDE spine in mass mode), oxidation
*consumes* silicon and grows **SiO₂** on top of it — and unlike diffusion, oxide growth has its own
**closed-form** kinetics, so this is a small **chip-local analytic/ODE module, not the frozen PDE
engine** (plan §2/§3: Deal–Grove is its own closed form, project-local until rule-of-three).

The model (Deal & Grove 1965)
-----------------------------
Oxidant (O₂ or H₂O) diffuses through the growing oxide and reacts at the Si/SiO₂ interface. Mass
balance through that two-step series gives the **linear-parabolic** relation for the oxide thickness
``x_ox``::

    x_ox² + A·x_ox = B·(t + τ)

with the exact solution (the analytical anchor)::

    x_ox(t) = (A/2)·(√(1 + 4·B·(t + τ)/A²) − 1)

Two physically-named regimes fall straight out:

  * **Linear / reaction-limited** (thin oxide, ``x_ox ≪ A/2``): ``A + 2·x_ox ≈ A`` so
    ``x_ox ≈ (B/A)·(t + τ)`` — growth is paced by the **interface reaction**, rate ``B/A`` (the
    *linear* rate constant). This is the gate-oxide regime.
  * **Parabolic / diffusion-limited** (thick oxide, ``x_ox ≫ A/2``): ``A + 2·x_ox ≈ 2·x_ox`` so
    ``x_ox ≈ √(B·(t + τ))`` — growth is paced by **oxidant diffusion** through the thickening film,
    rate ``B`` (the *parabolic* rate constant). This is the field/masking-oxide regime.

Equivalently, the differential the closed form integrates (the **ODE** of "analytic/ODE"):

    dx_ox/dt = B / (A + 2·x_ox)          (→ B/A at x→0, → B/2x_ox as x→∞)

``τ = (x_i² + A·x_i)/B`` is the time-shift that carries an **initial** oxide ``x_i`` (a re-oxidation,
or the dry-oxide rapid-initial offset — see the scope edge); for a bare wafer ``x_i = 0 → τ = 0``.
Grows oxide for **wet** (H₂O) and **dry** (O₂) ambients, on **(100)** or **(111)** silicon.

Validation triad (plan §3) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight, on its idealization).** The exact ``x_ox(t)`` satisfies the algebraic
  identity ``x_ox² + A·x_ox − B(t+τ) = 0`` to machine precision (pure algebra), reproduces the
  linear ``(B/A)·t`` (thin) and parabolic ``√(B·t)`` (thick) asymptotes in their regimes, and an
  independent **ODE** integration of ``dx/dt = B/(A+2x)`` recovers it (the analytic↔ODE
  consistency). **Scope edge, named — the thin-dry anomaly (the Massoud regime):** for *dry* O₂
  below ~30 nm the real oxide grows **faster** than Deal–Grove's linear rate predicts (Deal & Grove
  themselves fit a nonzero initial ``x_i ≈ 20 nm``/``τ > 0`` to absorb it; Massoud later added an
  empirical exponential term). v1 is **plain Deal–Grove — it does not model the Massoud
  enhancement** — so the thin-dry regime is named as a known model failure and a benchmark there does
  not wound the exact leg (the same discipline as carburize's constant-D scope edge).

* **Conservation (tight).** Growing oxide **eats silicon**: ``x_Si = 0.44·x_ox`` (the Si→SiO₂
  number-density bookkeeping — ~2.2e22 Si atoms/cm³ of oxide vs ~5.0e22/cm³ of crystal). A free
  mass balance on the **moving boundary**: of every micron of oxide, **0.44 µm sits *below*** the
  original wafer surface (consumed silicon) and **0.56 µm *above*** it (net swelling) — so
  ``si_consumed + oxide_above = x_ox`` exactly.

* **Benchmark (loose).** The rate constants ``B`` (parabolic) and ``B/A`` (linear), **wet vs dry**,
  vs the published Deal–Grove table — pinned to a **cited source at build** (the
  ``[[deal-grove-oxidation-source]]`` memory note; the carburize-diffusivity-source pattern, *not*
  carried from memory). Asserted loosely (the published points carry pressure/orientation/source
  spread): wet oxidizes ~6× faster than dry; both Arrhenius in ``T``; the (100) values land in the
  textbook band (≈ 0.10 µm dry, 0.64 µm wet at 1100 °C / 1 h).

Deferred coupling, named (out of v1)
------------------------------------
Oxidation back-reacts on the Phase-1 dopant profile two ways — **segregation** (dopant
redistributes across the moving Si/SiO₂ interface by its segregation coefficient) and
**oxidation-enhanced diffusion (OED)** (the interface injects silicon self-interstitials that speed
the underlying dopant diffusion). v1 takes only the **forward** direction (Phase 4 consumes a
Phase-1 profile *and* a Phase-2 oxide independently); the OED/segregation back-coupling is a named
deferral — the plain-scalar seam (an oxide thickness out) keeps it slottable later.

Units — Deal–Grove-native µm + hours (the per-module cited-data convention)
--------------------------------------------------------------------------
=====================  ==============  =====================================================
quantity               unit           note
=====================  ==============  =====================================================
oxide thickness x_ox   **µm**          reported in **nm** too (``*1e3``); the cross-module
                                        length currency (Phase 4 converts µm→cm at its boundary)
time t                 **hr**          **minutes** accepted at :func:`grow_oxide` (process unit)
B (parabolic)          **µm²/hr**      cited native — no conversion
B/A (linear)           **µm/hr**       cited native — no conversion
A                      **µm**          ``= B / (B/A)``
temperature            **°C**          → kelvin internally for the Arrhenius
=====================  ==============  =====================================================
This is **not** Phase 1a's CGS-cm — and that is the *same* principle, not a departure: each chip
module computes in **its cited data's native units** so no load-bearing constant is converted on the
way in (Phase 1a kept Fair ``D₀`` native cm²/s → CGS; Deal–Grove ``B/A`` is native **µm/hr** → µm-hr).
The cross-module currency is **µm** for lengths (junction depths and oxide thicknesses both reported
in µm). One unit system **within** this module; native units **per** module.

Validation boundary
-------------------
There is no shared engine here to lean on — this module *is* the closed form, so its tests carry the
whole triad: the algebraic identity + asymptotes + ODE consistency (analytic), the 0.44 silicon
bookkeeping (conservation), and the cited rate-constant table (benchmark). The constants ``C, Ea``
are cited Deal–Grove data, **not** fit to any thickness here — what makes the thickness benchmark a
cross-check, not a tautology.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .diffusion_dopant import K_BOLTZMANN_EV, ABS_ZERO

# --------------------------------------------------------------------------- #
# Unit conversions + the silicon-consumption ratio
# --------------------------------------------------------------------------- #
MIN_PER_HOUR = 60.0
UM_PER_NM = 1.0e-3              # 1 nm = 1e-3 µm  (report thin oxides as x_ox / UM_PER_NM)
SI_SIO2_RATIO = 0.44           # µm of silicon consumed per µm of SiO₂ grown (number-density ratio)

# Orientation factor on the LINEAR rate constant B/A only (the interface reaction is
# orientation-sensitive; B — oxidant diffusion through amorphous oxide — is not). The cited table is
# (111); (B/A)₍₁₁₁₎ = 1.68·(B/A)₍₁₀₀₎, so (100) divides by 1.68.
ORIENTATION_FACTOR: dict[str, float] = {"111": 1.0, "100": 1.0 / 1.68}


# --------------------------------------------------------------------------- #
# 1. The oxidant registry — cited Deal–Grove Arrhenius rate constants (µm, hr, eV)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class OxidationAmbient:
    """Deal–Grove rate-constant Arrhenius parameters for one oxidizing ambient.

    The parabolic rate constant ``B = C_B·exp(−Ea_B/kT)`` (µm²/hr — oxidant diffusion through the
    growing oxide) and the linear rate constant ``B/A = C_lin·exp(−Ea_lin/kT)`` (µm/hr — the
    Si/SiO₂ interface reaction). All native µm-hour-eV (the cited table's own units, kept native).
    ``C_lin`` is the **(111)** pre-exponential; the (100) value follows from :data:`ORIENTATION_FACTOR`.
    """

    name: str
    C_B: float       # µm²/hr  parabolic pre-exponential
    Ea_B: float      # eV      parabolic activation energy
    C_lin: float     # µm/hr   linear pre-exponential, (111) silicon
    Ea_lin: float    # eV      linear activation energy


# Deal & Grove (1965) rate constants, as tabulated in Plummer–Deal–Griffin / Jaeger (the same
# standard lineage Phase 1a's Fair D(T) cites). (111) silicon, wet = H₂O. Pinned to the cited
# source — see the deal-grove-oxidation-source memory note (NOT carried from memory). Note Ea_B(wet)
# = 0.78 eV is the table value (the 0.71 eV that floats in prose summaries is the less-reliable one).
AMBIENTS: dict[str, OxidationAmbient] = {
    "dry": OxidationAmbient("dry", C_B=7.72e2, Ea_B=1.23, C_lin=6.23e6, Ea_lin=2.00),
    "wet": OxidationAmbient("wet", C_B=3.86e2, Ea_B=0.78, C_lin=1.63e8, Ea_lin=2.05),
}


def _arrhenius(C: float, Ea: float, T_celsius: float) -> float:
    """``C·exp(−Ea/kT)`` with ``k`` in eV/K and ``T`` °C → kelvin internally."""
    T_K = T_celsius + ABS_ZERO
    if T_K <= 0.0:
        raise ValueError(f"temperature must be above absolute zero, got {T_celsius} °C")
    return C * math.exp(-Ea / (K_BOLTZMANN_EV * T_K))


@dataclass(frozen=True)
class RateConstants:
    """The Deal–Grove rate constants evaluated at one ``(ambient, T, orientation)``.

    ``B`` (µm²/hr) is the parabolic (diffusion-limited) constant; ``B_over_A`` (µm/hr) the linear
    (reaction-limited) constant; ``A`` (µm, a property) the crossover length ``B/(B/A)``. These are
    the plain numbers the benchmark leg pins against the cited table.
    """

    ambient: str
    orientation: str
    T_celsius: float
    B: float          # µm²/hr  parabolic rate constant
    B_over_A: float   # µm/hr   linear rate constant

    @property
    def A(self) -> float:
        """``A = B / (B/A)`` (µm) — the linear↔parabolic crossover length scale."""
        return self.B / self.B_over_A


def oxide_rate_constants(
    ambient: OxidationAmbient | str, T_celsius: float, orientation: str = "100",
) -> RateConstants:
    """Evaluate the Deal–Grove ``B`` and ``B/A`` for ``ambient`` at ``T`` (°C), ``orientation``.

    ``ambient`` is ``"dry"``/``"wet"`` (or an :class:`OxidationAmbient`); ``orientation`` is
    ``"100"`` (default — the device-relevant face the Phase-4 MOS is built on) or ``"111"`` (the
    cited table's own face, so the benchmark can pin the table exactly). The orientation factor
    scales the **linear** ``B/A`` only.
    """
    amb = AMBIENTS[ambient] if isinstance(ambient, str) else ambient
    if orientation not in ORIENTATION_FACTOR:
        raise ValueError(f"orientation must be one of {sorted(ORIENTATION_FACTOR)}, got {orientation!r}")
    B = _arrhenius(amb.C_B, amb.Ea_B, T_celsius)
    B_over_A = _arrhenius(amb.C_lin, amb.Ea_lin, T_celsius) * ORIENTATION_FACTOR[orientation]
    return RateConstants(amb.name, orientation, T_celsius, B, B_over_A)


# --------------------------------------------------------------------------- #
# 2. The closed form, its two limits, and the ODE (the analytical-limit legs)
# --------------------------------------------------------------------------- #
def tau_offset(x_initial: float, B: float, A: float) -> float:
    """Time-shift ``τ = (x_i² + A·x_i)/B`` (hr) carrying an initial oxide ``x_i`` (µm).

    ``τ`` is what lets the closed form start from a pre-existing oxide (a re-oxidation, or the named
    dry-oxide rapid-initial offset). For a bare wafer ``x_i = 0 → τ = 0``.
    """
    if B <= 0.0:
        raise ValueError(f"B must be positive, got {B}")
    return (x_initial**2 + A * x_initial) / B


def oxide_thickness(t_hours, B: float, A: float, x_initial: float = 0.0):
    """Exact Deal–Grove ``x_ox(t) = (A/2)·(√(1 + 4B(t+τ)/A²) − 1)`` (µm); scalar or array ``t``.

    The analytical anchor — the exact solution of ``x_ox² + A·x_ox = B(t+τ)``. ``t_hours`` may be a
    scalar or a NumPy array (for the vs-time curve). At ``t = 0`` it returns ``x_initial`` exactly
    (the τ machinery recovers the seed).
    """
    t = np.asarray(t_hours, dtype=float)
    if np.any(t < 0.0):
        raise ValueError("t_hours must be ≥ 0")
    tau = tau_offset(x_initial, B, A)
    x = 0.5 * A * (np.sqrt(1.0 + 4.0 * B * (t + tau) / A**2) - 1.0)
    return float(x) if x.ndim == 0 else x


def linear_limit(t_hours, B: float, A: float):
    """Thin-oxide (reaction-limited) asymptote ``x_ox ≈ (B/A)·t`` (µm), bare wafer.

    The ``x_ox ≪ A/2`` limit of the closed form — growth paced by the interface reaction at the
    constant linear rate ``B/A``. The clean asymptote (``x_i = 0``) the demo annotates; the closed
    form handles the general re-oxidation case.
    """
    return (B / A) * np.asarray(t_hours, dtype=float)


def parabolic_limit(t_hours, B: float):
    """Thick-oxide (diffusion-limited) asymptote ``x_ox ≈ √(B·t)`` (µm), bare wafer.

    The ``x_ox ≫ A/2`` limit — growth paced by oxidant diffusion through the film at the parabolic
    rate ``B``. The clean asymptote (``x_i = 0``) the demo annotates.
    """
    return np.sqrt(B * np.asarray(t_hours, dtype=float))


def growth_rate(x_ox, B: float, A: float):
    """Deal–Grove growth rate ``dx_ox/dt = B/(A + 2·x_ox)`` (µm/hr) — the ODE the closed form solves.

    The differential origin of the linear-parabolic law: ``→ B/A`` (linear) as ``x_ox → 0``, and
    ``→ B/(2·x_ox)`` (parabolic) as ``x_ox → ∞``. Integrating it reproduces :func:`oxide_thickness`
    (the analytic↔ODE consistency leg).
    """
    return B / (A + 2.0 * np.asarray(x_ox, dtype=float))


def integrate_growth_ode(
    t_hours: float, B: float, A: float, x_initial: float = 0.0, n_eval: int = 200,
):
    """Numerically integrate ``dx/dt = B/(A+2x)`` from 0 to ``t_hours`` → ``(t, x)`` arrays (µm).

    The independent ODE cross-check of the closed form: a stiff-free initial-value problem solved by
    :func:`scipy.integrate.solve_ivp` (tight ``rtol/atol``), which must reproduce
    :func:`oxide_thickness` to ~1e-6 (not machine precision — it is a numerical integration). Honors
    the plan's "analytic/ODE solve" framing concretely.
    """
    from scipy.integrate import solve_ivp

    t_eval = np.linspace(0.0, t_hours, n_eval)
    sol = solve_ivp(
        lambda t, y: growth_rate(y[0], B, A), (0.0, t_hours), [x_initial],
        t_eval=t_eval, rtol=1e-9, atol=1e-12,
    )
    return sol.t, sol.y[0]


# --------------------------------------------------------------------------- #
# 3. Silicon consumption — the moving-boundary mass balance (the conservation leg)
# --------------------------------------------------------------------------- #
def silicon_consumed(x_ox):
    """Silicon thickness consumed by growing ``x_ox`` of oxide: ``0.44·x_ox`` (µm); scalar or array.

    The Si→SiO₂ number-density bookkeeping (:data:`SI_SIO2_RATIO`): the Si/SiO₂ interface advances
    into the wafer by ``0.44·x_ox`` while the oxide top rises ``0.56·x_ox`` above the original
    surface, the two summing to ``x_ox``. The free mass-balance check on the moving boundary.
    """
    x = SI_SIO2_RATIO * np.asarray(x_ox, dtype=float)
    return float(x) if x.ndim == 0 else x


# --------------------------------------------------------------------------- #
# 4. Regime classification (the teaching annotation) + the bundled growth result
# --------------------------------------------------------------------------- #
def regime_at(x_ox: float, A: float) -> str:
    """Which Deal–Grove regime dominates at thickness ``x_ox`` — ``"linear"``/``"transition"``/``"parabolic"``.

    The crossover scale is ``x_ox ≈ A/2`` (where ``A`` and ``2·x_ox`` are comparable in the ODE
    denominator). ``2·x_ox/A < 0.5`` → linear (reaction-limited); ``> 2`` → parabolic
    (diffusion-limited); between → transition. The annotation the vs-time demo uses to mark where the
    curve bends from slope-1 to slope-½.
    """
    ratio = 2.0 * x_ox / A
    if ratio < 0.5:
        return "linear"
    if ratio > 2.0:
        return "parabolic"
    return "transition"


@dataclass(frozen=True)
class OxideGrowth:
    """The result of one oxidation step: the grown oxide and its moving-boundary bookkeeping.

    ``t_ox`` is the oxide thickness in **µm** (``t_ox_nm`` in nm) — the cross-module length currency
    (Phase 4's ``C_ox = ε_ox/t_ox`` converts µm→cm at its own boundary). ``si_consumed`` (µm) is the
    silicon eaten (``0.44·t_ox``) and ``oxide_above_original_surface`` (µm) the net swelling
    (``0.56·t_ox``); the two sum to ``t_ox``. ``rates`` are the :class:`RateConstants`; ``regime``
    which Deal–Grove regime dominates at this thickness; ``ambient``/``T_celsius``/``t_minutes``/
    ``orientation``/``x_initial`` echo the recipe. Plain scalars — the loose-coupling currency.
    """

    ambient: str
    orientation: str
    T_celsius: float
    t_minutes: float
    x_initial: float
    t_ox: float          # µm
    rates: RateConstants

    @property
    def t_ox_nm(self) -> float:
        """Oxide thickness in nanometres (the natural unit for thin gate oxides)."""
        return self.t_ox / UM_PER_NM

    @property
    def si_consumed(self) -> float:
        """Silicon consumed ``0.44·t_ox`` (µm) — the depth the Si/SiO₂ interface dropped."""
        return silicon_consumed(self.t_ox)

    @property
    def oxide_above_original_surface(self) -> float:
        """Net swelling ``0.56·t_ox`` (µm) — oxide grown *above* the original wafer surface."""
        return (1.0 - SI_SIO2_RATIO) * self.t_ox

    @property
    def regime(self) -> str:
        """The dominant Deal–Grove regime at the final thickness (:func:`regime_at`)."""
        return regime_at(self.t_ox, self.rates.A)


def grow_oxide(
    ambient: OxidationAmbient | str,
    T_celsius: float,
    t_minutes: float,
    orientation: str = "100",
    x_initial: float = 0.0,
) -> OxideGrowth:
    """Grow oxide for ``t_minutes`` at ``T_celsius`` in ``ambient`` → :class:`OxideGrowth`.

    The high-level recipe entry: takes the **process units** (minutes, °C, dry/wet, (100)/(111)) and
    an optional initial oxide ``x_initial`` (µm, for a re-oxidation), and returns the thickness +
    bookkeeping. Internally evaluates the cited rate constants and the exact closed form. *Recipe in,
    oxide out* — the Phase-2 banked step.
    """
    rates = oxide_rate_constants(ambient, T_celsius, orientation)
    t_hours = t_minutes / MIN_PER_HOUR
    x = oxide_thickness(t_hours, rates.B, rates.A, x_initial=x_initial)
    return OxideGrowth(
        ambient=rates.ambient, orientation=orientation, T_celsius=T_celsius,
        t_minutes=t_minutes, x_initial=x_initial, t_ox=float(x), rates=rates,
    )
