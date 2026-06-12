"""Determinism (ADR 0005 §5) — a fixed (seed, recipe, variation) reproduces the wafer exactly.

All randomness flows from one seeded ``numpy.random.default_rng`` consumed in fixed die order, so
the run is a reproducible roguelike "seed." Two runs with the same inputs must be **identical**
(field-by-field equality on the immutable :class:`WaferState`); a *different* seed must actually
move the wafer (proving the RNG is wired, not ignored).
"""
from __future__ import annotations

from fab_game import DEFAULT_RECIPE, NO_VARIATION, Variation, run_line
from fab_game.recipe import LithoKnobs, Recipe


def test_same_seed_same_wafer():
    """Identical (seed, recipe, variation) → identical WaferState (the determinism contract)."""
    a = run_line(DEFAULT_RECIPE, seed=7, variation=Variation(), grid_n=5)
    b = run_line(DEFAULT_RECIPE, seed=7, variation=Variation(), grid_n=5)
    assert a == b
    assert [d.cd_nm for d in a.dies] == [d.cd_nm for d in b.dies]
    assert [d.verdict for d in a.dies] == [d.verdict for d in b.dies]


def test_different_seed_moves_the_wafer():
    """A different seed perturbs the dies differently — the RNG genuinely drives the variation."""
    a = run_line(DEFAULT_RECIPE, seed=1, variation=Variation(), grid_n=5)
    b = run_line(DEFAULT_RECIPE, seed=2, variation=Variation(), grid_n=5)
    assert [d.cd_nm for d in a.dies] != [d.cd_nm for d in b.dies]


def test_no_variation_is_seed_independent():
    """With variation off, the wafer does not depend on the seed (no randomness consumed)."""
    a = run_line(DEFAULT_RECIPE, seed=1, variation=NO_VARIATION, grid_n=5)
    b = run_line(DEFAULT_RECIPE, seed=999, variation=NO_VARIATION, grid_n=5)
    assert [d.cd_nm for d in a.dies] == [d.cd_nm for d in b.dies]
    assert [d.V_t for d in a.dies] == [d.V_t for d in b.dies]


def test_recipe_changes_the_outcome():
    """A different knob (defocus) changes the scored wafer — the knob is actually consumed."""
    good = run_line(DEFAULT_RECIPE, seed=3, variation=Variation(), grid_n=5)
    bad = run_line(Recipe(litho=LithoKnobs(defocus_nm=200.0)), seed=3, variation=Variation(), grid_n=5)
    assert [d.nils for d in good.dies] != [d.nils for d in bad.dies]
