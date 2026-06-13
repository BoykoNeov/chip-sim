"""The G4 banked artifact: bad purification → contamination → a dead device, traced (and the rework).

The fab-line game's fourth demonstrable thing (plan §6 G4, §5a). G1–G3 built the harness, the boule,
and the physical die map; **G4 makes "badly purified feedstock" a device consequence**. Silicon
purification is **segregation** (zone refining, :mod:`chip.purification`): a feedstock grade is an
impurity vector, and one molten-zone pass scrubs each species by its cited ``k``. Three things shown:

1. **The scrubbing contrast (pure physics — the verifiable win).** One zone pass on a metallurgical-
   grade (MGS) feed: the tiny-``k`` **metals** (Fe ``k ≈ 8e-6``) are scrubbed ~5 orders of magnitude,
   while **boron** (``k ≈ 0.8``) is barely touched and the mobile-ion **Na** only modestly — the exact
   ``C_front/C_0 = k`` identity, straight from the one cited Trumbore ``k`` table. *Why segregation
   refining cleans metals superbly but cannot purify the dopants.*

2. **The contamination → dead device chain (the dramatic win).** That MGS feed, refined just **once**,
   leaves residual **mobile-ion Na** that incorporates into the gate oxide as charge ``Q_ox`` →
   ``ΔV_FB = −Q_ox/C_ox`` drives the threshold voltage **down** out the bottom of its spec window → the
   whole wafer is scrapped on ``V_t``, and the failure trail names the cause (Na contamination, not
   defocus). Across the grade ladder (clean → EGS → solar → MGS) ``V_t`` walks down as the feed dirties.

3. **The rework (purify harder).** Zone refining is reworkable by **more passes** (the plan's step-1
   rework): a second pass scrubs the Na ~2 more orders → ``V_t`` climbs back into spec → yield
   recovers. The residual **boron** (``k ≈ 0.8``) persists across passes — the un-refinable footnote
   (so the recovered ``V_t`` sits slightly off the pristine value).

The segregation law is cited and triad-tested (``chip/tests/test_purification.py``); the contamination
magnitudes (grade vectors, the Na→Q_ox incorporation length) are flagged house numbers; the wiring is
the game-layer mechanics invariant (``fab_game/tests/test_contamination.py``). A clean feed is the seam.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_purification
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from chip import czochralski as cz
from chip import purification as pur

from .pipeline import diagnose, run_line, wafer_yield
from .recipe import DEFAULT_RECIPE, PurificationKnobs, Recipe
from .spec import DEFAULT_SPECS
from .state import WaferState
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRID_N = 5                                    # a small uniform map (contamination is wafer-level)
GRADES = ("clean", "EGS", "solar", "MGS")     # the feedstock-grade ladder (clean → dirty)
MGS_PASSES = (1, 2, 3, 4)                      # the zone-pass rework sweep on the dirty MGS feed
DIRTY_GRADE = "MGS"

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g4.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g4.png"


@dataclass(frozen=True)
class DemoResult:
    """The scrubbing contrast + the grade-ladder V_t walk + the zone-pass rework — the bundle."""

    species: tuple[str, ...]
    k_values: dict[str, float]
    feed_vector: dict[str, float]            # the MGS feedstock impurity vector (cm⁻³)
    refined_vector: dict[str, float]         # …after one zone pass (cm⁻³)
    grades: tuple[str, ...]
    vt_by_grade: tuple[float, ...]           # device V_t at one pass, down the grade ladder
    yield_by_grade: tuple[float, ...]
    mgs_passes: tuple[int, ...]
    vt_by_pass: tuple[float, ...]            # device V_t vs zone passes (MGS) — the rework recovery
    yield_by_pass: tuple[float, ...]
    v_t_lo: float
    v_t_hi: float
    dead_wafer: WaferState                   # MGS, one pass — scrapped on V_t
    dead_trail: str                          # the failure trail naming the Na contamination
    recovered_wafer: WaferState              # MGS, two passes — recovered


def _recipe(grade: str, passes: int) -> Recipe:
    return Recipe(purification=PurificationKnobs(grade=grade, zone_passes=passes))


def _single_die_vt(grade: str, passes: int) -> float:
    """The (uniform) device V_t for a grade/pass count — one representative die, no variation."""
    w = run_line(_recipe(grade, passes), seed=SEED, variation=NO_VARIATION, grid_n=1)
    return float(w.dies[0].V_t)


def _wafer_yield(grade: str, passes: int) -> float:
    w = run_line(_recipe(grade, passes), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    return wafer_yield(w)


def compute() -> DemoResult:
    """Run the scrubbing contrast, the grade ladder, and the zone-pass rework (no plotting)."""
    feed = pur.FEEDSTOCK_GRADES[DIRTY_GRADE]
    refined = pur.zone_refine(feed, n_passes=1)
    species = tuple(feed.as_dict().keys())
    k_values = {s: cz.SEGREGATION_K[s] for s in species}

    vt_by_grade = tuple(_single_die_vt(g, 1) for g in GRADES)
    yield_by_grade = tuple(_wafer_yield(g, 1) for g in GRADES)
    vt_by_pass = tuple(_single_die_vt(DIRTY_GRADE, n) for n in MGS_PASSES)
    yield_by_pass = tuple(_wafer_yield(DIRTY_GRADE, n) for n in MGS_PASSES)

    dead_wafer = run_line(_recipe(DIRTY_GRADE, 1), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    dead_die = next(d for d in dead_wafer.dies if d.verdict.failed)
    dead_trail = diagnose(dead_die)
    recovered_wafer = run_line(_recipe(DIRTY_GRADE, 2), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)

    return DemoResult(
        species=species, k_values=k_values,
        feed_vector=feed.as_dict(), refined_vector=refined.as_dict(),
        grades=GRADES, vt_by_grade=vt_by_grade, yield_by_grade=yield_by_grade,
        mgs_passes=MGS_PASSES, vt_by_pass=vt_by_pass, yield_by_pass=yield_by_pass,
        v_t_lo=DEFAULT_SPECS.v_t.lo, v_t_hi=DEFAULT_SPECS.v_t.hi,
        dead_wafer=dead_wafer, dead_trail=dead_trail, recovered_wafer=recovered_wafer,
    )


def print_summary(r: DemoResult) -> None:
    """Print the scrubbing-contrast → dead-device → rework story — the demo's payoff in text."""
    print("\nThe fab line: bad purification → contamination → a dead device (and the rework)\n")
    print(f"  1. Zone-refining scrub of a {DIRTY_GRADE} feed (one pass, C_front/C_0 = k):")
    print("     species   k          feed (cm⁻³)   →  refined (cm⁻³)   scrubbed")
    for s in r.species:
        feed, ref, k = r.feed_vector[s], r.refined_vector[s], r.k_values[s]
        print(f"     {s:3s}      {k:9.2e}  {feed:9.2e}   →  {ref:9.2e}    ×{ref/feed if feed else 1:.1e}")
    print("     → metals (Fe) scrubbed ~5 orders; boron barely (k≈0.8) — segregation can't purify dopants.\n")

    print(f"  2. The grade ladder (one pass) walks V_t down (spec [{r.v_t_lo:.2f}, {r.v_t_hi:.2f}] V):")
    for g, vt, y in zip(r.grades, r.vt_by_grade, r.yield_by_grade):
        flag = "ok" if r.v_t_lo <= vt <= r.v_t_hi else "OUT"
        print(f"     {g:6s}: V_t = {vt:.3f} V  [{flag}]   yield {y:.0%}")
    print(f"\n     {DIRTY_GRADE} feed (1 pass) → residual Na poisons the gate oxide → V_t out the bottom:")
    print("     " + r.dead_trail.replace("\n", "\n     ") + "\n")

    print("  3. Rework — purify harder (more zone passes scrub the Na):")
    for n, vt, y in zip(r.mgs_passes, r.vt_by_pass, r.yield_by_pass):
        flag = "ok" if r.v_t_lo <= vt <= r.v_t_hi else "OUT"
        print(f"     {n} pass(es): V_t = {vt:.3f} V  [{flag}]   yield {y:.0%}")
    print(f"     → a 2nd pass scrubs the Na ~2 more orders → V_t back in spec → yield recovers "
          f"({wafer_yield(r.dead_wafer):.0%} → {wafer_yield(r.recovered_wafer):.0%}).")
    print("       (the residual boron persists across passes — the un-refinable footnote.)\n")
    print("  New: the cited zone-refining segregation law (chip.purification, triad-tested) + the")
    print("  device's lifted Q_ox=0 edge. The contamination→Q_ox→V_t wiring is the game layer.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the G4 purification artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import purification_figure

    fig = purification_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ², µ, → on legacy codepages

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
