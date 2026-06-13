"""The CG-2 banked artifact: the Voronkov V/G criterion — the in-model brake on pulling faster.

The second Czochralski **crystal-growth deepening** (plan §6a CG-2), a G2/CG-1 follow-on. CG-1 made
pull rate flatten the Scheil doping drift, but **one-sided** — pulling faster only helped, and its
demo named the cost as the deferred CG-2 brake. CG-2 builds that brake: the **Voronkov criterion**
(:func:`chip.czochralski.voronkov_ratio`) says the ratio of pull rate ``V`` to the interface thermal
gradient ``G``, against the critical ``ξ_t``, sets the grown-in microdefect type — ``V/G > ξ_t`` is
vacancy-rich (**voids / COPs**, which degrade gate-oxide integrity), ``V/G < ξ_t`` is interstitial-
rich (dislocations). So pulling faster (or running a cooler hot zone, lower ``G``) pushes growth into
the void regime, seeding a **killer-defect density that plugs into the G3 defect map** — the cost.

Why the demo is analytic (the load-bearing wiring note). The grown-in COPs are scattered by the
G3 stochastic layer (:mod:`fab_game.defects`), which fires **only with variation enabled** — and a
boule sweep runs at ``NO_VARIATION`` to isolate the clean Scheil signal (CG-1). So this demo shows the
CG-2 consequence as the **deterministic expected yield** ``poisson_yield(grown_in_density(V,G), A)`` —
exactly the law the stochastic scatter converges to (a G3 mechanics invariant, not re-shown here),
the same way CG-1 plotted the deterministic ``V_t`` walk. Three panels:

1. **The criterion (a G-sweep at fixed pull).** ``V/G`` vs the thermal gradient: it crosses ``ξ_t`` at
   ``G* = V/ξ_t``; below ``G*`` (a cool hot zone) growth is vacancy-rich and the COP yield falls, above
   it interstitial and **defect-free**. The *direction* is criterion-driven (cited ``ξ_t``); only the
   yield depth scales with the flagged void coefficient — so the panel barely depends on the house number.
2. **The brake (a pull-sweep at two hot zones).** Analytic defect yield vs pull rate at a baseline ``G``
   and an engineered hot-zone ``G``: pulling faster drops the yield (more COPs), and the hotter zone
   tolerates a faster pull before the voids switch on — the lever real "perfect silicon" growth uses.
3. **CG-1 + CG-2 together (which lever sets the pull).** Vs pull rate at the engineered hot-zone ``G``:
   the combined yield (CG-1 parametric in-spec fraction × CG-2 defect survival) is **maximized on the
   defect-free plateau ``V ≤ V* = ξ_t·G``**, then falls as voids switch on. The honest reading: CG-1's
   parametric fraction is **flat** across this range (it only rises at pulls where CG-2 has already
   crushed the yield), so the two do **not** trade off — **CG-2's criterion alone sets the optimal
   pull**. On yield the slow end of the plateau is no worse than the boundary; "grow as fast as the
   criterion allows" is motivated by **throughput, which is not modelled here**. The plateau's *location*
   is the cited ``ξ_t`` (coefficient-robust); only the fall-off depth past it is the flagged coefficient.

**Honesty (the repo's bar).** ``G`` is a **flagged house knob** (or, deferred, the shipped Robin heat
mode); the void→density **coefficient** is house; only the Voronkov criterion *form* + ``ξ_t`` are
cited. The interstitial-side dislocation/leakage cost and the **OSF-ring radial pattern** (the density
here is spatially uniform) are named deferred edges — and the per-particle "grown-in vs fab-floor"
attribution (the failure trail still reads a caught particle) is a deferred second-draw refinement.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_voronkov
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.czochralski import (
    VORONKOV_CRITICAL_RATIO,
    grown_in_defect_regime,
    void_defect_density,
    voronkov_ratio,
)
from chip.wafer_prep import poisson_yield

from .pipeline import run_batch
from .recipe import CzochralskiKnobs, Recipe
from .spec import DEFAULT_SPECS
from .state import die_area_cm2
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
DOPANT = "B"
XI_T = VORONKOV_CRITICAL_RATIO                      # ξ_t = 0.13 mm²/(K·min) (cited Voronkov)
# Panel 1 (criterion): a fixed pull, sweep the thermal gradient G across the V/I boundary.
V_FIXED_MM_MIN = 2.0                                # the fixed pull rate for the G-sweep
G_SWEEP_K_PER_MM = tuple(float(g) for g in np.linspace(2.0, 24.0, 80))
# Panel 2/3 (brake / unifier): sweep the pull rate at a baseline and an engineered hot-zone gradient.
G_BASELINE_K_PER_MM = 3.5                           # a typical hot zone (realistic CZ → vacancy-rich)
G_HOTZONE_K_PER_MM = 8.0                            # an engineered (hotter) zone → tolerates faster pull
PULL_SWEEP_MM_MIN = tuple(float(v) for v in np.linspace(0.3, 6.0, 60))   # the analytic curves
# Panel 3 fixes the engineered hot-zone G and sweeps the pull across the V/I boundary (V* = ξ_t·G),
# so the combined optimum sits AT the criterion boundary (a coefficient-robust location).
G_UNIFIER_K_PER_MM = G_HOTZONE_K_PER_MM
PULL_UNIFIER_MM_MIN = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0)   # the (costly) batch points for panel 3
# The die-map scale the analytic Poisson yield uses (the single die_area_cm2 the G3 map uses).
GRID_N = 5
WAFER_DIAMETER_MM = 200.0
# The boule sweep for the CG-1 parametric in-spec fraction (panel 3) — finer than CG-1's so the
# in-spec fraction resolves the benefit climb (not just the coarse 1/9 quantization).
N_WAFERS = 19
Z_MAX = 0.9

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-cg2.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-cg2.png"


@dataclass(frozen=True)
class DemoResult:
    """The criterion curve + the analytic defect-yield brake + the CG-1↔CG-2 unifier (no score)."""

    xi_t: float
    die_area_cm2: float
    # Panel 1 — the criterion (G-sweep at fixed pull):
    v_fixed: float
    g_sweep: tuple[float, ...]
    ratio_vs_g: tuple[float, ...]
    defect_yield_vs_g: tuple[float, ...]
    g_boundary: float                               # G* = V/ξ_t (the V/I boundary at the fixed pull)
    # Panel 2 — the brake (pull-sweep at two hot zones):
    g_baseline: float
    g_hotzone: float
    pull_sweep: tuple[float, ...]
    defect_yield_baseline: tuple[float, ...]
    defect_yield_hotzone: tuple[float, ...]
    # Panel 3 — the unifier (pull-sweep at the engineered hot-zone G):
    g_unifier: float
    v_boundary_unifier: float                       # V* = ξ_t·G — the V/I boundary (the optimum's seat)
    pull_unifier: tuple[float, ...]
    parametric_fraction: tuple[float, ...]          # CG-1 benefit: in-V_t-spec fraction down the boule
    defect_survival: tuple[float, ...]              # CG-2 cost: analytic poisson_yield(grown_in, A)
    combined_yield: tuple[float, ...]               # parametric × defect
    # The realistic operating point (the honest "typical CZ is vacancy-rich" anchor):
    realistic_ratio: float
    realistic_regime: str


def _parametric_in_spec_fraction(pull: float) -> float:
    """CG-1's benefit metric: the fraction of the boule (sliced 0→Z_MAX) whose mean V_t is in spec.

    Runs the real pipeline down the boule at this pull rate (NO_VARIATION → the clean Scheil signal,
    no defects scattered — the CG-2 cost is added analytically, not here). Flatter doping (faster pull)
    keeps more of the boule's V_t inside the window → a higher fraction.
    """
    recipe = Recipe(czochralski=CzochralskiKnobs(pull_rate_mm_min=pull))
    batch = run_batch(recipe, n_wafers=N_WAFERS, z_max=Z_MAX, seed=SEED,
                      variation=NO_VARIATION, grid_n=1)
    lo, hi = DEFAULT_SPECS.v_t.lo, DEFAULT_SPECS.v_t.hi
    in_spec = [lo <= batch.mean_V_t(w) <= hi for w in batch.wafers]
    return float(np.mean(in_spec))


def compute() -> DemoResult:
    """Build the criterion curve, the analytic defect-yield brake, and the CG-1↔CG-2 unifier."""
    area = die_area_cm2(GRID_N, WAFER_DIAMETER_MM)

    # Panel 1 — the criterion: at a fixed pull, sweep G → ξ = V/G → void density → analytic yield.
    ratio_vs_g = tuple(voronkov_ratio(V_FIXED_MM_MIN, g) for g in G_SWEEP_K_PER_MM)
    defect_yield_vs_g = tuple(poisson_yield(void_defect_density(r), area) for r in ratio_vs_g)
    g_boundary = V_FIXED_MM_MIN / XI_T              # G* where ξ = ξ_t

    # Panel 2 — the brake: sweep pull at two hot zones → analytic defect yield.
    def yield_at(pull: float, g: float) -> float:
        return poisson_yield(void_defect_density(voronkov_ratio(pull, g)), area)

    defect_yield_baseline = tuple(yield_at(v, G_BASELINE_K_PER_MM) for v in PULL_SWEEP_MM_MIN)
    defect_yield_hotzone = tuple(yield_at(v, G_HOTZONE_K_PER_MM) for v in PULL_SWEEP_MM_MIN)

    # Panel 3 — the unifier: CG-1 parametric in-spec fraction (rises) × CG-2 defect survival (falls),
    # at the engineered hot-zone G → the combined optimum sits at the V/I boundary V* = ξ_t·G.
    parametric_fraction = tuple(_parametric_in_spec_fraction(v) for v in PULL_UNIFIER_MM_MIN)
    defect_survival = tuple(yield_at(v, G_UNIFIER_K_PER_MM) for v in PULL_UNIFIER_MM_MIN)
    combined_yield = tuple(p * d for p, d in zip(parametric_fraction, defect_survival))

    realistic_ratio = voronkov_ratio(1.0, G_BASELINE_K_PER_MM)   # V≈1 mm/min, baseline G
    return DemoResult(
        xi_t=XI_T, die_area_cm2=area,
        v_fixed=V_FIXED_MM_MIN, g_sweep=G_SWEEP_K_PER_MM,
        ratio_vs_g=ratio_vs_g, defect_yield_vs_g=defect_yield_vs_g, g_boundary=g_boundary,
        g_baseline=G_BASELINE_K_PER_MM, g_hotzone=G_HOTZONE_K_PER_MM, pull_sweep=PULL_SWEEP_MM_MIN,
        defect_yield_baseline=defect_yield_baseline, defect_yield_hotzone=defect_yield_hotzone,
        g_unifier=G_UNIFIER_K_PER_MM, v_boundary_unifier=XI_T * G_UNIFIER_K_PER_MM,
        pull_unifier=PULL_UNIFIER_MM_MIN, parametric_fraction=parametric_fraction,
        defect_survival=defect_survival, combined_yield=combined_yield,
        realistic_ratio=realistic_ratio, realistic_regime=grown_in_defect_regime(realistic_ratio),
    )


def print_summary(r: DemoResult) -> None:
    """Print the criterion → brake → unifier story — the demo's payoff in text (no score)."""
    print("\nCrystal growth CG-2: the Voronkov V/G criterion — the in-model brake on pulling faster\n")

    print(f"  The criterion (Voronkov, cited): ξ = V/G vs ξ_t = {r.xi_t:.2f} mm²/(K·min)")
    print(f"     ξ > ξ_t → vacancy-rich (voids / COPs → gate-oxide-integrity killers)")
    print(f"     ξ < ξ_t → interstitial-rich (dislocation loops);  ξ = ξ_t → the OSF ring (defect-free edge)\n")

    print(f"  Realistic CZ (V≈1 mm/min, G={r.g_baseline:.1f} K/mm): ξ = {r.realistic_ratio:.2f} "
          f"→ {r.realistic_regime.upper()}-rich")
    print(f"  — i.e. typical growth is COP-containing unless the hot zone is engineered up to "
          f"G ≈ V/ξ_t ≈ {1.0 / r.xi_t:.1f} K/mm.\n")

    print(f"  The brake (analytic defect yield exp(−D_void·A), A = {r.die_area_cm2:.3f} cm²), pull-sweep:")
    for v, yb, yh in zip(r.pull_sweep, r.defect_yield_baseline, r.defect_yield_hotzone):
        if v in (0.5, 2.0, 4.0, 6.0) or abs(v - 1.0) < 0.06:
            print(f"     V={v:4.1f} mm/min:  yield(G={r.g_baseline:.1f}) = {yb:5.2f}   "
                  f"yield(G={r.g_hotzone:.1f}, hot zone) = {yh:5.2f}")
    print(f"  → pulling faster drops the defect yield; the hotter zone tolerates a faster pull.\n")

    print(f"  CG-1 + CG-2 together, pull-sweep at the hot zone G={r.g_unifier:.1f} K/mm:")
    print(f"     {'V (mm/min)':>11}  {'CG-1 parametric':>16}  {'CG-2 defect':>12}  {'combined':>9}")
    for v, p, d, c in zip(r.pull_unifier, r.parametric_fraction, r.defect_survival, r.combined_yield):
        mark = "  ← V/I boundary V*=ξ_t·G" if abs(v - r.v_boundary_unifier) < 0.13 else ""
        print(f"     {v:>11.2f}  {p:>16.2f}  {d:>12.2f}  {c:>9.2f}{mark}")
    print(f"  → The combined yield is MAXIMIZED on the defect-free plateau V ≤ V* = ξ_t·G "
          f"≈ {r.v_boundary_unifier:.1f} mm/min,")
    print(f"     then falls as voids switch on. But CG-1's parametric fraction is FLAT across this range")
    print(f"     (it only rises at pulls where CG-2 has already crushed the yield), so the two do NOT")
    print(f"     trade off — CG-2's criterion ALONE sets the optimal pull. On yield the slow end of the")
    print(f"     plateau is no worse than the boundary; the boundary's only edge is THROUGHPUT (unmodeled).")
    print(f"     The plateau's LOCATION is the cited ξ_t (coefficient-robust); only the fall-off depth")
    print(f"     past it is the FLAGGED void coefficient — a mechanism, not a tuned number.\n")

    print("  New: the cited Voronkov criterion (chip.czochralski, triad-tested); the thermal-gradient")
    print("  knob is opt-in (default = no grown-in voids → the G1–G7 banked demos byte-for-byte unchanged).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the CG-2 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import voronkov_figure

    fig = voronkov_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # ξ, →, ≈ on legacy codepages

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
