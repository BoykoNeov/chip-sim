"""Lateral dopant diffusion under a mask edge — the 2-D regime (Chip v1.8).

The consumer that finally pulls in the engine's **last deferred regime** (``Diffusion2D``, the
2026-06-11 third amendment of the unfreeze). Every prior chip diffusion step was 1-D: dopant
goes *down* into the wafer. But a real diffusion is patterned by a **mask** — the dopant enters
only through an open *window* in an oxide/nitride mask — and under the mask edge it spreads not
just down but **sideways**, *under the mask*. That lateral encroachment sets the real channel
length of a MOSFET (the gate doesn't fully control the laterally-diffused region), so it is a
first-class device-geometry effect, not a footnote.

The configuration (the cited one — see :mod:`engines.diffusion.diffusion2d` and the
``[[lateral-diffusion-source]]`` note) is a **constant-surface-source** diffusion through a mask
window: the surface is held at the solubility limit ``N_s`` where the window is **open**
(a :class:`~engines.diffusion.Dirichlet` face) and **sealed** (no-flux) under the mask. That
*piecewise* surface BC — :class:`~engines.diffusion.MaskedSurface` — is what makes the problem
genuinely 2-D: a uniform surface BC would keep it a product of two 1-D solves (separable), and the
lateral-under-mask curvature comes precisely from the *step* in the BC at the mask edge.

The headline result (the benchmark): the **lateral junction reaches ≈ 0.75–0.85 of the vertical
junction depth** — the classic "lateral diffusion ≈ 0.8 × vertical" rule. It is **contour-
dependent** (the ratio rises toward deeper, lower-``C_B/N_s`` contours), which falls straight out
of the 2-D solve here: a real device measures the ratio at its own background ``N_B``.

Why this is non-separable (and so *needs* the 2-D engine)
--------------------------------------------------------
A fully separable problem (uniform BCs, separable IC) is *exactly* the outer product of two 1-D
runs — the 1-D engine already does it, no 2-D needed. The mask edge breaks separability. So this
module is the honest demonstration that the 2-D regime earns its place: the **window-bulk** column
(far from the edge) recovers the 1-D constant-source ``erfc`` to machine-ish precision (the seam
back to the spine), while the **edge** region is irreducibly 2-D.

Units — semiconductor CGS, as the rest of chip
----------------------------------------------
Lengths in **cm** internally (``D`` is native Fair cm²/s, ``N_s`` native Trumbore cm⁻³), reported
in **µm** at the API boundary. Times in **s** (minutes accepted at the entry point). The dopant
registry, Arrhenius ``D(T)``, and solubilities are reused verbatim from :mod:`diffusion_dopant` —
this module adds only the 2-D geometry, no new physical constant.

Validation boundary
-------------------
The 2-D solver machinery (conservation, the dimensional-collapse seam, isotropy, monotonicity) is
the engine's, validated in ``engines/diffusion/tests/test_diffusion2d.py``. This module's tests
validate the **mask-edge instantiation**: the window-bulk column == the 1-D ``erfc`` (the seam),
and the lateral/vertical ratio vs the cited 0.75–0.85 band + its contour-dependence (the benchmark).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engines.diffusion import Diffusion2D, uniform_grid_2d, Neumann, MaskedSurface
from .diffusion_dopant import DOPANTS, Dopant, diffusivity, CM_PER_UM


# --------------------------------------------------------------------------- #
# The 2-D mask-edge profile
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MaskEdgeProfile:
    """A 2-D dopant field ``N(x, y)`` from a masked constant-source diffusion.

    ``x`` are lateral cell centers, ``y`` depth cell centers (both **cm**, from the wafer
    surface ``y=0``); ``N`` is the ``(nx, ny)`` profile (**cm⁻³**), ``N[i, j]`` at lateral
    ``x[i]`` / depth ``y[j]``. The **window** is open for ``x < x_edge`` (held at ``N_surface``);
    the **mask** seals ``x ≥ x_edge`` (no-flux). ``x = 0`` is the window's symmetry centre (a
    no-flux plane), so the ``N[0, :]`` column is the pristine 1-D constant-source profile.
    """

    x: np.ndarray
    y: np.ndarray
    N: np.ndarray
    x_edge: float           # cm — the mask edge (window: x < x_edge, mask: x ≥ x_edge)
    t: float                # s
    D: float                # cm²/s
    N_surface: float        # cm⁻³ (the window Dirichlet value)
    dopant: str
    T_celsius: float

    @property
    def window_column(self) -> np.ndarray:
        """The depth profile at the window centre ``x=0`` — the 1-D constant-source column."""
        return self.N[0, :]


@dataclass(frozen=True)
class JunctionGeometry:
    """The pn-junction geometry a mask-edge diffusion produces, at a background doping ``N_B``.

    ``vertical_um`` is the junction depth under the deep window (the 1-D junction); ``lateral_um``
    is how far the ``N = N_B`` contour reaches **under the mask**, measured from the mask edge;
    ``ratio = lateral / vertical`` is the cited lateral-diffusion ratio (≈ 0.75–0.85).
    """

    N_B: float
    vertical_um: float
    lateral_um: float
    ratio: float


# --------------------------------------------------------------------------- #
# The masked constant-source diffusion (the engine call)
# --------------------------------------------------------------------------- #
def lateral_diffusion(
    dopant: Dopant | str = "B",
    *,
    T_celsius: float = 1100.0,
    t_min: float = 60.0,
    N_surface: float | None = None,
    length_x_um: float = 4.0,
    length_y_um: float = 2.5,
    x_edge_um: float = 2.0,
    nx: int = 200,
    ny: int = 160,
    n_steps: int = 400,
) -> MaskEdgeProfile:
    """Constant-source diffusion through a mask window → the 2-D profile under the mask edge.

    The surface ``y=0`` is held at ``N_surface`` (default the dopant's solid-solubility limit)
    where the window is open (``x < x_edge``) and sealed under the mask (``x ≥ x_edge``); the
    other three faces are no-flux (``x=0`` = window symmetry centre, ``x=Lx`` = far under the
    mask, ``y=Ly`` = deep bulk — all chosen far enough that the junction contour is contained).

    Returns a :class:`MaskEdgeProfile`; read its junction with :func:`junction_geometry`.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    Ns = d.N_solid_solubility if N_surface is None else float(N_surface)
    D = diffusivity(d, T_celsius)
    Lx, Ly = length_x_um * CM_PER_UM, length_y_um * CM_PER_UM
    x_edge = x_edge_um * CM_PER_UM

    grid = uniform_grid_2d(Lx, Ly, nx, ny)
    window = grid.x.centers < x_edge                      # open where the window is, sealed under mask
    solver = Diffusion2D(
        grid, D,
        bc_xlo=Neumann(0.0), bc_xhi=Neumann(0.0),         # window symmetry centre / far under mask
        bc_ylo=MaskedSurface(Ns, window),                 # the surface: window Dirichlet | masked no-flux
        bc_yhi=Neumann(0.0),                              # deep bulk, no-flux
    )
    N = solver.solve(np.zeros(grid.shape), t_min * 60.0, (t_min * 60.0) / n_steps)
    return MaskEdgeProfile(
        x=grid.x.centers, y=grid.y.centers, N=N, x_edge=x_edge,
        t=t_min * 60.0, D=D, N_surface=Ns, dopant=d.name, T_celsius=T_celsius,
    )


# --------------------------------------------------------------------------- #
# Contour geometry — the junction reading
# --------------------------------------------------------------------------- #
def _last_crossing(coord: np.ndarray, values: np.ndarray, level: float) -> float:
    """The largest ``coord`` at which ``values`` crosses ``level`` (linear-interpolated).

    ``values`` is monotone-ish decreasing along ``coord`` (a diffusion tail); returns the
    interpolated coordinate of the deepest/furthest ``values == level`` crossing, or the first
    coordinate if it never reaches ``level`` (junction at the surface).
    """
    above = values >= level
    if not above.any():
        return float(coord[0])
    i = np.where(above)[0][-1]
    if i == values.size - 1:
        return float(coord[i])                            # contour runs off the domain edge
    # linear interpolation between coord[i] (≥ level) and coord[i+1] (< level)
    f = (values[i] - level) / (values[i] - values[i + 1])
    return float(coord[i] + f * (coord[i + 1] - coord[i]))


def junction_geometry(profile: MaskEdgeProfile, N_B: float) -> JunctionGeometry:
    """Measure the ``N = N_B`` junction's vertical depth and lateral under-mask reach.

    *Vertical*: the junction depth in the window-centre column (the 1-D junction). *Lateral*: the
    furthest the ``N = N_B`` contour reaches beyond the mask edge, over all depths (the contour
    wraps under the mask; its rightmost extent is the lateral diffusion distance). Both in **µm**.
    """
    x, y, N, x_edge = profile.x, profile.y, profile.N, profile.x_edge
    vertical = _last_crossing(y, profile.window_column, N_B)
    lateral_x = max(_last_crossing(x, N[:, j], N_B) for j in range(y.size))
    lateral = max(lateral_x - x_edge, 0.0)
    ratio = lateral / vertical if vertical > 0.0 else 0.0
    return JunctionGeometry(
        N_B=N_B,
        vertical_um=vertical / CM_PER_UM,
        lateral_um=lateral / CM_PER_UM,
        ratio=ratio,
    )
