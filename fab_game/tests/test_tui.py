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
from fab_game.plots import WAFER_FAIL_GLYPH, WAFER_PASS_GLYPH, _grid_n, wafer_map_text


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
