"""Chip Phase-4 validation: the compact MOS threshold voltage — the process→device triad.

Carries the whole plan §4 triad (microchip-fabrication.md). Like Phase 2 there is **no engine
underneath** — this module *is* the compact closed form — so its tests carry every leg:

* **Analytical limit (tight) — the INDEPENDENT depletion-Poisson solve.** The closed-form depletion
  charge ``√(2qε_Si N_A·2φ_F)`` is recovered by a numerical Poisson integration + root-find
  (:func:`device.depletion_charge_poisson`), the Phase-2 ``solve_ivp`` analogue. The body-effect √-law
  is kept only as a **cheap γ-consistency check** (same formula rearranged — it catches a γ typo, it is
  *not* the anchor).
* **Conservation (tight) — MOS charge neutrality / Gauss's law.** ``Q_g = −(Q_dep + Q_inv)`` closes to
  machine precision; above threshold ``Q_inv = −C_ox(V_GB − V_t)``; Gauss sets ``E_ox = Q_g/ε_ox``.
* **Benchmark (loose) — vs the cited MIT 6.012 worked example.** N⁺-poly / p-substrate ``N_A = 1e17`` /
  ``t_ox = 15 nm`` → ``V_FB = −0.97 V``, ``C_ox = 2.3e-7 F/cm²``, ``V_t ≈ 0.58 V`` (MIT 6.012 PS3 P2,
  [[mos-threshold-voltage-source]]); P2b,c give the conservation cross-check numbers. ``V_t`` rises with
  ``N_A`` and ``t_ox``.

Non-circularity: every constant (ε_Si, ε_ox, q, n_i, the poly band-edge φ_gate) is an independent
physical fact, none fit to a threshold voltage; the inputs ``N_A``/``t_ox`` arrive from upstream Phase-1/2
modules with their own cited data — so reproducing 0.58 V is a cross-check, not a refit.
"""
import math

import numpy as np
import pytest

from chip import device as dev


# --------------------------------------------------------------------------- #
# Benchmark: the cited MIT 6.012 PS3 Problem 2 worked example (pinned)
# --------------------------------------------------------------------------- #
def test_constants_are_the_cited_values():
    # Pin the physical constants (CGS-cm, [[mos-threshold-voltage-source]]). Load-bearing for every V_t.
    assert dev.EPS0 == pytest.approx(8.854e-14, rel=1e-3)
    assert dev.EPS_SI == pytest.approx(11.7 * dev.EPS0)
    assert dev.EPS_OX == pytest.approx(3.9 * dev.EPS0)
    assert dev.EPS_SI == pytest.approx(1.036e-12, rel=1e-2)
    assert dev.EPS_OX == pytest.approx(3.453e-13, rel=1e-2)
    assert dev.NI_300K == 1.0e10                         # MIT value (1.45e10 ↔ φ_F + ~10 mV; named)
    # Degenerate poly gate sits at a band edge: n⁺ = +0.55 V, p⁺ = −0.55 V.
    assert dev.GATE_POTENTIAL["n+poly"] == pytest.approx(+0.55)
    assert dev.GATE_POTENTIAL["p+poly"] == pytest.approx(-0.55)


def test_mit_worked_example_threshold_voltage():
    # MIT 6.012 PS3 (Spring 2007) Problem 2: n⁺-poly gate, p-substrate N_A=1e17, t_ox=15 nm.
    # Published intermediate + final values — the benchmark leg (loose, the model assembled from cited
    # constants reproduces the worked example).
    m = dev.threshold_voltage(N_A=1e17, t_ox_um=0.015, gate="n+poly")
    assert m.phi_F == pytest.approx(0.42, abs=0.01)      # MIT φ_p magnitude ≈ 0.42 V
    assert m.C_ox == pytest.approx(2.3e-7, rel=0.02)     # MIT C_ox = 2.3e-7 F/cm²
    assert m.V_FB == pytest.approx(-0.97, abs=0.01)      # MIT V_FB = −0.97 V
    assert m.V_t == pytest.approx(0.58, abs=0.02)        # MIT V_t ≈ 0.58 V


def test_threshold_rises_with_doping_and_oxide_thickness():
    # The V_t-vs-process-knobs trend (benchmark): heavier channel doping and thicker gate oxide both
    # raise V_t (more depletion charge to support; smaller C_ox).
    base = dev.threshold_voltage(1e17, 0.015).V_t
    assert dev.threshold_voltage(3e17, 0.015).V_t > base   # ↑ N_A → ↑ V_t
    assert dev.threshold_voltage(1e17, 0.030).V_t > base   # ↑ t_ox → ↑ V_t (smaller C_ox)


def test_p_plus_poly_gate_shifts_flatband_by_one_volt():
    # Swapping n⁺-poly (+0.55 V) for p⁺-poly (−0.55 V) shifts φ_gate by 1.1 V, so V_FB (and V_t) shift
    # by +1.1 V (the MIT P3d "1100 mV translation" fact, here on V_t).
    n = dev.threshold_voltage(1e17, 0.015, gate="n+poly")
    p = dev.threshold_voltage(1e17, 0.015, gate="p+poly")
    assert p.V_FB - n.V_FB == pytest.approx(1.1, abs=1e-6)
    assert p.V_t - n.V_t == pytest.approx(1.1, abs=1e-6)


# --------------------------------------------------------------------------- #
# Oxide charge — lifting the named Q_ox = 0 edge (the G4 mobile-ion contamination wire)
# --------------------------------------------------------------------------- #
def test_zero_oxide_charge_is_byte_for_byte_the_ideal_oxide():
    # The seam: Q_ox = 0 (the default) reproduces the ideal-oxide V_FB/V_t exactly — the term is skipped,
    # so no C_ox is needed and nothing changes for every existing caller (demo_device, the MIT example).
    ideal = dev.threshold_voltage(1e17, 0.015, gate="n+poly")
    explicit_zero = dev.threshold_voltage(1e17, 0.015, gate="n+poly", Q_ox=0.0)
    assert explicit_zero.V_FB == ideal.V_FB
    assert explicit_zero.V_t == ideal.V_t
    assert ideal.Q_ox == 0.0
    # flatband_voltage with Q_ox=0 needs no C_ox and equals the no-arg call bit-for-bit.
    assert dev.flatband_voltage(1e17, "n+poly", Q_ox=0.0) == dev.flatband_voltage(1e17, "n+poly")


def test_positive_oxide_charge_shifts_flatband_and_vt_down():
    # ΔV_FB = −Q_ox/C_ox: positive oxide charge (mobile Na⁺ from imperfect purification) drives V_FB —
    # and hence V_t — DOWN, by exactly Q_ox/C_ox. The cited MOS relation, the contamination→device wire.
    m0 = dev.threshold_voltage(1e17, 0.015, gate="n+poly")
    Q_ox = 3.0e-8                                          # C/cm² (~2e11 cm⁻² mobile ions)
    m = dev.threshold_voltage(1e17, 0.015, gate="n+poly", Q_ox=Q_ox)
    assert m.V_FB == pytest.approx(m0.V_FB - Q_ox / m0.C_ox, rel=1e-12)
    assert m.V_t == pytest.approx(m0.V_t - Q_ox / m0.C_ox, rel=1e-12)
    assert m.V_t < m0.V_t                                  # driven down
    assert m.Q_ox == Q_ox


def test_oxide_charge_shift_is_only_the_flatband_term():
    # The whole effect is the flat-band shift: only V_FB moves; φ_F, C_ox, Q_dep, γ are untouched (the
    # oxide charge does not change the depletion electrostatics, just the gate-voltage reference).
    m0 = dev.threshold_voltage(1e17, 0.015)
    m = dev.threshold_voltage(1e17, 0.015, Q_ox=3.0e-8)
    assert (m.phi_F, m.C_ox, m.Q_dep, m.gamma) == (m0.phi_F, m0.C_ox, m0.Q_dep, m0.gamma)
    assert (m.V_t - m0.V_t) == pytest.approx(m.V_FB - m0.V_FB, rel=1e-12)


def test_nonzero_oxide_charge_without_c_ox_raises():
    # A non-zero Q_ox needs the oxide capacitance (ΔV_FB = −Q_ox/C_ox); calling flatband_voltage with
    # Q_ox≠0 and no C_ox is a programming error, not a silent no-op.
    with pytest.raises(ValueError):
        dev.flatband_voltage(1e17, "n+poly", Q_ox=3.0e-8)          # no C_ox


# --------------------------------------------------------------------------- #
# Analytical limit: the INDEPENDENT depletion-Poisson solve (the anchor)
# --------------------------------------------------------------------------- #
def test_depletion_poisson_recovers_the_closed_form():
    # THE analytic anchor (the Phase-2 solve_ivp analogue): a numerical Poisson integration + root-find
    # for the depletion width recovers the closed-form Q_dep = √(2qε_Si N_A·2φ_F) — independently of the
    # √ expression. TIGHT (~1e-8): not machine precision (it is a numerical IVP + brentq) but far tighter
    # than any modeling tolerance.
    for N_A in (1e16, 1e17, 5e17, 1e18):
        phi_F = dev.fermi_potential(N_A)
        for V_SB in (0.0, 1.0, 3.0):
            q_closed = dev.depletion_charge(N_A, phi_F, V_SB)
            q_poisson = dev.depletion_charge_poisson(N_A, phi_F, V_SB)
            assert q_poisson == pytest.approx(q_closed, rel=1e-8)


def test_depletion_width_matches_the_analytic_quadratic():
    # The Poisson root-find returns W = √(2ε_Si·2φ_F/(qN_A)) (the depletion-approximation quadratic
    # ψ(0)=(qN_A/2ε_Si)W²=2φ_F solved for W) — a second view of the same independent solve.
    N_A, phi_F = 1e17, dev.fermi_potential(1e17)
    W = dev.depletion_width_poisson(N_A, phi_F)
    W_analytic = math.sqrt(2.0 * dev.EPS_SI * (2.0 * phi_F) / (dev.Q_ELEMENTARY * N_A))
    assert W == pytest.approx(W_analytic, rel=1e-8)
    assert 0.05e-4 < W < 0.5e-4                          # ~0.1 µm depletion width (sane scale)


def test_body_effect_sqrt_law_is_a_gamma_consistency_check_not_the_anchor():
    # The body-effect √-law is the SAME formula rearranged (V_t0 + γ(√(2φ_F+V_SB) − √(2φ_F)) factors
    # identically to the full V_t(V_SB)). It agrees to MACHINE precision — which only certifies γ is
    # consistent (catches a γ typo); it anchors no physics. Asserted as such, NOT as the analytic leg.
    m = dev.threshold_voltage(1e17, 0.015)
    for V_SB in (0.0, 0.5, 2.0, 5.0):
        full = dev.threshold_voltage(1e17, 0.015, V_SB=V_SB).V_t
        sqrt_law = dev.threshold_voltage_body_effect(m, V_SB)
        assert sqrt_law == pytest.approx(full, rel=1e-12)
    # γ is the documented √(2qε_Si N_A)/C_ox.
    assert m.gamma == pytest.approx(
        math.sqrt(2.0 * dev.Q_ELEMENTARY * dev.EPS_SI * 1e17) / m.C_ox)


def test_body_effect_raises_threshold_monotonically():
    # Reverse source–body bias widens the depletion charge → raises V_t (the √-law, increasing in V_SB).
    m = dev.threshold_voltage(1e17, 0.015)
    V_SB = np.array([0.0, 1.0, 2.0, 4.0])
    Vt = dev.threshold_voltage_body_effect(m, V_SB)
    assert np.all(np.diff(Vt) > 0)
    assert Vt[0] == pytest.approx(m.V_t0)


# --------------------------------------------------------------------------- #
# Conservation: MOS charge neutrality / Gauss's law
# --------------------------------------------------------------------------- #
def test_charge_neutrality_closes_to_machine_precision():
    # Q_g = −(Q_dep + Q_inv): the gate charge mirrors the total semiconductor charge, for any gate bias
    # above threshold. The defining conservation identity — closes exactly by construction.
    m = dev.threshold_voltage(1e17, 0.015)
    for V_GB in (1.0, 2.5, 4.9):
        Q_g = dev.gate_charge(V_GB, m)
        Q_inv = dev.inversion_charge(V_GB, m)
        assert Q_g + (m.Q_dep + Q_inv) == pytest.approx(0.0, abs=1e-18)


def test_inversion_charge_is_the_mit_p2b_cross_check():
    # MIT 6.012 P2b: above threshold Q_inv = −C_ox(V_GB − V_t). For Q_inv = −1e-6 C/cm² the required
    # bias is V_GB = V_t − Q_inv/C_ox ≈ 4.9 V — the cited operating point. Cross-check both directions.
    m = dev.threshold_voltage(1e17, 0.015)
    V_GB = m.V_t + 1.0e-6 / m.C_ox                       # ≈ 4.9 V (MIT)
    assert V_GB == pytest.approx(4.9, abs=0.1)
    assert dev.inversion_charge(V_GB, m) == pytest.approx(-1.0e-6, rel=1e-6)


def test_inversion_charge_is_zero_below_threshold():
    # No inversion layer below V_t (the surface is in depletion, not inversion). Q_inv = 0, so the gate
    # charge balances depletion alone: Q_g = −Q_dep.
    m = dev.threshold_voltage(1e17, 0.015)
    assert dev.inversion_charge(m.V_t - 0.1, m) == 0.0
    assert dev.gate_charge(m.V_t - 0.1, m) == pytest.approx(-m.Q_dep)


def test_gauss_oxide_field_identity_and_mit_p2c_value():
    # Gauss's law across the oxide: E_ox = Q_g/ε_ox holds in code to machine precision (the physical
    # conservation leg). And the MIT P2c arithmetic: a gate charge of 1e-6 C/cm² gives E_ox ≈ 2.9e6 V/cm.
    m = dev.threshold_voltage(1e17, 0.015)
    for V_GB in (2.0, 4.9):
        assert dev.oxide_field(V_GB, m) == pytest.approx(dev.gate_charge(V_GB, m) / dev.EPS_OX, rel=1e-12)
    assert 1.0e-6 / dev.EPS_OX == pytest.approx(2.9e6, rel=0.02)   # MIT P2c: Q_G=1e-6 → E_ox=2.9e6 V/cm


# --------------------------------------------------------------------------- #
# Optional honest long-channel drive current (the litho-CD geometry payoff)
# --------------------------------------------------------------------------- #
def test_saturation_current_scales_with_geometry_and_overdrive():
    # The honest way the Phase-3 CD moves a device number: I_Dsat = ½μC_ox(W/L)(V_GS−V_t)². Halving the
    # channel length (CD) doubles the current; doubling the overdrive quadruples it. (Long-channel — no
    # short-channel V_t rolloff, the named scope edge.)
    m_long = dev.threshold_voltage(1e17, 0.015, channel_length_um=1.0)
    m_short = dev.threshold_voltage(1e17, 0.015, channel_length_um=0.5)
    Vgs = m_long.V_t + 1.0
    I_long = dev.saturation_current(m_long, Vgs, width_um=10.0)
    I_short = dev.saturation_current(m_short, Vgs, width_um=10.0)
    assert I_short == pytest.approx(2.0 * I_long, rel=1e-9)         # ∝ 1/L
    I_2x = dev.saturation_current(m_long, m_long.V_t + 2.0, width_um=10.0)
    assert I_2x == pytest.approx(4.0 * I_long, rel=1e-9)           # ∝ (V_GS−V_t)²


def test_saturation_current_zero_below_threshold_and_needs_geometry():
    m = dev.threshold_voltage(1e17, 0.015, channel_length_um=1.0)
    assert dev.saturation_current(m, m.V_t - 0.1, width_um=10.0) == 0.0
    # Without a channel length (no Phase-3 CD wired) the drive-current readout is unavailable.
    m_no_geom = dev.threshold_voltage(1e17, 0.015)
    with pytest.raises(ValueError):
        dev.saturation_current(m_no_geom, m_no_geom.V_t + 1.0, width_um=10.0)


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #
def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        dev.fermi_potential(-1e17)
    with pytest.raises(ValueError):
        dev.oxide_capacitance(0.0)
    with pytest.raises(ValueError):
        dev.threshold_voltage(1e17, 0.015, gate="aluminum")    # no metal-gate work-function table (v1)
    with pytest.raises(ValueError):
        dev.thermal_voltage(-300.0)                            # below absolute zero
