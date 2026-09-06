"""Integration test for the deliberate-wafer-kill demo (:mod:`fab_game.demo_latchup_trap`).

The pieces are pinned elsewhere: ``chip/tests/test_latchup.py`` holds the two cited criteria and the
substrate lever, ``test_targets_highres.py`` holds the part's own window and the re-grade scrap that this
batch fixed, and ``test_journey.py`` holds the levers a player pulls. None of that is re-asserted here.

What only this demo can break is the **claim it exists to make**: that the latchup crossing lands
*inside* the high-res part's acceptance window, so that a substrate satisfying every published criterion
still costs the whole wafer. If the window or the crossing ever moves so that they stop overlapping, the
demo's headline quietly becomes false while every other test in the repo stays green -- so the overlap
itself is what is asserted, not the numbers on either side of it.
"""
from __future__ import annotations

import pytest

from fab_game import demo_latchup_trap as demo


@pytest.fixture(scope="module")
def rungs():
    return demo.run()


def test_the_ladder_spans_both_sides_of_the_part_window(rungs):
    """The ladder must bracket the window, or the demo is showing a slice of it and calling it the whole."""
    assert not rungs[0].passes_window, "the lightest rung should be below the window (native V_t too low)"
    assert not rungs[-1].passes_window, "the heaviest rung should be above it (the game default is logic)"
    assert any(r.passes_window for r in rungs)


def test_the_window_is_contiguous(rungs):
    """One window, not a ragged set -- otherwise 'inside the window' would not mean anything."""
    flags = [r.passes_window for r in rungs]
    first, last = flags.index(True), len(flags) - 1 - flags[::-1].index(True)
    assert all(flags[first:last + 1])


def test_the_latchup_crossing_falls_INSIDE_the_window_which_is_the_whole_demo(rungs):
    """**The claim.** The part's window contains both dead and buildable substrates.

    Below the crossing the wafer latches; above it, it does not. If the crossing ever moved outside the
    window this assertion is the only thing in the repo that would notice, because every component would
    still be individually correct -- the trap is a property of the *overlap*.
    """
    window = [r for r in rungs if r.passes_window]
    assert any(r.latches for r in window), "no trap: the whole window is buildable"
    assert any(not r.latches for r in window), "the window is entirely unbuildable -- that is a different bug"
    # And the split is a clean crossing in one direction: heavier is safer, so the dead rungs are the light
    # ones. (A ragged split would mean the trigger had stopped being monotone in the substrate doping.)
    assert max(r.n_seed for r in window if r.latches) < min(r.n_seed for r in window if not r.latches)


def test_a_trapped_rung_ships_nothing_and_a_safe_one_ships_everything(rungs):
    """All dies or none -- the B12 refusal, visible at the surface a player reads.

    The trap rung is the load-bearing one: it PASSES its own spec on paper and ships zero parts. Anything
    in between (a partial yield) would mean latchup had acquired a per-die gradient it is not entitled to.
    """
    window = [r for r in rungs if r.passes_window]
    for r in window:
        assert r.shipped in (0, r.n_dies), "latchup graded the wafer -- it is a wafer property, all or none"
    trapped = [r for r in window if r.latches]
    assert trapped and all(r.shipped == 0 for r in trapped)
    assert all(r.shipped == r.n_dies for r in window if not r.latches)


def test_the_margin_column_is_the_thing_that_predicts_it(rungs):
    """The 'see it coming' half: the printed margin agrees with the outcome on every rung, so the column
    a player consults before committing is not decorative."""
    for r in rungs:
        assert r.latches == (r.margin < 1.0)


def test_figure_builds(rungs, tmp_path, monkeypatch):
    """Smoke only (ADR 0002): the figure is not in the correctness path, just "renders without error"."""
    pytest.importorskip("matplotlib")
    monkeypatch.setattr(demo, "DOCS_FIGURE", tmp_path / demo.DOCS_FIGURE.name)
    assert demo.save_figure(rungs).is_file()


def test_summary_prints(rungs, capsys):
    demo.print_summary(rungs)
    out = capsys.readouterr().out
    assert "THE TRAP" in out
    assert "high-res" in out
    # The demo must keep saying WHY the cliff is not graded, since that is the part a reader will
    # otherwise mistake for a modelling shortfall.
    assert "ONE number for the" in out          # the reason it is not graded ...
    assert "refused to invent one" in out       # ... and that the refusal was deliberate

def test_the_crossing_is_solved_not_sampled(rungs):
    """The crossing must not depend on how finely the ladder happens to be sampled.

    It did, once: the figure's trap band was drawn between the window's lower edge and the heaviest
    *rung* that latched, so trimming one rung for runtime silently collapsed the band to zero width and
    the demo's own headline disappeared from its figure while every assertion still passed. The crossing
    is now bisected from the closed form, and this pins that it stays independent of the ladder.
    """
    crossing = demo.crossing_n_seed()
    heaviest_latching = max(r.n_seed for r in rungs if r.latches)
    lightest_safe = min(r.n_seed for r in rungs if not r.latches)
    assert heaviest_latching < crossing < lightest_safe      # bracketed by, and distinct from, the rungs
    assert crossing not in {r.n_seed for r in rungs}         # genuinely not a sampled value
    # And it is inside the part's window, which is the whole demo (asserted here on the SOLVED value,
    # since the rung-based version of this claim can be satisfied by an accident of sampling).
    window = [r for r in rungs if r.passes_window]
    assert min(r.n_seed for r in window) < crossing < max(r.n_seed for r in window)

