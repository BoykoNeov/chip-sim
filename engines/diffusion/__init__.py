"""1-D conservative parabolic (diffusion / heat) solver — the spine of the trio.

Public API (established at Steel Phase 1a; unfrozen 2026-06-10, now open + test-gated — see CONTRACT.md):

    from engines.diffusion import (
        Diffusion1D, Grid, uniform_grid, grid_from_edges,
        Dirichlet, Neumann, Robin,
    )
"""
from .diffusion1d import (
    Diffusion1D,
    Grid,
    uniform_grid,
    grid_from_edges,
    Dirichlet,
    Neumann,
    Robin,
)

__all__ = [
    "Diffusion1D",
    "Grid",
    "uniform_grid",
    "grid_from_edges",
    "Dirichlet",
    "Neumann",
    "Robin",
]
