"""The guided slider-driven slice — drive the whole line live and watch the wafer map + trail.

The §9 "first" UX step (plan ``docs/plans/fab-game.md`` §9; ADR 0002/0005): a thin, *importable*
skin that runs the already-validated line at a handful of the principal knobs and bundles the
result for the notebook to render. **Zero new physics** — it builds a :class:`~fab_game.recipe.Recipe`
from the exposed knobs, calls :func:`fab_game.run_line` (with the within-wafer
:class:`~fab_game.variation.Variation` **on**, so the die map shows real spatial structure — an
off-variation run collapses every die to the one nominal identity and the map is a binary all-pass /
all-fail flip, not a story), and returns the existing :class:`~fab_game.pipeline.LineResult` bundle.

**Why this is a module, not just an ``interact`` cell.** ``ipywidgets.interact`` runs its callback
inside an ``Output`` context that *captures* exceptions and paints them as cell output instead of
re-raising — so a broken call inside the slider would leave the notebook green and the breakage
untested. The load-bearing run + summary therefore live here and are smoke-tested by
``tests/test_dashboard.py`` (the same discipline ``chip/tests/test_chip_notebook.py`` states: the
validated calls go in importable/direct cells, the ``interact`` cells are sugar on top). The notebook
is a thin driver of these functions.

The exposed knobs are the dramatic, **legible** levers — not the full recipe:

* ``defocus_nm`` — the G1 focus error; with the center-to-edge focus bowl
  (:class:`~fab_game.variation.Variation`) it kills an **edge ring** (the canonical map-texture story).
* ``defect_density`` — the G3 killer-particle level (cm⁻²); scattered functional kills (the other
  map-texture story).
* ``slice_z`` — the axial boule position; Scheil segregation walks the substrate doping (hence
  ``V_t``) up the boule (the G2 difficulty curve — a roughly uniform shift → a yield/trail story).
* ``oxide_minutes`` — the gate-oxide drive; thinning the oxide lowers ``V_t`` (the G7 "adapt" lever
  that pulls the drifted tail back into spec).

Every other knob (purification grade, etch over/under-etch, the OSF/CG crystal-growth deepenings)
stays at its default and keeps its **own** focused demo — this is a guided slice, not a cockpit.
"""
from __future__ import annotations

from dataclasses import replace

from .pipeline import LineResult, diagnose, run_line
from .recipe import DEFAULT_RECIPE, Recipe
from .spec import DEFAULT_SPECS
from .variation import Variation


def dashboard_recipe(
    *,
    defocus_nm: float = 0.0,
    slice_z: float = 0.0,
    oxide_minutes: float = 20.0,
    defect_density: float = 0.0,
) -> Recipe:
    """Build a :class:`~fab_game.recipe.Recipe` from the dashboard's four exposed knobs.

    Every other knob group is left at :data:`~fab_game.recipe.DEFAULT_RECIPE` (the
    ``chip.demo_device`` seam), so at the default arguments this is ``DEFAULT_RECIPE`` exactly.
    """
    cz = DEFAULT_RECIPE.czochralski
    return replace(
        DEFAULT_RECIPE,
        litho=replace(DEFAULT_RECIPE.litho, defocus_nm=float(defocus_nm)),
        czochralski=replace(cz, slice_z=float(slice_z)),
        oxidation=replace(DEFAULT_RECIPE.oxidation, minutes=float(oxide_minutes)),
        wafer_prep=replace(DEFAULT_RECIPE.wafer_prep, defect_density=float(defect_density)),
    )


def run_dashboard(
    *,
    defocus_nm: float = 0.0,
    slice_z: float = 0.0,
    oxide_minutes: float = 20.0,
    defect_density: float = 0.0,
    seed: int = 0,
    grid_n: int = 9,
) -> LineResult:
    """Run the line at the exposed knobs (within-wafer :class:`Variation` **on**) → a :class:`LineResult`.

    The map needs the stochastic spread on to show spatial structure — the focus bowl's edge ring,
    the scattered particle kills — so this passes ``Variation()`` (unlike the headless demos that
    isolate one cause with ``NO_VARIATION``). Deterministic in ``seed`` (a roguelike "seed"): a given
    ``(seed, knobs)`` reproduces the wafer exactly.
    """
    recipe = dashboard_recipe(defocus_nm=defocus_nm, slice_z=slice_z,
                              oxide_minutes=oxide_minutes, defect_density=defect_density)
    wafer = run_line(recipe, seed=seed, variation=Variation(), specs=DEFAULT_SPECS, grid_n=grid_n)
    label = (f"defocus {defocus_nm:.0f} nm · slice z={slice_z:.2f} · "
             f"t_ox {oxide_minutes:.0f} min · D₀ {defect_density:.3f} cm⁻²")
    return LineResult.of(label, wafer)


def oxide_minutes_error(minutes: float) -> str | None:
    """A readable message if the gate-oxide drive is outside its domain (must be > 0 min), else ``None``.

    The shared *adapt-lever* check. The oxidation model **raises** for a non-positive bake (``t_ox`` must
    be positive), so both the dashboard and the roguelike screen call this before running the line and
    show the message instead of letting the raw ``ValueError`` reach Textual's (exception-swallowing) event
    loop. ``not (minutes > 0)`` also rejects ``NaN`` (every comparison with ``NaN`` is ``False``).
    """
    if not (minutes > 0.0):
        return (f"Gate-oxide drive must be greater than 0 min — no oxide grows in zero or negative "
                f"time. Got {minutes:g}.")
    return None


def knob_errors(*, slice_z: float = 0.0, oxide_minutes: float = 20.0,
                defect_density: float = 0.0) -> tuple[str, ...]:
    """Readable messages for any dashboard knob outside its physical domain (an empty tuple = all valid).

    The bounded knobs the underlying physics enforces by **raising** (or silently running as nonsense):
    the boule is only so long, so ``slice_z`` ∈ [0, 1); the gate-oxide bake must be positive; the
    killer-particle ``defect_density`` can't be negative. The thin TUI calls this **before**
    :func:`run_dashboard`, so an out-of-range field shows a readable note instead of propagating a raw
    ``ValueError`` into Textual's (exception-swallowing) event loop and killing the app. Pure/headless
    (ADR 0002/0005) — tested without textual. ``defocus_nm`` has no bounded domain (a signed offset; large
    values merely drive the yield to zero rather than raising), so it is not checked here.
    """
    errors: list[str] = []
    if not (0.0 <= slice_z < 1.0):                  # the half-open boule fraction (also rejects NaN)
        errors.append(f"Boule slice z must be in [0, 1) — the fraction of the boule solidified "
                      f"(0 = seed end, approaching 1 = tail). Got {slice_z:g}.")
    ox = oxide_minutes_error(oxide_minutes)
    if ox is not None:
        errors.append(ox)
    if defect_density < 0.0:                        # particles per cm² can't be negative (NaN passes — harmless)
        errors.append(f"Defect density can't be negative — it is killer particles per cm squared. "
                      f"Got {defect_density:g}.")
    return tuple(errors)


def dashboard_summary(result: LineResult) -> str:
    """The headline readout + the worst dead die's failure trail (the §9 "watch the trail" payoff).

    Reads only the already-computed :class:`LineResult` — **no physics**: the wafer yield and the mean
    device ``V_t`` / ``I_Dsat`` over the dies that produced one, then
    :func:`~fab_game.pipeline.diagnose` on the worst (outer-most) dead die — or a clean-wafer note when
    every die printed in spec. (Economics — the bin mix and profit — stays in G7's own ``demo_game``;
    at the default specs binning grades every part ``"pass"``, so a profit readout here would be a
    binning-policy artifact, not a signal.)
    """
    wafer = result.wafer
    vts = [d.V_t for d in wafer.dies if d.V_t is not None]
    ids = [d.i_dsat_mA for d in wafer.dies if d.i_dsat is not None]
    mean_vt = sum(vts) / len(vts) if vts else float("nan")
    mean_id = sum(ids) / len(ids) if ids else float("nan")
    head = (f"yield {result.yield_:.0%}  ·  mean V_t {mean_vt:.3f} V  ·  "
            f"mean I_Dsat {mean_id:.2f} mA")
    dead = result.dead_dies
    if not dead:
        return head + "\n every die printed in spec — a clean wafer."
    worst = max(dead, key=lambda d: d.radius_frac)
    return head + "\n" + diagnose(worst)
