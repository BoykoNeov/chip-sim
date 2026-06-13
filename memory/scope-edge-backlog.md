---
name: scope-edge-backlog
description: "scope-edge backlog doc (docs/plans/scope-edge-backlog.md) — the bag of named-but-unbuilt edges across the whole line, triaged by CONSUMER (promote-or-defer each); spine is the deferrals. Next build = oxygen/thermal donors then under-etch."
metadata:
  node_type: memory
  type: project
---

**project (2026-06-14):** Built `docs/plans/scope-edge-backlog.md` — a home + a **build verdict each**
for the bag of named scope edges accumulated across the line (the user's "plan for those and consumers"
ask). **The organizing spine is the CONSUMER, not a feature list** (advisor): the repo's load-bearing
discipline is *no regime without a named consumer* (the v1.6 "build explicit, not 2-D" lesson, restated
in [[fab-game-cg2]]/[[fab-game-cg3]] and in `etch_deposition.py`'s own refusal to build CMP), so the
doc's primary content is **the deferrals** — which edges have no consumer yet and stay fenced. A uniform
"how to build all ten" roadmap would have betrayed that bar.

**The triage (each consumer verified in code before asserting "promotable"):**
- **PROMOTABLE — build next:** **(C1) oxygen/thermal donors** — strongest; TD compensate p-substrate →
  shift net `N_A` → `V_t`/resistivity via the **confirmed G4a chain** (`device.py` reads `N_A` through
  `fermi_potential`/`flatband_voltage`/`Q_dep`); closed-form kinetics, no engine. **(D1) under-etch** —
  `etch_deposition.py` literally says "under-etch is named, not modelled"; residual/bridge → functional
  kill (the G5 void's yield channel); cheap G5-tier completion. Bundle C1+D1.
- **PROMOTABLE (corner):** **(A1) CG-2 interstitial→dislocation/leakage** — mirror of the vacancy side,
  feeds `lifetime.py`'s generation-leakage channel (`1/τ += C·ρ_disl`); but realistic CZ is vacancy-rich
  (ξ≈0.29) so it only bites at slow pull → symmetry, not main-line.
- **COUPLED — one build, §8-bounded:** **(A2) OSF ring + Robin-mode `G(r)`** are the SAME build — the
  ring is where `ξ(r)=ξ_t`, which needs a radial `G(r)`, which the engine's shipped Robin heat mode
  sources; consumer = edge-vs-center yield non-uniformity. **Promotable only as 1-D radial `G(r)`** —
  §8 says across-wafer is a per-die field NOT a full-wafer PDE. This is where Robin-`G` finally gets a
  consumer (standalone Robin-`G` still has none).
- **DEFERRED — no consumer (the point):** A3 striations (game-layer variance feed at most, not a chip
  triad), A4 facets/curvature (nothing reads interface *shape* — A2 gets `G(r)` from the heat field not
  the shape), A5 transient Stefan `X(t)` (the canonical anti-over-build — quasi-steady balance already
  built in CG-3 suffices; nothing reads `X(t)`; would need an engine+ADR), B1 engine 3-D (no 3-D device
  consumer — **trigger recorded**: corner/narrow-width/FinFET; the v1.6→v1.8 wait-for-the-consumer
  lesson verbatim), D2 CMP (`etch_deposition.py` already refuses it — nothing reads layer thickness;
  **split from under-etch** though the user grouped them), D3 package rebond (`recipe.py:295` "named,
  deferred edge" → a **game-layer rework rule** mirroring `rework_litho`, NOT a `chip/` triad).

**Citation discipline (advisor):** for unbuilt items the doc names the model *class* + *kind* of source
+ a "pin at build" flag — NO confabulated volume:page citations (e.g. thermal donors → "Kaiser–Frisch–
Reiss-class kinetics, exact ref pinned at build"). Docs-only change, no code/tests touched. Pointer
added from `fab-game.md` §6a. [[engine-unfrozen]] [[fab-game-cg2]] [[fab-game-cg3]] [[fab-game-g4]]
[[fab-game-g4b]] [[fab-game-g5]] [[fab-game-g6]]
