"""The CG-1 banked artifact: pull rate → effective segregation k_eff(v) → a flatter Scheil boule.

The first Czochralski **crystal-growth deepening** (plan §6a CG-1), a G2 follow-on. G2 grew the boule
with the *equilibrium* Trumbore segregation ``k₀`` (a well-mixed melt), so boron piles up down the
boule and the device ``V_t`` walks out of spec at the tail (the G7 difficulty curve). CG-1 adds the
**Burton–Prim–Slichter** effective coefficient: a thin diffusion boundary layer at the freezing
interface makes ``k_eff`` rise toward 1 with **pull rate**, so *pulling faster flattens the axial
doping drift* — a new front-of-line lever on the substrate spread.

This demo shows the **physics consequence only**, not a strategy/score comparison (CG-1 has no in-model
cost — see below), in three panels:

1. ``k_eff`` vs pull rate (the cited BPS curve): ``k_eff = k₀`` at zero pull (the well-mixed seam) →
   1 as pull → ∞ (complete solute trapping). **The honest magnitude (load-bearing):** boron's
   ``k₀ = 0.80`` *barely segregates already*, so at **realistic Si pull (~0.5–2 mm/min)** ``k_eff``
   only reaches ≈0.81–0.84 — a *modest* flattening; the near-flat boule needs pull rates **beyond
   realistic Si growth** (≳10–20 mm/min here), drawn but **labelled as an illustrative extrapolation**.
2. The axial doping profile ``N_A(z)`` at a few pull rates — flatter as pull rises (the seed end is
   pinned, the tail pulled down).
3. The device ``V_t(z)`` down the boule (the real pipeline) with its spec window: the equilibrium boule's
   tail exits the ceiling; a faster pull keeps more of the boule in spec — **the benefit side**.

**A framing note (the seed end is held fixed).** Every boule here is parameterized by the *same*
seed-end doping ``N_seed`` (the channel target) and differs only in ``k = k_eff`` — so all profiles share
the seed and diverge only in tail droop. That is the seam-preserving choice (``pull_rate=None`` ⇒ G2's
``k₀``, byte-for-byte). A *literal* "same melt pulled faster" would instead hold the **melt** concentration
``C₀`` fixed, and a higher ``k_eff`` would raise the seed end too (``C_s(0) = k_eff·C₀``); that variant is
not what is drawn — here pull rate is read as the knob that recovers a fixed seed-end target with a flatter
tail.

**The deferred brake (named loudly, per the repo's honesty bar).** CG-1 is one-sided *in-model*:
raising ``k_eff`` only flattens doping → only helps. Its real costs are the **next** crystal-growth
deepenings, **not modelled here** — the **V/G point-defect / microvoid criterion (CG-2)**, growth
**striations**, and the **dislocation / max-pull limit**. So this demo is *not* a "pull faster wins"
score claim; it is the doping-flattening consequence, with its cost explicitly off-model.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_crystal_growth
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.czochralski import (
    effective_segregation_coefficient,
    normalized_growth_velocity,
    segregation_coefficient,
)

from .pipeline import run_batch
from .recipe import CzochralskiKnobs, Recipe
from .spec import DEFAULT_SPECS
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
DOPANT = "B"
K0 = segregation_coefficient(DOPANT)               # 0.80 — boron barely segregates (the honest anchor)
REALISTIC_PULL_MAX = 2.0                           # mm/min — the upper edge of realistic Si pull (shaded)
PULL_SWEEP = tuple(float(v) for v in np.linspace(0.0, 25.0, 60))   # the k_eff(v) curve
# The representative pull rates whose boules we draw (None = equilibrium k₀; 10 = beyond realistic Si).
DEMO_PULLS: tuple[float | None, ...] = (None, 2.0, 10.0)
N_WAFERS = 9
Z_MAX = 0.9

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-cg1.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-cg1.png"


@dataclass(frozen=True)
class DemoResult:
    """The k_eff(v) curve + the per-pull-rate boule profiles + V_t walks — the bundle (no score)."""

    k0: float
    realistic_pull_max: float
    pull_sweep: tuple[float, ...]
    keff_sweep: tuple[float, ...]
    realistic_keff_max: float                      # k_eff at the realistic-pull edge (the modest number)
    demo_pulls: tuple[float | None, ...]
    demo_keffs: tuple[float, ...]                   # k_eff for each demo pull (k₀ for None)
    na_z: tuple[float, ...]                          # the smooth z grid for the N_A(z) curves
    z_positions: tuple[float, ...]                   # the discrete batch z's for the V_t(z) markers
    n_a_by_pull: dict                               # pull-label → N_A(z) (cm⁻³) down the boule
    v_t_by_pull: dict                               # pull-label → V_t(z) down the boule (the pipeline)
    v_t_walk_by_pull: dict                          # pull-label → V_t(tail) − V_t(seed)
    v_t_lo: float
    v_t_hi: float


def _label(pull: float | None) -> str:
    return "equilibrium (k₀)" if pull is None else f"{pull:.0f} mm/min"


def _recipe(pull: float | None) -> Recipe:
    return Recipe(czochralski=CzochralskiKnobs(pull_rate_mm_min=pull))


def compute() -> DemoResult:
    """Sweep k_eff(v), then the boule N_A(z)/V_t(z) at the representative pull rates (no plotting)."""
    keff_sweep = tuple(
        effective_segregation_coefficient(K0, normalized_growth_velocity(v)) for v in PULL_SWEEP)
    realistic_keff_max = effective_segregation_coefficient(
        K0, normalized_growth_velocity(REALISTIC_PULL_MAX))

    z = np.linspace(0.0, Z_MAX, 80)
    n_a_by_pull: dict = {}
    v_t_by_pull: dict = {}
    v_t_walk_by_pull: dict = {}
    demo_keffs = []
    z_positions: tuple[float, ...] = ()
    for pull in DEMO_PULLS:
        recipe = _recipe(pull)
        demo_keffs.append(recipe.boule.k)                       # k₀ for None, k_eff otherwise
        n_a_by_pull[_label(pull)] = tuple(float(x) for x in recipe.boule.axial_doping(z))
        # V_t down the boule through the real pipeline (one die / wafer, no variation — the clean signal).
        batch = run_batch(recipe, n_wafers=N_WAFERS, z_max=Z_MAX, seed=SEED,
                          variation=NO_VARIATION, grid_n=1)
        z_positions = batch.z_positions
        vts = tuple(batch.mean_V_t(w) for w in batch.wafers)
        v_t_by_pull[_label(pull)] = vts
        v_t_walk_by_pull[_label(pull)] = vts[-1] - vts[0]

    return DemoResult(
        k0=K0, realistic_pull_max=REALISTIC_PULL_MAX,
        pull_sweep=PULL_SWEEP, keff_sweep=keff_sweep, realistic_keff_max=realistic_keff_max,
        demo_pulls=DEMO_PULLS, demo_keffs=tuple(demo_keffs),
        na_z=tuple(float(x) for x in z), z_positions=z_positions,
        n_a_by_pull=n_a_by_pull, v_t_by_pull=v_t_by_pull,
        v_t_walk_by_pull=v_t_walk_by_pull,
        v_t_lo=DEFAULT_SPECS.v_t.lo, v_t_hi=DEFAULT_SPECS.v_t.hi,
    )


def print_summary(r: DemoResult) -> None:
    """Print the k_eff(v) → flatter-boule → V_t-walk story — the demo's payoff in text (no score)."""
    print("\nCrystal growth CG-1: pull rate → effective segregation k_eff(v) → a flatter Scheil boule\n")

    print(f"  k_eff(v) for boron (k₀ = {r.k0:.2f}) — Burton–Prim–Slichter (k_eff → 1 as pull → ∞):")
    for pull, keff in zip(r.demo_pulls, r.demo_keffs):
        tag = "  (well-mixed seam = G2's k₀)" if pull is None else (
            "  (beyond realistic Si pull — illustrative)" if pull and pull > r.realistic_pull_max else
            "  (realistic Si pull)")
        print(f"     {_label(pull):18s}: k_eff = {keff:.3f}   V_t walk (seed→tail) "
              f"{r.v_t_walk_by_pull[_label(pull)]:+.3f} V{tag}")
    print(f"\n  Honest magnitude: at realistic Si pull (≤ {r.realistic_pull_max:.0f} mm/min) k_eff only reaches "
          f"≈{r.realistic_keff_max:.2f} —")
    print(f"  boron barely segregates already (k₀={r.k0:.2f}), so the flattening is MODEST; the near-flat")
    print(f"  boule needs pull rates beyond realistic Si growth (the high-pull curve is illustrative).\n")

    print(f"  Consequence (V_t spec [{r.v_t_lo:.2f}, {r.v_t_hi:.2f}] V): the equilibrium boule's tail exits the")
    print(f"  ceiling; a faster pull keeps more of the boule in spec — the BENEFIT side. The COST of")
    print(f"  pulling faster (point-defect microvoids = CG-2, striations, dislocation/max-pull) is the")
    print(f"  deferred next deepening, NOT modelled here — so this is no 'pull faster wins' claim.\n")
    print("  New: the cited BPS k_eff (chip.czochralski, triad-tested); the pull-rate knob is opt-in")
    print("  (default = the well-mixed k₀ seam → the G2/G7 boule demos are byte-for-byte unchanged).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the CG-1 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import crystal_growth_figure

    fig = crystal_growth_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # k₀, →, ≈ on legacy codepages

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
