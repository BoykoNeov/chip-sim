"""Integration test for the G7 roguelike demo (the demo IS the integration check).

The game demo wires the scoring + session over the existing line into the roguelike artifact. Its
``compute`` is the end-to-end check that the physics-grounded difficulty curve (the Scheil V_t drift)
bites the boule tail, that the lever (thin the oxide) rescues it, and that a worse strategy banks less —
asserted on the robust thesis (naive exits spec at the tail; adapt holds; adapt scores more than scrap
scores more than naive), not brittle dollar amounts (the mechanics are pinned in test_scoring.py /
test_game.py).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game.demo_game import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the three playthroughs are the costly part)."""
    return compute()


def test_demo_scheil_drift_walks_naive_out_of_spec_where_adapt_holds(r):
    """The difficulty curve: the naive recipe's V_t exits the spec ceiling at the boule tail, while the
    adaptive oxide trim holds V_t inside the window across the whole boule."""
    assert r.vt_naive[-1] > r.vt_hi                            # naive: the tail walks out the top
    assert all(r.vt_lo <= v <= r.vt_hi for v in r.vt_adaptive) # adapt: held in spec down the boule
    # The tail wafer both strategies process: naive loses it, adapt keeps it.
    assert r.naive.history[-1].scorecard.n_good < r.adaptive.history[-1].scorecard.n_good


def test_demo_a_worse_strategy_banks_less(r):
    """Scored: adapting the recipe rescues the tail for premium (top score); cutting the loss (scrap)
    beats eating it (naive). The decision is the point — a worse strategy banks less."""
    assert r.adaptive.score > r.scrap.score > r.naive.score
    # Bookkeeping closes for each playthrough (budget = start + Σ profits).
    for sess in (r.naive, r.scrap, r.adaptive):
        assert sess.budget == sess.config.starting_budget + sum(rec.scorecard.profit for rec in sess.history)
    # The scrap strategy actually scrapped the doomed tail (≥1 scrapped turn).
    assert any(rec.scrapped for rec in r.scrap.history)


def test_game_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import game_figure

    fig = game_figure(r)
    assert len(fig.axes) >= 3                                 # drift / score / profit panels
    plt.pyplot.close(fig)
