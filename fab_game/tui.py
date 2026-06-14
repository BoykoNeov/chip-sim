"""The deferred Textual front-end — command the whole line from the terminal (the §9 TUI).

The terminal twin of the §9 ipywidgets slice (plan ``docs/plans/fab-game-tui.md``; ADR 0002/0005):
a **thin driver** of the already-validated, already-tested headless core
(:func:`fab_game.dashboard.run_dashboard` / :func:`~fab_game.dashboard.dashboard_summary` /
:func:`fab_game.plots.wafer_map_text`). The same four legible knobs + a seed, a live ASCII wafer
map, the headline readout + the worst-die failure trail. **Zero new physics, no engine touch, no
new device output** — the App computes nothing; every number/string it shows is the headless core
verbatim.

This is the **only** module that imports ``textual`` (the opt-in ``[tui]`` extra), and — like
:mod:`fab_game.plots` (matplotlib) — it is **not** re-exported from :mod:`fab_game.__init__`, so
``import fab_game`` and the always-on test suite stay headless. The load-bearing run + summary +
map live *outside* this surface (in ``dashboard``/``plots``) and are tested there: Textual, like
``ipywidgets.interact``, can swallow a callback exception and still look green, so the validated
work must be testable without it.

**The v2 follow-on lives here too** (plan §7): :class:`RoguelikeScreen` is the G7 roguelike loop —
a second screen driving :mod:`fab_game.game`'s :class:`~fab_game.game.GameSession` down one boule
(process / scrap / adapt a slice, watch the Scheil ``V_t`` drift, scored). Same doctrine: the session
model (``game.py``) and its renderers (``session_view.py``) are headless and tested; the screen only
binds buttons to them and renders the strings verbatim. :class:`FabLineApp` opens it from a *Play
roguelike* button (a button, not a shadowed letter binding); ``escape`` pops back.

Run it with ``pip install -e .[tui]`` then ``python -m fab_game.tui``.
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from .dashboard import dashboard_summary, knob_errors, oxide_minutes_error, run_dashboard
from .game import GameConfig, GameSession, new_session, process_wafer, scrap_wafer
from .guide import MODE_INTRO, dashboard_guide, roguelike_guide
from .plots import wafer_map_text
from .recipe import Recipe
from .session_view import (
    history_trail,
    inspect_line,
    oxide_recipe,
    session_header,
    session_summary,
)

# The four exposed knobs + the seed, each (run_dashboard kwarg, label, default). These are the §9
# dramatic/legible levers — defocus (the focus bowl's edge ring), defect density (scattered kills),
# slice z (the Scheil V_t walk), the gate-oxide drive (the "adapt" lever) — plus the roguelike seed.
# Every other recipe knob stays at its DEFAULT_RECIPE value, so the empty/default form is the seam.
_KNOB_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("defocus_nm", "Defocus (nm)", "0"),
    ("defect_density", "Defect density (cm⁻²)", "0"),
    ("slice_z", "Boule slice z [0,1)", "0"),
    ("oxide_minutes", "Gate-oxide drive (min)", "20"),
    ("seed", "Seed", "0"),
)


class FabLineApp(App):
    """A Textual App that drives :func:`fab_game.dashboard.run_dashboard` and renders the result.

    One screen: a column of knob inputs + a *Run* button on the left; the live wafer map and the
    summary/failure-trail panel on the right. Opening the App runs the default knobs — the
    ``DEFAULT_RECIPE`` seam → a clean 100 % wafer — so the player departs from the validated baseline.
    Deterministic in ``(seed, knobs)`` (inherited from ``run_dashboard``).

    **The launch-time mode** (``educational`` / ``prompt_mode``). Hardcore (``educational=False``, the
    default) is the bare cockpit — exactly today's TUI. Educational (``educational=True``) adds a
    **guide panel** on the right (the headless :func:`fab_game.guide.dashboard_guide` text, rendered
    verbatim) explaining every selector + readout and *what to try*; it is **presentation only** —
    no knob, recipe, or physics changes, so the seam (the clean default wafer) is byte-identical and
    the guide is hidden (``display: none`` → reserves no space) in hardcore. ``prompt_mode=True`` (the
    ``python -m fab_game.tui`` launch) opens a :class:`ModeSelectScreen` so the player picks the mode
    first; the pilot tests construct ``FabLineApp(educational=…)`` directly (no prompt), so they are
    unaffected.
    """

    TITLE = "fab-line — command the whole line"
    SUB_TITLE = "a thin terminal skin over the validated line (run_dashboard)"

    CSS = """
    #body { height: 1fr; }
    #controls { width: 38; padding: 1 2; border-right: solid $panel; }
    #controls Label { margin-top: 1; color: $text-muted; }
    #controls Input { margin-bottom: 0; }
    #run { margin-top: 2; width: 100%; }
    #play-game { margin-top: 1; width: 100%; }
    #panels { padding: 1 2; }
    #wafer { height: auto; padding: 1 0; }
    #map-legend { color: $text-muted; }
    #summary { height: auto; padding: 1 0; border-top: solid $panel; }
    /* The educational guide panel — hidden in hardcore (display:none reserves no space, so the
       hardcore layout is byte-identical); shown by _refresh_guide when educational. */
    #guide-box { display: none; height: 1fr; padding: 1 0; border-top: solid $panel; }
    #guide-box.shown { display: block; }
    #guide { color: $text-muted; }
    """

    # No keyboard run binding: a single-letter binding is shadowed the moment a knob Input has focus
    # (the common case right after editing), where the keystroke goes to the field instead — a
    # misleading footer affordance. The real run paths are the *Run* button and Enter in any field
    # (``on_input_submitted``). Quit stays (it is not contextual).
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, *, educational: bool = False, prompt_mode: bool = False) -> None:
        super().__init__()
        # The mode: hardcore (False) is today's bare cockpit; educational (True) shows the guide panel.
        # prompt_mode opens the ModeSelectScreen at launch so the player picks — set only by main(), so
        # the pilot tests that build FabLineApp(educational=…) directly never see the chooser.
        self.educational: bool = educational
        self._prompt_mode: bool = prompt_mode
        # The last rendered strings — stashed for the test to assert on (decoupled from widget
        # internals) and to make the "the TUI never recomputes" fidelity check trivial.
        self.last_summary: str = ""
        self.last_map: str = ""
        self.last_guide: str = dashboard_guide()       # the verbatim guide text (static; shown when educational)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="controls"):
                for key, label, default in _KNOB_FIELDS:
                    yield Label(label)
                    yield Input(value=default, id=f"in-{key}", type="number")
                yield Button("Run the line", id="run", variant="primary")
                yield Button("Play roguelike →", id="play-game")
            with Vertical(id="panels"):
                yield Static(id="wafer", markup=True)          # controlled glyphs + [green]/[red] tags
                yield Label("O pass   X fail", id="map-legend")
                yield Static(id="summary", markup=False)        # arbitrary computed text — no markup
                with VerticalScroll(id="guide-box"):            # educational only (hidden in hardcore)
                    yield Static(self.last_guide, id="guide", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        """Open on the seam: run the default (clean) knobs so the first frame is the validated baseline.

        Then reflect the current mode (show/hide the guide) and — on the real launch path
        (``prompt_mode``) — push the :class:`ModeSelectScreen` so the player picks educational vs hardcore.
        """
        self._run_and_render()
        self._refresh_guide()
        if self._prompt_mode:
            self.push_screen(ModeSelectScreen())

    def apply_mode(self, educational: bool) -> None:
        """Set the mode (the :class:`ModeSelectScreen` callback) and show/hide the guide panel accordingly."""
        self.educational = educational
        self._refresh_guide()

    def _refresh_guide(self) -> None:
        """Toggle the guide panel to match :attr:`educational` (render-only; never touches the line)."""
        self.query_one("#guide-box").set_class(self.educational, "shown")

    # --- the wiring: input → run → panels (one synchronous path, shared by mount/button/enter) --- #
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            self._run_and_render()
        elif event.button.id == "play-game":
            # the v2 roguelike loop (one boule, scored) — inherits the chosen mode
            self.push_screen(RoguelikeScreen(educational=self.educational))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._run_and_render()                                  # Enter in any field re-runs the line

    def _knobs(self) -> dict:
        """Read the input fields into ``run_dashboard`` kwargs, falling back to the default on bad input.

        Inputs are strings (and may be transiently empty mid-edit), so each parse is guarded — a
        malformed field uses its declared default rather than crashing the run. ``seed`` is an int
        (``int(float(...))`` so ``"3"`` and ``"3.0"`` both work); the rest are floats.
        """
        raw = {key: self.query_one(f"#in-{key}", Input).value for key, _, _ in _KNOB_FIELDS}
        defaults = {key: default for key, _, default in _KNOB_FIELDS}

        def num(key: str, cast) -> float | int:
            try:
                return cast(raw[key])
            except (TypeError, ValueError, ArithmeticError):     # ArithmeticError: int(float("1e999")) overflows
                return cast(defaults[key])

        return dict(
            defocus_nm=num("defocus_nm", float),
            defect_density=num("defect_density", float),
            slice_z=num("slice_z", float),
            oxide_minutes=num("oxide_minutes", float),
            seed=num("seed", lambda v: int(float(v))),
        )

    def _run_and_render(self) -> None:
        """Run the line at the current knobs and repaint both panels — the only place compute happens.

        Synchronous on purpose (``run_dashboard`` is plain CPU, sub-second): after one event-loop
        pause the panels are populated, which keeps the pilot test deterministic. The App **never**
        recomputes the readout — it renders the headless ``dashboard_summary`` / ``wafer_map_text``
        of the run verbatim.

        An out-of-domain-but-parseable knob (``slice_z`` outside ``[0, 1)``, a non-positive oxide bake)
        would otherwise make ``run_dashboard`` **raise** a ``ValueError`` straight into this Textual
        handler and kill the App, so a bad value is pre-screened (:func:`fab_game.dashboard.knob_errors`)
        into a readable note — and the run itself is wrapped as a belt-and-suspenders net (any domain raise
        we did not pre-screen still becomes a panel message, never an uncaught exception in the event loop).
        """
        knobs = self._knobs()
        errors = knob_errors(slice_z=knobs["slice_z"], oxide_minutes=knobs["oxide_minutes"],
                             defect_density=knobs["defect_density"])
        if errors:
            self.last_summary = ("Out-of-range knob — adjust it and run again:\n"
                                 + "\n".join(f" • {e}" for e in errors))
            self.query_one("#summary", Static).update(self.last_summary)
            return                                              # leave the wafer map on the last good run
        try:
            result = run_dashboard(**knobs)
        except (ValueError, ArithmeticError) as exc:            # the net: a domain raise we did not pre-screen
            self.last_summary = f"Could not run the line — {exc}"
            self.query_one("#summary", Static).update(self.last_summary)
            return
        self.last_map = wafer_map_text(result.wafer, color=True)
        self.last_summary = dashboard_summary(result)
        self.query_one("#wafer", Static).update(self.last_map)
        self.query_one("#summary", Static).update(self.last_summary)


class ModeSelectScreen(Screen):
    """The launch chooser: *Educational* (guided + explained) vs *Hardcore* (the bare cockpit).

    A thin front gate opened by :meth:`FabLineApp.on_mount` when the App is launched with
    ``prompt_mode=True`` (the ``python -m fab_game.tui`` path). It shows the headless
    :data:`fab_game.guide.MODE_INTRO` describing the two modes, and two Buttons; a press calls
    :meth:`FabLineApp.apply_mode` (which shows/hides the guide panel) and pops back to the dashboard
    underneath — which already rendered its clean seam on mount, so the choice only toggles the
    *presentation*. Like the other screens, the affordances are **Buttons, not single-letter
    bindings** (consistent with the documented footgun); ``q`` quits.
    """

    BINDINGS = [("q", "quit", "Quit")]

    CSS = """
    #mode-box { padding: 1 2; align: center middle; }
    #mode-intro { padding: 1 2; }
    #mode-buttons { height: auto; align: center middle; }
    #mode-buttons Button { margin: 1 2; min-width: 24; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="mode-box"):
            yield Static(MODE_INTRO, id="mode-intro", markup=False)
            with Horizontal(id="mode-buttons"):
                yield Button("Educational", id="mode-edu", variant="primary")
                yield Button("Hardcore", id="mode-hard")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Pick the mode (Educational/Hardcore), apply it to the dashboard, and reveal it (pop this gate)."""
        if event.button.id in ("mode-edu", "mode-hard"):
            self.app.apply_mode(event.button.id == "mode-edu")
            self.app.pop_screen()


class RoguelikeScreen(Screen):
    """The G7 roguelike loop (TUI v2): play one boule — process or scrap each slice, scored, on a budget.

    The deferred §7 follow-on (``docs/plans/fab-game-tui.md``): a second screen driving
    :mod:`fab_game.game`'s :class:`~fab_game.game.GameSession` down one boule (one run, each wafer a
    turn). One Input — the gate-oxide drive, the *adapt* lever — plus *Process* / *Scrap* / *New run*
    buttons; the three panels are the headless :mod:`fab_game.session_view` renderers verbatim (the
    status header, the next-slice *inspect* decision support, the append-only turn ledger). The
    difficulty curve is physics, not invention — the G2 Scheil ``V_t`` drift walks the substrate doping
    up the boule, so the tail forces the process/adapt/scrap call the inspect panel supports.

    A **thin driver** (ADR 0005): the screen computes nothing — ``game.py`` owns the session model
    (headless, tested) and ``session_view`` owns the strings (headless, tested). Like
    :class:`FabLineApp`, the action affordances are **Buttons, not single-letter bindings**: the oxide
    Input is auto-focused, so a letter binding would be shadowed the moment the player edits it (the
    documented footgun). Only ``escape`` / ``q`` — non-contextual, not key-captured by a focused Input —
    are bindings. Deterministic in ``(seed, decisions)`` (inherited from ``game.py``): the same actions
    reproduce the same session, so a playthrough equals the headless ``play(new_session(...), [...])``.
    """

    BINDINGS = [("escape", "app.pop_screen", "Back"), ("q", "quit", "Quit")]

    CSS = """
    #game-body { height: 1fr; }
    #game-controls { width: 44; padding: 1 2; border-right: solid $panel; }
    #game-controls Label { margin-top: 1; color: $text-muted; }
    #game-controls Button { margin-top: 1; width: 100%; }
    #game-panels { padding: 1 2; }
    #game-header { height: auto; padding: 1 0; }
    #inspect { height: auto; padding: 1 0; color: $text-muted; }
    #trail-legend { margin-top: 1; color: $text-muted; }
    #trail { height: 1fr; padding: 1 0; border-top: solid $panel; }
    /* The educational guide — hidden in hardcore (display:none reserves no space); shown when educational. */
    #game-guide-box { display: none; height: 1fr; padding: 1 0; border-top: solid $panel; }
    #game-guide-box.shown { display: block; }
    #game-guide { color: $text-muted; }
    """

    def __init__(self, config: GameConfig | None = None, *, seed: int = 0,
                 educational: bool = False) -> None:
        super().__init__()
        self._config = config if config is not None else GameConfig()
        self._seed = seed
        self._educational = educational                # presentation only — shows the roguelike guide panel
        self.session: GameSession = new_session(self._config, seed=seed)
        # The last-rendered strings — stashed for the test (decoupled from widget internals) and to make
        # the "the screen never recomputes" fidelity check trivial (mirrors FabLineApp.last_summary).
        self.last_header: str = ""
        self.last_inspect: str = ""
        self.last_trail: str = ""
        self.last_guide: str = roguelike_guide()       # the verbatim guide text (static; shown when educational)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="game-body"):
            with Vertical(id="game-controls"):
                yield Label("Gate-oxide drive (min) — thin it to pull V_t back (the adapt lever)")
                yield Input(value=f"{self._config.base_recipe.oxidation.minutes:g}",
                            id="in-oxide", type="number")
                yield Button("Process wafer", id="process", variant="primary")
                yield Button("Scrap wafer", id="scrap", variant="warning")
                yield Button("New run", id="reset")
                yield Button("Back to dashboard", id="back")
            with Vertical(id="game-panels"):
                yield Static(id="game-header", markup=False)
                yield Static(id="inspect", markup=False)
                yield Label("— turn history —", id="trail-legend")
                yield Static(id="trail", markup=False)
                with VerticalScroll(id="game-guide-box"):       # educational only (hidden in hardcore)
                    yield Static(self.last_guide, id="game-guide", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        """Open on a fresh run: the seam recipe at the seed slice → the inspect panel shows the baseline."""
        self._repaint()
        self.query_one("#game-guide-box").set_class(self._educational, "shown")

    # --- the wiring: button → session action → panels (the screen computes nothing) --- #
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "process":
            self._apply_action(lambda s: process_wafer(s, self._oxide_recipe()))
        elif bid == "scrap":
            self._apply_action(scrap_wafer)
        elif bid == "reset":
            self.session = new_session(self._config, seed=self._seed)
            self._repaint()
        elif bid == "back":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter in the oxide field **previews** the new knob (non-destructive); *Process* commits the turn."""
        self._repaint()

    def _oxide_minutes(self) -> float:
        """The oxide-drive field as minutes (the adapt lever), falling back to the base recipe on bad input.

        Guarded like the dashboard's ``_knobs``: a malformed / transiently-empty / overflowing field
        (e.g. ``"1e999"`` → ``OverflowError``) falls back to the base recipe's oxide minutes rather than
        crashing the turn. (Whether the parsed value is *in domain* — > 0 min — is a separate check,
        :func:`fab_game.dashboard.oxide_minutes_error`, used by :meth:`_repaint` / :meth:`_apply_action`.)
        """
        base = self._config.base_recipe
        raw = self.query_one("#in-oxide", Input).value
        try:
            return float(raw)
        except (TypeError, ValueError, ArithmeticError):
            return base.oxidation.minutes

    def _oxide_recipe(self) -> Recipe:
        """The current oxide knob as a recipe (the adapt lever) — the base recipe's drive set to the field."""
        return oxide_recipe(self._oxide_minutes(), base=self._config.base_recipe)

    def _apply_action(self, action) -> None:
        """Apply a session action (process / scrap), guarding the run-over case + a bad knob, then repaint.

        ``process_wafer`` / ``scrap_wafer`` **raise** once the run is over; a thin driver must never call
        them when done. The buttons are also disabled in :meth:`_repaint` once ``done`` (the honest
        affordance) — this guard is the belt to those suspenders, so a stray event can never throw into
        the event loop (which Textual could swallow — the failure the headless-core doctrine guards
        against). The second net catches a domain raise from the line itself: *Process* runs ``run_line``
        at the oxide knob, so a non-positive bake (which :meth:`_repaint` already pre-screens in the
        preview) becomes a readable note here too rather than an uncaught exception.
        """
        if self.session.done:
            return
        try:
            self.session = action(self.session)
        except (ValueError, ArithmeticError) as exc:            # a bad-knob domain raise — never into the loop
            self.last_inspect = f"Can't process this turn — {exc}"
            self.query_one("#inspect", Static).update(self.last_inspect)
            return
        self._repaint()

    def _repaint(self) -> None:
        """Repaint every panel from the current session via the headless ``session_view`` renderers.

        The only place the screen touches ``session_view``; it renders the strings verbatim and never
        recomputes a number. The inspect panel previews the next slice under the **current** oxide knob
        (so editing the field + Enter re-previews); once the run is over it shows the end-of-run tally
        and *Process* / *Scrap* are disabled.
        """
        s = self.session
        self.last_header = session_header(s)
        self.last_trail = history_trail(s)
        if s.done:
            self.last_inspect = session_summary(s)
        else:
            # the preview runs the line (inspect_line → projected_vt → run_line), so a non-positive oxide
            # bake would raise into the event loop — pre-screen it with the same readable note as Process.
            err = oxide_minutes_error(self._oxide_minutes())
            self.last_inspect = err if err is not None else inspect_line(s, self._oxide_recipe())
        self.query_one("#game-header", Static).update(self.last_header)
        self.query_one("#inspect", Static).update(self.last_inspect)
        self.query_one("#trail", Static).update(self.last_trail)
        done = s.done
        self.query_one("#process", Button).disabled = done
        self.query_one("#scrap", Button).disabled = done


def main() -> None:
    """Launch the TUI (the ``python -m fab_game.tui`` entry point) — prompt for the mode first."""
    FabLineApp(prompt_mode=True).run()


if __name__ == "__main__":
    main()
