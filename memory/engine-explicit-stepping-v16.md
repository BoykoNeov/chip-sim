---
name: engine-explicit-stepping-v16
description: "Microchip v1.6 (2026-06-11): explicit forward_euler (θ=0) stepping BUILT into engines.diffusion — the SECOND exercise of the unfreeze. Gating finding: explicit needs ~no new stepping code (it falls out of the θ-method at θ=0); the real content is the new conditional-CFL stability invariant. Advisor: build explicit NOT 2-D (anti-over-build, no 2-D consumer); the CFL trap = read dt_crit off the operator diagonal, not the textbook Δx²/2D."
metadata: 
  node_type: memory
  type: project
  originSessionId: ed080d86-8c6a-4294-a272-241505b75c30
---

**Microchip v1.6 — explicit `forward_euler` (θ=0) stepping: BUILT 2026-06-11.** The **second
amendment** under the unfreeze (see [[engine-unfrozen]]), chosen when the user picked "native
engine amendment" as the next direction (over a third chip phase or a 2-D build). The second of
`CONTRACT.md`'s deferred regimes promoted (nonlinear `D(u)` ✓v1.5 / 2-D / **explicit**).

**The gating finding (advisor-verified by tracing `step()`): explicit needed almost NO new
stepping code.** Forward Euler already *falls out* of the existing θ-method at θ=0 — the CN `else`
branch assembles `rhs = u0 + dt·(A₀·u0 + b0)`, then the implicit operator `(I − θ·dt·A)` degenerates
to the identity so `solve_banded` returns `rhs` unchanged. The only blocker was `_METHODS` not
listing `"forward_euler": 0.0`. So the amendment's real content is **not the stepping** but the
**new conditional-CFL stability invariant** the suite literally could not express before (no
conditionally-stable method existed to define a CFL boundary against — invariant 3 asserted
*unconditional* stability for the two implicit methods with nothing to contrast). A small θ=0
early-return branch in `step()` was added anyway (operator at `t0` only, no wasted `t1` assembly /
no solve) so the explicit path reads as first-class — **additive**: θ=1 + CN branches byte-for-byte
unchanged, the **28 prior engine invariants pass UNMODIFIED**.

**Durable advisor calls:**
- **(1) The gating call — build explicit, NOT 2-D.** Explicit rhythm-matches v1.5 (tight, additive,
  default unchanged), *completes a story* (the missing conditional counterpoint to unconditional
  stability), low-risk. A speculative 2-D subsystem (new class, sparse/ADI solver, 4-edge BCs, 2-D
  `state` array) has **no consumer** → cuts against the repo's rule-of-three / "name the extension,
  don't build it" culture (ADR 0003 §4); you'd be guessing the 2-D API with nothing to validate it.
  **2-D is now the last deferred regime — waits for a real consumer.** Its named demo when it comes:
  *lateral diffusion under a mask edge* (the cited lateral/vertical ≈ 0.8 rule), the tractable
  diffusion-only slice of the §5 2-D-TCAD tar pit.
- **(2) The CFL trap — read `dt_crit` off the operator diagonal, NOT the textbook `Δx²/2D`.** That
  closed form is only the uniform / constant-D / interior special case. The sharp von Neumann bound:
  monotonicity needs `1 + dt·diagᵢ ≥ 0` → **`dt_crit = 1/max|diagᵢ|`** (from `_operator`'s `diag`).
  The **Dirichlet ghost transmissibility** (`T_ghost = D/(0.5·Δx)`) + nonuniform small cells make
  boundary cells' `|diag|` larger → the bound is *tighter* there. `Δx²/2D` is anchored separately on
  the no-flux uniform case (interior binds, `1/max|diag| == Δx²/2D` to machine precision).

**Seal:** `engines/diffusion/tests/test_explicit.py` (**6 tests**) — *analytic* = stable-regime
eigenmode decay at exact `exp(−Dπ²t/L²)` + 1st-order-in-time (extends invariant 4, coarse grid so
CFL admits the dts); *conservation* = no-flux `ΣuᵢΔxᵢ` exact under θ=0 (FV telescoping is
θ-independent — real check, holds at any dt, non-uniform grid); *benchmark/headline* = the CFL
boundary (closed-form identity + the operator-diagonal bound on a non-uniform Dirichlet grid:
stable+monotone+decaying at `0.5·dt_crit`, Nyquist blow-up at `2·dt_crit`) + the
unconditional-vs-conditional contrast (backward Euler bounded at 20× CFL where forward Euler
explodes). Engine suite **28→34**, whole-repo fast lane **195→201**.

**No new ADR** (ADR 0004 pre-authorizes ordinary test-gated engine edits; the v1.6 plan entry is the
record). **No chip module / notebook touched** — a pure engine amendment, no chip consumer (exactly
the "no consumer, so the API is θ=0, impossible to guess wrong" point that made it the safe build).
`CONTRACT.md` amended (status second-amendment line, θ-method bullet, `method=` enum, invariant 3
conditional-CFL, invariant 4 forward-Euler 1st-order, `forward_euler`-built / `Not built: 2-D/3-D`);
README 28→34 + design note. Part of [[bigsim-program]]; lineage [[chip-highconc-v13]] (v1.5's `D(u)`
promotion was the first amendment).
