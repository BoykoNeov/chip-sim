"""Integration test for the G4b lifetime/leakage demo (the demo IS the integration check).

The G4b demo wires the new SRH lifetime/junction-leakage physics (:mod:`chip.lifetime`) through the
harness so the deep-level **metals** finally become a *device* consequence — the one net doping cannot
carry. Its ``compute`` is the end-to-end check that the metal → killed-lifetime → leaky-diode → yield
chain holds, asserted on the robust thesis (clean silicon is high-lifetime/low-leakage; a metal-laden
feed scraps the wafer on **leakage** while ``V_t`` stays fine; more zone passes recover it), not brittle
exact numbers (the SRH law is pinned in ``chip/tests/test_lifetime.py``, the wiring in
``test_leakage.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game import wafer_yield
from fab_game.demo_lifetime import compute


def test_demo_scaling_clean_is_high_lifetime_metal_is_leaky():
    """The cited order: clean float-zone silicon ~ms lifetime / mm length / pA leakage; metals kill all three."""
    r = compute()
    # The sweep runs clean → dirty: lifetime falls, diffusion length falls, leakage rises monotonically.
    assert r.tau_us_sweep[0] > r.tau_us_sweep[-1]
    assert r.L_um_sweep[0] > r.L_um_sweep[-1]
    assert r.leak_sweep[0] < r.leak_sweep[-1]
    assert r.tau_us_sweep[0] > 100.0                         # clean end ~ms (in µs) — high lifetime
    assert r.leak_sweep[0] < 1.0                             # …and a tiny (sub-nA/cm²) baseline leakage


def test_demo_metal_kill_is_isolated_vt_is_a_bystander():
    """The dramatic win: the metal feed (one pass) scraps the wafer on LEAKAGE while V_t reads fine."""
    r = compute()
    by_grade = dict(zip(r.ladder, zip(r.leak_by_grade, r.vt_by_grade, r.yield_by_grade)))
    # Clean/EGS/solar clear the leakage window; only the metal-laden feed blows it.
    for g in ("clean", "EGS", "solar"):
        leak, _, y = by_grade[g]
        assert leak <= r.leak_spec_hi and y == 1.0
    metal_leak, metal_vt, metal_yield = by_grade["metal"]
    assert metal_leak > r.leak_spec_hi                       # leakage out of spec → scrapped
    assert metal_yield == 0.0
    # V_t is a BYSTANDER: the metal feed's V_t is in spec (the metals never touch doping/oxide charge),
    # and equals the clean V_t bit-for-bit (Na = 0, net-doping shift = 0).
    assert r.v_t_lo <= metal_vt <= r.v_t_hi
    assert metal_vt == r.clean_vt
    # The failure trail names the deep-level-metal SRH root cause — NOT Na/Q_ox, NOT defocus.
    assert "leakage" in r.dead_trail and "SRH" in r.dead_trail
    assert "Q_ox" not in r.dead_trail


def test_demo_more_passes_recover_the_wafer():
    """Purify harder: the metals' tiny k scrubs fast → one extra pass recovers lifetime + leakage."""
    r = compute()
    assert wafer_yield(r.dead_wafer) == 0.0                  # one pass: leaky, scrapped
    assert wafer_yield(r.recovered_wafer) == 1.0            # two passes: recovered
    # Leakage vs passes: out of spec at one pass, back under it for ≥2 passes (and lifetime climbs).
    assert r.leak_by_pass[0] > r.leak_spec_hi
    assert all(lk <= r.leak_spec_hi for lk in r.leak_by_pass[1:])
    assert r.tau_us_by_pass[-1] > r.tau_us_by_pass[0]        # lifetime recovers toward the bulk value


def test_lifetime_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import lifetime_figure

    r = compute()
    fig = lifetime_figure(r)
    assert len(fig.axes) >= 3                               # scaling / leakage-ladder / rework panels
    plt.pyplot.close(fig)
