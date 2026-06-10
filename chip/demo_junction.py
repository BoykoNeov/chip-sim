"""The Phase-1a anchor demo: a pn junction from a two-step diffusion — recipe in, junction out.

*One solver, the chip face of the spine.* The frozen :mod:`engines.diffusion` that cooled
Steel's Jominy bar (heat mode) and carburized its gear tooth (carbon mass mode) now diffuses
**boron into silicon** (dopant mass mode) — proving the program spine reuses verbatim. The
classic two-step process:

  1. **Predeposition** — 950 °C, 15 min, surface held at the boron solid-solubility limit
     (≈ 3e20 cm⁻³): a thin ``erfc`` layer, dose-controlled (the Dirichlet face).
  2. **Drive-in** — 1100 °C, 30 min, surface **sealed**: the fixed dose redistributes ~8×
     deeper, the profile morphing from ``erfc`` toward a Gaussian (the Neumann(0) face), the
     surface concentration falling an order of magnitude.

A **pn junction** emerges where the boron profile crosses the wafer's n-type background
(``N_B`` = 1e15 cm⁻³): the junction depth ``x_j`` and the diffused-layer sheet resistance
``R_s`` are read off (:mod:`junction`). This is the banked Phase-1a artifact and the integration
test of the dopant mass-mode chain: ``diffusion_dopant.two_step`` → ``junction.analyze_junction``
→ ``plots``.

Published comparison points (reference facts, not redistributed data): a boron base/well
diffusion of this kind gives a junction ~1 µm deep and a sheet resistance of order 10²
Ω/sq (Plummer–Deal–Griffin; Sze; Irvin 1962, BSTJ 41:387 for the ``R_s·x_j`` curves the
benchmark cites). The diffusivity (Fair) and mobility (Masetti) are cited, *not* fit to these —
so the agreement is a cross-check, not a tautology.

Run headless (saves the figure, prints the table):

    python -m chip.demo_junction
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from engines.diffusion import uniform_grid
from . import diffusion_dopant as dd
from . import junction as jn

# The two-step recipe (the canonical Phase-1a anchor; mirrors diffusion_dopant.two_step defaults).
DOPANT = "B"
T_PREDEP, T_PREDEP_MIN = 950.0, 15.0       # predeposition: hot, short → a thin erfc source layer
T_DRIVEIN, T_DRIVEIN_MIN = 1100.0, 30.0    # drive-in: hotter, longer → deep redistribution
N_SURFACE = dd.DOPANTS["B"].N_solid_solubility   # predep at the solid-solubility limit (~3e20)
N_BACKGROUND = 1.0e15                       # n-type wafer background → the pn junction
LENGTH_UM, N_CELLS = 3.0, 600

# Published comparison band (reference facts — Plummer/Sze/Irvin). Drawn/printed for context, not
# asserted (the tests carry the loose benchmark; Irvin's curves are graphical).
PUBLISHED_XJ_UM = (0.5, 1.5)
PUBLISHED_RS_OHM_SQ = (50.0, 300.0)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-junction.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-junction.png"


def compute():
    """Run the whole Phase-1a chain; return ``(predep, drivein, junction, morph)``.

    ``morph`` is the list of ``(label, x, N)`` snapshots for the mechanism panel — the predep
    ``erfc`` then the drive-in at increasing elapsed times (the erfc→Gaussian relaxation).
    """
    grid = uniform_grid(LENGTH_UM * dd.CM_PER_UM, N_CELLS)
    predep = dd.predeposit(grid, DOPANT, T_PREDEP, T_PREDEP_MIN * 60.0, N_surface=N_SURFACE)
    drivein = dd.drive_in(grid, predep.N, DOPANT, T_DRIVEIN, T_DRIVEIN_MIN * 60.0)
    junction = jn.analyze_junction(drivein, DOPANT, N_BACKGROUND)

    # Morph snapshots: predep (drive-in t=0), then 1/4, 1/2, full drive-in time.
    morph = [("predep (erfc)", predep.x, predep.N)]
    for frac in (0.25, 0.5, 1.0):
        snap = dd.drive_in(grid, predep.N, DOPANT, T_DRIVEIN, T_DRIVEIN_MIN * 60.0 * frac)
        morph.append((f"drive-in {int(frac * T_DRIVEIN_MIN)} min", snap.x, snap.N))
    return predep, drivein, junction, morph


def print_summary(predep, drivein, junction) -> None:
    """Print the recipe → profile → junction story — the demo's payoff in text."""
    print(f"\nTwo-step {DOPANT} diffusion → pn junction into {N_BACKGROUND:.0e} cm⁻³ n-type Si\n")
    print(f"  predeposition: {T_PREDEP:.0f} °C, {T_PREDEP_MIN:.0f} min, "
          f"surface {predep.N_surface:.2e} cm⁻³ (solid-solubility, D = {predep.D:.2e} cm²/s)")
    print(f"     dose laid down: ∫N dx = {predep.dose:.3e} cm⁻²  "
          f"(= surface-flux integral {predep.surface_flux_dose:.3e}, "
          f"resid {abs(predep.dose - predep.surface_flux_dose) / predep.dose:.1e})")
    print(f"  drive-in:      {T_DRIVEIN:.0f} °C, {T_DRIVEIN_MIN:.0f} min, sealed surface "
          f"(D = {drivein.D:.2e} cm²/s)")
    print(f"     dose conserved: ∫N dx = {drivein.dose:.3e} cm⁻²  "
          f"(resid {abs(drivein.dose - predep.dose) / predep.dose:.1e}); "
          f"surface fell {predep.N[0]:.2e} → {drivein.N[0]:.2e} cm⁻³\n")
    print(f"  → junction depth  x_j = {junction.x_j_um:.3f} µm   "
          f"(published ~{PUBLISHED_XJ_UM[0]:.1f}–{PUBLISHED_XJ_UM[1]:.1f} µm)")
    print(f"  → sheet resistance R_s = {junction.R_s:.0f} Ω/sq   "
          f"(published ~{PUBLISHED_RS_OHM_SQ[0]:.0f}–{PUBLISHED_RS_OHM_SQ[1]:.0f} Ω/sq)")
    print(f"  → average resistivity R_s·x_j = {junction.rho_avg:.3e} Ω·cm  (Irvin's plotted quantity)\n")
    hdr = f"{'depth(µm)':>10} {'N(cm⁻³)':>12}"
    print(hdr); print("-" * len(hdr))
    idx = np.linspace(0, drivein.x.size - 1, 10).astype(int)
    for i in idx:
        print(f"{drivein.x[i] / dd.CM_PER_UM:10.3f} {drivein.N[i]:12.3e}")


def save_figure(predep, drivein, junction, morph) -> Path:
    """Render and save the pn-junction artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import junction_figure

    fig = junction_figure(predep, drivein, junction, morph=morph, dopant_label="boron")
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ⁻³, ≈ on legacy codepages

    predep, drivein, junction, morph = compute()
    print_summary(predep, drivein, junction)
    try:
        saved = save_figure(predep, drivein, junction, morph)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
