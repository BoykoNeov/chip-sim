"""F8 CMP / planarity (:mod:`chip.cmp`) — the step that gives the wire a spread of its own.

The triad, per ``docs/plans/cmp-planarity-f8.md`` + ``historical-modes.md``:

  * **tight — the forced-overpolish law:** ``overpolish/t_over = s/(1−s)``, with **no house constant**.
    ``s = 0`` gives *exactly* zero: a perfectly uniform polish dishes nothing, at any pattern, for any
    time. Every gram of dishing in the module is bought by non-uniformity;
  * **tight — the window collapse:** ``s_crit = L/(2+L)``, and :func:`polish_window_um` agrees with
    :func:`critical_nonuniformity` on both sides of it (the two are derived from one inequality, so a
    disagreement is a real bug, not a rounding question);
  * **tight — the Preston kinematic identity:** at matched carrier/platen speeds the pad–wafer relative
    speed is position-independent **exactly**, over radius *and* angle — which is what disqualifies
    Preston's ``V`` from carrying a centre-to-edge signature and hands it to ``P``;
  * **tight — ``R ∝ 1/H``:** ``resistance_factor == 1/(1−loss)``, cross-checked **against the real**
    :func:`chip.interconnect.wire_resistance` rather than against itself;
  * **the scale refusal made mechanical:** dishing returns *exactly* 0.0 below the cited trend's zero
    crossing, so a sub-micron signal line is an **erosion**-only regime — the module's second finding;
  * **the calibration pinned as a calibration:** :data:`DISH_SCALE` is a free multiplier the source does
    not fix, so the tests assert that every *quotable* leg is **invariant** to it. A claim that moves when
    an uncalibrated constant moves is not one this module gets to make.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math

import pytest

from chip import cmp, interconnect as ic


# --------------------------------------------------------------------------- #
# Preston's equation — linear in P and in V, and that linearity is load-bearing
# --------------------------------------------------------------------------- #
def test_preston_is_linear_in_pressure_and_speed():
    """Doubling either factor doubles the removal — no exponent softens the pressure profile."""
    base = cmp.preston_removal_um(3.0, 0.5, 60.0)
    assert cmp.preston_removal_um(6.0, 0.5, 60.0) == pytest.approx(2.0 * base)
    assert cmp.preston_removal_um(3.0, 1.0, 60.0) == pytest.approx(2.0 * base)
    assert cmp.preston_removal_um(3.0, 0.5, 120.0) == pytest.approx(2.0 * base)


def test_preston_removes_nothing_at_zero_pressure_speed_or_time():
    for args in ((0.0, 0.5, 60.0), (3.0, 0.0, 60.0), (3.0, 0.5, 0.0)):
        assert cmp.preston_removal_um(*args) == 0.0


@pytest.mark.parametrize("args", [(-1.0, 0.5, 60.0), (3.0, -0.5, 60.0), (3.0, 0.5, -1.0)])
def test_preston_refuses_negative_inputs(args):
    with pytest.raises(ValueError):
        cmp.preston_removal_um(*args)


# --------------------------------------------------------------------------- #
# The kinematic identity — the leg that disqualifies V (tight, exact)
# --------------------------------------------------------------------------- #
def test_matched_speeds_make_relative_speed_position_independent_exactly():
    """ω_w == ω_p ⇒ |v_rel| = ω·d at EVERY point on the wafer — over radius and angle both.

    This is the derived identity the module's pressure claim rests on: if velocity were position-
    dependent here, Preston's V could carry the centre-to-edge signature and the whole 'it is a pressure
    story' leg would collapse. Asserted exactly (``==``), not approximately.
    """
    omega, d = 5.0, 0.2
    expected = omega * d
    for r in (0.0, 0.05, 0.1, 0.15):
        for angle in (0.0, 0.7, 1.3, math.pi, 5.0):
            assert cmp.relative_speed_m_s(omega, omega, d, r, angle) == pytest.approx(expected)
    assert cmp.velocity_is_uniform(omega, omega)


def test_off_match_speeds_do_vary_with_position_but_only_by_a_few_percent():
    """The identity is specific to matched speeds — and off-match the spread is the literature's few %."""
    centre = cmp.relative_speed_m_s(6.0, 5.0, 0.2, 0.0)
    edge = cmp.relative_speed_m_s(6.0, 5.0, 0.2, 0.1, 1.3)
    assert centre != edge
    assert abs(edge - centre) / centre < 0.05
    assert not cmp.velocity_is_uniform(6.0, 5.0)


# --------------------------------------------------------------------------- #
# The pattern — density is a fraction below 1, and 1 is a divergence not a clamp
# --------------------------------------------------------------------------- #
def test_pattern_derives_line_width_and_oxide_space_from_the_cited_definition():
    """density := line width / pitch (the source's own definition), so both follow from the pair."""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.4)
    assert p.line_width_um == pytest.approx(100.0)
    assert p.oxide_space_um == pytest.approx(150.0)


@pytest.mark.parametrize("density", [1.0, 1.5, -0.1])
def test_pattern_refuses_density_outside_zero_to_one(density):
    """density = 1 leaves no oxide standing to carry the pad load — refused, not clamped."""
    with pytest.raises(ValueError):
        cmp.PatternGeometry(pitch_um=250.0, density=density)


def test_pattern_refuses_non_positive_pitch():
    with pytest.raises(ValueError):
        cmp.PatternGeometry(pitch_um=0.0)


# --------------------------------------------------------------------------- #
# The two efficiencies, each on its primary measured axis
# --------------------------------------------------------------------------- #
def test_dishing_is_exactly_zero_at_and_below_the_trend_zero_crossing():
    """A sub-micron signal line has NO dishing — exactly 0.0, not a clamped small number.

    This is the module's second finding made mechanical: dishing is a wide-feature problem, so at the
    sim's dimensions the loss is an EROSION story. A clamp to something tiny would blur that into a
    'small effect' instead of an absent one.
    """
    for pitch in (0.25, 0.5, 0.9, cmp.DISH_ZERO_PITCH_UM):
        p = cmp.PatternGeometry(pitch_um=pitch, density=0.5)
        assert cmp.dishing_efficiency(p) == 0.0
        assert p.sub_micron or pitch == cmp.DISH_ZERO_PITCH_UM


def test_dishing_rises_log_linearly_with_pitch_above_the_crossing():
    """Fig. 5's shape: equal ratios of pitch add equal dishing (log-linear), and it is monotone."""
    etas = [cmp.dishing_efficiency(cmp.PatternGeometry(pitch_um=p)) for p in (10.0, 100.0, 1000.0)]
    assert etas[0] < etas[1] < etas[2]
    assert (etas[1] - etas[0]) == pytest.approx(etas[2] - etas[1])      # equal per decade


def test_erosion_rises_with_density_and_diverges_as_the_oxide_runs_out():
    """η_erode ∝ d/(1−d): the standing oxide carries the pad load, so it blows up as its area → 0."""
    etas = [cmp.erosion_efficiency(cmp.PatternGeometry(0.5, d)) for d in (0.1, 0.5, 0.9, 0.99)]
    assert etas[0] < etas[1] < etas[2] < etas[3]
    assert cmp.erosion_efficiency(cmp.PatternGeometry(0.5, 0.0)) == 0.0
    assert cmp.erosion_efficiency(cmp.PatternGeometry(0.5, 0.999)) > 100.0


def test_total_loss_efficiency_is_the_sources_own_sum_of_the_two():
    """'By adding copper dishing to oxide erosion, we get the total copper loss in the trenches.'"""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    assert cmp.loss_efficiency(p) == pytest.approx(
        cmp.dishing_efficiency(p) + cmp.erosion_efficiency(p))


def test_at_the_sims_scale_the_loss_is_entirely_erosion():
    """The finding, asserted: on a 0.5 µm pitch every bit of the loss efficiency is the erosion term."""
    p = cmp.PatternGeometry(pitch_um=0.5, density=0.9)
    assert cmp.dishing_efficiency(p) == 0.0
    assert cmp.loss_efficiency(p) == cmp.erosion_efficiency(p) > 0.0


# --------------------------------------------------------------------------- #
# The headline — s/(1−s), and the window it closes
# --------------------------------------------------------------------------- #
def test_a_perfectly_uniform_polish_forces_exactly_zero_overpolish():
    """The sharpest form of the wall: dishing is bought by non-uniformity and by nothing else."""
    assert cmp.forced_overpolish_ratio(0.0) == 0.0                     # exactly


def test_forced_overpolish_is_the_closed_form_and_diverges():
    for s in (0.05, 0.1, 0.25, 0.5):
        assert cmp.forced_overpolish_ratio(s) == pytest.approx(s / (1.0 - s))
    assert cmp.forced_overpolish_ratio(0.5) == pytest.approx(1.0)
    assert cmp.forced_overpolish_ratio(0.99) > 90.0


@pytest.mark.parametrize("s", [1.0, 1.5, -0.01])
def test_forced_overpolish_refuses_s_outside_zero_to_one(s):
    with pytest.raises(ValueError):
        cmp.forced_overpolish_ratio(s)


def test_critical_nonuniformity_matches_the_derived_closed_form():
    """s_crit = L/(2+L) with L = loss_max·H₀/(η·t_over) — recomputed here from the inputs, not echoed."""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    H0, t_over, budget = 0.8, 0.7, 0.5
    L = budget * H0 / (cmp.loss_efficiency(p) * t_over)
    assert cmp.critical_nonuniformity(budget, H0, t_over, p) == pytest.approx(L / (2.0 + L))


def test_the_window_exists_below_s_crit_and_is_closed_above_it():
    """The two functions come from ONE inequality, so they must agree on both sides of the boundary."""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    H0, t_over, budget = 0.8, 0.7, 0.5
    s_crit = cmp.critical_nonuniformity(budget, H0, t_over, p)
    assert cmp.polish_window_um(budget, H0, t_over, s_crit * 0.9, p) is not None
    assert cmp.polish_window_um(budget, H0, t_over, s_crit * 1.1, p) is None


def test_a_closed_window_returns_none_rather_than_a_crossed_interval():
    """A caller taking the midpoint of an inverted interval would report a recipe that shorts AND thins."""
    p = cmp.PatternGeometry(pitch_um=1000.0, density=0.8)         # brutal pattern
    assert cmp.polish_window_um(0.2, 0.8, 0.7, 0.5, p) is None


def test_the_window_lower_bound_is_the_clearing_requirement():
    """Whatever else moves, the floor is 'clear the slowest site': t_over/(1−s)."""
    p = cmp.PatternGeometry(pitch_um=0.5, density=0.5)
    lo, _ = cmp.polish_window_um(0.5, 0.8, 0.7, 0.1, p)
    assert lo == pytest.approx(0.7 / 0.9)


def test_a_pattern_that_loses_nothing_has_no_binding_upper_bound():
    """η = 0 (sub-micron pitch, zero density) ⇒ the budget cannot be spent, so only clearing binds."""
    p = cmp.PatternGeometry(pitch_um=0.5, density=0.0)
    assert cmp.loss_efficiency(p) == 0.0
    assert cmp.critical_nonuniformity(0.5, 0.8, 0.7, p) == 1.0
    lo, hi = cmp.polish_window_um(0.5, 0.8, 0.7, 0.1, p)
    assert math.isinf(hi) and lo > 0.0


# --------------------------------------------------------------------------- #
# The polish itself — the two-sided window made concrete
# --------------------------------------------------------------------------- #
def test_under_polish_leaves_residual_copper_and_an_untouched_trench():
    """The short side: nothing has reached the trench yet, so the wire is still nominal thickness."""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    res = cmp.polish(0.4, overburden_um=0.7, trench_depth_um=0.8, pattern=p)
    assert not res.cleared
    assert res.residual_um == pytest.approx(0.3)
    assert res.overpolish_um == 0.0
    assert res.loss_fraction == 0.0
    assert res.thickness_um == pytest.approx(0.8)


def test_exactly_clearing_costs_nothing_the_seam_of_the_two_sided_window():
    """Removal == overburden is the boundary: cleared, and not one ångström of trench copper lost."""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    res = cmp.polish(0.7, overburden_um=0.7, trench_depth_um=0.8, pattern=p)
    assert res.cleared and res.residual_um == 0.0
    assert res.overpolish_um == 0.0 and res.loss_fraction == 0.0
    assert res.thickness_um == 0.8


def test_over_polish_thins_the_trench_by_both_mechanisms():
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    res = cmp.polish(0.75, overburden_um=0.7, trench_depth_um=0.8, pattern=p)
    assert res.cleared and res.overpolish_um == pytest.approx(0.05)
    assert res.dish_loss > 0.0 and res.erosion_loss > 0.0
    assert res.loss_fraction == pytest.approx(res.dish_loss + res.erosion_loss)
    assert res.thickness_um == pytest.approx(0.8 * (1.0 - res.loss_fraction))


def test_polishing_the_trench_out_raises_rather_than_returning_zero():
    """No conductor ⇒ no thickness and no resistance to report (chip.interconnect's floor discipline)."""
    p = cmp.PatternGeometry(pitch_um=1000.0, density=0.9)
    with pytest.raises(ValueError, match="polished out"):
        cmp.polish(1.5, overburden_um=0.7, trench_depth_um=0.8, pattern=p)


# --------------------------------------------------------------------------- #
# R ∝ 1/H — cross-checked against the real chip.interconnect, not against itself
# --------------------------------------------------------------------------- #
def test_resistance_factor_is_one_over_one_minus_loss():
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    res = cmp.polish(0.75, overburden_um=0.7, trench_depth_um=0.8, pattern=p)
    assert res.resistance_factor == pytest.approx(1.0 / (1.0 - res.loss_fraction))


def test_resistance_factor_reproduces_the_real_wire_resistance_ratio():
    """The whole point of the fraction: it IS what interconnect.wire_resistance returns on the thinner
    line, so the loss reaches τ_wire without chip.cmp importing F4's model or duplicating it."""
    p = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    H0 = 0.8
    res = cmp.polish(0.74, overburden_um=0.7, trench_depth_um=H0, pattern=p)
    rho, length, width = 1.68, 1000.0, 0.25
    nominal = ic.wire_resistance(rho, length, width, H0)
    polished = ic.wire_resistance(rho, length, width, res.thickness_um)
    assert polished / nominal == pytest.approx(res.resistance_factor)


# --------------------------------------------------------------------------- #
# The calibration, pinned AS a calibration
# --------------------------------------------------------------------------- #
def test_every_quotable_leg_is_invariant_to_the_calibrated_constant(monkeypatch):
    """DISH_SCALE is a free multiplier the source does not fix — so nothing quotable may depend on it.

    This test is the honesty ladder made executable: if a future edit routes a headline through
    ``DISH_SCALE``, this fails and the claim has to be re-classified rather than quietly inheriting the
    calibration's authority.
    """
    p_fine = cmp.PatternGeometry(pitch_um=0.5, density=0.9)
    before = (
        cmp.forced_overpolish_ratio(0.1),
        cmp.relative_speed_m_s(5.0, 5.0, 0.2, 0.1, 1.3),
        cmp.dishing_efficiency(p_fine),
        cmp.erosion_efficiency(p_fine),
        cmp.polish(0.75, 0.7, 0.8, p_fine).resistance_factor,
    )
    monkeypatch.setattr(cmp, "DISH_SCALE", cmp.DISH_SCALE * 3.0)
    after = (
        cmp.forced_overpolish_ratio(0.1),
        cmp.relative_speed_m_s(5.0, 5.0, 0.2, 0.1, 1.3),
        cmp.dishing_efficiency(p_fine),
        cmp.erosion_efficiency(p_fine),
        cmp.polish(0.75, 0.7, 0.8, p_fine).resistance_factor,
    )
    assert before == after


def test_the_calibrated_constant_does_move_the_wide_feature_magnitudes():
    """The companion assertion: DISH_SCALE is not inert, it is *quarantined*. If it moved nothing at
    all the previous test would be vacuous."""
    p_wide = cmp.PatternGeometry(pitch_um=250.0, density=0.5)
    assert cmp.dishing_efficiency(p_wide) == pytest.approx(
        cmp.DISH_SCALE * cmp.DISH_DECADE_SLOPE * math.log10(250.0 / cmp.DISH_ZERO_PITCH_UM))


# --------------------------------------------------------------------------- #
# The cited experiment, and the scale gap that decides which legs port
# --------------------------------------------------------------------------- #
def test_cited_overburden_follows_from_the_published_stack():
    """1.5 µm plated over a 0.8 µm trench ⇒ 0.7 µm standing above the field oxide."""
    assert cmp.CITED.overburden_um == pytest.approx(0.7)


def test_the_scale_gap_is_two_numbers_and_they_disagree_by_orders_of_magnitude():
    """Near-scale monotone legs port; the far-scale break point does not. The ratios say which is which."""
    nearest, break_point = cmp.CITED.scale_gap(0.5)
    assert nearest == pytest.approx(4.0)                # 2 µm smallest measured pitch — short extrapolation
    assert break_point == pytest.approx(200.0)          # 100 µm oxide space — refused
    assert break_point / nearest > 20.0


def test_the_source_supplies_no_radial_profile():
    """It averaged nine dies per wafer to remove exactly the variation slice 2 needs ⇒ that amplitude is
    a house number, and this pins the reason in the test suite rather than only in prose."""
    assert cmp.CITED.dies_averaged == 9
