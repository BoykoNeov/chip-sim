"""Explicit (forward Euler, θ=0) time stepping — the conditional-stability counterpoint.

Invariant 3 asserts *unconditional* stability for the two implicit methods. It is
defined against something: an explicit method that is stable only under a CFL
limit. ``forward_euler`` (θ=0) is that method — ``u^{n+1} = u^n + dt·(A·u^n + b)``,
no linear solve. It is 1st-order in time and conserves under no-flux (the
finite-volume telescoping is θ-independent), but it is **monotone** (discrete maximum
principle) *only* while ``dt ≤ 1/max|diag|`` — the sharp bound read off the operator
diagonal (``Δx²/2D`` on a uniform, constant-D, no-flux grid; *tighter* at Dirichlet
faces / small cells). It stays merely *bounded* a little past that (a
stable-but-non-monotone window, the two limits coinciding on a uniform grid) before it
runs away — so the tests bracket the max-principle at half the limit and full blow-up at 2×.

These tests pin: the stable-regime agreement with the analytic eigenmode, the
1st-order temporal slope, exact no-flux conservation, the closed-form CFL identity,
the blow-up-above / stable-below boundary read off the *operator diagonal*, and the
headline contrast — backward Euler stays bounded at a dt where forward Euler explodes.
"""
import numpy as np

from engines.diffusion import (
    Diffusion1D,
    uniform_grid,
    grid_from_edges,
    Dirichlet,
    Neumann,
)


def _dt_crit(solver) -> float:
    """The CFL limit from the assembled operator: dt ≤ 1/max|diag| (sharp von Neumann)."""
    _, diag, _, _ = solver._operator(0.0)
    return 1.0 / np.max(np.abs(diag))


def _alternating(n: int) -> np.ndarray:
    """The Nyquist (highest-frequency) mode — what an over-CFL explicit step amplifies."""
    return np.where(np.arange(n) % 2 == 0, 1.0, -1.0)


# --------------------------------------------------------------------------- #
# Analytic: forward Euler recovers the physics in the stable regime
# --------------------------------------------------------------------------- #
def test_forward_euler_matches_analytic_in_stable_regime():
    """Below CFL, θ=0 decays the no-flux eigenmode at the exact rate exp(−Dπ²t/L²)."""
    L, N, D, t_end = 1.0, 40, 1.0, 0.02
    g = uniform_grid(L, N)
    solver = Diffusion1D(g, D, Neumann(0.0), Neumann(0.0), method="forward_euler")
    dt = 0.4 * (L / N) ** 2 / (2.0 * D)  # comfortably under the CFL limit
    ic = np.cos(np.pi * g.centers / L)

    u = solver.solve(ic.copy(), t_end, dt)
    analytic = np.exp(-D * np.pi ** 2 * t_end / L ** 2) * np.cos(np.pi * g.centers / L)
    assert np.max(np.abs(u - analytic)) < 5e-3


def test_forward_euler_first_order_in_time():
    """θ=0 is 1st-order in time (like backward Euler) — extends invariant 4 additively."""
    L, N, D, t_end = 1.0, 20, 1.0, 0.02  # coarse grid so the CFL limit admits these dts
    g = uniform_grid(L, N)
    solver = Diffusion1D(g, D, Neumann(0.0), Neumann(0.0), method="forward_euler")
    ic = np.cos(np.pi * g.centers / L)
    cfl = (L / N) ** 2 / (2.0 * D)
    u_ref = solver.solve(ic.copy(), t_end, dt=t_end / 16384)  # ~exact in time, < cfl
    dts = [t_end / 32, t_end / 64, t_end / 128, t_end / 256]
    assert dts[0] < cfl  # every measured dt is stable
    errs = np.array([np.max(np.abs(solver.solve(ic.copy(), t_end, dt) - u_ref)) for dt in dts])
    slopes = np.log(errs[:-1] / errs[1:]) / np.log(2.0)
    assert np.all(slopes > 0.85), f"forward Euler not ~1st order in time: {slopes}"


# --------------------------------------------------------------------------- #
# Conservation: θ-independent (a real check, not a tautology)
# --------------------------------------------------------------------------- #
def test_forward_euler_conserves_under_no_flux():
    """No-flux ΣuᵢΔxᵢ is exact under θ=0 too — the FV face fluxes telescope regardless
    of the time scheme. Asserted on a NON-uniform grid (the harmonic-mean faces)."""
    edges = np.concatenate([np.linspace(0.0, 0.5, 25), np.linspace(0.5, 1.0, 16)[1:]])
    g = grid_from_edges(edges)
    solver = Diffusion1D(g, 1.0, Neumann(0.0), Neumann(0.0), method="forward_euler")
    u = np.exp(-((g.centers - 0.4) / 0.08) ** 2)
    total0 = solver.total(u)
    dt = 0.5 * _dt_crit(solver)  # stable; conservation in fact holds at any dt
    for _ in range(100):
        u = solver.step(u, dt)
    assert abs(solver.total(u) - total0) <= 1e-12 * abs(total0)


# --------------------------------------------------------------------------- #
# Benchmark: the CFL stability boundary (the headline)
# --------------------------------------------------------------------------- #
def test_cfl_bound_equals_dx2_over_2D_on_uniform_grid():
    """The operator-diagonal bound reduces to the textbook Δx²/2D on the clean case
    (uniform grid, constant D, no-flux: interior cells bind, boundaries add nothing)."""
    L, N, D = 1.0, 50, 0.7
    g = uniform_grid(L, N)
    solver = Diffusion1D(g, D, Neumann(0.0), Neumann(0.0), method="forward_euler")
    dx = L / N
    # Machine-precision identity (relative — the harmonic-mean + per-face division path
    # rounds differently from the direct closed form, but they agree to ~1e-15).
    assert abs(_dt_crit(solver) - dx ** 2 / (2.0 * D)) <= 1e-12 * (dx ** 2 / (2.0 * D))


def test_forward_euler_blows_up_above_cfl_stable_below():
    """The bound is read off the *operator diagonal*, so a Dirichlet face + a small cell
    tighten it (the advisor's point). Below it: bounded, monotone, decaying. Above it: the
    Nyquist mode amplifies without bound."""
    # Non-uniform grid with a refined left region, Dirichlet(0) at both ends → the smallest
    # cell adjacent to a Dirichlet ghost carries the largest |diag| and binds the CFL limit.
    edges = np.concatenate([np.linspace(0.0, 0.2, 30), np.linspace(0.2, 1.0, 25)[1:]])
    g = grid_from_edges(edges)
    solver = Diffusion1D(g, 1.0, Dirichlet(0.0), Dirichlet(0.0), method="forward_euler")
    dt_crit = _dt_crit(solver)
    ic = _alternating(g.n)
    hi = np.abs(ic).max()

    # Stable & monotone at half the limit: no new extrema (discrete maximum principle),
    # and the field decays toward the zero walls — the Nyquist mode is gone (the slowest,
    # domain-scale smooth remnant relaxes only over the diffusion time, far past 300 steps).
    u = ic.copy()
    for _ in range(300):
        u = solver.step(u, 0.5 * dt_crit)
        assert np.isfinite(u).all()
        assert np.abs(u).max() <= hi + 1e-12  # discrete maximum principle holds under CFL
    assert np.abs(u).max() < 0.5 * hi  # decayed well below the initial amplitude

    # Above the limit the Nyquist mode runs away.
    u = ic.copy()
    for _ in range(300):
        u = solver.step(u, 2.0 * dt_crit)
        if not np.isfinite(u).all() or np.abs(u).max() > 1e6:
            break
    assert (not np.isfinite(u).all()) or np.abs(u).max() > 1e6


def test_backward_euler_stable_where_forward_euler_blows_up():
    """The whole point of the amendment: at a dt many times the CFL limit, backward Euler
    stays bounded & monotone (unconditional) while forward Euler explodes (conditional)."""
    g = uniform_grid(1.0, 60)
    D = 1.0
    dt = 20.0 * (g.length / g.n) ** 2 / (2.0 * D)  # 20× the explicit limit
    ic = _alternating(g.n)

    be = Diffusion1D(g, D, Dirichlet(0.0), Dirichlet(0.0), method="backward_euler")
    u_be = ic.copy()
    for _ in range(50):
        u_be = be.step(u_be, dt)
    assert np.isfinite(u_be).all() and np.abs(u_be).max() <= np.abs(ic).max() + 1e-12

    fe = Diffusion1D(g, D, Dirichlet(0.0), Dirichlet(0.0), method="forward_euler")
    u_fe = ic.copy()
    for _ in range(50):
        u_fe = fe.step(u_fe, dt)
        if not np.isfinite(u_fe).all() or np.abs(u_fe).max() > 1e6:
            break
    assert (not np.isfinite(u_fe).all()) or np.abs(u_fe).max() > 1e6
