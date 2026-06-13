"""Integration test for the CG-2 demo (the demo IS the integration check).

The CG-2 demo shows the Voronkov V/G criterion as the in-model brake on pulling faster: the analytic
grown-in defect yield (the law the stochastic G3 scatter converges to) crosses at the V/I boundary,
pulling faster costs yield, and the combined CG-1-benefit × CG-2-cost peaks at the criterion boundary.
Asserted on the robust, **honest** theses — the *direction* (criterion-driven), not brittle numbers
(the physics is pinned in ``chip/tests/test_czochralski.py`` and the wiring in ``test_voronkov.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_voronkov import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-pull-rate batch runs are the costly part)."""
    return compute()


def test_demo_criterion_crosses_at_the_vi_boundary(r):
    """Panel 1: at fixed pull, raising the thermal gradient G raises the defect yield (less vacancy
    supersaturation) — ~0 in the deep-vacancy cool zone, →1 in the interstitial hot zone, crossing at
    G* = V/ξ_t. The *direction* is criterion-driven (the cited ξ_t), not the flagged coefficient."""
    ys = list(r.defect_yield_vs_g)
    assert ys == sorted(ys)                                  # monotone increasing in G
    assert ys[0] < 0.1                                       # cool zone (deep vacancy) → COP-killed
    assert ys[-1] == pytest.approx(1.0)                      # hot zone (interstitial) → defect-free
    assert r.g_boundary == pytest.approx(r.v_fixed / r.xi_t)  # G* = V/ξ_t
    assert r.realistic_regime == "vacancy"                   # realistic CZ is vacancy-rich (the honest anchor)


def test_demo_brake_faster_pull_lowers_yield_and_hotzone_tolerates_more(r):
    """Panel 2: the brake — the analytic defect yield falls monotonically as the pull rises (more COPs),
    and at every pull the engineered hot zone yields ≥ the baseline (a hotter G tolerates a faster pull)."""
    yb = list(r.defect_yield_baseline)
    assert yb == sorted(yb, reverse=True)                    # faster pull → lower yield
    # The hotter zone is never worse and is strictly better somewhere (it pushes the void onset out).
    assert all(yh >= ybi - 1e-12 for yh, ybi in zip(r.defect_yield_hotzone, yb))
    assert any(yh > ybi + 1e-6 for yh, ybi in zip(r.defect_yield_hotzone, yb))


def test_demo_unifier_combined_maximized_on_the_defect_free_plateau(r):
    """Panel 3 (the honest finding): the combined yield is MAXIMIZED on the defect-free plateau
    (V ≤ V*=ξ_t·G) then falls as voids switch on — but CG-1's parametric fraction is FLAT across this
    range, so the two do NOT trade off: CG-2's criterion ALONE sets the optimal pull. On yield the slow
    end of the plateau is no worse than the boundary (the boundary's edge is throughput, unmodeled)."""
    para = list(r.parametric_fraction)
    dfct = list(r.defect_survival)
    comb = list(r.combined_yield)
    assert dfct == sorted(dfct, reverse=True)                # CG-2 cost: defect survival falls with pull
    v = np.asarray(r.pull_unifier)
    on_plateau = v <= r.v_boundary_unifier + 1e-9
    assert on_plateau.sum() >= 2                             # the sweep resolves the plateau
    # No voids below V* (the criterion gate), and CG-1's parametric is flat there → the combined is flat
    # on the plateau (no interior peak; CG-1's benefit does not locate the optimum — CG-2 does).
    assert all(d == pytest.approx(1.0) for d, keep in zip(dfct, on_plateau) if keep)
    plateau_para = [p for p, keep in zip(para, on_plateau) if keep]
    assert max(plateau_para) - min(plateau_para) < 1e-9      # CG-1 parametric FLAT across the plateau
    # The optimum sits on the plateau (≤ V*), the slow end is no worse than the boundary (no trade-off),
    # and pulling well past the boundary is strictly worse.
    v_best = float(v[int(np.argmax(comb))])
    assert v_best <= r.v_boundary_unifier + 0.05
    i_bound = int(np.argmin(np.abs(v - r.v_boundary_unifier)))
    assert comb[0] >= comb[i_bound] - 1e-9                   # slow end ≥ boundary (CG-2-set, not CG-1)
    assert comb[-1] < max(comb)                              # past the boundary is worse


def test_voronkov_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import voronkov_figure

    fig = voronkov_figure(r)
    assert len(fig.axes) >= 3                                 # criterion / brake / unifier panels
    plt.pyplot.close(fig)
