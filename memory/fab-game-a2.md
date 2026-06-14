---
name: fab-game-a2
description: "fab-game A2 BUILT — the OSF ring = CG-2 made RADIAL: a radial G(r)→ξ(r)→V/I boundary (czochralski.py §1f), per-die killer density keyed on radius_frac → a COP-degraded vacancy core + clean rim (NOT a ring of kills; core mortality modest); closed-form, no engine. The scope-edge-backlog A2 ring half."
metadata: 
  node_type: memory
  type: project
  originSessionId: 2b6f20ff-b183-408a-9e25-9f3e2cc72ed5
---

**project (2026-06-14):** **A2 BUILT** — the **OSF ring** = **CG-2 made radial**, the across-wafer
crystal-growth deepening (the [[scope-edge-backlog]] A2 *ring* half — promoted; the **Robin-`G` sourcing**
half stays **FALSIFIED/deferred**, a steady gradient is closed-form so the engine can't earn its place).
CG-2 ([[fab-game-cg2]]) gave the crystal ONE `ξ=V/G` for the whole wafer (uniform regime); A2 lets `G`
vary with wafer **radius** → a radial defect pattern. New cited-tier physics in `chip/czochralski.py` §1f
(**additive** — CG-1/2/3 + C1 tests untouched): `radial_thermal_gradient(r,G_center,boost)=G_center·(1+
boost·r²)` (G rises toward the edge — periphery cools faster → `ξ(r)=V/G(r)` FALLS outward), `osf_ring_
radius(V,G_center,boost)` (the V/I boundary where `ξ(r)=ξ_t`: `r_OSF=√((V/(ξ_t·G_center)−1)/boost)`, or
`None` off-wafer), `radial_defect_regime` (topology helper). `OSF_RADIAL_GRADIENT_BOOST=1.0` flagged.

**THE finding (advisor, led with — the headline, NOT a footnote):** the reused vacancy `void_defect_
density` is **monotone in ξ**, so the killer-COP density PEAKS at the high-ξ **centre** and is **ZERO at
the ring** → the wafer map is a **COP-degraded vacancy CORE + a clean interstitial RIM — NOT a ring of
dead dies**. The OSF ring is the *boundary* where the kills **STOP**, not a band of kills. **Honest
magnitude (advisor done-check — the G7/CG-2 over-claim trap again):** the void coefficient is the same
*capped* CG-2 house number, so the core mortality is **modest** (demo: centre survival 0.67 ≈ 33%
analytic; 4/21 realized core-average kills), NOT a wipeout — say "COP-degraded", never "dead core"; what
is *provable* is the clean rim (zero density past the ring). (A literal
*degraded ring* — the stacking faults' own junction **leakage** — would feed the interstitial/`lifetime.
py` channel = the separately-deferred **A1** edge → building it here would reach into A1's consumer =
over-build, so it stays a NAMED deferred refinement. Advisor's Design-A-not-B call.)

**Triad (advisor-affirmed — flagged-phenomenology tier like CG-2, NO conservation law, and — the A2
correction — NO engine heat leg, the gradient is a closed-form house *profile*):** tight = the ring
**LOCATION** (`ξ(r_OSF)=ξ_t`, machine-precision crossing; **coefficient-robust** — `osf_ring_radius`
never takes the void coefficient, so the density's zero-crossing sits at `r_OSF` for ANY coefficient) +
the topology **SIGNS** (vacancy centre / interstitial edge). FLAGGED = the `G(r)` profile, the `boost`,
the ring *width*, and — say it plainly — **the ring's on-wafer EXISTENCE itself** (you pick the profile
so the boundary lands in `[0,1]` → illustrative, not a prediction). Density-falls-with-radius = a
**by-construction guard, NOT an anchor** (the v1.11/CG-2 reminder). `boost=0` → uniform `G≡G_center` →
**CG-2 byte-for-byte** (the seam).

**Wired (ONE knob, opt-in, seam-safe):** `CzochralskiKnobs.radial_gradient_boost: float|None=None`
**reinterprets** `thermal_gradient_K_per_mm` as the centre gradient `G_center` (so it requires the
direct-`G` + a `pull_rate`; **guarded incompatible with CG-3's `melt_gradient_K_per_mm`** — the two-`G`
guard) → `grown_in_defect_density_at(radius_frac)` (per-die: vacancy core catches COPs, rim exactly 0) +
`osf_ring_radius`/`osf_zone_regimes` props. **`scatter_defects` gained `density_fn: Callable|None`** —
`None` keeps the byte-identical uniform path (the seam; the `lam>0` guard only bites the radial branch),
provided → per-die `lam=density_fn(d)·area`. Pipeline passes `density_fn = base + cz.grown_in_defect_
density_at(d.radius_frac)` **only when `cz.is_osf_radial`** (non-radial call site untouched; the scalar
`effective_defect_density` is NOT used on the radial branch — the scalar `grown_in_defect_density` is
documented as the centre/worst value). Provenance records `osf_ring_radius`/`osf_zone_regimes`/centre+edge
density at the wafer level (per-particle attribution still the deferred 2nd-draw, as CG-2). **Default
`None` ⇒ uniform ⇒ G1–G7 banked demos byte-for-byte unchanged** — `test_defects`/`test_seam`/`test_voronkov`
PASS UNCHANGED (advisor's seam proof). Fast lane **592 passed** (+20: czochralski +8, `test_osf_ring` 8,
`test_demo_osf_ring` 4). No engine touch, no ADR.

**Demo `fab_game/demo_osf_ring.py` (`fab-game-a2.png`):** balanced house profile V=2, G_center=5, boost=6
→ ring at `r_OSF≈0.59`, ξ(0)=0.40>ξ_t=0.13>ξ(1)=0.057. 3 panels: (1) ξ(r) falls, crosses ξ_t at the ring
(3 zones shaded); (2) the kills STOP at the ring — per-die survival `exp(−D(r)·A)` climbs core→rim, void
density peaks centre/zero past ring; (3) the **G3 consumer** — a seeded stochastic wafer map (clean line),
COP × deaths only in the vacancy core (4/21), rim provably clean (0/40), OSF ring dashed. The consumer =
edge-vs-centre yield **non-uniformity** on the per-die map. **Deferred:** the degraded-ring leakage (A1),
`G(r)` from interface shape (A4 facets/curvature — but the ring uses a house profile, doesn't need it),
Robin-`G` sourcing (FALSIFIED — Steel program's). [[fab-game-cg2]] [[fab-game-g3]] [[scope-edge-backlog]]
[[engine-unfrozen]]
