"""2-D conservative parabolic PDE solver (diffusion / heat) — the deferred 2-D regime.

Solves the conservative 2-D parabolic equation

    ∂u/∂t = ∇·( D(x, y) ∇u ) + S(x, y)        on   (x, y) ∈ [0, Lx] × [0, Ly],

the tensor-product extension of the 1-D spine (:mod:`engines.diffusion.diffusion1d`).
This is the engine's **last deferred regime** — ``CONTRACT.md`` named "2-D/3-D" as the
final ``Not built`` line, with the array-``state`` boundary as the seam where it slots
in. The named consumer that finally pulls it in is **lateral dopant diffusion under a
mask edge** (chip ``diffusion_2d``): a constant-source window on the surface diffuses
both *down* and *sideways under the mask*, and the lateral junction reaches ≈ 0.8 of the
vertical depth — a genuinely 2-D, *non-separable* result (it needs the piecewise surface
BC below; a fully separable problem reduces to the 1-D engine and would not need this).

Discretization
--------------
* **Cell-centered finite volume on a tensor-product grid** (:class:`Grid2D` = an x-grid
  ⊗ a y-grid). The flux leaving a cell across a face equals the flux entering its
  neighbour, so interior fluxes telescope and ``Σ uᵢⱼ Δxᵢ Δyⱼ`` changes *only* through
  boundary fluxes → conservation is structural and exact under no-flux, on non-uniform
  grids too — exactly as in 1-D, now in both directions.
* **Backward-Euler only** (θ=1). The assembled operator ``A`` (``du/dt = A·u + b``) is a
  5-point stencil; ``(I − dt·A)`` is an **M-matrix** (positive diagonal, non-positive
  off-diagonals, diagonally dominant), so backward Euler is **unconditionally stable and
  monotone** (discrete maximum principle) and conservation telescopes — the 1-D engine's
  headline guarantees carry over verbatim. Solved with a sparse direct factorization
  (:func:`scipy.sparse.linalg.splu`), cached per ``dt`` (``A`` is time-independent here,
  so the factorization is reused across a fixed-``dt`` march for free). Crank–Nicolson /
  forward-Euler / nonlinear ``D(u)`` / anisotropic-tensor ``D`` are **deliberately not
  built** here — none has a consumer (the mask-edge demo is constant isotropic ``D``);
  they are the named next amendments if one arrives.
* Interior **face diffusivity = harmonic mean** of the two adjacent cell values (exact
  flux continuity across a ``D`` discontinuity; reduces to ``D`` for constant ``D``) —
  the same rule the 1-D engine uses, applied per face in each direction.

State layout (the ADR-0001 data boundary)
-----------------------------------------
``state`` is a plain 2-D ``ndarray`` of shape ``(nx, ny)``: ``state[i, j]`` is the
cell-centered ``u`` at lateral index ``i`` (``x``) and depth index ``j`` (``y``). It is
flattened C-order (``k = i·ny + j``) for the linear solve and reshaped back — the array,
and only it, crosses the per-step boundary, mirroring the 1-D contract (a compiled core
could reparameterize ``Grid2D``/``D``/BCs natively and expose the same array).

Boundary conditions
-------------------
The four edges are ``bc_xlo`` / ``bc_xhi`` (the ``x=0`` / ``x=Lx`` faces) and ``bc_ylo``
/ ``bc_yhi`` (``y=0`` / ``y=Ly``). Each may be a *uniform* :class:`Dirichlet` /
:class:`Neumann` / :class:`Robin` (reused from the 1-D module — applied identically along
the whole edge), **or** a :class:`MaskedSurface` (the genuinely-2-D piece): Dirichlet
``value`` on the cells where a boolean ``open_mask`` is ``True`` (the lithographic
*window*) and no-flux elsewhere (under the *mask*). That mixed, per-cell edge BC is what
makes the mask-edge problem non-separable — and it is the minimum the named consumer
needs, nothing more.

Sign / units conventions are inherited unchanged from the 1-D engine: flux ``J = −D ∂u/∂n``,
SI throughout, ``u`` a generic conserved intensive scalar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu

from .diffusion1d import Grid, Dirichlet, Neumann, Robin, _eval

# A 2-D edge BC is one of the 1-D scalar BCs (applied uniformly along the edge) or the
# piecewise MaskedSurface. D / source are scalar or a 2-D (nx, ny) array (time-independent).
EdgeBC = Union[Dirichlet, Neumann, Robin, "MaskedSurface"]
Field2D = Union[float, np.ndarray]


# --------------------------------------------------------------------------- #
# Grid (a tensor product of two 1-D finite-volume grids)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Grid2D:
    """Cell-centered 2-D finite-volume grid = an x-grid ⊗ a y-grid.

    Composed of two 1-D :class:`Grid` objects, so non-uniform grids (and the
    ``grid_from_edges`` constructor) are inherited for free in each direction.
    """

    x: Grid
    y: Grid

    @property
    def nx(self) -> int:
        return self.x.n

    @property
    def ny(self) -> int:
        return self.y.n

    @property
    def n(self) -> int:
        return self.x.n * self.y.n

    @property
    def shape(self) -> tuple:
        return (self.x.n, self.y.n)

    @property
    def cell_areas(self) -> np.ndarray:
        """The (nx, ny) array of cell areas ``Δxᵢ·Δyⱼ`` (the FV measure)."""
        return np.outer(self.x.widths, self.y.widths)


def uniform_grid_2d(length_x: float, length_y: float, nx: int, ny: int) -> Grid2D:
    """A uniform 2-D grid of ``nx × ny`` cells on ``[0, Lx] × [0, Ly]``."""
    from .diffusion1d import uniform_grid

    return Grid2D(x=uniform_grid(length_x, nx), y=uniform_grid(length_y, ny))


# --------------------------------------------------------------------------- #
# The genuinely-2-D boundary condition: a masked (piecewise) surface
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MaskedSurface:
    """A piecewise edge BC: **Dirichlet ``value`` under the window, no-flux under the mask.**

    ``open_mask`` is a boolean array (length = the number of cells along the edge it is
    attached to) that is ``True`` where the lithographic *window* is open — there the face
    is held at ``value`` (a scalar or ``value(t)``, exactly the 1-D :class:`Dirichlet`
    semantics) — and ``False`` under the *mask*, where the face is insulated (Neumann 0).

    This mixed, per-cell edge condition is the one piece the 2-D solver adds beyond the 1-D
    BC set, and it is what makes the mask-edge problem *non-separable* (a uniform edge BC
    keeps the problem a product of two 1-D solves; the step in the BC along the edge is the
    source of the lateral-under-mask curvature). Deliberately Dirichlet-or-no-flux only —
    a masked Robin/Neumann-flux edge has no consumer here.
    """

    value: object
    open_mask: np.ndarray


# --------------------------------------------------------------------------- #
# Solver
# --------------------------------------------------------------------------- #
class Diffusion2D:
    """Conservative 2-D parabolic solver; see the module docstring and CONTRACT.md.

    Parameters
    ----------
    grid : Grid2D
        The tensor-product finite-volume grid.
    D : float | ndarray
        Diffusivity — a scalar or a ``(nx, ny)`` cell-centered array ``D(x, y)`` (isotropic;
        the same ``D`` governs both directions). Time-independent in this build. Interior
        face diffusivity is the harmonic mean of the two adjacent cells.
    bc_xlo, bc_xhi, bc_ylo, bc_yhi : Dirichlet | Neumann | Robin | MaskedSurface
        Boundary condition on the ``x=0`` / ``x=Lx`` / ``y=0`` / ``y=Ly`` edge. A scalar
        BC is applied uniformly along the edge; :class:`MaskedSurface` is per-cell.
    source : float | ndarray, optional
        Source ``S(x, y)`` (units of ``u`` per unit time): scalar or ``(nx, ny)`` array.
        ``None`` means no source. Time-independent in this build.
    method : {"backward_euler"}
        Only backward Euler (θ=1) is built — the unconditionally stable, monotone,
        conservative scheme (see the module docstring for why CN/explicit are deferred).
    """

    def __init__(
        self,
        grid: Grid2D,
        D: Field2D,
        bc_xlo: EdgeBC,
        bc_xhi: EdgeBC,
        bc_ylo: EdgeBC,
        bc_yhi: EdgeBC,
        source: Union[Field2D, None] = None,
        method: str = "backward_euler",
    ) -> None:
        if method != "backward_euler":
            raise ValueError(
                "Diffusion2D builds backward_euler only (CN/explicit are deferred); "
                f"got {method!r}"
            )
        self.bcs = {"xlo": bc_xlo, "xhi": bc_xhi, "ylo": bc_ylo, "yhi": bc_yhi}
        for name, bc in self.bcs.items():
            if not isinstance(bc, (Dirichlet, Neumann, Robin, MaskedSurface)):
                raise TypeError(
                    f"bc_{name} must be Dirichlet/Neumann/Robin/MaskedSurface, got {bc!r}"
                )
            if isinstance(bc, MaskedSurface):
                edge_len = grid.ny if name in ("xlo", "xhi") else grid.nx
                mask = np.asarray(bc.open_mask, dtype=bool)
                if mask.shape != (edge_len,):
                    raise ValueError(
                        f"bc_{name}.open_mask must have length {edge_len} (cells along the "
                        f"edge), got shape {mask.shape}"
                    )
        self.grid = grid
        self.method = method
        self._Dc = self._D_field(D)              # (nx, ny) cell diffusivity
        self._source = self._source_field(source)
        # The diffusion operator A (du/dt = A·u + b_diff_const) is time-independent here, so
        # assemble its sparse matrix + the BC diagonal contributions once; only the
        # inhomogeneous b (Dirichlet values, Neumann fluxes, source) is rebuilt per step.
        self._A = self._assemble_operator()
        self._lu_cache: dict = {}               # dt -> splu(I - dt·A)

    # -- field coercion ------------------------------------------------------ #
    def _D_field(self, D: Field2D) -> np.ndarray:
        D = np.asarray(D, dtype=float)
        if D.ndim == 0:
            return np.full(self.grid.shape, float(D))
        if D.shape != self.grid.shape:
            raise ValueError(f"D must be scalar or shape {self.grid.shape}, got {D.shape}")
        return D

    def _source_field(self, S: Union[Field2D, None]) -> Union[np.ndarray, None]:
        if S is None:
            return None
        S = np.asarray(S, dtype=float)
        if S.ndim == 0:
            return np.full(self.grid.shape, float(S))
        if S.shape != self.grid.shape:
            raise ValueError(f"source must be scalar or shape {self.grid.shape}, got {S.shape}")
        return S

    # -- coefficient assembly ------------------------------------------------ #
    def _assemble_operator(self) -> sp.csc_matrix:
        """Assemble the sparse 5-point FV operator ``A`` (``du/dt = A·u + b``).

        Carries the interior diffusion couplings plus the *diagonal* parts of
        Dirichlet/Robin/MaskedSurface boundary cells (their inhomogeneous parts live in
        ``b``, rebuilt per step). The flattened index is ``k = i·ny + j``.
        """
        g = self.grid
        nx, ny = g.nx, g.ny
        Dc = self._Dc
        dx, dy = g.x.widths, g.y.widths
        dxf, dyf = np.diff(g.x.centers), np.diff(g.y.centers)  # center-to-center distances

        rows, cols, data = [], [], []
        diag = np.zeros((nx, ny))

        def idx(i, j):
            return i * ny + j

        # --- x-direction faces (between (i,j) and (i+1,j)), i = 0..nx-2 ---
        if nx >= 2:
            Dl = Dc[:-1, :]                       # (nx-1, ny)
            Dr = Dc[1:, :]
            Dface = 2.0 * Dl * Dr / (Dl + Dr)     # harmonic mean per face
            T = Dface / dxf[:, None]              # (nx-1, ny) transmissibility
            ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny), indexing="ij")
            kl = (ii * ny + jj).ravel()
            kr = ((ii + 1) * ny + jj).ravel()
            cl = (T / dx[:-1, None]).ravel()      # coupling into the left cell's row
            cr = (T / dx[1:, None]).ravel()       # coupling into the right cell's row
            rows.extend([kl, kr]); cols.extend([kr, kl]); data.extend([cl, cr])
            np.subtract.at(diag.reshape(-1), kl, cl)
            np.subtract.at(diag.reshape(-1), kr, cr)

        # --- y-direction faces (between (i,j) and (i,j+1)), j = 0..ny-2 ---
        if ny >= 2:
            Dd = Dc[:, :-1]
            Du = Dc[:, 1:]
            Dface = 2.0 * Dd * Du / (Dd + Du)
            T = Dface / dyf[None, :]              # (nx, ny-1)
            ii, jj = np.meshgrid(np.arange(nx), np.arange(ny - 1), indexing="ij")
            kd = (ii * ny + jj).ravel()
            ku = (ii * ny + (jj + 1)).ravel()
            cd = (T / dy[None, :-1]).ravel()
            cu = (T / dy[None, 1:]).ravel()
            rows.extend([kd, ku]); cols.extend([ku, kd]); data.extend([cd, cu])
            np.subtract.at(diag.reshape(-1), kd, cd)
            np.subtract.at(diag.reshape(-1), ku, cu)

        # --- boundary diagonal contributions (Dirichlet / Robin / masked window) ---
        for name, bc in self.bcs.items():
            self._apply_bc_diag(name, bc, diag)

        rows.append(np.arange(nx * ny))
        cols.append(np.arange(nx * ny))
        data.append(diag.ravel())
        A = sp.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(nx * ny, nx * ny),
        ).tocsc()
        return A

    def _edge_cells(self, name: str):
        """The (flat indices, perpendicular cell widths, edge cell diffusivities) for an edge."""
        g = self.grid
        nx, ny = g.nx, g.ny
        if name == "xlo":
            i = np.zeros(ny, dtype=int); j = np.arange(ny); dperp = g.x.widths[0]
        elif name == "xhi":
            i = np.full(ny, nx - 1); j = np.arange(ny); dperp = g.x.widths[-1]
        elif name == "ylo":
            i = np.arange(nx); j = np.zeros(nx, dtype=int); dperp = g.y.widths[0]
        else:  # yhi
            i = np.arange(nx); j = np.full(nx, ny - 1); dperp = g.y.widths[-1]
        k = i * ny + j
        # All cells along one edge share the same perpendicular width (uniform per edge):
        # the xlo/xhi edges are one x-cell deep, the ylo/yhi edges one y-cell deep.
        dperp = np.full(k.size, float(dperp))
        Db = self._Dc[i, j]
        return k, dperp, Db, (i, j)

    def _apply_bc_diag(self, name: str, bc: EdgeBC, diag: np.ndarray) -> None:
        """Add an edge BC's *diagonal* (homogeneous) contribution to ``A``."""
        k, dperp, Db, _ = self._edge_cells(name)
        flat = diag.reshape(-1)
        if isinstance(bc, Neumann):
            return  # no diagonal contribution (flux is purely inhomogeneous → b)
        if isinstance(bc, Dirichlet):
            T_ghost = Db / (0.5 * dperp)
            np.subtract.at(flat, k, T_ghost / dperp)
        elif isinstance(bc, Robin):
            h = _eval(bc.h, 0.0)
            a = Db / (0.5 * dperp)
            u_eff = np.where((a + h) != 0.0, a * h / (a + h), 0.0)
            np.subtract.at(flat, k, u_eff / dperp)
        else:  # MaskedSurface: Dirichlet only on the open (window) cells
            open_cells = np.asarray(bc.open_mask, dtype=bool)
            T_ghost = Db / (0.5 * dperp)
            np.subtract.at(flat, k[open_cells], (T_ghost / dperp)[open_cells])

    def _b_vector(self, t: float) -> np.ndarray:
        """The inhomogeneous vector ``b`` (Dirichlet values, Neumann fluxes, masked window, source)."""
        b = np.zeros(self.grid.n)
        for name, bc in self.bcs.items():
            self._apply_bc_b(name, bc, b, t)
        if self._source is not None:
            b += self._source.ravel()
        return b

    def _apply_bc_b(self, name: str, bc: EdgeBC, b: np.ndarray, t: float) -> None:
        k, dperp, Db, _ = self._edge_cells(name)
        if isinstance(bc, Neumann):
            q = _eval(bc.flux, t)
            # +x/+y outward normal: an "lo" face inflow adds +q/Δ, an "hi" face −q/Δ.
            sign = 1.0 if name in ("xlo", "ylo") else -1.0
            np.add.at(b, k, sign * q / dperp)
        elif isinstance(bc, Dirichlet):
            ub = _eval(bc.value, t)
            T_ghost = Db / (0.5 * dperp)
            np.add.at(b, k, T_ghost * ub / dperp)
        elif isinstance(bc, Robin):
            h = _eval(bc.h, t); ue = _eval(bc.u_ext, t)
            a = Db / (0.5 * dperp)
            u_eff = np.where((a + h) != 0.0, a * h / (a + h), 0.0)
            np.add.at(b, k, u_eff * ue / dperp)
        else:  # MaskedSurface
            open_cells = np.asarray(bc.open_mask, dtype=bool)
            ub = _eval(bc.value, t)
            T_ghost = Db / (0.5 * dperp)
            np.add.at(b, k[open_cells], (T_ghost * ub / dperp)[open_cells])

    # -- time stepping ------------------------------------------------------- #
    def _factor(self, dt: float):
        lu = self._lu_cache.get(dt)
        if lu is None:
            n = self.grid.n
            M = (sp.identity(n, format="csc") - dt * self._A).tocsc()
            lu = splu(M)
            self._lu_cache[dt] = lu
        return lu

    def step(self, state: np.ndarray, dt: float, t0: float = 0.0) -> np.ndarray:
        """Advance ``state`` (shape ``(nx, ny)``) by one backward-Euler step ``dt``.

        Does not mutate ``state``. The implicit operator is evaluated at ``t0 + dt``;
        ``(I − dt·A)`` is M-matrix → the step is unconditionally stable and monotone.
        """
        if dt <= 0.0:
            raise ValueError("dt must be positive")
        u0 = np.asarray(state, dtype=float)
        if u0.shape != self.grid.shape:
            raise ValueError(f"state must have shape {self.grid.shape}, got {u0.shape}")
        b = self._b_vector(t0 + dt)
        rhs = u0.ravel() + dt * b
        u1 = self._factor(dt).solve(rhs)
        return u1.reshape(self.grid.shape)

    def solve(self, state: np.ndarray, t_end: float, dt: float, t0: float = 0.0) -> np.ndarray:
        """Advance from ``t0`` to ``t0 + t_end`` in steps of ``dt`` (last step trimmed)."""
        if t_end < 0.0:
            raise ValueError("t_end must be non-negative")
        u = np.asarray(state, dtype=float).copy()
        t = t0
        remaining = t_end
        while remaining > 1e-12 * max(1.0, abs(dt)):
            h = min(dt, remaining)
            u = self.step(u, h, t0=t)
            t += h
            remaining -= h
        return u

    # -- diagnostics --------------------------------------------------------- #
    def total(self, state: np.ndarray) -> float:
        """The conserved integral ``∫∫ u dA = Σ uᵢⱼ Δxᵢ Δyⱼ``."""
        return float(np.sum(np.asarray(state, dtype=float) * self.grid.cell_areas))
