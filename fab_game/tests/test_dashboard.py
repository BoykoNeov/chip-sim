"""Smoke + mechanics test for the guided slider-driven slice (``fab_game.dashboard``).

The dashboard is the §9 "first" UX step: a thin, importable skin over the validated line that the
notebook drives with ``ipywidgets`` sliders. Because ``interact`` *captures* exceptions (a broken
call would leave the notebook green), the load-bearing run + summary must be tested **here**, not
only through the slider — the same discipline ``chip/tests/test_chip_notebook`` states.

What is asserted (mechanics, not magnitudes — ADR 0005 §5): the **seam** (default knobs ==
``DEFAULT_RECIPE`` → a clean wafer), **determinism** (a ``(seed, knobs)`` reproduces the wafer),
that the within-wafer ``Variation`` is **on** so the map carries real spatial structure (the
defocus edge ring), that yield is **monotone** in the dramatic knob, and that the failure trail
**names the cause**. The figure is a "builds without error" smoke test only (ADR 0002).
"""
from __future__ import annotations

import pytest

from fab_game import DEFAULT_RECIPE
from fab_game.dashboard import dashboard_recipe, dashboard_summary, run_dashboard


# --------------------------------------------------------------------------- #
# The seam — default knobs reproduce the nominal recipe and a clean wafer
# --------------------------------------------------------------------------- #
def test_default_recipe_is_the_seam():
    """At the default arguments every knob is the ``DEFAULT_RECIPE`` value — the dashboard recipe IS
    the nominal ``chip.demo_device`` recipe, so the guided slice opens on the validated seam."""
    assert dashboard_recipe() == DEFAULT_RECIPE


def test_default_run_is_a_clean_wafer():
    """The default (clean) recipe with the within-wafer variation on still prints every die: a 0 nm
    focus bowl is well inside the printability floor → 100 % yield (the clean baseline the player
    departs from)."""
    result = run_dashboard()
    assert result.yield_ == 1.0
    assert result.dead_dies == ()
    summary = dashboard_summary(result)
    assert "yield 100%" in summary
    assert "clean wafer" in summary


# --------------------------------------------------------------------------- #
# Determinism + the variation-on contract (the map must carry spatial structure)
# --------------------------------------------------------------------------- #
def test_deterministic_in_seed():
    """A ``(seed, knobs)`` pair reproduces the wafer exactly — the roguelike "seed" contract."""
    a = run_dashboard(defocus_nm=90.0, seed=3)
    b = run_dashboard(defocus_nm=90.0, seed=3)
    assert a.yield_ == b.yield_
    assert [d.verdict.passed for d in a.wafer.dies] == [d.verdict.passed for d in b.wafer.dies]


def test_variation_is_on_so_the_map_has_an_edge_ring():
    """The whole point of the live map: with ``Variation`` on, a partial defocus kills an **edge
    ring**, not a uniform flip — so the failed dies sit, on average, farther out than the survivors.
    (A ``NO_VARIATION`` run would make every die identical → an all-pass/all-fail map with no story.)"""
    result = run_dashboard(defocus_nm=90.0)
    passed = [d.radius_frac for d in result.wafer.dies if d.verdict.passed]
    failed = [d.radius_frac for d in result.wafer.dies if d.verdict.failed]
    assert passed and failed                                   # a partial kill (the ring), not a flip
    assert sum(failed) / len(failed) > sum(passed) / len(passed)


# --------------------------------------------------------------------------- #
# Propagation — yield is monotone in the dramatic knob; the trail names the cause
# --------------------------------------------------------------------------- #
def test_yield_is_monotone_in_defocus():
    """Sliding the focus knob walks the yield down: in focus → full wafer; a wipeout defocus → dead."""
    y0 = run_dashboard(defocus_nm=0.0).yield_
    y_mid = run_dashboard(defocus_nm=90.0).yield_
    y_hi = run_dashboard(defocus_nm=250.0).yield_
    assert y0 == 1.0
    assert y_hi == 0.0
    assert y0 > y_mid > y_hi


def test_summary_trail_names_defocus():
    """A defocus wipeout's failure trail names the litho focus error (NILS below the floor) — the
    "watch the failure trail" payoff."""
    summary = dashboard_summary(run_dashboard(defocus_nm=250.0))
    assert "FAIL" in summary
    assert "litho" in summary and "defocus" in summary
    assert "NILS" in summary


def test_summary_trail_names_a_killer_particle():
    """The other map-texture knob: a killer-particle density scatters functional kills the trail names
    as a caught particle (the G3 channel) — a different failure mode from defocus."""
    summary = dashboard_summary(run_dashboard(defect_density=0.06))
    assert "killer particle" in summary


def test_scheil_slice_walks_vt_out_the_top():
    """The G2 difficulty curve: a wafer sliced from the boule tail (``slice_z`` high) starts more
    heavily doped → its mean ``V_t`` drifts up out of the spec window (a near-total yield loss)."""
    result = run_dashboard(slice_z=0.85)
    assert result.yield_ < 0.1
    summary = dashboard_summary(result)
    assert "V_t" in summary


def test_oxide_lever_rescues_the_drifted_tail():
    """The G7 "adapt" lever: at the drifted tail (``slice_z`` high → ``V_t`` out the top), thinning
    the gate oxide lowers ``V_t`` back into spec — yield recovers. (The Goldilocks limit, over-thinning
    into the floor, is G7's own ``demo_game`` story.)"""
    drifted = run_dashboard(slice_z=0.85, oxide_minutes=20.0).yield_
    rescued = run_dashboard(slice_z=0.85, oxide_minutes=18.0).yield_
    assert rescued > drifted


# --------------------------------------------------------------------------- #
# The figure — a "builds without error" viz smoke test only (ADR 0002)
# --------------------------------------------------------------------------- #
def test_dashboard_figure_builds():
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    from fab_game.plots import dashboard_figure

    fig = dashboard_figure(run_dashboard(defocus_nm=90.0))
    assert len(fig.axes) >= 1                                  # the wafer-map panel
    mpl.pyplot.close(fig)
