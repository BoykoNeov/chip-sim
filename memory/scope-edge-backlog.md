---
name: scope-edge-backlog
description: "scope-edge backlog doc (docs/plans/scope-edge-backlog.md) — the bag of named-but-unbuilt edges across the whole line, triaged by CONSUMER (promote-or-defer each); spine is the deferrals. C1 thermal-donors + D1 under-etch + A1 interstitial→leakage + A2 OSF ring all BUILT (2026-06-14). A2 SPLIT: ring BUILT (closed-form), Robin-G FALSIFIED. E1 SPLIT (→ [[fab-game-e1]]): the D(t) thermal-budget path BUILT, the emergent-T heat-mode clause FALSIFIED (√(D/α)≈1e-6 → T is the setpoint over the junction; joins Robin-G). BACKLOG NOW EXHAUSTED — Next promotable = NONE; no chip-side heat-mode consumer → heat-mode Steel-only."
metadata: 
  node_type: memory
  type: project
  originSessionId: e06638ba-b41b-4350-a5e3-109ddf86c5ad
---

**project (2026-06-14):** Built `docs/plans/scope-edge-backlog.md` — a home + a **build verdict each**
for the bag of named scope edges accumulated across the line (the user's "plan for those and consumers"
ask). **The organizing spine is the CONSUMER, not a feature list** (advisor): the repo's load-bearing
discipline is *no regime without a named consumer* (the v1.6 "build explicit, not 2-D" lesson, restated
in [[fab-game-cg2]]/[[fab-game-cg3]] and in `etch_deposition.py`'s own refusal to build CMP), so the
doc's primary content is **the deferrals** — which edges have no consumer yet and stay fenced. A uniform
"how to build all ten" roadmap would have betrayed that bar.

**The triage (each consumer verified in code before asserting "promotable"):**
- **✅ BUILT (2026-06-14):** **(C1) oxygen/thermal donors** → [[fab-game-c1]] (cited KFR fourth-power
  rate; TD compensate p-substrate → net `N_A` → `V_t` via the G4a chain; czochralski.py §1e). **(D1)
  under-etch** → [[fab-game-d1]] (residual=UE·film → bridge SHORT, mirror of the void's open; etch_deposition.py
  §3). Bundled as the two quick deepenings. **Next promotable = A1.**
- **(original triage, for the deferrals' rationale):** C1/D1 were the PROMOTABLE-build-next pair — strongest
  + cheapest consumers; now built (above).
- **PROMOTABLE (corner):** **(A1) CG-2 interstitial→dislocation/leakage** — mirror of the vacancy side,
  feeds `lifetime.py`'s generation-leakage channel (`1/τ += C·ρ_disl`); but realistic CZ is vacancy-rich
  (ξ≈0.29) so it only bites at slow pull → symmetry, not main-line.
- **SPLIT on verification (2026-06-14):** **(A2) OSF ring + Robin-mode `G(r)`** were asserted as ONE
  build ("Robin-`G` finally earns a consumer") — verified-at-build, the second clause is **FALSE**, so
  they split. **The ring = ✅ BUILT → [[fab-game-a2]]** ("CG-2 made radial", closed-form): radial `G(r)`
  (flagged house profile) → `ξ(r)=V/G(r)` → ring where `ξ(r)=ξ_t` → per-die killer density keyed on
  `radius_frac` (consumer = edge-vs-center yield non-uniformity; `scatter_defects` gained a `density_fn`).
  Tight = ring *location* (coefficient-robust) + topology signs; flagged = `G(r)` magnitude, ring width,
  **and the ring's existence itself** (pure house number — the CG-1/CG-2 honest-magnitude pattern). THE
  finding: monotone `void_density` → COP-degraded vacancy core (modest) + clean rim, NOT a ring of kills. §8-bounded to
  1-D radial. **Robin-`G` sourcing = DEFERRED, premise FALSIFIED:** Voronkov reads a STEADY gradient →
  closed-form; the shipped engine can't beat it (verified in `diffusion1d.py`: `source` is `S(x,t)`
  field-INDEPENDENT → no fin sink → steady radial profile is a straight LINE; no advection; Cartesian
  `D_face/dx`, no cylindrical `1/r`). The "engine T(r)==slab" tight leg would be proof of REDUNDANCY.
  Escapes both walls (2-D=§8, cylindrical/sink term=over-build). **Heat mode's native consumer is the
  STEEL program** (`test_robin_heat.py`: Jominy/quench). THE RULE: heat-mode beats a closed form only for
  a *transient* (k(T)/time-dep BC/layered/coupled) problem, never a steady gradient. [[engine-unfrozen]]
- **DEFERRED — no consumer (the point):** A3 striations (game-layer variance feed at most, not a chip
  triad), A4 facets/curvature (nothing reads interface *shape* — the ring gets `G(r)` from a closed-form
  profile, not from interface shape), A5 transient Stefan `X(t)` (the canonical anti-over-build —
  quasi-steady balance already built in CG-3 suffices; nothing reads `X(t)`; would need an engine+ADR),
  B1 engine 3-D (no 3-D device consumer — **trigger recorded**: corner/narrow-width/FinFET; the v1.6→v1.8
  wait-for-the-consumer lesson verbatim), D2 CMP (`etch_deposition.py` already refuses it — nothing reads
  layer thickness; **split from under-etch** though the user grouped them), D3 package rebond
  (`recipe.py:295` "named, deferred edge" → a **game-layer rework rule** mirroring `rework_litho`, NOT a
  `chip/` triad), **Robin-`G` heat-mode sourcing (premise FALSIFIED 2026-06-14 — a steady gradient is
  closed-form; the engine can't earn its place; home = the Steel program)**, and **E1's emergent-`T`
  heat mode (premise FALSIFIED 2026-06-14 → [[fab-game-e1]] — `√(D/α)≈1e-6` ⇒ `T` is the setpoint over
  the junction; building heat-mode would reproduce it = proof of redundancy).**

**E1 SPLIT/BUILT (2026-06-14) → [[fab-game-e1]]:** the verify-at-build gate ("is `T` emergent or just the
setpoint?") resolved to **SETPOINT**, so E1 splits like A2: the **`D(t)` thermal-budget path is BUILT**
(`diffusion_dopant.py` §4 `ThermalProgram`/`thermal_budget`/`drive_in_program`, the OED `effective_Dt`
twin — a faster ramp → smaller `∫D dt` → shallower `x_j`, why RTA), while the **emergent-`T` heat-mode
engine is FALSIFIED/deferred** (joins Robin-`G`). **The backlog is now EXHAUSTED: Next promotable = NONE,
and there is NO chip-side heat-mode consumer → heat-mode is Steel-program-only.**

**Citation discipline (advisor):** for unbuilt items the doc names the model *class* + *kind* of source
+ a "pin at build" flag — NO confabulated volume:page citations (e.g. thermal donors → "Kaiser–Frisch–
Reiss-class kinetics, exact ref pinned at build"). Docs-only change, no code/tests touched. Pointer
added from `fab-game.md` §6a. [[engine-unfrozen]] [[fab-game-cg2]] [[fab-game-cg3]] [[fab-game-g4]]
[[fab-game-g4b]] [[fab-game-g5]] [[fab-game-g6]]
