"""Integration test for the CG-3 demo (the demo IS the integration check).

The CG-3 demo shows the Stefan interface balance capping the Voronkov ratio: ξ = V/G_s saturates at
ξ_max (latent heat couples G_s to the pull rate), so the grown-in COP cost is bounded — vs CG-2's
fixed-G runaway. Asserted on the robust theses — saturation, the linear G_s(V) coupling, the yield
floor — not brittle numbers (the physics is pinned in ``chip/tests/test_czochralski.py`` and the wiring
in ``test_stefan.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_stefan import compute


@pytest.fixture(scope="module")
def r():
    return compute()


def test_demo_xi_saturates_below_xi_max_vs_cg2_runaway(r):
    """Every Stefan-coupled ξ(V) rises monotonically with pull but stays strictly below ξ_max (the
    latent-heat cap), while CG-2's fixed-G ξ=V/G diverges past ξ_max. ξ_max is ~2–3× ξ_t."""
    assert 2.0 < r.xi_max / r.xi_t < 3.0
    for g_l in r.melt_grads:
        xi = list(r.xi_by_melt[g_l])
        assert xi == sorted(xi)                                  # ξ rises with pull
        assert max(xi) < r.xi_max                                # but stays below the cap (G_l > 0)
    assert max(r.xi_cg2_fixed) > r.xi_max                        # CG-2's fixed-G ξ runs past the cap


def test_demo_gs_rises_linearly_with_pull(r):
    """The coupling: G_s(V) is affine in pull (the latent term L·ρ·V/k_s — constant slope), so the
    second difference vanishes; it rises with pull and with the melt gradient."""
    for g_l in r.melt_grads:
        gs = np.asarray(r.gs_by_melt[g_l])
        assert gs[-1] > gs[0]                                    # rises with pull
        assert np.max(np.abs(np.diff(gs, 2))) < 1e-9            # affine (constant latent slope)
    # Higher melt gradient → higher G_s at every pull (the hot-zone lever).
    assert all(a < b for a, b in zip(r.gs_by_melt[r.melt_grads[0]], r.gs_by_melt[r.melt_grads[-1]]))


def test_demo_bounded_cost_floors_vs_collapse(r):
    """The bounded cost: the Stefan COP yield FLOORS (stays at/above the ξ_max floor) while CG-2's
    fixed-G yield COLLAPSES toward 0 — and the two agree at the reference pull (apples-to-apples)."""
    y3 = list(r.yield_cg3_ref)
    y2 = list(r.yield_cg2_fixed)
    assert all(y >= r.yield_floor - 1e-9 for y in y3)            # Stefan yield never falls below the floor
    assert r.yield_floor > 0.0                                   # the floor is a real, positive worst case
    assert y2[-1] < r.yield_floor                                # CG-2 fixed-G collapses below the floor
    assert y2[-1] < 0.05                                         # ...toward 0 at the fast end
    # The contrast is fair: G was frozen at its Stefan value at the reference pull, so the Stefan ξ and
    # the fixed-G ξ coincide there exactly (ξ_ref = V_ref/G_fixed) — verified on the demo's own fields.
    assert r.realistic_ratio == pytest.approx(1.0 / r.g_fixed)


def test_stefan_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import stefan_figure

    fig = stefan_figure(r)
    assert len(fig.axes) >= 3                                    # saturation / coupling / bounded-cost panels
    plt.pyplot.close(fig)
