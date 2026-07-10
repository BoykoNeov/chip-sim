"""Period oxidation ambients — HCl gettering & high-pressure oxidation (historical-modes A3).

The **backward axis** (``docs/plans/historical-modes.md``): the simulator's thermal-oxidation step, run
in two *period* configurations, so the limitations that motivated them become visible on observables the
sim already computes. Like :mod:`chip.doping_history` (A1), this is a **pure consumer** — it adds *no*
oxidation physics and changes *no* existing behaviour; it re-frames :mod:`chip.oxidation` (Deal–Grove) and
feeds the two existing consequence chains. Two orthogonal modes in one chunk (orthogonal because they land
on different observables — ``V_t`` vs the ``∫D dt`` budget):

The two modes and their (real, already-built) consumers
-------------------------------------------------------
* **HCl / chlorine-added oxidation (§A) → the Na→Q_ox→V_t chain (G4a).** Adding HCl (or a chlorocarbon)
  to the oxidizing ambient releases Cl₂, which **getters mobile sodium** at/through the growing oxide —
  it renders Na⁺ immobile/neutral or out-diffuses it (Kriegler, Cheng & Colton, *J. Electrochem. Soc.*
  119(3):388, 1972). The limitation it cured: **pre-HCl gate oxides drifted** (mobile-ion instability).
  Here it **lowers ``Q_ox``** → feeds the existing :func:`chip.purification.sodium_oxide_charge` →
  :func:`chip.device.threshold_voltage` chain: a marginal-Na feed that walked ``V_t`` down is recovered
  toward the clean-oxide value. The **seam**: ``chlorine_percent = 0`` (the pre-HCl period) getters
  nothing → the current ``Q_ox`` bit-for-bit. *Polarity note (unlike A1): the opt-in flag turns on the
  **successor** (HCl removes the Na penalty); the no-Cl default is the period that hit the wall.*

* **High-pressure oxidation (§B) → the ∫D dt collateral-budget chain (E1).** Both Deal–Grove rate
  constants are **linearly proportional to the oxidant partial pressure** (Henry's law: ``B, B/A ∝ C* ∝
  P``; measured linear over 5–20 atm by Razouk, Lie & Deal, *J. Electrochem. Soc.* 128(10), 1981). So the
  **same** oxide grows in **less time** at higher pressure → the underlying dopant profile spends **less
  collateral drive-in budget ``∫D dt``** while the (thick, isolation) oxide grows. The limitation it
  addressed: **thick isolation oxides cost too much diffusion budget at 1 atm** (the same currency E1's
  spike/RTA anneal saves on the anneal side). The **seam**: ``pressure_atm = 1.0`` → :func:`chip.oxidation.
  grow_oxide` bit-for-bit.

The honesty ladder (per ``historical-modes.md`` triad)
------------------------------------------------------
* **Tight — HP.** Because a **single shared exponent = 1** scales *both* ``B`` and ``B/A`` (the cited
  first-order/Henry's-law result), the crossover length ``A = B/(B/A)`` is **pressure-invariant** and the
  whole quadratic ``x² + A·x = P·B·t`` scales cleanly. Consequence: for a fixed target oxide the
  oxidation time obeys ``t ∝ 1/P`` **exactly, in every regime** (linear, transition, parabolic — not just
  the asymptotes), so the intrinsic collateral budget ``D_dopant(T)·t ∝ 1/P`` is an **exact algebraic
  identity**, not an approximation. Plus the ``P = 1`` seam.
* **Tight — HCl.** The seam: ``chlorine_percent = 0`` reproduces :func:`chip.purification.
  sodium_oxide_charge` bit-for-bit (the gettered charge is that charge times ``1 − fraction``, and the
  fraction is *identically* zero at 0 %). And the **sign/monotonicity**: more Cl ⇒ less ``Q_ox`` ⇒ ``V_t``
  recovers upward (a p-substrate n-MOS; Na⁺ is positive charge, ``ΔV_FB = −Q_ox/C_ox`` drives ``V_t``
  down, so removing it lifts ``V_t``).
* **Flagged — the magnitudes.** The **Cl gettering efficiency** curve (:func:`chlorine_gettering_fraction`
  — a saturating house form, ceiling < 1: Cl never removes *all* the Na) and the **temperature-reduction**
  worked example (:func:`temperature_for_same_oxide` — the *real* historical driver, but it needs a
  root-find for ``T`` and its magnitude is Arrhenius-dependent, so it is a demonstrated flagged number, not
  the tight leg).

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **HP — ideal linear pressure scaling.** Real *dry*-O₂ ``B/A`` is sometimes mildly **sub**-linear in
  pressure; this module adopts exponent 1 for both constants (making the ``1/P`` identity exact by
  construction) and does **not** model that sub-linearity — the tight leg is *conditional on* the ideal
  scaling.
* **HP — OED not folded in.** :mod:`chip.coupling` (v1.2) enhances the dopant diffusivity *during*
  oxidation, and OED scales with the oxidation rate — folding it in would break the clean ``1/P``. The
  collateral budget here is the **intrinsic** drive-in ``D·t`` only; OED is a named interaction that would
  add to it.
* **HCl — static offset, not drift dynamics.** The sim reads the **static** mobile-ion ``V_t`` offset
  HCl reduces, **not** the bias-temperature *drift over time* that was the historical failure mode; HCl
  lowers the offset magnitude, which is what is shown.
* **HCl — rate enhancement not modelled.** Chlorine also mildly speeds oxidation (``B``, ``B/A`` rise with
  Cl %); this module scopes HCl to the Na→``Q_ox``→``V_t`` consumer only and does not model the rate effect.

Units — inherited from the consumed modules (no new currency)
-------------------------------------------------------------
Oxide thickness **µm** (the cross-module length currency), oxidation time **hours** internally / minutes
at the recipe boundary (as :mod:`chip.oxidation`), diffusion budget **cm²** (as
:func:`chip.diffusion_dopant.thermal_budget`), ``Q_ox`` **C/cm²**, ``V_t`` **V** (as :mod:`chip.device`).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import oxidation as ox
from . import diffusion_dopant as dd
from . import purification as pur
from . import device as dev

# --------------------------------------------------------------------------- #
# §B. High-pressure oxidation — the ∫D dt collateral-budget consumer (E1)
# --------------------------------------------------------------------------- #
# The cited scaling: both Deal–Grove rate constants are LINEARLY proportional to the oxidant partial
# pressure (Henry's law C* ∝ P; measured linear over 5–20 atm by Razouk–Lie–Deal 1981). One SHARED
# exponent = 1 on both B and B/A keeps A = B/(B/A) pressure-invariant → the t ∝ 1/P identity is exact in
# every regime (see the module docstring). See the named scope edge: real dry B/A can be mildly sublinear.
PRESSURE_EXPONENT = 1.0            # cited first-order scaling B, B/A ∝ P (equal exponent → exact 1/P)


def pressure_scaled_rates(
    ambient: ox.OxidationAmbient | str, T_celsius: float, pressure_atm: float,
    orientation: str = "100",
) -> ox.RateConstants:
    """Deal–Grove rate constants at ``pressure_atm`` — the cited-source ``B, B/A ∝ P`` scaling.

    Evaluates the 1-atm :func:`chip.oxidation.oxide_rate_constants` and scales **both** ``B`` and
    ``B/A`` by ``pressure_atm**PRESSURE_EXPONENT`` (the equal exponent → ``A`` invariant). At
    ``pressure_atm = 1.0`` it *is* the 1-atm rates unchanged (the seam). ``oxidation.py`` is not
    touched — this is a consumer that reads its rates and rescales the result.
    """
    if pressure_atm <= 0.0:
        raise ValueError(f"pressure_atm must be > 0, got {pressure_atm}")
    base = ox.oxide_rate_constants(ambient, T_celsius, orientation)
    scale = pressure_atm ** PRESSURE_EXPONENT
    return ox.RateConstants(
        ambient=base.ambient, orientation=base.orientation, T_celsius=base.T_celsius,
        B=base.B * scale, B_over_A=base.B_over_A * scale,
    )


def oxidation_time_hours(x_target_um: float, rates: ox.RateConstants) -> float:
    """Time (hr) to grow a bare wafer to ``x_target_um`` (µm) of oxide at ``rates`` — the DG inverse.

    Reuses :func:`chip.oxidation.tau_offset`: ``τ = (x² + A·x)/B`` is *exactly* the time for the closed
    form to reach ``x`` from a bare surface (``oxide_thickness(τ, B, A) == x``), so no new inverse is
    introduced — the time-to-thickness map is the τ machinery already in the engine.
    """
    if x_target_um < 0.0:
        raise ValueError(f"x_target_um must be ≥ 0, got {x_target_um}")
    return ox.tau_offset(x_target_um, rates.B, rates.A)


def collateral_diffusion_budget(
    dopant: dd.Dopant | str, T_celsius: float, oxidation_hours: float,
) -> float:
    """Intrinsic dopant drive-in budget ``∫D dt = D(T)·t`` (cm²) spent while the oxide grows.

    Isothermal oxidation holds the wafer at ``T_celsius`` for ``oxidation_hours``, so the underlying
    profile sees a constant-``D`` drive-in of budget ``D_dopant(T)·t`` — the same ``∫D dt`` currency
    :func:`chip.diffusion_dopant.thermal_budget` reports (here degenerate/isothermal). ``D`` from
    :func:`chip.diffusion_dopant.diffusivity` (cm²/s); time hr→s. **Intrinsic only** — OED (which would
    add to it) is a named scope edge, not folded in.
    """
    if oxidation_hours < 0.0:
        raise ValueError(f"oxidation_hours must be ≥ 0, got {oxidation_hours}")
    D = dd.diffusivity(dopant, T_celsius)               # cm²/s
    return D * oxidation_hours * 3600.0                  # cm²


@dataclass(frozen=True)
class HPOxidation:
    """One high-pressure oxidation of a target oxide: the time & collateral budget at ``pressure_atm``.

    ``x_target_um`` the field/isolation oxide grown (µm), at ``T_celsius`` in ``ambient`` on
    ``orientation``; ``t_ox_hours`` the time it takes (:func:`oxidation_time_hours`); ``budget`` the
    intrinsic dopant ``∫D dt`` (cm²) spent meanwhile (:func:`collateral_diffusion_budget`, for
    ``dopant``). Plain scalars — the loose-coupling currency. The tight identity across a pressure sweep:
    both ``t_ox_hours`` and ``budget`` scale **exactly** as ``1/pressure_atm``."""

    ambient: str
    orientation: str
    dopant: str
    T_celsius: float
    x_target_um: float
    pressure_atm: float
    rates: ox.RateConstants
    t_ox_hours: float
    budget: float                # cm² — intrinsic ∫D dt during the oxidation


def hp_oxidation(
    x_target_um: float,
    *,
    dopant: dd.Dopant | str,
    ambient: ox.OxidationAmbient | str = "wet",
    T_celsius: float = 1050.0,
    pressure_atm: float = 1.0,
    orientation: str = "100",
) -> HPOxidation:
    """Grow ``x_target_um`` of ``ambient`` oxide at ``pressure_atm`` → time + collateral ``∫D dt`` budget.

    Defaults to the historically-relevant case: a **thick** wet field/isolation oxide at 1050 °C (the
    parabolic regime, where ``t_ox`` — and hence the ``1/P`` budget saving — is largest). ``dopant``
    (species key or :class:`~chip.diffusion_dopant.Dopant`) is the underlying profile whose collateral
    drive-in is charged. At ``pressure_atm = 1.0`` the rates are the plain Deal–Grove rates (the seam).
    """
    d = dd.DOPANTS[dopant] if isinstance(dopant, str) else dopant
    rates = pressure_scaled_rates(ambient, T_celsius, pressure_atm, orientation)
    t_hours = oxidation_time_hours(x_target_um, rates)
    budget = collateral_diffusion_budget(d, T_celsius, t_hours)
    return HPOxidation(
        ambient=rates.ambient, orientation=orientation, dopant=d.name,
        T_celsius=T_celsius, x_target_um=x_target_um, pressure_atm=pressure_atm,
        rates=rates, t_ox_hours=t_hours, budget=budget,
    )


def temperature_for_same_oxide(
    x_target_um: float,
    *,
    ambient: ox.OxidationAmbient | str = "wet",
    t_hours: float,
    pressure_atm: float,
    orientation: str = "100",
    T_bounds: tuple[float, float] = (600.0, 1200.0),
) -> float:
    """The reduced temperature that grows ``x_target_um`` in a **fixed** ``t_hours`` at ``pressure_atm`` (°C).

    The *real* historical driver, offered as a **FLAGGED worked example**, not a tight leg: high pressure
    lets you trade pressure for **temperature** — grow the same oxide in the same process time at a lower
    ``T`` — and because the dopant ``D`` is Arrhenius, dropping ``T`` collapses the collateral budget far
    more than the ``1/P`` time-saving alone. Solved by a root-find (``brentq``) over ``T_bounds`` for the
    ``T`` at which the pressure-scaled oxide reaches ``x_target_um`` at ``t_hours``; raises if the target
    is unreachable in the bracket. Magnitude is Arrhenius/bounds-dependent → flagged.
    """
    from scipy.optimize import brentq

    def thickness_gap(T: float) -> float:
        rates = pressure_scaled_rates(ambient, T, pressure_atm, orientation)
        return ox.oxide_thickness(t_hours, rates.B, rates.A) - x_target_um

    lo, hi = T_bounds
    if thickness_gap(lo) > 0.0 or thickness_gap(hi) < 0.0:
        raise ValueError(
            f"target oxide {x_target_um} µm at {t_hours} hr, {pressure_atm} atm is not reachable within "
            f"T ∈ {T_bounds} °C (grow thinner, longer, or widen the bracket)")
    return float(brentq(thickness_gap, lo, hi))


# --------------------------------------------------------------------------- #
# §A. HCl / chlorine oxidation — the Na→Q_ox→V_t gettering consumer (G4a)
# --------------------------------------------------------------------------- #
# Cl₂ (from HCl / a chlorocarbon in the ambient) getters mobile Na⁺ at the growing oxide — immobilizes,
# neutralizes or out-diffuses it (Kriegler–Cheng–Colton 1972). Modelled as a saturating removed-fraction
# of the incorporated mobile-ion charge. Both numbers are FLAGGED house calibration (ADR 0005 §5): the
# DIRECTION (Cl lowers Q_ox) is the cited/wired leg, the curve shape is a stand-in.
CHLORINE_MAX_GETTERING = 0.90     # FLAGGED — removed-fraction ceiling (Cl never getters ALL the Na)
CHLORINE_HALF_PERCENT = 1.5       # FLAGGED — Cl % (of the ambient) at half the ceiling removal


def chlorine_gettering_fraction(
    chlorine_percent: float,
    *,
    ceiling: float = CHLORINE_MAX_GETTERING,
    half_percent: float = CHLORINE_HALF_PERCENT,
) -> float:
    """Fraction of the mobile-Na oxide charge Cl getters — saturating, **0 at 0 % Cl** (the seam).

    ``f(pct) = ceiling · pct / (pct + half_percent)`` — a Langmuir-style saturating removal (FLAGGED
    house form): rising Cl % getters more Na but never all of it (``ceiling < 1``). At ``chlorine_percent
    = 0`` it is *identically* ``0`` — the pre-HCl period, where :func:`gettered_sodium_charge` reduces to
    the plain :func:`chip.purification.sodium_oxide_charge` bit-for-bit. Only the DIRECTION (more Cl → more
    removal) is asserted; the curve is a calibrated stand-in.
    """
    if chlorine_percent < 0.0:
        raise ValueError(f"chlorine_percent must be ≥ 0, got {chlorine_percent}")
    if not (0.0 <= ceiling < 1.0):
        raise ValueError(f"ceiling must be in [0, 1), got {ceiling}")
    if half_percent <= 0.0:
        raise ValueError(f"half_percent must be > 0, got {half_percent}")
    return ceiling * chlorine_percent / (chlorine_percent + half_percent)


def gettered_sodium_charge(
    N_Na: float,
    chlorine_percent: float = 0.0,
    *,
    incorporation_cm: float = pur.NA_OXIDE_INCORPORATION_CM,
    ceiling: float = CHLORINE_MAX_GETTERING,
    half_percent: float = CHLORINE_HALF_PERCENT,
) -> float:
    """Gate-oxide mobile-ion charge ``Q_ox`` (C/cm²) from bulk Na ``N_Na``, **after** HCl gettering.

    ``Q_ox = sodium_oxide_charge(N_Na) · (1 − chlorine_gettering_fraction(chlorine_percent))`` — the
    existing Na→``Q_ox`` bridge (:func:`chip.purification.sodium_oxide_charge`), reduced by the gettered
    fraction. **Seam:** ``chlorine_percent = 0`` → fraction ``0`` → exactly
    :func:`chip.purification.sodium_oxide_charge` (byte-identical); ``N_Na = 0`` → ``0`` regardless of Cl
    (nothing to getter). Feeds :func:`chip.device.threshold_voltage` as its ``Q_ox``.
    """
    q_ox = pur.sodium_oxide_charge(N_Na, incorporation_cm)
    fraction = chlorine_gettering_fraction(
        chlorine_percent, ceiling=ceiling, half_percent=half_percent)
    return q_ox * (1.0 - fraction)


@dataclass(frozen=True)
class HClOxidation:
    """One gate at bulk Na ``N_Na`` oxidised with ``chlorine_percent`` Cl: the gettered ``Q_ox`` and ``V_t``.

    ``Q_ox`` (C/cm²) the mobile-ion charge left after gettering (:func:`gettered_sodium_charge`); ``device``
    the resulting :class:`chip.device.MOSDevice` (its ``V_t`` is the observable). ``gettered_fraction`` the
    fraction Cl removed. The contrast the demo draws: ``chlorine_percent = 0`` (pre-HCl) sits low in ``V_t``;
    HCl lifts it toward the clean-oxide value."""

    N_Na: float
    chlorine_percent: float
    gettered_fraction: float
    Q_ox: float
    device: dev.MOSDevice


def hcl_oxidation(
    N_Na: float,
    chlorine_percent: float = 0.0,
    *,
    N_A: float = 1.0e17,
    t_ox_um: float = 0.02,
    gate: str = "n+poly",
    ceiling: float = CHLORINE_MAX_GETTERING,
    half_percent: float = CHLORINE_HALF_PERCENT,
) -> HClOxidation:
    """Oxidise a gate carrying bulk Na ``N_Na`` with ``chlorine_percent`` Cl → the ``Q_ox``-shifted ``V_t``.

    Wires the gettered charge into the existing device model: ``V_t`` from :func:`chip.device.
    threshold_voltage` at channel doping ``N_A`` (cm⁻³) and gate oxide ``t_ox_um`` (µm), with
    ``Q_ox = gettered_sodium_charge(N_Na, chlorine_percent)``. **Seam:** ``chlorine_percent = 0`` gives the
    pre-HCl ``V_t`` (the full mobile-ion penalty); a clean feed ``N_Na = 0`` gives the ideal-oxide ``V_t``
    (``Q_ox = 0``) at any Cl. Defaults are a thin-gate n-MOS on a p-substrate (the mobile-ion regime).
    """
    Q_ox = gettered_sodium_charge(
        N_Na, chlorine_percent, ceiling=ceiling, half_percent=half_percent)
    fraction = chlorine_gettering_fraction(
        chlorine_percent, ceiling=ceiling, half_percent=half_percent)
    device = dev.threshold_voltage(N_A=N_A, t_ox_um=t_ox_um, gate=gate, Q_ox=Q_ox)  # C_ox internal
    return HClOxidation(N_Na=N_Na, chlorine_percent=chlorine_percent,
                        gettered_fraction=fraction, Q_ox=Q_ox, device=device)
