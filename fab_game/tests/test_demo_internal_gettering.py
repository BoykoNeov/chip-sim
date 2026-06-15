"""Integration test for the S4 demo (the demo IS the integration check).

The S4 demo shows crucible oxygen's **dual-use**: above the cited precipitation threshold the gettering
efficiency switches on (the asset, leakage down), while the same oxygen makes thermal donors (the
liability, V_t down); the wafer yield is a single two-sided hump. Asserted on the robust, **honest**
theses — the two-sided window, the orthogonal directions, the monotonicities — not brittle numbers (the
physics is pinned in ``chip/tests/test_{czochralski,purification}.py`` and the wiring in
``test_internal_gettering.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_internal_gettering import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-[O_i] pipeline runs are the cost)."""
    return compute()


def test_demo_two_faces_switch_on_at_the_threshold(r):
    """Panel 1: gettering η is 0 below the cited precipitation threshold and rises monotonically above it;
    the thermal donors rise monotonically with oxygen too — the two faces of the same knob."""
    o = np.asarray(r.oxygen_fine)
    eff = np.asarray(r.efficiency_fine)
    ntd = np.asarray(r.donor_fine)
    assert np.all(eff[o <= r.critical_oxygen] == 0.0)            # nothing below the threshold (the seam)
    assert np.any(eff[o > r.critical_oxygen] > 0.0)             # switches on above it
    assert list(eff) == sorted(eff)                             # η monotone non-decreasing in [O_i]
    assert list(ntd) == sorted(ntd)                            # donors monotone non-decreasing in [O_i]
    assert eff.max() < 1.0                                      # never perfect (the flagged ceiling)


def test_demo_window_is_two_sided_leakage_below_vt_above(r):
    """Panel 2 (the headline): leakage falls (gettering) while V_t falls (donors); a non-empty PASS band
    sits between a leakage-limited low edge and a V_t-limited high edge."""
    assert r.pass_lo is not None and r.pass_hi is not None      # the Goldilocks band is non-empty
    leak = np.asarray(r.leak_pipe)
    vt = np.asarray(r.vt_pipe)
    o = np.asarray(r.oxygen_pipe)
    # The low edge fails on LEAKAGE (V_t fine), the high edge fails on V_t (leakage fine) — two-sided.
    assert leak[0] > r.leak_hi and r.v_t_lo <= vt[0] <= r.v_t_hi
    assert vt[-1] < r.v_t_lo and leak[-1] <= r.leak_hi
    # Inside the band both pass.
    inside = (o >= r.pass_lo) & (o <= r.pass_hi)
    assert np.all(leak[inside] <= r.leak_hi) and np.all(vt[inside] >= r.v_t_lo)


def test_demo_directions_are_orthogonal_and_monotone(r):
    """Both consequences point opposite ways: leakage DOWN (gettering), V_t DOWN (donors) — the trade-off
    on orthogonal channels. Leakage falls monotonically across the **verdict-relevant** region (gettering
    engaged AND V_t still passing); the two non-monotonicities outside it are the real, named secondary
    donor→N_A→depletion-width coupling (the forming-gas donors lower N_A, widening W ∝ 1/√N_A and nudging
    generation leakage up) — NOT the deferred over-precipitation U-shape — and both sit deep in
    already-failed territory (below the threshold leakage is ≫ spec; above the V_t crater the part is
    already scrapped), so they never touch the window."""
    vt = list(r.vt_pipe)
    assert vt == sorted(vt, reverse=True)                       # V_t falls monotonically (donors)
    assert r.base_leak > r.leak_hi                              # the feed genuinely needs gettering
    # In the region where the wafer could still pass — gettering on (O > threshold) AND V_t in window —
    # leakage falls strictly with oxygen (the gettering benefit, the verdict-relevant monotonicity).
    relevant = [lk for o, lk, v in zip(r.oxygen_pipe, r.leak_pipe, r.vt_pipe)
                if o > r.critical_oxygen and v >= r.v_t_lo]
    assert len(relevant) >= 3
    assert all(a > b for a, b in zip(relevant, relevant[1:]))   # strictly decreasing where it matters


def test_demo_yield_is_a_single_two_sided_hump(r):
    """Panel 3: the yield is 0 on the low-oxygen (leakage) side and 0 on the high-oxygen (V_t) side, with
    a passing interior — the dual-use window made a single curve."""
    y = np.asarray(r.yield_pipe)
    assert y[0] == 0.0 and y[-1] == 0.0                         # scrapped on both ends
    assert y.max() > 0.0                                        # but the interior wins


def test_internal_gettering_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import internal_gettering_figure

    fig = internal_gettering_figure(r)
    assert len(fig.axes) >= 3                                    # two-faces / Goldilocks / yield panels
    plt.pyplot.close(fig)
