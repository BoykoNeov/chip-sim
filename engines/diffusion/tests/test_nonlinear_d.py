"""Native nonlinear diffusivity: the state-dependent ``D = func(u)`` Picard path.

Added 2026-06-10 — the **first exercise of the engine unfreeze** (ADR 0004). The contract's
long-deferred "nonlinear ``D(u)``" regime is now built *into* the engine as a ``StateDependent``
wrapper solved per step by **Picard** iteration (the fully-implicit nonlinear backward-Euler solve),
promoting Microchip v1.3's consumer-side lagged-coefficient hack into the native engine surface.

These tests are the **invariants of that path** — and two of them (the degenerate seam and the
Picard-convergence/lagged-consistency pair) were *engine* properties all along: they migrated here
verbatim-in-spirit from `chip/tests/test_diffusion_highconc.py`, where v1.3 had to assert them
against a closure in the consumer's step-loop. Now they hold of `engines.diffusion` directly.

What is asserted:
* **Degenerate seam (tight).** A *constant* ``StateDependent`` reproduces the scalar-``D`` run
  **bit-for-bit** — the nonlinear hook *is* the engine when ``D`` does not vary.
* **Fixed point (tight).** The converged step satisfies its own nonlinear residual: re-assembling
  the linear operator with ``D`` frozen at the *output* field reproduces that field — i.e. Picard
  converged to the fully-implicit nonlinear solve, not merely a lag.
* **Conservation (tight, machinery).** ``Σ uᵢΔxᵢ`` is conserved to machine precision under no-flux
  *with a genuine ``D(u)`` active* — the finite-volume telescoping is ``D``-independent, so the
  nonlinear path inherits invariant #2 per Picard iterate.
* **Boltzmann similarity (tight, model-independent).** A constant-source profile into a semi-infinite
  medium collapses under ``η = x/√t`` for **any** ``D(u)`` — validating that the Picard solve
  converges to the correct self-similar nonlinear field, not just *a* fixed point.
* **Consistency (tight).** Pure-lagged (``picard_max_iter=1``) carries a first-order-in-``dt`` lag
  error that shrinks toward the converged solve as ``dt → 0`` — the scheme is consistent.
* **Bounds (empirical).** Backward Euler stays within ``[0, surface]`` for a Dirichlet-driven
  ``D(u)`` front (every Picard iterate obeys the discrete maximum principle, so the fixed point does;
  asserted empirically per the v1.3 "don't over-claim monotonicity" discipline).
"""
import numpy as np
import pytest
from scipy.special import erfc

from engines.diffusion import (
    Diffusion1D,
    uniform_grid,
    Dirichlet,
    Neumann,
    StateDependent,
)


# --------------------------------------------------------------------------- #
# Degenerate seam — a constant StateDependent IS the scalar engine, bit-for-bit
# --------------------------------------------------------------------------- #
def test_constant_state_dependent_equals_scalar_bitforbit():
    # The headline additivity check: a StateDependent whose func ignores u and returns a constant
    # must reproduce the plain scalar-D run to the bit. Picard converges in the first iterate (the
    # constant operator is reused unchanged), so the nonlinear path adds nothing when D doesn't vary.
    g = uniform_grid(1.0, 200)
    c = 0.3
    nl = Diffusion1D(g, StateDependent(lambda u: c), Dirichlet(1.0), Neumann(0.0))
    lin = Diffusion1D(g, c, Dirichlet(1.0), Neumann(0.0))
    u_nl = np.zeros(g.n)
    u_lin = np.zeros(g.n)
    for _ in range(50):
        u_nl = nl.step(u_nl, 1e-3)
        u_lin = lin.step(u_lin, 1e-3)
    assert np.max(np.abs(u_nl - u_lin)) == 0.0          # bit-for-bit

    # ... and a constant array-returning func is identical too (the array-D path).
    arr = np.full(g.n, c)
    nl_arr = Diffusion1D(g, StateDependent(lambda u: arr), Dirichlet(1.0), Neumann(0.0))
    u_arr = np.zeros(g.n)
    for _ in range(50):
        u_arr = nl_arr.step(u_arr, 1e-3)
    assert np.max(np.abs(u_arr - u_lin)) == 0.0


def test_constant_state_dependent_no_flux_conserves_exactly():
    # The structural conservation invariant survives the Picard wrapper for the trivial (constant) D
    # — a sanity floor for the genuine-D(u) conservation test below.
    g = uniform_grid(1.0, 128)
    u = np.cos(np.pi * g.centers) + 1.5
    s = Diffusion1D(g, StateDependent(lambda u: 0.2), Neumann(0.0), Neumann(0.0))
    t0 = s.total(u)
    for _ in range(100):
        u = s.step(u, 0.01)
    assert abs(s.total(u) - t0) <= 1e-12 * abs(t0)


# --------------------------------------------------------------------------- #
# Fixed point — Picard converged to the fully-implicit nonlinear solve
# --------------------------------------------------------------------------- #
def test_picard_step_satisfies_the_nonlinear_residual():
    # The defining property of the native path (vs a mere lag): the output field N¹ is a fixed point
    # of the within-step iteration. Freeze D at N¹ and do ONE linear backward-Euler solve from N⁰ —
    # it must reproduce N¹. (A pure-lagged scheme would NOT: its D is frozen at N⁰, not N¹.)
    g = uniform_grid(1.0, 150)
    u0 = 0.5 + 0.4 * np.cos(np.pi * g.centers)
    D_of_u = lambda u: 0.02 * (1.0 + u ** 2)            # smooth, genuinely state-dependent
    dt = 0.02

    nl = Diffusion1D(g, StateDependent(D_of_u), Neumann(0.0), Neumann(0.0))
    u1 = nl.step(u0, dt)

    lin_at_output = Diffusion1D(g, D_of_u(u1), Neumann(0.0), Neumann(0.0))   # D frozen at the OUTPUT
    u1_reassembled = lin_at_output.step(u0, dt)
    assert np.max(np.abs(u1 - u1_reassembled)) <= 1e-10 * np.max(np.abs(u1))

    # the pure-lagged step (D frozen at the INPUT) is measurably different — proving u1 is the
    # converged solve, not the predictor.
    lin_at_input = Diffusion1D(g, D_of_u(u0), Neumann(0.0), Neumann(0.0))
    u1_lagged = lin_at_input.step(u0, dt)
    assert np.max(np.abs(u1 - u1_lagged)) > 1e-8 * np.max(np.abs(u1))


def test_picard_converges_in_few_iterations_for_smooth_D():
    # Smooth D(u) → the Picard iteration converges in a handful of solves per step. Count func
    # evaluations (one per iterate inside _operator); a constant D is 2, this stiffer D a few more.
    g = uniform_grid(1.0, 150)
    u0 = 0.5 + 0.4 * np.cos(np.pi * g.centers)
    calls = {"n": 0}

    def D_of_u(u):
        calls["n"] += 1
        return 0.02 * (1.0 + 5.0 * u ** 2)

    nl = Diffusion1D(g, StateDependent(D_of_u), Neumann(0.0), Neumann(0.0))
    nl.step(u0, 0.02)
    assert calls["n"] <= 6                              # ~2–5 in practice, generously capped


# --------------------------------------------------------------------------- #
# Conservation with a GENUINE D(u) active — D-independent telescoping
# --------------------------------------------------------------------------- #
def test_no_flux_conservation_with_genuine_state_dependent_D():
    # The finite-volume face fluxes telescope for ANY non-negative D field, so Σ uΔx is conserved to
    # machine precision even while D varies strongly with the (evolving) field. Confirms the Picard
    # wrapper did not break invariant #2. (Says nothing about the D magnitude — a machinery check.)
    g = uniform_grid(1.0, 200)
    u = np.exp(-((g.centers - 0.5) ** 2) / 0.01) + 0.1
    D_of_u = lambda u: 0.05 * (1.0 + 3.0 * np.clip(u, 0.0, None))   # D rises with u (a "box" driver)
    s = Diffusion1D(g, StateDependent(D_of_u), Neumann(0.0), Neumann(0.0))
    t0 = s.total(u)
    for _ in range(300):
        u = s.step(u, 2e-3)
    assert abs(s.total(u) - t0) <= 1e-12 * abs(t0)


# --------------------------------------------------------------------------- #
# Boltzmann similarity — the model-independent nonlinear anchor
# --------------------------------------------------------------------------- #
def test_boltzmann_similarity_collapse_for_any_D_of_u():
    # For a constant-source diffusion into a semi-infinite medium, N(x,t) depends on x,t ONLY through
    # η = x/√t for ANY D(N). So N(x, t) and N(2x, 4t) coincide. Holds for a stiff (1+u²) nonlinearity,
    # validating that the Picard solve converges to the correct *self-similar* nonlinear field —
    # model-independent (no reliance on any particular D(u) form being "right").
    D_of_u = lambda u: 0.01 * (1.0 + 4.0 * np.clip(u, 0.0, None) ** 2)
    t = 0.05
    g1 = uniform_grid(1.0, 800)
    g2 = uniform_grid(2.0, 1600)

    def run(g, t_end, n_steps):
        s = Diffusion1D(g, StateDependent(D_of_u), Dirichlet(1.0), Neumann(0.0))
        u = np.zeros(g.n)
        return s.solve(u, t_end, t_end / n_steps)

    u1 = run(g1, t, 1600)
    u2 = run(g2, 4 * t, 3200)
    u2_at_2x = np.interp(2.0 * g1.centers, g2.centers, u2)
    assert np.max(np.abs(u1 - u2_at_2x)) < 5e-3        # collapse (numeric + interpolation error)


# --------------------------------------------------------------------------- #
# Consistency — pure-lagged approaches the converged solve as dt → 0
# --------------------------------------------------------------------------- #
def test_lagged_approaches_converged_as_dt_shrinks():
    # picard_max_iter=1 forces the pure-lagged predictor (one solve, D frozen at the old level). Its
    # first-order-in-dt lag error shrinks toward the fully-converged solve as dt → 0 — the scheme is
    # consistent (it does not converge to the wrong field). The converged path is dt-stable here.
    g = uniform_grid(1.0, 200)
    u0 = np.zeros(g.n)
    D_of_u = lambda u: 0.01 * (1.0 + 4.0 * np.clip(u, 0.0, None) ** 2)
    t = 0.05

    def converged(n_steps):
        s = Diffusion1D(g, StateDependent(D_of_u), Dirichlet(1.0), Neumann(0.0))
        return s.solve(u0.copy(), t, t / n_steps)

    def lagged(n_steps):
        s = Diffusion1D(g, StateDependent(D_of_u), Dirichlet(1.0), Neumann(0.0),
                        picard_max_iter=1)
        return s.solve(u0.copy(), t, t / n_steps)

    ref = converged(4000)                              # fine-dt converged reference
    err_coarse = np.max(np.abs(lagged(250) - ref))
    err_fine = np.max(np.abs(lagged(2000) - ref))
    assert err_fine < err_coarse                       # lag error shrinks with dt
    assert err_fine < 5e-3                              # and is small at the fine step


# --------------------------------------------------------------------------- #
# Bounds — backward Euler stays in [0, surface] for a Dirichlet-driven front
# --------------------------------------------------------------------------- #
def test_backward_euler_front_stays_within_bounds():
    # Every Picard iterate is a monotone backward-Euler solve (M-matrix, D≥0), bounded by the data
    # [0, surface]; so the fixed point is too. Asserted empirically (not as a monotonicity *claim*) —
    # a steep state-dependent front does not overshoot the Dirichlet surface or go negative.
    g = uniform_grid(1.0, 400)
    Nsurf = 1.0
    D_of_u = lambda u: 0.005 * (1.0 + 50.0 * np.clip(u, 0.0, None) ** 2)   # stiff "box" front
    s = Diffusion1D(g, StateDependent(D_of_u), Dirichlet(Nsurf), Neumann(0.0))
    u = np.zeros(g.n)
    for _ in range(400):
        u = s.step(u, 5e-4)
    assert u.min() >= -1e-12
    assert u.max() <= Nsurf * (1.0 + 1e-9)


# --------------------------------------------------------------------------- #
# API guard — a bare callable is still D(t), only the wrapper is nonlinear
# --------------------------------------------------------------------------- #
def test_bare_callable_is_time_not_state_dependent():
    # The wrapper is load-bearing: a bare callable remains the linear D(t) path (single solve), so the
    # existing D(t) contract is untouched. A constant D(t)=c equals the scalar run; only StateDependent
    # triggers Picard. (Guards against a future regression that sniffs callables for state-dependence.)
    g = uniform_grid(1.0, 100)
    u = np.cos(np.pi * g.centers)
    u_t = Diffusion1D(g, lambda t: 0.4, Neumann(0.0), Neumann(0.0)).solve(u.copy(), 0.1, 0.005)
    u_c = Diffusion1D(g, 0.4, Neumann(0.0), Neumann(0.0)).solve(u.copy(), 0.1, 0.005)
    assert np.allclose(u_t, u_c, rtol=0.0, atol=1e-12)
