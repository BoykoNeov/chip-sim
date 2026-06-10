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
  consistency). **Scope edge, promoted — the thin-dry anomaly (the Massoud regime):** for *dry* O₂
  below ~30 nm the real oxide grows **faster** than Deal–Grove's linear rate predicts (Deal & Grove
  themselves fit a nonzero initial ``x_i ≈ 20 nm``/``τ > 0`` to absorb it). v1 named this as the
  known model failure; **v1.1 builds it** — the cited **Massoud** correction (§5 below) is the
  separate opt-in entry :func:`grow_oxide_massoud`, while the plain-Deal–Grove path (and its exact
  anchor) stays bit-for-bit untouched: :func:`grow_oxide` never applies the enhancement (the same
  discipline as the exoplanet knobs' defaults-recover-v1).

The Massoud thin-dry correction (v1.1, §5)
------------------------------------------
The cited model is Massoud's **time-decay formulation** (Massoud & Plummer, *J. Appl. Phys.*
**62**\\ (8):3416–3423, 1987; the thin-regime data is Massoud, Plummer & Irene, *J. Electrochem.
Soc.* **132**\\ (11):2685–2693, 1985) — the Deal–Grove rate with two exponentially-decaying
enhancement terms in the *numerator*::

    dx_ox/dt = (B + K₁·e^{−t/τ₁} + K₂·e^{−t/τ₂}) / (A + 2·x_ox)

which (unlike the sibling thickness-decay form ``+C₁e^{−x/L₁}+C₂e^{−x/L₂}``, L₁≈1 nm/L₂≈7 nm,
of the 1985 paper) **integrates in closed form** — the quadratic identity gains two saturating
dose terms ``M_i = K_i·τ_i``::

    x_ox² + A·x_ox = B·t + M₁(1−e^{−t/τ₁}) + M₂(1−e^{−t/τ₂}) + (x_i² + A·x_i)

so the module keeps its exact-anchor discipline (closed form + independent ODE cross-check).
All six parameters are Arrhenius; the constants are pinned to the compiled tables in Hollauer,
*Modeling of Thermal Oxidation and Stress Effects* (TU Wien dissertation, 2007), §2.7 Tables
2.3/2.4 — **dry O₂ only, 800–1000 °C, (100)/(111)/(110)** (the cited fit range; outside it this
module *refuses* rather than extrapolates). Two durable source calls:

* **The coherent-set rule.** Massoud's ``K_i``/``τ_i`` were fit together with **his own refit
  ``B``/``B/A``** (*JECS* **132**\\ (7):1746–1753, 1985 — Table 2.3, different numbers from the
  Deal–Grove-1965 table above), so :func:`grow_oxide_massoud` uses the full Massoud-native set —
  the enhancement is **not** spliced onto the 1965 constants (mixing the two fits would be
  internally incoherent). Consequence: in the *thick* regime Massoud and plain-1965-Deal–Grove
  agree only approximately (two independent ``B`` fits), and that is honest, not a bug.
* **The τ sign-typo finding.** Hollauer's eqs (2.39)–(2.40) print ``τ_i = τ_i⁰·exp(−E_τ/kT)``,
  but with the table's ``τ⁰ ~ 1e-7 min`` that yields femtosecond decay times; the **positive**
  exponent (``exp(+E_τ/kT)`` — a time constant is an inverse rate, so its Arrhenius is inverted)
  gives τ₁ ≈ 1.2 min / τ₂ ≈ 7.5 min at 1000 °C and reproduces the dissertation's own Fig. 2.19
  (~25 nm at 1000 °C/20 min). The code uses the positive sign; the typo is named here so the
  pinned table is read consistently.

Scope edge that remains: the time-decay form ties the burst to **time since oxidation onset**,
not film thickness, so ``x_initial`` is algebraically supported but physically meaningful only
for thin/native seeds (a thick re-oxidation seed would wrongly re-apply the burst — use the
plain Deal–Grove path there). Wet oxidation has no thin-regime anomaly (no wet Massoud terms).

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

**v1.1 sharpening of the rule — native units per *cited dataset*.** The Massoud tables are
tabulated in **nm + minutes** (``K_i`` nm²/min, ``τ_i`` min, Massoud's ``B`` nm²/min), so the §5
Massoud block computes in nm-min — no load-bearing constant converted on the way in — and converts
**only at its boundary**: thickness arguments/results stay **µm** (the currency), process time stays
**minutes** (the same unit :func:`grow_oxide` already accepts). Display conversions of *results*
(nm ↔ µm, µm/hr for the bundled :class:`RateConstants`) are not load-bearing.

Validation boundary
-------------------
There is no shared engine here to lean on — this module *is* the closed form, so its tests carry the
whole triad: the algebraic identity + asymptotes + ODE consistency (analytic), the 0.44 silicon
bookkeeping (conservation), and the cited rate-constant table (benchmark). **A precise note on the
benchmark's strength** (the validated-vs-calibrated discipline): what carries this leg is **citation
fidelity** — the constants pinned to the published Deal–Grove table (*not* a tautology: they could be
miscited) — plus the independent tight algebraic-identity leg. The thickness comparison is a
**consistency check, not an independent cross-check**: unlike carburize's ``D`` (from *tracer-diffusion*,
a different measurement domain than the case depth it predicts), Deal–Grove's ``B``/``B/A`` were
**originally fit to oxide-thickness-vs-time data** (the 1965 paper), so computing thickness from them
and comparing to published thickness is closer to model-vs-itself. Hence thickness is asserted
*loosely* and the constants *tightly* — the honest split.
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
    ``orientation``/``x_initial`` echo the recipe. ``model`` says which growth law produced it —
    ``"deal-grove"`` (default) or ``"massoud"`` (the §5 thin-dry correction). Plain scalars — the
    loose-coupling currency.
    """

    ambient: str
    orientation: str
    T_celsius: float
    t_minutes: float
    x_initial: float
    t_ox: float          # µm
    rates: RateConstants
    model: str = "deal-grove"

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


# --------------------------------------------------------------------------- #
# 5. The Massoud thin-dry correction (v1.1) — cited time-decay enhancement
#    Native units of THIS block: nm + minutes (the cited tables' own units).
#    Boundary: thicknesses in/out stay µm (the currency), time stays minutes.
# --------------------------------------------------------------------------- #
NM_PER_UM = 1.0e3              # boundary conversion µm → nm for the Massoud block
# Reporting-only conversions for the bundled RateConstants (NOT load-bearing):
_NM2_MIN_TO_UM2_HR = 1.0e-6 * 60.0    # nm²/min → µm²/hr
_NM_MIN_TO_UM_HR = 1.0e-3 * 60.0      # nm/min → µm/hr

# The cited fit range (Hollauer Table 2.4): dry O₂, 800–1000 °C. Outside it the model REFUSES
# (ValueError) rather than extrapolates — the two-piece Massoud B/(B/A) Arrhenius (Table 2.3
# splits at 1000 °C) makes extrapolation actively wrong, not merely unvalidated.
MASSOUD_T_RANGE_C = (800.0, 1000.0)


@dataclass(frozen=True)
class MassoudParams:
    """The cited Massoud Arrhenius parameters for one crystal orientation (dry O₂, 800–1000 °C).

    ``C_B``/``Ea_B`` and ``C_lin``/``Ea_lin`` are **Massoud's own refit** ``B`` and ``B/A``
    (*JECS* 132(7):1746, 1985 — Hollauer Table 2.3, T < 1000 °C column; deliberately distinct
    from the Deal–Grove-1965 :data:`AMBIENTS` constants, the coherent-set rule). ``K1_0``/
    ``Ea_K1`` … ``tau2_0``/``Ea_tau2`` are the two enhancement terms (Massoud & Plummer 1987 —
    Hollauer Table 2.4). Native nm-min-eV throughout: ``C_B``/``K_i⁰`` nm²/min, ``C_lin``
    nm/min, ``τ_i⁰`` min. ``K_i = K_i⁰·exp(−Ea/kT)``; ``τ_i = τ_i⁰·exp(+Ea/kT)`` (the POSITIVE
    exponent — see the module-docstring sign-typo finding).
    """

    orientation: str
    C_B: float       # nm²/min   Massoud parabolic pre-exponential
    Ea_B: float      # eV
    C_lin: float     # nm/min    Massoud linear pre-exponential
    Ea_lin: float    # eV
    K1_0: float      # nm²/min   fast enhancement term (the first ~5 nm / L₁≈1 nm sibling)
    Ea_K1: float     # eV
    K2_0: float      # nm²/min   slow enhancement term (the ~25 nm / L₂≈7 nm sibling)
    Ea_K2: float     # eV
    tau1_0: float    # min       fast decay-time pre-exponential (T→∞ limit)
    Ea_tau1: float   # eV        positive-exponent Arrhenius
    tau2_0: float    # min       slow decay-time pre-exponential
    Ea_tau2: float   # eV        positive-exponent Arrhenius


# Hollauer (TU Wien diss., 2007) §2.7: Table 2.3 (T < 1000 °C columns) + Table 2.4, dry O₂,
# 800–1000 °C, per orientation — pinned at build from the dissertation PDF (massoud-thin-oxide
# source pin; the deal-grove-oxidation-source pattern, NOT carried from memory). Note Table 2.4's
# 8th row label "τ₁⁰" is the dissertation's second typo — it is τ₂⁰ (the values pair with E_τ2).
MASSOUD_DRY: dict[str, MassoudParams] = {
    "100": MassoudParams("100", C_B=1.70e11, Ea_B=2.22, C_lin=7.35e6, Ea_lin=1.76,
                         K1_0=2.49e11, Ea_K1=2.18, K2_0=3.72e11, Ea_K2=2.28,
                         tau1_0=4.14e-6, Ea_tau1=1.38, tau2_0=2.71e-7, Ea_tau2=1.88),
    "111": MassoudParams("111", C_B=1.34e9, Ea_B=1.71, C_lin=1.32e7, Ea_lin=1.74,
                         K1_0=2.70e9, Ea_K1=1.74, K2_0=1.33e9, Ea_K2=1.76,
                         tau1_0=1.72e-6, Ea_tau1=1.45, tau2_0=1.56e-7, Ea_tau2=1.90),
    "110": MassoudParams("110", C_B=3.73e8, Ea_B=1.63, C_lin=4.73e8, Ea_lin=2.10,
                         K1_0=4.07e8, Ea_K1=1.54, K2_0=1.20e8, Ea_K2=1.56,
                         tau1_0=5.38e-9, Ea_tau1=2.02, tau2_0=1.63e-8, Ea_tau2=2.12),
}


@dataclass(frozen=True)
class MassoudRates:
    """The Massoud model evaluated at one ``(T, orientation)`` — dry O₂, nm-min native.

    ``B`` (nm²/min) / ``B_over_A`` (nm/min) are Massoud's refit Deal–Grove constants; ``K1``/
    ``K2`` (nm²/min) the enhancement amplitudes and ``tau1``/``tau2`` (min) their decay times.
    ``M1``/``M2`` (nm²) are the saturating extra "doses" ``K_i·τ_i`` the closed form integrates
    to — the whole thin-regime burst is worth a finite ``M₁+M₂`` of extra ``x²+Ax``, after which
    growth is pure linear-parabolic again (the ~25 nm ceiling of the anomaly, in time form).
    """

    orientation: str
    T_celsius: float
    B: float          # nm²/min
    B_over_A: float   # nm/min
    K1: float         # nm²/min
    K2: float         # nm²/min
    tau1: float       # min
    tau2: float       # min

    @property
    def A(self) -> float:
        """``A = B/(B/A)`` (nm) — the crossover length of the underlying linear-parabolic law."""
        return self.B / self.B_over_A

    @property
    def M1(self) -> float:
        """``M₁ = K₁·τ₁`` (nm²) — the fast term's total extra quadratic dose."""
        return self.K1 * self.tau1

    @property
    def M2(self) -> float:
        """``M₂ = K₂·τ₂`` (nm²) — the slow term's total extra quadratic dose."""
        return self.K2 * self.tau2


def massoud_rate_constants(T_celsius: float, orientation: str = "100") -> MassoudRates:
    """Evaluate the cited Massoud model at ``T`` (°C, **800–1000 only**) and ``orientation``.

    Dry O₂ only (the anomaly is dry-specific; wet has no Massoud terms). Raises ``ValueError``
    outside the cited 800–1000 °C fit range (refuse-don't-extrapolate — the Massoud ``B``/``B/A``
    Arrhenius is the T<1000 °C piece of a two-piece fit) and for unknown orientations
    ((100)/(111)/(110) are cited). ``K_i`` use ``exp(−Ea/kT)``; ``τ_i`` use ``exp(+Ea/kT)``
    (the sign-typo finding — the positive sign reproduces Hollauer's own Fig. 2.19).
    """
    if orientation not in MASSOUD_DRY:
        raise ValueError(f"orientation must be one of {sorted(MASSOUD_DRY)}, got {orientation!r}")
    lo, hi = MASSOUD_T_RANGE_C
    if not (lo <= T_celsius <= hi):
        raise ValueError(
            f"the cited Massoud fit covers {lo:.0f}–{hi:.0f} °C (dry O₂); got {T_celsius} °C — "
            "refusing to extrapolate (use plain grow_oxide outside the thin-dry regime)")
    p = MASSOUD_DRY[orientation]
    T_K = T_celsius + ABS_ZERO
    return MassoudRates(
        orientation=orientation, T_celsius=T_celsius,
        B=_arrhenius(p.C_B, p.Ea_B, T_celsius),
        B_over_A=_arrhenius(p.C_lin, p.Ea_lin, T_celsius),
        K1=_arrhenius(p.K1_0, p.Ea_K1, T_celsius),
        K2=_arrhenius(p.K2_0, p.Ea_K2, T_celsius),
        tau1=p.tau1_0 * math.exp(p.Ea_tau1 / (K_BOLTZMANN_EV * T_K)),
        tau2=p.tau2_0 * math.exp(p.Ea_tau2 / (K_BOLTZMANN_EV * T_K)),
    )


def oxide_thickness_massoud(t_minutes, rates: MassoudRates, x_initial: float = 0.0):
    """Exact Massoud thickness ``x_ox(t)`` (µm) — the closed form of the time-decay model.

    Solves the integrated quadratic identity (the v1.1 analytical anchor)::

        x² + A·x = B·t + M₁(1−e^{−t/τ₁}) + M₂(1−e^{−t/τ₂}) + (x_i² + A·x_i)

    for ``x`` (all algebra in the cited nm-min units; ``t_minutes`` scalar or array, ``x_initial``
    µm at the boundary, result µm). At ``t = 0`` it returns ``x_initial`` exactly; with
    ``K₁ = K₂ = 0`` it *is* the plain Deal–Grove closed form (the degenerate-recovery seam the
    tests pin). ``x_initial`` is physically meaningful for thin/native seeds only (module
    docstring scope edge).
    """
    t = np.asarray(t_minutes, dtype=float)
    if np.any(t < 0.0):
        raise ValueError("t_minutes must be ≥ 0")
    A = rates.A
    xi_nm = x_initial * NM_PER_UM
    rhs = (rates.B * t
           + rates.M1 * -np.expm1(-t / rates.tau1)
           + rates.M2 * -np.expm1(-t / rates.tau2)
           + xi_nm**2 + A * xi_nm)
    x_nm = 0.5 * (np.sqrt(A**2 + 4.0 * rhs) - A)
    x = x_nm / NM_PER_UM
    return float(x) if x.ndim == 0 else x


def massoud_growth_rate(x_ox, t_minutes, rates: MassoudRates):
    """Massoud growth rate ``dx/dt = (B + K₁e^{−t/τ₁} + K₂e^{−t/τ₂})/(A + 2x)`` (**nm/min**).

    The ODE of the v1.1 closed form — explicitly **time**-dependent (the named contrast with the
    autonomous Deal–Grove :func:`growth_rate`): the enhancement is a transient tied to the
    oxidation onset, decaying on ``τ₁``/``τ₂`` onto the plain linear-parabolic rate. ``x_ox`` in
    µm (the currency); the rate is returned in the block's native nm/min.
    """
    x_nm = np.asarray(x_ox, dtype=float) * NM_PER_UM
    t = np.asarray(t_minutes, dtype=float)
    numer = rates.B + rates.K1 * np.exp(-t / rates.tau1) + rates.K2 * np.exp(-t / rates.tau2)
    return numer / (rates.A + 2.0 * x_nm)


def integrate_massoud_ode(
    t_minutes: float, rates: MassoudRates, x_initial: float = 0.0, n_eval: int = 200,
):
    """Numerically integrate the Massoud ODE from 0 to ``t_minutes`` → ``(t_min, x_µm)`` arrays.

    The independent cross-check of :func:`oxide_thickness_massoud` (the same analytic↔ODE leg the
    plain model carries via :func:`integrate_growth_ode`): ``solve_ivp`` at tight tolerance must
    reproduce the closed form to ~1e-6.
    """
    from scipy.integrate import solve_ivp

    t_eval = np.linspace(0.0, t_minutes, n_eval)
    sol = solve_ivp(
        lambda t, y: massoud_growth_rate(y[0], t, rates) / NM_PER_UM,
        (0.0, t_minutes), [x_initial], t_eval=t_eval, rtol=1e-9, atol=1e-12,
    )
    return sol.t, sol.y[0]


def grow_oxide_massoud(
    T_celsius: float, t_minutes: float, orientation: str = "100", x_initial: float = 0.0,
) -> OxideGrowth:
    """Grow a thin **dry** oxide with the Massoud correction → :class:`OxideGrowth` (v1.1 entry).

    The opt-in sibling of :func:`grow_oxide` for the thin-dry (gate-oxide) regime: same recipe
    units in (°C, minutes, orientation, optional µm seed), same plain-scalar result out — but the
    growth law is the cited Massoud time-decay model, on Massoud's own coherent constant set.
    The bundled :class:`RateConstants` reports the Massoud ``B``/``B/A`` converted to the module's
    µm-hr display units (reporting only); ``model="massoud"`` tags the result. The moving-boundary
    bookkeeping (``0.44``) is growth-law-independent and carries over unchanged.
    """
    rates = massoud_rate_constants(T_celsius, orientation)
    x = oxide_thickness_massoud(t_minutes, rates, x_initial=x_initial)
    reported = RateConstants(
        ambient="dry", orientation=orientation, T_celsius=T_celsius,
        B=rates.B * _NM2_MIN_TO_UM2_HR, B_over_A=rates.B_over_A * _NM_MIN_TO_UM_HR,
    )
    return OxideGrowth(
        ambient="dry", orientation=orientation, T_celsius=T_celsius,
        t_minutes=t_minutes, x_initial=x_initial, t_ox=float(x), rates=reported,
        model="massoud",
    )
