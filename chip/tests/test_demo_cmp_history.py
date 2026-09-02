"""Integration test for the CMP history demo (B11 — the F8 payload, end-to-end).

``test_cmp.py`` exercises :mod:`chip.cmp` with hardcoded inputs and never calls the demo: it already pins the
closed forms, the kinematic identity, the scale refusal and the calibration quarantine, and none of that is
re-asserted here. This test guards what only the demo can break — the **chaining** and the **words**:

  * **the period transistor is a bystander, bit-for-bit** — ``τ_gate`` is one float across every curve,
    because :func:`chip.interconnect.delay` reads ``I_Dsat`` in the gate term only; the middle panel's
    whole claim is that the spread is the wire's;
  * **the seam runs through the real wire model** — ``s = 0`` gives nominal thickness at every radius, and
    the copper curve is F4's number on the house :class:`chip.interconnect.WireGeometry` exactly;
  * **the window's floor and closure are chip.cmp's closed forms, not re-derived** — the floor is
    ``1/(1−s)`` (so the forced overpolish is the floor minus 1), the ceiling is ``None`` past ``s_crit``;
  * **the loss at the house pitch is erosion only** — dishing is exactly zero, so the right panel's
    "two levers" claim is not quietly a three-lever one;
  * **the figure's words**, which the fast lane otherwise cannot check (the golden tests confirm the prose
    did not *change*, never that it is still *true*).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import math
from pathlib import Path

import numpy as np
import pytest

from chip import cmp
from chip import device as dev
from chip import interconnect as ic

from chip import demo_cmp_history
from chip.demo_cmp_history import (
    HOUSE_GEOMETRY, HOUSE_PITCH_UM, MODERN_METAL, OVERBURDEN_UM, PERIOD_CHANNEL_L_UM, PERIOD_METAL,
    PERIOD_N_A, PERIOD_T_OX_UM, PERIOD_WIDTH_UM, R_BUDGET_LOOSE, R_BUDGET_TIGHT, S_CURVES, S_HOUSE,
    SHORT_POLISH_FRACTION, compute, house_pattern, loss_budget, polished_thickness_um,
)


@pytest.fixture(scope="module")
def r():
    return compute()


def test_the_period_transistor_is_the_real_untouched_device_chain(r):
    mos = dev.threshold_voltage(PERIOD_N_A, PERIOD_T_OX_UM, channel_length_um=PERIOD_CHANNEL_L_UM)
    assert r.mos.V_t == mos.V_t
    assert r.i_dsat_A == dev.saturation_current(mos, V_GS=ic.V_DD_HOUSE, width_um=PERIOD_WIDTH_UM)
    assert 0.3 < r.mos.V_t < 1.0                                          # era-plausible, not tuned


def test_the_transistor_is_a_bystander_tau_gate_is_one_float_on_every_curve(r):
    """The middle panel's claim: the spread is the WIRE's. Enforced by delay()'s construction, asserted here."""
    c_load = r.c_load_F
    for s in S_CURVES:
        for h in r.thickness_um[s]:
            assert ic.delay(ic.WireGeometry(thickness_um=float(h)), r.i_dsat_A, c_load,
                            metal=MODERN_METAL).tau_gate_s == r.tau_gate_s
    assert ic.delay(HOUSE_GEOMETRY, r.i_dsat_A, c_load, metal=PERIOD_METAL).tau_gate_s == r.tau_gate_s


def test_the_seam_runs_through_the_real_wire_model(r):
    """``s = 0`` ⇒ nominal thickness at every radius ⇒ F4's copper number, bit-for-bit, everywhere."""
    for radius in (0.0, 0.3, 0.7, 1.0):
        assert polished_thickness_um(radius, 0.0) == HOUSE_GEOMETRY.thickness_um
    f4 = ic.delay(HOUSE_GEOMETRY, r.i_dsat_A, r.c_load_F, metal=MODERN_METAL)
    assert r.tau_cu_uniform_s == f4.tau_total_s and r.tau_wire_cu_uniform_s == f4.tau_wire_s
    # …and the period line is the same house geometry in the period metal: flat by construction, and higher
    # by exactly the resistivity ratio (τ_wire ∝ R ∝ ρ at fixed geometry — prefactor-free).
    rho = {m.name: m.rho0_uohm_cm for m in ic.METALS.values()} if isinstance(ic.METALS, dict) else None
    al, cu = ic._resolve(PERIOD_METAL), ic._resolve(MODERN_METAL)
    assert r.tau_wire_al_s / r.tau_wire_cu_uniform_s == pytest.approx(al.rho0_uohm_cm / cu.rho0_uohm_cm)
    assert r.tau_al_s > r.tau_cu_uniform_s


def test_the_centre_is_f4s_number_and_the_rim_carries_the_forced_overpolish(r):
    """At the clear-everywhere time the slowest site removes exactly the overburden — nominal thickness — and
    every curve leaves that one point; the rim is thinner, monotonically, and more so at larger ``s``."""
    H0 = HOUSE_GEOMETRY.thickness_um
    prev_rim = H0
    for s in S_CURVES:
        H, tau = r.thickness_um[s], r.tau_total_s[s]
        assert not np.isnan(H).any()                                      # the float knife-edge is closed
        assert H[0] == H0 and tau[0] == r.tau_cu_uniform_s                 # the centre IS F4
        assert np.all(np.diff(H) <= 0.0) and np.all(np.diff(tau) >= 0.0)  # thinner and slower outward
        assert H[-1] < prev_rim                                            # …and more so at larger s
        prev_rim = H[-1]
        assert r.rim_loss[s] == pytest.approx(1.0 - H[-1] / H0)


def test_the_window_is_chip_cmps_closed_forms_not_a_re_derivation(r):
    s = r.s_axis
    assert np.allclose(r.floor_overburdens, 1.0 / (1.0 - s))
    assert np.allclose(r.forced_overpolish, r.floor_overburdens - 1.0)   # the floor minus 1, no constant
    assert r.forced_overpolish[0] == 0.0                                  # the seam of the wall
    pat = house_pattern()
    assert r.s_crit_tight == cmp.critical_nonuniformity(loss_budget(R_BUDGET_TIGHT), HOUSE_GEOMETRY.thickness_um,
                                                        OVERBURDEN_UM, pat)
    assert r.s_crit_loose == cmp.critical_nonuniformity(loss_budget(R_BUDGET_LOOSE), HOUSE_GEOMETRY.thickness_um,
                                                        OVERBURDEN_UM, pat)
    assert r.s_crit_tight < r.s_crit_loose                                # the budget moves the crossing…
    closed = np.isnan(r.ceiling_tight)
    assert closed[s > r.s_crit_tight + 1e-9].all() and not closed[s < r.s_crit_tight - 1e-9].any()   # …not the closure
    ok = ~closed
    assert np.all(r.ceiling_tight[ok] >= r.floor_overburdens[ok] - 1e-12)


def test_the_short_side_is_a_centre_disc_with_a_closed_form_edge(r):
    mean_short = SHORT_POLISH_FRACTION * OVERBURDEN_UM / (1.0 - S_HOUSE)
    assert r.short_r_star == cmp.shorted_radius_frac(S_HOUSE, mean_short, OVERBURDEN_UM)
    assert 0.0 < r.short_r_star < 1.0
    inside = r.r_axis < r.short_r_star
    assert np.isnan(r.tau_total_short_s[inside]).all()                    # no wire to read inside r*
    assert not np.isnan(r.tau_total_short_s[~inside]).any()
    # the rim is STILL over-polished on the short polish — thinner than nominal, so slower than F4
    assert r.tau_total_short_s[-1] > r.tau_cu_uniform_s
    # …but less so than at the clear time: polishing less shrinks the rim loss and grows the disc
    assert r.tau_total_short_s[-1] < r.tau_total_s[S_HOUSE][-1]


def test_at_the_house_pitch_the_loss_is_erosion_only_so_there_are_exactly_two_levers(r):
    assert r.dishing_efficiency_house == 0.0
    assert house_pattern().sub_micron
    assert r.dishing_efficiency_source_pitch > 1.0                        # what it WOULD be at 250 µm: off-scale
    for s in S_CURVES:
        vals = r.rim_loss_vs_density[s]
        ok = ~np.isnan(vals)
        assert np.all(np.diff(vals[ok]) > 0.0)                            # erosion ↑ with density, strictly
        # the product structure: loss(d) = η(d) · 2s/(1−s) · t_over/H₀, with η the module's own
        over_rim = OVERBURDEN_UM * 2.0 * s / (1.0 - s)
        i = int(np.argmin(np.abs(r.density_axis - r.house_density)))
        expect = cmp.erosion_efficiency(house_pattern(float(r.density_axis[i]))) * over_rim / HOUSE_GEOMETRY.thickness_um
        assert vals[i] == pytest.approx(expect)
    # and the house line's rim loss on the right panel IS the middle panel's rim loss (one number, two views)
    i = int(np.argmin(np.abs(r.density_axis - r.house_density)))
    assert r.rim_loss_vs_density[S_HOUSE][i] == pytest.approx(r.rim_loss[S_HOUSE], rel=1e-6)


def test_the_kinematic_identity_is_exact_and_a_near_match_barely_moves(r):
    assert r.v_matched_centre_m_s == r.v_matched_edge_m_s
    assert r.v_offmatch_spread < 0.05


def test_the_figure_says_what_the_enabling_claim_and_the_flags_are():
    """**The words, pinned.** Three things the figure must say, because nothing else can check them."""
    src = Path(demo_cmp_history.__file__).read_text(encoding="utf-8")
    assert "COPPER CANNOT BE PLASMA-ETCHED" in src                         # the enabling claim, on the suptitle
    assert "THE RADIAL AMPLITUDE s IS A HOUSE NUMBER" in src               # the flag, on the suptitle
    assert "NOT A LEVER — polishing less" in src                           # the S1 headline, on the panel
    assert "s_crit = L/(2+L)" in src and "s/(1−s)" in src                  # both closed forms named


def test_figure_builds(r):
    pytest.importorskip("matplotlib")               # the figure is not in the correctness path (ADR 0002)
    from chip.demo_cmp_history import save_figure
    assert save_figure(r).is_file()
