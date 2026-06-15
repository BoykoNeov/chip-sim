---
name: internal-gettering-source
description: "device-targets S4: cited internal-gettering DIRECTION — oxygen precipitates getter deep-level metals ABOVE a critical [O_i] (~12 ppma); precip needs vacancy-rich Si; Tan-Gardner-Tice PRL 64:196 (1990); ppma↔cm⁻³=5e16/ppma; efficiency magnitude FLAGGED. chip/czochralski.py §1h"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 8f187ae8-81ad-422a-848b-354a39aa3dbb
---

**device-targets S4 (2026-06-15):** the cited model behind `chip/czochralski.py §1h`
`internal_gettering_efficiency` — the BENEFICIAL face of crucible oxygen (the dual-use mirror of C1's
thermal donors [[fab-game-c1]]).

**The ONE cited DIRECTION (load-bearing; flag the magnitude — the repo's cite-direction rule):**
**internal (intrinsic) gettering** = bulk **oxygen precipitates** (+ their punched-out dislocations) are
sinks that trap **fast-diffusing transition metals** (Fe, Cu) out of the near-surface device region, and
precipitation switches on only **ABOVE a critical [O_i] supersaturation** — a wafer below the IG-window
lower edge (~12 ppma) does not precipitate enough to getter. **Tan–Gardner–Tice, "Mechanism of internal
gettering of interstitial impurities in CZ silicon," Phys. Rev. Lett. 64, 196 (1990)** (web-verified
mechanism); the IG-window lore + the denuded-zone/bulk-microdefect picture are the standard reviews
(Borghesi oxygen-in-Si review; Tan–Gardner–Tice). Web search also confirmed the **point-defect coupling**:
strong precipitation in **vacancy-rich** material, ~none in interstitial-rich → ties to the Voronkov
vacancy regime (realistic CZ ξ≈0.29 > ξ_t, [[fab-game-cg2]]); noted-not-modelled (criterion already gates
voids).

**ppma↔cm⁻³ (the advisor's flagged "coin-flip zone" — pinned, not from memory):** by atomic fraction
(Si = 5.0e22 cm⁻³) **1 ppma = 5.0e16 cm⁻³**, so the ~12 ppma threshold ≈ **6.0e17 cm⁻³** (the
new-ASTM-consistent figure; older ASTM IR-absorption calibrations — F121-76 4.81e17, F121-80 2.45e17,
JEIDA 3.03e17 cm⁻² coefficients on α — read ~25% higher). `IG_CRITICAL_OXYGEN_CM3 = 6e17` is the citation;
`IG_OXYGEN_SCALE_CM3=2e17` (precip-density ramp) + `IG_MAX_EFFICIENCY=0.95` (never-perfect ceiling) +
the whole removed-fraction curve are **FLAGGED house numbers** (ADR 0005 §5).

**Donor side re-anchored (same web pass):** the thermal-donor anneal is **<550 °C** (above → donors
dissociate), and the **universal final forming-gas/sinter (~400–450 °C)** sits in the TD-formation window
→ donors re-form from residual O at the last step (the non-skippable donor budget — the advisor's
hatch-closer; `fab_game` `forming_gas_anneal_min`, defaults 0 → C1 seam). The TD-control patent family
(WO2002084728A1) gives "at 450 °C, ~10 ppma forms ~10× the donors of ~5 ppma" (power-law ~3.5, consistent
with C1's KFR-4 [[fab-game-c1]]).

Consumed by `chip/purification.py` `getter_metals(contamination, efficiency)` (Fe/Cu only, never
Na/B/P → orthogonal to the V_t chain) before the [[fab-game-g4b]] `device_leakage` read. See
[[device-targets-plan]].
