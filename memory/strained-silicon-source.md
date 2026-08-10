---
name: strained-silicon-source
description: F5 cited source (Intel 90 nm uniaxial strain) + the S1 chip/strain.py build — the elasticity DEFINITION trap and the refusal that keeps the sign honest
metadata: 
  node_type: memory
  type: reference
  originSessionId: 82b0b8df-dd36-4ed3-8f62-b0e9237cd6a0
  modified: 2026-08-10T07:32:11.381Z
---

**The source (web-verified 2026-08-10, both legs from ONE paper — Intel 90 nm logic technology,
IEDM 2003 + the associated uniaxial-strain papers):** SiGe S/D selective epitaxy, **17% Ge** →
longitudinal **uniaxial compressive** → hole µ **>50%**, pMOS drive **+25%** (record 700/800 µA/µm at
1.2 V) · tensile silicon-nitride capping layer → **uniaxial tensile** nMOS → electron µ **+20%**, nMOS
drive **+10%** · the hole enhancement **persists at large vertical fields**. Independent second source:
**100% µ → 35% drive at L = 25 nm / W = 77 nm**. **NOT sourced at the house bar ⇒ ABSENT from the code:**
GPa per Ge%, and µ-vs-Ge% linearity. See [[strained-silicon-f5]] for the plan-level decisions.

**S1 BUILT 2026-08-10** — `chip/strain.py` + `chip/tests/test_strain.py`, `device.py` untouched (4th
consecutive slice). What the build added beyond the plan:

**The elasticity DEFINITION is the live trap** — the thing most likely to be silently wrong. Elasticity is
the ratio of **fractional gains** `(drive−1)/(µ−1)`, **not** of factors: on the nMOS pair that is
`0.10/0.20` = **0.500 exactly**, while `1.10/1.20` = **0.917** — a plausible-looking number that flatters
the model, and a test written on it would pass while asserting nothing. Both cited carriers land on
**exactly 0.500** (report as coincidence, not law); ⇒ `drive_overstatement = 1/elasticity = 2.0`.

**The bound is assertable against the REAL `device.py`, and only on the ideal-contact path.**
`saturation_current(mu_eff=MU_N_EFF·f)/saturation_current(...)` **== f exactly** — elasticity 1 by
construction — which is *why* the drive read is an upper bound. **With `R_series_ohm > 0` this fails by
design:** the source-degeneration quadratic already sub-linearizes µ→I on its own, so the elasticity-1
claim is scoped to the seam path (tested both ways).

**The refusal is the payload, not a guard rail.** `nmos_mobility()` **raises** on the hole mechanism rather
than returning 1.50 for an electron channel — a pMOS technique on n-channel would **invert the sign** while
looking like a result. Structural mirror of `interconnect.py` refusing Al on the narrow-wire axis;
`WIRED_MECHANISMS` is **derived** from the registry (the `NARROW_WIRE_METALS` pattern) so a hole leg can
never silently appear. `strained_mobility()` stays carrier-generic with a **required positional**
`mu_base` — defaulting it to `MU_N_EFF` would pair an *electron* mobility with a hole factor
([[high-k-dielectric-source]]'s incoherent-(φ_B,m*) failure).

**Gap-vs-fake-value, twice:** the seam record's `cited_elasticity`/`drive_overstatement` are **`None`**,
not `1.0` (no gain ⇒ no fraction of one to have reached the drive; `elasticity()` raises on that input);
and **there is no stress field at all** on `StrainMechanism` — a test asserts no `stress`/`gpa` field name
exists, because an empty field is how the unsourced GPa leaks back in. `ge_percent=17` is carried as cited
*data* (`None` on the CESL entry), never as a function input.

**Directions of every flag agree (all make the model's win the optimistic one):** hole µ is a cited
**floor** (">50%" stored as 1.50, never round a win up) ⇒ its 0.5 elasticity is an **upper** bound · the
25 nm point sits at **0.35** ⇒ the bound loosens as `L` shrinks · long-channel 1 is the ceiling.
