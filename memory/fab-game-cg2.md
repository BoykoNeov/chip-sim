---
name: fab-game-cg2
description: "fab-game CG-2 BUILT — Voronkov V/G criterion in chip/czochralski.py; vacancy/void COP density feeds the G3 defect map; the in-model brake CG-1 lacked; opt-in, seam-safe"
metadata: 
  node_type: memory
  type: project
  originSessionId: af9f62ce-8ebb-4040-af52-740987896b9f
---

**project (2026-06-13):** **CG-2 BUILT** — the second Czochralski **crystal-growth deepening** (plan
§6a; the brake [[fab-game-cg1]] deferred and [[fab-game-g2]]'s named cost). New cited physics in
`chip/czochralski.py` §1c (**additive** — Scheil/CG-1 tests untouched): `voronkov_ratio(V,G)=V/G`
(mm²/(K·min)) + `grown_in_defect_regime` (vacancy/interstitial/osf vs `VORONKOV_CRITICAL_RATIO=0.13`,
**Voronkov J. Cryst. Growth 59:625 1982**) + `void_defect_density(ξ)=coeff·max(0,ξ−ξ_t)` (FLAGGED
`COP_DENSITY_PER_RATIO_EXCESS_CM2=0.3`). `ξ=V/G > ξ_t` ⇒ **vacancy-rich** (voids/COPs → gate-oxide-
integrity killers); `< ξ_t` ⇒ interstitial (dislocations); `= ξ_t` ⇒ the OSF ring.

**Triad (advisor-affirmed — flagged-phenomenology tier like [[fab-game-g5]], NO conservation law):**
tight = the cited criterion *form* + `ξ_t` value (pinned, not from memory) **and** the definitional-
exact regime flip at `ξ=ξ_t` (the legit LIMIT leg, the CG-1 `Δ=0→k₀` analogue); **the zero-below-
threshold + monotone-above are BY-CONSTRUCTION regression guards, NOT anchors** (advisor — the v1.11
[[chip-device-2d-v111]] correction again); the void→density **coefficient is house/flagged** — it sets
the fall-off *depth*, never the window *location* (that is pure `ξ_t`), so it cannot manufacture the
trade-off's optimum. **`G` is a flagged house knob**; the shipped Robin heat-mode sourcing (`test_robin_
heat.py`) is the **named deferred refinement** (no consumer needs the field → "build explicit, not 2-D"
anti-over-build, advisor).

**Wired (ONE knob, opt-in, seam-safe):** `CzochralskiKnobs.thermal_gradient_K_per_mm: float|None=None`
(+ `voronkov_ratio`/`grown_in_defect_regime`/`grown_in_defect_density` props; setting `G` **requires** a
`pull_rate` → raises) → `Recipe.effective_defect_density = wafer_prep.defect_density + grown_in_defect_
density`, which the pipeline scatters through the **same cited G3 Poisson map** ([[fab-game-g3]] —
two Poisson processes superpose, so COPs ride the validated `poisson_yield`, non-circular). **Default
`None` ⇒ grown-in `=0.0` ⇒ `+0.0` exact ⇒ G1–G7 banked demos byte-for-byte unchanged** (and an
*interstitial*-regime growth adds 0 too — the cost is **criterion-gated**, the seam-relevant lever).
Fast lane 506→**522** (+16: czochralski +7, `test_voronkov` 5 wiring, `test_demo_voronkov` 4). No engine
touch, no ADR.

**THE payoff — the in-model brake CG-1 lacked:** pulling faster (or a cooler hot zone, `G`↓) pushes `ξ`
above `ξ_t` → COP killers → yield down. So pull rate is finally **two-sided**: CG-1 flattens doping
(benefit), CG-2 seeds voids (cost). **Honest magnitude (advisor, checked FIRST):** realistic CZ (V≈1
mm/min, G≈3.5) sits at `ξ≈0.29 > ξ_t` → **vacancy-rich** (historically COP-containing unless `G`
engineered up to ≈7.7 K/mm) — matches reality; coefficient recalibrated 1.0→0.3 so realistic CZ is a
*noticeable but survivable* ~0.5 COP yield at the coarse die (A=16 cm²), not an instant cliff.

**THE demo blocker (advisor, resolved before building — load-bearing):** the G3 stochastic scatter
fires **only with variation on**, but boule sweeps run `NO_VARIATION` to isolate the Scheil signal → a
naively-built demo would scatter ZERO grown-in COPs (looks like a wiring bug). So `demo_voronkov` shows
the CG-2 consequence **analytically** as `poisson_yield(grown_in(V,G), die_area)` — the law the scatter
*converges* to (already a G3 invariant, not re-shown noisily), the CG-1 way (deterministic). 3 panels:
(1) criterion G-sweep (coefficient-robust direction); (2) brake pull-sweep at two `G` (hotter zone
tolerates faster pull); (3) CG-1+CG-2 — combined = CG-1 parametric × CG-2 defect survival, **maximized
on the defect-free plateau `V≤V*=ξ_t·G`**, falls above. **THE honest finding (advisor done-check — the
G7 [[fab-game-g7]] over-claim pattern again, I papered over the flat plateau I'd noticed):** CG-1's
parametric fraction is **FLAT across the decision region** (only rises at pulls where CG-2 has already
crushed yield) → the two do **NOT trade off**; **CG-2's criterion ALONE sets the pull**. On yield the
slow plateau end = the boundary; the boundary's only edge is **throughput (UNMODELED)** — NOT "grow as
fast as the criterion allows" on yield grounds. The plateau *location* is the cited `ξ_t`
(coefficient-robust). Banked `fab-game-cg2.png`.

**Provenance honesty (advisor):** a **wafer-level** grown-in/`ξ`/regime note in the `wafer_prep`
StepRecord when grown-in `>0` — but the per-die failure trail (`diagnose`) still reads "caught N killer
particle(s)" (the fix is lower pull / higher `G`, not a cleaner line); per-particle grown-in-vs-process
tagging needs a 2nd Poisson draw + touches the determinism contract → **deferred, decided consciously**.
**Deferred edges:** interstitial-side dislocation/leakage cost (only vacancy→GOI wired), the **OSF-ring
radial pattern** (density uniform here), Robin-`G` sourcing, striations, **CG-3 Stefan front** (the last,
the only engine-physics one). [[fab-game-cg1]] [[fab-game-g2]] [[fab-game-g3]] [[engine-unfrozen]]
