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

Run it with ``pip install -e .[tui]`` then ``python -m fab_game.tui``.
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Static

from .dashboard import dashboard_summary, run_dashboard
from .plots import wafer_map_text

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
    """

    TITLE = "fab-line — command the whole line"
    SUB_TITLE = "a thin terminal skin over the validated line (run_dashboard)"

    CSS = """
    #body { height: 1fr; }
    #controls { width: 38; padding: 1 2; border-right: solid $panel; }
    #controls Label { margin-top: 1; color: $text-muted; }
    #controls Input { margin-bottom: 0; }
    #run { margin-top: 2; width: 100%; }
    #panels { padding: 1 2; }
    #wafer { height: auto; padding: 1 0; }
    #map-legend { color: $text-muted; }
    #summary { height: auto; padding: 1 0; border-top: solid $panel; }
    """

    # No keyboard run binding: a single-letter binding is shadowed the moment a knob Input has focus
    # (the common case right after editing), where the keystroke goes to the field instead — a
    # misleading footer affordance. The real run paths are the *Run* button and Enter in any field
    # (``on_input_submitted``). Quit stays (it is not contextual).
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        # The last rendered strings — stashed for the test to assert on (decoupled from widget
        # internals) and to make the "the TUI never recomputes" fidelity check trivial.
        self.last_summary: str = ""
        self.last_map: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="controls"):
                for key, label, default in _KNOB_FIELDS:
                    yield Label(label)
                    yield Input(value=default, id=f"in-{key}", type="number")
                yield Button("Run the line", id="run", variant="primary")
            with Vertical(id="panels"):
                yield Static(id="wafer", markup=True)          # controlled glyphs + [green]/[red] tags
                yield Label("O pass   X fail", id="map-legend")
                yield Static(id="summary", markup=False)        # arbitrary computed text — no markup
        yield Footer()

    def on_mount(self) -> None:
        """Open on the seam: run the default (clean) knobs so the first frame is the validated baseline."""
        self._run_and_render()

    # --- the wiring: input → run → panels (one synchronous path, shared by mount/button/enter) --- #
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            self._run_and_render()

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
            except (TypeError, ValueError):
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
        """
        knobs = self._knobs()
        result = run_dashboard(**knobs)
        self.last_map = wafer_map_text(result.wafer, color=True)
        self.last_summary = dashboard_summary(result)
        self.query_one("#wafer", Static).update(self.last_map)
        self.query_one("#summary", Static).update(self.last_summary)


def main() -> None:
    """Launch the TUI (the ``python -m fab_game.tui`` entry point)."""
    FabLineApp().run()


if __name__ == "__main__":
    main()
