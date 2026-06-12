# `engines/diffusion` — the diffusion/heat spine

The first and most-reused engine in the program (ARCHITECTURE.md §5): a
conservative 1-D parabolic (diffusion / heat) solver. Sealed at Steel
Phase 1a behind its validation suite and reused by Microchip (dopant profiles)
and Planet (EBM heat transport); **unfrozen 2026-06-10** — now open + test-gated
(the suite still gates; the surface is open to amendment). See `CONTRACT.md`.

## Load pointer (per-session working set, §11)

- **To *use* this engine** (from Steel/Chip/Planet): load **`CONTRACT.md`** only
  — the one-page API contract. You do not need this folder's internals.
- **To *modify* this engine:** `CONTRACT.md` + `diffusion1d.py` (and
  `diffusion2d.py` for the 2-D regime) + `tests/`. The tests are the seal — they
  must stay green, and they *are* the externalized memory of every contract
  downstream relies on (§6).

## Files

| File | What |
|---|---|
| `CONTRACT.md` | **The API contract.** Start here. PDE, modes, API, sign conventions, the guaranteed invariants, the validation boundary. |
| `diffusion1d.py` | The 1-D solver: `Diffusion1D`, `Grid`/`uniform_grid`/`grid_from_edges`, `Dirichlet`/`Neumann`/`Robin`, `StateDependent` (nonlinear `D(u)`). Cell-centered finite volume + θ-method stepping (`backward_euler` / `crank_nicolson` implicit, `forward_euler` explicit); Picard for the nonlinear path. |
| `diffusion2d.py` | The 2-D solver (the third amendment, 2026-06-12): `Diffusion2D` on a tensor-product `Grid2D`/`uniform_grid_2d`, plus the `MaskedSurface` edge BC (Dirichlet window / no-flux mask). 5-point cell-centered finite volume, backward-Euler only, sparse `splu` cached per `dt`; reuses the 1-D BCs and harmonic-mean faces. |
| `tests/` | The seal (45 tests): `test_erfc` (analytical limit + 2nd-order spatial convergence), `test_conservation` (exact no-flux mass balance), `test_stability` (unconditional stability, the implicit methods), `test_explicit` (`forward_euler` θ=0 — the CFL stability boundary + the unconditional-vs-conditional contrast), `test_source` (source-augmented conservation), `test_variable_d` (callable `D(t)` + array `D(x)`/harmonic mean), `test_time_order` (BE 1st- / CN 2nd-order in time), `test_robin_heat` (heat-mode Robin + flux bookkeeping), `test_nonlinear_d` (the `StateDependent` `D(u)` Picard path — degenerate seam, fixed point, conservation, Boltzmann similarity), `test_diffusion2d` (the 2-D regime — the dimensional-collapse seam to the 1-D engine, 2-D conservation/isotropy/monotonicity, O(dt) split-step convergence, the non-separable `MaskedSurface`). |

## Run the seal

```powershell
./run_tests.ps1 engines/diffusion        # from repo root  (or just ./run_tests.ps1)
```

## Design notes (the non-obvious choices)

- **Conservation is structural, not enforced.** Finite-volume face fluxes
  telescope, so `Σ uᵢΔxᵢ` moves only through the boundaries — true on
  non-uniform grids and at any dt. The residual in the test is accumulated
  linear-solver roundoff, not a scheme defect.
- **Backward Euler is the default for a reason.** It is unconditionally stable
  *and monotone* (discrete maximum principle), so a learner picks any dt without
  blow-up or spurious oscillation. Crank–Nicolson (θ=½) is offered for temporal
  accuracy but can oscillate at large dt — see `CONTRACT.md`. The explicit
  `forward_euler` (θ=0) is the *conditional* counterpoint: monotone only under the
  CFL limit `dt ≤ 1/max|diag|` and bounded only a little past it (`test_explicit`
  brackets the max-principle at half the limit and full blow-up at 2×, and contrasts
  it against backward Euler at the same dt) — the amendment that lets the suite
  *demonstrate* why the default is implicit rather than just assert it.
- **The engine carries no material constants.** Arrhenius `D₀,Q`, `α`, `h` are
  the consumer's; the engine consumes a generic `D` and BCs. This keeps the
  API surface minimal and the validation boundary honest.
- **Nonlinear `D(u)` is Picard, not Newton, and additive** (the first exercise of
  the unfreeze, 2026-06-10). A `StateDependent(func)` diffusivity is solved per step
  by Picard — each iterate is an ordinary linear backward-Euler solve, so it inherits
  the engine's monotonicity and structural conservation per iterate (Newton would
  need `dD/du` and lose that). Only `StateDependent` enters the Picard loop; the
  linear `D` forms are byte-for-byte unchanged, which is why the 18 prior tests pass
  unmodified. Microchip v1.3's `D(N)` box (`chip/diffusion_highconc.py`) was built on
  a consumer-side lag while the engine was frozen; the unfreeze promoted it here.
- **2-D is a separate module that reuses the spine, not a rewrite** (the third
  exercise of the unfreeze, 2026-06-12). `diffusion2d.py` extends the same
  cell-centered finite volume to a tensor-product grid: a sparse 5-point operator
  whose `(I − dt·A)` is an M-matrix, so unconditional stability, monotonicity and
  structural conservation carry over verbatim. The **dimensional-collapse seam**
  ties it back to the blessed 1-D engine at machine precision (a 2-D run uniform +
  no-flux in one direction *is* the 1-D solution in the other). It imports the 1-D
  primitives but touches no 1-D code path, so the 34 prior tests pass unmodified.
  Backward-Euler only; CN / explicit / nonlinear-`D(u)` / anisotropic `D` wait for a
  consumer. The one genuinely-2-D addition is `MaskedSurface` (a per-cell
  Dirichlet-window / no-flux-mask edge) — the non-separability its named consumer,
  lateral diffusion under a mask edge, needs.
- **The `state` array is the whole data contract** (ADR 0001): the seam for a
  future compiled core or a deferred heavy regime, and what the viz layer
  (ADR 0002) consumes. (The 2-D `state` is the same idea, a plain `(nx, ny)` array.)
