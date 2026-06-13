# Scope-edge backlog — the named-but-unbuilt edges, triaged by consumer

## Context

Across the build records this repo fences each new module's frontier with **named
scope edges** — phenomena it deliberately did *not* model, parked with a note. By
2026-06-14 a bag of them has accumulated, named across the crystal-growth deepenings
(`docs/plans/fab-game.md` §6a; memories [[fab-game-cg2]], [[fab-game-cg3]]), the engine
([[engine-unfrozen]]), and the mid/back-line process tiers ([[fab-game-g5]], [[fab-game-g6]]).

This doc gives that bag a home and a **build verdict each** — but its spine is not
"how to build all of them." The repo's load-bearing discipline is **no regime without a
named consumer** — the v1.6 "build explicit, *not* 2-D" lesson (an unused regime is an
unvalidated API guess), restated in the CG-2 and CG-3 records and in `etch_deposition.py`'s
own refusal to build CMP. So the primary content here is the **NO's**: which edges honestly
have no device/yield consumer and therefore **stay deferred**. A uniform roadmap that
promised all ten would betray exactly the bar these edges were fenced under.

Each entry carries five fields: **model class** (what physics, what *kind* of source — exact
citations are pinned *at build*, never confabulated here); **consumer** (the device or yield
*observable* that would read it — or "none"); **triad tier** (which legs would be tight vs
flagged, in the established honesty ladder); **engine/ADR** (does it touch `engines/diffusion`
or warrant a decision record); and the **verdict** (PROMOTABLE / COUPLED / DEFERRED, with why).

---

## The triage at a glance

The consumer column is the one that decides everything else.

| # | Edge | Origin | Consumer observable | Verdict |
|---|------|--------|--------------------|---------|
| C1 | **Oxygen / thermal donors** | new front-of-line | `V_t` / resistivity via net doping (G4a chain) | **PROMOTABLE — build first** |
| D1 | **Under-etch** | G5 (`etch_deposition.py`) | residual/bridge → functional kill (yield) | **PROMOTABLE** |
| A1 | **CG-2 interstitial → dislocation/leakage** | §6a CG-2 | reverse leakage via `lifetime.py` (G4b) | **PROMOTABLE (corner)** |
| A2 | **OSF ring (radial) + Robin-mode `G(r)` sourcing** | §6a CG-2 | edge-vs-center yield non-uniformity | **COUPLED — one build, §8-bounded** |
| A3 | **Striations** | §6a CG-1/CG-2 | none as a killer; at most a variance feed | DEFERRED (game-layer at most) |
| A4 | **CG-3 facets / interface curvature** | §6a CG-3 | none reads it | DEFERRED (no consumer) |
| A5 | **Transient Stefan front `X(t)`** | §6a CG-3 | none reads it; quasi-steady balance suffices | DEFERRED (engine-physics, no consumer) |
| B1 | **Engine 3-D regime** | [[engine-unfrozen]] | none (device is 1-D depth + 2-D x-section) | DEFERRED (record the trigger only) |
| D2 | **CMP / dishing / planarity** | G5 (`etch_deposition.py`) | weak — nothing reads layer thickness | DEFERRED (no consumer) |
| D3 | **Package rebond** | G6 (`recipe.py:295`) | rework accounting | DEFERRED → game-layer rework rule |

---

## Group A — Crystal-growth follow-ons (the §6a cluster)

### A1 — CG-2 interstitial-side dislocation / leakage cost  ·  PROMOTABLE (corner case)

- **Model class.** CG-2 ([[fab-game-cg2]]) wired only the *vacancy* side of the Voronkov
  criterion (`ξ > ξ_t` → voids/COPs → gate-oxide-integrity kill). The mirror side `ξ < ξ_t`
  (slow pull / steep `G`) grows **interstitial-rich** silicon → dislocation loops, an A/B-swirl
  defect population. The model is a second criterion-gated density `ρ_disl(ξ_t − ξ)` symmetric to
  the existing `void_defect_density`, feeding a *recombination/generation* term, not a particle
  count. Voronkov 1982 is **already cited** for the regime split; the dislocation→leakage
  coefficient is a new house/flagged number — pin the lifetime-degradation magnitude at build.
- **Consumer.** **Confirmed wired-able:** `lifetime.py` (G4b) already computes generation-limited
  reverse leakage `J_gen ∝ 1/τ` from a defect population (today: metal traps via `recombination_rate`).
  A dislocation term adds `1/τ += C·ρ_disl` — same channel, new contributor. The device observable
  is reverse leakage / off-state current, exactly G4b's killer.
- **Triad tier.** Same flagged-phenomenology tier as CG-2: tight = the definitional regime flip at
  `ξ = ξ_t` (the legit limit leg) and zero-above-threshold by construction; flagged = the
  dislocation→`τ` coefficient. No conservation law (like CG-2/G5).
- **Engine/ADR.** None — algebraic, consumer-side, like CG-2.
- **Verdict.** **PROMOTABLE but a corner.** Honest magnitude (the CG-2 finding): realistic CZ sits
  at `ξ ≈ 0.29 > ξ_t` → *vacancy*-rich, so the interstitial side only bites at deliberately slow
  pull or an over-steep `G`. It completes the criterion's symmetry and gives slow-pull a cost (today
  slow pull is free on yield), but it is not the main-line lever. Cheap; build after the higher-value
  items unless symmetry is wanted for its own sake.

### A2 — OSF ring (radial pattern) + Robin-mode `G(r)` sourcing  ·  COUPLED — one build

- **Model class.** Two of the user's named edges are **the same build**. The oxidation-induced
  stacking-fault (OSF) ring is the thin annulus where `ξ(r) = ξ_t` — the V/I boundary — which can
  only appear if `G` (hence `ξ = V/G`) **varies with wafer radius**. Sourcing a radial `G(r)` is
  exactly what the engine's **already-shipped Robin heat mode** is for (`engines/diffusion`'s `Robin`
  convective BC + heat mode; `test_robin_heat.py`) — a 1-D radial conduction/convection solve gives
  `G(r)`, which feeds `ξ(r)` and lights the ring where it crosses `ξ_t`. This is where Robin-mode
  *finally earns a consumer*; standalone "Robin-`G` sourcing" (CG-2's separate note) still has none.
- **Consumer.** Edge-vs-center **yield non-uniformity** on the existing per-die map: the ring is a
  radial band of `ξ ≈ ξ_t` (mixed defect) flanked by vacancy (center) and interstitial (edge)
  zones, so killer density varies by die radius → the wafer map shows a ring of degraded dies. Reads
  through the same G3 Poisson map ([[fab-game-g3]]) keyed on each die's radial position.
- **§8 boundary — name it loudly.** `fab-game.md` §8: the across-wafer map is *"a per-die parameter
  field, not a full-wafer PDE."* So this is promotable **only as a 1-D radial `G(r)` profile** sampled
  per die by radius — **not** a 2-D wafer PDE. Crossing into a true 2-D thermal-field solve would
  break §8 and needs its own decision.
- **Triad tier.** Tight = the ring *location* is the definitional `ξ(r) = ξ_t` crossing (pure `ξ_t`,
  coefficient-robust) + the Robin/heat-mode `G(r)` inherits the engine's validated heat invariants;
  flagged = the radial `G(r)` magnitude (hot-zone profile) and the ring *width*.
- **Engine/ADR.** No new engine physics (Robin heat mode exists). No ADR unless a dedicated 2-D
  thermal solve is added — which §8 says don't.
- **Verdict.** **COUPLED, promotable as the richest crystal-growth deepening** once edge-vs-center
  non-uniformity is wanted — but build it as 1-D radial, honoring §8. Higher value than A1 (it ties
  heat, pull, defect *and* spatial pattern into one mechanism) but more design surface (the per-die
  radial-position plumbing).

### A3 — Striations  ·  DEFERRED (game-layer at most)

- **Model class.** Rotational/convective micro-fluctuations of the interface growth rate → periodic
  dopant micro-segregation bands (resistivity striations). Model class: a time-periodic modulation of
  the BPS boundary layer δ(t) → `k_eff(t)` ripples on the CG-1 axial profile. Pin a striation-in-CZ
  reference at build.
- **Consumer.** **None as a killer.** Striations are a fine-scale *variance*, not a yield-killing
  defect and not a device-spec failure at this model's granularity. At most they feed a resistivity
  micro-variation into the **`fab_game` variation layer** (per ADR 0005, the stochastic spread lives
  in the game layer, not as a cited `chip/` triad).
- **Engine/ADR.** None.
- **Verdict.** **DEFERRED as physics.** If ever built, it belongs in `fab_game/variation.py` as a
  reproducible noise feed, not as a `chip/czochralski.py` triad — there is no tight leg to anchor and
  no killer consumer.

### A4 — CG-3 facets / interface curvature  ·  DEFERRED (no consumer)

- **Model class.** The solid-liquid interface is not flat: facets at preferred crystallographic
  planes and overall curvature from the radial thermal field. CG-3 ([[fab-game-cg3]]) built the
  **1-D** quasi-steady Stefan balance and explicitly deferred facets/curvature.
- **Consumer.** **None reads interface shape.** CG-2's `G` (the only Stefan consumer) takes the
  scalar interface gradient, already supplied. Curvature would matter for A2's radial `G(r)`, but A2
  gets `G(r)` from the Robin heat field, not from interface shape — so even A2 does not need this.
- **Engine/ADR.** Would be genuinely 2-D interface geometry — engine-adjacent.
- **Verdict.** **DEFERRED — the canonical physics-for-its-own-sake risk.** No observable reads it.
  Stays fenced until something downstream needs the interface *shape* (not just its gradient).

### A5 — Transient Stefan front `X(t)`  ·  DEFERRED (engine-physics, no consumer)

- **Model class.** The full free-boundary (Stefan) problem — the interface position `X(t)` advancing
  against the latent-heat flux jump `L·ρ·dX/dt = k_s·∂T/∂x|_s − k_l·∂T/∂x|_l`. This is the one CG
  item that is **genuine new engine physics** (a moving boundary with a phase-change source; the
  parabolic engine's BCs are fixed-domain).
- **Consumer.** **None.** CG-3's own finding: nothing reads `X(t)`; the only consumer (CG-2's `G`)
  needs the **quasi-steady interface balance**, which CG-3 already built closed-form. The v1.2 oxide
  receding-mesh precedent ([[chip-coupling-v12]]) shows moving boundaries can be done consumer-side
  *when a consumer exists*.
- **Engine/ADR.** Would likely warrant an **engine amendment + ADR** (a Stefan moving-boundary mode).
- **Verdict.** **DEFERRED — the textbook anti-over-build case.** Build only when a device/yield
  outcome needs the *transient front* itself (e.g. a fast-transient pull-rate ramp whose striation or
  micro-defect signature a consumer reads). Until then, the quasi-steady balance is sufficient and
  building the free-boundary solver would be an unvalidated engine API with no caller.

---

## Group B — Engine regime

### B1 — Engine 3-D regime  ·  DEFERRED (record the trigger, don't build)

- **Model class.** `engines/diffusion` has 1-D (v1.1) and 2-D (v1.8) parabolic solvers; **3-D is the
  only remaining deferred regime** ([[engine-unfrozen]]). A 3-D build is a tensor-product extension of
  the 2-D 5-point FV to a 7-point stencil — mechanically known, but a large surface (sparse 3-D
  assembly, `splu` scaling, a 3-D masked BC).
- **Consumer.** **None today.** The device stack is 1-D depth (`device.py`) + 2-D cross-section
  (`device_2d.py`, [[chip-device-2d-v111]]). Nothing reads a 3-D dopant field.
- **Engine/ADR.** Engine amendment, full-gate; ADR 0004 pre-authorizes test-gated engine regimes, so
  likely no *new* ADR, but a large amendment.
- **Verdict.** **DEFERRED — verbatim the v1.6→v1.8 lesson.** 2-D waited for its real consumer
  ("lateral diffusion under a mask edge") and was built the moment it arrived; 3-D waits the same way.
  **Record the trigger so it is named, don't plan the build:** a 3-D consumer would be a *corner /
  narrow-width / FinFET-style* device geometry where the dopant field is non-separable in all three
  axes (e.g. corner rounding of a S/D junction, or width-dependent `V_t` from a 3-D depletion corner).
  When such a device deepening is proposed, 3-D becomes its prerequisite — not before.

---

## Group C — Front-of-line new physics

### C1 — Oxygen / thermal donors  ·  PROMOTABLE — the strongest candidate, build first

- **Model class.** CZ silicon dissolves interstitial oxygen `[O_i]` from the quartz crucible;
  subsequent low-temperature anneals (~450 °C) nucleate **thermal donors** — oxygen clusters that act
  as *shallow donors*, adding n-type carriers. Model class: an oxygen-solubility term (oxygen
  incorporated during growth, a function of pull/rotation/melt) + a thermal-donor formation kinetics
  law (TD density rising with anneal time and a power of `[O_i]`). **Citations to pin at build:** a
  standard oxygen-solubility-in-CZ-Si reference and a thermal-donor-formation-kinetics reference
  (Kaiser–Frisch–Reiss-class kinetics) — *named as a class here, exact volume/page pinned at build,
  not confabulated.*
- **Consumer.** **Confirmed strongest.** `device.py`'s `V_t` reads net substrate doping `N_A`
  through `fermi_potential(N_A)`, `flatband_voltage(N_A)`, and `Q_dep = √(2qε_Si·N_A·2φ_F)`. Thermal
  donors are n-type → they *compensate* a p-substrate → shift effective `N_A` → shift `V_t` and
  resistivity. This is exactly the established **G4a `Na → net-doping → V_t` chain**
  ([[fab-game-g4]]) — a contaminant/defect that becomes a device consequence net doping can carry.
  The boule's `N_A` already flows from `czochralski.py`, so a TD term perturbs it in place.
- **Triad tier.** Tight = the clean limit (`[O_i] = 0` or no anneal ⇒ TD = 0 ⇒ `N_A` and `V_t`
  unchanged, the seam) + the compensation algebra (`N_net = N_A − N_TD`, exact); flagged = the TD
  formation magnitude and the oxygen-incorporation number (the loose/cited leg, like the metal
  device-degradation magnitudes in G4a/G4b).
- **Engine/ADR.** None — closed-form kinetics, consumer-side, like Scheil / Deal–Grove.
- **Verdict.** **PROMOTABLE — build first.** It is a clean, citable front-of-line physics module
  with a *confirmed* device consumer through the existing V_t chain, no engine touch, and it deepens
  the crystal-growth story on the *electrical* axis (CG-1/2/3 covered doping-profile, defects, and
  the interface; thermal donors are the missing oxygen/resistivity consequence). Highest value-to-cost
  in the bag.

---

## Group D — Mid/back-line process

### D1 — Under-etch  ·  PROMOTABLE

- **Model class.** `etch_deposition.py` (G5, [[fab-game-g5]]) built the **over**-etch leg
  (anisotropy → bias → CD shrink) and explicitly named under-etch as the unbuilt mirror: incomplete
  etch (etch depth < film thickness, e.g. low over-etch on a non-uniform film) leaves **residual film
  / stringers / bridges** between features. Model class: residual = `max(0, h − d_etched)` with a
  bridge/short criterion when residual spans the gap. Forms are textbook (Wolf & Tauber /
  Plummer–Deal–Griffin class, **already the cited basis** of the etch module); magnitudes flagged.
- **Consumer.** **Confirmed real.** A residual bridge is a **functional kill** — the same yield
  channel G5 already uses for the deposition keyhole void (a die that fails functionally). Plugs into
  the existing functional-fail path; no new machinery.
- **Triad tier.** Flagged-phenomenology, exactly the G5 tier: tight = the seam (full clear ⇒ zero
  residual ⇒ no bridge, by construction) + the residual algebra; flagged = the bridge-threshold
  magnitude. No conservation law (G5 has none).
- **Engine/ADR.** None.
- **Verdict.** **PROMOTABLE — the cheap completion.** It closes G5's named "over/under-etch" pair,
  adds a second etch failure mode (today only over-etch CD-shrink and void exist), and reuses the
  functional-kill consumer. Build after C1; together they are two quick, high-confidence deepenings.

### D2 — CMP / dishing / planarity  ·  DEFERRED (no consumer)

- **Model class.** Chemical-mechanical planarization — Preston's-equation-class removal rate +
  pattern-density-dependent **dishing/erosion** → post-CMP thickness non-uniformity.
- **Consumer.** **Weak/none — the code already says so.** `etch_deposition.py` (line ~64) explicitly
  refuses CMP: *"Building a CMP physics module here would be physics for its own sake (the repo's
  anti-over-build bar)."* Confirmed: nothing in the device or yield path reads a *layer thickness* as
  an observable — `device.py` reads `t_ox` (set by Deal–Grove, not CMP) and CD, not an interconnect
  layer thickness. **The user grouped CMP with under-etch, but they split:** under-etch has the
  functional-kill consumer (D1); CMP has none.
- **Engine/ADR.** None.
- **Verdict.** **DEFERRED.** Promotable only if a future deepening makes a planarized layer thickness
  an electrical observable (e.g. an interconnect RC or a depth-of-focus budget that reads post-CMP
  topography). Until that consumer exists, it stays fenced — by the module's own decision.

### D3 — Package rebond  ·  DEFERRED → game-layer rework rule (not a chip triad)

- **Model class / nature.** Re-bonding / re-attaching a die after a failed assembly step. `recipe.py`
  (line 295) names it: cracked-die scrap is irreversible, *"rebond is a named, deferred edge."* This
  is **not cited `chip/` physics** — it is a **rework policy**: an allowed second attempt at the
  assembly/bond step with its own recovery odds and cost.
- **Consumer.** The `fab_game` **rework accounting** — the same machinery as `rework_litho`
  (`pipeline.py`: dies reworked, recovered, the bookkeeping invariant that die totals are conserved)
  and the `REWORK_COSTS` scoring channel (`scoring.py`). The observable is recovered-die count and
  the profit hit.
- **Engine/ADR.** None. It is **game-layer**, governed by ADR 0005's mechanics-invariant discipline
  (determinism, bookkeeping closes), **not** a cited triad.
- **Verdict.** **DEFERRED → build as a game rework rule when wanted**, mirroring `rework_litho`:
  a `rework_bond` path that re-attempts assembly on failed dies, with recovery probability and
  `REWORK_COSTS["bond"]`, tested for the bookkeeping invariant (totals conserved, accounting closes)
  — **no physics triad**. Keep it out of `chip/`.

---

## Recommended sequencing

Promote in **consumer strength × cost** order; everything else stays deferred and named.

1. **C1 — Oxygen / thermal donors.** Strongest consumer (V_t/resistivity via the G4a chain), clean
   citable kinetics, no engine touch. The one to build next.
2. **D1 — Under-etch.** Cheap G5-tier completion, reuses the functional-kill consumer. Bundle with C1
   as two quick, high-confidence deepenings.
3. **A1 — CG-2 interstitial → leakage.** Completes Voronkov's symmetry through the `lifetime.py`
   leakage channel — but a corner (realistic CZ is vacancy-rich), so value is symmetry, not main-line.
4. **A2 — OSF ring + Robin-`G(r)`.** The richest crystal-growth deepening (heat + pull + defect +
   spatial pattern in one), gated by the §8 "1-D radial, not 2-D wafer PDE" boundary and the per-die
   radial-position plumbing. Build when edge-vs-center non-uniformity is the wanted story.

**Stay deferred (no consumer — this is the point, not a backlog of work):** A3 striations (game-layer
variance at most), A4 facets/curvature (nothing reads shape), A5 transient Stefan `X(t)` (quasi-steady
suffices), B1 engine 3-D (no 3-D device — trigger recorded), D2 CMP (no thickness observable), D3
rebond (game rework rule, not physics). Each is fenced behind a *named consumer that does not yet
exist*; promoting any of them without that consumer would be the unvalidated-API guess the gate exists
to catch.

---

*Cross-refs:* `docs/plans/fab-game.md` §6a (CG cluster), §8 (across-wafer ceiling); ADR 0005
(`docs/decisions/0005-fab-game-layering.md`, the physics/game layer split); ADR 0004 (engine
governance). Memories: [[fab-game-cg2]], [[fab-game-cg3]], [[engine-unfrozen]], [[fab-game-g4]],
[[fab-game-g4b]], [[fab-game-g5]], [[fab-game-g6]], [[chip-device-2d-v111]].
