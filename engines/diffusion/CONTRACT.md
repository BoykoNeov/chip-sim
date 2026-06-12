# `engines.diffusion` — 1-D + 2-D conservative parabolic solver — CONTRACT

> **Status: ACTIVE — unfrozen 2026-06-10** (originally FROZEN 2026-06-08, Steel
> Phase 1a). Validated behind its passing suite (`engines/diffusion/tests/`, run
> via `./run_tests.ps1`). This one page is still the unit of context downstream
> projects load — Microchip and Planet depend on *this*, never on
> `projects/steel/`. **Governance: open + test-gated.** The surface below is open
> to amendment — gated by re-running the suite (and a deliberate update to any
> invariant the amendment changes), no longer sealed behind an ADR + re-seal
> (ADR 0004) — but an amendment must not silently break an existing consumer.
> Opened so the engine
> can grow past the v1 surface (the deferred nonlinear `D(u)` / 2-D / explicit
> regimes noted below) by direct, test-gated amendment. **First amendment landed
> 2026-06-10: native nonlinear `D(u)` (`StateDependent`, invariant 6)** — additive,
> the 18 prior invariants pass unmodified. **Second amendment landed 2026-06-11:
> explicit `forward_euler` (θ=0) stepping (invariant 3)** — additive (only the
> θ=0 branch is new; the implicit paths are byte-for-byte unchanged, the 28 prior
> invariants pass unmodified). **Third amendment landed 2026-06-12: the 2-D regime
> (`Diffusion2D`, invariant 7)** — a *new module* (`diffusion2d.py`), tensor-product
> finite volume, backward-Euler only; additive by construction (it imports the 1-D
> primitives but touches no 1-D code path, so the 34 prior invariants pass unmodified);
> **3-D is now the last deferred regime.**

## What it solves

The conservative 1-D parabolic PDE

```
∂u/∂t = ∂/∂x( D(x,t) ∂u/∂x ) + S(x,t)        on   x ∈ [0, L]
```

`u` is a generic conserved intensive scalar. The engine is **material-agnostic**;
two usage patterns ship with Steel (the physics constants live in the *consumer*,
not here — see "Validation boundary"):

| Mode | `u` | `D` | Conserved quantity | Quench BC |
|---|---|---|---|---|
| **mass** | `%C` | `D(T) = D₀·exp(−Q/RT)` (carbon in austenite) | `∫C dx` | — |
| **heat** | `T` | `α = k/(ρc_p)` | enthalpy `∫ρc_p T dx` | Robin `h` |

The two differ *only* by relabelling `(u, D, BC params)` — that symmetry is why
one engine serves both, and why Planet's EBM heat transport is the same code.

## Discretization (fixed)

- **Cell-centered finite volume.** The flux leaving a cell across a face equals
  the flux entering its neighbour across that face, so interior fluxes telescope
  and `Σ uᵢΔxᵢ` changes *only* through boundary fluxes → conservation is
  structural and exact. Holds on **non-uniform** grids too.
- **θ-method time stepping**: `backward_euler` (θ=1, default) and
  `crank_nicolson` (θ=½) are implicit, one tridiagonal solve per step
  (`scipy.linalg.solve_banded`); `forward_euler` (θ=0) is explicit (no solve —
  `u^{n+1} = u^n + dt·(A·u^n + b)`), conditionally stable under the CFL limit
  (invariant 3).
- Interior **face diffusivity = harmonic mean** of the two cell values (exact
  flux continuity across a D-discontinuity; reduces to D for constant D).
- **Nonlinear `D(u)`** (a `StateDependent` diffusivity) is solved per step by
  **Picard** (successive substitution): each iterate is one ordinary linear
  tridiagonal solve with `D` frozen at the current field, repeated to a fixed point
  (= the fully-implicit nonlinear solve). Every iterate is the monotone, conservative
  single-step operator, so the nonlinear path inherits those guarantees — Picard,
  not Newton. Linear `D` forms skip the loop entirely.

## API

```python
from engines.diffusion import (
    Diffusion1D, Grid, uniform_grid, grid_from_edges,
    Dirichlet, Neumann, Robin, StateDependent,
)

grid   = uniform_grid(length, n)          # or grid_from_edges([...])  (non-uniform)
solver = Diffusion1D(grid, D, bc_left, bc_right, source=None,
                     method="backward_euler",    # or "crank_nicolson" / "forward_euler"
                     picard_tol=1e-10, picard_max_iter=100)   # nonlinear-D controls only

state = solver.step(state, dt, t0=0.0)            # one step; returns new array
state = solver.solve(state, t_end, dt, t0=0.0)    # march to t0+t_end
q     = solver.total(state)                       # ∫u dx = Σ uᵢΔxᵢ
J     = solver.flux(state, end, t=0.0)            # end ∈ {"left","right"}
```

- **`D`**: scalar, length-`n` cell-centered array `D(x)`, a callable `D(t)`
  returning either, or a `StateDependent(func)` wrapper for the **nonlinear**
  diffusivity `D = func(u)` (e.g. concentration-dependent `D(N)`). (`D(T)` is
  expressed as a callable closing over a temperature schedule:
  `lambda t: D0*np.exp(-Q/(R*T(t)))`.) A bare callable is always `D(t)`; **only**
  the `StateDependent` wrapper triggers the nonlinear per-step Picard solve
  (invariant 6) — the linear forms keep their single-solve `step()`.
- **`picard_tol`, `picard_max_iter`**: control the `StateDependent` Picard solve
  (convergence `max|Δu| ≤ picard_tol·max|u|`, capped at `picard_max_iter`,
  no raise on cap). Ignored for the linear `D` forms.
- **`source`**: scalar, length-`n` array, or callable `S(t)`; units of `u`/time.
- **Boundary conditions** (each end, independently):
  - `Dirichlet(value)` — `u = value` at the face (`value` scalar or `value(t)`).
  - `Neumann(flux=0.0)` — physical flux `J = −D ∂u/∂x = flux` in **+x**;
    `flux=0` is insulated / symmetry / no-flux (the conservation BC).
  - `Robin(h, u_ext)` — convective, applied with the **outward normal**:
    `−D ∂u/∂n = h(u − u_ext)`, so a single `h>0` cools toward `u_ext` at **both**
    ends (the expected quench). Series-resistance coefficient
    `U_eff = 1/(Δx/2D + 1/h)`.

### 2-D API (the third amendment)

```python
from engines.diffusion import (
    Diffusion2D, Grid2D, uniform_grid_2d, MaskedSurface,
    Dirichlet, Neumann, Robin,            # the 1-D edge BCs are reused unchanged
)

grid   = uniform_grid_2d(length_x, length_y, nx, ny)   # or Grid2D(x=grid1, y=grid2)
solver = Diffusion2D(grid, D,                           # D scalar or (nx, ny) array
                     bc_xlo, bc_xhi, bc_ylo, bc_yhi,    # each edge: a scalar BC …
                     source=None, method="backward_euler")

state = solver.step(state, dt, t0=0.0)            # state is a 2-D (nx, ny) ndarray
state = solver.solve(state, t_end, dt, t0=0.0)
q     = solver.total(state)                       # ∫∫u dA = Σ uᵢⱼ Δxᵢ Δyⱼ
```

- **`state`** is a plain 2-D `ndarray` of shape `(nx, ny)` (`state[i,j]` = `u` at lateral
  index `i`/`x`, depth index `j`/`y`); flattened C-order `k = i·ny + j` internally. Same
  ADR-0001 boundary as 1-D — the array, and only it, crosses the per-step boundary.
- **Edge BCs** `bc_xlo/bc_xhi/bc_ylo/bc_yhi`: a scalar `Dirichlet`/`Neumann`/`Robin`
  (applied uniformly along the whole edge), **or** `MaskedSurface(value, open_mask)` — a
  per-cell **Dirichlet under the window / no-flux under the mask** edge (`open_mask` a bool
  array of length = the cells along that edge). The masked surface is the one new BC, and
  the piece that makes the mask-edge problem non-separable.
- **Backward-Euler only** here; `D` time-independent. CN / explicit / nonlinear `D(u)` /
  anisotropic-tensor `D` are deferred (no consumer yet) — the named next 2-D amendments.

### Sign convention

Flux is `J = −D ∂u/∂x` (Fick), positive in **+x**. So at `"left"` `J>0` is inflow,
at `"right"` `J>0` is outflow. The exact backward-Euler identity
`total(stepped) − total(state) = dt·(flux(left) − flux(right))` holds to machine
precision (test `test_flux_bookkeeping_exact_backward_euler`).

### The data boundary (ADR 0001)

`state` is a **plain 1-D `ndarray`** of cell-centered `u`. That array — and only
it — crosses the per-step boundary: `step`/`solve` consume and return it,
`total`/`flux` consume it. No live objects cross. `Grid`, `D`, and BCs are
**construction-time configuration** that reduces to numbers during matrix
assembly; a compiled reimplementation (PyO3/Cython/…) parameterizes them natively
(e.g. `D₀,Q`; a BC enum + params) and exposes the same `state` array. The viz
layer (ADR 0002) consumes the same `state` — never a live solver object.

## Guaranteed invariants (what the test suite guarantees — = the contract)

1. **erfc semi-infinite profile** within tolerance, and **~2nd-order spatial
   convergence** (`test_erfc.py`; measured rates ≈ 2.00). The headline analytical
   limit — the carbon-into-austenite profile the whole program inherits.
2. **Exact conservation under no-flux** (`test_conservation.py`): `Σ uᵢΔxᵢ`
   constant, *any* dt, uniform or non-uniform grid. Exact in exact arithmetic; in
   floating point the only residual is accumulated linear-solver backward-error
   (~1e-11 over a long huge-dt run). Includes the source-augmented exact case
   (`test_source.py`).
3. **Stability, per method** (`test_stability.py`, `test_explicit.py`):
   - `backward_euler` — **unconditionally** stable **and monotone** (discrete
     maximum principle: no new extrema, no oscillation, any dt>0). *This is the
     "no oscillatory blow-up" guarantee the stability invariant names.*
   - `crank_nicolson` — **unconditionally** stable but **not monotone** (can produce
     decaying oscillations at large dt). Use it where temporal accuracy matters
     and dt is moderate, not for the headline stability claim.
   - `forward_euler` — **conditionally** well-behaved, with the same monotone-vs-
     merely-bounded split this invariant draws for BE vs CN, but now *dt-gated*: it is
     **monotone** (discrete maximum principle, no new extrema) iff `dt ≤ 1/max|diag|`
     — the sharp bound read off the assembled operator diagonal (`= Δx²/2D` on a
     uniform / constant-D / no-flux grid, *tighter* at Dirichlet faces and small
     cells). It stays merely **bounded (stable)** a little past that on non-uniform
     grids — a stable-but-non-monotone window of decaying oscillations up to
     `dt ≈ 2/|λ_min| ∈ [1/max|diag|, 2/max|diag|]` (the two limits coincide on a
     uniform grid, where the Nyquist eigenvalue is exactly `2·diag`) — and runs away
     without bound beyond it. `test_explicit.py` brackets this (max-principle at
     `0.5·dt_crit`, full blow-up by `2·dt_crit`) plus the headline contrast — backward
     Euler stays bounded *and* monotone at a dt where forward Euler explodes. The
     explicit method's value is exactly this conditional counterpoint that the two
     implicit methods' *unconditional* stability is defined against; it is **not** the
     default for production runs.
4. **Temporal order, per method** (`test_time_order.py`, `test_explicit.py`):
   backward Euler and forward Euler are 1st-order, Crank–Nicolson 2nd-order in
   time (measured against a tiny-dt reference so the slopes are purely temporal;
   the forward-Euler slope is measured on a coarse grid whose CFL limit admits the
   sampled dts).
5. **Variable diffusivity** (`test_variable_d.py`): the callable `D(t)` path
   matches the τ=∫D time-substitution analytic field (the carbon-during-cooling
   case steel uses next), and an array `D(x)` two-layer medium reproduces the
   exact series-resistance steady state — the one check that exercises the
   harmonic-mean face diffusivity.
6. **Nonlinear `D(u)`** (`test_nonlinear_d.py`, added 2026-06-10): a
   `StateDependent(func)` diffusivity is solved per step by **Picard** iteration to
   the fully-implicit nonlinear backward-Euler fixed point. Asserted: a *constant*
   `func` reproduces the scalar-`D` run **bit-for-bit** (the degenerate seam — the
   nonlinear hook *is* the engine); the Picard output satisfies its own nonlinear
   residual (converged, not a lag); `Σ uᵢΔxᵢ` stays conserved under no-flux with
   `D(u)` active (the telescoping is `D`-independent **per iterate**); and a
   constant-source profile collapses under `η = x/√t` for **any** `D(u)` (the
   model-independent self-similar anchor). **Additive:** only `StateDependent` enters
   the Picard loop, so invariants 1–5 pass **unmodified** (their tests are unchanged).

7. **2-D regime** (`Diffusion2D`, `tests/test_diffusion2d.py`, added 2026-06-12): the
   tensor-product backward-Euler solver (`Grid2D`, `MaskedSurface`, `uniform_grid_2d`).
   Asserted: the **dimensional-collapse seam** — a 2-D run uniform + no-flux in one
   direction reproduces the blessed 1-D engine solution in the other to **machine
   precision** (the tight anchor tying 2-D back to the spine; `< 1e-12`); **exact
   conservation** of `Σ uᵢⱼ Δxᵢ Δyⱼ` under no-flux on uniform *and* non-uniform grids
   (`≤ 1e-12`, telescoping per-direction); **isotropy** (a symmetric Gaussian spreads
   equally in x and y, `< 1e-12`); **monotonicity / bounds** at huge dt (the M-matrix
   maximum principle, no new extrema); **O(dt) operator-splitting convergence** to the
   outer product of two 1-D runs (a *convergence* check, not a seam — the discrete BE 2-D
   operator is a Kronecker *sum*, so the split-step product differs at O(dt²)); and that
   `MaskedSurface` is genuinely non-separable while only `backward_euler` is accepted.
   **Additive by construction:** `diffusion2d.py` imports the 1-D primitives but executes
   no 1-D code path, so invariants 1–6 pass **unmodified**.

## Validation boundary (what 1a does *not* claim)

Phase 1a validates the **solver machinery** with constant/given `D`. The
material parameter *values* — the Arrhenius `D₀, Q` for carbon, the `α` and
convective `h` for heat — are supplied by the **consumer** (`projects/steel/`)
and validated **there**, against the erfc carbon-profile benchmark and published
TTT/Jominy data (Steel plan §3, Phases 1–2). The validation suite here promises a
*correct generic parabolic solver*, not specific physical constants.

## Units & scope

- **SI throughout.** Mass vs heat mode differ only by relabelling.
- **Nonlinear `D(u)` is built** (2026-06-10, the first exercise of the unfreeze):
  pass `StateDependent(func)`; each step is Picard-solved (invariant 6).
- **Explicit `forward_euler` stepping is built** (2026-06-11, the second amendment):
  `method="forward_euler"` (θ=0), conditionally stable under the CFL limit (invariant 3).
- **2-D is built** (2026-06-12, the third amendment): `Diffusion2D` (`diffusion2d.py`),
  tensor-product finite volume, backward-Euler only (invariant 7). A separate module that
  reuses the 1-D primitives — the array-`state` boundary held, so it slotted in without
  touching the 1-D code path or any consumer.
- **Not built:** 3-D. The array-`state` boundary is the seam where that last deferred
  heavy regime (or a compiled core) is later slotted without touching consumers
  (ARCHITECTURE.md §8, ADR 0001).
