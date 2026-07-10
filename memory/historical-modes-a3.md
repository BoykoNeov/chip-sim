---
name: historical-modes-a3
description: "project (2026-07-10): historical-modes A3 BUILT — HCl mobile-Na gettering (→Q_ox→V_t) + high-pressure oxidation (→exact 1/P ∫D dt budget)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bf2fd20-d0eb-4cac-9a31-e85f7e8a2536
---

**Historical-modes A3 BUILT** (`chip/oxidation_history.py` + `demo_oxidation_history.py` + tests; gallery
card `hist·A3`; pure additive **consumer** of `oxidation.py`/`purification.py`/`device.py` — no engine
change, no existing behaviour touched, same discipline as [[historical-modes-a1]]). Two period oxidation
ambients bundled in ONE chunk because their consumers are **orthogonal** (V_t vs the ∫D dt budget):

**§A — HCl/chlorine gettering → the Na→Q_ox→V_t chain (G4a, [[fab-game-g4a]]).** Cl₂ (from HCl in the
ambient) getters mobile Na⁺ → **lowers Q_ox** → feeds the existing `purification.sodium_oxide_charge` →
`device.threshold_voltage` chain; a marginal-Na gate that walked V_t down recovers toward the clean-oxide
value. Model = a **saturating removed-fraction** `f=ceiling·pct/(pct+half)` (`CHLORINE_MAX_GETTERING=0.9`,
`CHLORINE_HALF_PERCENT=1.5` — both FLAGGED house numbers; only the DIRECTION is cited). Seam:
`chlorine_percent=0` → f≡0 → `sodium_oxide_charge` **bit-for-bit**. **Polarity is INVERTED vs A1**: the
opt-in flag turns on the *successor* (HCl removes the Na penalty); `Cl=0` is the pre-HCl period that hit the
wall. Cited: Kriegler–Cheng–Colton, *JECS* 119(3):388 (1972). Scope edges (named, not silent): models the
**static** mobile-ion V_t offset, NOT bias-temperature drift dynamics; Cl rate-enhancement (Cl also speeds
oxidation) not modelled — scoped to the V_t consumer only.

**§B — high-pressure oxidation → the ∫D dt collateral-budget chain (E1, [[fab-game-e1]]).** Both DG rate
constants scale `∝P` (Henry's law; measured linear 5–20 atm by **Razouk–Lie–Deal, *JECS* 128(10), 1981**).
**The load-bearing build decision (advisor):** apply ONE shared exponent = 1 to *both* B and B/A → `A=B/(B/A)`
is **pressure-invariant** → the whole quadratic `x²+Ax=P·B·t` scales cleanly → for a fixed target oxide
**oxidation time and collateral budget scale EXACTLY as 1/P in every regime** (linear/transition/parabolic,
NOT just asymptotes) — a genuine **tight** identity, not an approximation. Time-to-thickness reuses
`oxidation.tau_offset(x,B,A)=(x²+Ax)/B` (the DG inverse — no new function). Collateral budget = the
**intrinsic** isothermal `D_dopant(T)·t`, and a test pins it EQUAL to the real E1 `dd.thermal_budget(d,
ThermalProgram.isothermal(T, t·3600))` (isothermal takes SECONDS) — "feeds E1" tied to the actual consumer,
not a parallel formula. The bigger *historical* win — trade pressure for **temperature** (same oxide, same
time, lower T → Arrhenius D collapse; e.g. 0.5 µm wet field oxide, 1050→815 °C at 20 atm ⇒ ×701 less boron
budget) — ships as a **FLAGGED** worked example via a `brentq` root-find (`temperature_for_same_oxide`), NOT
a tight leg. Seam: `pressure_atm=1.0` → `grow_oxide` bit-for-bit. Scope edges: ideal-linear scaling (real
dry B/A can be mildly sublinear — the =1 choice makes the 1/P identity exact *by construction*, flagged);
OED ([[chip-coupling-v12]]) would add to the intrinsic budget — named, not folded in (would break the clean
1/P). Defaults target a THICK wet field oxide at 1050 °C (parabolic — where 1/P bites hardest).

Order [[historical-modes-a1]]: A1 ✅ → **A3 ✅** → B6 → H0 → A2 → A4 → B5. See [[deal-grove-oxidation-source]],
[[massoud-thin-oxide-source]].
