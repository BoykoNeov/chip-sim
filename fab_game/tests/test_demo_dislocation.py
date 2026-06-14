"""Integration test for the A1 dislocation demo (the demo IS the integration check).

The A1 demo shows the interstitial side of Voronkov: a too-slow pull (``ξ < ξ_t``) grows in dislocations
that raise junction **leakage** (not yield), so the criterion is two-sided — too-fast costs yield (COP
voids), too-slow costs leakage — with the defect-free optimum **at** ``ξ_t``. The radial panel completes
A2: a void-prone vacancy core + a dislocation-leaky rim flanking the one clean OSF-ring annulus.

Asserted on the robust, **honest** theses — the two-sided structure, the V_t bystander (leakage, not the
threshold), and the leaky rim — not brittle magnitudes (the physics is pinned in
``chip/tests/test_{czochralski,lifetime}.py`` and the wiring in ``test_dislocation.py``). The figure is
**not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke test only.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_dislocation import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the pipeline runs are the costly part)."""
    return compute()


def test_demo_two_sided_window_leakage_below_voids_above(r):
    """Panel 1: leakage (the dislocation cost) rises as ξ falls below ξ_t; the COP void density (the
    vacancy cost) rises as ξ rises above it — a cost on both sides, clean only at the ξ_t optimum."""
    xi = np.asarray(r.xi_of_g)
    leak = np.asarray(r.leak_of_xi)
    void = np.asarray(r.void_of_xi)
    # Interstitial side (ξ < ξ_t): leakage is elevated and the void density is zero.
    below = xi < r.xi_t
    above = xi > r.xi_t
    assert np.all(void[below] == 0.0)                        # no voids on the interstitial side
    assert leak[below].max() > r.leak_spec_hi                # leakage blows the window at a deep slow pull
    # Vacancy side (ξ > ξ_t): voids are present and leakage is the clean baseline.
    assert np.all(void[above] > 0.0)                         # voids on the vacancy side
    assert leak[above].max() < 1.0                           # leakage baseline on the vacancy side
    # Leakage falls monotonically as ξ rises (toward the optimum) across the interstitial side.
    order = np.argsort(xi[below])
    assert all(a >= b for a, b in zip(leak[below][order], leak[below][order][1:]))


def test_demo_leakage_ladder_vt_is_a_flat_bystander(r):
    """Panel 2 (the isolation headline): leakage climbs to a scrap on the slow side, while V_t reads the
    SAME value across the whole ladder — slow pull leaks the diode, it does not move the threshold."""
    vt = np.asarray(r.vt_by_step)
    leak = np.asarray(r.leak_by_step)
    assert np.allclose(vt, vt[0])                            # V_t flat across the ladder (the bystander)
    assert r.v_t_lo <= vt[0] <= r.v_t_hi                     # …and in spec everywhere
    assert leak[0] < 1.0                                     # the vacancy/optimum end: baseline leakage
    assert leak[-1] > r.leak_spec_hi                         # the deep-slow end: out of spec
    assert r.yield_by_step[0] == 1.0 and r.yield_by_step[-1] == 0.0
    # The deep-slow scrap names the grown-in dislocations (a crystal-growth cause, not a metal/Na one).
    assert "DISLOCATION" in r.dead_trail and "leakage" in r.dead_trail
    assert "deep-level-metal" not in r.dead_trail


def test_demo_radial_map_leaky_rim_clean_ring_void_core(r):
    """Panel 3 (the A2 completion): on a clean line, the radial growth fails dies only in the interstitial
    RIM (on leakage); the vacancy CORE carries the void density (the yield cost), and the OSF ring is the
    clean annulus between. Every leakage scrap sits past the ring."""
    assert r.zones == ("vacancy", "interstitial")
    assert 0.0 < r.ring_radius < 1.0
    assert r.rim_leak_failed > 0                             # the dislocation-leaky rim loses dies…
    void = np.asarray(r.void_density_of_die)
    leak = np.asarray(r.leak_of_die)
    rad = np.array([d.radius_frac for d in r.wafer.dies])
    # The core carries voids and is NOT leaky; the rim carries leakage and NOT voids (complementary).
    core, rim = rad < r.ring_radius, rad >= r.ring_radius
    assert void[core].max() > 0.0 and np.all(void[rim] == 0.0)
    assert leak[rim].max() > r.leak_spec_hi and np.all(leak[core] < 1.0)
    # Every leakage scrap is a rim die past the ring (the clean annulus is not scrapped).
    scrapped = [d for d in r.wafer.dies if d.verdict.failed
                and any("leakage" in s for s in d.verdict.reasons)]
    assert scrapped and all(d.radius_frac >= r.ring_radius for d in scrapped)


def test_dislocation_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import dislocation_figure

    fig = dislocation_figure(r)
    assert len(fig.axes) >= 3                                # window / ladder / wafer-map panels
    plt.pyplot.close(fig)
