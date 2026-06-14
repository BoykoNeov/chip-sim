"""Integration test for the journey demo (the demo IS the integration check — ADR 0002/0005).

The phase-1–3 journey demo wires the staged scaffold + the purification, crystal-growth *and* slice/cut
stages through the validated line: ``compute`` is the end-to-end check that the refine/grow/cut → forecast
(band + channel) → commit → finish chain holds together. Asserted on the robust thesis (purification walks
dead→ring→clean; growth is a two-sided window graded on *both* sides with an interior optimum; the slice
arc walks clean→ring→dead down the boule and is **coupled** to the phase-2 pull; the metal feed dies on
leakage, not V_t), not brittle numbers (the mechanics are pinned in ``test_journey.py``). The figure is a
"builds without error" smoke test only.

``compute`` is heavier now (three stages, grid_n=11), so it runs **once** as a module fixture.
"""
from __future__ import annotations

import pytest

from fab_game.demo_journey import compute


@pytest.fixture(scope="module")
def result():
    return compute()


# --------------------------------------------------------------------------- #
# Stage 1 — purification
# --------------------------------------------------------------------------- #
def test_demo_purification_arc_walks_dead_to_ring_to_clean(result):
    """A raw solar feed is scrapped, a fractional refine lands the graded ring, more → clean."""
    assert result.bands[0] == "dead"                        # raw feed: Na out of spec → scrapped
    assert "ring" in result.bands                           # a graded ring in the middle (rework band)
    assert result.bands[-1] == "clean"                      # refined enough: clean
    assert result.yields[-1] == 1.0
    assert 0.0 < result.ring_forecast.yield_ < 1.0          # the ring is a partial wafer
    assert "V_t" in (result.ring_forecast.channel or "")    # …failing on the mobile-ion V_t channel


# --------------------------------------------------------------------------- #
# Stage 2 — crystal growth (the two-sided window, graded both ways)
# --------------------------------------------------------------------------- #
def test_demo_growth_window_is_two_sided_and_graded(result):
    """The pull-rate window has a clean **interior** optimum with *partial* (graded, not 0↔1) yields on
    both flanks — the slow flank failing on dislocation leakage, the fast flank on voids."""
    assert "clean" in result.growth_bands                   # the optimum clears
    assert result.growth_bands[0] == "ring"                 # slow end: graded (not dead, not clean)
    assert result.growth_bands[-1] == "ring"                # fast end: graded
    # the optimum is interior — not the slowest or the fastest pull (a real two-sided window)
    assert result.growth_pulls[0] < result.growth_optimum_pull < result.growth_pulls[-1]
    assert "leakage" in (result.growth_arc[0].channel or "").lower()    # slow → dislocation leakage rim
    assert "void" in (result.growth_arc[-1].channel or "").lower()      # fast → void core


def test_demo_boule_drift_flattens_with_a_faster_pull(result):
    """CG-1, the 'watch it develop' view: the seed→tail V_t swing is smaller at the (faster) optimum pull."""
    swing = lambda b: b[-1][1] - b[0][1]
    assert swing(result.boule_opt) < swing(result.boule_slow)


# --------------------------------------------------------------------------- #
# Stage 3 — slice/cut (the graded V_t ring down the boule + the phase-2 coupling)
# --------------------------------------------------------------------------- #
def test_demo_slice_arc_walks_clean_to_ring_to_dead_down_the_boule(result):
    """Cutting near the seed is clean; cutting deeper walks a *graded* V_t edge ring (the outer dies cross
    the spec ceiling first), then dead at the tail — failing on the named Scheil-drift channel."""
    assert result.slice_bands[0] == "clean"                 # the seed end: in spec
    assert "ring" in result.slice_bands                     # a graded ring band exists (the rework signal)
    assert result.slice_bands[-1] == "dead"                 # the tail: Scheil-walked V_t out of spec
    assert 0.0 < result.slice_ring_forecast.yield_ < 1.0    # the ring is a partial wafer
    assert "scheil" in (result.slice_ring_forecast.channel or "").lower()
    # the cut sweep is monotone non-increasing down the boule (V_t only walks one way)
    assert list(result.slice_yields) == sorted(result.slice_yields, reverse=True)


def test_demo_slice_is_coupled_to_the_phase2_pull(result):
    """THE payoff: the same cut sweep is high-then-graded on the flat (optimum-pull) boule but stays low on
    the slow-pulled one (already lost to its leakage rim) — a flat boule can be cut deep, a slow one can't be
    sliced back to life."""
    deep_i = result.slice_zs.index(result.slice_commit_z)   # the deepest clean cut on the flat boule
    assert result.slice_yields[deep_i] >= 0.90              # flat boule: still clean this deep
    assert result.slice_yields_slow[deep_i] < result.slice_yields[deep_i]   # the slow boule is already lost
    assert max(result.slice_yields_slow) < max(result.slice_yields)         # the slow curve sits below throughout


# --------------------------------------------------------------------------- #
# End to end + the purification channel contrast
# --------------------------------------------------------------------------- #
def test_demo_finish_runs_and_scores_the_grown_wafer(result):
    """Commit both stages + finish: the clean, optimally-grown wafer runs the whole line and scores. Its
    yield is high but **not** a perfect 100% — the committed OSF ring always costs a few core/rim dies."""
    assert result.finish_result.yield_ >= 0.85              # grown wafer: clean OSF ring, a few core/rim lost
    assert result.finish_score.n_good > 0
    assert any("committed" in line for line in result.log)  # the accumulator writes are logged


def test_demo_metal_contrast_dies_on_leakage_not_vt(result):
    """A metal feed reads fine on V_t (Na = 0) yet is dead on junction leakage (the deep-level metals)."""
    assert result.metal_forecast.band == "dead"
    assert "leakage" in (result.metal_forecast.channel or "").lower()


def test_journey_figure_builds(result):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import journey_figure

    fig = journey_figure(result)
    assert len(fig.axes) >= 9                               # 3×3: purification + crystal-growth + slice rows
    plt.pyplot.close(fig)
