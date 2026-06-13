"""Leakage mechanics (ADR 0005 §5, G4b) — deep-level metals poison the diode, and it propagates.

The G4b wiring invariants (mechanics, not magnitudes): the feedstock grade's deep-level **metals**
(Fe/Cu), surviving zone refining, drive the minority-carrier SRH lifetime → junction reverse leakage
(:mod:`chip.lifetime`) at the device read; a metal-laden feed walks the leakage **out of its spec
window** while ``V_t`` stays fine → dead dies, traced to the metal SRH (the device consequence net
doping cannot carry — the gap G4a named, now wired); **more zone passes** (the rework) scrub the tiny-k
metals fast and recover yield; and a **clean grade is the seam** (no metals → the baseline-leakage,
ideal-oxide device unchanged).

Runs use ``NO_VARIATION`` so the contamination is the *only* signal (the G2/G3/G4a move of isolating
the new effect): the wafer is uniform, so it bins all-pass or all-fail on leakage.
"""
from __future__ import annotations

from chip import czochralski as cz
from chip.purification import FEEDSTOCK_GRADES

from fab_game import (
    DEFAULT_RECIPE, NO_VARIATION, PurificationKnobs, Recipe, run_line, wafer_yield,
)
from fab_game.pipeline import diagnose


def _run(grade: str, passes: int, gn: int = 3):
    recipe = Recipe(purification=PurificationKnobs(grade=grade, zone_passes=passes))
    return run_line(recipe, seed=0, variation=NO_VARIATION, grid_n=gn)


def test_clean_grade_is_the_seam_baseline_leakage():
    """The default clean grade → no metals → the baseline lifetime/leakage → full yield (the seam)."""
    w = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    assert w.contamination.Fe == 0.0 and w.contamination.Cu == 0.0
    for d in w.dies:
        assert d.tau is not None and d.j_leak is not None    # the device computed lifetime/leakage
        assert d.j_leak_nA_cm2 < 1.0                          # baseline ≪ the nA/cm² window
    assert wafer_yield(w) == 1.0


def test_wafer_carries_the_zone_refined_metal_vector():
    """The wafer's metals are the feed scrubbed by each species' cited (tiny) k — one pass."""
    w = _run("metal", 1)
    feed = FEEDSTOCK_GRADES["metal"]
    assert w.contamination.Fe == feed.Fe * cz.SEGREGATION_K["Fe"]
    assert w.contamination.Cu == feed.Cu * cz.SEGREGATION_K["Cu"]
    # The metal feed is Na/dopant-clean — so the leakage story is isolated from the V_t story.
    assert w.contamination.Na == 0.0 and w.contamination.net_doping_shift == 0.0


def test_metal_feed_kills_yield_on_leakage_and_names_the_cause():
    """A metal-laden feed (one pass) → residual Fe/Cu → SRH → leakage out of spec → dead dies, V_t fine."""
    clean = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    dirty = _run("metal", 1)
    assert wafer_yield(dirty) == 0.0                         # uniform wafer: every die fails on leakage
    assert wafer_yield(dirty) < wafer_yield(clean)
    dead = next(d for d in dirty.dies if d.verdict.failed)
    assert any("leakage" in r for r in dead.verdict.reasons)   # the parametric cause is leakage…
    assert not any("V_t" in r for r in dead.verdict.reasons)   # …NOT V_t (the metals don't touch it)
    # V_t reads the clean value bit-for-bit (Na=0, net-doping shift=0 — the isolation).
    assert dead.V_t == next(d.V_t for d in clean.dies if d.V_t is not None)
    # The failure trail names the deep-level-metal SRH root cause (not Q_ox/Na, not defocus).
    trail = diagnose(dead)
    assert "leakage" in trail and "SRH" in trail and "Q_ox" not in trail


def test_more_zone_passes_recovers_yield_the_rework():
    """Purifying harder scrubs the tiny-k metals → lifetime/leakage recover — the rework."""
    one = _run("metal", 1)
    two = _run("metal", 2)
    assert wafer_yield(two) > wafer_yield(one)
    assert wafer_yield(two) == 1.0
    # The metals scrub by k² at the leading end (front-tracking) — orders of magnitude per extra pass.
    assert two.contamination.Fe < one.contamination.Fe < FEEDSTOCK_GRADES["metal"].Fe
    # A representative die's lifetime climbs back toward the bulk value as the metal is scrubbed.
    tau_one = next(d.tau for d in one.dies if d.tau is not None)
    tau_two = next(d.tau for d in two.dies if d.tau is not None)
    assert tau_two > tau_one


def test_intermediate_grade_raises_leakage_but_can_still_pass():
    """A solar-grade feed's once-refined residual metal raises leakage but stays inside the window —
    the graded, monotone story (and the binding seam constraint: an intermediate grade is not scrapped)."""
    solar = _run("solar", 1)
    clean = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    j_solar = next(d.j_leak for d in solar.dies if d.j_leak is not None)
    j_clean = next(d.j_leak for d in clean.dies if d.j_leak is not None)
    assert j_solar > j_clean                                 # residual metal raises leakage
    assert wafer_yield(solar) == 1.0                         # …but still in spec (intermediate grade)
