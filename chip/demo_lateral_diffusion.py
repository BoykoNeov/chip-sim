"""The v1.8 anchor demo: **lateral diffusion under a mask edge** — the 2-D regime, banked.

The engine's last deferred regime (``Diffusion2D``), pulled in by its named consumer. A boron
constant-source diffusion enters the wafer through an open **window** in a mask and spreads both
*down* and **sideways under the mask**; the pn junction (where ``N`` crosses the background ``N_B``)
is a 2-D contour that curves under the mask edge. Two stories on one figure:

  * **The banked readout (left) — the junction curving under the mask.** The 2-D boron field
    ``N(x, y)`` (log scale, depth downward), the mask drawn on the surface (open window | hatched
    mask), and the ``N = N_B`` junction contour overlaid — flat and deep under the window, wrapping
    up and **under the mask** at the edge. The **vertical** junction depth (window centre) and the
    **lateral** reach under the mask are marked; their ratio is the headline.

  * **The mechanism (right) — the lateral/vertical ratio and its contour-dependence.** The cited
    "lateral ≈ 0.8 × vertical" rule is not a single number: the ratio **rises toward deeper
    (lower-``C_B/N_s``) contours** — Kennedy–O'Brien's finding that the junction sits closer to its
    source at the surface than in the bulk — which falls straight out of the 2-D solve. The
    engine-computed ratio vs ``C_B/N_s`` passes through the cited **0.75–0.85 band** (shaded) at the
    shallow contours and runs a touch *above* it deeper, reaching ~0.9 at a realistic device
    junction. That ~0.9 is the model's own deep-contour value (within the read-off uncertainty of the
    1965 graph — **not** a sourced number); the benchmark is *loose* — the validation weight is
    carried by the tight ``erfc`` window-column anchor below, not by hitting 0.8 precisely.

The seam back to the spine: the **window-centre column** (``x = 0``, far from the edge) is the
pristine 1-D constant-source ``erfc`` — its junction depth matches the analytic
``erfcinv(C_B/N_s)·2√(Dt)`` to numerical precision. The 2-D regime earns its place only at the
*edge*, where the problem is non-separable.

System: **boron**, **1100 °C / 60 min**, surface at the Trumbore solubility ``N_s = 3×10²⁰ cm⁻³``;
mask edge 2 µm from the window centre. Reference facts (cited, not rederived — the
``[[lateral-diffusion-source]]`` note): the constant-surface-source mask-window configuration and its
contour-dependent lateral/vertical ratio, anchored on the constant-source worked point ≈ 0.82 at
``C_B/N_s = 10⁻⁴`` (after Kennedy–O'Brien 1965, via a secondary fabrication text). The model
reproduces the regime and the contour-dependence, landing within ~5–10 % of that one cited point —
running slightly high, **not** more accurate than the 1965 solution.

Run headless (saves the figure, prints the table):

    python -m chip.demo_lateral_diffusion
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.special import erfcinv

from . import diffusion_2d
from .diffusion_dopant import CM_PER_UM

# The demo recipe — a boron source/drain-like constant-source diffusion through a mask window.
DOPANT = "B"
T_CELSIUS = 1100.0
T_MIN = 60.0
LENGTH_X_UM = 4.0
LENGTH_Y_UM = 2.5
X_EDGE_UM = 2.0
NX, NY = 200, 160
N_STEPS = 400

# The device junction (the headline contour) and the contour family that shows the dependence.
N_B_DEVICE = 1.0e15                                  # a realistic lightly-doped wafer background
CONTOUR_FRACS = (1.0e-2, 1.0e-3, 1.0e-4, 1.0e-5)    # C_B / N_s for the ratio-vs-contour curve

# The cited constant-source rule-of-thumb band (lateral ≈ 0.75–0.85 × vertical) — drawn as the
# shaded reference. Anchored on K–O's worked point ≈ 0.82 at C_B/N_s = 1e-4 ([[lateral-diffusion-
# source]]); the model's curve passes through it at shallow contours and runs slightly above deeper.
RATIO_BAND = (0.75, 0.85)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-lateral-diffusion.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-lateral-diffusion.png"


def _analytic_vertical_um(frac: float, D: float, t: float) -> float:
    """The 1-D constant-source junction depth ``erfcinv(C_B/N_s)·2√(Dt)`` (µm) — the seam check."""
    return float(erfcinv(frac) * 2.0 * math.sqrt(D * t)) / CM_PER_UM


def compute():
    """Run the demo: the 2-D field, the device junction, and the ratio-vs-contour family.

    Returns a dict of plain arrays/scalars (ADR 0002 — no live object crosses to the view).
    """
    profile = diffusion_2d.lateral_diffusion(
        DOPANT, T_celsius=T_CELSIUS, t_min=T_MIN,
        length_x_um=LENGTH_X_UM, length_y_um=LENGTH_Y_UM, x_edge_um=X_EDGE_UM,
        nx=NX, ny=NY, n_steps=N_STEPS,
    )
    device = diffusion_2d.junction_geometry(profile, N_B_DEVICE)

    fracs = np.array(CONTOUR_FRACS)
    geoms = [diffusion_2d.junction_geometry(profile, f * profile.N_surface) for f in fracs]
    ratios = np.array([g.ratio for g in geoms])
    verticals = np.array([g.vertical_um for g in geoms])
    laterals = np.array([g.lateral_um for g in geoms])
    # The seam: the window-centre vertical junction is the analytic 1-D erfc junction.
    analytic_vert = np.array([_analytic_vertical_um(f, profile.D, profile.t) for f in fracs])

    return dict(
        profile=profile, device=device, N_B_device=N_B_DEVICE,
        fracs=fracs, ratios=ratios, verticals=verticals, laterals=laterals,
        analytic_vert=analytic_vert, ratio_band=RATIO_BAND,
    )


def print_summary(data) -> None:
    """Print the lateral-diffusion story — the demo's payoff in text."""
    p, dev = data["profile"], data["device"]
    print(f"\nLateral diffusion under a mask edge — {p.dopant}, {p.T_celsius:.0f} °C / "
          f"{p.t / 60:.0f} min, N_s = {p.N_surface:.1e} cm⁻³\n")
    print(f"  diffusion length 2√(Dt) = {2 * math.sqrt(p.D * p.t) / CM_PER_UM:.3f} µm   "
          f"(D = {p.D:.2e} cm²/s); mask edge at x = {p.x_edge / CM_PER_UM:.1f} µm\n")
    print(f"  Device junction (N_B = {data['N_B_device']:.0e} cm⁻³): "
          f"vertical = {dev.vertical_um:.3f} µm, lateral = {dev.lateral_um:.3f} µm  "
          f"→ ratio = {dev.ratio:.2f}\n")
    print("  The cited rule is contour-dependent (the ratio rises toward deeper contours):")
    print("    {:>10} {:>12} {:>12} {:>8} {:>14}".format(
        "C_B/N_s", "vertical µm", "lateral µm", "ratio", "1-D erfc µm"))
    for frac, v, l, r, av in zip(data["fracs"], data["verticals"], data["laterals"],
                                 data["ratios"], data["analytic_vert"]):
        print(f"    {frac:>10.0e} {v:>12.3f} {l:>12.3f} {r:>8.3f} {av:>14.3f}")
    band = data["ratio_band"]
    print(f"\n  Cited constant-source band lateral/vertical ≈ {band[0]:.2f}–{band[1]:.2f} (≈0.8 rule, "
          f"K–O 1965): the shallow contours sit in it; the curve runs a touch above deeper, so the")
    print(f"  device deep-contour junction reaches ~{dev.ratio:.2f} — the model's value, within the "
          f"read-off uncertainty of the 1965 graph (loose benchmark, not a sourced number).")
    print(f"  Seam (tight anchor): the window-centre vertical junction = the 1-D erfc junction "
          f"erfcinv(C_B/N_s)·2√(Dt) (last two columns agree).\n")


def save_figure(data) -> Path:
    """Render and save the lateral-diffusion artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import lateral_diffusion_figure

    fig = lateral_diffusion_figure(data)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")         # µ, √, ², →, ⁻³ on legacy codepages

    data = compute()
    print_summary(data)
    try:
        saved = save_figure(data)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
