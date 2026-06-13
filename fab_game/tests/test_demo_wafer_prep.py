"""Integration test for the G3 wafer-prep demo (the demo IS the integration check).

The wafer-prep demo wires the new defect-limited yield physics (:mod:`chip.wafer_prep`) through the
harness into the particle-map artifact. Its ``compute`` is the end-to-end check that the
scatter → functional-yield + the geometry scrap/re-polish chain holds together — asserted on the
robust thesis (the placement converges to the cited law; the dirty line kills dies; the TTV scrap
recovers by re-polish), not brittle exact numbers (the yield law is pinned in ``test_wafer_prep.py``,
the placement/geometry wiring in ``test_defects.py`` / ``test_geometry.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game import wafer_yield
from fab_game.demo_wafer_prep import compute


def test_demo_particle_map_kills_dies_functionally():
    """The dirty-line wafer scatters killers → some dies dead functionally, yield < 1 (the map)."""
    r = compute()
    w = r.dirty_wafer
    assert sum(len(d.defects) for d in w.dies) > 0          # particles landed
    killed = [d for d in w.dies if d.killed_by_defect]
    assert killed and all(d.verdict.failed for d in killed)  # caught a killer ⇒ functional fail
    assert wafer_yield(w) < 1.0


def test_demo_placement_converges_to_the_cited_poisson_law():
    """The empirical defect yield sweep hugs the cited exp(−D₀·A) curve — the headline G3 thesis."""
    r = compute()
    assert r.empirical_yields[0] == 1.0 and r.poisson_yields[0] == 1.0   # D₀=0 → perfect, both
    # Every swept density: the placement mean sits within a loose tolerance of the cited law.
    for emp, law in zip(r.empirical_yields, r.poisson_yields):
        assert emp == pytest.approx(law, abs=0.03)
    # And both fall monotonically with density (the defect-limited yield curve).
    assert list(r.poisson_yields) == sorted(r.poisson_yields, reverse=True)


def test_demo_geometry_scrap_recovers_by_repolish_at_a_thickness_cost():
    """A weak CMP scraps the wafer on TTV; the re-polish recovers it, having eaten thickness."""
    r = compute()
    assert wafer_yield(r.scrap_wafer) == 0.0                # scrapped on flatness
    assert wafer_yield(r.repolished_wafer) == 1.0           # re-polish recovered it
    assert r.repolished_wafer.geometry.thickness_um < r.scrap_wafer.geometry.thickness_um


def test_wafer_prep_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import wafer_prep_figure

    r = compute()
    fig = wafer_prep_figure(r)
    assert len(fig.axes) >= 3                               # particle map / yield curve / geometry panels
    plt.pyplot.close(fig)
