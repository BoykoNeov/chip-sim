# 0004 — Unfreeze the diffusion engine (open + test-gated)

Status: Accepted — 2026-06-10
Scope: `engines/diffusion`. Supersedes the Steel Phase-1a freeze recorded in
`engines/diffusion/CONTRACT.md` (the *governance* clause only; the API and the
validated invariants are unchanged).

## Context

`engines.diffusion` was **FROZEN** at the end of Steel Phase 1a (2026-06-08):
the API surface was sealed behind its passing validation suite, and the contract
declared that *changing the frozen surface means a new ADR + re-running the seal*.
The freeze existed to give the downstream consumers (Microchip, Planet) a stable
surface they could depend on without tracking the engine's internals.

The freeze did its job. Over Microchip v1.1–v1.4 the recurring finding was that
each new regime (OED, dopant segregation, concentration-dependent `D(N)`,
defocus) **fit within the frozen surface** without an amendment — the engine's
generic `D` (scalar / array / callable), its BC set, and the per-step `state`
array were expressive enough every time. That is a real result, but it also means
the *ceremony* the freeze imposed — an ADR + re-seal for any surface change — was
never actually exercised, while the engine's own contract still lists genuinely
deferred regimes (`Not in v1`: nonlinear `D(u)`, 2-D/3-D, explicit stepping) that
a consumer may eventually want to grow **into the engine** rather than route
around via a consumer-side closure.

Two things the freeze bundled together are worth separating:

1. **Immutability + ADR ceremony** — the surface may not change without a new ADR
   and a re-seal.
2. **The validation guarantee** — every invariant in the contract is backed by a
   passing test, and the suite gates every change.

Only (1) has outlived its usefulness. (2) is the engine's whole value and must
not be weakened.

## Decision

**Unfreeze `engines.diffusion`. Governance shifts from *frozen + ADR-gated* to
*open + test-gated*.**

- The API surface is **open to direct amendment**. Growing the engine (e.g. a
  native nonlinear `D(u)` path, a second spatial dimension, an explicit
  integrator) no longer requires a fresh ADR + re-seal; it is an ordinary edit.
- **The test suite still gates.** Every amendment re-runs `engines/diffusion/tests/`
  and must keep it green. An amendment that *changes* an invariant updates the
  corresponding test deliberately, in the same change — the invariants remain "the
  contract," just no longer immutable.
- **An amendment must not silently break an existing consumer.** Microchip and
  Planet still load `CONTRACT.md` as their one-page dependency surface; a change
  that alters observable behaviour for them is a breaking change and is called
  out as such (full-gate run, ADR 0003).
- The contract's `## Frozen invariants` section is renamed `## Guaranteed
  invariants`; the status banner records the dates (frozen 2026-06-08, unfrozen
  2026-06-10) and the new governance inline.

Net: **keep the gate, drop the seal.**

## Consequences

- `+` A deferred engine-native regime (nonlinear `D(u)`, 2-D, explicit stepping)
  can be built directly into the engine when a consumer needs it, instead of
  being approximated by a consumer-side stateful closure (the v1.3 `D(N)`
  pattern) or blocked on ADR ceremony.
- `+` The contract stops over-promising immutability it never needed: the
  "ADR + re-seal for any change" clause was never exercised across v1.1–v1.4.
- `−` Consumers lose the hard guarantee that the surface *cannot* move. Mitigated
  by the retained test-gate, the "don't silently break a consumer" rule, and the
  full-gate-on-push CI (ADR 0003) that re-runs every consumer's suite on an
  engine edit.
- `−` "Frozen-engine" language is now scattered through the repo's prose
  (module docstrings, the plan, READMEs) and the build-history memories. Present-
  tense engine descriptions are corrected; the historical build narratives that
  describe what was true *when written* are left as the record (rewording them
  would rewrite history).

## Alternatives considered

- **Keep the freeze; amend per-regime via ADRs as designed.** Rejected: the
  ceremony was never needed across four versions, and it actively discourages the
  one thing the freeze's own "Not in v1" list anticipates — growing a deferred
  regime into the engine.
- **Unfreeze by deleting the contract's governance clause with no record.**
  Rejected: an unexplained `ACTIVE` banner is exactly what a future reader trips
  on. This ADR + the dated banner carry the *why*.
- **Drop the test-gate too (fully open engine).** Rejected outright: the suite is
  the engine's entire trustworthiness. Unfreezing removes immutability, not
  validation.

## Follow-up — contract framing retired (2026-06-14)

This ADR took the engine from *frozen + ADR-gated* to *open + test-gated* but
kept the **"contract"** framing — the `CONTRACT.md` banner, the
"= the contract" invariants heading, the "load this one page" / "the seal"
language in the engine README, and the consumers'-dependency-surface promise.

That framing is now dropped: `engines.diffusion` is treated as a plain tested
library. The present-tense contract language was demoted to ordinary reference
docs (`CONTRACT.md` retitled and re-bannered but kept at the same path so links
don't break; engine README + `__init__` + the engine test comments reworded).
**The test-gate is unchanged** — the suite still gates every edit; this drops
the remaining *ceremony*, not the *validation*, continuing this ADR's own
"keep the gate, drop the seal" direction one step further.

Left untouched as historical record (rewording them would rewrite history, per
this ADR's "no record" alternative and its `−` consequence on scattered prose):
ADR 0001's frozen-`CONTRACT.md` language, this ADR's own decision text above,
the build-narrative memories, the plan's dated build entries, and the
consumer-side build narratives (e.g. `chip/coupling.py`'s v1.2 finding).
