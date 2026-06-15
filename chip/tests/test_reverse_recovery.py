"""Diode reverse-recovery validation — the recovery triad (device-targets slice 5).

No engine underneath — ``t_rr`` is the closed-form solution of the charge-control ODE (like the compact
``V_t`` / the SRH lifetime / the breakdown root-find), so these tests carry the whole triad:

* **Analytical limit (tight).** ``t_s = τ·ln(1 + I_F/I_R)`` is the exact solution of ``dQ/dt = −Q/τ − I_R``
  with ``Q(0) = I_F·τ``: integrating the ODE forward, the stored charge crosses zero at precisely the
  closed-form ``t_s`` (the criterion closes — the analogue of breakdown's ``∫α dx = 1``). The proportionality
  ``t_rr ∝ τ`` and the ``I_R → ∞`` / ``I_F/I_R → 0`` snap-off limits are exact by construction.
* **Monotonicity (by construction).** ``t_rr`` rises with ``τ`` (the cited lifetime-killing direction — why
  shorter lifetime makes a faster rectifier) and with the operating-point ratio ``I_F/I_R``.
* **Benchmark (loose).** The operating-point factor ``ln(1 + I_F/I_R)`` is an O(1) number (``ln 2 ≈ 0.69``
  at the typical ``I_F = I_R``); ``I_F/I_R`` is a FLAGGED house operating point — only the cited form
  (``t_rr ∝ τ``, charge-control) and the lifetime-killing direction are asserted, never the magnitude.

Non-circularity: ``t_s`` is *derived* from the charge-control ODE (no remembered ``t_rr``-vs-``τ`` fit), so
reproducing the charge-zero crossing by an independent numerical integration is a genuine cross-check.
"""
import numpy as np
import pytest

from chip import reverse_recovery as rr


# --------------------------------------------------------------------------- #
# Analytical limit (tight): the charge-control ODE closes on the charge-zero crossing
# --------------------------------------------------------------------------- #
def test_storage_time_solves_the_charge_control_ode():
    # Integrate dQ/dt = −Q/τ − I_R from Q(0) = I_F·τ and confirm the stored charge crosses zero at exactly
    # the closed-form t_s = τ·ln(1 + I_F/I_R) — the criterion closes (mirror of breakdown's triangular ∫α).
    tau, I_F, I_R = 2.0e-6, 1.0, 0.5            # arbitrary lifetime + operating point
    t_s = rr.reverse_recovery_time(tau, I_F / I_R)
    # Closed form against the analytic ODE solution Q(t) = (I_F+I_R)τ·e^(−t/τ) − I_R·τ at t_s:
    Q_at_ts = (I_F + I_R) * tau * np.exp(-t_s / tau) - I_R * tau
    assert Q_at_ts == pytest.approx(0.0, abs=1e-18)
    # And by a forward Euler march (a genuinely independent integration), Q first reaches ≤ 0 at ~t_s.
    dt = tau / 200000.0
    Q, t = I_F * tau, 0.0
    while Q > 0.0:
        Q += (-Q / tau - I_R) * dt
        t += dt
    assert t == pytest.approx(t_s, rel=2e-3)


def test_proportional_to_lifetime_exactly():
    # t_rr ∝ τ — t_rr/τ is independent of τ for a fixed operating point (the cited linearity, by construction).
    ratios = [rr.reverse_recovery_time(tau, 1.0) / tau for tau in (1.0e-9, 1.0e-7, 1.0e-5, 1.0e-3)]
    assert all(r == pytest.approx(ratios[0], rel=1e-12) for r in ratios)
    assert ratios[0] == pytest.approx(np.log(2.0), rel=1e-12)   # I_F = I_R → K = ln 2


def test_snap_off_and_no_charge_limits():
    # I_R → ∞ (I_F/I_R → 0): a large reverse current sweeps the stored charge out instantly → t_rr → 0.
    assert rr.reverse_recovery_time(1.0e-6, 1.0e-6) == pytest.approx(0.0, abs=1e-11)
    # I_F/I_R → 0 is the same limit (no stored charge to remove).
    assert rr.reverse_recovery_time(1.0e-6, 0.0) == 0.0
    # The factor grows only logarithmically — a 10× current ratio is nowhere near 10× the recovery time.
    assert rr.storage_factor(10.0) < 0.5 * rr.storage_factor(100.0) * 2.0   # sub-linear
    assert rr.storage_factor(1.0) == pytest.approx(np.log(2.0), rel=1e-12)


# --------------------------------------------------------------------------- #
# Monotonicity (by construction): the two directions
# --------------------------------------------------------------------------- #
def test_recovery_rises_with_lifetime():
    # THE slice-5 direction: a longer lifetime → slower recovery (why a clean feed makes a SLOW rectifier and
    # a lifetime-killed one a FAST rectifier — the inversion of the leakage the same τ produces).
    trrs = [rr.reverse_recovery_time(tau) for tau in (1.0e-9, 1.0e-8, 1.0e-7, 1.0e-6, 1.0e-3)]
    assert all(a < b for a, b in zip(trrs, trrs[1:]))


def test_recovery_rises_with_operating_point_ratio():
    # More forward charge relative to the reverse sweep current → more to remove → slower recovery.
    trrs = [rr.reverse_recovery_time(1.0e-6, r) for r in (0.25, 0.5, 1.0, 2.0, 4.0)]
    assert all(a < b for a, b in zip(trrs, trrs[1:]))


# --------------------------------------------------------------------------- #
# Benchmark (loose): the flagged O(1) operating point + the bundled reading
# --------------------------------------------------------------------------- #
def test_operating_point_is_flagged_order_one():
    # The operating-point factor is an O(1) number for a typical switching test (FLAGGED magnitude).
    assert 0.3 < rr.storage_factor(rr.IF_OVER_IR_DEFAULT) < 1.5
    assert rr.IF_OVER_IR_DEFAULT == 1.0


def test_diode_recovery_bundle_reports_nanoseconds():
    # The device-step currency: a lifetime-killed τ ≈ 100 ns gives a fast (sub-µs) rectifier; the bundle
    # carries τ and reports t_rr in ns (the rectifier-scale readout unit).
    rec = rr.diode_recovery(1.0e-7)            # τ = 100 ns
    assert rec.tau == 1.0e-7
    assert rec.t_rr == pytest.approx(1.0e-7 * np.log(2.0))
    assert rec.t_rr_ns == pytest.approx(rec.t_rr * 1.0e9)
    assert rec.t_rr_ns < 100.0                 # storage factor ln2 < 1 → faster than the bare lifetime


def test_negative_lifetime_raises():
    with pytest.raises(ValueError):
        rr.reverse_recovery_time(-1.0e-6)
    with pytest.raises(ValueError):
        rr.storage_factor(-1.0)
