# Plan — fab-game Textual TUI (the deferred terminal front-end)

Status: **Planned, not built** (drafted 2026-06-14). A *deferred-build* shape doc — decisions,
risks, and the seam/acceptance criteria, **not** a full spec. Build when wanted.

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

## 7. v2 sketch — the roguelike loop (deferred)

When v1 is banked and a session loop is wanted: add a second Textual screen driving
`fab_game.game.GameSession` — `process_wafer` / `scrap_wafer` / the oxide-thinning *adapt* lever —
down one boule (one run), surfacing the G2 Scheil `V_t` drift as the difficulty curve and the
`ScoreCard` (budget / revenue / profit) as the running score. Still a thin driver: `game.py` already
owns the entire session model headless and tested (G7); the screen only renders it and binds keys.
The tycoon economy stays deferred (ADR 0005).

## 8. What this is NOT

- **Not new physics / not a new device output** — pure front-end over `run_dashboard`.
- **Not an engine touch, not an ADR** — additive game-layer UI under ADR 0002/0005 (like §9).
- **Not the tycoon** — the economy layer is a separately-deferred item.
- **Not a full spec** — a deferred-build shape doc; widget-level layout is settled at build time.
