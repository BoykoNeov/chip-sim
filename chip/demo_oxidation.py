"""The Phase-2 anchor demo: thermal oxide grown by Deal–Grove — recipe in, oxide out.

The chip's **second exact anchor** and its one closed-form step. Where Phase 1a diffused dopant
through the PDE spine, this grows **SiO₂** by the analytic **Deal–Grove** linear-parabolic
law (:mod:`oxidation`) — no engine, just the closed form ``x_ox² + A·x_ox = B(t+τ)``. The headline is
the **wet-vs-dry** contrast on one wafer:

  * **dry O₂** — slow, controllable: the **gate-oxide** ambient (tens of nm in tens of minutes).
  * **wet H₂O** — ~6× faster: the **field/masking-oxide** ambient (sub-µm in an hour).

Over a sweep of time the curve rides the **linear** ``(B/A)·t`` asymptote while thin
(reaction-limited) and bends onto the **parabolic** ``√(B·t)`` asymptote when thick
(diffusion-limited) — the two regimes the plan names, drawn straight on the figure. Each micron of
oxide also **eats 0.44 µm of silicon** (the moving-boundary bookkeeping).

Published comparison points (reference facts, not redistributed data): at 1100 °C / 1 h on (100)
silicon, **dry ≈ 0.10 µm**, **wet ≈ 0.64 µm** (Deal & Grove 1965; Plummer–Deal–Griffin; Jaeger — the
``[[deal-grove-oxidation-source]]`` note). The rate constants are cited, *not* fit to these — so the
agreement is a cross-check, not a tautology.

Run headless (saves the figure, prints the table):

    python -m chip.demo_oxidation
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import oxidation as ox

# The demo recipe (a representative oxidation showing the wet/dry contrast and both regimes).
T_OX = 1100.0                  # °C — hot enough that wet reaches the parabolic regime within hours
ORIENTATION = "100"            # the device-relevant face (the Phase-4 MOS is built on (100))
T_TABLE_MIN = 60.0             # the 1-hour point compared to the published table
T_RANGE_HOURS = (1.0e-2, 1.0e1)   # 0.6 min → 10 h: spans the linear→parabolic bend
N_T = 200

# Published comparison points (reference facts — Deal–Grove/Plummer/Jaeger), (100), 1100 °C, 1 h.
# Drawn/printed for context, not asserted (the tests carry the loose benchmark band).
PUBLISHED_DRY_UM = 0.10
PUBLISHED_WET_UM = 0.64

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-oxidation.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-oxidation.png"


def compute():
    """Run the wet & dry Deal–Grove sweeps; return ``(t_hours, curves, table)``.

    ``curves`` is the list of ``(label, x_ox, B, A, color)`` the figure consumes (one per ambient,
    sharing ``t_hours``); ``table`` is ``{ambient: OxideGrowth}`` at the 1-hour table point.
    """
    from .plots import DRY_COLOR, WET_COLOR

    t_hours = np.logspace(np.log10(T_RANGE_HOURS[0]), np.log10(T_RANGE_HOURS[1]), N_T)
    curves = []
    table = {}
    for ambient, label, color in (("dry", "dry O₂", DRY_COLOR), ("wet", "wet H₂O", WET_COLOR)):
        r = ox.oxide_rate_constants(ambient, T_OX, ORIENTATION)
        x_ox = ox.oxide_thickness(t_hours, r.B, r.A)
        curves.append((label, x_ox, r.B, r.A, color))
        table[ambient] = ox.grow_oxide(ambient, T_OX, T_TABLE_MIN, orientation=ORIENTATION)
    return t_hours, curves, table


def print_summary(table) -> None:
    """Print the recipe → rate constants → thickness story — the demo's payoff in text."""
    print(f"\nDeal–Grove thermal oxidation at {T_OX:.0f} °C on ({ORIENTATION}) silicon\n")
    published = {"dry": PUBLISHED_DRY_UM, "wet": PUBLISHED_WET_UM}
    for ambient in ("dry", "wet"):
        g = table[ambient]
        r = g.rates
        print(f"  {ambient:>3} ({'O₂' if ambient == 'dry' else 'H₂O'}):  "
              f"B = {r.B:.3e} µm²/hr,  B/A = {r.B_over_A:.3e} µm/hr,  A = {r.A:.3f} µm")
        print(f"        → {T_TABLE_MIN:.0f} min: x_ox = {g.t_ox:.3f} µm ({g.t_ox_nm:.0f} nm)  "
              f"[published ~{published[ambient]:.2f} µm];  regime: {g.regime}")
        print(f"          consumes {g.si_consumed:.3f} µm Si "
              f"(+ {g.oxide_above_original_surface:.3f} µm above the surface = {g.t_ox:.3f} µm oxide)\n")
    wet, dry = table["wet"].t_ox, table["dry"].t_ox
    print(f"  → wet grows {wet / dry:.1f}× faster than dry (H₂O diffuses through oxide far faster than O₂)\n")


def save_figure(t_hours, curves) -> Path:
    """Render and save the oxide-growth artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import oxidation_figure

    fig = oxidation_figure(t_hours, curves, T_celsius=T_OX, orientation=ORIENTATION)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ₂, µ, → on legacy codepages

    t_hours, curves, table = compute()
    print_summary(table)
    try:
        saved = save_figure(t_hours, curves)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
