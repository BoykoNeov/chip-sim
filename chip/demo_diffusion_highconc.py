"""The v1.3 anchor demo: concentration-dependent diffusivity D(N) — the high-concentration box.

Phase 1a diffused dopants with a **constant, intrinsic** ``D`` and read a smooth ``erfc`` predep. But
a predeposition runs *at the solid-solubility limit* — the maximum concentration — and there real
diffusion is **concentration-enhanced**: the diffusivity rises with the local carrier concentration,
so the high-concentration front steepens into a near-vertical **"box"** and the junction pushes far
deeper than the constant-``D`` ``erfc`` predicts. This demo makes that visible by running the *same*
phosphorus predeposition two ways on one depth axis and overlaying them:

  * **constant intrinsic ``D``** — the Phase-1a assumption (a smooth ``erfc``);
  * **``D(N)`` (Fair charge-state)** — phosphorus's doubly-negative-vacancy ``(n/n_i)²`` term makes
    ``D`` enormous near the surface and intrinsic in the dilute tail → the **box**, deeper junction.

The decisive build note (the headline): ``D(N)`` is a genuine **nonlinear** diffusivity, and it now
runs on the engine's **native nonlinear path** — wrapped in :class:`~engines.diffusion.StateDependent`
and solved per step by **Picard** (the fully-implicit nonlinear backward-Euler solve). This is the
**first exercise of the engine unfreeze** (ADR 0004): the v1.3 consumer-side lagged-coefficient hook
(a workaround for the then-frozen engine) is **promoted** into the engine itself (:mod:`diffusion_highconc`
is now a thin step-loop over the solver).

The banked artifact (`docs/figures/chip-highconc.png`): two panels — left, the box profile (constant
``D`` erfc vs the ``D(N)`` box, junctions marked); right, the mechanism (``D_eff/D_intrinsic`` vs
depth — huge at the surface, ×1 in the tail — *that* is what carves the box).

Cited basis (reference facts, not redistributed): the Fair charge-state model + coefficients
(Plummer–Deal–Griffin Ch. 7; Fair & Tsai 1977). **Honesty caveat owned on the figure:** this is an
*equilibrium* charge-state model — it captures the box **front** and the deeper junction, but **not**
the anomalous phosphorus **tail** (non-equilibrium I-injection / clustering — Velichko 2019; the named
scope edge). Full electrical activation (``n = N``) is the flagged approximation.

Run headless (saves the figure, prints the table):

    python -m chip.demo_diffusion_highconc
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from engines.diffusion import uniform_grid

from . import diffusion_highconc as hc
from . import diffusion_dopant as dd

# The demo recipe: a phosphorus predeposition at the solubility limit, the regime where the box forms.
DOPANT = "P"                   # the showcase: the (n/n_i)² double-negative-vacancy box driver
T_PREDEP = 1000.0              # °C
T_PREDEP_MIN = 30.0            # min
N_SURFACE = dd.DOPANTS["P"].N_solid_solubility   # 1.2e21 cm⁻³ (Trumbore P solubility)
N_BACKGROUND = 1.0e15          # cm⁻³ — the p-type wafer the n-type box junctions into
N_ACTIVE_MAX = hc.N_ACTIVE_MAX_P   # active-carrier plateau cap (Velichko ~3.4e20) → the physical magnitude
LENGTH_UM = 1.5
N_CELLS = 800
N_STEPS = 800

# NB: repo root is parents[1] for a file in chip/ (post the standalone-chip-sim flatten).
_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-highconc.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-highconc.png"


def compute() -> dict:
    """Run the constant-``D`` vs ``D(N)`` phosphorus predep (+ the ``n¹`` companion) → the figure case.

    Returns a dict carrying the shared depth axis, the three profiles, their junction depths, the
    ``D_eff/D_intrinsic`` enhancement along the box, and the cited annotations.
    """
    grid = uniform_grid(LENGTH_UM * dd.CM_PER_UM, N_CELLS)
    D_int = hc.intrinsic_diffusivity_lowconc(DOPANT, T_PREDEP)
    common = dict(N_surface=N_SURFACE, n_steps=N_STEPS)

    # The headline box is the **active-carrier-capped** (physical) one; the uncapped full-activation
    # model is shown as the upper bound (its (n/n_i)² magnitude is ~10× larger — the activation caveat).
    box = hc.predeposit_highconc(grid, DOPANT, T_PREDEP, T_PREDEP_MIN * 60.0,
                                 n_active_max=N_ACTIVE_MAX, **common)
    box_unc = hc.predeposit_highconc(grid, DOPANT, T_PREDEP, T_PREDEP_MIN * 60.0, **common)
    const = hc.constant_D_predeposit(grid, DOPANT, T_PREDEP, T_PREDEP_MIN * 60.0, D_int,
                                     N_surface=N_SURFACE, n_steps=N_STEPS)

    # the diffusivity enhancement along the (capped) box profile (the mechanism panel)
    enhancement = hc.effective_diffusivity(DOPANT, box.N, T_PREDEP, N_ACTIVE_MAX) / D_int
    enh_unc = hc.effective_diffusivity(DOPANT, box_unc.N, T_PREDEP) / D_int

    def xj(N, x=grid.centers):
        return hc.junction_depth_simple(x, N, N_BACKGROUND) / dd.CM_PER_UM

    return {
        "name": {"P": "phosphorus", "As": "arsenic", "B": "boron", "Sb": "antimony"}[DOPANT],
        "x": grid.centers,
        "box": box.N,                       # the capped (physical) box — the headline
        "box_uncapped": box_unc.N,          # full-activation upper bound (faint on the figure)
        "const": const,
        "enhancement": enhancement,
        "surface_enhancement": float(enhancement[0]),            # ~×42 (capped, physical)
        "surface_enhancement_uncapped": float(enh_unc[0]),       # ~×486 (uncapped upper bound)
        "xj_box": xj(box.N),
        "xj_box_uncapped": xj(box_unc.N),
        "xj_const": xj(const),
        "n_i": hc.intrinsic_carrier_concentration(T_PREDEP),
        "n_active_max": N_ACTIVE_MAX,
        "N_background": N_BACKGROUND,
        "N_surface": N_SURFACE,
        "D_intrinsic": D_int,
    }


def print_summary(case: dict) -> None:
    """Print the recipe → box → deeper-junction story — the demo's payoff in text."""
    print(f"\nConcentration-dependent diffusivity D(N): a {case['name']} predeposition at "
          f"{T_PREDEP:.0f} °C for {T_PREDEP_MIN:.0f} min\n"
          f"(surface at solubility {case['N_surface']:.1e} cm⁻³; n_i = {case['n_i']:.2e} cm⁻³)\n")
    print(f"  surface diffusivity enhancement  D_eff/D_intrinsic (the (n/n_i)² double-neg-vacancy term):")
    print(f"      active-carrier-capped (physical, n≤{case['n_active_max']:.1e}):  ×{case['surface_enhancement']:.0f}")
    print(f"      full activation (n=N, upper bound):                  ×{case['surface_enhancement_uncapped']:.0f}")
    print(f"  junction depth into N_B = {case['N_background']:.0e}:")
    print(f"      constant intrinsic D (erfc):     x_j = {case['xj_const']:.3f} µm")
    print(f"      D(N) box (capped, physical):     x_j = {case['xj_box']:.3f} µm   "
          f"(×{case['xj_box']/case['xj_const']:.1f} deeper)")
    print(f"      D(N) box (uncapped, upper bound):x_j = {case['xj_box_uncapped']:.3f} µm\n")
    print("  → the high-concentration front diffuses fast (enhanced D) and steepens into a BOX; the\n"
          "    dilute tail stays intrinsic. D(N) runs on the engine's NATIVE nonlinear path\n"
          "    (StateDependent + Picard = the fully-implicit nonlinear backward-Euler solve) — the\n"
          "    first exercise of the engine unfreeze (the v1.3 consumer-side lag, promoted).\n"
          "  (the ×486 uncapped magnitude is the raw equilibrium model; the active-carrier plateau cap\n"
          "   gives the physical ×42. scope edge: equilibrium D(n) captures the box front + deeper\n"
          "   junction, NOT the anomalous phosphorus tail — that is non-equilibrium I-injection/clustering.)\n")


def save_figure(case: dict) -> Path:
    """Render and save the box-profile artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import highconc_figure

    fig = highconc_figure(case)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ₂, µ, →, ∫ on legacy codepages

    case = compute()
    print_summary(case)
    try:
        saved = save_figure(case)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
