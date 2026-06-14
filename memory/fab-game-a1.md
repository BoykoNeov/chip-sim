---
name: fab-game-a1
description: "fab-game A1 BUILT — the interstitial side of Voronkov: slow pull (ξ<ξ_t) → grown-in dislocations → junction LEAKAGE (chip/czochralski.py §1g dislocation_defect_density, the void-density mirror; chip/lifetime.py dislocation_recombination_rate, 1/τ+=K·ρ_disl). Two-sided defect window (fast→yield, slow→leakage, optimum at ξ_t); A1 is A2's deferred leaky-rim consumer → OSF ring = the one annulus clean of both. No new knob, no engine, corner."
metadata:
  node_type: memory
  type: project
  originSessionId: 2b6f20ff-b183-408a-9e25-9f3e2cc72ed5
---

**project (2026-06-14):** **A1 BUILT** — the **interstitial side** of the Voronkov criterion (the
[[scope-edge-backlog]] A1 edge, the last named CG follow-on with a consumer). CG-2 ([[fab-game-cg2]])
wired only the **vacancy** side (`ξ=V/G > ξ_t` → COP voids → the G3 **yield** map); A1 wires the mirror
`ξ < ξ_t` (slow pull / over-steep `G`) → **interstitial-rich** silicon → grown-in **dislocations**, which
are recombination centres → they raise junction **LEAKAGE** (the G4b [[fab-game-g4b]] [[chip-coupling-v12]]-style
`chip.lifetime` channel), **not** the yield map. New cited-tier physics (additive; CG-1/2/3 + C1 + A2 tests
untouched):
- `chip/czochralski.py` §1g `dislocation_defect_density(ξ)=coeff·max(0,ξ_t−ξ)` — the **exact mirror** of
  `void_defect_density`, reflected across `ξ_t`; `DISLOCATION_DENSITY_PER_RATIO_DEFICIT_CM2=1e6` flagged.
  Same cited regime split (**Voronkov J.Cryst.Growth 59:625 1982**, already pinned by CG-2).
- `chip/lifetime.py` `dislocation_recombination_rate(ρ_disl)=K·ρ_disl` (`DISLOCATION_RECOMBINATION_COEFF=30`
  flagged) + a `dislocation_density=` kwarg on `srh_lifetime`/`device_leakage` → `1/τ = 1/τ_bulk + Σσ_n·v_th·N
  + K·ρ_disl` (the metals' channel, **a new contributor not a new output**).

**THE payoff — a two-sided defect window (advisor's headline).** Before A1 a SLOW pull was **free** on yield
(CG-1 flattened doping = benefit, CG-2's COP cost only switched on ABOVE ξ_t). A1 closes it: too-fast costs
**yield** (COP voids), too-slow costs **leakage** (dislocations), the defect-free optimum **AT ξ_t** (both
densities zero). The optimum's **LOCATION is the cited ξ_t (coefficient-robust, tight)**; only the cost
**depths** flag. **A1 is also A2's deferred consumer:** A2 ([[fab-game-a2]]) proved the OSF interstitial
**rim** clean *of voids* but deferred its dislocation leakage to A1 → now the rim is dislocation-**leaky** per
die → **the OSF ring is the one annulus clean of BOTH failure modes** (void-killed core / leaky rim / clean
ring). Demo `fab-game-a1.png`: radial V=2,G_center=5,boost=6 → 32/40 rim dies scrapped on leakage, ring r≈0.59.

**Triad (advisor-affirmed — flagged-phenomenology tier, EXACTLY CG-2/A2's: NO conservation law, NO engine).**
TIGHT = the definitional flip at `ξ=ξ_t` (the legit LIMIT leg) — density 0 at AND above ξ_t **by construction**
(a guard, **NOT an anchor** — the v1.11/CG-2 reminder); the seam ρ_disl=0 → τ=τ_bulk **bit-for-bit**. FLAGGED =
the czochralski density coefficient **AND** the lifetime `K` — **only their PRODUCT (3e7) sets the leakage
depth** (ONE flagged magnitude factored across two modules for modularity — the `void_defect_density`→
`poisson_yield` split mirrored; advisor: do **not** present as two independent calibrations).

**THE binding calibration (advisor's G4b-style "pin numbers FIRST"):** chain verified numerically before any
module code — `clean 0.009 < MGS-2pass 0.046 < solar-1pass 1.1 < WINDOW 10 < dislocation scrap` (a deep slow
pull V=1,G=20→ξ=0.05 → 21.9 nA/cm²; deepest ξ→0 tops ~35 — **modest, ~3× window, not a cliff**). Just below ξ_t
(G=8→ξ=0.125) leakage is a survivable 1.4 nA/cm² → a real in-window interstitial band. Existing leakage tests
(solar/MGS clear the window) unaffected (they set no CZ gradient).

**Wired — NO new knob (advisor's one-code-path call), seam-safe.** `CzochralskiKnobs.interstitial_dislocation_
density[_at(radius_frac)]` reads the **existing** `(V,G)` and switches on automatically on the interstitial
side; uniform path = the scalar, radial path = per-die `dislocation_defect_density(voronkov_ratio(V,G(r)))`
(the rim complement of `grown_in_defect_density_at`). Threaded to **BOTH** `device_step` call sites — main loop
**and rework** (advisor's flagged blind spot) — keyed on `radius_frac`. `device_step` gained a `dislocation_
density=` kwarg + a `rho_disl` fingerprint (added only when >0 → vacancy/clean device record byte-unchanged);
`diagnose` distinguishes the dislocation leakage (crystal-growth, ξ<ξ_t) from the metal-SRH leakage (G4b) via
the fingerprint. Wafer-level provenance records the interstitial/rim dislocation density. **Default seam:**
`ξ ≥ ξ_t` or CG-2 off ⇒ ρ_disl=0 ⇒ `device_leakage` byte-for-byte ⇒ G1–G7 + all prior demos unchanged;
`test_seam`/`test_defects`/`test_leakage`/`test_voronkov`/`test_osf_ring` PASS UNCHANGED. **V_t/I_Dsat never
move** (the bystander — slow pull leaks the diode, not the threshold; demo ladder V_t=0.547 flat across all).

**Honest magnitude (lead with it — the CG-2 finding restated):** realistic CZ is **vacancy-side** (ξ≈0.29>ξ_t),
so the dislocation cost only bites at a **deliberately** slow pull / over-steep G → A1 is a **CORNER**, its
value the criterion's SYMMETRY (slow pull no longer free) + A2's rim, NOT a main-line trade-off.

Demo `fab_game/demo_dislocation.py` (`fab-game-a1.png`, 3 panels): two-sided ξ-window · leakage ladder with
V_t the flat bystander · radial void-core/leaky-rim/clean-ring map. Fast lane **611 passed** (+19: czochralski
+3, lifetime +4, `test_dislocation` 8, `test_demo_dislocation` 4). No engine, no ADR. **Still deferred:** the
dislocation→τ *magnitude* (flagged), high-injection, gettering/precipitation. [[fab-game-cg2]] [[fab-game-a2]]
[[fab-game-g4b]] [[scope-edge-backlog]] [[engine-unfrozen]]
