"""Smoke + mechanics test for the deferred Textual TUI (``fab_game.tui``) and its pure map renderer.

Two legs, mirroring ``test_dashboard.py``'s discipline (mechanics not magnitudes, ADR 0005 §5; the
render is a "builds without error / wires correctly" smoke test, ADR 0002 — the physics is already
validated upstream):

1. **The pure map renderer — tested with no Textual at all.** ``wafer_map_text`` is the load-bearing,
   Textual-independent core (``fab_game.plots`` imports neither textual nor matplotlib at module
   level), so it is asserted directly: a clean run is all pass glyphs, a defocus wipeout is all fail
   glyphs, the grid shape matches the die map, and ``color=True`` only *wraps* the glyphs.

2. **The App smoke test — ``importorskip("textual")`` + Textual's in-process ``run_test()`` pilot,**
   driven from a manual ``asyncio.run`` wrapper inside a sync test (NOT a ``pytest-asyncio``
   dependency — keeps ``[test]`` lean). It proves the *wiring* (input → ``run_dashboard`` → panels):
   the App opens on the clean seam, a defocus run shows the failure trail, and — the §5 fidelity
   contract — the panel text equals the headless ``dashboard_summary`` verbatim (the TUI never
   recomputes). The textual import stays *inside* each test fn, after the skip, so collection on the
   uninstalled fast lane never imports textual.
"""
from __future__ import annotations

import pytest

from fab_game.dashboard import dashboard_summary, run_dashboard
from fab_game.game import GameConfig, new_session, play
from fab_game.guide import dashboard_guide, roguelike_guide
from fab_game.plots import WAFER_FAIL_GLYPH, WAFER_PASS_GLYPH, _grid_n, wafer_map_text
from fab_game.session_view import (
    history_trail,
    inspect_line,
    oxide_recipe,
    session_header,
    session_summary,
)


# --------------------------------------------------------------------------- #
# 1. The pure map renderer (no Textual) — the load-bearing, independently testable leg
# --------------------------------------------------------------------------- #
def test_map_clean_wafer_is_all_pass_glyphs():
    """The default (clean) run prints every die: the map carries one pass glyph per die and no fail glyph."""
    wafer = run_dashboard().wafer
    text = wafer_map_text(wafer)
    assert text.count(WAFER_PASS_GLYPH) == len(wafer.dies)
    assert WAFER_FAIL_GLYPH not in text


def test_map_defocus_wipeout_is_all_fail_glyphs():
    """A defocus wipeout kills the whole wafer (yield 0) → every die is the fail glyph, no survivors."""
    wafer = run_dashboard(defocus_nm=250.0).wafer
    text = wafer_map_text(wafer)
    assert WAFER_FAIL_GLYPH in text
    assert WAFER_PASS_GLYPH not in text


def test_map_shape_matches_the_die_grid():
    """The map is ``grid_n`` rows tall and carries exactly one glyph per die (the circle's clipped cells
    are blank), so its shape mirrors the wafer's die map."""
    wafer = run_dashboard(defocus_nm=90.0).wafer        # a partial kill → both glyphs present
    text = wafer_map_text(wafer)
    assert len(text.split("\n")) == _grid_n(wafer)
    assert text.count(WAFER_PASS_GLYPH) + text.count(WAFER_FAIL_GLYPH) == len(wafer.dies)


def test_map_color_only_wraps_the_glyphs():
    """``color=True`` wraps pass/fail glyphs in Rich markup for the TUI panel without changing the glyph
    count — the plain default is what the other tests pin."""
    wafer = run_dashboard(defocus_nm=90.0).wafer
    plain = wafer_map_text(wafer)
    colored = wafer_map_text(wafer, color=True)
    assert plain != colored
    assert "[green]" in colored and "[red]" in colored
    assert colored.count(WAFER_PASS_GLYPH) == plain.count(WAFER_PASS_GLYPH)
    assert colored.count(WAFER_FAIL_GLYPH) == plain.count(WAFER_FAIL_GLYPH)


# --------------------------------------------------------------------------- #
# 2. The App (importorskip textual) — proves input → run_dashboard → panels
# --------------------------------------------------------------------------- #
def test_app_opens_on_the_clean_seam():
    """The App opened at default knobs runs the seam recipe → a clean wafer; the summary panel reads the
    headless ``dashboard_summary`` of that clean run verbatim (fidelity), and the map is all-pass."""
    pytest.importorskip("textual")
    import asyncio

    from fab_game.tui import FabLineApp

    async def scenario():
        app = FabLineApp()
        async with app.run_test() as pilot:
            await pilot.pause()                                 # let on_mount's run settle
            assert "yield 100%" in app.last_summary
            assert "clean wafer" in app.last_summary
            assert app.last_summary == dashboard_summary(run_dashboard())   # never recomputed
            assert WAFER_PASS_GLYPH in app.last_map and WAFER_FAIL_GLYPH not in app.last_map

    asyncio.run(scenario())


def test_app_run_button_shows_the_failure_trail():
    """Set the defocus knob to a wipeout, press *Run* (the button wiring), and the summary panel shows the
    litho failure trail — equal to the headless run verbatim, the map all-fail."""
    pytest.importorskip("textual")
    import asyncio

    from fab_game.tui import FabLineApp

    async def scenario():
        app = FabLineApp()
        async with app.run_test(size=(120, 50)) as pilot:      # tall enough that Run is on-screen
            await pilot.pause()
            app.query_one("#in-defocus_nm").value = "250"      # a wipeout defocus
            await pilot.click("#run")                           # the button → _run_and_render
            await pilot.pause()
            assert "FAIL" in app.last_summary
            assert "litho" in app.last_summary and "defocus" in app.last_summary
            assert "NILS" in app.last_summary
            assert app.last_summary == dashboard_summary(run_dashboard(defocus_nm=250.0))
            assert WAFER_FAIL_GLYPH in app.last_map

    asyncio.run(scenario())


# --------------------------------------------------------------------------- #
# 3. The v2 roguelike screen (importorskip textual) — navigation/seam + the fidelity loop
# --------------------------------------------------------------------------- #
def test_play_button_opens_the_roguelike_screen_on_a_fresh_run():
    """The dashboard's *Play roguelike* button pushes ``RoguelikeScreen``; it opens on a fresh run whose
    panels equal the headless ``session_view`` renderers of ``new_session`` verbatim; ``escape`` pops back."""
    pytest.importorskip("textual")
    import asyncio

    from fab_game.tui import FabLineApp, RoguelikeScreen

    async def scenario():
        app = FabLineApp()
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            await pilot.click("#play-game")                     # the button wiring → push_screen
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, RoguelikeScreen)
            seam = new_session(GameConfig(), seed=0)            # the screen's default fresh run
            assert screen.last_header == session_header(seam)  # rendered verbatim (never recomputed)
            assert "roguelike" in screen.last_header and "0/" in screen.last_header
            assert screen.last_trail == history_trail(seam) and "no turns played yet" in screen.last_trail
            assert screen.last_inspect == inspect_line(seam, oxide_recipe(20.0))  # seed-slice projection
            assert "slice z=0.00" in screen.last_inspect
            await pilot.press("escape")                          # escape pops back to the dashboard
            await pilot.pause()
            assert not isinstance(app.screen, RoguelikeScreen)

    asyncio.run(scenario())


def test_roguelike_screen_drives_the_session_exactly_like_the_headless_model():
    """Drive a known process / adapt / scrap sequence through the screen's buttons and assert the
    resulting session equals the headless ``play(new_session(cfg, seed), [same decisions])`` **verbatim**
    (budget / score / history) — the §5 fidelity contract: the thin driver never diverges from the model.
    Also: the boule exhausts → the action buttons disable and the inspect panel shows the end tally."""
    pytest.importorskip("textual")
    import asyncio

    from textual.widgets import Button, Input

    from fab_game.tui import FabLineApp, RoguelikeScreen

    cfg = GameConfig(n_wafers=3, z_max=0.9, grid_n=3)
    decisions = [oxide_recipe(20.0), oxide_recipe(17.0), "scrap"]   # process · adapt (thin) · scrap the tail

    async def scenario():
        app = FabLineApp()
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            screen = RoguelikeScreen(cfg, seed=5)
            await app.push_screen(screen)
            await pilot.pause()

            screen.query_one("#in-oxide", Input).value = "20"   # turn 0: process at the seam oxide
            await pilot.click("#process")
            await pilot.pause()
            screen.query_one("#in-oxide", Input).value = "17"   # turn 1: adapt — thin the gate oxide
            await pilot.click("#process")
            await pilot.pause()
            await pilot.click("#scrap")                          # turn 2: scrap the doomed tail
            await pilot.pause()

            expected = play(new_session(cfg, seed=5), decisions)
            assert screen.session.budget == expected.budget
            assert screen.session.score == expected.score
            assert [(r.wafer_index, r.scorecard.revenue, r.scorecard.cost, r.scrapped, r.scorecard.n_good)
                    for r in screen.session.history] == \
                   [(r.wafer_index, r.scorecard.revenue, r.scorecard.cost, r.scrapped, r.scorecard.n_good)
                    for r in expected.history]
            # The run is over: the action buttons disable (the honest affordance) and the inspect panel
            # shows the end-of-run tally — all rendered from the headless renderers verbatim.
            assert screen.session.done and screen.session.boule_exhausted
            assert screen.query_one("#process", Button).disabled
            assert screen.query_one("#scrap", Button).disabled
            assert screen.last_header == session_header(expected)
            assert screen.last_inspect == session_summary(expected)
            assert screen.last_trail == history_trail(expected)

    asyncio.run(scenario())


# --------------------------------------------------------------------------- #
# 4. Educational vs hardcore — the launch mode (presentation only; the seam is untouched)
# --------------------------------------------------------------------------- #
def test_hardcore_app_hides_the_guide_and_educational_shows_it_verbatim():
    """``FabLineApp(educational=False)`` is the bare cockpit — the guide panel is hidden (no ``shown``
    class → ``display:none`` reserves no space, the hardcore layout byte-identical). ``educational=True``
    shows it, and the panel text is the headless ``dashboard_guide()`` **verbatim** (fidelity — the App
    composes no prose). In *both* modes the line itself is the clean seam (educational is render-only)."""
    pytest.importorskip("textual")
    import asyncio

    from fab_game.tui import FabLineApp

    async def hardcore():
        app = FabLineApp()                                  # educational=False, the default (today's TUI)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            assert app.educational is False
            box = app.query_one("#guide-box")
            # The COMPUTED display, not just the class: the selector resolved to display:none and the box
            # occupies a ZERO region → it reserves no space, so the hardcore layout is byte-identical.
            assert box.display is False and box.region.area == 0
            assert app.last_summary == dashboard_summary(run_dashboard())  # the seam, unperturbed by mode

    async def educational():
        app = FabLineApp(educational=True)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            box = app.query_one("#guide-box")
            # Resolved to actually VISIBLE (display:block + a non-empty on-screen region), not merely
            # class-tagged — a CSS-selector typo would leave the class set but the panel blank.
            assert box.display is True and box.region.area > 0
            # The panel is built from the stash verbatim (``yield Static(self.last_guide)``), so the stash
            # equalling the headless prose IS the fidelity pin (the App composes no prose of its own).
            assert app.last_guide == dashboard_guide()
            assert app.last_summary == dashboard_summary(run_dashboard())  # the line is STILL the seam

    asyncio.run(hardcore())
    asyncio.run(educational())


def test_mode_select_screen_picks_educational_or_hardcore():
    """Launched with ``prompt_mode=True`` (the ``python -m fab_game.tui`` path) the App opens on the
    :class:`ModeSelectScreen`; pressing *Educational* sets the mode, pops back to the dashboard, and
    shows the guide; *Hardcore* leaves it hidden. The chooser only toggles presentation."""
    pytest.importorskip("textual")
    import asyncio

    from textual.widgets import Button

    from fab_game.tui import FabLineApp, ModeSelectScreen

    async def pick(button_id: str, *, expect_shown: bool, expect_edu: bool):
        app = FabLineApp(prompt_mode=True)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, ModeSelectScreen)             # the chooser is the front gate
            assert app.screen.query_one("#mode-edu", Button) and app.screen.query_one("#mode-hard", Button)
            await pilot.click(button_id)                                # pick a mode → apply + pop
            await pilot.pause()
            assert not isinstance(app.screen, ModeSelectScreen)         # revealed the dashboard underneath
            assert app.educational is expect_edu
            assert app.query_one("#guide-box").display is expect_shown  # the COMPUTED display, post-choice

    asyncio.run(pick("#mode-edu", expect_shown=True, expect_edu=True))
    asyncio.run(pick("#mode-hard", expect_shown=False, expect_edu=False))


def test_play_roguelike_inherits_the_educational_mode_and_shows_its_guide():
    """The dashboard's *Play roguelike* button carries the chosen mode into ``RoguelikeScreen``: in
    educational mode the screen shows its own guide (``roguelike_guide()`` verbatim); the session it
    drives is still the headless ``new_session`` seam (the mode is render-only)."""
    pytest.importorskip("textual")
    import asyncio

    from fab_game.tui import FabLineApp, RoguelikeScreen

    async def scenario():
        app = FabLineApp(educational=True)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            await pilot.click("#play-game")
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, RoguelikeScreen) and screen._educational is True
            box = screen.query_one("#game-guide-box")
            assert box.display is True and box.region.area > 0            # resolved to visible, not just tagged
            assert screen.last_guide == roguelike_guide()                 # the verbatim headless prose
            # The driven session is still the headless fresh run — the guide changed nothing.
            assert screen.session.budget == new_session(GameConfig(), seed=0).budget

    asyncio.run(scenario())


# --------------------------------------------------------------------------- #
# 5. Out-of-domain knobs show a readable note instead of crashing the App (regression)
# --------------------------------------------------------------------------- #
def test_out_of_range_dashboard_knob_shows_a_note_instead_of_crashing():
    """The bug: an out-of-domain-but-parseable value (``slice_z`` outside ``[0, 1)``) used to raise a raw
    ``ValueError`` straight into the Textual handler and kill the App. Now *Run* pre-screens it → the
    summary panel shows the readable note, the App stays alive, and the wafer map is untouched (the last
    clean seam). This pilot is the real regression — it raises on the un-fixed code; the headless
    ``knob_errors`` test never would."""
    pytest.importorskip("textual")
    import asyncio

    from textual.widgets import Input

    from fab_game.tui import FabLineApp

    async def scenario():
        app = FabLineApp()
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            seam_map = app.last_map                              # the clean mount run
            app.query_one("#in-slice_z", Input).value = "1.5"   # a boule slice past the tail (out of [0, 1))
            await pilot.click("#run")                            # would previously crash the App
            await pilot.pause()
            assert app.is_running                                # still alive — no uncaught exception
            assert "slice z" in app.last_summary and "[0, 1)" in app.last_summary
            assert app.last_map == seam_map                      # the run was skipped; the map is unchanged

    asyncio.run(scenario())


def test_zero_oxide_in_the_roguelike_does_not_crash_preview_or_process():
    """The roguelike's only player knob is the gate-oxide drive, and BOTH the live preview
    (``inspect_line → projected_vt → run_line``) and *Process* run the line — two separate crash sites for
    a non-positive bake. Entering ``"0"`` and pressing Enter (the preview) then clicking *Process* must
    each show a readable note, not raise into the event loop, and process must refuse the doomed turn (no
    record appended)."""
    pytest.importorskip("textual")
    import asyncio

    from textual.widgets import Input

    from fab_game.tui import FabLineApp, RoguelikeScreen

    async def scenario():
        app = FabLineApp()
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            screen = RoguelikeScreen(seed=0)
            await app.push_screen(screen)
            await pilot.pause()

            oxide = screen.query_one("#in-oxide", Input)
            oxide.value = "0"                                    # a zero-time bake — out of domain
            oxide.focus()
            await pilot.pause()
            await pilot.press("enter")                           # preview path: must not crash
            await pilot.pause()
            assert app.is_running
            assert "oxide" in screen.last_inspect                # the readable note, not a stack trace

            n_turns = len(screen.session.history)
            await pilot.click("#process")                        # process path: must not crash either
            await pilot.pause()
            assert app.is_running
            assert len(screen.session.history) == n_turns        # the doomed turn was refused (no record)
            assert "process" in screen.last_inspect.lower()      # the net's "Can't process this turn — …" note

    asyncio.run(scenario())
