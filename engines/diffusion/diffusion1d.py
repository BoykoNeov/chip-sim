"""1-D conservative parabolic PDE solver (diffusion / heat) — the program spine.

Solves the conservative 1-D parabolic equation

    ∂u/∂t = ∂/∂x( D(x, t) ∂u/∂x ) + S(x, t)        on   x ∈ [0, L],

where ``u`` is a generic conserved intensive scalar. Two usage patterns ship
with the Steel project (CONTRACT.md); the engine itself is material-agnostic:

  * **mass mode** — ``u = %C``, ``D = D(T)`` supplied by the consumer (carbon in
    austenite, Arrhenius ``D₀·exp(−Q/RT)``). Conserved quantity: ``∫C dx``.
  * **heat mode** — ``ρc_p ∂T/∂t = ∂/∂x(k ∂T/∂x)``: pass ``D = α = k/(ρc_p)`` and
    a Robin boundary for the quench. Conserved quantity: enthalpy ``∫ρc_p T dx``.

The two differ only by relabelling ``(u, D, BC params)`` — that symmetry is *why*
one engine serves both.

Discretization
--------------
* **Cell-centered finite volume.** The flux leaving a cell across a face is
  exactly the flux entering its neighbour across that same face, so interior
  fluxes telescope under summation and ``Σ uᵢ Δxᵢ`` changes *only* through the
  boundary fluxes. Conservation is therefore structural and exact (to machine
  precision) under no-flux boundaries — on uniform *and* non-uniform grids.
* **θ-method time stepping**, one tridiagonal solve per implicit step
  (``scipy.linalg.solve_banded``):
    - ``backward_euler`` (θ=1, default) — unconditionally stable *and monotone*
      (discrete maximum principle: no new extrema, no oscillation, for any dt>0).
    - ``crank_nicolson`` (θ=½) — 2nd-order in time, unconditionally stable but
      *not monotone* (can produce decaying oscillations at large dt).
    - ``forward_euler`` (θ=0) — explicit (no linear solve; ``u^{n+1} = u^n +
      dt·(A·u^n + b)``), 1st-order in time, but only **conditionally** well-behaved:
      **monotone** (discrete maximum principle) iff ``dt ≤ 1/max|diag|`` — the CFL
      limit read off the operator diagonal (= ``Δx²/2D`` on a uniform, constant-D,
      no-flux grid; *tighter* at Dirichlet faces and small cells) — and merely
      **bounded** a little past that (a stable-but-non-monotone window up to
      ``≈2/|λ_min| ≤ 2/max|diag|``, the two limits coinciding on a uniform grid)
      before it runs away. The explicit counterpoint the implicit methods'
      unconditional stability is defined against — not the default for production runs.

Nonlinear (state-dependent) diffusivity
----------------------------------------
``D`` may also be a :class:`StateDependent` wrapper around a callable ``func(u)`` — a diffusivity
that depends on the *unknown field itself* (e.g. the concentration-dependent dopant diffusivity
``D(N)``). The engine then solves each implicit step **nonlinearly** by **Picard** iteration:
assemble the operator with ``D`` frozen at the current iterate, do the one tridiagonal solve,
re-evaluate ``D`` at the new field, repeat to a fixed point — which *is* the fully-implicit
nonlinear backward-Euler solve. Every inner solve is an ordinary linear backward-Euler step with
``D ≥ 0``, so the nonlinear scheme **inherits the per-iterate invariants** (the discrete maximum
principle and structural finite-volume conservation) — Picard, deliberately, not Newton. A constant
``func`` converges in the first iterate and reproduces the scalar-``D`` run bit-for-bit. The linear
``D`` forms (scalar / array / ``D(t)``) are untouched: only a :class:`StateDependent` ``D`` enters
the Picard loop.

The data boundary (ADR 0001)
----------------------------
The ``state`` is a plain 1-D ``ndarray`` of cell-centered ``u`` values. That
array is the data contract: :meth:`Diffusion1D.step` / :meth:`solve`
consume and return exactly it, and :meth:`total` / :meth:`flux` consume it. No
live objects cross that boundary. The grid, ``D``, and boundary conditions are
*construction-time configuration*: a compiled reimplementation parameterizes
them natively (e.g. ``D₀, Q``; a BC enum + params) — the Python callable/dataclass
forms here are assembly conveniences that reduce to numbers during matrix
assembly and never enter the state representation.

Sign convention
---------------
The flux is the physical flux density ``J = −D ∂u/∂x`` (Fick's first law),
positive in the **+x** direction. So at the *left* boundary ``J>0`` is inflow and
at the *right* boundary ``J>0`` is outflow. :meth:`flux` returns ``J`` in that
convention. Robin BCs are applied with the **outward normal** at each end, so a
single ``h>0`` cools toward ``u_ext`` at *both* ends (the expected quench).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union

import numpy as np
from scipy.linalg import solve_banded

# ``D`` may be a scalar, a length-N array (cell-centered D(x)), or a callable of
# time returning either (covers D(t), and D(T) when the consumer closes over a
# temperature schedule). A BC parameter may likewise be a scalar or callable(t).
ArrayLike = Union[float, np.ndarray]
DSpec = Union[float, np.ndarray, Callable[[float], ArrayLike]]
BCParam = Union[float, Callable[[float], float]]

_METHODS = {"forward_euler": 0.0, "backward_euler": 1.0, "crank_nicolson": 0.5}


# --------------------------------------------------------------------------- #
# Grid (plain numeric data — not a stateful object)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Grid:
    """Cell-centered 1-D finite-volume grid.

    ``edges`` are the N+1 cell-face positions; ``centers`` and ``widths`` (Δx)
    are the N cell centers and widths. Non-uniform grids are fully supported.
    """

    edges: np.ndarray
    centers: np.ndarray
    widths: np.ndarray

    @property
    def n(self) -> int:
        return int(self.centers.size)

    @property
    def length(self) -> float:
        return float(self.edges[-1] - self.edges[0])


def uniform_grid(length: float, n: int) -> Grid:
    """A uniform grid of ``n`` cells on ``[0, length]``."""
    if n < 2:
        raise ValueError("need at least 2 cells")
    edges = np.linspace(0.0, float(length), n + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    return Grid(edges=edges, centers=centers, widths=widths)


def grid_from_edges(edges: ArrayLike) -> Grid:
    """A (possibly non-uniform) grid from explicit, increasing cell-face positions."""
    edges = np.asarray(edges, dtype=float)
    if edges.ndim != 1 or edges.size < 3:
        raise ValueError("edges must be a 1-D array of at least 3 face positions")
    if np.any(np.diff(edges) <= 0):
        raise ValueError("edges must be strictly increasing")
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    return Grid(edges=edges, centers=centers, widths=widths)


# --------------------------------------------------------------------------- #
# Boundary conditions (construction-time configuration)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Dirichlet:
    """Fixed boundary value: ``u = value`` at the boundary face.

    ``value`` may be a scalar or a callable ``value(t)`` (e.g. a ramping surface
    concentration). Implemented via a half-cell ghost transmissibility — locally
    first-order at the face but globally second-order (the erfc test confirms it).
    """

    value: BCParam


@dataclass(frozen=True)
class Neumann:
    """Fixed flux: physical flux ``J = −D ∂u/∂x = flux`` in the +x direction.

    ``flux = 0`` (the default) is the insulated / symmetry / no-flux boundary —
    the one under which mass is conserved exactly.
    """

    flux: BCParam = 0.0


@dataclass(frozen=True)
class Robin:
    """Convective (Newton-cooling) boundary, applied with the OUTWARD normal:

        −D ∂u/∂n = h (u − u_ext).

    A single ``h > 0`` therefore cools toward ``u_ext`` at *both* ends — the
    physically expected quench behaviour. Discretized with a series-resistance
    effective coefficient ``U_eff = 1 / (Δx/2D + 1/h)`` (half-cell conduction in
    series with the convective film).
    """

    h: BCParam
    u_ext: BCParam


def _eval(param: BCParam, t: float) -> float:
    """Evaluate a possibly time-dependent scalar BC parameter at time ``t``."""
    return float(param(t)) if callable(param) else float(param)


# --------------------------------------------------------------------------- #
# Nonlinear diffusivity (state-dependent D = func(u))
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StateDependent:
    """A nonlinear, **state-dependent** diffusivity ``D = func(u)`` — the engine's native
    nonlinear path.

    Wrapping a callable in ``StateDependent`` (rather than passing a bare callable, which the
    engine reads as the time-dependent ``D(t)``) declares that ``D`` depends on the *unknown
    field* ``u`` itself, so each implicit step is solved **nonlinearly** by Picard iteration
    (see :meth:`Diffusion1D._step_nonlinear` and the module docstring). ``func`` takes the
    length-``N`` cell-centered state ``u`` and returns ``D`` as a scalar or a length-``N``
    cell-centered array.

    A *constant* ``func`` converges in the first iterate and reproduces the scalar-``D`` run
    **bit-for-bit** — the hook *is* the engine. Spatial / temporal dependence, when needed, is
    carried by the consumer closing the callable over its grid / schedule; the wrapper itself is
    deliberately ``func(u)`` only (Picard, not Newton — no Jacobian, no ``D(u, t)`` generality).
    """

    func: Callable[[np.ndarray], ArrayLike]


# --------------------------------------------------------------------------- #
# Solver
# --------------------------------------------------------------------------- #
class Diffusion1D:
    """Conservative 1-D parabolic solver; see the module docstring and CONTRACT.md.

    Parameters
    ----------
    grid : Grid
        The finite-volume grid (use :func:`uniform_grid` / :func:`grid_from_edges`).
    D : float | ndarray | callable | StateDependent
        Diffusivity. Scalar, length-N cell-centered array ``D(x)``, a callable
        ``D(t)`` returning either, or a :class:`StateDependent` wrapper ``D = func(u)``
        for the **nonlinear** (concentration-dependent) path (Picard-solved per step).
        Interior face diffusivity is the harmonic mean of the two adjacent cell values
        (correct flux continuity for layered media).
    bc_left, bc_right : Dirichlet | Neumann | Robin
        Boundary condition at each end, independently.
    source : float | ndarray | callable, optional
        Source term ``S(x, t)`` (units of ``u`` per unit time). Scalar, length-N
        array, or callable ``S(t)``. ``None`` means no source.
    method : {"backward_euler", "crank_nicolson", "forward_euler"}
        Time-integration scheme; backward Euler (default) is the unconditionally
        stable *and monotone* one the stability invariant guarantees. ``forward_euler``
        is the explicit (θ=0) scheme — conditionally stable only under the CFL limit
        ``dt ≤ 1/max|diag|`` — kept as the explicit counterpoint, not for production.
    picard_tol : float, optional
        Convergence tolerance for the nonlinear (``StateDependent`` ``D``) Picard
        iteration: a step is converged when the max change between iterates is
        ``≤ picard_tol · max|u|`` (scaled by the field magnitude, so it is robust for
        many-decade profiles). Ignored for linear ``D``.
    picard_max_iter : int, optional
        Safety cap on Picard iterations per step (smooth ``D`` converges in ~2–5).
        On reaching it the best estimate is returned without raising. Ignored for linear ``D``.
    """

    def __init__(
        self,
        grid: Grid,
        D: Union[DSpec, "StateDependent"],
        bc_left: Union[Dirichlet, Neumann, Robin],
        bc_right: Union[Dirichlet, Neumann, Robin],
        source: Union[DSpec, None] = None,
        method: str = "backward_euler",
        picard_tol: float = 1e-10,
        picard_max_iter: int = 100,
    ) -> None:
        if method not in _METHODS:
            raise ValueError(f"method must be one of {sorted(_METHODS)}, got {method!r}")
        for bc in (bc_left, bc_right):
            if not isinstance(bc, (Dirichlet, Neumann, Robin)):
                raise TypeError(f"boundary condition must be Dirichlet/Neumann/Robin, got {bc!r}")
        self.grid = grid
        self._D = D
        self.bc_left = bc_left
        self.bc_right = bc_right
        self._source = source
        self.method = method
        self.theta = _METHODS[method]
        self.picard_tol = float(picard_tol)
        self.picard_max_iter = int(picard_max_iter)
        # distance between adjacent cell centers (length N-1) — the face widths
        # over which the interior gradient is taken.
        self._dx_face = np.diff(grid.centers)

    # -- coefficient assembly ------------------------------------------------ #
    def _D_cells(self, t: float, u: Union[np.ndarray, None] = None) -> np.ndarray:
        """Cell-centered diffusivity as a length-N array.

        Evaluated at time ``t`` for the linear forms (scalar / array / callable ``D(t)``); for a
        :class:`StateDependent` ``D`` it is evaluated at the supplied field ``u`` (``func(u)``).
        """
        if isinstance(self._D, StateDependent):
            if u is None:
                raise ValueError("a StateDependent D requires the current field u to evaluate")
            D = self._D.func(np.asarray(u, dtype=float))
        elif callable(self._D):
            D = self._D(t)
        else:
            D = self._D
        D = np.asarray(D, dtype=float)
        if D.ndim == 0:
            D = np.full(self.grid.n, float(D))
        if D.shape != (self.grid.n,):
            raise ValueError(f"D must be scalar or length {self.grid.n}, got shape {D.shape}")
        return D

    def _source_vec(self, t: float) -> Union[np.ndarray, None]:
        if self._source is None:
            return None
        S = self._source(t) if callable(self._source) else self._source
        S = np.asarray(S, dtype=float)
        if S.ndim == 0:
            S = np.full(self.grid.n, float(S))
        if S.shape != (self.grid.n,):
            raise ValueError(f"source must be scalar or length {self.grid.n}, got shape {S.shape}")
        return S

    def _operator(self, t: float, u: Union[np.ndarray, None] = None):
        """Assemble the semidiscrete system  du/dt = A·u + b  at time ``t``.

        Returns the three diagonals of the tridiagonal matrix ``A`` (``sub[i] =
        A[i, i-1]``, ``diag[i] = A[i, i]``, ``sup[i] = A[i, i+1]``) and the
        boundary/source vector ``b``. ``A`` carries the diffusion operator plus
        the diagonal contributions of Dirichlet/Robin boundaries; ``b`` carries
        their inhomogeneous parts, the Neumann flux, and the source. For a
        :class:`StateDependent` ``D`` the diffusivity is frozen at the iterate ``u``.
        """
        g = self.grid
        n = g.n
        dx = g.widths
        Dc = self._D_cells(t, u)

        # Interior face transmissibilities  T_{i+1/2} = D_face / dist(centers).
        # Harmonic-mean face diffusivity gives exact flux continuity across a
        # discontinuity in D and reduces to D for constant D.
        Dface = 2.0 * Dc[:-1] * Dc[1:] / (Dc[:-1] + Dc[1:])
        T = Dface / self._dx_face  # length n-1, T[k] couples cells k and k+1

        sub = np.zeros(n)
        diag = np.zeros(n)
        sup = np.zeros(n)
        b = np.zeros(n)

        # Face k (k = 0..n-2) connects cells k and k+1, contributing
        #   du_k/dt   += T[k] (u_{k+1} - u_k) / dx_k
        #   du_{k+1}/dt += T[k] (u_k - u_{k+1}) / dx_{k+1}
        sup[:-1] += T / dx[:-1]
        diag[:-1] += -T / dx[:-1]
        sub[1:] += T / dx[1:]
        diag[1:] += -T / dx[1:]

        self._apply_bc(self.bc_left, "left", t, Dc, diag, b)
        self._apply_bc(self.bc_right, "right", t, Dc, diag, b)

        S = self._source_vec(t)
        if S is not None:
            b += S
        return sub, diag, sup, b

    def _apply_bc(self, bc, end: str, t: float, Dc: np.ndarray, diag: np.ndarray, b: np.ndarray) -> None:
        g = self.grid
        if end == "left":
            i, dxi, Db = 0, g.widths[0], Dc[0]
        else:
            i, dxi, Db = g.n - 1, g.widths[-1], Dc[-1]

        if isinstance(bc, Neumann):
            # Physical flux J in +x prescribed at the face. At the left face this
            # adds +J/Δx to du_0/dt (inflow); at the right face −J/Δx (outflow).
            q = _eval(bc.flux, t)
            b[i] += (q if end == "left" else -q) / dxi
        elif isinstance(bc, Dirichlet):
            ub = _eval(bc.value, t)
            T_ghost = Db / (0.5 * dxi)  # half-cell transmissibility to the fixed face
            diag[i] += -T_ghost / dxi
            b[i] += T_ghost * ub / dxi
        else:  # Robin
            h = _eval(bc.h, t)
            ue = _eval(bc.u_ext, t)
            a = Db / (0.5 * dxi)  # half-cell conduction (= 2D/Δx)
            u_eff = (a * h / (a + h)) if (a + h) != 0.0 else 0.0
            diag[i] += -u_eff / dxi
            b[i] += u_eff * ue / dxi

    # -- time stepping ------------------------------------------------------- #
    def step(self, state: np.ndarray, dt: float, t0: float = 0.0) -> np.ndarray:
        """Advance ``state`` by one step ``dt`` (from time ``t0``); returns the new state.

        Does not mutate ``state``. With time-dependent ``D``/BC/source the implicit
        operator is evaluated at ``t0 + dt`` (and, for Crank–Nicolson, the explicit
        part at ``t0``).
        """
        if dt <= 0.0:
            raise ValueError("dt must be positive")
        u0 = np.asarray(state, dtype=float)
        if u0.shape != (self.grid.n,):
            raise ValueError(f"state must have length {self.grid.n}, got shape {u0.shape}")
        if isinstance(self._D, StateDependent):
            return self._step_nonlinear(u0, dt, t0)
        theta = self.theta
        t1 = t0 + dt

        if theta == 0.0:  # forward Euler (explicit): operator at t0, no linear solve
            # u^{n+1} = u^n + dt·(A·u^n + b), with A, b assembled at the OLD time t0.
            # Monotone (discrete max principle) iff dt ≤ 1/max|diag| (= Δx²/2D on a
            # uniform constant-D no-flux grid); stable a little past that, then blows
            # up — the conditional counterpoint to the implicit methods. See test_explicit.
            sub0, diag0, sup0, b0 = self._operator(t0)
            rate = diag0 * u0 + b0
            rate[:-1] += sup0[:-1] * u0[1:]
            rate[1:] += sub0[1:] * u0[:-1]
            return u0 + dt * rate

        sub1, diag1, sup1, b1 = self._operator(t1)

        if theta == 1.0:  # backward Euler
            rhs = u0 + dt * b1
        else:  # Crank–Nicolson: explicit half at t0
            sub0, diag0, sup0, b0 = self._operator(t0)
            rhs = u0.copy()
            rhs[:-1] += (1.0 - theta) * dt * sup0[:-1] * u0[1:]
            rhs[1:] += (1.0 - theta) * dt * sub0[1:] * u0[:-1]
            rhs += (1.0 - theta) * dt * diag0 * u0
            rhs += dt * (theta * b1 + (1.0 - theta) * b0)

        # Implicit operator  (I − θ dt A)  in scipy banded storage (l=u=1):
        #   ab[0, 1:]  = super-diagonal,  ab[1, :] = diagonal,  ab[2, :-1] = sub.
        n = self.grid.n
        ab = np.zeros((3, n))
        ab[0, 1:] = -dt * theta * sup1[:-1]
        ab[1, :] = 1.0 - dt * theta * diag1
        ab[2, :-1] = -dt * theta * sub1[1:]
        return solve_banded((1, 1), ab, rhs)

    def _step_nonlinear(self, u0: np.ndarray, dt: float, t0: float) -> np.ndarray:
        """One implicit step with a :class:`StateDependent` ``D``, by Picard iteration.

        Each iterate freezes ``D`` at the current field estimate and does **one** ordinary linear
        tridiagonal solve (so it inherits the engine's monotone, conservative single-step machinery);
        re-evaluating ``D`` at the result and repeating drives the within-step coefficient to its
        fixed point — the fully-implicit nonlinear backward-Euler (or θ-method) solve. The lagged
        predictor is ``u0``; convergence is the max iterate-change scaled by ``max|u|`` (robust for
        many-decade profiles). A constant ``D`` converges in the first iterate and returns the
        scalar-``D`` result bit-for-bit. Pure Picard — no relaxation/damping — preserves that seam.
        """
        theta = self.theta
        n = self.grid.n
        t1 = t0 + dt

        # Crank–Nicolson explicit half uses D at the OLD (known) state u0 — assembled once,
        # outside the Picard loop. Backward Euler (theta=1) has no explicit half.
        if theta != 1.0:
            sub0, diag0, sup0, b0 = self._operator(t0, u0)
            rhs_expl = u0.copy()
            rhs_expl[:-1] += (1.0 - theta) * dt * sup0[:-1] * u0[1:]
            rhs_expl[1:] += (1.0 - theta) * dt * sub0[1:] * u0[:-1]
            rhs_expl += (1.0 - theta) * dt * diag0 * u0

        u_iter = u0
        u_new = u0
        for _ in range(self.picard_max_iter):
            sub1, diag1, sup1, b1 = self._operator(t1, u_iter)  # D frozen at the current iterate
            if theta == 1.0:  # backward Euler
                rhs = u0 + dt * b1
            else:  # Crank–Nicolson: explicit half (D at u0) + implicit half (D at the iterate)
                rhs = rhs_expl + dt * (theta * b1 + (1.0 - theta) * b0)
            ab = np.zeros((3, n))
            ab[0, 1:] = -dt * theta * sup1[:-1]
            ab[1, :] = 1.0 - dt * theta * diag1
            ab[2, :-1] = -dt * theta * sub1[1:]
            u_new = solve_banded((1, 1), ab, rhs)
            scale = max(float(np.max(np.abs(u_new))), 1.0)
            if np.max(np.abs(u_new - u_iter)) <= self.picard_tol * scale:
                break
            u_iter = u_new
        return u_new

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
        """The conserved integral ``∫ u dx = Σ uᵢ Δxᵢ``."""
        return float(np.sum(np.asarray(state, dtype=float) * self.grid.widths))

    def flux(self, state: np.ndarray, end: str, t: float = 0.0) -> float:
        """Physical flux ``J = −D ∂u/∂x`` at a boundary, positive in +x.

        ``end`` is ``"left"`` or ``"right"``. The discrete identity
        ``total(stepped) − total(state) = dt·(flux(left) − flux(right))`` holds
        exactly for backward Euler — i.e. this diagnostic is consistent with the
        conservation the operator enforces.
        """
        u = np.asarray(state, dtype=float)
        Dc = self._D_cells(t, u)
        if end == "left":
            bc, dxi, Db, u_cell = self.bc_left, self.grid.widths[0], Dc[0], u[0]
        elif end == "right":
            bc, dxi, Db, u_cell = self.bc_right, self.grid.widths[-1], Dc[-1], u[-1]
        else:
            raise ValueError("end must be 'left' or 'right'")

        if isinstance(bc, Neumann):
            return _eval(bc.flux, t)
        if isinstance(bc, Dirichlet):
            ub = _eval(bc.value, t)
            # J = −D ∂u/∂x with the half-cell gradient; signs differ by end.
            grad = (u_cell - ub) if end == "left" else (ub - u_cell)
            return float(-Db * grad / (0.5 * dxi))
        # Robin: outward flux U_eff·(u_cell − u_ext); +x flux flips sign at left.
        h = _eval(bc.h, t)
        ue = _eval(bc.u_ext, t)
        a = Db / (0.5 * dxi)
        u_eff = (a * h / (a + h)) if (a + h) != 0.0 else 0.0
        outflow = u_eff * (u_cell - ue)
        return float(-outflow if end == "left" else outflow)
