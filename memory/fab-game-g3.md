---
name: fab-game-g3
description: "project (2026-06-13): G3 BUILT — wafer prep + killer-particle Poisson yield + TTV/bow geometry; the die map made physical"
metadata: 
  node_type: memory
  type: project
  originSessionId: b1e310d4-74bb-4d74-ac80-f583b11bb698
---

**G3 BUILT (2026-06-13)** — "the die map made physical" on [[fab-game]] (G1 [[fab-game-g1]], G2
[[fab-game-g2]] done). New cited physics `chip/wafer_prep.py` + game wiring; fast lane 338→**373**
(+35: 14 chip triad, 9 `test_defects`, 7 `test_geometry`, 4 `test_demo_wafer_prep`, +1 seam). **No
engine amendment, no ADR, no chip gallery card** (artifact in the game layer). Commits `d9997ae`
(+`aacc09f` rework_polish guard).

**THE physics — defect-limited yield (Murphy/Poisson).** A die catching a **killer** particle is dead
**functionally**; P(zero killers) on area `A` at killer density `D₀` = `Y=exp(−D₀·A)`. Carried the
**Stapper negative-binomial** `(1+D₀A/α)^(−α)` *formula* for the `α→∞`→Poisson limit leg (clustering
RAISES yield; Murphy's triangular ≈ α≈4.2) but built Poisson (un-clustered) placement — **clustered
placement = named scope edge, deferred** (the G2-discipline: build the tight core, fence the loose).
Geometry = **exact bookkeeping** (slice→lap/CMP → thickness/TTV/bow; CMP improves TTV not bow). Cited
**Murphy 1964 (Proc. IEEE 52:1537, verified)** + Stapper (author-level); `D₀`/α flagged loose.

**Triad** (`test_wafer_prep.py`, 14): analytic = `Y(0)=1` **exact** (the one bit-exact anchor) +
`α→∞`→Poisson (a **convergent/tolerance** limit, NOT bit-exact unlike Scheil's `k→1`); conservation =
**area-additivity** `Y(A₁+A₂)=Y(A₁)·Y(A₂)` (deterministic identity — NOT an RNG test; advisor: chip/
stays flake-free); benchmark = cited forms + illustrative `D₀` band.

**THE build-correctness crux (advisor, the G2 "N_seed-exact" analogue): one byte-identical `A_die`.**
`state.die_area_cm2(grid_n, wafer_diameter_mm) = (2/grid_n · radius_cm)²` is the SINGLE definition both
the placement and the closed form route through → the empirical kill rate converges to `exp(−D₀A)`.
Placement (`fab_game/defects.py`) = **per-die Poisson** `nᵢ~Poisson(D₀·A_die)`, points uniform in the
die's cell — which by the **Poisson restriction/superposition** property IS the global wafer scatter
restricted to kept dies (sidesteps off-wafer/edge-exclusion discards; positions in `[-1,1]` wafer-radius
units). All placed defects are killers (D₀ = *killer* density); `killer` flag kept for future cosmetic
particles. The **convergence MC test lives in fab_game** (seeded `default_rng`, tol 0.02–0.03, verified
inside) — doubles as the propagation-wired invariant.

**Wiring.** `Die` += `defects`/`killed_by_defect`; `WaferState` += `geometry`; `WaferPrepKnobs` (geometry
+ `defect_density`, **default 0.0** = clean line → seam + G1/G2 demos byte-for-byte unchanged; scatter
short-circuits no-RNG when disabled OR density≤0). RNG order: scatter first (step 1), then perts.
Killer defect = a **functional** fail in `SpecSet.verdict` (transistor exists but dead — distinct from
litho-not-resolved where device *refuses*). `GeometrySpec` (TTV hi=1.0µm / bow hi=40µm) = **wafer-level
scrap** (fails every die), threaded once through `_test_wafer`. `rework_polish` = re-CMP a TTV scrap
(eats thickness, can't fix bow or remove a particle; leaves passing dies untouched). `wafer_prep` is
provenance step 1; `diagnose` got a killer-defect branch.

**Q's resolved (advisor):** geometry = **gate-only** (don't wire TTV→litho-focus; G1 defocus + G2 Scheil
already carry propagation — the **TTV→DOF-budget** wire is the named next edge, honest framing = residual
*site-flatness* not raw bow eats DOF since wafers are vacuum-chucked flat). Poisson core not NB-placement.

**Banked** `demo_wafer_prep`/`fab-game-g3.png` (3-panel): the **particle map** (× at locations, red=killed
dies) + the empirical yield **converging to the cited Poisson curve** (the headline, λ=0.49→68% at the
map density) + the **TTV scrap→re-polish** (740→700µm thickness cost). Demo uses a **defects-only
Variation** (enabled, all parametric σ/trend zeroed) to isolate the defect signal (the G2 NO_VARIATION
move). [[engine-unfrozen]] untouched.
