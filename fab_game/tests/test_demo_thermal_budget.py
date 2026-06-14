"""Integration test for the E1 demo (the demo IS the integration check).

The E1 demo shows a spike/RTA anneal's thermal budget → a shallower junction: the diffusion budget
``∫D(T(t))dt`` accrues in a narrow window near the peak (the Arrhenius collapse), so a faster ramp
deposits less budget → a shallower ``x_j`` (and higher ``R_s``), and the equivalent isothermal time
``t_eq`` shrinks like ``1/β`` — tracked by the ``D0``-independent Laplace closed form. Asserted on the
robust theses (the *concentration* of the budget, the monotone directions, the Laplace match), not
brittle numbers (the physics is pinned in ``chip/tests/test_diffusion_dopant.py`` — the seam, the
equivalence-inverse, conservation, and the Laplace leg).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_thermal_budget import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-ramp-rate pipeline solves are the cost)."""
    return compute()


def test_demo_budget_accrues_near_the_peak(r):
    """Panel 1: the cumulative budget rises 0 → 1, monotone, and is CONCENTRATED near the peak — the
    top 50 °C carries the large majority of ∫D dt while spanning only a small fraction of the clock
    (the Arrhenius collapse), and the representative spike is a multi-× clock-vs-budget collapse."""
    frac = np.asarray(r.cumulative_budget_frac)
    T = np.asarray(r.T_profile)
    assert frac[0] == 0.0 and frac[-1] == pytest.approx(1.0)
    assert np.all(np.diff(frac) >= -1e-12)                       # monotone nondecreasing
    inc = np.diff(frac)
    Tmid = 0.5 * (T[1:] + T[:-1])
    top = Tmid >= r.peak_C - 50.0
    assert inc[top].sum() > 0.6                                  # >60 % of the budget in the top 50 °C
    assert inc[top].sum() > 3.0 * top.mean()                     # budget far more concentrated than time
    assert r.ref_duration_s > 3.0 * r.ref_t_eq_s                # the clock-vs-budget collapse (≈7×)


def test_demo_faster_ramp_gives_shallower_junction(r):
    """Panel 2: faster ramp → less budget → shallower x_j and higher R_s (monotone), every spike
    shallower than the isothermal baseline (its whole point — a smaller budget at a hotter peak)."""
    x_j = list(r.x_j_um)
    R_s = list(r.R_s)
    assert x_j == sorted(x_j, reverse=True)                      # x_j falls as the ramp steepens
    assert R_s == sorted(R_s)                                    # R_s rises (shallower, less total dose deep)
    assert all(x < r.x_j_iso_um for x in x_j)                    # all spikes shallower than the baseline
    assert r.R_s_iso < min(R_s)                                  # the baseline (deeper) has the lowest R_s


def test_demo_equivalent_time_collapses_and_matches_laplace(r):
    """The t_eq collapse: the equivalent isothermal time shrinks with ramp rate (∝1/β) and is far below
    the clock time; the D0-independent Laplace closed form tracks the exact (trapezoid) budget to a few %."""
    t_eq = list(r.t_eq_numeric_s)
    assert t_eq == sorted(t_eq, reverse=True)                    # t_eq falls with ramp rate
    assert all(te < dur for te, dur in zip(t_eq, r.durations_s)) # t_eq ≪ the clock time, every rate
    max_rel = max(abs(n - l) / l for n, l in zip(r.t_eq_numeric_s, r.t_eq_laplace_s))
    assert max_rel < 0.10                                        # Laplace ≈ exact (~5 %)


def test_thermal_budget_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import thermal_budget_figure

    fig = thermal_budget_figure(r)
    assert len(fig.axes) >= 2                                    # budget-accrual + ramp-sweep panels
    plt.pyplot.close(fig)
