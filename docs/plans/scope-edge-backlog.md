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
| C1 | **Oxygen / thermal donors** | new front-of-line | `V_t` / resistivity via net doping (G4a chain) | **✅ BUILT (2026-06-14)** |
| D1 | **Under-etch** | G5 (`etch_deposition.py`) | residual/bridge → functional kill (yield) | **✅ BUILT (2026-06-14)** |
| A1 | **CG-2 interstitial → dislocation/leakage** | §6a CG-2 | reverse leakage via `lifetime.py` (G4b) | **✅ BUILT (2026-06-14)** |
| A2 | **OSF ring (radial `G(r)`)** + Robin-mode sourcing | §6a CG-2 | edge-vs-center yield non-uniformity | **SPLIT (2026-06-14): ring ✅ BUILT (closed-form); Robin-`G` DEFERRED (premise FALSIFIED)** |
| A3 | **Striations** | §6a CG-1/CG-2 | none as a killer; at most a variance feed | DEFERRED (game-layer at most) |
| E1 | **Transient spike/RTA anneal `T(t)` → `D(T(t))`** | heat-mode consumer search | `x_j`/`R_s` via the `∫D dt` thermal budget | **SPLIT (2026-06-14): heat-mode FALSIFIED (`√(D/α)≈1e-6` → setpoint); the `D(t)` budget path ✅ BUILT** |
| A4 | **CG-3 facets / interface curvature** | §6a CG-3 | none reads it | DEFERRED (no consumer) |
| A5 | **Transient Stefan front `X(t)`** | §6a CG-3 | none reads it; quasi-steady balance suffices | DEFERRED (engine-physics, no consumer) |
| B1 | **Engine 3-D regime** | [[engine-unfrozen]] | none (device is 1-D depth + 2-D x-section) | DEFERRED (record the trigger only) |
| D2 | **CMP / dishing / planarity** | G5 (`etch_deposition.py`) | weak — nothing reads layer thickness | DEFERRED (no consumer) |
| D3 | **Package rebond** | G6 (`recipe.py:295`) | rework accounting | DEFERRED → game-layer rework rule |

---

## Group A — Crystal-growth follow-ons (the §6a cluster)

### A1 — CG-2 interstitial-side dislocation / leakage cost  ·  ✅ BUILT (2026-06-14)

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
- **As built (2026-06-14).** `chip/czochralski.py` §1g — `dislocation_defect_density(ξ) =
  coeff·max(0, ξ_t − ξ)` (the **mirror** of `void_defect_density`, reflected across `ξ_t`;
  `DISLOCATION_DENSITY_PER_RATIO_DEFICIT_CM2` flagged) — feeds `chip/lifetime.py`'s new
  `dislocation_recombination_rate(ρ_disl) = K·ρ_disl` (`DISLOCATION_RECOMBINATION_COEFF` flagged) via
  a `dislocation_density=` kwarg on `srh_lifetime`/`device_leakage` (`1/τ += K·ρ_disl`, the **same**
  channel as the deep-level metals — a *new contributor*, not a new output). **No new game knob** —
  `CzochralskiKnobs.interstitial_dislocation_density[_at(r)]` reads the *existing* `(V, G)` and
  switches on automatically on the interstitial side; threaded to **both** `device_step` call sites
  (main + rework) keyed on `radius_frac`. **THE payoff:** the Voronkov criterion is now **two-sided** —
  too-fast costs **yield** (CG-2 COP voids), too-slow costs **leakage** (A1 dislocations), the
  defect-free optimum **at** `ξ_t` (where both densities are zero; the cited, coefficient-robust
  location). It is also **A2's deferred consumer**: the OSF interstitial **rim** (clean *of voids*) is
  dislocation-**leaky** per die → the OSF ring is the one annulus clean of *both* failure modes. Banked
  `fab_game/demo_dislocation.py` (`fab-game-a1.png`, 3 panels: two-sided window · leakage ladder with
  V_t the flat bystander · the radial void-core/leaky-rim/clean-ring map). Fast lane +20 (czochralski +3,
  lifetime +4, `test_dislocation` 8 wiring, `test_demo_dislocation` 4 — minus 1 absorbed). No engine, no ADR.
- **Verdict.** **✅ BUILT — but a corner, as predicted.** Honest magnitude (the CG-2 finding, led with):
  realistic CZ sits at `ξ ≈ 0.29 > ξ_t` → *vacancy*-rich, so the interstitial side only bites at a
  *deliberately* slow pull or an over-steep `G`. Its value is the criterion's **symmetry** (slow pull is
  no longer free on yield) and **A2's rim**, not a main-line trade-off. **Still deferred:** the
  dislocation→`τ` *magnitude* (flagged), high-injection, gettering/precipitation.

### A2 — OSF ring (radial pattern) + Robin-mode `G(r)` sourcing  ·  SPLIT on verification (2026-06-14)

> **Verified at build-time (2026-06-14) — the engine premise is FALSIFIED; A2 splits in two.** The
> backlog asserted these two named edges were *one* build because *"Robin-mode finally earns a
> consumer."* On verification against the engine code that second clause is **false**, so the build and
> the heat-mode sourcing separate. The ring is a real (closed-form) consumer; Robin-`G` stays deferred.

- **Model class.** The oxidation-induced stacking-fault (OSF) ring is the thin annulus where
  `ξ(r) = ξ_t` — the V/I boundary — which can only appear if `G` (hence `ξ = V/G`) **varies with wafer
  radius**. A radial `G(r)` → `ξ(r) = V/G(r)` → the ring lights where it crosses `ξ_t`. The original
  claim was that the engine's **already-shipped Robin heat mode** would *source* `G(r)` — see the
  falsification below.
- **Consumer.** Edge-vs-center **yield non-uniformity** on the existing per-die map: the ring is a
  radial band of `ξ ≈ ξ_t` (mixed defect) flanked by vacancy (center) and interstitial (edge)
  zones, so killer density varies by die radius → the wafer map shows a ring of degraded dies. Reads
  through the same G3 Poisson map ([[fab-game-g3]]) keyed on each die's radial position. **Real.**
- **The ring — ✅ BUILT (2026-06-14) as a CLOSED FORM ("CG-2 made radial").** `G(r)` is a **flagged house
  radial profile**, not a solve. Triad: tight = the ring *location* (`ξ(r)=ξ_t`, pure `ξ_t`,
  coefficient-robust) + the topology signs (vacancy core / interstitial edge); flagged = the `G(r)`
  magnitude, the ring *width*, and **the ring's existence itself** (a pure house number — lead with this,
  the CG-1/CG-2 honest-magnitude pattern). **No conservation leg** (matches CG-2/3), and — the correction
  — **no engine heat-invariant leg** (the engine is not used). The per-die radial-density wiring
  (`scatter_defects` taking a per-die density, the scalar path = the seam) is the sound part.
  **As built:** `chip/czochralski.py` §1f — `radial_thermal_gradient` (`G(r)=G_center·(1+boost·r²)`,
  the flagged profile), `osf_ring_radius` (the tight V/I location, coefficient-free), `radial_defect_regime`
  (the topology helper). Wired via `CzochralskiKnobs.radial_gradient_boost` (reinterprets
  `thermal_gradient_K_per_mm` as `G_center`; requires the direct-`G` + a pull; guarded against CG-3) →
  `grown_in_defect_density_at(radius_frac)` → a per-die `density_fn` in `scatter_defects` → the G3 Poisson
  map keyed on `radius_frac`. **THE finding (advisor, led with):** the reused (monotone) `void_defect_density`
  peaks at the high-ξ **centre** and is **zero at the ring**, so the map is a **COP-degraded vacancy core
  + a clean interstitial rim — NOT a ring of dead dies** (the core mortality is *modest*, the same capped
  CG-2 coefficient; the rim is *provably* clean); the ring is the *boundary* where the kills **stop**.
  Default `boost=None` ⇒ uniform ⇒ **CG-2 byte-for-byte** (the existing `test_defects`/`test_seam`/
  `test_voronkov` pass unchanged). Banked artifact `fab_game/demo_osf_ring.py` (`fab-game-a2.png`); fast
  lane +20 (czochralski +8, `test_osf_ring` 8, `test_demo_osf_ring` 4). **Still deferred:** the literal
  *degraded ring* (the OSF band's own stacking-fault **leakage** → the interstitial/`lifetime.py` channel
  = the separately-deferred **A1** edge — building it here would reach into A1's consumer = over-build).
- **Robin-`G` sourcing — DEFERRED, premise FALSIFIED (no consumer a closed form can't serve).** Voronkov
  reads a **steady** gradient, and a steady 1-D radial conduction profile is **closed-form**. The shipped
  Robin heat mode actively cannot beat it, verified in `engines/diffusion/diffusion1d.py`: (a) `source`
  is `S(x,t)`, **independent of the field `u`** — so the standard 1-D **fin** reduction (lateral loss as
  a distributed `−m²(T−T_amb)`) is inexpressible; lateral cooling enters only at the single rim face → the
  steady radial profile is a straight **line**; (b) **no advection** (the pull rate never enters); (c)
  Cartesian transmissibility `D_face/dx` with **no cylindrical `1/r`** weighting. A planned "tight leg" of
  *engine `T(r)` == analytic slab profile* would be **proof of redundancy** — validating the solver
  against an answer you can write directly. Both escapes are walls: a true 2-D `(r,z)` solve is fenced by
  §8; a cylindrical/sink engine term is an amendment = over-build. **The heat mode's native consumer is
  the Steel program** (`test_robin_heat.py`: *"the lumped-capacitance / Jominy validation belongs to the
  Steel Phase-2 triad, not here"*); chip-sim shares the engine and has **correctly declined** to
  manufacture a chip-side consumer. **The rule this verifies:** heat-mode beats a closed form only for a
  *transient* problem (`k(T)` / arbitrary time-dependent BC / layered media / field coupling) — **never a
  steady gradient.** The one chip-side candidate meeting that bar is **E1**.
- **§8 boundary (unchanged).** The ring is promotable **only as a 1-D radial `G(r)` sampled per die by
  radius** — *not* a 2-D wafer PDE (`fab-game.md` §8). A true 2-D thermal-field solve would break §8.
- **Engine/ADR.** None — the ring is consumer-side closed form (the engine is retired as decorative).
- **Verdict.** **SPLIT (2026-06-14):** ring **✅ BUILT (closed-form, "CG-2 made radial")** → per-die OSF
  non-uniformity (edge-vs-center yield); Robin-`G` sourcing **DEFERRED — premise falsified** (a steady
  gradient is closed-form; the engine cannot earn its place; its home is the Steel program).

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
  scalar interface gradient, already supplied. Curvature would matter for A2's radial `G(r)`, but A2's
  ring gets `G(r)` from a **closed-form house profile** (the Robin-heat-field sourcing was falsified —
  see A2), not from interface shape — so even A2's ring does not need this.
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

### C1 — Oxygen / thermal donors  ·  ✅ BUILT (2026-06-14)

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
- **Verdict.** **✅ BUILT (2026-06-14).** `chip/czochralski.py` §1e — `thermal_donor_density`
  (saturating exponential), `thermal_donor_formation_rate` (the **cited Kaiser–Frisch–Reiss fourth-power
  initial rate `∝[O_i]⁴`**, Phys. Rev. 112, 1546, 1958 — verified before pinning), `thermal_donor_saturation`
  (flagged cube law `∝[O_i]³`), `net_doping_after_donors` (exact `N_A−N_TD` compensation + a type-inversion
  guard). Triad shape = the flagged-phenomenology tier (no conservation law): tight = the **seam** (no
  oxygen *or* no anneal ⇒ `N_TD=0` exact, by both paths) + the exact compensation algebra; the **one cited
  direction** is the fourth-power rate; the saturating form, the cube exponent, and every magnitude are
  flagged house numbers (do **not** borrow Scheil's anchors). Wired into `fab_game` via `CzochralskiKnobs`
  (`oxygen_conc_cm3`/`thermal_donor_anneal_min`, both opt-in → the seam) → `Recipe.effective_channel_N_A`
  → the existing G4a `V_t` chain; `diagnose` names the donor compensation. Banked artifact
  `fab_game/demo_thermal_donors.py` (`fab-game-c1.png`). The crystal-growth story's *electrical* axis
  (CG-1/2/3 covered doping-profile, defects, the interface). **Still deferred:** `[O_i]=f(pull/rotation/melt)`,
  the higher-T "new donor"/precipitation regimes, type inversion (a guarded named edge).

---

## Group D — Mid/back-line process

### D1 — Under-etch  ·  ✅ BUILT (2026-06-14)

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
- **Verdict.** **✅ BUILT (2026-06-14).** `chip/etch_deposition.py` §3 — `under_etch_residual`
  (`residual = UE·film`, exact, seam at `UE=0`), `residual_bridges` (a flagged absolute threshold), and
  the `under_etch` → `UnderEtchResult` bundle (mirroring `deposit_fill`). Triad = the G5 flagged tier:
  tight = the seam (`UE=0` ⇒ residual 0 bit-for-bit) + the residual algebra (a guard); the bridge
  threshold magnitude is house, only the "thicker residual → a continuous short" direction is cited.
  Wired via `EtchDepositionKnobs.under_etch_frac` (opt-in; a `__post_init__` guard makes over/under-etch
  mutually exclusive), a `Die.bridged` field, the `spec.verdict` functional-fail gate (parallel to
  `voided`), and a `diagnose` fingerprint. Banked artifact `fab_game/demo_under_etch.py`
  (`fab-game-d1.png`) — the residual cliff + the **etch process window** (a Goldilocks window bracketed
  by an under-etch *short* and an over-etch CD-collapse *open*). Closes G5's named "over/under-etch" pair
  — a second etch failure mode (a *short*; the void is an *open*) reusing the functional-kill consumer.

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

## Group E — Thermal-transient (the heat-mode consumer search)

This group exists because A2's verification (above) asked a sharper question than "build the OSF ring":
**does the shipped Robin/heat-mode engine have *any* chip-side consumer a closed form can't serve?** The
answer fixes the rule — heat-mode beats a closed form **only** for a *transient* problem (`k(T)` /
arbitrary time-dependent BC / layered media / field coupling), never a steady gradient — and surfaces the
single candidate that meets it: **E1**. On verification (below) **E1's heat-mode clause is also
falsified** — the spike anneal's `T(t)` is spatially uniform over the junction (`√(D/α)≈1e-6`), so its
real content is the already-shipped `D(t)` budget path. **The search therefore closes with NO chip-side
heat-mode consumer: heat-mode is Steel-program-only.** What E1 *did* yield is the `D(t)` thermal-budget
deepening (`∫D dt` → shallower `x_j`).

### E1 — Transient spike/RTA anneal `T(t)` → `D(T(t))`  ·  SPLIT on verification (2026-06-14)

> **Verified at build-time (2026-06-14) — the heat-mode premise is FALSIFIED; E1 splits like A2.** The
> backlog parked E1 as *"the one real heat-mode consumer,"* pending the gate *"is `T` emergent or just
> the setpoint?"* Running that gate against the physics, the heat-mode clause is **false** — so the
> emergent-`T` engine build and the real (`D(t)`) deepening separate, exactly as A2's ring/Robin-`G` did.

- **THE verify-at-build gate — resolved against heat-mode.** In silicon the **dopant/thermal
  diffusivity ratio** `√(D_dopant/α_thermal) ≈ √(1.5e-13 / 0.1) ≈ 1.2e-6` (order-of-magnitude robust —
  α_Si never drops below ~0.1 cm²/s). Heat is ~10⁶× more diffusive than dopant, so **at a junction's
  length scale the thermal field is always flat**: to sharpen a thermal gradient across a 0.5 µm junction
  needs a ~25 ns pulse, during which a boron atom moves ~0.001 nm. Two independent legs: (a) E1's
  *named* consumer (dopant diffusion via `D(T)`) can only see a spatially-uniform `T(t)` → `D(T(t))`
  **is** the engine's already-shipped `D(t)`; (b) the one place `T` *is* spatially emergent — the
  ~775 µm **wafer-thickness** gradient in a flash/spike anneal — has **no chip-diffusion consumer** (its
  would-be consumer is thermoelastic slip/stress, unmodeled, not E1). This is how TSUPREM/Sentaurus
  actually model thermal ramps: a uniform `T(t)` through `D(T(t))`, never a heat PDE coupled to dopant.
  (Melt/liquid-phase laser anneal — the *only* place a transient heat solve genuinely bites — is the
  separately-deferred **A5** Stefan front, a different regime with liquid `D`, not solid `D(T(t))`.)
- **Consumer (of the real `D(t)` part).** `x_j` / `R_s` via the existing junction chain — the spike's
  junction depth is set by the **thermal budget** `∫D(T(t))dt`, not the clock time.
- **The `D(t)` budget path — ✅ BUILT (2026-06-14), the OED `effective_Dt` twin.** `chip/diffusion_dopant.py`
  §4 — `ThermalProgram` (a piecewise-linear spike `T(t)` with `.isothermal` as the seam),
  `thermal_budget = ∫D(T(t))dt` (the direct analogue of `coupling.effective_Dt`, just driven by `T(t)`
  instead of the oxidation rate), `equivalent_isothermal_time = budget/D(T_peak)`, `drive_in_program`
  (sealed drive-in under the schedule via the engine's callable-`D(t)` — `_diffuse` unchanged), and
  `spike_budget_time_laplace` (the `D0`-independent Laplace closed form `t_eq ≈ hold + (k·T_peak²/Ea)·
  (1/β_up+1/β_down)`). Triad: tight = the **seam** (`ThermalProgram.isothermal` ⇒ `drive_in` **bit-for-bit**,
  the constant-callable-`D`==scalar guarantee) + the **equivalence inverse** (`equivalent_isothermal_time`
  genuinely inverts `thermal_budget` — a ramp run == an isothermal `drive_in` at `t_eq`, numeric≈numeric)
  + dose **conservation** under `D(t)` + the **Laplace** finding (exact budget ≈ Laplace to ~5 %); no
  conservation amendment (sealed drive-in inherits it). **THE finding:** the Arrhenius integral is
  dominated by a narrow window near the peak — a 19 s spike to 1050 °C deposits only ~2.5 s of
  peak-equivalent budget (a ~7× collapse; the top ~50 °C of the ramp carries ~84 % of `∫D dt`), so a
  faster ramp → smaller budget → **shallower** `x_j` (why RTA gives shallow junctions). Wired via
  `DiffusionKnobs.drivein_program` (opt-in; `None` ⇒ the isothermal step, the pipeline byte-for-byte) →
  `two_step(drivein_program=…)` → `diffusion_junction`. Banked `fab_game/demo_thermal_budget.py`
  (`fab-game-e1.png`, 2 panels: the budget-accrual collapse · `x_j`/`t_eq` vs ramp rate).
- **The heat-mode engine — DEFERRED, premise FALSIFIED (joins Robin-`G`).** Building heat-mode here would
  reproduce the uniform-`T` setpoint — *proof of its own redundancy*, the same structural failure A2's
  Robin-`G` hit. **No remaining chip-side heat-mode consumer exists** — heat-mode is confirmed
  **Steel-program-only** (`test_robin_heat.py`). The rule A2 surfaced holds and is now closed: heat-mode
  beats a closed form only for a *transient* problem, and E1's "transient" turned out to be a
  spatially-uniform `T(t)` the `D(t)` path already serves.
- **Engine/ADR.** None — consumer-side `D(t)`, no engine touch, no ADR (the OED precedent exactly).
- **Verdict.** **SPLIT (2026-06-14):** the `D(t)` thermal-budget path **✅ BUILT** (RTA → `∫D dt` →
  shallower `x_j`); the emergent-`T` heat-mode engine **DEFERRED — premise falsified** (`√(D/α)≈1e-6` →
  `T` is the setpoint over the junction; heat-mode's home is the Steel program).

---

## Recommended sequencing

Promote in **consumer strength × cost** order; everything else stays deferred and named.

1. **C1 — Oxygen / thermal donors.** ✅ **BUILT (2026-06-14)** — strongest consumer (V_t/resistivity via
   the G4a chain), the cited KFR fourth-power kinetics, no engine touch.
2. **D1 — Under-etch.** ✅ **BUILT (2026-06-14)** — the cheap G5-tier completion, reuses the
   functional-kill consumer. Bundled with C1 as the two quick, high-confidence deepenings.
3. **A1 — CG-2 interstitial → leakage.** ✅ **BUILT (2026-06-14).** Completes Voronkov's symmetry through
   the `lifetime.py` leakage channel (slow pull → dislocations → `1/τ += K·ρ_disl` → a leaky diode) → a
   **two-sided** defect window (fast→yield, slow→leakage, optimum at `ξ_t`); also A2's deferred
   *degraded-rim* consumer (the OSF rim is clean *of voids* but dislocation-leaky). A corner — realistic
   CZ is vacancy-rich — so the value is symmetry, not main-line.
4. **A2 — OSF ring (radial `G(r)`), closed-form.** ✅ **BUILT (2026-06-14).** The ring shipped as a
   **closed-form** radial `G(r)` → per-die OSF non-uniformity (edge-vs-center yield), §8-bounded to 1-D
   radial, the engine does **not** participate; **Robin-`G` sourcing stays DEFERRED — premise falsified**
   (a steady gradient is closed-form; the shipped engine cannot beat it). With **A1** now built, the
   OSF ring is the one annulus clean of *both* failure modes (void core / leaky rim).
5. **E1 — transient spike/RTA anneal → `D(T(t))`, the `D(t)` budget path.** ✅ **BUILT (2026-06-14).** The
   `∫D(T(t))dt` thermal-budget deepening (the OED `effective_Dt` twin) → a faster ramp deposits less
   budget → a shallower `x_j` (why RTA gives shallow junctions). The **heat-mode engine clause is
   FALSIFIED** (`√(D/α)≈1e-6` → `T` is the setpoint over the junction), joining Robin-`G`.

**Next promotable = NONE.** With E1 verified, **the named-consumer search is exhausted**: every remaining
edge lacks a device/yield consumer (or had one, Robin-`G`/E1-heat-mode, that verification falsified). The
backlog is now a pure list of honestly-deferred frontier — which is the point. **Heat-mode is confirmed
Steel-program-only**; there is no chip-side heat-mode consumer left to find.

**Stay deferred (no consumer — this is the point, not a backlog of work):** A3 striations (game-layer
variance at most), A4 facets/curvature (nothing reads shape), A5 transient Stefan `X(t)` (quasi-steady
suffices; also the *only* place a transient heat solve bites — melt laser anneal — but a different,
liquid-`D` regime, not E1's solid `D(T(t))`), B1 engine 3-D (no 3-D device — trigger recorded), D2 CMP
(no thickness observable), D3 rebond (game rework rule, not physics), **Robin-`G` heat-mode sourcing AND
E1's emergent-`T` heat mode (both premises FALSIFIED 2026-06-14 — a steady *or* a junction-uniform
gradient is closed-form; heat mode's home is the Steel program).** Each is fenced behind a *named consumer
that does not exist* (or, for Robin-`G`/E1-heat-mode, one that turned out not to exist); promoting any
without that consumer would be the unvalidated-API guess the gate exists to catch.

---

*Cross-refs:* `docs/plans/fab-game.md` §6a (CG cluster), §8 (across-wafer ceiling); ADR 0005
(`docs/decisions/0005-fab-game-layering.md`, the physics/game layer split); ADR 0004 (engine
governance). Memories: [[fab-game-cg2]], [[fab-game-cg3]], [[engine-unfrozen]], [[fab-game-g4]],
[[fab-game-g4b]], [[fab-game-g5]], [[fab-game-g6]], [[chip-device-2d-v111]].
