"""Conservative parabolic (diffusion / heat) solver — the spine of the trio.

Public API (validated at Steel Phase 1a; see CONTRACT.md for the reference):

    from engines.diffusion import (
        Diffusion1D, Grid, uniform_grid, grid_from_edges,
        Dirichlet, Neumann, Robin, StateDependent,
        Diffusion2D, Grid2D, uniform_grid_2d, MaskedSurface,
    )

``StateDependent`` (added 2026-06-10, the first exercise of the unfreeze) wraps a ``D = func(u)``
callable for the native nonlinear (concentration-dependent) diffusivity path. The 2-D solver
(``Diffusion2D`` + ``Grid2D``/``uniform_grid_2d``/``MaskedSurface``, added 2026-06-12, the third
amendment) is the last deferred regime — the tensor-product extension that finally lands the
mask-edge lateral-diffusion consumer; the 1-D scalar BCs (``Dirichlet``/``Neumann``/``Robin``) are
reused for uniform 2-D edges, and ``MaskedSurface`` adds the one genuinely-2-D piecewise edge BC.
"""
from .diffusion1d import (
    Diffusion1D,
    Grid,
    uniform_grid,
    grid_from_edges,
    Dirichlet,
    Neumann,
    Robin,
    StateDependent,
)
from .diffusion2d import (
    Diffusion2D,
    Grid2D,
    uniform_grid_2d,
    MaskedSurface,
)

__all__ = [
    "Diffusion1D",
    "Grid",
    "uniform_grid",
    "grid_from_edges",
    "Dirichlet",
    "Neumann",
    "Robin",
    "StateDependent",
    "Diffusion2D",
    "Grid2D",
    "uniform_grid_2d",
    "MaskedSurface",
]
