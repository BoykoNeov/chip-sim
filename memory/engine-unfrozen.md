---
name: engine-unfrozen
description: "engines.diffusion was UNFROZEN 2026-06-10 (governance open + test-gated, was frozen + ADR-gated). Future chip work MAY amend the engine directly (suite-gated, must not silently break consumers) — no longer forced to fit WITHIN the frozen surface. The whole v1.x 'fits within the frozen engine' framing is now a historical lineage, not a live constraint."
metadata: 
  node_type: memory
  type: project
  originSessionId: 0dd83a64-02c2-4cda-82b5-d438fde3a026
---

**`engines.diffusion` was unfrozen on 2026-06-10** at the user's direction ("unfreeze
all engines in the contract"). The Steel-Phase-1a **FROZEN** seal (2026-06-08) is lifted:
governance shifts **frozen + ADR-gated → open + test-gated**.

**What this changes for future work (the load-bearing point):** the v1.1–v1.4 reflex —
contort a new regime so it *fits WITHIN the frozen engine* via a consumer-side
stateful-closure / `D(t)` hook (the v1.3 `D(N)` lagged-coefficient pattern) — is **no
longer a hard constraint**. A deferred engine-native regime (native nonlinear `D(u)`,
2-D, an explicit integrator — the `Not in v1` list) MAY now be built **directly into the
engine**. The recurring "decisive finding = it fits within the frozen engine, no
amendment" across [[chip-coupling-v12]] / [[chip-highconc-v13]] / [[litho-defocus-v14]]
is now **historical lineage** (true when built), not a live gate. Don't re-derive
"must avoid touching the engine" — it's allowed.

**FIRST AMENDMENT LANDED (2026-06-10, v1.5): native nonlinear `D(u)` is BUILT** — the
prophecy above is now exercised. `engines/diffusion` gained `StateDependent(func)` (a
`D = func(u)` wrapper), solved per step by **Picard** (the fully-implicit nonlinear
backward-Euler solve) — and v1.3's `D(N)` box ([[chip-highconc-v13]]) was **promoted off
the consumer-side lag onto this native path** (`diffusion_highconc._diffuse_dn` is now a
thin step-loop over a `StateDependent` solver; the `picard_iters` knob is gone). Durable
engineering calls (advisor-confirmed): **(1) Picard, NOT Newton** — every iterate is a
standard linear backward-Euler solve with `D≥0`, so the nonlinear path *inherits* the
engine's per-iterate invariants (discrete-max-principle #3 + structural conservation #2);
Newton would need `dD/du` and lose monotone-per-iterate. **(2) Additive STRUCTURALLY** —
only `StateDependent` enters the Picard loop; every linear `D` form keeps the unchanged
single-solve `step()`, so the **18 prior engine invariants pass UNMODIFIED** (the proof it
didn't break a consumer; "if you're editing an existing engine test, it isn't additive").
**(3)** convergence norm scaled by field max (`max|Δu| ≤ tol·max|u|`) for the ~1e21→1e15
profile; **(4)** pure Picard / no damping so constant-`D` is bit-for-bit the scalar run.
New invariant **6** in `CONTRACT.md` + the `Not in v1` line flipped (`D(u)` built; 2-D /
explicit remain). New engine seal `engines/diffusion/tests/test_nonlinear_d.py` (10 tests — incl.
a Crank–Nicolson degenerate-seam lock, since `_step_nonlinear` covers θ=½ too though all consumers
use backward Euler); engine suite **18→28**, whole-repo fast lane **188**. **No new ADR** — ADR 0004 names native
nonlinear `D(u)` as *the* example of an ordinary test-gated edit. Box physics + v1.3 demo
numbers unchanged (v1.3 `picard_iters=2` was already ~converged).

**What did NOT change (keep the gate, drop the seal):**
- The **test suite still gates.** Every amendment re-runs `engines/diffusion/tests/` and
  keeps it green; an amendment that *changes* an invariant updates its test deliberately,
  same change. The invariants are still "the contract," just no longer immutable.
- An amendment **must not silently break an existing consumer** (chip still loads
  `CONTRACT.md` as its one-page dependency surface; a behaviour change for it is a
  breaking change → full-gate run, ADR 0003).
- Editing the engine is still the **full-gate** trigger (ADR 0003), and the API +
  validated invariants are unchanged by the unfreeze itself.

**Where it's recorded (chip-sim `main`, direct, pushed to origin):**
- `4536ec0` — `CONTRACT.md` banner FROZEN→ACTIVE, `## Frozen invariants`→`## Guaranteed
  invariants`, rationale + dates folded into the banner.
- `26bf0c9` — **ADR `docs/decisions/0004-unfreeze-engine.md`** (the formal record, supersedes
  the 1a freeze clause) + the engine-adjacent now-false claims (`engines/__init__.py`,
  `engines/diffusion/{README,__init__,diffusion1d}`, engine test docstrings, top `README`).
- `ae07db4` — the chip-wide narrative: "frozen engine/spine/contract" → plain across 22
  chip modules/tests + the plan. **Preserved on purpose:** `@dataclass(frozen=True)`,
  the numerical **frozen-coefficient** / "`D` frozen at the old state" scheme, "frozen
  dataclasses", `sealed`/`re-seal` BCs, and **ADRs 0001–0003** (historical, superseded by
  0004, not edited in place).

**Scope note:** this repo vendors its own copy of `engines/diffusion`. steel-sim /
planet-sim (their own repos, same engine lineage) are **untouched** — their copies stay
frozen unless unfrozen there too. Part of [[bigsim-program]].
