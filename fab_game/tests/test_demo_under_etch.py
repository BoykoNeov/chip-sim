"""Integration test for the D1 demo (the demo IS the integration check).

The D1 demo shows under-etch → residual film → a bridging short: the residual rises through the origin
(UE=0 is the seam), the yield steps off a functional cliff as the residual crosses the bridge threshold
(the CD untouched), and the etch process window is bracketed by a short (under-etch) and an open
(over-etch CD collapse). Asserted on the robust, **honest** theses — the *direction* and the window
shape, not brittle numbers (the physics is pinned in ``chip/tests/test_etch_deposition.py`` and the
wiring in ``test_etch.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game.demo_under_etch import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-point pipeline runs are the costly part)."""
    return compute()


def test_demo_residual_through_origin_and_crosses_threshold(r):
    """Panel 1: residual = UE·film starts at 0 (UE=0 — the seam), rises linearly, and a thicker film
    reaches the bridge threshold at a smaller under-etch fraction."""
    for h in r.films_nm:
        res = list(r.residual_by_film[h])
        assert res[0] == 0.0                                     # UE=0 ⇒ residual 0 (the seam)
        assert res == sorted(res)                               # monotone rising with UE
    # A thicker film crosses the (flagged) threshold sooner (at a smaller UE).
    thin, thick = min(r.films_nm), max(r.films_nm)
    def first_cross(h):
        return next(u for u, v in zip(r.ue_sweep, r.residual_by_film[h]) if v > r.bridge_threshold_nm)
    assert first_cross(thick) < first_cross(thin)


def test_demo_bridging_cliff_is_a_functional_kill(r):
    """Panel 2: the yield steps 100 % → 0 % as the residual crosses the threshold, and the CD is
    UNTOUCHED throughout (under-etch is a functional short, not a CD shift)."""
    assert r.yield_vs_ue[0] == 1.0                              # UE=0 (seam) → full yield
    assert r.yield_vs_ue[-1] == 0.0                            # deep under-etch → bridged → dead
    assert r.yield_vs_ue == tuple(sorted(r.yield_vs_ue, reverse=True))   # monotone cliff (never recovers)
    assert max(r.cd_vs_ue) - min(r.cd_vs_ue) < 1e-9            # CD flat — a functional, not parametric, kill
    # The cliff sits where residual = UE·film crosses the threshold.
    assert r.ue_bridge_onset == pytest.approx(r.bridge_threshold_nm / r.nominal_film_nm)


def test_demo_process_window_is_bracketed_by_a_short_and_an_open(r):
    """Panel 3: the in-spec window sits between an under-etch SHORT (left, bridged) and an over-etch
    OPEN (right, CD collapse) — endpoint control is bracketed both ways."""
    x = list(r.etch_axis)
    y = list(r.yield_vs_etch)
    # A good window exists in the middle, and both extremes are dead (the bracketing).
    assert any(yi >= 1.0 for yi in y)                          # a non-empty in-spec window
    assert y[0] == 0.0 and y[-1] == 0.0                        # deep under-etch and deep over-etch both die
    assert r.window_lo > x[0] and r.window_hi < x[-1]         # the window is interior (bracketed)
    # The left edge dies by a BRIDGE (short); the right edge dies by CD collapse (open, not bridged).
    assert r.bridged_vs_etch[0] is True                       # under-etch extreme → bridged short
    assert r.bridged_vs_etch[-1] is False                     # over-etch extreme → an open, not a bridge
    assert r.cd_vs_etch[-1] < r.cd_lo                         # the over-etch extreme collapsed the CD


def test_under_etch_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import under_etch_figure

    fig = under_etch_figure(r)
    assert len(fig.axes) >= 3                                  # residual / cliff / process-window panels
    plt.pyplot.close(fig)
