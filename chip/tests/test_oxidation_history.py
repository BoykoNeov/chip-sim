"""Historical-modes A3 — HCl gettering & high-pressure oxidation (``chip.oxidation_history``).

The triad, per ``docs/plans/historical-modes.md``:

  * **tight — HP:** the ``pressure_atm = 1.0`` seam (:func:`chip.oxidation.grow_oxide` bit-for-bit) + the
    **exact** ``t ∝ 1/P`` and ``budget ∝ 1/P`` identity across *every* regime (linear, transition,
    parabolic) — the equal-exponent → invariant-``A`` consequence;
  * **tight — HCl:** the ``chlorine_percent = 0`` seam (:func:`chip.purification.sodium_oxide_charge`
    bit-for-bit) + the sign/monotonicity of the recovery (more Cl → less ``Q_ox`` → higher ``V_t``);
  * **flagged:** the Cl gettering-efficiency curve (saturating, ceiling < 1) — asserted only by shape/sign,
    and the T-reduction magnitude (not tested tightly — a demonstrated flagged number).

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import numpy as np
import pytest

from chip import oxidation as ox
from chip import diffusion_dopant as dd
from chip import purification as pur
from chip import oxidation_history as oh


# --------------------------------------------------------------------------- #
# §B High-pressure oxidation — tight
# --------------------------------------------------------------------------- #
def test_pressure_seam_is_bit_for_bit_grow_oxide():
    """pressure_atm = 1.0 → the plain Deal–Grove rates, and the grow time reproduces grow_oxide exactly."""
    r = oh.hp_oxidation(0.5, dopant="B", ambient="wet", T_celsius=1050.0, pressure_atm=1.0)
    base = ox.oxide_rate_constants("wet", 1050.0, "100")
    assert r.rates.B == base.B and r.rates.B_over_A == base.B_over_A     # seam: rates unscaled
    # the τ-inverse grow time, fed back through grow_oxide, reproduces the target oxide bit-for-bit
    grown = ox.grow_oxide("wet", 1050.0, r.t_ox_hours * ox.MIN_PER_HOUR)
    assert grown.t_ox == pytest.approx(r.x_target_um, rel=1e-12)


def test_A_is_pressure_invariant():
    """The equal exponent on B and B/A leaves A = B/(B/A) invariant (the reason 1/P is exact)."""
    base = oh.pressure_scaled_rates("wet", 1050.0, 1.0)
    for P in (2.0, 5.0, 20.0):
        scaled = oh.pressure_scaled_rates("wet", 1050.0, P)
        assert scaled.A == pytest.approx(base.A, rel=1e-12)


@pytest.mark.parametrize("x_target_um", [0.02, 0.2, 0.5, 1.0])   # spans linear → transition → parabolic
@pytest.mark.parametrize("P", [2.0, 5.0, 20.0])
def test_time_and_budget_scale_exactly_as_one_over_P(x_target_um, P):
    """For a fixed oxide, both grow time and collateral ∫D dt scale EXACTLY as 1/P — in every regime."""
    r1 = oh.hp_oxidation(x_target_um, dopant="B", ambient="wet", T_celsius=1050.0, pressure_atm=1.0)
    rP = oh.hp_oxidation(x_target_um, dopant="B", ambient="wet", T_celsius=1050.0, pressure_atm=P)
    assert rP.t_ox_hours == pytest.approx(r1.t_ox_hours / P, rel=1e-12)
    assert rP.budget == pytest.approx(r1.budget / P, rel=1e-12)


def test_oxidation_time_is_the_tau_offset_inverse():
    """oxidation_time_hours reuses tau_offset — grow_oxide at that time lands on the target (the DG inverse)."""
    rates = oh.pressure_scaled_rates("wet", 1050.0, 5.0)
    t = oh.oxidation_time_hours(0.3, rates)
    assert t == ox.tau_offset(0.3, rates.B, rates.A)                     # literally the τ machinery
    assert ox.oxide_thickness(t, rates.B, rates.A) == pytest.approx(0.3, rel=1e-12)


def test_collateral_budget_is_isothermal_D_times_t():
    """The collateral budget is the intrinsic isothermal drive-in D(T)·t (the ∫D dt currency)."""
    b = oh.collateral_diffusion_budget("B", 1050.0, 0.5)
    assert b == pytest.approx(dd.diffusivity("B", 1050.0) * 0.5 * 3600.0, rel=1e-12)


def test_collateral_budget_is_the_real_E1_thermal_budget():
    """The collateral ∫D dt IS the E1 consumer: it equals dd.thermal_budget of the isothermal program.

    Not merely a parallel D·t formula — the same integral E1's spike/RTA machinery computes, here for the
    degenerate isothermal (flat-T) oxidation program (ThermalProgram.isothermal takes SECONDS)."""
    t_hours = 0.937
    prog = dd.ThermalProgram.isothermal(1050.0, t_hours * 3600.0)
    assert oh.collateral_diffusion_budget("B", 1050.0, t_hours) == pytest.approx(
        dd.thermal_budget("B", prog), rel=1e-9)


# --------------------------------------------------------------------------- #
# §B High-pressure oxidation — flagged (the T-reduction worked example)
# --------------------------------------------------------------------------- #
def test_temperature_for_same_oxide_reduces_T_and_collapses_budget():
    """Trading pressure for temperature grows the same oxide at LOWER T → far less collateral budget."""
    base = oh.hp_oxidation(0.5, dopant="B", ambient="wet", T_celsius=1050.0, pressure_atm=1.0)
    T_red = oh.temperature_for_same_oxide(0.5, ambient="wet", t_hours=base.t_ox_hours, pressure_atm=20.0)
    assert T_red < 1050.0                                               # pressure buys a lower temperature
    # the reduced-T oxide really reaches the target in the same time (the root-find's defining property)
    rates_red = oh.pressure_scaled_rates("wet", T_red, 20.0)
    assert ox.oxide_thickness(base.t_ox_hours, rates_red.B, rates_red.A) == pytest.approx(0.5, rel=1e-6)
    # and the Arrhenius collapse beats the bare 1/P time-saving (the historical point)
    budget_red = oh.collateral_diffusion_budget("B", T_red, base.t_ox_hours)
    assert budget_red < base.budget / 20.0


def test_temperature_for_same_oxide_raises_when_unreachable():
    """An oxide too thick for the T bracket at that pressure refuses rather than extrapolate."""
    with pytest.raises(ValueError, match="not reachable"):
        oh.temperature_for_same_oxide(5.0, ambient="wet", t_hours=0.01, pressure_atm=1.0)


# --------------------------------------------------------------------------- #
# §A HCl / chlorine gettering — tight (seam + sign)
# --------------------------------------------------------------------------- #
def test_chlorine_seam_reproduces_sodium_oxide_charge_bit_for_bit():
    """chlorine_percent = 0 getters nothing → exactly purification.sodium_oxide_charge (byte-identical)."""
    for N_Na in (1e15, 1e16, 5e16):
        assert oh.gettered_sodium_charge(N_Na, 0.0) == pur.sodium_oxide_charge(N_Na)


def test_gettering_fraction_is_zero_at_zero_cl_and_saturates_below_one():
    """The fraction is identically 0 at 0 % Cl (the seam) and rises monotonically to a ceiling < 1."""
    assert oh.chlorine_gettering_fraction(0.0) == 0.0
    fr = [oh.chlorine_gettering_fraction(p) for p in (0.5, 1.0, 3.0, 6.0, 100.0)]
    assert all(a < b for a, b in zip(fr, fr[1:]))                       # strictly increasing
    assert fr[-1] < oh.CHLORINE_MAX_GETTERING < 1.0                     # never getters all the Na


def test_hcl_recovers_vt_monotonically_toward_the_clean_oxide():
    """More Cl → less Q_ox → V_t climbs monotonically back toward the clean-oxide (Q_ox = 0) value."""
    N_Na = 1e16
    devs = [oh.hcl_oxidation(N_Na, pct) for pct in (0.0, 1.0, 3.0, 6.0)]
    vt = [h.device.V_t for h in devs]
    q_ox = [h.Q_ox for h in devs]
    assert all(a < b for a, b in zip(vt, vt[1:]))                       # V_t recovers upward
    assert all(a > b for a, b in zip(q_ox, q_ox[1:]))                   # Q_ox falls
    clean = oh.hcl_oxidation(0.0, 0.0).device.V_t                       # Q_ox = 0 ceiling
    assert vt[0] < vt[-1] < clean                                       # pre-HCl < gettered < clean


def test_clean_feed_gives_zero_qox_at_any_chlorine():
    """N_Na = 0 → Q_ox = 0 regardless of Cl (nothing to getter) — the clean-wafer seam."""
    for pct in (0.0, 2.0, 6.0):
        assert oh.gettered_sodium_charge(0.0, pct) == 0.0


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def test_pressure_and_gettering_reject_bad_inputs():
    """The consumer guards its physical ranges (the established idiom)."""
    with pytest.raises(ValueError, match="pressure_atm"):
        oh.pressure_scaled_rates("wet", 1050.0, 0.0)
    with pytest.raises(ValueError, match="chlorine_percent"):
        oh.chlorine_gettering_fraction(-1.0)
    with pytest.raises(ValueError, match="half_percent"):
        oh.chlorine_gettering_fraction(1.0, half_percent=0.0)
