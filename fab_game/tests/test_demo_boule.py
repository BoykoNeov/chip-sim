"""Integration test for the G2 boule demo (the demo IS the integration check).

The boule demo wires the new Scheil physics (:mod:`chip.czochralski`) through the validated back end
into the batch-down-the-boule artifact. Its ``compute`` is the end-to-end check that the boule →
slice → device → spec chain holds together — asserted on the robust thesis (the seed reproduces the
demo, the tail is scrapped by rising substrate doping), not brittle exact numbers (the Scheil maths
are pinned in ``test_czochralski.py``, the wiring in ``test_boule.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from chip import demo_device

from fab_game.demo_boule import compute


def test_demo_seed_slice_matches_demo_device():
    """The first slice (z=0) is the demo_device substrate exactly — the boule adds no physics there."""
    r = compute()
    assert r.batch.z_positions[0] == 0.0
    assert r.batch.channel_N_As[0] == demo_device.CHANNEL_N_A == 1.0e17


def test_demo_shows_the_scheil_spread_and_scraps_the_tail():
    """Down the boule N_A and V_t rise and the tail leaves the V_t window — the G2 story holds."""
    r = compute()
    b = r.batch
    # The Scheil walk: substrate doping and device V_t both rise strictly toward the tail.
    vts = [b.mean_V_t(w) for w in b.wafers]
    assert b.channel_N_As[-1] > b.channel_N_As[0]
    assert vts[-1] > vts[0]
    # The seed passes its V_t window; the tail's V_t has left it (scrapped) — the consequence.
    assert r.v_t_lo <= vts[0] <= r.v_t_hi
    assert vts[-1] > r.v_t_hi
    assert r.scrap_z is not None and 0.0 < r.scrap_z < 1.0
    assert b.yields[0] == 1.0 and b.yields[-1] == 0.0


def test_boule_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import boule_figure

    r = compute()
    fig = boule_figure(r)
    assert len(fig.axes) >= 3                          # Scheil / V_t-window / yield panels
    plt.pyplot.close(fig)
