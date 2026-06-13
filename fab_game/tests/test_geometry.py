"""Wafer geometry (G3) — the TTV/bow scrap gate and the re-polish rework (ADR 0005 §5 mechanics).

Geometry is a **wafer-level** property (the §3 thickness/TTV/bow field): out of spec scraps the
whole wafer (a front-of-line flatness reject). The re-polish rework recovers a TTV scrap by removing
more silicon — **at the cost of thickness** (the plan's "re-polish eats thickness"), but it cannot
fix bow (CMP planarizes TTV, not bow) and it cannot remove a killer particle. These pin the
bookkeeping (good+bad=total, accounting closes) on a wafer-level rework.
"""
from __future__ import annotations

from fab_game import DEFAULT_RECIPE, NO_VARIATION, Variation, run_line, wafer_yield
from fab_game.pipeline import rework_polish
from fab_game.recipe import Recipe, WaferPrepKnobs
from fab_game.spec import DEFAULT_SPECS


def test_nominal_geometry_is_in_spec_and_recorded():
    w = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    g = w.geometry
    assert g is not None
    assert DEFAULT_SPECS.geometry.check(g) is None           # nominal wafer is NOT scrapped (the seam)
    assert g.thickness_um == 740.0 and g.ttv_um < DEFAULT_SPECS.geometry.ttv_um.hi


def test_bad_cmp_scraps_the_whole_wafer_on_ttv():
    # A weak CMP leaves the TTV above the flatness window → every die fails functionally (yield 0),
    # all citing the geometry scrap (not a parametric reason).
    bad = Recipe(wafer_prep=WaferPrepKnobs(slice_ttv_um=4.0, cmp_ttv_improvement=0.5))   # → TTV 2.0 µm
    w = run_line(bad, seed=0, variation=Variation(), grid_n=5)
    assert w.geometry.ttv_um > DEFAULT_SPECS.geometry.ttv_um.hi
    assert wafer_yield(w) == 0.0
    assert all(d.verdict.failed and any("TTV" in r for r in d.verdict.reasons) for d in w.dies)


def test_high_bow_scraps_the_wafer():
    bad = Recipe(wafer_prep=WaferPrepKnobs(slice_bow_um=60.0))                            # > 40 µm window
    w = run_line(bad, seed=0, variation=NO_VARIATION, grid_n=3)
    assert wafer_yield(w) == 0.0
    assert all(any("bow" in r for r in d.verdict.reasons) for d in w.dies)


def test_rework_polish_recovers_a_ttv_scrap_and_eats_thickness():
    bad = Recipe(wafer_prep=WaferPrepKnobs(slice_ttv_um=4.0, cmp_ttv_improvement=0.5))   # TTV 2.0 → scrap
    w = run_line(bad, seed=0, variation=NO_VARIATION, grid_n=5)
    good_before = sum(d.verdict.passed for d in w.dies)
    assert good_before == 0                                   # scrapped: nothing passed

    w2 = rework_polish(w, extra_removal_um=40.0, extra_ttv_improvement=0.9)
    good_after = sum(d.verdict.passed for d in w2.dies)
    assert w2.geometry.ttv_um < DEFAULT_SPECS.geometry.ttv_um.hi   # back in flatness spec
    assert w2.geometry.thickness_um < w.geometry.thickness_um      # re-polish ate thickness
    # Accounting closes: the rework record's recovery reconciles with the yield change.
    rec = w2.rework_log[-1]
    assert rec.step == "polish"
    assert rec.n_recovered == good_after - good_before
    assert good_after > good_before                          # the scrap was recovered
    assert w2.n_dies == w.n_dies                             # no die created/destroyed


def test_rework_polish_cannot_fix_bow():
    # CMP planarizes TTV, not bow — a bow scrap is NOT recoverable by re-polishing.
    bad = Recipe(wafer_prep=WaferPrepKnobs(slice_bow_um=60.0))
    w = run_line(bad, seed=0, variation=NO_VARIATION, grid_n=3)
    w2 = rework_polish(w, extra_removal_um=40.0, extra_ttv_improvement=0.9)
    assert wafer_yield(w2) == 0.0                            # still scrapped (bow unchanged)
    assert w2.geometry.bow_um == w.geometry.bow_um


def test_rework_polish_over_removal_raises():
    import pytest
    w = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    with pytest.raises(ValueError):
        rework_polish(w, extra_removal_um=10_000.0)          # eats the whole wafer


def test_rework_polish_does_not_resurrect_a_killer_defect():
    # A die killed by a particle stays dead after a re-polish (geometry rework ≠ defect removal).
    dirty = Recipe(wafer_prep=WaferPrepKnobs(
        defect_density=0.3, slice_ttv_um=4.0, cmp_ttv_improvement=0.5))   # both a TTV scrap AND dirt
    w = run_line(dirty, seed=2, variation=Variation(), grid_n=7)
    w2 = rework_polish(w, extra_removal_um=40.0, extra_ttv_improvement=0.9)
    # The TTV scrap lifts, but dies that caught a killer particle are still failed functionally.
    killed = [d for d in w2.dies if d.killed_by_defect]
    assert killed                                            # the dirty line did place some
    assert all(d.verdict.failed for d in killed)
