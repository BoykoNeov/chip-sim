"""Integration test for the CG-1 demo (the demo IS the integration check).

The CG-1 demo wires the new Burton–Prim–Slichter ``k_eff`` (:mod:`chip.czochralski`) through the
``pull_rate_mm_min`` knob into the boule and shows the consequence: pulling faster flattens the axial
doping and so the device ``V_t`` walk down the boule. Asserted on the robust, **honest** thesis —
``k_eff`` rises with pull from ``k₀`` toward 1, the flattening at realistic Si pull is *modest*, and the
``V_t`` walk shrinks monotonically — not brittle numbers (the physics is pinned in
``chip/tests/test_czochralski.py``). This is a physics-consequence demo, **not** a score comparison
(CG-1 has no in-model cost — that is CG-2).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game.demo_crystal_growth import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-pull-rate batch runs are the costly part)."""
    return compute()


def test_demo_keff_rises_from_k0_toward_one_modestly_at_realistic_pull(r):
    """k_eff starts at k₀ (zero pull = the well-mixed seam), rises monotonically toward 1, and is only
    *modestly* above k₀ at the realistic-Si-pull edge — boron barely segregates (the honest magnitude)."""
    assert r.keff_sweep[0] == pytest.approx(r.k0)             # zero pull → k₀ exactly (the seam point)
    assert list(r.keff_sweep) == sorted(r.keff_sweep)        # monotone increasing in pull rate
    assert r.keff_sweep[-1] > 0.97                            # the high-pull end approaches complete trapping
    # The load-bearing honesty: at realistic Si pull the lift is modest (k₀ ≈ 0.80 → < ~0.85).
    assert r.k0 < r.realistic_keff_max < 0.88


def test_demo_faster_pull_flattens_the_vt_walk(r):
    """The consequence: the V_t walk (seed → tail) shrinks as pull rate rises — equilibrium walks the
    furthest out, the faster pulls flatten it (the benefit side)."""
    walks = [r.v_t_walk_by_pull[lbl] for lbl in r.v_t_by_pull]   # in DEMO_PULLS order (slow → fast)
    assert walks[0] > walks[1] > walks[2] > 0.0               # monotonically flatter, still rising (k<1)
    # The equilibrium boule's tail exits the spec ceiling; the fastest demo pull keeps it in.
    labels = list(r.v_t_by_pull)
    assert r.v_t_by_pull[labels[0]][-1] > r.v_t_hi            # equilibrium tail out of spec
    assert r.v_t_by_pull[labels[-1]][-1] <= r.v_t_hi          # fast-pull tail back in spec


def test_demo_profiles_share_the_seed_and_flatten_at_the_tail(r):
    """Every pull rate's boule has the SAME seed-end doping (the seam) and a lower tail for faster pull."""
    labels = list(r.n_a_by_pull)
    seeds = {r.n_a_by_pull[lbl][0] for lbl in labels}
    assert len(seeds) == 1                                    # all share the seed-end N_A (pinned)
    # The tail (last z) is progressively lower as pull rises (flatter profile).
    tails = [r.n_a_by_pull[lbl][-1] for lbl in labels]
    assert tails[0] > tails[1] > tails[2]


def test_crystal_growth_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import crystal_growth_figure

    fig = crystal_growth_figure(r)
    assert len(fig.axes) >= 3                                 # k_eff / profile / V_t-walk panels
    plt.pyplot.close(fig)
