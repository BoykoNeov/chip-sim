"""2-D conservative parabolic solver — the invariants of the last deferred regime.

Added 2026-06-11 — the **third exercise of the engine unfreeze** (ADR 0004), and the one the
contract named last (``Not built: 2-D/3-D``). ``Diffusion2D`` is the tensor-product extension of
the 1-D spine, pulled in by its named consumer (chip mask-edge lateral diffusion). These tests are
the invariants of that path; the *physics* benchmark (the lateral/vertical ≈ 0.8 ratio) lives with
the consumer, in ``chip/tests`` — here we validate the **machinery**.

What is asserted:
* **Dimensional-collapse seam (tight, the headline).** A 2-D run that is uniform + no-flux in one
  direction reproduces the **1-D engine's** solution in the other, to **machine precision** — the
  2-D operator *is* the blessed 1-D operator when one dimension is inert (``L_x`` annihilates
  x-constant fields). This is the additive degenerate seam, the 2-D analogue of v1.5's
  ``StateDependent(const)==scalar`` and v1.6's θ=0 fall-out. (Note: the *continuous* "2-D = outer
  product of two 1-D runs" theorem is **not** machine-exact for backward Euler at finite dt — the
  discrete operator is a Kronecker *sum*, ``(I−dt(Lx⊕Ly)) ≠ (I−dtLx)⊗(I−dtLy)``, differing at
  O(dt²); that appears below as a *convergence* check, not a seam.)
* **Conservation (tight, machinery).** ``Σ uᵢⱼ Δxᵢ Δyⱼ`` is conserved to machine precision under
  all-no-flux, any dt, on uniform **and** non-uniform tensor grids — the FV telescoping holds in
  both directions.
* **Separability convergence (the theorem + the BE subtlety).** A separable problem converges to
  the outer product of two 1-D runs as ``dt → 0`` (the splitting error is O(dt) global, halving
  with dt) — validating the continuous separability theorem while documenting why it is not the
  machine-precision seam.
* **Isotropic spreading (analytic anchor).** A narrow blob in a large no-flux box spreads with
  variance ``2Dt`` in **both** axes, and the two second moments agree to machine precision — the
  operator is isotropic (couples x and y identically).
* **Backward-Euler unconditional stability + monotonicity.** A Dirichlet-driven front stays within
  ``[0, surface]`` (no overshoot, no negativity) at a *huge* dt — the 2-D operator is an M-matrix.
* **The masked surface — the genuinely-2-D piece.** Far from the mask edge the windowed column
  recovers the 1-D constant-source profile (the BC reduces to 1-D in the bulk); under the mask the
  field is non-zero only by *lateral* diffusion (a uniform no-flux surface would give exactly zero
  there) — the non-separable signature the consumer needs.
* **API guards.** Only backward Euler; the masked edge's mask length is validated; D shape is checked.
"""
import numpy as np
import pytest

from engines.diffusion import (
    Diffusion1D,
    Diffusion2D,
    Grid2D,
    uniform_grid,
    uniform_grid_2d,
    grid_from_edges,
    Dirichlet,
    Neumann,
    MaskedSurface,
)


# --------------------------------------------------------------------------- #
# Dimensional-collapse seam — the 2-D operator IS the 1-D engine when one axis is inert
# --------------------------------------------------------------------------- #
def test_collapse_in_y_equals_1d_engine_bitclose():
    # Uniform + no-flux in x, a Dirichlet drive at y=0: the problem has no x-dependence, so every
    # column must equal the 1-D y-solution. L_x annihilates an x-constant field exactly, so the 2-D
    # backward-Euler step reduces to the 1-D y-step to machine precision (solver backward-error only).
    nx, ny = 6, 80
    D = 0.2
    g2 = uniform_grid_2d(1.0, 1.0, nx, ny)
    s2 = Diffusion2D(g2, D, Neumann(0.0), Neumann(0.0), Dirichlet(1.0), Neumann(0.0))
    u2 = np.zeros(g2.shape)
    s1 = Diffusion1D(uniform_grid(1.0, ny), D, Dirichlet(1.0), Neumann(0.0))
    u1 = np.zeros(ny)
    for _ in range(60):
        u2 = s2.step(u2, 1e-3)
        u1 = s1.step(u1, 1e-3)
    assert np.max(np.abs(u2 - u1[None, :])) < 1e-12


def test_collapse_in_x_equals_1d_engine_bitclose():
    # The symmetric statement: uniform + no-flux in y, a Dirichlet drive at x=0 → every row equals the
    # 1-D x-solution. Guards that the x-direction assembly is the mirror of the y-direction one.
    nx, ny = 90, 5
    D = 0.35
    g2 = uniform_grid_2d(1.0, 1.0, nx, ny)
    s2 = Diffusion2D(g2, D, Dirichlet(1.0), Neumann(0.0), Neumann(0.0), Neumann(0.0))
    u2 = np.zeros(g2.shape)
    s1 = Diffusion1D(uniform_grid(1.0, nx), D, Dirichlet(1.0), Neumann(0.0))
    u1 = np.zeros(nx)
    for _ in range(60):
        u2 = s2.step(u2, 1e-3)
        u1 = s1.step(u1, 1e-3)
    assert np.max(np.abs(u2 - u1[:, None])) < 1e-12


# --------------------------------------------------------------------------- #
# Conservation — Σ uΔxΔy under all-no-flux, uniform and non-uniform grids
# --------------------------------------------------------------------------- #
def test_no_flux_conservation_uniform_grid():
    g = uniform_grid_2d(1.0, 1.0, 50, 60)
    s = Diffusion2D(g, 0.3, Neumann(0.0), Neumann(0.0), Neumann(0.0), Neumann(0.0))
    X, Y = g.x.centers[:, None], g.y.centers[None, :]
    u = np.exp(-((X - 0.5) ** 2 + (Y - 0.5) ** 2) / 0.02) + 0.1
    t0 = s.total(u)
    for _ in range(200):
        u = s.step(u, 0.01)            # large dt; backward Euler unconditional
    assert abs(s.total(u) - t0) <= 1e-12 * abs(t0)


def test_no_flux_conservation_nonuniform_grid():
    # Telescoping must hold on a non-uniform tensor grid too (a graded mesh in both directions) — the
    # 2-D extension of the 1-D non-uniform conservation invariant.
    xe = np.linspace(0.0, 1.0, 41) ** 1.4          # graded in x
    ye = np.linspace(0.0, 1.0, 51) ** 0.7          # graded in y
    g = Grid2D(grid_from_edges(xe), grid_from_edges(ye))
    s = Diffusion2D(g, 0.25, Neumann(0.0), Neumann(0.0), Neumann(0.0), Neumann(0.0))
    X, Y = g.x.centers[:, None], g.y.centers[None, :]
    u = np.cos(np.pi * X) * np.cos(np.pi * Y) + 2.0
    t0 = s.total(u)
    for _ in range(150):
        u = s.step(u, 0.02)
    assert abs(s.total(u) - t0) <= 1e-12 * abs(t0)


# --------------------------------------------------------------------------- #
# Separability — converges to the outer product of two 1-D runs (the BE-splitting subtlety)
# --------------------------------------------------------------------------- #
def test_separable_converges_to_outer_product_of_1d_runs():
    # Constant D, all-no-flux (a product BC) and a separable IC a(x)·b(y): the *continuous* solution
    # is A(x,t)·B(y,t). Backward Euler does NOT reproduce that product exactly at finite dt — the
    # discrete operator is a Kronecker SUM, so the 2-D step and the product of two 1-D steps differ at
    # O(dt²)/step, O(dt) globally. So the discrepancy must (a) be small and (b) ~halve as dt halves —
    # confirming the theorem in the limit and that this is a convergence check, not the machine seam.
    nx, ny = 40, 50
    D = 0.3
    g = uniform_grid_2d(1.0, 1.0, nx, ny)
    a = 1.0 + 0.5 * np.cos(np.pi * g.x.centers)
    b = 1.0 + 0.3 * np.cos(2 * np.pi * g.y.centers)
    u0 = np.outer(a, b)
    t_end = 0.05
    gx, gy = uniform_grid(1.0, nx), uniform_grid(1.0, ny)

    def discrepancy(n_steps):
        dt = t_end / n_steps
        u2 = Diffusion2D(g, D, Neumann(0.0), Neumann(0.0), Neumann(0.0), Neumann(0.0)).solve(
            u0.copy(), t_end, dt)
        Ax = Diffusion1D(gx, D, Neumann(0.0), Neumann(0.0)).solve(a.copy(), t_end, dt)
        By = Diffusion1D(gy, D, Neumann(0.0), Neumann(0.0)).solve(b.copy(), t_end, dt)
        return np.max(np.abs(u2 - np.outer(Ax, By)))

    coarse, fine = discrepancy(20), discrepancy(40)
    assert coarse < 1e-3                       # small (the product theorem nearly holds)
    assert 1.8 < coarse / fine < 2.2           # ~halves with dt → O(dt) splitting error → 0


# --------------------------------------------------------------------------- #
# Isotropic spreading — the 2-D heat kernel, variance 2Dt in both axes
# --------------------------------------------------------------------------- #
def test_isotropic_gaussian_spread():
    # A narrow blob at the center of a large no-flux box spreads with variance 2Dt in each direction
    # (before it reaches the walls). The two second moments grow equally — the operator is isotropic.
    N, L, D = 120, 4.0, 0.5
    g = uniform_grid_2d(L, L, N, N)
    X, Y = g.x.centers[:, None], g.y.centers[None, :]
    x0 = y0 = L / 2
    u = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / (2 * 0.02))
    s = Diffusion2D(g, D, Neumann(0.0), Neumann(0.0), Neumann(0.0), Neumann(0.0))

    def moments(f):
        A = g.cell_areas
        m = np.sum(f * A)
        return np.sum(f * A * (X - x0) ** 2) / m, np.sum(f * A * (Y - y0) ** 2) / m
    vx0, vy0 = moments(u)
    t_end = 0.3
    u = s.solve(u, t_end, 1e-3)
    vx, vy = moments(u)
    assert abs((vx - vx0) - 2 * D * t_end) < 0.02 * (2 * D * t_end)   # within ~2% (discretization)
    assert abs((vy - vy0) - 2 * D * t_end) < 0.02 * (2 * D * t_end)
    assert abs(vx - vy) < 1e-12                                       # isotropy, to machine precision


# --------------------------------------------------------------------------- #
# Backward Euler — unconditionally stable AND monotone (M-matrix) in 2-D
# --------------------------------------------------------------------------- #
def test_backward_euler_monotone_bounded_at_huge_dt():
    # A Dirichlet surface drives a front into a zero field; backward Euler must stay within the data
    # bounds [0, Nsurf] — no overshoot, no negative undershoot — even at a dt far past any explicit
    # CFL limit. This is the 2-D M-matrix discrete maximum principle (the engine's headline guarantee).
    g = uniform_grid_2d(1.0, 1.0, 60, 60)
    Nsurf = 1.0
    s = Diffusion2D(g, 1.0, Neumann(0.0), Neumann(0.0), Dirichlet(Nsurf), Neumann(0.0))
    u = np.zeros(g.shape)
    for _ in range(50):
        u = s.step(u, 0.5)             # dt = 0.5 with Δ≈0.017 → ~1e3× any explicit limit
    assert u.min() >= -1e-12
    assert u.max() <= Nsurf * (1.0 + 1e-9)


# --------------------------------------------------------------------------- #
# The masked surface — bulk recovers 1-D, and the genuinely-2-D lateral signature
# --------------------------------------------------------------------------- #
def test_masked_surface_bulk_recovers_1d_constant_source():
    # Deep under the window (the x=0 symmetry edge, many diffusion-lengths from the mask edge), the
    # vertical column must match a 1-D constant-source diffusion — i.e. the masked BC reduces to the
    # 1-D Dirichlet surface where the window is wide. Tight (the edge is too far to perturb x=0).
    Lx, Ly, D, t_end = 6.0, 4.0, 1.0, 0.25
    g = uniform_grid_2d(Lx, Ly, 180, 160)
    window = g.x.centers < 3.0
    s = Diffusion2D(g, D, Neumann(0.0), Neumann(0.0), MaskedSurface(1.0, window), Neumann(0.0))
    u = s.solve(np.zeros(g.shape), t_end, 5e-4)
    s1 = Diffusion1D(uniform_grid(Ly, 160), D, Dirichlet(1.0), Neumann(0.0))
    u1 = s1.solve(np.zeros(160), t_end, 5e-4)
    assert np.max(np.abs(u[0, :] - u1)) < 1e-4


def test_masked_surface_is_non_separable_lateral_diffusion():
    # The genuinely-2-D signature: under the mask (x > x_edge) the field is non-zero ONLY by lateral
    # diffusion from the window — a uniform no-flux surface there would give exactly zero. So just past
    # the edge the surface concentration is a real fraction of the window value, and it decays to ~0
    # deep under the mask (the lateral reach is finite, ~√(2Dt)). A separable/1-D model cannot produce
    # this x-structure under a sealed surface.
    Lx, Ly, D, t_end = 6.0, 4.0, 1.0, 0.25
    g = uniform_grid_2d(Lx, Ly, 180, 160)
    x_edge = 3.0
    window = g.x.centers < x_edge
    s = Diffusion2D(g, D, Neumann(0.0), Neumann(0.0), MaskedSurface(1.0, window), Neumann(0.0))
    u = s.solve(np.zeros(g.shape), t_end, 5e-4)
    surf = u[:, 0]
    bulk = surf[g.x.centers < 1.0].mean()
    just_past = surf[np.argmin(np.abs(g.x.centers - (x_edge + 0.3)))]
    deep_mask = surf[g.x.centers > x_edge + 2.0].mean()
    assert just_past > 0.1 * bulk           # real lateral leak under the mask
    assert deep_mask < 1e-3 * bulk          # but it decays laterally → ~0 deep under the mask


# --------------------------------------------------------------------------- #
# API guards
# --------------------------------------------------------------------------- #
def test_only_backward_euler_is_built():
    g = uniform_grid_2d(1.0, 1.0, 10, 10)
    with pytest.raises(ValueError, match="backward_euler"):
        Diffusion2D(g, 1.0, Neumann(0.0), Neumann(0.0), Neumann(0.0), Neumann(0.0),
                    method="crank_nicolson")


def test_masked_surface_mask_length_and_D_shape_validated():
    g = uniform_grid_2d(1.0, 1.0, 10, 12)      # nx=10, ny=12
    bad_mask = np.ones(7, dtype=bool)          # wrong length for the ylo edge (should be nx=10)
    with pytest.raises(ValueError, match="open_mask"):
        Diffusion2D(g, 1.0, Neumann(0.0), Neumann(0.0), MaskedSurface(1.0, bad_mask), Neumann(0.0))
    with pytest.raises(ValueError, match="shape"):
        Diffusion2D(g, np.ones((3, 3)), Neumann(0.0), Neumann(0.0), Neumann(0.0), Neumann(0.0))
