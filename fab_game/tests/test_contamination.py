"""Contamination mechanics (ADR 0005 §5, G4) — purification scrubs the wafer, and it propagates.

The G4 wiring invariants (mechanics, not magnitudes): the feedstock grade is zone-refined into the
wafer-level :class:`chip.purification.Contamination` vector; a dirty grade's residual **mobile-ion
Na** poisons the gate oxide (``Q_ox``) and walks ``V_t`` out of its spec window → dead dies, traced
to the contamination; **more zone passes** (the plan's step-1 rework) scrubs the Na and recovers
yield; and a **clean grade is the seam** (no contamination → the ideal-oxide device unchanged).

Runs use ``NO_VARIATION`` so the contamination is the *only* signal (the G2/G3 move of isolating the
new effect from the G1 focus bowl): the wafer is uniform, so it bins all-pass or all-fail on V_t.
"""
from __future__ import annotations

from chip import czochralski as cz
from chip.purification import FEEDSTOCK_GRADES

from fab_game import (
    DEFAULT_RECIPE, NO_VARIATION, PurificationKnobs, Recipe, run_line, wafer_yield,
)
from fab_game.pipeline import diagnose


def _run(grade: str, passes: int):
    recipe = Recipe(purification=PurificationKnobs(grade=grade, zone_passes=passes))
    return run_line(recipe, seed=0, variation=NO_VARIATION, grid_n=3)


def test_clean_grade_is_the_seam_no_contamination():
    """The default clean grade → an all-zero contamination vector → full yield (the ideal-oxide device)."""
    w = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    assert w.contamination.is_clean
    assert wafer_yield(w) == 1.0


def test_wafer_carries_the_zone_refined_vector():
    """The wafer's contamination is the feedstock grade scrubbed by each species' cited k (one pass)."""
    w = _run("MGS", 1)
    feed = FEEDSTOCK_GRADES["MGS"]
    # Single pass leaves each species at k·C_feed (the exact leading-end value, reusing czochralski's k).
    assert w.contamination.Na == feed.Na * cz.SEGREGATION_K["Na"]
    assert w.contamination.Fe == feed.Fe * cz.SEGREGATION_K["Fe"]
    # The scrubbing contrast on the wafer itself: Fe scrubbed ~5 orders, Na far less (its k is larger).
    assert w.contamination.Fe / feed.Fe < w.contamination.Na / feed.Na


def test_dirty_feedstock_kills_yield_on_vt_and_names_the_cause():
    """A dirty MGS feed, one pass → residual Na → Q_ox → V_t out the bottom of its window → dead dies."""
    clean = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    dirty = _run("MGS", 1)
    assert wafer_yield(dirty) < wafer_yield(clean)          # contamination drops yield
    assert wafer_yield(dirty) == 0.0                        # uniform wafer: every die fails on V_t
    dead = next(d for d in dirty.dies if d.verdict.failed)
    assert any("V_t" in r for r in dead.verdict.reasons)    # the parametric cause is V_t
    # The failure trail names the contamination root cause (Q_ox from mobile-ion Na).
    trail = diagnose(dead)
    assert "purification" in trail and "Q_ox" in trail


def test_more_zone_passes_recovers_yield_the_rework():
    """Purifying harder (more zone passes) scrubs the Na and brings V_t back into spec — the rework."""
    one = _run("MGS", 1)
    two = _run("MGS", 2)
    assert wafer_yield(two) > wafer_yield(one)              # more passes → cleaner feed → yield recovers
    assert wafer_yield(two) == 1.0
    # The residual boron (k≈0.8, barely scrubbed) persists — its net-doping bump is the un-refinable
    # footnote, so the recovered V_t need not equal the pristine value (it sits slightly off).
    assert two.contamination.B > 0.0


def test_resistivity_is_coherent_with_the_effective_doping():
    """The wafer's reported resistivity tracks its *effective* doping — the two doping-derived fields
    never silently disagree (a dirty feed's residual-dopant net shift moves both, coherently)."""
    w = _run("MGS", 1)
    # channel_N_A is the effective doping (boule + residual shift); resistivity must be computed from it.
    assert w.resistivity_ohm_cm == cz.resistivity(w.channel_N_A, "B")
    # And the residual acceptor actually moved it off the pristine boule value (the gap is real, ~%).
    clean = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    assert w.channel_N_A > clean.channel_N_A                 # residual B raised the net doping
    assert w.resistivity_ohm_cm < clean.resistivity_ohm_cm   # …so resistivity dropped, coherently


def test_intermediate_grade_shifts_vt_but_can_still_pass():
    """A solar-grade feed shifts V_t down (Na present) but not out of spec — the graded, monotone story."""
    solar = _run("solar", 1)
    clean = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    v_solar = next(d.V_t for d in solar.dies if d.V_t is not None)
    v_clean = next(d.V_t for d in clean.dies if d.V_t is not None)
    assert v_solar < v_clean                                # Na shifts it down
    assert wafer_yield(solar) == 1.0                        # but still in spec (intermediate grade)
