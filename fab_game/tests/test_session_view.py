"""Headless renderers for the roguelike screen (``fab_game.session_view``) — the load-bearing leg.

The §9 / TUI-plan discipline: the strings the Textual ``RoguelikeScreen`` renders are built and tested
**here**, with no Textual at all, because the App (like ``ipywidgets.interact``) can swallow a callback
exception and still look green. Pure game policy (ADR 0005 §5) — these assert *mechanics*: the inspect
preview builds the **same** recipe the turn commits (the fidelity contract), the in/out-of-spec wording
tracks the ``V_t`` spec window, and the header / ledger / tally reconcile against the session model.
"""
from __future__ import annotations

from dataclasses import replace

from fab_game.game import GameConfig, new_session, play, process_wafer, scrap_wafer
from fab_game.recipe import DEFAULT_RECIPE
from fab_game.session_view import (
    history_trail,
    inspect_line,
    oxide_recipe,
    projected_vt,
    session_header,
    session_summary,
    turn_line,
    turn_recipe,
)


# --------------------------------------------------------------------------- #
# The fidelity contract: preview builds the EXACT recipe the turn will run
# --------------------------------------------------------------------------- #
def test_turn_recipe_overrides_slice_z_to_the_boule_position_like_process_wafer():
    """``turn_recipe`` mirrors ``process_wafer``'s internal recipe-at-z: the chosen recipe with its
    ``slice_z`` overridden to the session's next slice — so the inspect preview is the wafer the turn runs.
    """
    cfg = GameConfig(n_wafers=6, z_max=0.9, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE, DEFAULT_RECIPE, DEFAULT_RECIPE])  # advance to turn 3
    assert s.next_slice_z == cfg.slice_z(3) > 0.0                       # the boule has moved off the seed
    r = turn_recipe(s, DEFAULT_RECIPE)
    assert r.czochralski.slice_z == s.next_slice_z                       # ← the override (the fidelity pin)
    # Everything else is the chosen recipe untouched (only slice_z moves).
    assert r == replace(DEFAULT_RECIPE,
                        czochralski=replace(DEFAULT_RECIPE.czochralski, slice_z=s.next_slice_z))


def test_turn_recipe_defaults_to_the_config_base_recipe():
    """With no recipe given, ``turn_recipe`` uses ``config.base_recipe`` (still slice_z-overridden)."""
    cfg = GameConfig(n_wafers=4, grid_n=3)
    s = new_session(cfg, seed=0)
    assert turn_recipe(s) == replace(cfg.base_recipe,
                                     czochralski=replace(cfg.base_recipe.czochralski, slice_z=s.next_slice_z))


def test_oxide_recipe_sets_only_the_gate_oxide_drive():
    """The adapt lever touches only ``oxidation.minutes``; at the default 20 min it is the base by value."""
    assert oxide_recipe(20.0) == DEFAULT_RECIPE                          # the seam (default oxide = 20 min)
    thinned = oxide_recipe(16.0)
    assert thinned.oxidation.minutes == 16.0
    assert replace(thinned, oxidation=DEFAULT_RECIPE.oxidation) == DEFAULT_RECIPE   # nothing else moved


def test_projected_vt_tracks_the_oxide_lever_and_the_boule_drift():
    """The inspect ``V_t`` falls when the oxide is thinned (the lever) and rises down the boule (the drift)."""
    cfg = GameConfig(n_wafers=8, z_max=0.9, grid_n=3)
    s0 = new_session(cfg, seed=0)
    base_vt = projected_vt(s0)
    assert projected_vt(s0, oxide_recipe(16.0)) < base_vt               # thinner oxide → lower V_t
    # Down the boule the substrate doping rises (Scheil) → V_t walks up under the same recipe.
    s_tail = play(new_session(cfg, seed=0), [DEFAULT_RECIPE] * 6)
    assert projected_vt(s_tail) > base_vt


def test_projected_vt_equals_a_direct_nominal_run_of_the_turn_recipe():
    """The preview is exactly ``run_line`` of ``turn_recipe`` at one nominal die — no hidden recompute path."""
    from fab_game.pipeline import run_line
    from fab_game.variation import NO_VARIATION

    cfg = GameConfig(n_wafers=5, grid_n=3)
    s = play(new_session(cfg, seed=1), [DEFAULT_RECIPE, DEFAULT_RECIPE])
    direct = run_line(turn_recipe(s, oxide_recipe(17.0)),
                      variation=NO_VARIATION, specs=cfg.specs, grid_n=1).dies[0].V_t
    assert projected_vt(s, oxide_recipe(17.0)) == direct


# --------------------------------------------------------------------------- #
# The inspect line: in/out-of-spec wording tracks the V_t window
# --------------------------------------------------------------------------- #
def test_inspect_line_flags_in_spec_at_the_seed_and_out_of_spec_down_the_drifted_tail():
    cfg = GameConfig(n_wafers=8, z_max=0.9, grid_n=3)
    win = cfg.specs.v_t
    s0 = new_session(cfg, seed=0)
    line0 = inspect_line(s0)
    assert "in spec" in line0 and win.check(projected_vt(s0)) is None   # the seed slice prints in spec
    assert "slice z=0.00" in line0 and f"[{win.lo:.2f}, {win.hi:.2f}]" in line0
    # Walk to the last slice (z=0.9): the Scheil drift has driven the naive V_t past the ceiling → OUT.
    s_tail = play(new_session(cfg, seed=0), [DEFAULT_RECIPE] * 7)
    assert win.check(projected_vt(s_tail)) is not None                   # the drift bites (deterministic)
    assert "OUT of spec" in inspect_line(s_tail)


def test_inspect_line_reports_run_over_when_the_boule_is_exhausted():
    cfg = GameConfig(n_wafers=2, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE, DEFAULT_RECIPE])
    assert s.done
    assert "run is over" in inspect_line(s)


# --------------------------------------------------------------------------- #
# Header / ledger / tally reconcile against the session model
# --------------------------------------------------------------------------- #
def test_session_header_carries_the_budget_score_and_progress():
    cfg = GameConfig(n_wafers=5, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE, DEFAULT_RECIPE])
    head = session_header(s)
    assert "roguelike" in head and "2/5 wafers" in head
    assert f"${s.budget:.2f}" in head and f"${s.score:+.2f}" in head


def test_session_header_flags_run_over_states():
    exhausted = play(new_session(GameConfig(n_wafers=2, grid_n=3), seed=0), [DEFAULT_RECIPE, DEFAULT_RECIPE])
    assert "boule exhausted" in session_header(exhausted)
    rogue = GameConfig(n_wafers=8, grid_n=3, starting_budget=10.0, wafer_cost=500.0)
    bankrupt = play(new_session(rogue, seed=0), [DEFAULT_RECIPE] * 8)
    assert bankrupt.bankrupt and "BANKRUPT" in session_header(bankrupt)
    sand = play(new_session(replace(rogue, sandbox=True), seed=0), [DEFAULT_RECIPE] * 8)
    assert "sandbox" in session_header(sand) and "BANKRUPT" not in session_header(sand)


def test_history_trail_is_append_only_and_one_line_per_turn():
    cfg = GameConfig(n_wafers=4, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE, "scrap", DEFAULT_RECIPE])
    lines = history_trail(s).split("\n")
    assert len(lines) == len(s.history) == 3
    assert lines[0].startswith("T0") and lines[1].startswith("T1") and lines[2].startswith("T2")
    assert "scrap" in lines[1] and "process" in lines[0]
    # An empty session reads as the no-turns note (not a blank panel).
    assert "no turns played yet" in history_trail(new_session(cfg, seed=0))


def test_turn_line_shows_profit_and_outcome_for_process_vs_scrap():
    cfg = GameConfig(n_wafers=4, grid_n=3)
    proc = process_wafer(new_session(cfg, seed=0), DEFAULT_RECIPE).history[-1]
    scrap = scrap_wafer(new_session(cfg, seed=0)).history[-1]
    pl, sl = turn_line(proc), turn_line(scrap)
    assert f"${proc.scorecard.profit:+7.2f}" in pl and f"{proc.scorecard.n_good}/{proc.scorecard.n_total} good" in pl
    assert "scrap" in sl and "scrapped unprocessed" in sl


def test_session_summary_tallies_processed_scrapped_and_good():
    cfg = GameConfig(n_wafers=4, z_max=0.9, grid_n=3)
    s = play(new_session(cfg, seed=0), [DEFAULT_RECIPE, "scrap", DEFAULT_RECIPE, DEFAULT_RECIPE])
    summary = session_summary(s)
    assert "boule exhausted" in summary and f"${s.budget:.2f}" in summary
    assert "3 processed, 1 scrapped" in summary
    assert f"{sum(r.scorecard.n_good for r in s.history)} good dies shipped" in summary
