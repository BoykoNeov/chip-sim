"""Integration test for the A2 OSF-ring demo (the demo IS the integration check).

The A2 demo shows the OSF ring as CG-2 made radial: a radial ``G(r)`` makes ``ξ(r) = V/G(r)`` fall from
centre to edge, crossing the cited ``ξ_t`` at the ring; the reused (monotone) void density then peaks at
the centre and is zero past the ring, so the wafer map is a **COP-degraded vacancy core + a clean
interstitial rim** (the core mortality modest, the rim provably clean) — the ring is the *boundary* where
the kills stop, not a band of kills.

Asserted on the robust, **honest** theses — the ring *location* (``ξ(r_OSF)=ξ_t``) and the topology
signs (the tight legs), and the kills-stop-at-the-ring direction — not brittle magnitudes (the physics
is pinned in ``chip/tests/test_czochralski.py`` and the wiring in ``test_osf_ring.py``). The figure is
**not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke test only.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_osf_ring import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the pipeline wafer-map run is the costly part)."""
    return compute()


def test_demo_radial_criterion_falls_and_crosses_at_the_ring(r):
    """Panel 1: ξ(r)=V/G(r) falls monotonically from centre to edge (G rises outward), and the OSF ring
    sits exactly where ξ(r_OSF)=ξ_t — the tight, coefficient-robust location."""
    xi = np.asarray(r.xi_of_r)
    assert xi[0] > r.xi_t > xi[-1]                           # vacancy centre, interstitial edge
    assert np.all(np.diff(xi) < 0.0)                         # ξ(r) strictly falls outward
    assert 0.0 < r.ring_radius < 1.0
    # ξ at the ring radius equals ξ_t (interpolated off the sweep — the definitional crossing).
    xi_at_ring = float(np.interp(r.ring_radius, r.r_grid, r.xi_of_r))
    assert xi_at_ring == pytest.approx(r.xi_t, abs=2e-3)
    assert r.zones == ("vacancy", "interstitial")            # the topology signs


def test_demo_consequence_kills_peak_at_centre_and_stop_at_the_ring(r):
    """Panel 2 (the headline): the void density is monotone in ξ → it PEAKS at the centre and is ZERO at
    and beyond the ring; the per-die survival climbs from the degraded core to a clean rim (exactly 1 past
    the ring). The ring is the boundary where the kills stop, not a ring of kills."""
    dens = np.asarray(r.density_of_r)
    surv = np.asarray(r.survival_of_r)
    assert dens[0] > 0.0                                     # COP-degraded vacancy core (centre)
    assert all(a >= b for a, b in zip(dens, dens[1:]))       # density monotone non-increasing (a guard)
    assert surv[0] < 1.0                                     # the core loses dies
    assert all(a <= b for a, b in zip(surv, surv[1:]))       # survival monotone non-decreasing
    assert surv[-1] == pytest.approx(1.0)                    # clean interstitial rim
    # Past the ring the density is exactly zero (the kills have stopped) → survival is exactly 1.
    past = np.asarray(r.r_grid) >= r.ring_radius
    assert np.all(dens[past] == 0.0)
    assert np.all(surv[past] == pytest.approx(1.0))


def test_demo_wafer_map_kills_the_core_and_spares_the_rim(r):
    """Panel 3 (the consumer): on a clean line the radial growth kills dies **only** in the vacancy core
    — the rim is provably clean (zero grown-in density past the ring) — and kills do happen. The
    edge-vs-centre yield non-uniformity made physical on the per-die G3 map."""
    assert r.rim_killed == 0                                 # the interstitial rim survives
    assert r.core_killed > 0                                 # the vacancy core loses dies
    assert r.core_dies > 0 and r.rim_dies > 0               # the ring genuinely splits the wafer
    # Cross-check against the dies directly: every killed die sits inside the ring radius.
    killed = [d for d in r.wafer.dies if d.killed_by_defect]
    assert killed and all(d.radius_frac < r.ring_radius for d in killed)


def test_osf_ring_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import osf_ring_figure

    fig = osf_ring_figure(r)
    assert len(fig.axes) >= 3                                # criterion / consequence / wafer-map panels
    plt.pyplot.close(fig)
