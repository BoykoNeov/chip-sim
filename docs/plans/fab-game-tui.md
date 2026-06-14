# Plan — fab-game Textual TUI (the deferred terminal front-end)

Status: **v1 BUILT (2026-06-14); v2 roguelike loop BUILT (2026-06-14); Educational/Hardcore launch mode
BUILT (2026-06-14)** (all drafted same day). The plan below is the as-built shape; the launch-mode
follow-on is recorded in §9. **v2 (§7) landed:** `fab_game/session_view.py` (the headless renderers —
`turn_recipe`/`oxide_recipe`/`projected_vt`/`inspect_line`/`session_header`/`turn_line`/`history_trail`/
`session_summary`, re-exported from `__init__`, tested by `tests/test_session_view.py`) + a
`RoguelikeScreen` in `tui.py` driving `game.py`'s `GameSession` (oxide-knob *adapt* lever + Process/Scrap
Buttons, panels rendered from `session_view` verbatim, `session.done`-guarded + buttons disabled when
over), opened from a *Play roguelike* button on `FabLineApp`. The pilot leg pins the §5 fidelity contract:
a driven Process/adapt/Scrap sequence yields a session **equal to** the headless
`play(new_session(cfg, seed), [same decisions])`. **What landed in v1:** `fab_game/tui.py` (`FabLineApp` — the
only module importing `textual`, *not* re-exported from `fab_game/__init__`, mirroring `plots.py`),
the new headless `fab_game.plots.wafer_map_text(wafer, *, color=False)` renderer, the `[tui]` extra
(`textual>=8`, verified on 8.2.7), and `fab_game/tests/test_tui.py` (4 pure-renderer legs + 2
`importorskip` App-pilot legs). **Verified:** fast lane 637 green; the App test runs clean 5×5 under
`-n auto` (no notebook-style flake → the `slow`/`xdist_group` escape hatch was **not** needed —
`run_test()` is in-process asyncio, no zmq/subprocess); with `textual` uninstalled the suite stays
green (4 pass / 2 skip) and `import fab_game` stays textual-free (the headless-safe criterion). The
one as-built deviation from §4's sketch: the App-pilot button test passes `run_test(size=(120, 50))`
so the *Run* button is on-screen for `pilot.click` (the default 80×24 pilot screen clipped it).

This is the terminal front-end promised three times already and never built: the main plan's
§9 ("A Textual TUI next … still a thin skin"), §10's UX ladder, and the G7 note ("a Textual
front-end would be a thin driver of this session, added when wanted"). It is now cheap to build,
because **its headless core already exists and is tested**: the §9 ipywidgets slice landed
`fab_game/dashboard.py` (`run_dashboard` / `dashboard_summary`) — explicitly banked as "the
headless, tested core of the deferred Textual TUI." This TUI is a *driver* of that core, nothing
more.

## 1. Scope

**v1 (this plan): a thin `run_dashboard` mirror.** The terminal twin of the §9 notebook slice —
the same four legible knobs + a seed, a live wafer map, the headline + worst-die failure trail.
**Zero new physics, no engine touch, no new device output.** It is to the TUI what the §9
notebook cell is to `interact`: a thin skin over the already-validated line.

**v2 (deferred follow-on, sketched in §7): the G7 roguelike loop.** Wire `fab_game/game.py`'s
`GameSession` (process / scrap / adapt a wafer, watch the Scheil `V_t` drift, score the run) into
the same App as a second screen. Listed in memory as a *separate* deferred item ("Textual TUI +
tycoon"); kept out of v1 so the first cut stays a pure dashboard mirror.

Out of scope entirely: any new physics, a web/Godot front-end (ADR 0002 deep-end / ADR 0005
tycoon-future), and the tycoon economy.

## 2. Architecture

```
fab_game/tui.py        # NEW — a Textual App; the only module that imports `textual`
  └─ drives ─▶ fab_game.dashboard.run_dashboard(**knobs, seed)  → LineResult   (unchanged)
              fab_game.dashboard.dashboard_summary(result)      → str          (unchanged)
              fab_game.plots.wafer_map_text(wafer)              → str          (NEW, headless)
```

- **`fab_game/tui.py`** — a `textual.app.App` subclass (call it `FabLineApp`). One screen:
  - **Inputs** for the four exposed knobs — `defocus_nm`, `defect_density`, `slice_z`,
    `oxide_minutes` — plus an integer `seed`. Textual `Input` (numeric) or `Slider` widgets; an
    explicit *Run* binding (or reactive-on-change) re-invokes `run_dashboard`.
  - **A wafer-map panel** rendering `wafer_map_text(result.wafer)` (green pass / red fail on the
    circle — the terminal analog of `dashboard_figure`).
  - **A summary panel** (`Static`) showing `dashboard_summary(result)` verbatim — headline yield /
    mean `V_t` / mean `I_Dsat` + the worst dead die's failure trail.
  - Deterministic in `(seed, knobs)` — the roguelike "seed" contract, inherited free from
    `run_dashboard`.

- **The one new headless helper — `fab_game/plots.wafer_map_text(wafer) -> str`.** An ASCII
  rendering of the die map: pass = a green glyph, fail = a red one, laid on the wafer circle,
  built **purely from `wafer.dies`** (each die already carries `radius_frac` + `verdict.passed`).
  This is **not speculative** — `plots._wafer_map` (the matplotlib panel `dashboard_figure` draws)
  *already* places the dies spatially; `wafer_map_text` reuses that same per-die placement, just
  emitting characters instead of patches. It lives in `plots.py` (peer to `dashboard_figure`) and
  is a **pure function tested without Textual** — the same reason §9 put the load-bearing run +
  summary *outside* `interact`: Textual, like `interact`, can swallow a callback exception and
  leave the surface looking green, so the load-bearing string-building must be testable on its own.

**Why this respects the doctrine.** ADR 0002 §4's progressive-enhancement ladder already sanctions
"an interactive surface per pedagogy" behind the headless data boundary; `[viz]` (matplotlib) and
`[notebook]` (ipywidgets) are the standing precedent that a *new interactive surface rides 0002's
umbrella without its own ADR*. `run_dashboard → LineResult` **is** that array-out boundary. ADR
0005's "no game engine as authority; thin UI" is satisfied by construction — the TUI computes
nothing. **So: no new ADR.** (Optional: a one-line status note appended to ADR 0002 acknowledging
the TUI as a realized interactive target — nice-to-have, not required.)

## 3. Dependency

A new optional-extra in `pyproject.toml`, mirroring `[viz]` / `[notebook]`:

```toml
[project.optional-dependencies]
tui = ["textual>=0.5"]
```

- `textual` is imported **only** by `fab_game/tui.py` and gated in its test by `importorskip`.
- The compute core (`numpy`/`scipy`) and the always-on test suite stay **headless** — `textual`
  never enters the fast lane uninstalled. Install for use with `pip install -e .[tui]`.

## 4. Test plan (the section to get right — this repo has async-test scar tissue)

`fab_game/tests/test_tui.py`, mirroring `test_dashboard.py`'s discipline (mechanics not magnitudes,
ADR 0005 §5; the render is a "builds without error" smoke test, ADR 0002):

1. **The pure map renderer — tested with no Textual at all.** `wafer_map_text(wafer)` over a known
   wafer: a clean run's grid carries the pass glyph and no fail glyph; a defocus wipeout carries the
   fail glyph; the string has the expected die count / shape. This is the load-bearing,
   Textual-independent leg.

2. **The App smoke test — `importorskip("textual")` + Textual's `run_test()` pilot.** `run_test()`
   is an **async context manager**, so the concrete driver decision (named here, not glossed) is: a
   **manual `asyncio.run(...)` wrapper inside a sync test — NOT a new `pytest-asyncio` dependency**
   (keeps `[test]` = `pytest` + `pytest-xdist` only, the lean-dep posture). Shape:

   ```python
   def test_app_runs_the_line_and_shows_the_summary():
       pytest.importorskip("textual")
       import asyncio
       from fab_game.tui import FabLineApp

       async def scenario():
           app = FabLineApp()
           async with app.run_test() as pilot:
               # default knobs → clean wafer; summary panel shows the seam
               await pilot.pause()
               assert "clean wafer" in app.query_one("#summary", ...).renderable  # or app state
       asyncio.run(scenario())
   ```

   Assert against the App's own state / queried widget text — e.g. default knobs → "clean wafer";
   a `defocus_nm=250` run → "FAIL" / "litho" / "NILS" in the summary (the same strings
   `test_dashboard.py` already pins on `dashboard_summary`). Keep widget-internal assertions thin —
   the *content* is already covered by the `dashboard_summary` tests; this leg only proves the App
   wires input → `run_dashboard` → panels.

3. **xdist-safety — a verification step with an escape hatch, NOT a flat claim.** The chip-notebook
   flake (memory: `chip-notebook-flake`) was *precisely* an async/event-loop test that raced under
   `-n auto`; so we do **not** assert "fast and xdist-safe" up front. Textual's `run_test()` is an
   **in-process** asyncio loop (no subprocess, no zmq/Jupyter kernel), so the *expectation* is that
   it is fast and parallel-safe and rides the fast lane like any other test. **The build step is to
   verify that** — run it under `pytest -n auto` a handful of times. **Escape hatch if it flakes:**
   it inherits the notebook's exact remedy — `@pytest.mark.slow` + `@pytest.mark.xdist_group("slow")`
   so it drops off the fast lane and never co-schedules under xdist. This is the honest framing given
   the documented hazard; it costs nothing to write down now.

## 5. The seam & acceptance criteria

- **Seam (default knobs).** `FabLineApp` opened at default knobs runs `dashboard_recipe()` ==
  `DEFAULT_RECIPE` → a **clean wafer** (100 % yield), and the summary panel reads `dashboard_summary`
  of that clean run ("yield 100% … clean wafer"). The TUI adds no state that perturbs the line.
- **Fidelity to the core.** Every number/string the TUI shows is `dashboard_summary` /
  `wafer_map_text` verbatim — the TUI never recomputes. A run at `(seed, knobs)` matches the
  headless `run_dashboard(seed=…, **knobs)` exactly.
- **Determinism.** Same `(seed, knobs)` → same wafer map + summary (inherited from `run_dashboard`).
- **Headless-safe.** With `textual` absent, the suite is green (the App test `importorskip`-skips;
  the map-renderer test still runs). The fast lane never imports `textual`.
- **Mechanics, not magnitudes** (ADR 0005 §5): the App test proves *wiring* (input → run → panels),
  not physics — the physics is already validated upstream.

## 6. Home of this doc & the stubs to link

This is a dedicated file (one of two equally-good choices — the other being a new subsection inside
`fab-game.md`, where every G-step lives; chosen dedicated for a front-end that will grow when built).
On landing, the existing TUI stubs point here: **fab-game.md §9** ("A Textual TUI next") and the
**G7 BUILT note** ("the TUI is deliberately deferred"). Memory: do **not** write a "BUILT" memory for
this — at most append "(plan drafted at `docs/plans/fab-game-tui.md`)" to the existing
`[[fab-game]]` "Textual TUI deferred" line when convenient.

## 7. v2 — the roguelike loop (**BUILT 2026-06-14**)

As sketched and built: a second Textual screen (`RoguelikeScreen`) driving `fab_game.game.GameSession`
— `process_wafer` / `scrap_wafer` / the oxide-thinning *adapt* lever — down one boule (one run),
surfacing the G2 Scheil `V_t` drift as the difficulty curve (the `inspect_line` decision support) and the
`ScoreCard` (budget / score / per-turn profit + bin mix) as the running ledger. A thin driver: `game.py`
owns the session model and the new headless `session_view.py` owns the strings (both tested without
Textual — the §9/§4 discipline that the load-bearing string-building lives outside the swallow-prone
interactive surface); the screen only renders them and binds buttons.

**Two as-built notes beyond the sketch.** (a) *No wafer map on this screen* — the `RunRecord` carries no
`WaferState`, and the spatial map is the dashboard screen's job; the roguelike screen is the
economic/decision arc (header + inspect + ledger). (b) *Actions are Buttons, not the sketched "binds
keys"* — the oxide `Input` is auto-focused, so a single-letter action binding would be shadowed the
moment the player edits it (the same footgun §4/`FabLineApp` documents); only `escape`/`q` (non-contextual)
are bindings. The action handlers no-op + the buttons disable once `session.done` (the model *raises* when
the run is over — a thin driver must never let that throw into the swallow-prone loop).

The tycoon economy stays deferred (ADR 0005).

## 9. Educational vs Hardcore launch mode (**BUILT 2026-06-14**)

A launch-time choice layered on the built TUI: `python -m fab_game.tui` now opens a `ModeSelectScreen`
(two Buttons + the `MODE_INTRO` blurb) before the dashboard. **Hardcore** is the bare cockpit — the TUI
exactly as v1/v2 shipped. **Educational** adds a verbatim **guide panel** to both the dashboard and the
roguelike screen: a plain-language glossary of every selector + readout (defocus, defect density, boule
slice z, gate-oxide drive, seed, V_t, I_Dsat, NILS, CD, leakage, the bins, the Scheil drift, the failure
trail, process/adapt/scrap) plus *what-to-do* strategy — exploratory on the dashboard ("crank defocus →
watch the ring die"), the decision on the roguelike screen ("the tail forces adapt-vs-scrap; mind the
I_Dsat ceiling").

**As-built shape — the same doctrine as the rest of this plan.** The load-bearing prose lives in a new
import-pure module **`fab_game/guide.py`** (`dashboard_guide` / `roguelike_guide` / `glossary_text` /
`MODE_INTRO`, re-exported from `__init__`, tested by `tests/test_guide.py` *without* textual); the TUI
renders those strings **verbatim** (the App composes no prose). Educational mode is **presentation only**
— no knob, recipe, or physics changes — so:

- **The seam is byte-identical.** `FabLineApp(educational=False)` (the default; what the existing pilots
  construct) is unchanged, and the guide panel is `display: none` in hardcore → it reserves no space, so
  the hardcore layout and the `pilot.click("#run")`/`#play-game` legs are untouched. The clean default
  wafer (the §5 seam) is the same in both modes.
- **Two flags, forced by "don't break the pilots."** `FabLineApp(educational: bool, prompt_mode: bool)`:
  the pilots build `FabLineApp(educational=…)` directly (no chooser); only `main()` passes
  `prompt_mode=True` to open the `ModeSelectScreen`. The mode-screen picks the mode (`apply_mode`) and
  pops back to the dashboard underneath — which already rendered its clean seam on mount.
- **Tests** (mechanics, ADR 0005 §5): `test_guide.py` pins the *completeness* (every named concept +
  every dashboard selector has a glossary entry) and that each guide mentions them + carries its
  what-to-do block; the import-purity leg runs in a **fresh subprocess** (not this process's
  `sys.modules`, which a co-scheduled `test_tui` pilot pollutes with textual under `-n auto`). New
  `test_tui.py` legs prove the chooser wires (Educational shows the guide, Hardcore hides it, the line
  stays the seam) and that *Play roguelike* inherits the mode. Verified green serially and under
  `-n auto` (no notebook-style flake).

No new physics, no engine touch, no new ADR — additive game-layer UI under ADR 0002/0005, exactly like
§9 of the main plan and the v1/v2 TUI.

## 8. What this is NOT

- **Not new physics / not a new device output** — pure front-end over `run_dashboard`.
- **Not an engine touch, not an ADR** — additive game-layer UI under ADR 0002/0005 (like §9).
- **Not the tycoon** — the economy layer is a separately-deferred item.
- **Not a full spec** — a deferred-build shape doc; widget-level layout is settled at build time.
