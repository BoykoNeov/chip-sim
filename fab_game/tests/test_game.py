"""G7 session mechanics — determinism, bookkeeping closes, the boule-drift arc, sandbox vs roguelike.

Pure game policy (ADR 0005 §5): the dollars are flagged house numbers, so these assert the **mechanics**
— a fixed (seed, decisions) reproduces the run; the budget/score/history accounting closes and is
append-only; the physics-grounded **difficulty curve** (the G2 Scheil V_t drift) actually bites the
boule tail and the **lever** (thin the oxide) rescues it; and sandbox vs roguelike is one mode flag.
"""
from __future__ import annotations

from dataclasses import replace

from fab_game.game import (
    GameConfig,
    ReworkSpec,
    new_session,
    play,
    process_wafer,
    scrap_wafer,
)
from fab_game.recipe import DEFAULT_RECIPE, LithoKnobs, OxidationKnobs, Recipe


def _adaptive(z: float) -> Recipe:
    """The lever: thin the gate oxide as the boule drifts (≈ 20.5 − 5.5·z min) → pull V_t back into spec."""
    return Recipe(oxidation=OxidationKnobs(minutes=20.5 - 5.5 * z))


# --------------------------------------------------------------------------- #
# Determinism + bookkeeping
# --------------------------------------------------------------------------- #
def test_a_fixed_seed_and_decisions_reproduce_the_run():
    cfg = GameConfig(n_wafers=5, grid_n=3)
    decisions = [DEFAULT_RECIPE, DEFAULT_RECIPE, "scrap", DEFAULT_RECIPE, DEFAULT_RECIPE]
    a = play(new_session(cfg, seed=7), decisions)
    b = play(new_session(cfg, seed=7), decisions)
    assert a.budget == b.budget and a.score == b.score
    assert [(r.wafer_index, r.scorecard.revenue, r.scorecard.cost, r.scrapped) for r in a.history] \
        == [(r.wafer_index, r.scorecard.revenue, r.scorecard.cost, r.scrapped) for r in b.history]


def test_budget_and_score_bookkeeping_closes():
    cfg = GameConfig(n_wafers=5, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE] * 5)
    # budget = starting + Σ profits; score = cumulative profit; history append-only (one rec / turn).
    assert s.budget == cfg.starting_budget + sum(r.scorecard.profit for r in s.history)
    assert abs(s.score - sum(r.scorecard.profit for r in s.history)) < 1e-9
    assert len(s.history) == 5 and [r.wafer_index for r in s.history] == [0, 1, 2, 3, 4]
    # Each turn's profit reconciles against its own revenue and cost (no money created/destroyed).
    for r in s.history:
        assert r.scorecard.profit == r.scorecard.revenue - r.scorecard.cost


def test_scrap_costs_only_the_scrap_fee_and_earns_nothing():
    cfg = GameConfig(n_wafers=4, grid_n=3, starting_budget=100.0)
    s = scrap_wafer(new_session(cfg, seed=0))
    assert s.history[-1].scrapped is True
    assert s.history[-1].scorecard.revenue == 0.0
    assert s.budget == 100.0 - cfg.scrap_cost                  # only the sunk-substrate cost
    assert s.wafer_index == 1                                  # the slice was consumed (advanced down boule)


# --------------------------------------------------------------------------- #
# The boule-drift arc: the Scheil V_t walk dies the tail; thinning the oxide rescues it
# --------------------------------------------------------------------------- #
def test_naive_recipe_loses_the_boule_tail_that_adaptive_rescues():
    cfg = GameConfig(n_wafers=6, z_max=0.9, grid_n=3)
    naive = play(new_session(cfg, seed=0), [DEFAULT_RECIPE] * cfg.n_wafers)
    # Adaptive: thin the oxide at each slice (the lever) — recipe chosen per turn from the slice z.
    sess = new_session(cfg, seed=0)
    while not sess.done:
        sess = process_wafer(sess, _adaptive(sess.next_slice_z))
    adaptive = sess
    # The tail turn: the naive wafer's V_t has walked out of spec (fewer good dies) where adaptive holds.
    assert naive.history[-1].scorecard.n_good < adaptive.history[-1].scorecard.n_good
    # Over the whole boule, adapting the recipe scores strictly more (the lever is worth playing).
    assert adaptive.score > naive.score


def test_scrapping_the_doomed_tail_beats_processing_it():
    # When the tail will fail anyway, scrapping (pay scrap_cost) beats processing (pay full wafer_cost
    # for ~zero revenue) — the "cut your losses" decision is real.
    cfg = GameConfig(n_wafers=6, z_max=0.9, grid_n=3)
    process_tail = play(new_session(cfg, seed=0), [DEFAULT_RECIPE] * cfg.n_wafers)
    scrap_tail = play(new_session(cfg, seed=0), [DEFAULT_RECIPE] * 4 + ["scrap", "scrap"])
    # The last two slices are doomed under the naive recipe; scrapping them loses less than processing.
    assert scrap_tail.score > process_tail.score


# --------------------------------------------------------------------------- #
# Rework folds into a turn (the existing tested paths), at a cost
# --------------------------------------------------------------------------- #
def test_litho_rework_in_a_turn_recovers_dies_at_a_cost():
    cfg = GameConfig(n_wafers=3, grid_n=5)
    bad = Recipe(litho=LithoKnobs(defocus_nm=90.0))            # a defocused exposure → an edge ring dies
    plain = process_wafer(new_session(cfg, seed=0), bad)
    fixed = process_wafer(new_session(cfg, seed=0), bad,
                          rework=ReworkSpec(kind="litho", focus_correction_nm=-90.0))
    # Rework recovers good dies (more revenue) but costs the rework fee — and is flagged in the record.
    assert fixed.history[-1].scorecard.n_good >= plain.history[-1].scorecard.n_good
    assert fixed.history[-1].reworked is True
    assert fixed.history[-1].scorecard.cost > plain.history[-1].scorecard.cost
    # Net identity (the monotonicity bound): the reworked turn nets exactly (recovered revenue − the
    # rework fee) over the plain run — rework never banks more than the value it recovered minus its cost.
    from fab_game.scoring import REWORK_COSTS
    fr, pr = fixed.history[-1].scorecard, plain.history[-1].scorecard
    recovered = fr.revenue - pr.revenue
    assert fr.profit == pr.profit + recovered - REWORK_COSTS["litho"]


# --------------------------------------------------------------------------- #
# Sandbox vs roguelike — one mode flag (the bankrupt gate)
# --------------------------------------------------------------------------- #
def test_roguelike_goes_bankrupt_where_sandbox_explores_on():
    # A punishing setup: tiny budget, expensive wafers → the budget goes negative early.
    rogue = GameConfig(n_wafers=8, grid_n=3, starting_budget=10.0, wafer_cost=500.0)
    sand = replace(rogue, sandbox=True)
    r = play(new_session(rogue, seed=0), [DEFAULT_RECIPE] * 8)
    s = play(new_session(sand, seed=0), [DEFAULT_RECIPE] * 8)
    assert r.budget < 0 and r.bankrupt and r.done            # roguelike: the negative budget ends it…
    assert len(r.history) < 8                                 # …and the run stopped early (play() bails on done)
    assert s.budget < 0 and not s.bankrupt                    # sandbox: budget can go negative without ending
    assert len(s.history) == 8                                # …so the whole boule was explored


def test_processing_after_the_run_is_over_raises():
    import pytest

    cfg = GameConfig(n_wafers=2, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE, DEFAULT_RECIPE])
    assert s.boule_exhausted and s.done
    with pytest.raises(ValueError):
        process_wafer(s, DEFAULT_RECIPE)
    with pytest.raises(ValueError):
        scrap_wafer(s)
