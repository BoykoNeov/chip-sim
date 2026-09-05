"""The autonomous fast path — a wall-clock optimization that must change NO number.

When the operator is time- and field-independent (a numeric ``D``, numeric BC parameters, a numeric
or absent source) :class:`Diffusion1D` assembles the semidiscrete operator once and factorizes the
implicit matrix once per ``dt`` (LAPACK ``gttrf``), then back-solves per step (``gttrs``) instead of
re-eliminating with ``solve_banded`` every step. Both are the same partial-pivoting tridiagonal
elimination, so the results are **bit-identical** — asserted here with ``array_equal``, not
``allclose``, for every scheme and every BC family, against the general (uncached) path reached by
handing the SAME constants in as callables of time.

The seam this protects: every consumer march (``chip.diffusion_dopant._diffuse`` — 600 steps per
predep/drive-in, thousands per fab-game wafer) rides the fast path, while every ``D(t)`` schedule
(the RTA budget, OED) and every ramped BC rides the general one; a learner comparing the two must
never see a numerical difference that is the cache's, not the physics'.
"""
import numpy as np
import pytest

from engines.diffusion import Diffusion1D, Dirichlet, Neumann, Robin, StateDependent, uniform_grid

N = 300
L = 2.0e-4
D = 1.0e-13
BCS = {
    "dirichlet-neumann": (Dirichlet(1.0e20), Neumann(0.0)),
    "neumann-neumann": (Neumann(0.0), Neumann(0.0)),
    "robin-dirichlet": (Robin(1.0e-9, 5.0e19), Dirichlet(0.0)),
    "neumann-flux": (Neumann(2.0e6), Neumann(0.0)),
}
DT = {"backward_euler": 3.0, "crank_nicolson": 3.0, "forward_euler": 1.0e-3}   # FE under its CFL


def _march(solver, u0, dt, n_steps):
    u, t = np.array(u0, dtype=float), 0.0
    fluxes = []
    for _ in range(n_steps):
        u = solver.step(u, dt, t0=t)
        t += dt
        fluxes.append(solver.flux(u, "left", t=t))
    return u, np.array(fluxes)


def _seed():
    x = uniform_grid(L, N).centers
    return 1.0e19 * np.exp(-((x - 0.3 * L) / (0.1 * L)) ** 2) + 1.0e15


@pytest.mark.parametrize("bc_name", sorted(BCS))
@pytest.mark.parametrize("method", sorted(DT))
def test_fast_path_is_bit_identical_to_the_general_path(method, bc_name):
    grid = uniform_grid(L, N)
    bcl, bcr = BCS[bc_name]
    fast = Diffusion1D(grid, D, bcl, bcr, method=method)
    slow = Diffusion1D(grid, lambda t: D, bcl, bcr, method=method)   # same D, as D(t) → uncached
    assert fast._autonomous and not slow._autonomous
    u_fast, j_fast = _march(fast, _seed(), DT[method], 120)
    u_slow, j_slow = _march(slow, _seed(), DT[method], 120)
    assert np.array_equal(u_fast, u_slow)
    assert np.array_equal(j_fast, j_slow)


def test_a_changed_dt_refactorizes_rather_than_reusing_the_stale_factor():
    grid = uniform_grid(L, N)
    fast = Diffusion1D(grid, D, Dirichlet(1.0e20), Neumann(0.0))
    slow = Diffusion1D(grid, lambda t: D, Dirichlet(1.0e20), Neumann(0.0))
    u_f = u_s = _seed()
    for dt in (1.0, 5.0, 1.0, 0.25):        # revisits a dt → must be re-keyed, not confused
        u_f = fast.step(u_f, dt)
        u_s = slow.step(u_s, dt)
        assert np.array_equal(u_f, u_s)


def test_source_and_array_D_stay_on_the_fast_path_and_match():
    grid = uniform_grid(L, N)
    D_x = D * (1.0 + 0.5 * np.sin(np.linspace(0.0, 3.0, N)))
    S = 1.0e14 * np.ones(N)
    fast = Diffusion1D(grid, D_x, Neumann(0.0), Neumann(0.0), source=S)
    slow = Diffusion1D(grid, lambda t: D_x, Neumann(0.0), Neumann(0.0), source=lambda t: S)
    assert fast._autonomous and not slow._autonomous
    u_f, _ = _march(fast, _seed(), 2.0, 60)
    u_s, _ = _march(slow, _seed(), 2.0, 60)
    assert np.array_equal(u_f, u_s)


@pytest.mark.parametrize("kind", ["D(t)", "StateDependent", "ramped-Dirichlet", "S(t)"])
def test_anything_time_or_field_dependent_is_not_autonomous(kind):
    grid = uniform_grid(L, N)
    kw = {}
    Dspec, bcl = D, Dirichlet(1.0e20)
    if kind == "D(t)":
        Dspec = lambda t: D  # noqa: E731
    elif kind == "StateDependent":
        Dspec = StateDependent(lambda u: D * np.ones_like(u))
    elif kind == "ramped-Dirichlet":
        bcl = Dirichlet(lambda t: 1.0e20 * min(1.0, t / 10.0))
    else:
        kw["source"] = lambda t: 0.0
    assert not Diffusion1D(grid, Dspec, bcl, Neumann(0.0), **kw)._autonomous


def test_cached_operator_is_read_only():
    grid = uniform_grid(L, N)
    solver = Diffusion1D(grid, D, Dirichlet(1.0e20), Neumann(0.0))
    sub, diag, sup, b = solver._operator(0.0)
    for arr in (sub, diag, sup, b, solver._D_cells(0.0)):
        with pytest.raises(ValueError):
            arr[0] = 123.0
    assert solver._operator(0.0) is solver._operator(1.0e9)     # served from the cache, any t
