"""The G3 banked artifact: the die map made physical — killer particles → functional yield + TTV scrap.

The fab-line game's third demonstrable thing (plan §6 G3). G1 made the wafer a *die map*; G2 gave
each wafer a substrate from the boule; **G3 makes the map physical**: killer particle defects are
scattered at **locations** across the wafer, a die that catches one is dead **functionally** (the
cited defect-limited yield, :mod:`chip.wafer_prep`), and the wafer carries a **geometry** (TTV/bow)
that scraps it if out of flatness spec — recoverable by a re-polish that **eats thickness**.

Three things are shown:

1. **The particle map.** One dirty-line wafer: killer particles scattered at their locations, the
   dies they hit dead (functional fails) — a yield map that is now *spatial defects*, not just the
   center-to-edge parametric trend of G1.
2. **The placement obeys the cited law.** The empirical defect-limited yield, swept over the killer
   density ``D₀``, hugs the closed form ``Y = exp(−D₀·A_die)`` (Murphy/Poisson) — the random
   placement *converges to* the validated physics (the same byte-identical die area drives both).
3. **Geometry gate + re-polish.** A weak CMP leaves the TTV out of flatness spec → the whole wafer
   is scrapped; a re-polish lowers the TTV back in spec and recovers it — at the cost of thickness.

The yield *law* is cited and triad-tested (``chip/tests/test_wafer_prep.py``); the *placement* and
its convergence are the game-layer mechanics invariant (``fab_game/tests/test_defects.py``). Only the
front-of-line wiring is new.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_wafer_prep
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip import wafer_prep as wp

from .defects import scatter_defects
from .pipeline import rework_polish, run_line, wafer_yield
from .recipe import Recipe, WaferPrepKnobs
from .spec import DEFAULT_SPECS
from .state import WaferState, build_die_map, die_area_cm2
from .variation import Variation

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 7
GRID_N = 7                                   # 37-die map — enough to scatter a legible particle field
DIAM_MM = 200.0
MAP_DENSITY = 0.06                           # cm⁻² killer density for the particle-map wafer (~40 % killed)

# A defects-ONLY stochastic layer: ``enabled`` so particles are scattered, but every parametric trend
# / jitter zeroed — so the *only* thing that kills a die on the particle map is a killer particle (the
# G2 move of isolating the new signal, here the defect functional yield, from the G1 focus bowl).
DEFECTS_ONLY = Variation(enabled=True, focus_tilt_nm=0.0, t_ox_edge_frac=0.0,
                         focus_sigma_nm=0.0, cd_sigma_nm=0.0, t_ox_sigma_frac=0.0)
SWEEP_DENSITIES = tuple(np.linspace(0.0, 0.4, 9))   # the yield-vs-D₀ sweep
SWEEP_SEEDS = 60                             # realizations averaged at each density (the empirical yield)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g3.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g3.png"


@dataclass(frozen=True)
class DemoResult:
    """The dirty-line wafer + the yield-vs-D₀ sweep + the geometry scrap/re-polish — the bundle."""

    dirty_wafer: WaferState
    map_density: float
    die_area_cm2: float
    sweep_densities: tuple[float, ...]
    empirical_yields: tuple[float, ...]      # mean defect-survival fraction at each density (placement)
    poisson_yields: tuple[float, ...]        # exp(−D₀·A_die), the cited closed form (same area)
    scrap_wafer: WaferState                  # a TTV-scrapped wafer
    repolished_wafer: WaferState             # …recovered by a re-polish (at a thickness cost)


def _empirical_defect_yield(density: float, dies, *, seeds: int) -> float:
    """Mean zero-defect (survival) fraction over ``seeds`` placements at ``density`` — the placement yield."""
    if density <= 0.0:
        return 1.0
    rng = np.random.default_rng(0)
    survived = total = 0
    for _ in range(seeds):
        out = scatter_defects(dies, defect_density=density, grid_n=GRID_N,
                              wafer_diameter_mm=DIAM_MM, rng=rng, enabled=True)
        for events in out.values():
            total += 1
            survived += len(events) == 0
    return survived / total


def compute() -> DemoResult:
    """Run the dirty-line wafer, the yield-vs-D₀ sweep, and the geometry scrap/re-polish (no plotting)."""
    A = die_area_cm2(GRID_N, DIAM_MM)
    dies = build_die_map(grid_n=GRID_N)

    # 1. The particle-map wafer: a dirty line, full pipeline, defects-only variation so dies bin
    #    pass/functional-fail purely on the killer particles they caught.
    dirty = Recipe(wafer_prep=WaferPrepKnobs(defect_density=MAP_DENSITY))
    dirty_wafer = run_line(dirty, seed=SEED, variation=DEFECTS_ONLY, specs=DEFAULT_SPECS, grid_n=GRID_N)

    # 2. The yield-vs-density sweep: empirical placement yield vs the cited Poisson law (same area).
    empirical = tuple(_empirical_defect_yield(d, dies, seeds=SWEEP_SEEDS) for d in SWEEP_DENSITIES)
    poisson = tuple(float(wp.poisson_yield(d, A)) for d in SWEEP_DENSITIES)

    # 3. Geometry: a weak CMP scraps the wafer on TTV; a re-polish recovers it (eats thickness).
    weak_cmp = Recipe(wafer_prep=WaferPrepKnobs(slice_ttv_um=4.0, cmp_ttv_improvement=0.5))   # TTV 2.0 µm
    scrap = run_line(weak_cmp, seed=SEED, specs=DEFAULT_SPECS, grid_n=GRID_N)
    repolished = rework_polish(scrap, extra_removal_um=40.0, extra_ttv_improvement=0.9)

    return DemoResult(
        dirty_wafer=dirty_wafer, map_density=MAP_DENSITY, die_area_cm2=A,
        sweep_densities=tuple(float(d) for d in SWEEP_DENSITIES),
        empirical_yields=empirical, poisson_yields=poisson,
        scrap_wafer=scrap, repolished_wafer=repolished)


def print_summary(r: DemoResult) -> None:
    """Print the particle-map → yield-law → geometry story — the demo's payoff in text."""
    w = r.dirty_wafer
    n_defects = sum(len(d.defects) for d in w.dies)
    n_killed = sum(bool(d.killed_by_defect) for d in w.dies)
    print("\nThe fab line: the die map made physical — killer particles → functional yield, + the TTV scrap\n")
    print(f"  Particle-map wafer: killer density D₀ = {r.map_density:.3f} cm⁻², die area A = "
          f"{r.die_area_cm2:.1f} cm²  (→ λ = D₀·A = {r.map_density * r.die_area_cm2:.2f} killers/die)")
    print(f"    scattered {n_defects} killer particles over {w.n_dies} dies → {n_killed} dies dead "
          f"(functional), yield {wafer_yield(w):.0%}\n")
    print("  Defect-limited yield obeys the cited Poisson law  Y = exp(−D₀·A):")
    print("    D₀ (cm⁻²)   empirical (placement)   exp(−D₀·A) (cited)")
    for d, e, p in zip(r.sweep_densities, r.empirical_yields, r.poisson_yields):
        print(f"    {d:6.3f}        {e:6.1%}                {p:6.1%}")
    g0, g1 = r.scrap_wafer.geometry, r.repolished_wafer.geometry
    print(f"\n  Geometry gate: weak CMP → TTV {g0.ttv_um:.2f} µm > {DEFAULT_SPECS.geometry.ttv_um.hi:.2f} µm "
          f"flatness spec → wafer SCRAPPED (yield {wafer_yield(r.scrap_wafer):.0%}).")
    rec = r.repolished_wafer.rework_log[-1]
    print(f"    re-polish → TTV {g1.ttv_um:.3f} µm (in spec), thickness {g0.thickness_um:.0f} → "
          f"{g1.thickness_um:.0f} µm (ate {g0.thickness_um - g1.thickness_um:.0f} µm) → "
          f"yield {wafer_yield(r.repolished_wafer):.0%} (recovered {rec.n_recovered} dies)\n")
    print("  New: the cited Murphy/Poisson yield law (chip.wafer_prep, triad-tested). The stochastic")
    print("  placement converges to it; the functional yield + geometry gate are the wiring.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the G3 wafer-prep artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import wafer_prep_figure

    fig = wafer_prep_figure(r)
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
