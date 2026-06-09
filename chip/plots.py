"""Chip-local plot helpers — the render layer (Chip Phase 1a; ADR 0002).

The **viz floor**: static matplotlib figures that *consume* the plain arrays
:mod:`diffusion_dopant` / :mod:`junction` produce. Per ADR 0002 this layer is strictly
downstream of correctness — a figure draws already-validated numbers, it is never evidence of
validity (the triad tests do that). It is the only place in chip that imports a plotting
library; the compute modules stay headless so the test suite never needs matplotlib.

The headline view is the **mechanism** one ADR 0002 §5 calls for: the ``erfc`` → Gaussian
**profile morph** as predeposition gives way to drive-in, so a learner sees *why the junction
moves* — the fixed dose spreading deeper, the surface concentration falling, the profile
crossing the background doping further from the surface. These helpers start project-local; a
primitive earns promotion to a shared ``viz/`` only by rule-of-three (ARCHITECTURE.md §6) —
chip's concentration-vs-depth line is the candidate third use of steel's profile-vs-depth line.

Requires the optional ``viz`` extra (``pip install -e .[viz]``).
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from .diffusion_dopant import DopantProfile, CM_PER_UM
from .junction import Junction

# Stable colours: warm = the shallow predep source step, cool = the deep redistributed drive-in.
PREDEP_COLOR = "#e07b39"      # warm — the constant-source erfc, concentrated near the surface
DRIVEIN_COLOR = "#2f6fb0"     # cool — the sealed-surface Gaussian, spread deep
BACKGROUND_COLOR = "#888888"  # the wafer's opposite-type background doping N_B
JUNCTION_COLOR = "#c0392b"    # the pn junction (where the profile crosses N_B)


def _depth_um(x: np.ndarray) -> np.ndarray:
    """Cell-centre depths cm → µm (the reported length unit)."""
    return np.asarray(x) / CM_PER_UM


def junction_figure(
    predep: DopantProfile,
    drivein: DopantProfile,
    junction: Junction,
    morph: list[tuple[str, np.ndarray, np.ndarray]] | None = None,
    dopant_label: str = "boron",
) -> "plt.Figure":
    """The banked pn-junction artifact: the two-step profile + junction, beside the morph.

    Left panel (**the junction** — the banked readout): the predep ``erfc`` and the final
    drive-in profile on one depth axis (log concentration), the background ``N_B`` as a horizontal
    line, and the junction depth ``x_j`` marked where the drive-in crosses it — with ``x_j`` and
    ``R_s`` annotated. *Recipe in, junction out.*

    Right panel (**the mechanism** — why the junction moves): ``morph`` is an optional list of
    ``(label, x_cm, N)`` snapshots of the drive-in at increasing times, showing the ``erfc``
    relaxing toward a Gaussian as the fixed dose spreads deeper and the surface falls. If omitted,
    only the junction panel is drawn.

    Consumes plain arrays / the :class:`Junction` dataclass — no live solver object (ADR 0002).
    """
    ncols = 2 if morph else 1
    fig, axes = plt.subplots(1, ncols, figsize=(13 if morph else 7.5, 6), squeeze=False)
    ax_j = axes[0][0]

    # --- left: the junction readout -------------------------------------------------
    xj_um = junction.x_j_um
    ax_j.semilogy(_depth_um(predep.x), np.maximum(predep.N, 1.0), color=PREDEP_COLOR, lw=2,
                  label=f"predeposition (erfc), surface {predep.N[0]:.1e} cm⁻³")
    ax_j.semilogy(_depth_um(drivein.x), np.maximum(drivein.N, 1.0), color=DRIVEIN_COLOR, lw=2.4,
                  label=f"drive-in (≈Gaussian), surface {drivein.N[0]:.1e} cm⁻³")
    ax_j.axhline(junction.N_background, color=BACKGROUND_COLOR, ls="--", lw=1.4,
                 label=f"background $N_B$ = {junction.N_background:.0e} cm⁻³")
    ax_j.axvline(xj_um, color=JUNCTION_COLOR, ls=":", lw=1.8)
    ax_j.plot([xj_um], [junction.N_background], "o", color=JUNCTION_COLOR, ms=8, zorder=5)
    ax_j.annotate(
        f"pn junction\n$x_j$ = {xj_um:.2f} µm\n$R_s$ = {junction.R_s:.0f} Ω/sq",
        xy=(xj_um, junction.N_background),
        xytext=(xj_um * 0.42, junction.N_background * 40),
        color=JUNCTION_COLOR, fontsize=10, ha="center",
        arrowprops=dict(arrowstyle="->", color=JUNCTION_COLOR, lw=1.2),
    )
    upper = max(predep.N[0], drivein.N[0]) * 3
    ax_j.set_ylim(junction.N_background * 0.2, upper)
    ax_j.set_xlim(0, min(_depth_um(drivein.x)[-1], xj_um * 2.2))
    ax_j.set_xlabel("depth  (µm)")
    ax_j.set_ylabel("dopant concentration $N$  (cm⁻³)")
    ax_j.set_title(f"pn junction from a two-step {dopant_label} diffusion")
    ax_j.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    ax_j.grid(True, which="both", alpha=0.18)

    # --- right: the erfc → Gaussian morph (mechanism) -------------------------------
    if morph:
        ax_m = axes[0][1]
        n = len(morph)
        cmap = plt.get_cmap("viridis")
        for k, (label, x, N) in enumerate(morph):
            ax_m.semilogy(_depth_um(x), np.maximum(N, 1.0), lw=2,
                          color=cmap(k / max(n - 1, 1)), label=label)
        ax_m.axhline(junction.N_background, color=BACKGROUND_COLOR, ls="--", lw=1.2)
        ax_m.set_ylim(junction.N_background * 0.2, morph[0][2][0] * 3)
        ax_m.set_xlim(0, min(_depth_um(drivein.x)[-1], xj_um * 2.2))
        ax_m.set_xlabel("depth  (µm)")
        ax_m.set_ylabel("dopant concentration $N$  (cm⁻³)")
        ax_m.set_title("the morph: erfc → Gaussian as the dose drives in")
        ax_m.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
        ax_m.grid(True, which="both", alpha=0.18)

    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return fig
