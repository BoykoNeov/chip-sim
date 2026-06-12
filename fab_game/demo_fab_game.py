"""The G1 banked artifact: one bad knob → a dead die, with the failure trail.

The fab-line game's first demonstrable thing (plan §1 "the dramatic early win", §6 G1). It runs
the **same wafer** twice through the *already-validated* diffusion → oxidation → lithography →
device back end — once at a **good** recipe, once with a single bad knob (**defocus**) — and shows
the consequence ripple end to end:

    defocus the exposure → the aerial image loses edge sharpness (NILS collapses) →
    the gate no longer prints reliably → those dies leave the spec window → the wafer yield drops,
    and the failure trail names *defocus* as the cause.

The center-to-edge focus bowl makes the failure **spatial**: the wafer's edge ring dies while the
centre survives — exactly the depth-of-focus story a real fab fights. Then a litho **rework** (strip
resist, re-expose at corrected focus) recovers the lost dies, closing the loop. **All reuse, zero
new physics** — every number traces to a ``chip/`` module that already passes its triad; this demo
proves the *mechanism* (state, propagation, spec, yield, rework), not a new equation.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_fab_game
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .pipeline import LineResult, diagnose, rework_litho, run_line, wafer_yield
from .recipe import DEFAULT_RECIPE, LithoKnobs, Recipe
from .spec import DEFAULT_SPECS
from .state import Die, WaferState
from .variation import Variation

# --- The demo recipes (the good run, and the one-bad-knob run) --------------- #
SEED = 0
GRID_N = 7                              # 37 dies on the wafer — enough to show the edge ring
VARIATION = Variation()                 # the house-default within-wafer non-uniformity (flagged)

GOOD_RECIPE = DEFAULT_RECIPE                                    # defocus = 0 → in focus
BAD_DEFOCUS_NM = 90.0                                           # the single bad knob (NILS-collapse regime)
BAD_RECIPE = Recipe(litho=LithoKnobs(defocus_nm=BAD_DEFOCUS_NM))
FOCUS_CORRECTION_NM = -BAD_DEFOCUS_NM                           # the rework: re-centre focus
# An EXTREME defocus exercises the plan §1 *literal* chain: defocus large enough to collapse the CD
# itself (out of window) and drive I_Dsat over its ceiling — the regime past mere NILS loss. (For a
# symmetric feature the CD midpoint is defocus-robust until here; NILS is the *primary* signature,
# CD/I_Dsat the *extreme*-defocus one — the G1 finding.)
EXTREME_DEFOCUS_NM = 320.0
EXTREME_RECIPE = Recipe(litho=LithoKnobs(defocus_nm=EXTREME_DEFOCUS_NM))

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g1.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g1.png"


@dataclass(frozen=True)
class DemoResult:
    """The two scored wafers, the chosen dead die + its trail, and the reworked wafer — the bundle."""

    good: LineResult
    bad: LineResult
    extreme: LineResult
    reworked: WaferState
    reworked_yield: float
    dead_die: Die | None
    dead_trail: str


def _worst_dead_die(wafer: WaferState) -> Die | None:
    """The failed die furthest out (the most defocused) — the cleanest 'why did this die?' example."""
    dead = [d for d in wafer.dies if d.verdict is not None and d.verdict.failed]
    return max(dead, key=lambda d: d.radius_frac) if dead else None


def compute() -> DemoResult:
    """Run the good and bad wafers + the rework → :class:`DemoResult` (no plotting)."""
    good = LineResult.of("good (in focus)", run_line(
        GOOD_RECIPE, seed=SEED, variation=VARIATION, specs=DEFAULT_SPECS, grid_n=GRID_N))
    bad = LineResult.of(f"bad (defocus {BAD_DEFOCUS_NM:.0f} nm)", run_line(
        BAD_RECIPE, seed=SEED, variation=VARIATION, specs=DEFAULT_SPECS, grid_n=GRID_N))
    extreme = LineResult.of(f"extreme (defocus {EXTREME_DEFOCUS_NM:.0f} nm)", run_line(
        EXTREME_RECIPE, seed=SEED, variation=VARIATION, specs=DEFAULT_SPECS, grid_n=GRID_N))

    dead = _worst_dead_die(bad.wafer)
    trail = diagnose(dead) if dead is not None else "(no dead die — the bad recipe printed clean)"

    reworked = rework_litho(bad.wafer, BAD_RECIPE, specs=DEFAULT_SPECS, variation=VARIATION,
                            focus_correction_nm=FOCUS_CORRECTION_NM)
    return DemoResult(good=good, bad=bad, extreme=extreme, reworked=reworked,
                      reworked_yield=wafer_yield(reworked), dead_die=dead, dead_trail=trail)


def print_summary(r: DemoResult) -> None:
    """Print the recipe → yield → failure-trail → rework story — the demo's payoff in text."""
    print("\nThe fab line: one bad knob → a dead die, with the failure trail\n")
    print(f"  GOOD recipe (in focus)        →  yield {r.good.yield_:6.1%}  "
          f"({r.good.wafer.n_dies - len(r.good.dead_dies)}/{r.good.wafer.n_dies} dies good)")
    print(f"  BAD  recipe (defocus {BAD_DEFOCUS_NM:.0f} nm)   →  yield {r.bad.yield_:6.1%}  "
          f"({r.bad.wafer.n_dies - len(r.bad.dead_dies)}/{r.bad.wafer.n_dies} dies good)  "
          f"← one knob, {len(r.bad.dead_dies)} dead dies")
    print(f"\n  Why did the dies die? (the failure trail of the worst-hit die)\n")
    for line in r.dead_trail.splitlines():
        print("    " + line)
    print(f"\n  Rework — strip resist, re-expose at {FOCUS_CORRECTION_NM:+.0f} nm focus correction:")
    print(f"    yield {r.bad.yield_:.1%}  →  {r.reworked_yield:.1%}  "
          f"(recovered {r.reworked.rework_log[-1].n_recovered} dies)\n")

    # The G1 finding: at *moderate* defocus the casualty is NILS (image sharpness), while the CD
    # midpoint and I_Dsat hold; only an EXTREME defocus collapses the CD out of window and pushes
    # I_Dsat over its ceiling — the plan §1 'CD → channel → I_Dsat' chain, demonstrated here.
    ext = _worst_dead_die(r.extreme.wafer)
    if ext is not None:
        lr = next(rec for rec in ext.history if rec.step == "litho")
        dr = next((rec for rec in ext.history if rec.step == "device"), None)
        idsat = dr.outputs.get("i_dsat") if dr and "i_dsat" in dr.outputs else None
        print(f"  EXTREME defocus ({EXTREME_DEFOCUS_NM:.0f} nm) → the CD itself collapses (the plan's literal chain):")
        print(f"    yield {r.extreme.yield_:.1%}; worst die CD {lr.outputs['cd_nm']:.1f} nm"
              + (f", I_Dsat {idsat * 1e3:.2f} mA" if idsat is not None else "")
              + f"  → {', '.join(ext.verdict.reasons)}\n")

    print("  All reuse, zero new physics: every number is a chip/ module that already passes its triad.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the wafer-map artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import fab_game_figure

    fig = fab_game_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # → ↳ on legacy codepages

    r = compute()
    print_summary(r)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
