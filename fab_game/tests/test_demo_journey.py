"""Integration test for the journey demo (the demo IS the integration check — ADR 0002/0005).

The phase-1 journey demo wires the staged scaffold + the purification stage through the validated line:
``compute`` is the end-to-end check that the refine → forecast (band + channel) → commit → finish chain
holds together. Asserted on the robust thesis (the arc walks dead → ring → clean; finish scores a refined
feed; the metal feed dies on the *leakage* channel, not V_t), not brittle numbers (the mechanics are
pinned in ``test_journey.py``, the physics in the chip/contamination suites). The figure is a "builds
without error" smoke test only.
"""
from __future__ import annotations

import pytest

from fab_game.demo_journey import compute


def test_demo_arc_walks_dead_to_ring_to_clean():
    """The showcase: a raw solar feed is scrapped, a fractional refine lands the graded ring, more → clean."""
    r = compute()
    assert r.bands[0] == "dead"                              # raw feed: Na out of spec → scrapped
    assert "ring" in r.bands                                 # a graded ring in the middle (the rework band)
    assert r.bands[-1] == "clean"                            # refined enough: clean
    assert r.yields[-1] == 1.0 and r.yields[-1] >= r.yields[0]
    assert 0.0 < r.ring_forecast.yield_ < 1.0               # the ring is a partial wafer
    assert "V_t" in (r.ring_forecast.channel or "")         # …failing on the mobile-ion V_t channel


def test_demo_finish_runs_and_scores_a_refined_feed():
    """Commit + finish: the refined feed runs the whole line → a full wafer → a scored card."""
    r = compute()
    assert r.finish_result.yield_ == 1.0
    assert r.finish_score.n_good > 0
    assert any("committed purification" in line for line in r.log)   # the accumulator write is logged


def test_demo_metal_contrast_dies_on_leakage_not_vt():
    """The other channel: a metal feed reads fine on V_t (Na = 0) yet is dead on junction leakage."""
    r = compute()
    assert r.metal_forecast.band == "dead"
    assert "leakage" in (r.metal_forecast.channel or "").lower()


def test_journey_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import journey_figure

    fig = journey_figure(compute())
    assert len(fig.axes) >= 3                                # trajectory / arc / wafer-map panels
    plt.pyplot.close(fig)
